import { Blob as NodeBlob } from 'node:buffer';
import { webcrypto } from 'node:crypto';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { assertSoundContext, currentSoundRecordings, nativeSourceLabel, nativeSources, selectedSound, segmentIsValid, SOUND_ANALYSIS_TIMEOUT_MS, SOUND_CHUNK_BYTES, SOUND_MAX_BYTES } from '../../src/cockpit/referenceSound/referenceSoundModel';
import type { CommandAck } from '../../src/ws/protocol';
import type { ReferenceSoundContext, ReferenceSoundSession } from '../../src/ws/referenceSound';
import { audioFile, patchBytes, prepareSound, sha, soundAck, soundControls, soundHarness, soundSession, soundSummary, sourceRecord, wav } from './referenceSoundTestSupport';

beforeEach(() => {
  vi.stubGlobal('Blob', NodeBlob);
  vi.stubGlobal('crypto', webcrypto);
  vi.spyOn(URL, 'createObjectURL').mockImplementation(() => `blob:${Math.random()}`);
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });

describe('native source response labels are presentation, not authority', () => {
  it('distinguishes indexed and working A4 headers without claiming firmware or freshness', () => {
    const record = { ...sourceRecord, device_id: 'analog_four_mk2' };
    expect(nativeSourceLabel({ ...record, payload_hex: '00203c06005201010000' })).toContain('indexed KIT bank');
    expect(nativeSourceLabel({ ...record, payload_hex: '00203c06005801011400' })).toContain('working RAM; freshness unverified');
    expect(nativeSourceLabel({ ...record, payload_hex: '00203c06005901010000' })).toContain('unclassified');
    expect(nativeSourceLabel({ ...record, payload_hex: '00203c06005802010000' })).toContain('unclassified');
    expect(nativeSourceLabel({ ...record, payload_hex: '00203c06015801010000' })).toContain('unclassified');
    expect(nativeSourceLabel(sourceRecord)).toBe(`${sourceRecord.kit_name} / ${sourceRecord.record_id}`);
  });
});

