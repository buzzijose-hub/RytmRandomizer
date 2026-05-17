# Performance Snapshot Target Scope Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive target-scope model/report for Rytm-only, Analog-Four-only, and both-machines Live Snapshot operation.

**Architecture:** Create one focused module that normalizes a target string into active and untouched device scopes. Wire a CLI report around it. The module remains independent from SysEx decoders and MIDI providers so future hardware paths can reuse it as a safety gate.

**Tech Stack:** Python dataclasses, existing passive CLI/help pattern, pytest.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_performance_snapshot_target.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add import-safety test**

```python
def test_importing_performance_snapshot_target_is_passive_and_silent():
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import rytm_randomizer.performance_snapshot_target; assert 'mido' not in sys.modules; assert 'rtmidi' not in sys.modules"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [x] **Step 2: Add target behavior tests**

```python
plan = build_performance_snapshot_target_plan("rytm")
assert plan.active_device_keys == ("analog_rytm",)
assert plan.untouched_device_keys == ("analog_four",)
```

- [x] **Step 3: Add CLI help and report tests**

```powershell
pytest tests\test_performance_snapshot_target.py tests\test_cli.py::test_performance_snapshot_target_report_help_exits_zero -q
```

Expected before implementation: fail for missing module/help route.

### Task 2: Target Scope Module

**Files:**
- Create: `rytm_randomizer/performance_snapshot_target.py`

- [x] **Step 1: Add dataclasses**

Add immutable `PerformanceSnapshotDeviceScope` and
`PerformanceSnapshotTargetPlan`.

- [x] **Step 2: Normalize target aliases**

Accept `rytm`, `analog-rytm`, `a4`, `analog-four`, `analog_four`, `analog4`,
`both`, and `all`.

- [x] **Step 3: Format report and error**

Report active devices, untouched devices, device actions, and safety text.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add route**

```powershell
python -m rytm_randomizer.cli performance-snapshot-target-report --target rytm
```

- [x] **Step 2: Add help text**

Document that the report is passive and enforces the leave-other-machine-alone
rule.

### Task 4: Verification

**Files:**
- Test: `tests/test_performance_snapshot_target.py`
- Test: `tests/test_cli.py`
- Test: `tests/architecture/test_no_side_effects.py`
- Test: `tests/architecture/test_observability.py`

- [x] **Step 1: Run focused tests**

```powershell
pytest tests\test_performance_snapshot_target.py tests\test_cli.py::test_performance_snapshot_target_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected: pass after implementation.

- [x] **Step 2: Run passive safety tests**

```powershell
pytest tests\test_performance_snapshot_target.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 3: Run full suite**

```powershell
pytest -q
```

Expected: pass.
