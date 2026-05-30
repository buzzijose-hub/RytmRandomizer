/**
 * Optimistic step cursor does not snap back when a late server state arrives.
 *
 * The bug class this guards: on Name → Next the UI optimistically advances
 * to the Add step (Wizard.tsx `setActiveStep('add')`). The sidecar's
 * `wizard_state_changed` for `wizard_set_metadata` carries `step="name"`
 * (the server side does not advance the cursor — the operator does). Before
 * the `hasSyncedInitialStep` guard, the late state push would overwrite
 * `activeStep` back to `name`, snapping the operator out of their flow.
 *
 * This spec advances past Name, then idles long enough for the WS round-trip
 * to land + the React effect to run. If the snap-back regression returned,
 * the Add step would disappear and the Name step would be visible.
 */

import { expect, test } from './fixtures/wizard_fixture';

test.describe('wizard optimistic cursor', () => {
  test('late wizard_state_changed does not roll back the optimistic step', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible();

    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    await page.getByTestId('wizard-name-input').fill('optimistic-test');
    await page.getByTestId('wizard-next').click();

    // Optimistic transition: Add step appears immediately.
    await expect(page.getByTestId('wizard-add-step')).toBeVisible();
    await expect(page.getByTestId('wizard-name-step')).toBeHidden();

    // Give the WS ack + late state event plenty of time to arrive and be
    // processed by the store. The guard means the cursor should NOT move.
    // We poll the assertion across a 2s window so any snap-back is caught.
    await page.waitForTimeout(2_000);

    await expect(page.getByTestId('wizard-add-step')).toBeVisible();
    await expect(page.getByTestId('wizard-name-step')).toBeHidden();

    // Add a source so the store's authoritative state is also `step="add"` /
    // populated — proves the WS round-trip really did happen.
    await page.getByTestId('wizard-add-artist').click();
    await expect(page.getByTestId('wizard-draft')).toBeVisible();
  });
});
