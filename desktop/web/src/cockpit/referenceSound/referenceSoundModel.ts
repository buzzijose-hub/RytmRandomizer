import type { CockpitClient } from '../../ws/client';
import type { KitCaptureDeviceId, LibraryRecord } from '../../ws/protocol';
import type {
  ReferenceSoundAction, ReferenceSoundAudioSelection, ReferenceSoundCandidate, ReferenceSoundContext,
  ReferenceSoundControl, ReferenceSoundRecording, ReferenceSoundReply, ReferenceSoundSession, ReferenceSoundSessionSummary,
} from '../../ws/referenceSound';

export const SOUND_CHUNK_BYTES = 192 * 1024;
export const SOUND_MAX_BYTES = 16 * 1024 * 1024;
// The isolated audio worker is bounded at 60s; allow its cleanup and WS dispatch.
export const SOUND_ANALYSIS_TIMEOUT_MS = 70_000;

export interface ReferenceSoundView {
  sessions: ReferenceSoundSessionSummary[];
  session: ReferenceSoundSession | null;
  controls: ReferenceSoundControl[];
  sourceId: string;
  deviceId: KitCaptureDeviceId;
  target: number;
  parameters: string[];
  locks: string[];
  strength: number;
  startFrame: number;
  frameCount: number;
  stale: boolean;
  busy: string | null;
  received: number;
  uploadSize: number;
  error: string | null;
  originalUrl: string | null;
  segmentUrl: string | null;
  recordingUrl: string | null;
  recordingSha: string | null;
}

class Superseded extends Error {}

export function nativeSources(records: readonly LibraryRecord[]): LibraryRecord[] {
  return records.filter((record) => record.source_frame != null &&
    (record.device_id === 'analog_rytm_mk2' || record.device_id === 'analog_four_mk2'));
}

export function nativeSourceLabel(record: LibraryRecord): string {
  // Header-only presentation. The server validates source bytes and authority.
  if (record.device_id !== 'analog_four_mk2') return `${record.kit_name} / ${record.record_id}`;
  const header = record.payload_hex.slice(0, 18).toLowerCase();
  let kind = 'response kind unclassified';
  if (header.startsWith('00203c0600') && header.slice(12, 16) === '0101') {
    if (header.slice(10, 12) === '52') kind = 'indexed KIT bank';
    if (header.slice(10, 12) === '58') kind = 'working RAM; freshness unverified';
  }
  return `${record.kit_name} / ${kind} / ${record.record_id}`;
}

export function selectedSound(view: ReferenceSoundView): ReferenceSoundCandidate | undefined {
  return view.stale ? undefined : view.session?.candidates.find(
    (candidate) => candidate.candidate_id === view.session?.selected_candidate_id,
  );
}

export function currentSoundRecordings(view: ReferenceSoundView): ReferenceSoundRecording[] {
  const candidate = selectedSound(view);
  return candidate === undefined ? [] : view.session!.recordings.filter((recording) =>
    recording.candidate_id === candidate.candidate_id && recording.candidate_sha256 === candidate.frame_sha256);
}

export function segmentIsValid(view: ReferenceSoundView): boolean {
  const original = view.session?.segment.original;
  return original !== undefined && Number.isInteger(view.startFrame) && Number.isInteger(view.frameCount) &&
    view.startFrame >= 0 && view.frameCount / original.sample_rate >= 0.05 &&
    view.frameCount / original.sample_rate <= 8 && view.startFrame + view.frameCount <= original.frame_count;
}

export function decodeSoundBytes(encoded: string): Uint8Array<ArrayBuffer> {
  return Uint8Array.from(atob(encoded), (character) => character.charCodeAt(0));
}

function encodeSoundBytes(bytes: Uint8Array): string {
  let binary = '';
  for (const byte of bytes) binary += String.fromCharCode(byte);
  return btoa(binary);
}

async function digest(bytes: Uint8Array<ArrayBuffer>): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', bytes);
  return Array.from(new Uint8Array(hash), (byte) => byte.toString(16).padStart(2, '0')).join('');
}

