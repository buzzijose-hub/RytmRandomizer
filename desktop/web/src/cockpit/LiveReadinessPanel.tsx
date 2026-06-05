import type {
  LiveGuiAnalyzerPanelControlDict,
  LiveGuiAnalyzerSpectrumBandDict,
  LiveGuiAnalyzerWaveformBinDict,
  LiveGuiDeviceInventoryCardDict,
  LiveGuiHardwareRailActionDict,
  LiveGuiHardwareRailCardDict,
  LiveGuiHardwareRailSafetyCheckDict,
  LiveGuiLastActionDict,
  LiveGuiQueuedCommandDict,
  LiveGuiRytmPadSurfaceCardDict,
  LiveGuiRytmTwelvePadSurfaceModelDict,
  LiveGuiSafetyChecklistItemDict,
  LiveGuiSceneCardDict,
  LiveGuiScenePreviewQueueItemDict,
  LiveGuiSnapshotCompatibilityPadDict,
  LiveGuiSnapshotHistoryControlDict,
  LiveGuiSnapshotHistoryEntryDict,
  LiveGuiStatusFooterItemDict,
  LiveGuiUndoStackEntryDict,
  LivePerformanceFlowModel,
  LivePerformanceFlowStepModel,
  LiveReadinessModel,
  LiveReadinessPanelViewProps,
} from '../types/live_gui_protocol';

export type {
  LivePerformanceFlowModel,
  LiveReadinessModel,
  LiveReadinessPanelProps,
  LiveReadinessPanelViewProps,
} from '../types/live_gui_protocol';

const PASSIVE_SAFETY = [
  'passive/read-only',
  'in-memory only',
  'no MIDI sending',
  'no port opening',
  'no hardware mutation',
] as const;

const BLOCKED_ACTIONS = [
  'open_midi_port',
  'arm_hardware',
  'send_midi',
  'write_sysex',
  'mutate_hardware',
] as const;

const REPLAY_COMMANDS = ['python -m rytm_randomizer.cli live-gui-status-footer-model-report'] as const;

export const DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL: LivePerformanceFlowModel = {
  model_version: 'live-gui-performance-flow-model-v1',
  flow_id: 'oxi-rytm-a4-performance-flow',
  flow_status: 'mock-safe',
  current_step_key: 'capture-anchor',
  steps: [
    flowStep(
      'capture-anchor',
      1,
      'Capture Anchor',
      'setup',
      'kit/resnapshot',
      'A4 soft-capture reference',
      'receive-only',
      'Z + send',
      'safe',
    ),
    flowStep(
      'kit-core',
      2,
      'Kit Core',
      'foundation',
      'kit-core',
      'review bass/stab candidates',
      'stage-review-send',
      'home',
      'staged',
    ),
    flowStep(
      'hard-groove',
      3,
      'Hard Groove',
      'pressure',
      'hard-groove',
      'review rhythmic contour',
      'stage-review-send',
      'home',
      'staged',
    ),
    flowStep(
      'industrial',
      4,
      'Industrial',
      'texture',
      'industrial',
      'review texture motion',
      'stage-review-send',
      'home',
      'staged',
    ),
    flowStep(
      'dub-pressure',
      5,
      'Dub Pressure',
      'space',
      'dub-pressure',
      'review delay/reverb space',
      'stage-review-send',
      'home',
      'staged',
    ),
    flowStep(
      'transition',
      6,
      'Transition',
      'handoff',
      'transition',
      'review bridge candidate',
      'dry-run-only',
      'home',
      'review',
    ),
    flowStep(
      'home',
      7,
      'Home',
      'recovery',
      'Z + send',
      'keep A4 review-only',
      'restore-anchor',
      'kit/resnapshot',
      'safe',
    ),
  ],
  blocked_actions: [
    'a4_outbound_macro_send',
    'unattended_hardware_behavior',
    'open_midi_port_without_arm',
    'send_without_dry_run',
  ],
  safety_lines: PASSIVE_SAFETY,
  replay_commands: [
    'python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json',
    'python -m rytm_randomizer.cli oxi-live-macro-catalog-report --json',
    'python -m rytm_randomizer.cli analog-four-oxi-macro-report --json',
  ],
};

