/**
 * Scoped randomization — pure engine/selector branches + the interactive mask
 * grid (per-track / per-group toggles) and depth slider.
 */

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import {
  ScopedRandomizationPanel,
  availableGroups,
} from '../../../src/cockpit/panels/ScopedRandomizationPanel';
import {
  clampDepth,
  planScope,
  planTrackScope,
  reach,
  roundHalfEven,
  scopedRandomizationPanelSpec,
  type ScopeTrackData,
} from '../../../src/cockpit/panels/scopedRandomizationPanelSpec';

const TRACK: ScopeTrackData = {
  track: 1,
  profileName: 'Test',
  anchor: { A: 50, B: 90, 'SRC Waveform': 1, NOBOUND: 10 },
  safe: { A: [0, 100], B: [0, 100], 'SRC Waveform': [0, 3] },
  groups: [
    ['g1', ['A', 'B', 'SRC Waveform', 'NOBOUND']],
    ['g2', ['A']],
  ],
};

describe('scope engine (pure)', () => {
  it('clampDepth bounds the macro', () => {
    expect(clampDepth(-1)).toBe(0);
    expect(clampDepth(5)).toBe(1);
    expect(clampDepth(0.5)).toBe(0.5);
  });

  it('reach prefers the wider side and ties resolve upward', () => {
    expect(reach(50, 0, 100)).toBe(50); // tie -> up
    expect(reach(90, 0, 100)).toBe(-90); // down wins
    expect(reach(10, 0, 100)).toBe(90); // up wins
  });

  it('roundHalfEven matches bankers rounding', () => {
    expect(roundHalfEven(58.5)).toBe(58);
    expect(roundHalfEven(59.5)).toBe(60);
    expect(roundHalfEven(62.5)).toBe(62);
    expect(roundHalfEven(2.4)).toBe(2);
    expect(roundHalfEven(2.6)).toBe(3);
    expect(roundHalfEven(-2.5)).toBe(-2);
  });

  it('planTrackScope skips missing bounds + discrete params and dedupes', () => {
    const plan = planTrackScope(TRACK, { tracks: new Set([1]), groups: new Set(['g1', 'g2']) }, 1);
    // NOBOUND (no safe) and SRC Waveform (discrete) skipped; A appears once.
    expect(plan.deltas.map((d) => d.name)).toEqual(['A', 'B']);
    // A: anchor 50 (0,100) tie->up full depth -> 100; B: anchor 90 down -> 0
    expect(plan.deltas.find((d) => d.name === 'A')!.planned).toBe(100);
    expect(plan.deltas.find((d) => d.name === 'B')!.planned).toBe(0);
    expect(plan.changedCount).toBe(2);
  });

  it('planTrackScope clamps an out-of-range anchor before reaching', () => {
    const t: ScopeTrackData = {
      track: 1,
      profileName: 'x',
      anchor: { P: 200 },
      safe: { P: [0, 100] },
      groups: [['g', ['P']]],
    };
    const plan = planTrackScope(t, { tracks: new Set([1]), groups: new Set(['g']) }, 1);
    expect(plan.deltas[0]!.anchor).toBe(200);
    expect(plan.deltas[0]!.planned).toBe(0); // clamp 100 -> down 100
  });

  it('planTrackScope ignores out-of-scope groups', () => {
    const plan = planTrackScope(TRACK, { tracks: new Set([1]), groups: new Set(['g2']) }, 0.5);
    expect(plan.deltas.every((d) => d.group === 'g2')).toBe(true);
  });

  it('planScope readiness: no tracks', () => {
    const plan = planScope([TRACK], { tracks: new Set(), groups: new Set(['g1']) }, 0.5);
    expect(plan.ready).toBe(false);
    expect(plan.readinessReason).toBe('no tracks selected');
  });

  it('planScope readiness: no groups', () => {
    const plan = planScope([TRACK], { tracks: new Set([1]), groups: new Set() }, 0.5);
    expect(plan.readinessReason).toBe('no parameter groups selected');
  });

  it('planScope readiness: zero depth', () => {
    const plan = planScope([TRACK], { tracks: new Set([1]), groups: new Set(['g1']) }, 0);
    expect(plan.readinessReason).toBe('depth is 0.0 (no movement)');
  });

  it('planScope readiness: no reachable continuous params', () => {
    const t: ScopeTrackData = {
      track: 1,
      profileName: 'x',
      anchor: { 'SRC Waveform': 1 },
      safe: { 'SRC Waveform': [0, 3] },
      groups: [['osc', ['SRC Waveform']]],
    };
    const plan = planScope([t], { tracks: new Set([1]), groups: new Set(['osc']) }, 0.5);
    expect(plan.readinessReason).toBe('mask selects no reachable continuous parameters');
  });

  it('planScope ready path only includes selected tracks', () => {
    const t2: ScopeTrackData = { ...TRACK, track: 2 };
    const plan = planScope([TRACK, t2], { tracks: new Set([2]), groups: new Set(['g1']) }, 0.5);
    expect(plan.trackPlans.map((p) => p.track)).toEqual([2]);
    expect(plan.ready).toBe(true);
  });
});

