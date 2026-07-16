# Analog Four Audio Patch Genome Implementation Plan

> Status: in-flight
> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:test-driven-development. This plan is structured for one bundled PR with maximum-parallelization sidecar exploration and no stacked PRs, per docs/PLAN_REQUIREMENTS.md Gate 16.

**Goal:** Add a Synplant-inspired audio/description-to-Analog-Four patch genome that produces four A4 patch candidates, a selected candidate DNA sheet, front-panel dial targets, CC/NRPN transport metadata, a learning packet that explains candidate ranking, trait-to-A4 routes, future capture steps, passive initialized-baseline comparison for clean-slate A4 SysEx exports, passive patch-corpus nearest-match ranking for starter or captured A4 audio/patch examples, passive SysEx field calibration facts for Filter1 Frequency, Filter1 Resonance, Filter2 Frequency, and Filter2 Resonance, and live-dial readiness, plus a gated send-plan bridge that can preview or explicitly arm compiler-approved live-dial rows without promoting screen-only destinations.

**Architecture:** Keep A4-specific facts in `rytm_randomizer/data/`, deterministic audio-intelligence translation in `rytm_randomizer/style_analysis/`, passive operator output in focused `rytm_randomizer/reports/` modules registered through `cli_registry`, and active output only in `rytm_randomizer/app.py` behind `--arm` plus a confirmation flag. Screen-only NRPN destination rows remain skipped until their ordinals are captured.

**Tech Stack:** Python 3.11 stdlib, existing `FeatureReport` style-analysis pipeline, existing manual-backed `analog_four_midi.py`, passive CLI registry.

---

## Workstream Graph

