"""Passive Rytm snapshot-machine routing helpers."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ...data.profiles import PROFILES
from ...data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    RytmMachineProfile,
    get_rytm_pad_capability,
    is_machine_allowed_on_pad,
)

_PROFILE_KEY_BY_MACHINE_VALUE: Final[Mapping[int, str]] = MappingProxyType(
    {int(profile["machine_value"]): key for key, profile in PROFILES.items()}
)
_MACHINE_PROFILE_BY_VALUE: Final[Mapping[int, RytmMachineProfile]] = MappingProxyType(
    {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}
)


@dataclass(frozen=True)
class RytmSnapshotMachineRoute:
    """Routing result for one snapshot-derived Rytm pad/machine pair."""

    pad: int
    machine_value: int
    machine_key: str | None
    profile_key: str | None
    ready: bool
    reason: str


@dataclass(frozen=True)
class RytmSnapshotMachineRoutingResult:
    """Aggregate snapshot-machine routing result for a requested Rytm pad set."""

    routes_by_pad: Mapping[int, RytmSnapshotMachineRoute]
    profile_keys_by_pad: Mapping[int, str]
    ready_pad_count: int
    blocked_pad_count: int
    ready: bool
    readiness_reason: str


def _route_one(pad: int, machine_value: int) -> RytmSnapshotMachineRoute:
    try:
        capability = get_rytm_pad_capability(pad)
    except KeyError as exc:
        return RytmSnapshotMachineRoute(pad, machine_value, None, None, False, str(exc))

    machine_profile = _MACHINE_PROFILE_BY_VALUE.get(machine_value)
    if machine_profile is None:
        return RytmSnapshotMachineRoute(
            pad=pad,
            machine_value=machine_value,
            machine_key=None,
            profile_key=None,
            ready=False,
            reason=f"Unknown Rytm machine value: {machine_value}",
        )

    if not is_machine_allowed_on_pad(pad, machine_profile.key):
        return RytmSnapshotMachineRoute(
            pad=pad,
            machine_value=machine_value,
            machine_key=machine_profile.key,
            profile_key=None,
            ready=False,
            reason=(
                f"{machine_profile.label} is not legal on Pad {pad} / " f"{capability.track_code}"
            ),
        )

    if machine_profile.support_status != "mutable_v134":
        return RytmSnapshotMachineRoute(
            pad=pad,
            machine_value=machine_value,
            machine_key=machine_profile.key,
            profile_key=None,
            ready=False,
            reason=(
                f"{machine_profile.label} is selectable-only; " "snapshot mutation is not ready yet"
            ),
        )

    profile_key = _PROFILE_KEY_BY_MACHINE_VALUE.get(machine_value)
    if profile_key is None:
        return RytmSnapshotMachineRoute(
            pad=pad,
            machine_value=machine_value,
            machine_key=machine_profile.key,
            profile_key=None,
            ready=False,
            reason=f"{machine_profile.label} has no V1.34 profile key for snapshot mutation",
        )

    return RytmSnapshotMachineRoute(
        pad=pad,
        machine_value=machine_value,
        machine_key=machine_profile.key,
        profile_key=profile_key,
        ready=True,
        reason=f"{machine_profile.label} is snapshot-mutable via profile {profile_key}",
    )


def route_rytm_snapshot_machine_values(
    pad_machine_values: Mapping[int, int],
) -> RytmSnapshotMachineRoutingResult:
    """Route snapshot-derived Rytm machine values to V1.34 profile keys."""

    if not pad_machine_values:
        return RytmSnapshotMachineRoutingResult(
            routes_by_pad=MappingProxyType({}),
            profile_keys_by_pad=MappingProxyType({}),
            ready_pad_count=0,
            blocked_pad_count=0,
            ready=False,
            readiness_reason="no snapshot machine values supplied",
        )

    routes = {
        pad: _route_one(pad, machine_value)
        for pad, machine_value in sorted(pad_machine_values.items())
    }
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


__all__ = [
    "RytmSnapshotMachineRoute",
    "RytmSnapshotMachineRoutingResult",
    "route_rytm_snapshot_machine_values",
]
