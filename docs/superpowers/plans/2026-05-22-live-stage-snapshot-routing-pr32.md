# Live Stage Snapshot Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a passive `style-performance-arc-stage-routing-report` command that turns a selected live runbook into show-facing snapshot route cards for Rytm plus Analog Four.

**Architecture:** Add one report module under `rytm_randomizer/reports/` that composes the existing live runbook, cue sheet, style reference matching, saved-kit snapshot selection, and mock-preview layers. The feature remains passive/read-only: it does not open MIDI ports, send MIDI, execute commands, or mutate hardware.

**Tech Stack:** Python frozen dataclasses, existing `CliCommand` registry, existing passive report formatter, existing style-analysis `FeatureReport` contract, pytest, coverage, ruff, black, isort, vulture, and architecture gates.

---

## Why

Jose needs a practical live-show bridge between the intelligence layer and what happens on stage. The existing reports can choose style arcs, create cue sheets, and build runbooks, but they do not yet show a cue-by-cue "what snapshot and machine lane will this touch?" card. This feature gives the performer a readable and JSON-ready stage routing packet before any armed hardware work begins.

## Scope

- Create `rytm_randomizer/reports/live_stage_snapshot_routing.py`
  - Builds `StylePerformanceArcStageSnapshotRoutingReport`.
  - Builds one route card per live cue.
  - Carries Rytm slot, kit name, payload fingerprint, planned pads, and mock row counts.
  - Carries Analog Four slot, kit name, payload fingerprint, planned tracks, mock row counts, and deferred/candidate row counts.
  - Accepts direct arc, text description, injected `FeatureReport`, audio path, or library path.
  - Emits deterministic text and JSON.
  - Registers `style-performance-arc-stage-routing-report`.
- Wire the passive CLI lazy command map and command help.
- Update README, manual hardware validation, status, style analysis docs, CLI help fixture, and passive CLI safety coverage.
- Do not add active MIDI behavior, hardware I/O, or a new device strategy.

## TDD Tasks

- [x] Write RED tests for route-card building, text output, JSON output, reference matching, scope edges, parser/handler behavior, help dispatch, and passive CLI safety.
- [x] Implement the passive report module by composing the existing live runbook.
- [x] Wire CLI/help/docs and update the top-level help fixture.
- [x] Add edge coverage for injected analyzer `FeatureReport`, audio/library source commands, deferred/blocker summaries, no-event cards, event limit behavior, and route-status inference.
- [x] Run focused tests for all touched behavior.
- [x] Run architecture, fast/full, coverage, lint, vulture, and review gates before commit.
- [x] Exact-stage only intended files, commit, push, open PR, and request review automatically.

## Plan-Requirements Conformance

- [x] **Gate 1** - 100% branch coverage on touched files; the new report module is tested at 100% statement/branch coverage and project coverage remains above the ratchet.
- [x] **Gate 2** - V1.34 parity remains byte-identical; this passive report does not alter engines, `group_runner`, `scene_runner`, or parity fixtures.
- [x] **Gate 3** - Lint clean with ruff, black `--target-version=py311`, and isort `--profile black`.
- [x] **Gate 4** - No new dead code; vulture was run on the touched implementation/test surfaces.
- [x] **Gate 5** - Docs updated in `README.md`, `docs/STATUS.md`, `docs/STYLE_ANALYSIS.md`, `docs/MANUAL_HARDWARE_VALIDATION.md`, `docs/ARCHITECTURE.md`, and `docs/ARCHITECTURE_DIAGRAMS.md`.
- [x] **Gate 6** - Type-system hygiene preserved with frozen dataclasses, `Final` constants, explicit types, and no bare `Any`.
- [x] **Gate 7** - Observability adoption is not required for this cold passive report path; no runtime hot path or hardware send loop was added.
- [x] **Gate 8** - Test hygiene preserved by extending the existing focused style-performance, CLI, safety, and docs tests.
- [x] **Gate 9** - Module organization hygiene preserved; the new code lives under `rytm_randomizer/reports/`.
- [x] **Gate 10** - String-literal dispatch hygiene preserved; CLI routing uses the existing lazy `CliCommand` registry pattern.
- [x] **Gate 11** - Shared fixtures preserved; tests reuse existing helpers and do not introduce duplicate fixture infrastructure.
- [x] **Gate 12** - Module-level constants use `Final`.
- [x] **Gate 13** - No new environment variables were introduced.
- [x] **Gate 14** - Maintainability review completed with sidecar code-review agents; the feature composes existing runbook/cue-sheet/preview abstractions.
- [x] **Gate 15** - Learning capture not needed; no new reusable process lesson or rule change was discovered.
- [x] **Gate 16** - Execution shape is one clean-base feature PR against `modularize-v1.34`, not a stacked PR.
- [x] **Gate 17** - Abstraction reuse confirmed: existing passive report formatter, CLI registry, style reference matching, live runbook, cue sheet, saved-kit selection, and mock-preview structures are reused.
- [x] **Gate 18** - Architecture docs refreshed for the new style-performance stage-routing report surface.

## Strict Rules Confirmation

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a connected device.
- [x] **Lazy MIDI imports** - no new top-level `mido` or `python-rtmidi` imports.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` are unchanged.
- [x] **Passive default** - `python -m rytm_randomizer.cli` remains passive and the new command is covered by passive CLI safety tests.
- [x] **No stacked PRs** - the branch targets `modularize-v1.34`.
- [x] **No `--no-verify`** - hooks/checks are not bypassed.
