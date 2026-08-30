/**
 * Tests for the top-level Cockpit container — provider wiring, default profile list,
 * panel composition, lift-state interaction between SnapshotPanel and ActionBar.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, fireEvent, render, screen, within } from '@testing-library/react';

import { Cockpit } from '../../src/cockpit/Cockpit';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, availableProfiles, sessionLive, sessionMock, snapshot } from './_fixtures';

describe('Cockpit', () => {
  beforeEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
      useCockpitStore.getState().setProfileCatalog([...availableProfiles]);
    });
  });
  afterEach(() => {
    act(() => {
      useCockpitStore.getState().reset();
    });
  });

  it('mounts the FULL cockpit tree with a pristine store (no sidecar, nothing hydrated)', () => {
    // The App no longer gates on sessionStatus: every panel must render a
    // graceful empty/degraded state from all-null slices without throwing.
    const fake = new FakeCockpitClient();
    render(<Cockpit client={fake.asClient()} />);

    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.getByTestId('header-bar')).toHaveTextContent('disconnected');
    expect(screen.getByTestId('snapshot-panel')).toHaveTextContent('Waiting for snapshot…');
    expect(screen.getByTestId('device-rail')).toBeInTheDocument();
    expect(screen.getByTestId('mutation-panel')).toBeInTheDocument();
    // Device-specific center panels are mutually exclusive; A4 is exercised
    // after selecting its card below.
    expect(screen.queryByTestId('patch-genome-panel')).not.toBeInTheDocument();
    expect(screen.getByTestId('live-readiness-panel')).toBeInTheDocument();
    expect(screen.getByTestId('safety-rail')).toBeInTheDocument();
    // Bottom-rail registry panels mount and degrade (empty states, no crash).
    expect(screen.getByTestId('live-midi-monitor')).toBeInTheDocument();
    expect(screen.getByTestId('connection-doctor')).toBeInTheDocument();
    expect(screen.getByTestId('library-panel')).toBeInTheDocument();
    expect(screen.getByTestId('library-load')).toBeEnabled();
    expect(screen.getByTestId('kit-morph')).toBeInTheDocument();

    // Sidecar-requiring affordances are present but disabled, with a reason.
    expect(screen.getByTestId('arm-open-button')).toBeDisabled();
    expect(screen.getByTestId('arm-open-button')).toHaveAttribute(
      'title',
      'Requires sidecar connection',
    );
    expect(screen.getByTestId('action-regen')).toBeDisabled();
    expect(screen.getByTestId('action-save')).toBeDisabled();
    expect(screen.getByTestId('action-send')).toBeDisabled();
  });

  it('renders the root + HeaderBar + both panels', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSnapshot(snapshot);
    });
    render(<Cockpit client={fake.asClient()} />);
    expect(screen.getByTestId('cockpit-root')).toBeInTheDocument();
    expect(screen.getByTestId('header-bar')).toBeInTheDocument();
    expect(screen.getByTestId('snapshot-panel')).toBeInTheDocument();
    expect(screen.getByTestId('live-readiness-panel')).toBeInTheDocument();
    expect(screen.queryByTestId('patch-genome-panel')).not.toBeInTheDocument();
    expect(screen.getByTestId('mutation-panel')).toBeInTheDocument();
  });

  it('renders mock-safe device and safety rails for the dry-run cockpit', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });
    render(<Cockpit client={fake.asClient()} />);

    const deviceRail = screen.getByTestId('device-rail');
    expect(within(deviceRail).getByText('Analog Rytm MKII')).toBeInTheDocument();
    expect(within(deviceRail).getByText('Analog Four MKII')).toBeInTheDocument();
    expect(screen.getAllByText('Mock Safe').length).toBeGreaterThan(0);
    expect(screen.getAllByText('No MIDI Port Open').length).toBeGreaterThan(0);
    expect(within(screen.getByTestId('safety-rail')).getByText('Simulation / Mock')).toBeInTheDocument();
  });

  it('renders the registry-backed profile catalogue from the store', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSnapshot(snapshot);
    });
    render(<Cockpit client={fake.asClient()} />);
    // The bootstrap catalogue contains "Industrial" + "Warehouse" scene profiles.
    expect(screen.getByTestId('profile-chip-scene-industrial')).toBeInTheDocument();
    expect(screen.getByTestId('profile-chip-scene-warehouse')).toBeInTheDocument();
  });

  it('previewOn state lifted to <Cockpit /> propagates between ActionBar and SnapshotPanel', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionLive);
      useCockpitStore.getState().setSnapshot(snapshot);
    });
    render(<Cockpit client={fake.asClient()} />);
    // Initially preview is off.
    expect(screen.queryByText(/PREVIEW ON/)).not.toBeInTheDocument();
    fireEvent.click(screen.getByTestId('action-preview'));
    // After the toggle the SnapshotPanel meta shows "PREVIEW ON".
    expect(screen.getByText(/PREVIEW ON/)).toBeInTheDocument();
    // And the ActionBar reflects the new state.
    expect(screen.getByTestId('action-preview')).toHaveTextContent('PREVIEW (on)');
  });

  it('switches the cockpit center view from Rytm pads to Analog Four tracks', () => {
    const fake = new FakeCockpitClient();
    act(() => {
      useCockpitStore.getState().setSessionStatus(sessionMock);
      useCockpitStore.getState().setSnapshot(snapshot);
    });

    render(<Cockpit client={fake.asClient()} />);

    expect(screen.getByTestId('pad-card-1')).toHaveTextContent('BD Hard');
    fireEvent.click(screen.getByTestId('device-select-analog-four-mk2'));

    expect(screen.queryByTestId('pad-card-1')).not.toBeInTheDocument();
    expect(screen.getByTestId('a4-track-card-1')).toBeVisible();
    expect(screen.getByTestId('a4-track-card-4')).toBeVisible();
    expect(screen.getByTestId('patch-genome-panel')).toHaveTextContent('A4 Patch Genome');
    expect(screen.getByTestId('mutation-panel')).toBeInTheDocument();
    expect(screen.getByTestId('safety-rail')).toHaveTextContent('Mock Safe');
  });

  it('opens the shared prepare-to-receive workflow from either machine card', async () => {
    const fake = new FakeCockpitClient();
    fake.ackQueue.push(
      {
        request_id: 'rytm-inputs',
        ok: true,
        capture_enabled: false,
        capture_device_id: 'analog_rytm_mk2',
        capture_inputs: [],
      },
      {
        request_id: 'a4-inputs',
        ok: true,
        capture_enabled: false,
        capture_device_id: 'analog_four_mk2',
        capture_inputs: [],
      },
    );
    act(() => useCockpitStore.getState().setSessionStatus(sessionMock));

    render(<Cockpit client={fake.asClient()} />);

    fireEvent.click(screen.getByTestId('capture-kit-analog-rytm-mk2'));
    expect(await screen.findByText('Prepare Analog Rytm MKII to receive')).toBeInTheDocument();
    fireEvent.click(screen.getByLabelText('Close kit capture'));
    expect(screen.getByTestId('snapshot-panel')).toBeInTheDocument();
    fireEvent.click(screen.getByTestId('capture-kit-analog-four-mk2'));
    expect(await screen.findByText('Prepare Analog Four MKII to receive')).toBeInTheDocument();
  });
});
