# Live GUI Test Harness Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive GUI/audio-analyzer test-harness contract that consumes the live GUI playback-validation matrix and emits deterministic fixture, suite, and binding metadata for a future GUI runner.

**Architecture:** The report lives under `rytm_randomizer/reports/`, reuses the playback-validation builder/parser, and registers one passive CLI command through `CliCommand`. It produces stdout/JSON metadata only and never launches GUI, dispatches events, runs a test harness, writes files, reads audio streams, opens MIDI ports, or sends MIDI.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Harness Contract

**Files:**
- Create: `tests/test_live_gui_test_harness_contract_report.py`
- Create: `rytm_randomizer/reports/live_gui_test_harness_contract.py`
- Modify: `rytm_randomizer/reports/live_gui_playback_validation.py`

- [x] Write failing tests for suites, fixtures, bindings, JSON, formatting, status edges, replay edge handling, CLI parsing, and passive safety.
- [x] Run the new test file and confirm it fails because the report module is missing.
- [x] Implement the passive harness contract, including a public playback-validation parser wrapper.
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

- [x] Register `style-performance-arc-live-gui-test-harness-contract-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, fixture coverage, passive MIDI-safety coverage, README and docs notes.
- [x] Regenerate `tests/fixtures/cli_help_expected.txt` from `python -m rytm_randomizer.cli --help`.
- [x] Run focused CLI/passive tests and update any deterministic fixture drift.

### Task 3: Verification And Local Commit

**Files:**
- All intended files above.

- [x] Run focused harness-contract tests.
- [x] Run focused coverage for `rytm_randomizer.reports.live_gui_test_harness_contract`.
- [x] Run lint, architecture, fast/full, package coverage, and mechanical review gates.
- [x] Exact-stage only intended harness-contract files, excluding parity fixtures and unrelated CRLF noise.
- [x] Commit locally without pushing while PR #94 waits for review.
