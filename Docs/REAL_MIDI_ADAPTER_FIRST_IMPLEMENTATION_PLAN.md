# Real MIDI Adapter First Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Plan the first future implementation slice for a narrow real MIDI
adapter boundary without adding real MIDI dependencies, opening ports, sending
MIDI, adding active CLI commands, or touching hardware.

**Architecture:** The future implementation should create a small
`rytm_randomizer/real_midi_adapter.py` boundary that is import-safe,
dependency-absent-safe, fake-provider-testable, and completely unwired from
passive CLI behavior. The adapter boundary should expose explicit provider and
sender concepts while using fake providers in tests only; dependency selection
and hardware validation remain separate future gates.

**Tech Stack:** Python standard library only, existing
`rytm_randomizer.mock_midi.MidiMessage`, existing closeout coverage in
`Scripts/closeout_check.ps1`, no `mido`, no real MIDI backend.

---

## 1. Purpose

Define the future first implementation slice for the real MIDI adapter
boundary.

This is an implementation plan only.

This document does not implement an adapter.

This document does not add tests.

This document does not add dependencies, import real MIDI libraries, open
ports, send MIDI, add active CLI commands, add hardware behavior, or start
hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 507ee2e Add real MIDI adapter first implementation design review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- real MIDI adapter boundary safety tests are in closeout
- first adapter implementation design/spec is reviewed and accepted
- first adapter implementation plan is now being documented

Accepted safety baseline:

- real MIDI import safety tests are in closeout
- real MIDI passive CLI safety tests are in closeout
- real MIDI adapter boundary safety tests are in closeout
- real MIDI dependency selection remains deferred
- `mido` remains absent
- no real MIDI backend exists
- no real MIDI adapter module exists
- no hardware validation has started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Scope

The future implementation slice may create:

- `rytm_randomizer/real_midi_adapter.py`

The future implementation slice may modify:

- `tests/test_real_midi_adapter_boundary.py`

The future implementation slice should not modify:

- `Scripts/closeout_check.ps1`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_hybrid_randomizer_v134.py`
- package metadata
- runtime execution/dispatch code

No new closeout label should be needed because `tests/test_real_midi_adapter_boundary.py`
is already included in closeout as:

- `=== Test: Real MIDI Adapter Boundary ===`

## 4. Future File Responsibilities

Future `rytm_randomizer/real_midi_adapter.py` should own:

- import-safe adapter boundary definitions
- deterministic adapter errors
- fake-provider-friendly port provider boundary
- sender boundary that can send to fake ports in tests
- deterministic result objects for fake-provider sends
- CC-like translation from inert `MidiMessage` data to backend-neutral data

Future `tests/test_real_midi_adapter_boundary.py` should own:

- adapter import safety
- dependency absence safety
- fake provider behavior
- missing/unknown port safe failure
- sender construction guards
- fake-provider send behavior
- passive CLI regression safety
- active-boundary scope guard safety
- V1.34 reference protection

## 5. Non-Goals

Do not include:

- `mido`
- any real MIDI dependency
- package metadata changes
- real port listing
- real port opening
- real MIDI sending
- active CLI commands
- execute-command
- send-command
- hardware-test
- passive CLI wiring to the adapter
- command dispatch
- command execution
- scene execution
- SysEx
- GUI/capture
- Analog Four
- Pads 5-12
- machine/profile expansion
- profile `"4"` implementation
- profile `"3"` active-boundary support
- hardware validation
- turning hardware on

## 6. Implementation Tasks

### Task 1: Replace Adapter-Absence Test With Import-Safety Tests

**Files:**

- Modify: `tests/test_real_midi_adapter_boundary.py`

The current test file proves `rytm_randomizer/real_midi_adapter.py` does not
exist. The future implementation must replace that absence assertion with
import-safety assertions once the adapter file is introduced.

- [ ] **Step 1: Replace `test_real_midi_adapter_module_is_not_implemented_yet`**

Replace the existing test:

```python
def test_real_midi_adapter_module_is_not_implemented_yet():
    adapter_path = PROJECT_ROOT / "rytm_randomizer" / "real_midi_adapter.py"

    assert not adapter_path.exists()
    assert find_spec("rytm_randomizer.real_midi_adapter") is None
