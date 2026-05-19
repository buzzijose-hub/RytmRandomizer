# A4-Only Snapshot Independence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let Analog-Four-only snapshot planning run from an Analog Four saved kit source without requiring any Rytm snapshot file.

**Architecture:** Keep the existing dual-machine bridge as the shared boundary, but make the Rytm side optional when the normalized target is `analog-four`. The bridge will synthesize an inactive zero-pad Rytm plan for report compatibility, and the CLI/app argument layers will stop requiring Rytm snapshot inputs for A4-only runs.

**Tech Stack:** Python dataclasses, existing passive CLI parser, existing app entry point, pytest, Black, Ruff, isort.

---

### Task 1: Shared Bridge Independence

**Files:**
- Modify: `rytm_randomizer/dual_machine/mock_bridge.py`
- Test: `tests/test_dual_machine_mock_bridge.py`

- [ ] **Step 1: Write the failing bridge test**

```python
def test_dual_bridge_analog_four_target_can_omit_rytm_snapshot_path(tmp_path):
    from rytm_randomizer.dual_machine.mock_bridge import (
        build_dual_machine_mock_bridge,
        capture_dual_machine_mock_messages,
        format_dual_machine_mock_bridge_report,
    )

    a4_path = tmp_path / "a4-kits.syx"
    a4_path.write_bytes(make_a4_kit_record(kit_name="A4 SOLO", track_values={1: {20: 64}}))

    bridge = build_dual_machine_mock_bridge(
        None,
        slot=None,
        depth="micro",
        target="analog-four",
        analog_four_sysex_path=str(a4_path),
        analog_four_slot=1,
    )
    sender = capture_dual_machine_mock_messages(bridge)
    report = "\n".join(format_dual_machine_mock_bridge_report(bridge))

    assert bridge.target_plan.canonical_target == "analog-four"
    assert bridge.rytm_source == "not captured for target analog-four"
    assert bridge.rytm_plan.scanned_pad_count == 0
    assert bridge.rytm_message_count == 0
    assert bridge.analog_four_source == "saved-kit snapshot candidates"
    assert {message.metadata["device"] for message in sender.sent_messages} == {
        "Analog Four MKII"
    }
    assert "Rytm source path: <not required>" in report
    assert "Rytm planned pads: 0 / 0" in report
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests\test_dual_machine_mock_bridge.py::test_dual_bridge_analog_four_target_can_omit_rytm_snapshot_path -q`

Expected: fail because `build_dual_machine_mock_bridge()` currently requires and decodes a Rytm path.

- [ ] **Step 3: Implement inactive Rytm plan**

Change `build_dual_machine_mock_bridge()` to accept `rytm_sysex_path: str | Path | None` and `slot: int | None`, then:

```python
if _is_device_active_key(target_plan, "analog_rytm"):
    if rytm_sysex_path is None or slot is None:
        raise ValueError("Rytm snapshot path and slot are required for target rytm or both")
    rytm_plan = build_snapshot_mutation_plan_from_file(rytm_sysex_path, slot=slot, depth=depth)
else:
    rytm_plan = _build_inactive_rytm_plan(depth)
```

The inactive plan is:

```python
SnapshotMutationPlan(
    slot_number=0,
    kit_name="",
    depth=depth,
    snapshot_parameter_map_status="not_captured_for_target_analog_four",
    pads=(),
)
```

- [ ] **Step 4: Verify green**

Run: `python -m pytest tests\test_dual_machine_mock_bridge.py::test_dual_bridge_analog_four_target_can_omit_rytm_snapshot_path tests\test_dual_machine_mock_bridge.py -q`

Expected: all selected tests pass.

### Task 2: Passive CLI Pathless A4-Only Form

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Test: `tests/test_dual_machine_mock_bridge.py`
- Test: `tests/test_cli.py`

- [ ] **Step 1: Write failing CLI test**

