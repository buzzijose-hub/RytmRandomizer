/**
 * Wizard wire-format types — one-to-one mirror of `cockpit/ws/wizard_protocol.py`.
 *
 * Source spec: `docs/superpowers/specs/2026-05-24-profile-wizard-design.md` (Phase 2).
 *
 * Any change here MUST be matched on the Python side. Keep this file flat — it's a pure
 * type module so the data model is grep-able without indirection.
 */

import type { ProfileKind, StyleTrait, TraitPadWeight, TransitionCurve } from '../ws/protocol';

// ---------- Domain enums (literal unions) ----------

/** Kind of inspiration the operator points the wizard at. */
export type WizardSourceKind = 'kit' | 'sound' | 'song' | 'album' | 'artist';

/** How the operator supplied the source: a file on disk, a folder, or a textual reference. */
export type WizardSourceMode = 'file' | 'folder' | 'reference';

/** Lifecycle status for an analysis job. */
export type AnalysisStatus = 'pending' | 'analyzing' | 'ok' | 'failed';

/** Four sequential wizard steps the operator walks through. */
export type WizardStep = 'name' | 'add' | 'analyze' | 'review';

// ---------- Core wizard data abstractions ----------

export interface InspirationSource {
  source_id: string; // ULID
  kind: WizardSourceKind;
  mode: WizardSourceMode;
  /** Path for file/folder sources; the textual name for reference sources. */
  location: string;
  display_name: string;
  /** ISO-8601 UTC timestamp. */
  added_at: string;
}

export interface AnalysisJob {
  source_id: string; // references InspirationSource.source_id
  status: AnalysisStatus;
  /** 0.0 .. 1.0 */
  progress: number;
  error: string | null;
  /** Empty until status === 'ok'. */
  extracted_traits: StyleTrait[];
}

/**
 * Wire-format mirror of Python `AnalysisJob.to_dict()`. Structurally identical to
 * `AnalysisJob` today, but kept as a distinct named type so the `analysis_progress`
 * payload contract is grep-able and any future divergence (e.g. server-only fields)
 * surfaces as a type error at the parity boundary instead of silently.
 */
export interface AnalysisJobDict {
  source_id: string;
  status: AnalysisStatus;
  progress: number;
  error: string | null;
  extracted_traits: StyleTrait[];
}

/**
 * The wizard's candidate ProfileModel — same shape as `ProfileModel` but always carries
 * `kind: 'user'` and is materialised by the WS-C ProfileBuilder. We define a wizard-local
 * alias so the type surface stays self-contained.
 */
export interface CandidateProfileModel {
  profile_id: string; // ULID
  name: string;
  kind: ProfileKind; // always "user" in practice
  model_version: string;
  traits: StyleTrait[];
  pad_mappings: TraitPadWeight[];
  transition_curve: TransitionCurve;
  source_summary: string;
}

export interface WizardState {
  wizard_id: string; // ULID
  step: WizardStep;
  name: string | null;
  description: string | null;
  sources: InspirationSource[];
  jobs: AnalysisJob[];
  /** Populated once the operator reaches the review step. */
  candidate_profile: CandidateProfileModel | null;
}

// ---------- Commands (UI → Python sidecar) ----------

export interface WizardStartCommand {
  type: 'wizard_start';
}

export interface WizardSetMetadataCommand {
  type: 'wizard_set_metadata';
  name?: string;
  description?: string;
}

export interface WizardAddSourceCommand {
  type: 'wizard_add_source';
  kind: WizardSourceKind;
  mode: WizardSourceMode;
  location: string;
  display_name: string;
}

export interface WizardRemoveSourceCommand {
  type: 'wizard_remove_source';
  source_id: string;
}

export interface WizardAnalyzeCommand {
  type: 'wizard_analyze';
}

export interface WizardReviewCommand {
  type: 'wizard_review';
}

export interface WizardSaveCommand {
  type: 'wizard_save';
}

export interface WizardCancelCommand {
  type: 'wizard_cancel';
}

export type WizardCommand =
  | WizardStartCommand
  | WizardSetMetadataCommand
  | WizardAddSourceCommand
  | WizardRemoveSourceCommand
  | WizardAnalyzeCommand
  | WizardReviewCommand
  | WizardSaveCommand
  | WizardCancelCommand;

export type WizardCommandType = WizardCommand['type'];

// ---------- Events (Python sidecar → UI · push) ----------

export interface WizardStateChangedEvent {
  type: 'wizard_state_changed';
  state: WizardState;
}

/**
 * Per-job progress event. The payload mirrors the Python sidecar exactly
 * (`{"type": "analysis_progress", "job": <AnalysisJob.to_dict()>}`) — the full job
 * is nested so `status`, `progress`, `error`, and `extracted_traits` all propagate
 * through one event channel. See `tests/cockpit/test_protocol_parity.py` for the
 * cross-language guard that pins this shape.
 */
export interface AnalysisProgressEvent {
  type: 'analysis_progress';
  job: AnalysisJobDict;
}

export interface ProfileCreatedEvent {
  type: 'profile_created';
  profile: CandidateProfileModel;
}

export type WizardEvent =
  | WizardStateChangedEvent
  | AnalysisProgressEvent
  | ProfileCreatedEvent;

export type WizardEventType = WizardEvent['type'];

// ---------- Type guards ----------

/**
 * Narrow a parsed message to a WizardEvent. Used by the wizard_store binding when it
 * filters the multiplexed event stream from `CockpitClient`.
 */
export function isWizardEvent(msg: unknown): msg is WizardEvent {
  if (msg === null || typeof msg !== 'object') return false;
  const obj = msg as Record<string, unknown>;
  if (typeof obj.type !== 'string') return false;
  const types: ReadonlyArray<WizardEventType> = [
    'wizard_state_changed',
    'analysis_progress',
    'profile_created',
  ];
  return (types as ReadonlyArray<string>).includes(obj.type);
}