export const DEFAULT_LIVE_READINESS_MODEL: LiveReadinessModel = {
  pad_surface: {
    model_version: 'live_gui_12_pad_surface_v1',
    pad_count: 12,
    active_pad_count: 4,
    planned_pad_count: 8,
    cards_by_pad: cardsByPad([
      pad(1, 'BD', 'BD Hard', 'active_v134', true, 'kick', 'BD Hard', 7, 4, 3, [
        'BD Hard',
        'BD Sharp',
        'BD Classic',
        'BD Acoustic',
      ]),
      pad(2, 'SD', 'SD Classic', 'active_v134', true, 'snare', 'SD Classic', 6, 4, 2, [
        'SD Hard',
        'SD Classic',
        'SD FM',
        'BD Classic',
      ]),
      pad(3, 'CH/OH', 'CH Closed', 'active_v134', true, 'hat', 'CH Closed', 9, 4, 5, [
        'CH Closed',
        'OH Open',
        'SY Raw',
        'RS Riser',
      ]),
      pad(4, 'FX/FLT', 'OH Open', 'active_v134', true, 'cymbal', 'OH Open', 9, 4, 5, [
        'OH Open',
        'CH Closed',
        'BD Acoustic',
        'FX Metal',
      ]),
      pad(5, 'BT', 'BT Rim', 'planned_v134', false, 'tom', 'BT Rim', 3, 1, 2, ['BT Rim']),
      pad(6, 'LT', 'LT Low', 'planned_v134', false, 'tom', 'LT Low', 3, 1, 2, ['LT Low']),
      pad(7, 'MT', 'MT Mid', 'planned_v134', false, 'tom', 'MT Mid', 3, 1, 2, ['MT Mid']),
      pad(8, 'HT', 'HT High', 'planned_v134', false, 'tom', 'HT High', 3, 1, 2, ['HT High']),
      pad(9, 'CP', 'CP Clap', 'planned_v134', false, 'perc', 'CP Clap', 4, 1, 3, ['CP Clap']),
      pad(10, 'RS', 'RS Riser', 'planned_v134', false, 'fx', 'RS Riser', 4, 1, 3, ['RS Riser']),
      pad(11, 'SY', 'SY Raw', 'planned_v134', false, 'synth', 'SY Raw', 4, 1, 3, ['SY Raw']),
      pad(12, 'BD', 'BD Acoustic', 'planned_v134', false, 'kick', 'BD Acoustic', 3, 1, 2, [
        'BD Acoustic',
      ]),
    ]),
    blocked_actions: BLOCKED_ACTIONS,
    safety: PASSIVE_SAFETY,
  },
  device_inventory: {
    model_version: 'live_gui_device_inventory_v1',
    device_count: 2,
    cards_by_device_id: {
      analog_rytm_mk2: device(
        'analog_rytm_mk2',
        'Analog Rytm MKII',
        0,
        12,
        '1',
        '00 20 3c',
        '12-pad drum and sample performance surface',
      ),
      analog_four_mk2: device(
        'analog_four_mk2',
        'Analog Four MKII',
        1,
        4,
        '1',
        '00 20 3c',
        '4-track synth performance surface',
      ),
    },
    blocked_actions: BLOCKED_ACTIONS,
    safety: PASSIVE_SAFETY,
  },
  scene_queue: {
    model_version: 'live-gui-scene-queue-model-v1',
    source_module: 'reports.live_gui_scene_queue_model',
    scene_count: 6,
    queue_status: 'review-needed',
    scene_cards: [
      scene('S0', 1, 'Home Clean', 'Return to anchors', 'home', [1, 2, 3, 4], [], ['micro'], 15, 18, 'safe'),
      scene('S1', 2, 'Rolling', 'Introduce rolling low-end motion', 'rolling', [1, 2, 3, 4], ['body'], ['groove'], 42, 42, 'armed'),
      scene('S2', 3, 'Deeper Tunnel', 'Push into depth and movement', 'deeper', [1, 2, 3, 4], ['filter'], ['groove'], 42, 68, 'armed'),
      scene('S3', 4, 'Metallic Pressure', 'Add metallic tension and grit', 'intense_grit', [1, 2, 3, 4], ['grit'], ['strong'], 68, 93, 'high-risk'),
      scene('S4', 5, 'Controlled Chaos', 'Max motion with control', 'wild_controlled', [1, 2, 3, 4], ['full'], ['strong'], 85, 121, 'high-risk'),
      scene('S5', 6, 'Back to Clean', 'Release back to anchors', 'clean', [1, 2, 3, 4], [], ['micro'], 15, 22, 'safe'),
    ],
    preview_queue: [
      queueItem('S1', 1, 'current', 'Rolling', 'armed', 16, 42, [1, 2, 3, 4], 42),
      queueItem('S1A', 2, 'up-next-1', 'Rolling Light', 'armed', 16, 22, [1, 2, 3, 4], 35),
      queueItem('S2', 3, 'up-next-2', 'Deeper Tunnel', 'armed', 32, 42, [1, 2, 3, 4], 68),
      queueItem('S3', 4, 'up-next-3', 'Metallic Pressure', 'high-risk', 32, 68, [1, 2, 3, 4], 93),
    ],
    safety_lines: PASSIVE_SAFETY,
    blocked_actions: BLOCKED_ACTIONS,
  },
  status_footer: {
    status_footer_version: 'live-gui-status-footer-model-v1',
    status_footer_id: 'default-status-footer',
    session_label: 'Live Session',
    items: [
      footerItem('safety', 0, 'Mock Safe', 'No hardware will be changed', 'safe', 'safe'),
      footerItem('midi-port', 1, 'No MIDI Port Open', 'No MIDI port selected', 'closed', 'safe'),
      footerItem('hardware', 2, 'Hardware Off', 'Hardware controls locked', 'off', 'safe'),
      footerItem('mode', 3, 'Simulation / Mock', 'Simulation mode', 'simulation', 'info'),
      footerItem('send-state', 4, 'no unsaved sends', 'Send queue clean', 'clean', 'safe'),
      footerItem('version', 5, 'Version', 'v1.34.0', 'info', 'info'),
    ],
    safety_lines: PASSIVE_SAFETY,
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: REPLAY_COMMANDS,
  },
  snapshot_history: {
    snapshot_history_version: 'live-gui-snapshot-history-model-v1',
    snapshot_history_id: 'default-snapshot-history',
    session_label: 'Live Session',
    current_id: 'snap-3',
    current_index: 2,
    entry_count: 3,
    entries: [
      historyEntry(0, 'snap-1', 'Initial snapshot', 'root', null, null, false),
      historyEntry(1, 'snap-2', 'Auto snapshot 2', 'preview', 'snap-1', 'regen', false),
      historyEntry(2, 'snap-3', 'industrial-peak', 'saved', 'snap-2', 'send', true),
    ],
    controls: [
      control('undo', 0, 'Undo', true, 'snap-2', 'Undo to previous snapshot snap-2.'),
      control('redo', 1, 'Redo', false, null, 'No redo stack is modeled by the cockpit history store yet.'),
      control('load-current', 2, 'Load Current', false, 'snap-3', 'Current snapshot is already loaded.'),
    ],
    safety_lines: PASSIVE_SAFETY,
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: REPLAY_COMMANDS,
  },
  safety_checklist: {
    safety_checklist_version: 'live-gui-safety-checklist-model-v1',
    safety_checklist_id: 'default-safety-checklist',
    session_label: 'Live Session',
    checklist_status: 'passed',
    passed_count: 4,
    total_count: 4,
    items: [
      safetyItem(
        'conflicting-sessions',
        0,
        'No conflicting sessions',
        'passed',
        'safe',
        'No conflicting sessions detected',
        'No action required.',
      ),
      safetyItem(
        'guards-enabled',
        1,
        'All guards enabled',
        'passed',
        'safe',
        'All safety guards enabled',
        'No action required.',
      ),
      safetyItem(
        'snapshot-compatible',
        2,
        'Snapshot compatibility verified',
        'passed',
        'safe',
        'Snapshot compatibility verified',
        'No action required.',
      ),
      safetyItem(
        'parameter-limits',
        3,
        'Parameter limits within safe range',
        'passed',
        'safe',
        'Parameter limits within safe range',
        'No action required.',
      ),
    ],
    arm_gate: {
      key: 'arm-hardware',
      label: 'Arm Hardware',
      state: 'locked',
      enabled: false,
      reason: 'Arm Hardware stays locked until SEND readiness, dry run, MIDI port, and hardware metadata are all ready.',
      requirements: ['send plan ready', 'dry run complete', 'MIDI port open', 'hardware connected'],
      midi_port_name: null,
      midi_port_open: false,
      hardware_connected: false,
      send_plan_ready: false,
      dry_run_complete: false,
      test_id: 'safety-checklist-arm-hardware',
    },
    safety_lines: PASSIVE_SAFETY,
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: REPLAY_COMMANDS,
  },
  command_queue: {
    command_queue_version: 'live-gui-command-queue-model-v1',
    command_queue_id: 'default-command-queue',
    session_label: 'Live Session',
    queue_status: 'queued',
    dry_run_active: true,
    hardware_armed: false,
    active_command_key: null,
    queued_commands: [
      command('queued-command-snapshot-save', 0, 'Snapshot Save (Pre-Mutation)', 'snapshot-save', 'history', 0),
      command('queued-command-mutate-pad-11', 1, 'Mutate Pad 11 (SY Raw)', 'mutate-pad', 'Pad 11 / SY Raw', 8),
      command('queued-command-mutate-pad-1', 2, 'Mutate Pad 1 (BD Hard)', 'mutate-pad', 'Pad 1 / BD Hard', 7),
      command('queued-command-parameter-lock-check', 3, 'Parameter Lock Check', 'preflight-check', 'snapshot compatibility', 0),
    ],
    last_actions: [
      actionRow('last-action-snap-3', 0, 'Send snapshot', 'current', 'send', 'snap-3', 'saved snapshot via send'),
      actionRow('last-action-snap-2', 1, 'Preview generated', 'past', 'regen', 'snap-2', 'auto snapshot via regen'),
    ],
    undo_stack: [
      undoEntry('undo-stack-snap-3', 0, 'industrial-peak', 'current', 'snap-3', true),
      undoEntry('undo-stack-snap-2', 1, 'Auto snapshot 2', 'available', 'snap-2', false),
    ],
    safety_lines: PASSIVE_SAFETY,
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: REPLAY_COMMANDS,
  },
  analyzer_panel: {
    title: 'Analyzer (Post-Mutation Preview)',
    panel_model_version: 'live-gui-analyzer-panel-model-v1',
    panel_id: 'default-analyzer-panel',
    panel_status: 'empty',
    panel_mode: 'split',
    reference_label: 'No reference loaded',
    source_kind: 'none',
    confidence: 'none',
    bpm: 0,
    tempo_stability_percent: 0,
    waveform_bins: [
      waveformBin(0, 'bin 1', 0, 'empty'),
      waveformBin(1, 'bin 2', 0, 'empty'),
      waveformBin(2, 'bin 3', 0, 'empty'),
      waveformBin(3, 'bin 4', 0, 'empty'),
    ],
    spectrum_bands: [
      band('low', 'Low', 20, 120, 0, 'empty'),
      band('body', 'Body', 120, 350, 0, 'empty'),
      band('mid', 'Mid', 350, 2500, 0, 'empty'),
      band('high', 'High', 2500, 12000, 0, 'empty'),
      band('noise', 'Noise', 12000, 20000, 0, 'empty'),
    ],
    controls: [
      analyzerControl('preview', 'Preview', false, 'waiting-for-reference'),
      analyzerControl('dry_run', 'Dry Run', false, 'waiting-for-reference'),
      analyzerControl('arm_hardware', 'Arm Hardware', false, 'locked'),
    ],
    required_actions: ['load-reference'],
    blocked_actions: BLOCKED_ACTIONS,
    safety: {
      passive: true,
      reads_audio_files: false,
      records_audio: false,
      streams_audio: false,
      launches_gui: false,
      opens_ports: false,
      sends_midi: false,
      mutates_hardware: false,
      writes_files: false,
    },
    replay_commands: [
      'python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description <reference-notes> --json',
    ],
  },
  hardware_rail: {
    model_version: 'live-gui-hardware-rail-v1',
    rail_id: 'default-hardware-rail',
    session_label: 'Live Session',
    device_label: 'Analog Rytm MKII',
    mode_label: 'Simulation / Mock',
    rail_status: 'mock-safe',
    dry_run_active: true,
    hardware_requested: false,
    port_status: 'none',
    selected_port_name: null,
    available_ports: [],
    safety_checks: [
      hardwareCheck('no-conflicting-sessions', 'no-conflicting-sessions', true, 'passed'),
      hardwareCheck('guards-enabled', 'guards-enabled', true, 'passed'),
      hardwareCheck('snapshot-compatible', 'snapshot-compatible', true, 'passed'),
      hardwareCheck('parameter-limits-safe', 'parameter-limits-safe', true, 'passed'),
    ],
    safety_check_count: 4,
    safety_checks_passed: 4,
    failing_safety_checks: [],
    arm_status: 'locked',
    arm_locked: true,
    cards: [
      hardwareCard(
        'mock-dry-run',
        'Mock / Dry Run',
        'active',
        'safe',
        'All changes are simulated. No hardware will be modified.',
        ['preview and dry-run controls are metadata only'],
        hardwareAction('toggle-dry-run', 'Toggle dry run', false, 'passive GUI state toggle metadata only'),
      ),
      hardwareCard(
        'midi-port',
        'MIDI Port',
        'none',
        'blocked',
        'No MIDI port selected or opened.',
        [],
        hardwareAction('select-midi-port', 'Open MIDI Port', false, 'no passive port labels supplied'),
      ),
      hardwareCard(
        'arm-hardware',
        'Arm Hardware',
        'locked',
        'blocked',
        'Hardware arm is locked until prerequisites are satisfied.',
        ['dry-run mode is active'],
        hardwareAction('arm-hardware', 'Arm hardware', false, 'dry-run mode is active'),
      ),
    ],
    required_actions: ['select-midi-port', 'disable-dry-run-before-hardware', 'request-hardware-arm'],
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: REPLAY_COMMANDS,
    safety: PASSIVE_SAFETY,
  },
  snapshot_compatibility: {
    model_version: 'live-gui-snapshot-compatibility-v1',
    compatibility_id: 'default-snapshot-compatibility',
    panel_label: 'Snapshot Compatibility',
    session_label: 'Live Session',
    compatibility_status: 'compatible',
    status_badge: 'Compatible',
    summary: '12 of 12 pads are snapshot-mutable for mock-safe review.',
    pad_count: 12,
    snapshot_mutable_pad_count: 4,
    planned_pad_count: 8,
    view_details_enabled: true,
    pads: [
      compatibilityPad(1, 'BD', 'BD Hard', 'compatible', 'ready', true, 7, 4, 3, ''),
      compatibilityPad(2, 'SD', 'SD Classic', 'compatible', 'ready', true, 6, 4, 2, ''),
      compatibilityPad(3, 'CH/OH', 'CH Closed', 'compatible', 'ready', true, 9, 4, 5, ''),
      compatibilityPad(4, 'FX/FLT', 'OH Open', 'compatible', 'ready', true, 9, 4, 5, ''),
      compatibilityPad(5, 'BT', 'BT Rim', 'compatible', 'ready', true, 3, 1, 2, ''),
      compatibilityPad(6, 'LT', 'LT Low', 'compatible', 'ready', true, 3, 1, 2, ''),
      compatibilityPad(7, 'MT', 'MT Mid', 'compatible', 'ready', true, 3, 1, 2, ''),
      compatibilityPad(8, 'HT', 'HT High', 'compatible', 'ready', true, 3, 1, 2, ''),
      compatibilityPad(9, 'CP', 'CP Clap', 'compatible', 'ready', true, 4, 1, 3, ''),
      compatibilityPad(10, 'RS', 'RS Riser', 'compatible', 'ready', true, 4, 1, 3, ''),
      compatibilityPad(11, 'SY', 'SY Raw', 'compatible', 'ready', true, 4, 1, 3, ''),
      compatibilityPad(12, 'BD', 'BD Acoustic', 'compatible', 'ready', true, 3, 1, 2, ''),
    ],
    required_actions: ['review-planned-pad-locks', 'implement-remaining-pad-engines'],
    blocked_actions: BLOCKED_ACTIONS,
    replay_commands: ['python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report'],
    safety: PASSIVE_SAFETY,
  },
};

