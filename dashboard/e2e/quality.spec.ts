import { test, expect } from './fixtures/test-fixtures';

// Helper to wait for page load without networkidle (which can timeout with WebSocket)
async function waitForPageReady(page: import('@playwright/test').Page) {
  await page.waitForLoadState('domcontentloaded');
  // Wait for loading spinners to disappear
  await page.waitForFunction(() => {
    const spinners = document.querySelectorAll('.loading, [class*="animate-spin"]');
    return spinners.length === 0;
  }, { timeout: 15000 }).catch(() => {
    // Some pages may have persistent loading states
  });
}

test.describe('Quality Page', () => {
  // Increase timeout for slower page loads
  test.setTimeout(45000);

  test.beforeEach(async ({ page }) => {
    await page.goto('/quality', { timeout: 30000 });
    await waitForPageReady(page);
  });

  test('displays quality page header', async ({ page }) => {
    const heading = page.locator('h1').filter({ hasText: /Quality/i });
    await expect(heading).toBeVisible({ timeout: 10000 });
  });

  test('shows quality score or metrics', async ({ page }) => {
    // Wait for quality data to load - look for score display or issue counts
    const qualityContent = page.locator('[class*="card"]').filter({
      has: page.locator('text=/Quality Score|Critical|Warnings|Documents/')
    }).first();
    await expect(qualityContent).toBeVisible({ timeout: 15000 });
  });

  test('shows overview tab by default', async ({ page }) => {
    // Quality page loads to overview by default
    await expect(page).toHaveURL('/quality');

    // Should show score display
    const scoreDisplay = page.locator('text=/Quality Score/i').first();
    await expect(scoreDisplay).toBeVisible({ timeout: 15000 });
  });

  test('can navigate to analysis tab', async ({ page }) => {
    const tab = page.getByRole('tab', { name: /Analysis/i });
    await expect(tab).toBeVisible({ timeout: 15000 });
    await tab.click();
    await expect(page).toHaveURL(/\/quality\/analysis/);
  });

  test('can navigate to activity tab', async ({ page }) => {
    const tab = page.getByRole('tab', { name: /Activity/i });
    await expect(tab).toBeVisible({ timeout: 15000 });
    await tab.click();
    await expect(page).toHaveURL(/\/quality\/activity/);
  });
});

test.describe('Quality Sub-Pages', () => {
  // Increase timeout for sub-page tests that load additional data
  test.setTimeout(60000);

  test('overview page shows quality score', async ({ page }) => {
    await page.goto('/quality');
    await waitForPageReady(page);

    // Page header should be visible
    await expect(page.locator('h1')).toBeVisible({ timeout: 15000 });

    // Should show quality score
    const hasContent = await page.locator('text=/Quality Score|Critical|Warnings|Documents/i').first().isVisible({ timeout: 20000 }).catch(() => false);
    expect(hasContent).toBe(true);
  });

  test('analysis page loads with expandable sections', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Wait for navigation to complete and URL to be correct
    await expect(page).toHaveURL(/\/quality\/analysis/);

    // Wait for DOM to be ready
    await page.waitForLoadState('domcontentloaded');

    // Should show expandable sections for analysis types
    const hasContent = await page.locator('text=/Semantic Analysis|Knowledge Graph|Readability|Freshness|Code Sync|Advanced Analysis/i').first().isVisible({ timeout: 20000 }).catch(() => false);
    expect(hasContent).toBe(true);
  });

  test('analysis page has semantic analysis section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for semantic analysis expandable section
    const semanticSection = page.locator('text=/Semantic Analysis/i').first();
    await expect(semanticSection).toBeVisible({ timeout: 15000 });
  });

  test('analysis page has knowledge graph section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for knowledge graph expandable section
    const kgSection = page.locator('text=/Knowledge Graph/i').first();
    await expect(kgSection).toBeVisible({ timeout: 15000 });
  });

  test('analysis page has readability section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for readability expandable section
    const readabilitySection = page.locator('text=/Readability/i').first();
    await expect(readabilitySection).toBeVisible({ timeout: 15000 });
  });

  test('analysis page has freshness section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for freshness expandable section
    const freshnessSection = page.locator('text=/Freshness.*Staleness/i').first();
    await expect(freshnessSection).toBeVisible({ timeout: 15000 });
  });

  test('analysis page has code sync section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for code sync expandable section
    const codeSyncSection = page.locator('text=/Code Sync/i').first();
    await expect(codeSyncSection).toBeVisible({ timeout: 15000 });
  });

  test('analysis page has advanced analysis section', async ({ page }) => {
    await page.goto('/quality/analysis');
    await waitForPageReady(page);

    // Check for advanced analysis expandable section
    const advancedSection = page.locator('text=/Advanced Analysis/i').first();
    await expect(advancedSection).toBeVisible({ timeout: 15000 });
  });

  test('activity page shows audit log or commits', async ({ page }) => {
    await page.goto('/quality/activity');
    await waitForPageReady(page);

    await expect(page.locator('h1')).toBeVisible({ timeout: 15000 });

    // Should show activity content
    const hasContent = await page.locator('text=/Recent Commits|Audit Log|No recent/i').first().isVisible({ timeout: 20000 }).catch(() => false);
    expect(hasContent).toBe(true);
  });
});
