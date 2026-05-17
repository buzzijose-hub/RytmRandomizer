# Dual-Machine Live Snapshot Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive readiness gate that classifies dual-machine mock bridge streams before any future live sender can use them.

**Architecture:** Create `dual_machine_live_snapshot_readiness.py` that consumes `DualMachineMockBridge`, inspects captured mock messages, and reports per-device readiness. Wire one CLI command that accepts the same bridge inputs.

**Tech Stack:** Python dataclasses, existing passive CLI/help pattern, pytest.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_dual_machine_live_snapshot_readiness.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add import-safety test**

Assert importing `rytm_randomizer.dual_machine_live_snapshot_readiness` is silent
and does not import `mido` or `rtmidi`.

- [x] **Step 2: Add safe-starter readiness test**

Build the existing safe-starter bridge and assert overall readiness is true,
Rytm is `ready_mapped_cc`, and A4 is `ready_safe_starter_cc`.

- [x] **Step 3: Add A4 snapshot candidate blocking test**

Build a bridge with `analog_four_sysex_path` and assert overall readiness is
false because the A4 side is `blocked_candidate_unverified`.

- [x] **Step 4: Add CLI and help tests**

Assert the new report command and `--help` output exist and remain passive.

### Task 2: Readiness Module

**Files:**
- Create: `rytm_randomizer/dual_machine_live_snapshot_readiness.py`

- [x] **Step 1: Add readiness dataclasses**

Define `DualMachineDeviceReadiness` and `DualMachineLiveSnapshotReadiness`.

- [x] **Step 2: Evaluate bridge readiness**

Capture mock messages from the bridge and classify active/untouched devices.
Any `saved_offset_candidate` message blocks hardware-send readiness.

- [x] **Step 3: Format report and errors**

Report target, ready flag, reason, combined message count, per-device status,
mapping policy, and passive safety boundary.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add CLI route**

Parse the same arguments as `dual-machine-mock-bridge-report`, then build the
bridge and readiness report.

- [x] **Step 2: Update help text**

Document that the command is a readiness gate and not an active sender.

### Task 4: Verification

- [x] **Step 1: Focused tests**

```powershell
pytest tests\test_dual_machine_live_snapshot_readiness.py tests\test_cli.py::test_dual_machine_live_snapshot_readiness_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

- [x] **Step 2: Real dual dump check**

```powershell
python -m rytm_randomizer.cli dual-machine-live-snapshot-readiness-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1
```

- [x] **Step 3: Broader passive tests**

```powershell
pytest tests\test_dual_machine_live_snapshot_readiness.py tests\test_dual_machine_mock_bridge.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

- [x] **Step 4: Full suite**

```powershell
pytest -q
```