describe('reference sound retained workflow', () => {
  it('uses bounded upload offsets, exact source metadata, eight server alternatives and long worker deadlines', async () => {
    const h = soundHarness();
    const changes = vi.fn();
    const unsubscribe = h.model.subscribe(changes);
    await prepareSound(h);
    expect(h.calls.map((call) => call.command.type === 'reference_sound' ? call.command.action : call.command.type)).toEqual([
      'upload_begin', 'upload_chunk', 'upload_finish', 'read_audio', 'controls', 'generate',
    ]);
    const generate = h.calls.at(-1)!;
    expect(generate.command).toEqual({ type: 'reference_sound', action: 'generate', session_id: 'sound-original', source_record_id: 'native-source',
      device_id: 'analog_rytm_mk2', target: 1, parameters: ['dec', 'lev'], locks: [], strength: 0.5 });
    expect(generate.options).toEqual({ timeoutMs: SOUND_ANALYSIS_TIMEOUT_MS });
    expect(h.model.snapshot().session?.candidates).toHaveLength(8);
    expect(selectedSound(h.model.snapshot())?.changes[0]).toMatchObject({ source_value: 64, proposed_value: 80, rendered_value: 72 });
    expect(h.model.snapshot().originalUrl).toMatch(/^blob:/);
    expect(h.model.snapshot().segmentUrl).toMatch(/^blob:/);
    expect(changes).toHaveBeenCalled();
    unsubscribe();
    await h.model.select('candidate-2');
    expect(selectedSound(h.model.snapshot())?.candidate_id).toBe('candidate-2');
    await h.model.select('candidate-2', true);
    expect(h.model.snapshot().session?.favorites).toEqual(['candidate-2']);
    await h.model.select('candidate-2', false);
    expect(h.model.snapshot().session?.favorites).toEqual([]);
  });

  it('chunks upload and retained playback at 192 KiB, verifies checksums, and releases URLs', async () => {
    const audio = wav(100_000, 96_000);
    const h = soundHarness(audio);
    await h.model.importReference(audioFile(audio));
    const chunks = h.calls.filter((call) => call.command.type === 'reference_sound' && call.command.action === 'upload_chunk');
    expect(chunks).toHaveLength(2);
    expect(chunks.map((call) => call.command.type === 'reference_sound' && call.command.action === 'upload_chunk' &&
      [call.command.offset, atob(call.command.chunk).length])).toEqual([[0, SOUND_CHUNK_BYTES], [SOUND_CHUNK_BYTES, audio.length - SOUND_CHUNK_BYTES]]);
    expect(h.calls.filter((call) => call.command.type === 'reference_sound' && call.command.action === 'read_audio')).toHaveLength(2);
    h.model.dispose();
    expect(URL.revokeObjectURL).toHaveBeenCalledTimes(2);
    await h.model.refresh();
    expect(h.calls.at(-1)?.command).not.toMatchObject({ action: 'list' });
    h.model.activate();
    await h.model.refresh();
    expect(h.model.snapshot().sessions).toHaveLength(1);
  });

  it('loads and imports the existing source library without wire-supplied paths', async () => {
    const h = soundHarness();
    await h.model.loadLibrary();
    await h.model.loadLibrary(true);
    expect(h.calls.map((call) => call.command)).toEqual([{ type: 'library_list' }, { type: 'library_import_captures' }, { type: 'library_list' }]);
    expect(h.published).toHaveBeenCalledWith([sourceRecord]);
  });

  it('hides stale selection when scope, source, segment, strength or native identity changes', async () => {
    const h = soundHarness();
    await prepareSound(h);
    h.model.toggleField('dec', true);
    expect(selectedSound(h.model.snapshot())).toBeUndefined();
    expect(h.model.snapshot().locks).toEqual(['dec']);
    h.model.toggleField('dec', true);
    h.model.toggleField('lev', false);
    h.model.toggleField('lev', false);
    h.model.toggleField('unsupported', false);
    expect(h.model.snapshot().parameters).toEqual(['dec', 'lev']);
    h.model.setStrength(0.4);
    h.model.setSegment(20, 400);
    await h.model.applySegment();
    expect(h.calls.find((call) => call.command.type === 'reference_sound' && call.command.action === 'segment')?.command)
      .toMatchObject({ start_frame: 20, frame_count: 400 });
    expect(h.model.snapshot().session?.candidates).toEqual([]);
    await h.model.chooseSource('', 'analog_four_mk2', 1);
    expect(h.model.snapshot().controls).toEqual([]);
    await h.model.chooseSource(sourceRecord.record_id, 'analog_rytm_mk2', 1);
    h.model.setRecords([{ ...sourceRecord, source_frame: { ...sourceRecord.source_frame!, sha256: 'changed' } }]);
    expect(h.model.snapshot().sourceId).toBe('');
    await h.model.chooseSource(sourceRecord.record_id, 'analog_rytm_mk2', 1);
    h.model.setRecords([]);
    expect(h.model.snapshot().sourceId).toBe('');
  });

  it('keeps a deliberate new source draft during library refresh', async () => {
    const h = soundHarness();
    await prepareSound(h);
    const other = { ...sourceRecord, record_id: 'other', source_frame: { ...sourceRecord.source_frame!, sha256: 'other-sha' } };
    h.model.setRecords([sourceRecord, other]);
    await h.model.chooseSource('other', 'analog_rytm_mk2', 1);
    h.model.setRecords([sourceRecord, other]);
    expect(h.model.snapshot().sourceId).toBe('other');
  });

  it('protects unsupported controls and explicitly locked fields in the generation contract', async () => {
    const h = soundHarness();
    await prepareSound(h);
    h.model.toggleField('lev', true);
    await h.model.generate();
    expect(h.calls.at(-1)?.command).toMatchObject({ parameters: ['dec', 'lev'], locks: ['lev'] });
    expect(h.model.snapshot().error).toBeNull();
    h.model.toggleField('dec', true);
    await h.model.generate();
    expect(h.model.snapshot().error).toMatch(/unlocked supported field/);
  });

  it('reopens server favorites and exact segment playback with source metadata, never localStorage', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.select('candidate-2', true);
    const saved = h.getSession();
    const restarted = soundHarness();
    restarted.setSession(saved);
    const storage = vi.spyOn(Storage.prototype, 'setItem');
    await restarted.model.refresh();
    await restarted.model.reopen(saved.session_id);
    expect(restarted.model.snapshot().session?.favorites).toEqual(['candidate-2']);
    expect(restarted.model.snapshot().sourceId).toBe('native-source');
    expect(restarted.model.snapshot().segmentUrl).toMatch(/^blob:/);
    expect(restarted.model.snapshot().originalUrl).toMatch(/^blob:/);
    expect(storage).not.toHaveBeenCalled();
    h.model.dispose();
    restarted.model.dispose();
  });

  it('can reopen an ungenerated reference, and generated work whose native library source is absent', async () => {
    const h = soundHarness();
    await h.model.reopen('sound-original');
    expect(h.model.snapshot().session?.context).toBeNull();
    h.setSession(soundSession(wav(), true));
    h.model.setRecords([]);
    await h.model.reopen('sound-generated');
    expect(h.model.snapshot().sourceId).toBe('');
    expect(selectedSound(h.model.snapshot())?.candidate_id).toBe('candidate-1');
  });

  it('keeps catalog summaries compact while the active reopened session stays complete', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.record(audioFile());
    expect(h.model.snapshot().sessions[0]).toMatchObject({ candidate_count: 8, recording_count: 1 });
    expect(Object.keys(h.model.snapshot().sessions[0]!)).toEqual([
      'session_id', 'title', 'segment', 'context', 'favorites', 'candidate_count', 'recording_count',
    ]);
    await h.model.refresh();
    expect(h.model.snapshot().sessions[0]).toEqual(soundSummary(h.getSession()));
    expect(h.model.snapshot().session?.candidates).toHaveLength(8);
    expect(h.model.snapshot().session?.recordings[0]?.feature_deltas).toHaveLength(11);
  });

  it.each(['analog_rytm_mk2', 'analog_four_mk2'] as const)('restores distinct original, segment and supplied recording artifacts after restart (%s)', async (deviceId) => {
    const originalAudio = wav(16_000);
    const recordingAudio = wav(400);
    recordingAudio[44] = 7;
    const h = soundHarness(originalAudio);
    await h.model.importReference(audioFile(originalAudio));
    h.model.setSegment(100, 400);
    await h.model.applySegment();
    await h.model.chooseSource(sourceRecord.record_id, 'analog_rytm_mk2', 1);
    await h.model.generate();
    await h.model.record(audioFile(recordingAudio));
    const saved = h.getSession();
    saved.context!.device_id = deviceId;
    saved.candidates = saved.candidates.map((candidate) => ({ ...candidate, device_id: deviceId }));
    const restored = soundHarness(originalAudio);
    restored.setSession(saved);
    restored.addRecordingAudio(recordingAudio);
    const blobs = vi.mocked(URL.createObjectURL);
    blobs.mockClear();
    await restored.model.reopen(saved.session_id);
    const loadedBytes = await Promise.all(blobs.mock.calls.map(async ([blob]) =>
      new Uint8Array(await (blob as Blob).arrayBuffer())));
    expect(loadedBytes.map(sha)).toEqual([sha(originalAudio), saved.segment.sha256, sha(recordingAudio)]);
    expect(new Set(loadedBytes.map(sha)).size).toBe(3);
    expect(restored.model.snapshot()).toMatchObject({ recordingSha: sha(recordingAudio), originalUrl: expect.stringMatching(/^blob:/),
      segmentUrl: expect.stringMatching(/^blob:/), recordingUrl: expect.stringMatching(/^blob:/) });
    expect(restored.calls.filter(({ command }) => command.type === 'reference_sound' && command.action === 'read_audio').map(({ command }) => command))
      .toEqual([
        { type: 'reference_sound', action: 'read_audio', session_id: saved.session_id, offset: 0, audio_kind: 'original' },
        { type: 'reference_sound', action: 'read_audio', session_id: saved.session_id, offset: 0 },
        { type: 'reference_sound', action: 'read_audio', session_id: saved.session_id, offset: 0, audio_kind: 'recording', recording_sha256: sha(recordingAudio) },
      ]);
    h.model.dispose(); restored.model.dispose();
  });

  it('reloads reference kinds and selects only recognized recordings of the selected candidate', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.record(audioFile());
    const firstSha = h.getSession().recordings[0]!.audio_sha256;
    const secondAudio = wav(400);
    secondAudio[44] = 1;
    await h.model.record(audioFile(secondAudio));
    expect(h.model.snapshot().recordingSha).toBe(sha(secondAudio));
    await h.model.playRecording(firstSha);
    expect(h.model.snapshot().recordingSha).toBe(firstSha);
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'recording', recording_sha256: firstSha });
    const beforeRefine = h.calls.length;
    await h.model.refine(0.5);
    expect(h.calls).toHaveLength(beforeRefine);
    expect(h.model.snapshot().error).toMatch(/latest supplied recording/);
    await h.model.playReference('original');
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'original' });
    await h.model.playReference('segment');
    expect(h.calls.at(-1)?.command).toMatchObject({ audio_kind: 'segment' });
    await h.model.select('candidate-2');
    const before = h.calls.length;
    await h.model.playRecording(firstSha);
    expect(h.calls).toHaveLength(before);
    expect(h.model.snapshot().error).toMatch(/exact candidate/);
    await h.model.select('candidate-1');
    expect(h.model.snapshot().recordingUrl).toMatch(/^blob:/);
    expect(h.model.snapshot().recordingSha).toBe(sha(secondAudio));
    h.model.invalidate();
    expect(currentSoundRecordings(h.model.snapshot())).toEqual([]);
  });

  it('can refine from latest retained feedback when playback is not currently loaded', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile());
    h.model.dispose();
    h.model.activate();
    expect(h.model.snapshot().recordingSha).toBeNull();
    await h.model.refine(0.5);
    expect(h.model.snapshot().session?.refinements).toHaveLength(1);
  });

  it('preserves actual recording playback and candidate count when zero residual refinement is idempotent', async () => {
    const h = soundHarness(); await prepareSound(h);
    await h.model.record(audioFile());
    const saved = h.getSession();
    saved.recordings = saved.recordings.map((recording) => ({ ...recording, distance: 0, score: 100,
      feature_deltas: recording.feature_deltas.map((delta) => ({ ...delta, render_value: delta.reference_value, absolute_delta: 0, weighted_delta: 0 })) }));
    h.setSession(saved);
    await h.model.reopen(saved.session_id);
    const recordingUrl = h.model.snapshot().recordingUrl;
    await h.model.refine(0.5);
    await h.model.refine(0.5);
    expect(h.model.snapshot().session?.candidates).toHaveLength(8);
    expect(h.model.snapshot().session?.refinements).toEqual([]);
    expect(selectedSound(h.model.snapshot())?.candidate_id).toBe('candidate-1');
    expect(h.model.snapshot().recordingUrl).toBe(recordingUrl);
    expect(h.model.snapshot().recordingSha).toBe(saved.recordings[0]!.audio_sha256);
  });

  it('accepts a cached generate response containing the eight native alternatives plus retained refinements', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile());
    await h.model.refine(0.5);
    const saved = h.getSession();
    h.send.mockResolvedValueOnce(soundAck({ session: saved }));
    await h.model.generate();
    expect(h.model.snapshot().error).toBeNull();
    expect(h.model.snapshot().session).toBe(saved);
    expect(h.model.snapshot().session?.candidates).toHaveLength(9);
    expect(selectedSound(h.model.snapshot())?.candidate_id).toBe('refined-1');
  });

  it('scores only supplied recordings of exact candidate SHA and bounds gain/refinement rounds', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.record(audioFile());
    expect(h.calls.at(-1)).toMatchObject({ command: { action: 'record', candidate_id: 'candidate-1', candidate_sha256: sha(patchBytes), upload_id: 'owned-upload' },
      options: { timeoutMs: SOUND_ANALYSIS_TIMEOUT_MS } });
    expect(h.model.snapshot().recordingUrl).toMatch(/^blob:/);
    await h.model.select('candidate-1', true);
    expect(h.model.snapshot().recordingUrl).not.toBeNull();
    await h.model.refine(0.25);
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'refine', correction_gain: 0.25 });
    expect(h.model.snapshot().recordingUrl).toBeNull();
    await h.model.record(audioFile());
    await h.model.refine(1);
    await h.model.record(audioFile());
    await h.model.refine(0);
    expect(h.model.snapshot().session?.refinements).toHaveLength(3);
    await h.model.refine(0.5);
    expect(h.model.snapshot().error).toMatch(/at most three rounds/);
  });

  it('downloads checksum-verified server bytes via Blob without sending to hardware', async () => {
    vi.useFakeTimers();
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    const h = soundHarness();
    await prepareSound(h);
    await h.model.download(0);
    expect(click).toHaveBeenCalledOnce();
    expect((click.mock.contexts[0] as HTMLAnchorElement).download).toBe('KIT001-candidate-1.syx');
    await vi.advanceTimersByTimeAsync(1000);
    expect(URL.revokeObjectURL).toHaveBeenCalled();
    expect(h.calls.every((call) => call.command.type === 'reference_sound')).toBe(true);
    vi.useRealTimers();
  });
});

