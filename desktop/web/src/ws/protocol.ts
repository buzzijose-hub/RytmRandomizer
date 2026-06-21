/**
 * Wire-format types mirroring the Python dataclasses in `rytm_randomizer/cockpit/data/`
 * and the WebSocket Protocol in `rytm_randomizer/cockpit/ws/protocol.py`.
 *
 * Source spec: `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md`
 *
 * Keep these types one-to-one with the Python side. Any change here MUST be matched
 * in the Python `cockpit/ws/protocol.py` (WS-E) and the dataclasses in
 * `cockpit/data/` (WS-A).
 */

import type { LiveGuiPerformanceConsoleModelDict } from '../types/live_gui_protocol';
import type { WizardEvent } from '../types/wizard_protocol';

// ---------- Domain enums (literal unions) ----------

export type DeviceKind = 'analog_rytm_mk2' | 'analog_four';

export type ProfileKind = 'scene' | 'user';

export type TransitionCurve = 'linear' | 'progressive' | 'progressive_w_release';

export type SafetyStatus = 'safe' | 'armed' | 'high_risk';

export type SendPlanReadinessReason =
  | 'ready'
  | 'candidate_high_risk'
  | 'profile_mismatch'
  | 'source_snapshot_mismatch'
  | 'no_sendable_changes';

export type HistoryEntryKind = 'auto' | 'saved';

export type HistoryVia = 'send' | 'regen' | 'load' | 'import';

export type SessionMode = 'live' | 'mock';

export type ExportTarget = 'binary' | 'json';

// ---------- Core data abstractions (spec §"Core Data Abstractions") ----------

export interface PadState {
  pad_id: number; // 1..12 Rytm tracks
  machine: string; // e.g. "BD Hard"
  params: Record<string, number>; // per-parameter values (tun, dec, lev, ...)
}

export interface Snapshot {
  snapshot_id: string; // ULID
  device: string; // "analog_rytm_mk2" | "analog_four"
  captured_at: string; // ISO-8601 UTC timestamp
  pads: PadState[]; // ordered by pad_id
  scene_slot: string | null; // device's scene memory slot (e.g. "A01") or null
  bpm: number | null;
}

export interface StyleTrait {
  name: string; // "rolling_low_end" | "metallic_tension" | ...
  value: number; // 0.0..1.0
}

export interface TraitPadWeight {
  trait: string; // references StyleTrait.name
  pad_id: number;
  weight: number; // 0.0..1.0
}

export interface ProfileModel {
  profile_id: string; // ULID
  name: string; // "buzzi" | "Industrial" (scene)
  kind: ProfileKind;
  model_version: string; // semver
  traits: StyleTrait[];
  pad_mappings: TraitPadWeight[];
  transition_curve: TransitionCurve;
  source_summary: string;
}

export interface PadDelta {
  pad_id: number;
  proposed_params: Record<string, number>;
  changed_keys: string[]; // which params actually change vs. current
}

export interface MutationCandidate {
  candidate_id: string; // ULID
  source_snapshot_id: string;
  profile_id: string;
  depth: number; // 0.10..0.90
  seed: number;
  pad_deltas: PadDelta[];
  safety_status: SafetyStatus;
  estimated_midi_msgs: number;
}

export interface SendPlanPacket {
  pad_id: number;
  parameter: string;
  channel: number;
  control: number;
  value: number;
}

export interface CockpitSendPlan {
  plan_id: string;
  candidate_id: string;
  source_snapshot_id: string;
  profile_id: string;
  ready: boolean;
  readiness_reason: SendPlanReadinessReason;
  safety_status: SafetyStatus;
  estimated_midi_msgs: number;
  pad_count: number;
  locked_pad_ids: number[];
  blocked_reasons: SendPlanReadinessReason[];
  packets: SendPlanPacket[];
}

export interface OperatorPackageRehearsal {
  rehearsal_id: string;
  operator_package_id: string;
  step_key: string;
  slot_key: string;
  label?: string;
  cockpit_binding?: string;
  local_action?: string;
  stage_target?: string;
  recovery_command?: string;
  operator_command?: string;
  package_export_key?: string;
  snapshot_id?: string;
  depth_percent?: number;
  mock_safe: boolean;
  rehearsal_status: string;
  safety_status?: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  blocked_actions?: string[];
  safety_lines?: string[];
}

export interface OperatorPackageSequenceRehearsal {
  rehearsal_id: string;
  operator_package_id: string;
  step_count: number;
  step_keys: string[];
  snapshot_id?: string;
  mock_safe: boolean;
  rehearsal_status: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  blocked_actions?: string[];
  safety_lines?: string[];
  step_rehearsals: OperatorPackageRehearsal[];
}

export interface HistoryEntry {
  snapshot: Snapshot;
  kind: HistoryEntryKind;
  parent_id: string | null;
  via: HistoryVia | null;
  label: string | null;
}

export interface History {
  entries: HistoryEntry[]; // chronological
  current_id: string;
}

// ---------- Events (Engine → UI, push) ----------

export interface SnapshotChangedEvent {
  type: 'snapshot_changed';
  snapshot: Snapshot;
}

export interface MutationPreviewedEvent {
  type: 'mutation_previewed';
  candidate: MutationCandidate | null; // null = preview off
}

