const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { createHash } = require('node:crypto');
const { test } = require('node:test');
const helper = require('../e2e/fixtures/reference_sound_real_input_journey.cjs');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');

function pcm(frames, rate = 44100) {
  const bytes = Buffer.alloc(44 + frames * 2);
  bytes.write('RIFF'); bytes.writeUInt32LE(bytes.length - 8, 4); bytes.write('WAVEfmt ', 8);
  bytes.writeUInt32LE(16, 16); bytes.writeUInt16LE(1, 20); bytes.writeUInt16LE(1, 22);
  bytes.writeUInt32LE(rate, 24); bytes.writeUInt32LE(rate * 2, 28);
  bytes.writeUInt16LE(2, 32); bytes.writeUInt16LE(16, 34); bytes.write('data', 36);
  bytes.writeUInt32LE(frames * 2, 40);
  bytes.writeInt16LE(17, 44);
  if (frames > 264600) bytes.writeInt16LE(1234, 44 + 264600 * 2);
  return bytes;
}

function privateFixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'real-input-fake-unit-'));
  t.after(() => {
    assert(path.basename(root).startsWith('real-input-fake-unit-'));
    assert.equal(path.dirname(root), fs.realpathSync(os.tmpdir()));
    fs.rmSync(root, { recursive: true, force: true });
  });
  const repo = path.join(root, 'repo'), runRoot = path.join(root, 'qa'), inputs = path.join(root, 'private');
  for (const directory of [repo, runRoot, inputs, path.join(repo, '.git')]) fs.mkdirSync(directory);
  const raw = { qa_only: true };
  const data = { source: Buffer.from('fake source only; priming subprocess is NOT executed'), reference: pcm(400000), take2: pcm(44100), take3: pcm(500000) };
  for (const [key, bytes] of Object.entries(data)) {
    const filename = path.join(inputs, `${key}.${key === 'source' ? 'syx' : 'wav'}`);
    fs.writeFileSync(filename, bytes);
    raw[key] = { path: filename, sha256: digest(bytes) };
  }
  const locations = { repo, runRoot };
  const config = helper.validateRealInputConfig(raw, locations);
  return { root, raw, data, locations, config };
}

const control = (parameter, overrides = {}) => ({ parameter, mutable: true, reasons: [], source_value: 64,
  source_display: '0', units: 'centered-64-native-u7', domain: { minimum: 0, maximum: 127, quantum: 1, values: [] },
  offsets: [10], output_authority: 'local-file-only', send_supported: false, ...overrides });
const controls = () => [control('noise_fade'), control('filter1_frequency', { offsets: [20, 21], units: 'q8.8' }),
  control('osc1_tuning', { mutable: false, reasons: ['mandatory_parameter_protection'] }),
  control('disproved_field', { mutable: false, reasons: ['mapping_disproved'], domain: null })];

class FakeScope {
  constructor(rows) {
    this.rows = new Map(rows.map(row => [row.parameter, { mutable: row.mutable, mutate: row.mutable, lock: true }]));
    this.writes = [];
  }
  getByLabel(label, options) {
    assert.deepEqual(options, { exact: true });
    const match = /^(Mutate|Lock) (.+)$/.exec(label);
    assert(match, `Unexpected scope selector: ${label}`);
    const key = match[1].toLowerCase(), field = match[2], row = this.rows.get(field);
    assert(row, 'Unknown fake scope field');
    const write = value => {
      assert(row.mutable, 'Attempt to operate a protected/disproved field');
      row[key] = value; this.writes.push({ field, key, value });
      if (key === 'lock' && value) row.mutate = false;
      if (key === 'mutate' && value) row.lock = false;
    };
    return { isEnabled: async () => row.mutable, isChecked: async () => row[key],
      check: async () => write(true), uncheck: async () => write(false) };
  }
}

