# V1.34 First Narrow Runtime/Active-Facing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the first narrow future implementation packet that can bridge runtime intent to the mock-only active boundary for profile `2` without adding real MIDI, ports, CLI execution wiring, runtime mutation, active CLI commands, or hardware behavior.

**Architecture:** Add one future mock-only bridge module that accepts an inert runtime intent, applies existing runtime-plan and active-boundary safety checks, and records messages through `MockMidiSender` only. The bridge remains package-internal/test-only, has no CLI entry point, imports no real MIDI libraries, and keeps unsupported/parked scope blocked.

**Tech Stack:** Python standard library dataclasses/typing, existing `rytm_randomizer.runtime_plan`, existing `rytm_randomizer.active_boundary`, existing `rytm_randomizer.mock_midi`, existing closeout PowerShell script.

---

## 1. Purpose

Create a concrete implementation plan for the first narrow runtime/active-facing
packet after the accepted passive/runtime visibility phase.

This document is a plan only.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `b4e5919 Add next branch selection after passive runtime visibility review`

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase
- passive/runtime visibility phase accepted
- first narrow runtime/active-facing implementation plan selected
- plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Planned Candidate

Planned first candidate:

- source kind: `group_profile`
- source key: `2`
- source name: My BD Hard
- target concept: Pad 1 / BD Hard
- current runtime-plan status: supported planning input, blocked by default
- current active-boundary status: accepted first mock-only active candidate
- message behavior: record inert mock `MidiMessage` data through
  `MockMidiSender` only

This planned candidate is still:

- mock-only
- test-only
- no real MIDI
- no ports
- no hardware
- no CLI execution wiring
- no runtime mutation
- blocked unless explicitly armed and dry-run confirmed in test-only code

## 4. Planned Future Files

Future implementation packet should create:

- `rytm_randomizer/mock_runtime_active_bridge.py`
  - owns the first mock-only bridge between runtime intent and active-boundary
    evaluation
  - imports only existing inert modules:
    - `rytm_randomizer.runtime_plan`
    - `rytm_randomizer.active_boundary`
    - `rytm_randomizer.mock_midi`
  - exposes no CLI command names
  - opens no ports
  - sends no real MIDI

- `tests/test_mock_runtime_active_bridge.py`
  - verifies the bridge is mock-only and inert
  - verifies profile `2` succeeds only when armed and dry-run confirmed
  - verifies all failure paths emit no messages
  - verifies profile `3`, profile `4`, unknown keys, and unsupported source
    kinds fail safely

Future implementation packet should update:

- `Scripts/closeout_check.ps1`
  - add one closeout section:
    - `=== Test: Mock Runtime Active Bridge ===`
  - run `tests/test_mock_runtime_active_bridge.py`

Future implementation packet must not update:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `pyproject.toml`
- `requirements.txt`
- `setup.py`
- `setup.cfg`
- existing metadata source files
- runtime dispatch/execution modules
- active CLI command modules

## 5. Planned Future Module Shape

Future module name:

- `rytm_randomizer.mock_runtime_active_bridge`

Planned public names:

- `RuntimeActiveBridgeRequest`
- `RuntimeActiveBridgeResult`
- `evaluate_mock_runtime_active_bridge`

Planned behavior:

- accept a `RuntimeActiveBridgeRequest`
- require a `MockMidiSender`
- build or consume an inert runtime intent
- validate runtime scope with `validate_runtime_intent_scope`
- refuse anything not supported by runtime planning
- require `armed=True`
- require `dry_run_confirmed=True`
- call `evaluate_mock_active_boundary` only after runtime scope, arming, and
  dry-run confirmation are valid
- return copied/immutable result metadata
- record messages in the supplied `MockMidiSender` only
- emit no messages on failure

Planned failure reasons:

- `missing_arming`
- `missing_dry_run_confirmation`
- `runtime_scope_blocked`
- `active_boundary_rejected`
- `unsupported_source_kind`
- `unsupported_or_unknown_key`
- `profile_4_parked`
- `invalid_request`
- `invalid_sender`

## 6. Future Implementation Tasks

### Task 1: Add Failing Bridge Tests

**Files:**

- Create: `tests/test_mock_runtime_active_bridge.py`

- [ ] **Step 1: Create import and safety tests**

```python
from pathlib import Path
import importlib
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_importing_mock_runtime_active_bridge_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.mock_runtime_active_bridge"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_bridge_imports_no_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.mock_runtime_active_bridge", None)
    importlib.import_module("rytm_randomizer.mock_runtime_active_bridge")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules
```

- [ ] **Step 2: Add the profile `2` success test**

