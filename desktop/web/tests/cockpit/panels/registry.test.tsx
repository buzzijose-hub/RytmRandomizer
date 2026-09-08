/**
 * Registry-manifest tests.
 *
 * The point of these is structural, not cosmetic: before the `store-slice`
 * variant existed, `PANEL_REGISTRY` held exactly one entry (the analyzer)
 * while five interactive panels were hand-mounted in `Cockpit.tsx` — the
 * layout bypassed the extension seam that is supposed to describe it. These
 * tests pin that every cockpit panel is reachable *through the registry*, so
 * a future panel added by hand fails here rather than silently re-opening the
 * bypass.
 */

import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CockpitClientProvider } from '../../../src/cockpit/context';
import { PanelHost } from '../../../src/cockpit/panels/PanelHost';
import { PANEL_REGISTRY, panelsForRegion } from '../../../src/cockpit/panels/registry';
import { FakeCockpitClient } from '../_fixtures';

const EXPECTED_BOTTOM_PANEL_IDS: ReadonlyArray<string> = [
  'live-midi-monitor',
  'connection-doctor',
  'library',
  'scoped-randomization',
  'kit-morph',
  'show-kit-forge',
];

/** Each bottom panel's own root testid, in manifest order. */
const EXPECTED_BOTTOM_TESTIDS: ReadonlyArray<string> = [
  'live-midi-monitor',
  'connection-doctor',
  'library-panel',
  'scoped-randomization',
  'kit-morph',
  'show-kit-forge',
];

describe('panel registry manifest', () => {
  it('registers every bottom-rail panel, in layout order, as a store-slice entry', () => {
    const bottom = panelsForRegion('bottom');
    expect(bottom.map((entry) => entry.id)).toEqual(EXPECTED_BOTTOM_PANEL_IDS);
    expect(bottom.every((entry) => entry.kind === 'store-slice')).toBe(true);
  });

  it('exposes unique panel ids across every region', () => {
    const ids = PANEL_REGISTRY.map((entry) => entry.id);
    expect(new Set(ids).size).toBe(ids.length);
  });

  it('returns an empty list for a region with no registered panels', () => {
    expect(panelsForRegion('left-rail')).toEqual([]);
  });

  it('PanelHost mounts every registered bottom panel with no console packet', () => {
    const fake = new FakeCockpitClient();
    render(
      <CockpitClientProvider client={fake.asClient()}>
        <PanelHost region="bottom" />
      </CockpitClientProvider>,
    );
    for (const testId of EXPECTED_BOTTOM_TESTIDS) {
      expect(screen.getByTestId(testId)).toBeInTheDocument();
    }
  });
});
