# Rytm Engine Cycle Starter Shaping Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive 12-pad starter-shaping layer to the Rytm engine-cycle planner.

**Architecture:** Create a focused starter-profile/planner module that consumes the existing `RytmEngineCyclePlan`, adds common safe filter/amp CC events, captures them in `MockMidiSender`, and exposes a passive CLI report. Existing active senders stay unchanged.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, existing `rytm_engine_cycle_plan`, pytest.

---

### Task 1: Starter Profile Tests

**Files:**
- Create: `tests/test_rytm_engine_cycle_starter_profiles.py`

- [ ] **Step 1: Write failing tests**

Add tests that import the future module passively, resolve starter profile aliases,
reject unknown profiles with valid choices, build a 12-pad Birmingham starter plan,
capture 84 mock messages, and format a passive report.

- [ ] **Step 2: Run the focused tests**

Run:

```powershell
pytest tests\test_rytm_engine_cycle_starter_profiles.py -q
```

Expected: fails because `rytm_randomizer.rytm_engine_cycle_starter_profiles`
does not exist yet.

### Task 2: Starter Profile Implementation

**Files:**
- Create: `rytm_randomizer/rytm_engine_cycle_starter_profiles.py`

- [ ] **Step 1: Implement profile dataclasses**

Create frozen dataclasses for starter parameters, pad profiles, starter events,
pad starter plans, and full starter plans.

- [ ] **Step 2: Add four deterministic profiles**

Add `balanced`, `birmingham-dark`, `detroit-classic`, and `peak-time` with 12 pad
profiles each. Every pad uses six common Rytm CCs: 74, 75, 76, 80, 81, and 10.

- [ ] **Step 3: Add planner, mock capture, and report formatter**

Combine machine-select events from `RytmEngineCyclePlan` with starter parameters,
capture them into `MockMidiSender`, and format a deterministic passive report.

- [ ] **Step 4: Run focused tests**

Run:

```powershell
pytest tests\test_rytm_engine_cycle_starter_profiles.py -q
```

Expected: pass.

### Task 3: CLI Report

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Write CLI tests**

Add help and command tests for `rytm-engine-cycle-starter-plan-report`.

- [ ] **Step 2: Run CLI tests**

Run:

```powershell
pytest tests\test_cli.py::test_rytm_engine_cycle_starter_plan_report_help_exits_zero tests\test_rytm_engine_cycle_starter_profiles.py::test_rytm_engine_cycle_starter_plan_report_cli_accepts_style_and_profile -q
```

Expected: fail until the command and help text are wired.

- [ ] **Step 3: Implement CLI command and help**

Parse `--style`, optional `--discovery`, and optional `--profile`; build the
engine-cycle plan, wrap it in a starter plan, and print the passive starter report.

- [ ] **Step 4: Run focused CLI verification**

Run the focused CLI tests plus top-level help fixture verification.

### Task 4: Full Verification and Commit

**Files:**
- All changed files

- [ ] **Step 1: Run full tests**

Run:

```powershell
pytest -q
```

Expected: all tests pass.

- [ ] **Step 2: Run diff checks**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
```

Expected: no whitespace errors and no monolith drift.

- [ ] **Step 3: Commit and push**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-rytm-engine-cycle-starter-shaping-design.md docs/superpowers/plans/2026-05-17-rytm-engine-cycle-starter-shaping.md tests/test_rytm_engine_cycle_starter_profiles.py tests/test_cli.py tests/fixtures/cli_help_expected.txt rytm_randomizer/rytm_engine_cycle_starter_profiles.py rytm_randomizer/cli.py rytm_randomizer/help_text.py
git commit -m "Add Rytm engine cycle starter shaping plan"
git push
```
