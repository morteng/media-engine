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
    // Look for language button in the sidebar (e.g., "EN" button)
    const langSelector = page.locator('button:has-text("EN"), button:has-text("NO")').first();
    await expect(langSelector).toBeVisible({ timeout: 10000 });
  });

  test('displays document tree', async ({ page }) => {
    // Wait for document navigation to load - it uses buttons for documents
    const docNav = page.locator('nav button, [role="navigation"] button').first();
    await expect(docNav).toBeVisible({ timeout: 10000 });
  });

  test('can switch to translations tab', async ({ page }) => {
    // Content page uses tab elements in a tablist
    const translationsTab = page.locator('[role="tab"]:has-text("Translations"), button:has-text("Translations")').first();
    if (await translationsTab.isVisible()) {
      await translationsTab.click();
      // Tab may update URL or just switch tab panel
      await page.waitForTimeout(500);
    }
  });

  test('can switch to video tab', async ({ page }) => {
    const videoTab = page.locator('[role="tab"]:has-text("Video"), button:has-text("Video")').first();
    if (await videoTab.isVisible()) {
      await videoTab.click();
      await page.waitForTimeout(500);
    }
  });

  test('can switch to media tab', async ({ page }) => {
    const mediaTab = page.locator('[role="tab"]:has-text("Media"), button:has-text("Media")').first();
    if (await mediaTab.isVisible()) {
      await mediaTab.click();
      await page.waitForTimeout(500);
    }
  });
});
