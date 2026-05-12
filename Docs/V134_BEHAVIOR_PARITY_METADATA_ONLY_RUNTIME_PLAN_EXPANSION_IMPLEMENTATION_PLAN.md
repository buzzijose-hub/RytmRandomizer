# Metadata-Only Runtime Plan Expansion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add metadata-only blocked-preview visibility to the existing mock-only runtime plan scaffold without adding execution, MIDI, ports, CLI wiring, active behavior, or hardware behavior.

**Architecture:** Extend the current inert `RuntimePlanPreview` surface with copied, immutable metadata that describes source, safety, support, parking, arming, and stable reason-code information. Preserve the current blocked-preview behavior and keep all future changes confined to `rytm_randomizer/runtime_plan.py` and `tests/test_runtime_plan.py`.

**Tech Stack:** Python standard library dataclasses, `types.MappingProxyType`, pytest, existing closeout suite. No `mido`, `rtmidi`, port provider, CLI execution layer, dispatch layer, package metadata changes, or hardware dependency.

---

## 1. Purpose

Define the tiny future implementation plan for metadata-only runtime plan
expansion after the accepted first runtime plan expansion design review.

This is a documentation-only implementation plan.

It does not implement runtime plan expansion.

It does not add tests.

It does not change closeout.

It does not add CLI execution wiring, runtime execution, dispatch, command
execution, MIDI, ports, package metadata changes, active behavior, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `56bfe39 Add first runtime plan expansion design review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- mock-only runtime plan scaffold implemented and accepted
- metadata-only runtime plan expansion design reviewed and accepted
- metadata-only runtime plan expansion implementation plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream Inputs

Accepted design review:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_PLAN_EXPANSION_DESIGN_REVIEW.md`

Accepted design:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_PLAN_EXPANSION_DESIGN.md`

Accepted current runtime plan scaffold review:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_SCAFFOLD_CHECKPOINT_REVIEW.md`

Current runtime plan module:

- `rytm_randomizer/runtime_plan.py`

Current runtime plan tests:

- `tests/test_runtime_plan.py`

Current closeout coverage:

- `=== Test: Runtime Plan ===`

## 4. Future File Structure

Future implementation should modify only:

- `rytm_randomizer/runtime_plan.py`
  - add stable reason-code constants
  - add immutable metadata to `RuntimePlanPreview`
  - add a helper for building blocked-preview metadata
  - keep every preview blocked
- `tests/test_runtime_plan.py`
  - add tests for supported-profile metadata
  - add tests for unknown-key metadata
  - add tests for parked-profile metadata
  - add tests for metadata immutability

Future implementation should not modify:

- `Scripts/closeout_check.ps1`
  - `tests/test_runtime_plan.py` is already covered
- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- package metadata
- runtime execution/dispatch logic
- active CLI commands

## 5. Task 1: Supported Profile Metadata

**Files:**

- Modify: `tests/test_runtime_plan.py`
- Modify later: `rytm_randomizer/runtime_plan.py`

- [ ] **Step 1: Write failing test for supported profile metadata**

Add this test to `tests/test_runtime_plan.py`:

```python
def test_supported_group_profile_2_preview_metadata_is_inert_and_explicit():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
        armed=False,
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.metadata == {
        "source_kind": "group_profile",
        "source_key": "2",
        "target": "Pad 1 / My BD Hard",
        "source_label": "group_profile:2",
        "request_kind": "runtime_plan_preview",
        "supported": True,
        "parked": False,
        "arming_required": True,
        "armed": False,
        "reason_code": "execution_not_implemented",
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
        "would_execute": False,
    }
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_supported_group_profile_2_preview_metadata_is_inert_and_explicit -q
```

Expected:

- FAIL because `RuntimePlanPreview` does not yet expose this metadata.

- [ ] **Step 3: Add minimal metadata support**

Modify `rytm_randomizer/runtime_plan.py`.

Add reason-code constants near `SUPPORTED_GROUP_PROFILE_KEYS`:

