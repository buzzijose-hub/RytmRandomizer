# Reference Discovery Slider Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add passive reference/discovery slider semantics to the style snapshot routing reports so future GUI/audio-analyzer consumers can request conservative, balanced, discovery, or wild-discovery planning from the same captured kit snapshot.

**Architecture:** Add one shared discovery policy under `rytm_randomizer/data/`, then pass the bounded `0..100` amount through the existing Rytm, Analog Four, and dual-machine style routing planners. Keep the slice passive/read-only: no MIDI sends, no renderer changes, no real ports, and no V1.34 parity fixture changes.

**Tech Stack:** Existing data layer, Device Strategy routing modules, passive CLI registry/report modules, stdlib JSON, pytest, architecture gates, and review gate.

---

## Scope

This slice gives the reports the slider brain Jose described:

- `0-20`: reference mode, preserve the current kit identity and expose fewer zones.
- `21-60`: balanced mode, keep the live snapshot identity while allowing moderate zone movement.
- `61-85`: discovery mode, show broader legal candidates and stronger zone movement.
- `86-100`: wild discovery mode, maximum passive planning pressure while still obeying pad/track compatibility.

The output remains a preview only. It does not render parameter deltas or touch hardware.

## File Structure

- Create `rytm_randomizer/data/style_discovery.py`: shared frozen policy records, constants, and the `style_discovery_policy()` lookup.
- Modify `rytm_randomizer/data/__init__.py`: re-export uppercase policy constants only.
- Modify `tests/test_data_layer.py`: pin the slider bands and default amount.
- Modify `rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py`: accept `discovery_amount`, store the policy fields on plans, and scale favored zones/candidate limits.
- Modify `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`: accept the same policy and expose it on track/plan output.
- Modify `rytm_randomizer/reports/{rytm_style_snapshot_routing,analog_four_style_snapshot_routing,dual_machine_style_snapshot_routing}.py`: add `--discovery N`, text fields, and JSON fields.
- Modify `tests/test_rytm_style_snapshot_routing.py`, `tests/test_analog_four_style_snapshot_routing.py`, `tests/test_dual_machine_style_snapshot_routing_report.py`, and `tests/test_cli.py`: cover parser validation, JSON/text output, and CLI subprocess behavior.
- Modify `rytm_randomizer/help_text.py`, `tests/fixtures/cli_help_expected.txt`, `README.md`, `docs/STATUS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document the passive slider surface.

## Tasks

### Task 1: Red Tests

- [x] Add data-layer tests that prove `style_discovery_policy(0)`, `20`, `21`, `60`, `61`, `85`, `86`, and `100` map to the expected bands and reject `-1`/`101`.
- [x] Add Rytm tests that compare `discovery_amount=10` against `discovery_amount=95`: reference mode must reduce the favored-zone/candidate surface and mark machine switching as unavailable; wild discovery must widen the surface and allow compatible machine switching.
- [x] Add Analog Four tests that expose the same discovery amount/band on plan tracks.
- [x] Add report/CLI tests for `--discovery N`, JSON fields, text fields, and bad input.
- [x] Run the focused test command and verify the failures are the expected missing-policy/missing-argument failures.

### Task 2: Implementation

- [x] Add the shared `style_discovery.py` policy module with frozen records and explicit typed constants.
- [x] Thread `discovery_amount` through Rytm, Analog Four, and dual-machine route planning.
- [x] Add text and JSON report fields for `discovery_amount`, `discovery_band`, and `machine_switching_allowed`.
- [x] Add `--discovery N` parsing to all three passive style-routing report commands.
- [x] Update help, README, status, and PR-body notes.

### Task 3: Verification

- [x] Run focused style-routing/data tests with `-n 0`.
- [x] Run focused coverage on touched report/strategy modules.
- [x] Run vulture on touched style-routing files and tests.
- [x] Run `python -m pytest tests/architecture/ -q`.
- [x] Run ruff, black check, and isort check.
- [x] Run `python -m pytest -m fast`.
- [x] Run `python -m pytest`.
- [x] Run full coverage.
- [x] Run `python scripts/code_review_gate.py --mode cli`.
- [x] Commit locally only; do not push/open a stacked PR while PR #56 remains open.

## Plan-Requirements Conformance

- [x] Gate 1 - target 100% branch coverage on touched report/strategy/data files.
- [x] Gate 2 - V1.34 parity unchanged; review gate runs parity.
- [x] Gate 3 - lint trio required before commit.
- [x] Gate 4 - vulture clean on touched files.
- [x] Gate 5 - README, status, help fixture, and PR-body docs updated.
- [x] Gate 6 - no `Any`; use frozen dataclasses and explicit types.
- [ ] Gate 7 - N/A: passive planning/report output only, no hot MIDI send path.
- [x] Gate 8 - focused tests cover parser, plan, text, JSON, and CLI subprocess output.
- [x] Gate 9 - no new top-level modules.
- [x] Gate 10 - no legacy string-literal mode/intensity dispatch.
- [x] Gate 11 - existing snapshot fixtures reused.
- [x] Gate 12 - module-level constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: slider policy only, no parameter renderer.
- [ ] Gate 15 - N/A: no new learned skill/rule required.
- [x] Gate 16 - local-only checkpoint while PR #56 is open; no push/stacked PR.
- [x] Gate 17 - reuses `data/`, existing Device Strategy planners, report formatter, and CLI registry.
- [x] Gate 18 - docs/help updated for changed passive behavior.
