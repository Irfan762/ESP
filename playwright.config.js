// playwright.config.js
// GSoC Proposal: Official Playwright test runner config.
// This produces the dark-themed HTML dashboard with traces, browser badges,
// and "View Trace" links — exactly what mentors expect to see.

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Test directory
  testDir: './playwright-tests',

  // Run all tests in parallel
  fullyParallel: true,

  // Fail the build on CI if test.only is accidentally left in
  forbidOnly: !!process.env.CI,

  // Retry failed tests once on CI
  retries: process.env.CI ? 1 : 0,

  // Reporter — this generates the official dark HTML dashboard
  reporter: [
    ['html', { outputFolder: 'playwright-html-report', open: 'never' }],
    ['list'],   // also print to terminal
  ],

  // Global settings for all tests
  use: {
    // Django dev server base URL
    baseURL: 'http://127.0.0.1:8000',

    // Capture trace on first retry — viewable in the HTML dashboard
    trace: 'on-first-retry',

    // Screenshot on failure
    screenshot: 'only-on-failure',

    // Video on failure
    video: 'retain-on-failure',

    // Headless by default; set HEADED=1 env var to watch
    headless: !process.env.HEADED,
  },

  // Run against Chromium, Firefox, and WebKit — shows browser badges in report
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
});
