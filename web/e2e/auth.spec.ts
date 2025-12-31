import { test, expect } from './base';

test.describe('Authentication', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Check if we are on the login page
    await expect(page).toHaveURL(/\/login/);

    // Wait for form to be ready
    await expect(page.getByLabel(/邮箱地址/i)).toBeVisible();
    await expect(page.getByLabel(/密码/i)).toBeVisible();

    // Fill in credentials
    await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
    await page.getByLabel(/密码/i).fill('adminpassword');

    // Click login button
    await page.getByRole('button', { name: /登录/i }).click();

    // Wait for navigation - login should redirect away from /login
    // Increase timeout to allow for API call and navigation
    await page.waitForURL((url) => {
      return !url.pathname.includes('/login');
    }, { timeout: 10000 });

    // Verify we are no longer on login page
    await expect(page).not.toHaveURL(/\/login/);
  });
});