function sameScope(left: readonly string[], right: readonly string[]): boolean {
  return left.length === right.length && left.every((parameter) => right.includes(parameter));
}

export function assertSoundContext(session: ReferenceSoundSession, context: ReferenceSoundContext): void {
  const actual = session.context;
  if (actual === null || actual.source_sha256 !== context.source_sha256 ||
    actual.segment_sha256 !== context.segment_sha256 || actual.device_id !== context.device_id ||
    actual.target !== context.target || actual.strength !== context.strength ||
    !sameScope(actual.parameters, context.parameters) || !sameScope(actual.locks, context.locks) ||
    session.refinements.length > 3 || session.candidates.length !== 8 + session.refinements.length || session.candidates.some((candidate) =>
      candidate.source_sha256 !== context.source_sha256 || candidate.device_id !== context.device_id ||
      candidate.target !== context.target || candidate.output_authority !== 'local-file-only' ||
      candidate.changes.some((change) => !context.parameters.includes(change.parameter) || context.locks.includes(change.parameter)),
    )) {
    throw new Error('Returned candidates do not match the exact source, segment and field scope. Refresh and generate again.');
  }
}

/** Transient UI drafts only. All sound sessions/favorites/feedback persist on the server. */
export class ReferenceSoundModel {
  private view: ReferenceSoundView = {
    sessions: [], session: null, controls: [], sourceId: '', deviceId: 'analog_rytm_mk2', target: 1,
    parameters: [], locks: [], strength: 0.5, startFrame: 0, frameCount: 0, stale: false,
    busy: null, received: 0, uploadSize: 0, error: null,
    originalUrl: null, segmentUrl: null, recordingUrl: null, recordingSha: null,
  };
  private readonly listeners = new Set<() => void>();
  private revision = 0;
  private uploadOpen = false;
  private disposed = false;
  private records: readonly LibraryRecord[] = [];

  constructor(private readonly client: Pick<CockpitClient, 'send'>,
    private readonly publishLibrary: (records: LibraryRecord[]) => void) {}

  activate(): void { this.disposed = false; }

  snapshot = (): ReferenceSoundView => this.view;
  subscribe = (listener: () => void): (() => void) => {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  };

  private update(patch: Partial<ReferenceSoundView>): void {
    if (this.disposed) return;
    this.view = { ...this.view, ...patch };
    for (const listener of this.listeners) listener();
  }

  setRecords(records: readonly LibraryRecord[]): void {
    const previous = this.records.find((record) => record.record_id === this.view.sourceId);
    this.records = nativeSources(records);
    const source = this.records.find((record) => record.record_id === this.view.sourceId);
    if (this.view.sourceId !== '' && (source === undefined ||
      (previous !== undefined && source.source_frame?.sha256 !== previous.source_frame?.sha256))) {
      this.invalidate();
      this.update({ sourceId: '', controls: [], parameters: [], locks: [] });
    }
  }

  private check(revision: number): void {
    if (this.disposed || revision !== this.revision) throw new Superseded();
  }

  private async request(action: ReferenceSoundAction, revision: number): Promise<ReferenceSoundReply> {
    this.check(revision);
    const heavy = action.action === 'generate' || action.action === 'record' || action.action === 'refine';
    const ack = await this.client.send({ type: 'reference_sound', ...action },
      heavy ? { timeoutMs: SOUND_ANALYSIS_TIMEOUT_MS } : undefined);
    this.check(revision);
    if (!ack.ok) throw new Error(ack.message ?? ack.code ?? ack.error ?? 'Reference-sound request refused.');
    if (ack.reference_sound === undefined) throw new Error('Sidecar did not return reference-sound data. Refresh the session.');
    return ack.reference_sound;
  }

  private async sessionRequest(action: ReferenceSoundAction, revision: number): Promise<ReferenceSoundSession> {
    const reply = await this.request(action, revision);
    if (!('session' in reply)) throw new Error('Sidecar did not return a retained session.');
    return reply.session;
  }

