# Analog Four Snapshot Mock Runtime Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four snapshot mock-runtime report that captures saved-offset mutation candidates into inert mock events.

**Architecture:** Create `analog_four_snapshot_mock_runtime.py` next to the A4 snapshot planner. Reuse `AnalogFourSnapshotMutationPlan` as the source of truth, capture each planned offset into `MockMidiSender` with a non-CC message type, and wire one passive CLI report.

**Tech Stack:** Python dataclasses/helpers, existing passive CLI/help pattern, pytest.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_analog_four_snapshot_mock_runtime.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add import-safety test**

```python
def test_importing_analog_four_snapshot_mock_runtime_is_passive_and_silent():
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import rytm_randomizer.analog_four_snapshot_mock_runtime; assert 'mido' not in sys.modules; assert 'rtmidi' not in sys.modules"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [x] **Step 2: Add mock-event capture test**

Build a synthetic A4 kit record with saved values in track blocks. Build a
snapshot mutation plan at `micro` depth, capture mock events, and assert:

```python
assert len(sender.sent_messages) == plan.planned_change_count == 9
assert first.type == "saved_offset_candidate"
assert first.channel == 0
assert first.control == 20
assert first.value == 67
assert first.metadata["device"] == "Analog Four MKII"
assert first.metadata["track"] == 1
assert first.metadata["saved_offset"] == 20
assert first.metadata["cc_mapping_claimed"] is False
assert first.metadata["sends_real_midi"] is False
```

- [x] **Step 3: Add CLI help/report tests**

```powershell
pytest tests\test_analog_four_snapshot_mock_runtime.py tests\test_cli.py::test_analog_four_snapshot_mock_runtime_report_help_exits_zero -q
```

Expected before implementation: fail for missing module and CLI route.

### Task 2: Mock Runtime Module

**Files:**
- Create: `rytm_randomizer/analog_four_snapshot_mock_runtime.py`

- [x] **Step 1: Add build helper**

Expose `build_analog_four_snapshot_mock_runtime_from_file(path, slot, depth)`
that returns the existing `AnalogFourSnapshotMutationPlan`.

- [x] **Step 2: Add capture helper**

Expose `capture_analog_four_snapshot_mock_messages(plan)`. It must validate
that `plan` is an `AnalogFourSnapshotMutationPlan`, then send one inert
`MidiMessage` per planned change with `message_type="saved_offset_candidate"`.

- [x] **Step 3: Add formatter and error formatter**

The report must include source path, kit, depth, planned tracks, planned
changes, mock sender count, per-track message counts, a mock event stream, the
candidate/unverified policy, and the passive safety boundary.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add CLI route**

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
```

- [x] **Step 2: Add command help**

Document that the command captures saved-offset candidates only and does not
claim CC mappings.

### Task 4: Verification

- [x] **Step 1: Focused tests**

```powershell
pytest tests\test_analog_four_snapshot_mock_runtime.py tests\test_cli.py::test_analog_four_snapshot_mock_runtime_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

- [x] **Step 2: Real dump CLI check**

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mock-runtime-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1 --depth micro
```

- [x] **Step 3: Broader passive tests**

```powershell
pytest tests\test_analog_four_snapshot_mock_runtime.py tests\test_analog_four_snapshot_mutation_planner.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

- [x] **Step 4: Full suite**

```powershell
pytest -q
```
