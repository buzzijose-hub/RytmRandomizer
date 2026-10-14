import { createHash } from 'node:crypto';
import { File as NodeFile } from 'node:buffer';
import { vi } from 'vitest';

import type { Command, CommandAck, LibraryRecord } from '../../src/ws/protocol';
import type { SendCommandOptions } from '../../src/ws/client';
import type { ReferenceSoundAnalysis, ReferenceSoundCandidate, ReferenceSoundControl, ReferenceSoundRecording, ReferenceSoundReply, ReferenceSoundSession, ReferenceSoundSessionSummary } from '../../src/ws/referenceSound';
import { ReferenceSoundModel, SOUND_CHUNK_BYTES } from '../../src/cockpit/referenceSound/referenceSoundModel';
import { FakeCockpitClient } from './_fixtures';

export function sha(bytes: Uint8Array): string { return createHash('sha256').update(bytes).digest('hex'); }

export function wav(frames = 8000, rate = 8000): Uint8Array<ArrayBuffer> {
  const bytes = new Uint8Array(44 + frames * 2);
  const view = new DataView(bytes.buffer);
  for (const [offset, text] of [[0, 'RIFF'], [8, 'WAVE'], [12, 'fmt '], [36, 'data']] as const) {
    for (let index = 0; index < text.length; index++) bytes[offset + index] = text.charCodeAt(index);
  }
  view.setUint32(4, bytes.length - 8, true);
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, rate, true);
  view.setUint32(28, rate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  view.setUint32(40, frames * 2, true);
  return bytes;
}

export function audioFile(bytes = wav(), name = 'reference.wav'): File {
  // jsdom's File lacks Blob.arrayBuffer; use the existing Node Web File API.
  return new NodeFile([bytes], name, { type: 'audio/wav' }) as unknown as File;
}

export const patchBytes = Uint8Array.from([0xf0, 0x01, 0xf7]);
export const sourceRecord: LibraryRecord = {
  record_id: 'native-source', device_id: 'analog_rytm_mk2', kit_name: 'Native kit', fingerprint: 'fingerprint',
  captured_at: '2026-10-12', tags: [], payload_hex: '',
  source_frame: { artifact_name: 'source.syx', sha256: sha(patchBytes), byte_count: 3 }, source_origin: 'file_import',
};
export const soundControls: ReferenceSoundControl[] = [
  { parameter: 'dec', source_value: 64, source_display: '64', units: 'native u7 coarse; companion byte retained',
    domain: { minimum: 0, maximum: 127, quantum: 1, values: [] }, offsets: [100], reasons: [], mutable: true,
    output_authority: 'local-file-only', send_supported: false },
  { parameter: 'lev', source_value: 80, source_display: '80', units: 'u7',
    domain: { minimum: 0, maximum: 127, quantum: 1, values: [] }, offsets: [101], reasons: [], mutable: true,
    output_authority: 'local-file-only', send_supported: false },
  { parameter: 'unsupported', source_value: 7, source_display: null, units: 'unknown', domain: null, offsets: [102],
    reasons: ['mandatory_parameter_protection'], mutable: false, output_authority: 'local-file-only', send_supported: false },
];

export function analysis(audio = wav()): ReferenceSoundAnalysis {
  return {
    report: { source_type: 'audio', confidence: 'medium', bpm: 0, tempo_stability: 0, kick_density: 0, percussion_density: 0,
      low_end_weight: 0.5, spectral_brightness: 0.5, texture_noise: 0.5, energy_arc: [0.5], content_hash: sha(audio), derived_at: '2026-10-12' },
    features: { audio_sha256: sha(audio), duration: 1, attack: 0.5, decay: 0.5, sustain: 0.5, tail: 0.5, brightness: 0.5,
      spectral_flatness: 0.5, noise: 0.5, low_end: 0.5, harmonicity: 0.5, transient: 0.5, modulation: 0.5 },
    evidence: { dominant_frequency_hz: null, dominant_note: null, pitch_confidence: 0, tonal_stability: 0.5, spectral_movement: 0.5 },
    // Controlled fake DSP metadata for workflow tests, never acoustic evidence.
    diagnostics: { audio_sha256: sha(audio), pcm_sha256: sha(audio), sample_rate: 8000, channels: 1,
      start_sample: 0, sample_count: (audio.length - 44) / 2, pitch_method: 'librosa.pyin.v1',
      qualified_pitch_hz: 440, spectral_peak_hz: 440, rms: 0.1, peak: 0.2, clipped_fraction: 0,
      pitch_status: 'qualified', pitch_confidence: 0.9, voiced_fraction: 0.9, pitch_stability_cents: 0,
      octave_ambiguous: false, frame_count: 10, stable_pitch_frame_count: 9, onset_count: 0, note_count: 1,
      multiple_pitch: false, warnings: [], refinement_blockers: [] },
  };
}

