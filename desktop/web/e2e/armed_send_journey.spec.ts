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

import { test, expect, type SidecarHandle } from './fixtures/wizard_fixture';
import type { Page, WebSocket } from '@playwright/test';
import {
  isEvent,
  type CockpitSendPlan,
  type Event as CockpitEvent,
  type MutationCandidate,
} from '../src/ws/protocol';

/** How long to let the sidecar's connection poll publish its first enumeration. */
const ENUMERATION_TIMEOUT_MS = 8_000;
/** Bounded operator candidate search, never a retry of a failed SEND. */
const MAX_CANDIDATES = 8;
const PAIRED_CONTROL_MESSAGE =
  'Paired-control precision is unverified. No part of this plan will be sent.';

async function openCockpit(page: Page, sidecar: SidecarHandle): Promise<WebSocket> {
  const connected = page.waitForEvent('websocket', {
    predicate: (socket) => {
      const url = new URL(socket.url());
      return url.hostname === sidecar.host && url.port === String(sidecar.port);
    },
  });
  await page.goto('/');
  await expect(page.getByTestId('cockpit-root')).toBeVisible({ timeout: 10_000 });
  return connected;
}

function readEvent(payload: string | Buffer): CockpitEvent | null {
  const message: unknown = JSON.parse(
    typeof payload === 'string' ? payload : payload.toString('utf8'),
  );
  return isEvent(message) ? message : null;
}

/** Observe real sidecar events; every command still comes from a UI click. */
async function eventAfterUI(
  socket: WebSocket,
  type: CockpitEvent['type'],
  action: () => Promise<void>,
): Promise<CockpitEvent> {
  const received = socket.waitForEvent('framereceived', {
    predicate: ({ payload }) => readEvent(payload)?.type === type,
    timeout: ENUMERATION_TIMEOUT_MS,
  });
  await action();
  const event = readEvent((await received).payload);
  if (event === null || event.type !== type) {
    throw new Error(`Expected sidecar ${type} event after UI action`);
  }
  return event;
}

async function previewAfterUI(
  socket: WebSocket,
  action: () => Promise<void>,
): Promise<MutationCandidate> {
  const event = await eventAfterUI(socket, 'mutation_previewed', action);
  if (event.type !== 'mutation_previewed' || event.candidate === null) {
    throw new Error('Expected a genuine generated preview after UI action');
  }
  return event.candidate;
}

async function prepareCurrentCandidate(
  page: Page,
  socket: WebSocket,
  candidate: MutationCandidate,
): Promise<CockpitSendPlan> {
  const prepare = page.getByTestId('action-prepare-send-plan');
  await expect(prepare).toBeEnabled({ timeout: ENUMERATION_TIMEOUT_MS });
  const event = await eventAfterUI(socket, 'send_plan_changed', () => prepare.click());
  if (event.type !== 'send_plan_changed' || event.send_plan === null) {
    throw new Error('Expected a genuine prepared plan after PREPARE');
  }
  expect(event.send_plan.candidate_id).toBe(candidate.candidate_id);
  return event.send_plan;
}

async function expectPairedControlRefusal(page: Page, plan: CockpitSendPlan): Promise<void> {
  expect(plan.ready).toBe(false);
  expect(plan.blocked_reasons).toContain('paired_control_precision_unverified');
  await expect(page.getByTestId('action-send')).toBeDisabled();
  await expect(page.getByTestId('safety-rail')).toContainText(PAIRED_CONTROL_MESSAGE);
  await expect(page.getByTestId('send-confirm-dialog')).toHaveCount(0);
}

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
  await expect(chips.first()).toHaveAttribute('aria-pressed', 'true');
}

/**
 * Turn the ghost preview on.
 *
 * The sidecar only pushes `mutation_previewed { candidate }` while preview is
 * on, and the UI gates PREPARE on having seen a candidate — so the operator
 * journey genuinely starts here, not at REGEN.
 */
async function enablePreview(page: Page, socket: WebSocket): Promise<void> {
  const toggle = page.getByTestId('action-preview');
  if ((await toggle.getAttribute('aria-pressed')) !== 'true') {
    await previewAfterUI(socket, () => toggle.click());
    await expect(toggle).toHaveAttribute('aria-pressed', 'true');
  }
}

