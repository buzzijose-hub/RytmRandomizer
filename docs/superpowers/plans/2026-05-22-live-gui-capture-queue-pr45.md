# Live GUI Capture Queue PR45 Plan

## Why

The merged live GUI rehearsal-session packet can guide repeated cue captures, but
the future desktop GUI/audio analyzer still needs a deterministic queue shape:
which listen-only takes to capture, how to label them, which target packet each
take compares against, and which active actions remain blocked. This slice adds
that passive handoff without writing files, opening MIDI ports, recording audio,
or sending hardware messages.

## Scope

- Add `rytm_randomizer.reports.live_gui_capture_queue`.
- Register `style-performance-arc-live-gui-capture-queue-report` through the
  existing lazy CLI registry path.
- Extend help text, CLI fixtures, passive MIDI-safety coverage, README, status,
  style-analysis docs, manual validation notes, and architecture diagrams.
- Keep the feature report-only and composition-based: it consumes
  `live_gui_rehearsal_session` and re-emits upstream JSON sections.

## Workstreams

| Workstream | Owns | Depends on |
|---|---|---|
| Report model | Capture-slot and analyzer-job dataclasses, deterministic IDs, text/JSON format | PR #90 rehearsal session |
| CLI wiring | Lazy command registration, parser, help text, top-level fixture | Report model |
| Docs/status | README/status/style-analysis/manual-validation/diagram updates | CLI shape |
| Verification | Focused tests, coverage, architecture, lint, fast/full suites | Completed implementation |

## Parity Impact

No V1.34 runtime engine, group runner, scene runner, or parity fixture behavior is
changed. The feature only adds a new passive report and docs/help references.
Do not regenerate parity fixtures.

## Conformance Expectations

- Gate 1: new module receives 100% branch coverage.
- Gate 2: V1.34 parity is untouched.
- Gate 3: passive CLI remains read-only and never opens MIDI ports.
- Gate 4: no hardware-pinned package changes.
- Gate 5: lazy imports remain intact; no top-level `mido` import.
- Gate 6: no `Any` escape hatches.
- Gate 7: deterministic text/JSON report output.
- Gate 8: focused tests cover validation and guarded states.
- Gate 9: no new top-level package modules.
- Gate 10: no string-literal policy drift beyond command/help text.
- Gate 11: tests reuse existing fixtures.
- Gate 12: no CI workflow changes.
- Gate 13: parity capture mode is not used.
- Gate 14: observability unchanged; no runtime hot path.
- Gate 15: docs updated with changed behavior.
- Gate 16: one non-stacked PR against `modularize-v1.34`.
- Gate 17: reuses the rehearsal-session abstraction instead of duplicating upstream layers.
- Gate 18: architecture diagrams updated for the new passive command surface.

## Test Plan

- `python -m pytest tests\test_live_gui_capture_queue_report.py -n 0`
- `python -m pytest --cov=rytm_randomizer.reports.live_gui_capture_queue --cov-branch --cov-report=term-missing tests\test_live_gui_capture_queue_report.py -n 0`
- Focused CLI/help/passive MIDI-safety tests.
- Architecture suite.
- Ruff, Black check, and isort check.
- `python -m pytest -m fast`
- `python -m pytest`
- `python scripts\code_review_gate.py --mode cli`
- Full branch coverage command.
- Vulture sweep.

## Rollback

Revert the PR commit. The new report is additive and has no migration step,
stored state, hardware side effects, or fixture regeneration.
