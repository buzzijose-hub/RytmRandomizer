# Live GUI Interaction Script Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI interaction-script report that consumes the analyzer frame and emits deterministic operator action bindings for a future desktop GUI.

**Architecture:** The feature lives under `rytm_randomizer/reports/` and composes the live GUI analyzer-frame packet. It projects frame events, visual assertions, and status into ordered interaction steps, GUI control bindings, disabled hardware/action locks, deterministic JSON, and replay commands without launching a GUI or touching audio/MIDI/hardware.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand` lazy registration, existing live GUI analyzer-frame report composition, pytest fast tests, repo architecture and review gates.

---

## Workstreams

- [x] Add behavior tests first for interaction steps, control bindings, status propagation, JSON/text formatting, parser validation, CLI dispatch, passive CLI safety, help text, and README freshness.
- [x] Expose a public analyzer-frame CLI parser wrapper so downstream report commands can reuse the upstream argument contract without duplicating parsing logic.
- [x] Add `rytm_randomizer/reports/live_gui_interaction_script.py` with frozen dataclasses, deterministic script ids, frame composition, JSON/text formatting, CLI command registration, replay commands, and passive safety lines.
- [x] Wire the command into `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`.
- [x] Update passive CLI safety tests, CLI coverage tests, CLI help fixture, README, architecture docs/diagrams, manual validation, style-analysis docs, and status notes.
- [x] Run focused tests, architecture tests, fast/full tests, coverage, lint, and review gates.
- [ ] After PR #94 and the local GUI packet checkpoints land, rebase or recreate from `origin/modularize-v1.34`, rerun all gates, exact-stage only intended files, push, open a non-stacked PR, request review, and link this plan in the PR body.

## Behavior Contract

- The report requires exactly one reference source and exactly one captured evidence source through the upstream analyzer-frame command contract.
- The report requires at least one saved-kit source path through the upstream frame/overlay/render/screen reports.
- The script status mirrors the analyzer-frame status: `ready`, `review-needed`, or `blocked`.
- Interaction steps are ordered and deterministic: mount frame, inspect analyzer meters, inspect threshold markers, review selected capture, compare reference, and hold disabled hardware actions.
- GUI control bindings expose future desktop controls with deterministic test ids, enabled/disabled state, source pointers, and operator copy.
- Active actions remain blocked: no GUI launch, no GUI event dispatch, no file writing, no audio recording, no audio streaming, no MIDI sending, no port opening, and no hardware mutation.
- JSON embeds the upstream analyzer frame, analyzer overlay, render tree, screen contract, and prior passive packets so a future GUI can consume one stable payload.

## Verification Plan

- Red check: `python -m pytest tests/test_live_gui_interaction_script_report.py -n 0` must fail before the report module exists.
- Focused: `python -m pytest tests/test_live_gui_interaction_script_report.py -n 0`
- Focused coverage: `python -m pytest tests/test_live_gui_interaction_script_report.py --cov=rytm_randomizer.reports.live_gui_interaction_script --cov-branch --cov-report=term-missing -n 0`
- CLI/passive: `python -m pytest tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture tests/test_cli.py::test_readme_mentions_style_performance_arc_live_gui_interaction_script_command -n 0`
- Architecture: `python -m pytest tests/architecture/ -q`
- Fast: `python -m pytest -m fast`
- Full: `python -m pytest`
- Coverage: `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- Lint: `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`
- Review gate: `python scripts\code_review_gate.py --mode cli`

## 18-Gate Closeout Notes

- Gate 1 - Branch coverage on touched files: covered by focused interaction-script coverage and whole-package coverage gates.
- Gate 2 - V1.34 parity fixtures: no parity output changes; full tests keep the byte-frozen parity set green.
- Gate 3 - Lint / format / type clean: ruff, black, and isort are part of closeout.
- Gate 4 - Dead-code purge clean: new code is directly covered by focused tests and exercised by CLI coverage.
- Gate 5 - Documentation update: README, STATUS, STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, ARCHITECTURE, ARCHITECTURE_DIAGRAMS, help text, and CLI fixtures are updated.
- Gate 6 - Type-system hygiene: frozen dataclasses, explicit types, no `Any` escape hatches.
- Gate 7 - Observability adoption: N/A, this report is passive/read-only and performs no hot-path state transition, CC send, or guardrail mutation.
- Gate 8 - Test hygiene: tests reuse repo fixtures and exercise parser, CLI dispatch, JSON/text, interaction-step mapping, control-binding mapping, replay-command fallback, and edge cases.
- Gate 9 - Module organization hygiene: new behavior stays inside the existing `reports/` subpackage.
- Gate 10 - String-literal dispatch hygiene: no mode/intensity/page mutation dispatch added.
- Gate 11 - Shared fixtures: saved-kit fixtures reuse `tests/conftest.py`.
- Gate 12 - Module-level constants use `Final`: constants in the new report are `Final`.
- Gate 13 - Env vars: no new environment variables.
- Gate 14 - Maintainability review: code review checks abstraction reuse, docs freshness, side effects, replay-command safety, and house style.
- Gate 15 - Learning phase: N/A for this local feature slice; no repo-level learned skill is expected.
- Gate 16 - Execution shape: this stays local while PR #94 is open, then becomes a non-stacked PR from `origin/modularize-v1.34`.
- Gate 17 - Abstraction reuse and genericization: reuses analyzer frame, overlay, render tree, screen contract, capture review, passive formatter, style analysis, saved-kit fixtures, and `CliCommand`.
- Gate 18 - Architecture-doc and diagram freshness: `ARCHITECTURE.md` and `ARCHITECTURE_DIAGRAMS.md` include the new report/command surface and refreshed module counts.
