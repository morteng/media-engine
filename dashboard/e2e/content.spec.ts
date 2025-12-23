import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('Content Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/content');
    await waitForApi(page);
  });

  test('displays content page header', async ({ page }) => {
    const heading = page.locator('h1, h2').filter({ hasText: /Content|Documents/ }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('shows language selector', async ({ page }) => {
    // Look for language tabs or selector
    const langSelector = page.locator('text=EN, text=NO, text=English, text=Norwegian').first();
    await expect(langSelector).toBeVisible({ timeout: 10000 });
  });

  test('displays document tree', async ({ page }) => {
    // Wait for document list to load
    const docList = page.locator('[class*="tree"], [class*="list"], ul').first();
    await expect(docList).toBeVisible({ timeout: 10000 });
  });

  test('can switch to translations tab', async ({ page }) => {
    const translationsTab = page.locator('a[href="/content/translations"], button:has-text("Translations")').first();
    if (await translationsTab.isVisible()) {
      await translationsTab.click();
      await expect(page).toHaveURL(/\/content\/translations/);
    }
  });

  test('can switch to video tab', async ({ page }) => {
    const videoTab = page.locator('a[href="/content/video"], button:has-text("Video")').first();
    if (await videoTab.isVisible()) {
      await videoTab.click();
      await expect(page).toHaveURL(/\/content\/video/);
    }
  });

  test('can switch to media tab', async ({ page }) => {
    const mediaTab = page.locator('a[href="/content/media"], button:has-text("Media")').first();
    if (await mediaTab.isVisible()) {
      await mediaTab.click();
      await expect(page).toHaveURL(/\/content\/media/);
    }
  });
});
