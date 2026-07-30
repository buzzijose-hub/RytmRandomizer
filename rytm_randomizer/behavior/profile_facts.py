"""Typed read-only views over the V1.34 ``PROFILES`` registry entries.

:data:`rytm_randomizer.data.PROFILES` is the untyped V1.34 fact table —
each entry is a heterogeneous dict mixing names, anchors, safe bounds and
zone groupings. The behavior planners (:mod:`morph`, :mod:`scope`) only
ever *read* four well-known fields, so this module is the single typed
boundary that narrows those fields once instead of scattering casts
through every planner.

Pure accessors: no I/O, no mutation of the registry (every return value
is a fresh copy), and an unknown ``profile_key`` raises ``KeyError``
loudly — exactly the behavior the planners already documented.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import cast

from ..data import PROFILES

__all__ = [
    "profile_anchor",
    "profile_display_name",
    "profile_safe_bounds",
    "profile_zone_groups",
]


def _entry(profile_key: str) -> Mapping[str, object]:
    """Return one ``PROFILES`` entry as an opaque mapping (``KeyError`` when unknown)."""

    return cast("Mapping[str, object]", PROFILES[profile_key])


def profile_display_name(profile_key: str) -> str:
    """The profile's operator-facing display name (``PROFILES[key]["name"]``)."""

    return cast("str", _entry(profile_key)["name"])


def profile_anchor(profile_key: str) -> dict[str, int]:
    """A fresh copy of the profile's anchor map (param name -> anchor value)."""

    return dict(cast("Mapping[str, int]", _entry(profile_key)["anchor"]))


def profile_safe_bounds(profile_key: str) -> dict[str, tuple[int, int]]:
    """A fresh copy of the profile's safe bounds (param name -> ``(low, high)``)."""

    raw = cast("Mapping[str, Sequence[int]]", _entry(profile_key)["safe"])
    return {name: (bound[0], bound[1]) for name, bound in raw.items()}


def profile_zone_groups(profile_key: str) -> dict[str, tuple[str, ...]]:
    """A fresh copy of the profile's zone groups (group name -> param names)."""

    raw = cast("Mapping[str, Sequence[str]]", _entry(profile_key)["zones"])
    return {name: tuple(params) for name, params in raw.items()}
