# Rytm Snapshot Machine-Fact Decoder Implementation Plan

> Status: in-flight (branch codex/rytm-snapshot-pad-compatibility-pr1)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decode passive Rytm kit snapshots into per-pad machine facts so snapshot mode can explain, route, and eventually mutate the currently loaded kit instead of loading anchors first.

**Architecture:** Keep all Rytm-specific interpretation under the existing Device Strategy boundary. Extend `AnalogRytmSnapshotDecoder` with immutable machine-fact data derived from the already-unpacked kit payload, then feed those facts into PR #50's routing planner only after the decoder marks them promoted and safe. This PR remains passive/mock-safe: no MIDI ports, no armed sender, no hardware mutation.

**Tech Stack:** Python 3.11, frozen dataclasses, existing `snapshot/envelope.py`, existing Rytm machine catalog, existing `AnalogRytmMutationPlanner.plan_for_machine_values`, pytest, ruff, black, isort.

---

## Context

PR #49 added the passive 12-pad snapshot compatibility report. PR #50 adds `plan_for_machine_values(snapshot, depth, pad_machine_values)` so a caller can pass a validated `{pad: machine_value}` map into the Rytm mutation planner.

The next missing piece is the decoder bridge: turn a real Rytm kit SysEx snapshot into that `{pad: machine_value}` map.

Read-only analysis of Jose's local Rytm kit dumps on 2026-05-20 found:

- `G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx` contains 128 kit SysEx messages.
- Each kit message is 2998 bytes on the wire.
- After stripping `F0/F7`, removing the Elektron manufacturer prefix, and unpacking the 7-bit payload, each kit body is 2618 bytes.
- The real kit name begins at unpacked offset `8`, not offset `0`.
- Candidate per-pad machine values appear at `174 + (162 * (pad - 1))`.
- The candidate vector is strongly consistent for pads 1-5 and 9-12 across the supplied kit banks.
- Pads 6-8 produce stable values `30, 0, 0` in the supplied dumps, which do not directly match the current `xt_classic` CC15 catalog value. Treat those as candidate-only until verified.

This plan therefore promotes the header/name correction and a conservative machine-fact decoder that can report candidate/promoted status without pretending pads 6-8 are fully solved.

## File Structure

- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
  - Correct real kit-name offset handling.
  - Add immutable per-pad machine fact dataclasses.
  - Add `machine_facts` to `RytmKitSnapshot`.
  - Add a pure extraction helper that reads candidate machine bytes from `snapshot.unpacked`.
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
  - Re-export new machine-fact dataclasses if tests need public access.
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py`
  - Add a small convenience method that plans from promoted snapshot facts only, delegating to `plan_for_machine_values`.
- Test: `tests/test_devices_strategies_snapshot_decoder.py`
  - Cover real-layout kit name offset and machine-fact extraction.
- Test: `tests/test_devices_strategies_mutation_planner.py`
  - Cover planner refusal when snapshot facts are candidate-only or absent.
- Do not modify `rytm_randomizer/reports/rytm_snapshot_pad_compatibility.py` in this PR.
  - Keep the report follow-up separate unless the reviewer explicitly asks for it.
- Modify: `docs/STATUS.md`
  - Add one concise checkpoint line only after behavior exists.

## Task 1: Fix Real Rytm Kit Header Decoding

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
- Test: `tests/test_devices_strategies_snapshot_decoder.py`

- [ ] **Step 1: Write the failing real-layout kit-name test**

Add this helper to `tests/test_devices_strategies_snapshot_decoder.py` beside the existing `_kit_payload` helper:

```python
def _real_layout_kit_payload(name: bytes = b"KIT 1") -> bytes:
    """Build a packed Rytm kit body that matches the observed real dump header."""

    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        RYTM_KIT_TYPE_BYTE,
    )

    unpacked = bytearray(bytes([0x52, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x06]))
    unpacked.extend(name.ljust(16, b"\x00"))
    unpacked.extend(bytes([0x00] * 2600))
    packed = _pack_elektron_7bit(bytes(unpacked))
    return bytes([0x00, 0x20, 0x3C, RYTM_KIT_TYPE_BYTE]) + packed
```

Add the test:

```python
def test_decode_extracts_kit_name_from_real_layout_offset() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_real_layout_kit_payload(name=b"KIT 12"), slot=11)

    assert snap.kit_name == "KIT 12"
