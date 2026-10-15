/** Browser rehearsal uses a mocked WebSocket only: no Python sidecar or MIDI. */
import { expect, test } from '@playwright/test';

import type { CommandEnvelope, Event } from '../src/ws/protocol';
import { history, profile, readyDualMachineStage, sendPlan, sessionMock, snapshot } from '../tests/cockpit/_fixtures';
import { forgeCaptures, forgeEntry, showBankState } from '../tests/cockpit/showKitForgeFixture';
import { parameterEvent } from '../tests/cockpit/parameterScopeFixture';
import { a4TransportReport } from '../tests/cockpit/a4PreparationFixture';

import { trackConsoleErrors } from './fixtures/console_guard';

test('Show Kit Forge displays paired evidence and rehearses exact offline audition at two viewport sizes', async ({ page }, testInfo) => {
  await page.route('**/favicon.ico', (route) => route.fulfill({ status: 204 }));
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
    { ...parameterEvent, a4_parameters: null },
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
      socket.send(JSON.stringify({ request_id: payload.request_id, ok: true,
        ...(payload.command.type === 'show_bank_list' && 'a4_preparation' in payload.command
          ? { a4_preparation: a4TransportReport(false) } : {}),
      }));
      if (payload.command.type === 'show_bank_list') {
        socket.send(JSON.stringify({ type: 'show_bank_changed', show_bank: showBankState }));
      }
      if (payload.command.type === 'get_mutation_parameters') {
        socket.send(JSON.stringify({ ...parameterEvent, a4_parameters: null }));
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
  await forge.getByRole('button', { name: 'Preview Rytm', exact: true }).click();
  await expect.poll(() => sent.filter(payload => payload.command.type === 'show_bank_select_candidate').map(payload => payload.command)).toEqual([{
    type: 'show_bank_select_candidate', bank_id: 'bank-one', entry_id: forgeEntry.entry_id,
    candidate_id: pair.candidate_id, expected_revision: 7,
  }]);
  expect(sent.some(payload => payload.command.type === 'toggle_preview')).toBe(false);
  await forge.getByRole('button', { name: 'Dry-run exact Rytm plan' }).click();
  await expect.poll(() => sent.filter((payload) => payload.command.type === 'send').map((payload) => payload.command)).toEqual([{ type: 'send', send_plan_id: plan.plan_id }]);
  await expect(forge.getByRole('button', { name: 'A4 SEND blocked — offline only' })).toBeDisabled();
  await expect(forge.getByRole('alert')).toContainText('Fingerprint mismatch');
  const desktopBounds = await forge.boundingBox();
  expect(desktopBounds!.width).toBeGreaterThan(1300);
  const packets = page.getByTestId('safety-rail').getByRole('table', { name: 'Exact prepared Rytm packets', exact: true });
  const assertPacketGeometry = async (): Promise<void> => {
    await expect(packets).toBeVisible();
    const channelLines = await packets.getByRole('columnheader', { name: 'Channel', exact: true }).evaluate((cell) => {
      const range = document.createRange(); range.selectNodeContents(cell);
      return new Set([...range.getClientRects()].map((rect) => Math.round(rect.top))).size;
    });
    expect(channelLines).toBe(1);
    for (let index = 0; index < plan.packets.length; index += 1) {
      const packet = plan.packets[index]!;
      const cells = packets.locator('tbody tr').nth(index).locator('td');
      await expect(cells).toHaveText([String(packet.pad_id), packet.parameter, String(packet.channel + 1), String(packet.control), String(packet.value)]);
      for (const column of [0, 2, 3, 4]) {
        const geometry = await cells.nth(column).evaluate((cell) => {
          const range = document.createRange();
          range.selectNodeContents(cell);
          const bounds = cell.getBoundingClientRect();
          const rectangles = [...range.getClientRects()];
          return { lines: new Set(rectangles.map((rect) => Math.round(rect.top))).size, contained: rectangles.every((rect) => rect.left >= bounds.left && rect.right <= bounds.right) };
        });
        expect(geometry).toEqual({ lines: 1, contained: true });
      }
    }
    const overflow = await packets.evaluate((table) => [table, ...table.querySelectorAll('*')].filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1).map((element) => element.tagName));
    expect(overflow).toEqual([]);
  };
  await assertPacketGeometry();
  await packets.scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('packet-inspection-desktop.png') });
  await forge.locator('.show-kit-forge-header').scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-desktop.png') });
  await forge.getByRole('heading', { name: 'Compare candidates', exact: true }).scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-candidates.png') });
  const preparation = forge.getByRole('region', { name: 'A4 audition preparation' });
  await preparation.getByRole('button', { name: 'Review A4 preparation' }).click();
  await preparation.getByText('CC7 mapping evidence: incomplete', { exact: true }).click();
  const mappingTable = preparation.getByRole('table', { name: 'A4 native to CC7 mapping evidence' });
  await expect(mappingTable).toBeVisible();
  await expect(mappingTable).toContainText('osc1_level');
  await expect(mappingTable).toContainText('native_transport_scale_conflict');
  await expect(preparation).toContainText('A4 SEND remains blocked.');
  await mappingTable.scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('a4-transport-evidence-desktop.png') });

  await page.setViewportSize({ width: 600, height: 900 });
  await mappingTable.scrollIntoViewIfNeeded();
  expect(await preparation.evaluate((element) => element.getBoundingClientRect().right <= innerWidth)).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('a4-transport-evidence-narrow.png') });
  await forge.locator('.show-kit-forge-header').scrollIntoViewIfNeeded();
  await expect(forge).toBeVisible();
  const bounds = await forge.boundingBox();
  expect(bounds!.width).toBeLessThanOrEqual(600);
  await assertPacketGeometry();
  await packets.scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath('packet-inspection-narrow.png') });
  await page.screenshot({ path: testInfo.outputPath('show-kit-forge-narrow.png') });
  await page.setViewportSize({ width: 390, height: 844 });
  await mappingTable.scrollIntoViewIfNeeded();
  expect(await preparation.evaluate((element) => {
    const bounds = element.getBoundingClientRect();
    return bounds.left >= 0 && bounds.right <= innerWidth;
  })).toBe(true);
  expect(await mappingTable.locator('td').evaluateAll((cells) => cells.every((cell) => {
    const range = document.createRange(); range.selectNodeContents(cell);
    const bounds = cell.getBoundingClientRect();
    return [...range.getClientRects()].every((rect) => rect.left >= bounds.left - 1 && rect.right <= bounds.right + 1);
  }))).toBe(true);
  await page.screenshot({ path: testInfo.outputPath('a4-transport-evidence-mobile.png') });
  errors.assertClean();
});