export function soundSession(audio = wav(), generated = false): ReferenceSoundSession {
  const measured = analysis(audio);
  const rate = new DataView(audio.buffer, audio.byteOffset).getUint32(24, true);
  const candidates: ReferenceSoundCandidate[] = Array.from({ length: 8 }, (_, index) => ({
    candidate_id: `candidate-${index + 1}`, label: `Alternative ${index + 1}`, direction: `direction-${index + 1}`,
    device_id: 'analog_rytm_mk2', target: 1, source_sha256: sha(patchBytes), frame_sha256: sha(patchBytes), frame_size: patchBytes.length,
    changes: [{ parameter: 'dec', source_value: 64, proposed_value: 80 + index, rendered_value: 72 + index,
      source_display: '64', proposed_display: String(80 + index), rendered_display: String(72 + index), units: 'u7',
      rationale: 'Measured decay contribution; bounded blend from source.', offsets: [100] }],
    limitations: ['Local file only; no verified physical match'], intended_unpacked_offsets: [100], changed_unpacked_offsets: [100],
    changed_wire_offsets: [1], features: measured.features, output_authority: 'local-file-only', hardware_send_validated: false, roundtrip_redecoded: true,
  }));
  return { schema_version: 1, session_id: generated ? 'sound-generated' : 'sound-original', title: 'reference.wav',
    segment: { original: { sample_rate: rate, channels: 1, sample_width: 2, frame_count: (audio.length - 44) / 2,
      sha256: sha(audio), seconds: (audio.length - 44) / (rate * 2) }, start_frame: 0, frame_count: (audio.length - 44) / 2, sha256: sha(audio) },
    context: generated ? { device_id: 'analog_rytm_mk2', target: 1, source_sha256: sha(patchBytes), segment_sha256: sha(audio), parameters: ['dec', 'lev'], locks: [], strength: 0.5 } : null,
    analysis: generated ? measured : null, candidates: generated ? candidates : [], selected_candidate_id: generated ? 'candidate-1' : null,
    favorites: [], recordings: [], refinements: [],
  };
}

export function soundAck(reference_sound: ReferenceSoundReply): CommandAck { return { ok: true, request_id: 'sound-test', reference_sound }; }

export function soundSummary(session = soundSession()): ReferenceSoundSessionSummary {
  return { session_id: session.session_id, title: session.title, segment: session.segment, context: session.context,
    favorites: session.favorites, candidate_count: session.candidates.length, recording_count: session.recordings.length };
}