```

- [ ] **Step 2: Add the local test packer**

Add this test helper near `_kit_payload`:

```python
def _pack_elektron_7bit(unpacked: bytes) -> bytes:
    out = bytearray()
    for start in range(0, len(unpacked), 7):
        group = unpacked[start : start + 7]
        header = 0
        for index, byte in enumerate(group):
            header |= ((byte >> 7) & 0x01) << index
            out.append(byte & 0x7F)
        out.insert(len(out) - len(group), header)
    return bytes(out)
```

- [ ] **Step 3: Run the decoder test to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py::test_decode_extracts_kit_name_from_real_layout_offset -n 0
```

Expected: FAIL because the decoder currently reads the kit name from offset `0`.

- [ ] **Step 4: Correct the kit-name offset**

In `analog_rytm_snapshot_decoder.py`, replace:

```python
_KIT_NAME_OFFSET: Final[int] = 1
```

with:

```python
_KIT_NAME_OFFSET: Final[int] = 8
```

Then update the decode call to read directly from the real unpacked offset:

```python
kit_name = read_ascii_name(unpacked, offset=_KIT_NAME_OFFSET, length=_KIT_NAME_LENGTH)
```

- [ ] **Step 5: Update old simplified tests**

The old `_kit_payload` helper built name bytes at offset `0`. Either update it to use `_real_layout_kit_payload`, or keep it only for malformed-payload tests and move name assertions to the real-layout helper. Do not preserve the old offset as alternate production behavior.

- [ ] **Step 6: Run decoder tests**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py -n 0
```

Expected: PASS.

## Task 2: Add Passive Machine-Fact Dataclasses

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_devices_strategies_snapshot_decoder.py`

- [ ] **Step 1: Write the failing dataclass import test**

Add:

```python
def test_snapshot_exports_machine_fact_types() -> None:
    from rytm_randomizer.devices.strategies import (
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    fact = RytmSnapshotMachineFact(
        pad=1,
        raw_machine_value=0,
        decoded_machine_value=0,
        promoted=True,
        reason="promoted",
    )
    facts = RytmSnapshotMachineFacts(facts_by_pad={1: fact}, promoted=False)

    assert facts.facts_by_pad[1] is fact
    assert facts.promoted is False
```

- [ ] **Step 2: Run the test to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py::test_snapshot_exports_machine_fact_types -n 0
```

Expected: FAIL because the types do not exist.

- [ ] **Step 3: Add frozen dataclasses**

Add to `analog_rytm_snapshot_decoder.py`:

```python
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
```

Then add:

```python
@dataclass(frozen=True)
class RytmSnapshotMachineFact:
    """One passive machine-value fact decoded from a Rytm kit snapshot."""

    pad: int
    raw_machine_value: int
    decoded_machine_value: int | None
    promoted: bool
    reason: str


@dataclass(frozen=True)
class RytmSnapshotMachineFacts:
    """Passive machine facts for all decoded Rytm pads."""

    facts_by_pad: Mapping[int, RytmSnapshotMachineFact]
    promoted: bool


def _empty_machine_facts() -> RytmSnapshotMachineFacts:
    return RytmSnapshotMachineFacts(facts_by_pad=MappingProxyType({}), promoted=False)
```

- [ ] **Step 4: Export the types**

Add the two new types to `rytm_randomizer/devices/strategies/__init__.py` imports and `__all__`.

- [ ] **Step 5: Run the dataclass test**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py::test_snapshot_exports_machine_fact_types -n 0
```

Expected: PASS.

## Task 3: Extract Candidate Machine Facts From Snapshot Bytes

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py`
- Test: `tests/test_devices_strategies_snapshot_decoder.py`

- [ ] **Step 1: Write the failing extraction tests**

Add:

```python
def test_decode_extracts_candidate_machine_facts_from_real_layout() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    payload = _real_layout_kit_payload(name=b"LIVE")
    snap = AnalogRytmSnapshotDecoder().decode(payload, slot=0)

    assert snap.machine_facts.facts_by_pad[1].raw_machine_value == 0
    assert snap.machine_facts.facts_by_pad[2].raw_machine_value == 2
    assert snap.machine_facts.facts_by_pad[3].raw_machine_value == 4
    assert snap.machine_facts.facts_by_pad[10].raw_machine_value == 10
    assert snap.machine_facts.facts_by_pad[12].raw_machine_value == 12
    assert snap.machine_facts.promoted is False
