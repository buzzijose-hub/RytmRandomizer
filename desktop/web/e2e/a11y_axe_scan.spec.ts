/**
 * E2E axe-core scan per top-level route. Same per-route grandfathered
 * floor map as the Vitest smoke suite so they cannot drift apart.
 *
 * Uses the wizard_fixture which boots a real Python sidecar — the
 * Cockpit only renders <main data-testid="cockpit-root"> after a
 * session_status arrives over the WebSocket. Without the sidecar the
 * App stays on the "Connecting…" placeholder forever and the
 * cockpit-root testid never appears, so a plain @playwright/test
 * spec times out (CI saw 10s timeouts on this).
 */
import AxeBuilder from '@axe-core/playwright';

import { expect, test } from './fixtures/wizard_fixture';

// Per-route floor map. Each fix-cluster task drops its entry to 0.
const FLOORS: Record<string, number> = {
  '/': 0,
  '/#/wizard': 0,
};

const ROUTES = Object.keys(FLOORS);

for (const route of ROUTES) {
  // Fixture parameter `sidecar` is mandatory even though we don't use it
  // directly — referencing it tells Playwright to boot the sidecar before
  // the test runs.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  test(`axe-core scan on route ${route}`, async ({ page, sidecar }) => {
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
