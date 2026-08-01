/**
 * Kit morphing — pure PanelSpec selector + a deterministic client-side port of
 * `rytm_randomizer/behavior/morph.py`.
 *
 * The passive interpolation table renders through the schema-driven PanelSpec
 * platform (`PanelRenderer`); the interactive morph-amount slider lives in
 * `KitMorphPanel.tsx`. Everything here is pure — no React, no fetch, no state —
 * and passive: it produces a previewable plan the operator can arm-and-send
 * through the existing ArmedApply seam, and reaches no transmit path itself.
 *
 * Continuous params blend linearly `round(source + amount*(target-source))`;
 * discrete selectors threshold at the midpoint (source below 0.5, target at or
 * above), matching the Python engine.
 */

import type { PanelSpecDict } from '../../types/live_gui_protocol';

import { DISCRETE_PARAM_NAMES, roundHalfEven } from './scopedRandomizationPanelSpec';

export const AMOUNT_MIN = 0.0;
export const AMOUNT_MAX = 1.0;
export const DISCRETE_THRESHOLD = 0.5;

export interface MorphTrackData {
  readonly track: number;
  readonly sourceName: string;
  readonly targetName: string;
  readonly source: Readonly<Record<string, number>>;
  readonly target: Readonly<Record<string, number>>;
  /** Ordered group -> ordered param names. */
  readonly groups: ReadonlyArray<readonly [string, ReadonlyArray<string>]>;
}

export interface MorphParam {
  readonly name: string;
  readonly group: string;
  readonly source: number;
  readonly target: number;
  readonly interpolated: number;
  readonly discrete: boolean;
  readonly moved: boolean;
}

export interface MorphTrackPlan {
  readonly track: number;
  readonly sourceName: string;
  readonly targetName: string;
  readonly params: ReadonlyArray<MorphParam>;
  readonly unmatched: ReadonlyArray<string>;
  readonly movedCount: number;
}

export interface MorphPlan {
  readonly amount: number;
  readonly trackPlans: ReadonlyArray<MorphTrackPlan>;
  readonly totalMoved: number;
  readonly ready: boolean;
  readonly readinessReason: string;
}

export function clampAmount(amount: number): number {
  if (amount < AMOUNT_MIN) return AMOUNT_MIN;
  if (amount > AMOUNT_MAX) return AMOUNT_MAX;
  return amount;
}

export function interpolateValue(
  source: number,
  target: number,
  amount: number,
  discrete: boolean,
): number {
  const clamped = clampAmount(amount);
  if (discrete) {
    return clamped >= DISCRETE_THRESHOLD ? target : source;
  }
  return roundHalfEven(source + clamped * (target - source));
}

export function planMorphTrack(
  data: MorphTrackData,
  groups: ReadonlySet<string>,
  amount: number,
): MorphTrackPlan {
  const clamped = clampAmount(amount);
  const params: MorphParam[] = [];
  const unmatched: string[] = [];
  const seen = new Set<string>();
  for (const [groupName, paramNames] of data.groups) {
    if (!groups.has(groupName)) continue;
    for (const name of paramNames) {
      if (seen.has(name)) continue;
      seen.add(name);
      const inSource = Object.prototype.hasOwnProperty.call(data.source, name);
      const inTarget = Object.prototype.hasOwnProperty.call(data.target, name);
      if (inSource && inTarget) {
        const discrete = DISCRETE_PARAM_NAMES.has(name);
        const source = data.source[name]!;
        const target = data.target[name]!;
        const interpolated = interpolateValue(source, target, clamped, discrete);
        params.push({
          name,
          group: groupName,
          source,
          target,
          interpolated,
          discrete,
          moved: interpolated !== source,
        });
      } else if (inSource || inTarget) {
        unmatched.push(name);
      }
    }
  }
  const movedCount = params.filter((p) => p.moved).length;
  return {
    track: data.track,
    sourceName: data.sourceName,
    targetName: data.targetName,
    params,
    unmatched,
    movedCount,
  };
}

export function planMorph(
  tracks: ReadonlyArray<MorphTrackData>,
  groups: ReadonlySet<string>,
  amount: number,
): MorphPlan {
  const clamped = clampAmount(amount);
  const trackPlans = tracks.map((t) => planMorphTrack(t, groups, clamped));
  const totalMoved = trackPlans.reduce((sum, p) => sum + p.movedCount, 0);
  let ready: boolean;
  let readinessReason: string;
  if (groups.size === 0) {
    ready = false;
    readinessReason = 'no parameter groups selected';
  } else if (clamped === AMOUNT_MIN) {
    ready = false;
    readinessReason = 'amount is 0.0 (source unchanged)';
  } else if (totalMoved === 0) {
    ready = false;
    readinessReason = 'source and target already match in scope';
  } else {
    ready = true;
    readinessReason = 'ready';
  }
  return { amount: clamped, trackPlans, totalMoved, ready, readinessReason };
}

const SAFETY_LINES: ReadonlyArray<string> = [
  'passive/read-only',
  'preview plan only — no transmit path',
  'arm-and-send via the senders ArmedApply seam',
];

/** Build the passive PanelSpec for a morph plan. */
export function kitMorphPanelSpec(plan: MorphPlan): PanelSpecDict {
  const readyBadge = plan.ready
    ? { label: 'ready', tone: 'ok' as const, icon: '✓' }
    : { label: plan.readinessReason, tone: 'warn' as const, icon: '!' };
  const interpRows: string[][] = [];
  for (const trackPlan of plan.trackPlans) {
    for (const p of trackPlan.params) {
      interpRows.push([
        `Pad ${trackPlan.track}`,
        p.group,
        p.name,
        p.discrete ? 'discrete' : 'linear',
        String(p.source),
        String(p.target),
        String(p.interpolated),
      ]);
    }
  }
  return {
    panel_id: 'kit-morph',
    title: 'Kit morph preview',
    status_badges: [
      { label: `amount ${plan.amount.toFixed(2)}`, tone: 'neutral', icon: 'i' },
      readyBadge,
    ],
    sections: [
      {
        heading: 'Morph',
        kind: 'rows',
        rows: [`total params moved: ${plan.totalMoved}`],
        table: null,
        chips: [],
      },
      {
        heading: 'Interpolation',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Pad', 'Group', 'Param', 'Kind', 'Source', 'Target', 'Interp'],
          rows: interpRows,
        },
        chips: [],
      },
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: SAFETY_LINES,
  };
}