/** Select an actual supported preview scope, retaining its seed through PREPARE. */
async function prepareSendPlan(page: Page, socket: WebSocket): Promise<void> {
  await enablePreview(page, socket);
  const clearTargets = page.getByTestId('rytm-target-summary').getByRole('button');
  if (await clearTargets.isEnabled()) {
    await previewAfterUI(socket, () => clearTargets.click());
  }

  // The default snapshot includes paired LFO Depth. A broad generated
  // candidate may correctly refuse; inspect that refusal before narrowing
  // scope, rather than assuming REGEN always produces a sendable plan.
  for (let attempt = 0; attempt < MAX_CANDIDATES; attempt += 1) {
    const candidate = await previewAfterUI(socket, () => page.getByTestId('action-regen').click());
    const broadPlan = await prepareCurrentCandidate(page, socket, candidate);
    if (candidate.pad_deltas.some((delta) => delta.changed_keys.includes('lfo_depth'))) {
      await expectPairedControlRefusal(page, broadPlan);
    } else if (broadPlan.packets.length > 0) {
      expect(broadPlan.ready).toBe(true);
      await expect(page.getByTestId('action-send')).toBeEnabled();
    } else {
      expect(broadPlan.ready).toBe(false);
      expect(broadPlan.blocked_reasons).toContain('no_sendable_changes');
      await expect(page.getByTestId('action-send')).toBeDisabled();
    }

    const supported = candidate.pad_deltas.find(
      (delta) => !delta.changed_keys.includes('lfo_depth') &&
        broadPlan.packets.some((packet) => packet.pad_id === delta.pad_id),
    );
    if (supported === undefined) continue;

    const card = page.getByTestId(`pad-card-${supported.pad_id}`);
    const target = card.getByRole('button', { name: `Target pad ${supported.pad_id}`, exact: true });
    const scoped = await previewAfterUI(socket, () => target.click());
    expect(scoped.seed).toBe(candidate.seed);
    expect(scoped.source_snapshot_id).toBe(candidate.source_snapshot_id);
    expect(scoped.pad_deltas).toEqual([supported]);
    await expect(
      card.getByRole('button', { name: `Remove pad ${supported.pad_id}`, exact: true }),
    ).toHaveAttribute('aria-pressed', 'true');
    await expect(card.getByTestId('knob-ghost-LDP')).toHaveCount(0);

    const plan = await prepareCurrentCandidate(page, socket, scoped);
    expect(plan.ready).toBe(true);
    expect(plan.blocked_reasons).toEqual([]);
    expect(plan.target_pad_ids).toEqual([supported.pad_id]);
    expect(plan.packets).toEqual(
      broadPlan.packets.filter((packet) => packet.pad_id === supported.pad_id),
    );
    expect(plan.packets.length).toBeGreaterThan(0);
    await expect(page.getByTestId('action-send')).toBeEnabled();
    return;
  }
  throw new Error(
    `No pad with unchanged paired LFO Depth and supported changes in ${MAX_CANDIDATES} genuine UI candidates`,
  );
}

test.describe('armed SEND journey (I2)', () => {
  test('changed paired LFO Depth blocks the whole plan and explains the refusal', async ({
    page,
    sidecar,
  }) => {
    const socket = await openCockpit(page, sidecar);
    await selectFirstProfile(page);
    await enablePreview(page, socket);

    for (let attempt = 0; attempt < MAX_CANDIDATES; attempt += 1) {
      const candidate = await previewAfterUI(socket, () => page.getByTestId('action-regen').click());
      const plan = await prepareCurrentCandidate(page, socket, candidate);
      const paired = candidate.pad_deltas.find((delta) => delta.changed_keys.includes('lfo_depth'));
      if (paired === undefined) {
        expect(plan.ready).toBe(plan.packets.length > 0);
        if (plan.ready) await expect(page.getByTestId('action-send')).toBeEnabled();
        else await expect(page.getByTestId('action-send')).toBeDisabled();
        continue;
      }
      await expect(
        page.getByTestId(`pad-card-${paired.pad_id}`).getByTestId('knob-ghost-LDP'),
      ).toHaveCount(1);
      expect(plan.packets.length).toBeGreaterThan(0);
      await expectPairedControlRefusal(page, plan);
      return;
    }
    throw new Error(`No changed paired LFO Depth in ${MAX_CANDIDATES} genuine UI candidates`);
  });

  test('unarmed SEND is a single click and needs no confirmation dialog', async ({
    page,
    sidecar,
  }) => {
    expect(sidecar.token.length).toBeGreaterThan(20);
    const socket = await openCockpit(page, sidecar);

    await selectFirstProfile(page);
    await prepareSendPlan(page, socket);

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
    const socket = await openCockpit(page, sidecar);
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
    await prepareSendPlan(page, socket);

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
    await prepareSendPlan(page, socket);
    await expect(page.getByTestId('action-send')).toContainText('DRY-RUN SEND');
  });
});
