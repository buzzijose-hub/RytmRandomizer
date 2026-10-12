import type { KitCaptureDeviceId } from './protocol';

/** Wire mirrors of cockpit/export/reference_sound_*; no live-output authority. */
export interface ReferenceSoundFeatures {
  audio_sha256: string;
  duration: number;
  attack: number;
  decay: number;
  sustain: number;
  tail: number;
  brightness: number;
  spectral_flatness: number;
  noise: number;
  low_end: number;
  harmonicity: number;
  transient: number;
  modulation: number;
}

export interface ReferenceSoundAnalysis {
  report: {
    source_type: string;
    confidence: string;
    bpm: number;
    tempo_stability: number;
    kick_density: number;
    percussion_density: number;
    low_end_weight: number;
    spectral_brightness: number;
    texture_noise: number;
    energy_arc: number[];
    content_hash: string;
    derived_at: string;
  };
  features: ReferenceSoundFeatures;
  evidence: {
    dominant_frequency_hz: number | null;
    dominant_note: string | null;
    pitch_confidence: number;
    tonal_stability: number;
    spectral_movement: number;
  };
}

export interface ReferenceAudioInfo {
  sample_rate: number;
  channels: number;
  sample_width: number;
  frame_count: number;
  sha256: string;
  seconds: number;
}

export interface ReferenceSoundControl {
  parameter: string;
  source_value: number;
  source_display: string | null;
  units: string;
  domain: { minimum: number; maximum: number; quantum: number; values: number[] } | null;
  offsets: number[];
  reasons: string[];
  mutable: boolean;
  output_authority: 'local-file-only';
  send_supported: false;
}

export interface ReferenceSoundChange {
  parameter: string;
  source_value: number;
  proposed_value: number;
  rendered_value: number;
  source_display: string | null;
  proposed_display: string;
  rendered_display: string | null;
  units: string;
  rationale: string;
  offsets: number[];
}

export interface ReferenceSoundCandidate {
  candidate_id: string;
  direction: string;
  label: string;
  device_id: KitCaptureDeviceId;
  target: number;
  source_sha256: string;
  frame_sha256: string;
  frame_size: number;
  changes: ReferenceSoundChange[];
  limitations: string[];
  intended_unpacked_offsets: number[];
  changed_unpacked_offsets: number[];
  changed_wire_offsets: number[];
  features: ReferenceSoundFeatures;
  output_authority: 'local-file-only';
  hardware_send_validated: false;
  roundtrip_redecoded: true;
}

export interface ReferenceSoundContext {
  device_id: KitCaptureDeviceId;
  target: number;
  source_sha256: string;
  segment_sha256: string;
  parameters: string[];
  locks: string[];
  strength: number;
}

export interface ReferenceSoundRecording {
  candidate_id: string;
  candidate_sha256: string;
  audio_sha256: string;
  features: ReferenceSoundAnalysis;
  distance: number;
  score: number;
  metric: string;
  feature_deltas: {
    feature: keyof Omit<ReferenceSoundFeatures, 'audio_sha256' | 'duration'>;
    reference_value: number;
    render_value: number;
    absolute_delta: number;
    weight: number;
    weighted_delta: number;
  }[];
  physical_validation: false;
}

export type ReferenceSoundAudioSelection =
  | { audio_kind?: 'segment' | 'original'; recording_sha256?: never }
  | { audio_kind: 'recording'; recording_sha256: string };

export interface ReferenceSoundSession {
  schema_version: 1;
  session_id: string;
  title: string;
  segment: { original: ReferenceAudioInfo; start_frame: number; frame_count: number; sha256: string };
  context: ReferenceSoundContext | null;
  analysis: ReferenceSoundAnalysis | null;
  candidates: ReferenceSoundCandidate[];
  selected_candidate_id: string | null;
  favorites: string[];
  recordings: ReferenceSoundRecording[];
  refinements: { parent_id: string; recording_sha256: string; gain: number; features: ReferenceSoundFeatures }[];
}

export interface ReferenceSoundSessionSummary {
  session_id: string;
  title: string;
  segment: ReferenceSoundSession['segment'];
  context: ReferenceSoundContext | null;
  favorites: string[];
  candidate_count: number;
  recording_count: number;
}

export type ReferenceSoundAction =
  | { action: 'upload_begin'; size: number }
  | { action: 'upload_chunk'; upload_id: string; offset: number; chunk: string }
  | { action: 'upload_finish'; upload_id: string; title: string }
  | { action: 'cancel' }
  | { action: 'list' }
  | { action: 'controls'; source_record_id: string; device_id: KitCaptureDeviceId; target: number }
  | { action: 'segment'; session_id: string; start_frame: number; frame_count: number }
  | { action: 'generate'; session_id: string; source_record_id: string; device_id: KitCaptureDeviceId; target: number; parameters: string[]; locks: string[]; strength: number }
  | { action: 'select'; session_id: string; candidate_id: string }
  | { action: 'favorite'; session_id: string; candidate_id: string; favorite: boolean }
  | { action: 'record'; session_id: string; candidate_id: string; candidate_sha256: string; upload_id: string }
  | { action: 'refine'; session_id: string; candidate_id: string; correction_gain: number }
  | { action: 'reopen'; session_id: string }
  | ({ action: 'read_audio'; session_id: string; offset: number } & ReferenceSoundAudioSelection)
  | { action: 'export'; session_id: string; candidate_id: string; destination_slot: number };

export type ReferenceSoundCommand = { type: 'reference_sound' } & ReferenceSoundAction;

export type ReferenceSoundReply =
  | { upload_id: string; received: number }
  | { cancelled: true }
  | { sessions: ReferenceSoundSessionSummary[] }
  | { controls: ReferenceSoundControl[] }
  | { session: ReferenceSoundSession }
  | { audio_chunk: string; size: number; offset: number; sha256: string }
  | { sysex_base64: string; sha256: string; candidate_id: string; destination_slot: number };
