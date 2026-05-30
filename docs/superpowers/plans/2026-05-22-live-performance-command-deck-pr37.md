# Live Performance Command Deck Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live command deck report that turns the live transition timeline into an operator-ready "what do I do right now?" packet for live performance and future GUI/audio-analyzer routing.

**Architecture:** The feature adds one report module under `rytm_randomizer/reports/` and composes the existing `StylePerformanceArcLiveTransitionTimelineReport`. It does not add device-family code, does not touch the V1.34 engine/parity surface, and does not open hardware paths; CLI wiring stays lazy through `cli_registry` and `cli.py`.

**Tech Stack:** Python 3.11, frozen dataclasses, existing passive report formatter helpers, existing CLI registry, pytest, ruff, black, isort.

---

## Why

Jose's live-performance workflow needs the software to move beyond "here is the show timeline" into "here is the current cue, the next safe moves, and the recovery path." The already-merged live transition timeline provides cue-to-cue prep, launch, hold, recovery, and machine handoff rows. This PR builds the next passive layer: an operator-facing command deck for a selected cue, with lookahead cards and replayable passive commands.

## Workstream Graph

| Workstream | Owns | Depends On | Parallel With |
|---|---|---|---|
| WS1 Plan + RED tests | plan doc, focused report tests | current `origin/modularize-v1.34` | docs/help inspection agents |
| WS2 Report module | `rytm_randomizer/reports/live_command_deck.py` | WS1 RED tests | docs wording inspection |
| WS3 CLI/help/docs | `cli.py`, `help_text.py`, README/docs/status/diagrams | WS2 public API | fixture/test wiring |
| WS4 Verification + PR | gates, exact staging, PR body | WS1-WS3 | none |

## File Ownership

