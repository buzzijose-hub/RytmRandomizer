# Live GUI Desktop View-Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI desktop view-model report that consumes desktop component contracts and emits deterministic future-GUI binding metadata.

**Architecture:** The report lives under `rytm_randomizer/reports/`, consumes `StylePerformanceArcLiveGuiDesktopComponentContractReport`, and exposes a passive CLI command through `CliCommand`. It emits stdout/JSON only: component view models, state bindings, disabled action view models, style tokens, acceptance checks, blocked actions, and replay commands without launching a GUI, mounting components, dispatching events, starting a dev server, executing commands, writing files, opening MIDI ports, recording or streaming audio, comparing audio, or sending hardware messages. Explicit `--audio` and `--library` paths remain read-only inputs to the existing passive style-analysis path.

**Tech Stack:** Python dataclasses, existing passive report formatter helpers, existing CLI registry, pytest TDD, existing docs/help fixtures.

---

### Task 1: TDD Desktop View-Model Report

**Files:**
- Create: `tests/test_live_gui_desktop_view_model_report.py`
- Create: `rytm_randomizer/reports/live_gui_desktop_view_model.py`

- [x] Write failing tests for contract id/version, status inheritance, component view models, state bindings, disabled action view models, style tokens, acceptance checks, JSON payload, formatted text, replay command replacement, parser coverage, handler coverage, and passive-safety boundaries.
- [x] Run `python -m pytest tests/test_live_gui_desktop_view_model_report.py -n 0` and confirm it fails because the report module/CLI command is missing.
- [x] Implement the passive desktop view-model report by composing `live_gui_desktop_component_contract.py`, not by reimplementing upstream app-plan or component-contract logic.
- [x] Run `python -m pytest tests/test_live_gui_desktop_view_model_report.py -n 0` and confirm it passes.

### Task 2: CLI, Help, And Passive-Safety Wiring

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_cli_coverage.py`
- Modify: `tests/test_real_midi_passive_cli_safety.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] Register `style-performance-arc-live-gui-desktop-view-model-report` lazily in the passive CLI.
- [x] Add command help, top-level usage, command list entry, CLI fixture coverage, and passive MIDI import-safety coverage.
- [x] Run focused CLI expectations and update deterministic help fixture drift:
  - `python -m pytest tests/test_cli.py tests/test_cli_coverage.py -n 0`
  - `python -m pytest tests/test_live_gui_desktop_view_model_report.py tests/test_real_midi_passive_cli_safety.py tests/test_cli.py tests/test_cli_coverage.py -n 0`

### Task 3: Docs And Operator Notes

**Files:**
- Modify: `README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/STYLE_ANALYSIS.md`

- [x] Add the command to the README command list and live preflight chain.
- [x] Update architecture docs/diagrams so the passive report chain and module count include `live_gui_desktop_view_model.py`.
- [x] Update manual validation and style-analysis docs to explain that view-model packets remain metadata-only and do not launch a GUI, open ports, record/stream/compare audio, or send MIDI.
- [x] Update `docs/STATUS.md` with the local checkpoint.

### Task 4: Verification And PR

**Files:**
- All intended files above.

- [x] Run focused report, CLI, passive-safety, docs/help tests.
- [x] Run architecture, fast, full, package coverage, lint, and mechanical review gates.
- [x] Exact-stage only intended view-model files, excluding unrelated CRLF/parity checkout noise.
- [x] Commit, push, open a non-stacked PR against `modularize-v1.34`, request review, and include this plan in the PR body.

## Closeout Notes

- Plan requirements: the PR body must link this plan and carry the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `CliCommand`, formatter, and shared live-GUI helper boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR commit for this report; because the command is passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, same-process passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
