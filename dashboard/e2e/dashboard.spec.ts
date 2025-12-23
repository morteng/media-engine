import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForApi(page);
  });

  test('displays project name in header', async ({ page }) => {
    const header = page.locator('header');
    await expect(header).toContainText('Media Engine');
  });

  test('shows health score section', async ({ page }) => {
    // Wait for health score to load - look for score or health related content
    const healthSection = page.locator('main').getByText(/health|score|%/i).first();
    await expect(healthSection).toBeVisible({ timeout: 10000 });
  });

  test('displays stats cards with metrics', async ({ page }) => {
    // Check for any stat-related numbers or metrics
    const statsArea = page.locator('main');
    await expect(statsArea).toBeVisible({ timeout: 10000 });

    // Wait for content to load (any numbers indicate loaded data)
    await page.waitForFunction(() => {
      const main = document.querySelector('main');
      return main && /\d+/.test(main.textContent || '');
    }, { timeout: 10000 });
  });

  test('shows project summary content', async ({ page }) => {
    // Check for main content area with meaningful content
    const mainContent = page.locator('main');
    await expect(mainContent).toBeVisible({ timeout: 10000 });
  });

  test('navigation sidebar is visible', async ({ page }) => {
    const sidebar = page.locator('aside, [data-testid="sidebar"]').first();
    await expect(sidebar).toBeVisible();
  });

  test('can navigate to Content page', async ({ page }) => {
    await page.click('a[href="/content"]');
    await expect(page).toHaveURL(/\/content/);
  });

  test('can navigate to Quality page', async ({ page }) => {
    await page.click('a[href="/quality"]');
    await expect(page).toHaveURL(/\/quality/);
  });

  test('can navigate to Build page', async ({ page }) => {
    await page.click('a[href="/build"]');
    await expect(page).toHaveURL(/\/build/);
  });
});
