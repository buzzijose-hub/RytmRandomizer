/**
 * Tests for SnapshotPanel — waits-for-snapshot placeholder, renders pads, ghost overlay,
 * and includes the HistoryStrip.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { render, screen, within } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { SnapshotPanel } from '../../src/cockpit/SnapshotPanel';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, candidate, history, snapshot } from './_fixtures';

function renderWith(previewOn = false): FakeCockpitClient {
  const fake = new FakeCockpitClient();
  render(
    <CockpitClientProvider client={fake.asClient()}>
      <SnapshotPanel previewOn={previewOn} />
    </CockpitClientProvider>,
  );
  return fake;
}

describe('SnapshotPanel', () => {
  beforeEach(() => {
    useCockpitStore.getState().reset();
  });
  afterEach(() => {
    useCockpitStore.getState().reset();
  });

  it('renders the placeholder when snapshot is null', () => {
    renderWith();
    expect(screen.getByText('Waiting for snapshot…')).toBeInTheDocument();
  });

  it('renders one PadCard per pad in the snapshot', () => {
    useCockpitStore.getState().setSnapshot(snapshot);
    useCockpitStore.getState().setHistory(history);
    renderWith();
    for (const pad of snapshot.pads) {
      expect(screen.getByTestId(`pad-card-${pad.pad_id}`)).toBeInTheDocument();
    }
  });

  it('shows "PREVIEW ON" in the panel meta when previewOn=true', () => {
    useCockpitStore.getState().setSnapshot(snapshot);
    useCockpitStore.getState().setHistory(history);
    renderWith(true);
    expect(screen.getByText(/PREVIEW ON/)).toBeInTheDocument();
  });

  it('does not show "PREVIEW ON" when previewOn=false', () => {
    useCockpitStore.getState().setSnapshot(snapshot);
    useCockpitStore.getState().setHistory(history);
    renderWith(false);
    expect(screen.queryByText(/PREVIEW ON/)).not.toBeInTheDocument();
  });

  it('renders bpm + scene_slot in the meta when present', () => {
    useCockpitStore.getState().setSnapshot(snapshot);
    renderWith();
    expect(screen.getByText(/132 BPM/)).toBeInTheDocument();
    expect(screen.getByText(/scene A01/)).toBeInTheDocument();
  });

  it('omits the bpm + scene_slot bits when both are null', () => {
    useCockpitStore.getState().setSnapshot({ ...snapshot, bpm: null, scene_slot: null });
    renderWith();
    expect(screen.queryByText(/BPM/)).not.toBeInTheDocument();
    expect(screen.queryByText(/scene/)).not.toBeInTheDocument();
  });

  it('propagates the candidate to PadCards as ghost overlays when previewOn=true', () => {
    useCockpitStore.getState().setSnapshot(snapshot);
    useCockpitStore.getState().setPreviewCandidate(candidate);
    renderWith(true);
    // pad 1 + pad 3 both have a `tun` proposed in the candidate fixture; scope to pad 1.
    const pad1 = screen.getByTestId('pad-card-1');
    expect(within(pad1).getByTestId('knob-ghost-TUN')).toBeInTheDocument();
  });
});