  private async run(label: string, execute: (revision: number) => Promise<void>): Promise<void> {
    if (this.disposed || this.view.busy !== null) return;
    const revision = this.revision;
    this.update({ busy: label, error: null, received: 0, uploadSize: 0 });
    try {
      await execute(revision);
    } catch (error) {
      if (!(error instanceof Superseded)) {
        this.update({ error: error instanceof Error ? error.message : 'Reference-sound operation failed.' });
        if (this.uploadOpen) await this.cancelRemote();
      }
    } finally {
      this.update({ busy: null });
    }
  }

  private async cancelRemote(): Promise<void> {
    try {
      const ack = await this.client.send({ type: 'reference_sound', action: 'cancel' });
      if (!ack.ok) throw new Error(ack.message ?? 'Cancellation refused. Reconnect before continuing.');
      this.uploadOpen = false;
    } catch (error) {
      this.update({ error: error instanceof Error ? error.message : 'Cancellation failed. Reconnect before continuing.' });
    }
  }

  cancel = async (): Promise<void> => {
    this.revision++;
    await this.cancelRemote();
  };

  invalidate(): void {
    this.revision++;
    this.update({ stale: this.view.session?.context != null, error: null });
    if (this.view.busy !== null) void this.cancelRemote();
  }

  setSegment(startFrame: number, frameCount: number): void {
    this.invalidate();
    this.update({ startFrame, frameCount });
  }

  setStrength(strength: number): void {
    this.invalidate();
    this.update({ strength });
  }

  toggleField(parameter: string, lock: boolean): void {
    if (!this.view.controls.some((control) => control.parameter === parameter && control.mutable)) return;
    this.invalidate();
    const key = lock ? 'locks' : 'parameters';
    const current = this.view[key];
    this.update({ [key]: current.includes(parameter) ? current.filter((item) => item !== parameter) : [...current, parameter] });
  }

  private setAudio(key: 'originalUrl' | 'segmentUrl' | 'recordingUrl', blob: Blob | null): void {
    const previous = this.view[key];
    if (previous !== null) URL.revokeObjectURL(previous);
    this.update({ [key]: blob === null ? null : URL.createObjectURL(blob) });
    if (key === 'recordingUrl' && blob === null) this.update({ recordingSha: null });
  }

  private adopt(session: ReferenceSoundSession): void {
    const summary: ReferenceSoundSessionSummary = {
      session_id: session.session_id, title: session.title, segment: session.segment, context: session.context,
      favorites: session.favorites, candidate_count: session.candidates.length, recording_count: session.recordings.length,
    };
    this.update({ session, sessions: [summary, ...this.view.sessions.filter((item) => item.session_id !== session.session_id)],
      startFrame: session.segment.start_frame, frameCount: session.segment.frame_count, stale: false });
  }

  refresh = async (): Promise<void> => this.run('Loading sessions', async (revision) => {
    const reply = await this.request({ action: 'list' }, revision);
    if (!('sessions' in reply)) throw new Error('Sidecar did not return the session catalog.');
    this.update({ sessions: reply.sessions });
  });

  loadLibrary = async (importCaptures = false): Promise<void> => this.run('Loading native source library', async (revision) => {
    if (importCaptures) {
      const imported = await this.client.send({ type: 'library_import_captures' });
      this.check(revision);
      if (!imported.ok) throw new Error(imported.message ?? 'Capture import refused.');
    }
    const ack = await this.client.send({ type: 'library_list' });
    this.check(revision);
    if (!ack.ok || ack.library_records == null) throw new Error(ack.message ?? 'Source library could not be loaded.');
    this.setRecords(ack.library_records);
    this.publishLibrary(ack.library_records);
  });

  chooseSource = async (sourceId: string, deviceId: KitCaptureDeviceId, target: number): Promise<void> => {
    this.invalidate();
    this.update({ sourceId, deviceId, target, controls: [], parameters: [], locks: [] });
    if (sourceId === '') return;
    await this.run('Reading native fields', async (revision) => {
      const reply = await this.request({ action: 'controls', source_record_id: sourceId, device_id: deviceId, target }, revision);
      if (!('controls' in reply)) throw new Error('Sidecar did not return native source fields.');
      this.update({ controls: reply.controls, parameters: reply.controls.filter((control) => control.mutable).map((control) => control.parameter) });
    });
  };