test('private configuration preserves original byte/metadata snapshots with fixed sample-exact bounds', t => {
  const { config, data } = privateFixture(t);
  assert(Object.isFrozen(config) && Object.isFrozen(config.take3.info) && Object.isFrozen(config.source.snapshot));
  assert.equal(config.reference.info.sample_rate, 44100);
  assert.deepEqual(config.take3.selection, { start_frame: 264600, frame_count: 176400,
    pcm_sha256: digest(data.take3.subarray(44 + 264600 * 2, 44 + 441000 * 2)) });
  helper.assertSegmentBounds(config.reference.info, 0, 352800);
  helper.assertSegmentBounds(config.take3.info, 264600, 176400);
  helper.assertRealInputsUnchanged(config);
  for (const key of Object.keys(data)) assert.deepEqual(fs.readFileSync(config[key].path), data[key]);
  assert.throws(() => helper.assertRealInputsUnchanged({ ...config }), /returned by validate/);
});

test('configuration refuses opt-in, expected-hash, relative, checkout and owned-output violations', t => {
  const { raw, locations, root, data } = privateFixture(t);
  const validate = value => helper.validateRealInputConfig(value, locations);
  for (const value of [{ ...raw, qa_only: false }, { ...raw, qa_only: 'true' }, { ...raw, source: undefined },
    { ...raw, source: { ...raw.source, path: 'relative.syx' } },
    { ...raw, source: { ...raw.source, sha256: '' } },
    { ...raw, source: { ...raw.source, sha256: 'f'.repeat(64) } }]) assert.throws(() => validate(value));
  const elsewhere = path.join(root, 'another-checkout'); fs.mkdirSync(elsewhere); fs.mkdirSync(path.join(elsewhere, '.git'));
  for (const directory of [locations.repo, locations.runRoot, elsewhere]) {
    const filename = path.join(directory, 'private-source.syx'); fs.writeFileSync(filename, data.source);
    assert.throws(() => validate({ ...raw, source: { ...raw.source, path: filename } }));
  }
  assert.throws(() => helper.validateRealInputConfig(raw, { ...locations, runRoot: root }), /separate from checkout/);
});

test('configuration refuses bad WAV rates/layouts/chunks and implicit cropping of a long take2', t => {
  const { raw, locations } = privateFixture(t);
  const invalid = [pcm(44100, 22050), pcm(352801), pcm(2204), Buffer.from('not a WAV')];
  const partial = pcm(44100); partial.writeUInt32LE(partial.length, 4); invalid.push(partial);
  const float = pcm(44100); float.writeUInt16LE(3, 20); invalid.push(float);
  for (const bytes of invalid) {
    fs.writeFileSync(raw.take2.path, bytes);
    assert.throws(() => helper.validateRealInputConfig({ ...raw, take2: { ...raw.take2, sha256: digest(bytes) } }, locations));
  }
});

test('read-only snapshot detects changed content, metadata and redirected owned state', t => {
  const { raw, config, root } = privateFixture(t);
  const original = fs.readFileSync(raw.take2.path);
  fs.writeFileSync(raw.take2.path, Buffer.from('replaced'));
  assert.throws(() => helper.assertRealInputsUnchanged(config), /hash mismatch/);
  fs.writeFileSync(raw.take2.path, original);
  assert.throws(() => helper.assertRealInputsUnchanged(config), /metadata changed/);
  const outside = path.join(root, 'redirect'); fs.mkdirSync(outside);
  fs.symlinkSync(outside, path.join(config.runRoot, 'state'), 'junction');
  assert.throws(() => helper.assertRealInputsUnchanged(config), /redirect through symlinks/);
});

