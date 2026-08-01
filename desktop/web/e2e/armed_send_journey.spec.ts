/**
 * E2E: the full ARMED SEND operator journey, browser → sidecar → seam.
 *
 *   arm → exact port + token → PREPARE → confirmed SEND → disarm
 *
 * ## Why this spec has to exist
 *
 * The Vitest cockpit suite drives a `FakeCockpitClient`: it can prove the UI
 * *emits* `{ type: 'send', confirm: true }`, but it cannot prove the sidecar
 * *accepts* it. Those are exactly the two halves that drifted apart — the
 * frontend shipped a bare `{ type: 'send' }` while
 * `cockpit/ws/handlers.py::_armed_send_over_seam` had begun refusing any
 * armed send without `confirm: true`. Every unit test on both sides was
 * green; the live SEND button simply could not succeed. Only a real browser
 * against a real sidecar catches that class of bug, which is what this file
 * is for.
 *
 * ## Harness requirement, and what happens without it
 *
 * Arming is fail-closed by design: `_resolve_arm_port_name` refuses unless
 * the operator-named port matches **exactly one** entry in the sidecar's live
 * output enumeration, and `ExactOutputOpener` then has to actually open it.
 * So this journey needs one real, enumerable MIDI output on the host running
 * the test. On a developer Mac that is an IAC Driver bus (Audio MIDI Setup →
 * MIDI Studio → IAC Driver → "Device is online"); on Linux CI it is an ALSA
 * virtual port; on Windows, loopMIDI.
 *
 * When no such port exists the spec **skips with a named reason** rather than
 * asserting something weaker and calling it a pass. Two things are deliberate
 * there:
 *
 *   1. It does not fabricate a port through a test-only backdoor in the
 *      sidecar. A hook that lets a test conjure an armable output is a hook
 *      that exists in the shipped binary, and the arm path is the one place
 *      in this codebase where "fail closed" is the entire point.
 *   2. The skip is loud (`test.skip` with the reason in the message), so a CI
 *      lane that silently lost its virtual port reads as "not run", never as
 *      "passed".
 *
 * The unarmed half of the journey — which needs no MIDI port at all — is a
 * separate, always-running test below, so this file has real teeth on every
 * host. See the PR body for the current CI status of the armed lane.
 */

import { test, expect } from './fixtures/wizard_fixture';
import type { Page } from '@playwright/test';

/** How long to let the sidecar's connection poll publish its first enumeration. */
const ENUMERATION_TIMEOUT_MS = 8_000;

/**
 * Read the outputs the sidecar has actually enumerated, straight from the
 * cockpit's own store — i.e. exactly the list the arm dialog will offer.
 */
async function enumeratedOutputs(page: Page): Promise<string[]> {
  await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
  await page.getByTestId('arm-open-button').click();
  const select = page.getByTestId('arm-port-select');
  await expect(select).toBeVisible();
  // Option 0 is the "Select a port…" placeholder; the rest are real ports.
  const values = await select.locator('option').evaluateAll((opts) =>
    opts.map((o) => (o as HTMLOptionElement).value).filter((v) => v !== ''),
  );
  return values;
}

/**
 * Select a profile so the sidecar has something to mutate.
 *
 * `prepare_send_plan` refuses with "no active profile" until one is chosen,
 * and the chip ids come from the sidecar's own registry — so pick the first
 * chip the cockpit actually rendered rather than hard-coding an id.
 */
async function selectFirstProfile(page: Page): Promise<void> {
  const chips = page.getByTestId('profile-chips').getByRole('button');
  await expect(chips.first()).toBeVisible({ timeout: ENUMERATION_TIMEOUT_MS });
  await chips.first().click();
}

/**
 * Turn the ghost preview on.
 *
 * The sidecar only pushes `mutation_previewed { candidate }` while preview is
 * on, and the UI gates PREPARE on having seen a candidate — so the operator
 * journey genuinely starts here, not at REGEN.
 */
