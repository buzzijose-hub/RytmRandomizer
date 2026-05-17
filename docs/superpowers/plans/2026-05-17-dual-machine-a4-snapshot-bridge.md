# Dual-Machine A4 Snapshot Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let the passive dual-machine mock bridge use saved Analog Four snapshot mock events when an A4 snapshot path is supplied.

**Architecture:** Extend `dual_machine_mock_bridge.py` with snapshot-backed A4 bridge changes while preserving the safe-starter fallback. Extend the CLI parser for optional `--analog-four-path` and `--analog-four-slot`, then update help text and tests.

**Tech Stack:** Python dataclasses, existing passive CLI/help pattern, pytest.

---

### Task 1: Failing Tests

**Files:**
- Modify: `tests/test_dual_machine_mock_bridge.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Add A4 synthetic kit helper**

Add a local `make_a4_kit_record()` helper to `tests/test_dual_machine_mock_bridge.py`
matching the A4 snapshot planner fixtures.

- [x] **Step 2: Add bridge API test**

Assert that calling `build_dual_machine_mock_bridge(..., analog_four_sysex_path=<path>, analog_four_slot=1)` changes `analog_four_source` to snapshot candidates, captures `saved_offset_candidate` A4 messages, and preserves Rytm CC messages.

- [x] **Step 3: Add CLI test**

Assert the existing command accepts:

```powershell
dual-machine-mock-bridge-report <rytm-path> --slot 1 --depth micro --analog-four-path <a4-path> --analog-four-slot 1
```

The report should include the A4 source path, A4 kit name, candidate status,
and no CC mapping claim.

- [x] **Step 4: Add help assertion**

Update the dual bridge help test to assert `--analog-four-path` and
`--analog-four-slot` are documented.

### Task 2: Bridge Implementation

**Files:**
- Modify: `rytm_randomizer/dual_machine_mock_bridge.py`

- [x] **Step 1: Add snapshot bridge change dataclass**

Create an A4 snapshot change representation with track, channel, track name,
saved offset, word index, baseline, planned value, delta, mapping status, and
source.

- [x] **Step 2: Add optional A4 snapshot plan builder**

Extend `build_dual_machine_mock_bridge()` with `analog_four_sysex_path=None` and
`analog_four_slot=None`. If path is absent, keep the safe-starter plan. If path
is present, require a slot and build A4 snapshot-backed track plans.

- [x] **Step 3: Capture A4 snapshot events**

When an A4 snapshot-backed change is present, capture it as a `MidiMessage` with
`message_type="saved_offset_candidate"` instead of `build_cc_message()`.

- [x] **Step 4: Format report lines**

Show A4 source path, slot, kit, candidate status, and no-CC-mapping policy only
when snapshot-backed A4 is active.

### Task 3: CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [x] **Step 1: Parse optional A4 snapshot flags**

Accept both old and new forms, with optional target at the end.

- [x] **Step 2: Update usage/help text**

Document the snapshot-backed A4 form and the safe-starter fallback.

### Task 4: Verification

- [x] **Step 1: Focused tests**

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_dual_machine_mock_bridge_report_help_exits_zero tests\test_cli.py::test_top_level_help_exits_zero_and_matches_fixture -q
```

- [x] **Step 2: Real dual dump check**

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1
```

- [x] **Step 3: Broader passive tests**

```powershell
pytest tests\test_dual_machine_mock_bridge.py tests\test_analog_four_snapshot_mock_runtime.py tests\test_cli.py tests\architecture\test_no_side_effects.py tests\architecture\test_observability.py -q
```

- [x] **Step 4: Full suite**

```powershell
pytest -q
```