export function soundHarness(audio = wav()) {
  const fake = new FakeCockpitClient();
  let session = soundSession(audio);
  let received = 0;
  let uploadParts: Uint8Array[] = [];
  let segmentAudio = audio;
  const recordedAudio = new Map<string, Uint8Array<ArrayBuffer>>([[sha(audio), audio]]);
  const calls: Array<{ command: Command; options: SendCommandOptions | undefined }> = [];
  const published = vi.fn();
  const send = vi.spyOn(fake, 'send').mockImplementation(async (command: Command, options?: SendCommandOptions) => {
    calls.push({ command, options });
    if (command.type === 'library_import_captures') return { ok: true, request_id: 'import' };
    if (command.type === 'library_list') return { ok: true, request_id: 'library', library_records: [sourceRecord] };
    if (command.type !== 'reference_sound') throw new Error('Unexpected non-reference command');
    switch (command.action) {
      case 'cancel': return soundAck({ cancelled: true });
      case 'list': return soundAck({ sessions: [soundSummary(session)] });
      case 'controls': return soundAck({ controls: soundControls });
      case 'upload_begin': received = 0; uploadParts = []; return soundAck({ upload_id: 'owned-upload', received });
      case 'upload_chunk': {
        const bytes = Uint8Array.from(atob(command.chunk), (character) => character.charCodeAt(0));
        uploadParts.push(bytes);
        received += bytes.length;
        return soundAck({ upload_id: command.upload_id, received });
      }
      case 'upload_finish': segmentAudio = audio; session = soundSession(audio); return soundAck({ session });
      case 'read_audio': {
        const bytes = command.audio_kind === 'original' ? audio
          : command.audio_kind === 'recording' ? recordedAudio.get(command.recording_sha256)! : segmentAudio;
        return soundAck({ audio_chunk: Buffer.from(bytes.slice(command.offset, command.offset + SOUND_CHUNK_BYTES)).toString('base64'),
          size: bytes.length, offset: command.offset, sha256: sha(bytes) });
      }
      case 'segment': segmentAudio = wav(command.frame_count, session.segment.original.sample_rate);
        session = { ...soundSession(audio), segment: { ...session.segment, start_frame: command.start_frame, frame_count: command.frame_count, sha256: sha(segmentAudio) } }; return soundAck({ session });
      case 'generate': session = { ...soundSession(audio, true), segment: session.segment, context: { ...soundSession(audio, true).context!,
        segment_sha256: session.segment.sha256, parameters: command.parameters, locks: command.locks, strength: command.strength, device_id: command.device_id, target: command.target },
        candidates: soundSession(audio, true).candidates.map((candidate) => ({ ...candidate, device_id: command.device_id, target: command.target })) }; return soundAck({ session });
      case 'reopen': return soundAck({ session });
      case 'select': session = { ...session, selected_candidate_id: command.candidate_id }; return soundAck({ session });
      case 'favorite': session = { ...session, selected_candidate_id: command.candidate_id, favorites: command.favorite ? [command.candidate_id] : [] }; return soundAck({ session });
      case 'record': {
        const original = Uint8Array.from(Buffer.concat(uploadParts));
        const info = soundSession(original).segment.original;
        const start = command.start_frame ?? 0;
        const count = command.frame_count ?? info.frame_count;
        const bytes = wav(count, info.sample_rate);
        bytes.set(original.subarray(44 + start * 2, 44 + (start + count) * 2), 44);
        const measured = analysis(bytes);
        const weights: ReadonlyArray<[ReferenceSoundRecording['feature_deltas'][number]['feature'], number]> = [
          ['attack', 0.12], ['decay', 0.09], ['sustain', 0.08], ['tail', 0.08], ['brightness', 0.15], ['spectral_flatness', 0.08],
          ['noise', 0.10], ['low_end', 0.12], ['harmonicity', 0.08], ['transient', 0.06], ['modulation', 0.04],
        ];
        for (const [feature] of weights) measured.features[feature] = 0.6;
        recordedAudio.set(sha(bytes), bytes);
        session = { ...session, recordings: [...session.recordings, { candidate_id: command.candidate_id, candidate_sha256: command.candidate_sha256,
        audio_sha256: sha(bytes), features: measured, score: 90, distance: 0.1,
        feature_deltas: weights.map(([feature, weight]) => ({ feature, reference_value: 0.5, render_value: 0.6, absolute_delta: 0.1, weight, weighted_delta: 0.1 * weight })),
        metric: 'weighted normalized 11-feature L1 distance; score = round(100 * (1 - distance)); not a probability or verified sound match', physical_validation: false,
        segment: { original: info, start_frame: start, frame_count: count, sha256: sha(bytes) },
        pitch_comparison: { delta_cents: 0, octave_difference: 0, support_status: 'supported', blockers: [] } }] }; return soundAck({ session });
      }
      case 'refine': {
        const recording = session.recordings.filter((item) => item.candidate_id === command.candidate_id).at(-1)!;
        if (recording.distance === 0) return soundAck({ session });
        const candidate = { ...session.candidates.find((item) => item.candidate_id === command.candidate_id)!, candidate_id: `refined-${session.refinements.length + 1}` };
        session = { ...session, candidates: [...session.candidates, candidate], selected_candidate_id: candidate.candidate_id,
          refinements: [...session.refinements, { parent_id: command.candidate_id, recording_sha256: recording.audio_sha256, gain: command.correction_gain,
            features: analysis(audio).features }] }; return soundAck({ session });
      }
      case 'measure': session = { ...session, analysis: { ...session.analysis!, diagnostics: analysis(audio).diagnostics! } }; return soundAck({ session });
      case 'export': return soundAck({ sysex_base64: Buffer.from(patchBytes).toString('base64'), sha256: sha(patchBytes),
        candidate_id: command.candidate_id, destination_slot: command.destination_slot });
    }
  });
  const model = new ReferenceSoundModel(fake.asClient(), published);
  model.setRecords([sourceRecord]);
  return { fake, model, send, calls, published, getSession: () => session,
    addRecordingAudio: (bytes: Uint8Array<ArrayBuffer>) => { recordedAudio.set(sha(bytes), bytes); },
    setSession: (value: ReferenceSoundSession) => {
      session = value;
      segmentAudio = wav(value.segment.frame_count, value.segment.original.sample_rate);
      segmentAudio.set(audio.subarray(44 + value.segment.start_frame * 2, 44 + (value.segment.start_frame + value.segment.frame_count) * 2), 44);
    } };
}

export async function prepareSound(harness: ReturnType<typeof soundHarness>): Promise<void> {
  await harness.model.importReference(audioFile());
  await harness.model.chooseSource(sourceRecord.record_id, 'analog_rytm_mk2', 1);
  await harness.model.generate();
}
