/**
 * Tests for PadCard — renders one pad's machine + knobs, ghost overlay when previewOn,
 * and the LockButton toggling via the usePadLocks hook.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { PadCard } from '../../src/cockpit/PadCard';
import { useCockpitStore } from '../../src/state';

import { FakeCockpitClient, candidate, snapshot } from './_fixtures';

function renderWith(node: JSX.Element, fake = new FakeCockpitClient()): FakeCockpitClient {
  render(<CockpitClientProvider client={fake.asClient()}>{node}</CockpitClientProvider>);
  return fake;
}

describe('PadCard', () => {
  beforeEach(() => useCockpitStore.getState().reset());
  afterEach(() => useCockpitStore.getState().reset());

  it('renders the pad title, machine name, and grouped Overbridge-style parameters', () => {
    const pad = snapshot.pads[0]!;
    renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={false} />);
    expect(screen.getByText('Pad 1')).toBeInTheDocument();
    expect(screen.getByText('BD Hard')).toBeInTheDocument();
    const card = screen.getByTestId('pad-card-1');
    expect(within(card).getByTestId('knob-TUN')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-DEC')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-LEV')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-FLT')).toBeInTheDocument();
    expect(within(card).getByText('Synth')).toBeInTheDocument();
    expect(within(card).getByText('Sweep Time')).toBeInTheDocument();
    expect(within(card).getByText('Snap Amount')).toBeInTheDocument();
    expect(within(card).getByText('Hold Time')).toBeInTheDocument();
    expect(within(card).getByText('Sample')).toBeInTheDocument();
    expect(within(card).getByText('Sample Tune')).toBeInTheDocument();
    expect(within(card).getByText('Filter Envelope')).toBeInTheDocument();
    expect(within(card).getByText('Filter Frequency')).toBeInTheDocument();
    expect(within(card).getByText('Amp Envelope')).toBeInTheDocument();
    expect(within(card).getByText('Overdrive')).toBeInTheDocument();
    expect(within(card).getByText('LFO')).toBeInTheDocument();
    expect(within(card).getByText('LFO Speed')).toBeInTheDocument();
  });

  it('marks absent grouped params as not mapped without hiding the section', () => {
    const pad = snapshot.pads[3]!; // CY Crash, empty params
    renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={false} />);
    const card = screen.getByTestId('pad-card-4');
    expect(within(card).getByText('Synth')).toBeInTheDocument();
    expect(within(card).getAllByText('not mapped').length).toBeGreaterThan(0);
  });

  it('renders ghost knobs when previewOn=true and the candidate touches this pad', () => {
    const pad = snapshot.pads[0]!; // pad 1, has deltas in `candidate`
    renderWith(<PadCard pad={pad} previewCandidate={candidate} previewOn={true} />);
    expect(screen.getByTestId('knob-ghost-TUN')).toBeInTheDocument();
    expect(screen.getByTestId('knob-ghost-DEC')).toBeInTheDocument();
  });

  it('omits the ghost when previewOn=false even if a candidate is present', () => {
    const pad = snapshot.pads[0]!;
    renderWith(<PadCard pad={pad} previewCandidate={candidate} previewOn={false} />);
    expect(screen.queryByTestId('knob-ghost-TUN')).not.toBeInTheDocument();
  });

  it('omits the ghost when the candidate has no delta for this pad', () => {
    // pad 2 not in candidate.pad_deltas
    const pad = snapshot.pads[1]!;
    renderWith(<PadCard pad={pad} previewCandidate={candidate} previewOn={true} />);
    expect(screen.queryByTestId('knob-ghost-TUN')).not.toBeInTheDocument();
  });

  it('omits the ghost for a knob whose key the proposed_params does not include', () => {
    // pad 3 only has tun proposed; dec/lev/flt should NOT show ghosts.
    const pad = snapshot.pads[2]!;
    renderWith(<PadCard pad={pad} previewCandidate={candidate} previewOn={true} />);
    expect(screen.getByTestId('knob-ghost-TUN')).toBeInTheDocument();
    expect(screen.queryByTestId('knob-ghost-DEC')).not.toBeInTheDocument();
  });

  it('omits the ghost when previewCandidate is null', () => {
    const pad = snapshot.pads[0]!;
    renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={true} />);
    expect(screen.queryByTestId('knob-ghost-TUN')).not.toBeInTheDocument();
  });

  it('suppresses every preview ghost when the pad is authoritatively locked', () => {
    useCockpitStore.getState().setRytmPadLocks([1]);
    const pad = snapshot.pads[0]!;

    renderWith(<PadCard pad={pad} previewCandidate={candidate} previewOn={true} />);

    expect(screen.getByTestId('pad-card-1')).toHaveClass('locked');
    expect(screen.queryByTestId('knob-ghost-TUN')).not.toBeInTheDocument();
    expect(screen.queryByTestId('knob-ghost-DEC')).not.toBeInTheDocument();
  });

  it('clicking the lock button toggles the locked class and emits set_pad_lock', async () => {
    const pad = snapshot.pads[0]!;
    const fake = renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={false} />);
    const card = screen.getByTestId('pad-card-1');
    expect(card.className).toBe('pad-card');
    const btn = within(card).getByRole('button', { name: 'Lock pad 1' });
    fireEvent.click(btn);
    // After lock the class flips.
    expect(screen.getByTestId('pad-card-1').className).toBe('pad-card locked');
    expect(fake.sent).toEqual([{ type: 'set_pad_lock', pad_id: 1, locked: true }]);
  });

  it('shows targeted and inactive pad states for an explicit multi-select scope', () => {
    useCockpitStore.getState().setMutationTargets([2], []);
    renderWith(
      <PadCard pad={snapshot.pads[0]!} previewCandidate={null} previewOn={false} />,
    );

    const card = screen.getByTestId('pad-card-1');
    expect(card).toHaveClass('inactive');
    expect(card).toHaveAttribute('data-target-state', 'inactive');
  });

  it('adds a Rytm pad to the explicit mutation target include-list', () => {
    const fake = renderWith(
      <PadCard pad={snapshot.pads[0]!} previewCandidate={null} previewOn={false} />,
    );

    fireEvent.click(screen.getByRole('button', { name: 'Target pad 1' }));

    expect(fake.sent).toEqual([
      {
        type: 'set_mutation_targets',
        device_id: 'analog_rytm_mk2',
        target_ids: [1],
      },
    ]);
    expect(screen.getByTestId('pad-card-1')).toHaveClass('targeted');
    expect(screen.getByRole('button', { name: 'Remove pad 1' })).toBePressed();
  });
});
