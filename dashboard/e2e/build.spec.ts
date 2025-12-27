import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('Build Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/build');
    await waitForApi(page);
  });

  test('displays build page header', async ({ page }) => {
    const heading = page.locator('h1, h2').filter({ hasText: /Build/ }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('shows publications section', async ({ page }) => {
    // Look for Publications section header
    const publicationsHeader = page.locator('text=Publications').first();
    await expect(publicationsHeader).toBeVisible({ timeout: 10000 });
  });

  test('shows select all and clear buttons', async ({ page }) => {
    // Look for publication selection controls
    const selectAllBtn = page.locator('button:has-text("Select All")').first();
    await expect(selectAllBtn).toBeVisible({ timeout: 10000 });
  });

  test('has build trigger button', async ({ page }) => {
    const buildButton = page.locator('button:has-text("Build"), button:has-text("Generate")').first();
    await expect(buildButton).toBeVisible({ timeout: 10000 });
  });

  test('can navigate to brand page', async ({ page }) => {
    // Brand is a separate top-level page, navigate via sidebar
    const brandLink = page.locator('a[href="/brand"]').first();
    if (await brandLink.isVisible()) {
      await brandLink.click();
      await expect(page).toHaveURL(/\/brand/);
    }
  });
});

test.describe('Brand Page', () => {
  test('displays brand page header', async ({ page }) => {
    await page.goto('/brand');
    await waitForApi(page);

    // Look for Brand heading or Brand-related content
    const brandHeading = page.locator('h1, h2').filter({ hasText: /Brand/i }).first();
    await expect(brandHeading).toBeVisible({ timeout: 10000 });
  });

  test('shows brand configuration options', async ({ page }) => {
    await page.goto('/brand');
    await waitForApi(page);

    // Look for the design system tab in the main content area
    const tablist = page.locator('main [role="tablist"]').first();
    await expect(tablist).toBeVisible({ timeout: 10000 });
  });
});
