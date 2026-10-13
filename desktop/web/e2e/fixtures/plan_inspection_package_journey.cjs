/* Read-only packaged rehearsal proof; canonical driver owns launch and cleanup. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { expect } = require('@playwright/test');

function assertExactPad2Plan(plan, candidate) {
  const allowed = { flt: 74, amp_decay: 80, overdrive: 81, reverb: 83 };
  const deltas = candidate.pad_deltas.filter(delta => delta.changed_keys.length);
  assert(deltas.length > 0 && deltas.every(delta => delta.pad_id === 2));
  const expected = [...deltas].sort((left, right) => left.pad_id - right.pad_id).flatMap(delta =>
    [...delta.changed_keys].sort().map(parameter => {
      assert(Object.hasOwn(allowed, parameter));
      const value = delta.proposed_params[parameter];
      assert(Number.isInteger(value) && value >= 0 && value <= 127);
      return { pad_id: delta.pad_id, parameter, channel: delta.pad_id - 1, control: allowed[parameter], value };
    }));
  assert(plan.ready);
  assert.equal(plan.candidate_id, candidate.candidate_id);
  assert.deepEqual(plan.blocked_reasons, []);
  assert.deepEqual(plan.packets, expected);
  return expected;
}

async function exercisePlanInspectionPackage({ page, latest, connected, processOperation, summary, save, reportRoot, record, digest }) {
  const checked = (name, detail = {}) => {
    const result = { name, passed: true, ...detail };
    summary.plan_inspection.checks.push(result); record({ kind: 'plan-inspection-check', ...result }); save();
  };
  summary.plan_inspection = { checks: [], screenshots: [], resources: [], physical_validation: false };
  const sample = phase => {
    const resource = processOperation('sample');
    const privateBytes = resource.processes.reduce((total, item) => total + item.private_bytes, 0);
    assert(resource.free_ram_bytes > 6 * 1024 ** 3, 'Resource floor reached; stop safely');
    assert(privateBytes < 3 * 1024 ** 3, 'Owned app private-memory ceiling reached');
    const measurement = { phase, private_bytes: privateBytes, process_count: resource.processes.length, handles: resource.processes.reduce((total, item) => total + item.handles, 0), free_ram_bytes: resource.free_ram_bytes };
    summary.plan_inspection.resources.push(measurement); record({ kind: 'plan-inspection-resource', ...measurement }); save();
  };
  await connected();
  sample('connected');
  await page.setViewportSize({ width: 1440, height: 1000 });
  const forge = page.getByTestId('show-kit-forge');
  const scope = page.getByTestId('mutation-parameters-panel');
  const rail = page.getByTestId('safety-rail');
  await page.getByTestId('profile-chips').getByRole('button').first().click();
  await forge.getByLabel('Bank name', { exact: true }).fill('One Pad2 inspection');
  await forge.getByRole('button', { name: 'Create show bank', exact: true }).click();
  await expect(forge.getByRole('button', { name: 'Refresh source files', exact: true })).toBeEnabled();
  await forge.getByRole('button', { name: 'Refresh source files', exact: true }).click();
  await forge.getByRole('combobox', { name: 'Rytm source file', exact: true }).selectOption({ index: 1 });
  await forge.getByRole('combobox', { name: 'Analog Four source file', exact: true }).selectOption({ index: 1 });
  const slots = forge.getByLabel('Source hardware slot (1–128)');
  await slots.nth(0).fill('20'); await slots.nth(1).fill('20');
  await forge.getByRole('button', { name: 'Adopt source files', exact: true }).click();
  await expect(forge.getByRole('heading', { name: 'Forge candidate pairs', exact: true })).toBeVisible();
  await scope.getByRole('button', { name: 'Pad 2 rehearsal', exact: true }).click();
  await forge.getByLabel('Candidate count', { exact: true }).selectOption('1');
  await forge.getByLabel('Starting seed', { exact: true }).fill('3000');
  const depth = forge.getByRole('slider');
  await depth.press('Home');
  for (let step = 0; step < 10; step++) await depth.press('ArrowRight');
  await expect(depth).toHaveValue('0.1');
  await forge.getByRole('button', { name: 'Forge 1 candidate pairs', exact: true }).click();
  const card = forge.getByRole('article', { name: 'Candidate 1', exact: true });
  await expect(card).toBeVisible();
  const bank = latest.show_bank_changed.show_bank.banks.find(value => value.bank_id === latest.show_bank_changed.show_bank.active_bank_id);
  const entry = bank.entries.find(value => value.entry_id === bank.active_entry_id);
  const candidate = entry.candidates[0];
  assert.equal(candidate.recipe.depth, 0.1);
  assert.equal(candidate.recipe.seed, 3000);
  assert.deepEqual(candidate.analog_four_candidate.values, []);
  assert.equal(candidate.analog_four_candidate.semantic_fingerprint, candidate.source_a4_fingerprint);
  assert.equal(candidate.analog_four_candidate.sysex.frame_sha256, entry.analog_four_source.sysex.frame_sha256);
  const deltas = candidate.rytm_candidate.pad_deltas.filter(delta => delta.changed_keys.length);
  assert(deltas.length > 0 && deltas.every(delta => delta.pad_id === 2 && delta.changed_keys.every(key => ['flt', 'amp_decay', 'overdrive', 'reverb'].includes(key))));
  await card.getByRole('button', { name: 'Select for audition', exact: true }).click();
  await forge.getByRole('button', { name: 'Preview Rytm', exact: true }).click();
  await forge.getByRole('button', { name: 'Prepare exact plan', exact: true }).click();
  await expect.poll(() => latest.send_plan_changed?.send_plan?.ready).toBe(true);
  const plan = structuredClone(latest.send_plan_changed.send_plan);
  const expectedPackets = assertExactPad2Plan(plan, candidate.rytm_candidate);
  const table = rail.getByRole('table', { name: 'Exact prepared Rytm packets', exact: true });
  await expect(table).toBeVisible();
  await expect(rail).toContainText(plan.plan_id);
  const rows = await table.locator('tbody tr').allTextContents();
  assert.equal(rows.length, plan.packets.length);
  for (let index = 0; index < plan.packets.length; index++) {
    const packet = plan.packets[index];
    const cells = await table.locator('tbody tr').nth(index).locator('th,td').allTextContents();
    assert.deepEqual(cells.map(value => value.trim()), [String(packet.pad_id), packet.parameter, String(packet.channel + 1), String(packet.control), String(packet.value)]);
  }
  await expect(rail.getByText('Hardware Off', { exact: true })).toBeVisible();
  checked('exact-server-packets-before-arm-four-control-scope', { plan_id: plan.plan_id, packets: plan.packets, depth: 0.1, seed: 3000 });
  sample('prepared');
  for (const width of [1440, 600]) {
    await page.setViewportSize({ width, height: 1000 });
    await table.scrollIntoViewIfNeeded();
    assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    const name = `plan-inspection-${width}.png`;
    await page.screenshot({ path: path.join(reportRoot, name) });
    summary.plan_inspection.screenshots.push({ name, sha256: digest(fs.readFileSync(path.join(reportRoot, name))), width });
  }
  checked('desktop-and-narrow-plan-inspection-no-document-overflow');
  await scope.getByRole('button', { name: 'Select none', exact: true }).click();
  await expect.poll(() => latest.send_plan_changed?.send_plan).toBeNull();
  await expect(table).toHaveCount(0);
  await expect(page.getByTestId('action-send')).toBeDisabled();
  checked('scope-change-removes-stale-plan-and-keeps-send-disabled');
  await scope.getByRole('button', { name: 'Pad 2 rehearsal', exact: true }).click();
  await card.getByRole('button', { name: 'Select for audition', exact: true }).click();
  await forge.getByRole('button', { name: 'Preview Rytm', exact: true }).click();
  await forge.getByRole('button', { name: 'Prepare exact plan', exact: true }).click();
  await expect.poll(() => latest.send_plan_changed?.send_plan?.ready).toBe(true);
  const beforeRestart = structuredClone(latest.send_plan_changed.send_plan);
  assert.deepEqual(assertExactPad2Plan(beforeRestart, candidate.rytm_candidate), expectedPackets);
  await expect(table).toBeVisible();
  await expect(rail).toContainText(beforeRestart.plan_id);
  checked('ready-visible-plan-immediately-before-owned-restart', { plan_id: beforeRestart.plan_id });
  const recovery = processOperation('restart-backend');
  assert(recovery.token_rotated && recovery.shell_preserved);
  summary.restarts.push({ ...recovery, at: new Date().toISOString() }); save();
  await connected();
  await expect.poll(() => latest.send_plan_changed?.send_plan).toBeNull();
  await expect(table).toHaveCount(0);
  await expect(page.getByTestId('action-send')).toBeDisabled();
  checked('owned-restart-remains-disarmed-without-stale-plan');
  sample('restarted');
}

module.exports = { exercisePlanInspectionPackage, assertExactPad2Plan };
