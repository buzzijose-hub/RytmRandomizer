/**
 * Routing smoke test — would have caught the production bug where
 * `MutationPanel.handleLaunchWizard` set `window.location.hash = '/wizard'`
 * but `App.tsx` did NOT listen for `hashchange`, so the wizard never mounted.
 *
 * The test is intentionally minimal: click the launcher, assert the wizard
 * mounts. A green run here proves that the hash-route plumbing connects
 * the cockpit launcher to the wizard root.
 *
 * NOTE for reviewers: until FIX-B lands the `hashchange` listener in App.tsx,
 * this test (and every spec downstream that begins with launching the wizard)
 * will fail. That failure is the entire point of this suite — it's the
 * automated regression net that was missing when the bug shipped.
 */

import { expect, test } from './fixtures/wizard_fixture';

test.describe('wizard routing', () => {
  test('launcher click mounts the wizard, back navigates to cockpit', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');

    // Wait for the cockpit to finish bootstrapping (session_status pushed by
    // the sidecar). The launcher is rendered inside MutationPanel, which only
    // mounts once the cockpit has a non-null sessionStatus.
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('mutation-panel-launch-wizard')).toBeVisible();

    await page.getByTestId('mutation-panel-launch-wizard').click();

    // The wizard's root carries `data-testid="wizard-root"`; the cockpit's
    // root must disappear so we don't render both panels at once.
    await expect(page.getByTestId('wizard-root')).toBeVisible();
    await expect(page.getByTestId('cockpit-root')).toBeHidden();

    // Browser back returns to the cockpit (clears the `#/wizard` hash).
    await page.goBack();
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('wizard-root')).toBeHidden();
  });
});
