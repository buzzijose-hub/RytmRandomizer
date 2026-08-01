/**
 * Scoped randomization — pure PanelSpec selector + a deterministic client-side
 * port of `rytm_randomizer/behavior/scope.py`.
 *
 * The passive delta table renders through the schema-driven PanelSpec platform
 * (`PanelRenderer`); the interactive mask grid (per-track / per-group chips) and
 * the depth slider live in `ScopedRandomizationPanel.tsx`. Everything here is
 * pure — no React, no fetch, no state — and passive: it produces a previewable
 * plan the operator can arm-and-send through the existing ArmedApply seam, and
 * reaches no transmit path itself.
 *
 * The plan math mirrors the Python engine byte-for-byte: move each in-scope
 * continuous parameter toward the wider safe edge by `round(depth * reach)`;
 * discrete selectors are held on their anchor.
 */

import type { PanelSpecDict } from '../../types/live_gui_protocol';

export const DEPTH_MIN = 0.0;
export const DEPTH_MAX = 1.0;
export const TRACK_COUNT = 12;

/** Selector params held on their anchor by a scoped intensity sweep. */
export const DISCRETE_PARAM_NAMES: ReadonlySet<string> = new Set([
  'FLT Type',
  'LFO Destination',
  'LFO Multiplier',
  'LFO Trig Mode',
  'LFO Waveform',
  'SRC Mod Type',
  'SRC Osc 1 Wave',
  'SRC Osc 2 Wave',
  'SRC Waveform',
]);

export interface ScopeTrackData {
  readonly track: number;
  readonly profileName: string;
  readonly anchor: Readonly<Record<string, number>>;
  readonly safe: Readonly<Record<string, readonly [number, number]>>;
  /** Ordered group -> ordered param names. */
  readonly groups: ReadonlyArray<readonly [string, ReadonlyArray<string>]>;
}

export interface ScopeMask {
  readonly tracks: ReadonlySet<number>;
  readonly groups: ReadonlySet<string>;
}

export interface ScopeParamDelta {
  readonly name: string;
  readonly group: string;
  readonly anchor: number;
  readonly planned: number;
  readonly delta: number;
}

export interface ScopeTrackPlan {
  readonly track: number;
  readonly profileName: string;
  readonly deltas: ReadonlyArray<ScopeParamDelta>;
  readonly changedCount: number;
}

export interface ScopePlan {
  readonly depth: number;
  readonly trackPlans: ReadonlyArray<ScopeTrackPlan>;
  readonly totalChanged: number;
  readonly ready: boolean;
  readonly readinessReason: string;
}

export function clampDepth(depth: number): number {
  if (depth < DEPTH_MIN) return DEPTH_MIN;
  if (depth > DEPTH_MAX) return DEPTH_MAX;
  return depth;
}

/** Signed maximum reach toward the wider safe edge; ties resolve upward. */
export function reach(anchor: number, low: number, high: number): number {
  const up = high - anchor;
  const down = anchor - low;
  return up >= down ? up : -down;
}

/**
 * Round-half-to-even (banker's rounding) — matches Python's built-in `round()`,
 * so the client-side plan is byte-identical to the reference engine at the .5
 * boundary (e.g. `round(58.5) === 58`, not 59).
 */
export function roundHalfEven(value: number): number {
  const floor = Math.floor(value);
  const diff = value - floor;
  if (diff < 0.5) return floor;
  if (diff > 0.5) return floor + 1;
  // Exactly .5 -> pick the even neighbor.
  return floor % 2 === 0 ? floor : floor + 1;
}

function scaledOffset(reachValue: number, depth: number): number {
  return roundHalfEven(reachValue * depth);
}

export function planTrackScope(
  data: ScopeTrackData,
  mask: ScopeMask,
  depth: number,
): ScopeTrackPlan {
  const clamped = clampDepth(depth);
  const deltas: ScopeParamDelta[] = [];
  const seen = new Set<string>();
  for (const [groupName, paramNames] of data.groups) {
    if (!mask.groups.has(groupName)) continue;
    for (const name of paramNames) {
      if (seen.has(name)) continue;
      seen.add(name);
      const anchorValue = data.anchor[name];
      const bound = data.safe[name];
      if (anchorValue === undefined || bound === undefined || DISCRETE_PARAM_NAMES.has(name)) {
        continue;
      }
      const [low, high] = bound;
      const clampedAnchor = Math.min(Math.max(anchorValue, low), high);
      const planned = clampedAnchor + scaledOffset(reach(clampedAnchor, low, high), clamped);
      deltas.push({
        name,
        group: groupName,
        anchor: anchorValue,
        planned,
        delta: planned - anchorValue,
      });
    }
  }
  const changedCount = deltas.filter((d) => d.delta !== 0).length;
  return { track: data.track, profileName: data.profileName, deltas, changedCount };
}

export function planScope(
  tracks: ReadonlyArray<ScopeTrackData>,
  mask: ScopeMask,
  depth: number,
): ScopePlan {
  const clamped = clampDepth(depth);
  const trackPlans = tracks
    .filter((t) => mask.tracks.has(t.track))
    .map((t) => planTrackScope(t, mask, clamped));
  const totalChanged = trackPlans.reduce((sum, p) => sum + p.changedCount, 0);
  let ready: boolean;
  let readinessReason: string;
  if (mask.tracks.size === 0) {
    ready = false;
    readinessReason = 'no tracks selected';
  } else if (mask.groups.size === 0) {
    ready = false;
    readinessReason = 'no parameter groups selected';
  } else if (clamped === DEPTH_MIN) {
    ready = false;
    readinessReason = 'depth is 0.0 (no movement)';
  } else if (totalChanged === 0) {
    ready = false;
    readinessReason = 'mask selects no reachable continuous parameters';
  } else {
    ready = true;
    readinessReason = 'ready';
  }
  return { depth: clamped, trackPlans, totalChanged, ready, readinessReason };
}

const SAFETY_LINES: ReadonlyArray<string> = [
  'passive/read-only',
  'preview plan only — no transmit path',
  'arm-and-send via the senders ArmedApply seam',
];

/** Build the passive PanelSpec for a scope plan. */
export function scopedRandomizationPanelSpec(plan: ScopePlan): PanelSpecDict {
  const readyBadge = plan.ready
    ? { label: 'ready', tone: 'ok' as const, icon: '✓' }
    : { label: plan.readinessReason, tone: 'warn' as const, icon: '!' };
  const deltaRows: string[][] = [];
  for (const trackPlan of plan.trackPlans) {
    for (const d of trackPlan.deltas) {
      const sign = d.delta >= 0 ? '+' : '';
      deltaRows.push([
        `Pad ${trackPlan.track}`,
        d.group,
        d.name,
        String(d.anchor),
        String(d.planned),
        `${sign}${d.delta}`,
      ]);
    }
  }
  return {
    panel_id: 'scoped-randomization',
    title: 'Scoped randomization preview',
    status_badges: [{ label: `depth ${plan.depth.toFixed(2)}`, tone: 'neutral', icon: 'i' }, readyBadge],
    sections: [
      {
        heading: 'Mask',
        kind: 'rows',
        rows: [`total params moved: ${plan.totalChanged}`],
        table: null,
        chips: [],
      },
      {
        heading: 'Parameter deltas',
        kind: 'table',
        rows: [],
        table: {
          columns: ['Pad', 'Group', 'Param', 'Anchor', 'Planned', 'Delta'],
          rows: deltaRows,
        },
        chips: [],
      },
    ],
    required_actions: [],
    blocked_actions: [],
    safety_lines: SAFETY_LINES,
  };
}
