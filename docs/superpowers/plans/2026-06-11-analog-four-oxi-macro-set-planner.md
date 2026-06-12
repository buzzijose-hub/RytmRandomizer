# Analog Four OXI Macro Set Planner Implementation Plan

> Status: in-flight (PR pending)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four OXI-style set planner that sequences existing A4 macro/readiness rows into a live-set queue contract without adding an A4 SEND path.

**Architecture:** Reuse `rytm_randomizer/data/analog_four_oxi_macros.py`, `reports/analog_four_oxi_macro_report.py`, and `reports/analog_four_oxi_macro_readiness.py`. Add one focused passive report module plus lazy CLI registration, keeping full A4 macro SEND blocked and preserving the existing operator-present one-row validation boundary.

**Tech Stack:** Python 3.11, frozen dataclasses, passive CLI registry, deterministic JSON, pytest, ruff, black, isort.

---

## File Structure

- Create `rytm_randomizer/reports/analog_four_oxi_macro_set_planner.py`
  - Builds a deterministic set sequence from the existing A4 macro vocabulary.
  - Converts every step into readiness/recovery cards.
  - Emits JSON for Cockpit and operator-readable text for CLI use.
  - Opens no ports and sends no MIDI.
- Modify `rytm_randomizer/cli.py`
  - Add one lazy command entry for `analog-four-oxi-macro-set-planner-report`.
- Modify `rytm_randomizer/help_text.py`
  - Document the passive planner command.
- Create `tests/test_analog_four_oxi_macro_set_planner.py`
  - Cover deterministic default sequence, custom sequence parsing, JSON, text formatting, CLI behavior, and passive import safety.
- Modify `README.md`
  - Add the set planner to the passive A4/OXI command list.
- Modify `docs/STATUS.md`
  - Record the new passive set-planner surface.

## Task 1: Red Tests For The Planner Contract

**Files:**
- Create: `tests/test_analog_four_oxi_macro_set_planner.py`

- [x] **Step 1: Write the failing default planner tests**

Cover the default `home -> hard-groove -> dub-pressure -> industrial-transition -> home` sequence, passive flags, and blocked full macro SEND.

- [x] **Step 2: Run focused tests and verify red**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_set_planner.py -n 0
```

Expected: fail because `rytm_randomizer.reports.analog_four_oxi_macro_set_planner` does not exist yet.

## Task 2: Implement The Passive Report

**Files:**
- Create: `rytm_randomizer/reports/analog_four_oxi_macro_set_planner.py`

- [x] **Step 1: Add frozen report dataclasses**

Add `AnalogFourOxiSetStep` and `AnalogFourOxiSetPlannerReport` with no mutable fields.

- [x] **Step 2: Build planner data from existing macro/readiness reports**

Use existing macro/readiness builders instead of duplicating parameter facts.

- [x] **Step 3: Add text and JSON formatters**

Expose deterministic text lines and a JSON payload suitable for Cockpit queue rendering.

- [x] **Step 4: Run focused planner tests and verify green**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_set_planner.py -n 0
```

Expected: all planner tests pass.

## Task 3: Wire The CLI Command

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_analog_four_oxi_macro_set_planner.py`

- [x] **Step 1: Add lazy command registration**

Register `analog-four-oxi-macro-set-planner-report` through the existing lazy CLI table.

- [x] **Step 2: Add help text**

Document that the command is passive/read-only and keeps A4 full macro SEND blocked.

- [x] **Step 3: Run CLI tests**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_set_planner.py -n 0
```

Expected: CLI parser and handler tests pass.

## Task 4: Docs And Status

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Update README passive report list**

Add the set planner command beside the existing A4 macro and readiness commands.

- [x] **Step 2: Update status**

Add a single current-status bullet describing the passive A4 set planner and no-send boundary.

## Task 5: Verification

**Files:**
- All touched files.

- [x] **Step 1: Run focused Python tests**

```powershell
python -m pytest tests\test_analog_four_oxi_macro_set_planner.py tests\test_analog_four_oxi_macro_readiness.py tests\test_analog_four_oxi_macro_report.py -n 0
```

- [x] **Step 2: Run safety and architecture checks**

```powershell
python -m pytest tests\test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests\architecture\ -q
```

- [x] **Step 3: Run lint/format/whitespace checks**

```powershell
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
git diff --check
```

## Task 6: Cockpit JSON Adapter Hardening

**Files:**
- Modify: `desktop/web/src/cockpit/styleCrateQueueModel.ts`
- Modify: `desktop/web/tests/cockpit/styleCrateQueueModel.test.ts`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Add red tests for backend set-planner JSON**

Cover the `analog-four-oxi-macro-set-planner-report --json` snake_case payload
shape and ensure Cockpit can consume a custom set name, current/up-next macro
steps, blocked actions, safety flags, and report-owned replay command.

- [x] **Step 2: Add the Cockpit adapter**

Add `toStyleCrateAnalogFourSetPlan` and an optional `toStyleCrateQueueModel`
input so the style queue can use real backend A4 set planner JSON while keeping
the default `warehouse-arc` fallback populated.

- [x] **Step 3: Verify frontend contract**

Run:

```powershell
npm.cmd run test:run -- tests/cockpit/styleCrateQueueModel.test.ts
npm.cmd run typecheck
```

Expected: affected Cockpit model tests and TypeScript build pass.

## Task 7: Exact Replay Command Preservation

**Files:**
- Modify: `rytm_randomizer/reports/analog_four_oxi_macro_set_planner.py`
- Modify: `tests/test_analog_four_oxi_macro_set_planner.py`
- Modify: `docs/STATUS.md`

- [x] **Step 1: Add red test for custom set-plan replay**

Cover custom `--set-name`, `--sequence`, and `--seed` JSON output so the
payload's `replay_command` can reproduce the exact set plan instead of falling
back to the default `warehouse-arc` command.

- [x] **Step 2: Compute replay command from resolved plan arguments**

Keep the default replay command unchanged for the default set plan, while
preserving non-default set name, macro sequence, and seed arguments for custom
set plans.

- [x] **Step 3: Verify focused backend contract**

Run:

```powershell
python -m pytest tests\test_analog_four_oxi_macro_set_planner.py -n 0
```

Expected: all planner tests pass.

## Self-Review

- Spec coverage: covers A4 set sequencing, readiness rows, replay commands, blocked active actions, docs, CLI, JSON payloads, and the Cockpit adapter from backend JSON to frontend model.
- Safety coverage: no port opening, no MIDI sending, no hardware mutation, no full A4 macro SEND.
- Architecture coverage: new work stays inside `reports/`, existing CLI registry, existing data/report surfaces, and does not add top-level packages.
