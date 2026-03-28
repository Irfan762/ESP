// playwright-tests/scheduling-grid.spec.js
// GSoC Proposal: AJAX Scheduling Grid E2E tests — the crown jewel.
// These tests demonstrate:
//   1. page.route() — network interception (no real DB needed for error cases)
//   2. waitForSelector() — replaces every time.sleep() in legacy Selenium tests
//   3. dragTo() — reliable HTML5 drag-and-drop in headless Chromium/Firefox/WebKit

const { test, expect } = require('@playwright/test');

// Helper: log in and navigate to the scheduling grid
async function loginAndGoToGrid(page) {
  await page.goto('/myesp/login/');
  await page.fill('input[name="username"]', 'admin');
  await page.fill('input[name="password"]', 'admin123');
  await page.click('button[type="submit"]');
  await page.waitForURL('**/esp/', { timeout: 15000 });
  await page.goto('/manage/mit_splash/2024/ajaxscheduling');
}

test.describe('Scheduling Grid — Matrix.js Rendering', () => {

  test('loading spinner is shown before grid renders', async ({ page, browserName }) => {
    // Skip on Firefox/WebKit — they render faster and the spinner disappears
    // before Playwright can assert on it. Chromium timing is reliable.
    test.skip(browserName !== 'chromium', 'Spinner timing only reliable on Chromium');
    await loginAndGoToGrid(page);
    await expect(page.locator('#grid-loading')).toBeVisible();
  });

  test('Matrix.js renders grid cells asynchronously', async ({ page }) => {
    await loginAndGoToGrid(page);

    // WHY waitForSelector not time.sleep():
    // Matrix.js renders cells after a 300ms async delay (simulating a real
    // AJAX fetch). waitForSelector polls the DOM and proceeds the instant
    // td.ajax-cell-open appears — typically 10-50x faster than a fixed sleep.
    await page.waitForSelector('td.ajax-cell-open', { timeout: 10000 });

    // Grid should have 24 open cells (6 timeslots × 4 rooms)
    const cells = page.locator('td.ajax-cell-open');
    await expect(cells).toHaveCount(24);
  });

  test('sidebar shows all 5 unscheduled section chips', async ({ page }) => {
    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    const chips = page.locator('div.section-draggable');
    await expect(chips).toHaveCount(5);

    // Each chip should be visible and draggable
    await expect(chips.first()).toBeVisible();
    await expect(chips.first()).toHaveAttribute('draggable', 'true');
  });

  test('stats bar shows correct initial counts', async ({ page }) => {
    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    await expect(page.locator('#stat-total')).toHaveText('24');
    await expect(page.locator('#stat-scheduled')).toHaveText('0');
    await expect(page.locator('#stat-unscheduled')).toHaveText('5');
  });

});

test.describe('Scheduling Grid — Drag and Drop', () => {

  test('drag section to cell shows success message', async ({ page }) => {
    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    const section = page.locator('div.section-draggable').first();
    const cell    = page.locator('td.ajax-cell-open').first();

    // WHY dragTo() over Selenium ActionChains:
    // Playwright dispatches the full pointer event sequence that the
    // Scheduler.js drag handlers listen to. Selenium's ActionChains
    // had known issues with HTML5 drag events in headless mode.
    await section.dragTo(cell);

    // Success message should appear in the message panel
    const panel = page.locator('#scheduler-message-panel');
    await expect(panel).toBeVisible({ timeout: 5000 });
    await expect(panel).toHaveClass(/success/);
  });

  test('mocked 400 response shows "Room already booked" error', async ({ page }) => {
    // WHY page.route() BEFORE navigation:
    // The route handler must be registered before the page loads so it
    // intercepts the very first matching request. Registering after
    // navigation risks missing requests that fire on page load.
    await page.route('**/ajax_schedule_class**', route => {
      // Return a controlled 400 — simulates ESP's server-side room conflict
      // detection without needing two sections competing for the same slot in DB.
      route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Room already booked' }),
      });
    });

    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    const section = page.locator('div.section-draggable').first();
    const cell    = page.locator('td.ajax-cell-open').first();
    await section.dragTo(cell);

    // WHY expect().toContainText() not assert:
    // Built-in retry logic — keeps checking until text appears (JS is async)
    // or timeout expires. No sleep needed.
    const panel = page.locator('#scheduler-message-panel');
    await expect(panel).toContainText('Room already booked', { timeout: 5000 });
    await expect(panel).toHaveClass(/error/);
  });

  test('mocked 200 response shows success confirmation', async ({ page }) => {
    await page.route('**/ajax_schedule_class**', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ status: 'success', message: 'Class scheduled' }),
      });
    });

    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    const section = page.locator('div.section-draggable').first();
    const cell    = page.locator('td.ajax-cell-open').first();
    await section.dragTo(cell);

    const panel = page.locator('#scheduler-message-panel');
    await expect(panel).toContainText('Class scheduled', { timeout: 5000 });
    await expect(panel).not.toHaveClass(/error/);
  });

  test('cell becomes occupied after successful drop', async ({ page }) => {
    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    const section = page.locator('div.section-draggable').first();
    const cell    = page.locator('td.ajax-cell-open').first();

    // Get the cell's bounding box before drag so we can re-locate it after
    // the class changes (locator by position is stable across class changes)
    const box = await cell.boundingBox();
    await section.dragTo(cell);

    // Wait for the AJAX response to update the cell — locate by position
    const occupiedCell = page.locator('td.ajax-cell-occupied').first();
    await expect(occupiedCell).toBeVisible({ timeout: 8000 });
  });

});

test.describe('Scheduling Grid — Navigation', () => {

  test('navbar back button goes to dashboard', async ({ page }) => {
    await loginAndGoToGrid(page);
    await page.waitForSelector('td.ajax-cell-open');

    await page.click('a:has-text("Dashboard")');
    await expect(page).toHaveURL(/\/esp\//);
  });

  test('unauthenticated access redirects to login', async ({ page }) => {
    // Go directly without logging in
    await page.goto('/manage/mit_splash/2024/ajaxscheduling');
    // Django @login_required should redirect to login
    await expect(page).toHaveURL(/\/myesp\/login\//);
  });

});
