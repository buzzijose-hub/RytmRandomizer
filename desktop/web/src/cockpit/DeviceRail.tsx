import type { ReactNode } from 'react';

import { useCockpitStore } from '../state';
import type {
  LiveGuiDeviceInventoryCardDict,
  LiveGuiDualDeviceRigDeviceDict,
  LiveGuiDualDeviceRigReadinessModelDict,
  LiveGuiDualDeviceRigTrackDict,
  LiveGuiRytmPadSurfaceCardDict,
  LiveGuiSnapshotCompatibilityPadDict,
  PadState,
  SessionStatus,
  Snapshot,
} from '../types';

import {
  ANALOG_FOUR_DEVICE_ID,
  ANALOG_FOUR_TRACKS,
  type CockpitDeviceId,
  RYTM_DEVICE_ID,
} from './devices';

const DEFAULT_SESSION_LABEL = 'Live Session';
const RYTM_PAD_COUNT = 12;

interface BuildDeviceRailReadinessModelOptions {
  snapshot: Snapshot | null;
  session: SessionStatus | null;
}

export interface DeviceRailProps {
  activeDeviceId: CockpitDeviceId;
  onSelectDevice: (deviceId: CockpitDeviceId) => void;
}

export function DeviceRail({ activeDeviceId, onSelectDevice }: DeviceRailProps): JSX.Element {
  const snapshot = useCockpitStore((s) => s.snapshot);
  const session = useCockpitStore((s) => s.sessionStatus);
  const model = buildDeviceRailReadinessModel({ snapshot, session });
  const rytmDevice = model.devices.find(
    (device) => device.device_id === RYTM_DEVICE_ID,
  ) as LiveGuiDualDeviceRigDeviceDict;
  const analogFourDevice = model.devices.find(
    (device) => device.device_id === ANALOG_FOUR_DEVICE_ID,
  ) as LiveGuiDualDeviceRigDeviceDict;
  const rytmTracks = model.tracks.filter((track) => track.device_id === RYTM_DEVICE_ID);
  const analogFourTracks = model.tracks.filter(
    (track) => track.device_id === ANALOG_FOUR_DEVICE_ID,
  );

  return (
    <aside className="device-rail" data-testid="device-rail" aria-label="Device status">
      <div className="rail-section-title">Devices</div>
      <DeviceCard
        name={rytmDevice.display_name}
        status={deviceDisplayStatus(rytmDevice)}
        detail={`${rytmDevice.mapped_track_count} pads mapped`}
        active={activeDeviceId === RYTM_DEVICE_ID}
        testId={rytmDevice.test_id}
        selectTestId="device-select-analog-rytm-mk2"
        onSelect={() => onSelectDevice(RYTM_DEVICE_ID)}
      >
        <div className="device-chip-grid" aria-label="Analog Rytm pad map">
          {rytmTracks.map((track) => (
            <span
              className={track.enabled ? 'device-chip active' : 'device-chip locked'}
              data-testid={track.test_id}
              key={track.test_id}
            >
              <span className="device-chip-index">{track.track_number}</span>
              <span className="device-chip-role">{track.label}</span>
            </span>
          ))}
        </div>
        <p className="device-port-state">{rytmDevice.port_state}</p>
      </DeviceCard>
      <DeviceCard
        name={analogFourDevice.display_name}
        status={deviceDisplayStatus(analogFourDevice)}
        detail={`${analogFourDevice.planned_track_count} tracks staged`}
        active={activeDeviceId === ANALOG_FOUR_DEVICE_ID}
        testId={analogFourDevice.test_id}
        selectTestId="device-select-analog-four-mk2"
        onSelect={() => onSelectDevice(ANALOG_FOUR_DEVICE_ID)}
      >
        <div className="device-chip-grid" aria-label="Analog Four staged track map">
          {analogFourTracks.map((track) => (
            <span className="device-chip staged" data-testid={track.test_id} key={track.test_id}>
              <span className="device-chip-index">{track.track_label}</span>
              <span className="device-chip-role">{track.role}</span>
            </span>
          ))}
        </div>
        <p className="device-port-state">{analogFourDevice.port_state}</p>
      </DeviceCard>
    </aside>
  );
}

