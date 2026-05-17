# Dual-Machine Active Send Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive dual-machine active-send plan gate that lists which bridge events are eligible for future hardware sending and which events remain blocked.

**Architecture:** Reuse `dual_machine_mock_bridge` for message capture and `dual_machine_live_snapshot_readiness` for overall readiness. Add a focused `dual_machine_active_send_plan` module that converts inert mock messages into send-plan events, then expose it through the passive CLI.

**Tech Stack:** Python dataclasses, existing pytest suite, existing CLI dispatch and static help fixtures.

---

## File Structure

- Create `rytm_randomizer/dual_machine_active_send_plan.py`: send-plan dataclasses, builder, formatter, and error formatter.
- Create `tests/test_dual_machine_active_send_plan.py`: focused passive import, builder, formatter, and CLI command tests.
- Modify `rytm_randomizer/cli.py`: add `dual-machine-active-send-plan-report` route using the same argument shape as the bridge/readiness commands.
- Modify `rytm_randomizer/help_text.py`: add usage and command help.
- Modify `tests/test_cli.py`: add help coverage and update expected `USAGE`.
- Modify `tests/fixtures/cli_help_expected.txt`: keep top-level help fixture exact.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_dual_machine_active_send_plan.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add focused tests for the new send-plan API**

Create tests that expect `build_dual_machine_active_send_plan`, `format_dual_machine_active_send_plan_report`, and `format_dual_machine_active_send_plan_error` to exist. The tests should build synthetic Rytm and Analog Four SysEx records using the existing helper style from `tests/test_dual_machine_live_snapshot_readiness.py`.

- [x] **Step 2: Add CLI help coverage**

Add `test_dual_machine_active_send_plan_report_help_exits_zero` to `tests/test_cli.py`. Assert the help contains `active send plan`, `--analog-four-path <path>`, `saved-offset candidate events are blocked`, and `no MIDI sending`.

- [x] **Step 3: Run the tests and watch them fail**

Run:

```powershell
pytest tests\test_dual_machine_active_send_plan.py tests\test_cli.py::test_dual_machine_active_send_plan_report_help_exits_zero -q
```

Expected: failures because the module and CLI help command do not exist yet.

### Task 2: Send-Plan Module

**Files:**
- Create: `rytm_randomizer/dual_machine_active_send_plan.py`
- Test: `tests/test_dual_machine_active_send_plan.py`

- [x] **Step 1: Implement dataclasses**

Add immutable dataclasses for `DualMachineSendPlanEvent` and `DualMachineActiveSendPlan`. Add count properties for eligible, blocked, and combined events.

- [x] **Step 2: Implement builder**

Implement `build_dual_machine_active_send_plan(bridge)`. Validate that `bridge` is a `DualMachineMockBridge`, evaluate readiness, capture messages, mark `cc` as eligible, mark `saved_offset_candidate` as blocked, and mark unknown types blocked.

- [x] **Step 3: Implement formatters**

Add deterministic report and error formatters. Include policy lines that mapped CC messages are the only eligible events and saved-offset candidates are blocked.

- [x] **Step 4: Run focused module tests**

Run:

```powershell
pytest tests\test_dual_machine_active_send_plan.py -q
```

Expected: module tests pass or fail only on missing CLI route.

### Task 3: CLI and Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add static help text**

Add the command to `USAGE`, top-level help usage, command list, and `HELP_TEXT["dual-machine-active-send-plan-report"]`.

- [x] **Step 2: Add CLI route**

Add a parser branch near the existing dual-machine readiness route. Reuse the bridge builder and pass the resulting bridge into `build_dual_machine_active_send_plan`.

- [x] **Step 3: Run focused CLI tests**

Run:

```powershell
pytest tests\test_dual_machine_active_send_plan.py tests\test_cli.py::test_dual_machine_active_send_plan_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected: pass.

### Task 4: Real Dump Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run the real-dump command**

Run:

```powershell
python -m rytm_randomizer.cli dual-machine-active-send-plan-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1
```

Expected: send plan ready false, 60 eligible mapped CC messages, 24 blocked candidate events, and passive no-MIDI safety lines.

- [x] **Step 2: Run broad regression checks**

Run:

```powershell
pytest tests\test_dual_machine_active_send_plan.py tests\test_dual_machine_live_snapshot_readiness.py tests\test_dual_machine_mock_bridge.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 3: Run the full suite**

Run:

```powershell
pytest -q
```

Expected: pass with the existing skipped tests only.

### Task 5: Commit and Push

**Files:**
- All files changed above.

- [x] **Step 1: Run final diff guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

Expected: no whitespace errors, protected V1.34 file unchanged, and only intended files changed.

- [ ] **Step 2: Stage and commit**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-dual-machine-active-send-plan-design.md docs/superpowers/plans/2026-05-17-dual-machine-active-send-plan.md rytm_randomizer/dual_machine_active_send_plan.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_dual_machine_active_send_plan.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git diff --cached --check
git commit -m "Add dual-machine active send plan gate"
```

- [ ] **Step 3: Push**

Run:

```powershell
git push
```

Expected: branch `codex/dual-machine-mock-bridge` pushed to origin.