  private async upload(file: File, revision: number): Promise<string> {
    if (!/\.wav$/i.test(file.name) || file.size < 44 || file.size > SOUND_MAX_BYTES) {
      throw new Error('Choose a PCM WAV between 44 bytes and 16 MiB; references must be at most 120 seconds.');
    }
    this.uploadOpen = true;
    const begin = await this.request({ action: 'upload_begin', size: file.size }, revision);
    if (!('upload_id' in begin) || begin.received !== 0) throw new Error('Invalid upload acknowledgement. Cancel and choose the WAV again.');
    this.update({ uploadSize: file.size });
    for (let offset = 0; offset < file.size; offset += SOUND_CHUNK_BYTES) {
      const bytes = new Uint8Array(await file.slice(offset, offset + SOUND_CHUNK_BYTES).arrayBuffer());
      const reply = await this.request({ action: 'upload_chunk', upload_id: begin.upload_id, offset, chunk: encodeSoundBytes(bytes) }, revision);
      if (!('received' in reply) || reply.upload_id !== begin.upload_id || reply.received !== offset + bytes.length) {
        throw new Error('Upload position disagrees with the sidecar. Choose the WAV again.');
      }
      this.update({ received: reply.received });
    }
    return begin.upload_id;
  }

  importReference = async (file: File): Promise<void> => this.run('Uploading reference', async (revision) => {
    const uploadId = await this.upload(file, revision);
    const session = await this.sessionRequest({ action: 'upload_finish', upload_id: uploadId, title: file.name.slice(0, 120) }, revision);
    this.uploadOpen = false;
    this.setAudio('segmentUrl', null);
    this.adopt(session);
    this.setAudio('originalUrl', file);
    this.setAudio('recordingUrl', null);
    await this.readSegment(session, revision);
  });

  private async readSegment(session: ReferenceSoundSession, revision: number): Promise<void> {
    this.setAudio('segmentUrl', await this.readAudio(session, {}, revision));
  }

  private async readAudio(session: ReferenceSoundSession, selection: ReferenceSoundAudioSelection, revision: number): Promise<Blob> {
    const expectedSha = selection.audio_kind === 'original' ? session.segment.original.sha256
      : selection.audio_kind === 'recording' ? selection.recording_sha256 : session.segment.sha256;
    const parts: Uint8Array<ArrayBuffer>[] = [];
    let offset = 0;
    let size = 0;
    do {
      const reply = await this.request({ action: 'read_audio', session_id: session.session_id, offset, ...selection }, revision);
      if (!('audio_chunk' in reply) || reply.offset !== offset || reply.sha256 !== expectedSha ||
        reply.size < 44 || reply.size > SOUND_MAX_BYTES || (offset > 0 && reply.size !== size)) {
        throw new Error('Retained audio identity or playback position changed. Reopen the session.');
      }
      size = reply.size;
      const bytes = decodeSoundBytes(reply.audio_chunk);
      if (bytes.length === 0 || bytes.length > SOUND_CHUNK_BYTES || offset + bytes.length > size) {
        throw new Error('Retained audio chunk is empty or exceeds its declared size.');
      }
      parts.push(bytes);
      offset += bytes.length;
    } while (offset < size);
    const blob = new Blob(parts, { type: 'audio/wav' });
    if (await digest(new Uint8Array(await blob.arrayBuffer())) !== expectedSha) {
      throw new Error('Retained audio checksum failed. Restore its saved WAV.');
    }
    this.check(revision);
    return blob;
  }

  playReference = async (kind: 'original' | 'segment'): Promise<void> => this.run('Loading retained reference playback', async (revision) => {
    const session = this.view.session;
    if (session === null) throw new Error('Choose a retained reference session before loading playback.');
    this.setAudio(kind === 'original' ? 'originalUrl' : 'segmentUrl',
      await this.readAudio(session, { audio_kind: kind }, revision));
  });

