# Rytm Style Mutation Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Enrich the passive Rytm style mutation-intent rows with style-target bias and musical direction so future renderers know whether a safe parameter should generally move higher, lower, shorter, longer, or stay centered.

**Architecture:** Extend the existing `rytm_randomizer/devices/strategies/analog_rytm_style_mutation_intent.py` strategy in place. It already owns the style-to-zone-to-parameter contract, so the bias calculation belongs beside row creation rather than in a new package/module. Update the passive report and JSON output to expose the bias metadata while still rendering no CC target values and sending no MIDI.

**Tech Stack:** Existing style target vectors, passive Rytm mutation-intent strategy/report, CLI help fixture, pytest, coverage, architecture tests, lint, and code review gate.

---

## Scope

This slice answers: "For this style and discovery amount, is this parameter supposed to be pushed up, pulled down, shortened, lengthened, or kept centered?"

It does not compute final CC values. It does not decode current parameter values from the kit dump. It does not call `guarded_send`, open ports, or touch hardware.

## File Structure

- Modify `rytm_randomizer/devices/strategies/analog_rytm_style_mutation_intent.py`: add `target_bias` and `target_direction` fields to intent rows and calculate them from `STYLE_TARGET_VECTORS`.
- Modify `rytm_randomizer/reports/rytm_style_mutation_intent.py`: include bias/direction in text and JSON payloads.
- Modify `tests/test_rytm_style_mutation_intent.py`: red/green tests for grit, filter-frequency, decay/hold, LFO, JSON, and report text.
- Modify `README.md`, `docs/STATUS.md`, and `docs/superpowers/plans/2026-05-21-style-target-routing-pr-body.md`: document that the local mutation-intent report now includes style bias and direction metadata.

## Tasks

### Task 1: Red Tests

- [x] Assert that a Birmingham pressure grit row exposes high bias and `higher` direction.
- [x] Assert that a dark filter-frequency row exposes `lower` direction.
- [x] Assert that decay/hold rows can expose `shorter` or `longer` depending on the style vector.
- [x] Assert JSON rows include `target_bias` and `target_direction`.
- [x] Assert text rows include `bias N` and `direction <label>`.
- [x] Run focused tests and verify they fail before implementation.

### Task 2: Implementation

- [x] Add a zone-axis scoring helper using the same style target axes as the routing model.
- [x] Add a parameter-direction helper:
  - `FLT Frequency`: `lower` for dark styles, `higher` for bright styles, otherwise `center`.
  - `Decay`/`Hold`: `shorter` for transient-heavy short-tail styles, `longer` for long-tail styles, otherwise `center`.
  - LFO parameters: `higher` for motion-heavy styles, otherwise `center`.
  - grit/transient/noise/overdrive/resonance parameters: `higher` for high grit/drive/metal styles, otherwise `center`.
  - all other rows: `center`.
- [x] Extend `RytmStyleMutationIntentRow` with `target_bias` and `target_direction`.
- [x] Update text and JSON report formatting.
- [x] Update docs/status/PR-body notes.

### Task 3: Verification

- [x] Run focused mutation-intent/report/CLI tests with `-n 0`.
- [x] Run focused coverage on the updated strategy/report modules.
- [x] Run vulture on touched files.
- [x] Run `python -m pytest tests/architecture/ -q`.
- [x] Run ruff, black check, and isort check.
- [x] Run `python -m pytest -m fast`.
- [x] Run `python -m pytest`.
- [x] Run full coverage.
- [x] Run `python scripts/code_review_gate.py --mode cli`.
- [ ] Commit locally only; do not push/open a stacked PR while PR #56 remains open.

## Plan-Requirements Conformance

- [x] Gate 1 - target 100% branch coverage on updated strategy/report behavior.
- [x] Gate 2 - V1.34 parity unchanged; review gate runs parity.
- [x] Gate 3 - lint trio required before commit.
- [x] Gate 4 - vulture clean on touched files.
- [x] Gate 5 - README, status, and PR-body docs updated.
- [x] Gate 6 - explicit frozen dataclass fields; no `Any`.
- [ ] Gate 7 - N/A: passive planning/report metadata only, no hot MIDI send path.
- [x] Gate 8 - focused tests cover report text, JSON, and direction rules.
- [x] Gate 9 - no new package/module needed; work stays in existing strategy/report files.
- [x] Gate 10 - no legacy string-literal mode/intensity dispatch.
- [x] Gate 11 - existing snapshot fixtures reused.
- [x] Gate 12 - module-level constants use `Final`.
- [ ] Gate 13 - N/A: no environment variables.
- [x] Gate 14 - bounded scope: direction metadata only, no value renderer/sender.
- [ ] Gate 15 - N/A: no new learned skill/rule required.
- [x] Gate 16 - local-only checkpoint while PR #56 is open; no push/stacked PR.
- [x] Gate 17 - reuses existing style target vectors, mutation-intent rows, report formatter, and CLI registry.
- [x] Gate 18 - docs/help updated if visible behavior changes.