```python
REASON_EXECUTION_NOT_IMPLEMENTED = "execution_not_implemented"
REASON_UNSUPPORTED_KEY = "unsupported_key"
REASON_UNSUPPORTED_SOURCE_KIND = "unsupported_source_kind"
REASON_PROFILE_4_PARKED = "profile_4_parked"
REASON_MISSING_ARMING = "missing_arming"
```

Add immutable metadata to `RuntimePlanPreview`:

```python
@dataclass(frozen=True)
class RuntimePlanPreview:
    """Blocked runtime preview that never executes."""

    intent: RuntimeIntent
    safety: RuntimeSafetyEnvelope
    status: str
    reason: str
    would_execute: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
```

Add helper functions:

```python
_REASON_CODE_BY_REASON = {
    "execution not implemented": REASON_EXECUTION_NOT_IMPLEMENTED,
    "unsupported key": REASON_UNSUPPORTED_KEY,
    "unsupported source kind": REASON_UNSUPPORTED_SOURCE_KIND,
    "profile 4 parked": REASON_PROFILE_4_PARKED,
    "missing arming": REASON_MISSING_ARMING,
}


def _reason_code_for(reason: str) -> str:
    return _REASON_CODE_BY_REASON.get(reason, reason.replace(" ", "_").replace("-", "_"))


def _build_blocked_preview_metadata(
    intent: RuntimeIntent,
    reason: str,
    *,
    supported: bool = False,
    parked: bool = False,
) -> dict[str, object]:
    return {
        "source_kind": intent.source_kind,
        "source_key": intent.source_key,
        "target": intent.target,
        "source_label": f"{intent.source_kind}:{intent.source_key}",
        "request_kind": "runtime_plan_preview",
        "supported": supported,
        "parked": parked,
        "arming_required": True,
        "armed": intent.armed,
        "reason_code": _reason_code_for(reason),
        "mock_only": True,
        "sends_real_midi": False,
        "ports_allowed": False,
        "hardware_required": False,
        "would_execute": False,
    }
```

Update `create_blocked_runtime_preview`:

```python
def create_blocked_runtime_preview(
    intent: RuntimeIntent,
    reason: str,
    *,
    supported: bool = False,
    parked: bool = False,
) -> RuntimePlanPreview:
    return RuntimePlanPreview(
        intent=intent,
        safety=RuntimeSafetyEnvelope(reason=reason),
        status="blocked",
        reason=reason,
        would_execute=False,
        metadata=_build_blocked_preview_metadata(
            intent,
            reason,
            supported=supported,
            parked=parked,
        ),
    )
```

Update the supported branch in `validate_runtime_intent_scope`:

```python
    return create_blocked_runtime_preview(
        intent,
        "execution not implemented",
        supported=True,
    )
```

- [ ] **Step 4: Run test and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_supported_group_profile_2_preview_metadata_is_inert_and_explicit -q
```

Expected:

- PASS.

## 6. Task 2: Unsupported And Parked Metadata

**Files:**

- Modify: `tests/test_runtime_plan.py`
- Modify later: `rytm_randomizer/runtime_plan.py`

- [ ] **Step 1: Write failing tests for unsupported and parked metadata**

Add these tests:

```python
def test_unknown_key_preview_metadata_fails_safely():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="unknown",
        target="unknown",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.reason == "unsupported key"
    assert preview.metadata["reason_code"] == "unsupported_key"
    assert preview.metadata["supported"] is False
    assert preview.metadata["parked"] is False
    assert preview.metadata["would_execute"] is False
    assert preview.metadata["mock_only"] is True


