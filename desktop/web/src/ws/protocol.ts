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

export type HistoryVia = 'send' | 'regen' | 'load' | 'import' | 'capture';

export type SessionMode = 'live' | 'mock';

export type ExportTarget = 'binary' | 'json';

/**
 * The passive connection lifecycle vocabulary — mirrors
 * `rytm_randomizer/cockpit/device/connection.py::ConnectionPhase` (the
 * wire authority is the inline Literal on `ConnectionStateDict` in
 * `cockpit/ws/protocol.py`).
 */
export type ConnectionPhase = 'disconnected' | 'searching' | 'listening' | 'armed' | 'fault';

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

export interface ProfileCatalogItem {
  profile_id: string;
  name: string;
  kind: ProfileKind;
  model_version: string;
  source_summary: string;
}

export type AnalogFourPatchTransportStatus =
  | 'cc-ready'
  | 'nrpn-ready'
  | 'screen-only-nrpn'
  | 'screen-only';

export interface AnalogFourPatchValue {
  parameter: string;
  section: string;
  encoder: string;
  screen_value: string;
  midi_value: number | null;
  cc_msb: number | null;
  cc_lsb: number | null;
  nrpn_address: number[] | null;
  transport_status: AnalogFourPatchTransportStatus;
  dial_direction: string;
}

export interface AnalogFourPatchGene {
  track: number;
  family: string;
  rationale: string;
  confidence: string;
  value: AnalogFourPatchValue;
}

export interface AnalogFourPatchCandidate {
  column: number;
  label: string;
  role: string;
  closeness: number;
  genes: AnalogFourPatchGene[];
}

export interface AnalogFourPatchTrait {
  key: string;
  label: string;
  intensity: number;
  evidence: string[];
}

export interface AnalogFourPatchGenome {
  version: string;
  device_id: string;
  mode: string;
  selected_track: number;
  source_hash: string;
  source_confidence: string;
  candidate_count: number;
  traits: AnalogFourPatchTrait[];
  candidates: AnalogFourPatchCandidate[];
  safety: string[];
}

