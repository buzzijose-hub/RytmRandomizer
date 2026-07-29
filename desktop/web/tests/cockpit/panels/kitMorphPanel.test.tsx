/**
 * Kit morph — pure engine/selector branches + the interactive group mask and
 * morph-amount slider.
 */

import { describe, expect, it } from 'vitest';
import { fireEvent, render, screen, within } from '@testing-library/react';

import {
  KitMorphPanel,
  availableMorphGroups,
} from '../../../src/cockpit/panels/KitMorphPanel';
import {
  clampAmount,
  interpolateValue,
  kitMorphPanelSpec,
  planMorph,
  planMorphTrack,
  type MorphTrackData,
} from '../../../src/cockpit/panels/kitMorphPanelSpec';

const TRACK: MorphTrackData = {
  track: 1,
  sourceName: 'S',
  targetName: 'T',
  source: { A: 10, B: 20, 'SRC Waveform': 0 },
  target: { A: 30, C: 40, 'SRC Waveform': 3 },
  groups: [
    ['g1', ['A', 'B', 'SRC Waveform', 'C', 'GHOST']],
    ['g2', ['A']],
  ],
};

describe('morph engine (pure)', () => {
  it('clampAmount bounds the macro', () => {
    expect(clampAmount(-1)).toBe(0);
    expect(clampAmount(2)).toBe(1);
    expect(clampAmount(0.5)).toBe(0.5);
  });

  it('interpolateValue blends continuous linearly (bankers rounding)', () => {
    expect(interpolateValue(10, 20, 0, false)).toBe(10);
    expect(interpolateValue(10, 20, 1, false)).toBe(20);
    expect(interpolateValue(10, 20, 0.5, false)).toBe(15);
    // 59 -> 58 at 0.5 = 58.5 -> 58 (half-even), the parity-critical case.
    expect(interpolateValue(59, 58, 0.5, false)).toBe(58);
  });

  it('interpolateValue thresholds discrete selectors at the midpoint', () => {
    expect(interpolateValue(0, 3, 0.49, true)).toBe(0);
    expect(interpolateValue(0, 3, 0.5, true)).toBe(3);
  });

  it('planMorphTrack matches, dedupes, and reports unmatched', () => {
    const plan = planMorphTrack(TRACK, new Set(['g1', 'g2']), 0.5);
    expect(plan.params.map((p) => p.name)).toEqual(['A', 'SRC Waveform']);
    expect(new Set(plan.unmatched)).toEqual(new Set(['B', 'C']));
    const a = plan.params.find((p) => p.name === 'A')!;
    expect(a.interpolated).toBe(20);
    expect(a.discrete).toBe(false);
    const wave = plan.params.find((p) => p.name === 'SRC Waveform')!;
    expect(wave.interpolated).toBe(3);
    expect(wave.discrete).toBe(true);
  });

  it('planMorphTrack ignores out-of-scope groups', () => {
    const plan = planMorphTrack(TRACK, new Set(['g2']), 0.5);
    expect(plan.params.every((p) => p.group === 'g2')).toBe(true);
  });

  it('movedCount excludes unchanged params', () => {
    const t: MorphTrackData = {
      track: 1,
      sourceName: 'S',
      targetName: 'T',
      source: { A: 10, B: 20 },
      target: { A: 10, B: 40 },
      groups: [['g', ['A', 'B']]],
    };
    const plan = planMorphTrack(t, new Set(['g']), 1);
    expect(plan.movedCount).toBe(1);
  });

  it('planMorph readiness: no groups', () => {
    const plan = planMorph([TRACK], new Set(), 0.5);
    expect(plan.readinessReason).toBe('no parameter groups selected');
  });

  it('planMorph readiness: zero amount', () => {
    const plan = planMorph([TRACK], new Set(['g1']), 0);
    expect(plan.readinessReason).toBe('amount is 0.0 (source unchanged)');
  });

  it('planMorph readiness: already matching', () => {
    const t: MorphTrackData = {
      track: 1,
      sourceName: 'S',
      targetName: 'T',
      source: { A: 10 },
      target: { A: 10 },
      groups: [['g', ['A']]],
    };
    const plan = planMorph([t], new Set(['g']), 0.5);
    expect(plan.readinessReason).toBe('source and target already match in scope');
  });

  it('planMorph ready path', () => {
    const plan = planMorph([TRACK], new Set(['g1']), 0.5);
    expect(plan.ready).toBe(true);
    expect(plan.totalMoved).toBeGreaterThan(0);
  });
});