```python
def test_dual_machine_mock_bridge_cli_accepts_a4_only_without_rytm_path(tmp_path):
    a4_path = tmp_path / "a4-kits.syx"
    a4_path.write_bytes(make_a4_kit_record(kit_name="CLI A4 SOLO", track_values={1: {20: 64}}))

    result = run_cli(
        "dual-machine-mock-bridge-report",
        "--target",
        "analog-four",
        "--depth",
        "micro",
        "--analog-four-path",
        str(a4_path),
        "--analog-four-slot",
        "1",
    )

    assert result.returncode == 0
    assert "Target: analog-four" in result.stdout
    assert "Rytm source path: <not required>" in result.stdout
    assert "Analog Four kit: CLI A4 SOLO" in result.stdout
    assert "Analog Four mock messages: 1" in result.stdout
    assert result.stderr == ""
```

- [ ] **Step 2: Verify red**

Run: `python -m pytest tests\test_dual_machine_mock_bridge.py::test_dual_machine_mock_bridge_cli_accepts_a4_only_without_rytm_path -q`

Expected: usage failure because the parser currently requires a positional Rytm path and `--slot`.

- [ ] **Step 3: Implement parser support**

Refactor `_parse_dual_machine_bridge_cli_args()` to return `rytm_path`, `slot`, and `depth`. Preserve the old positional form:

```text
dual-machine-mock-bridge-report <rytm-path> --slot 1 --depth micro ...
```

Add the new A4-only form:

```text
dual-machine-mock-bridge-report --target analog-four --depth micro --analog-four-path <a4-path> --analog-four-slot 1
```

Reject pathless forms unless `target` normalizes to `analog-four`.

- [ ] **Step 4: Wire parser output**

Every CLI command that calls `build_dual_machine_mock_bridge()` should pass `parsed["rytm_path"]` instead of `args[1]`, and error formatting should use `parsed["rytm_path"] or "<not required>"`.

- [ ] **Step 5: Verify green**

Run: `python -m pytest tests\test_dual_machine_mock_bridge.py tests\test_cli.py::test_dual_machine_mock_bridge_help_exits_zero -q`

Expected: all selected tests pass.

### Task 3: App Dry-Run A4-Only Snapshot Send

**Files:**
- Modify: `rytm_randomizer/app.py`
- Test: `tests/test_app_entry.py`

- [ ] **Step 1: Write failing app test**

Add a dry-run test showing:

```text
--dry-run --dual-machine-snapshot-send --snapshot-target analog-four --snapshot-depth micro --analog-four-path <a4> --analog-four-slot 1
```

works without `--snapshot-path` or `--snapshot-slot`.

- [ ] **Step 2: Verify red**

Run the one app test and confirm the current validation rejects missing `--snapshot-path` and `--snapshot-slot`.

- [ ] **Step 3: Relax app validation**

For `--dual-machine-snapshot-send`, require `--snapshot-depth` and `--snapshot-target` always. Require `--snapshot-path` and `--snapshot-slot` only when target includes Rytm. Require `--analog-four-path` and `--analog-four-slot` when target is `analog-four` and the request is intended to use saved A4 snapshots.

- [ ] **Step 4: Verify green**

Run the app test plus existing dual-machine snapshot app tests.

### Task 4: Documentation And Gate

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/DUAL_MACHINE_MOCK_BRIDGE_CHECKPOINT.md`

- [ ] **Step 1: Update operator docs**

Add the new A4-only command shape and explain that no Rytm file is required for `--target analog-four`.

- [ ] **Step 2: Run verification**

Run:

```powershell
python -m pytest tests\test_dual_machine_mock_bridge.py tests\test_dual_machine_guarded_sender.py tests\test_app_entry.py -q
python -m pytest tests\architecture -q
python -m pytest -m fast -q
python -m pytest -q
python -m black --check .
python -m ruff check .
python -m isort --check-only rytm_randomizer tests
git diff --check
```

- [ ] **Step 3: Commit and push**

Commit with:

```powershell
git add docs\STATUS.md docs\DUAL_MACHINE_MOCK_BRIDGE_CHECKPOINT.md rytm_randomizer\dual_machine\mock_bridge.py rytm_randomizer\cli.py rytm_randomizer\help_text.py rytm_randomizer\app.py tests\test_dual_machine_mock_bridge.py tests\test_app_entry.py tests\test_cli.py docs\superpowers\plans\2026-05-19-a4-only-snapshot-independence.md
git commit -m "feat: allow A4-only snapshot bridge without Rytm path"
git push
```
