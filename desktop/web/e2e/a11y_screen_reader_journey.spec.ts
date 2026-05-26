/**
 * 3-checkpoint SR-equivalent journey via page.ariaSnapshot() YAML fixtures.
 * See docs/superpowers/specs/2026-05-25-ada-aa-accessibility-design.md
 * §"Manual SR test plan" for the per-checkpoint expectations.
 *
 * Why the `wizard_fixture` (full sidecar boot) and not plain `@playwright/test`:
 * `App.tsx` only renders `<Cockpit/>` or `<Wizard/>` once `sessionStatus !== null`,
 * which requires a real `session_status` push from the Python sidecar. Without
 * the sidecar all three checkpoints would snapshot the "Connecting…" placeholder
 * instead of the routes under test.
 *
 * Why `expect(page).toMatchAriaSnapshot()` (not `expect(string).toMatchSnapshot()`):
 * the cockpit history strip renders a server-minted ULID per snapshot (e.g.
 * "Load snapshot 01KSG...") which changes every fresh sidecar boot. Only the
 * `toMatchAriaSnapshot` matcher interprets `/regex/` lines inside the YAML as
 * regex patterns — `toMatchSnapshot` does a strict string compare and would
 * fail on every re-run. The YAML fixtures keep the stable ARIA tree shape
 * intact and only swap a `/regex/` placeholder for the dynamic ULID.
 */
import { expect, test } from './fixtures/wizard_fixture';

test.describe('SR-equivalent journey snapshots', () => {
  test('1. cockpit boot — landmark + title + tab order', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await expect(page).toMatchAriaSnapshot({ name: 'checkpoint-1-cockpit-boot.aria.yml' });
  });

  test('2. wizard landing — name step heading + form', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await page.evaluate(() => {
      window.location.hash = '#/wizard';
    });
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    await page.getByTestId('wizard-name-step').waitFor({ state: 'visible' });
    await expect(page).toMatchAriaSnapshot({ name: 'checkpoint-2-wizard-name.aria.yml' });
  });

  test('3. name step empty-submit error state', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await page.getByTestId('cockpit-root').waitFor({ state: 'visible' });
    await page.evaluate(() => {
      window.location.hash = '#/wizard';
    });
    await page.getByTestId('wizard-root').waitFor({ state: 'visible' });
    await page.getByTestId('wizard-name-step').waitFor({ state: 'visible' });

    // Submit the empty name to trigger the role="alert" + aria-invalid path
    // (see NameStep.handleSubmit). Using the test-id rather than raw Tab keys
    // keeps the spec robust against changes to the tab order while still
    // exercising the exact code path a keyboard user would reach with Enter.
    await page.getByTestId('wizard-next').click();

    // The error region is rendered synchronously by NameStep when the trimmed
    // name is empty. Wait on the role="alert" so the snapshot captures the
    // post-error tree, not the pre-submit one.
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page).toMatchAriaSnapshot({ name: 'checkpoint-3-name-error.aria.yml' });
  });
});
