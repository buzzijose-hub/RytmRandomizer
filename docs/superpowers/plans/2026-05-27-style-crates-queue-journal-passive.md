# Style Crates, Queue, And Mutation Journal Passive Plan

> Status: in-flight

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:test-driven-development for implementation and
> superpowers:verification-before-completion before closeout. Steps use
> checkbox (`- [ ]`) syntax for tracking.

## Goal

Add a passive MVP for Style Crates, Style Queue, and Mutation Journal so the
operator can inspect curated mutation moves, staged future moves, and saved
mutation accidents without changing any hardware behavior.

## Scope

- Add immutable data records for style crates, crate moves, queued moves,
  future danger modes, and journal entries.
- Add curated default crates:
  - Dark Hypnotic
  - Peak Time
  - Hard Groove
  - Dub Pressure
  - Industrial/Broken
  - Deep Minimal
  - Chaos Fills
  - Transitions
  - Saved Accidents
- Add a passive report and CLI command:
  `python -m rytm_randomizer.cli style-crates-queue-journal-report [--json]`
- Add docs and tests proving the surface is passive, deterministic, and
  future-GUI ready.

## Non-Goals

- No MIDI sends.
- No MIDI port opening.
- No hardware mutation.
- No GUI launch.
- No audio analyzer.
- No queue dispatch.
- No journal persistence writes.
- No V1.34 parity fixture regeneration.

## Workstreams

### Task 1: TDD Data And Report Model

**Files:**

- Create: `tests/test_style_crates_queue_journal.py`
- Create: `rytm_randomizer/data/style_crates.py`
- Create: `rytm_randomizer/reports/style_crates_queue_journal.py`

- [x] Write failing tests for crate keys, move metadata bounds, 12-pad targets,
      queue references, journal replay metadata, immutability, deterministic
      formatting, JSON serialization, CLI parser/handler behavior, and passive
      import safety.
- [x] Run focused tests and confirm the new imports fail before implementation.
- [x] Implement frozen dataclasses, validated default catalog, report builder,
      formatter, JSON converter, and registered CLI command.
- [x] Re-run focused tests and confirm they pass.

### Task 2: CLI And Docs Integration

**Files:**

- Edit: `rytm_randomizer/cli.py`
- Edit: `rytm_randomizer/help_text.py`
- Edit: `tests/test_cli.py`
- Edit: `tests/test_cli_coverage.py`
- Edit: `docs/CLI_REFERENCE.md`
- Edit: `docs/STATUS.md`

- [x] Register the lazy passive CLI command.
- [x] Add help text and usage entries.
- [x] Add subprocess CLI coverage for text, JSON, determinism, and bad args.
- [x] Update operator docs and status.

### Task 3: Verification And PR

- [x] Run focused tests.
- [x] Run architecture tests.
- [x] Run fast and full test suites as feasible.
- [x] Run lint trio.
- [x] Exact-stage only intended files, excluding existing checkout/parity noise.
- [ ] Commit, push, and open a non-stacked PR against `modularize-v1.34`.

## 18-Gate Notes

- Gate 1 coverage: focused tests cover all new data/report behavior and CLI
  edges.
- Gate 2 parity: no V1.34 engine/group/scene output changes.
- Gate 3 source safety: no external sources are read; analyzer future is docs
  only.
- Gate 4 deterministic output: report text and JSON are stable.
- Gate 5 docs: spec, plan, CLI reference, and status docs are updated.
- Gate 6 boundaries: new DTOs are frozen dataclasses.
- Gate 7 side effects: passive report only; stdout/JSON only.
- Gate 8 observability: no logger/trace path because there is no active I/O.
- Gate 9 placement: new work stays under existing `data/` and `reports/`.
- Gate 10 enums/literals: danger modes and queue states use canonical literals
  in the data module.
- Gate 11 shared fixtures: tests use existing CLI/report patterns.
- Gate 12 constants: module constants use `Final`.
- Gate 13 parity fixtures: no capture/regeneration.
- Gate 14 passive CLI safety: command is auto-discovered by the passive sweep.
- Gate 15 rollback: revert the passive data/report/docs/test commit.
- Gate 16 cascade: one clean-base PR, not stacked on #135.
- Gate 17 abstraction reuse: reuses existing passive report formatter and style
  catalog patterns.
- Gate 18 docs/diagrams: docs describe the new passive surface; no runtime
  architecture diagram is required for this small catalog/report slice.

## Done Criteria

- Focused tests pass.
- CLI command prints deterministic text and JSON.
- Passive safety sweep covers the command.
- Architecture and lint gates pass.
- PR remains one passive, non-stacked feature slice.