function flowStep(
  key: string,
  order: number,
  label: string,
  phase: string,
  rytmCommand: string,
  analogFourAction: string,
  sendPolicy: string,
  recoveryAction: string,
  status: string,
): LivePerformanceFlowStepModel {
  return {
    key,
    order,
    label,
    phase,
    rytm_command: rytmCommand,
    analog_four_action: analogFourAction,
    send_policy: sendPolicy,
    recovery_action: recoveryAction,
    status,
  };
}

function cardsByPad(
  cards: ReadonlyArray<LiveGuiRytmPadSurfaceCardDict>,
): Readonly<Record<number, LiveGuiRytmPadSurfaceCardDict>> {
  return Object.fromEntries(cards.map((card) => [card.pad, card])) as Readonly<
    Record<number, LiveGuiRytmPadSurfaceCardDict>
  >;
}

function pad(
  padNumber: number,
  trackCode: string,
  label: string,
  surfaceState: string,
  uiEnabled: boolean,
  defaultRole: string,
  defaultMachineLabel: string,
  legalMachineCount: number,
  snapshotMutableMachineCount: number,
  selectableOnlyMachineCount: number,
  primaryMachineLabels: ReadonlyArray<string>,
): LiveGuiRytmPadSurfaceCardDict {
  return {
    pad: padNumber,
    track_code: trackCode,
    label,
    surface_state: surfaceState,
    ui_enabled: uiEnabled,
    ui_locked: !uiEnabled,
    lock_reason: uiEnabled ? '' : 'awaiting V1.34-compatible mutation routing for pads 5-12',
    default_role: defaultRole,
    default_machine_label: defaultMachineLabel,
    legal_machine_count: legalMachineCount,
    snapshot_mutable_machine_count: snapshotMutableMachineCount,
    selectable_only_machine_count: selectableOnlyMachineCount,
    primary_machine_labels: primaryMachineLabels,
  };
}