describe('cancellation, refusals and bounded failures', () => {
  it('cancels an owned worker and never adopts a result from the old scope', async () => {
    const h = soundHarness();
    await prepareSound(h);
    let resolve!: (ack: CommandAck) => void;
    h.send.mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    const pending = h.model.generate();
    await h.model.generate(); // busy: no duplicate worker
    h.model.toggleField('dec', true);
    expect(h.model.snapshot().stale).toBe(true);
    resolve(soundAck({ session: soundSession(wav(), true) }));
    await pending;
    expect(h.model.snapshot().stale).toBe(true);
    expect(h.model.snapshot().error).toBeNull();
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'cancel' });
  });

  it('explicit cancel and unmount revoke ownership even if late data arrives', async () => {
    const h = soundHarness();
    h.send.mockImplementationOnce(() => new Promise(() => {}));
    void h.model.importReference(audioFile());
    await h.model.cancel();
    h.model.dispose();
    expect(h.calls.filter((call) => call.command.type === 'reference_sound' && call.command.action === 'cancel')).toHaveLength(2);
  });

  it('cancels between chunks before another upload chunk or finish can be sent', async () => {
    const h = soundHarness();
    let resolve!: (ack: CommandAck) => void;
    h.send.mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    const upload = h.model.importReference(audioFile());
    await h.model.cancel();
    resolve(soundAck({ upload_id: 'obsolete', received: 0 }));
    await upload;
    expect(h.model.snapshot().session).toBeNull();
  });

  it('never updates a disposed model after an owned response completes', async () => {
    const h = soundHarness();
    let resolve!: (ack: CommandAck) => void;
    h.send.mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    const pending = h.model.refresh();
    h.model.dispose();
    resolve(soundAck({ sessions: [soundSummary()] }));
    await pending;
    expect(h.model.snapshot().sessions).toEqual([]);
  });

  it('refuses missing native-control data while reopening a generated session', async () => {
    const h = soundHarness(); h.setSession(soundSession(wav(), true));
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'controls'
      ? Promise.resolve(soundAck({ cancelled: true })) : original(command, ...rest));
    await h.model.reopen('sound-generated');
    expect(h.model.snapshot().error).toMatch(/native source fields/);
  });

  it.each([
    { ok: false, request_id: 'x', message: 'Missing audio runtime; launch audio-enabled delivery.' },
    { ok: false, request_id: 'x', code: 'ERR_VALIDATION' },
    { ok: false, request_id: 'x', error: 'Missing retained artifact' },
    { ok: false, request_id: 'x' },
    { ok: true, request_id: 'x' },
    soundAck({ cancelled: true }),
  ])('reports actionable server refusal/missing payload %#', async (ack) => {
    const h = soundHarness();
    h.send.mockResolvedValueOnce(ack);
    await h.model.refresh();
    expect(h.model.snapshot().error).not.toBeNull();
    expect(h.model.snapshot().busy).toBeNull();
  });

  it.each([new Error('Disconnected'), 'unknown transport failure'])('handles transport errors without retry (%s)', async (failure) => {
    const h = soundHarness();
    h.send.mockRejectedValueOnce(failure);
    await h.model.refresh();
    expect(h.send).toHaveBeenCalledOnce();
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it.each([
    { ok: false, request_id: 'x', message: 'DISARM first' },
    { ok: false, request_id: 'x' },
  ])('reports cancellation refusal %#', async (ack) => {
    const h = soundHarness();
    h.send.mockResolvedValueOnce(ack);
    await h.model.cancel();
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it.each([new Error('Reconnect'), 'socket gone'])('reports failed cancellation (%s)', async (failure) => {
    const h = soundHarness();
    h.send.mockRejectedValueOnce(failure);
    await h.model.cancel();
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it.each([audioFile(wav(), 'not.wav.mp3'), audioFile(new Uint8Array(43)), audioFile(new Uint8Array(SOUND_MAX_BYTES + 1))])('refuses unsupported filename/size before upload (%s)', async (file) => {
    const h = soundHarness();
    await h.model.importReference(file);
    expect(h.send).not.toHaveBeenCalled();
    expect(h.model.snapshot().error).toMatch(/PCM WAV/);
  });

  it.each([soundAck({ cancelled: true }), soundAck({ upload_id: 'x', received: 3 })])('clears unfinished upload on invalid begin %#', async (reply) => {
    const h = soundHarness();
    h.send.mockResolvedValueOnce(reply);
    await h.model.importReference(audioFile());
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'cancel' });
  });

  it.each([soundAck({ cancelled: true }), soundAck({ upload_id: 'different', received: 16044 }), soundAck({ upload_id: 'owned-upload', received: 1 })])('rejects missing/mismatched chunk ack and cancels %#', async (reply) => {
    const h = soundHarness();
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'upload_chunk'
      ? Promise.resolve(reply) : original(command, ...rest));
    await h.model.importReference(audioFile());
    expect(h.model.snapshot().error).toMatch(/position/);
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'cancel' });
  });

  it('refuses missing session data at finish and missing controls', async () => {
    const h = soundHarness();
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'upload_finish'
      ? Promise.resolve(soundAck({ cancelled: true })) : original(command, ...rest));
    await h.model.importReference(audioFile());
    expect(h.model.snapshot().error).toMatch(/retained session/);
    h.send.mockResolvedValueOnce(soundAck({ cancelled: true }));
    await h.model.chooseSource('native-source', 'analog_rytm_mk2', 1);
    expect(h.model.snapshot().error).toMatch(/native source fields/);
  });

  it.each([
    {}, { audio_chunk: '', size: 16044, offset: 0, sha256: sha(wav()) },
    { audio_chunk: btoa('x'), size: 43, offset: 0, sha256: sha(wav()) },
    { audio_chunk: btoa('x'), size: SOUND_MAX_BYTES + 1, offset: 0, sha256: sha(wav()) },
    { audio_chunk: btoa('x'), size: 44, offset: 1, sha256: sha(wav()) },
    { audio_chunk: btoa('x'), size: 44, offset: 0, sha256: 'different' },
    { audio_chunk: btoa('x'.repeat(SOUND_CHUNK_BYTES + 1)), size: SOUND_MAX_BYTES, offset: 0, sha256: sha(wav()) },
    { audio_chunk: btoa('x'.repeat(45)), size: 44, offset: 0, sha256: sha(wav()) },
    { audio_chunk: btoa('x'.repeat(44)), size: 44, offset: 0, sha256: sha(wav()) },
  ])('refuses corrupt/misbound playback %#', async (reply) => {
    const h = soundHarness();
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'read_audio'
      ? Promise.resolve({ ok: true, request_id: 'x', reference_sound: reply } as CommandAck) : original(command, ...rest));
    await h.model.reopen('sound-original');
    expect(h.model.snapshot().segmentUrl).toBeNull();
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it('refuses a changed playback total size between chunks', async () => {
    const audio = wav(100_000, 96_000);
    const h = soundHarness(audio);
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'read_audio' && command.offset > 0
      ? Promise.resolve(soundAck({ audio_chunk: btoa('x'), size: audio.length - 1, offset: command.offset, sha256: sha(audio) })) : original(command, ...rest));
    await h.model.reopen('sound-original');
    expect(h.model.snapshot().error).toMatch(/identity/);
  });

  it('rejects another artifact returned for retained-recording playback', async () => {
    const h = soundHarness(); await prepareSound(h);
    const recordingAudio = wav(400);
    await h.model.record(audioFile(recordingAudio));
    const original = h.send.getMockImplementation()!;
    h.send.mockImplementation((command, ...rest) => command.type === 'reference_sound' && command.action === 'read_audio' && command.audio_kind === 'recording'
      ? Promise.resolve(soundAck({ audio_chunk: Buffer.from(wav()).toString('base64'), offset: 0, size: wav().length, sha256: sha(wav()) }))
      : original(command, ...rest));
    await h.model.playRecording(sha(recordingAudio));
    expect(h.model.snapshot().error).toMatch(/identity/);
    expect(h.model.snapshot().recordingUrl).toBeNull();
  });

  it('sends only an explicit audition range and plays the exact retained segment, not the supplied multi-note file', async () => {
    const h = soundHarness(); await prepareSound(h);
    const original = wav(80_000);
    original[44 + 8000 * 2] = 42;
    await h.model.record(audioFile(original), { start_frame: 8000, frame_count: 40_000 });
    expect(h.model.snapshot().error).toBeNull();
    const record = h.getSession().recordings.at(-1)!;
    expect(record.segment).toMatchObject({ start_frame: 8000, frame_count: 40_000, original: { sha256: sha(original) } });
    expect(record.audio_sha256).not.toBe(sha(original));
    expect(h.calls.find(({ command }) => command.type === 'reference_sound' && command.action === 'record')?.command)
      .toMatchObject({ start_frame: 8000, frame_count: 40_000 });
    expect(h.calls.at(-1)?.command).toMatchObject({ action: 'read_audio', recording_sha256: record.audio_sha256 });
    expect(h.model.snapshot().recordingSha).toBe(record.audio_sha256);
  });

  it.each(['missing', 'held', 'blocked'] as const)('rejects %s diagnostics without making a refine request or replacing retained favorites', async (mode) => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile()); await h.model.select('candidate-1', true);
    const saved = structuredClone(h.getSession());
    if (mode === 'missing') delete saved.recordings[0]!.features.diagnostics;
    if (mode === 'held') saved.recordings[0]!.pitch_comparison!.support_status = 'held';
    if (mode === 'blocked') saved.recordings[0]!.pitch_comparison!.blockers = ['pitch_mismatch'];
    h.setSession(saved); await h.model.reopen(saved.session_id);
    const count = h.calls.length;
    await h.model.refine(0.5);
    expect(h.model.snapshot().error).toMatch(/Refinement held/);
    expect(h.calls).toHaveLength(count);
    expect(h.getSession()).toEqual(saved);
  });

  it('adds retained reference diagnostics without changing any candidate, source, scope or favorite identity', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.select('candidate-1', true);
    const old = structuredClone(h.getSession()); delete old.analysis!.diagnostics;
    h.setSession(old); await h.model.reopen(old.session_id);
    await h.model.measureReference();
    expect(h.model.snapshot().error).toBeNull();
    expect(h.calls.at(-1)).toMatchObject({ command: { action: 'measure', session_id: old.session_id }, options: { timeoutMs: SOUND_ANALYSIS_TIMEOUT_MS } });
    expect(h.getSession().candidates).toEqual(old.candidates);
    expect(h.getSession().context).toEqual(old.context);
    expect(h.getSession().favorites).toEqual(old.favorites);
    expect(h.getSession().analysis?.diagnostics).toBeDefined();
  });

  it('preserves older Noise Fade candidates but refuses new refinement until a current-model session is generated', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile());
    const old = structuredClone(h.getSession());
    old.context = { ...old.context!, device_id: 'analog_four_mk2', parameters: ['noise_fade'] };
    h.setSession(old); await h.model.reopen(old.session_id);
    const count = h.calls.length; await h.model.refine(0.5);
    expect(h.model.snapshot().error).toMatch(/Legacy Noise Fade/);
    expect(h.calls).toHaveLength(count); expect(h.getSession().candidates).toEqual(old.candidates);
  });

  it('rejects diagnostic refresh before generation or after scope changes without making a request', async () => {
    const h = soundHarness(); await h.model.importReference(audioFile());
    const count = h.calls.length; await h.model.measureReference();
    expect(h.calls).toHaveLength(count); expect(h.model.snapshot().error).toMatch(/source-bound/);
    await h.model.chooseSource('native-source', 'analog_rytm_mk2', 1); await h.model.generate(); h.model.setStrength(0.25);
    const next = h.calls.length; await h.model.measureReference();
    expect(h.calls).toHaveLength(next); expect(h.model.snapshot().error).toMatch(/source-bound/);
  });

  it.each(['session', 'candidate', 'context', 'segment'] as const)('refuses %s identity drift in a diagnostic refresh', async (part) => {
    const h = soundHarness(); await prepareSound(h);
    const old = structuredClone(h.getSession());
    const next = structuredClone(old);
    if (part === 'session') next.session_id = 'sound-other';
    if (part === 'candidate') next.candidates[0]!.candidate_id = 'changed';
    if (part === 'context') next.context!.strength = 0.1;
    if (part === 'segment') next.segment.sha256 = 'other';
    h.send.mockResolvedValueOnce(soundAck({ session: next }));
    await h.model.measureReference();
    expect(h.model.snapshot().error).toMatch(/changed retained source/);
    expect(h.model.snapshot().session).toEqual(old);
  });

  it.each([{ start_frame: -1, frame_count: 400 }, { start_frame: 0.5, frame_count: 400 }, { start_frame: 0, frame_count: 0 }, { start_frame: 0, frame_count: 400.5 }])('refuses an invalid audition range before upload (%s)', async (segment) => {
    const h = soundHarness(); await prepareSound(h);
    const count = h.calls.length;
    const before = structuredClone(h.getSession());
    await h.model.record(audioFile(), segment);
    expect(h.model.snapshot().error).toMatch(/integer audition/);
    expect(h.calls).toHaveLength(count);
    expect(h.getSession()).toEqual(before);
  });

  it('never adopts canceled retained-recording playback or retries a refusal', async () => {
    const h = soundHarness(); await prepareSound(h); await h.model.record(audioFile());
    const recordingSha = h.getSession().recordings[0]!.audio_sha256;
    let resolve!: (ack: CommandAck) => void;
    h.send.mockImplementationOnce(() => new Promise((done) => { resolve = done; }));
    const pending = h.model.playRecording(recordingSha);
    await h.model.cancel();
    resolve(soundAck({ audio_chunk: Buffer.from(wav()).toString('base64'), size: wav().length, offset: 0, sha256: recordingSha }));
    await pending;
    expect(h.model.snapshot().recordingUrl).toBeNull();
    h.send.mockResolvedValueOnce({ ok: false, request_id: 'x', message: 'That recording is not retained in this session.' });
    const count = h.calls.length;
    await h.model.playRecording(recordingSha);
    expect(h.model.snapshot().error).toMatch(/not retained/);
    expect(h.calls).toHaveLength(count);
    expect(h.model.snapshot().recordingUrl).toBeNull();
  });

  it('bounds segment, generation, record, refinement and export preconditions without requests', async () => {
    const h = soundHarness();
    expect(segmentIsValid(h.model.snapshot())).toBe(false);
    expect(selectedSound(h.model.snapshot())).toBeUndefined();
    await h.model.applySegment();
    await h.model.generate();
    await h.model.record(audioFile());
    await h.model.refine(0.5);
    await h.model.download(0);
    await h.model.select('candidate-1');
    await h.model.playReference('original');
    await h.model.playRecording('unrecognized');
    expect(h.send).not.toHaveBeenCalled();
    await prepareSound(h);
    for (const [start, count] of [[-1, 400], [0.5, 400], [0, 399.5], [0, 399], [0, 64001], [7999, 400]]) {
      h.model.setSegment(start!, count!);
      expect(segmentIsValid(h.model.snapshot())).toBe(false);
    }
    await h.model.generate();
    h.model.setSegment(0, 400);
    await h.model.generate(); // unretained draft
    expect(h.model.snapshot().error).toMatch(/Retain/);
    await h.model.reopen('sound-generated');
    for (const gain of [NaN, -0.1, 1.1]) { await h.model.refine(gain); expect(h.model.snapshot().error).toMatch(/gain/); }
    await h.model.refine(0.5); // no recording
    expect(h.model.snapshot().error).toMatch(/recording/);
    h.model.invalidate();
    await h.model.select('candidate-1');
    expect(h.model.snapshot().error).toMatch(/changed scope/);
  });

  it('refuses generation with missing or wrong-device source and out-of-range strength', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.chooseSource(sourceRecord.record_id, 'analog_four_mk2', 1);
    await h.model.generate();
    expect(h.model.snapshot().error).toMatch(/native KIT/);
    await h.model.chooseSource(sourceRecord.record_id, 'analog_rytm_mk2', 1);
    for (const strength of [NaN, -1, 2]) { h.model.setStrength(strength); await h.model.generate(); expect(h.model.snapshot().error).not.toBeNull(); }
  });

  it('bounds recording counts and clears recording playback when switching candidates', async () => {
    const h = soundHarness();
    await prepareSound(h);
    await h.model.record(audioFile());
    await h.model.select('candidate-2');
    expect(h.model.snapshot().recordingUrl).toBeNull();
    const session = h.getSession();
    h.setSession({ ...session, recordings: Array.from({ length: 16 }, () => session.recordings[0]!) });
    await h.model.reopen(session.session_id);
    await h.model.record(audioFile());
    expect(h.model.snapshot().error).toMatch(/16 recordings/);
  });

  it.each([
    { ok: false, request_id: 'x', message: 'File import refused' },
    { ok: false, request_id: 'x' },
  ])('reports import refusal %#', async (reply) => {
    const h = soundHarness(); h.send.mockResolvedValueOnce(reply);
    await h.model.loadLibrary(true);
    expect(h.model.snapshot().error).not.toBeNull();
  });
  it.each([{ ok: true, request_id: 'x' }, { ok: false, request_id: 'x', message: 'Library missing' }])('reports missing library %#', async (reply) => {
    const h = soundHarness(); h.send.mockResolvedValueOnce(reply);
    await h.model.loadLibrary();
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it.each([
    soundAck({ cancelled: true }),
    soundAck({ sysex_base64: '', candidate_id: 'different', sha256: sha(patchBytes), destination_slot: 0 }),
    soundAck({ sysex_base64: '', candidate_id: 'candidate-1', sha256: sha(patchBytes), destination_slot: 1 }),
    soundAck({ sysex_base64: '', candidate_id: 'candidate-1', sha256: 'different', destination_slot: 0 }),
    soundAck({ sysex_base64: '', candidate_id: 'candidate-1', sha256: sha(patchBytes), destination_slot: 0 }),
    soundAck({ sysex_base64: btoa('bad'), candidate_id: 'candidate-1', sha256: sha(patchBytes), destination_slot: 0 }),
  ])('fails closed on missing/corrupt export %#', async (reply) => {
    const h = soundHarness(); await prepareSound(h);
    h.send.mockResolvedValueOnce(reply);
    await h.model.download(0);
    expect(h.model.snapshot().error).not.toBeNull();
  });

  it.each([NaN, -1, 128, 0.5])('requires a strict explicit zero-based export slot (%s)', async (slot) => {
    const h = soundHarness(); await prepareSound(h);
    h.send.mockClear();
    await h.model.download(slot);
    expect(h.send).not.toHaveBeenCalled();
    expect(h.model.snapshot().error).toMatch(/explicit scratch KIT/);
  });

  it('accepts retargeted export SHA without changing retained candidate or recording provenance', async () => {
    const h = soundHarness(); await prepareSound(h);
    const before = h.model.snapshot().session;
    const exported = Uint8Array.from([0xf0, 0x7f, 0xf7]);
    const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
    h.send.mockResolvedValueOnce(soundAck({ sysex_base64: Buffer.from(exported).toString('base64'), sha256: sha(exported), candidate_id: 'candidate-1', destination_slot: 127 }));
    await h.model.download(127);
    expect(h.model.snapshot().error).toBeNull();
    expect(h.model.snapshot().session).toBe(before);
    expect((click.mock.contexts[0] as HTMLAnchorElement).download).toBe('KIT128-candidate-1.syx');
  });
});

