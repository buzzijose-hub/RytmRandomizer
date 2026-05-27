/**
 * Shared live-GUI protocol types.
 *
 * Source of truth: the sibling TypedDict contracts in
 * `rytm_randomizer/reports/live_gui_*_model.py`.
 * `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`
 * keeps these TypeScript field names aligned with the Python contracts.
 */

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
  controls: ReadonlyArray<LiveGuiAnalyzerPanelControlDict>;
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
