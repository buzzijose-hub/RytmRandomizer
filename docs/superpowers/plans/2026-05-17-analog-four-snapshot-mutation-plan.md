# Analog Four Snapshot Mutation Plan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a passive Analog Four snapshot mutation planner using saved captured values and unverified offset candidates.

**Architecture:** Create `analog_four_snapshot_mutation_planner.py` beside the existing A4 snapshot/diff modules. Reuse the A4 snapshot decoder helpers to unpack the selected kit record and scan track blocks for CC-like saved words. Wire a passive CLI report and tests without importing MIDI libraries.

**Tech Stack:** Python dataclasses, existing passive CLI/help pattern, pytest.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_analog_four_snapshot_mutation_planner.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add import-safety test**

```python
def test_importing_analog_four_snapshot_mutation_planner_is_passive_and_silent():
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import rytm_randomizer.analog_four_snapshot_mutation_planner; assert 'mido' not in sys.modules; assert 'rtmidi' not in sys.modules"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [x] **Step 2: Add captured-value planning test**

Build a synthetic A4 kit with saved values in each track block. Assert that the
planner reports four tracks, candidate offset changes, and captured baselines.

- [x] **Step 3: Add CLI help/report test**

```powershell
pytest tests\test_analog_four_snapshot_mutation_planner.py tests\test_cli.py::test_analog_four_snapshot_mutation_plan_report_help_exits_zero -q
```

Expected before implementation: fail for missing module and CLI route.

### Task 2: Planner Module

**Files:**
- Create: `rytm_randomizer/analog_four_snapshot_mutation_planner.py`

- [x] **Step 1: Add dataclasses**

Define `AnalogFourSnapshotPlannedOffsetChange`,
`AnalogFourTrackMutationPlan`, and `AnalogFourSnapshotMutationPlan`.

- [x] **Step 2: Build plan from file/bytes**

Use the selected kit record, kit name, and per-track blocks. Reject invalid
depths with `AnalogFourSnapshotMutationPlanError`.

- [x] **Step 3: Select candidate offsets**

Scan 16-bit words after the track name region, keep values in `0..127`, choose
up to six offsets per track, and apply bounded deltas.

- [x] **Step 4: Format report and errors**

The report must say `candidate_unverified`, `captured-value relative`,
`candidate offsets only`, `no parameter names claimed`, and `no MIDI sending`.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`
- Modify: `tests/architecture/test_observability.py`

- [x] **Step 1: Add CLI route**

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
```

- [x] **Step 2: Add help text**

Document the passive boundary and unverified-offset status.

- [x] **Step 3: Add error class to observability architecture allow-list**

Add `AnalogFourSnapshotMutationPlanError` to the taxonomy conformance test list.

### Task 4: Verification

- [x] **Step 1: Focused tests**

```powershell
pytest tests\test_analog_four_snapshot_mutation_planner.py tests\test_cli.py::test_analog_four_snapshot_mutation_plan_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

- [x] **Step 2: Real dump CLI check**

```powershell
python -m rytm_randomizer.cli analog-four-snapshot-mutation-plan-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1 --depth micro
```

- [x] **Step 3: Broader passive tests**

```powershell
pytest tests\test_analog_four_snapshot_mutation_planner.py tests\test_analog_four_snapshot_decoder.py tests\test_analog_four_controlled_diff.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

- [x] **Step 4: Full suite**

```powershell
pytest -q
```