| WS | Title | Depends on | Parallel-safe with | Owned files |
|---|---|---|---|---|
| WS-A | A4 display scales + patch-template facts | none | WS-B, WS-C, WS-D | `rytm_randomizer/data/analog_four_display.py`, `rytm_randomizer/data/analog_four_patch_templates.py`, `tests/test_analog_four_display.py`, `rytm_randomizer/data/__init__.py` |
| WS-B | Patch genome compiler | WS-A | WS-C, WS-D | `rytm_randomizer/style_analysis/analog_four_patch_genome.py`, `tests/test_analog_four_patch_genome.py` |
| WS-C | Passive report + CLI | WS-A, WS-B | WS-D | `rytm_randomizer/reports/analog_four_patch_genome.py`, `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py`, `tests/test_analog_four_patch_genome_report.py` |
| WS-D | Docs + status | none | WS-A, WS-B, WS-C | `README.md`, `docs/CLI_REFERENCE.md`, `docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, `docs/STATUS.md`, this plan |
| WS-E | Patch learning + live-dial readiness | WS-A, WS-B | WS-D | `rytm_randomizer/data/analog_four_learning.py`, `rytm_randomizer/style_analysis/analog_four_patch_learning.py`, `rytm_randomizer/reports/analog_four_patch_learning.py`, `tests/test_analog_four_patch_learning*.py` |
| WS-F | Patch send-plan bridge + gated app send | WS-A, WS-B, WS-E | WS-D | `rytm_randomizer/style_analysis/analog_four_patch_send_plan.py`, `rytm_randomizer/reports/analog_four_patch_send_plan.py`, `rytm_randomizer/senders/midi_event_plan.py`, `rytm_randomizer/app.py`, `tests/test_analog_four_patch_send_plan*.py`, `tests/test_app_validate_one_cc.py` |
| WS-G | Patch capture-corpus nearest matching | WS-A, WS-B, WS-E | WS-D | `rytm_randomizer/data/analog_four_patch_corpus.py`, `rytm_randomizer/style_analysis/analog_four_patch_corpus.py`, `rytm_randomizer/reports/analog_four_patch_corpus.py`, `tests/test_analog_four_patch_corpus*.py` |
| WS-H | Initialized SysEx baseline comparison | WS-G | WS-D | `rytm_randomizer/reports/analog_four_baseline.py`, `tests/test_analog_four_baseline_report.py` |
| WS-I | First A4 SysEx field calibration facts | WS-H | WS-D | `rytm_randomizer/data/analog_four_sysex_calibration.py`, `tests/test_analog_four_sysex_calibration.py`, `rytm_randomizer/data/__init__.py` |

## Execution Shape

- **Worktree assignment:** `C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\a4-audio-patch-genome-passive` on branch `codex/a4-audio-patch-genome-passive`.
- **Disjoint ownership:** WS-A and WS-I own `data/`, WS-B owns `style_analysis/`, WS-C owns `reports/` plus CLI/help, WS-D owns docs.
- **Agent crew:** main agent performs TDD/implementation; read-only explorers inspect CLI/report and A4 reuse points in parallel.
- **Self-driving rules:** no human prompts; routine file edits, formatting, docs, tests, and fixes continue automatically.
- **Auto-merge cascade:** not used locally; PR shape is one non-stacked bundled branch.
- **Auto-rebase rules:** if base drift appears, rebase/cherry-pick only this branch's commits and never reset user changes in the original checkout.
- **On-disk state:** PR #206, branch `codex/a4-audio-patch-genome-passive`, this plan document, and the committed test/coverage evidence are the durable recovery state; no long-running monitor or external state file is required.
- **Kickoff trigger:** user requested autonomous continuation on 2026-07-03.
- **Termination condition:** tests and docs pass locally as far as feasible; final response lists changed files, verification, and residual hardware-validation limits.
- **Hard time budget:** no wall-clock budgeted automation is running; this is a finite PR update that stops after local gates, push, and PR status checks.
- **Recovery procedure:** read this plan, run `git status --short --branch`, inspect PR #206, then rerun the focused A4 patch tests before continuing after compaction.
- **Permission profile:** local file edits and passive tests only; refuse force-push, hardware pin bumps, parity capture, and unarmed real-MIDI sends.
- **Stop signals:** a user "stop/wait" message pauses; otherwise continue.

## Implementation Tasks

1. Add failing tests for bipolar A4 screen values, enum/front-panel labels, and CC/NRPN metadata.
2. Add failing tests for a deterministic four-candidate patch genome from a synthetic `FeatureReport`.
3. Add failing tests for text/JSON report output and passive CLI handling.
4. Implement the display scale data and helpers.
5. Implement the style-analysis patch genome compiler using `FeatureReport` and the existing `build_reference_style_blueprint` trait surface.
6. Implement the passive report module and lazy CLI registration.
7. Implement the passive patch-learning packet/report with candidate scoring, trait routing, capture matrix, and live-dial readiness.
8. Implement the passive send-plan compiler/report and gated app dry-run/armed send bridge.
9. Implement the passive capture-corpus nearest-match compiler/report with synthetic starter rows and optional captured corpus file input.
10. Implement the passive initialized-baseline report for Jose's Test 1 kit, pattern+kit, and whole-project SysEx exports.
11. Promote passive A4 SysEx field calibration facts from Jose's Filter1 Frequency, Filter1 Resonance, Filter2 Frequency, and Filter2 Resonance captures.
12. Update operator docs and architecture/status references.
13. Run focused tests, then fast/architecture/lint verification as feasible.

## Safety Contract

- Passive CLI reports open no MIDI ports and send no MIDI.
- App dry-run sends only to the in-memory mock sender.
- App armed send requires `--arm --a4-patch-send-plan --confirm-a4-patch-send-plan`.
- No SysEx writing.
- No parity fixture regeneration.
- CC-ready rows are explicit `0..127` values.
- NRPN-only enum/destination rows are represented honestly as front-panel/manual rows unless the manual-backed ordinal is known.
- Screen-only destination rows are skipped by the active send-plan bridge.
- Patch learning is explanatory and deterministic; it does not claim a trained model or hardware-captured A4 state until future capture data exists.
- Patch corpus matching labels synthetic starter rows separately from captured hardware rows; it does not claim trained model status or hardware-backed certainty until real A4 recordings are supplied and validated.
- Initialized-baseline comparison reads local SysEx exports and fingerprints supported saved-kit payloads only; it does not write SysEx, mutate hardware, send MIDI, or claim parameter-level A4 DNA extraction while saved-kit offsets remain candidate-only.
- SysEx calibration facts are data-only evidence from operator-supplied exports; they do not write SysEx, mutate hardware, send MIDI, or claim a complete A4 kit writer until more fields are captured and validated.

## Plan-Requirements Conformance

Per docs/PLAN_REQUIREMENTS.md, this plan commits to:

- [x] Gate 1 (100% branch coverage on touched files) -- focused tests cover new behavior; coverage command will be run if feasible.
- [x] Gate 2 (V1.34 parity byte-identical) -- no V1.34 engine/golden paths touched.
- [x] Gate 3 (lint/format/type clean) -- ruff/black/isort run before closeout as feasible.
- [x] Gate 4 (dead-code purge) -- no unused public surfaces; report and compiler are test-covered.
- [x] Gate 5 (docs updated) -- README, CLI reference, STATUS, ARCHITECTURE, diagrams updated.
- [x] Gate 6 (type-system hygiene) -- frozen dataclasses and explicit types; no `Any` aliases.
- [x] Gate 7 (observability adoption) -- passive reports stay inert; the active send bridge wraps the armed batch in an operation span, records categorized error metrics, and reuses the existing `midi_io` per-message breadcrumbs.
- [x] Gate 8 (test hygiene) -- tests mirror source responsibilities and use real code.
- [x] Gate 9 (module organization) -- new files live under existing `data/`, `style_analysis/`, and `reports/` subpackages.
- [x] Gate 10 (string-literal dispatch hygiene) -- no new mode/page dispatch ladder; CLI uses registry.
- [x] Gate 11 (shared fixtures) -- no duplicated multi-file fixtures.
- [x] Gate 12 (Final constants) -- new constants annotated.
- [x] Gate 13 (env vars) -- no new environment variables.
- [x] Gate 14 (maintainability) -- small focused modules; no oversized report module.
- [x] Gate 15 (learning phase) -- review findings were captured in this plan and PR evidence; no reusable skill extraction is warranted because the patterns are feature-specific A4 patch-template data placement and send-plan observability fixes already covered by existing rules.
- [x] Gate 16 (execution shape) -- one isolated worktree, branch `codex/a4-audio-patch-genome-passive`, one bundled PR (#206) against `modularize-v1.34`, no stacked base branch.
- [x] Gate 17 (abstraction reuse) -- reuses A4 MIDI data, `FeatureReport`, blueprint traits, report formatter, CLI registry, and passive SysEx evidence/fingerprint conventions.
- [x] Gate 18 (architecture freshness) -- architecture docs/diagrams updated for the new passive reports, style-analysis surfaces, and gated app send bridge.