test('priming uses the supplied primary CLI and canonical isolated LibraryStore, never reads WAVs in Python', t => {
  const { config, locations, data } = privateFixture(t);
  let calls = 0;
  const result = helper.primeReferenceRealInputSources(locations.repo, locations.runRoot, 'primary-python-cli', config, (python, args, options) => {
    calls++;
    assert.equal(python, 'primary-python-cli'); assert.equal(args[0], '-c'); assert.equal(args[2], config.state);
    assert.match(args[1], /LibraryStore\(Path\(sys\.argv\[1\]\) \/ 'roaming' \/ 'rytm-randomizer' \/ 'library'\)/);
    assert.match(args[1], /decode_kit_capture_frame\('analog_four_mk2', original\)/);
    assert.match(args[1], /origin='file_import'/);
    assert.match(args[1], /assert store\.read_source_frame\(record\.record_id\) == original/);
    assert(!/mido|rtmidi|open_port|arm|\.wav/.test(args[1]));
    assert.deepEqual(JSON.parse(options.input), { path: config.source.path, sha256: config.source.sha256 });
    assert.equal(options.cwd, config.repo); assert.equal(options.windowsHide, true); assert.equal(options.timeout, 15000);
    for (const key of ['RYTM_RAND_MIDI_BACKEND', 'RYTM_RAND_UPDATES', 'RYTM_RAND_UPDATE_BEACON']) assert.equal(options.env[key], 'off');
    for (const key of ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMBA_NUM_THREADS']) assert.equal(options.env[key], '1');
    assert.equal(options.env.PYTHONDONTWRITEBYTECODE, '1'); assert.equal(options.env.USERPROFILE, config.state);
    return { status: 0, stdout: JSON.stringify({ record_id: 'a'.repeat(16), source_sha256: config.source.sha256, hardware_validation: false }) };
  });
  assert.equal(calls, 1); assert.equal(result.hardware_validation, false);
  assert.throws(() => helper.primeReferenceRealInputSources(locations.repo, locations.runRoot, 'fake', config, () => ({ status: 1 })), /priming failed/);
  assert.throws(() => helper.primeReferenceRealInputSources(locations.repo, locations.runRoot, 'fake', config, () => ({ status: 0, stdout: JSON.stringify({ record_id: 'a'.repeat(16), source_sha256: 'b'.repeat(64), hardware_validation: false }) })));
  for (const key of Object.keys(data)) assert.deepEqual(fs.readFileSync(config[key].path), data[key]);
});

test('fake scope exercises every supported checkbox including Noise Fade and never operates protected/disproved fields', async () => {
  const rows = controls(), panel = new FakeScope(rows);
  assert.deepEqual(await helper.selectSupportedScope(panel, rows), ['noise_fade', 'filter1_frequency']);
  assert.deepEqual(panel.writes, [
    { field: 'noise_fade', key: 'lock', value: false }, { field: 'noise_fade', key: 'mutate', value: true },
    { field: 'filter1_frequency', key: 'lock', value: false }, { field: 'filter1_frequency', key: 'mutate', value: true },
  ]);
  panel.rows.get('disproved_field').mutate = true;
  await assert.rejects(helper.selectSupportedScope(panel, rows), /Protected field must not be selected/);
  for (const bad of [[...rows, rows[0]], [control('noise_fade', { reasons: ['mapping_disproved'] })],
    [control('noise_fade', { send_supported: true })], [control('noise_fade', { domain: null })], [control('filter1_frequency')]]) {
    assert.throws(() => helper.supportedParameters(bad));
  }
});

test('Noise Fade signed native bounds are checked before centered conversion and never clamped', () => {
  for (const signed of [-64, -1, 0, 63]) helper.assertNoiseFadeNative(control('noise_fade', { source_value: signed + 64, source_display: String(signed) }));
  const change = { ...control('noise_fade'), proposed_value: 127, proposed_display: '63', rendered_value: 0, rendered_display: '-64' };
  helper.assertNoiseFadeNative(change);
  for (const bad of [{ ...change, proposed_display: '64', proposed_value: 127 }, { ...change, rendered_display: '-65' },
    { ...change, source_display: null }, { ...change, proposed_value: 63 }, { ...change, units: 'unipolar' },
    { ...change, rendered_value: 0.5 }]) assert.throws(() => helper.assertNoiseFadeNative(bad));
});

test('generated payload checks all eight directions, exact source/scope and version 2 with nonvacuous Noise Fade coverage', t => {
  const { config } = privateFixture(t), rows = controls(), parameters = helper.supportedParameters(rows);
  const change = { ...rows[0], proposed_value: 127, proposed_display: '63', rendered_value: 100, rendered_display: '36' };
  const candidates = ['closest', 'darker', 'brighter', 'metallic', 'percussive', 'atmospheric', 'deeper', 'animated'].map((direction, index) => ({
    candidate_id: String(index), direction, device_id: 'analog_four_mk2', target: 1, source_sha256: config.source.sha256,
    output_authority: 'local-file-only', hardware_send_validated: false, roundtrip_redecoded: true,
    intended_unpacked_offsets: [10], changed_unpacked_offsets: [10], changes: [change],
  }));
  const session = { context: { device_id: 'analog_four_mk2', target: 1, source_sha256: config.source.sha256,
    segment_sha256: 's', parameters, locks: [], inference_version: 2 }, segment: { sha256: 's' }, candidates };
  helper.assertGeneratedSession(session, config, rows, parameters);
  for (const update of [{ inference_version: 1 }, { inference_version: undefined }, { target: 2 },
    { parameters: ['noise_fade'] }, { source_sha256: 'wrong' }, { locks: ['noise_fade'] }]) {
    assert.throws(() => helper.assertGeneratedSession({ ...session, context: { ...session.context, ...update } }, config, rows, parameters));
  }
  for (const update of [{ hardware_send_validated: true }, { direction: 'refined' }, { changes: [] },
    { intended_unpacked_offsets: [99], changed_unpacked_offsets: [99] }, { changed_unpacked_offsets: [99] },
    { changes: [{ ...change, parameter: 'disproved_field' }] }]) {
    const broken = candidates.map(candidate => ({ ...candidate, ...update }));
    assert.throws(() => helper.assertGeneratedSession({ ...session, candidates: broken }, config, rows, parameters));
  }
});

test('quiet/unpitched real recording holds never promote the Welch peak or invent an octave mismatch', () => {
  const reference = { diagnostics: { qualified_pitch_hz: null, spectral_peak_hz: 82.095, pitch_status: 'uncertain', refinement_blockers: ['quiet_audio', 'pitch_uncertain'] } };
  const recording = { physical_validation: false, features: { diagnostics: { refinement_blockers: ['quiet_audio'] } },
    pitch_comparison: { support_status: 'held', delta_cents: null, octave_difference: null, blockers: ['quiet_audio', 'pitch_uncertain'] } };
  helper.assertRecordingHold(recording, reference);
  helper.assertRecordingHold(recording, { diagnostics: { ...reference.diagnostics, pitch_status: 'unpitched' } });
  for (const update of [{ qualified_pitch_hz: 82.095 }, { spectral_peak_hz: 164.19 }, { pitch_status: 'qualified' }]) {
    assert.throws(() => helper.assertRecordingHold(recording, { diagnostics: { ...reference.diagnostics, ...update } }));
  }
  for (const update of [{ support_status: 'supported' }, { octave_difference: 1 }, { delta_cents: 1200 },
    { blockers: ['pitch_mismatch'] }, { blockers: [] }, { blockers: ['pitch_uncertain'] }]) {
    assert.throws(() => helper.assertRecordingHold({ ...recording, pitch_comparison: { ...recording.pitch_comparison, ...update } }, reference));
  }
});

test('exact recording segment verifier refuses wrong original hash, range, rate and impossible bounds', t => {
  const { config } = privateFixture(t);
  const segment = { original: { ...config.take3.info, sha256: config.take3.sha256 }, start_frame: 264600, frame_count: 176400, sha256: 'a'.repeat(64) };
  helper.assertSegmentIdentity(segment, config.take3, 264600, 176400);
  for (const update of [{ start_frame: 0 }, { frame_count: 176401 }, { sha256: 'bad' },
    { original: { ...segment.original, sha256: 'b'.repeat(64) } }, { original: { ...segment.original, sample_rate: 22050 } }]) {
    assert.throws(() => helper.assertSegmentIdentity({ ...segment, ...update }, config.take3, 264600, 176400));
  }
  for (const [start, count] of [[true, 10000], [0, 2204], [-1, 44100], [0.5, 44100], [0, 352801], [490000, 44100], [0, NaN]]) {
    assert.throws(() => helper.assertSegmentBounds(config.take3.info, start, count));
  }
});
