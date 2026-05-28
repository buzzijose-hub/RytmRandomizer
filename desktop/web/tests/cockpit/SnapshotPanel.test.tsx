/**
 * Tests for SnapshotPanel — waits-for-snapshot placeholder, renders pads, ghost overlay,
 * and includes the HistoryStrip.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { act, render, screen, within } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import {
  ANALOG_FOUR_DEVICE_ID,
  type CockpitDeviceId,
  RYTM_DEVICE_ID,
} from '../../src/cockpit/devices';
import { SnapshotPanel } from '../../src/cockpit/SnapshotPanel';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, candidate, history, snapshot } from './_fixtures';

function renderWith(
  previewOn = false,
  activeDeviceId: CockpitDeviceId = RYTM_DEVICE_ID,
): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <SnapshotPanel activeDeviceId={activeDeviceId} previewOn={previewOn} />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('SnapshotPanel', () => {
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

  it('renders the placeholder when snapshot is null', () => {
    renderWith();
    expect(screen.getByText('Waiting for snapshot…')).toBeInTheDocument();
  });

  it('renders one PadCard per pad in the snapshot', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setHistory(history);
    });
    renderWith();
    for (const pad of snapshot.pads) {
      expect(screen.getByTestId(`pad-card-${pad.pad_id}`)).toBeInTheDocument();
    }
    expect(screen.getByTestId('pad-card-12')).toHaveTextContent('BD Acoustic');
    expect(screen.getByText('12 pads ready for dry-run review')).toBeInTheDocument();
  });

  it('shows "PREVIEW ON" in the panel meta when previewOn=true', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setHistory(history);
    });
    renderWith(true);
    expect(screen.getByText(/PREVIEW ON/)).toBeInTheDocument();
  });

  it('does not show "PREVIEW ON" when previewOn=false', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setHistory(history);
    });
    renderWith(false);
    expect(screen.queryByText(/PREVIEW ON/)).not.toBeInTheDocument();
  });

  it('renders bpm + scene_slot in the meta when present', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
    });
    renderWith();
    expect(screen.getByText(/132 BPM/)).toBeInTheDocument();
    expect(screen.getByText(/scene A01/)).toBeInTheDocument();
  });

  it('omits the bpm + scene_slot bits when both are null', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot({ ...snapshot, bpm: null, scene_slot: null });
    });
    renderWith();
    expect(screen.queryByText(/BPM/)).not.toBeInTheDocument();
    expect(screen.queryByText(/scene/)).not.toBeInTheDocument();
  });

  it('propagates the candidate to PadCards as ghost overlays when previewOn=true', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setPreviewCandidate(candidate);
    });
    renderWith(true);
    // pad 1 + pad 3 both have a `tun` proposed in the candidate fixture; scope to pad 1.
    const pad1 = screen.getByTestId('pad-card-1');
    expect(within(pad1).getByTestId('knob-ghost-TUN')).toBeInTheDocument();
  });

  it('renders the Analog Four four-track cockpit view when selected', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot(snapshot);
      useCockpitStore.getState().setHistory(history);
    });

    renderWith(true, ANALOG_FOUR_DEVICE_ID);

    expect(screen.getByTestId('snapshot-panel')).toHaveAttribute(
      'data-active-device',
      ANALOG_FOUR_DEVICE_ID,
    );
    expect(screen.getByText('Analog Four MKII')).toBeInTheDocument();
    expect(screen.getByText('4 tracks ready for dry-run review')).toBeInTheDocument();
    expect(screen.getByText(/PREVIEW ON/)).toBeInTheDocument();
    expect(screen.getAllByTestId(/a4-track-card-/)).toHaveLength(4);

    const track1 = screen.getByTestId('a4-track-card-1');
    expect(track1).toHaveTextContent('Bass / low pulse');
    expect(within(track1).getByTestId('a4-track-1-zone-oscillator')).toHaveTextContent(
      'Oscillators',
    );
    expect(within(track1).getByTestId('a4-track-1-zone-filter')).toHaveTextContent(
      'Filter 1 Frequency',
    );
    expect(within(track1).getByTestId('a4-track-1-zone-drive')).toHaveTextContent(
      'NRPN-only / deferred',
    );
  });

  it('renders the Analog Four track view without bpm or preview labels when both are absent', () => {
    act(() => {
      useCockpitStore.getState().setSnapshot({ ...snapshot, bpm: null });
    });

    renderWith(false, ANALOG_FOUR_DEVICE_ID);

    expect(screen.getByText('Analog Four MKII')).toBeInTheDocument();
    expect(screen.queryByText(/BPM/)).not.toBeInTheDocument();
    expect(screen.queryByText(/PREVIEW ON/)).not.toBeInTheDocument();
    expect(screen.getAllByTestId(/a4-track-card-/)).toHaveLength(4);
  });
});
