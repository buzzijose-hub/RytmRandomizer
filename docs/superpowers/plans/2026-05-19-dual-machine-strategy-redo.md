# Dual-Machine Strategy Redo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the Rytm + Analog Four dual-machine foundation as one bundled PR that follows the merged PR #43 `Device` Strategy architecture and keeps live operator commands human-friendly.

**Architecture:** Machine-specific behavior lives behind registered `Device` instances. `AnalogRytmDevice` remains the reference device. The redo adds a registered `AnalogFourDevice`, A4 strategy modules for snapshot decoding, mutation planning, and message rendering, generic guarded/hardware senders that consume `Device.message_renderer`, and a dual-machine target resolver that fans out through `devices.all_devices()` for `rytm`, `a4`, and `both`.

**Tech Stack:** Python 3.11, pytest with `pytest.mark.fast`, dataclasses, `typing.Protocol`, existing `rytm_randomizer.devices` registry, existing `rytm_randomizer.snapshot` Strategy Protocols, existing `MockMidiSender` / `RealMidiSender` MIDI boundary.

---

## Preconditions

- Work from the isolated worktree at `C:\Users\Jose Buzzi\Documents\RytmRandomizer\.worktrees\dual-machine-strategy-redo`.
- Base branch is `origin/modularize-v1.34` at or after merge commit `6452b44`.
- Do not send MIDI during this plan. Hardware validation is manual and comes after tested runtime paths exist.
- Keep this as one bundled PR against `modularize-v1.34`; do not open stacked PRs.
- Do not add architecture-test allowlist entries unless the PR body explains the reviewer-approved exception.

## File Structure

Create:

- `docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md` - source-material map from PR #36 and closed stacked PRs to the new strategy architecture.
- `rytm_randomizer/devices/analog_four.py` - composition-only `AnalogFourDevice` registered with the device registry.
- `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py` - A4 snapshot dataclass and snapshot decoder strategy.
- `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py` - A4 plan/event dataclasses and readiness-gated planner strategy.
- `rytm_randomizer/devices/strategies/analog_four_message_renderer.py` - A4 renderer strategy for mock messages and CC triples.
- `rytm_randomizer/senders/__init__.py` - generic sender package exports.
- `rytm_randomizer/senders/guarded.py` - dry-run/readiness-checked generic send path.
- `rytm_randomizer/senders/hardware.py` - arm-gated real MIDI generic send path.
- `rytm_randomizer/dual_machine/__init__.py` - dual-machine orchestration package exports.
- `rytm_randomizer/dual_machine/targets.py` - human-friendly target aliases resolved through `devices.all_devices()`.
- `rytm_randomizer/dual_machine/reports.py` - combined target/readiness report helpers.
- `tests/test_analog_four_device.py`
- `tests/test_devices_strategies_analog_four_snapshot_decoder.py`
- `tests/test_devices_strategies_analog_four_mutation_planner.py`
- `tests/test_devices_strategies_analog_four_message_renderer.py`
- `tests/test_senders_guarded.py`
- `tests/test_senders_hardware.py`
- `tests/test_dual_machine_targets.py`
- `tests/test_dual_machine_reports.py`

Modify:

- `rytm_randomizer/devices/__init__.py` - import/register `AnalogFourDevice` and export public names if needed.
- `rytm_randomizer/devices/strategies/__init__.py` - export A4 strategies and dataclasses.
- `rytm_randomizer/cli.py` - add passive report commands only after the core target resolver exists.
- `rytm_randomizer/help_text.py` - document passive operator command names.
- `docs/STATUS.md` - update project status after the implementation is in place.
- `docs/MANUAL_HARDWARE_VALIDATION.md` - add manual validation steps, not automated sends.

Do not create:

- `rytm_randomizer/analog_four/`
- `rytm_randomizer/rytm/`
- `rytm_randomizer/essence/`
- per-device sender modules such as `analog_four_sender.py` or `rytm_sender.py`

## Task 1: Capture The Migration Map

**Files:**
- Create: `docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md`

- [ ] **Step 1: Inspect the source PR review and file list**

Run:

```powershell
gh pr view 36 --json comments,reviewDecision,mergeStateStatus,state,url,title,headRefName,baseRefName
gh pr view 36 --json files --jq '.files[].path'
```

Expected:

- PR #36 is open or superseded with changes requested.
- Review mentions the redo path through `Device` Strategy capabilities.
- The file list includes old top-level surfaces such as `rytm_randomizer/analog_four/`, `rytm_randomizer/dual_machine/`, and `rytm_randomizer/essence/`.

- [ ] **Step 2: Create the migration-map document**

Add `docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md` with this structure:

```markdown
# Dual-Machine Strategy Redo Migration Map

## Source Material

- PR #36: architecture review source for the redo.
- Closed stacked PRs #37-#41: source material only; do not reopen the cascade.

## Migration Table

| Old surface | New home | Action |
|---|---|---|
| `rytm_randomizer/analog_four/snapshot_decoder.py` | `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py` | Migrate public decode behavior behind `AnalogFourSnapshotDecoder.decode(raw, slot)`. |
| `rytm_randomizer/analog_four/snapshot_mock_runtime.py` | `rytm_randomizer/devices/strategies/analog_four_message_renderer.py` and `rytm_randomizer/senders/guarded.py` | Split pure rendering from sending. |
| `rytm_randomizer/analog_four/controlled_diff.py` | `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py` | Keep planning intent; remove cross-family private imports. |
| `rytm_randomizer/dual_machine/*` | `rytm_randomizer/dual_machine/targets.py` and `rytm_randomizer/dual_machine/reports.py` | Keep orchestration/reporting only; depend on `devices.all_devices()`. |
| per-device sender modules | `rytm_randomizer/senders/guarded.py` and `rytm_randomizer/senders/hardware.py` | Collapse duplicate sender logic. |
| Rytm engine internals under `essence/` or `rytm/` | existing `data/`, `engines/`, or `devices/strategies/` modules | Do not create parallel device subpackages. |

## Preserved Operator Contracts

- `rytm` / `rytm-only`
- `a4` / `a4-only`
- `both`
- snapshot mode primary
- anchor mode retained as explicit controlled baseline

## Dropped Or Deferred

- GUI implementation
- audio analyzer
- genre prompt kit generation
- continuous knob tracking
- automated hardware sends in tests
```

- [ ] **Step 3: Self-review the migration map**

Run:

```powershell
rg -n "REPLACE_ME|UNDECIDED|INCOMPLETE" docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md
```

Expected: no output.

- [ ] **Step 4: Commit the migration map**

Run:

```powershell
git add docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md
git commit -m "docs: map dual-machine strategy redo"
```

Expected: commit succeeds.

## Task 2: Add Analog Four Snapshot Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py`
- Create: `tests/test_devices_strategies_analog_four_snapshot_decoder.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`

- [ ] **Step 1: Write the failing snapshot-decoder tests**

Create `tests/test_devices_strategies_analog_four_snapshot_decoder.py`:

```python
"""Tests for Analog Four snapshot decoder Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _a4_kit_payload(name: bytes = b"A4KIT") -> bytes:
    """Build a minimal A4 kit-dump-like body for decoder tests.

    The first three bytes are Elektron's manufacturer ID. The fourth byte is
    the A4 candidate kit type byte used by this strategy test. The next 16
    bytes carry a NUL-padded ASCII name. The decoder treats the remaining bytes
    as opaque candidate payload until offsets are promoted.
    """

    padded_name = name[:16].ljust(16, b"\x00")
    return bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02, 0x03])


def test_decode_returns_analog_four_kit_snapshot_with_slot_and_name() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    snapshot = AnalogFourSnapshotDecoder().decode(_a4_kit_payload(b"FOUR01"), slot=2)

    assert isinstance(snapshot, AnalogFourKitSnapshot)
    assert snapshot.slot == 2
    assert snapshot.kit_name == "FOUR01"
    assert snapshot.raw == _a4_kit_payload(b"FOUR01")
    assert snapshot.offsets_promoted is False


def test_decode_rejects_negative_slot() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    with pytest.raises(ValueError, match="slot must be non-negative"):
        AnalogFourSnapshotDecoder().decode(_a4_kit_payload(), slot=-1)


def test_decode_rejects_payload_without_elektron_prefix() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = bytes([0x7E, 0x7E, 0x7E, 0x07]) + bytes(24)

    with pytest.raises(ValueError, match="Elektron manufacturer id"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_is_deterministic_for_same_input() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    decoder = AnalogFourSnapshotDecoder()
    payload = _a4_kit_payload(b"DET")

    assert decoder.decode(payload, slot=1) == decoder.decode(payload, slot=1)
```

- [ ] **Step 2: Run the new tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_snapshot_decoder.py -n 0 -q
```

Expected: FAIL because `AnalogFourSnapshotDecoder` and `AnalogFourKitSnapshot` are not exported.

- [ ] **Step 3: Implement the snapshot strategy**

Create `rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py`:

```python
"""Analog Four MK2 snapshot decoder Strategy."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

_ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])
_A4_CANDIDATE_KIT_TYPE_BYTE: Final[int] = 0x07
_KIT_NAME_OFFSET: Final[int] = 4
_KIT_NAME_LENGTH: Final[int] = 16


@dataclass(frozen=True)
class AnalogFourKitSnapshot:
    """Candidate Analog Four kit snapshot captured from a SysEx payload."""

    slot: int
    kit_name: str
    raw: bytes
    offsets_promoted: bool = False


class AnalogFourSnapshotDecoder:
    """Decode a candidate Analog Four kit snapshot from raw bytes."""

    def decode(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        """Decode ``raw`` into an :class:`AnalogFourKitSnapshot`.

        The A4 offsets are candidate-level at this stage. The decoder validates
        the Elektron prefix and preserves raw bytes; promoted offset extraction
        comes in a later task after the migration map identifies the exact old
        PR #36 behavior to move.
        """

        if slot < 0:
            raise ValueError("AnalogFourSnapshotDecoder.decode: slot must be non-negative")
        if not raw.startswith(_ELEKTRON_MFR_ID):
            raise ValueError("AnalogFourSnapshotDecoder.decode: missing Elektron manufacturer id")
        if len(raw) < _KIT_NAME_OFFSET + _KIT_NAME_LENGTH:
            raise ValueError("AnalogFourSnapshotDecoder.decode: payload too short for kit name")
        if raw[3] != _A4_CANDIDATE_KIT_TYPE_BYTE:
            raise ValueError(
                "AnalogFourSnapshotDecoder.decode: candidate kit type byte 0x07 not present"
            )

        name_bytes = raw[_KIT_NAME_OFFSET : _KIT_NAME_OFFSET + _KIT_NAME_LENGTH]
        kit_name = name_bytes.split(b"\x00", 1)[0].decode("ascii", errors="ignore")
        return AnalogFourKitSnapshot(
            slot=slot,
            kit_name=kit_name,
            raw=bytes(raw),
            offsets_promoted=False,
        )
```

- [ ] **Step 4: Export the new names**

Modify `rytm_randomizer/devices/strategies/__init__.py` to import and export:

```python
from .analog_four_snapshot_decoder import AnalogFourKitSnapshot, AnalogFourSnapshotDecoder
```

and include these strings in `__all__`:

```python
"AnalogFourKitSnapshot",
"AnalogFourSnapshotDecoder",
```

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_snapshot_decoder.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: new tests pass; architecture tests pass.

Commit:

```powershell
git add rytm_randomizer/devices/strategies/analog_four_snapshot_decoder.py rytm_randomizer/devices/strategies/__init__.py tests/test_devices_strategies_analog_four_snapshot_decoder.py
git commit -m "feat: add Analog Four snapshot strategy"
```

## Task 3: Add Analog Four Mutation Planner Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py`
- Create: `tests/test_devices_strategies_analog_four_mutation_planner.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`

- [ ] **Step 1: Write the failing mutation-planner tests**

Create `tests/test_devices_strategies_analog_four_mutation_planner.py`:

```python
"""Tests for Analog Four mutation planner Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _snapshot(*, offsets_promoted: bool = False):
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot

    return AnalogFourKitSnapshot(
        slot=1,
        kit_name="A4",
        raw=b"\x00\x20\x3c\x07" + bytes(32),
        offsets_promoted=offsets_promoted,
    )


def test_plan_returns_not_ready_when_offsets_are_candidate_only() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    plan = AnalogFourMutationPlanner(seed=0).plan(_snapshot(offsets_promoted=False), depth=1)

    assert plan.ready is False
    assert plan.events == ()
    assert "offsets are candidate" in plan.readiness_reason


def test_plan_returns_ready_events_when_offsets_are_promoted() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    plan = AnalogFourMutationPlanner(seed=0).plan(_snapshot(offsets_promoted=True), depth=1)

    assert plan.ready is True
    assert plan.readiness_reason == ""
    assert len(plan.events) == 4
    assert {event.track for event in plan.events} == {1, 2, 3, 4}


def test_plan_rejects_wrong_snapshot_type() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    with pytest.raises(ValueError, match="AnalogFourKitSnapshot"):
        AnalogFourMutationPlanner().plan("not a snapshot", depth=1)  # type: ignore[arg-type]


def test_plan_rejects_depth_outside_bounds() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    planner = AnalogFourMutationPlanner()

    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=-1)
    with pytest.raises(ValueError, match=r"\[0,\s*7\]"):
        planner.plan(_snapshot(offsets_promoted=True), depth=8)


def test_plan_is_deterministic_for_same_seed_slot_and_depth() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlanner

    planner = AnalogFourMutationPlanner(seed=99)
    snap = _snapshot(offsets_promoted=True)

    assert planner.plan(snap, depth=3) == planner.plan(snap, depth=3)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_mutation_planner.py -n 0 -q
```

Expected: FAIL because the planner names are not exported.

- [ ] **Step 3: Implement the planner**

Create `rytm_randomizer/devices/strategies/analog_four_mutation_planner.py`:

```python
"""Analog Four MK2 mutation planner Strategy."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Final

from .analog_four_snapshot_decoder import AnalogFourKitSnapshot

MAX_A4_DEPTH: Final[int] = 7


@dataclass(frozen=True)
class AnalogFourPlanEvent:
    """One target change in an Analog Four mutation plan."""

    track: int
    parameter: str
    control: int
    value: int


@dataclass(frozen=True)
class AnalogFourMutationPlan:
    """Complete A4 mutation plan for one snapshot and depth."""

    snapshot: AnalogFourKitSnapshot
    depth: int
    events: tuple[AnalogFourPlanEvent, ...] = field(default_factory=tuple)
    ready: bool = True
    readiness_reason: str = ""


class AnalogFourMutationPlanner:
    """Mutation planner for candidate Analog Four snapshots."""

    def __init__(self, *, seed: int = 0) -> None:
        self._seed = seed

    def plan(self, snapshot: AnalogFourKitSnapshot, depth: int) -> AnalogFourMutationPlan:
        """Build an A4 mutation plan.

        Candidate-only snapshots deliberately produce ``ready=False`` so the
        generic sender refuses real hardware sends until offsets are promoted.
        """

        if not isinstance(snapshot, AnalogFourKitSnapshot):
            raise ValueError(
                "AnalogFourMutationPlanner.plan: snapshot must be an "
                f"AnalogFourKitSnapshot, got {type(snapshot).__name__}"
            )
        if depth < 0 or depth > MAX_A4_DEPTH:
            raise ValueError(
                f"AnalogFourMutationPlanner.plan: depth must be in [0, {MAX_A4_DEPTH}], "
                f"got {depth}"
            )
        if not snapshot.offsets_promoted:
            return AnalogFourMutationPlan(
                snapshot=snapshot,
                depth=depth,
                events=(),
                ready=False,
                readiness_reason="Analog Four offsets are candidate-only; promote offsets before real send",
            )

        rng_seed = (self._seed * 1_000_003) ^ (snapshot.slot * 1009) ^ depth
        rng = random.Random(rng_seed)  # noqa: S311 - non-crypto mutation planning
        events = tuple(
            AnalogFourPlanEvent(
                track=track,
                parameter="Filter 1 Frequency",
                control=74,
                value=rng.randint(48, 96) if depth else 64,
            )
            for track in range(1, 5)
        )
        return AnalogFourMutationPlan(
            snapshot=snapshot,
            depth=depth,
            events=events,
            ready=True,
            readiness_reason="",
        )
```

- [ ] **Step 4: Export the planner names**

Modify `rytm_randomizer/devices/strategies/__init__.py` to import and export:

```python
from .analog_four_mutation_planner import (
    AnalogFourMutationPlan,
    AnalogFourMutationPlanner,
    AnalogFourPlanEvent,
    MAX_A4_DEPTH,
)
```

and include these strings in `__all__`:

```python
"AnalogFourMutationPlan",
"AnalogFourMutationPlanner",
"AnalogFourPlanEvent",
"MAX_A4_DEPTH",
```

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_mutation_planner.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: new tests pass; architecture tests pass.

Commit:

```powershell
git add rytm_randomizer/devices/strategies/analog_four_mutation_planner.py rytm_randomizer/devices/strategies/__init__.py tests/test_devices_strategies_analog_four_mutation_planner.py
git commit -m "feat: add Analog Four mutation strategy"
```

## Task 4: Add Analog Four Message Renderer Strategy

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_four_message_renderer.py`
- Create: `tests/test_devices_strategies_analog_four_message_renderer.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`

- [ ] **Step 1: Write the failing renderer tests**

Create `tests/test_devices_strategies_analog_four_message_renderer.py`:

```python
"""Tests for Analog Four message renderer Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _plan_event():
    from rytm_randomizer.devices.strategies import (
        AnalogFourKitSnapshot,
        AnalogFourMutationPlan,
        AnalogFourPlanEvent,
    )

    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    event = AnalogFourPlanEvent(track=2, parameter="Filter 1 Frequency", control=74, value=91)
    plan = AnalogFourMutationPlan(snapshot=snapshot, depth=1, events=(event,))
    return plan, event


def test_to_mock_message_renders_midi_message_for_event() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer
    from rytm_randomizer.mock_midi import MidiMessage

    plan, event = _plan_event()
    message = AnalogFourMessageRenderer().to_mock_message(event, plan)

    assert isinstance(message, MidiMessage)
    assert message.type == "cc"
    assert message.channel == 1
    assert message.control == 74
    assert message.value == 91
    assert message.metadata["track"] == 2
    assert message.metadata["parameter"] == "Filter 1 Frequency"


def test_to_cc_triple_renders_channel_control_value() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourMessageRenderer

    plan, event = _plan_event()

    assert AnalogFourMessageRenderer().to_cc_triple(event, plan) == (1, 74, 91)


def test_renderer_rejects_track_outside_1_to_4() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogFourKitSnapshot,
        AnalogFourMessageRenderer,
        AnalogFourMutationPlan,
        AnalogFourPlanEvent,
    )

    snapshot = AnalogFourKitSnapshot(slot=1, kit_name="A4", raw=b"", offsets_promoted=True)
    event = AnalogFourPlanEvent(track=5, parameter="Filter 1 Frequency", control=74, value=91)
    plan = AnalogFourMutationPlan(snapshot=snapshot, depth=1, events=(event,))

    with pytest.raises(ValueError, match="track must be in \\[1, 4\\]"):
        AnalogFourMessageRenderer().to_cc_triple(event, plan)
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_message_renderer.py -n 0 -q
```

Expected: FAIL because `AnalogFourMessageRenderer` is not exported.

- [ ] **Step 3: Implement the renderer**

Create `rytm_randomizer/devices/strategies/analog_four_message_renderer.py`:

```python
"""Analog Four MK2 message renderer Strategy."""

from __future__ import annotations

from typing import Final

from ...mock_midi import MidiMessage, build_cc_message
from .analog_four_mutation_planner import AnalogFourMutationPlan, AnalogFourPlanEvent

_TRACK_COUNT: Final[int] = 4


class AnalogFourMessageRenderer:
    """Render Analog Four plan events into mock messages or CC triples."""

    def to_mock_message(
        self, event: AnalogFourPlanEvent, plan: AnalogFourMutationPlan
    ) -> MidiMessage:
        """Render one event into an inert mock MIDI message."""

        channel, control, value = self.to_cc_triple(event, plan)
        return build_cc_message(
            channel=channel,
            control=control,
            value=value,
            metadata={
                "device_id": "analog_four_mk2",
                "track": event.track,
                "parameter": event.parameter,
                "snapshot_slot": plan.snapshot.slot,
            },
        )

    def to_cc_triple(
        self, event: AnalogFourPlanEvent, plan: AnalogFourMutationPlan
    ) -> tuple[int, int, int]:
        """Render one event into a zero-based MIDI CC triple."""

        if not isinstance(plan, AnalogFourMutationPlan):
            raise TypeError(
                "AnalogFourMessageRenderer.to_cc_triple expected AnalogFourMutationPlan, "
                f"got {type(plan).__name__}"
            )
        if not isinstance(event, AnalogFourPlanEvent):
            raise TypeError(
                "AnalogFourMessageRenderer.to_cc_triple expected AnalogFourPlanEvent, "
                f"got {type(event).__name__}"
            )
        if event.track < 1 or event.track > _TRACK_COUNT:
            raise ValueError(
                f"AnalogFourMessageRenderer.to_cc_triple: track must be in [1, 4], "
                f"got {event.track}"
            )
        if event.control < 0 or event.control > 127:
            raise ValueError("AnalogFourMessageRenderer.to_cc_triple: control must be in [0, 127]")
        if event.value < 0 or event.value > 127:
            raise ValueError("AnalogFourMessageRenderer.to_cc_triple: value must be in [0, 127]")

        return (event.track - 1, event.control, event.value)
```

- [ ] **Step 4: Export the renderer**

Modify `rytm_randomizer/devices/strategies/__init__.py` to import and export:

```python
from .analog_four_message_renderer import AnalogFourMessageRenderer
```

and include this string in `__all__`:

```python
"AnalogFourMessageRenderer",
```

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_four_message_renderer.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: new tests pass; architecture tests pass.

Commit:

```powershell
git add rytm_randomizer/devices/strategies/analog_four_message_renderer.py rytm_randomizer/devices/strategies/__init__.py tests/test_devices_strategies_analog_four_message_renderer.py
git commit -m "feat: add Analog Four message renderer"
```

## Task 5: Register AnalogFourDevice

**Files:**
- Create: `rytm_randomizer/devices/analog_four.py`
- Create: `tests/test_analog_four_device.py`
- Modify: `rytm_randomizer/devices/__init__.py`

- [ ] **Step 1: Write the failing device tests**

Create `tests/test_analog_four_device.py`:

```python
"""Tests for registered AnalogFourDevice."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_analog_four_device_registers_with_device_registry() -> None:
    from rytm_randomizer.devices import all_devices, get_device

    assert "analog_four_mk2" in all_devices()
    assert get_device("analog_four_mk2").display_name == "Elektron Analog Four MKII"


def test_analog_four_device_satisfies_device_protocol() -> None:
    from rytm_randomizer.devices import Device, get_device

    assert isinstance(get_device("analog_four_mk2"), Device)


def test_analog_four_device_exposes_expected_identity_attributes() -> None:
    from rytm_randomizer.devices import get_device

    a4 = get_device("analog_four_mk2")

    assert a4.device_id == "analog_four_mk2"
    assert a4.default_midi_channel == 0
    assert a4.track_count == 4
    assert a4.sysex_manufacturer_id == bytes([0x00, 0x20, 0x3C])
    assert a4.report_header == "RytmRandomizer Analog Four MK2 Guarded Send"


def test_analog_four_device_convenience_methods_delegate_to_strategies() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import AnalogFourMutationPlan

    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    a4 = get_device("analog_four_mk2")

    snapshot = a4.decode_snapshot(raw, slot=1)
    plan = a4.plan_mutation(snapshot, depth=1)

    assert isinstance(plan, AnalogFourMutationPlan)
    assert plan.ready is False
    assert a4.to_mock_messages(plan) == []
    assert tuple(a4.to_cc_messages(plan)) == ()
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_analog_four_device.py -n 0 -q
```

Expected: FAIL because `analog_four_mk2` is not registered.

- [ ] **Step 3: Implement the device**

Create `rytm_randomizer/devices/analog_four.py`:

```python
"""AnalogFourDevice composition surface."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Final

from ..mock_midi import MidiMessage
from . import registry
from .base import Device
from .strategies import (
    AnalogFourKitSnapshot,
    AnalogFourMessageRenderer,
    AnalogFourMutationPlan,
    AnalogFourMutationPlanner,
    AnalogFourSnapshotDecoder,
)

_ELEKTRON_MFR_ID: Final[bytes] = bytes([0x00, 0x20, 0x3C])
_REPORT_HEADER: Final[str] = "RytmRandomizer Analog Four MK2 Guarded Send"


class AnalogFourDevice:
    """Analog Four MKII surfaced as a registered Device."""

    device_id: Final[str] = "analog_four_mk2"
    display_name: Final[str] = "Elektron Analog Four MKII"
    default_midi_channel: Final[int] = 0
    track_count: Final[int] = 4
    sysex_manufacturer_id: Final[bytes] = _ELEKTRON_MFR_ID
    report_header: Final[str] = _REPORT_HEADER

    def __init__(self) -> None:
        self.snapshot_decoder = AnalogFourSnapshotDecoder()
        self.mutation_planner = AnalogFourMutationPlanner()
        self.message_renderer = AnalogFourMessageRenderer()

    def decode_snapshot(self, raw: bytes, slot: int) -> AnalogFourKitSnapshot:
        return self.snapshot_decoder.decode(raw, slot=slot)

    def plan_mutation(self, snapshot: AnalogFourKitSnapshot, depth: int) -> AnalogFourMutationPlan:
        return self.mutation_planner.plan(snapshot, depth)

    def to_mock_messages(self, plan: AnalogFourMutationPlan) -> list[MidiMessage]:
        if not isinstance(plan, AnalogFourMutationPlan):
            raise TypeError(
                "AnalogFourDevice.to_mock_messages expected AnalogFourMutationPlan, got "
                f"{type(plan).__name__}"
            )
        if not plan.ready:
            return []
        return [self.message_renderer.to_mock_message(event, plan) for event in plan.events]

    def to_cc_messages(self, plan: AnalogFourMutationPlan) -> Iterable[tuple[int, int, int]]:
        if not isinstance(plan, AnalogFourMutationPlan):
            raise TypeError(
                "AnalogFourDevice.to_cc_messages expected AnalogFourMutationPlan, got "
                f"{type(plan).__name__}"
            )
        if not plan.ready:
            return ()
        return tuple(self.message_renderer.to_cc_triple(event, plan) for event in plan.events)


registry.register_device(AnalogFourDevice())


def _assert_protocol_conformance() -> None:
    if not isinstance(registry.get_device("analog_four_mk2"), Device):
        raise AssertionError(  # noqa: S101 - structural typing invariant
            "AnalogFourDevice does not conform to Device protocol"
        )


_assert_protocol_conformance()
```

- [ ] **Step 4: Import the device from package init**

Modify `rytm_randomizer/devices/__init__.py` so importing `rytm_randomizer.devices` imports both concrete device modules for registration:

```python
from . import analog_four as _analog_four  # noqa: F401
from . import analog_rytm as _analog_rytm  # noqa: F401
```

Keep existing public exports intact.

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_analog_four_device.py -n 0 -q
python -m pytest tests/architecture/test_device_protocol_enforcement.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: all pass with no architecture allowlist additions.

Commit:

```powershell
git add rytm_randomizer/devices/analog_four.py rytm_randomizer/devices/__init__.py tests/test_analog_four_device.py
git commit -m "feat: register Analog Four device"
```

## Task 6: Add Human-Friendly Target Resolution

**Files:**
- Create: `rytm_randomizer/dual_machine/__init__.py`
- Create: `rytm_randomizer/dual_machine/targets.py`
- Create: `tests/test_dual_machine_targets.py`

- [ ] **Step 1: Write the failing target tests**

Create `tests/test_dual_machine_targets.py`:

```python
"""Tests for dual-machine target resolution."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_resolve_target_accepts_rytm_aliases() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    for alias in ("rytm", "rytm-only"):
        devices = resolve_target_devices(alias)
        assert tuple(devices) == ("analog_rytm_mk2",)


def test_resolve_target_accepts_a4_aliases() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    for alias in ("a4", "a4-only"):
        devices = resolve_target_devices(alias)
        assert tuple(devices) == ("analog_four_mk2",)


def test_resolve_target_accepts_both_alias() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    devices = resolve_target_devices("both")

    assert tuple(devices) == ("analog_rytm_mk2", "analog_four_mk2")


def test_resolve_target_rejects_unknown_alias() -> None:
    from rytm_randomizer.dual_machine.targets import resolve_target_devices

    with pytest.raises(ValueError, match="unknown target"):
        resolve_target_devices("octatrack")
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_dual_machine_targets.py -n 0 -q
```

Expected: FAIL because `rytm_randomizer.dual_machine` does not exist.

- [ ] **Step 3: Implement target resolution**

Create `rytm_randomizer/dual_machine/targets.py`:

```python
"""Human-friendly dual-machine target resolution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Final

from ..devices import Device, all_devices

_ALIASES: Final[dict[str, tuple[str, ...]]] = {
    "rytm": ("analog_rytm_mk2",),
    "rytm-only": ("analog_rytm_mk2",),
    "a4": ("analog_four_mk2",),
    "a4-only": ("analog_four_mk2",),
    "both": ("analog_rytm_mk2", "analog_four_mk2"),
}


def resolve_target_devices(
    target: str,
    *,
    registry: Mapping[str, Device] | None = None,
) -> Mapping[str, Device]:
    """Resolve a live-friendly target alias to registered devices."""

    normalized = target.strip().lower()
    if normalized not in _ALIASES:
        raise ValueError(
            "unknown target "
            f"{target!r}; expected one of {', '.join(sorted(_ALIASES))}"
        )
    source = all_devices() if registry is None else registry
    return {device_id: source[device_id] for device_id in _ALIASES[normalized]}
```

Create `rytm_randomizer/dual_machine/__init__.py`:

```python
"""Dual-machine orchestration helpers."""

from __future__ import annotations

from .targets import resolve_target_devices

__all__ = ["resolve_target_devices"]
```

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_dual_machine_targets.py -n 0 -q
python -m pytest tests/architecture/test_device_protocol_enforcement.py -n 0 -q
```

Expected: all pass; architecture test proves `dual_machine` does not import concrete device families.

Commit:

```powershell
git add rytm_randomizer/dual_machine/__init__.py rytm_randomizer/dual_machine/targets.py tests/test_dual_machine_targets.py
git commit -m "feat: resolve dual-machine target aliases"
```

## Task 7: Add Generic Guarded Sender

**Files:**
- Create: `rytm_randomizer/senders/__init__.py`
- Create: `rytm_randomizer/senders/guarded.py`
- Create: `tests/test_senders_guarded.py`

- [ ] **Step 1: Write the failing guarded-sender tests**

Create `tests/test_senders_guarded.py`:

```python
"""Tests for generic guarded sender."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _a4_not_ready_plan():
    from rytm_randomizer.devices import get_device

    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    a4 = get_device("analog_four_mk2")
    snapshot = a4.decode_snapshot(raw, slot=0)
    return a4, a4.plan_mutation(snapshot, depth=1)


def test_guarded_send_refuses_not_ready_plan_without_messages() -> None:
    from rytm_randomizer.senders.guarded import guarded_send

    device, plan = _a4_not_ready_plan()
    result = guarded_send(device, plan)

    assert result.ready is False
    assert result.sent_count == 0
    assert "candidate-only" in result.reason


def test_guarded_send_renders_ready_plan_to_mock_messages() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.senders.guarded import guarded_send

    rytm = get_device("analog_rytm_mk2")
    snapshot = RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b"")
    plan = rytm.plan_mutation(snapshot, depth=1)
    result = guarded_send(rytm, plan)

    assert result.ready is True
    assert result.sent_count == len(plan.events)
    assert result.reason == ""
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_senders_guarded.py -n 0 -q
```

Expected: FAIL because `rytm_randomizer.senders.guarded` does not exist.

- [ ] **Step 3: Implement guarded sender**

Create `rytm_randomizer/senders/guarded.py`:

```python
"""Generic guarded sender for Device mutation plans."""

from __future__ import annotations

from dataclasses import dataclass, field

from ..devices import Device


@dataclass(frozen=True)
class GuardedSendResult:
    """Result of a dry-run/readiness-checked send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""
    messages: tuple[object, ...] = field(default_factory=tuple)


def guarded_send(device: Device, plan: object) -> GuardedSendResult:
    """Render ``plan`` through ``device`` without opening hardware."""

    ready = bool(getattr(plan, "ready", False))
    reason = str(getattr(plan, "readiness_reason", "plan is not ready"))
    if not ready:
        return GuardedSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason=reason,
            messages=(),
        )
    messages = tuple(device.to_mock_messages(plan))
    return GuardedSendResult(
        device_id=device.device_id,
        ready=True,
        sent_count=len(messages),
        reason="",
        messages=messages,
    )
```

Create `rytm_randomizer/senders/__init__.py`:

```python
"""Generic senders that consume registered Device strategies."""

from __future__ import annotations

from .guarded import GuardedSendResult, guarded_send

__all__ = ["GuardedSendResult", "guarded_send"]
```

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_senders_guarded.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: all pass.

Commit:

```powershell
git add rytm_randomizer/senders/__init__.py rytm_randomizer/senders/guarded.py tests/test_senders_guarded.py
git commit -m "feat: add generic guarded sender"
```

## Task 8: Add Arm-Gated Hardware Sender

**Files:**
- Create: `rytm_randomizer/senders/hardware.py`
- Create: `tests/test_senders_hardware.py`
- Modify: `rytm_randomizer/senders/__init__.py`

- [ ] **Step 1: Write the failing hardware-sender tests**

Create `tests/test_senders_hardware.py`:

```python
"""Tests for generic hardware sender gates."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class RecordingSender:
    def __init__(self) -> None:
        self.messages: list[tuple[int, int, int]] = []

    def send(self, message: tuple[int, int, int]) -> None:
        self.messages.append(message)


def test_hardware_send_refuses_when_not_armed() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.strategies import RytmKitSnapshot
    from rytm_randomizer.senders.hardware import hardware_send

    rytm = get_device("analog_rytm_mk2")
    plan = rytm.plan_mutation(RytmKitSnapshot(slot=0, kit_name="", raw=b"", unpacked=b""), depth=1)
    sender = RecordingSender()

    result = hardware_send(rytm, plan, sender=sender, armed=False)

    assert result.ready is False
    assert result.sent_count == 0
    assert sender.messages == []
    assert "requires --arm" in result.reason


def test_hardware_send_refuses_not_ready_plan_even_when_armed() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.senders.hardware import hardware_send

    a4 = get_device("analog_four_mk2")
    raw = bytes([0x00, 0x20, 0x3C, 0x07]) + b"A4".ljust(16, b"\x00") + bytes(8)
    plan = a4.plan_mutation(a4.decode_snapshot(raw, slot=0), depth=1)
    sender = RecordingSender()

    result = hardware_send(a4, plan, sender=sender, armed=True)

    assert result.ready is False
    assert result.sent_count == 0
    assert sender.messages == []
    assert "candidate-only" in result.reason
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_senders_hardware.py -n 0 -q
```

Expected: FAIL because `rytm_randomizer.senders.hardware` does not exist.

- [ ] **Step 3: Implement hardware sender**

Create `rytm_randomizer/senders/hardware.py`:

```python
"""Generic arm-gated hardware sender for Device mutation plans."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from ..devices import Device


class TripleSender(Protocol):
    """Boundary for sending rendered CC triples in tests and production."""

    def send(self, message: tuple[int, int, int]) -> None: ...


@dataclass(frozen=True)
class HardwareSendResult:
    """Result of an arm-gated hardware send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""


def hardware_send(
    device: Device,
    plan: object,
    *,
    sender: TripleSender,
    armed: bool,
) -> HardwareSendResult:
    """Send a plan to hardware only when armed and ready."""

    if not armed:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason="hardware send requires --arm",
        )

    ready = bool(getattr(plan, "ready", False))
    reason = str(getattr(plan, "readiness_reason", "plan is not ready"))
    if not ready:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason=reason,
        )

    triples = tuple(device.to_cc_messages(plan))
    for triple in triples:
        sender.send(triple)
    return HardwareSendResult(
        device_id=device.device_id,
        ready=True,
        sent_count=len(triples),
        reason="",
    )
```

- [ ] **Step 4: Export hardware sender**

Modify `rytm_randomizer/senders/__init__.py` to import and export:

```python
from .hardware import HardwareSendResult, TripleSender, hardware_send
```

and include:

```python
"HardwareSendResult",
"TripleSender",
"hardware_send",
```

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_senders_hardware.py -n 0 -q
python -m pytest tests/architecture/test_no_side_effects.py -n 0 -q
python -m pytest tests/architecture/ -q
```

Expected: all pass and no real MIDI imports are pulled by passive modules.

Commit:

```powershell
git add rytm_randomizer/senders/__init__.py rytm_randomizer/senders/hardware.py tests/test_senders_hardware.py
git commit -m "feat: add arm-gated hardware sender"
```

## Task 9: Add Dual-Machine Reports

**Files:**
- Create: `rytm_randomizer/dual_machine/reports.py`
- Create: `tests/test_dual_machine_reports.py`
- Modify: `rytm_randomizer/dual_machine/__init__.py`

- [ ] **Step 1: Write the failing report tests**

Create `tests/test_dual_machine_reports.py`:

```python
"""Tests for dual-machine reports."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def test_target_report_lists_devices_for_both_target() -> None:
    from rytm_randomizer.dual_machine.reports import target_report

    text = target_report("both")

    assert "Target: both" in text
    assert "analog_rytm_mk2" in text
    assert "analog_four_mk2" in text
    assert "Rytm" in text
    assert "Analog Four" in text


def test_target_report_lists_single_a4_target() -> None:
    from rytm_randomizer.dual_machine.reports import target_report

    text = target_report("a4")

    assert "Target: a4" in text
    assert "analog_four_mk2" in text
    assert "analog_rytm_mk2" not in text
```

- [ ] **Step 2: Run tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_dual_machine_reports.py -n 0 -q
```

Expected: FAIL because `dual_machine.reports` does not exist.

- [ ] **Step 3: Implement report helper**

Create `rytm_randomizer/dual_machine/reports.py`:

```python
"""Operator-facing reports for dual-machine target selection."""

from __future__ import annotations

from .targets import resolve_target_devices


def target_report(target: str) -> str:
    """Return a passive report for the selected target alias."""

    devices = resolve_target_devices(target)
    lines = [f"Target: {target}", "Devices:"]
    for device_id, device in devices.items():
        lines.append(
            f"- {device_id}: {device.display_name} "
            f"({device.track_count} tracks/pads)"
        )
    return "\n".join(lines)
```

Modify `rytm_randomizer/dual_machine/__init__.py`:

```python
from .reports import target_report
from .targets import resolve_target_devices

__all__ = ["resolve_target_devices", "target_report"]
```

- [ ] **Step 4: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_dual_machine_reports.py -n 0 -q
python -m pytest tests/test_dual_machine_targets.py -n 0 -q
```

Expected: all pass.

Commit:

```powershell
git add rytm_randomizer/dual_machine/__init__.py rytm_randomizer/dual_machine/reports.py tests/test_dual_machine_reports.py
git commit -m "feat: add dual-machine target reports"
```

## Task 10: Wire Passive CLI Report Commands

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Write failing CLI tests**

Add tests to `tests/test_cli.py`:

```python
def test_dual_machine_target_report_prints_both_devices(capsys) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["dual-machine-target-report", "both"])

    out = capsys.readouterr().out
    assert exit_code == 0
    assert "Target: both" in out
    assert "analog_rytm_mk2" in out
    assert "analog_four_mk2" in out


def test_dual_machine_target_report_rejects_unknown_target(capsys) -> None:
    from rytm_randomizer.cli import main

    exit_code = main(["dual-machine-target-report", "octatrack"])

    err = capsys.readouterr().err
    assert exit_code == 2
    assert "unknown target" in err
```

- [ ] **Step 2: Run CLI tests and verify they fail**

Run:

```powershell
python -m pytest tests/test_cli.py::test_dual_machine_target_report_prints_both_devices tests/test_cli.py::test_dual_machine_target_report_rejects_unknown_target -n 0 -q
```

Expected: FAIL because the command does not exist.

- [ ] **Step 3: Add the passive CLI command**

Modify `rytm_randomizer/cli.py` to dispatch:

```python
if command == "dual-machine-target-report":
    if len(argv) != 2:
        print("Usage: python -m rytm_randomizer.cli dual-machine-target-report <rytm|a4|both>", file=sys.stderr)
        return 2
    from .dual_machine.reports import target_report

    try:
        print(target_report(argv[1]))
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0
```

Place the command near the other passive report commands. Do not import
`dual_machine.reports` at module import time if the surrounding CLI style keeps
report imports local.

- [ ] **Step 4: Update help text and fixture**

Modify `rytm_randomizer/help_text.py` and `tests/fixtures/cli_help_expected.txt` to include:

```text
  python -m rytm_randomizer.cli dual-machine-target-report <rytm|a4|both>
```

and command label:

```text
  dual-machine-target-report
                     Print the passive dual-machine target report.
```

- [ ] **Step 5: Run tests and commit**

Run:

```powershell
python -m pytest tests/test_cli.py -n 0 -q
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0 -q
python -m pytest tests/architecture/test_no_side_effects.py -n 0 -q
```

Expected: all pass; passive CLI still does not import or open real MIDI.

Commit:

```powershell
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/fixtures/cli_help_expected.txt
git commit -m "feat: add passive dual-machine target report"
```

## Task 11: Update Operator Docs And Status

**Files:**
- Modify: `docs/STATUS.md`
- Modify: `docs/MANUAL_HARDWARE_VALIDATION.md`
- Modify: `docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md`
- Create: `tests/test_manual_hardware_validation_doc.py`

- [ ] **Step 1: Update status doc**

Add a status note to `docs/STATUS.md`:

```markdown
## Dual-Machine Strategy Redo

- PR #43 is merged and is the governing architecture baseline.
- Rytm and Analog Four target language is operator-friendly: `rytm`, `a4`, `both`.
- Machine-specific behavior routes through registered `Device` Strategy capabilities.
- Hardware validation remains manual; automated tests do not open MIDI ports.
```

- [ ] **Step 2: Update manual hardware validation**

Add a manual-only section to `docs/MANUAL_HARDWARE_VALIDATION.md`:

```markdown
## Dual-Machine Strategy Redo Manual Validation

These checks are manual only. Do not add them to CI.

1. Run `python -m rytm_randomizer.cli dual-machine-target-report rytm`.
2. Confirm the report lists only `analog_rytm_mk2`.
3. Run `python -m rytm_randomizer.cli dual-machine-target-report a4`.
4. Confirm the report lists only `analog_four_mk2`.
5. Run `python -m rytm_randomizer.cli dual-machine-target-report both`.
6. Confirm both devices are listed.
7. Do not run armed hardware sends until the A4 readiness report says the plan is ready.
```

- [ ] **Step 3: Update migration map status**

Append:

```markdown
## Implementation Status

- `AnalogFourDevice` registered through `devices/registry.py`.
- `dual_machine` target selection goes through `devices.all_devices()`.
- Generic sender package added; readiness gates are centralized.
- No architecture-test allowlist entries were added.
```

- [ ] **Step 4: Add the manual-validation doc test**

Create `tests/test_manual_hardware_validation_doc.py`:

```python
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manual_hardware_validation_documents_dual_machine_strategy_redo() -> None:
    text = (ROOT / "docs" / "MANUAL_HARDWARE_VALIDATION.md").read_text()

    assert "## Dual-Machine Strategy Redo Manual Validation" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report rytm" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report a4" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report both" in text
    assert "manual only" in text.lower()
```

- [ ] **Step 5: Run docs checks and commit**

Run:

```powershell
python -m pytest tests/test_manual_hardware_validation_doc.py -n 0 -q
python -m pytest tests/architecture/test_plan_requirements_referenced.py -n 0 -q
```

Expected: all pass.

Commit:

```powershell
git add docs/STATUS.md docs/MANUAL_HARDWARE_VALIDATION.md docs/DUAL_MACHINE_STRATEGY_REDO_MIGRATION_MAP.md tests/test_manual_hardware_validation_doc.py
git commit -m "docs: update dual-machine strategy status"
```

## Task 12: Full Verification And PR Preparation

**Files:**
- No source files should be modified in this task unless verification reveals a defect.

- [ ] **Step 1: Run focused changed-area tests**

Run:

```powershell
python -m pytest tests/test_analog_four_device.py tests/test_devices_strategies_analog_four_snapshot_decoder.py tests/test_devices_strategies_analog_four_mutation_planner.py tests/test_devices_strategies_analog_four_message_renderer.py tests/test_dual_machine_targets.py tests/test_dual_machine_reports.py tests/test_senders_guarded.py tests/test_senders_hardware.py -q
```

Expected: all pass.

- [ ] **Step 2: Run architecture gate**

Run:

```powershell
python -m pytest tests/architecture/ -q
```

Expected: all pass with no allowlist additions.

- [ ] **Step 3: Run fast suite**

Run:

```powershell
python -m pytest -m fast -q
```

Expected: all pass.

- [ ] **Step 4: Run full suite**

Run:

```powershell
python -m pytest -q
```

Expected: all pass.

- [ ] **Step 5: Run lint trio**

Run:

```powershell
python -m ruff check rytm_randomizer/ tests/
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Expected: all clean.

- [ ] **Step 6: Run coverage**

Run:

```powershell
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
```

Expected: project coverage stays at or above 95 percent pure-branch coverage.

- [ ] **Step 7: Prepare PR body**

Create a local PR body file at `docs/superpowers/plans/2026-05-19-dual-machine-strategy-redo-pr-body.md` with:

```markdown
## Summary

- Adds registered `AnalogFourDevice` through the PR #43 `Device` Strategy architecture.
- Adds generic guarded/hardware sender surfaces that consume registered devices.
- Adds human-friendly target aliases: `rytm`, `a4`, `both`.
- Keeps hardware sends manual and gated.

## Test plan

- [ ] `python -m pytest -q`
- [ ] `python -m pytest tests/architecture/ -q`
- [ ] `python -m pytest -m fast -q`
- [ ] `python -m ruff check rytm_randomizer/ tests/`
- [ ] `python -m black --check --target-version=py311 .`
- [ ] `python -m isort --profile black --check-only .`
- [ ] `python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing`

## Plan-requirements conformance

- [ ] Gate 1: Coverage at or above 95 percent; touched-file branch coverage covered by focused tests.
- [ ] Gate 2: V1.34 parity fixtures unchanged.
- [ ] Gate 3: Lint/format/type gates clean.
- [ ] Gate 4: Dead-code check not worsened; no unused public surfaces.
- [ ] Gate 5: Docs updated.
- [ ] Gate 6: Protocol strategy architecture used; no bare `Any` escape hatches added.
- [ ] Gate 7: Passive reports remain operator-readable; no hardware side effects.
- [ ] Gate 8: Tests follow `test_<unit>_<behavior>_when_<condition>` naming.
- [ ] Gate 9: New code lives under subpackages.
- [ ] Gate 10: Target aliases centralized in `dual_machine.targets`.
- [ ] Gate 11: Shared fixtures reused where practical.
- [ ] Gate 12: Module constants annotated `Final`.
- [ ] Gate 13: No env vars introduced.
- [ ] Gate 14: Sender duplication collapsed.
- [ ] Gate 15: Design and plan captured under `docs/superpowers/`.
- [ ] Gate 16: One bundled PR against `modularize-v1.34`, no stacked PRs.
```

- [ ] **Step 8: Push and open one PR**

Run:

```powershell
git status --short --branch
git push -u origin codex/dual-machine-strategy-redo
gh pr create --base modularize-v1.34 --head codex/dual-machine-strategy-redo --title "[codex] Redo dual-machine strategy architecture" --body-file docs/superpowers/plans/2026-05-19-dual-machine-strategy-redo-pr-body.md --draft
```

Expected: one draft PR opens against `modularize-v1.34`. Do not open stacked PRs.

## Execution Notes

- Machines may remain on during implementation, but do not use them until a manual hardware validation step is explicitly selected.
- The first implementation slice should be Task 1 followed by Task 2. That proves the new A4 strategy seam before senders depend on it.
- If a task reveals that the candidate A4 kit type byte or name offset differs from the test fixture, pause and update the snapshot-decoder tests and implementation together with a note in the migration map. Do not silently widen the decoder.
- Keep each task as its own commit so reviewers can read the bundle in logical chunks while still approving one PR.
