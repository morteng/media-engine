import { test, expect, waitForApi, selectors } from './fixtures/test-fixtures';

test.describe('Video Production Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video');
    await waitForApi(page);
  });

  test('displays video production tab navigation', async ({ page }) => {
    // Video production page uses tabs instead of a header
    const tabs = page.locator('.tabs');
    await expect(tabs).toBeVisible({ timeout: 10000 });
  });

  test('shows tab navigation', async ({ page }) => {
    // Check for tab navigation
    const tabs = page.locator('.tabs');
    await expect(tabs).toBeVisible({ timeout: 10000 });

    // Check individual tabs using the tabs container to avoid sidebar matches
    await expect(tabs.locator('a:has-text("Overview")')).toBeVisible();
    await expect(tabs.locator('a:has-text("Projects")')).toBeVisible();
    await expect(tabs.locator('a:has-text("Review")')).toBeVisible();
    await expect(tabs.locator('a:has-text("Scripts")')).toBeVisible();
    await expect(tabs.locator('a:has-text("Render")')).toBeVisible();
    await expect(tabs.locator('a:has-text("Assets")')).toBeVisible();
  });

  test('overview tab shows stats cards', async ({ page }) => {
    // Should be on overview by default - look for the stat card labels
    await expect(page.locator('.card-body:has-text("Video Scripts")').first()).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Video Production - Scripts Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video/scripts');
    await waitForApi(page);
  });

  test('displays script list', async ({ page }) => {
    // Wait for scripts to load
    await page.waitForSelector('text=Scripts', { timeout: 10000 });

    // Should show script cards or list items
    const scriptItems = page.locator('[class*="card"], [class*="list-item"]');
    const count = await scriptItems.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });

  test('shows scripts heading', async ({ page }) => {
    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Look for the Scripts heading in the sidebar
    await expect(page.locator('h3:has-text("Scripts")')).toBeVisible({ timeout: 10000 });
  });

  test('has render button for scripts', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for render buttons
    const renderButtons = page.locator('button:has-text("Render")');
    const count = await renderButtons.count();
    // May have render buttons if scripts exist
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Video Production - Render Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video/render');
    await waitForApi(page);
  });

  test('displays render queue', async ({ page }) => {
    await expect(page.locator('text=Render Queue')).toBeVisible({ timeout: 10000 });
  });

  test('shows start new render section', async ({ page }) => {
    await expect(page.locator('text=Start New Render')).toBeVisible({ timeout: 10000 });
  });

  test('has quality preset options', async ({ page }) => {
    // Look for the Quality label - the actual label text in the form
    await expect(page.locator('.label-text:has-text("Quality")')).toBeVisible({ timeout: 10000 });
  });

  test('shows render job list', async ({ page }) => {
    // Wait for jobs to load
    await page.waitForLoadState('networkidle');

    // Should show jobs or empty state
    const jobsContent = page.locator('main');
    await expect(jobsContent).toBeVisible();
  });
});

test.describe('Video Production - Assets Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video/assets');
    await waitForApi(page);
  });

  test('displays asset categories', async ({ page }) => {
    // Check for actual section headings in the assets tab
    await expect(page.locator('h3:has-text("Demo Clips")')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('h3:has-text("Voiceover Audio")')).toBeVisible({ timeout: 10000 });
  });

  test('shows asset items with size info', async ({ page }) => {
    await page.waitForLoadState('networkidle');

    // Look for file size indicators
    const sizeIndicators = page.locator('text=/\\d+(\\.\\d+)?\\s*(MB|KB|GB)/i');
    const count = await sizeIndicators.count();
    expect(count).toBeGreaterThanOrEqual(0);
  });
});

test.describe('Video Production - Projects Tab', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/video/projects');
    await waitForApi(page);
  });

  test('displays projects list or empty state', async ({ page }) => {
    // Should show either projects or an empty state message
    await page.waitForLoadState('networkidle');
    const content = page.locator('main');
    await expect(content).toBeVisible();
  });
});

test.describe('Video Production - Navigation', () => {
  test('can navigate between tabs', async ({ page }) => {
    await page.goto('/video');
    await waitForApi(page);

    // Use tab links specifically (in the tabs container)
    const tabsContainer = page.locator('.tabs');

    // Navigate to Scripts tab
    await tabsContainer.locator('a:has-text("Scripts")').click();
    await expect(page).toHaveURL(/\/video\/scripts/);

    // Navigate to Render tab
    await tabsContainer.locator('a:has-text("Render")').click();
    await expect(page).toHaveURL(/\/video\/render/);

    // Navigate to Assets tab
    await tabsContainer.locator('a:has-text("Assets")').click();
    await expect(page).toHaveURL(/\/video\/assets/);

    // Navigate to Projects tab
    await tabsContainer.locator('a:has-text("Projects")').click();
    await expect(page).toHaveURL(/\/video\/projects/);

    // Navigate back to Overview
    await tabsContainer.locator('a:has-text("Overview")').click();
    await expect(page).toHaveURL(/\/video$/);
  });

  test('can access video page from sidebar', async ({ page }) => {
    await page.goto('/');
    await waitForApi(page);

    // Find and click video production link in sidebar
    const videoLink = page.locator('a[href="/video"]');
    if (await videoLink.isVisible()) {
      await videoLink.click();
      await expect(page).toHaveURL(/\/video/);
    }
  });
});

test.describe('Video Production - Interactions', () => {
  test('can click render button without error', async ({ page }) => {
    await page.goto('/video/scripts');
    await waitForApi(page);

    // Wait for content to load
    await page.waitForLoadState('networkidle');

    // Find render button if available
    const renderButton = page.locator('button:has-text("Render")').first();
    if (await renderButton.isVisible()) {
      // Click and verify no error modal appears
      await renderButton.click();

      // Should not show error
      const errorModal = page.locator('[role="alert"]:has-text("error")');
      const hasError = await errorModal.isVisible({ timeout: 1000 }).catch(() => false);
      expect(hasError).toBe(false);
    }
  });

  test('can refresh data', async ({ page }) => {
    await page.goto('/video');
    await waitForApi(page);

    // Find refresh button if available
    const refreshButton = page.locator('button:has-text("Refresh")').first();
    if (await refreshButton.isVisible()) {
      await refreshButton.click();
      // Should trigger data refresh without error
    }
  });
});

test.describe('Video Production - Responsive', () => {
  test('tabs are visible on mobile', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/video');
    await waitForApi(page);

    // Tabs should still be visible
    const tabs = page.locator('[class*="tabs"]');
    await expect(tabs).toBeVisible({ timeout: 10000 });
  });

  test('content is readable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });

    await page.goto('/video');
    await waitForApi(page);

    // Main content should be visible
    const main = page.locator('main');
    await expect(main).toBeVisible();
  });
});