```python
def test_profile_2_bridge_records_mock_messages_only_when_armed_and_confirmed():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is True
    assert result.reason == "accepted_mock_only"
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert result.would_execute is False
    assert result.emitted_messages == sender.sent_messages
    assert len(sender.sent_messages) == 1
    assert sender.sent_messages[0].metadata["source_key"] == "2"
```

- [ ] **Step 3: Add safe-failure tests**

```python
def test_missing_arming_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=False,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_missing_dry_run_confirmation_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=True,
        dry_run_confirmed=False,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()
```

- [ ] **Step 4: Add unsupported and parked scope tests**

```python
def test_profile_3_remains_runtime_supported_but_bridge_rejected():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="3",
        target="Pad 2 / My BD Classic",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "active_boundary_rejected"
    assert result.metadata["runtime_supported"] is True
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_4_remains_parked_and_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="4",
        target="Pad 1 / My BD Acoustic",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "profile_4_parked"
    assert result.metadata["parked"] is True
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()
```

- [ ] **Step 5: Run the new test file and confirm it fails for the missing module**

Run:

```powershell
python .\tests\test_mock_runtime_active_bridge.py
```

Expected result before implementation:

```text
ModuleNotFoundError: No module named 'rytm_randomizer.mock_runtime_active_bridge'
```

### Task 2: Add The Mock Runtime/Active Bridge

**Files:**

- Create: `rytm_randomizer/mock_runtime_active_bridge.py`

- [ ] **Step 1: Create the module with inert dataclasses**

```python
"""Mock-only bridge from runtime intent to active-boundary evaluation.

This module is test-only and inert. It does not import MIDI libraries, open
ports, send real MIDI, expose CLI commands, dispatch runtime behavior, mutate
runtime state, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from .active_boundary import ActiveBoundaryRequest, evaluate_mock_active_boundary
from .mock_midi import MidiMessage, MockMidiSender
from .runtime_plan import RuntimeIntent, validate_runtime_intent_scope


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class RuntimeActiveBridgeRequest:
    """Mock-only request for the first narrow runtime/active bridge."""

    source_kind: str
    source_key: str
    target: str
    armed: bool = False
    dry_run_confirmed: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_key", str(self.source_key))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


@dataclass(frozen=True)
class RuntimeActiveBridgeResult:
    """Mock-only result for the first narrow runtime/active bridge."""

    accepted: bool
    reason: str
    emitted_messages: tuple[MidiMessage, ...] = ()
    would_execute: bool = False
    mock_only: bool = True
    sends_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "emitted_messages", tuple(self.emitted_messages))
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))
```

- [ ] **Step 2: Add the bridge evaluation behavior**

```python
def _runtime_intent_from_request(request: RuntimeActiveBridgeRequest) -> RuntimeIntent:
    return RuntimeIntent(
        source_kind=request.source_kind,
        source_key=request.source_key,
        target=request.target,
        armed=request.armed,
        metadata=request.metadata,
    )


def _base_metadata(
    request: RuntimeActiveBridgeRequest,
    *,
    reason: str,
    runtime_supported: bool = False,
    parked: bool = False,
) -> dict[str, object]:
    return {
        "source_kind": request.source_kind,
        "source_key": request.source_key,
        "target": request.target,
        "armed": request.armed,
        "dry_run_confirmed": request.dry_run_confirmed,
        "runtime_supported": runtime_supported,
        "parked": parked,
        "reason": reason,
        "mock_only": True,
        "sends_real_midi": False,
        "would_execute": False,
    }


def _failure(
    request: RuntimeActiveBridgeRequest,
    reason: str,
    *,
    runtime_supported: bool = False,
    parked: bool = False,
) -> RuntimeActiveBridgeResult:
    return RuntimeActiveBridgeResult(
        accepted=False,
        reason=reason,
        emitted_messages=(),
        metadata=_base_metadata(
            request,
            reason=reason,
            runtime_supported=runtime_supported,
            parked=parked,
        ),
    )


def evaluate_mock_runtime_active_bridge(
    request: RuntimeActiveBridgeRequest,
    sender: MockMidiSender,
) -> RuntimeActiveBridgeResult:
    """Evaluate one mock-only runtime intent through the active boundary."""

    if not isinstance(request, RuntimeActiveBridgeRequest):
        raise TypeError("request must be a RuntimeActiveBridgeRequest")
    if not isinstance(sender, MockMidiSender):
        raise TypeError("sender must be a MockMidiSender")

    if not request.armed:
        return _failure(request, "missing_arming")
    if not request.dry_run_confirmed:
        return _failure(request, "missing_dry_run_confirmation")

    runtime_preview = validate_runtime_intent_scope(_runtime_intent_from_request(request))
    runtime_supported = bool(runtime_preview.metadata["supported"])
    parked = bool(runtime_preview.metadata["parked"])

    if request.source_kind != "group_profile":
        return _failure(request, "unsupported_source_kind")
    if parked:
        return _failure(request, "profile_4_parked", parked=True)
    if not runtime_supported:
        return _failure(request, "unsupported_or_unknown_key")

    boundary_result = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind=request.source_kind,
            source_key=request.source_key,
            armed=request.armed,
            dry_run_confirmed=request.dry_run_confirmed,
            target=request.target,
            metadata=request.metadata,
        ),
        sender,
    )

    if not boundary_result.accepted:
        return _failure(
            request,
            "active_boundary_rejected",
            runtime_supported=runtime_supported,
            parked=parked,
        )

    return RuntimeActiveBridgeResult(
        accepted=True,
        reason=boundary_result.reason,
        emitted_messages=boundary_result.emitted_messages,
        metadata=_base_metadata(
            request,
            reason=boundary_result.reason,
            runtime_supported=runtime_supported,
            parked=parked,
        ),
    )
```

