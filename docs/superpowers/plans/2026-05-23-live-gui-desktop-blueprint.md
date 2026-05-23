# Live GUI Desktop Blueprint Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI desktop blueprint report that consumes the implementation bridge and emits deterministic future desktop-GUI implementation metadata.

**Architecture:** The report lives under `rytm_randomizer/reports/`, consumes `StylePerformanceArcLiveGuiImplementationBridgeReport`, and exposes a passive CLI command through `CliCommand`. It emits stdout/JSON only: blueprint sections, implementation tasks, fixture file hints, acceptance checks, blocked actions, and replay commands for future GUI work without launching a GUI, running a renderer, executing commands, opening MIDI ports, reading audio, or writing files.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Desktop Blueprint Report

**Files:**
- Create: `tests/test_live_gui_desktop_blueprint_report.py`
- Create: `rytm_randomizer/reports/live_gui_desktop_blueprint.py`

- [x] Write failing tests for blueprint id/version, status inheritance, sections, tasks, fixture hints, acceptance checks, JSON payload, formatted text, replay command replacement, parser coverage, handler coverage, and passive-safety boundaries.
- [x] Run `python -m pytest tests/test_live_gui_desktop_blueprint_report.py -n 0` and confirm it fails because the report module is missing.
- [x] Implement the passive desktop blueprint report.
- [x] Run `python -m pytest tests/test_live_gui_desktop_blueprint_report.py -n 0` and confirm it passes.

### Task 2: CLI, Help, And Docs Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/STYLE_ANALYSIS.md`

- [x] Register `style-performance-arc-live-gui-desktop-blueprint-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, fixture coverage, passive MIDI-safety coverage, README and docs notes.
- [x] Regenerate `tests/fixtures/cli_help_expected.txt` from `python -m rytm_randomizer.cli --help`.
- [x] Run focused CLI/passive tests and update deterministic fixture drift.

### Task 3: Verification And Local Commit

**Files:**
- All intended files above.

- [x] Run focused blueprint tests.
- [x] Run focused coverage for `rytm_randomizer.reports.live_gui_desktop_blueprint`.
- [x] Run lint, architecture, fast/full, package coverage, and mechanical review gates.
- [x] Exact-stage only intended blueprint files, excluding parity fixtures and unrelated CRLF noise.
- [x] Bundled into PR #95 after PR #94 landed; the branch is non-stacked against `origin/modularize-v1.34`, pushed for review, and no sibling PR dependency remains.

## Bundle Closeout Addendum

- Plan requirements: PR #95 links this plan and carries the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `data/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR #95 bundle commit(s) for this report chain; because the commands are passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
- Bundle status: PR #94 merged; this work was recreated from `origin/modularize-v1.34`, bundled into PR #95, pushed with exact-path staging, and review was requested.