```

with:

```python
def test_real_midi_adapter_import_is_side_effect_free():
    result = run_python(
        """
import sys
import rytm_randomizer.real_midi_adapter as adapter

assert adapter.__name__ == "rytm_randomizer.real_midi_adapter"
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [ ] **Step 2: Run the new import-safety test and verify it fails first**

Run:

```powershell
python .\tests\test_real_midi_adapter_boundary.py
```

Expected before implementation:

- failure because `rytm_randomizer.real_midi_adapter` does not exist
- no hardware required
- no port opening
- no MIDI sending

- [ ] **Step 3: Do not edit passive source token guards**

Keep `PASSIVE_SOURCE_FILES` unchanged:

```python
PASSIVE_SOURCE_FILES = (
    PROJECT_ROOT / "rytm_randomizer" / "cli.py",
    PROJECT_ROOT / "rytm_randomizer" / "registry_report.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_midi.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_message_mapper.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_mapper_report.py",
    PROJECT_ROOT / "rytm_randomizer" / "active_boundary.py",
    PROJECT_ROOT / "rytm_randomizer" / "active_boundary_report.py",
)
```

The real adapter file is intentionally not a passive source file.

### Task 2: Add Dependency-Absent And Fake Provider Tests

**Files:**

- Modify: `tests/test_real_midi_adapter_boundary.py`

- [ ] **Step 1: Add dependency-absent safe failure test**

Add:

```python
def test_build_real_midi_sender_requires_explicit_provider():
    from rytm_randomizer.real_midi_adapter import (
        RealMidiDependencyError,
        build_real_midi_sender,
    )

    try:
        build_real_midi_sender(provider=None, port_name="Fake Rytm")
    except RealMidiDependencyError as exc:
        assert str(exc) == "real_midi_provider_required"
    else:
        raise AssertionError("expected RealMidiDependencyError")
```

- [ ] **Step 2: Add fake provider test helpers**

Add:

```python
class FakeOutputPort:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)
```

- [ ] **Step 3: Add unknown port safe failure test**

Add:

```python
def test_real_midi_port_provider_unknown_port_fails_safely():
    from rytm_randomizer.real_midi_adapter import (
        RealMidiPortError,
        RealMidiPortProvider,
    )

    provider = RealMidiPortProvider(output_names=("Fake Rytm",), ports={})

    try:
        provider.open_output("Missing Port")
    except RealMidiPortError as exc:
        assert str(exc) == "unknown_midi_output_port: Missing Port"
    else:
        raise AssertionError("expected RealMidiPortError")
```

- [ ] **Step 4: Add fake-provider send test**

Add:

```python
def test_real_midi_sender_records_to_fake_port_only():
    from rytm_randomizer.mock_midi import build_cc_message
    from rytm_randomizer.real_midi_adapter import (
        RealMidiPortProvider,
        build_real_midi_sender,
    )

    fake_port = FakeOutputPort()
    provider = RealMidiPortProvider(
        output_names=("Fake Rytm",),
        ports={"Fake Rytm": fake_port},
    )
    sender = build_real_midi_sender(provider=provider, port_name="Fake Rytm")
    message = build_cc_message(
        channel=0,
        control=16,
        value=0,
        metadata={
            "source_kind": "group_profile",
            "source_key": "2",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )

    result = sender.send_messages([message])

    assert result.port_name == "Fake Rytm"
    assert result.message_count == 1
    assert result.sent_real_midi is False
    assert fake_port.sent == [
        {
            "message_type": "cc",
            "channel": 0,
            "control": 16,
            "value": 0,
            "metadata": dict(message.metadata),
        }
    ]
```

- [ ] **Step 5: Add unsupported message type safe failure test**

Add:

```python
def test_real_midi_sender_rejects_unsupported_message_type():
    from rytm_randomizer.mock_midi import MidiMessage
    from rytm_randomizer.real_midi_adapter import (
        RealMidiPortProvider,
        RealMidiSendError,
        build_real_midi_sender,
    )

    fake_port = FakeOutputPort()
    provider = RealMidiPortProvider(
        output_names=("Fake Rytm",),
        ports={"Fake Rytm": fake_port},
    )
    sender = build_real_midi_sender(provider=provider, port_name="Fake Rytm")
    message = MidiMessage(message_type="note_on", channel=0, control=16, value=1)

    try:
        sender.send_messages([message])
    except RealMidiSendError as exc:
        assert str(exc) == "unsupported_midi_message_type: note_on"
    else:
        raise AssertionError("expected RealMidiSendError")

    assert fake_port.sent == []
```

- [ ] **Step 6: Run tests and verify they fail before implementation**

Run:

```powershell
python .\tests\test_real_midi_adapter_boundary.py
```

Expected before implementation:

- failures for missing `rytm_randomizer.real_midi_adapter`

### Task 3: Create Minimal Adapter Boundary

**Files:**

- Create: `rytm_randomizer/real_midi_adapter.py`

- [ ] **Step 1: Create the future module**

Create `rytm_randomizer/real_midi_adapter.py` with:

```python
"""Import-safe real MIDI adapter boundary.

This module defines a future real MIDI boundary without importing real MIDI
libraries at module import time. Unit tests must use fake providers only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Protocol, Sequence

from .mock_midi import MidiMessage


class RealMidiDependencyError(RuntimeError):
    """Raised when a real MIDI provider is required but absent."""


class RealMidiPortError(RuntimeError):
    """Raised when MIDI port selection fails safely."""


class RealMidiSendError(RuntimeError):
    """Raised when a send request cannot be translated safely."""


class RealMidiOutputPort(Protocol):
    """Minimal output-port protocol for fake-provider tests."""

    def send(self, message: object) -> None:
        """Record or send one backend-specific message."""


def _freeze_metadata(metadata: Mapping[str, object] | None) -> Mapping[str, object]:
    if metadata is None:
        return MappingProxyType({})
    return MappingProxyType(dict(metadata))


@dataclass(frozen=True)
class RealMidiSendResult:
    """Result for adapter sends through an injected provider."""

    port_name: str
    message_count: int
    sent_real_midi: bool = False
    metadata: Mapping[str, object] = field(default_factory=lambda: MappingProxyType({}))

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_metadata(self.metadata))


