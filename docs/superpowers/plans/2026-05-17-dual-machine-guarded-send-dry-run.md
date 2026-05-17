# Dual-Machine Guarded Send Dry-Run Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a mock-only guarded sender dry-run that emits only ready active-send-plan CC events and refuses blocked plans.

**Architecture:** Reuse `dual_machine_active_send_plan` as the policy source. Add a small `dual_machine_guarded_sender` module that takes a plan plus an injected `MockMidiSender`, then add a passive CLI report command that builds the bridge, builds the plan, and runs the guarded dry-run.

**Tech Stack:** Python dataclasses, existing `MockMidiSender`, existing CLI dispatch, pytest.

---

## File Structure

- Create `rytm_randomizer/dual_machine_guarded_sender.py`: guarded dry-run dataclass, executor, bridge helper, formatter, and error formatter.
- Create `tests/test_dual_machine_guarded_sender.py`: API and CLI tests.
- Modify `rytm_randomizer/cli.py`: add passive `dual-machine-guarded-send-dry-run-report` route.
- Modify `rytm_randomizer/help_text.py`: add usage and command help.
- Modify `tests/test_cli.py`: add help coverage and update expected usage.
- Modify `tests/fixtures/cli_help_expected.txt`: update top-level help fixture.

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_dual_machine_guarded_sender.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add API tests**

Write tests for missing arming, missing dry-run confirmation, safe-starter accepted emission, target `rytm` accepted emission, and combined A4 snapshot candidate refusal.

- [x] **Step 2: Add CLI help and command tests**

Add help coverage in `tests/test_cli.py`. Add command tests in `tests/test_dual_machine_guarded_sender.py` for refused combined snapshots and accepted Rytm-only target scope.

- [x] **Step 3: Run red tests**

Run:

```powershell
pytest tests\test_dual_machine_guarded_sender.py tests\test_cli.py::test_dual_machine_guarded_send_dry_run_report_help_exits_zero -q
```

Expected: fail because the module and CLI command do not exist yet.

### Task 2: Guarded Sender Module

**Files:**
- Create: `rytm_randomizer/dual_machine_guarded_sender.py`
- Test: `tests/test_dual_machine_guarded_sender.py`

- [x] **Step 1: Implement dataclass and executor**

Add `DualMachineGuardedSendResult` and `execute_dual_machine_guarded_send`.

- [x] **Step 2: Implement bridge dry-run helper**

Add `build_dual_machine_guarded_send_dry_run(bridge)` to create the send plan,
execute it into `MockMidiSender`, and return the result.

- [x] **Step 3: Implement formatter**

Add deterministic report and error formatters with explicit mock-only and
no-MIDI safety lines.

- [x] **Step 4: Run focused tests**

Run:

```powershell
pytest tests\test_dual_machine_guarded_sender.py -q
```

Expected: module tests pass or fail only on missing CLI route.

### Task 3: CLI and Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add static help text**

Add the new command to top-level usage, command list, and command-specific help.

- [x] **Step 2: Add CLI route**

Parse the same argument shape as the active send plan report. Build the bridge,
run `build_dual_machine_guarded_send_dry_run`, and print the formatter output.

- [x] **Step 3: Run focused CLI checks**

Run:

```powershell
pytest tests\test_dual_machine_guarded_sender.py tests\test_cli.py::test_dual_machine_guarded_send_dry_run_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected: pass.

### Task 4: Verification

**Files:**
- No source changes expected.

- [x] **Step 1: Run real-dump refusal check**

Run:

```powershell
python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1
```

Expected: accepted false, reason `blocked_by_unverified_candidates`, emitted mock messages 0, blocked events 24.

- [x] **Step 2: Run real-dump Rytm-only check**

Run:

```powershell
python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --target rytm
```

Expected: accepted true, emitted mock messages 60, blocked events 0.

- [x] **Step 3: Run broad regression**

Run:

```powershell
pytest tests\test_dual_machine_guarded_sender.py tests\test_dual_machine_active_send_plan.py tests\test_dual_machine_live_snapshot_readiness.py tests\test_dual_machine_mock_bridge.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 4: Run full suite**

Run:

```powershell
pytest -q
```

Expected: pass with existing skipped tests only.

### Task 5: Commit and Push

**Files:**
- All files above.

- [x] **Step 1: Run final guards**

Run:

```powershell
git diff --check
git diff --exit-code -- rytm_hybrid_randomizer_v134.py
git status --short
```

- [ ] **Step 2: Stage and commit**

Run:

```powershell
git add docs/superpowers/specs/2026-05-17-dual-machine-guarded-send-dry-run-design.md docs/superpowers/plans/2026-05-17-dual-machine-guarded-send-dry-run.md rytm_randomizer/dual_machine_guarded_sender.py rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_dual_machine_guarded_sender.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git diff --cached --check
git commit -m "Add dual-machine guarded send dry-run"
```

- [ ] **Step 3: Push**

Run:

```powershell
git push
```
