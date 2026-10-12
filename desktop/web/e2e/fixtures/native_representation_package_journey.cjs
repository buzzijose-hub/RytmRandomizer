/* Bounded affected-journey QA. The endurance driver owns the app and secrets. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { expect } = require('@playwright/test');
const { syntheticWav } = require('./reference_sound_package_journey.cjs');

const ORIGINAL_SHA256 = '50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e';
const ORIGINAL_FILE = 'tests/fixtures/native_representation/a4_init_retained.syx';
const FREE_RAM_FLOOR = 6 * 1024 ** 3;

function runVerifier(repo, runRoot, python, source, input = {}) {
  const result = spawnSync(python, ['-c', source, repo, path.join(runRoot, 'state')], {
    cwd: repo, input: JSON.stringify(input), encoding: 'utf8', timeout: 15_000,
    windowsHide: true,
    env: { ...process.env, PYTHONPATH: repo, RYTM_RAND_MIDI_BACKEND: 'off', RYTM_RAND_UPDATES: 'off' },
  });
  assert.equal(result.status, 0, 'Canonical native-representation QA verifier refused');
  return JSON.parse(result.stdout.trim());
}

function primeNativeRepresentationSources(repo, runRoot, python) {
  const source = `from pathlib import Path
from hashlib import sha256
import json, sys
from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
from rytm_randomizer.cockpit.library.store import LibraryStore
from rytm_randomizer.data.analog_four_f1_contract import A4_F1_KIT_BODY_OFFSETS
from rytm_randomizer.data.analog_four_saved_kit_layout import A4_KIT_NAME_OFFSET, A4_KIT_NAME_LENGTH
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import decode_analog_four_saved_kit_payload, encode_analog_four_saved_kit_payload
root, state = map(Path, sys.argv[1:])
original_path = root / '${ORIGINAL_FILE}'
original = original_path.read_bytes()
assert sha256(original).hexdigest() == '${ORIGINAL_SHA256}'
decoded = decode_analog_four_saved_kit_payload(original[1:-1], require_trailer=True)
store = LibraryStore(state / 'roaming' / 'rytm-randomizer' / 'library')
records = []
for key, native, command, name in [('indexed_odd',16257,0x52,'QA F1 ODD'),('working_odd',16257,0x58,'QA F1 ODD'),('indexed_max',32766,0x52,'QA F1 MAX')]:
    body = bytearray(decoded.unpacked)
    body[A4_KIT_NAME_OFFSET:A4_KIT_NAME_OFFSET+A4_KIT_NAME_LENGTH] = name.encode('ascii').ljust(A4_KIT_NAME_LENGTH,b'\\0')
    for offset in A4_F1_KIT_BODY_OFFSETS:
        body[offset:offset+2] = native.to_bytes(2,'big')
    prefix = bytearray(decoded.prefix)
    prefix[5] = command
    encoded = encode_analog_four_saved_kit_payload(bytes(prefix), bytes(body))
    frame = b'\\xf0' + encoded.payload + b'\\xf7'
    result = decode_kit_capture_frame('analog_four_mk2',frame)
    record = store.retain_source(result,origin='file_import')
    assert store.read_source_frame(record.record_id) == frame
    records.append(dict(key=key,record_id=record.record_id,frame_sha256=sha256(frame).hexdigest(),body_sha256=sha256(body).hexdigest(),native=native,command=command,frame_bytes=len(frame),synthetic_variant=True))
assert records[0]['body_sha256'] == records[1]['body_sha256']
assert records[0]['record_id'] != records[1]['record_id']
assert original_path.read_bytes() == original
print(json.dumps(dict(original_sha256=sha256(original).hexdigest(),sources=records)))
`;
  const primed = runVerifier(repo, runRoot, python, source);
  return { ...primed, checks: [], screenshots: [], passed: false,
    helper_sha256: require('node:crypto').createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'),
    synthetic_audio_only: true, physical_validation: false,
    server_refusal_probe: 'not run by this journey; source unit-test results are a separate acceptance requirement',
    packaging_limits: 'UI runs the packaged backend with developer paths removed; source verifier only checks retained artifacts and does not certify physical behavior' };
}

function verifyRetainedSession(repo, runRoot, python, view, sources) {
  const source = `from pathlib import Path
from hashlib import sha256
import json, sys
from rytm_randomizer.cockpit.library.store import LibraryStore
from rytm_randomizer.cockpit.export.reference_sound_store import ReferenceSoundStore
from rytm_randomizer.cockpit.export.reference_sound_session import ReferenceSoundWorkspace
from rytm_randomizer.cockpit.export.reference_sound_display import reference_sound_operator_session
from rytm_randomizer.data.analog_four_kit_fields import format_a4_fixed_8_8
from rytm_randomizer.devices import get_analog_four_native_field_capability, resolve_saved_kit_capture_capability
root, state = map(Path,sys.argv[1:])
request = json.load(sys.stdin)
view = request['view']
directory = state / 'roaming' / 'rytm-randomizer' / 'reference-sounds'
store = ReferenceSoundStore(directory)
workspace = ReferenceSoundWorkspace(store)
stored = workspace.reopen(view['session_id'])
assert reference_sound_operator_session(stored) == view
library = LibraryStore(state / 'roaming' / 'rytm-randomizer' / 'library')
for item in request['sources']:
    assert sha256(library.read_source_frame(item['record_id'])).hexdigest() == item['frame_sha256']
native = get_analog_four_native_field_capability()
source_frame = store.read_artifact(stored['context']['source_sha256'],'syx')
assert sha256(source_frame).hexdigest() == request['sources'][0]['frame_sha256']
assert native.read_native_fields(source_frame).value('filter1_frequency',1).encoded_native == 16257
codec = resolve_saved_kit_capture_capability('analog_four_mk2').capability
source_body = codec.decode_saved_kit_capture(source_frame).unpacked
assert int.from_bytes(source_body[128:130],'big') == 16257
records = []
for candidate in stored['candidates']:
    frame = workspace.candidate(stored['session_id'],candidate['candidate_id']).frame
    assert sha256(frame).hexdigest() == candidate['frame_sha256']
    value = native.read_native_fields(frame).value('filter1_frequency',1)
    candidate_body = codec.decode_saved_kit_capture(frame).unpacked
    changed = [index for index,pair in enumerate(zip(source_body,candidate_body,strict=True)) if pair[0] != pair[1]]
    assert set(changed).issubset({128,129})
    assert int.from_bytes(candidate_body[128:130],'big') == value.encoded_native
    assert codec.encode_saved_kit_capture(codec.decode_saved_kit_capture(frame)) == frame
    for change in candidate['changes']:
        assert change['parameter'] == 'filter1_frequency'
        assert change['source_display'] == format_a4_fixed_8_8(16257)
        assert change['rendered_value'] == value.encoded_native
        assert change['rendered_display'] == format_a4_fixed_8_8(value.encoded_native)
    records.append(dict(candidate_id=candidate['candidate_id'],frame_sha256=candidate['frame_sha256'],native=value.encoded_native,changed_body_offsets=changed,stored_rendered_labels=[change['rendered_display'] for change in candidate['changes']]))
assert sha256((root / '${ORIGINAL_FILE}').read_bytes()).hexdigest() == '${ORIGINAL_SHA256}'
print(json.dumps(dict(manifest_sha256=sha256((directory / (stored['session_id']+'.sound.json')).read_bytes()).hexdigest(),source_sha256=stored['context']['source_sha256'],favorites=stored['favorites'],candidates=records,original_unchanged=True)))
`;
  return runVerifier(repo, runRoot, python, source, { view, sources });
}

async function exerciseNativeRepresentationPackage({ page, latest, connected, processOperation, summary, save, reportRoot, record, digest, repo, runRoot, python, budgetSeconds }) {
  const evidence = summary.native_representation;
  const started = Date.now();
  assert(Number.isFinite(budgetSeconds) && budgetSeconds > 0 && budgetSeconds <= 600);
  evidence.budget_seconds = budgetSeconds;
  evidence.free_ram_floor_bytes = FREE_RAM_FLOOR;
  const checkpoint = name => {
    summary.phase = `native-representation-${name}`; save();
    assert(Date.now() - started < budgetSeconds * 1000, 'Bounded native journey deadline reached');
    const resource = processOperation('sample');
    const privateBytes = resource.processes.reduce((total, item) => total + item.private_bytes, 0);
    record({ kind: 'native-representation-resource', phase: name, resource, private_bytes: privateBytes });
    assert(resource.free_ram_bytes > FREE_RAM_FLOOR, 'Resource floor reached; stop safely');
    assert(privateBytes < 3 * 1024 ** 3, 'Owned app private-memory ceiling reached');
  };
  const checked = (name, detail = {}) => {
    const result = { name, passed: true, ...detail };
    evidence.checks.push(result); record({ kind: 'native-representation-check', ...result }); save();
  };
  const screenshot = async (name, locator) => {
    await locator.scrollIntoViewIfNeeded();
    const image = path.join(reportRoot, name);
    await page.screenshot({ path: image });
    evidence.screenshots.push({ name, sha256: digest(fs.readFileSync(image)), viewport: page.viewportSize() }); save();
  };
  checkpoint('initial-connection');
  const appPages = page.context().browser().contexts().flatMap(context => context.pages()).filter(item => item.url().includes('tauri.localhost'));
  assert.equal(appPages.length, 1, 'Exactly one owned packaged UI page is allowed');
  await connected();
  await expect(page.getByTestId('action-send')).toBeDisabled();
  await page.setViewportSize({ width: 1440, height: 1000 });
  const panel = page.getByTestId('reference-sound-panel');
  await panel.getByRole('button', { name: 'Open reference sound', exact: true }).click();
  await panel.getByRole('button', { name: 'Load source library', exact: true }).click();
  await expect.poll(() => latest.library_records?.length).toBe(3);
  for (const source of evidence.sources) {
    const libraryRecord = latest.library_records.find(item => item.record_id === source.record_id);
    assert(libraryRecord);
    assert.equal(libraryRecord.source_frame.sha256, source.frame_sha256);
  }
  await panel.getByRole('combobox', { name: 'Device', exact: true }).selectOption('analog_four_mk2');
  const sources = panel.getByRole('combobox', { name: 'Source Library record', exact: true });
  await expect(sources.locator('option')).toHaveCount(4);
  const byKey = key => evidence.sources.find(item => item.key === key);
  checked('canonical-priming-retained-original-and-three-verified-synthetic-sources', { original_sha256: evidence.original_sha256, source_frame_sha256: evidence.sources.map(item => item.frame_sha256) });
  const option = source => sources.locator('option').filter({ hasText: source.record_id });
  await expect(option(byKey('indexed_odd'))).toContainText('indexed KIT bank');
  await expect(option(byKey('working_odd'))).toContainText('working RAM; freshness unverified');
  assert.notEqual(byKey('indexed_odd').record_id, byKey('working_odd').record_id);
  assert.equal(byKey('indexed_odd').body_sha256, byKey('working_odd').body_sha256);
  checked('source-library-kind-labels-and-distinct-raw-identities');

  const audio = syntheticWav(440);
  const beforeAudio = latest.reference_sound_session;
  await panel.getByLabel('Original WAV', { exact: true }).setInputFiles({ name: 'native-representation-synthetic.wav', mimeType: 'audio/wav', buffer: audio });
  await expect.poll(() => latest.reference_sound_session !== beforeAudio && latest.reference_sound_session?.title === 'native-representation-synthetic.wav').toBe(true);
  assert.equal(latest.reference_sound_session.segment.original.sha256, digest(audio));
  checked('synthetic-reference-import-hash', { sha256: digest(audio), physical_validation: false });
  const generate = panel.getByRole('button', { name: 'Generate eight alternatives', exact: true });
  const table = panel.getByRole('table', { name: 'Native field scope and protections', exact: true });
  const f1row = table.getByRole('row').filter({ has: page.getByRole('rowheader', { name: 'filter1_frequency', exact: true }) });
  const choose = async key => {
    checkpoint(key);
    const previous = latest.reference_sound_controls;
    await sources.selectOption(byKey(key).record_id);
    await expect.poll(() => latest.reference_sound_controls !== previous && latest.reference_sound_controls?.some(item => item.parameter === 'filter1_frequency')).toBe(true);
    await expect(f1row).toHaveCount(1);
    await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
    const control = latest.reference_sound_controls.find(item => item.parameter === 'filter1_frequency');
    assert.equal(control.source_value, byKey(key).native);
    assert.equal(control.send_supported, false);
    return control;
  };
  const clearSelected = async () => {
    for (const box of await table.getByRole('checkbox', { name: /^Mutate / }).all()) {
      if (await box.isEnabled() && await box.isChecked()) await box.uncheck();
    }
  };
  const working = await choose('working_odd');
  assert.equal(working.source_display, '63.50');
  assert(latest.reference_sound_controls.every(item => item.mutable === false));
  await expect(f1row.getByRole('checkbox', { name: 'Mutate filter1_frequency', exact: true })).toBeDisabled();
  await expect(f1row).toContainText('working_kit_freshness_unverified');
  await expect(generate).toBeDisabled();
  checked('working-source-controls-and-generate-read-only', { native: 16257, label: '63.50' });
  await screenshot('native-working-desktop.png', f1row);

  const maximum = await choose('indexed_max');
  assert.equal(maximum.source_display, '127.99');
  assert.equal(maximum.domain, null); assert.equal(maximum.mutable, false);
  await clearSelected();
  await expect(f1row).toContainText('127.99 / 32766');
  await expect(f1row.getByRole('checkbox', { name: 'Mutate filter1_frequency', exact: true })).toBeDisabled();
  await expect(generate).toBeDisabled();
  checked('legal-maximum-passive-not-new-sampling-authority', { native: 32766, label: '127.99' });
  await screenshot('native-maximum-desktop.png', f1row);

  const indexed = await choose('indexed_odd');
  assert.equal(indexed.source_display, '63.50'); assert.equal(indexed.mutable, true);
  assert.equal(indexed.domain.minimum, 0); assert.equal(indexed.domain.maximum, 32512);
  await expect(f1row).toContainText('63.50 / 16257');
  await expect(f1row).toContainText('NRPN14=8128');
  await expect(f1row).toContainText('lost native bit=1');
  await expect(f1row).toContainText('not Hz');
  await expect(f1row).toContainText('output unverified');
  await clearSelected();
  await f1row.getByRole('checkbox', { name: 'Mutate filter1_frequency', exact: true }).check();
  await expect(generate).toBeEnabled();
  checked('indexed-exact-word-truncated-label-wire-loss-and-legacy-domain', { native: 16257, label: '63.50', wire14: 8128, lost_native_bit: 1, mutation_maximum: 32512 });
  await screenshot('native-indexed-odd-desktop.png', f1row);
  checkpoint('candidate-generation');
  await generate.click();
  await expect(panel.getByRole('group', { name: 'Native alternatives', exact: true }).getByRole('radio')).toHaveCount(8, { timeout: 65_000 });
  await expect(panel.getByRole('button', { name: 'Favorite candidate', exact: true })).toBeEnabled();
  const generated = latest.reference_sound_session;
  assert.equal(generated.context.source_sha256, byKey('indexed_odd').frame_sha256);
  assert.deepEqual(generated.context.parameters, ['filter1_frequency']);
  assert.equal(generated.context.target, 1);
  assert.equal(new Set(generated.candidates.map(item => item.candidate_id)).size, 8);
  assert(generated.candidates.some(item => item.changes.length > 0));
  for (const candidate of generated.candidates) {
    assert.equal(candidate.source_sha256, byKey('indexed_odd').frame_sha256);
    assert.equal(candidate.hardware_send_validated, false);
    assert.equal(candidate.roundtrip_redecoded, true);
    for (const change of candidate.changes) {
      assert.equal(change.parameter, 'filter1_frequency'); assert.equal(change.source_value, 16257);
      assert.equal(change.source_display, '63.50'); assert.deepEqual(change.offsets, [128, 129]);
      assert(change.rendered_value >= 0 && change.rendered_value <= 32512);
    }
  }
  await panel.getByRole('button', { name: 'Favorite candidate', exact: true }).click();
  await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
  await expect.poll(() => latest.reference_sound_session?.favorites.length).toBe(1);
  const retained = structuredClone(latest.reference_sound_session);
  assert(retained.favorites.includes(retained.selected_candidate_id));
  const beforeRestart = verifyRetainedSession(repo, runRoot, python, retained, evidence.sources);
  checked('packaged-generation-favorite-and-canonical-retained-native-identity', beforeRestart);

  checkpoint('owned-backend-restart');
  assert.equal(summary.restarts.length, 0, 'Only one owned backend restart is allowed');
  const recovery = processOperation('restart-backend');
  assert(recovery.token_rotated && recovery.shell_preserved);
  summary.restarts.push({ ...recovery, at: new Date().toISOString() }); save();
  await connected();
  await panel.getByRole('button', { name: 'Refresh sessions', exact: true }).click();
  await expect(panel.getByRole('button', { name: 'Refresh sessions', exact: true })).toBeEnabled();
  await panel.getByRole('combobox', { name: 'Retained session', exact: true }).selectOption(retained.session_id);
  const previousSession = latest.reference_sound_session;
  await panel.getByRole('button', { name: 'Reopen session', exact: true }).click();
  await expect.poll(() => latest.reference_sound_session !== previousSession && latest.reference_sound_session?.session_id === retained.session_id).toBe(true);
  assert.deepEqual(latest.reference_sound_session, retained);
  assert.deepEqual(verifyRetainedSession(repo, runRoot, python, retained, evidence.sources), beforeRestart);
  await expect(panel.getByRole('button', { name: 'Remove favorite', exact: true })).toBeVisible();
  await expect(page.getByTestId('action-send')).toBeDisabled();
  await expect(page.getByTestId('safety-rail').getByText('Hardware Off')).toBeVisible();
  checked('one-owned-restart-exact-session-favorite-native-recall-disarmed');
  await page.setViewportSize({ width: 600, height: 900 });
  await expect(panel.getByRole('table', { name: 'Exact native changes', exact: true })).toBeVisible();
  assert(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth));
  await screenshot('native-recall-narrow.png', panel.getByRole('table', { name: 'Exact native changes', exact: true }));
  checked('narrow-viewport-no-document-overflow', { width: 600, height: 900 });
  checkpoint('completed');
  evidence.elapsed_seconds = (Date.now() - started) / 1000;
  evidence.session_id = retained.session_id;
  evidence.passed = true; save();
}

module.exports = { primeNativeRepresentationSources, exerciseNativeRepresentationPackage };
