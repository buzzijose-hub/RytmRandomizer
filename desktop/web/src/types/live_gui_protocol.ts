/**
 * Shared live-GUI protocol types.
 *
 * GENERATED — edit the Python TypedDicts and re-run
 * scripts/generate_live_gui_protocol_ts.py.
 *
 * Source of truth: the sibling TypedDict contracts in
 * `rytm_randomizer/reports/live_gui_*_model.py`.
 * `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`
 * keeps these TypeScript field names aligned with the Python contracts.
 */

import type { StyleCrateRehearsalDeckDict } from './style_crate_rehearsal_deck';

export interface LiveGuiRytmPadSurfaceCardDict {
  pad: number;
  track_code: string;
  label: string;
  surface_state: string;
  ui_enabled: boolean;
  ui_locked: boolean;
  lock_reason: string;
  default_role: string;
  default_machine_label: string;
  legal_machine_count: number;
  snapshot_mutable_machine_count: number;
  selectable_only_machine_count: number;
  primary_machine_labels: ReadonlyArray<string>;
}

export interface LiveGuiRytmTwelvePadSurfaceModelDict {
  model_version: string;
  pad_count: number;
  active_pad_count: number;
  planned_pad_count: number;
  cards_by_pad: Readonly<Record<number, LiveGuiRytmPadSurfaceCardDict>>;
  blocked_actions: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiDeviceInventoryCardDict {
  device_id: string;
  display_name: string;
  order: number;
  track_count: number;
  default_midi_channel_label: string;
  sysex_manufacturer_id_hex: string;
  role_summary: string;
  port_state: string;
  hardware_state: string;
  mock_state: string;
  can_open_port: boolean;
  can_arm_hardware: boolean;
  capability_badges: ReadonlyArray<string>;
  passive: boolean;
}

export interface LiveGuiDeviceInventoryModelDict {
  model_version: string;
  device_count: number;
  cards_by_device_id: Readonly<Record<string, LiveGuiDeviceInventoryCardDict>>;
  blocked_actions: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiSceneCardDict {
  scene_key: string;
  order: number;
  label: string;
  description: string;
  action: string;
  affected_pads: ReadonlyArray<number>;
  zone_tokens: ReadonlyArray<string>;
  depth_tokens: ReadonlyArray<string>;
  mutation_depth_percent: number;
  dry_run_message_count: number;
  status: string;
  operator_hint: string;
  passive: boolean;
}

export interface LiveGuiScenePreviewQueueItemDict {
  scene_key: string;
  queue_index: number;
  queue_position: string;
  label: string;
  status: string;
  estimated_duration_seconds: number;
  mutation_depth_percent: number;
  affected_pads: ReadonlyArray<number>;
  dry_run_message_count: number;
  passive: boolean;
}

export interface LiveGuiSceneQueueModelDict {
  model_version: string;
  source_module: string;
  scene_count: number;
  queue_status: string;
  scene_cards: ReadonlyArray<LiveGuiSceneCardDict>;
  preview_queue: ReadonlyArray<LiveGuiScenePreviewQueueItemDict>;
  safety_lines: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
}

export interface LiveGuiStatusFooterItemDict {
  key: string;
  order: number;
  label: string;
  value: string;
  state: string;
  severity: string;
  action_label: string;
  action_enabled: boolean;
  test_id: string;
}

export interface LiveGuiStatusFooterModelDict {
  status_footer_version: string;
  status_footer_id: string;
  session_label: string;
  items: ReadonlyArray<LiveGuiStatusFooterItemDict>;
  safety_lines: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiSnapshotHistoryEntryDict {
  key: string;
  order: number;
  snapshot_id: string;
  label: string;
  kind: string;
  via: string | null;
  parent_id: string | null;
  device: string;
  pad_count: number;
  scene_slot: string | null;
  bpm_label: string;
  is_current: boolean;
  is_saved: boolean;
  can_load: boolean;
  can_undo_to: boolean;
  summary: string;
  test_id: string;
}

export interface LiveGuiSnapshotHistoryControlDict {
  key: string;
  order: number;
  label: string;
  enabled: boolean;
  target_snapshot_id: string | null;
  reason: string;
  test_id: string;
}

export interface LiveGuiSnapshotHistoryModelDict {
  snapshot_history_version: string;
  snapshot_history_id: string;
  session_label: string;
  current_id: string;
  current_index: number;
  entry_count: number;
  entries: ReadonlyArray<LiveGuiSnapshotHistoryEntryDict>;
  controls: ReadonlyArray<LiveGuiSnapshotHistoryControlDict>;
  safety_lines: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiSafetyChecklistItemDict {
  key: string;
  order: number;
  label: string;
  status: string;
  severity: string;
  message: string;
  operator_action: string;
  test_id: string;
}

export interface LiveGuiArmHardwareGateDict {
  key: string;
  label: string;
  state: string;
  enabled: boolean;
  reason: string;
  requirements: ReadonlyArray<string>;
  midi_port_name: string | null;
  midi_port_open: boolean;
  hardware_connected: boolean;
  send_plan_ready: boolean;
  dry_run_complete: boolean;
  test_id: string;
}

export interface LiveGuiSafetyChecklistModelDict {
  safety_checklist_version: string;
  safety_checklist_id: string;
  session_label: string;
  checklist_status: string;
  passed_count: number;
  total_count: number;
  items: ReadonlyArray<LiveGuiSafetyChecklistItemDict>;
  arm_gate: LiveGuiArmHardwareGateDict;
  safety_lines: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiQueuedCommandDict {
  key: string;
  order: number;
  label: string;
  status: string;
  enabled: boolean;
  action_type: string;
  target: string;
  dry_run_only: boolean;
  estimated_message_count: number;
  operator_action: string;
  test_id: string;
}

export interface LiveGuiLastActionDict {
  key: string;
  order: number;
  label: string;
  status: string;
  action_type: string;
  snapshot_id: string;
  device: string;
  result: string;
  detail: string;
  test_id: string;
}

export interface LiveGuiUndoStackEntryDict {
  key: string;
  order: number;
  label: string;
  status: string;
  snapshot_id: string;
  is_current: boolean;
  is_undo_target: boolean;
  is_load_target: boolean;
  action_type: string;
  test_id: string;
}

export interface LiveGuiCommandQueueModelDict {
  command_queue_version: string;
  command_queue_id: string;
  session_label: string;
  queue_status: string;
  dry_run_active: boolean;
  hardware_armed: boolean;
  active_command_key: string | null;
  queued_commands: ReadonlyArray<LiveGuiQueuedCommandDict>;
  last_actions: ReadonlyArray<LiveGuiLastActionDict>;
  undo_stack: ReadonlyArray<LiveGuiUndoStackEntryDict>;
  safety_lines: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiAnalyzerWaveformBinDict {
  index: number;
  label: string;
  value_percent: number;
  status: string;
}

export interface LiveGuiAnalyzerSpectrumBandDict {
  key: string;
  label: string;
  low_hz: number;
  high_hz: number;
  value_percent: number;
  status: string;
}

export interface LiveGuiAnalyzerPanelControlDict {
  key: string;
  label: string;
  enabled: boolean;
  status: string;
}

export interface LiveGuiAnalyzerPanelModelDict {
  title: string;
  panel_model_version: string;
  panel_id: string;
  panel_status: string;
  panel_mode: string;
  reference_label: string;
  source_kind: string;
  confidence: string;
  bpm: number;
  tempo_stability_percent: number;
  waveform_bins: ReadonlyArray<LiveGuiAnalyzerWaveformBinDict>;
  spectrum_bands: ReadonlyArray<LiveGuiAnalyzerSpectrumBandDict>;
  controls: Readonly<Record<string, LiveGuiAnalyzerPanelControlDict>>;
  required_actions: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety: Readonly<Record<string, boolean>>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiHardwareRailActionDict {
  key: string;
  label: string;
  enabled: boolean;
  reason: string;
  test_id: string;
}

export interface LiveGuiHardwareRailCardDict {
  key: string;
  title: string;
  status: string;
  severity: string;
  summary: string;
  details: ReadonlyArray<string>;
  actions: ReadonlyArray<LiveGuiHardwareRailActionDict>;
  test_id: string;
}

export interface LiveGuiHardwareRailSafetyCheckDict {
  key: string;
  label: string;
  passed: boolean;
  status: string;
  test_id: string;
}

export interface LiveGuiHardwareRailModelDict {
  model_version: string;
  rail_id: string;
  session_label: string;
  device_label: string;
  mode_label: string;
  rail_status: string;
  dry_run_active: boolean;
  hardware_requested: boolean;
  port_status: string;
  selected_port_name: string | null;
  available_ports: ReadonlyArray<string>;
  safety_checks: ReadonlyArray<LiveGuiHardwareRailSafetyCheckDict>;
  safety_check_count: number;
  safety_checks_passed: number;
  failing_safety_checks: ReadonlyArray<string>;
  arm_status: string;
  arm_locked: boolean;
  cards: ReadonlyArray<LiveGuiHardwareRailCardDict>;
  required_actions: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiSnapshotCompatibilityPadDict {
  pad: number;
  track_code: string;
  label: string;
  status: string;
  severity: string;
  map_safe: boolean;
  snapshot_mutation_enabled: boolean;
  allowed_machine_count: number;
  mutable_machine_count: number;
  selectable_machine_count: number;
  lock_reason: string;
  machine_labels: ReadonlyArray<string>;
  test_id: string;
}

export interface LiveGuiSnapshotCompatibilityModelDict {
  model_version: string;
  compatibility_id: string;
  panel_label: string;
  session_label: string;
  compatibility_status: string;
  status_badge: string;
  summary: string;
  pad_count: number;
  snapshot_mutable_pad_count: number;
  planned_pad_count: number;
  view_details_enabled: boolean;
  pads: ReadonlyArray<LiveGuiSnapshotCompatibilityPadDict>;
  required_actions: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiDualDeviceRigDeviceDict {
  device_id: string;
  display_name: string;
  order: number;
  track_count: number;
  mapped_track_count: number;
  active_track_count: number;
  planned_track_count: number;
  status: string;
  role_summary: string;
  port_state: string;
  hardware_state: string;
  summary: string;
  test_id: string;
}

export interface LiveGuiDualDeviceRigTrackDict {
  device_id: string;
  track_number: number;
  track_label: string;
  label: string;
  role: string;
  state: string;
  enabled: boolean;
  source: string;
  test_id: string;
}

export interface LiveGuiDualDeviceRigReadinessModelDict {
  model_version: string;
  rig_id: string;
  session_label: string;
  rig_status: string;
  total_device_count: number;
  total_track_count: number;
  active_track_count: number;
  planned_track_count: number;
  pad_surface: LiveGuiRytmTwelvePadSurfaceModelDict;
  device_inventory: LiveGuiDeviceInventoryModelDict;
  hardware_rail: LiveGuiHardwareRailModelDict;
  snapshot_compatibility: LiveGuiSnapshotCompatibilityModelDict;
  devices: ReadonlyArray<LiveGuiDualDeviceRigDeviceDict>;
  tracks: ReadonlyArray<LiveGuiDualDeviceRigTrackDict>;
  required_actions: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceFlowStepDict {
  key: string;
  order: number;
  label: string;
  phase: string;
  rytm_command: string;
  analog_four_action: string;
  send_policy: string;
  recovery_action: string;
  status: string;
}

export interface LiveGuiAnalogFourReadinessDict {
  readiness: string;
  command: string;
  summary: string;
  blocked_active_actions: ReadonlyArray<string>;
}

export interface LiveGuiAnalogFourSetPlanDict {
  set_name: string;
  current_macro: string;
  up_next_macros: ReadonlyArray<string>;
  step_count: number;
  replay_command: string;
  summary: string;
  blocked_active_actions: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceFlowModelDict {
  model_version: string;
  source_module: string;
  flow_id: string;
  flow_status: string;
  current_step_key: string;
  steps: ReadonlyArray<LiveGuiPerformanceFlowStepDict>;
  analog_four_readiness: LiveGuiAnalogFourReadinessDict;
  analog_four_set_plan: LiveGuiAnalogFourSetPlanDict;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleMacroActionCardDict {
  macro_key: string;
  order: number;
  label: string;
  shell_command: string;
  send_policy: string;
  recovery_action: string;
  risk_label: string;
  affected_pads: ReadonlyArray<number>;
  pad_count: number;
  status: string;
  hardware_action_state: string;
  hardware_send_enabled: boolean;
  dry_run_only: boolean;
  operator_hint: string;
  test_id: string;
}

export interface LiveGuiPerformanceConsoleMacroActionDeckDict {
  deck_version: string;
  deck_id: string;
  deck_status: string;
  current_macro_key: string;
  cards: ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleRytmLanePolicyPadGroupDict {
  group_key: string;
  pads: ReadonlyArray<number>;
  summary: string;
  lane_policy: string;
  operator_note: string;
}

export interface LiveGuiPerformanceConsoleRytmPadPolicyCardDict {
  amount: string | null;
  density: string | null;
  bias: string | null;
  lane_policies: Readonly<Record<string, string>>;
  section_family_allowlists: Readonly<Record<string, ReadonlyArray<string>>>;
}

export interface LiveGuiPerformanceConsoleRytmMacroPolicyRowDict {
  macro_key: string;
  order: number;
  label: string;
  style_crate: string;
  risk_label: string;
  energy: number;
  risk: number;
  affected_pads: ReadonlyArray<number>;
  locked_pads: ReadonlyArray<number>;
  lane_policy_summary: string;
  pad_policy_cards: Readonly<Record<string, LiveGuiPerformanceConsoleRytmPadPolicyCardDict>>;
  recovery_action: string;
  summary: string;
}

export interface LiveGuiPerformanceConsoleRytmLanePolicyMatrixDict {
  matrix_version: string;
  matrix_id: string;
  matrix_status: string;
  source_report: string;
  macro_count: number;
  pad_groups: ReadonlyArray<LiveGuiPerformanceConsoleRytmLanePolicyPadGroupDict>;
  macro_rows: ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleRehearsalChapterDict {
  order: number;
  name: string;
  label: string;
  rytm_command: string;
  macro_sequence: ReadonlyArray<string>;
  a4_review_action: string;
  operator_intent: string;
  recovery_action: string;
}

export interface LiveGuiPerformanceConsoleRehearsalCueDict {
  chapter_name: string;
  label: string;
  oxi_action: string;
  rytm_stage_command: string;
  inspect_command: string;
  fire_command: string;
  recovery_command: string;
  a4_action: string;
  expected_result: string;
  blocked_action: string;
}

export interface LiveGuiPerformanceConsolePadLaneCheckDict {
  pads: ReadonlyArray<number>;
  summary: string;
  expected_motion: string;
  warning: string;
}

export interface LiveGuiPerformanceConsoleMacroCheckpointDict {
  name: string;
  label: string;
  risk_label: string;
  recovery_action: string;
  affected_pads: ReadonlyArray<number>;
  summary: string;
  checkpoints: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleHardwareValidationStepDict {
  name: string;
  device: string;
  operator_path: string;
  validation_mode: string;
  expected_evidence: string;
  safety_boundary: string;
}

export interface LiveGuiPerformanceConsolePromotionCriterionDict {
  name: string;
  device: string;
  current_status: string;
  required_evidence: string;
  promotes_to: string;
  safety_note: string;
}

export interface LiveGuiPerformanceConsoleReplayCommandDict {
  name: string;
  execution_mode: string;
  command: string;
  purpose: string;
  expected_observation: string;
  opens_ports: boolean;
  sends_midi: string;
  safety_note: string;
}

export interface LiveGuiPerformanceConsoleRehearsalBoardDict {
  board_version: string;
  board_id: string;
  board_status: string;
  title: string;
  launch_command: string;
  studio_workflow: ReadonlyArray<string>;
  chapters: ReadonlyArray<LiveGuiPerformanceConsoleRehearsalChapterDict>;
  operator_cues: ReadonlyArray<LiveGuiPerformanceConsoleRehearsalCueDict>;
  pad_lane_checks: ReadonlyArray<LiveGuiPerformanceConsolePadLaneCheckDict>;
  macro_checkpoints: ReadonlyArray<LiveGuiPerformanceConsoleMacroCheckpointDict>;
  hardware_validation_runway: ReadonlyArray<LiveGuiPerformanceConsoleHardwareValidationStepDict>;
  promotion_criteria: ReadonlyArray<LiveGuiPerformanceConsolePromotionCriterionDict>;
  recovery_checks: ReadonlyArray<string>;
  next_hardware_validations: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<LiveGuiPerformanceConsoleReplayCommandDict>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleControllerTemplateRowDict {
  assignment_key: string;
  page_key: string;
  page_label: string;
  page_index: number;
  slot: number;
  label: string;
  target_device: string;
  target_scope: string;
  intent_key: string;
  action: string;
  lane: string;
  safety_tier: string;
  recovery_action: string;
  operator_note: string;
}

export interface LiveGuiPerformanceConsoleControllerTemplatePageCardDict {
  page_key: string;
  page_label: string;
  page_index: number;
  row_count: number;
  first_slot: number;
  last_slot: number;
}

export interface LiveGuiPerformanceConsoleControllerGestureOutcomeDict {
  step: number;
  assignment_key: string;
  page_key: string;
  slot: number;
  gesture: string;
  value_delta: number;
  resolved_intent_key: string;
  resolved_action: string;
  resolved_target_device: string;
  resolved_target_scope: string;
  lane: string;
  safety_tier: string;
  recovery_action: string;
  status: string;
  operator_goal: string;
  notes: string;
}

export interface LiveGuiPerformanceConsoleControllerBrainPanelDict {
  panel_version: string;
  panel_id: string;
  panel_status: string;
  source_report: string;
  title: string;
  profile_key: string;
  profile_label: string;
  controller_family: string;
  controller_layout: string;
  scenario_key: string;
  scenario_label: string;
  scenario_summary: string;
  template_row_count: number;
  template_rows: ReadonlyArray<LiveGuiPerformanceConsoleControllerTemplateRowDict>;
  template_page_count: number;
  template_page_cards: ReadonlyArray<LiveGuiPerformanceConsoleControllerTemplatePageCardDict>;
  gesture_count: number;
  gesture_outcomes: ReadonlyArray<LiveGuiPerformanceConsoleControllerGestureOutcomeDict>;
  operator_notes: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureWorkflowStepDict {
  step_key: string;
  label: string;
  operator_command: string;
  description: string;
  cockpit_state: string;
  safety_note: string;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureDifferentiatorDict {
  name: string;
  label: string;
  summary: string;
  controller_limit: string;
  why_it_matters: string;
}

export interface LiveGuiPerformanceConsoleLiveKitCapturePanelDict {
  panel_version: string;
  panel_id: string;
  panel_status: string;
  title: string;
  tagline: string;
  source_report: string;
  launch_command: string;
  workflow_steps: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureWorkflowStepDict>;
  differentiators: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureDifferentiatorDict>;
  recovery_commands: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchSlotDict {
  slot_key: string;
  label: string;
  slot_status: string;
  operator_command: string;
  stores: string;
  source: string;
  safety_note: string;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureAnchorCheckDict {
  check_key: string;
  label: string;
  status: string;
  evidence: string;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureAnchorVerificationDict {
  anchor_key: string;
  expected_kit_label: string;
  fingerprint_source: string;
  checks: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureAnchorCheckDict>;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureReadinessGateDict {
  gate_key: string;
  label: string;
  status: string;
  operator_action: string;
  cockpit_action_allowed: boolean;
  blocked_action: string;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureMutationReadinessDict {
  readiness_status: string;
  ready_gate_count: number;
  blocked_gate_count: number;
  gates: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureReadinessGateDict>;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureRecoveryGateDict {
  gate_key: string;
  label: string;
  operator_sequence: string;
  expected_result: string;
  required_before_fire: boolean;
}

export interface LiveGuiPerformanceConsoleLiveKitCapturePackageManifestDict {
  manifest_version: string;
  manifest_id: string;
  source_panel_id: string;
  exports_files: boolean;
  includes: ReadonlyArray<string>;
  disabled_controls: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchDict {
  workbench_version: string;
  workbench_id: string;
  workbench_status: string;
  title: string;
  summary: string;
  source_panel_id: string;
  launch_command: string;
  capture_slots: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchSlotDict>;
  anchor_verification: LiveGuiPerformanceConsoleLiveKitCaptureAnchorVerificationDict;
  mutation_readiness: LiveGuiPerformanceConsoleLiveKitCaptureMutationReadinessDict;
  recovery_gates: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureRecoveryGateDict>;
  package_manifest: LiveGuiPerformanceConsoleLiveKitCapturePackageManifestDict;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionSlotDict {
  slot_key: string;
  label: string;
  style_crate: string;
  slot_status: string;
  energy: number;
  risk: number;
  target_pads: ReadonlyArray<number>;
  operator_sequence: ReadonlyArray<string>;
  recovery_command: string;
  seed: string;
  notes: string;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionQueueDict {
  queue_key: string;
  queue_status: string;
  fire_command: string;
  review_command: string;
  recovery_command: string;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionCheckDict {
  check_key: string;
  label: string;
  status: string;
  required: boolean;
  evidence: string;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionJournalPreviewDict {
  name: string;
  seed: string;
  tags: ReadonlyArray<string>;
  pads: ReadonlyArray<number>;
  depth: string;
  guardrail_mode: string;
  value_summary: string;
  notes: string;
  replay_policy: string;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionSummaryDict {
  slot_count: number;
  queue_count: number;
  check_count: number;
  journal_preview_count: number;
}

export interface LiveGuiPerformanceConsoleLiveKitPackageAuditionDict {
  audition_version: string;
  audition_id: string;
  audition_status: string;
  title: string;
  summary: string;
  source_workbench_id: string;
  source_package_manifest_version: string;
  audition_summary: LiveGuiPerformanceConsoleLiveKitPackageAuditionSummaryDict;
  audition_slots: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitPackageAuditionSlotDict>;
  audition_queue: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitPackageAuditionQueueDict>;
  package_checks: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitPackageAuditionCheckDict>;
  journal_preview: LiveGuiPerformanceConsoleLiveKitPackageAuditionJournalPreviewDict;
  disabled_controls: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageManifestDict {
  manifest_version: string;
  package_kind: string;
  package_id: string;
  source_audition_id: string;
  source_workbench_id: string;
  source_package_manifest_version: string;
  slot_count: number;
  queue_count: number;
  recovery_count: number;
  journal_preview_count: number;
  exports_files: boolean;
  includes: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict {
  step_key: string;
  label: string;
  slot_key: string;
  queue_status: string;
  local_action: string;
  operator_command: string;
  cockpit_binding: string;
  stage_target: string;
  recovery_command: string;
  safety_status: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageSlotBindingDict {
  slot_key: string;
  style_crate: string;
  crate_key: string;
  queue_key: string;
  depth_percent: number;
  journal_seed: string;
  package_export_key: string;
  value_source: string;
  action_preview: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageRecoveryRequirementDict {
  requirement_key: string;
  label: string;
  command: string;
  required_before_send: boolean;
  evidence: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageJournalCommitPreviewDict {
  name: string;
  seed: string;
  tags: ReadonlyArray<string>;
  pads: ReadonlyArray<number>;
  depth: string;
  guardrail_mode: string;
  value_summary: string;
  notes: string;
  replay_policy: string;
  commit_status: string;
  write_policy: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageLocalExportPreviewDict {
  export_kind: string;
  export_status: string;
  writes_files: boolean;
  extra_fields: ReadonlyArray<string>;
  source_audition_id: string;
  selected_slot_policy: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorPackageDict {
  operator_package_version: string;
  operator_package_id: string;
  operator_package_status: string;
  title: string;
  summary: string;
  source_audition_id: string;
  source_workbench_id: string;
  source_package_manifest_version: string;
  package_manifest: LiveGuiPerformanceConsoleLiveKitOperatorPackageManifestDict;
  operator_steps: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict>;
  slot_bindings: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitOperatorPackageSlotBindingDict>;
  recovery_requirements: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitOperatorPackageRecoveryRequirementDict>;
  journal_commit_preview: LiveGuiPerformanceConsoleLiveKitOperatorPackageJournalCommitPreviewDict;
  local_export_preview: LiveGuiPerformanceConsoleLiveKitOperatorPackageLocalExportPreviewDict;
  disabled_controls: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStageDict {
  stage_key: string;
  label: string;
  policy: string;
  status: string;
  summary: string;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  mutates_snapshot: boolean;
  applies_send_plan: boolean;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStepDict {
  order: number;
  step_key: string;
  label: string;
  slot_key: string;
  package_export_key: string;
  queue_status: string;
  local_action: string;
  operator_command: string;
  recovery_command: string;
  depth_percent: number;
  preview_status: string;
  mock_apply_status: string;
  receipt_status: string;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerReadinessSummaryDict {
  mock_safe: boolean;
  opened_midi_port: boolean;
  sent_midi: boolean;
  writes_files: boolean;
  mutated_snapshot: boolean;
  applied_send_plan: boolean;
  events_emitted: boolean;
  required_recovery_count: number;
}

export interface LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict {
  ledger_version: string;
  ledger_id: string;
  ledger_status: string;
  title: string;
  operator_package_id: string;
  source_audition_id: string;
  source_workbench_id: string;
  review_stage_count: number;
  step_count: number;
  review_stages: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStageDict>;
  step_rows: ReadonlyArray<LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStepDict>;
  readiness_summary: LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerReadinessSummaryDict;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleAnalogFourReviewStepDict {
  order: number;
  macro_name: string;
  macro_label: string;
  summary: string;
  seed: number;
  intensity: number;
  energy: number;
  readiness: string;
  event_count: number;
  ready_count: number;
  review_count: number;
  blocked_count: number;
  validation_command: string;
  recovery_action: string;
}

export interface LiveGuiPerformanceConsoleAnalogFourReviewFocusDict {
  macro_name: string;
  macro_label: string;
  seed: number;
  intensity: number;
  energy: number;
  readiness: string;
  event_count: number;
  ready_count: number;
  review_count: number;
  blocked_count: number;
  shown_count: number;
}

export interface LiveGuiPerformanceConsoleAnalogFourReadinessEventDict {
  track: number;
  role: string;
  lane: string;
  parameter: string;
  channel: number;
  control: number;
  value: number;
  status: string;
  validation_command: string;
  reason: string;
}

export interface LiveGuiPerformanceConsoleAnalogFourReviewSurfaceDict {
  surface_version: string;
  surface_id: string;
  surface_status: string;
  title: string;
  set_name: string;
  step_count: number;
  current_step: LiveGuiPerformanceConsoleAnalogFourReviewStepDict;
  up_next: ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReviewStepDict>;
  steps: ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReviewStepDict>;
  review_focus: LiveGuiPerformanceConsoleAnalogFourReviewFocusDict;
  readiness_events: ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReadinessEventDict>;
  preflight_command: string;
  validation_steps: ReadonlyArray<string>;
  recovery_notes: ReadonlyArray<string>;
  promotion_gates: ReadonlyArray<string>;
  replay_command: string;
  readiness_replay_command: string;
  opens_ports: boolean;
  sends_midi: boolean;
  hardware_required: boolean;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleDeviceInventoryModelDict {
  model_version: string;
  device_count: number;
  cards: ReadonlyArray<LiveGuiDeviceInventoryCardDict>;
  blocked_actions: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleRytmTwelvePadSurfaceModelDict {
  model_version: string;
  pad_count: number;
  active_pad_count: number;
  planned_pad_count: number;
  cards: ReadonlyArray<LiveGuiRytmPadSurfaceCardDict>;
  blocked_actions: ReadonlyArray<string>;
  safety: ReadonlyArray<string>;
}

export interface LiveGuiPerformanceConsoleModelDict {
  console_version: string;
  source_module: string;
  console_id: string;
  session_label: string;
  console_status: string;
  hardware_mode: string;
  device_inventory: LiveGuiPerformanceConsoleDeviceInventoryModelDict;
  rytm_pad_surface: LiveGuiPerformanceConsoleRytmTwelvePadSurfaceModelDict;
  rytm_lane_policy_matrix: LiveGuiPerformanceConsoleRytmLanePolicyMatrixDict;
  performance_flow: LiveGuiPerformanceFlowModelDict;
  macro_action_deck: LiveGuiPerformanceConsoleMacroActionDeckDict;
  rehearsal_board: LiveGuiPerformanceConsoleRehearsalBoardDict;
  controller_brain_panel: LiveGuiPerformanceConsoleControllerBrainPanelDict;
  live_kit_capture_panel: LiveGuiPerformanceConsoleLiveKitCapturePanelDict;
  live_kit_capture_workbench: LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchDict;
  live_kit_package_audition: LiveGuiPerformanceConsoleLiveKitPackageAuditionDict;
  live_kit_operator_package: LiveGuiPerformanceConsoleLiveKitOperatorPackageDict;
  operator_package_review_ledger: LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict;
  analog_four_review_surface: LiveGuiPerformanceConsoleAnalogFourReviewSurfaceDict;
  style_queue: StyleCrateRehearsalDeckDict;
  analyzer_panel: LiveGuiAnalyzerPanelModelDict;
  snapshot_history: LiveGuiSnapshotHistoryModelDict;
  command_queue: LiveGuiCommandQueueModelDict;
  safety_checklist: LiveGuiSafetyChecklistModelDict;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
  replay_commands: ReadonlyArray<string>;
}

export interface BadgeDict {
  label: string;
  tone: 'ok' | 'warn' | 'risk' | 'neutral';
  icon: string;
}

export interface TableDict {
  columns: ReadonlyArray<string>;
  rows: ReadonlyArray<ReadonlyArray<string>>;
}

export interface PanelSectionDict {
  heading: string;
  kind: 'rows' | 'table' | 'chips';
  rows: ReadonlyArray<string>;
  table: TableDict | null;
  chips: ReadonlyArray<string>;
}

export interface PanelSpecDict {
  panel_id: string;
  title: string;
  status_badges: ReadonlyArray<BadgeDict>;
  sections: ReadonlyArray<PanelSectionDict>;
  required_actions: ReadonlyArray<string>;
  blocked_actions: ReadonlyArray<string>;
  safety_lines: ReadonlyArray<string>;
}

export interface LiveReadinessModel {
  pad_surface: LiveGuiRytmTwelvePadSurfaceModelDict;
  device_inventory: LiveGuiDeviceInventoryModelDict;
  scene_queue: LiveGuiSceneQueueModelDict;
  status_footer: LiveGuiStatusFooterModelDict;
  snapshot_history: LiveGuiSnapshotHistoryModelDict;
  safety_checklist: LiveGuiSafetyChecklistModelDict;
  command_queue: LiveGuiCommandQueueModelDict;
  analyzer_panel: LiveGuiAnalyzerPanelModelDict;
  hardware_rail: LiveGuiHardwareRailModelDict;
  snapshot_compatibility: LiveGuiSnapshotCompatibilityModelDict;
}

export interface LiveReadinessPanelProps {
  model?: LiveReadinessModel;
}

export type LivePerformanceFlowStepModel = LiveGuiPerformanceFlowStepDict;

export type LivePerformanceFlowModel = LiveGuiPerformanceFlowModelDict;

export interface LiveReadinessPanelViewProps extends LiveReadinessPanelProps {
  performanceFlow?: LivePerformanceFlowModel;
}
