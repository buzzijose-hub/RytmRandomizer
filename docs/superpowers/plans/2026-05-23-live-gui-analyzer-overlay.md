# Live GUI Analyzer Overlay Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Keep the work passive/mock-safe, exact-stage only intended files, and do not open stacked PRs.

**Goal:** Add a passive live GUI analyzer-overlay report that consumes the live GUI render tree and emits deterministic meter overlays for a future desktop GUI/audio-analyzer surface.

**Architecture:** The feature lives under `rytm_randomizer/reports/` and composes the live GUI render-tree packet. It projects capture-review metric decisions onto render-tree nodes as meter widgets, threshold markers, selected-capture badges, node annotations, blocked active actions, replay commands, and deterministic JSON while embedding the upstream render tree.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand` lazy registration, existing live GUI render-tree report composition, pytest fast tests, repo architecture and review gates.

---

## Workstreams

- [x] Add behavior tests first for meter widget mapping, threshold markers, selected capture badge, node annotations, overlay status, JSON/text formatting, parser validation, CLI dispatch, passive CLI safety, help text, and README freshness.
- [x] Add `rytm_randomizer/reports/live_gui_analyzer_overlay.py` with frozen dataclasses, deterministic overlay ids, render-tree composition, JSON/text formatting, CLI command registration, replay commands, and passive safety lines.
- [x] Expose a public render-tree CLI parser wrapper so downstream report commands can reuse the upstream argument contract without duplicating parsing logic.
- [x] Wire the command into `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`.
- [x] Update passive CLI safety tests, CLI coverage tests, CLI help fixture, README, architecture docs/diagrams, manual validation, style-analysis docs, and status notes.
- [x] Run focused tests, architecture tests, fast/full tests, coverage, lint, and review gates.
- [ ] After PR #94 lands, rebase or recreate from `origin/modularize-v1.34`, rerun all gates, exact-stage only intended files, push, open a non-stacked PR, request review, and link this plan in the PR body.

## Behavior Contract

- The report requires exactly one reference source: `--description`, `--audio`, or `--library`.
- The report requires exactly one captured evidence source: `--capture-description`, `--capture-audio`, or `--capture-library`.
- The report requires at least one saved-kit source path through the upstream screen/render reports.
- The overlay status is `ready` when the selected capture decision is `go`, `review-needed` when it is `repeat`, and `blocked` when it is `hold` or the render tree is held.
- Meter widgets are ordered by the selected capture decision metric order and link to analyzer render nodes when present.
- Threshold markers emit passive pass/warn/hold visual metadata for every meter widget.
- Node annotations map render-tree nodes to analyzer metric, capture decision, and blocked-control meanings so a future GUI can paint overlays without reading report internals.
- Path options are read-only inputs. The command may read supplied evidence or saved-kit paths through upstream passive reports, but it never writes files, records audio, launches a GUI, opens ports, sends MIDI, or mutates hardware.
- JSON embeds the upstream render tree, screen contract, and prior passive packets so a future GUI can consume one stable payload.

## Verification Plan

- Red check: `python -m pytest tests/test_live_gui_analyzer_overlay_report.py -n 0` must fail before the report module exists.
- Focused: `python -m pytest tests/test_live_gui_analyzer_overlay_report.py -n 0`
- CLI/passive: `python -m pytest tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py tests/test_cli.py::test_top_level_help_exits_zero_and_matches_fixture tests/test_cli.py::test_readme_mentions_style_performance_arc_live_gui_analyzer_overlay_command -n 0`
- Architecture: `python -m pytest tests/architecture/ -q`
- Fast: `python -m pytest -m fast`
- Full: `python -m pytest`
- Coverage: `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- Lint: `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`
- Review gate: `python scripts\code_review_gate.py --mode cli`

## 18-Gate Closeout Notes

- Gate 1 - Branch coverage on touched files: covered by focused overlay coverage and whole-package coverage gates.
- Gate 2 - V1.34 parity fixtures: no parity output changes; full tests keep the byte-frozen parity set green.
- Gate 3 - Lint / format / type clean: ruff, black, and isort are part of closeout.
- Gate 4 - Dead-code purge clean: new code is directly covered by focused tests and exercised by CLI coverage.
- Gate 5 - Documentation update: README, STATUS, STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, ARCHITECTURE, ARCHITECTURE_DIAGRAMS, help text, and CLI fixtures are updated.
- Gate 6 - Type-system hygiene: frozen dataclasses, explicit types, no `Any` escape hatches.
- Gate 7 - Observability adoption: N/A, this report is passive/read-only and performs no hot-path state transition, CC send, or guardrail mutation.
- Gate 8 - Test hygiene: tests reuse repo fixtures and exercise parser, CLI dispatch, JSON/text, meter mapping, threshold mapping, node annotations, replay-command fallback, and edge cases.
- Gate 9 - Module organization hygiene: new behavior stays inside the existing `reports/` subpackage.
- Gate 10 - String-literal dispatch hygiene: no mode/intensity/page mutation dispatch added.
- Gate 11 - Shared test fixtures: saved-kit fixtures reuse `tests/conftest.py`.
- Gate 12 - Module-level constants use `Final`: constants in the new report are `Final`.
- Gate 13 - Env vars: no new environment variables.
- Gate 14 - Maintainability review: code review checks abstraction reuse, docs freshness, side effects, replay-command safety, and house style.
- Gate 15 - Learning phase: N/A for this single feature slice; no repo-level learned skill is expected.
- Gate 16 - Execution shape: this stays local while PR #94 is open, then becomes a non-stacked PR from `origin/modularize-v1.34`.
- Gate 17 - Abstraction reuse and genericization: reuses render tree, screen contract, capture review, passive formatter, style analysis, saved-kit fixtures, and `CliCommand`.
- Gate 18 - Architecture-doc and diagram freshness: `ARCHITECTURE.md` and `ARCHITECTURE_DIAGRAMS.md` include the new report/command surface and refreshed module counts.