```

Add:

```python
def test_decode_marks_tom_pads_candidate_only_until_verified() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    snap = AnalogRytmSnapshotDecoder().decode(_real_layout_kit_payload(), slot=0)

    for pad in (6, 7, 8):
        fact = snap.machine_facts.facts_by_pad[pad]
        assert fact.promoted is False
        assert "candidate-only" in fact.reason
```

- [ ] **Step 2: Make `_real_layout_kit_payload` install candidate bytes**

Inside `_real_layout_kit_payload`, after allocating `unpacked`, set:

```python
machine_values = {
    1: 0,
    2: 2,
    3: 4,
    4: 6,
    5: 7,
    6: 30,
    7: 0,
    8: 0,
    9: 9,
    10: 10,
    11: 11,
    12: 12,
}
for pad, value in machine_values.items():
    unpacked[174 + (162 * (pad - 1))] = value
```

- [ ] **Step 3: Run the extraction tests to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py::test_decode_extracts_candidate_machine_facts_from_real_layout tests/test_devices_strategies_snapshot_decoder.py::test_decode_marks_tom_pads_candidate_only_until_verified -n 0
```

Expected: FAIL because `RytmKitSnapshot` does not expose `machine_facts`.

- [ ] **Step 4: Add extraction constants**

Add:

```python
_TRACK_COUNT: Final[int] = 12
_TRACK_MACHINE_VALUE_OFFSET: Final[int] = 174
_TRACK_SOUND_STRIDE: Final[int] = 162
_CANDIDATE_ONLY_PADS: Final[frozenset[int]] = frozenset({6, 7, 8})
```

- [ ] **Step 5: Add extractor helper**

Add:

```python
def _extract_machine_facts(unpacked: bytes) -> RytmSnapshotMachineFacts:
    facts: dict[int, RytmSnapshotMachineFact] = {}
    for pad in range(1, _TRACK_COUNT + 1):
        offset = _TRACK_MACHINE_VALUE_OFFSET + (_TRACK_SOUND_STRIDE * (pad - 1))
        if offset >= len(unpacked):
            fact = RytmSnapshotMachineFact(
                pad=pad,
                raw_machine_value=-1,
                decoded_machine_value=None,
                promoted=False,
                reason=f"candidate machine offset {offset} is outside snapshot payload",
            )
        else:
            raw_value = unpacked[offset]
            promoted = pad not in _CANDIDATE_ONLY_PADS
            fact = RytmSnapshotMachineFact(
                pad=pad,
                raw_machine_value=raw_value,
                decoded_machine_value=raw_value if promoted else None,
                promoted=promoted,
                reason="promoted machine fact" if promoted else "candidate-only tom-pad machine fact",
            )
        facts[pad] = fact
    return RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(facts),
        promoted=all(fact.promoted for fact in facts.values()),
    )
```

- [ ] **Step 6: Add `machine_facts` to `RytmKitSnapshot` without breaking existing callers**

Update the dataclass:

```python
machine_facts: RytmSnapshotMachineFacts = field(default_factory=_empty_machine_facts)
```

Update `decode()`:

```python
machine_facts = _extract_machine_facts(unpacked)
return RytmKitSnapshot(
    slot=slot,
    kit_name=kit_name,
    raw=raw,
    unpacked=unpacked,
    machine_facts=machine_facts,
)
```

The default factory keeps existing direct constructors in these files valid while the decoder path gains real facts:

- `tests/test_devices.py`
- `tests/test_devices_strategies_message_renderer.py`
- `tests/test_devices_strategies_mutation_planner.py`
- `tests/test_senders_guarded.py`
- `tests/test_senders_hardware.py`

- [ ] **Step 7: Run snapshot decoder tests**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py -n 0
```

Expected: PASS.

## Task 4: Planner Convenience Method Refuses Unpromoted Snapshot Facts

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py`
- Test: `tests/test_devices_strategies_mutation_planner.py`

- [ ] **Step 1: Write the failing planner tests**

Add:

