# Rytm Engine Cycle Starter Send Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add opt-in starter-shaping support to guarded dry-run and armed Rytm engine-cycle send.

**Architecture:** Keep the current `RytmEngineCyclePlan` send path intact. Allow the guarded and hardware senders to also accept `RytmEngineCycleStarterPlan`, formatting profile-aware reports and emitting each starter event in order.

**Tech Stack:** Python dataclasses, existing app parser, existing mock/hardware sender boundaries, pytest.

---

### Task 1: Sender Contract Tests

**Files:**
- Modify: `tests/test_rytm_engine_cycle_guarded_sender.py`
- Modify: `tests/test_rytm_engine_cycle_hardware_sender.py`

- [ ] **Step 1: Add failing guarded sender test**

Verify a Birmingham starter plan emits 84 mock messages, includes profile
metadata, and formats Pad 5 machine select followed by `FLT Frequency CC74`.

- [ ] **Step 2: Add failing hardware sender test**

Verify a Birmingham starter plan sends 84 fake real-MIDI messages after guards
accept, with Pad 5 `CC15 -> 17` followed by `CC74 -> 108`.

### Task 2: App Wiring Tests

**Files:**
- Modify: `tests/test_app_entry.py`

- [ ] **Step 1: Add dry-run app test**

Verify `--dry-run --rytm-engine-cycle --engine-cycle-starter-profile birmingham-dark`
prints the profile and captures 84 mock messages.

- [ ] **Step 2: Add armed app test**

Verify `--arm --rytm-engine-cycle --engine-cycle-starter-profile birmingham-dark`
sends 84 fake real-MIDI messages only after port selection and `SEND`.

### Task 3: Implementation

**Files:**
- Modify: `rytm_randomizer/rytm_engine_cycle_guarded_sender.py`
- Modify: `rytm_randomizer/rytm_engine_cycle_hardware_sender.py`
- Modify: `rytm_randomizer/app.py`

- [ ] **Step 1: Teach senders about starter plans**

Accept either `RytmEngineCyclePlan` or `RytmEngineCycleStarterPlan`, using helper
functions for counts, result metadata, and message construction.

- [ ] **Step 2: Add app flag**

Add `--engine-cycle-starter-profile`, include it in the request, and build a
starter plan when supplied.

- [ ] **Step 3: Preserve old behavior**

Run existing no-starter engine-cycle tests and confirm they still expect 12
messages.

### Task 4: Verification and Commit

Run focused tests, manual app dry-run, full test suite, `git diff --check`, and
the monolith drift check. Commit and push.
