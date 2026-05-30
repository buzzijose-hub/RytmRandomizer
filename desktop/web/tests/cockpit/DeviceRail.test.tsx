import { act, render, screen, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { DeviceRail, buildDeviceRailReadinessModel } from '../../src/cockpit/DeviceRail';
import { ANALOG_FOUR_DEVICE_ID, RYTM_DEVICE_ID } from '../../src/cockpit/devices';
import { useCockpitStore } from '../../src/state';

import { sessionMock, snapshot } from './_fixtures';

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

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

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
      port_state: 'No MIDI port open',
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
    });

    expect(model.rig_status).toBe('mock-safe');
    expect(model.total_track_count).toBe(16);
    expect(model.active_track_count).toBe(0);
    expect(model.planned_track_count).toBe(16);
    expect(model.devices[0]).toMatchObject({
      mapped_track_count: 12,
      active_track_count: 0,
      planned_track_count: 12,
      port_state: 'No MIDI port open',
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

  it('keeps both device cards mock-safe when no MIDI port is open', () => {
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(<DeviceRail activeDeviceId={RYTM_DEVICE_ID} onSelectDevice={() => undefined} />);

    expect(screen.getByTestId('device-card-analog-rytm-mk2')).toHaveTextContent('Mock Safe');
    expect(screen.getByTestId('device-card-analog-four-mk2')).toHaveTextContent('Mock Staged');
    expect(screen.getByTestId('device-rail')).toHaveTextContent('No MIDI port open');
  });

  it('renders planned Rytm pads as locked before a snapshot is loaded', () => {
    render(<DeviceRail />);

    const rytm = screen.getByTestId('device-card-analog-rytm-mk2');
    expect(within(rytm).getAllByTestId(/device-rail-rytm-pad-/)).toHaveLength(12);
    expect(within(rytm).getByTestId('device-rail-rytm-pad-1')).toHaveClass('locked');
    expect(within(rytm).getByTestId('device-rail-rytm-pad-12')).toHaveTextContent('Pad 12');
  });
});
