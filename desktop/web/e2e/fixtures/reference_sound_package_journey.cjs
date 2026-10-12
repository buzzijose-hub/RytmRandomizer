/* Offline packaged UI proof. Ownership/cleanup stay in offline_endurance_driver. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { expect } = require('@playwright/test');

function syntheticWav(frequency) {
  const count = 11025;
  const audio = Buffer.alloc(44 + count * 2);
  audio.write('RIFF'); audio.writeUInt32LE(audio.length - 8, 4); audio.write('WAVEfmt ', 8);
  audio.writeUInt32LE(16, 16); audio.writeUInt16LE(1, 20); audio.writeUInt16LE(1, 22);
  audio.writeUInt32LE(22050, 24); audio.writeUInt32LE(44100, 28);
  audio.writeUInt16LE(2, 32); audio.writeUInt16LE(16, 34); audio.write('data', 36);
  audio.writeUInt32LE(count * 2, 40);
  for (let index = 0; index < count; index++) audio.writeInt16LE(Math.round(16000 * Math.sin(2 * Math.PI * frequency * index / 22050)), 44 + index * 2);
  return audio;
}

function primeReferenceSources(repo, runRoot, python) {
  const source = `from pathlib import Path
import sys
from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
from rytm_randomizer.cockpit.library.store import LibraryStore
root, state = map(Path, sys.argv[1:])
store = LibraryStore(state / 'roaming' / 'rytm-randomizer' / 'library')
for device, name in [('analog_rytm_mk2','RYTM_RIO145_AR_CORE_RETURN_Kit.syx'),('analog_four_mk2','A4_RIO145_CORE_RETURN_Kit.syx')]:
    store.retain_source(decode_kit_capture_frame(device,(root / 'tests' / 'fixtures' / 'rio145' / name).read_bytes()), origin='file_import')
`;
  const result = spawnSync(python, ['-c', source, repo, path.join(runRoot, 'state')], {
    cwd: repo, env: { ...process.env, PYTHONPATH: repo, RYTM_RAND_MIDI_BACKEND: 'off' },
    windowsHide: true, encoding: 'utf8', timeout: 15_000,
  });
  assert.equal(result.status, 0, 'Isolated reference source priming failed');
}

async function exerciseReferenceSoundPackage({ page, latest, connected, processOperation, summary, save, reportRoot, record, digest }) {
  await connected();
  const panel = page.getByTestId('reference-sound-panel');
  await expect(panel).toBeVisible();
  await panel.getByRole('button', { name: 'Open reference sound', exact: true }).click();
  await panel.getByRole('button', { name: 'Load source library', exact: true }).click();
  await expect(panel.getByRole('combobox', { name: 'Source Library record', exact: true }).locator('option')).toHaveCount(2);
  const retained = [];
  for (const [device, target, field] of [['analog_rytm_mk2', 2, 'filter_frequency'], ['analog_four_mk2', 3, 'filter1_frequency']]) {
    summary.phase = `reference-import-${device}`; save();
    const audio = syntheticWav(440);
    await panel.getByLabel('Original WAV', { exact: true }).setInputFiles({ name: `${device}.wav`, mimeType: 'audio/wav', buffer: audio });
    await expect.poll(() => latest.reference_sound_session?.title).toBe(`${device}.wav`);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    assert.equal(latest.reference_sound_session.segment.original.sha256, digest(audio));
    await panel.getByLabel('Start frame', { exact: true }).fill('2205');
    await panel.getByLabel('Frame count', { exact: true }).fill('6615');
    await panel.getByRole('button', { name: 'Retain segment', exact: true }).click();
    await expect.poll(() => latest.reference_sound_session?.segment.start_frame).toBe(2205);
    assert.equal(latest.reference_sound_session.segment.frame_count, 6615);
    await panel.getByRole('combobox', { name: 'Device', exact: true }).selectOption(device);
    await panel.getByRole('combobox', { name: 'Source Library record', exact: true }).selectOption({ index: 1 });
    await panel.getByLabel(device === 'analog_four_mk2' ? 'Target track' : 'Target pad', { exact: true }).fill(String(target));
    await expect(panel.getByLabel(`Mutate ${field}`, { exact: true })).toBeEnabled();
    for (const control of await panel.getByRole('checkbox', { name: /^Mutate / }).all()) if (await control.isEnabled() && await control.isChecked()) await control.uncheck();
    await panel.getByLabel(`Mutate ${field}`, { exact: true }).check();
    summary.phase = `reference-generate-${device}`; save();
    await panel.getByRole('button', { name: 'Generate eight alternatives', exact: true }).click();
    await expect(panel.getByRole('group', { name: 'Native alternatives' }).getByRole('radio')).toHaveCount(8, { timeout: 65_000 });
    const generated = latest.reference_sound_session;
    assert.deepEqual(generated.context.parameters, [field]);
    assert.equal(generated.context.target, target);
    assert(generated.candidates.every(candidate => candidate.roundtrip_redecoded && candidate.hardware_send_validated === false && candidate.changes.every(change => change.parameter === field)));
    await panel.getByRole('button', { name: 'Favorite candidate', exact: true }).click();
    await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
    summary.phase = `reference-record-${device}`; save();
    await panel.getByLabel('Supplied candidate recording WAV (0.05-8s)', { exact: true }).setInputFiles({ name: 'synthetic-only-comparison.wav', mimeType: 'audio/wav', buffer: syntheticWav(880) });
    await expect.poll(() => latest.reference_sound_session?.recordings.length, { timeout: 65_000 }).toBe(1);
    assert.equal(latest.reference_sound_session.recordings[0].physical_validation, false);
    await expect(panel.getByRole('table', { name: /Supplied recording ranking/ })).toBeVisible();
    await panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true }).click();
    await expect.poll(() => latest.reference_sound_session?.refinements.length, { timeout: 65_000 }).toBe(1);
    await panel.getByLabel('Scratch KIT slot (1-128)', { exact: true }).fill('128');
    const beforeExport = latest.reference_sound_export;
    const intendedCandidate = latest.reference_sound_session.selected_candidate_id;
    await panel.getByRole('button', { name: 'Download .syx', exact: true }).click();
    await expect.poll(() => latest.reference_sound_export !== beforeExport &&
      latest.reference_sound_export?.candidate_id === intendedCandidate &&
      latest.reference_sound_export?.destination_slot === 127).toBe(true);
    const exported = latest.reference_sound_export;
    const frame = Buffer.from(exported.sysex_base64, 'base64');
    assert.equal(digest(frame), exported.sha256);
    assert.equal(frame[0], 0xf0); assert.equal(frame.at(-1), 0xf7);
    assert([...frame.subarray(1, -1)].every(byte => byte < 128));
    record({ kind: 'reference-native-export', device, sha256: exported.sha256, bytes: frame.length, destination_slot: 127, physical_validation: false });
    retained.push(structuredClone(latest.reference_sound_session));
    await expect(page.getByTestId('action-send')).toBeDisabled();
    const resource = processOperation('sample');
    assert(resource.free_ram_bytes > 6 * 1024 ** 3);
    record({ kind: 'reference-resource', device, resource });
  }
  summary.phase = 'reference-owned-backend-restart'; save();
  const recovery = processOperation('restart-backend');
  summary.restarts.push({ ...recovery, at: new Date().toISOString() });
  await connected();
  await panel.getByRole('button', { name: 'Refresh sessions', exact: true }).click();
  for (const expected of retained) {
    await panel.getByRole('combobox', { name: 'Retained session', exact: true }).selectOption(expected.session_id);
    await panel.getByRole('button', { name: 'Reopen session', exact: true }).click();
    await expect.poll(() => latest.reference_sound_session?.session_id).toBe(expected.session_id);
    assert.deepEqual(latest.reference_sound_session, expected);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    await expect(panel.getByLabel('Original reference playback')).toBeVisible();
    await expect(page.getByTestId('action-send')).toBeDisabled();
  }
  await page.setViewportSize({ width: 600, height: 900 });
  await panel.scrollIntoViewIfNeeded();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await page.screenshot({ path: path.join(reportRoot, 'reference-sound-narrow.png') });
  summary.reference_sound = { devices: retained.map(session => session.context.device_id), sessions: retained.map(session => ({ session_id: session.session_id, original_sha256: session.segment.original.sha256, segment_sha256: session.segment.sha256, source_sha256: session.context.source_sha256, candidate_count: session.candidates.length, favorite_count: session.favorites.length, recording_count: session.recordings.length, refinement_count: session.refinements.length })), synthetic_audio_only: true, physical_validation: false };
}

module.exports = { primeReferenceSources, exerciseReferenceSoundPackage, syntheticWav };
