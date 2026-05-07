# Active Boundary Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. Subagent-driven development is not recommended for this plan because the first boundary is small, candidate-specific, and should remain in one review thread.

**Goal:** Implement the first mock-first active boundary for group profile `"2"` / My BD Hard without real MIDI, ports, CLI wiring, or hardware behavior.

**Architecture:** Add one small `active_boundary.py` module that accepts a request, checks mock-only arming requirements, and emits inert `MidiMessage` objects through an injected `MockMidiSender` only when the request is armed and dry-run confirmed. Add one focused test file and one closeout label. The passive CLI, real MIDI, dispatch, hardware, and profile `"4"` remain untouched.

**Tech Stack:** Python standard library, dataclasses, existing `MockMidiSender`, existing `MidiMessage`, existing `map_group_profile_to_mock_messages`, existing PowerShell closeout.

---

## 1. Purpose

Define the exact future implementation steps for the first mock-first active
boundary.

This is a plan only. It does not create code, tests, MIDI behavior, port
opening, active CLI commands, dispatch, or hardware behavior in this slice.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ef5cfa6 Add active boundary implementation design review

Accepted candidate:

- group profile `"2"` / My BD Hard

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. File Structure

Future implementation should touch only:

- Create: `rytm_randomizer/active_boundary.py`
- Create: `tests/test_active_boundary.py`
- Modify: `Scripts/closeout_check.ps1`

Files that must not be edited:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- runtime execution/dispatch modules
- metadata source files

## 4. Task 1: Write Active Boundary Tests

**Files:**

- Create: `tests/test_active_boundary.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_active_boundary.py` with this content:

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


def test_importing_active_boundary_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.active_boundary"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_missing_arming_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=False,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert sender.sent_messages == ()


def test_missing_dry_run_confirmation_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=False,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_unknown_key_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="DOES_NOT_EXIST",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_4_remains_parked_and_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="4",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_2_emits_mock_messages_only_when_armed_and_confirmed():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
        metadata={"operator_intent": "mock-only candidate proof"},
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is True
    assert result.reason == "accepted_mock_only"
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert result.emitted_messages == sender.sent_messages
    assert len(result.emitted_messages) == 1
    assert result.emitted_messages[0].metadata["source_key"] == "2"
    assert result.emitted_messages[0].metadata["mock_only"] is True
    assert result.emitted_messages[0].metadata["sends_real_midi"] is False


def test_passive_cli_report_stays_read_only():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_real_midi_libraries_are_imported():
    import rytm_randomizer.active_boundary  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_active_cli_command_names_are_exposed():
    import rytm_randomizer.active_boundary as boundary

    exposed_names = set(dir(boundary))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names


if __name__ == "__main__":
    test_importing_active_boundary_prints_nothing()
    test_missing_arming_emits_no_messages()
    test_missing_dry_run_confirmation_emits_no_messages()
    test_unknown_key_emits_no_messages()
    test_profile_4_remains_parked_and_emits_no_messages()
    test_profile_2_emits_mock_messages_only_when_armed_and_confirmed()
    test_passive_cli_report_stays_read_only()
    test_no_real_midi_libraries_are_imported()
    test_no_active_cli_command_names_are_exposed()