export function buildDeviceRailReadinessModel({
  snapshot,
  session,
}: BuildDeviceRailReadinessModelOptions): LiveGuiDualDeviceRigReadinessModelDict {
  const pads = [...(snapshot?.pads ?? [])].sort((left, right) => left.pad_id - right.pad_id);
  const portState = session?.midi_port ?? 'No MIDI port open';
  const hardwareState = session?.mode === 'live' && session.armed ? 'armed' : 'mock-safe';
  const padSurfaceCards = Object.fromEntries(
    pads.map((pad) => [pad.pad_id, rytmPadSurfaceCard(pad)]),
  ) as Readonly<Record<number, LiveGuiRytmPadSurfaceCardDict>>;
  const activeRytmTrackCount = pads.length;
  const plannedRytmTrackCount = Math.max(0, RYTM_PAD_COUNT - activeRytmTrackCount);
  const deviceInventoryCards = {
    [RYTM_DEVICE_ID]: deviceInventoryCard({
      deviceId: RYTM_DEVICE_ID,
      displayName: 'Elektron Analog Rytm MKII',
      order: 1,
      trackCount: Math.max(RYTM_PAD_COUNT, pads.length),
      roleSummary: '12-pad drum and percussion surface',
      portState,
      hardwareState,
      mockState: 'mock-safe available',
      passive: true,
    }),
    [ANALOG_FOUR_DEVICE_ID]: deviceInventoryCard({
      deviceId: ANALOG_FOUR_DEVICE_ID,
      displayName: 'Elektron Analog Four MKII',
      order: 2,
      trackCount: ANALOG_FOUR_TRACKS.length,
      roleSummary: 'staged synth movement plan',
      portState: 'No MIDI port open',
      hardwareState: 'mock-staged',
      mockState: 'staged only',
      passive: true,
    }),
  };
  const rytmTracks = Array.from({ length: RYTM_PAD_COUNT }, (_, index) => {
    const padNumber = index + 1;
    const pad = pads.find((candidatePad) => candidatePad.pad_id === padNumber);
    return pad === undefined ? plannedRytmTrack(padNumber) : rytmTrackFromPad(pad);
  });
  const analogFourTracks = ANALOG_FOUR_TRACKS.map((track) => ({
    device_id: ANALOG_FOUR_DEVICE_ID,
    track_number: track.track,
    track_label: track.trackLabel,
    label: track.trackLabel,
    role: track.roleLabel,
    state: 'mock_staged',
    enabled: false,
    source: 'analog-four-staged-plan',
    test_id: `device-rail-a4-track-${track.track}`,
  }));
  const tracks: ReadonlyArray<LiveGuiDualDeviceRigTrackDict> = [
    ...rytmTracks,
    ...analogFourTracks,
  ];
  const activeTrackCount = tracks.filter((track) => track.enabled).length;
  const plannedTrackCount = tracks.length - activeTrackCount;
  const devices: ReadonlyArray<LiveGuiDualDeviceRigDeviceDict> = [
    {
      device_id: RYTM_DEVICE_ID,
      display_name: 'Analog Rytm MKII',
      order: 1,
      track_count: Math.max(RYTM_PAD_COUNT, pads.length),
      mapped_track_count: Math.max(RYTM_PAD_COUNT, pads.length),
      active_track_count: activeRytmTrackCount,
      planned_track_count: plannedRytmTrackCount,
      status: pads.length === 0 ? 'not-loaded' : 'mock-safe',
      role_summary: '12-pad drum and percussion surface',
      port_state: portState,
      hardware_state: hardwareState,
      summary: `${Math.max(RYTM_PAD_COUNT, pads.length)} tracks / mock-safe`,
      test_id: 'device-card-analog-rytm-mk2',
    },
    {
      device_id: ANALOG_FOUR_DEVICE_ID,
      display_name: 'Analog Four MKII',
      order: 2,
      track_count: ANALOG_FOUR_TRACKS.length,
      mapped_track_count: ANALOG_FOUR_TRACKS.length,
      active_track_count: 0,
      planned_track_count: ANALOG_FOUR_TRACKS.length,
      status: 'mock-staged',
      role_summary: 'staged synth movement plan',
      port_state: 'No MIDI port open',
      hardware_state: 'mock-staged',
      summary: `${ANALOG_FOUR_TRACKS.length} tracks / mock-staged`,
      test_id: 'device-card-analog-four-mk2',
    },
  ];

  return {
    model_version: 'live-gui-dual-device-rig-readiness-v1',
    rig_id: 'device-rail-zustand',
    session_label: DEFAULT_SESSION_LABEL,
    rig_status: 'mock-safe',
    total_device_count: devices.length,
    total_track_count: tracks.length,
    active_track_count: activeTrackCount,
    planned_track_count: plannedTrackCount,
    pad_surface: {
      model_version: 'live-gui-12-pad-surface-v1',
      pad_count: RYTM_PAD_COUNT,
      active_pad_count: activeRytmTrackCount,
      planned_pad_count: plannedRytmTrackCount,
      cards_by_pad: padSurfaceCards,
      blocked_actions: ['no MIDI port opened', 'no MIDI sending'],
      safety: ['passive/read-only', 'mock-first display model'],
    },
    device_inventory: {
      model_version: 'live-gui-device-inventory-v1',
      device_count: devices.length,
      cards_by_device_id: deviceInventoryCards,
      blocked_actions: ['no MIDI port enumeration', 'no hardware mutation'],
      safety: ['passive/read-only', 'device rail display only'],
    },
    hardware_rail: {
      model_version: 'live-gui-hardware-rail-v1',
      rail_id: 'device-rail-hardware-boundary',
      session_label: DEFAULT_SESSION_LABEL,
      device_label: 'Analog Rytm MKII',
      mode_label: session?.mode ?? 'mock',
      rail_status: hardwareState,
      dry_run_active: true,
      hardware_requested: false,
      port_status: portState,
      selected_port_name: session?.midi_port ?? null,
      available_ports: [],
      safety_checks: [
        {
          key: 'mock-first',
          label: 'Mock-first rail rendering',
          passed: true,
          status: 'passed',
          test_id: 'device-rail-safety-mock-first',
        },
      ],
      safety_check_count: 1,
      safety_checks_passed: 1,
      failing_safety_checks: [],
      arm_status: 'locked',
      arm_locked: true,
      cards: [],
      required_actions: ['run dry-run before hardware'],
      blocked_actions: ['no MIDI port opened', 'no MIDI sending'],
      replay_commands: [],
      safety: ['passive/read-only'],
    },
    snapshot_compatibility: {
      model_version: 'live-gui-snapshot-compatibility-v1',
      compatibility_id: snapshot?.snapshot_id ?? 'no-snapshot',
      panel_label: 'Snapshot Compatibility',
      session_label: DEFAULT_SESSION_LABEL,
      compatibility_status: pads.length === 0 ? 'not-loaded' : 'compatible',
      status_badge: pads.length === 0 ? 'No snapshot' : 'Compatible',
      summary:
        pads.length > 0
          ? `${activeRytmTrackCount} pads are mutation-ready for mock-safe review.`
          : 'No snapshot loaded.',
      pad_count: pads.length,
      snapshot_mutable_pad_count: activeRytmTrackCount,
      planned_pad_count: plannedRytmTrackCount,
      view_details_enabled: pads.length > 0,
      pads: pads.map(snapshotCompatibilityPad),
      required_actions: [],
      blocked_actions: ['no MIDI port opened', 'no MIDI sending'],
      replay_commands: [],
      safety: ['passive/read-only'],
    },
    devices,
    tracks,
    required_actions: ['review dual-device readiness before arming hardware'],
    blocked_actions: ['no GUI-side MIDI send', 'no unattended hardware behavior'],
    replay_commands: [],
    safety: ['passive/read-only', 'mock-first display model'],
  };
}

