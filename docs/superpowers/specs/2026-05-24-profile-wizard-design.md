# Profile Wizard Design — Phase 2

**Date:** 2026-05-24
**Status:** Draft — pending user review
**Base branch:** `modularize-v1.34`
**Builds on:** `docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md` (merged via PR #99)

## Why

Phase 1 (PR #99) shipped the cockpit GUI + Python sidecar + WebSocket Protocol + 7 built-in scene profiles. Profiles can be SELECTED but not yet CREATED through the UI. Phase 2 closes that gap: an authoring surface where the operator points the system at musical inspiration (folders of SysEx, audio files, artist names) and gets a deployable `ProfileModel`.

The user's stated end-state from the brainstorm: "creating a profile will require you to analyze music to get an understanding of the inspiration." Phase 2 implements exactly that loop.

## Three deployment stages — Phase 2's role

| Stage | What Phase 2 adds |
|---|---|
| Authoring | **THE NEW WORK** — wizard UI + analysis pipeline + ProfileModel builder |
| GUI Runtime | Inherits user-authored profiles from disk automatically (Phase 1 already loads them) |
| Hardware Runtime | Phase 2 outputs the same `ProfileModel` format Phase 3 will export to binary |

## The wizard flow

Four steps, exactly as the operator experiences them:

1. **Name** — operator types a name (e.g., "buzzi"), optional description, optional color tag.
2. **Add sources** — operator adds one or more `InspirationSource`s: pick a file/folder via dialog, or type a reference (artist/album/song name with no file). Each source is typed (`kit`/`sound`/`song`/`album`/`artist`). Sources accumulate in a list; operator can remove items.
3. **Analyze** — operator hits "Analyze." Backend runs each source through the analysis pipeline. Per-source progress shown live. Failures are flagged with a "fix" option (retry, remove, or replace).
4. **Review + save** — operator sees the derived `StyleTrait` values (the bars in the cockpit's reference panel) and the `TraitPadWeight` mapping. They can rename, adjust description, or back up to re-analyze. Save writes the `ProfileModel` to `~/.rytm-randomizer/profiles/<id>.json` and emits `profile_created`. The cockpit's `ProfileChips` picks up the new profile automatically.

## The core data abstractions

Adds these new typed entities (frozen dataclasses, all in `cockpit/wizard/`):

```python
@dataclass(frozen=True)
class InspirationSource:
    source_id: str                                # ULID
    kind: Literal["kit", "sound", "song", "album", "artist"]
    mode: Literal["file", "folder", "reference"]
    location: str                                  # path for file/folder; name for reference
    display_name: str                              # user-facing label
    added_at: datetime

@dataclass(frozen=True)
class AnalysisJob:
    source_id: str                                 # references InspirationSource
    status: Literal["pending", "analyzing", "ok", "failed"]
    progress: float                                # 0.0..1.0
    error: str | None
    extracted_traits: tuple[StyleTrait, ...]       # what the analyzer produced (empty until ok)

@dataclass(frozen=True)
class WizardState:
    wizard_id: str                                 # ULID — one per wizard session
    step: Literal["name", "add", "analyze", "review"]
    name: str | None
    description: str | None
    sources: tuple[InspirationSource, ...]
    jobs: tuple[AnalysisJob, ...]
    candidate_profile: ProfileModel | None         # set when review-step reached
```

## The two new Protocols (extending PR #99's WS Protocol)

### Wizard commands (UI → Python sidecar)

```
wizard_start                  {}                            → { ok, wizard_id }
wizard_set_metadata           { name?, description? }       → { ok, state }
wizard_add_source             { kind, mode, location,
                                display_name }              → { ok, state, source_id }
wizard_remove_source          { source_id }                 → { ok, state }
wizard_analyze                {}                            → { ok }  # emits analysis_progress events
wizard_review                 {}                            → { ok, candidate_profile }
wizard_save                   {}                            → { ok, profile_id }
wizard_cancel                 {}                            → { ok }
```

### Wizard events (Python sidecar → UI · push)

```
wizard_state_changed          { state: WizardState }
analysis_progress             { job: AnalysisJob }                 # one per source update
profile_created               { profile: ProfileModel }            # final event after save
```

The cockpit's existing `profile_changed` event also fires after `wizard_save` so the active-profile UI updates.

## Analysis adapter

Bridges `InspirationSource` to the existing `style_analysis/` infrastructure:

- **Audio file/folder** (kind: song/album/sound) → `style_analysis.extractor.extract_features(path) -> FeatureReport` (already exists) → `feature_report_to_traits(feature_report)` → tuple[StyleTrait, ...]
- **SysEx file/folder** (kind: kit) → new `sysex_analyzer.extract_kit_traits(path)` that parses the kit dump + extracts per-pad parameter statistics + maps to traits
- **Reference** (kind: artist/album/song with mode=reference) → `reference_analyzer.lookup_traits(text)` — for Phase 2 this is a stub that returns sensible defaults from a small built-in lookup (Surgeon → industrial-heavy, Daniel Avery → drone-heavy, etc.) — real audio-fingerprint lookup is Phase 3+.

All analyzers run synchronously per source on a worker thread; the WS server reports progress between sources.

## ProfileBuilder

Combines analyzed sources into one `ProfileModel`:

```python
def build_profile(
    name: str,
    description: str | None,
    jobs: tuple[AnalysisJob, ...],
) -> ProfileModel:
    """Aggregate per-source traits → ProfileModel.

    - Traits: weighted average of `extracted_traits` across all OK jobs, normalized.
    - pad_mappings: derived from trait names via a small built-in trait→pad table.
    - kind: "user"
    - model_version: "1.0.0" initially; re-analysis bumps the patch level.
    """
```

The built-in trait→pad mapping (a `Final` table in `cockpit/wizard/pad_mapping.py`) defines which traits influence which pads. Standard: `rolling_low_end → Pad 1 (BD)`, `metallic_tension → Pad 2 (SD)`, `hat_density → Pad 3 (CH/OH)`, `filter_motion → Pad 4 (FX/FLT)`. Operator-overridable in a later iteration (out of scope for Phase 2).

## The frontend surface

New `desktop/web/src/wizard/` subdirectory with:

- `<Wizard />` — top-level container, routes between 4 steps
- `<WizardSteps />` — step indicator (Name · Add · Analyze · Review)
- `<NameStep />` — text input for name + description
- `<AddStep />` — source list + per-kind add buttons (`+ kit`, `+ sound`, `+ song`, `+ album`, `+ artist`) → file/folder picker via Tauri dialog plugin OR text input for references
- `<AnalyzeStep />` — per-source progress bars + retry/remove on failure
- `<ReviewStep />` — derived traits bars + pad mapping table + save button
- `<WizardLauncher />` — small "Create profile…" button in the cockpit's MutationPanel that opens the wizard (modal or route)

State flows through the same `cockpit/state/store.ts` extended with a `wizard` slice; WS events update it.

## What stays unchanged

- All Phase 1 Protocol commands and events continue working unchanged.
- The cockpit UI continues working unchanged — the wizard is additive.
- V1.34 parity contract — Phase 2 touches no engine code; existing `MutationPlanner` strategy stays the V1.34 path.
- Passive/active boundary — wizard is passive; it never sends MIDI; only the cockpit's armed runtime does.
- `mido` lazy-import discipline — wizard analyzers don't touch `mido` at all.

## 18-gate conformance plan

- [x] **Gate 1** — 100% branch coverage on every new file (enforced per WS).
- [x] **Gate 2** — V1.34 parity unchanged (no engine code touched).
- [x] **Gate 3** — lint/format/type clean (ruff + black + isort + TypeScript strict).
- [x] **Gate 4** — no new dead code.
- [x] **Gate 5** — docs updated (WS-G).
- [x] **Gate 6** — frozen dataclasses, Protocols, no bare `Any`.
- [x] **Gate 7** — observability: `get_metrics().record_*` on wizard commands + analysis decisions.
- [x] **Gate 8** — intent-named tests.
- [x] **Gate 9** — module organization: new `cockpit/wizard/` subpackage; no new top-level `*.py`.
- [x] **Gate 10** — `Literal` types for `kind`, `mode`, `status`, `step`.
- [x] **Gate 11** — shared fixtures (`wizard_session` fixture in `tests/cockpit/conftest.py`).
- [x] **Gate 12** — `Final` constants throughout.
- [x] **Gate 13** — no new env vars introduced.
- [x] **Gate 14** — maintainability audit (§ pre/post in the plan).
- [x] **Gate 15** — learning extraction.
- [x] **Gate 16** — execution shape (parallel WSes in worktrees).
- [x] **Gate 17** — abstraction reuse: wizard reuses existing `style_analysis/`, `cockpit/data`, `cockpit/profiles`, `cockpit/ws` infrastructure.
- [x] **Gate 18** — architecture-doc + diagram freshness (WS-G).

Exceptions: none.

## Out of scope

- Audio fingerprint lookup against external services (Phase 3+).
- Operator-editable trait→pad mapping UI (deferred).
- Phase 3 model export pipeline standalone CLI.
- Phase 4 hardware runtime.