  private async restoreRecording(session: ReferenceSoundSession, revision: number): Promise<void> {
    const recording = currentSoundRecordings(this.view).at(-1);
    if (recording === undefined) return;
    const blob = await this.readAudio(session, { audio_kind: 'recording', recording_sha256: recording.audio_sha256 }, revision);
    this.setAudio('recordingUrl', blob);
    this.update({ recordingSha: recording.audio_sha256 });
  }

  playRecording = async (recordingSha: string): Promise<void> => this.run('Loading retained supplied recording', async (revision) => {
    if (!currentSoundRecordings(this.view).some((recording) => recording.audio_sha256 === recordingSha)) {
      throw new Error('Choose a retained supplied recording of this exact candidate in the selected session.');
    }
    this.setAudio('recordingUrl', null);
    this.update({ recordingSha });
    const blob = await this.readAudio(this.view.session!, { audio_kind: 'recording', recording_sha256: recordingSha }, revision);
    this.setAudio('recordingUrl', blob);
  });

  applySegment = async (): Promise<void> => this.run('Retaining exact segment', async (revision) => {
    if (!segmentIsValid(this.view)) throw new Error('Select an exact 0.05-8 second segment within the original frame count.');
    const session = this.view.session!;
    const next = await this.sessionRequest({ action: 'segment', session_id: session.session_id,
      start_frame: this.view.startFrame, frame_count: this.view.frameCount }, revision);
    this.adopt(next);
    this.setAudio('segmentUrl', null);
    this.setAudio('recordingUrl', null);
    await this.readSegment(next, revision);
  });

  generate = async (): Promise<void> => this.run('Analyzing and generating eight alternatives', async (revision) => {
    const { session, sourceId, deviceId, target, parameters, locks, strength, startFrame, frameCount } = this.view;
    const source = this.records.find((record) => record.record_id === sourceId);
    if (session === null || source?.source_frame == null || source.device_id !== deviceId ||
      !segmentIsValid(this.view) || startFrame !== session.segment.start_frame || frameCount !== session.segment.frame_count ||
      !parameters.some((parameter) => !locks.includes(parameter)) || !Number.isFinite(strength) || strength < 0 || strength > 1) {
      throw new Error('Retain a valid segment, choose a native KIT and select at least one unlocked supported field.');
    }
    const context: ReferenceSoundContext = { source_sha256: source.source_frame.sha256, segment_sha256: session.segment.sha256,
      device_id: deviceId, target, parameters, locks, strength };
    const next = await this.sessionRequest({ action: 'generate', session_id: session.session_id,
      source_record_id: sourceId, device_id: deviceId, target, parameters, locks, strength }, revision);
    assertSoundContext(next, context);
    this.adopt(next);
    this.setAudio('recordingUrl', null);
  });

  reopen = async (sessionId: string): Promise<void> => this.run('Reopening retained session', async (revision) => {
    const session = await this.sessionRequest({ action: 'reopen', session_id: sessionId }, revision);
    this.adopt(session);
    this.setAudio('originalUrl', null);
    this.setAudio('segmentUrl', null);
    this.setAudio('recordingUrl', null);
    const context = session.context;
    if (context !== null) {
      const source = this.records.find((record) => record.device_id === context.device_id && record.source_frame?.sha256 === context.source_sha256);
      this.update({ sourceId: source?.record_id ?? '', deviceId: context.device_id, target: context.target,
        parameters: context.parameters, locks: context.locks, strength: context.strength, controls: [] });
      if (source !== undefined) {
        const reply = await this.request({ action: 'controls', source_record_id: source.record_id, device_id: context.device_id, target: context.target }, revision);
        if (!('controls' in reply)) throw new Error('Sidecar did not return native source fields.');
        this.update({ controls: reply.controls });
      }
    }
    this.setAudio('originalUrl', await this.readAudio(session, { audio_kind: 'original' }, revision));
    await this.readSegment(session, revision);
    await this.restoreRecording(session, revision);
  });

