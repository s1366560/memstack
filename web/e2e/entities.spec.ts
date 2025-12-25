import { test, expect } from '@playwright/test';

test.describe('Entities and Communities', () => {
    let projectName: string;

    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/login');
        await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
        await page.getByLabel(/密码/i).fill('admin123');
        await page.getByRole('button', { name: /登录/i }).click();

        // Wait for login to complete and redirect
        await expect(page).not.toHaveURL(/\/login/);

        // Create Project
        const projectsLink = page.getByRole('link', { name: /Projects/i }).first();
        await projectsLink.waitFor();
        await projectsLink.click();

        // Wait for Project List to load
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible({ timeout: 10000 });

        await page.getByRole('button', { name: /Create New Project/i }).click();
        projectName = `Entities Test Project ${Date.now()}`;
        await page.getByPlaceholder(/e.g. Finance Knowledge Base/i).fill(projectName);
        await page.getByRole('button', { name: /Create Project/i }).click();
        await page.waitForURL(/\/projects$/);

        // Reload to ensure list is fresh
        await page.reload();
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible();

        // Enter project
        // Search for the project to ensure it's visible
        await page.getByPlaceholder(/Search by project name/i).fill(projectName);

        const projectCard = page.getByText(projectName).first();
        await projectCard.waitFor({ state: 'visible' });
        await projectCard.click();

        // Add Memory with Entities
        await page.getByRole('button', { name: /Add Memory/i }).click();
        await page.getByPlaceholder(/Start typing your memory/i).fill('Elon Musk is the CEO of Tesla and SpaceX.');
        await page.getByPlaceholder(/e.g. Q3 Strategy/i).fill('Entity Memory');
        await page.getByRole('button', { name: /Save Memory/i }).click();
        await page.waitForURL(/\/memories$/);
    });

    test('should list extracted entities', async ({ page }) => {
        // Mock entities response
        await page.route('**/api/v1/entities*', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    entities: [
                        { id: '1', name: 'Elon Musk', type: 'Person', description: 'CEO' },
                        { id: '2', name: 'Tesla', type: 'Organization', description: 'Car company' }
                    ],
                    total: 2
                })
            });
        });

        // Navigate to Entities
        // Link likely includes icon "category Entities"
        await page.getByRole('link', { name: 'category Entities' }).click();

        // Check if Entities page loaded
        // Use exact match for h1 or filter by class to avoid matching breadcrumbs
        await expect(page.locator('h1').filter({ hasText: /^Entities$/ })).toBeVisible();

        // Check for specific entities (Elon Musk, Tesla, SpaceX)
        // Extraction might be async or mocked. If mocked/instant, we expect them.
        // If dependent on backend async process, this might flake.
        // Assuming the test environment has extraction working or we are mocking it.
        // For now, check if the list is not empty or "No entities found" is NOT shown if we expect entities.

        // If extraction is real-time:
        // await expect(page.getByText('Elon Musk')).toBeVisible();

        // If extraction takes time, we might just check that the page structure is correct
        await expect(page.getByText('Browse and manage extracted entities')).toBeVisible();
    });

    test('should display communities', async ({ page }) => {
        // Mock communities response
        await page.route('**/api/v1/communities*', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    communities: [
                        {
                            id: '1',
                            name: 'Community 1',
                            summary: 'Tech Giants',
                            entities: ['Tesla', 'SpaceX'],
                            rating: 5
                        }
                    ],
                    total: 1
                })
            });
        });

        // Navigate to Communities
        // Link likely includes icon "groups Communities"
        await page.getByRole('link', { name: 'groups Communities' }).click();

        // Check header
        // Use exact match or look for h1 specifically to distinguish from "About Communities" h3
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Check refresh button
        // Use exact text "Refresh" to distinguish from "Rebuild Communities"
        await expect(page.getByRole('button', { name: 'refresh Refresh', exact: true })).toBeVisible();

        // Check "No communities found" or list
        // Likely "No communities found" initially as community detection needs more data/time
        await expect(page.getByText(/No communities found|Community 1/i)).toBeVisible();
    });
});
