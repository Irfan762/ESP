"""
tests/e2e/conftest.py
---------------------
GSoC Proposal: Playwright + pytest-django integration layer.

WHY THIS FILE EXISTS:
The legacy ESP test suite used django-selenium (last released ~2015), which
requires a running external Selenium server and has no auto-wait semantics.
This conftest wires Playwright's modern page object directly into
pytest-django's `live_server` fixture, giving us:
  - A real Django dev server spun up per test session
  - Playwright's built-in auto-waiting (no more `time.sleep()` hacks)
  - Full network interception (used in test_scheduling_grid.py)

IMPORTANT — async context note:
pytest-playwright runs Playwright inside an asyncio event loop. Django's ORM
is synchronous and raises SynchronousOnlyOperation if called from async
context. We work around this by setting DJANGO_ALLOW_ASYNC_UNSAFE=1 (safe
for tests only) and using TransactionTestCase-style DB access via
pytest.mark.django_db(transaction=True) on each test.
"""

import os
import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache

# Allow Django's synchronous ORM to be called from within Playwright's
# asyncio event loop. This is the standard approach for pytest-playwright
# + pytest-django integration. NEVER set this in production code.
os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "1")


# ---------------------------------------------------------------------------
# Cache flush fixture
# WHY autouse=True: ESP's CacheFlushTestCase flushes cache around every test
# to prevent cross-test state leakage from Django's per-request cache middleware.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def flush_cache_around_test():
    """
    Mirrors ESP's CacheFlushTestCase.setUp/tearDown behaviour.
    Runs before AND after every single Playwright test in this directory.
    """
    cache.clear()
    yield
    cache.clear()


# ---------------------------------------------------------------------------
# live_page fixture
# WHY: pytest-playwright's built-in `page` fixture doesn't know about
# Django's live_server base URL. We attach it so tests use relative paths.
# ---------------------------------------------------------------------------
@pytest.fixture()
def live_page(page, live_server):
    """
    A Playwright `page` pre-configured with the Django live_server base URL.
    """
    page.base_url = live_server.url
    return page


# ---------------------------------------------------------------------------
# auth_page fixture
# WHY: Most ESP admin views require authentication. Rather than repeating
# the login flow in every test, we create one authenticated session here.
# This is the Playwright-recommended pattern for auth:
# https://playwright.dev/python/docs/auth
# ---------------------------------------------------------------------------
@pytest.fixture()
def auth_page(live_page, django_user_model):
    """
    Returns a Playwright `page` already logged in as a test admin.
    """
    django_user_model.objects.create_superuser(
        username="test_admin",
        email="admin@test.esp",
        password="testpass123",
    )

    live_page.goto(f"{live_page.base_url}/myesp/login/")
    live_page.fill("input[name='username']", "test_admin")
    live_page.fill("input[name='password']", "testpass123")
    live_page.click("button[type='submit']")

    # WHY wait_for_url instead of time.sleep(): Playwright polls the URL
    # until it matches or times out — zero flakiness from race conditions.
    live_page.wait_for_url(f"{live_page.base_url}/esp/**")

    return live_page
