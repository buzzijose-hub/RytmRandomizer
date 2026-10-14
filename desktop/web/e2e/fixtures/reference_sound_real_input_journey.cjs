/* Explicit private-input QA only. The parent owns launch, restart and cleanup.
 * Supplied historical takes exercise recording quality and persistence; they
 * are not claimed to be auditions of the new full-scope generated candidate.
 * validateRealInputConfig({ qa_only: true, source, reference, take2, take3 },
 *   { repo, runRoot }) requires { path: absolutePrivatePath, sha256 } per input.
 * primeReferenceRealInputSources(repo, runRoot, python, config) retains only KIT
 * bytes in the parent's isolated LibraryStore. exercise returns an exact session
 * payload; call reopenReferenceSoundRealInput({ ...args, expected }) AFTER the
 * parent's owned-backend restart. No input paths belong in committed config.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { spawnSync } = require('node:child_process');

const INPUT_KEYS = Object.freeze(['source', 'reference', 'take2', 'take3']);
const DIRECTIONS = Object.freeze(['closest', 'darker', 'brighter', 'metallic', 'percussive', 'atmospheric', 'deeper', 'animated']);
const RATE = 44100;
const validatedConfigs = new WeakSet();
const sha256 = bytes => createHash('sha256').update(bytes).digest('hex');
const inside = (root, target) => {
  const relative = path.relative(root, target);
  return relative === '' || (!path.isAbsolute(relative) && relative !== '..' && !relative.startsWith(`..${path.sep}`));
};

function requireAbsolute(value) {
  assert(typeof value === 'string' && path.isAbsolute(value) && !value.includes('\0'), 'QA paths must be absolute');
  return path.resolve(value);
}

// Resolve existing ancestors too: a symlinked state/library must not escape.
function resolvedLocation(value) {
  const target = requireAbsolute(value);
  if (fs.existsSync(target)) return fs.realpathSync(target);
  return path.join(resolvedLocation(path.dirname(target)), path.basename(target));
}

function inGitCheckout(filename) {
  let current = path.dirname(filename);
  for (;;) {
    if (fs.existsSync(path.join(current, '.git'))) return true;
    const parent = path.dirname(current);
    if (parent === current) return false;
    current = parent;
  }
}

function inputSnapshot(filename, expected, maximum) {
  assert(/^[a-f0-9]{64}$/.test(expected), 'Expected SHA-256 must be explicit lowercase hex');
  const stat = fs.statSync(filename);
  assert(stat.isFile() && stat.size > 0 && stat.size <= maximum, 'Input must be a bounded regular file');
  const bytes = fs.readFileSync(filename);
  assert.equal(sha256(bytes), expected, 'Private input hash mismatch');
  return { bytes, snapshot: Object.freeze({ size: stat.size, mtimeMs: stat.mtimeMs, ctimeMs: stat.ctimeMs, mode: stat.mode, ino: stat.ino, dev: stat.dev, sha256: expected }) };
}

function wavInfo(bytes) {
  assert(bytes.length >= 44 && bytes.toString('ascii', 0, 4) === 'RIFF' && bytes.toString('ascii', 8, 12) === 'WAVE', 'Expected original PCM WAV');
  const end = bytes.readUInt32LE(4) + 8;
  assert.equal(end, bytes.length, 'Truncated or trailing WAV bytes');
  let format, dataSize, dataOffset;
  for (let offset = 12; offset < end;) {
    assert(offset + 8 <= end, 'Truncated WAV chunk');
    const size = bytes.readUInt32LE(offset + 4);
    const body = offset + 8;
    assert(body + size <= end, 'WAV chunk exceeds input');
    const name = bytes.toString('ascii', offset, offset + 4);
    if (name === 'fmt ') {
      assert(format === undefined && size >= 16, 'Invalid WAV format chunk');
      assert.equal(bytes.readUInt16LE(body), 1, 'Only unchanged integer PCM inputs are accepted');
      const channels = bytes.readUInt16LE(body + 2), sample_rate = bytes.readUInt32LE(body + 4);
      const bits = bytes.readUInt16LE(body + 14), block = bytes.readUInt16LE(body + 12);
      assert([1, 2].includes(channels) && [16, 24, 32].includes(bits), 'Unsupported PCM layout');
      assert.equal(block, channels * bits / 8);
      assert.equal(bytes.readUInt32LE(body + 8), sample_rate * block);
      format = { channels, sample_rate, sample_width: bits / 8, block };
    } else if (name === 'data') {
      assert(dataSize === undefined, 'Ambiguous multiple WAV data chunks');
      dataSize = size;
      dataOffset = body;
    }
    offset = body + size + (size % 2);
    assert(offset <= end, 'Missing WAV chunk padding');
  }
  assert(format && dataSize > 0 && dataSize % format.block === 0, 'Missing or partial PCM frames');
  assert(dataSize / format.block / format.sample_rate <= 120, 'Original WAV exceeds the existing 120s boundary');
  return Object.freeze({ channels: format.channels, sample_rate: format.sample_rate, sample_width: format.sample_width, frame_count: dataSize / format.block, data_offset: dataOffset });
}

function assertSegmentBounds(info, start, count) {
  assert(Number.isSafeInteger(start) && start >= 0 && Number.isSafeInteger(count), 'Segment requires exact integer frames');
  assert(count >= Math.ceil(info.sample_rate * 0.05) && count <= info.sample_rate * 8 && start + count <= info.frame_count, 'Segment outside original or 0.05-8s bounds');
}

function assertOwnedLocations(repo, runRoot) {
  const checkout = fs.realpathSync(requireAbsolute(repo));
  const owned = fs.realpathSync(requireAbsolute(runRoot));
  assert(fs.statSync(owned).isDirectory() && !inside(checkout, owned) && !inside(owned, checkout), 'QA root must be separate from checkout');
  for (const key of ['APPDATA', 'LOCALAPPDATA', 'XDG_CONFIG_HOME', 'USERPROFILE', 'HOME']) {
    if (process.env[key] && path.isAbsolute(process.env[key])) assert(!inside(owned, resolvedLocation(process.env[key])), 'QA root cannot contain user data/home');
  }
  const state = path.join(owned, 'state');
  for (const directory of [state, path.join(state, 'roaming'), path.join(state, 'roaming', 'rytm-randomizer'), path.join(state, 'roaming', 'rytm-randomizer', 'library')]) {
    assert.equal(resolvedLocation(directory), directory, 'Owned state must not redirect through symlinks');
  }
  return { repo: checkout, runRoot: owned, state };
}

function validateRealInputConfig(raw, locations) {
  assert(raw && raw.qa_only === true, 'Real inputs require explicit QA-only configuration');
  const owned = assertOwnedLocations(locations.repo, locations.runRoot);
  const inputs = {};
  for (const key of INPUT_KEYS) {
    const item = raw[key];
    assert(item && typeof item.path === 'string' && typeof item.sha256 === 'string', 'Every real input needs path and expected hash');
    const requested = requireAbsolute(item.path);
    const filename = fs.realpathSync(requested);
    assert(!inside(owned.repo, filename) && !inGitCheckout(filename) && !inGitCheckout(requested), 'Private inputs must be outside Git checkouts');
    assert(!inside(owned.runRoot, filename) && !inside(path.dirname(filename), owned.runRoot), 'Original inputs and QA output must be disjoint');
    assert(path.extname(filename).toLowerCase() === (key === 'source' ? '.syx' : '.wav'), 'Unexpected input extension');
    const { bytes, snapshot } = inputSnapshot(filename, item.sha256, (key === 'source' ? 2 : 16) * 1024 ** 2);
    let audio = {};
    if (key !== 'source') {
      const info = wavInfo(bytes);
      assert.equal(info.sample_rate, RATE, 'This real-input exercise requires original 44100Hz PCM');
      const start = key === 'take3' ? 264600 : 0;
      const count = key === 'reference' ? 352800 : key === 'take3' ? 176400 : info.frame_count;
      assertSegmentBounds(info, start, count);
      const block = info.channels * info.sample_width;
      // Hash a read-only view of the exact original interleaved samples.
      audio = { info, selection: Object.freeze({ start_frame: start, frame_count: count,
        pcm_sha256: sha256(bytes.subarray(info.data_offset + start * block, info.data_offset + (start + count) * block)) }) };
    }
    inputs[key] = Object.freeze({ path: filename, sha256: item.sha256, snapshot, ...audio });
  }
  assert.equal(new Set(INPUT_KEYS.map(key => inputs[key].path)).size, 4, 'Use distinct original inputs');
  const config = Object.freeze({ qa_only: true, ...owned, ...inputs });
  validatedConfigs.add(config);
  return config;
}

function assertRealInputsUnchanged(config) {
  assert(validatedConfigs.has(config), 'Pass the config returned by validateRealInputConfig');
  assert.deepEqual(assertOwnedLocations(config.repo, config.runRoot), { repo: config.repo, runRoot: config.runRoot, state: config.state });
  for (const key of INPUT_KEYS) {
    const item = config[key];
    assert.equal(fs.realpathSync(item.path), item.path, 'Original path was redirected');
    assert.deepEqual(inputSnapshot(item.path, item.sha256, (key === 'source' ? 2 : 16) * 1024 ** 2).snapshot, item.snapshot, 'Original input metadata changed');
  }
}

function primeReferenceRealInputSources(repo, runRoot, python, config, run = spawnSync) {
  assertRealInputsUnchanged(config);
  assert.equal(fs.realpathSync(requireAbsolute(repo)), config.repo);
  assert.equal(fs.realpathSync(requireAbsolute(runRoot)), config.runRoot);
  assert(typeof python === 'string' && python.length > 0, 'Parent must supply its primary Python CLI');
  const source = `from pathlib import Path
from hashlib import sha256
import json, sys
from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
from rytm_randomizer.cockpit.library.store import LibraryStore
request = json.load(sys.stdin)
original_path = Path(request['path'])
original = original_path.read_bytes()
assert sha256(original).hexdigest() == request['sha256']
store = LibraryStore(Path(sys.argv[1]) / 'roaming' / 'rytm-randomizer' / 'library')
record = store.retain_source(decode_kit_capture_frame('analog_four_mk2', original), origin='file_import')
assert store.read_source_frame(record.record_id) == original
assert original_path.read_bytes() == original
print(json.dumps(dict(record_id=record.record_id, source_sha256=sha256(original).hexdigest(), hardware_validation=False)))
`;
  try {
    const result = run(python, ['-c', source, config.state], {
      cwd: config.repo, input: JSON.stringify({ path: config.source.path, sha256: config.source.sha256 }),
      encoding: 'utf8', windowsHide: true, timeout: 15_000,
      env: { ...process.env, PYTHONPATH: config.repo, PYTHONDONTWRITEBYTECODE: '1',
        RYTM_RAND_MIDI_BACKEND: 'off', RYTM_RAND_UPDATES: 'off', RYTM_RAND_UPDATE_BEACON: 'off',
        APPDATA: path.join(config.state, 'roaming'), LOCALAPPDATA: path.join(config.state, 'local'),
        HOME: config.state, USERPROFILE: config.state, XDG_CONFIG_HOME: path.join(config.state, 'config'),
        OPENBLAS_NUM_THREADS: '1', OMP_NUM_THREADS: '1', MKL_NUM_THREADS: '1', NUMBA_NUM_THREADS: '1' },
    });
    assert.equal(result.status, 0, 'Isolated real source priming failed');
    const retained = JSON.parse(result.stdout.trim());
    assert.match(retained.record_id, /^[a-f0-9]{16}$/);
    assert.equal(retained.source_sha256, config.source.sha256);
    assert.equal(retained.hardware_validation, false);
    return retained;
  } finally { assertRealInputsUnchanged(config); }
}

function supportedParameters(controls) {
  assert(Array.isArray(controls) && controls.length > 0 && controls.length <= 256, 'Missing source-bound controls');
  assert.equal(new Set(controls.map(control => control.parameter)).size, controls.length, 'Duplicate scope field');
  const parameters = [];
  for (const control of controls) {
    assert.match(control.parameter, /^[a-z][a-z0-9_]*$/);
    assert.equal(control.output_authority, 'local-file-only');
    assert.equal(control.send_supported, false);
    assert(Array.isArray(control.reasons));
    const supported = control.domain !== null && control.domain !== undefined && control.reasons.length === 0;
    assert.equal(control.mutable, supported, 'Scope eligibility disagrees with protection/domain');
    if (supported) parameters.push(control.parameter);
  }
  assert(parameters.includes('noise_fade'), 'Actual source must support current-model Noise Fade');
  return parameters;
}

async function selectSupportedScope(panel, controls) {
  const parameters = supportedParameters(controls);
  for (const control of controls) {
    const mutate = panel.getByLabel(`Mutate ${control.parameter}`, { exact: true });
    const lock = panel.getByLabel(`Lock ${control.parameter}`, { exact: true });
    assert.equal(await mutate.isEnabled(), control.mutable, 'UI scope differs from source control eligibility');
    assert.equal(await lock.isEnabled(), control.mutable);
    if (control.mutable) {
      await lock.uncheck();
      await mutate.check();
      assert.equal(await mutate.isChecked(), true);
      assert.equal(await lock.isChecked(), false);
    } else {
      assert.equal(await mutate.isChecked(), false, 'Protected field must not be selected');
      assert.equal(await lock.isChecked(), true, 'Protected field must remain locked');
    }
  }
  return parameters;
}

function assertNoiseFadeNative(value) {
  assert.equal(value.units, 'centered-64-native-u7');
  const pairs = 'source_display' in value && !('proposed_value' in value)
    ? [['source_display', 'source_value']]
    : [['source_display', 'source_value'], ['proposed_display', 'proposed_value'], ['rendered_display', 'rendered_value']];
  for (const [display, encoded] of pairs) {
    assert(typeof value[display] === 'string' && /^-?\d+$/.test(value[display]), 'Noise Fade requires explicit signed native units');
    const signed = Number(value[display]);
    assert(Number.isInteger(signed) && signed >= -64 && signed <= 63, 'Noise Fade intent outside -64..63 BEFORE conversion');
    assert(Number.isInteger(value[encoded]) && value[encoded] >= 0 && value[encoded] <= 127);
    assert.equal(value[encoded], signed + 64, 'Noise Fade centered conversion disagrees');
  }
}

function assertGeneratedSession(session, config, controls, parameters) {
  const context = session.context;
  assert.equal(context.device_id, 'analog_four_mk2');
  assert.equal(context.target, 1);
  assert.equal(context.source_sha256, config.source.sha256);
  assert.equal(context.segment_sha256, session.segment.sha256);
  assert.deepEqual([...context.parameters].sort(), [...parameters].sort());
  assert.deepEqual(context.locks, []);
  if (parameters.includes('noise_fade')) assert.equal(context.inference_version, 2);
  assert.equal(session.candidates.length, 8);
  assert.deepEqual(session.candidates.map(candidate => candidate.direction), DIRECTIONS);
  assert.equal(new Set(session.candidates.map(candidate => candidate.candidate_id)).size, 8);
  assertNoiseFadeNative(controls.find(control => control.parameter === 'noise_fade'));
  const allowedOffsets = new Set(controls.filter(control => parameters.includes(control.parameter)).flatMap(control => control.offsets));
  let fadeChanges = 0;
  for (const candidate of session.candidates) {
    assert.equal(candidate.device_id, context.device_id);
    assert.equal(candidate.target, 1);
    assert.equal(candidate.source_sha256, config.source.sha256);
    assert.equal(candidate.hardware_send_validated, false);
    assert.equal(candidate.output_authority, 'local-file-only');
    assert.equal(candidate.roundtrip_redecoded, true);
    const intended = new Set(candidate.intended_unpacked_offsets);
    assert([...intended].every(offset => allowedOffsets.has(offset)), 'Candidate intended bytes escaped selected controls');
    assert(candidate.changed_unpacked_offsets.every(offset => intended.has(offset)), 'Candidate escaped native byte scope');
    for (const change of candidate.changes) {
      const control = controls.find(item => item.parameter === change.parameter);
      assert(control && control.mutable && parameters.includes(change.parameter), 'Candidate mutated protected/out-of-scope field');
      assert.equal(change.source_value, control.source_value);
      assert.equal(change.units, control.units);
      assert.deepEqual(change.offsets, control.offsets);
      if (change.parameter === 'noise_fade') { assertNoiseFadeNative(change); fadeChanges++; }
    }
  }
  assert(fadeChanges > 0, 'Noise Fade bound check must exercise actual changes');
}

function assertUnqualifiedReference(analysis) {
  const diagnostics = analysis.diagnostics;
  assert.equal(diagnostics.qualified_pitch_hz, null, 'Spectral peak must not become a qualified fundamental');
  assert(['unpitched', 'uncertain'].includes(diagnostics.pitch_status));
  assert(Number.isFinite(diagnostics.spectral_peak_hz));
  assert.equal(diagnostics.spectral_peak_hz.toFixed(3), '82.095', 'Retained real-reference Welch peak changed');
}

function assertRecordingHold(recording, referenceAnalysis) {
  assertUnqualifiedReference(referenceAnalysis);
  assert.equal(recording.physical_validation, false);
  const comparison = recording.pitch_comparison;
  assert.equal(comparison.support_status, 'held');
  assert.equal(comparison.delta_cents, null);
  assert.equal(comparison.octave_difference, null);
  assert(comparison.blockers.length > 0 && !comparison.blockers.includes('pitch_mismatch'), 'Unqualified pitch cannot establish mismatch');
  assert(comparison.blockers.some(code => ['quiet_audio', 'pitch_uncertain'].includes(code)), 'Expected quiet/uncertain refinement hold');
  const quality = [...referenceAnalysis.diagnostics.refinement_blockers, ...recording.features.diagnostics.refinement_blockers];
  assert(quality.every(code => comparison.blockers.includes(code)), 'Comparison dropped quality blockers');
}

function assertSegmentIdentity(segment, input, start, count) {
  assertSegmentBounds(input.info, start, count);
  assert.equal(segment.original.sha256, input.sha256);
  for (const key of ['sample_rate', 'channels', 'sample_width', 'frame_count']) assert.equal(segment.original[key], input.info[key]);
  assert.equal(segment.start_frame, start);
  assert.equal(segment.frame_count, count);
  assert.match(segment.sha256, /^[a-f0-9]{64}$/);
}

async function assertPlayback(expect, panel, label, expectedSha, expectedPcm) {
  const audio = panel.getByLabel(label, { exact: true });
  await expect(audio).toBeVisible();
  const playback = () => audio.evaluate(async element => {
    if (!element.src.startsWith('blob:')) return null;
    const bytes = await (await fetch(element.src)).arrayBuffer();
    const hash = async data => Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', data)), byte => byte.toString(16).padStart(2, '0')).join('');
    const view = new DataView(bytes);
    for (let offset = 12; offset + 8 <= bytes.byteLength;) {
      const size = view.getUint32(offset + 4, true), body = offset + 8;
      if (body + size > bytes.byteLength) return null;
      if (view.getUint32(offset, false) === 0x64617461) return { sha256: await hash(bytes), pcm_sha256: await hash(new Uint8Array(bytes, body, size)) };
      offset = body + size + size % 2;
    }
    return null;
  });
  await expect.poll(async () => (await playback())?.sha256).toBe(expectedSha);
  if (expectedPcm !== undefined) assert.equal((await playback()).pcm_sha256, expectedPcm, 'Playback must preserve the exact original PCM range');
}

async function assertReferencePresentation(expect, panel, session, config) {
  await assertPlayback(expect, panel, 'Original reference playback', config.reference.sha256);
  await assertPlayback(expect, panel, 'Retained reference segment playback', session.segment.sha256, config.reference.selection.pcm_sha256);
  await expect(panel.getByLabel('Start frame', { exact: true })).toHaveValue('0');
  await expect(panel.getByLabel('Frame count', { exact: true })).toHaveValue('352800');
  await expect(panel.getByText(`Retained frames 0:352800 / SHA-256 ${session.segment.sha256}`, { exact: true })).toBeVisible();
}

async function exerciseReferenceSoundRealInput({ page, latest, connected, summary, save, reportRoot, record, digest, config }) {
  assertRealInputsUnchanged(config);
  assert(inside(config.runRoot, resolvedLocation(reportRoot)), 'Reports must stay in the owned QA root');
  const { expect } = require('@playwright/test');
  const phase = name => { summary.phase = `reference-real-input-${name}`; save(); };
  try {
    phase('connect');
    await connected();
    await expect(page.getByTestId('action-send')).toBeDisabled();
    const panel = page.getByTestId('reference-sound-panel');
    await expect(panel).toBeVisible();
    const open = panel.getByRole('button', { name: 'Open reference sound', exact: true });
    if (await open.isVisible()) await open.click();
    phase('import-original');
    const previous = latest.reference_sound_session;
    await panel.getByLabel('Original WAV', { exact: true }).setInputFiles(config.reference.path);
    await expect.poll(() => latest.reference_sound_session !== previous && latest.reference_sound_session?.segment.original.sha256 === config.reference.sha256).toBe(true);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    await panel.getByLabel('Start frame', { exact: true }).fill('0');
    await panel.getByLabel('Frame count', { exact: true }).fill('352800');
    await panel.getByRole('button', { name: 'Retain segment', exact: true }).click();
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    assertSegmentIdentity(latest.reference_sound_session.segment, config.reference, 0, 352800);
    await assertReferencePresentation(expect, panel, latest.reference_sound_session, config);
    phase('exact-source-scope');
    await panel.getByRole('button', { name: 'Load source library', exact: true }).click();
    await expect.poll(() => latest.library_records?.some(item => item.device_id === 'analog_four_mk2' && item.source_frame?.sha256 === config.source.sha256)).toBe(true);
    const sources = latest.library_records.filter(item => item.device_id === 'analog_four_mk2' && item.source_frame?.sha256 === config.source.sha256);
    assert.equal(sources.length, 1, 'Exact original source must identify one LibraryStore record');
    await panel.getByRole('combobox', { name: 'Device', exact: true }).selectOption('analog_four_mk2');
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    const previousControls = latest.reference_sound_controls;
    await panel.getByRole('combobox', { name: 'Source Library record', exact: true }).selectOption(sources[0].record_id);
    await expect.poll(() => latest.reference_sound_controls !== previousControls && latest.reference_sound_controls?.length > 0).toBe(true);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    await expect(panel.getByLabel('Target track', { exact: true })).toHaveValue('1');
    const controls = structuredClone(latest.reference_sound_controls);
    const parameters = await selectSupportedScope(panel, controls);
    phase('generate');
    await panel.getByRole('button', { name: 'Generate eight alternatives', exact: true }).click();
    await expect(panel.getByRole('group', { name: 'Native alternatives' }).getByRole('radio')).toHaveCount(8, { timeout: 65_000 });
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    assertGeneratedSession(latest.reference_sound_session, config, controls, parameters);
    assertUnqualifiedReference(latest.reference_sound_session.analysis);
    const reference = latest.reference_sound_session;
    assert.equal(reference.analysis.features.audio_sha256, reference.segment.sha256);
    assert.equal(reference.analysis.diagnostics.audio_sha256, reference.segment.sha256);
    assert.equal(reference.analysis.diagnostics.sample_rate, RATE);
    assert.equal(reference.analysis.diagnostics.start_sample, 0);
    assert.equal(reference.analysis.diagnostics.sample_count, 352800);
    const closest = latest.reference_sound_session.candidates.find(candidate => candidate.direction === 'closest');
    await panel.getByRole('group', { name: 'Native alternatives' }).getByRole('radio').nth(0).check();
    await expect.poll(() => latest.reference_sound_session?.selected_candidate_id).toBe(closest.candidate_id);
    await panel.getByRole('button', { name: 'Favorite candidate', exact: true }).click();
    await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
    assert(latest.reference_sound_session.favorites.includes(closest.candidate_id));
    const recordTake = async (key, start, count, explicit) => {
      phase(`record-${key}`);
      await panel.getByLabel('Audition start frame (optional)', { exact: true }).fill(explicit ? String(start) : '');
      await panel.getByLabel('Audition frame count (optional)', { exact: true }).fill(explicit ? String(count) : '');
      const before = latest.reference_sound_session.recordings.length;
      await panel.getByLabel('Supplied candidate recording WAV (0.05-8s)', { exact: true }).setInputFiles(config[key].path);
      await expect.poll(() => latest.reference_sound_session?.recordings.length, { timeout: 65_000 }).toBe(before + 1);
      await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
      const session = latest.reference_sound_session, recording = session.recordings.at(-1);
      assertSegmentIdentity(recording.segment, config[key], start, count);
      assert.equal(recording.audio_sha256, recording.segment.sha256);
      assert.equal(recording.features.features.audio_sha256, recording.audio_sha256);
      assert.equal(recording.features.diagnostics.audio_sha256, recording.audio_sha256);
      assert.equal(recording.features.diagnostics.sample_rate, RATE);
      assert.equal(recording.features.diagnostics.start_sample, 0);
      assert.equal(recording.features.diagnostics.sample_count, count);
      assert.equal(recording.candidate_id, closest.candidate_id);
      assert.equal(recording.candidate_sha256, closest.frame_sha256);
      assertRecordingHold(recording, session.analysis);
      await expect(panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true })).toBeDisabled();
      await expect(panel.getByRole('table', { name: 'Controlled audition diagnostics', exact: true })).toBeVisible();
      await expect(panel.getByText(new RegExp(`Analyzed audition: frames ${start}:${count} /`))).toBeVisible();
      await expect(panel.getByText(new RegExp(`original SHA-256 ${config[key].sha256}`))).toBeVisible();
      await assertPlayback(expect, panel, 'Supplied candidate recording playback', recording.audio_sha256, config[key].selection.pcm_sha256);
      await expect(page.getByTestId('action-send')).toBeDisabled();
      record({ kind: 'reference-real-input-recording', input: key, original_sha256: config[key].sha256, segment_sha256: recording.audio_sha256, start_frame: start, frame_count: count, pitch_comparison: recording.pitch_comparison, hardware_validation: false });
    };
    await recordTake('take2', 0, config.take2.info.frame_count, false);
    await recordTake('take3', 264600, 176400, true);
    const expected = structuredClone(latest.reference_sound_session);
    assert.equal(expected.refinements.length, 0);
    await assertReferencePresentation(expect, panel, expected, config);
    await expect(panel.getByRole('table', { name: /Supplied recording ranking/ })).toBeVisible();
    await panel.scrollIntoViewIfNeeded();
    const screenshot = path.join(reportRoot, 'reference-sound-real-input.png');
    await page.screenshot({ path: screenshot });
    summary.reference_sound_real_input = { session_id: expected.session_id, source_sha256: config.source.sha256, original_sha256: config.reference.sha256,
      segment_sha256: expected.segment.sha256, parameters, candidate_count: 8, favorite_count: expected.favorites.length, recording_count: expected.recordings.length,
      hardware_validation: false, candidate_audition_association_validated: false,
      purpose: 'recording-quality and persistence exercise, not sound-match proof',
      synthetic_audio_only: false, reopened_exact: false, screenshot_sha256: digest(fs.readFileSync(screenshot)) };
    phase('await-parent-restart');
    return expected;
  } finally { assertRealInputsUnchanged(config); }
}

async function reopenReferenceSoundRealInput({ page, latest, connected, summary, save, record, config, expected }) {
  assertRealInputsUnchanged(config);
  assert(expected && expected.context?.source_sha256 === config.source.sha256 && expected.segment.original.sha256 === config.reference.sha256, 'Reopen requires the exact exercise payload');
  const { expect } = require('@playwright/test');
  try {
    summary.phase = 'reference-real-input-reopen'; save();
    await connected();
    await expect(page.getByTestId('action-send')).toBeDisabled();
    const panel = page.getByTestId('reference-sound-panel');
    const open = panel.getByRole('button', { name: 'Open reference sound', exact: true });
    if (await open.isVisible()) await open.click();
    await panel.getByRole('button', { name: 'Load source library', exact: true }).click();
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    await panel.getByRole('button', { name: 'Refresh sessions', exact: true }).click();
    const before = latest.reference_sound_session;
    await panel.getByRole('combobox', { name: 'Retained session', exact: true }).selectOption(expected.session_id);
    await panel.getByRole('button', { name: 'Reopen session', exact: true }).click();
    await expect.poll(() => latest.reference_sound_session !== before && latest.reference_sound_session?.session_id === expected.session_id).toBe(true);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    assert.deepEqual(latest.reference_sound_session, expected);
    await assertReferencePresentation(expect, panel, expected, config);
    await assertPlayback(expect, panel, 'Supplied candidate recording playback', expected.recordings.at(-1).audio_sha256, config.take3.selection.pcm_sha256);
    await expect(panel.getByText(/Analyzed audition: frames 264600:176400 \//)).toBeVisible();
    await expect(panel.getByText(new RegExp(`original SHA-256 ${config.take3.sha256}`))).toBeVisible();
    await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
    await expect(panel.getByRole('button', { name: 'Refine candidate (0/3)', exact: true })).toBeDisabled();
    await expect(page.getByTestId('action-send')).toBeDisabled();
    summary.reference_sound_real_input.reopened_exact = true;
    record({ kind: 'reference-real-input-exact-reopen', session_id: expected.session_id, hardware_validation: false });
    save();
  } finally { assertRealInputsUnchanged(config); }
}

module.exports = { validateRealInputConfig, assertRealInputsUnchanged, primeReferenceRealInputSources,
  exerciseReferenceSoundRealInput, reopenReferenceSoundRealInput, assertSegmentBounds, supportedParameters,
  selectSupportedScope, assertNoiseFadeNative, assertGeneratedSession, assertUnqualifiedReference, assertRecordingHold, assertSegmentIdentity };
