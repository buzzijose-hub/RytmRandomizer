# Live Style Audition Set PR19 Plan

## Goal

Add one passive/mock-safe operator report that auditions several style targets in
sequence against the same Rytm and/or Analog Four saved-kit bank inputs. The
report should reuse the existing ranked style selection mock-preview layer for
each style, then summarize the whole set as text or JSON.

## Scope

- New report module under `rytm_randomizer/reports/`.
- New passive CLI command: `dual-machine-style-live-audition-report`.
- Text output for live/studio operators and JSON output for future GUI/audio
  analyzer consumers.
- Rytm-only, Analog Four-only, and dual-machine scopes are supported through the
  existing selection scope normalizer.
- No hardware sends, MIDI rendering, port opening, or runtime mutation.

## Implementation Sequence

1. Write failing tests for the multi-style plan builder, formatter, JSON
   contract, parser, CLI handler, CLI help, README visibility, lazy command
   import, and passive MIDI safety.
2. Implement the report by composing
   `build_dual_machine_style_selection_mock_preview_report()` once per style.
3. Register the command through `cli_registry` lazy dispatch and add static help.
4. Update README/status docs and the top-level CLI help fixture.
5. Run focused tests, architecture checks, lint, fast/full test suites, coverage,
   and review gate before push.

## Gate Notes

- Gate 1: touched report/test files will be covered by focused tests plus
  coverage run.
- Gate 2: no V1.34 runtime/parity behavior is changed; parity fixtures are not
  regenerated.
- Gate 3: ruff, black, and isort must pass.
- Gate 4: vulture must not report new dead code.
- Gate 5: README and `docs/STATUS.md` are updated.
- Gate 6: uses frozen dataclasses, `Final` constants, and explicit types.
- Gate 7: report-only path has no hot MIDI path and no metrics adoption need.
- Gate 8: new behavior tests are isolated and use existing SysEx fixtures.
- Gate 9: no new top-level modules; report stays under `reports/`.
- Gate 10: no new mode dispatch literals beyond the CLI command name.
- Gate 11: existing `conftest.py` kit payload helper is reused.
- Gate 12: module constants use `Final`.
- Gate 13: no new environment variables.
- Gate 14: complexity is bounded by composition of existing reports.
- Gate 15: no new learned skill/rule needed.
- Gate 16: one clean-base PR from `modularize-v1.34`, not stacked.
- Gate 17: reuses the existing style selection mock-preview report instead of
  creating a parallel selection engine.
- Gate 18: no architecture-surface change; docs/diagrams remain current.