class RealMidiPortProvider:
    """Explicit output-port provider for fake-provider tests.

    This provider does not discover hardware. It only exposes the names and
    fake ports injected by tests or a future explicitly-approved backend.
    """

    def __init__(
        self,
        output_names: Sequence[str] = (),
        ports: Mapping[str, RealMidiOutputPort] | None = None,
    ) -> None:
        self._output_names = tuple(output_names)
        self._ports = dict(ports or {})

    def list_output_names(self) -> tuple[str, ...]:
        return self._output_names

    def open_output(self, port_name: str) -> RealMidiOutputPort:
        if port_name not in self._output_names:
            raise RealMidiPortError(f"unknown_midi_output_port: {port_name}")
        try:
            return self._ports[port_name]
        except KeyError as exc:
            raise RealMidiPortError(f"unavailable_midi_output_port: {port_name}") from exc


class RealMidiSender:
    """Sender boundary that can be tested with fake output ports only."""

    def __init__(self, provider: RealMidiPortProvider, port_name: str) -> None:
        if not isinstance(provider, RealMidiPortProvider):
            raise TypeError("provider must be a RealMidiPortProvider")
        if not isinstance(port_name, str) or not port_name:
            raise RealMidiPortError("midi_output_port_required")
        self._provider = provider
        self._port_name = port_name
        self._port = provider.open_output(port_name)

    @property
    def port_name(self) -> str:
        return self._port_name

    def send_messages(self, messages: Sequence[MidiMessage]) -> RealMidiSendResult:
        translated_messages = [_translate_message(message) for message in messages]
        for translated_message in translated_messages:
            self._port.send(translated_message)
        return RealMidiSendResult(
            port_name=self._port_name,
            message_count=len(translated_messages),
            sent_real_midi=False,
            metadata={"fake_provider_only": True},
        )


