"""
tests/e2e/test_auth_smoke.py
-----------------------------
GSoC Proposal: Smoke test for the ESP login flow.

WHY THIS TEST:
Before testing complex features like the scheduling grid, we need a fast
"canary" test that confirms the live server is up, the login view renders,
and Django's session auth works end-to-end. If this fails, all other E2E
tests are meaningless — so it runs first (alphabetically) and is cheap.

This replaces the pattern of manually verifying the dev server in a browser
before running the old Selenium suite.
"""

import pytest
from playwright.sync_api import expect


# Mark the whole module as needing DB access.
# WHY: pytest-django blocks DB access by default for speed. We need it here
# to create the test user via the `auth_page` / `django_user_model` fixtures.
pytestmark = pytest.mark.django_db(transaction=True)


def test_login_redirects_to_dashboard(live_page, django_user_model):
    """
    Smoke test: a valid login should redirect to /esp/.

    Uses `live_page` (not `auth_page`) so we can test the login form itself.
    """
    # Arrange — create a regular user (not superuser) to test the common path
    django_user_model.objects.create_user(
        username="smoke_user",
        password="smokepass123",
    )

    # Act — navigate to the login page
    live_page.goto(f"{live_page.base_url}/myesp/login/")

    # WHY fill() over send_keys(): Playwright's fill() clears the field first
    # and dispatches proper input events, making it reliable across all browsers
    live_page.fill("input[name='username']", "smoke_user")
    live_page.fill("input[name='password']", "smokepass123")

    # Submit the form
    live_page.click("button[type='submit']")

    # Assert — Playwright's `expect` has built-in retry logic (default 5s timeout)
    # WHY expect() over assert page.url == ...: expect() will keep retrying until
    # the condition is true or the timeout expires, eliminating race conditions
    # that plagued the old `time.sleep(2)` pattern in the Selenium tests.
    expect(live_page).to_have_url(f"{live_page.base_url}/esp/")


def test_invalid_login_stays_on_login_page(live_page):
    """
    Negative smoke test: wrong credentials should NOT redirect.
    Ensures the auth view returns a 200 with an error, not a 302.
    """
    live_page.goto(f"{live_page.base_url}/myesp/login/")
    live_page.fill("input[name='username']", "nobody")
    live_page.fill("input[name='password']", "wrongpassword")
    live_page.click("button[type='submit']")

    # Should stay on the login page — URL must NOT change to /esp/
    expect(live_page).to_have_url(f"{live_page.base_url}/myesp/login/")

    # The login form should display an error message
    error_locator = live_page.locator(".errorlist, .alert-danger, #login-error").first
    expect(error_locator).to_be_visible()
