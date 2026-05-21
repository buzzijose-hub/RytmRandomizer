# Rytm Style Snapshot Routing PR58 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the first passive Rytm style-to-snapshot routing preview so a captured kit snapshot can be evaluated against a selected techno style target before any mutation rendering or MIDI output.

**Architecture:** Keep this slice under the existing Rytm Device Strategy and passive report boundaries. A new pure strategy helper consumes `RytmKitSnapshot` plus a `STYLE_TARGET_VECTORS` key, reuses snapshot machine routing and the 12-pad machine catalog, then emits deterministic per-pad planning facts: readiness, favored mutation zones, and legal machine candidates. A new report/CLI command formats that preview without opening ports, sending MIDI, invoking guarded senders, or touching hardware.

**Tech Stack:** Python 3.11, frozen dataclasses, `MappingProxyType`, existing `devices/strategies` helpers, existing passive CLI registry, pytest fast tests, architecture gate, ruff, black, isort.

---

## Scope Rules

- Start only after PR #56 and PR57 have landed on `origin/modularize-v1.34`.
- Create a fresh clean-base branch from `origin/modularize-v1.34`; do not push from this local draft branch.
- Do not open a stacked PR.
- Do not import `mido`.
- Do not touch V1.34 parity fixtures.
- Do not add a new top-level package module.
- Do not call `guarded_send`, real MIDI providers, or hardware adapters.
- Do not choose mutation values yet; PR58 only plans style-aware readiness and emphasis.
- Keep Rytm-only scope. Analog Four style routing is a later PR through its own Device Strategy path.

## File Structure

- Create `rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py`
  - Owns pure style-aware Rytm snapshot routing dataclasses and helpers.
  - Depends on `data.rytm_machine_catalog`, `data.style_targets`, and existing `analog_rytm_snapshot_routing`.
- Modify `rytm_randomizer/devices/strategies/__init__.py`
  - Re-export the new Rytm strategy dataclasses and planner function.
- Create `rytm_randomizer/reports/rytm_style_snapshot_routing.py`
  - Formats a passive operator report and registers `rytm-style-snapshot-routing-report`.
- Modify `rytm_randomizer/cli.py`
  - Adds lazy command registration for the new passive report command.
- Modify `rytm_randomizer/help_text.py`
  - Adds command-specific help and updates top-level usage/help.
- Create `tests/test_rytm_style_snapshot_routing.py`
  - Focused fast tests for pure planner behavior, report formatting, parser behavior, and handler behavior.
- Modify `tests/test_cli.py`
  - Adds subprocess CLI coverage for the new command and safe failures.
- Modify `tests/fixtures/cli_help_expected.txt`
  - Updates top-level help fixture.
- Modify `README.md`, `docs/STATUS.md`, and `docs/ARCHITECTURE_DIAGRAMS.md`
  - Documents the passive style-aware snapshot routing layer.

---

### Task 1: Add Failing Pure Planner Tests

**Files:**
- Create: `tests/test_rytm_style_snapshot_routing.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_rytm_style_snapshot_routing.py` with:

