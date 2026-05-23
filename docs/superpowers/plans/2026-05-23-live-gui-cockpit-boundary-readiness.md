# Live GUI Cockpit Boundary Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive GUI cockpit boundary-readiness report that consumes the live GUI desktop render harness and emits deterministic metadata for the future cockpit implementation boundary.

**Architecture:** The report lives under `rytm_randomizer/reports/`, reuses the desktop render-harness builder/parser, and registers one passive CLI command through `CliCommand`. It produces stdout/JSON metadata only and never launches a GUI, starts a Tauri/web shell, starts a sidecar server, reads audio streams, opens MIDI ports, or sends MIDI.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Boundary-Readiness Report

**Files:**
- Create: `tests/test_live_gui_cockpit_boundary_readiness_report.py`
- Create: `rytm_randomizer/reports/live_gui_cockpit_boundary_readiness.py`

- [x] Write failing tests for boundary checks, Rytm 12-pad/A4 4-track device scope checks, future WebSocket env docs, optional toolchain guardrails, blocked actions, JSON, formatting, CLI parsing, status edges, and passive safety.
- [x] Run the new test file and confirm it fails because the report module/help/CLI command are missing.
- [x] Implement the passive boundary-readiness report from the desktop render harness.
- [x] Run the new test file and confirm it passes.

### Task 2: CLI, Help, And Docs Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `README.md`
- Modify: `CONTRIBUTING.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/LOCAL_DEV_TOOLING_NOTES.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/STYLE_ANALYSIS.md`

- [x] Register `style-performance-arc-live-gui-cockpit-boundary-readiness-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, fixture coverage, passive MIDI-safety coverage, README and docs notes.
- [x] Document `RYTM_RAND_WS_PORT` as a reserved future cockpit env var, not active runtime configuration.
- [x] Run focused CLI/passive tests and update deterministic help fixture drift.

### Task 3: Verification And Local Commit

**Files:**
- All intended files above.

- [x] Run focused boundary-readiness tests.
- [x] Run focused coverage for `rytm_randomizer.reports.live_gui_cockpit_boundary_readiness`.
- [x] Run lint, architecture, fast/full, package coverage, and mechanical review gates.
- [x] Exact-stage only intended boundary-readiness files, excluding parity fixtures and unrelated CRLF noise.
- [x] Prepare the branch for a non-stacked PR against `origin/modularize-v1.34` after final local diff review.

## Bundle Closeout Addendum

- Plan requirements: the PR links this plan and carries the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR bundle commit for this report; because the command is passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
- Bundle status: this work was created from `origin/modularize-v1.34` after PR #98 landed and remains independent of Eddie's draft PR #99.
