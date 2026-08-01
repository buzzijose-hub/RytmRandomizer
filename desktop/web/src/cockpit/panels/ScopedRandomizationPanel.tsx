/**
 * ScopedRandomizationPanel — the classic Rytm mask+intensity randomizer UX as
 * a passive preview. A per-track / per-group mask grid (aria-pressed toggle
 * buttons) plus a depth slider recompute the deterministic ScopePlan entirely
 * client-side; the resulting parameter-delta table renders through the generic
 * PanelRenderer.
 *
 * **Static demonstration, and the UI says so.** The tracks come from the
 * committed `scopeMorphDemoData.json` fixture, not the connected instrument,
 * and the plan is recomputed in TypeScript. Cross-language parity with
 * `behavior/scope.py` is pinned by `scopeMorphParity.test.ts`, but only over
 * the mask/depth combinations that fixture covers — the slider and mask
 * toggles reach states no backend computed. `DemoDataBanner` labels that in
 * the panel so nobody mistakes illustrative arithmetic for a prepared send
 * plan.
 *
 * Passive per the Live-but-Passive rule: nothing here sends MIDI or reaches the
 * ArmedApply seam. Slider a11y follows the house APG pattern
 * (aria-label + aria-valuetext); value/min/max are exposed cleanly.
 */

import { useMemo, useState } from 'react';

import { DemoDataBanner } from './DemoDataBanner';
import { DEMO_SCOPE_TRACKS } from './scopeMorphDemoData';
import {
  DEPTH_MAX,
  DEPTH_MIN,
  planScope,
  scopedRandomizationPanelSpec,
  type ScopeMask,
  type ScopeTrackData,
} from './scopedRandomizationPanelSpec';
import { PanelRenderer } from './PanelRenderer';
import './panel.css';

export const DEPTH_STEP = 0.05;
const DEFAULT_DEPTH = 0.5;

/** Distinct group names across the roster, in first-seen order. */
export function availableGroups(tracks: ReadonlyArray<ScopeTrackData>): string[] {
  const seen: string[] = [];
  for (const track of tracks) {
    for (const [group] of track.groups) {
      if (!seen.includes(group)) seen.push(group);
    }
  }
  return seen;
}

function toggle<T>(set: ReadonlySet<T>, value: T): Set<T> {
  const next = new Set(set);
  if (next.has(value)) {
    next.delete(value);
  } else {
    next.add(value);
  }
  return next;
}

export interface ScopedRandomizationPanelProps {
  tracks?: ReadonlyArray<ScopeTrackData>;
}

export function ScopedRandomizationPanel({
  tracks = DEMO_SCOPE_TRACKS,
}: ScopedRandomizationPanelProps): JSX.Element {
  const groups = useMemo(() => availableGroups(tracks), [tracks]);
  const [selectedTracks, setSelectedTracks] = useState<ReadonlySet<number>>(
    () => new Set(tracks.map((t) => t.track)),
  );
  const [selectedGroups, setSelectedGroups] = useState<ReadonlySet<string>>(() => new Set(groups));
  const [depth, setDepth] = useState(DEFAULT_DEPTH);

  const mask: ScopeMask = { tracks: selectedTracks, groups: selectedGroups };
  const plan = planScope(tracks, mask, depth);
  const depthPercent = Math.round(depth * 100);

  return (
    <div className="cockpit-panel-stack" data-testid="scoped-randomization">
      <DemoDataBanner what="scoped randomization" testId="scope-demo-banner" />
      <div className="cockpit-panel-controls">
        <fieldset className="cockpit-panel-fieldset">
          <legend>Tracks</legend>
          <div className="cockpit-panel-toggle-row">
            {tracks.map((track) => {
              const on = selectedTracks.has(track.track);
              return (
                <button
                  key={track.track}
                  type="button"
                  className="cockpit-mask-toggle"
                  aria-pressed={on}
                  data-testid={`scope-track-${track.track}`}
                  onClick={() => setSelectedTracks((prev) => toggle(prev, track.track))}
                >
                  Pad {track.track}
                </button>
              );
            })}
          </div>
        </fieldset>
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
                  data-testid={`scope-group-${group}`}
                  onClick={() => setSelectedGroups((prev) => toggle(prev, group))}
                >
                  {group}
                </button>
              );
            })}
          </div>
        </fieldset>
        <label className="cockpit-panel-slider">
          <span>Depth {depthPercent}%</span>
          <input
            type="range"
            min={DEPTH_MIN}
            max={DEPTH_MAX}
            step={DEPTH_STEP}
            value={depth}
            aria-label="Randomization depth"
            aria-valuetext={`${depthPercent} percent`}
            data-testid="scope-depth-slider"
            onChange={(ev) => setDepth(Number.parseFloat(ev.target.value))}
          />
        </label>
      </div>
      <PanelRenderer spec={scopedRandomizationPanelSpec(plan)} />
    </div>
  );
}