function device(
  deviceId: string,
  displayName: string,
  order: number,
  trackCount: number,
  defaultMidiChannelLabel: string,
  manufacturerId: string,
  roleSummary: string,
): LiveGuiDeviceInventoryCardDict {
  return {
    device_id: deviceId,
    display_name: displayName,
    order,
    track_count: trackCount,
    default_midi_channel_label: defaultMidiChannelLabel,
    sysex_manufacturer_id_hex: manufacturerId,
    role_summary: roleSummary,
    port_state: 'not_open',
    hardware_state: 'locked',
    mock_state: 'mock_safe',
    can_open_port: false,
    can_arm_hardware: false,
    capability_badges: ['snapshot_decode', 'mutation_plan', 'mock_render', 'guarded_send'],
    passive: true,
  };
}

function scene(
  sceneKey: string,
  order: number,
  label: string,
  description: string,
  action: string,
  affectedPads: ReadonlyArray<number>,
  zoneTokens: ReadonlyArray<string>,
  depthTokens: ReadonlyArray<string>,
  depthPercent: number,
  dryRunMessages: number,
  status: string,
): LiveGuiSceneCardDict {
  return {
    scene_key: sceneKey,
    order,
    label,
    description,
    action,
    affected_pads: affectedPads,
    zone_tokens: zoneTokens,
    depth_tokens: depthTokens,
    mutation_depth_percent: depthPercent,
    dry_run_message_count: dryRunMessages,
    status,
    operator_hint: status === 'high-risk' ? 'High-risk scene requires dry run first.' : 'Ready for passive review.',
    passive: true,
  };
}