```python
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _style_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
                2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
                3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
                10: RytmSnapshotMachineFact(10, 10, 10, True, "promoted"),
            }
        ),
        promoted=True,
    )
    return RytmKitSnapshot(
        slot=4,
        kit_name="STYLEKIT",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _candidate_only_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                6: RytmSnapshotMachineFact(
                    6,
                    8,
                    None,
                    False,
                    "candidate-only tom-pad machine fact",
                ),
            }
        ),
        promoted=False,
    )
    return RytmKitSnapshot(
        slot=5,
        kit_name="CANDIDATE",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def test_style_snapshot_routing_requires_known_style_key():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_rytm_style_snapshot_routes(_style_snapshot(), "ghost_style")


def test_style_snapshot_routing_reports_ready_and_blocked_pads():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")

    assert plan.kit_name == "STYLEKIT"
    assert plan.slot == 4
    assert plan.style_key == "birmingham_pressure"
    assert plan.ready_pad_count == 3
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is True
    assert plan.pads_by_pad[1].route_ready is True
    assert plan.pads_by_pad[1].profile_key == "2"
    assert plan.pads_by_pad[10].track_code == "OH"
    assert plan.pads_by_pad[10].current_machine_key == "oh_classic"
    assert plan.pads_by_pad[10].route_ready is False
    assert "selectable-only" in plan.pads_by_pad[10].readiness_reason


def test_style_snapshot_routing_uses_style_vector_for_favored_zones():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    birmingham = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")
    deep = plan_rytm_style_snapshot_routes(_style_snapshot(), "deep_dark_hypnosis")

    assert birmingham.favored_zones[:3] == ("grit", "body", "amp")
    assert "filter" in deep.favored_zones
    assert "lfo" in deep.favored_zones


def test_style_snapshot_routing_ranks_legal_machine_candidates_per_pad():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "mills_hypnotic")

    assert plan.pads_by_pad[1].compatible_machine_candidates[0].machine_key == "bd_fm"
    pad_10_candidates = {
        candidate.machine_key for candidate in plan.pads_by_pad[10].compatible_machine_candidates
    }
    assert "oh_classic" in pad_10_candidates
    assert "oh_metallic" in pad_10_candidates
    assert "xt_classic" not in pad_10_candidates
    assert plan.pads_by_pad[10].mutable_machine_candidates == ()


def test_style_snapshot_routing_blocks_candidate_only_machine_facts():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_candidate_only_snapshot(), "warehouse_peak")

    assert plan.ready_pad_count == 0
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is False
    assert plan.pads_by_pad[6].track_code == "LT"
    assert plan.pads_by_pad[6].route_ready is False
    assert "candidate-only" in plan.pads_by_pad[6].readiness_reason
```

- [ ] **Step 2: Run the failing tests**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py -n 0
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing'`.

---

### Task 2: Implement Pure Style Snapshot Routing

**Files:**
- Create: `rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py`
- Modify: `rytm_randomizer/devices/strategies/__init__.py`
- Test: `tests/test_rytm_style_snapshot_routing.py`

- [ ] **Step 1: Add the strategy helper**

Create `rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py`:

