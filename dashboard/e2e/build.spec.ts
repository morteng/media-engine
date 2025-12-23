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

  test('shows format selection options', async ({ page }) => {
    // Look for format options like HTML, PPTX, XLSX
    const formatOption = page.locator('text=HTML, text=PPTX, text=PowerPoint, text=Excel').first();
    await expect(formatOption).toBeVisible({ timeout: 10000 });
  });

  test('shows language selection', async ({ page }) => {
    // Look for language selection
    const langOption = page.locator('text=English, text=Norwegian, text=EN, text=NO').first();
    await expect(langOption).toBeVisible({ timeout: 10000 });
  });

  test('has build trigger button', async ({ page }) => {
    const buildButton = page.locator('button:has-text("Build"), button:has-text("Generate")').first();
    await expect(buildButton).toBeVisible({ timeout: 10000 });
  });

  test('can navigate to brand tab', async ({ page }) => {
    const brandTab = page.locator('a[href="/build/brand"], button:has-text("Brand")').first();
    if (await brandTab.isVisible()) {
      await brandTab.click();
      await expect(page).toHaveURL(/\/build\/brand/);
    }
  });
});

test.describe('Brand Page', () => {
  test('displays brand configuration', async ({ page }) => {
    await page.goto('/build/brand');
    await waitForApi(page);

    // Look for brand-related content
    const brandContent = page.locator('text=Brand, text=Colors, text=Typography').first();
    await expect(brandContent).toBeVisible({ timeout: 10000 });
  });

  test('shows color palette', async ({ page }) => {
    await page.goto('/build/brand');
    await waitForApi(page);

    // Look for color-related content
    const colorContent = page.locator('text=Primary, text=Secondary, text=Accent, text=Color').first();
    await expect(colorContent).toBeVisible({ timeout: 10000 });
  });
});
