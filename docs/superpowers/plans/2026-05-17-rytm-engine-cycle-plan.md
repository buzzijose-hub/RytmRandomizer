# Rytm Engine Cycle Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Rytm engine-cycle planner that ranks full-palette machine candidates for all 12 pads and captures a mock CC15 cycle stream.

**Architecture:** Extend the existing `machine_catalog` support taxonomy with a machine-selectable tier, then add one report module that consumes style intent plus role ranking. Wire a passive CLI command and help text; keep active hardware paths unchanged.

**Tech Stack:** Python frozen dataclasses, existing style intent and machine catalog modules, passive CLI dispatch, `MockMidiSender`, pytest.

---

## File Structure

- Modify `rytm_randomizer/machine_catalog.py`
  - Add `machine_selectable` support status and individual known-value Rytm engines.
  - Preserve existing default ranking behavior for current snapshot paths.
- Create `rytm_randomizer/rytm_engine_cycle_plan.py`
  - Owns engine-cycle plan DTOs, builder, mock capture, formatter, and error formatter.
- Modify `rytm_randomizer/cli.py` and `rytm_randomizer/help_text.py`
  - Add passive `rytm-engine-cycle-plan-report --style <text> [--discovery <0..1>]`.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Keep top-level help deterministic.
- Tests:
  - Create `tests/test_rytm_engine_cycle_plan.py`.
  - Extend `tests/test_machine_catalog.py` and `tests/test_cli.py`.

## Steps

- [x] Add red tests for machine-selectable catalog values, style-ranked engine candidates, mock CC15 capture, CLI output, and help text.
- [x] Run focused tests and confirm they fail against the current catalog/report surface.
- [x] Extend `machine_catalog.py` with machine-selectable engines and optional inclusion in ranking.
- [x] Implement `rytm_engine_cycle_plan.py`.
- [x] Wire CLI parsing and help text.
- [x] Run focused tests, real project passive report, broader regressions, full suite, diff checks, commit, and push.