export interface SendPlanChangedEvent {
  type: 'send_plan_changed';
  send_plan: CockpitSendPlan | null; // null = stale/cleared plan
}

export interface HistoryUpdatedEvent {
  type: 'history_updated';
  history: History;
}

export interface ProfileChangedEvent {
  type: 'profile_changed';
  profile: ProfileModel | null;
}

export interface PerformanceConsoleChangedEvent {
  type: 'performance_console_changed';
  performance_console: LiveGuiPerformanceConsoleModelDict | null;
}

export interface SessionStatusEvent {
  type: 'session_status';
  armed: boolean;
  midi_port: string | null;
  mode: SessionMode;
  unsaved_sends: number;
}

export type Event =
  | SnapshotChangedEvent
  | MutationPreviewedEvent
  | SendPlanChangedEvent
  | HistoryUpdatedEvent
  | ProfileChangedEvent
  | PerformanceConsoleChangedEvent
  | SessionStatusEvent
  | WizardEvent;

export type EventType = Event['type'];

// ---------- Commands (UI → Engine, request/response) ----------

export interface SelectProfileCommand {
  type: 'select_profile';
  profile_id: string;
}

export interface SetDepthCommand {
  type: 'set_depth';
  depth: number;
}

export interface SetPadLockCommand {
  type: 'set_pad_lock';
  pad_id: number;
  locked: boolean;
}

export interface TogglePreviewCommand {
  type: 'toggle_preview';
  on: boolean;
}

export interface RegenCommand {
  type: 'regen';
}

export interface PrepareSendPlanCommand {
  type: 'prepare_send_plan';
}

export interface SendCommand {
  type: 'send';
}

export interface SaveCommand {
  type: 'save';
  label?: string;
}

export interface LoadSnapshotCommand {
  type: 'load_snapshot';
  snapshot_id: string;
}

export interface UndoCommand {
  type: 'undo';
}

export interface ExportProfileModelCommand {
  type: 'export_profile_model';
  profile_id: string;
  target: ExportTarget;
}

export interface RehearseOperatorPackageStepCommand {
  type: 'rehearse_operator_package_step';
  operator_package_id: string;
  step_key: string;
  slot_key: string;
  package_export_key: string;
  snapshot_id: string;
  depth_percent: number;
  mock_safe: boolean;
}

export interface RehearseOperatorPackageSequenceCommand {
  type: 'rehearse_operator_package_sequence';
  operator_package_id: string;
  step_keys: string[];
  package_export_keys: Record<string, string>;
  snapshot_id: string;
  mock_safe: boolean;
}

export type Command =
  | SelectProfileCommand
  | SetDepthCommand
  | SetPadLockCommand
  | TogglePreviewCommand
  | RegenCommand
  | PrepareSendPlanCommand
  | SendCommand
  | SaveCommand
  | LoadSnapshotCommand
  | UndoCommand
  | ExportProfileModelCommand
  | RehearseOperatorPackageStepCommand
  | RehearseOperatorPackageSequenceCommand;

export type CommandType = Command['type'];

// ---------- Command envelope (request_id correlated with ack) ----------

/**
 * The UI wraps every Command in an envelope with a request_id so the server can correlate
 * the async ack with the originating request. The server may also emit unsolicited Events
 * which DO NOT carry a request_id.
 */
export interface CommandEnvelope<C extends Command = Command> {
  request_id: string;
  command: C;
}

export interface CommandAck {
  request_id: string;
  ok: boolean;
  // Optional contextual payload returned with the ack (e.g. new candidate after set_depth).
  candidate?: MutationCandidate;
  send_plan?: CockpitSendPlan | null;
  send_plan_id?: string;
  snapshot_id?: string;
  new_snapshot_id?: string;
  model_bytes?: string; // base64 for binary, raw json otherwise
  model_bytes_b64?: string; // Python sidecar's explicit base64 field name
  operator_package_rehearsal?: OperatorPackageRehearsal;
  operator_package_sequence_rehearsal?: OperatorPackageSequenceRehearsal;
  error?: string;
  code?: string;
  message?: string;
}

/**
 * Type guard: is a parsed JSON message an Event (engine → ui push)?
 * Events carry `type`, no `request_id`.
 */
export function isEvent(msg: unknown): msg is Event {
  if (msg === null || typeof msg !== 'object') return false;
  const obj = msg as Record<string, unknown>;
  if (typeof obj.type !== 'string') return false;
  if ('request_id' in obj) return false;
  const eventTypes: ReadonlyArray<EventType> = [
    'snapshot_changed',
    'mutation_previewed',
    'send_plan_changed',
    'history_updated',
    'profile_changed',
    'performance_console_changed',
    'session_status',
    'wizard_state_changed',
    'analysis_progress',
    'profile_created',
  ];
  return (eventTypes as ReadonlyArray<string>).includes(obj.type);
}

/**
 * Type guard: is a parsed JSON message a CommandAck (engine → ui response)?
 * Acks carry `request_id` and `ok`.
 */
export function isCommandAck(msg: unknown): msg is CommandAck {
  if (msg === null || typeof msg !== 'object') return false;
  const obj = msg as Record<string, unknown>;
  return typeof obj.request_id === 'string' && typeof obj.ok === 'boolean';
}
