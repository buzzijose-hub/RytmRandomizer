/**
 * Cancel mid-flow clears wizard state and returns the operator to the cockpit.
 *
 * Walks through Name → Add to prove the wizard has accumulated state, then
 * clicks Cancel. Asserts:
 *   1. The cockpit is visible again.
 *   2. Re-launching the wizard starts back at the Name step (no carry-over).
 *
 * The Cancel button on the Name step is wired to `handleCancel` in Wizard.tsx
 * which sends `wizard_cancel` + navigates to `#/`. We assert through the UI
 * rather than peeking at the store so the test stays black-box.
 */

import { expect, test } from './fixtures/wizard_fixture';

test.describe('wizard cancel', () => {
  test('cancel clears state; re-launch starts fresh on the Name step', async ({
    page,
    sidecar: _sidecar,
  }) => {
    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible();

    // ----- First launch: name → add, then cancel from the name step -----
    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    await page.getByTestId('wizard-name-input').fill('to-be-cancelled');
    await page.getByTestId('wizard-next').click();
    await expect(page.getByTestId('wizard-add-step')).toBeVisible();

    // Go back to the name step so we can hit Cancel (only NameStep renders
    // the Cancel button via Wizard.tsx's `handleCancel` wiring).
    await page.getByTestId('wizard-back').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();

    await page.getByTestId('wizard-cancel').click();

    // Cockpit is back; no orphan wizard root left over.
    await expect(page.getByTestId('cockpit-root')).toBeVisible();
    await expect(page.getByTestId('wizard-root')).toBeHidden();

    // ----- Second launch: state should be fresh (empty name field, step=name) -----
    await page.getByTestId('mutation-panel-launch-wizard').click();
    await expect(page.getByTestId('wizard-name-step')).toBeVisible();
    await expect(page.getByTestId('wizard-name-input')).toHaveValue('');
  });
});
