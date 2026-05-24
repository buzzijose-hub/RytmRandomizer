/**
 * Tests for PadCard — renders one pad's machine + knobs, ghost overlay when previewOn,
 * and the LockButton toggling via the usePadLocks hook.
 */

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { PadCard } from '../../src/cockpit/PadCard';

import { FakeCockpitClient, candidate, snapshot } from './_fixtures';

function renderWith(node: JSX.Element, fake = new FakeCockpitClient()): FakeCockpitClient {
  render(<CockpitClientProvider client={fake.asClient()}>{node}</CockpitClientProvider>);
  return fake;
}

describe('PadCard', () => {
  it('renders the pad title + machine name + 4 primary knobs', () => {
    const pad = snapshot.pads[0]!;
    renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={false} />);
    expect(screen.getByText('Pad 1')).toBeInTheDocument();
    expect(screen.getByText('BD Hard')).toBeInTheDocument();
    const card = screen.getByTestId('pad-card-1');
    expect(within(card).getByTestId('knob-TUN')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-DEC')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-LEV')).toBeInTheDocument();
    expect(within(card).getByTestId('knob-FLT')).toBeInTheDocument();
  });

  it('falls back to 0 for absent params (pad with empty params)', () => {
    const pad = snapshot.pads[3]!; // CY Crash, empty params
    renderWith(<PadCard pad={pad} previewCandidate={null} previewOn={false} />);
    const card = screen.getByTestId('pad-card-4');
    // Each knob renders its current value text; 4 zeros for empty params.
    const zeros = within(card).getAllByText('0');
    expect(zeros.length).toBe(4);
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
});