describe('kitMorphPanelSpec (pure)', () => {
  it('renders ready badge + interpolation table with kind labels', () => {
    const plan = planMorph([TRACK], new Set(['g1']), 0.5);
    const spec = kitMorphPanelSpec(plan);
    expect(spec.panel_id).toBe('kit-morph');
    expect(spec.status_badges[1]).toMatchObject({ label: 'ready', tone: 'ok' });
    const table = spec.sections.find((s) => s.heading === 'Interpolation')!.table!;
    expect(table.columns).toEqual([
      'Pad',
      'Group',
      'Param',
      'Kind',
      'Source',
      'Target',
      'Interp',
    ]);
    const kinds = new Set(table.rows.map((r) => r[3]));
    expect(kinds.has('linear')).toBe(true);
    expect(kinds.has('discrete')).toBe(true);
  });

  it('renders a warn badge for a not-ready plan', () => {
    const spec = kitMorphPanelSpec(planMorph([TRACK], new Set(), 0.5));
    expect(spec.status_badges[1]).toMatchObject({
      label: 'no parameter groups selected',
      tone: 'warn',
    });
  });
});

describe('availableMorphGroups', () => {
  it('collects distinct groups in first-seen order', () => {
    expect(availableMorphGroups([TRACK])).toEqual(['g1', 'g2']);
  });

  it('returns an empty list for no tracks', () => {
    expect(availableMorphGroups([])).toEqual([]);
  });

  it('dedupes a group shared across tracks', () => {
    const t2: MorphTrackData = { ...TRACK, track: 2 };
    expect(availableMorphGroups([TRACK, t2])).toEqual(['g1', 'g2']);
  });
});

describe('KitMorphPanel (interactive)', () => {
  it('renders the source->target endpoints and a ready plan by default', () => {
    render(<KitMorphPanel />);
    const panel = screen.getByTestId('kit-morph');
    expect(within(panel).getByTestId('kit-morph-endpoints').textContent).toContain('→');
    expect(within(panel).getByText('ready')).toBeInTheDocument();
  });

  it('deselecting all groups flips the badge to not-ready', () => {
    render(<KitMorphPanel />);
    const panel = screen.getByTestId('kit-morph');
    fireEvent.click(within(panel).getByTestId('morph-group-src'));
    fireEvent.click(within(panel).getByTestId('morph-group-filter'));
    expect(within(panel).getByText('no parameter groups selected')).toBeInTheDocument();
  });

  it('re-selecting a group updates the mask', () => {
    render(<KitMorphPanel />);
    const panel = screen.getByTestId('kit-morph');
    const src = within(panel).getByTestId('morph-group-src');
    fireEvent.click(src);
    expect(src).toHaveAttribute('aria-pressed', 'false');
    fireEvent.click(src);
    expect(src).toHaveAttribute('aria-pressed', 'true');
  });

  it('renders empty endpoint labels when given no tracks', () => {
    render(<KitMorphPanel tracks={[]} />);
    const panel = screen.getByTestId('kit-morph');
    // Empty source/target fallbacks: the endpoints render just the arrow.
    expect(within(panel).getByTestId('kit-morph-endpoints').textContent).toBe(' → ');
    expect(within(panel).getByText('no parameter groups selected')).toBeInTheDocument();
  });

  it('the amount slider exposes value/min/max and updates the plan', () => {
    render(<KitMorphPanel />);
    const panel = screen.getByTestId('kit-morph');
    const slider = within(panel).getByTestId('kit-morph-slider');
    expect(slider).toHaveAttribute('aria-label', 'Morph amount');
    expect(slider).toHaveAttribute('min', '0');
    expect(slider).toHaveAttribute('max', '1');
    fireEvent.change(slider, { target: { value: '0' } });
    expect(within(panel).getByText('amount 0.00')).toBeInTheDocument();
    expect(within(panel).getByText('amount is 0.0 (source unchanged)')).toBeInTheDocument();
  });
});
