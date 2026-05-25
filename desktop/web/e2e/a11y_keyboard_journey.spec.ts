/**
 * Cockpit + wizard happy paths driven via page.keyboard only.
 * Forbids page.click() — every UI surface must be keyboard-reachable.
 *
 * Phase A: skeleton with a single skipped test. Phase B fix tasks
 * un-skip + flesh out as their cluster lands.
 */
import { test, expect } from '@playwright/test';

test.describe('A11y keyboard journey (no mouse allowed)', () => {
  test.skip('cockpit boot: Tab order header → mutation → snapshot → action', async ({
    page,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible', timeout: 10_000 });
    // Sanity: focus body, then Tab through.
    await page.keyboard.press('Tab');
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(focused).not.toBe('BODY');
    // Cluster 1 task fleshes out the full Tab sequence assertions.
  });
});
