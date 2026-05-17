# Snapshot Mock Runtime Report Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a passive CLI report that converts Rytm saved-snapshot mutation plans into inert mock CC messages.

**Architecture:** Reuse `sysex_snapshot_decoder` and `snapshot_mutation_planner` as the data source. Add a focused `snapshot_mock_runtime` module that captures planned changes into `MockMidiSender` and formats a report. Wire one new CLI route and help entry.

**Tech Stack:** Python dataclasses and local passive modules; pytest for TDD; no MIDI provider imports.

---

### Task 1: Failing Tests

**Files:**
- Create: `tests/test_snapshot_mock_runtime.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add import-safety test**

```python
def test_importing_snapshot_mock_runtime_is_passive_and_silent():
    result = subprocess.run(
        [sys.executable, "-c", "import sys; import rytm_randomizer.snapshot_mock_runtime; assert 'mido' not in sys.modules; assert 'rtmidi' not in sys.modules"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [x] **Step 2: Add mock capture behavior test**

```python
sender = capture_snapshot_mutation_mock_messages(plan)
assert len(sender.sent_messages) == plan.planned_change_count
assert sender.sent_messages[0].channel == 0
assert sender.sent_messages[0].metadata["source_kind"] == "snapshot_mutation_plan"
```

- [x] **Step 3: Add CLI report test**

Run:

```powershell
pytest tests\test_snapshot_mock_runtime.py tests\test_cli.py::test_sysex_snapshot_mock_runtime_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected before implementation: failures for the missing module and CLI route.

### Task 2: Passive Bridge Module

**Files:**
- Create: `rytm_randomizer/snapshot_mock_runtime.py`

- [x] **Step 1: Add file-level safety boundary**

```python
"""Passive mock MIDI bridge for Rytm saved-snapshot mutation plans."""
```

- [x] **Step 2: Capture planned changes into `MockMidiSender`**

Each planned change becomes one `build_cc_message(...)` call with wire channel
`midi_channel - 1` and metadata preserving pad, machine, parameter, baseline,
planned value, and delta.

- [x] **Step 3: Format deterministic report**

The report includes slot, kit, depth, planned pad count, planned change count,
mock sender count, mock stream preview, mutation policy, and safety text.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Add CLI route**

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mock-runtime-report <path> --slot <1-128> --depth <micro|groove|strong>
```

- [x] **Step 2: Add help text and top-level usage**

The help entry explains that the command captures planned CC moves into an inert
mock sender and does not send MIDI.

### Task 4: Verification

**Files:**
- Test: `tests/test_snapshot_mock_runtime.py`
- Test: `tests/test_cli.py`
- Test: `tests/architecture/test_no_side_effects.py`
- Test: `tests/architecture/test_observability.py`

- [x] **Step 1: Run focused tests**

```powershell
pytest tests\test_snapshot_mock_runtime.py tests\test_cli.py::test_sysex_snapshot_mock_runtime_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

Expected: pass.

- [x] **Step 2: Run broader passive safety tests**

```powershell
pytest tests\test_snapshot_mock_runtime.py tests\test_snapshot_mutation_planner.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

Expected: pass.

- [x] **Step 3: Run full suite**

```powershell
pytest -q
```

Expected: pass.
