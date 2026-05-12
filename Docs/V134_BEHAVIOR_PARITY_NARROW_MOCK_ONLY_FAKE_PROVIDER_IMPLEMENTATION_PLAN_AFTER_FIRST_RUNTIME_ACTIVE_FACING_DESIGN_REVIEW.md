# Narrow Mock-Only Fake-Provider Runtime Bridge Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Define the smallest future mock-only/fake-provider implementation
packet for the accepted runtime/active-facing bridge without adding real MIDI,
ports, active CLI execution, or hardware behavior.

**Architecture:** Add a narrow runtime planning layer that can represent
operator intent, safety envelope, blocked preview, and fake-provider recording
without execution. The layer must stay separate from passive CLI browsing and
must be tested as inert, mock-only behavior before any later active boundary
work.

**Tech Stack:** Python standard library, dataclasses, existing passive
metadata/reporting patterns, pytest, existing closeout suite. No `mido`,
`rtmidi`, real MIDI library, port provider, or hardware dependency.

---

## 1. Purpose

This is a documentation-only implementation plan.

It defines a future narrow mock-only/fake-provider implementation packet after
the accepted first runtime/active-facing design review.

It does not implement runtime code.

It does not add tests.

It does not add fixtures.

It does not update closeout.

It does not wire CLI execution.

It does not add MIDI, ports, active behavior, or hardware behavior.

## 1A. Implementation Status

This plan has now been implemented by:

- `f14e329 Add mock-only runtime plan scaffold`

Implementation checkpoint:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_SCAFFOLD_CHECKPOINT.md`

Implemented files:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- `Scripts/closeout_check.ps1`

The implementation remains mock-only and inert. It adds no real MIDI, ports,
CLI execution wiring, dispatch, command execution, runtime mutation, package
metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `ca874d6 Add first runtime active-facing design review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 12 behavior-parity coverage report implemented and accepted
- Packet 12 behavior-parity report CLI visibility implemented and accepted
- Packet 12 report data alignment implemented and accepted
- first runtime/active-facing design plan reviewed and accepted
- `PZ`, `B`, and `L` runtime-adjacent safe-failure trio frozen for now
- narrow mock-only/fake-provider implementation plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Inputs

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ACTIVE_FACING_DESIGN_PLAN_AFTER_FROZEN_FRONTIER_REVIEW.md`

Accepted upstream design:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ACTIVE_FACING_DESIGN_PLAN_AFTER_FROZEN_FRONTIER.md`

Accepted upstream milestone:

- `ca874d6 Add first runtime active-facing design review`

Accepted design concepts:

- RuntimeIntent
- RuntimeSafetyEnvelope
- RuntimePlanPreview
- MockRuntimeProvider
- ActiveBoundaryAdapter

These remain future implementation targets only.

## 4. Future File Structure

Future implementation should create:

- `rytm_randomizer/runtime_plan.py`
  - defines inert runtime planning dataclasses and safe-failure helpers
  - imports only standard library and passive-safe modules
  - must not import `mido`, `rtmidi`, port providers, CLI dispatch, or hardware
    adapters
- `tests/test_runtime_plan.py`
  - proves the runtime planning layer is inert, deterministic, and safe
  - proves unknown/unsupported/missing-arming paths fail safely
  - proves no real MIDI libraries are imported
  - proves no ports are opened and no MIDI is sent

Future implementation should modify:

- `Scripts/closeout_check.ps1`
  - add a single closeout entry labeled:
    - `=== Test: Runtime Plan ===`
  - run `tests/test_runtime_plan.py`

Future implementation should not modify:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- package metadata
- runtime execution/dispatch logic
- active CLI commands

## 5. Task 1: Runtime Planning Dataclasses

**Files:**

- Create: `rytm_randomizer/runtime_plan.py`
- Create: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write import safety test**

Add this test to `tests/test_runtime_plan.py`:

```python
import importlib


def test_runtime_plan_import_prints_nothing(capsys):
    importlib.import_module("rytm_randomizer.runtime_plan")
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_runtime_plan_import_prints_nothing -q
```

Expected:

- FAIL because `rytm_randomizer.runtime_plan` does not exist yet.

- [ ] **Step 3: Create minimal runtime plan module**

Create `rytm_randomizer/runtime_plan.py`:

```python
"""Mock-only runtime planning primitives.

This module is inert. It does not import MIDI libraries, open ports, send MIDI,
or connect to hardware.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class RuntimeIntent:
    source_kind: str
    source_key: str
    target: str
    armed: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True)
class RuntimeSafetyEnvelope:
    mock_only: bool = True
    sends_real_midi: bool = False
    ports_allowed: bool = False
    hardware_required: bool = False
    reason: str = "mock-only runtime planning"


@dataclass(frozen=True)
class RuntimePlanPreview:
    intent: RuntimeIntent
    safety: RuntimeSafetyEnvelope
    status: str
    reason: str
    would_execute: bool = False


class MockRuntimeProvider:
    """In-memory fake provider for future runtime planning tests only."""

    def __init__(self) -> None:
        self._records: list[RuntimePlanPreview] = []

    @property
    def records(self) -> tuple[RuntimePlanPreview, ...]:
        return tuple(self._records)

    def record(self, preview: RuntimePlanPreview) -> RuntimePlanPreview:
        self._records.append(preview)
        return preview

    def clear(self) -> None:
        self._records.clear()
```

- [ ] **Step 4: Run import test and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_runtime_plan_import_prints_nothing -q
```

Expected:

- PASS.

## 6. Task 2: Safe-Failure Preview Helper

**Files:**

- Modify: `rytm_randomizer/runtime_plan.py`
- Modify: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write safe-failure tests**

Add tests:

```python
from rytm_randomizer.runtime_plan import (
    RuntimeIntent,
    RuntimeSafetyEnvelope,
    create_blocked_runtime_preview,
)


def test_runtime_safety_envelope_defaults_are_inert():
    safety = RuntimeSafetyEnvelope()
    assert safety.mock_only is True
    assert safety.sends_real_midi is False
    assert safety.ports_allowed is False
    assert safety.hardware_required is False


def test_create_blocked_runtime_preview_never_executes():
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
        armed=False,
        metadata={"mock_only": True},
    )

    preview = create_blocked_runtime_preview(intent, "missing arming")

    assert preview.intent == intent
    assert preview.safety.mock_only is True
    assert preview.safety.sends_real_midi is False
    assert preview.safety.ports_allowed is False
    assert preview.safety.hardware_required is False
    assert preview.status == "blocked"
    assert preview.reason == "missing arming"
    assert preview.would_execute is False
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- FAIL because `create_blocked_runtime_preview` is not defined yet.

- [ ] **Step 3: Add minimal helper**

Add to `rytm_randomizer/runtime_plan.py`:

```python
def create_blocked_runtime_preview(
    intent: RuntimeIntent,
    reason: str,
) -> RuntimePlanPreview:
    return RuntimePlanPreview(
        intent=intent,
        safety=RuntimeSafetyEnvelope(reason=reason),
        status="blocked",
        reason=reason,
        would_execute=False,
    )
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- PASS.

## 7. Task 3: Unsupported Scope Guard

**Files:**

- Modify: `rytm_randomizer/runtime_plan.py`
- Modify: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write unsupported scope tests**

Add tests:

```python
from rytm_randomizer.runtime_plan import validate_runtime_intent_scope


def test_unknown_key_fails_safely():
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="unknown",
        target="unknown",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "unsupported key"
    assert preview.would_execute is False


def test_profile_4_remains_parked():
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="4",
        target="Pad 1 / My BD Acoustic",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.status == "blocked"
    assert preview.reason == "profile 4 parked"
    assert preview.would_execute is False
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- FAIL because `validate_runtime_intent_scope` is not defined yet.

- [ ] **Step 3: Add minimal scope validation**

Add to `rytm_randomizer/runtime_plan.py`:

```python
SUPPORTED_GROUP_PROFILE_KEYS = frozenset({"2", "3"})


def validate_runtime_intent_scope(intent: RuntimeIntent) -> RuntimePlanPreview:
    if intent.source_kind != "group_profile":
        return create_blocked_runtime_preview(intent, "unsupported source kind")
    if intent.source_key == "4":
        return create_blocked_runtime_preview(intent, "profile 4 parked")
    if intent.source_key not in SUPPORTED_GROUP_PROFILE_KEYS:
        return create_blocked_runtime_preview(intent, "unsupported key")
    return create_blocked_runtime_preview(intent, "execution not implemented")
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- PASS.

## 8. Task 4: MockRuntimeProvider Recording

**Files:**

- Modify: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write provider recording test**

Add test:

```python
from rytm_randomizer.runtime_plan import MockRuntimeProvider


def test_mock_runtime_provider_records_in_memory_only():
    provider = MockRuntimeProvider()
    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
    )
    preview = create_blocked_runtime_preview(intent, "execution not implemented")

    assert provider.records == ()

    recorded = provider.record(preview)

    assert recorded == preview
    assert provider.records == (preview,)

    provider.clear()
    assert provider.records == ()
