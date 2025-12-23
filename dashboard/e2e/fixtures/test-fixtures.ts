import { test as base, expect } from '@playwright/test';

/**
 * Extended test fixtures for Media Engine Dashboard E2E tests
 */
export const test = base.extend<{
  /**
   * Wait for the dashboard to be fully loaded
   */
  waitForDashboard: () => Promise<void>;
}>({
  waitForDashboard: async ({ page }, use) => {
    await use(async () => {
      // Wait for the main content area to be visible
      await page.waitForSelector('[data-testid="main-content"], main', { timeout: 10000 });
      // Wait for any loading spinners to disappear
      await page.waitForFunction(() => {
        const spinners = document.querySelectorAll('[class*="animate-spin"]');
        return spinners.length === 0;
      }, { timeout: 10000 }).catch(() => {
        // Ignore timeout - some pages may have persistent spinners
      });
    });
  },
});

export { expect };

/**
 * Common selectors used across tests
 */
export const selectors = {
  // Layout
  sidebar: '[data-testid="sidebar"], aside',
  header: 'header',
  mainContent: 'main',

  // Navigation
  navDashboard: 'a[href="/"]',
  navContent: 'a[href="/content"]',
  navQuality: 'a[href="/quality"]',
  navBuild: 'a[href="/build"]',
  navAiAssist: 'a[href="/ai-assist"]',

  // Dashboard
  healthScore: '[data-testid="health-score"]',
  statsCard: '[data-testid="stat-card"]',

  // Common UI
  spinner: '[class*="animate-spin"]',
  badge: '[class*="badge"]',
  button: 'button',
};

/**
 * Wait for API responses to complete
 */
export async function waitForApi(page: import('@playwright/test').Page) {
  await page.waitForLoadState('networkidle');
}