async function enablePreview(page: Page): Promise<void> {
  const toggle = page.getByTestId('action-preview');
  if ((await toggle.getAttribute('aria-pressed')) !== 'true') {
    await toggle.click();
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
  }
}

/** Drive the cockpit to a PREPARE-d, ready send plan. */
async function prepareSendPlan(page: Page): Promise<void> {
  await enablePreview(page);
  // REGEN guarantees a fresh candidate regardless of the boot-time depth.
  await page.getByTestId('action-regen').click();
  const prepare = page.getByTestId('action-prepare-send-plan');
  await expect(prepare).toBeEnabled({ timeout: ENUMERATION_TIMEOUT_MS });
  await prepare.click();
  await expect(page.getByTestId('action-send')).toBeEnabled();
}

test.describe('armed SEND journey (I2)', () => {
  test('unarmed SEND is a single click and needs no confirmation dialog', async ({
    page,
    sidecar,
  }) => {
    expect(sidecar.token.length).toBeGreaterThan(20);
    await page.goto('/');
    await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });

    await selectFirstProfile(page);
    await prepareSendPlan(page);

    const send = page.getByTestId('action-send');
    // Mock session ⇒ dry-run label, and the sidecar does not demand confirm.
    await expect(send).toContainText('DRY-RUN SEND');
    await send.click();

    // No confirmation dialog appears on the unarmed path...
    await expect(page.getByTestId('send-confirm-dialog')).toHaveCount(0);
    // ...and the send landed: the plan is consumed, so SEND disables again
    // until the operator PREPAREs a fresh one.
    await expect(send).toBeDisabled();
  });

  test('arm → exact port + token → prepare → confirmed SEND → disarm', async ({
    page,
    sidecar,
  }) => {
    await page.goto('/');
    const outputs = await enumeratedOutputs(page);

    test.skip(
      outputs.length === 0,
      'No MIDI output enumerated on this host, so the fail-closed arm path ' +
        'cannot be exercised end-to-end. Enable a virtual MIDI output ' +
        '(macOS: IAC Driver bus online; Linux: ALSA virtual port; Windows: ' +
        'loopMIDI) and re-run. This spec deliberately does NOT fake a port ' +
        'through a sidecar backdoor — see the file header.',
    );

    const portName = outputs[0]!;

    // --- ARM: exact port + token + explicit confirm -------------------------
    await page.getByTestId('arm-port-select').selectOption(portName);
    await page.getByTestId('arm-token-input').fill(sidecar.token);
    const confirmArm = page.getByTestId('arm-confirm-button');
    await expect(confirmArm).toBeEnabled();
    await confirmArm.click();

    // The dialog closes only on an accepted arm; the button flips to Disarm.
    await expect(page.getByTestId('arm-dialog')).toHaveCount(0);
    await expect(page.getByTestId('disarm-button')).toBeVisible();

    // --- PREPARE ------------------------------------------------------------
    await selectFirstProfile(page);
    await prepareSendPlan(page);

    // Armed ⇒ live label, not the dry-run one.
    const send = page.getByTestId('action-send');
    await expect(send).toContainText('SEND');
    await expect(send).not.toContainText('DRY-RUN SEND');

    // --- SEND: per-action confirmation is mandatory -------------------------
    await send.click();
    const dialog = page.getByTestId('send-confirm-dialog');
    await expect(dialog).toBeVisible();
    await expect(dialog).toContainText(portName);

    await page.getByTestId('send-confirm-button').click();
    await expect(dialog).toHaveCount(0);

    // The sidecar accepted the confirmed send: the plan is consumed and no
    // error surfaced. A refusal (`confirm` missing / seam refusal) would leave
    // the plan in place and log an operator error instead.
    await expect(send).toBeDisabled();

    // --- DISARM: always one click, never behind a dialog --------------------
    await page.getByTestId('disarm-button').click();
    await expect(page.getByTestId('arm-open-button')).toBeVisible();
    // Back to passive: the label reverts to the dry-run wording.
    await prepareSendPlan(page);
    await expect(page.getByTestId('action-send')).toContainText('DRY-RUN SEND');
  });
});