describe('scopedRandomizationPanelSpec (pure)', () => {
  it('renders ready badge + delta table with signed deltas', () => {
    const plan = planScope([TRACK], { tracks: new Set([1]), groups: new Set(['g1']) }, 1);
    const spec = scopedRandomizationPanelSpec(plan);
    expect(spec.panel_id).toBe('scoped-randomization');
    expect(spec.status_badges[1]).toMatchObject({ label: 'ready', tone: 'ok' });
    const table = spec.sections.find((s) => s.heading === 'Parameter deltas')!.table!;
    expect(table.columns).toEqual(['Pad', 'Group', 'Param', 'Anchor', 'Planned', 'Delta']);
    const signs = table.rows.map((r) => r[5]![0]);
    expect(signs).toContain('+');
    expect(signs).toContain('-');
  });

  it('renders a warn badge for a not-ready plan', () => {
    const plan = planScope([TRACK], { tracks: new Set(), groups: new Set() }, 0.5);
    const spec = scopedRandomizationPanelSpec(plan);
    expect(spec.status_badges[1]).toMatchObject({ label: 'no tracks selected', tone: 'warn' });
  });
});

describe('availableGroups', () => {
  it('collects distinct groups in first-seen order', () => {
    expect(availableGroups([TRACK])).toEqual(['g1', 'g2']);
  });
});

describe('ScopedRandomizationPanel (interactive)', () => {
  it('starts fully selected and renders a ready plan', () => {
    render(<ScopedRandomizationPanel />);
    const panel = screen.getByTestId('scoped-randomization');
    expect(within(panel).getByTestId('scope-track-1')).toHaveAttribute('aria-pressed', 'true');
    expect(within(panel).getByTestId('scope-group-src')).toHaveAttribute('aria-pressed', 'true');
    expect(within(panel).getByText('ready')).toBeInTheDocument();
  });

  it('deselecting all tracks flips the badge to not-ready', () => {
    render(<ScopedRandomizationPanel />);
    const panel = screen.getByTestId('scoped-randomization');
    fireEvent.click(within(panel).getByTestId('scope-track-1'));
    fireEvent.click(within(panel).getByTestId('scope-track-2'));
    expect(within(panel).getByTestId('scope-track-1')).toHaveAttribute('aria-pressed', 'false');
    expect(within(panel).getByText('no tracks selected')).toBeInTheDocument();
  });

  it('toggling a group off then on updates the mask', () => {
    render(<ScopedRandomizationPanel />);
    const panel = screen.getByTestId('scoped-randomization');
    const filterBtn = within(panel).getByTestId('scope-group-filter');
    fireEvent.click(filterBtn);
    expect(filterBtn).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(filterBtn);
    expect(filterBtn).toHaveAttribute('aria-pressed', 'true');
  });

  it('the depth slider exposes value/min/max and updates the plan', () => {
    render(<ScopedRandomizationPanel />);
    const panel = screen.getByTestId('scoped-randomization');
    const slider = within(panel).getByTestId('scope-depth-slider');
    expect(slider).toHaveAttribute('aria-label', 'Randomization depth');
    expect(slider).toHaveAttribute('min', '0');
    expect(slider).toHaveAttribute('max', '1');
    fireEvent.change(slider, { target: { value: '0' } });
    expect(within(panel).getByText('depth 0.00')).toBeInTheDocument();
    expect(within(panel).getByText('depth is 0.0 (no movement)')).toBeInTheDocument();
  });

  it('labels itself a static demonstration so canned values are not read as device state', () => {
    render(<ScopedRandomizationPanel />);
    const banner = screen.getByTestId('scope-demo-banner');
    expect(banner).toHaveAttribute('role', 'note');
    expect(banner).toHaveTextContent('Static demonstration.');
    expect(banner).toHaveTextContent('scoped randomization');
    expect(banner).toHaveTextContent('not your connected instrument');
    expect(banner).toHaveTextContent('nothing here is armed or transmitted');
  });
});