function queueItem(
  sceneKey: string,
  queueIndex: number,
  queuePosition: string,
  label: string,
  status: string,
  durationSeconds: number,
  depthPercent: number,
  affectedPads: ReadonlyArray<number>,
  dryRunMessages: number,
): LiveGuiScenePreviewQueueItemDict {
  return {
    scene_key: sceneKey,
    queue_index: queueIndex,
    queue_position: queuePosition,
    label,
    status,
    estimated_duration_seconds: durationSeconds,
    mutation_depth_percent: depthPercent,
    affected_pads: affectedPads,
    dry_run_message_count: dryRunMessages,
    passive: true,
  };
}

function footerItem(
  key: string,
  order: number,
  label: string,
  value: string,
  state: string,
  severity: string,
): LiveGuiStatusFooterItemDict {
  return {
    key,
    order,
    label,
    value,
    state,
    severity,
    action_label: 'Review',
    action_enabled: false,
    test_id: `status-footer-${key}`,
  };
}

function historyEntry(
  order: number,
  snapshotId: string,
  label: string,
  kind: string,
  parentId: string | null,
  via: string | null,
  isCurrent: boolean,
): LiveGuiSnapshotHistoryEntryDict {
  return {
    key: `snapshot-${order}`,
    order,
    snapshot_id: snapshotId,
    label,
    kind,
    via,
    parent_id: parentId,
    device: 'analog_rytm_mk2',
    pad_count: 12,
    scene_slot: 'A01',
    bpm_label: '132 BPM',
    is_current: isCurrent,
    is_saved: kind === 'saved',
    can_load: !isCurrent,
    can_undo_to: isCurrent && parentId !== null,
    summary: 'analog_rytm_mk2: 12 pad(s), scene A01, 132 BPM',
    test_id: `snapshot-history-entry-${order}`,
  };
}

function control(
  key: string,
  order: number,
  label: string,
  enabled: boolean,
  targetSnapshotId: string | null,
  reason: string,
): LiveGuiSnapshotHistoryControlDict {
  return {
    key,
    order,
    label,
    enabled,
    target_snapshot_id: targetSnapshotId,
    reason,
    test_id: `snapshot-history-control-${key}`,
  };
}

function safetyItem(
  key: string,
  order: number,
  label: string,
  status: string,
  severity: string,
  message: string,
  operatorAction: string,
): LiveGuiSafetyChecklistItemDict {
  return {
    key,
    order,
    label,
    status,
    severity,
    message,
    operator_action: operatorAction,
    test_id: `safety-checklist-${key}`,
  };
}