def _translate_message(message: MidiMessage) -> Mapping[str, object]:
    if not isinstance(message, MidiMessage):
        raise TypeError("message must be a MidiMessage")
    if message.message_type != "cc":
        raise RealMidiSendError(
            f"unsupported_midi_message_type: {message.message_type}"
        )
    return {
        "message_type": message.message_type,
        "channel": message.channel,
        "control": message.control,
        "value": message.value,
        "metadata": dict(message.metadata),
    }


def build_real_midi_sender(
    provider: RealMidiPortProvider | None,
    port_name: str,
) -> RealMidiSender:
    """Build a sender only from an explicit provider and port name."""

    if provider is None:
        raise RealMidiDependencyError("real_midi_provider_required")
    return RealMidiSender(provider=provider, port_name=port_name)
```

- [ ] **Step 2: Run adapter boundary tests**

Run:

```powershell
python .\tests\test_real_midi_adapter_boundary.py
```

Expected after implementation:

- all tests in `test_real_midi_adapter_boundary.py` pass
- no real MIDI dependency imported
- no ports opened
- no MIDI sent
- V1.34 reference diff remains empty

### Task 4: Preserve Passive Safety Regression Tests

**Files:**

- Modify: `tests/test_real_midi_adapter_boundary.py`

- [ ] **Step 1: Keep passive import regression test unchanged**

Keep:

```python
def test_passive_imports_do_not_load_adapter_or_real_midi_modules():
    imports = "\n".join(f"import {module}" for module in PASSIVE_MODULES)
    checks = "\n".join(
        f"assert {module_name!r} not in sys.modules, {module_name!r}"
        for module_name in FORBIDDEN_IMPORTED_MODULES
    )
    result = run_python(
        f"""
import sys
{imports}
{checks}
"""
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""
```

- [ ] **Step 2: Keep passive CLI regression test unchanged**

Keep:

```python
def test_passive_cli_commands_do_not_load_adapter_or_real_midi_modules():
    result = run_python(
        f"""
import sys
from rytm_randomizer import cli
commands = {PASSIVE_CLI_COMMANDS!r}
for command in commands:
    exit_code = cli.main(list(command))
    assert exit_code == 0, command
for module_name in {FORBIDDEN_IMPORTED_MODULES!r}:
    assert module_name not in sys.modules, module_name
"""
    )

    assert result.returncode == 0
    assert result.stderr == ""
```

- [ ] **Step 3: Keep active-boundary scope guard unchanged**

Keep:

```python
def test_active_boundary_scope_still_rejects_profiles_3_and_4():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    accepted_sender = MockMidiSender()
    accepted = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="2",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        accepted_sender,
    )

    unsupported_results = []
    for key in ("3", "4"):
        sender = MockMidiSender()
        result = evaluate_mock_active_boundary(
            ActiveBoundaryRequest(
                source_kind="group_profile",
                source_key=key,
                armed=True,
                dry_run_confirmed=True,
                target="mock",
            ),
            sender,
        )
        unsupported_results.append((result, sender))

    assert accepted.accepted is True
    assert accepted_sender.sent_messages == accepted.emitted_messages
    for result, sender in unsupported_results:
        assert result.accepted is False
        assert result.emitted_messages == ()
        assert sender.sent_messages == ()