def test_profile_4_preview_metadata_remains_parked():
    from rytm_randomizer.runtime_plan import RuntimeIntent, validate_runtime_intent_scope

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="4",
        target="Pad 1 / My BD Acoustic",
    )

    preview = validate_runtime_intent_scope(intent)

    assert preview.reason == "profile 4 parked"
    assert preview.metadata["reason_code"] == "profile_4_parked"
    assert preview.metadata["supported"] is False
    assert preview.metadata["parked"] is True
    assert preview.metadata["would_execute"] is False
    assert preview.metadata["mock_only"] is True
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_unknown_key_preview_metadata_fails_safely tests/test_runtime_plan.py::test_profile_4_preview_metadata_remains_parked -q
```

Expected:

- FAIL until the validation branches pass `parked=True` for profile `4`.

- [ ] **Step 3: Update validation branches**

Modify `validate_runtime_intent_scope`:

```python
def validate_runtime_intent_scope(intent: RuntimeIntent) -> RuntimePlanPreview:
    if intent.source_kind != "group_profile":
        return create_blocked_runtime_preview(intent, "unsupported source kind")
    if intent.source_key == "4":
        return create_blocked_runtime_preview(intent, "profile 4 parked", parked=True)
    if intent.source_key not in SUPPORTED_GROUP_PROFILE_KEYS:
        return create_blocked_runtime_preview(intent, "unsupported key")
    return create_blocked_runtime_preview(
        intent,
        "execution not implemented",
        supported=True,
    )
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py::test_unknown_key_preview_metadata_fails_safely tests/test_runtime_plan.py::test_profile_4_preview_metadata_remains_parked -q
```

Expected:

- PASS.

## 7. Task 3: Metadata Immutability And Existing Safety

**Files:**

- Modify: `tests/test_runtime_plan.py`

- [ ] **Step 1: Write metadata immutability test**

Add this test:

```python
def test_runtime_plan_preview_metadata_is_copied_and_immutable():
    from rytm_randomizer.runtime_plan import (
        RuntimeIntent,
        create_blocked_runtime_preview,
    )

    intent = RuntimeIntent(
        source_kind="group_profile",
        source_key="2",
        target="Pad 1 / My BD Hard",
    )

    preview = create_blocked_runtime_preview(
        intent,
        "execution not implemented",
        supported=True,
    )

    assert preview.metadata["source_key"] == "2"
    assert_mapping_is_immutable(preview.metadata)
```

- [ ] **Step 2: Run metadata and existing runtime plan tests**

Run:

```powershell
python -m pytest tests/test_runtime_plan.py -q
```

Expected:

- PASS.

## 8. Task 4: Closeout And Protected Diffs

**Files:**

- Review only.

- [ ] **Step 1: Run full closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
```

Expected:

- closeout completes
- `=== Test: Runtime Plan ===` appears
- V1.34 reference diff is empty

- [ ] **Step 2: Confirm V1.34 untouched**

Run:

```powershell
git diff -- rytm_hybrid_randomizer_v134.py
```

Expected:

- no output.

- [ ] **Step 3: Confirm package metadata untouched**

Run:

```powershell
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
```

Expected:

- no output.

- [ ] **Step 4: Check status**

Run:

```powershell
git status --short
```

Expected:

```text
 M rytm_randomizer/runtime_plan.py
 M tests/test_runtime_plan.py
```

## 9. Task 5: Commit Future Implementation

**Files:**

- Commit only after verification.

- [ ] **Step 1: Stage approved future implementation files**

Run:

```powershell
git add .\rytm_randomizer\runtime_plan.py `
        .\tests\test_runtime_plan.py
```

- [ ] **Step 2: Commit**

Run:

```powershell
git commit -m "Add metadata-only runtime plan preview metadata"
```

- [ ] **Step 3: Final closeout**

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git status --short
```

Expected:

- closeout completes
- `git status --short` returns no output

## 10. Forbidden Scope

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
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- dispatch
- command execution
- scene execution
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

## 11. Decision

The metadata-only runtime plan expansion implementation plan is documented.

The plan is not implementation.

Future implementation remains separately gated.

Hardware remains off.

## 12. Review Status

This implementation plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_METADATA_ONLY_RUNTIME_PLAN_EXPANSION_IMPLEMENTATION_PLAN_REVIEW.md`

The review accepts this document as the current implementation plan for
metadata-only runtime plan preview metadata.

The next selected branch is:

- implement metadata-only runtime plan preview metadata

Accepted future implementation scope:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
