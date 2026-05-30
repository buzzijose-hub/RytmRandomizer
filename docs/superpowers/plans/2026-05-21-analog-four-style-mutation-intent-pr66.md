# Analog Four Style Mutation Intent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four style mutation-intent report that turns an A4 kit snapshot plus style target into track/zone bias and direction metadata without rendering parameter values or touching hardware.

**Architecture:** Reuse the existing Analog Four style snapshot-routing plan as the source of track roles, favored zones, discovery-band policy, and candidate-only offset readiness. Add a focused strategy under `rytm_randomizer/devices/strategies/` and a passive report under `rytm_randomizer/reports/`, mirroring the Rytm mutation-intent shape while staying honest that A4 offsets still block real mutation.

**Tech Stack:** Existing A4 snapshot decoder, style target vectors, style discovery policy, passive CLI registry, pytest, coverage, architecture tests, lint, and code review gate.

---

## Scope

This slice answers: "For this Analog Four snapshot and style target, which tracks/zones should be pushed, and in which broad musical direction?"

It does not decode current A4 parameter values, render final CC/NRPN values, open a MIDI port, call a guarded sender, or mutate hardware.

## File Structure

- Modify `rytm_randomizer/devices/strategies/analog_four_style_snapshot_routing.py`: expose public zone-bias helper data so the intent layer can reuse the routing axes instead of duplicating them.
- Create `rytm_randomizer/devices/strategies/analog_four_style_mutation_intent.py`: build frozen dataclasses for A4 track zone-intent rows and plans.
- Modify `rytm_randomizer/devices/strategies/__init__.py`: re-export the new strategy types and planner.
- Create `rytm_randomizer/reports/analog_four_style_mutation_intent.py`: text/JSON report and passive CLI command.
- Modify `rytm_randomizer/cli.py`, `rytm_randomizer/help_text.py`, and `tests/fixtures/cli_help_expected.txt`: lazy command registration and help text.
- Modify `tests/test_analog_four_style_mutation_intent.py` and `tests/test_cli.py`: TDD coverage for planner, report, JSON, parser, CLI, and safety.
- Modify `README.md`, `docs/STATUS.md`, `docs/ARCHITECTURE_DIAGRAMS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document visible passive command behavior.

## Tasks

### Task 1: Red Tests

- [x] Write failing planner tests for A4 track zone-intent rows, candidate-only readiness, discovery depth, and direction rules.
- [x] Write failing report tests for operator-facing text and JSON payloads.
- [x] Write failing CLI tests for command help, text output, JSON output, and safe unknown-style errors.
- [x] Run focused tests with `python -m pytest tests/test_analog_four_style_mutation_intent.py tests/test_cli.py -n 0 -k "analog_four_style_mutation_intent"`.

### Task 2: Strategy And Report

- [x] Expose a public A4 style zone-bias helper from the existing routing strategy.
- [x] Add the A4 mutation-intent strategy dataclasses and planner.
- [x] Add the passive report formatter, JSON serializer, CLI parser, and handler.
- [x] Wire the command lazily through `cli.py` and help text.

### Task 3: Docs And Verification

- [x] Update README/status/architecture diagrams/PR-body notes for the new passive command.
- [x] Run focused tests and coverage for the new strategy/report modules.
- [x] Run vulture on touched A4 intent files.
- [x] Run `python -m pytest tests/architecture/ -q`.
- [x] Run ruff, black check, and isort check.
- [x] Run `python -m pytest -m fast`.
- [x] Run `python -m pytest`.
- [x] Run full coverage.
- [x] Run `python scripts/code_review_gate.py --mode cli`.
- [ ] Commit locally only; do not push/open a stacked PR while PR #56 remains open.

## Plan-Requirements Conformance

- [x] Gate 1 - target 100% coverage on the new strategy/report behavior.
- [x] Gate 2 - V1.34 parity unchanged; review gate runs parity.
- [x] Gate 3 - lint trio required before commit.
- [x] Gate 4 - vulture clean on touched files.
- [x] Gate 5 - README/status/diagram/PR-body docs updated for visible command behavior.
- [x] Gate 6 - explicit frozen dataclasses; no `Any`.
- [ ] Gate 7 - N/A: passive planning/report metadata only, no hot MIDI send path.
- [x] Gate 8 - tests cover planner, report, JSON, CLI, and safety.
- [x] Gate 9 - no new top-level modules; work stays in existing subpackages.
- [x] Gate 10 - no guarded string equality dispatch.
- [x] Gate 11 - existing local SysEx fixtures/helpers reused.
- [x] Gate 12 - module constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: track/zone intent only, no value renderer/sender.
- [ ] Gate 15 - N/A: no new learned skill/rule required.
- [x] Gate 16 - local-only checkpoint while PR #56 is open; no push/stacked PR.
- [x] Gate 17 - reuses existing A4 style routing, discovery policy, target vectors, passive formatter, and CLI registry.
- [x] Gate 18 - docs/help updated for new visible report.