- Create `rytm_randomizer/reports/live_command_deck.py`: frozen report/card dataclasses, timeline composition, text formatter, JSON serializer, CLI parser/handler, safety lines, `CliCommand` registration.
- Modify `rytm_randomizer/cli.py`: add one lazy command mapping for `style-performance-arc-live-command-deck-report`.
- Modify `rytm_randomizer/help_text.py`: add top-level usage, command list entry, command-specific help, and `HELP_TEXT` mapping.
- Modify `tests/test_style_performance_arcs_report.py`: add RED-first builder/formatter/json/parser/handler/CLI dispatch tests.
- Modify `tests/test_cli.py`, `tests/test_cli_coverage.py`, `tests/test_real_midi_passive_cli_safety.py`, `tests/fixtures/cli_help_expected.txt`: CLI surface and passive safety coverage.
- Modify `README.md`, `docs/STYLE_ANALYSIS.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, `docs/STATUS.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`: docs freshness for the new passive command/report surface.

## Behavior Contract

- Command name: `style-performance-arc-live-command-deck-report`.
- Inputs: exactly one of `--arc`, `--description`, `--audio`, `--library`; optional `--rytm`, `--analog-four`, `--scope`, `--rank`, `--total-minutes`, `--segment-minutes`, `--discovery-start`, `--discovery-end`.
- Command-deck controls: `--cue N` selects the current cue, `--lookahead N` includes the next N cards, `--events --limit N` controls optional preview rows, `--json` emits deterministic JSON.
- `--cue` must be positive and within the available transition-card range.
- `--lookahead` and `--limit` must be non-negative; `0` means no lookahead or all events respectively.
- Text output includes command deck summary, current cue, lookahead, launch sequence, machine handoff, recovery controls, replayable passive commands, and safety.
- JSON output nests `live_command_deck`, `live_transition_timeline`, `live_show_export`, downstream live reports, `reference_match`, and `safety`.
- The whole path remains passive: no real MIDI rendering, no MIDI sending, no port opening, no command execution, no file writing.

## TDD Steps

- [ ] **Step 1: Write failing tests for command-deck report behavior.**

  Add tests that import the not-yet-existing `rytm_randomizer.reports.live_command_deck` module and assert:

  ```python
  report = build_style_performance_arc_live_command_deck_report(
      arc_key="jose_warehouse_five_hour",
      rytm_sysex_path=rytm_path,
      analog_four_sysex_path=a4_path,
      cue_number=2,
      lookahead_count=2,
      total_minutes=60,
      segment_minutes=30,
  )
  assert report.current_cue.cue_number == 2
  assert len(report.lookahead_cues) == 2
  assert report.timeline.selected_arc_key == "jose_warehouse_five_hour"
  ```

- [ ] **Step 2: Verify RED.**

  Run:

  ```powershell
  python -m pytest tests\test_style_performance_arcs_report.py -k "live_command_deck" -n 0
  ```

  Expected: fail because `rytm_randomizer.reports.live_command_deck` is missing or the command is not registered.

- [ ] **Step 3: Implement the passive report module.**

  Build from `StylePerformanceArcLiveTransitionTimelineReport`, do not parse serialized JSON, and keep all records frozen dataclasses. Reuse `powershell_literal_arg`, `PassiveReportHeader`, `passive_report_lines`, and `normalize_selection_scope`.

- [ ] **Step 4: Wire CLI/help.**

  Add the lazy CLI mapping and command-specific help. Keep help language passive and avoid active-send vocabulary.

- [ ] **Step 5: Add docs and fixture updates.**

  Update README/manual/style docs plus architecture docs because a new CLI/report surface triggers Gate 18. Update the CLI help fixture after verifying the output.

- [ ] **Step 6: Verify focused behavior and coverage.**

  Run:

  ```powershell
  python -m pytest tests\test_style_performance_arcs_report.py -k "live_command_deck or cli_dispatch_and_help or resolve_help" -n 0
  python -m pytest tests\test_cli.py tests\test_cli_coverage.py tests\test_real_midi_passive_cli_safety.py -k "live_command_deck or live_transition_timeline or passive_commands or help" -n 0
  python -m pytest tests\test_style_performance_arcs_report.py -k "live_command_deck" --cov=rytm_randomizer.reports.live_command_deck --cov-branch --cov-report=term-missing -n 0
  ```

- [ ] **Step 7: Run full gates.**

  Run architecture, fast/full pytest, coverage, lint, and review gate. Do not use `-o addopts=''`.

- [ ] **Step 8: Exact-stage and open one PR.**

  Stage only the intended files from this plan, commit, push, and create a non-stacked PR against `modularize-v1.34` using the repo PR tooling so reviewer request is automated.

## Plan-Requirements Conformance

- [x] Gate 1 - 100% branch coverage on touched report module; focused coverage command listed.
- [x] Gate 2 - V1.34 parity remains byte-identical; this PR does not touch engines/group/scene parity behavior or regenerate fixtures.
- [x] Gate 3 - ruff, black, and isort run before push.
- [x] Gate 4 - dead-code review via ruff/vulture/review gate before push.
- [x] Gate 5 - README, STATUS, manual validation, style analysis, architecture docs, and diagrams updated.
- [x] Gate 6 - frozen dataclasses and explicit types; no `Any`.
- [ ] Gate 7 - N/A: passive report composition only, no state transition, guardrail decision, or MIDI send hot path.
- [x] Gate 8 - behavior-focused tests with clear names in the existing report test file.
- [x] Gate 9 - new code lives under existing `reports/` subpackage.
- [x] Gate 10 - no new mode/intensity/page string dispatch; scope normalization reuses existing helper.
- [x] Gate 11 - no duplicated shared fixtures.
- [x] Gate 12 - module constants annotated `Final`.
- [ ] Gate 13 - N/A: no new environment variables.
- [x] Gate 14 - maintainability addressed by composing existing timeline/report layers rather than adding a parallel surface.
- [ ] Gate 15 - N/A: no reusable learned skill needed for this passive report slice.
- [x] Gate 16 - work is isolated in a codex worktree and shipped as one non-stacked PR.
- [x] Gate 17 - abstraction reuse: consumes `cli_registry`, passive formatter helpers, and the transition timeline dataclass API.
- [x] Gate 18 - architecture docs and diagrams updated for the new CLI/report surface.

## Rollback Plan

Revert the single feature commit. The report is passive and not referenced by existing active runtime paths, so removal of the command mapping, report module, tests, and docs restores the previous command surface without touching V1.34 parity behavior.

## Done Criteria

- Command works in text and JSON modes.
- Invalid cue/lookahead/event limits fail deterministically.
- Passive CLI safety sweep includes the new command and does not import real MIDI modules.
- Focused coverage reaches 100% branch coverage for `live_command_deck.py`.
- Architecture, lint, full tests, coverage, and review gates pass.
- PR is opened against `modularize-v1.34` with reviewer requested and the full 18-gate checklist.