```

- [ ] **Step 2: Run the test to confirm it fails before implementation**

Run:

```powershell
python .\tests\test_active_boundary.py
```

Expected:

- failure because `rytm_randomizer.active_boundary` does not exist

If `python` is not available, use the project closeout command after Task 2.

## 5. Task 2: Implement Mock-First Active Boundary

**Files:**

- Create: `rytm_randomizer/active_boundary.py`

- [ ] **Step 1: Create the module**

Create `rytm_randomizer/active_boundary.py` with this content:

```python
"""Mock-first active boundary for tests only.

This module does not import MIDI libraries, open ports, send MIDI, expose CLI
commands, dispatch runtime behavior, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .mock_message_mapper import map_group_profile_to_mock_messages
from .mock_midi import MidiMessage, MockMidiSender

SUPPORTED_SOURCE_KIND = "group_profile"
SUPPORTED_SOURCE_KEY = "2"


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class ActiveBoundaryRequest:
    """Mock-only request for the future active boundary."""

    source_kind: str
    source_key: str
    armed: bool = False
    dry_run_confirmed: bool = False
    target: str = "mock"
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_key", str(self.source_key))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class ActiveBoundaryResult:
    """Mock-only active boundary result."""

    accepted: bool
    emitted_messages: tuple[MidiMessage, ...]
    reason: str
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class ActiveBoundaryError(ValueError):
    """Raised when active boundary inputs are invalid for tests."""


def _failure(reason: str, request: ActiveBoundaryRequest) -> ActiveBoundaryResult:
    return ActiveBoundaryResult(
        accepted=False,
        emitted_messages=(),
        reason=reason,
        metadata={
            "source_kind": request.source_kind,
            "source_key": request.source_key,
            "mock_only": True,
            "sends_real_midi": False,
        },
    )


def evaluate_mock_active_boundary(
    request: ActiveBoundaryRequest,
    sender: MockMidiSender,
) -> ActiveBoundaryResult:
    """Evaluate the accepted candidate through the mock-only active boundary."""

    if not isinstance(request, ActiveBoundaryRequest):
        raise TypeError("request must be an ActiveBoundaryRequest")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not request.armed:
        return _failure("missing_arming", request)
    if not request.dry_run_confirmed:
        return _failure("missing_dry_run_confirmation", request)
    if request.source_kind != SUPPORTED_SOURCE_KIND:
        return _failure("unsupported_source_kind", request)
    if request.source_key != SUPPORTED_SOURCE_KEY:
        return _failure("unsupported_or_unknown_key", request)

    messages = tuple(map_group_profile_to_mock_messages(SUPPORTED_SOURCE_KEY))
    sender.send_many(messages)
    return ActiveBoundaryResult(
        accepted=True,
        emitted_messages=messages,
        reason="accepted_mock_only",
        metadata={
            "source_kind": request.source_kind,
            "source_key": request.source_key,
            "target": request.target,
            "mock_only": True,
            "sends_real_midi": False,
        },
    )
```

- [ ] **Step 2: Run the active boundary test**

Run:

```powershell
python .\tests\test_active_boundary.py
```

Expected:

- exit code `0`
- no output

## 6. Task 3: Add Closeout Coverage

**Files:**

- Modify: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Add the closeout label**

In `Scripts/closeout_check.ps1`, add this block after the existing
`=== Test: Mock-Only Active Candidate ===` block:

```powershell
"" | Add-Content $summary
"=== Test: Active Boundary ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_active_boundary.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_active_boundary.log" | Add-Content $summary
```

- [ ] **Step 2: Run closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- closeout completes
- output includes `=== Test: Active Boundary ===`
- no failure output appears under that label

## 7. Task 4: Verify Safety Boundaries

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
?? rytm_randomizer/active_boundary.py
?? tests/test_active_boundary.py
```

If `rytm_randomizer/cli.py`, runtime execution files, metadata files, or
`rytm_hybrid_randomizer_v134.py` appear, stop and review before continuing.

## 8. Task 5: Commit The Active Boundary Slice

**Files:**

- Stage: `rytm_randomizer/active_boundary.py`
- Stage: `tests/test_active_boundary.py`
- Stage: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Stage approved files**

Run:

```powershell
git add .\rytm_randomizer\active_boundary.py `
        .\tests\test_active_boundary.py `
        .\Scripts\closeout_check.ps1
```

- [ ] **Step 2: Commit**

Run:

```powershell
git commit -m "Add mock-first active boundary"
```

- [ ] **Step 3: Final closeout**

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

This implementation must not add:

- real MIDI
- mido
- MIDI port opening
- MIDI sending
- hardware detection
- hardware send
- active CLI commands
- CLI wiring to active behavior
- dispatch
- command execution
- scene execution
- hardware behavior
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- execute-command
- send-command
- hardware-test
- hardware validation
- profile `"4"` implementation

## 10. Self-Review

Spec coverage:

- accepted candidate `"2"` is covered
- arming failure is covered
- dry-run confirmation failure is covered
- unknown key failure is covered
- profile `"4"` parked behavior is covered
- success path through `MockMidiSender` is covered
- passive CLI regression is covered
- no-real-MIDI import check is covered
- closeout coverage is defined

Placeholder scan:

- no placeholder work remains in this plan

Type and API consistency:

- uses `ActiveBoundaryRequest`
- uses `ActiveBoundaryResult`
- defines `ActiveBoundaryError`
- uses `evaluate_mock_active_boundary(request, sender)`
- uses existing `MockMidiSender`
- uses existing `MidiMessage`
- uses existing `map_group_profile_to_mock_messages`

## 11. Decision

This plan is ready for a future mock-first active boundary implementation
slice.

Recommended execution approach:

- inline execution in the main thread
- no subagents yet
- one small commit

Hardware remains off.