function command(
  key: string,
  order: number,
  label: string,
  actionType: string,
  target: string,
  estimatedMessageCount: number,
): LiveGuiQueuedCommandDict {
  return {
    key,
    order,
    label,
    status: 'queued',
    enabled: false,
    action_type: actionType,
    target,
    dry_run_only: true,
    estimated_message_count: estimatedMessageCount,
    operator_action: 'Review this queued command; dispatch remains disabled in passive mode.',
    test_id: key,
  };
}

function actionRow(
  key: string,
  order: number,
  label: string,
  status: string,
  actionType: string,
  snapshotId: string,
  detail: string,
): LiveGuiLastActionDict {
  return {
    key,
    order,
    label,
    status,
    action_type: actionType,
    snapshot_id: snapshotId,
    device: 'analog_rytm_mk2',
    result: 'ok',
    detail,
    test_id: `last-action-${order}`,
  };
}

function undoEntry(
  key: string,
  order: number,
  label: string,
  status: string,
  snapshotId: string,
  isCurrent: boolean,
): LiveGuiUndoStackEntryDict {
  return {
    key,
    order,
    label,
    status,
    snapshot_id: snapshotId,
    is_current: isCurrent,
    is_undo_target: !isCurrent,
    is_load_target: !isCurrent,
    action_type: 'load-snapshot',
    test_id: `undo-stack-${order}`,
  };
}

function waveformBin(
  index: number,
  label: string,
  valuePercent: number,
  status: string,
): LiveGuiAnalyzerWaveformBinDict {
  return { index, label, value_percent: valuePercent, status };
}

function band(
  key: string,
  label: string,
  lowHz: number,
  highHz: number,
  valuePercent: number,
  status: string,
): LiveGuiAnalyzerSpectrumBandDict {
  return { key, label, low_hz: lowHz, high_hz: highHz, value_percent: valuePercent, status };
}

function analyzerControl(
  key: string,
  label: string,
  enabled: boolean,
  status: string,
): LiveGuiAnalyzerPanelControlDict {
  return { key, label, enabled, status };
}

function hardwareCheck(
  key: string,
  label: string,
  passed: boolean,
  status: string,
): LiveGuiHardwareRailSafetyCheckDict {
  return {
    key,
    label,
    passed,
    status,
    test_id: `hardware-rail-safety-${key}`,
  };
}

function hardwareAction(
  key: string,
  label: string,
  enabled: boolean,
  reason: string,
): LiveGuiHardwareRailActionDict {
  return { key, label, enabled, reason, test_id: `hardware-rail-action-${key}` };
}

function hardwareCard(
  key: string,
  title: string,
  status: string,
  severity: string,
  summary: string,
  details: ReadonlyArray<string>,
  action: LiveGuiHardwareRailActionDict,
): LiveGuiHardwareRailCardDict {
  return {
    key,
    title,
    status,
    severity,
    summary,
    details,
    actions: [action],
    test_id: `hardware-rail-card-${key}`,
  };
}

function compatibilityPad(
  padNumber: number,
  trackCode: string,
  label: string,
  status: string,
  severity: string,
  snapshotMutationEnabled: boolean,
  allowedMachineCount: number,
  mutableMachineCount: number,
  selectableMachineCount: number,
  lockReason: string,
): LiveGuiSnapshotCompatibilityPadDict {
  return {
    pad: padNumber,
    track_code: trackCode,
    label,
    status,
    severity,
    map_safe: allowedMachineCount > 0,
    snapshot_mutation_enabled: snapshotMutationEnabled,
    allowed_machine_count: allowedMachineCount,
    mutable_machine_count: mutableMachineCount,
    selectable_machine_count: selectableMachineCount,
    lock_reason: lockReason,
    machine_labels: [label],
    test_id: `snapshot-compatibility-pad-${String(padNumber).padStart(2, '0')}`,
  };
}

function orderedPadCards(
  model: LiveGuiRytmTwelvePadSurfaceModelDict,
): ReadonlyArray<LiveGuiRytmPadSurfaceCardDict> {
  return Object.values(model.cards_by_pad).sort((left, right) => left.pad - right.pad);
}

function orderedDeviceCards(
  cardsByDeviceId: LiveReadinessModel['device_inventory']['cards_by_device_id'],
): ReadonlyArray<LiveGuiDeviceInventoryCardDict> {
  return Object.values(cardsByDeviceId).sort((left, right) => left.order - right.order);
}

export function LiveReadinessPanel({
  model = DEFAULT_LIVE_READINESS_MODEL,
  performanceFlow = DEFAULT_LIVE_PERFORMANCE_FLOW_MODEL,
}: LiveReadinessPanelViewProps): JSX.Element {
  return (
    <section
      className="cockpit-panel live-readiness-panel"
      data-testid="live-readiness-panel"
      aria-labelledby="live-readiness-title"
    >
      <header className="live-readiness-header">
        <h2 id="live-readiness-title">Live Readiness</h2>
        <p className="panel-meta">Passive GUI consumers for cockpit readiness models</p>
      </header>
      <div className="live-readiness-grid">
        <LiveTwelvePadSurface model={model.pad_surface} />
        <LiveDeviceInventory model={model.device_inventory} />
        <LiveSceneQueue model={model.scene_queue} />
        <LivePerformanceFlow model={performanceFlow} />
        <LiveStatusFooter model={model.status_footer} />
        <LiveSnapshotHistory model={model.snapshot_history} />
        <LiveSafetyChecklist model={model.safety_checklist} />
        <LiveCommandQueue model={model.command_queue} />
        <LiveAnalyzerPanel model={model.analyzer_panel} />
        <LiveHardwareRail model={model.hardware_rail} />
        <LiveSnapshotCompatibility model={model.snapshot_compatibility} />
      </div>
    </section>
  );
}

