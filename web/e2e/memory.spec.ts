import { test, expect } from '@playwright/test';

test.describe('Memory Operations', () => {
    const projectName = `Test Project ${Date.now()}`;

    test.beforeEach(async ({ page }) => {
        // Login
        await page.goto('/login');
        await page.getByLabel(/邮箱地址/i).fill('admin@memstack.ai');
        await page.getByLabel(/密码/i).fill('admin123');
        await page.getByRole('button', { name: /登录/i }).click();
        await expect(page).not.toHaveURL(/\/login/);

        // Create a project for this test suite (or navigate to one)
        // For reliability, creating a fresh project is better, but might be slow.
        // Let's reuse a "Test Project" if it exists, or create it.
        // Or just create one to be safe.

        // Handle dialogs (confirm delete)
        page.on('dialog', dialog => dialog.accept());

        const projectsLink = page.getByRole('link', { name: /Projects/i }).first();
        if (await projectsLink.isVisible()) {
            await projectsLink.click();
        }

        // Cleanup existing projects if needed
        const moreButton = page.locator('button:has(.material-symbols-outlined:text("more_vert"))').first();
        if (await moreButton.isVisible()) {
            await moreButton.click();
            await page.getByText('Delete Project').click();
            await page.waitForTimeout(1000);
        }

        // Create new project
        await page.getByRole('button', { name: /Create New Project/i }).click();
        // Use placeholder to match the input
        await page.getByPlaceholder(/e.g. Finance Knowledge Base/i).fill(projectName);
        await page.getByRole('button', { name: /Create Project/i }).click();

        // Wait for navigation with increased timeout for this specific action
        await page.waitForURL(/\/projects$/, { timeout: 15000 });

        // Reload to ensure list is fresh
        await page.reload();
        await expect(page.getByRole('heading', { name: /Project Management/i })).toBeVisible();

        // Navigate into the project
        // Search for the project to ensure it's visible even if there are many projects
        await page.getByPlaceholder(/Search by project name/i).fill(projectName);

        // Wait for the project card to be stable and clickable
        const projectCard = page.getByText(projectName).first();
        await projectCard.waitFor({ state: 'visible' });
        await projectCard.click();
    });

    test('should create a new memory and visualize it', async ({ page }) => {
        // Navigate to "Add Memory"
        // Assuming there is an "Add Memory" button in the project overview or memory list
        await page.getByRole('button', { name: /Add Memory/i }).click();

        // Fill memory content
        const memoryContent = 'Playwright E2E Test Memory: ' + Date.now();
        // NewMemory.tsx uses a textarea with a placeholder
        await page.getByPlaceholder(/Start typing your memory/i).fill(memoryContent);

        // Add title if available
        await page.getByPlaceholder(/e.g. Q3 Strategy/i).fill('E2E Memory Title');

        // Save
        await page.getByRole('button', { name: /Save Memory/i }).click();

        // Verify redirect to memory list
        // URL pattern: /project/:id/memories
        await expect(page).toHaveURL(/\/memories$/);

        // Check if memory is listed
        await expect(page.getByText('E2E Memory Title')).toBeVisible();

        // Navigate to Graph view
        // Assuming sidebar has "Graph" link
        await page.getByRole('link', { name: /Graph/i }).click();

        // Verify graph container is present
        // CytoscapeGraph renders a canvas inside a div
        const _graphContainer = page.locator('.cytoscape-container, canvas').first();
        // Since canvas selectors can be tricky, check for the parent container or specific text
        // The graph component has "Nodes:" and "Edges:" text in the toolbar
        await expect(page.getByText(/Nodes:/i)).toBeVisible();
        await expect(page.getByText(/Edges:/i)).toBeVisible();
    });
});
