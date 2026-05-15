"""Profile metadata captured for scaffold-level tests.

This module intentionally contains only stable V1.34 identifiers and MIDI CC
metadata that non-hardware tests can validate.

Every value here is now *derived* from the shared data layer
(:mod:`rytm_randomizer.data`) instead of being hand-re-typed:

* ``GROUP_LAYOUT`` is the canonical four-pad layout, re-exported verbatim.
* ``GROUP_PROFILE_METADATA`` is built from the canonical ``PROFILES`` registry
  (name + machine value) plus the canonical ``GROUP_LAYOUT`` (pad placement).
* ``PAD_3_SY_RAW_CC_MAP`` is sliced from the canonical ``SY_RAW_PARAMS`` CC map.

Because there is exactly one copy of every underlying value, this module can
never drift from the monolith. ``tests/test_data_layer.py`` guards this.
"""

from __future__ import annotations

from .constants import PAD1_DEFAULT_HOME
from .data import GROUP_LAYOUT, PROFILES, SY_RAW_PARAMS

# Group-profile keys that are in scope for the modular scaffold. These are the
# subset of the canonical PROFILES registry that the four-pad layout uses.
_GROUP_PROFILE_KEYS = ("2", "3", "4", "5")

# SY Raw SRC parameter names exposed in the Pad 3 scaffold CC map.
_PAD_3_SY_RAW_CC_NAMES = ("SRC Noise Level", "SRC Balance")

PAD_1_DEFAULT_PROFILE = {
    "pad": 1,
    "name": PAD1_DEFAULT_HOME,
    "role": "default/home",
}

# Sliced from the canonical SY_RAW_PARAMS CC map so the CC numbers can never
# drift from the monolith's SY Raw param definitions.
PAD_3_SY_RAW_CC_MAP = {name: SY_RAW_PARAMS[name] for name in _PAD_3_SY_RAW_CC_NAMES}

PAD_PROFILES = {
    1: PAD_1_DEFAULT_PROFILE,
    3: {
        "pad": 3,
        "name": "SY Raw",
        "cc_map": PAD_3_SY_RAW_CC_MAP,
    },
}


def _build_group_profile_metadata() -> dict[str, dict[str, object]]:
    """Derive GROUP_PROFILE_METADATA from the shared PROFILES + GROUP_LAYOUT.

    ``name`` and ``machine_value`` come straight from the canonical profile
    registry. ``group_pad`` is the pad in ``GROUP_LAYOUT`` whose ``profile``
    points at this key (the inverse of the layout mapping).
    """

    profile_to_pad = {layout["profile"]: pad for pad, layout in GROUP_LAYOUT.items()}
    metadata: dict[str, dict[str, object]] = {}
    for key in _GROUP_PROFILE_KEYS:
        profile = PROFILES[key]
        metadata[key] = {
            "name": profile["name"],
            "machine_value": profile["machine_value"],
            "group_pad": profile_to_pad[key],
        }
    return metadata


GROUP_PROFILE_METADATA = _build_group_profile_metadata()

# GROUP_LAYOUT is re-exported verbatim from the shared data layer
# (single source of truth) via the import above.

__all__ = [
    "PAD_1_DEFAULT_PROFILE",
    "PAD_3_SY_RAW_CC_MAP",
    "PAD_PROFILES",
    "GROUP_PROFILE_METADATA",
    "GROUP_LAYOUT",
]