function deviceDisplayStatus(device: LiveGuiDualDeviceRigDeviceDict): string {
  if (device.device_id === RYTM_DEVICE_ID) {
    return device.hardware_state === 'armed' ? 'Armed' : 'Mock Safe';
  }
  return 'Mock Staged';
}

function rytmPadSurfaceCard(pad: PadState): LiveGuiRytmPadSurfaceCardDict {
  return {
    pad: pad.pad_id,
    track_code: String(pad.pad_id),
    label: pad.machine,
    surface_state: 'active_v134',
    ui_enabled: true,
    ui_locked: false,
    lock_reason: '',
    default_role: pad.machine,
    default_machine_label: pad.machine,
    legal_machine_count: 1,
    snapshot_mutable_machine_count: 1,
    selectable_only_machine_count: 0,
    primary_machine_labels: [pad.machine],
  };
}

function rytmTrackFromPad(pad: PadState): LiveGuiDualDeviceRigTrackDict {
  return {
    device_id: RYTM_DEVICE_ID,
    track_number: pad.pad_id,
    track_label: `Pad ${pad.pad_id}`,
    label: pad.machine,
    role: pad.machine,
    state: 'active_v134',
    enabled: true,
    source: 'rytm-12-pad-surface',
    test_id: `device-rail-rytm-pad-${pad.pad_id}`,
  };
}

