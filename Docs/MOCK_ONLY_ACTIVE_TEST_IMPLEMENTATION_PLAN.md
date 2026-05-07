# Mock-Only Active Test Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Subagent-driven development is not recommended for this plan because the work is small, touches shared closeout state, and should remain in one review thread.

**Goal:** Add focused mock-only test coverage for the accepted first candidate, group profile `"2"` / My BD Hard, without adding active behavior.

**Architecture:** This is a coverage-only implementation plan. It adds one mock-only test file that exercises the existing `rytm_randomizer.mock_message_mapper` and `rytm_randomizer.mock_midi` boundaries. No runtime module, CLI command, real MIDI backend, port provider, or hardware-facing path is created.

**Tech Stack:** Python standard library, existing project test style, `MockMidiSender`, `MidiMessage`, `map_group_profile_to_mock_messages`, PowerShell closeout.

---

## 1. Purpose

Define the exact future implementation steps for the first mock-only active
test candidate.

This document is a plan only. It does not create tests, edit code, open ports,
send MIDI, add active execution, wire CLI behavior, or require hardware.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 66623ef Add first-candidate mock-only active test design review

Current accepted candidate:

- group profile `"2"` / My BD Hard

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. File Structure

Future implementation should touch only these files:

- Create: `tests/test_mock_only_active_candidate.py`
- Modify: `Scripts/closeout_check.ps1`

No other files should be changed unless the first test run exposes a genuine
gap in existing mock-only helpers.

Files that must not be edited:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- runtime execution/dispatch logic
- existing metadata source files

## 4. Expected Test Scope

The future test file should prove:

- group profile `"2"` maps to deterministic inert mock messages
- the candidate message has expected metadata
- `MockMidiSender` records the candidate message in order
- unknown keys emit no messages and fail safely
- unsupported profile `"4"` emits no messages and fails safely
- passive CLI report behavior remains unchanged
- no real MIDI library is imported
- no active behavior names are exposed
- V1.34 reference remains untouched through closeout

The future test file should not:

- add profile `"4"` support
- add real MIDI
- import `mido`
- open ports
- send MIDI
- add active CLI commands
- add hardware behavior

## 5. Task 1: Add Candidate Test File

**Files:**

- Create: `tests/test_mock_only_active_candidate.py`

- [ ] **Step 1: Create the mock-only candidate test file**

Create `tests/test_mock_only_active_candidate.py` with this content:

```python
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def fixture_text(filename):
    return normalize_newlines((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_first_candidate_profile_2_maps_to_expected_mock_message():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MidiMessage

    messages = map_group_profile_to_mock_messages("2")

    assert len(messages) == 1
    assert isinstance(messages[0], MidiMessage)
    assert messages[0].message_type == "mock_group_profile"
    assert messages[0].channel == 1
    assert messages[0].control == 0
    assert messages[0].value == 0


def test_first_candidate_profile_2_metadata_is_inert_and_explicit():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages

    message = map_group_profile_to_mock_messages("2")[0]

    assert message.metadata == {
        "source_kind": "group_profile",
        "source_key": "2",
        "source_name": "My BD Hard",
        "group_pad": 1,
        "machine_value": 0,
        "target": "Pad 1 / BD Hard",
        "mock_only": True,
        "sends_real_midi": False,
    }


def test_first_candidate_messages_are_deterministic():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages

    first = map_group_profile_to_mock_messages("2")
    second = map_group_profile_to_mock_messages("2")

    assert first == second


def test_first_candidate_records_through_mock_sender_only():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MockMidiSender

    messages = map_group_profile_to_mock_messages("2")
    sender = MockMidiSender()

    sender.send_many(messages)

    assert sender.sent_messages == tuple(messages)


def test_unknown_candidate_key_emits_no_messages():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()

    try:
        sender.send_many(map_group_profile_to_mock_messages("DOES_NOT_EXIST"))
    except MockMessageMappingError as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("unknown candidate key should fail safely")

    assert sender.sent_messages == ()


def test_unsupported_profile_4_emits_no_messages_and_remains_parked():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()

    try:
        sender.send_many(map_group_profile_to_mock_messages("4"))
    except MockMessageMappingError as exc:
        assert "is not supported by the mock mapper" in str(exc)
    else:
        raise AssertionError("profile 4 should remain unsupported")

    assert sender.sent_messages == ()


def test_first_candidate_imports_no_real_midi_libraries():
    import rytm_randomizer.mock_message_mapper  # noqa: F401
    import rytm_randomizer.mock_midi  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_stays_read_only():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_active_behavior_names_are_exposed_by_candidate_modules():
    import rytm_randomizer.mock_message_mapper as mapper
    import rytm_randomizer.mock_midi as mock_midi

    exposed_names = set(dir(mapper)) | set(dir(mock_midi))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
```

- [ ] **Step 2: Run the new test file directly**

Run:

```powershell
python .\tests\test_mock_only_active_candidate.py
```

Expected:

- exit code `0`
- no output
- no hardware required
- no ports opened
- no MIDI sent

If the command fails because `python` is not available, run the full closeout
instead, because closeout resolves the project Python command.

## 6. Task 2: Add Closeout Coverage

**Files:**

- Modify: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Add the closeout label and test invocation**

In `Scripts/closeout_check.ps1`, add this block after the existing
`=== Test: Mock Mapper Report ===` block:

```powershell
"" | Add-Content $summary
"=== Test: Mock-Only Active Candidate ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_only_active_candidate.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_only_active_candidate.log" | Add-Content $summary
```

- [ ] **Step 2: Run closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- closeout completes
- output includes `=== Test: Mock-Only Active Candidate ===`
- no failure output appears under that label

## 7. Task 3: Verify Safety Boundaries

**Files:**

- No file changes in this task

- [ ] **Step 1: Verify V1.34 reference diff**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected:

- no output

- [ ] **Step 2: Verify only approved files changed**

Run:

```powershell
git status --short
```

Expected before commit:

```text
 M Scripts/closeout_check.ps1
?? tests/test_mock_only_active_candidate.py
```

If any runtime, CLI, metadata, or V1.34 file appears, stop and review before
continuing.

## 8. Task 4: Commit The Mock-Only Test Slice

**Files:**

- Stage: `tests/test_mock_only_active_candidate.py`
- Stage: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Stage the approved files**

Run:

```powershell
git add .\tests\test_mock_only_active_candidate.py `
        .\Scripts\closeout_check.ps1
```

- [ ] **Step 2: Commit**

Run:

```powershell
git commit -m "Add mock-only active candidate tests"
```

- [ ] **Step 3: Run final closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

Expected:

- closeout passes
- V1.34 reference diff is empty
- `git status --short` prints nothing

## 9. Forbidden Scope

The implementation slice must not add:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- active execution
- active CLI commands
- CLI wiring to active behavior
- dispatch
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- profile `"4"` implementation
- hardware validation

## 10. Self-Review

Spec coverage:

- first candidate group profile `"2"` is covered
- deterministic messages are covered
- metadata inspection is covered
- `MockMidiSender` recording is covered
- unknown and unsupported failure paths are covered
- passive CLI read-only regression is covered
- no-real-MIDI import checks are covered
- V1.34 reference check is covered through closeout

Placeholder scan:

- no placeholder work remains in this plan

Type and API consistency:

- uses existing `map_group_profile_to_mock_messages`
- uses existing `MockMessageMappingError`
- uses existing `MockMidiSender`
- uses existing `MidiMessage`

## 11. Decision

This plan is ready for a future mock-only implementation slice.

Recommended execution approach:

- Inline execution in the main thread
- no subagents yet
- one small commit

Hardware remains off.
