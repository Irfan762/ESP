"""
tests/e2e/test_scheduling_grid.py
----------------------------------
GSoC Proposal: Playwright E2E test for the AJAX scheduling grid.

WHY THIS IS THE CROWN JEWEL:
The ESP scheduling grid (Matrix.js + Scheduler.js) is a complex legacy
JavaScript interface that:
  1. Renders a dynamic grid via AJAX after page load
  2. Handles drag-and-drop to schedule classes into rooms/timeslots
  3. Makes POST requests to /ajax_schedule_class on each drop
  4. Displays inline error/success messages without a page reload

The old Selenium tests couldn't reliably test this because:
  - No network interception → couldn't simulate server errors
  - Required `time.sleep()` to wait for JS rendering → flaky in CI
  - Couldn't assert on XHR response-driven DOM changes

Playwright solves ALL of these with:
  - page.route() for network mocking
  - page.wait_for_selector() / expect() for deterministic DOM waiting
  - Full drag-and-drop support via .drag_to()
"""

import json
import pytest
from playwright.sync_api import expect, Route, Request

# All tests in this module need DB + a live server
pytestmark = pytest.mark.django_db(transaction=True)

# The program URL slug used in the scheduling grid route.
# In a real test run this would be created via a factory/fixture.
PROGRAM_URL = "mit_splash/2024"


def test_scheduling_grid_renders(auth_page):
    """
    Verify that Matrix.js finishes rendering the grid before we interact.

    WHY wait_for_selector() instead of time.sleep():
    Matrix.js populates the grid asynchronously after an AJAX call to fetch
    section/room data. The old Selenium approach used `time.sleep(3)` which
    is both slow and still flaky on loaded CI machines.

    wait_for_selector() polls the DOM efficiently and proceeds the instant
    the element appears — typically 10-50x faster than a fixed sleep.
    """
    auth_page.goto(f"{auth_page.base_url}/manage/{PROGRAM_URL}/ajaxscheduling")

    # Wait for Matrix.js to finish rendering open cells.
    # 'td.ajax-cell-open' is only present after the JS grid initialisation
    # completes — this is our reliable "grid is ready" signal.
    auth_page.wait_for_selector("td.ajax-cell-open", timeout=15_000)

    # Confirm at least one draggable section exists in the unscheduled panel
    section = auth_page.locator("div.section-draggable").first
    expect(section).to_be_visible()


def test_drag_drop_shows_room_conflict_error(auth_page):
    """
    Simulate a drag-and-drop that triggers a 400 'Room already booked' error.

    WHY page.route() (network mocking):
    We don't want this test to depend on a specific DB state (two sections
    competing for the same room). Instead, we intercept the POST that
    Scheduler.js fires on drop and return a controlled 400 response.

    Benefits:
      - Test is deterministic regardless of DB fixture state
      - We can test every error code/message the UI should handle
      - No need to set up complex conflicting schedule fixtures
      - The test runs faster (no real DB write round-trip)
    """

    # --- Step 1: Register the network intercept BEFORE navigation ---
    # WHY before navigation: page.route() is registered on the page context.
    # If we navigate first, the page might fire requests before the route
    # handler is in place and we'd miss them.
    def handle_schedule_request(route: Route, request: Request):
        """
        Intercept POST to /ajax_schedule_class and return a mocked 400.

        This simulates the server-side conflict detection that ESP's
        scheduling backend performs (checking room/timeslot availability).
        """
        # Fulfill with a 400 and the exact JSON body the JS error handler
        # expects. This tests that Scheduler.js correctly parses and
        # displays the `error` field from the response body.
        route.fulfill(
            status=400,
            content_type="application/json",
            body=json.dumps({"error": "Room already booked"}),
        )

    # Intercept any URL containing 'ajax_schedule_class' (GET or POST)
    auth_page.route("**/ajax_schedule_class**", handle_schedule_request)

    # --- Step 2: Navigate and wait for the grid to be ready ---
    auth_page.goto(f"{auth_page.base_url}/manage/{PROGRAM_URL}/ajaxscheduling")

    # Deterministic wait — only proceed once Matrix.js has rendered the grid.
    # This replaces every `time.sleep()` call in the legacy Selenium suite.
    auth_page.wait_for_selector("td.ajax-cell-open", timeout=15_000)

    # --- Step 3: Perform the drag-and-drop ---
    # Grab the first unscheduled section and the first open cell
    section = auth_page.locator("div.section-draggable").first
    target_cell = auth_page.locator("td.ajax-cell-open").first

    # WHY .drag_to() over ActionChains:
    # Playwright's drag_to() dispatches the full sequence of
    # pointerdown → pointermove → pointerup events that Scheduler.js
    # listens to, making it behaviorally identical to a real user drag.
    # Selenium's ActionChains had known issues with HTML5 drag-and-drop
    # events not firing correctly in headless mode.
    section.drag_to(target_cell)

    # --- Step 4: Assert the error message appears in the UI ---
    # Scheduler.js should read the `error` field from the 400 response
    # and inject it into #scheduler-message-panel.
    message_panel = auth_page.locator("#scheduler-message-panel")

    # WHY expect().to_contain_text() over assert:
    # This has built-in retry logic — it will keep checking until the text
    # appears (JS is async) or the timeout expires. No sleep needed.
    expect(message_panel).to_contain_text("Room already booked", timeout=5_000)

    # Also assert the panel has an error styling class so we know the UI
    # is communicating failure clearly to the scheduler operator
    expect(message_panel).to_have_class("error")


def test_successful_schedule_shows_confirmation(auth_page):
    """
    Contrast test: a 200 response should show a success message.

    WHY include this: Having both the error AND success path tested proves
    that the message panel logic is conditional on the response status,
    not just always showing one state.
    """

    def handle_success(route: Route, request: Request):
        route.fulfill(
            status=200,
            content_type="application/json",
            body=json.dumps({"status": "success", "message": "Class scheduled"}),
        )

    auth_page.route("**/ajax_schedule_class**", handle_success)
    auth_page.goto(f"{auth_page.base_url}/manage/{PROGRAM_URL}/ajaxscheduling")
    auth_page.wait_for_selector("td.ajax-cell-open", timeout=15_000)

    section = auth_page.locator("div.section-draggable").first
    target_cell = auth_page.locator("td.ajax-cell-open").first
    section.drag_to(target_cell)

    message_panel = auth_page.locator("#scheduler-message-panel")
    expect(message_panel).to_contain_text("Class scheduled", timeout=5_000)
    expect(message_panel).not_to_have_class("error")
