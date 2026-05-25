/**
 * E2E axe-core scan per top-level route. Same per-route grandfathered
 * floor map as the Vitest smoke suite so they cannot drift apart.
 */
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

// Per-route floor map. Each fix-cluster task drops its entry to 0.
const FLOORS: Record<string, number> = {
  '/': 0,
  '/#/wizard': 0,
};

const ROUTES = Object.keys(FLOORS);

for (const route of ROUTES) {
  test(`axe-core scan on route ${route}`, async ({ page }) => {
    await page.goto(route);
    // Wait for the cockpit/wizard root to mount (no `domcontentloaded`
    // race — the Cockpit waits for a session_status event).
    await page
      .getByTestId(route === '/' ? 'cockpit-root' : 'wizard-root')
      .waitFor({ state: 'visible', timeout: 10_000 });
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const violations = results.violations.length;
    expect(
      violations,
      `${route}: ${results.violations.map((v) => v.id).join(', ')}`,
    ).toBeLessThanOrEqual(FLOORS[route]);
  });
}
