// playwright-tests/auth.spec.js
// GSoC Proposal: Authentication smoke tests.
// Mirrors tests/e2e/test_auth_smoke.py — shown in the HTML dashboard
// with the chromium/firefox/webkit browser badges.

const { test, expect } = require('@playwright/test');

test.describe('Authentication Flow', () => {

  test('login page renders correctly', async ({ page }) => {
    await page.goto('/myesp/login/');

    // ESP logo and title visible
    await expect(page.locator('.logo-box')).toBeVisible();
    await expect(page.locator('h1')).toContainText('Educational Studies Program');

    // Form fields present
    await expect(page.locator('input[name="username"]')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('valid login redirects to dashboard', async ({ page }) => {
    await page.goto('/myesp/login/');

    // WHY fill() not type(): fill() clears the field first and dispatches
    // proper input events — reliable across all browsers in headless mode.
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');

    // WHY waitForURL not time.sleep(): Playwright polls until URL matches
    // or timeout expires — zero flakiness from race conditions.
    await page.waitForURL('**/esp/');
    await expect(page).toHaveURL(/\/esp\//);
  });

  test('invalid credentials stay on login page with error', async ({ page }) => {
    await page.goto('/myesp/login/');
    await page.fill('input[name="username"]', 'wronguser');
    await page.fill('input[name="password"]', 'wrongpass');
    await page.click('button[type="submit"]');

    // Should NOT redirect
    await expect(page).toHaveURL(/\/myesp\/login\//);

    // Error message must appear
    await expect(page.locator('.errorlist').first()).toBeVisible();
  });

  test('logout redirects to login page', async ({ page }) => {
    // Login first
    await page.goto('/myesp/login/');
    await page.fill('input[name="username"]', 'admin');
    await page.fill('input[name="password"]', 'admin123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/esp/');

    // Then logout
    await page.goto('/myesp/logout/');
    await expect(page).toHaveURL(/\/myesp\/login\//);
  });

});
