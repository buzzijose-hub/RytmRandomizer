# Rytm Style Mutation Intent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Rytm style mutation-intent report that turns a captured kit snapshot, style target, and reference/discovery amount into per-pad zone/parameter intent rows without rendering MIDI or touching hardware.

**Architecture:** Reuse the existing `plan_rytm_style_snapshot_routes()` output as the compatibility gate. Add one pure strategy module under `rytm_randomizer/devices/strategies/` that maps ready pads and favored zones to profile-safe parameters, then add one passive report/CLI module under `rytm_randomizer/reports/`. Keep this as planning metadata only: no `guarded_send`, no message renderer, no real MIDI boundary, and no V1.34 parity fixture changes.

**Tech Stack:** Existing data layer, Rytm Device Strategy modules, passive CLI registry/help, JSON report payloads, pytest, architecture tests, vulture, and repo review gates.

---

## Scope

This slice answers: "If I snapshot my Rytm kit and ask for Birmingham pressure at discovery 75, what pads and parameter zones is the software intending to push?"

It does not generate final CC values. It does not choose new machines beyond the existing style-routing candidates. It does not send MIDI. It gives the next runtime slice a concrete, tested contract for style-aware parameter selection.

## File Structure

- Create `rytm_randomizer/devices/strategies/analog_rytm_style_mutation_intent.py`: frozen intent dataclasses, zone-to-parameter matching, and `plan_rytm_style_mutation_intent()`.
- Modify `rytm_randomizer/devices/strategies/__init__.py`: export the new dataclasses and planner.
- Create `rytm_randomizer/reports/rytm_style_mutation_intent.py`: passive text/JSON report, CLI parser, and command registration.
- Modify `rytm_randomizer/cli.py`: lazy-register `rytm-style-mutation-intent-report`.
- Modify `rytm_randomizer/help_text.py` and `tests/fixtures/cli_help_expected.txt`: expose the new passive command.
- Modify `tests/test_rytm_style_snapshot_routing.py` or create `tests/test_rytm_style_mutation_intent.py`: cover the strategy and report behavior.
- Modify `tests/test_cli.py`: cover subprocess help/command/json behavior.
- Modify `README.md`, `docs/STATUS.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document the passive command.

## Tasks

### Task 1: Red Tests

- [x] Add tests proving a ready Rytm snapshot plus `birmingham_pressure` emits intent rows for ready pads only, includes discovery amount/band/depth label, and maps favored zones to concrete profile parameters.
- [x] Add tests proving selectable-only or candidate-only pads appear as blocked and produce no parameter intent rows.
- [x] Add tests for text and JSON report output.
- [x] Add CLI parser tests for `<syx-path> <style-key> [--slot N] [--discovery N] [--json]`, including bad style/discovery input.
- [x] Add help/subprocess tests so the command remains passive and discoverable.
- [x] Run focused tests and verify they fail because the new module/command does not exist yet.

### Task 2: Implementation

- [x] Add `RytmStyleMutationIntentRow`, `RytmStyleMutationPadIntent`, and `RytmStyleMutationIntentPlan` frozen dataclasses.
- [x] Add a deterministic zone-to-parameter matcher that maps:
  - `body` -> `SRC Tune`, `SRC Decay`, `SRC Hold`, `AMP Decay`
  - `amp` -> `AMP Attack`, `AMP Hold`, `AMP Decay`, `AMP Overdrive`
  - `filter` -> `FLT Frequency`, `FLT Resonance`, `FLT Env Depth`, `FLT Decay`
  - `grit` -> `AMP Overdrive`, `SRC Snap`, `SRC Transient`, `SRC Noise Level`, `SRC Impact`
  - `lfo` -> `LFO Speed`, `LFO Depth`, `LFO Fade`, `LFO Destination`
  - `morph` -> `SRC Balance`, `SRC Detune`, `SRC Osc 1 Wave`, `SRC Osc 2 Wave`
- [x] Build intent rows from each ready pad's resolved `profile_key` and the profile `safe` table.
- [x] Add text/JSON report output with passive safety lines.
- [x] Wire the CLI lazy registry/help.
- [x] Update docs/status/PR body.

### Task 3: Verification

- [x] Run focused mutation-intent/report/CLI tests with `-n 0`.
- [x] Run focused coverage on the new strategy/report modules.
- [x] Run vulture on touched files.
- [x] Run `python -m pytest tests/architecture/ -q`.
- [x] Run ruff, black check, and isort check.
- [x] Run `python -m pytest -m fast`.
- [x] Run `python -m pytest`.
- [x] Run full coverage.
- [x] Run `python scripts/code_review_gate.py --mode cli`.
- [ ] Commit locally only; do not push/open a stacked PR while PR #56 remains open.

## Plan-Requirements Conformance

- [x] Gate 1 - target 100% branch coverage on new strategy/report files.
- [x] Gate 2 - V1.34 parity unchanged; review gate runs parity.
- [x] Gate 3 - lint trio required before commit.
- [x] Gate 4 - vulture clean on touched files.
- [x] Gate 5 - README, status, help fixture, architecture diagrams, and PR-body docs updated.
- [x] Gate 6 - frozen dataclasses and explicit types; no `Any`.
- [ ] Gate 7 - N/A: passive planning/report output only, no hot MIDI send path.
- [x] Gate 8 - focused tests cover parser, strategy, text, JSON, and CLI subprocess output.
- [x] Gate 9 - new work stays under existing subpackages.
- [x] Gate 10 - no legacy string-literal mode/intensity dispatch.
- [x] Gate 11 - existing snapshot fixtures reused.
- [x] Gate 12 - module-level constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: parameter intent only, no renderer/sender.
- [ ] Gate 15 - N/A: no new learned skill/rule required.
- [x] Gate 16 - local-only checkpoint while PR #56 is open; no push/stacked PR.
- [x] Gate 17 - reuses existing style routing, data profiles, report formatter, and CLI registry.
- [x] Gate 18 - docs/help updated for changed passive behavior.
