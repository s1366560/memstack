import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('should login successfully with valid credentials', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login');

    // Check if we are on the login page
    await expect(page).toHaveURL(/\/login/);
    
    // Fill in credentials
    await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
    await page.getByLabel(/密码/i).fill('admin123');
    
    // Click login button
    await page.getByRole('button', { name: /登录/i }).click();

    // Verify redirection to dashboard (assuming it goes to root or dashboard)
    // Adjust this expectation based on actual redirect
    await expect(page).not.toHaveURL(/\/login/);
  });
});
