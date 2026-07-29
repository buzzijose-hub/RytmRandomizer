/**
 * KitMorphPanel — kit morphing as a playable, passive preview. A per-group
 * mask plus a morph-amount slider recompute the deterministic MorphPlan
 * (source -> target interpolation) entirely client-side; the resulting
 * per-parameter interpolation table renders through the generic PanelRenderer.
 *
 * Passive per the Live-but-Passive rule: nothing here sends MIDI or reaches the
 * ArmedApply seam. The operator arms-and-sends the previewed plan through the
 * existing seam elsewhere. Slider a11y follows the house APG pattern
 * (aria-label + aria-valuetext); value/min/max are exposed cleanly.
 */

import { useMemo, useState } from 'react';

import { DEMO_MORPH_TRACKS } from './scopeMorphDemoData';
import {
  AMOUNT_MAX,
  AMOUNT_MIN,
  kitMorphPanelSpec,
  planMorph,
  type MorphTrackData,
} from './kitMorphPanelSpec';
import { PanelRenderer } from './PanelRenderer';
import './panel.css';

export const AMOUNT_STEP = 0.05;
const DEFAULT_AMOUNT = 0.5;

/** Distinct group names across the roster, in first-seen order. */
export function availableMorphGroups(tracks: ReadonlyArray<MorphTrackData>): string[] {
  const seen: string[] = [];
  for (const track of tracks) {
    for (const [group] of track.groups) {
      if (!seen.includes(group)) seen.push(group);
    }
  }
  return seen;
}

function toggle(set: ReadonlySet<string>, value: string): Set<string> {
  const next = new Set(set);
  if (next.has(value)) {
    next.delete(value);
  } else {
    next.add(value);
  }
  return next;
}

export interface KitMorphPanelProps {
  tracks?: ReadonlyArray<MorphTrackData>;
}

export function KitMorphPanel({ tracks = DEMO_MORPH_TRACKS }: KitMorphPanelProps): JSX.Element {
  const groups = useMemo(() => availableMorphGroups(tracks), [tracks]);
  const [selectedGroups, setSelectedGroups] = useState<ReadonlySet<string>>(() => new Set(groups));
  const [amount, setAmount] = useState(DEFAULT_AMOUNT);

  const plan = planMorph(tracks, selectedGroups, amount);
  const amountPercent = Math.round(amount * 100);
  const targetLabel = tracks.length > 0 ? tracks[0]!.targetName : '';
  const sourceLabel = tracks.length > 0 ? tracks[0]!.sourceName : '';

  return (
    <div className="cockpit-panel-stack" data-testid="kit-morph">
      <div className="cockpit-panel-controls">
        <span className="cockpit-panel-note" data-testid="kit-morph-endpoints">
          {sourceLabel} → {targetLabel}
        </span>
        <fieldset className="cockpit-panel-fieldset">
          <legend>Groups</legend>
          <div className="cockpit-panel-toggle-row">
            {groups.map((group) => {
              const on = selectedGroups.has(group);
              return (
                <button
                  key={group}
                  type="button"
                  className="cockpit-mask-toggle"
                  aria-pressed={on}
                  data-testid={`morph-group-${group}`}
                  onClick={() => setSelectedGroups((prev) => toggle(prev, group))}
                >
                  {group}
                </button>
              );
            })}
          </div>
        </fieldset>
        <label className="cockpit-panel-slider">
          <span>Morph {amountPercent}%</span>
          <input
            type="range"
            min={AMOUNT_MIN}
            max={AMOUNT_MAX}
            step={AMOUNT_STEP}
            value={amount}
            aria-label="Morph amount"
            aria-valuetext={`${amountPercent} percent`}
            data-testid="kit-morph-slider"
            onChange={(ev) => setAmount(Number.parseFloat(ev.target.value))}
          />
        </label>
      </div>
      <PanelRenderer spec={kitMorphPanelSpec(plan)} />
    </div>
  );
}