- [ ] **Step 3: Run the bridge tests**

Run:

```powershell
python .\tests\test_mock_runtime_active_bridge.py
```

Expected result after implementation:

```text
<no output>
```

### Task 3: Add Closeout Coverage

**Files:**

- Modify: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Add the closeout section**

```powershell
"=== Test: Mock Runtime Active Bridge ===" | Add-Content $summary
& $pythonExe @pythonArgs .\tests\test_mock_runtime_active_bridge.py 2>&1 | Tee-Object -FilePath "$logDir\latest_test_mock_runtime_active_bridge.log" | Add-Content $summary
```

- [ ] **Step 2: Run full closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected result:

```text
Closeout complete.
```

### Task 4: Protected Diff And Status Checks

**Files:**

- No file edits in this task.

- [ ] **Step 1: Confirm protected diffs and status**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected `git status --short` result before commit:

```text
 M Scripts/closeout_check.ps1
?? rytm_randomizer/mock_runtime_active_bridge.py
?? tests/test_mock_runtime_active_bridge.py
```

Expected protected diff output:

```text

```

### Task 5: Commit The Implementation Packet

**Files:**

- Stage:
  - `rytm_randomizer/mock_runtime_active_bridge.py`
  - `tests/test_mock_runtime_active_bridge.py`
  - `Scripts/closeout_check.ps1`

- [ ] **Step 1: Commit**

Run:

```powershell
git add .\rytm_randomizer\mock_runtime_active_bridge.py `
        .\tests\test_mock_runtime_active_bridge.py `
        .\Scripts\closeout_check.ps1

git commit -m "Add mock runtime active bridge"
```

- [ ] **Step 2: Run final closeout from committed state**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected result:

- closeout complete
- V1.34 reference diff empty
- package metadata diff empty
- `git status --short` no output

## 7. Required Preservation Checks

The future implementation packet must preserve:

- profile `2` success only through mock-only bridge with `MockMidiSender`
- profile `3` runtime-plan support but active-boundary rejection
- profile `4` parked behavior
- unknown keys safe failure
- unsupported source kinds safe failure
- missing arming safe failure
- missing dry-run confirmation safe failure
- passive CLI commands remaining read-only
- no real MIDI imports
- no port opening
- no MIDI sending
- no active CLI command names
- V1.34 reference untouched
- package metadata untouched

## 8. Non-Goals For The Future Implementation Packet

The future implementation packet must not add:

- CLI command
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- package metadata changes
- profile `4` mapper support
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- hardware behavior
- hardware validation

## 9. Review Gate Before Implementation

Before executing this plan, create a documentation-only review/acceptance gate
for this plan.

The review gate should confirm:

- the candidate remains profile `2` only
- the bridge remains mock-only
- no CLI wiring is planned
- no real MIDI is planned
- no ports are planned
- no hardware is planned
- profile `3` and profile `4` remain non-success cases
- V1.34 and package metadata remain protected

## 10. Self-Review

Spec coverage:

- exact goal and non-goals are documented
- candidate scope is profile `2` only
- future files are listed
- future tests are listed with concrete test code
- closeout and protected diff expectations are listed
- passive CLI and unsupported/parked behavior remain protected

Placeholder scan:

- no unresolved markers
- no unresolved task names
- no unspecified future file paths

Type consistency:

- `RuntimeActiveBridgeRequest`, `RuntimeActiveBridgeResult`, and
  `evaluate_mock_runtime_active_bridge` are named consistently across tests and
  implementation steps

## 11. Decision

This plan is ready for a documentation-only review/acceptance checkpoint.

No implementation in this slice.

Hardware remains off.
