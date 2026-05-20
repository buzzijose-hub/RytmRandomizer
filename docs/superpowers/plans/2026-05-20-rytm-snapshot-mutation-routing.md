# Rytm Snapshot Mutation Routing Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first passive/mock-safe Rytm snapshot mutation routing slice, so a snapshot-derived pad-to-machine map can be validated and converted into planner profile keys before any MIDI rendering.

**Architecture:** Keep routing under the Rytm Device Strategy boundary. A new pure strategy helper maps `(pad, machine_value)` facts to V1.34 profile keys using the existing Rytm machine catalog and `PROFILES`; `AnalogRytmMutationPlanner` then consumes validated pad/profile mappings through a new explicit method. The default `plan(snapshot, depth)` behavior remains the existing four-pad anchor mode.

**Tech Stack:** Python 3.11+, frozen dataclasses, existing `rytm_randomizer.data` profile/catalog modules, pytest, ruff, black, isort.

---

## File Structure

- Create `rytm_randomizer/devices/strategies/analog_rytm_snapshot_routing.py`
  - Owns pure snapshot-machine routing for the Rytm.
  - Does not decode SysEx, render MIDI, open ports, or send hardware messages.
- Modify `rytm_randomizer/devices/strategies/__init__.py`
  - Re-export the new router dataclasses/functions for strategy tests.
- Modify `rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py`
  - Extract the current pad/profile planning loop into a private helper.
  - Add `plan_for_machine_values(snapshot, depth, pad_machine_values)` that routes first and refuses unsafe snapshots with `ready=False`.
  - Keep `plan(snapshot, depth)` byte-shape compatible for the existing four-pad route.
- Modify `tests/test_devices_strategies_mutation_planner.py`
  - Add focused planner tests for machine-value routing readiness/refusal.
- Create `tests/test_devices_strategies_analog_rytm_snapshot_routing.py`
  - Cover the pure router behavior and blocked reasons.
- Modify `docs/STATUS.md`
  - Add one concise checkpoint line once behavior exists.

## Task 1: Pure Rytm Snapshot Machine Router

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_rytm_snapshot_routing.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_devices_strategies_analog_rytm_snapshot_routing.py`

- [x] **Step 1: Write the failing router tests**

```python
"""Tests for passive Rytm snapshot-machine routing."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def test_route_machine_values_accepts_mutable_legal_machine() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({1: 0, 2: 3, 3: 32})

    assert result.ready is True
    assert result.ready_pad_count == 3
    assert result.blocked_pad_count == 0
    assert result.profile_keys_by_pad == {1: "2", 2: "10", 3: "5"}
    assert result.routes_by_pad[1].machine_key == "bd_hard"
    assert result.routes_by_pad[2].machine_key == "sd_classic"
    assert result.routes_by_pad[3].machine_key == "sy_raw"


def test_route_machine_values_blocks_selectable_only_machine() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({10: 10})

    assert result.ready is False
    assert result.ready_pad_count == 0
    assert result.blocked_pad_count == 1
    route = result.routes_by_pad[10]
    assert route.ready is False
    assert route.profile_key is None
    assert route.machine_key == "oh_classic"
    assert "selectable-only" in route.reason


def test_route_machine_values_blocks_illegal_pad_machine_pair() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({10: 8})

    assert result.ready is False
    route = result.routes_by_pad[10]
    assert route.machine_key == "xt_classic"
    assert "not legal on Pad 10 / OH" in route.reason


def test_route_machine_values_blocks_unknown_pad_and_machine_value() -> None:
    from rytm_randomizer.devices.strategies import route_rytm_snapshot_machine_values

    result = route_rytm_snapshot_machine_values({0: 0, 1: 127})

    assert result.ready is False
    assert "Unknown Rytm pad: 0" in result.routes_by_pad[0].reason
    assert "Unknown Rytm machine value: 127" in result.routes_by_pad[1].reason
```

- [x] **Step 2: Run the router tests to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_rytm_snapshot_routing.py -n 0
```

Expected: FAIL because `tests/test_devices_strategies_analog_rytm_snapshot_routing.py` imports symbols that do not exist yet.

- [x] **Step 3: Implement the pure router**

Add this shape to `rytm_randomizer/devices/strategies/analog_rytm_snapshot_routing.py`:

```python
"""Passive Rytm snapshot-machine routing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from ...data.profiles import PROFILES
from ...data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    get_rytm_pad_capability,
    is_machine_allowed_on_pad,
)