```python
"""Passive style-aware Analog Rytm snapshot routing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.rytm_machine_catalog import (
    MUTABLE_V134,
    RYTM_MACHINE_PROFILES_BY_KEY,
    RytmMachineProfile,
    allowed_machine_profiles_for_pad,
    get_rytm_pad_capability,
)
from ...data.style_targets import STYLE_TARGET_VECTORS, StyleTargetVector
from .analog_rytm_snapshot_decoder import RytmKitSnapshot
from .analog_rytm_snapshot_routing import (
    RytmSnapshotMachineRoute,
    route_rytm_snapshot_machine_values,
)

_ZONE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "body": (
            "low_end_weight",
            "drive_pressure",
            "warehouse_intensity",
            "decay_tail",
        ),
        "amp": (
            "transient_density",
            "attack_sharpness",
            "percussive_density",
        ),
        "filter": (
            "darkness",
            "space_depth",
            "tonal_center_weight",
        ),
        "grit": (
            "noise_grit",
            "industrial_edge",
            "metallicity",
            "drive_pressure",
        ),
        "lfo": (
            "motion_amount",
            "repetition_hypnosis",
            "space_depth",
        ),
        "morph": (
            "tonal_center_weight",
            "motion_amount",
            "metallicity",
        ),
    }
)

_ROLE_AXIS_WEIGHTS: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "kick": ("low_end_weight", "drive_pressure", "warehouse_intensity"),
        "snare": ("transient_density", "attack_sharpness", "percussive_density"),
        "rim": ("transient_density", "attack_sharpness", "minimal_restraint"),
        "clap": ("transient_density", "space_depth", "percussive_density"),
        "tom": ("low_end_weight", "decay_tail", "percussive_density"),
        "hihat": ("transient_density", "metallicity", "percussive_density"),
        "cymbal": ("metallicity", "space_depth", "decay_tail"),
        "cowbell": ("metallicity", "attack_sharpness", "percussive_density"),
        "synth": ("tonal_center_weight", "motion_amount", "repetition_hypnosis"),
        "noise": ("noise_grit", "industrial_edge", "darkness"),
        "fm": ("metallicity", "attack_sharpness", "motion_amount"),
        "utility": ("noise_grit", "industrial_edge", "minimal_restraint"),
    }
)

_MAX_CANDIDATES: Final[int] = 5


@dataclass(frozen=True)
class RytmStyleMachineCandidate:
    """One legal machine candidate ranked for a style target."""

    machine_key: str
    label: str
    machine_value: int
    support_status: str
    score: int


@dataclass(frozen=True)
class RytmStyleSnapshotPadPlan:
    """One pad's style-aware snapshot routing preview."""

    pad: int
    track_code: str
    label: str
    current_machine_value: int | None
    current_machine_key: str | None
    profile_key: str | None
    route_ready: bool
    readiness_reason: str
    favored_zones: tuple[str, ...]
    compatible_machine_candidates: tuple[RytmStyleMachineCandidate, ...]
    mutable_machine_candidates: tuple[RytmStyleMachineCandidate, ...]


@dataclass(frozen=True)
class RytmStyleSnapshotRoutingPlan:
    """Passive style-aware routing plan for one Rytm kit snapshot."""

    kit_name: str
    slot: int
    style_key: str
    favored_zones: tuple[str, ...]
    ready_pad_count: int
    blocked_pad_count: int
    partial_snapshot_mutation_ready: bool
    pads_by_pad: Mapping[int, RytmStyleSnapshotPadPlan]


def _axis_sum(target: StyleTargetVector, axes: tuple[str, ...]) -> int:
    values = target.as_mapping()
    return sum(values[axis] for axis in axes)


def _favored_zones(target: StyleTargetVector) -> tuple[str, ...]:
    scored = sorted(
        (
            (zone, _axis_sum(target, axes))
            for zone, axes in _ZONE_AXIS_WEIGHTS.items()
        ),
        key=lambda item: (-item[1], item[0]),
    )
    return tuple(zone for zone, score in scored if score >= 150)[:4]


def _candidate_score(profile: RytmMachineProfile, target: StyleTargetVector) -> int:
    score = 0
    for tag in profile.role_tags:
        axes = _ROLE_AXIS_WEIGHTS.get(tag)
        if axes is not None:
            score += _axis_sum(target, axes)
    if profile.support_status == MUTABLE_V134:
        score += 25
    return score


def _candidate(profile: RytmMachineProfile, target: StyleTargetVector) -> RytmStyleMachineCandidate:
    return RytmStyleMachineCandidate(
        machine_key=profile.key,
        label=profile.label,
        machine_value=profile.machine_value,
        support_status=profile.support_status,
        score=_candidate_score(profile, target),
    )


def _ranked_candidates(
    pad: int,
    target: StyleTargetVector,
) -> tuple[RytmStyleMachineCandidate, ...]:
    candidates = [_candidate(profile, target) for profile in allowed_machine_profiles_for_pad(pad)]
    return tuple(
        sorted(
            candidates,
            key=lambda candidate: (
                -candidate.score,
                candidate.support_status != MUTABLE_V134,
                candidate.machine_key,
            ),
        )[:_MAX_CANDIDATES]
    )


def _machine_key_for_route(route: RytmSnapshotMachineRoute) -> str | None:
    if route.machine_key is not None:
        return route.machine_key
    for profile in RYTM_MACHINE_PROFILES_BY_KEY.values():
        if profile.machine_value == route.machine_value:
            return profile.key
    return None


def _pad_plan(
    *,
    pad: int,
    route: RytmSnapshotMachineRoute,
    target: StyleTargetVector,
    favored_zones: tuple[str, ...],
) -> RytmStyleSnapshotPadPlan:
    capability = get_rytm_pad_capability(pad)
    candidates = _ranked_candidates(pad, target)
    mutable_candidates = tuple(
        candidate for candidate in candidates if candidate.support_status == MUTABLE_V134
    )
    return RytmStyleSnapshotPadPlan(
        pad=pad,
        track_code=capability.track_code,
        label=capability.label,
        current_machine_value=route.machine_value,
        current_machine_key=_machine_key_for_route(route),
        profile_key=route.profile_key,
        route_ready=route.ready,
        readiness_reason=route.reason,
        favored_zones=favored_zones,
        compatible_machine_candidates=candidates,
        mutable_machine_candidates=mutable_candidates,
    )


def plan_rytm_style_snapshot_routes(
    snapshot: RytmKitSnapshot,
    style_key: str,
) -> RytmStyleSnapshotRoutingPlan:
    """Return a passive style-aware routing preview for one Rytm snapshot."""

    if not isinstance(snapshot, RytmKitSnapshot):
        raise ValueError(
            "plan_rytm_style_snapshot_routes: snapshot must be a "
            f"RytmKitSnapshot, got {type(snapshot).__name__}"
        )
    normalized_key = style_key.strip().lower()
    target = STYLE_TARGET_VECTORS.get(normalized_key)
    if target is None:
        raise ValueError(f"Unknown style target key: {style_key}")

    favored_zones = _favored_zones(target)
    pads: dict[int, RytmStyleSnapshotPadPlan] = {}
    for pad, fact in sorted(snapshot.machine_facts.facts_by_pad.items()):
        if fact.decoded_machine_value is None:
            route = RytmSnapshotMachineRoute(
                pad=pad,
                machine_value=fact.raw_machine_value,
                machine_key=None,
                profile_key=None,
                ready=False,
                reason=fact.reason,
            )
        else:
            route = route_rytm_snapshot_machine_values(
                {pad: fact.decoded_machine_value}
            ).routes_by_pad[pad]
        pads[pad] = _pad_plan(
            pad=pad,
            route=route,
            target=target,
            favored_zones=favored_zones,
        )

    ready_count = sum(1 for pad_plan in pads.values() if pad_plan.route_ready)
    return RytmStyleSnapshotRoutingPlan(
        kit_name=snapshot.kit_name,
        slot=snapshot.slot,
        style_key=normalized_key,
        favored_zones=favored_zones,
        ready_pad_count=ready_count,
        blocked_pad_count=len(pads) - ready_count,
        partial_snapshot_mutation_ready=ready_count > 0,
        pads_by_pad=MappingProxyType(pads),
    )


__all__ = [
    "RytmStyleMachineCandidate",
    "RytmStyleSnapshotPadPlan",
    "RytmStyleSnapshotRoutingPlan",
    "plan_rytm_style_snapshot_routes",
]
```

