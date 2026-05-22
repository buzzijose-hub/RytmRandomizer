# Live Performance Transition Timeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live-performance transition timeline that consumes the live show export packet and produces operator/GUI-ready cue transition states without touching hardware.

**Architecture:** The feature adds one report module under `rytm_randomizer/reports/` and registers one lazy passive CLI command. It composes `reports.live_show_export` instead of re-reading snapshots directly, preserving the existing arc -> cockpit -> show export chain and keeping all MIDI paths inactive.

**Tech Stack:** Python dataclasses, existing `CliCommand` registry, `reports.formatter` passive formatting helpers, pytest TDD, GitHub PR checklist gates.

---

## Design Checkpoint

The prior merged live-performance reports already climb from style/reference selection to stage routing, rehearsal state, cockpit, and live show export. The next complete layer should answer the live-show question: "I am moving between cues; what do I prep, launch, hold, or recover right now?"

This PR adds `style-performance-arc-live-transition-timeline-report`, a passive report that:

- consumes `StylePerformanceArcLiveShowExportReport` or builds one from the same arc/reference CLI arguments;
- emits deterministic transition cards for every cue;
- labels each transition with a phase (`launch`, `soundcheck`, `rescue`, or `review`);
- includes prep windows, machine handoff summaries, hold/recovery actions, passive replay commands, and capped event previews;
- exposes JSON shaped for a future GUI/live-performance state view;
- never writes files, opens ports, imports real MIDI, sends MIDI, or mutates hardware.

## Files

- Create `rytm_randomizer/reports/live_transition_timeline.py`
- Modify `rytm_randomizer/cli.py`
- Modify `rytm_randomizer/help_text.py`
- Modify `tests/test_style_performance_arcs_report.py`
- Modify `tests/test_cli.py`
- Modify `tests/test_cli_coverage.py`
- Modify `tests/test_real_midi_passive_cli_safety.py`
- Modify `tests/fixtures/cli_help_expected.txt`
- Modify `README.md`
- Modify `docs/STYLE_ANALYSIS.md`
- Modify `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify `docs/STATUS.md`
- Modify `docs/ARCHITECTURE.md`
- Modify `docs/ARCHITECTURE_DIAGRAMS.md`

## Tasks

### Task 1: Add Failing Behavior Tests

- [ ] Write focused tests that import the new report module, build a timeline from a live show export, assert transition card fields, JSON nesting, PowerShell-safe replay commands, CLI parsing, CLI dispatch, and event-preview limits.
- [ ] Run `python -m pytest tests\test_style_performance_arcs_report.py -k "live_transition_timeline" -n 0`.
- [ ] Expected RED: `ModuleNotFoundError` for `rytm_randomizer.reports.live_transition_timeline`.

### Task 2: Implement Passive Report Module

- [ ] Create the report module with frozen dataclasses, `Final` constants, passive safety lines, build/from-export functions, formatter, JSON serializer, parser, handler, and `CliCommand`.
- [ ] Reuse `build_style_performance_arc_live_show_export_report`, `to_style_performance_arc_live_show_export_json`, `PassiveReportHeader`, `passive_report_lines`, and `powershell_literal_arg`.
- [ ] Run the focused test and fix until green.

### Task 3: Wire CLI, Help, And Safety Sweeps

- [ ] Add the lazy command registration in `cli.py`.
- [ ] Add usage/help text and fixture rows.
- [ ] Add the new command to passive no-real-MIDI sweeps.
- [ ] Run focused CLI/help/safety tests.

### Task 4: Update Operator Docs

- [ ] Update README command examples and live-performance prose.
- [ ] Update STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, STATUS, ARCHITECTURE, and ARCHITECTURE_DIAGRAMS for the new passive report surface.

### Task 5: Verify And Publish

- [ ] Run focused report tests.
- [ ] Run CLI/safety/doc tests.
- [ ] Run architecture tests.
- [ ] Run lint, vulture, full pytest, coverage, and code review gate.
- [ ] Exact-stage only intended files, commit, push, open one non-stacked PR with reviewer requested.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) - focused tests and coverage run before PR.
- [x] Gate 2 (V1.34 parity fixtures byte-identical) - passive report only; no parity fixture regeneration.
- [x] Gate 3 (lint/format/type clean) - ruff, black, and isort before PR.
- [x] Gate 4 (dead-code purge) - vulture before PR.
- [x] Gate 5 (docs updated before PR open) - README and relevant docs updated.
- [x] Gate 6 (type-system hygiene) - frozen dataclasses, explicit types, no `Any`.
- [x] Gate 7 (observability adoption) - passive report formatting only; no hot-path state transition or MIDI send.
- [x] Gate 8 (test hygiene) - intent-named tests; existing fixtures reused.
- [x] Gate 9 (module organization hygiene) - new code lives under `reports/`, no top-level module.
- [x] Gate 10 (string-literal dispatch hygiene) - no mode/intensity dispatch changes.
- [x] Gate 11 (shared fixtures) - use existing test helper pattern.
- [x] Gate 12 (module-level constants use `Final`) - every constant annotated.
- [x] Gate 13 (env vars: docs + safe default) - no env vars added.
- [x] Gate 14 (maintainability review) - plan documents the seam and scope.
- [x] Gate 15 (learning phase) - no new reusable learned skill needed unless review finds one.
- [x] Gate 16 (execution shape) - isolated worktree, autonomous execution, no stacked PR.
- [x] Gate 17 (abstraction reuse and genericization) - composes live show export and formatter helpers.
- [x] Gate 18 (architecture-doc and diagram freshness) - docs updated for the new CLI/report surface.

## Rollback

Revert this PR to remove the passive timeline command and docs. It does not alter V1.34 runtime behavior, fixtures, hardware pins, or MIDI boundaries.
