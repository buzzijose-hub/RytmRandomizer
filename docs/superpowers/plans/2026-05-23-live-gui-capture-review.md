# Live GUI Capture Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` or `superpowers:executing-plans` to implement this plan task-by-task. Keep the work passive/mock-safe, exact-stage only intended files, and do not open stacked PRs.

**Goal:** Add a passive live GUI capture-review report that consumes the existing live GUI capture queue plus one captured FeatureReport and turns the operator's rehearsal evidence into deterministic `go`, `repeat`, or `hold` decisions.

**Architecture:** The feature lives in `rytm_randomizer/reports/` as another passive report in the style-performance arc chain. It reuses the existing capture queue and GUI rehearsal session packets, extracts or accepts a captured FeatureReport, compares it against the queued analyzer target, and emits operator-only review decisions. It does not touch hardware, open MIDI ports, record audio, write files, or mutate kits.

**Tech Stack:** Python 3.11, frozen dataclasses, `CliCommand` lazy registration, existing style-analysis FeatureReport extraction helpers, pytest fast tests, repo architecture and review gates.

---

## Workstreams

- [x] Add behavior tests first for `go`, `repeat`, `hold`, JSON/text formatting, parser validation, CLI dispatch, and passive safety registration.
- [x] Add `rytm_randomizer/reports/live_gui_capture_review.py` with frozen dataclasses, deterministic ids, metric comparisons, JSON/text formatting, and CLI command registration.
- [x] Wire the command into `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`.
- [x] Update passive CLI safety tests, CLI coverage tests, README, style-analysis docs, manual hardware validation notes, architecture diagrams, and status notes.
- [x] Run focused tests, architecture tests, fast/full tests, coverage, lint, and repo review gate.
- [x] Exact-stage only intended files, commit, push, open a non-stacked PR, request review, and update the monitor automation.

## Behavior Contract

- The report requires exactly one reference source: `--description`, `--audio`, or `--library`.
- The report requires exactly one captured evidence source: `--capture-description`, `--capture-audio`, or `--capture-library`.
- The report requires at least one saved-kit source path so the review stays tied to the Rytm/A4 snapshot workflow.
- `go` means the measured capture is inside guidance and can be used as the operator's rehearsal reference. It never arms hardware.
- `repeat` means the capture is close enough to keep rehearsing, but one or more metrics are outside preferred guidance.
- `hold` means the slot is not ready, the requested slot is invalid, tempo/energy evidence is missing, or a blocker must be resolved before trusting the capture.
- JSON embeds the upstream capture queue and previous passive packets so future GUI/audio-analyzer work can consume one stable payload.

## Verification Plan

- Focused: `python -m pytest tests/test_live_gui_capture_review_report.py -n 0`
- CLI/passive: `python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0`
- Architecture: `python -m pytest tests/architecture/ -q`
- Fast: `python -m pytest -m fast`
- Full: `python -m pytest`
- Coverage: `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`
- Lint: `python -m ruff check . && python -m black --check --target-version=py311 . && python -m isort --profile black --check-only .`
- Review gate: `python scripts\code_review_gate.py --mode cli` (local fallback because `just` is unavailable in this shell)

## 18-Gate Closeout Notes

- Gate 1 - Branch coverage on touched files: covered by focused capture-review coverage and whole-package coverage gates.
- Gate 2 - V1.34 parity fixtures: no parity output changes; review gate runs the byte-frozen parity set.
- Gate 3 - Lint / format / type clean: ruff, black, and isort are part of closeout.
- Gate 4 - Dead-code purge clean: vulture runs against the new report/test slice.
- Gate 5 - Documentation update: README, STATUS, STYLE_ANALYSIS, MANUAL_HARDWARE_VALIDATION, help text, and CLI fixtures are updated.
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
- Gate 17 - Abstraction reuse and genericization: reuses capture queue, analyzer targets, passive formatter, style analysis, and `CliCommand`.
- Gate 18 - Architecture-doc and diagram freshness: `ARCHITECTURE.md` and `ARCHITECTURE_DIAGRAMS.md` include the new report/command surface.

## Bundle Closeout Addendum

- Plan requirements: PR #95 links this plan and carries the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `data/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR #95 bundle commit(s) for this report chain; because the commands are passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
- Bundle status: PR #94 merged; this work was recreated from `origin/modularize-v1.34`, bundled into PR #95, pushed with exact-path staging, and review was requested.
