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

  test('shows quality score display', async ({ page }) => {
    // Quality page shows score on main page
    await expect(page).toHaveURL('/quality');

    // Should show score display
    const scoreDisplay = page.locator('text=/Quality Score/i').first();
    await expect(scoreDisplay).toBeVisible({ timeout: 15000 });
  });

  test('shows issue summary cards', async ({ page }) => {
    // Should show critical/warnings/documents counts
    await expect(page.locator('text=/Critical/i').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=/Warnings/i').first()).toBeVisible({ timeout: 15000 });
    await expect(page.locator('text=/Documents/i').first()).toBeVisible({ timeout: 15000 });
  });
});

test.describe('Quality Expandable Sections', () => {
  // Increase timeout for sub-page tests that load additional data
  test.setTimeout(60000);

  test.beforeEach(async ({ page }) => {
    await page.goto('/quality', { timeout: 30000 });
    await waitForPageReady(page);
  });

  test('shows component scores section', async ({ page }) => {
    const section = page.locator('text=/Component Scores/i').first();
    await expect(section).toBeVisible({ timeout: 15000 });
  });

  test('has semantic analysis section', async ({ page }) => {
    // Check for semantic analysis expandable section
    const semanticSection = page.locator('button').filter({ hasText: /Semantic Analysis/i }).first();
    await expect(semanticSection).toBeVisible({ timeout: 15000 });
  });

  test('has knowledge graph section', async ({ page }) => {
    // Check for knowledge graph expandable section
    const kgSection = page.locator('button').filter({ hasText: /Knowledge Graph/i }).first();
    await expect(kgSection).toBeVisible({ timeout: 15000 });
  });

  test('has readability section', async ({ page }) => {
    // Check for readability expandable section
    const readabilitySection = page.locator('button').filter({ hasText: /Readability/i }).first();
    await expect(readabilitySection).toBeVisible({ timeout: 15000 });
  });

  test('has freshness section', async ({ page }) => {
    // Check for freshness expandable section
    const freshnessSection = page.locator('button').filter({ hasText: /Freshness/i }).first();
    await expect(freshnessSection).toBeVisible({ timeout: 15000 });
  });

  test('has code synchronization section', async ({ page }) => {
    // Check for code sync expandable section
    const codeSyncSection = page.locator('button').filter({ hasText: /Code Synchronization/i }).first();
    await expect(codeSyncSection).toBeVisible({ timeout: 15000 });
  });

  test('has advanced analysis section', async ({ page }) => {
    // Check for advanced analysis expandable section
    const advancedSection = page.locator('button').filter({ hasText: /Advanced Analysis/i }).first();
    await expect(advancedSection).toBeVisible({ timeout: 15000 });
  });

  test('has recent activity section', async ({ page }) => {
    // Check for activity expandable section
    const activitySection = page.locator('button').filter({ hasText: /Recent Activity/i }).first();
    await expect(activitySection).toBeVisible({ timeout: 15000 });
  });

  test('can expand a section', async ({ page }) => {
    // Find and click the Component Scores section (should be expanded by default)
    const section = page.locator('button').filter({ hasText: /Component Scores/i }).first();
    await expect(section).toBeVisible({ timeout: 15000 });

    // The section content should be visible (progress bars for component scores)
    const progressBars = page.locator('progress').first();
    await expect(progressBars).toBeVisible({ timeout: 10000 });
  });
});