```

- [ ] **Step 2: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- PASS.

## 9. Task 5: Real MIDI/Port Safety Tests

**Files:**

- Modify: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write real MIDI import safety test**

Add test:

```python
import sys


def test_runtime_plan_does_not_import_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.runtime_plan", None)
    importlib.import_module("rytm_randomizer.runtime_plan")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules
```

- [ ] **Step 2: Write passive CLI remains separate test**

Add test:

```python
def test_runtime_plan_is_not_cli_execution_wiring():
    runtime_plan = importlib.import_module("rytm_randomizer.runtime_plan")

    assert not hasattr(runtime_plan, "execute_command")
    assert not hasattr(runtime_plan, "send_command")
    assert not hasattr(runtime_plan, "hardware_test")
```

- [ ] **Step 3: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- PASS.

## 10. Task 6: Closeout Entry

**Files:**

- Modify: `Scripts/closeout_check.ps1`

- [ ] **Step 1: Add closeout label**

Add one closeout section:

```powershell
Write-Host ""
Write-Host "=== Test: Runtime Plan ==="
& $python -m pytest tests/test_runtime_plan.py -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
```

- [ ] **Step 2: Run full closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- Closeout completes.
- `=== Test: Runtime Plan ===` appears.
- V1.34 reference diff is empty.

## 11. Task 7: Protected Diff And Commit

**Files:**

- Review only.

- [ ] **Step 1: Confirm V1.34 untouched**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected:

- no output.

- [ ] **Step 2: Confirm package metadata untouched**

Run:

```powershell
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
```

Expected:

- no output.

- [ ] **Step 3: Check status**

Run:

```powershell
git status --short
```

Expected:

```text
 M Scripts/closeout_check.ps1
?? rytm_randomizer/runtime_plan.py
?? tests/test_runtime_plan.py
```

- [ ] **Step 4: Commit**

Run:

```powershell
git add .\rytm_randomizer\runtime_plan.py `
        .\tests\test_runtime_plan.py `
        .\Scripts\closeout_check.ps1

git commit -m "Add mock-only runtime plan scaffold"
```

- [ ] **Step 5: Final closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git status --short
```

Expected:

- Closeout completes.
- `git status --short` returns no output.

## 12. Forbidden Scope For Future Implementation

The future implementation must not add:

- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- runtime mutation
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- scene execution
- global mutation execution
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- hardware behavior
- package metadata changes

## 13. Self-Review

Spec coverage:

- RuntimeIntent is covered in Task 1.
- RuntimeSafetyEnvelope is covered in Task 1 and Task 2.
- RuntimePlanPreview is covered in Task 1 and Task 2.
- MockRuntimeProvider is covered in Task 1 and Task 4.
- Safe-failure requirements are covered in Task 2 and Task 3.
- No-real-MIDI and no-port guardrails are covered in Task 5 and Task 7.
- Closeout integration is covered in Task 6.

Placeholder scan:

- No unresolved placeholders or unspecified implementation steps remain.

Type consistency:

- Function and class names are consistent across tasks:
  - `RuntimeIntent`
  - `RuntimeSafetyEnvelope`
  - `RuntimePlanPreview`
  - `MockRuntimeProvider`
  - `create_blocked_runtime_preview`
  - `validate_runtime_intent_scope`

Scope check:

- This plan is intentionally narrow.
- It creates one future module, one future test file, and one closeout entry.
- It does not wire CLI execution or introduce MIDI.

## 14. Decision

The narrow mock-only/fake-provider implementation plan is documented.

The plan is not implementation.

Future implementation remains separately gated.

Hardware remains off.

## 15. Review Status

This implementation plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_NARROW_MOCK_ONLY_FAKE_PROVIDER_IMPLEMENTATION_PLAN_REVIEW_AFTER_FIRST_RUNTIME_ACTIVE_FACING_DESIGN_REVIEW.md`

The review accepts this document as the current implementation plan for the
first narrow mock-only/fake-provider runtime bridge.

The next selected branch is:

- implement the narrow mock-only runtime plan scaffold

Accepted future implementation scope:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- one closeout label:
  - `=== Test: Runtime Plan ===`

The review adds no runtime plan implementation, runtime module, tests, fixture
changes, closeout script changes, CLI changes, CLI execution wiring, dispatch,
command execution, runtime execution, MIDI, ports, package metadata changes,
active behavior, or hardware behavior.
