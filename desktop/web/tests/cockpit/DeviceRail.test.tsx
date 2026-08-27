import { act, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import {
  DeviceRail,
  HARDWARE_NOTICE_BY_PHASE,
  buildDeviceRailReadinessModel,
  resolveConnectionPhase,
} from '../../src/cockpit/DeviceRail';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from '../../src/cockpit/devices';
import { useCockpitStore } from '../../src/state';
import type { ConnectionStateDict } from '../../src/ws/protocol';

import {
  connectionFault,
  connectionListening,
  patchGenome,
  readyDualMachineStage,
  sessionLive,
  sessionMock,
  snapshot,
} from './_fixtures';

const connectionSearching: ConnectionStateDict = {
  phase: 'searching',
  available_inputs: [],
  available_outputs: [],
  selected_input: null,
  selected_output: null,
  last_error_fingerprint: null,
  changed_at: 500.0,
};

describe('DeviceRail', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('renders the full Rytm 12-pad surface and staged Analog Four track plan', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(
      <DeviceRail
        activeDeviceId={RYTM_DEVICE_ID}
        onSelectDevice={() => undefined}
        onCaptureDevice={() => undefined}
      />,
    );

    const rail = screen.getByTestId('device-rail');
    const rytm = within(rail).getByTestId('device-card-analog-rytm-mk2');
    const analogFour = within(rail).getByTestId('device-card-analog-four-mk2');

    expect(rytm).toHaveTextContent('Analog Rytm MKII');
    expect(rytm).toHaveTextContent('12 pads mapped');
    expect(within(rytm).getAllByTestId(/device-rail-rytm-pad-/)).toHaveLength(12);
    const pad12 = within(rytm).getByTestId('device-rail-rytm-pad-12');
    expect(pad12).toHaveTextContent('BD Acoustic');
    expect(pad12).toHaveClass('active');

    expect(analogFour).toHaveTextContent('Analog Four MKII');
    expect(analogFour).toHaveTextContent('4 tracks staged');
    expect(within(analogFour).getAllByTestId(/device-rail-a4-track-/)).toHaveLength(4);
    expect(within(analogFour).getByTestId('device-rail-a4-track-1')).toHaveTextContent(
      'Bass / low pulse',
    );
    expect(within(analogFour).getByTestId('device-rail-a4-track-4')).toHaveTextContent(
      'Space / accent',
    );
  });

  it('marks the selected device and emits selection changes', () => {
    const selected: string[] = [];
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(
      <DeviceRail
        activeDeviceId={ANALOG_FOUR_DEVICE_ID}
        onSelectDevice={(deviceId) => selected.push(deviceId)}
        onCaptureDevice={() => undefined}
      />,
    );

    expect(screen.getByTestId('device-card-analog-four-mk2')).toHaveClass('active');
    expect(screen.getByTestId('device-card-analog-rytm-mk2')).not.toHaveClass('active');

    screen.getByTestId('device-select-analog-rytm-mk2').click();
    expect(selected).toEqual([RYTM_DEVICE_ID]);
  });

  it('builds the rendered rail from the dual-device readiness model contract', () => {
    const model = buildDeviceRailReadinessModel({
      session: sessionMock,
      snapshot,
      connection: null,
    });

    expect(model.model_version).toBe('live-gui-dual-device-rig-readiness-v1');
    expect(model.rig_status).toBe('mock-safe');
    expect(model.total_device_count).toBe(2);
    expect(model.total_track_count).toBe(16);
    expect(model.active_track_count).toBe(12);
    expect(model.planned_track_count).toBe(4);
    expect(model.devices.map((device) => device.device_id)).toEqual([
      'analog_rytm_mk2',
      'analog_four_mk2',
    ]);
    expect(model.devices[0]).toMatchObject({
      display_name: 'Analog Rytm MKII',
      mapped_track_count: 12,
      active_track_count: 12,
      planned_track_count: 0,
      status: 'mock-safe',
      // sessionMock reports phase 'disconnected' → honest no-hardware notice.
      port_state: 'No hardware detected — device scan idle',
    });
    expect(model.devices[1]).toMatchObject({
      display_name: 'Analog Four MKII',
      mapped_track_count: 4,
      planned_track_count: 4,
      status: 'mock-staged',
    });
    expect(model.tracks[0]).toMatchObject({
      device_id: 'analog_rytm_mk2',
      track_number: 1,
      label: 'BD Hard',
      source: 'rytm-12-pad-surface',
      test_id: 'device-rail-rytm-pad-1',
    });
    expect(model.tracks[11]).toMatchObject({
      device_id: 'analog_rytm_mk2',
      track_number: 12,
      enabled: true,
      state: 'active_v134',
      source: 'rytm-12-pad-surface',
    });
    expect(model.tracks[15]).toMatchObject({
      device_id: 'analog_four_mk2',
      track_number: 4,
      role: 'Space / accent',
      source: 'analog-four-staged-plan',
      test_id: 'device-rail-a4-track-4',
    });
  });

  it('builds a passive no-snapshot readiness model before a snapshot is loaded', () => {
    const model = buildDeviceRailReadinessModel({
      session: null,
      snapshot: null,
      connection: null,
    });

    expect(model.rig_status).toBe('mock-safe');
    expect(model.total_track_count).toBe(16);
    expect(model.active_track_count).toBe(0);
    expect(model.planned_track_count).toBe(16);
    expect(model.devices[0]).toMatchObject({
      mapped_track_count: 12,
      active_track_count: 0,
      planned_track_count: 12,
      // No session + no connection slice → phase defaults to 'disconnected'.
      port_state: 'No hardware detected — device scan idle',
      status: 'not-loaded',
    });
    expect(model.tracks[0]).toMatchObject({
      device_id: 'analog_rytm_mk2',
      track_number: 1,
      enabled: false,
      state: 'planned_v134',
      source: 'rytm-12-pad-surface-planned',
    });
    expect(model.snapshot_compatibility).toMatchObject({
      compatibility_id: 'no-snapshot',
      compatibility_status: 'not-loaded',
      status_badge: 'No snapshot',
      summary: 'No snapshot loaded.',
      view_details_enabled: false,
    });
  });

  it('shows an explicit no-hardware banner on both cards when disconnected (no port open)', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(
      <DeviceRail
        activeDeviceId={RYTM_DEVICE_ID}
        onSelectDevice={() => undefined}
        onCaptureDevice={() => undefined}
      />,
    );

    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent('Awaiting stage');
    expect(screen.getByTestId('device-card-analog-four-mk2')).toHaveTextContent('Awaiting stage');
    expect(
      screen.getByTestId('device-card-analog-rytm-mk2-hardware-banner'),
    ).toHaveTextContent('No hardware detected — device scan idle');
    expect(
      screen.getByTestId('device-card-analog-four-mk2-hardware-banner'),
    ).toHaveTextContent('No hardware detected — device scan idle');
    // The mock preview content stays, but is labelled as preview data.
    expect(screen.getAllByText('Preview — mock data')).toHaveLength(2);
    // No real port line while nothing is detected.
    expect(screen.queryByTestId('device-rail-rytm-port-state')).not.toBeInTheDocument();
    expect(screen.queryByTestId('device-rail-a4-port-state')).not.toBeInTheDocument();
  });

  it('says "still scanning" on every card while the sidecar searches for hardware', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setConnection(connectionSearching);
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(
      screen.getByTestId('device-card-analog-rytm-mk2-hardware-banner'),
    ).toHaveTextContent('No hardware detected — still scanning (every 2 s)');
    expect(
      screen.getByTestId('device-card-analog-four-mk2-hardware-banner'),
    ).toHaveTextContent('No hardware detected — still scanning (every 2 s)');
  });

  it('names the real port and drops the banner when the connection is listening', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setConnection(connectionListening);
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(screen.queryByTestId('device-card-analog-rytm-mk2-hardware-banner')).not.toBeInTheDocument();
    expect(screen.queryByTestId('device-card-analog-four-mk2-hardware-banner')).not.toBeInTheDocument();
    expect(screen.getByTestId('device-rail-rytm-port-state')).toHaveTextContent(
      'Port: Analog Rytm MK2 OUT',
    );
    expect(screen.getByTestId('device-rail-a4-port-state')).toHaveTextContent('No MIDI port open');
  });

  it('surfaces a fault banner pointing at the Connection Doctor', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setConnection(connectionFault);
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(
      screen.getByTestId('device-card-analog-rytm-mk2-hardware-banner'),
    ).toHaveTextContent('Connection fault — open the Connection Doctor for details');
  });

  it('resolves the phase from connection first, then session, then disconnected', () => {
    expect(resolveConnectionPhase(connectionListening, sessionMock)).toBe('listening');
    expect(resolveConnectionPhase(null, sessionLive)).toBe('armed');
    expect(resolveConnectionPhase(null, null)).toBe('disconnected');
  });

  it('maps every no-hardware phase to a notice and every live phase to null', () => {
    expect(HARDWARE_NOTICE_BY_PHASE.listening).toBeNull();
    expect(HARDWARE_NOTICE_BY_PHASE.armed).toBeNull();
    expect(HARDWARE_NOTICE_BY_PHASE.disconnected).toContain('No hardware detected');
    expect(HARDWARE_NOTICE_BY_PHASE.searching).toContain('still scanning');
    expect(HARDWARE_NOTICE_BY_PHASE.fault).toContain('Connection Doctor');
  });

  it('builds port facts from the live connection slice when listening', () => {
    const model = buildDeviceRailReadinessModel({
      session: sessionMock,
      snapshot: null,
      connection: connectionListening,
    });

    expect(model.devices[0]).toMatchObject({ port_state: 'Analog Rytm MK2 OUT' });
    expect(model.hardware_rail.selected_port_name).toBe('Analog Rytm MK2 OUT');
    expect(model.hardware_rail.available_ports).toEqual(['Analog Rytm MK2 OUT']);
  });

  it('joins enumerated output names when nothing is selected yet', () => {
    const model = buildDeviceRailReadinessModel({
      session: null,
      snapshot: null,
      connection: {
        ...connectionListening,
        selected_output: null,
        available_outputs: ['Rytm OUT', 'IAC Bus 1'],
      },
    });

    expect(model.devices[0]).toMatchObject({ port_state: 'Rytm OUT, IAC Bus 1' });
    expect(model.hardware_rail.selected_port_name).toBeNull();
    expect(model.hardware_rail.available_ports).toEqual(['Rytm OUT', 'IAC Bus 1']);
  });

  it('admits when listening hardware reports no output name at all', () => {
    const model = buildDeviceRailReadinessModel({
      session: null,
      snapshot: null,
      connection: { ...connectionListening, selected_output: null, available_outputs: [] },
    });

    expect(model.devices[0]).toMatchObject({
      port_state: 'Hardware detected — no port name reported',
    });
  });

  it('falls back to the session midi_port when armed without a connection slice', () => {
    const model = buildDeviceRailReadinessModel({
      session: sessionLive,
      snapshot,
      connection: null,
    });

    expect(model.devices[0]).toMatchObject({ port_state: 'IAC Driver Bus 1' });
    expect(model.hardware_rail.selected_port_name).toBe('IAC Driver Bus 1');
    expect(model.hardware_rail.available_ports).toEqual([]);
  });

  it('renders planned Rytm pads as locked before a snapshot is loaded', () => {
    render(
      <DeviceRail
        activeDeviceId={RYTM_DEVICE_ID}
        onSelectDevice={() => undefined}
        onCaptureDevice={() => undefined}
      />,
    );

    const rytm = screen.getByTestId('device-card-analog-rytm-mk2');
    expect(within(rytm).getAllByTestId(/device-rail-rytm-pad-/)).toHaveLength(12);
    expect(within(rytm).getByTestId('device-rail-rytm-pad-1')).toHaveClass('locked');
    expect(within(rytm).getByTestId('device-rail-rytm-pad-12')).toHaveTextContent('Pad 12');
  });

  it('offers the same prepare-to-receive control on Rytm and A4', () => {
    const requested: string[] = [];

    render(
      <DeviceRail
        activeDeviceId={RYTM_DEVICE_ID}
        onSelectDevice={() => undefined}
        onCaptureDevice={(deviceId) => requested.push(deviceId)}
      />,
    );

    screen.getByTestId('capture-kit-analog-rytm-mk2').click();
    screen.getByTestId('capture-kit-analog-four-mk2').click();

    expect(requested).toEqual([RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID]);
    expect(screen.getAllByText('Capture Current Kit')).toHaveLength(2);
  });

  it('renders the authoritative per-machine lifecycle and the explicit OXI boundary', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage(readyDualMachineStage);
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    const rytmStage = screen.getByTestId('device-card-analog-rytm-mk2-stage');
    expect(rytmStage).toHaveTextContent('Connectionconnected');
    expect(rytmStage).toHaveTextContent('Capturecaptured');
    expect(rytmStage).toHaveTextContent('TargetsDefault all');
    expect(rytmStage).toHaveTextContent('Locks2');
    expect(rytmStage).toHaveTextContent('Candidateready');
    expect(rytmStage).toHaveTextContent('Planready');
    expect(rytmStage).toHaveTextContent('Authoritynot armed');
    expect(rytmStage).toHaveTextContent('Recovery confirm exact plan');

    const a4Stage = screen.getByTestId('device-card-analog-four-mk2-stage');
    expect(a4Stage).toHaveTextContent('Planblocked');
    expect(a4Stage).toHaveTextContent('Blocked a4 semantic mapping unpromoted');
    expect(a4Stage).toHaveTextContent('Recovery capture current kit');

    const oxi = screen.getByTestId('oxi-ownership-boundary');
    expect(oxi).toHaveTextContent(
      'OXI owns sequencing, notes, triggers, mutes, and pattern motion.',
    );
    expect(oxi).toHaveTextContent('No direct OXI control');
    expect(oxi).toHaveTextContent('sends no OXI notes, triggers, mutes, or pattern commands');
  });

  it('isolates an A4 disconnect and exposes stale/recovery state without downgrading Rytm', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        revision: 9,
        analog_four: {
          ...readyDualMachineStage.analog_four,
          connection_state: 'disconnected',
          candidate_state: 'stale',
          plan_state: 'stale',
          blocked_reasons: ['device_disconnected'],
          recovery_actions: ['reconnect_device', 'capture_current_kit', 'prepare_again'],
          last_error: 'A4 cable removed',
        },
      });
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent(
      'Ready · Passive',
    );
    const a4 = screen.getByTestId('device-card-analog-four-mk2');
    expect(a4).toHaveTextContent('Disconnected');
    expect(a4).toHaveTextContent('Candidatestale');
    expect(a4).toHaveTextContent('Planstale');
    expect(a4).toHaveTextContent('reconnect device');
    expect(a4).toHaveTextContent('Last error: A4 cable removed');
  });

  it('shows an optimistic A4 target/lock change as stale until a fresh genome arrives', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        analog_four: {
          ...readyDualMachineStage.analog_four,
          candidate_state: 'ready',
          recovery_actions: [
            ...readyDualMachineStage.analog_four.recovery_actions,
            'analyze_patch_again',
          ],
        },
      });
      useCockpitStore.getState().setPatchGenome(patchGenome);
      useCockpitStore.getState().setA4TrackLocks([3]);
    });

    render(<DeviceRail activeDeviceId={ANALOG_FOUR_DEVICE_ID} onSelectDevice={() => undefined} />);

    const a4 = screen.getByTestId('device-card-analog-four-mk2');
    expect(a4).toHaveTextContent('Stale');
    expect(a4).toHaveTextContent('Candidatestale');
    expect(a4).toHaveTextContent('analyze patch again');
  });

  it('adds the A4 re-analysis recovery action when the backend stage omits it', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        analog_four: {
          ...readyDualMachineStage.analog_four,
          candidate_state: 'ready',
          recovery_actions: [],
        },
      });
      useCockpitStore.getState().setPatchGenome(patchGenome);
      useCockpitStore.getState().setA4TrackLocks([3]);
    });

    render(<DeviceRail activeDeviceId={ANALOG_FOUR_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(screen.getByTestId('device-card-analog-four-mk2')).toHaveTextContent(
      'analyze patch again',
    );
  });

  it('surfaces exceptional OXI authority flags and armed Rytm readiness', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        oxi_owns_sequencing: false,
        direct_oxi_control: true,
        rytm: { ...readyDualMachineStage.rytm, authority_state: 'armed' },
      });
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent(
      'Ready · Armed',
    );
    const oxi = screen.getByTestId('oxi-ownership-boundary');
    expect(oxi).toHaveTextContent('has not confirmed OXI sequencing ownership');
    expect(oxi).toHaveTextContent('Backend reported direct OXI control');
  });

  it('distinguishes a captured lane from an idle lane before candidate generation', () => {
    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        rytm: {
          ...readyDualMachineStage.rytm,
          candidate_state: 'none',
          plan_state: 'none',
        },
      });
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);
    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent('Captured');

    act(() => {
      useCockpitStore.getState().setDualMachineStage({
        ...readyDualMachineStage,
        rytm: {
          ...readyDualMachineStage.rytm,
          capture_state: 'not_captured',
          candidate_state: 'none',
          plan_state: 'none',
        },
      });
    });
    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent('Stage idle');
  });
});