describe('wire identity and scope binding', () => {
  it('requires retained original frames rather than old capture-only/favorite records', () => {
    expect(nativeSources([{ ...sourceRecord, source_frame: null }, { ...sourceRecord, device_id: 'other' },
      { ...sourceRecord, device_id: 'analog_four_mk2' }, sourceRecord])).toHaveLength(2);
  });

  it.each([
    { context: null }, { context: { source_sha256: 'different' } }, { context: { segment_sha256: 'different' } },
    { context: { device_id: 'analog_four_mk2' } }, { context: { target: 2 } }, { context: { strength: 1 } },
    { context: { parameters: ['dec'] } }, { context: { parameters: ['dec', 'wrong'] } }, { context: { locks: ['dec'] } },
    { candidates: [] }, { candidate: { source_sha256: 'different' } }, { candidate: { device_id: 'analog_four_mk2' } },
    { candidate: { target: 2 } }, { candidate: { output_authority: 'hardware' } }, { change: { parameter: 'unsupported' } },
  ])('rejects drift from exact source, scope or local-file authority %#', (change) => {
    const session = soundSession(wav(), true);
    const context = session.context!;
    if ('context' in change) session.context = change.context === null ? null : { ...context, ...change.context } as ReferenceSoundContext;
    if ('candidates' in change) session.candidates = change.candidates!;
    if ('candidate' in change) session.candidates[0] = { ...session.candidates[0]!, ...change.candidate } as ReferenceSoundSession['candidates'][number];
    if ('change' in change) session.candidates[0]!.changes[0] = { ...session.candidates[0]!.changes[0]!, ...change.change };
    expect(() => assertSoundContext(session, context)).toThrow(/exact source/);
  });

  it('rejects a rendered change to an explicitly locked field even with matching context', () => {
    const session = soundSession(wav(), true);
    session.context!.locks = ['dec'];
    expect(() => assertSoundContext(session, session.context!)).toThrow();
  });

  it('rejects a generated session that exceeds the bounded refinement count', () => {
    const session = soundSession(wav(), true);
    session.refinements = Array.from({ length: 4 }, () => ({ parent_id: 'candidate-1', recording_sha256: sha(wav()), gain: 0.5, features: session.analysis!.features }));
    expect(() => assertSoundContext(session, session.context!)).toThrow();
  });

  it('preserves unsupported source cells and accepts exact native metadata', () => {
    expect(soundControls[2]?.mutable).toBe(false);
    const session = soundSession(wav(), true);
    expect(() => assertSoundContext(session, session.context!)).not.toThrow();
  });
});