```

### Task 5: Verify Full Closeout And Commit

**Files:**

- Verify: `Scripts/closeout_check.ps1`
- Verify: `rytm_hybrid_randomizer_v134.py`
- Verify: `rytm_randomizer/real_midi_adapter.py`
- Verify: `tests/test_real_midi_adapter_boundary.py`

- [ ] **Step 1: Run targeted adapter boundary tests**

Run:

```powershell
python .\tests\test_real_midi_adapter_boundary.py
```

Expected:

- exit code `0`
- no stdout required unless existing tests print
- no real MIDI dependency imported
- no hardware required

- [ ] **Step 2: Run full closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- closeout completes
- `=== Test: Real MIDI Adapter Boundary ===` remains present
- `=== V1.34 Reference Diff ===` remains empty
- `=== Git Status ===` lists only the intended future implementation files
  before commit

- [ ] **Step 3: Confirm protected reference is untouched**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected:

- no output

- [ ] **Step 4: Confirm no package metadata changed**

Run:

```powershell
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
```

Expected:

- no output, unless a separately reviewed dependency decision explicitly
  approves a package metadata change

- [ ] **Step 5: Inspect final status**

Run:

```powershell
git status --short
```

Expected before commit:

```text
 M tests/test_real_midi_adapter_boundary.py
?? rytm_randomizer/real_midi_adapter.py
```

No docs or closeout changes are expected for the future implementation slice.

- [ ] **Step 6: Commit future implementation slice**

Run:

```powershell
git add .\rytm_randomizer\real_midi_adapter.py `
        .\tests\test_real_midi_adapter_boundary.py

git commit -m "Add first real MIDI adapter boundary"
```

## 7. Required Future Follow-Up

After the future implementation slice, create a documentation checkpoint that
records:

- new adapter module
- updated adapter boundary tests
- closeout result
- V1.34 reference diff
- dependency selection still deferred
- package metadata unchanged
- no real MIDI dependency
- no port opening
- no MIDI sending
- no active CLI commands
- no hardware behavior
- hardware off

## 8. Still Forbidden After This Plan

This plan does not authorize:

- implementation in this slice
- dependency selection
- package metadata changes
- real MIDI imports
- real port opening
- MIDI sending
- active CLI commands
- hardware validation
- profile `"4"` implementation
- profile `"3"` active-boundary support
- turning hardware on

## 9. Self-Review

Spec coverage:

- future module ownership is covered in Tasks 3 and 5
- dependency isolation is covered in Tasks 1, 2, and 3
- port provider boundary is covered in Tasks 2 and 3
- sender boundary is covered in Tasks 2 and 3
- passive CLI separation is covered in Task 4
- active-boundary scope limits are covered in Task 4
- V1.34 reference protection is covered in Task 5

Placeholder scan:

- no placeholder implementation steps remain
- future code snippets are included explicitly
- future commands and expected results are included explicitly

Type consistency:

- planned names match the accepted design/spec:
  `RealMidiDependencyError`, `RealMidiPortError`, `RealMidiSendError`,
  `RealMidiPortProvider`, `RealMidiSender`, `RealMidiSendResult`, and
  `build_real_midi_sender`

## 10. Safe Next Options

Safe next options:

- review and accept this implementation plan
- pause at this clean planning checkpoint
- return to passive/project documentation

Unsafe next moves:

- implementing the adapter before plan review
- adding `mido`
- selecting or installing a real MIDI dependency
- changing package metadata
- opening ports
- sending MIDI
- adding active CLI commands
- turning on hardware
- implementing profile `"4"`
- adding profile `"3"` active-boundary support

## 11. Recommendation

Prefer a documentation-only review/acceptance gate for this implementation
plan next.

After that, the future implementation slice may be considered, still with no
real MIDI dependency, no real ports, no MIDI sending, no active CLI commands,
and no hardware.

## 12. Decision

The first adapter implementation plan is documented.

Adapter implementation remains blocked until this plan is reviewed and
accepted.

Real MIDI dependency selection remains deferred.

Hardware validation remains blocked.

Hardware remains off.

No implementation is added in this slice.
