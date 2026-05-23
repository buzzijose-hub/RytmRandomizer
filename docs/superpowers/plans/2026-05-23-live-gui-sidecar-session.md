# Live GUI Sidecar Session Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Keep the work passive/mock-safe, exact-stage only intended files, and do not open stacked PRs.

**Goal:** Add one passive sidecar session packet that composes the live GUI capture review into the single JSON/text contract a future desktop sidecar can consume during rehearsal.

**Architecture:** The feature lives under `rytm_randomizer/reports/` and composes the already-merged live GUI capture-review report. It produces a deterministic current sidecar state: selected arc, cue state, machine/analyzer/capture panels, capture decision rows, disabled active controls, replay commands, and safety rails. It remains report-only: no GUI runtime, no audio recording, no file writing, no MIDI rendering, no port opening, and no hardware sends.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand` lazy registration, existing style-analysis FeatureReport extraction helpers, pytest fast tests, repo architecture and review gates.

---

## Workstreams

- [x] Add failing focused tests for sidecar packet composition, JSON/text formatting, go/repeat/hold status mapping, CLI dispatch, parser errors, help text, passive CLI safety, README freshness, and docs references.
- [x] Add `rytm_randomizer/reports/live_gui_sidecar_session.py` with frozen dataclasses, deterministic ids, capture-review composition, JSON/text formatting, CLI command registration, and replay commands.
- [x] Wire the command into `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`.
- [x] Update passive CLI safety lists, CLI coverage tests, CLI help fixture, README, style-analysis docs, manual validation notes, architecture docs/diagrams, and status notes.
- [x] Run focused tests, architecture tests, fast/full tests, coverage, lint, and repo review gate.
- [ ] Exact-stage only intended files, commit, push, open a non-stacked PR, request review, and update the monitor automation.

## Behavior Contract

- The report requires exactly one reference source: `--description`, `--audio`, or `--library`.
- The report requires exactly one captured evidence source: `--capture-description`, `--capture-audio`, or `--capture-library`.
- The report requires at least one saved-kit source path so the sidecar session remains tied to the Rytm/A4 snapshot workflow.
- The sidecar status maps capture-review decisions to GUI language: `ready` for go, `needs-repeat` for repeat, and `hold` for blocked evidence.
- JSON embeds the upstream capture review and previous passive packets so a future GUI can consume one stable payload.
- Every active control is disabled in this slice; the packet can describe future buttons, but it cannot arm, record, mutate, write files, open ports, or send MIDI.

## Verification Plan

- Focused: `python -m pytest tests/test_live_gui_sidecar_session_report.py -n 0`
- CLI/passive: `python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0`
- Architecture: `python -m pytest tests/architecture/ -q`
- Fast: `python -m pytest -m fast`
- Full: `python -m pytest`
- Coverage: `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- Lint: `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`
- Review gate: `python scripts\code_review_gate.py --mode cli`

## 18-Gate Closeout Notes

- Gate 1 - Branch coverage on touched files: covered by focused sidecar-session coverage and whole-package coverage gates.
- Gate 2 - V1.34 parity fixtures: no parity output changes; review gate runs the byte-frozen parity set.
- Gate 3 - Lint / format / type clean: ruff, black, and isort are part of closeout.
- Gate 4 - Dead-code purge clean: new code is covered by focused tests and lint.
- Gate 5 - Documentation update: README, STATUS, STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, help text, CLI fixture, ARCHITECTURE, and diagrams are updated.
- Gate 6 - Type-system hygiene: frozen dataclasses, explicit types, no `Any` escape hatches.
- Gate 7 - Observability adoption: N/A, this report is passive/read-only and performs no hot-path state transition, CC send, or guardrail mutation.
- Gate 8 - Test hygiene: tests use repo fixtures and exercise parser, CLI dispatch, JSON/text, and edge cases.
- Gate 9 - Module organization hygiene: new behavior stays inside the existing `reports/` subpackage.
- Gate 10 - String-literal dispatch hygiene: no mode/intensity/page mutation dispatch added.
- Gate 11 - Shared test fixtures: saved-kit fixtures reuse `tests/conftest.py`.
- Gate 12 - Module-level constants use `Final`: constants in the new report are `Final`.
- Gate 13 - Env vars: no new environment variables.
- Gate 14 - Maintainability review: code review checks abstraction reuse, docs freshness, side effects, and house style.
- Gate 15 - Learning phase: N/A for this single feature slice; no repo-level learned skill was discovered.
- Gate 16 - Execution shape: non-stacked PR from `origin/modularize-v1.34`; no sibling PR dependency.
- Gate 17 - Abstraction reuse and genericization: reuses capture review, capture queue, analyzer targets, passive formatter, style analysis, and `CliCommand`.
- Gate 18 - Architecture-doc and diagram freshness: `ARCHITECTURE.md` and `ARCHITECTURE_DIAGRAMS.md` include the new report/command surface.