function plannedRytmTrack(padNumber: number): LiveGuiDualDeviceRigTrackDict {
  return {
    device_id: RYTM_DEVICE_ID,
    track_number: padNumber,
    track_label: `Pad ${padNumber}`,
    label: `Pad ${padNumber}`,
    role: 'Planned',
    state: 'planned_v134',
    enabled: false,
    source: 'rytm-12-pad-surface-planned',
    test_id: `device-rail-rytm-pad-${padNumber}`,
  };
}

function deviceInventoryCard({
  deviceId,
  displayName,
  order,
  trackCount,
  roleSummary,
  portState,
  hardwareState,
  mockState,
  passive,
}: {
  deviceId: string;
  displayName: string;
  order: number;
  trackCount: number;
  roleSummary: string;
  portState: string;
  hardwareState: string;
  mockState: string;
  passive: boolean;
}): LiveGuiDeviceInventoryCardDict {
  return {
    device_id: deviceId,
    display_name: displayName,
    order,
    track_count: trackCount,
    default_midi_channel_label: 'none',
    sysex_manufacturer_id_hex: '00 20 3C',
    role_summary: roleSummary,
    port_state: portState,
    hardware_state: hardwareState,
    mock_state: mockState,
    can_open_port: false,
    can_arm_hardware: false,
    capability_badges: ['passive', 'mock-first'],
    passive,
  };
}

function snapshotCompatibilityPad(pad: PadState): LiveGuiSnapshotCompatibilityPadDict {
  return {
    pad: pad.pad_id,
    track_code: String(pad.pad_id),
    label: pad.machine,
    status: 'compatible',
    severity: 'safe',
    map_safe: true,
    snapshot_mutation_enabled: true,
    allowed_machine_count: 1,
    mutable_machine_count: 1,
    selectable_machine_count: 1,
    lock_reason: '',
    machine_labels: [pad.machine],
    test_id: `device-rail-compat-pad-${pad.pad_id}`,
  };
}

function DeviceCard({
  name,
  status,
  detail,
  active,
  testId,
  selectTestId,
  onSelect,
  children,
}: {
  name: string;
  status: string;
  detail: string;
  active: boolean;
  testId: string;
  selectTestId: string;
  onSelect: () => void;
  children: ReactNode;
}): JSX.Element {
  return (
    <section
      className={active ? 'device-card active' : 'device-card'}
      aria-label={name}
      data-testid={testId}
    >
      <div className="device-card-header">
        <div>
          <h2>{name}</h2>
          <p>{detail}</p>
        </div>
        <span className={active ? 'device-status ready' : 'device-status staged'}>{status}</span>
      </div>
      <button
        type="button"
        className="device-select-button"
        aria-pressed={active}
        data-testid={selectTestId}
        onClick={onSelect}
      >
        {active ? 'Viewing' : 'View'}
      </button>
      {children}
    </section>
  );
}