- [ ] **Step 2: Re-export from strategies package**

In `rytm_randomizer/devices/strategies/__init__.py`, import and export:

```python
from .analog_rytm_style_snapshot_routing import (
    RytmStyleMachineCandidate,
    RytmStyleSnapshotPadPlan,
    RytmStyleSnapshotRoutingPlan,
    plan_rytm_style_snapshot_routes,
)
```

Add these names to `__all__`:

```python
    "RytmStyleMachineCandidate",
    "RytmStyleSnapshotPadPlan",
    "RytmStyleSnapshotRoutingPlan",
    "plan_rytm_style_snapshot_routes",
```

- [ ] **Step 3: Run planner tests**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py -n 0
```

Expected: planner tests pass or fail only because report/CLI tests have not been added yet.

- [ ] **Step 4: Commit**

```bash
git add rytm_randomizer/devices/strategies/analog_rytm_style_snapshot_routing.py rytm_randomizer/devices/strategies/__init__.py tests/test_rytm_style_snapshot_routing.py
git commit -m "feat: add passive Rytm style snapshot routing"
```

---

### Task 3: Add Passive Report Tests And Formatter

**Files:**
- Modify: `tests/test_rytm_style_snapshot_routing.py`
- Create: `rytm_randomizer/reports/rytm_style_snapshot_routing.py`

- [ ] **Step 1: Add failing report tests**

Append these tests to `tests/test_rytm_style_snapshot_routing.py`:

```python
def test_style_snapshot_routing_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    lines = format_rytm_style_snapshot_routing_report(
        _style_snapshot(),
        style_key="birmingham_pressure",
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style snapshot routing"
    assert "Kit: STYLEKIT" in lines
    assert "Slot: 4" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "- Ready pads: 3" in lines
    assert "- Blocked pads: 1" in lines
    assert "Favored zones: grit, body, amp" in text
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "  Current machine: oh_classic / CC15 10" in text
    assert "  Route ready: False" in text
    assert "  Mutable candidates: none" in text
    assert "  Compatible candidates:" in text
    assert "oh_metallic" in text
    assert "xt_classic" not in text
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_style_snapshot_routing" in lines
    assert "In-memory only: True" in lines


def test_style_snapshot_routing_report_rejects_unknown_style_safely():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        format_rytm_style_snapshot_routing_report(_style_snapshot(), style_key="ghost_style")
```

- [ ] **Step 2: Run report tests and verify failure**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py -n 0 -k report
```

Expected: fails with `ModuleNotFoundError: No module named 'rytm_randomizer.reports.rytm_style_snapshot_routing'`.

- [ ] **Step 3: Add report module**

Create `rytm_randomizer/reports/rytm_style_snapshot_routing.py`:

```python
"""Passive Rytm style snapshot routing report."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..devices.strategies import RytmKitSnapshot, RytmStyleSnapshotRoutingPlan
from ..devices.strategies.analog_rytm_style_snapshot_routing import (
    RytmStyleMachineCandidate,
    plan_rytm_style_snapshot_routes,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines
from .rytm_snapshot_intelligence import (
    decode_supported_rytm_snapshots_from_path,
    select_supported_rytm_snapshot,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm style snapshot routing"
SOURCE_MODULE: Final[str] = "reports.rytm_style_snapshot_routing"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "style routing metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "rytm-style-snapshot-routing-report usage: "
    "<syx-path> <style-key> [--slot N]"
)
_DEFAULT_SLOT: Final[int] = 0


def _join(values: Sequence[str]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _candidate_text(candidate: RytmStyleMachineCandidate) -> str:
    return (
        f"{candidate.machine_key} / CC15 {candidate.machine_value} "
        f"({candidate.support_status}, score {candidate.score})"
    )


def _candidate_lines(
    title: str,
    candidates: Sequence[RytmStyleMachineCandidate],
) -> list[str]:
    lines = [f"  {title}:"]
    if not candidates:
        lines.append("    - none")
        return lines
    lines.extend(f"    - {_candidate_text(candidate)}" for candidate in candidates)
    return lines


def _body_lines(plan: RytmStyleSnapshotRoutingPlan) -> list[str]:
    lines = [
        f"Kit: {plan.kit_name}",
        f"Slot: {plan.slot}",
        f"Style target: {plan.style_key}",
        "Summary:",
        f"- Ready pads: {plan.ready_pad_count}",
        f"- Blocked pads: {plan.blocked_pad_count}",
        f"- Partial snapshot mutation ready: {plan.partial_snapshot_mutation_ready}",
        f"Favored zones: {_join(plan.favored_zones)}",
        "Pads:",
    ]
    for pad in sorted(plan.pads_by_pad):
        pad_plan = plan.pads_by_pad[pad]
        machine_text = (
            "unknown"
            if pad_plan.current_machine_key is None
            else f"{pad_plan.current_machine_key} / CC15 {pad_plan.current_machine_value}"
        )
        lines.extend(
            [
                f"Pad {pad_plan.pad} / {pad_plan.track_code} / {pad_plan.label}:",
                f"  Current machine: {machine_text}",
                f"  Profile key: {pad_plan.profile_key or 'none'}",
                f"  Route ready: {pad_plan.route_ready}",
                f"  Reason: {pad_plan.readiness_reason}",
                f"  Favored zones: {_join(pad_plan.favored_zones)}",
            ]
        )
        lines.extend(_candidate_lines("Mutable candidates", pad_plan.mutable_machine_candidates))
        lines.extend(
            _candidate_lines(
                "Compatible candidates",
                pad_plan.compatible_machine_candidates,
            )
        )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return lines


def format_rytm_style_snapshot_routing_report(
    snapshot_or_plan: RytmKitSnapshot | RytmStyleSnapshotRoutingPlan,
    *,
    style_key: str,
) -> list[str]:
    """Return deterministic operator-facing lines for style snapshot routing."""

    plan = (
        snapshot_or_plan
        if isinstance(snapshot_or_plan, RytmStyleSnapshotRoutingPlan)
        else plan_rytm_style_snapshot_routes(snapshot_or_plan, style_key)
    )
    return passive_report_lines(_HEADER, _body_lines(plan))


def _parse_nonnegative_int(value: str, *, option: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc
    if parsed < 0:
        raise ValueError(f"{option} must be >= 0")
    return parsed


def _parse_cli_args(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) < 2:
        raise ValueError(_USAGE)
    sysex_path = Path(argv[0])
    style_key = argv[1]
    slot = _DEFAULT_SLOT
    remaining = list(argv[2:])
    while remaining:
        option = remaining.pop(0)
        if len(remaining) < 1:
            raise ValueError(_USAGE)
        value = remaining.pop(0)
        if option == "--slot":
            slot = _parse_nonnegative_int(value, option=option)
        else:
            raise ValueError(_USAGE)
    return {"sysex_path": sysex_path, "style_key": style_key, "slot": slot}


def _handle_cli_report(*, sysex_path: Path, style_key: str, slot: int) -> int:
    try:
        snapshots = decode_supported_rytm_snapshots_from_path(sysex_path)
        snapshot = select_supported_rytm_snapshot(sysex_path, slot, snapshots)
        lines = format_rytm_style_snapshot_routing_report(snapshot, style_key=style_key)
    except (OSError, ValueError, NotImplementedError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_cli_error(exc: Exception) -> str:
    return f"Error: {exc}"


RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-style-snapshot-routing-report",
    summary="Print passive Rytm style snapshot routing for a SysEx file.",
    args_parser=_parse_cli_args,
    handler=_handle_cli_report,
    error_formatter=_format_cli_error,
)

register(RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND)

__all__ = [
    "REPORT_TITLE",
    "RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "format_rytm_style_snapshot_routing_report",
]
```

- [ ] **Step 4: Run report tests**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py -n 0
```

Expected: all current style snapshot routing tests pass.

- [ ] **Step 5: Commit**

```bash
git add rytm_randomizer/reports/rytm_style_snapshot_routing.py tests/test_rytm_style_snapshot_routing.py
git commit -m "feat: add passive Rytm style routing report"
```

---

### Task 4: Wire Passive CLI And Help

**Files:**
- Modify: `rytm_randomizer/cli.py`
- Modify: `rytm_randomizer/help_text.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/fixtures/cli_help_expected.txt`

- [ ] **Step 1: Add failing CLI tests**

In `tests/test_cli.py`, add:

```python
def test_rytm_style_snapshot_routing_report_command_exits_zero_and_is_passive(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    syx_path = tmp_path / "kit.syx"
    syx_path.write_bytes(bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"STYLE") + bytes([0xF7]))

    result = _run_cli(
        "rytm-style-snapshot-routing-report",
        str(syx_path),
        "birmingham_pressure",
    )

    assert result.returncode == 0
    assert "RytmRandomizer passive Rytm style snapshot routing" in result.stdout
    assert "Style target: birmingham_pressure" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert "- no port opening" in result.stdout
    assert result.stderr == ""


def test_rytm_style_snapshot_routing_report_unknown_style_fails_safely(tmp_path):
    from conftest import rytm_real_layout_kit_payload

    syx_path = tmp_path / "kit.syx"
    syx_path.write_bytes(bytes([0xF0]) + rytm_real_layout_kit_payload(name=b"STYLE") + bytes([0xF7]))

    result = _run_cli("rytm-style-snapshot-routing-report", str(syx_path), "ghost_style")

    assert result.returncode == 2
    assert result.stdout == ""
    assert "Unknown style target key: ghost_style" in result.stderr
    assert "Traceback" not in result.stderr
```

- [ ] **Step 2: Run failing CLI tests**

Run:

```bash
python -m pytest tests/test_cli.py -n 0 -k "rytm_style_snapshot_routing"
```

Expected: fails because the command is not registered.

- [ ] **Step 3: Wire CLI lazy command**

In `rytm_randomizer/cli.py`, add the lazy command tuple:

```python
(
    "rytm-style-snapshot-routing-report",
    "rytm_randomizer.reports.rytm_style_snapshot_routing",
    "RYTM_STYLE_SNAPSHOT_ROUTING_CLI_COMMAND",
),
```

- [ ] **Step 4: Update help text**

In `rytm_randomizer/help_text.py`, update usage:

```text
rytm-snapshot-mutation-preview-report <syx-path> [--slot N] [--depth N] [--events] [--limit N]
rytm-style-snapshot-routing-report <syx-path> <style-key> [--slot N]
```

Add command help:

```python
def _rytm_style_snapshot_routing_report_help() -> str:
    return """RytmRandomizer passive CLI: rytm-style-snapshot-routing-report

Usage:
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> [--slot N]

Description:
  Reads a local Analog Rytm SysEx kit dump, selects a supported kit snapshot,
  and prints passive style-aware routing readiness for the selected style target.
  The report shows favored zones, route-ready pads, blocked pads, and legal
  machine candidates without rendering mutation values.

Safety:
  passive/read-only
  style routing metadata only
  no MIDI sending
  no port opening
  no command execution
  no hardware mutation
  no hardware required
"""
```

Map it in the help dictionary:

```python
"rytm-style-snapshot-routing-report": _rytm_style_snapshot_routing_report_help,
```

- [ ] **Step 5: Update help fixture**

In `tests/fixtures/cli_help_expected.txt`, add:

```text
  python -m rytm_randomizer.cli rytm-style-snapshot-routing-report <syx-path> <style-key> [--slot N]
```

and:

```text
  rytm-style-snapshot-routing-report
                     Print passive Rytm style snapshot routing for a SysEx file.
```

- [ ] **Step 6: Run CLI tests**

Run:

```bash
python -m pytest tests/test_cli.py tests/test_rytm_style_snapshot_routing.py -n 0 -k "rytm_style_snapshot_routing or style_snapshot_routing or cli_help"
```

Expected: the focused CLI/help tests pass.

- [ ] **Step 7: Commit**

```bash
git add rytm_randomizer/cli.py rytm_randomizer/help_text.py tests/test_cli.py tests/fixtures/cli_help_expected.txt tests/test_rytm_style_snapshot_routing.py
git commit -m "feat: expose passive Rytm style routing CLI"
```

---

### Task 5: Docs, Verification, And PR Body

**Files:**
- Modify: `README.md`
- Modify: `docs/STATUS.md`
- Modify: `docs/ARCHITECTURE_DIAGRAMS.md`
- Create: `docs/superpowers/plans/2026-05-21-rytm-style-snapshot-routing-pr58-pr-body.md`

- [ ] **Step 1: Update README**

Add this example near the snapshot and style command examples:

```text
python -m rytm_randomizer.cli rytm-style-snapshot-routing-report path/to/kit.syx birmingham_pressure   # passive style-aware Rytm snapshot routing
```

Add this paragraph near the style target description:

```text
The Rytm style snapshot routing report is the first bridge from style intent to captured-kit planning. It reads a local Rytm kit dump, applies one style target vector, and reports favored mutation zones, route-ready pads, blocked pads, and legal machine candidates. It remains metadata-only: no mutation values are rendered, no MIDI port is opened, and no hardware message is sent.
```

- [ ] **Step 2: Update STATUS**

Add the top entry:

```text
- 2026-05-21: Rytm style snapshot routing PR58 prepared after the passive style target vector layer. The passive preview now bridges a captured Rytm kit snapshot and a selected style target into per-pad readiness, favored zones, and legal machine candidates without rendering mutation values or sending MIDI.
```

- [ ] **Step 3: Update architecture diagrams**

In `docs/ARCHITECTURE_DIAGRAMS.md`, add `analog_rytm_style_snapshot_routing.py` to the `devices/strategies` source summaries and add `rytm_style_snapshot_routing.py` to report/CLI diagrams.

- [ ] **Step 4: Run focused verification**

Run:

```bash
python -m pytest tests/test_rytm_style_snapshot_routing.py tests/test_cli.py -n 0 -k "style_snapshot_routing or rytm_style_snapshot_routing or cli_help"
python -m pytest tests/architecture/ -q
python -m pytest -m fast
```

Expected: all pass.

- [ ] **Step 5: Run full closeout verification**

Run:

```bash
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python scripts/code_review_gate.py --mode cli
```

Expected: all pass. `code_review_gate.py` must show lint, architecture, and V1.34 parity gates green.

- [ ] **Step 6: Commit docs**

```bash
git add README.md docs/STATUS.md docs/ARCHITECTURE_DIAGRAMS.md
git commit -m "docs: describe Rytm style snapshot routing"
```

- [ ] **Step 7: Write PR body**

Create `docs/superpowers/plans/2026-05-21-rytm-style-snapshot-routing-pr58-pr-body.md` using the repository PR template. Include:

```markdown
## What changed

- Added passive Rytm style snapshot routing under the Device Strategy boundary.
- Added an operator-facing report and CLI command for style target to snapshot readiness.
- Documented the new passive bridge from style targets to future mutation planning.

## Test plan

- [ ] `python -m pytest tests/test_rytm_style_snapshot_routing.py tests/test_cli.py -n 0 -k "style_snapshot_routing or rytm_style_snapshot_routing or cli_help"`
- [ ] `python -m pytest tests/architecture/ -q`
- [ ] `python -m pytest -m fast`
- [ ] `python -m pytest`
- [ ] `python -m ruff check .`
- [ ] `python -m black --check --target-version=py311 .`
- [ ] `python -m isort --profile black --check-only .`
- [ ] `python scripts/code_review_gate.py --mode cli`

## Plan

- Plan doc: `docs/superpowers/plans/2026-05-21-rytm-style-snapshot-routing-pr58.md`
```

Then paste and complete the required 18-gate checklist and strict-rules block from `.github/PULL_REQUEST_TEMPLATE.md`.

- [ ] **Step 8: Commit PR body**

```bash
git add docs/superpowers/plans/2026-05-21-rytm-style-snapshot-routing-pr58-pr-body.md
git commit -m "docs: prepare Rytm style routing PR body"
```

## Self-Review

- Spec coverage: implements PR58 from the style routing design: passive Rytm snapshot preview using style target vectors, 12-pad compatibility, blocked reasons, and no MIDI/hardware behavior.
- Placeholder scan: no TBD/TODO/fill-in steps remain; all behavior steps include code or exact commands.
- Type consistency: `RytmStyleSnapshotRoutingPlan`, `RytmStyleSnapshotPadPlan`, and `RytmStyleMachineCandidate` are named consistently across strategy, report, tests, and docs.
- Scope check: Analog Four, slider blend semantics, analyzer vectors, runtime mutation rendering, and armed hardware sending remain later PRs.
