/**
 * Cross-language parity: the client-side scope/morph engines must reproduce
 * the Python reference engines byte-for-byte over the canonical demo data.
 *
 * `tests/cockpit/fixtures/scope_morph_expected.json` is generated from
 * `rytm_randomizer.behavior.{scope,morph}` (see the PR body). If a profile or
 * engine changes, regenerate both the demo data and this expected fixture and
 * review the diff.
 */

import { describe, expect, it } from 'vitest';

import { DEMO_MORPH_TRACKS, DEMO_SCOPE_TRACKS } from '../../../src/cockpit/panels/scopeMorphDemoData';
import { planMorph } from '../../../src/cockpit/panels/kitMorphPanelSpec';
import { planScope } from '../../../src/cockpit/panels/scopedRandomizationPanelSpec';

import expected from '../fixtures/scope_morph_expected.json';

describe('scope/morph client-Python parity', () => {
  it('reproduces the Python scope plan for the demo mask + depth 0.5', () => {
    const plan = planScope(
      DEMO_SCOPE_TRACKS,
      { tracks: new Set([1, 2]), groups: new Set(['src', 'filter']) },
      0.5,
    );
    expect({
      depth: plan.depth,
      totalChanged: plan.totalChanged,
      ready: plan.ready,
      readinessReason: plan.readinessReason,
      tracks: plan.trackPlans.map((tp) => ({
        track: tp.track,
        changedCount: tp.changedCount,
        deltas: tp.deltas.map((d) => ({
          name: d.name,
          group: d.group,
          anchor: d.anchor,
          planned: d.planned,
          delta: d.delta,
        })),
      })),
    }).toEqual(expected.scope);
  });

  it('reproduces the Python morph plan for the demo groups + amount 0.5', () => {
    const plan = planMorph(DEMO_MORPH_TRACKS, new Set(['src', 'filter']), 0.5);
    expect({
      amount: plan.amount,
      totalMoved: plan.totalMoved,
      ready: plan.ready,
      readinessReason: plan.readinessReason,
      tracks: plan.trackPlans.map((tp) => ({
        track: tp.track,
        movedCount: tp.movedCount,
        unmatched: [...tp.unmatched],
        params: tp.params.map((p) => ({
          name: p.name,
          group: p.group,
          source: p.source,
          target: p.target,
          interpolated: p.interpolated,
          discrete: p.discrete,
          moved: p.moved,
        })),
      })),
    }).toEqual(expected.morph);
  });
});
