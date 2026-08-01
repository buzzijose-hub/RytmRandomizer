/**
 * Canonical demonstration data for the scoped-randomization and kit-morph
 * panels, generated from the Python V1.34 profile registry so the interactive
 * client preview matches the CLI report byte-for-byte.
 *
 * Regenerate (adds/updates this JSON only) with:
 *
 *   .venv/bin/python - <<'PY'
 *   import json, pathlib
 *   from rytm_randomizer.behavior import scope, morph
 *   ...  # see scripts/notes or the PR body
 *   PY
 *
 * `tests/test_scope_morph_demo_data.py` asserts this fixture stays in sync
 * with the Python engines, so a profile change surfaces as a reviewable diff.
 */

import type { MorphTrackData } from './kitMorphPanelSpec';
import type { ScopeTrackData } from './scopedRandomizationPanelSpec';
import demo from './scopeMorphDemoData.json';

interface DemoData {
  readonly scopeTracks: ReadonlyArray<ScopeTrackData>;
  readonly morphTracks: ReadonlyArray<MorphTrackData>;
}

const typed = demo as unknown as DemoData;

export const DEMO_SCOPE_TRACKS: ReadonlyArray<ScopeTrackData> = typed.scopeTracks;
export const DEMO_MORPH_TRACKS: ReadonlyArray<MorphTrackData> = typed.morphTracks;