  select = async (candidateId: string, favorite?: boolean): Promise<void> => this.run('Retaining selection', async (revision) => {
    const session = this.view.session;
    if (session === null || this.view.stale) throw new Error('Generate again before choosing a candidate from changed scope.');
    const action: ReferenceSoundAction = favorite === undefined
      ? { action: 'select', session_id: session.session_id, candidate_id: candidateId }
      : { action: 'favorite', session_id: session.session_id, candidate_id: candidateId, favorite };
    const next = await this.sessionRequest(action, revision);
    const changed = next.selected_candidate_id !== session.selected_candidate_id;
    if (changed) this.setAudio('recordingUrl', null);
    this.adopt(next);
    if (changed) await this.restoreRecording(next, revision);
  });

  record = async (file: File): Promise<void> => this.run('Uploading and measuring supplied recording', async (revision) => {
    const candidate = selectedSound(this.view);
    if (candidate === undefined || this.view.session!.recordings.length >= 16) throw new Error('Choose a current candidate; this session allows at most 16 recordings.');
    const uploadId = await this.upload(file, revision);
    const session = await this.sessionRequest({ action: 'record', session_id: this.view.session!.session_id,
      candidate_id: candidate.candidate_id, candidate_sha256: candidate.frame_sha256, upload_id: uploadId }, revision);
    this.uploadOpen = false;
    this.adopt(session);
    this.setAudio('recordingUrl', file);
    this.update({ recordingSha: currentSoundRecordings(this.view).at(-1)!.audio_sha256 });
  });

  refine = async (gain: number): Promise<void> => this.run('Refining measured candidate', async (revision) => {
    const candidate = selectedSound(this.view);
    const session = this.view.session;
    if (candidate === undefined || session === null || session.refinements.length >= 3 || !Number.isFinite(gain) || gain < 0 || gain > 1 ||
      !session.recordings.some((record) => record.candidate_id === candidate.candidate_id && record.candidate_sha256 === candidate.frame_sha256)) {
      throw new Error('Supply a recording of this exact candidate first. Refinement gain is 0-1, with at most three rounds.');
    }
    const latest = currentSoundRecordings(this.view).at(-1)!;
    if (this.view.recordingSha !== null && this.view.recordingSha !== latest.audio_sha256) {
      throw new Error('Select the latest supplied recording for refinement; older recordings remain available for comparison.');
    }
    const next = await this.sessionRequest({ action: 'refine', session_id: session.session_id, candidate_id: candidate.candidate_id, correction_gain: gain }, revision);
    this.adopt(next);
    if (next.selected_candidate_id !== candidate.candidate_id) this.setAudio('recordingUrl', null);
  });

  download = async (destinationSlot: number): Promise<void> => this.run('Preparing native SysEx download', async (revision) => {
    const candidate = selectedSound(this.view);
    if (candidate === undefined) throw new Error('Choose a current candidate before exporting.');
    if (!Number.isInteger(destinationSlot) || destinationSlot < 0 || destinationSlot > 127) {
      throw new Error('Enter an explicit scratch KIT slot from 1 to 128 before downloading.');
    }
    const reply = await this.request({ action: 'export', session_id: this.view.session!.session_id,
      candidate_id: candidate.candidate_id, destination_slot: destinationSlot }, revision);
    if (!('sysex_base64' in reply) || reply.candidate_id !== candidate.candidate_id || reply.destination_slot !== destinationSlot) {
      throw new Error('Export identity does not match the chosen candidate.');
    }
    const bytes = decodeSoundBytes(reply.sysex_base64);
    if (bytes.length !== candidate.frame_size || await digest(bytes) !== reply.sha256) throw new Error('Export checksum failed. Reopen the retained candidate.');
    this.check(revision);
    const url = URL.createObjectURL(new Blob([bytes], { type: 'application/octet-stream' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = `KIT${String(destinationSlot + 1).padStart(3, '0')}-${candidate.candidate_id.replace(/[^a-zA-Z0-9_-]/g, '_')}.syx`;
    link.click();
    // Delay revocation until the browser has consumed the download URL.
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  dispose = (): void => {
    this.revision++;
    if (this.view.busy !== null) void this.cancelRemote();
    this.setAudio('originalUrl', null);
    this.setAudio('segmentUrl', null);
    this.setAudio('recordingUrl', null);
    this.disposed = true;
    this.listeners.clear();
  };
}
