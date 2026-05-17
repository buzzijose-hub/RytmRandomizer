# Target-Aware Mock Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the passive dual-machine mock bridge obey Live Snapshot target scope.

**Architecture:** Reuse `performance_snapshot_target` inside `dual_machine_mock_bridge`. Store the target plan on `DualMachineMockBridge`, derive message counts from active devices, and filter mock message capture before messages enter `MockMidiSender`.

**Tech Stack:** Python dataclasses, existing passive CLI, existing `MockMidiSender`, pytest.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/test_dual_machine_mock_bridge.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add Rytm-only target test**

```python
bridge = build_dual_machine_mock_bridge(path, slot=1, depth="micro", target="rytm")
sender = capture_dual_machine_mock_messages(bridge)
assert bridge.target_plan.canonical_target == "rytm"
assert bridge.analog_four_message_count == 0
assert {m.metadata["device"] for m in sender.sent_messages} == {"Analog Rytm MKII"}
```

- [x] **Step 2: Add Analog-Four-only target test**

```python
bridge = build_dual_machine_mock_bridge(path, slot=1, depth="micro", target="analog-four")
sender = capture_dual_machine_mock_messages(bridge)
assert bridge.rytm_message_count == 0
assert bridge.analog_four_message_count == 8
assert {m.metadata["device"] for m in sender.sent_messages} == {"Analog Four MKII"}
```

- [x] **Step 3: Add CLI target test**

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_dual_machine_mock_bridge_report_help_exits_zero -q
```

Expected before implementation: fail for missing `target` argument and help.

### Task 2: Bridge Implementation

**Files:**
- Modify: `rytm_randomizer/dual_machine_mock_bridge.py`

- [x] **Step 1: Add `target_plan` field**

Default `target="both"` in `build_dual_machine_mock_bridge`.

- [x] **Step 2: Filter message counts**

`rytm_message_count` returns zero when Rytm is untouched. `analog_four_message_count`
returns zero when Analog Four is untouched.

- [x] **Step 3: Filter captured messages**

`capture_dual_machine_mock_messages` sends Rytm messages only when
`analog_rytm` is active and Analog Four messages only when `analog_four` is
active.

- [x] **Step 4: Add report target lines**

Print target, active devices, and untouched devices near the top of the report.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add `--target` CLI variant**

Keep the existing six-argument command as default `both`. Add an eight-argument
variant ending in `--target <target>`.

- [x] **Step 2: Route target errors**

Catch `PerformanceSnapshotTargetError` and format with the existing
dual-machine mock bridge error report.

- [x] **Step 3: Update help text**

Document the target-aware command form and untouched-machine behavior.

### Task 4: Verification

- [x] **Step 1: Focused tests**

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_dual_machine_mock_bridge_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

- [x] **Step 2: Real dump CLI checks**

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --target rytm
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --target analog-four
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --target both
```

- [x] **Step 3: Broader passive tests**

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_performance_snapshot_target.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

- [x] **Step 4: Full suite**

```powershell
pytest -q
```
