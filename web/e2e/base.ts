import { test as base } from '@playwright/test';
import fs from 'fs';
import path from 'path';

export const test = base.extend({
  page: async ({ page }, use) => {
    await use(page);
    
    // Collect coverage from window.__coverage__
    const coverage = await page.evaluate(() => (window as any).__coverage__);
    if (coverage) {
      const dir = path.join(process.cwd(), '.nyc_output');
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
      
      // Save with a unique name
      const filename = `coverage-${Date.now()}-${Math.floor(Math.random() * 10000)}.json`;
      fs.writeFileSync(
        path.join(dir, filename),
        JSON.stringify(coverage)
      );
    }
  },
});

export { expect } from '@playwright/test';
