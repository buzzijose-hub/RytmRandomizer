# Analog Four Audio Patch Genome Implementation Plan

> Status: in-flight
> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:test-driven-development. This plan is structured for one bundled PR with maximum-parallelization sidecar exploration and no stacked PRs, per docs/PLAN_REQUIREMENTS.md Gate 16.

**Goal:** Add a passive Synplant-inspired audio/description-to-Analog-Four patch genome that produces four A4 patch candidates, a selected candidate DNA sheet, front-panel dial targets, and CC/NRPN transport metadata without opening MIDI ports or mutating hardware.

**Architecture:** Keep A4-specific facts in `rytm_randomizer/data/`, deterministic audio-intelligence translation in `rytm_randomizer/style_analysis/`, and operator output in a focused `rytm_randomizer/reports/` module registered through `cli_registry`. The live-dial-in path remains a future promotion step: this PR emits manual/CC/NRPN-ready rows and never routes NRPN-only rows through the existing CC-only A4 renderer.

**Tech Stack:** Python 3.11 stdlib, existing `FeatureReport` style-analysis pipeline, existing manual-backed `analog_four_midi.py`, passive CLI registry.

---

## Workstream Graph

| WS | Title | Depends on | Parallel-safe with | Owned files |
|---|---|---|---|---|
| WS-A | A4 display scales | none | WS-B, WS-C, WS-D | `rytm_randomizer/data/analog_four_display.py`, `tests/test_analog_four_display.py`, `rytm_randomizer/data/__init__.py` |
| WS-B | Patch genome compiler | WS-A | WS-C, WS-D | `rytm_randomizer/style_analysis/analog_four_patch_genome.py`, `rytm_randomizer/style_analysis/__init__.py`, `tests/test_analog_four_patch_genome.py` |
| WS-C | Passive report + CLI | WS-A, WS-B | WS-D | `rytm_randomizer/reports/analog_four_patch_genome.py`, `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py`, `tests/test_analog_four_patch_genome_report.py` |
| WS-D | Docs + status | none | WS-A, WS-B, WS-C | `README.md`, `docs/CLI_REFERENCE.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/STATUS.md`, this plan |

## Execution Shape

- **Worktree assignment:** `C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\a4-audio-patch-genome` on branch `codex/a4-audio-patch-genome`.
- **Disjoint ownership:** WS-A owns `data/`, WS-B owns `style_analysis/`, WS-C owns `reports/` plus CLI/help, WS-D owns docs.
- **Agent crew:** main agent performs TDD/implementation; read-only explorers inspect CLI/report and A4 reuse points in parallel.
- **Self-driving rules:** no human prompts; routine file edits, formatting, docs, tests, and fixes continue automatically.
- **Auto-merge cascade:** not used locally; PR shape is one non-stacked bundled branch.
- **Auto-rebase rules:** if base drift appears, rebase/cherry-pick only this branch's commits and never reset user changes in the original checkout.
- **On-disk state:** git branch + this plan document are the durable state; no long-running monitor or external state file is required for this single bundled PR.
- **Kickoff trigger:** user requested autonomous continuation on 2026-07-03.
- **Termination condition:** tests and docs pass locally as far as feasible; final response lists changed files, verification, and residual hardware-validation limits.
- **Hard time budget:** current Codex session budget; no background services are left running.
- **Recovery procedure:** read this plan, `git status`, and rerun focused tests before continuing after compaction.
- **Permission profile:** local file edits and passive tests only; refuse force-push, hardware pin bumps, parity capture, and unarmed real-MIDI sends.
- **Stop signals:** a user "stop/wait" message pauses; otherwise continue.

## Implementation Tasks

1. Add failing tests for bipolar A4 screen values, enum/front-panel labels, and CC/NRPN metadata.
2. Add failing tests for a deterministic four-candidate patch genome from a synthetic `FeatureReport`.
3. Add failing tests for text/JSON report output and passive CLI handling.
4. Implement the display scale data and helpers.
5. Implement the style-analysis patch genome compiler using `FeatureReport` and the existing `build_reference_style_blueprint` trait surface.
6. Implement the passive report module and lazy CLI registration.
7. Update operator docs and architecture/status references.
8. Run focused tests, then fast/architecture/lint verification as feasible.

## Safety Contract

- Passive report only.
- No MIDI port opening.
- No MIDI sending.
- No SysEx writing.
- No parity fixture regeneration.
- CC-ready rows are explicit `0..127` values.
- NRPN-only enum/destination rows are represented honestly as front-panel/manual rows unless the manual-backed ordinal is known.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) -- focused tests cover new behavior; coverage command will be run if feasible.
- [x] Gate 2 (V1.34 parity byte-identical) -- no V1.34 engine/golden paths touched.
- [x] Gate 3 (lint/format/type clean) -- ruff/black/isort run before closeout as feasible.
- [x] Gate 4 (dead-code purge) -- no unused public surfaces; report and compiler are test-covered.
- [x] Gate 5 (docs updated) -- README, CLI reference, STATUS, ARCHITECTURE, diagrams updated.
- [x] Gate 6 (type-system hygiene) -- frozen dataclasses and explicit types; no `Any` aliases.
- [x] Gate 7 (observability adoption) -- no hot send/state-transition path; report is passive rendering.
- [x] Gate 8 (test hygiene) -- tests mirror source responsibilities and use real code.
- [x] Gate 9 (module organization) -- new files live under existing `data/`, `style_analysis/`, and `reports/` subpackages.
- [x] Gate 10 (string-literal dispatch hygiene) -- no new mode/page dispatch ladder; CLI uses registry.
- [x] Gate 11 (shared fixtures) -- no duplicated multi-file fixtures.
- [x] Gate 12 (Final constants) -- new constants annotated.
- [x] Gate 13 (env vars) -- no new environment variables.
- [x] Gate 14 (maintainability) -- small focused modules; no oversized report module.
- [x] Gate 15 (learning phase) -- no new reusable skill needed unless verification surfaces a repeatable pattern.
- [x] Gate 16 (execution shape) -- one isolated branch, one bundled PR, no human gate.
- [x] Gate 17 (abstraction reuse) -- reuses A4 MIDI data, `FeatureReport`, blueprint traits, report formatter, and CLI registry.
- [x] Gate 18 (architecture freshness) -- architecture docs/diagrams updated for the new passive report + style-analysis surface.
