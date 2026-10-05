/**
 * Tests for PadCard — renders one pad's machine + knobs, ghost overlay when previewOn,
 * and the LockButton toggling via the usePadLocks hook.
 */

import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import { CockpitClientProvider } from '../../src/cockpit/context';
import { PadCard } from '../../src/cockpit/PadCard';
import { useCockpitStore } from '../../src/state';
import type { PadState, SrcParameter } from '../../src/ws/protocol';
import { parameterGroupsForPad, RYTM_PARAMETER_GROUPS } from '../../src/cockpit/parameterGroups';

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

  it('preserves legacy groups for an empty canonical metadata list', () => {
    const pad = { ...snapshot.pads[0]!, src_parameters: [] };
    expect(parameterGroupsForPad(pad)).toBe(RYTM_PARAMETER_GROUPS);
  });
});

const srcDecay: SrcParameter = {
  key: 'src_dual_vco_2',
  parameter: 'Osc 1 Decay',
  machine_key: 'dual_vco',
  channel: 0,
  cc_msb: 18,
  cc_lsb: null,
  nrpn_msb: 1,
  nrpn_lsb: 2,
  mutation_status: 'documented_only',
  pad_compatible: true,
  live_blockers: [],
};

function srcPad(row: SrcParameter = srcDecay, params = { [row.key]: 72 }): PadState {
  return { pad_id: 1, machine: 'SY Dual VCO', params, src_parameters: [row] };
}

function srcCandidate(key = srcDecay.key) {
  return {
    ...candidate,
    pad_deltas: [{ pad_id: 1, proposed_params: { [key]: 91 }, changed_keys: [key] }],
  };
}

describe('PadCard canonical SRC', () => {
  beforeEach(() => useCockpitStore.getState().reset());
  afterEach(() => useCockpitStore.getState().reset());

  it('renders canonical names and exact wire facts with numeric CC7 values', () => {
    const fake = renderWith(<PadCard pad={srcPad()} previewCandidate={null} previewOn={false} />);
    expect(screen.getByText('Osc 1 Decay')).toBeInTheDocument();
    expect(screen.getByText('CC7 / Ch 1 / CC 18')).toBeInTheDocument();
    expect(screen.getByText('NRPN 1:2')).toBeInTheDocument();
    expect(screen.getByText('Catalog: documented only')).toBeInTheDocument();
    expect(within(screen.getByTestId('knob-CC18')).getByText('72')).toBeInTheDocument();
    expect(screen.queryByText('Sweep Time')).not.toBeInTheDocument();
    expect(screen.getByText('Sample')).toBeInTheDocument();
    expect(screen.getByText('Filter Frequency')).toBeInTheDocument();
    expect(screen.queryByText(/Blocked:/)).not.toBeInTheDocument();
    expect(fake.sent).toEqual([]);
  });

  it('keeps absent pending SRC controls visible with exact backend refusal codes', () => {
    const pending = { ...srcDecay, parameter: 'Osc 2 Detune', live_blockers: ['src_requires_guarded_detune_window'] };
    renderWith(<PadCard pad={srcPad(pending, {})} previewCandidate={srcCandidate()} previewOn={true} />);
    expect(screen.getByText('Osc 2 Detune')).toBeInTheDocument();
    expect(screen.getByText('value unavailable')).toBeInTheDocument();
    expect(screen.getByText('Blocked: value unavailable')).toBeInTheDocument();
    expect(screen.getByText('Blocked: src_requires_guarded_detune_window')).toBeInTheDocument();
    expect(screen.queryByTestId('knob-CC18')).not.toBeInTheDocument();
  });

  it('renders policy-blocked values but never draws their proposed ghost', () => {
    const blocked = { ...srcDecay, live_blockers: ['src_cy_ride_slot_unverified'] };
    renderWith(<PadCard pad={srcPad(blocked)} previewCandidate={srcCandidate()} previewOn={true} />);
    expect(screen.getByTestId('knob-CC18')).toBeInTheDocument();
    expect(screen.getByText('Blocked: src_cy_ride_slot_unverified')).toBeInTheDocument();
    expect(screen.queryByTestId('knob-ghost-CC18')).not.toBeInTheDocument();
  });

  it('shows multiple blockers, incompatible pads and paired addresses without implying precision support', () => {
    const row = {
      ...srcDecay,
      channel: 11,
      cc_lsb: 50,
      pad_compatible: false,
      live_blockers: ['src_pitch_protected', 'src_selector_protected'],
    };
    renderWith(<PadCard pad={srcPad(row)} previewCandidate={srcCandidate()} previewOn={true} />);
    expect(screen.getByText('CC7 / Ch 12 / CC 18 + 50')).toBeInTheDocument();
    expect(screen.getByText('Blocked: incompatible pad')).toBeInTheDocument();
    expect(screen.getByText('Blocked: src_pitch_protected')).toBeInTheDocument();
    expect(screen.getByText('Blocked: src_selector_protected')).toBeInTheDocument();
    expect(screen.getByText('Blocked: paired_control_precision_unverified')).toBeInTheDocument();
    expect(screen.queryByTestId('knob-ghost-CC18')).not.toBeInTheDocument();
  });

  it.each([
    { pad_compatible: false, cc_lsb: null },
    { pad_compatible: true, cc_lsb: 50 },
  ])('suppresses a preview independently for incompatibility or pairing: %s', (facts) => {
    renderWith(
      <PadCard pad={srcPad({ ...srcDecay, ...facts })} previewCandidate={srcCandidate()} previewOn={true} />,
    );
    expect(screen.queryByTestId('knob-ghost-CC18')).not.toBeInTheDocument();
    expect(screen.getByTestId('knob-CC18')).toBeInTheDocument();
  });

  it.each([
    { nrpn_msb: null, nrpn_lsb: 2 },
    { nrpn_msb: 1, nrpn_lsb: null },
  ])('does not invent an incomplete NRPN address: %s', (address) => {
    renderWith(<PadCard pad={srcPad({ ...srcDecay, ...address })} previewCandidate={null} previewOn={false} />);
    expect(screen.getByText('NRPN unavailable')).toBeInTheDocument();
  });

  it('preserves numeric preview ghosts, target toggles and authoritative locks', () => {
    const fake = renderWith(<PadCard pad={srcPad()} previewCandidate={srcCandidate()} previewOn={true} />);
    expect(screen.getByTestId('knob-ghost-CC18')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Target pad 1' }));
    expect(screen.getByTestId('pad-card-1')).toHaveClass('targeted');
    expect(screen.getByTestId('knob-ghost-CC18')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Lock pad 1' }));
    expect(screen.getByTestId('pad-card-1')).toHaveClass('locked');
    expect(screen.queryByTestId('knob-ghost-CC18')).not.toBeInTheDocument();
    expect(fake.sent).toEqual([
      { type: 'set_mutation_targets', device_id: 'analog_rytm_mk2', target_ids: [1] },
      { type: 'set_pad_lock', pad_id: 1, locked: true },
    ]);
  });
});