export function LivePerformanceFlow({ model }: { model: LivePerformanceFlowModel }): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-performance-flow">
      <SurfaceTitle title="Performance Flow" meta={`${model.steps.length} steps / ${model.flow_status}`} />
      <div className="live-performance-rail">
        {model.steps.map((step) => (
          <article
            key={step.key}
            className={`live-performance-step ${step.status} ${
              step.key === model.current_step_key ? 'current' : 'next'
            }`}
            data-testid={`live-performance-flow-step-${step.key}`}
          >
            <span className="live-pad-index">
              {step.order}. {step.phase}
            </span>
            <strong>{step.label}</strong>
            <span>Rytm: {step.rytm_command}</span>
            <span>A4: {step.analog_four_action}</span>
            <small>
              {step.send_policy} / recovery {step.recovery_action}
            </small>
          </article>
        ))}
      </div>
      <div className="live-chip-row">
        {model.blocked_actions.map((action) => (
          <span key={action} className="live-chip live-chip-blocked">
            {action}
          </span>
        ))}
      </div>
      <div className="live-chip-row">
        {model.replay_commands.map((commandText) => (
          <span key={commandText} className="live-chip">
            {commandText}
          </span>
        ))}
      </div>
    </section>
  );
}

function SurfaceTitle({ title, meta }: { title: string; meta: string }): JSX.Element {
  return (
    <header className="live-surface-header">
      <h3>{title}</h3>
      <span>{meta}</span>
    </header>
  );
}