export interface AnalogFourPatchGenomePayload {
  source: { type: string; value: string };
  selected_candidate: number;
  selected_track: number;
  selected: AnalogFourPatchCandidate;
  genome: AnalogFourPatchGenome;
  safety: string[];
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
  target_pad_ids: number[];
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

export interface OperatorPackageApplyPreviewStep {
  order: number;
  step_key: string;
  label: string;
  slot_key: string;
  package_export_key: string;
  local_action: string;
  operator_command: string;
  recovery_command: string;
  readiness_status: string;
  blocked_action: string;
}

export interface OperatorPackageApplyPreviewReadinessCheck {
  check: string;
  status: string;
  required?: boolean;
  operator_package_id?: string;
  step_count?: number;
  binding_count?: number;
}

export interface OperatorPackageApplyPreviewRecoveryRequirement {
  requirement_key: string;
  label: string;
  command: string;
  required_before_send: boolean;
  evidence: string;
}

export interface OperatorPackageApplyPreviewDryRunSummary {
  apply_policy: string;
  would_apply_steps: number;
  would_open_midi_port: boolean;
  would_send_midi: boolean;
  would_write_files: boolean;
  would_mutate_snapshot: boolean;
  events_emitted: boolean;
}

export interface OperatorPackageApplyPreview {
  preview_id: string;
  operator_package_id: string;
  snapshot_id: string;
  mock_safe: boolean;
  preview_status: string;
  apply_policy: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  step_count: number;
  step_keys: string[];
  apply_steps: OperatorPackageApplyPreviewStep[];
  readiness_checks: OperatorPackageApplyPreviewReadinessCheck[];
  recovery_requirements: OperatorPackageApplyPreviewRecoveryRequirement[];
  blocked_actions: string[];
  safety_lines: string[];
  dry_run_summary: OperatorPackageApplyPreviewDryRunSummary;
}

export interface OperatorPackageMockApplyStep {
  order: number;
  step_key: string;
  label: string;
  slot_key: string;
  package_export_key: string;
  local_action: string;
  operator_command: string;
  recovery_command: string;
  mock_apply_status: string;
  blocked_action: string;
}

export interface OperatorPackageMockApplyDryRunSummary {
  apply_policy: string;
  mock_applied_steps: number;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  mutated_snapshot: boolean;
  applied_send_plan: boolean;
  events_emitted: boolean;
}

export interface OperatorPackageMockApply {
  mock_apply_id: string;
  operator_package_id: string;
  snapshot_id: string;
  mock_safe: boolean;
  mock_apply_status: string;
  apply_policy: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  mutated_snapshot: boolean;
  applied_send_plan: boolean;
  emitted_events: boolean;
  step_count: number;
  step_keys: string[];
  mock_apply_steps: OperatorPackageMockApplyStep[];
  readiness_checks: OperatorPackageApplyPreviewReadinessCheck[];
  recovery_requirements: OperatorPackageApplyPreviewRecoveryRequirement[];
  blocked_actions: string[];
  safety_lines: string[];
  dry_run_summary: OperatorPackageMockApplyDryRunSummary;
}

export interface OperatorPackageReceiptStep extends OperatorPackageApplyPreviewStep {
  receipt_status: string;
}

export interface OperatorPackageReceiptReadinessCheck
  extends OperatorPackageApplyPreviewReadinessCheck {
  writes_files?: boolean;
  events_emitted?: boolean;
}

export interface OperatorPackageReceiptAuditSummary {
  receipt_policy: string;
  recorded_steps: number;
  records_apply_preview: boolean;
  would_open_midi_port: boolean;
  would_send_midi: boolean;
  would_write_files: boolean;
  would_mutate_snapshot: boolean;
  would_apply_send_plan: boolean;
  events_emitted: boolean;
}

export interface OperatorPackageReceipt {
  receipt_id: string;
  receipt_digest: string;
  operator_package_id: string;
  snapshot_id: string;
  mock_safe: boolean;
  receipt_status: string;
  receipt_policy: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  mutated_snapshot: boolean;
  applied_send_plan: boolean;
  events_emitted: boolean;
  step_count: number;
  step_keys: string[];
  receipt_steps: OperatorPackageReceiptStep[];
  readiness_checks: OperatorPackageReceiptReadinessCheck[];
  recovery_requirements: OperatorPackageApplyPreviewRecoveryRequirement[];
  blocked_actions: string[];
  safety_lines: string[];
  audit_summary: OperatorPackageReceiptAuditSummary;
}

/**
 * One passive connection observation — mirrors Python `ConnectionStateDict`
 * (`rytm_randomizer/cockpit/ws/protocol.py`). Whole-state per event.
 */
export interface ConnectionStateDict {
  phase: ConnectionPhase;
  available_inputs: string[];
  available_outputs: string[];
  selected_input: string | null;
  selected_output: string | null;
  last_error_fingerprint: string | null;
  changed_at: number;
}

/**
 * One coalesced row inside a `midi_activity` batch — mirrors the row shape
 * built by `rytm_randomizer/cockpit/device/midi_monitor.py::MidiInputMonitor.flush`.
 */
export interface MidiActivityRow {
  channel: number;
  pad: number;
  control: number;
  value: number;
  repeat_count: number;
  observed_at: number;
  labels: string[];
}

/** The `midi_activity` payload — one coalesced batch of passive observations. */
export interface MidiActivityBatch {
  port: string;
  batch: MidiActivityRow[];
  dropped: number;
  ignored: number;
  read_errors: number;
}

/**
 * One library record — mirrors
 * `rytm_randomizer/cockpit/library/store.py::LibraryRecord.to_dict`.
 */
export interface LibraryRecord {
  record_id: string;
  device_id: string;
  kit_name: string;
  fingerprint: string;
  captured_at: string;
  tags: string[];
  payload_hex: string;
}

/**
 * Outcome of one captures-import run — mirrors
 * `rytm_randomizer/cockpit/library/store.py::LibraryImportResult.to_dict`.
 */
export interface LibraryImportResult {
  imported: LibraryRecord[];
  imported_count: number;
  skipped_existing: number;
  failed_files: string[];
}

/**
 * One wire-safe categorized error observation — mirrors
 * `rytm_randomizer/cockpit/diagnostics.py::ErrorJournalEntry.to_dict`.
 */
export interface DiagnosticsJournalEntry {
  fingerprint: string;
  message: string;
  context: Record<string, string>;
  ts: number;
}

/**
 * The read-only `diagnostics` command payload — mirrors
 * `rytm_randomizer/cockpit/diagnostics.py::build_diagnostics_payload`.
 */
export interface DiagnosticsPayload {
  journal: DiagnosticsJournalEntry[];
  errors_by_kind: Record<string, number>;
  connection: ConnectionStateDict | null;
  available_inputs: string[];
  available_outputs: string[];
  platform: string;
  driver_hint: string;
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

export interface ProfileCatalogChangedEvent {
  type: 'profile_catalog_changed';
  profiles: ProfileCatalogItem[];
}

export type KitCaptureDeviceId = 'analog_rytm_mk2' | 'analog_four_mk2';
export type KitCaptureLayoutStatus = 'mutation_ready' | 'captured_mapping_pending';
export type KitParameterReadiness =
  | 'rytm_anchor_ready'
  | 'exact_kit_anchor_offsets_candidate';

export interface KitCaptureLayoutItem {
  index: number;
  label: string;
  status: KitCaptureLayoutStatus;
  detail: string;
}

export interface KitCaptureResult {
  device_id: KitCaptureDeviceId;
  kit_name: string;
  slot: number | null;
  fingerprint: string;
  frame_bytes: number;
  captured_at: string;
  snapshot_layout: string;
  parameter_readiness: KitParameterReadiness;
  round_trip_verified: boolean;
  input_only: boolean;
  sent_midi: boolean;
  layout_items: KitCaptureLayoutItem[];
}

export interface KitCapturesChangedEvent {
  type: 'kit_captures_changed';
  captures: KitCaptureResult[];
}

export interface MutationTargetsChangedEvent {
  type: 'mutation_targets_changed';
  rytm_pad_targets: number[];
  a4_track_targets: number[];
}

/** Whole-state lock authority used for bootstrap, reconnect, and every lock revision. */
export interface MutationLocksChangedEvent {
  type: 'mutation_locks_changed';
  rytm_pad_locks: number[];
  a4_track_locks: number[];
}

// Mirrors `rytm_randomizer/cockpit/data/stage.py` exactly. Stage events replace
// this shape wholesale; clients must never merge individual machine fields.
export type StageDeviceId = 'analog_rytm_mk2' | 'analog_four_mk2';
export type StageConnectionState = 'unknown' | 'connected' | 'disconnected';
export type StageCaptureState = 'not_captured' | 'captured' | 'failed';
export type StageArtifactState = 'none' | 'ready' | 'stale' | 'blocked';
export type StageAuthorityState = 'not_armed' | 'armed' | 'blocked';

export interface MachineStageState {
  device_id: StageDeviceId;
  connection_state: StageConnectionState;
  capture_state: StageCaptureState;
  target_ids: number[];
  locked_ids: number[];
  effective_ids: number[];
  candidate_state: StageArtifactState;
  plan_state: StageArtifactState;
  authority_state: StageAuthorityState;
  blocked_reasons: string[];
  recovery_actions: string[];
  last_error: string | null;
}

export interface DualMachineStageState {
  revision: number;
  rytm: MachineStageState;
  analog_four: MachineStageState;
  oxi_owns_sequencing: boolean;
  direct_oxi_control: boolean;
}

export interface DualMachineStageChangedEvent {
  type: 'dual_machine_stage_changed';
  stage: DualMachineStageState;
}

export interface PatchGenomeChangedEvent {
  type: 'patch_genome_changed';
  patch_genome: AnalogFourPatchGenomePayload;
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
  connection_phase: ConnectionPhase;
  unsaved_sends: number;
  /** Additive capability flag; older sidecars may omit it. */
  capture_enabled?: boolean;
  /**
   * Auto-update contract I1: the sidecar half's strict-SemVer version.
   *
   * Read-only server -> client state carried on the handshake frame.
   * Optional because a pre-I1 sidecar (a dev loop pinned to an older
   * checkout) omits it entirely; consumers treat `undefined` as
   * "version unknown" and must never block on it.
   */
  app_version?: string;
}

/** `connection_changed` — the full fresh ConnectionStateDict (never a delta). */
export interface ConnectionChangedEvent {
  type: 'connection_changed';
  connection: ConnectionStateDict;
}

/**
 * `midi_activity` — one coalesced batch of passive input observations.
 * The documented exception to the whole-state rule: the UI appends.
 */
export interface MidiActivityEvent {
  type: 'midi_activity';
  midi_activity: MidiActivityBatch;
}

/** `library_changed` — the full fresh library record listing. */
export interface LibraryChangedEvent {
  type: 'library_changed';
  library: { records: LibraryRecord[] };
}

export type Event =
  | SnapshotChangedEvent
  | MutationPreviewedEvent
  | SendPlanChangedEvent
  | HistoryUpdatedEvent
  | ProfileChangedEvent
  | ProfileCatalogChangedEvent
  | KitCapturesChangedEvent
  | MutationTargetsChangedEvent
  | MutationLocksChangedEvent
  | DualMachineStageChangedEvent
  | PatchGenomeChangedEvent
  | PerformanceConsoleChangedEvent
  | SessionStatusEvent
  | ConnectionChangedEvent
  | MidiActivityEvent
  | LibraryChangedEvent
  | WizardEvent;

export type EventType = Event['type'];

// ---------- Commands (UI → Engine, request/response) ----------

export interface SelectProfileCommand {
  type: 'select_profile';
  profile_id: string;
}

export interface AnalyzePatchGenomeCommand {
  type: 'analyze_patch_genome';
  description: string;
  track: number;
}

export interface ListCaptureInputsCommand {
  type: 'list_capture_inputs';
  device_id: KitCaptureDeviceId;
}

export interface CaptureCurrentKitCommand {
  type: 'capture_current_kit';
  device_id: KitCaptureDeviceId;
  input_port: string;
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

export interface SetA4TrackLockCommand {
  type: 'set_a4_track_lock';
  track: number;
  locked: boolean;
}

export interface SetMutationTargetsCommand {
  type: 'set_mutation_targets';
  device_id: KitCaptureDeviceId;
  target_ids: number[];
}

export interface ClearMutationTargetsCommand {
  type: 'clear_mutation_targets';
  device_id: KitCaptureDeviceId;
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

/**
 * `send { confirm? }` — apply the current candidate to the device.
 *
 * `confirm` is the **per-action** operator confirmation. "Armed" is a session
 * state; every individual write is still a separate operator decision, so the
 * sidecar refuses an armed send unless the command itself carries
 * `confirm: true` (`cockpit/ws/handlers.py::_armed_send_over_seam`).
 *
 * The field is optional because the mock / dry-run path deliberately does NOT
 * require it: an unarmed send touches no hardware and must stay a single
 * click. Only the ArmedApply seam reads it.
 */
export interface SendCommand {
  type: 'send';
  confirm?: boolean;
  /** Exact prepared plan being confirmed; mandatory for armed sessions. */
  send_plan_id?: string;
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

export interface PreviewOperatorPackageApplyCommand {
  type: 'preview_operator_package_apply';
  operator_package_id: string;
  step_keys: string[];
  package_export_keys: Record<string, string>;
  snapshot_id: string;
  mock_safe: boolean;
}

export interface MockApplyOperatorPackageCommand {
  type: 'mock_apply_operator_package';
  operator_package_id: string;
  step_keys: string[];
  package_export_keys: Record<string, string>;
  snapshot_id: string;
  mock_safe: boolean;
}

export interface BuildOperatorPackageReceiptCommand {
  type: 'build_operator_package_receipt';
  operator_package_id: string;
  step_keys: string[];
  package_export_keys: Record<string, string>;
  snapshot_id: string;
  mock_safe: boolean;
}

/**
 * `arm { arm_token, confirm, port_name? }` — explicit in-UI arm. Requires the
 * operator token AND `confirm: true`; arming is a two-factor in-UI decision,
 * never implicit (Live-but-Passive rule).
 */
export interface ArmCommand {
  type: 'arm';
  arm_token: string;
  confirm: boolean;
  port_name?: string | null;
}

/** `disarm {}` — tear down the armed seam, restore the passive device. */
export interface DisarmCommand {
  type: 'disarm';
}

/** `diagnostics {}` — read-only health query (journal + metrics + hints). */
export interface DiagnosticsCommand {
  type: 'diagnostics';
}

/** `library_list {}` — full library record listing. */
export interface LibraryListCommand {
  type: 'library_list';
}

/** `library_search { query }` — case-insensitive record search. */
export interface LibrarySearchCommand {
  type: 'library_search';
  query: string;
}

/** `library_tag { record_id, tags }` — replace one record's tags. */
export interface LibraryTagCommand {
  type: 'library_tag';
  record_id: string;
  tags: string[];
}

/** `library_delete { record_id }` — remove one record from the library. */
export interface LibraryDeleteCommand {
  type: 'library_delete';
  record_id: string;
}

/**
 * `library_import_captures {}` — import the boot-time-configured captures dir.
 * Deliberately carries no path field (no wire-supplied filesystem paths).
 */
export interface LibraryImportCapturesCommand {
  type: 'library_import_captures';
}

export type Command =
  | AnalyzePatchGenomeCommand
  | ListCaptureInputsCommand
  | CaptureCurrentKitCommand
  | SelectProfileCommand
  | SetDepthCommand
  | SetPadLockCommand
  | SetA4TrackLockCommand
  | SetMutationTargetsCommand
  | ClearMutationTargetsCommand
  | TogglePreviewCommand
  | RegenCommand
  | PrepareSendPlanCommand
  | SendCommand
  | SaveCommand
  | LoadSnapshotCommand
  | UndoCommand
  | ExportProfileModelCommand
  | RehearseOperatorPackageStepCommand
  | RehearseOperatorPackageSequenceCommand
  | PreviewOperatorPackageApplyCommand
  | MockApplyOperatorPackageCommand
  | BuildOperatorPackageReceiptCommand
  | ArmCommand
  | DisarmCommand
  | DiagnosticsCommand
  | LibraryListCommand
  | LibrarySearchCommand
  | LibraryTagCommand
  | LibraryDeleteCommand
  | LibraryImportCapturesCommand;

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
  operator_package_apply_preview?: OperatorPackageApplyPreview;
  operator_package_mock_apply?: OperatorPackageMockApply;
  operator_package_receipt?: OperatorPackageReceipt;
  armed?: boolean;
  midi_port?: string | null;
  diagnostics?: DiagnosticsPayload | null;
  library_records?: LibraryRecord[] | null;
  library_record?: LibraryRecord | null;
  library_record_id?: string | null;
  library_import?: LibraryImportResult | null;
  patch_genome?: AnalogFourPatchGenomePayload;
  capture_enabled?: boolean;
  capture_device_id?: KitCaptureDeviceId;
  capture_inputs?: string[];
  kit_capture?: KitCaptureResult;
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
    'profile_catalog_changed',
    'kit_captures_changed',
    'mutation_targets_changed',
    'mutation_locks_changed',
    'dual_machine_stage_changed',
    'patch_genome_changed',
    'performance_console_changed',
    'session_status',
    'connection_changed',
    'midi_activity',
    'library_changed',
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
