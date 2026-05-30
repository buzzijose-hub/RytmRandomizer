# Live Stage Rehearsal State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a passive `style-performance-arc-stage-rehearsal-state-report` command that turns stage-routing route cards into show-facing rehearsal state for Rytm plus Analog Four.

**Architecture:** Add one report module under `rytm_randomizer/reports/` that composes the existing stage snapshot-routing report. The feature remains passive/read-only: it does not open MIDI ports, send MIDI, execute commands, or mutate hardware.

**Tech Stack:** Python frozen dataclasses, existing `CliCommand` registry, existing passive report formatter, existing style-analysis `FeatureReport` contract, pytest, coverage, ruff, black, isort, vulture, and architecture gates.

---

## Why

Jose needs the live-performance planning layer to answer the practical show question: which cues are ready, which cues need rehearsal, and which cues must stay blocked before any armed hardware path is used. Stage-routing already exposes saved-kit slots, fingerprints, planned pads/tracks, mock rows, and deferred rows. This slice wraps those route cards into operator decisions and machine states that a future GUI/audio-analyzer can display without touching hardware.

## Scope

- Create `rytm_randomizer/reports/live_stage_rehearsal_state.py`
  - Builds `StylePerformanceArcStageRehearsalStateReport`.
  - Accepts direct arc, text description, injected `FeatureReport`, audio path, or library path.
  - Reuses `build_style_performance_arc_stage_snapshot_routing_report`.
  - Exposes cue-level go/rehearse/do-not-arm state.
  - Exposes aggregate and cue-level Rytm/A4 machine states.
  - Emits rehearsal steps, operator prompts, capped event previews, deterministic text, and deterministic JSON.
  - Registers `style-performance-arc-stage-rehearsal-state-report`.
- Wire the passive CLI lazy command map and command help.
- Update README, manual hardware validation, status, style analysis docs, CLI help fixture, architecture docs, and passive CLI safety coverage.
- Do not add active MIDI behavior, hardware I/O, or a new device strategy.

## TDD Tasks

- [x] Write RED tests for rehearsal-state building, text output, JSON output, reference matching, scope edges, parser/handler behavior, help dispatch, docs, and passive CLI safety.
- [x] Implement the passive report module by composing the existing stage routing report.
- [x] Wire CLI/help/docs and update the top-level help fixture.
- [x] Add edge coverage for injected analyzer `FeatureReport`, audio/library source paths, event limit behavior, and go/rehearse/do-not-arm state inference.
- [x] Run focused tests for all touched behavior.
- [x] Run architecture, fast/full, coverage, lint, vulture, and review gates before commit.
- [x] Exact-stage only intended files, commit, push, open PR, and request review automatically.

## Plan-Requirements Conformance

- [x] **Gate 1** - 100% branch coverage on touched files; the new report module is tested through focused API, formatter, JSON, parser, handler, and CLI paths, and project coverage remains above the ratchet.
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
- [x] **Gate 14** - Maintainability review completed with sidecar code-review agents; the feature composes existing stage-routing/live-runbook/cue-sheet abstractions.
- [x] **Gate 15** - Learning capture not needed; no new reusable process lesson or rule change was discovered.
- [x] **Gate 16** - Execution shape is one clean-base feature PR against `modularize-v1.34`, not a stacked PR.
- [x] **Gate 17** - Abstraction reuse confirmed: existing passive report formatter, CLI registry, style reference matching, live runbook, cue sheet, saved-kit selection, mock-preview structures, and stage-routing route cards are reused.
- [x] **Gate 18** - Architecture docs refreshed for the new style-performance stage-rehearsal-state report surface.

## Strict Rules Confirmation

- [x] **No hardware in tests** - no test opens a real MIDI port or mutates a connected device.
- [x] **Lazy MIDI imports** - no new top-level `mido` or `python-rtmidi` imports.
- [x] **Hardware-pinned packages** - `mido==1.3.3` and `python-rtmidi==1.5.8` are unchanged.
- [x] **Passive default** - `python -m rytm_randomizer.cli` remains passive and the new command is covered by passive CLI safety tests.
- [x] **No stacked PRs** - the branch targets `modularize-v1.34`.
- [x] **No `--no-verify`** - hooks/checks are not bypassed.
