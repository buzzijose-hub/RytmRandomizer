/** Browser rehearsal uses a mocked WebSocket only: no Python sidecar or MIDI. */
import { expect, test } from '@playwright/test';

import type { CommandEnvelope, Event } from '../src/ws/protocol';
import { history, profile, readyDualMachineStage, sendPlan, sessionMock, snapshot } from '../tests/cockpit/_fixtures';
import { forgeCaptures, forgeEntry, showBankState } from '../tests/cockpit/showKitForgeFixture';

import { trackConsoleErrors } from './fixtures/console_guard';

test('Show Kit Forge displays paired evidence and rehearses exact offline audition at two viewport sizes', async ({ page }, testInfo) => {
  const errors = trackConsoleErrors(page);
  const sent: CommandEnvelope[] = [];
  const pair = forgeEntry.candidates[0]!;
  const plan = {
    ...sendPlan,
    candidate_id: pair.rytm_candidate.candidate_id,
    source_snapshot_id: pair.rytm_candidate.source_snapshot_id,
    profile_id: pair.rytm_candidate.profile_id,
    target_pad_ids: pair.recipe.rytm_scope.target_ids,
    locked_pad_ids: pair.recipe.rytm_scope.locked_ids,
    packets: sendPlan.packets.filter((packet) => packet.pad_id === 1),
    estimated_midi_msgs: 1,
    pad_count: 1,
  };
  const events: Event[] = [
    { type: 'session_status', ...sessionMock },
    { type: 'snapshot_changed', snapshot },
    { type: 'profile_changed', profile },
    { type: 'history_updated', history },
    { type: 'kit_captures_changed', captures: forgeCaptures },
    { type: 'mutation_targets_changed', rytm_pad_targets: pair.recipe.rytm_scope.target_ids, a4_track_targets: [] },
    { type: 'mutation_locks_changed', rytm_pad_locks: pair.recipe.rytm_scope.locked_ids, a4_track_locks: [] },
    { type: 'dual_machine_stage_changed', stage: { ...readyDualMachineStage, rytm: { ...readyDualMachineStage.rytm, target_ids: pair.recipe.rytm_scope.target_ids } } },
    { type: 'mutation_previewed', candidate: pair.rytm_candidate },
    { type: 'send_plan_changed', send_plan: plan },
    { type: 'show_bank_changed', show_bank: showBankState },
  ];
  await page.routeWebSocket('ws://127.0.0.1:4317/ws', (socket) => {
    socket.onMessage((message) => {
      const payload = JSON.parse(message.toString()) as CommandEnvelope | { type: 'hello' };
      if ('type' in payload) {
        for (const event of events) socket.send(JSON.stringify(event));
        return;
      }
      sent.push(payload);
      socket.send(JSON.stringify({ request_id: payload.request_id, ok: true }));
      if (payload.command.type === 'show_bank_list') {
        socket.send(JSON.stringify({ type: 'show_bank_changed', show_bank: showBankState }));
      }
    });
  });
  await page.addInitScript(() => {
    (window as unknown as { __RYTM_RAND_WS_TOKEN__: string }).__RYTM_RAND_WS_TOKEN__ = 'mock-show-forge-browser-token';
  });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.goto('/');
  const forge = page.getByTestId('show-kit-forge');
  await expect(forge.getByLabel('Server banks')).toHaveValue('bank-one');
  await expect(forge.getByRole('button', { name: 'Dry-run exact Rytm plan' })).toBeEnabled();
  await forge.getByRole('button', { name: 'Dry-run exact Rytm plan' }).click();
  await expect.poll(() => sent.filter((payload) => payload.command.type === 'send').map((payload) => payload.command)).toEqual([{ type: 'send', send_plan_id: plan.plan_id }]);
  await expect(forge.getByRole('button', { name: 'A4 SEND blocked — offline only' })).toBeDisabled();
  await expect(forge.getByRole('alert')).toContainText('Fingerprint mismatch');
  const desktopBounds = await forge.boundingBox();
  expect(desktopBounds!.width).toBeGreaterThan(1300);
  await forge.locator('.show-kit-forge-header').scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-desktop.png') });
  await forge.getByRole('heading', { name: 'Compare candidates', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-candidates.png') });

  await page.setViewportSize({ width: 600, height: 900 });
  await forge.locator('.show-kit-forge-header').scrollIntoViewIfNeeded();
  await expect(forge).toBeVisible();
  const bounds = await forge.boundingBox();
  expect(bounds!.width).toBeLessThanOrEqual(600);
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-narrow.png') });
  errors.assertClean();
});
