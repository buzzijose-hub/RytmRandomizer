/**
 * Captures page.ariaSnapshot() at the 8 documented checkpoints from
 * the spec (§"Manual SR test plan"). Phase C (Task 12) commits the
 * actual YAML fixtures after all fixes are in place.
 *
 * Until then, this spec is `test.skip()` so CI doesn't fail on missing
 * snapshot files.
 */
import { test, expect } from '@playwright/test';

test.describe('A11y SR-equivalent journey (page.ariaSnapshot fixtures)', () => {
  test.skip('cockpit-boot snapshot', async ({ page }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    const snapshot = await page.ariaSnapshot();
    expect(snapshot).toMatchSnapshot('cockpit-boot.aria.yml');
  });
});
