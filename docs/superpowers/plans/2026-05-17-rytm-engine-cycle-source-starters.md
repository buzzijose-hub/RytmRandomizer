# Rytm Engine Cycle Source Starters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add optional engine-source starter values to the Rytm engine-cycle starter plan.

**Architecture:** Extend `rytm_engine_cycle_starter_profiles.py` with a machine-key source-starter catalog and an opt-in `include_engine_source_starters` planner flag. Reuse the existing guarded and hardware senders, updating only their formatting for the new event role. Add an app flag to turn the layer on.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, existing app parser, pytest.

---

### Task 1: Planner Tests

**Files:**
- Modify: `tests/test_rytm_engine_cycle_starter_profiles.py`

- [ ] **Step 1: Add failing source-starter test**

Build a Birmingham starter plan with `include_engine_source_starters=True`.
Expect 132 total events, 48 engine-source events, and Pad 5 to include `SRC Slot
1 CC16 -> 100` before common `FLT Frequency CC74 -> 108`.

### Task 2: Sender/App Tests

**Files:**
- Modify: `tests/test_rytm_engine_cycle_guarded_sender.py`
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Add failing guarded sender test**

Verify the guarded mock sender emits 132 messages and formats
`engine_source_parameter` preview lines.

- [ ] **Step 2: Add failing app dry-run test**

Verify `--engine-cycle-source-starters` plus `--engine-cycle-starter-profile auto`
emits 132 mock messages.

### Task 3: Implementation

**Files:**
- Modify: `rytm_randomizer/rytm_engine_cycle_starter_profiles.py`
- Modify: `rytm_randomizer/rytm_engine_cycle_guarded_sender.py`
- Modify: `rytm_randomizer/rytm_engine_cycle_hardware_sender.py`
- Modify: `rytm_randomizer/app.py`

- [ ] **Step 1: Add source starter catalog**

Add four CC16-23 starter values for machine keys used by the current engine
cycle planner.

- [ ] **Step 2: Add planner option**

Insert engine-source events after machine select when
`include_engine_source_starters=True`.

- [ ] **Step 3: Wire app flag**

Add `--engine-cycle-source-starters` and pass it to the starter planner.

### Task 4: Verification and Commit

Run focused tests, manual dry-run, full suite, `git diff --check`, and the
monolith drift check. Commit and push.
