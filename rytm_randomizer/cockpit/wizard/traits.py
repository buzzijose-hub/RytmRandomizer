"""Canonical wizard trait names. Single source of truth for analyzers + builder.

Every wizard analyzer (reference, sysex, audio) emits the same four traits in
the same deterministic order. Centralising the tuple here means a new analyzer
or a new builder consumer never needs to reach through one peer module to
borrow the constant from another — there is exactly one import path.
"""

from __future__ import annotations

from typing import Final

#: Names of the four canonical wizard traits, in deterministic display order.
WIZARD_TRAIT_NAMES: Final[tuple[str, ...]] = (
    "rolling_low_end",
    "metallic_tension",
    "hat_density",
    "filter_motion",
)


__all__ = ["WIZARD_TRAIT_NAMES"]