@dataclass(frozen=True)
class RytmSnapshotMachineRoute:
    pad: int
    machine_value: int
    machine_key: str | None
    profile_key: str | None
    ready: bool
    reason: str


@dataclass(frozen=True)
class RytmSnapshotMachineRoutingResult:
    routes_by_pad: Mapping[int, RytmSnapshotMachineRoute]
    profile_keys_by_pad: Mapping[int, str]
    ready_pad_count: int
    blocked_pad_count: int
    ready: bool
    readiness_reason: str


def _profile_key_by_machine_value() -> dict[int, str]:
    return {int(profile["machine_value"]): key for key, profile in PROFILES.items()}


def _machine_profile_by_value():
    return {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}


def _route_one(pad: int, machine_value: int) -> RytmSnapshotMachineRoute:
    profiles_by_value = _machine_profile_by_value()
    try:
        capability = get_rytm_pad_capability(pad)
    except KeyError as exc:
        return RytmSnapshotMachineRoute(pad, machine_value, None, None, False, str(exc))

    machine_profile = profiles_by_value.get(machine_value)
    if machine_profile is None:
        return RytmSnapshotMachineRoute(
            pad,
            machine_value,
            None,
            None,
            False,
            f"Unknown Rytm machine value: {machine_value}",
        )

    if not is_machine_allowed_on_pad(pad, machine_profile.key):
        return RytmSnapshotMachineRoute(
            pad,
            machine_value,
            machine_profile.key,
            None,
            False,
            (
                f"{machine_profile.label} is not legal on Pad {pad} / "
                f"{capability.track_code}"
            ),
        )

    if machine_profile.support_status != "mutable_v134":
        return RytmSnapshotMachineRoute(
            pad,
            machine_value,
            machine_profile.key,
            None,
            False,
            f"{machine_profile.label} is selectable-only; snapshot mutation is not ready yet",
        )

    profile_key = _profile_key_by_machine_value().get(machine_value)
    if profile_key is None:
        return RytmSnapshotMachineRoute(
            pad,
            machine_value,
            machine_profile.key,
            None,
            False,
            f"{machine_profile.label} has no V1.34 profile key for snapshot mutation",
        )

    return RytmSnapshotMachineRoute(
        pad,
        machine_value,
        machine_profile.key,
        profile_key,
        True,
        f"{machine_profile.label} is snapshot-mutable via profile {profile_key}",
    )


def route_rytm_snapshot_machine_values(
    pad_machine_values: Mapping[int, int],
) -> RytmSnapshotMachineRoutingResult:
    routes = {pad: _route_one(pad, machine_value) for pad, machine_value in pad_machine_values.items()}
    ready_profiles = {
        pad: route.profile_key
        for pad, route in routes.items()
        if route.ready and route.profile_key is not None
    }
    blocked_reasons = tuple(route.reason for route in routes.values() if not route.ready)
    return RytmSnapshotMachineRoutingResult(
        routes_by_pad=MappingProxyType(routes),
        profile_keys_by_pad=MappingProxyType(ready_profiles),
        ready_pad_count=len(ready_profiles),
        blocked_pad_count=len(routes) - len(ready_profiles),
        ready=not blocked_reasons and bool(routes),
        readiness_reason="; ".join(blocked_reasons),
    )
```

- [x] **Step 4: Export the router**

In `rytm_randomizer/devices/strategies/__init__.py`, import and add to `__all__`:

```python
from .analog_rytm_snapshot_routing import (
    RytmSnapshotMachineRoute,
    RytmSnapshotMachineRoutingResult,
    route_rytm_snapshot_machine_values,
)
```

- [x] **Step 5: Run the router tests to verify GREEN**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_rytm_snapshot_routing.py -n 0
```

Expected: PASS.

## Task 2: Planner Entry Point For Snapshot Machine Values

**Files:**
- Modify: `rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py`
- Test: `tests/test_devices_strategies_mutation_planner.py`

- [x] **Step 1: Write failing planner tests**

Append tests that assert:

```python
def test_planner_can_plan_from_snapshot_machine_values_for_mutable_pads() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner, RytmKitSnapshot

    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"")
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
        snapshot,
        depth=1,
        pad_machine_values={1: 0, 2: 3, 3: 32},
    )

    assert plan.ready is True
    assert {event.pad for event in plan.events} == {1, 2, 3}
    assert {event.profile_key for event in plan.events} == {"2", "10", "5"}


def test_planner_refuses_snapshot_machine_values_with_blocked_pad() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmMutationPlanner, RytmKitSnapshot

    snapshot = RytmKitSnapshot(slot=7, kit_name="LIVE", raw=b"", unpacked=b"")
    plan = AnalogRytmMutationPlanner(seed=1).plan_for_machine_values(
        snapshot,
        depth=1,
        pad_machine_values={1: 0, 10: 10},
    )

    assert plan.ready is False
    assert plan.events == ()
    assert "selectable-only" in plan.readiness_reason
```

- [x] **Step 2: Run planner tests to verify RED**

Run:

```powershell
python -m pytest tests/test_devices_strategies_mutation_planner.py::test_planner_can_plan_from_snapshot_machine_values_for_mutable_pads tests/test_devices_strategies_mutation_planner.py::test_planner_refuses_snapshot_machine_values_with_blocked_pad -n 0
```

Expected: FAIL because `plan_for_machine_values` does not exist.

- [x] **Step 3: Refactor planner into a private helper**

Move the current `for pad in sorted(PAD_PROFILE_KEY)` loop into:

```python
def _plan_for_profile_keys(
    self,
    snapshot: RytmKitSnapshot,
    depth: int,
    pad_profile_keys: Mapping[int, str],
) -> RytmMutationPlan:
```

Keep `plan(snapshot, depth)` calling `_plan_for_profile_keys(snapshot, depth, PAD_PROFILE_KEY)`.

- [x] **Step 4: Add `plan_for_machine_values`**

Use `route_rytm_snapshot_machine_values(pad_machine_values)`. If routing is not ready, return a `RytmMutationPlan` with `events=()`, `ready=False`, and the routing `readiness_reason`. If routing is ready, call `_plan_for_profile_keys` with `routing.profile_keys_by_pad`.

- [x] **Step 5: Verify planner tests GREEN**

Run the two targeted tests again. Expected: PASS.

## Task 3: Documentation And Gates

**Files:**
- Modify: `docs/STATUS.md`

- [x] **Step 1: Add one status checkpoint**

Add a top entry:

```markdown
- 2026-05-20: Rytm snapshot mutation routing PR2 started after PR #49. Added passive machine-value routing from snapshot-derived `(pad, machine_value)` facts to V1.34 profile keys, with selectable-only/illegal machines refused before any MIDI rendering. This remains mock/passive and sends no hardware messages.
```

- [ ] **Step 2: Run focused and full verification**

Run:

```powershell
python -m pytest tests/test_devices_strategies_analog_rytm_snapshot_routing.py tests/test_devices_strategies_mutation_planner.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only rytm_randomizer tests scripts
python scripts/code_review_gate.py --mode cli
```

Expected: all pass. If root formatting sees checkout line-ending noise, do not stage unrelated parity or test fixture files; use explicit path staging.

- [ ] **Step 3: Commit the verified slice**

Run:

```powershell
git add -- rytm_randomizer/devices/strategies/analog_rytm_snapshot_routing.py `
  rytm_randomizer/devices/strategies/__init__.py `
  rytm_randomizer/devices/strategies/analog_rytm_mutation_planner.py `
  tests/test_devices_strategies_analog_rytm_snapshot_routing.py `
  tests/test_devices_strategies_mutation_planner.py `
  docs/STATUS.md `
  docs/superpowers/plans/2026-05-20-rytm-snapshot-mutation-routing.md
git commit -m "feat: route Rytm snapshot machine values"
```

Expected: commit includes only intended files.

## Self-Review

- Spec coverage: covers the approved follow-up sequence item "Rytm snapshot mutation routing for all 12 pads" without adding hardware sends, capture, GUI, Analog Four, or audio analysis.
- Placeholder scan: no TODO/TBD/fill-in placeholders remain.
- Type consistency: public symbols use `RytmSnapshotMachineRoute`, `RytmSnapshotMachineRoutingResult`, and `route_rytm_snapshot_machine_values`; planner method is `plan_for_machine_values(snapshot, depth, pad_machine_values)`.
