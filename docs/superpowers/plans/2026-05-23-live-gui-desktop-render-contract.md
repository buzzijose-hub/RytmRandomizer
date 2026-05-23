# Live GUI Desktop Render Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive desktop render-contract report that consumes the live GUI desktop view-model packet and emits deterministic render surfaces, prop/state bindings, assertions, style-token bindings, blocked actions, and replay commands for a future GUI implementation.

**Architecture:** The report lives under `rytm_randomizer/reports/`, reuses the desktop view-model builder/parser, and registers one passive CLI command through `CliCommand`. It produces stdout/JSON metadata only and never launches GUI, mounts components, executes a renderer, writes files, opens audio streams, opens MIDI ports, or sends MIDI.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Render Contract Report

**Files:**
- Create: `tests/test_live_gui_desktop_render_contract_report.py`
- Create: `rytm_randomizer/reports/live_gui_desktop_render_contract.py`

- [x] Write failing tests for render surfaces, render bindings, style-token bindings, assertions, JSON, formatting, status edges, replay edge handling, CLI parsing, and passive safety.
- [x] Run the new test file and confirm it fails because the render-contract report module is missing.
- [x] Implement the passive render-contract report by adapting the upstream desktop view-model packet into render metadata.
- [x] Run the new test file and confirm it passes.

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

- [x] Register `style-performance-arc-live-gui-desktop-render-contract-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, fixture coverage, passive MIDI-safety coverage, README and docs notes.
- [x] Update `tests/fixtures/cli_help_expected.txt` to match `python -m rytm_randomizer.cli --help`.
- [x] Run focused CLI/passive tests and update deterministic fixture drift only for this command.

### Task 3: Verification And Local Commit

**Files:**
- All intended files above.

- [x] Run focused render-contract tests.
- [x] Run focused coverage for `rytm_randomizer.reports.live_gui_desktop_render_contract`.
- [x] Run lint, architecture, fast/full, package coverage, and mechanical review gates.
- [x] Exact-stage only intended render-contract files, excluding parity fixtures and unrelated CRLF noise.
- [ ] Open one non-stacked PR against `origin/modularize-v1.34` with the required checklist and this plan link.

## Bundle Closeout Addendum

- Plan requirements: this PR must link this plan and carry the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `data/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the render-contract PR bundle; because the command is passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
