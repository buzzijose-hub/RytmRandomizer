# Live GUI Desktop Component Contract Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI desktop component-contract report that consumes the desktop app plan and emits deterministic component implementation contracts for a future desktop performance GUI.

**Architecture:** The report lives under `rytm_randomizer/reports/`, consumes `StylePerformanceArcLiveGuiDesktopAppPlanReport`, and exposes a passive CLI command through `CliCommand`. It emits stdout/JSON only: component contracts, prop contracts, disabled action contracts, test selectors, acceptance checks, blocked actions, and replay commands without launching a GUI, mounting components, dispatching events, starting a dev server, executing commands, writing files, opening MIDI ports, reading audio, or sending hardware messages.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Desktop Component Contract Report

**Files:**
- Create: `tests/test_live_gui_desktop_component_contract_report.py`
- Create: `rytm_randomizer/reports/live_gui_desktop_component_contract.py`

- [x] Write failing tests for contract id/version, status inheritance, component contracts, prop contracts, disabled action contracts, test selectors, acceptance checks, JSON payload, formatted text, replay command replacement, parser coverage, handler coverage, and passive-safety boundaries.
- [x] Run `python -m pytest tests/test_live_gui_desktop_component_contract_report.py -n 0` and confirm it fails because the report module is missing.
- [x] Implement the passive desktop component-contract report.
- [x] Run `python -m pytest tests/test_live_gui_desktop_component_contract_report.py -n 0` and confirm it passes.

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

- [x] Register `style-performance-arc-live-gui-desktop-component-contract-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, fixture coverage, passive MIDI-safety coverage, README and docs notes.
- [x] Regenerate `tests/fixtures/cli_help_expected.txt` from `python -m rytm_randomizer.cli --help`.
- [x] Run focused CLI/passive tests and update deterministic fixture drift.

### Task 3: Verification And Local Commit

**Files:**
- All intended files above.

- [x] Run focused component-contract tests.
- [x] Run focused coverage for `rytm_randomizer.reports.live_gui_desktop_component_contract`.
- [x] Run lint, architecture, fast/full, package coverage, and mechanical review gates.
- [x] Exact-stage only intended component-contract files, excluding parity fixtures and unrelated CRLF noise.
- [x] Commit locally without pushing while PR #94 waits for review.