```python
def test_planner_refuses_snapshot_machine_facts_until_promoted() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner

    snapshot = _make_snapshot(slot=7)
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_snapshot_machine_facts(
        snapshot,
        depth=1,
    )

    assert plan.ready is False
    assert plan.events == ()
    assert "candidate-only" in plan.readiness_reason
```

Add:

```python
def test_planner_uses_promoted_snapshot_machine_facts() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogRytmMutationPlanner,
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad={
            1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
            2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
            3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
        },
        promoted=True,
    )
    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"", machine_facts=facts)

    plan = AnalogRytmMutationPlanner(seed=1).plan_for_snapshot_machine_facts(
        snapshot,
        depth=1,
    )

    assert plan.ready is True
    assert {event.pad for event in plan.events} == {1, 2, 3}
```

- [ ] **Step 2: Run planner tests to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_mutation_planner.py::test_planner_refuses_snapshot_machine_facts_until_promoted tests/test_devices_strategies_mutation_planner.py::test_planner_uses_promoted_snapshot_machine_facts -n 0
```

Expected: FAIL because `plan_for_snapshot_machine_facts` does not exist.

- [ ] **Step 3: Implement the planner method**

Add to `AnalogRytmMutationPlanner`:

```python
def plan_for_snapshot_machine_facts(
    self,
    snapshot: RytmKitSnapshot,
    depth: int,
) -> RytmMutationPlan:
    """Build a plan from machine facts already decoded on ``snapshot``."""

    self._validate_inputs(snapshot, depth)
    if not snapshot.machine_facts.promoted:
        return RytmMutationPlan(
            snapshot=snapshot,
            depth=depth,
            events=(),
            ready=False,
            readiness_reason="snapshot machine facts are candidate-only; promote offsets before mutation",
        )

    machine_values = {
        pad: fact.decoded_machine_value
        for pad, fact in snapshot.machine_facts.facts_by_pad.items()
        if fact.decoded_machine_value is not None
    }
    return self.plan_for_machine_values(snapshot, depth, machine_values)
```

If mypy/pyright objects to `int | None`, use an explicit loop:

```python
machine_values: dict[int, int] = {}
for pad, fact in snapshot.machine_facts.facts_by_pad.items():
    if fact.decoded_machine_value is not None:
        machine_values[pad] = fact.decoded_machine_value
```

- [ ] **Step 4: Run planner tests**

Run:

```powershell
python -m pytest tests/test_devices_strategies_mutation_planner.py -n 0
```

Expected: PASS.

## Task 5: Closeout Verification

**Files:**
- Modify: `docs/STATUS.md`

- [ ] **Step 1: Add status checkpoint**

Add one line near the top of `docs/STATUS.md`:

```markdown
- 2026-05-20: Added passive Rytm snapshot machine-fact decoding plan/implementation. Real kit names now decode from the observed Rytm kit header offset, machine facts are extracted from the 12-pad kit payload, and tom-pad values remain candidate-only until hardware/manual verification promotes them.
```

- [ ] **Step 2: Run focused tests**

Run:

```powershell
python -m pytest tests/test_devices_strategies_snapshot_decoder.py tests/test_devices_strategies_mutation_planner.py -n 0
```

Expected: PASS.

- [ ] **Step 3: Run architecture, fast, full, coverage, lint, and review gates**

Run:

```powershell
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m vulture rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py tests/test_devices_strategies_snapshot_decoder.py tests/test_devices_strategies_mutation_planner.py --min-confidence 80
python scripts/code_review_gate.py --mode cli
```

Expected: all PASS. Do not push if any gate fails.

## Done Criteria

- Real-layout Rytm kit names decode from offset `8`.
- Snapshot machine facts are immutable, passive, and attached to `RytmKitSnapshot`.
- Machine facts decode all 12 pad slots, but pads 6-8 remain candidate-only until verified.
- The planner can refuse candidate-only snapshot facts safely.
- The planner can delegate promoted facts into PR #50's machine-value route.
- No real MIDI imports, no port openings, no hardware sends.
- V1.34 parity remains byte-identical.
- No stacked PR is opened; implementation waits for PR #50 to merge, then starts from fresh `origin/modularize-v1.34`.

## Execution Handoff

After PR #50 merges, create a fresh branch from `origin/modularize-v1.34`, copy or keep this plan in that branch, then execute with TDD. Do not add this work to the PR #50 branch unless Eddie explicitly asks for it as review feedback.
