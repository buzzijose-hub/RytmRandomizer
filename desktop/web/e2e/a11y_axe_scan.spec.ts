/**
 * E2E axe-core scans for Cockpit, Wizard and Appliance. Each route has a
 * zero-violation floor and must reach its real, sidecar-backed state first.
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

test.use({ sidecarEnv: { RYTM_RAND_APPLIANCE_SIMULATION: '0' } });

// Per-route floor map. Each fix-cluster task drops its entry to 0.
const FLOORS: Record<string, number> = {
  '/': 0,
  '/#/wizard': 0,
  '/#/appliance': 0,
};

const ROUTES = Object.keys(FLOORS);
const ROOTS: Record<string, string> = {
  '/': 'cockpit-root',
  '/#/wizard': 'wizard-root',
  '/#/appliance': 'appliance',
};

for (const route of ROUTES) {
  // Fixture parameter `sidecar` is mandatory even though we don't use it
  // directly — referencing it tells Playwright to boot the sidecar before
  // the test runs.
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  test(`axe-core scan on route ${route}`, async ({ page, sidecar }) => {
    await page.goto(route);
    // The Appliance mounts its disconnected shell immediately; wait for
    // authenticated appliance state so we do not audit only that placeholder.
    await page
      .getByTestId(ROOTS[route]!)
      .waitFor({ state: 'visible', timeout: 10_000 });
    if (route === '/#/appliance') {
      await expect(page.getByRole('heading', { name: 'HOME / PERFORM' })).toBeVisible();
      await expect(page.getByText('PASSIVE / DISARMED', { exact: true })).toBeVisible();
      await expect(page.getByRole('button', { name: /^Pad \d+,/ })).toHaveCount(12);
    }
    const results = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa'])
      .analyze();
    const violations = results.violations.length;
    const detail = results.violations
      .map((v) => {
        const targets = v.nodes
          .slice(0, 3)
          .map((n) => n.target.join(' > '))
          .join('; ');
        return `${v.id} (${v.impact}): ${v.help} — ${targets}`;
      })
      .join('\n  ');
    expect(violations, `${route}:\n  ${detail}`).toBeLessThanOrEqual(FLOORS[route]);
  });
}
