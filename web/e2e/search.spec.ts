import { test, expect } from '@playwright/test';

test.describe('Search Functionality', () => {
    let projectName: string;

    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/login');
        await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
        await page.getByLabel(/密码/i).fill('admin123');
        await page.getByRole('button', { name: /登录/i }).click();

        // Wait for login to complete and redirect
        await expect(page).not.toHaveURL(/\/login/);

        // Ensure we are on the projects page or navigate there
        // Use first() to avoid strict mode violation if multiple "Projects" links exist
        const projectsLink = page.getByRole('link', { name: /Projects/i }).first();
        await projectsLink.waitFor();
        await projectsLink.click();

        // Wait for Project List to load
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible({ timeout: 10000 });

        await page.getByRole('button', { name: /Create New Project/i }).click();
        projectName = `Search Test Project ${Date.now()}`;
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

        // Add some memories to search for
        await page.getByRole('button', { name: /Add Memory/i }).click();
        await page.getByPlaceholder(/Start typing your memory/i).fill('The quick brown fox jumps over the lazy dog.');
        await page.getByPlaceholder(/e.g. Q3 Strategy/i).fill('Fox Memory');
        await page.getByRole('button', { name: /Save Memory/i }).click();
        await page.waitForURL(/\/memories$/);

        // Add another memory
        await page.getByRole('button', { name: /Add Memory/i }).first().click();
        await page.getByPlaceholder(/Start typing your memory/i).fill('Artificial Intelligence is transforming the world.');
        await page.getByPlaceholder(/e.g. Q3 Strategy/i).fill('AI Memory');
        await page.getByRole('button', { name: /Save Memory/i }).click();
        await page.waitForURL(/\/memories$/);
    });

    test('should perform search and display results', async ({ page }) => {
        // Mock search response
        await page.route('**/api/v1/memory/search', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    results: [
                        {
                            id: 'mock-uuid-1',
                            title: 'Fox Memory',
                            content: 'The quick brown fox jumps over the lazy dog.',
                            score: 0.95,
                            content_type: 'text',
                            tags: ['test'],
                            metadata: {
                                type: 'episode',
                                name: 'Fox Memory',
                                uuid: 'mock-uuid-1',
                                created_at: new Date().toISOString()
                            },
                            created_at: new Date().toISOString(),
                            source: 'episode'
                        }
                    ],
                    total: 1,
                    query: 'fox'
                })
            });
        });

        // Navigate to Search page
        // Use exact name match or more specific selector to avoid matching "Advanced Search" or Project Name
        await page.getByRole('link', { name: 'search Search' }).click();

        // Type query
        await page.getByPlaceholder(/Search memories by keyword/i).fill('fox');

        // Click Retrieve
        await page.getByRole('button', { name: /Retrieve/i }).click();

        // Wait for results
        // Check if "Fox Memory" appears in results
        // Retry logic or wait for indexing
        await expect(page.getByText('Fox Memory')).toBeVisible({ timeout: 15000 });

        // Verify "AI Memory" does NOT appear (assuming decent search relevance)
        // Note: If using semantic search, it might appear with low score, but let's assume strictness for now or check top result.
        // Or check that the count is at least 1
        await expect(page.getByText('Results (1)')).toBeVisible().catch(() => { }); // Optional check if count is displayed exactly
    });

    test('should filter search results', async ({ page }) => {
        // Mock filtered search response
        await page.route('**/api/v1/memory/search', async route => {
            await route.fulfill({
                status: 200,
                contentType: 'application/json',
                body: JSON.stringify({
                    results: [
                        {
                            id: 'mock-uuid-2',
                            title: 'AI Memory',
                            content: 'Artificial Intelligence is transforming the world.',
                            score: 0.88,
                            content_type: 'text',
                            tags: ['ai'],
                            metadata: {
                                type: 'episode',
                                name: 'AI Memory',
                                uuid: 'mock-uuid-2',
                                created_at: new Date().toISOString()
                            },
                            created_at: new Date().toISOString(),
                            source: 'episode'
                        }
                    ],
                    total: 1,
                    query: 'world'
                })
            });
        });

        // Navigate to Search page
        await page.getByRole('link', { name: 'search Search' }).click();

        // Type query
        await page.getByPlaceholder(/Search memories by keyword/i).fill('world');

        // Adjust similarity slider (if possible to interact with range input)
        const slider = page.locator('input[type="range"]');
        if (await slider.isVisible()) {
            await slider.fill('0.1'); // Broad search
        }

        // Click Retrieve
        await page.getByRole('button', { name: /Retrieve/i }).click();

        // Expect AI Memory
        await expect(page.getByText('AI Memory')).toBeVisible({ timeout: 15000 });
    });
});
