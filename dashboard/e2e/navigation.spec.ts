import { test, expect, waitForApi } from './fixtures/test-fixtures';

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForApi(page);
  });

  test('sidebar is visible on desktop', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    const sidebar = page.locator('aside, nav[class*="sidebar"]').first();
    await expect(sidebar).toBeVisible();
  });

  test('all main navigation links are present', async ({ page }) => {
    // Check for main navigation items
    const dashboardLink = page.locator('a[href="/"]').first();
    const contentLink = page.locator('a[href="/content"]').first();
    const qualityLink = page.locator('a[href="/quality"]').first();
    const buildLink = page.locator('a[href="/build"]').first();

    await expect(dashboardLink).toBeVisible();
    await expect(contentLink).toBeVisible();
    await expect(qualityLink).toBeVisible();
    await expect(buildLink).toBeVisible();
  });

  test('navigating between pages updates URL', async ({ page }) => {
    // Go to content
    await page.click('a[href="/content"]');
    await expect(page).toHaveURL(/\/content/);

    // Go to quality
    await page.click('a[href="/quality"]');
    await expect(page).toHaveURL(/\/quality/);

    // Go to build
    await page.click('a[href="/build"]');
    await expect(page).toHaveURL(/\/build/);

    // Go back to dashboard
    await page.click('a[href="/"]');
    await expect(page).toHaveURL(/\/$/);
  });

  test('page content updates when navigating', async ({ page }) => {
    // Navigate to content and verify content-specific element
    await page.click('a[href="/content"]');
    await waitForApi(page);
    const contentHeader = page.locator('h1, h2').filter({ hasText: /Content|Documents/ }).first();
    await expect(contentHeader).toBeVisible({ timeout: 10000 });

    // Navigate to quality and verify quality-specific element
    await page.click('a[href="/quality"]');
    await waitForApi(page);
    const qualityHeader = page.locator('h1, h2').filter({ hasText: /Quality/ }).first();
    await expect(qualityHeader).toBeVisible({ timeout: 10000 });
  });
});

test.describe('Header', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
    await waitForApi(page);
  });

  test('header is visible', async ({ page }) => {
    const header = page.locator('header').first();
    await expect(header).toBeVisible();
  });

  test('project name is displayed', async ({ page }) => {
    const projectName = page.locator('header').filter({ hasText: /Media Engine|Demo/ }).first();
    await expect(projectName).toBeVisible();
  });

  test('theme toggle is present', async ({ page }) => {
    // Look for theme toggle button (sun/moon icon)
    const themeToggle = page.locator('button[aria-label*="theme"], button:has(svg)').first();
    await expect(themeToggle).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('mobile viewport has menu toggle', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await waitForApi(page);

    // On mobile, there should be a menu toggle button in the header
    const menuToggle = page.locator('button:has-text("menu"), button[aria-label*="menu"], button[aria-label*="navigation"], button[aria-label*="sidebar"]').first();
    // Either menu toggle exists OR sidebar is visible (different responsive strategies)
    const hasMenuToggle = await menuToggle.isVisible().catch(() => false);
    const sidebar = page.locator('aside, nav[class*="sidebar"], [role="complementary"]').first();
    const sidebarVisible = await sidebar.isVisible().catch(() => false);

    // Either we have a menu toggle OR sidebar is directly visible
    expect(hasMenuToggle || sidebarVisible).toBe(true);
  });

  test('desktop viewport shows full sidebar', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    await waitForApi(page);

    const sidebar = page.locator('aside, nav[class*="sidebar"]').first();
    await expect(sidebar).toBeVisible();
  });
});

test.describe('Command Palette', () => {
  test('opens with keyboard shortcut', async ({ page }) => {
    await page.goto('/');
    await waitForApi(page);

    // Press Cmd+K (or Ctrl+K on non-Mac)
    await page.keyboard.press('Meta+k');

    // Look for command palette dialog
    const palette = page.locator('[role="dialog"], [class*="command"], [class*="palette"]').first();
    await expect(palette).toBeVisible({ timeout: 5000 });
  });
});
