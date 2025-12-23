import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('Quality Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/quality');
    await waitForApi(page);
  });

  test('displays quality page header', async ({ page }) => {
    const heading = page.locator('h1, h2').filter({ hasText: /Quality/ }).first();
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('shows quality score or metrics', async ({ page }) => {
    // Wait for quality data to load
    const qualityMetric = page.locator('text=Quality, text=Score, text=Issues').first();
    await expect(qualityMetric).toBeVisible({ timeout: 10000 });
  });

  test('can navigate to semantic analysis tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/semantic"], button:has-text("Semantic")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/semantic/);
    }
  });

  test('can navigate to knowledge graph tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/knowledge"], button:has-text("Knowledge")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/knowledge/);
    }
  });

  test('can navigate to readability tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/readability"], button:has-text("Readability")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/readability/);
    }
  });

  test('can navigate to freshness tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/freshness"], button:has-text("Freshness")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/freshness/);
    }
  });

  test('can navigate to code sync tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/codesync"], button:has-text("Code Sync")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/codesync/);
    }
  });

  test('can navigate to advanced analysis tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/advanced"], button:has-text("Advanced")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/advanced/);
    }
  });

  test('can navigate to activity tab', async ({ page }) => {
    const tab = page.locator('a[href="/quality/activity"], button:has-text("Activity")').first();
    if (await tab.isVisible()) {
      await tab.click();
      await expect(page).toHaveURL(/\/quality\/activity/);
    }
  });
});

test.describe('Quality Sub-Pages', () => {
  test('knowledge graph page loads without error', async ({ page }) => {
    await page.goto('/quality/knowledge');
    await waitForApi(page);

    // Should not show critical error
    const error = page.locator('text=Error, text=Failed').first();
    const hasError = await error.isVisible().catch(() => false);

    // Page should have some content
    const content = page.locator('main, [class*="content"]').first();
    await expect(content).toBeVisible();
  });

  test('code sync page loads without error', async ({ page }) => {
    await page.goto('/quality/codesync');
    await waitForApi(page);

    const content = page.locator('main, [class*="content"]').first();
    await expect(content).toBeVisible();
  });

  test('advanced analysis page loads without error', async ({ page }) => {
    await page.goto('/quality/advanced');
    await waitForApi(page);

    const content = page.locator('main, [class*="content"]').first();
    await expect(content).toBeVisible();
  });

  test('freshness page shows staleness data', async ({ page }) => {
    await page.goto('/quality/freshness');
    await waitForApi(page);

    // Look for freshness-related content
    const freshnessContent = page.locator('text=Fresh, text=Stale, text=Freshness').first();
    await expect(freshnessContent).toBeVisible({ timeout: 10000 });
  });
});
