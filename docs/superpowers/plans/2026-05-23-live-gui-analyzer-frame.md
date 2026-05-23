# Live GUI Analyzer Frame Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive live GUI analyzer-frame report that consumes the analyzer overlay and emits deterministic GUI frame/test-harness metadata.

**Architecture:** The feature lives under `rytm_randomizer/reports/` and composes the live GUI analyzer-overlay packet. It projects overlay meters, threshold markers, capture badges, and disabled controls into ordered frame events and visual assertions while embedding the upstream overlay/render-tree payload.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand` lazy registration, existing live GUI analyzer-overlay report composition, pytest fast tests, repo architecture and review gates.

---

## Workstreams

- [x] Add behavior tests first for ordered frame events, visual assertions, frame status, JSON/text formatting, parser validation, CLI dispatch, passive CLI safety, help text, and README freshness.
- [x] Add `rytm_randomizer/reports/live_gui_analyzer_frame.py` with frozen dataclasses, deterministic frame ids, overlay composition, JSON/text formatting, CLI command registration, replay commands, and passive safety lines.
- [x] Expose a public analyzer-overlay CLI parser wrapper so downstream report commands can reuse the upstream argument contract without duplicating parsing logic.
- [x] Wire the command into `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`.
- [x] Update passive CLI safety tests, CLI coverage tests, CLI help fixture, README, architecture docs/diagrams, manual validation, style-analysis docs, and status notes.
- [x] Run focused tests, architecture tests, fast/full tests, coverage, lint, and review gates.
- [x] PR #94 has landed; this work was recreated from `origin/modularize-v1.34`, bundled into PR #95, rerun through the local gates, pushed as a non-stacked PR, review requested, and this plan is linked from the PR body.

## Behavior Contract

- The report requires exactly one reference source: `--description`, `--audio`, or `--library`.
- The report requires exactly one captured evidence source: `--capture-description`, `--capture-audio`, or `--capture-library`.
- The report requires at least one saved-kit source path through the upstream overlay/render reports.
- The frame status mirrors the overlay status: `ready`, `review-needed`, or `blocked`.
- Frame events are ordered and deterministic: overlay mount, meter paint events, threshold marker paint events, selected capture badge paint, and disabled-control locks.
- Visual assertions mirror the events so a future GUI test harness can verify meter status, threshold-marker state, capture-badge state, and disabled-control locks without reading report internals.
- Path options are read-only inputs. The command may read supplied evidence or saved-kit paths through upstream passive reports, but it never writes files, records audio, launches a GUI, renders frames, opens ports, sends MIDI, or mutates hardware.
- JSON embeds the upstream analyzer overlay, render tree, screen contract, and prior passive packets so a future GUI can consume one stable payload.

## Verification Plan

- Red check: `python -m pytest tests/test_live_gui_analyzer_frame_report.py -n 0` must fail before the report module exists.
- Focused: `python -m pytest tests/test_live_gui_analyzer_frame_report.py -n 0`
- Focused coverage: `python -m pytest tests/test_live_gui_analyzer_frame_report.py --cov=rytm_randomizer.reports.live_gui_analyzer_frame --cov-branch --cov-report=term-missing -n 0`
- CLI/passive: `python -m pytest tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture tests/test_cli.py::test_readme_mentions_style_performance_arc_live_gui_analyzer_frame_command -n 0`
- Architecture: `python -m pytest tests/architecture/ -q`
- Fast: `python -m pytest -m fast`
- Full: `python -m pytest`
- Coverage: `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- Lint: `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`
- Review gate: `python scripts\code_review_gate.py --mode cli`

## 18-Gate Closeout Notes

- Gate 1 - Branch coverage on touched files: covered by focused frame coverage and whole-package coverage gates.
- Gate 2 - V1.34 parity fixtures: no parity output changes; full tests keep the byte-frozen parity set green.
- Gate 3 - Lint / format / type clean: ruff, black, and isort are part of closeout.
- Gate 4 - Dead-code purge clean: new code is directly covered by focused tests and exercised by CLI coverage.
- Gate 5 - Documentation update: README, STATUS, STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, ARCHITECTURE, ARCHITECTURE_DIAGRAMS, help text, and CLI fixtures are updated.
- Gate 6 - Type-system hygiene: frozen dataclasses, explicit types, no `Any` escape hatches.
- Gate 7 - Observability adoption: N/A, this report is passive/read-only and performs no hot-path state transition, CC send, or guardrail mutation.
- Gate 8 - Test hygiene: tests reuse repo fixtures and exercise parser, CLI dispatch, JSON/text, frame-event mapping, assertion mapping, replay-command fallback, and edge cases.
- Gate 9 - Module organization hygiene: new behavior stays inside the existing `reports/` subpackage.
- Gate 10 - String-literal dispatch hygiene: no mode/intensity/page mutation dispatch added.
- Gate 11 - Shared fixtures: saved-kit fixtures reuse `tests/conftest.py`.
- Gate 12 - Module-level constants use `Final`: constants in the new report are `Final`.
- Gate 13 - Env vars: no new environment variables.
- Gate 14 - Maintainability review: code review checks abstraction reuse, docs freshness, side effects, replay-command safety, and house style.
- Gate 15 - Learning phase: N/A for this local feature slice; no repo-level learned skill is expected.
- Gate 16 - Execution shape: PR #95 is non-stacked from `origin/modularize-v1.34`; PR #94 has landed and there is no sibling PR dependency.
- Gate 17 - Abstraction reuse and genericization: reuses analyzer overlay, render tree, screen contract, capture review, passive formatter, style analysis, saved-kit fixtures, and `CliCommand`.
- Gate 18 - Architecture-doc and diagram freshness: `ARCHITECTURE.md` and `ARCHITECTURE_DIAGRAMS.md` include the new report/command surface and refreshed module counts.

## Bundle Closeout Addendum

- Plan requirements: PR #95 links this plan and carries the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `data/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR #95 bundle commit(s) for this report chain; because the commands are passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
- Bundle status: PR #94 merged; this work was recreated from `origin/modularize-v1.34`, bundled into PR #95, pushed with exact-path staging, and review was requested.
