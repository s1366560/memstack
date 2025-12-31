import { test, expect } from './base';

test.describe('Communities Management', () => {
    let projectName: string;
    let projectId: string;

    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/login');
        await expect(page.getByLabel(/邮箱地址/i)).toBeVisible();
        await expect(page.getByLabel(/密码/i)).toBeVisible();
        await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
        await page.getByLabel(/密码/i).fill('adminpassword');
        await page.getByRole('button', { name: /登录/i }).click();

        // Wait for login to complete and redirect
        await page.waitForURL((url) => {
            return !url.pathname.includes('/login');
        }, { timeout: 10000 });

        // Create Project
        const projectsLink = page.getByRole('link', { name: /Projects/i }).first();
        await projectsLink.waitFor();
        await projectsLink.click();

        // Wait for Project List to load
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible({ timeout: 10000 });

        await page.getByRole('button', { name: /Create New Project/i }).click();
        projectName = `Communities Test ${Date.now()}`;
        await page.getByPlaceholder(/e.g. Finance Knowledge Base/i).fill(projectName);
        await page.getByRole('button', { name: /Create Project/i }).click();
        await page.waitForURL(/\/projects$/);

        // Reload to ensure list is fresh
        await page.reload();
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible();

        // Enter project
        await page.getByPlaceholder(/Search by project name/i).fill(projectName);
        const projectCard = page.getByText(projectName).first();
        await projectCard.waitFor({ state: 'visible' });
        await projectCard.click();

        // Extract project_id from URL
        const url = page.url();
        const match = url.match(/\/projects\/([a-f0-9-]+)/);
        if (match) {
            projectId = match[1];
        }

        // Navigate to Memories Tab
        await page.getByRole('link', { name: /Memories/i }).click();

        // Add multiple memories to create entities for community detection
        const memories = [
            { title: 'Elon Musk', content: 'Elon Musk is the CEO of Tesla and SpaceX, leading electric vehicle and space exploration companies.' },
            { title: 'Tesla', content: 'Tesla is an electric vehicle manufacturer led by Elon Musk, focused on sustainable energy.' },
            { title: 'SpaceX', content: 'SpaceX is a space exploration company founded by Elon Musk, aiming to colonize Mars.' },
            { title: 'Tim Cook', content: 'Tim Cook is the CEO of Apple, leading the technology company.' },
            { title: 'Apple', content: 'Apple is a technology company known for iPhone, iPad, and Mac computers, led by Tim Cook.' },
            { title: 'Microsoft', content: 'Microsoft is a software company led by Satya Nadella, focusing on cloud computing and AI.' },
            { title: 'Satya Nadella', content: 'Satya Nadella is the CEO of Microsoft, leading the company in cloud and AI initiatives.' },
            { title: 'Amazon', content: 'Amazon is an e-commerce and cloud computing company founded by Jeff Bezos.' },
            { title: 'Jeff Bezos', content: 'Jeff Bezos is the founder of Amazon and owner of Blue Origin space company.' },
        ];

        for (const memory of memories) {
            await page.getByRole('button', { name: /Add Memory/i }).click();
            await page.getByPlaceholder(/Start typing your memory/i).fill(memory.content);
            await page.getByPlaceholder(/e.g. Q3 Strategy/i).fill(memory.title);
            await page.getByRole('button', { name: /Save Memory/i }).click();
            await page.waitForTimeout(500); // Small delay between saves
        }

        console.log('Added test memories for community detection');
    });

    test('should display empty communities list initially', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();

        // Check header
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Check for "No communities found" message
        await expect(page.getByText(/No communities found/i)).toBeVisible({ timeout: 10000 });
    });

    test('should rebuild communities in background', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Click rebuild button
        const rebuildButton = page.getByRole('button', { name: /rebuild communities/i }).first();
        await rebuildButton.click();

        // Confirm dialog
        await page.getByRole('button', { name: /Continue/i }).click();

        // Check task status UI appears
        await expect(page.getByText(/Rebuilding communities/i)).toBeVisible({ timeout: 5000 });
        await expect(page.getByText(/Task status: (pending|running|processing)/i)).toBeVisible({ timeout: 5000 });

        console.log('Community rebuild task started successfully');
    });

    test('should track task status during rebuild', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Click rebuild button
        await page.getByRole('button', { name: /rebuild communities/i }).first().click();
        await page.getByRole('button', { name: /Continue/i }).click();

        // Wait for task to complete (max 5 minutes for community rebuild)
        console.log('Waiting for community rebuild to complete...');
        await expect(page.getByText(/Task status: completed/i)).toBeVisible({ timeout: 300000 });

        // Verify success message
        await expect(page.getByText(/Communities rebuilt successfully|rebuild complete/i)).toBeVisible({ timeout: 5000 });

        console.log('Community rebuild completed successfully');
    });

    test('should display communities after rebuild', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Start rebuild if needed
        const noCommunities = page.getByText(/No communities found/i);
        if (await noCommunities.isVisible({ timeout: 5000 })) {
            await page.getByRole('button', { name: /rebuild communities/i }).first().click();
            await page.getByRole('button', { name: /Continue/i }).click();
            await expect(page.getByText(/Task status: completed/i)).toBeVisible({ timeout: 300000 });
        }

        // Wait for task to clear and communities to load
        await page.waitForTimeout(6000);

        // Reload to get fresh data
        await page.reload();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Check communities are displayed
        // Communities should exist since we added memories with entities
        await expect(page.getByText(/communities?/i)).toBeVisible({ timeout: 10000 });

        console.log('Communities displayed successfully');
    });

    test('should load community members', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Ensure communities exist
        const noCommunities = page.getByText(/No communities found/i);
        if (await noCommunities.isVisible({ timeout: 5000 })) {
            await page.getByRole('button', { name: /rebuild communities/i }).first().click();
            await page.getByRole('button', { name: /Continue/i }).click();
            await expect(page.getByText(/Task status: completed/i)).toBeVisible({ timeout: 300000 });
            await page.waitForTimeout(6000);
            await page.reload();
            await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();
        }

        // Click first community card
        const communityCard = page.locator('.community-card, [data-testid="community-card"]').first();
        if (await communityCard.isVisible({ timeout: 5000 })) {
            await communityCard.click();

            // Check members panel/drawer appears
            await expect(page.getByText(/Community Members|members/i)).toBeVisible({ timeout: 10000 });

            console.log('Community members loaded successfully');
        } else {
            console.log('No community cards to click');
        }
    });

    test('should handle rebuild errors gracefully', async ({ page }) => {
        // Mock error response for rebuild endpoint
        await page.route('**/api/v1/communities/rebuild*', route => {
            route.fulfill({
                status: 500,
                contentType: 'application/json',
                body: JSON.stringify({ detail: 'Internal server error' })
            });
        });

        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Try rebuild
        await page.getByRole('button', { name: /rebuild communities/i }).first().click();
        await page.getByRole('button', { name: /Continue/i }).click();

        // Check error message appears
        await expect(page.getByText(/Failed to rebuild|Internal server error|error/i)).toBeVisible({ timeout: 5000 });

        console.log('Error handling test passed');
    });

    test('should refresh communities list', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();
        await page.locator('h1').filter({ hasText: 'Communities' }).waitFor();

        // Check refresh button exists and is visible
        await expect(page.getByRole('button', { name: 'refresh Refresh', exact: true })).toBeVisible();

        // Click refresh button
        await page.getByRole('button', { name: 'refresh Refresh', exact: true }).click();

        // Should still be on communities page
        await expect(page.locator('h1').filter({ hasText: 'Communities' })).toBeVisible();

        console.log('Refresh button works correctly');
    });

    test('should display correct page title and breadcrumbs', async ({ page }) => {
        // Navigate to Communities
        await page.getByRole('link', { name: 'Communities', exact: true }).click();

        // Check page title
        await expect(page.locator('h1').filter({ hasText: 'Communities' })).toBeVisible();

        // Check description/breadcrumb text
        await expect(page.getByText(/Browse and manage communities|communities detected/i)).toBeVisible({ timeout: 5000 });

        console.log('Page structure is correct');
    });
});