export function LiveTwelvePadSurface({
  model,
}: {
  model: LiveReadinessModel['pad_surface'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-12-pad-surface">
      <SurfaceTitle title="Pad Surface" meta={`${model.active_pad_count} active pads, ${model.planned_pad_count} planned pads`} />
      <div className="live-pad-grid">
        {orderedPadCards(model).map((padItem) => (
          <article
            key={padItem.pad}
            className={`live-pad-card ${padItem.surface_state}`}
            data-testid={`live-pad-${padItem.pad}`}
          >
            <span className="live-pad-index">Pad {padItem.pad}</span>
            <strong>{padItem.label}</strong>
            <span>{padItem.track_code}</span>
            <span>{padItem.default_role}</span>
            <span>{padItem.default_machine_label}</span>
            <small>{padItem.lock_reason || 'ready for dry-run review'}</small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveDeviceInventory({
  model,
}: {
  model: LiveReadinessModel['device_inventory'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-device-inventory">
      <SurfaceTitle title="Device Inventory" meta={`${model.device_count} devices`} />
      <div className="live-list">
        {orderedDeviceCards(model.cards_by_device_id).map((deviceItem) => (
          <article key={deviceItem.device_id} className="live-row">
            <strong>{deviceItem.display_name}</strong>
            <span>{deviceItem.role_summary}</span>
            <span>
              {deviceItem.track_count} tracks / {deviceItem.mock_state}
            </span>
            <div className="live-chip-row">
              {deviceItem.capability_badges.map((capability) => (
                <span key={capability} className="live-chip">
                  {capability}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSceneQueue({
  model,
}: {
  model: LiveReadinessModel['scene_queue'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-scene-queue">
      <SurfaceTitle title="Scene Queue" meta={model.queue_status} />
      <div className="live-scene-rail">
        {model.scene_cards.map((sceneItem) => (
          <article key={sceneItem.scene_key} className={`live-scene-card ${sceneItem.status}`}>
            <strong>{sceneItem.scene_key}</strong>
            <span>{sceneItem.label}</span>
            <small>{sceneItem.description}</small>
            <span>{sceneItem.affected_pads.join('/')}</span>
            <span>{sceneItem.mutation_depth_percent}%</span>
            <span>{sceneItem.dry_run_message_count} msgs</span>
          </article>
        ))}
      </div>
      <div className="live-preview-queue">
        {model.preview_queue.map((item) => (
          <article key={`${item.queue_position}-${item.scene_key}`} className="live-preview-step">
            <strong>{item.scene_key}</strong>
            <span>{item.label}</span>
            <small>
              {item.queue_position} / {item.estimated_duration_seconds}s / {item.status}
            </small>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveStatusFooter({
  model,
}: {
  model: LiveReadinessModel['status_footer'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-status-footer">
      <SurfaceTitle title="Status Footer" meta={`${model.items.length} chips`} />
      <div className="live-chip-grid">
        {model.items.map((item) => (
          <article key={item.key} className={`live-status-chip ${item.severity}`}>
            <strong>{item.label}</strong>
            <span>{item.value}</span>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSnapshotHistory({
  model,
}: {
  model: LiveReadinessModel['snapshot_history'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-snapshot-history">
      <SurfaceTitle title="Snapshot History" meta={`${model.entry_count} entries`} />
      <div className="live-list">
        {model.entries.map((entry) => (
          <article key={entry.snapshot_id} className={`live-row ${entry.is_current ? 'current' : 'past'}`}>
            <strong>{entry.label}</strong>
            <span>{entry.snapshot_id}</span>
            <small>{entry.summary}</small>
          </article>
        ))}
      </div>
      <div className="live-action-strip">
        {model.controls.map((controlItem) => (
          <button
            key={controlItem.key}
            type="button"
            className="live-readiness-action"
            disabled
            title={controlItem.reason}
          >
            {controlItem.label} / {controlItem.enabled ? 'enabled' : 'disabled'}
          </button>
        ))}
      </div>
    </section>
  );
}

export function LiveSafetyChecklist({
  model,
}: {
  model: LiveReadinessModel['safety_checklist'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-safety-checklist">
      <SurfaceTitle
        title="Safety Checklist"
        meta={`${model.passed_count} / ${model.total_count} / ${model.checklist_status}`}
      />
      <div className="live-list">
        {model.items.map((item) => (
          <article key={item.key} className={`live-row ${item.status}`}>
            <strong>{item.label}</strong>
            <span>{item.status}</span>
            <small>{item.message}</small>
          </article>
        ))}
      </div>
      <button
        type="button"
        className="live-readiness-action live-readiness-action-locked"
        disabled
        title={model.arm_gate.reason}
      >
        {model.arm_gate.label} / {model.arm_gate.state}
      </button>
    </section>
  );
}

export function LiveCommandQueue({
  model,
}: {
  model: LiveReadinessModel['command_queue'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-command-queue">
      <SurfaceTitle title="Command Queue" meta={model.queue_status} />
      <div className="live-command-columns">
        <div>
          <h4>Queued</h4>
          {model.queued_commands.map((commandItem) => (
            <article key={commandItem.key} className="live-row">
              <strong>{commandItem.label}</strong>
              <span>{commandItem.target}</span>
              <small>
                {commandItem.status} / {commandItem.estimated_message_count} msgs
              </small>
            </article>
          ))}
        </div>
        <div>
          <h4>Last Actions</h4>
          {model.last_actions.map((action) => (
            <article key={action.key} className="live-row">
              <strong>{action.label}</strong>
              <span>{action.status}</span>
              <small>{action.detail}</small>
            </article>
          ))}
        </div>
        <div>
          <h4>Undo Stack</h4>
          {model.undo_stack.map((entry) => (
            <article key={entry.key} className="live-row">
              <strong>{entry.label}</strong>
              <span>{entry.status}</span>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

export function LiveAnalyzerPanel({
  model,
}: {
  model: LiveReadinessModel['analyzer_panel'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-analyzer-panel">
      <SurfaceTitle title={model.title} meta={model.panel_status} />
      <p className="live-reference-label">{model.reference_label}</p>
      <div className="live-metric-row">
        <span>{model.bpm.toFixed(1)} BPM</span>
        <span>{model.tempo_stability_percent}%</span>
      </div>
      <div className="live-meter-stack">
        {model.waveform_bins.map((binItem) => (
          <MeterRow key={binItem.label} label={binItem.label} value={binItem.value_percent} status={binItem.status} />
        ))}
      </div>
      <div className="live-meter-stack">
        {model.spectrum_bands.map((bandItem) => (
          <MeterRow key={bandItem.key} label={bandItem.label} value={bandItem.value_percent} status={bandItem.status} />
        ))}
      </div>
    </section>
  );
}

function MeterRow({ label, value, status }: { label: string; value: number; status: string }): JSX.Element {
  return (
    <div className="live-meter-row">
      <span>{label}</span>
      <span
        className={`live-meter ${status}`}
        role="meter"
        aria-label={`${label} ${status}`}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
      >
        <span style={{ width: `${value}%` }} />
      </span>
      <strong>{value}%</strong>
    </div>
  );
}

export function LiveHardwareRail({
  model,
}: {
  model: LiveReadinessModel['hardware_rail'];
}): JSX.Element {
  return (
    <section className="live-surface" data-testid="live-hardware-rail">
      <SurfaceTitle title="Hardware Rail" meta={model.rail_status} />
      <div className="live-list">
        {model.cards.map((card) => (
          <article key={card.key} className={`live-row ${card.status}`}>
            <strong>{card.title}</strong>
            <span>{card.status}</span>
            <small>{card.summary}</small>
            <div className="live-action-strip">
              {card.actions.map((action) => (
                <button
                  key={action.key}
                  type="button"
                  className="live-readiness-action"
                  data-action-enabled={String(action.enabled)}
                  disabled
                  title={action.reason}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function LiveSnapshotCompatibility({
  model,
}: {
  model: LiveReadinessModel['snapshot_compatibility'];
}): JSX.Element {
  return (
    <section className="live-surface live-surface-wide" data-testid="live-snapshot-compatibility">
      <SurfaceTitle title={model.panel_label} meta={model.status_badge} />
      <p className="panel-meta">{model.summary}</p>
      <div className="live-compatibility-grid">
        {model.pads.map((padItem) => (
          <article key={padItem.pad} className={`live-compatibility-pad ${padItem.status}`}>
            <strong>Pad {padItem.pad}</strong>
            <span>{padItem.label}</span>
            <span>{padItem.status}</span>
            <small>{padItem.mutable_machine_count} mutable machines</small>
          </article>
        ))}
      </div>
    </section>
  );
}
