"""Pure helpers shared by every wizard analyzer.

Lifting these here means each analyzer composes a single source of
truth: no analyzer reimplements averaging, clamping, or the neutral
profile. Adding a new analyzer is a single-file change.
"""

from __future__ import annotations

from typing import Final

from ..data.profile_model import StyleTrait
from .traits import WIZARD_TRAIT_NAMES

_UNIT_MIN: Final[float] = 0.0
_UNIT_MAX: Final[float] = 1.0


def clamp_unit(value: float) -> float:
    """Clamp ``value`` into ``[0.0, 1.0]``.

    The wizard's trait surface is unit-normalised by contract, so every
    arithmetic that derives a trait routes through this helper. Out-of-range
    inputs map to the nearest clamp edge — no exception.
    """

    if value < _UNIT_MIN:
        return _UNIT_MIN
    if value > _UNIT_MAX:
        return _UNIT_MAX
    return float(value)


def neutral_traits() -> tuple[StyleTrait, ...]:
    """Return the canonical 4-trait tuple at ``0.5`` apiece (neutral).

    Used as the analyzer's "I have no opinion" fallback for empty inputs
    (empty audio folders, empty SysEx dumps, blank reference text).
    """

    return tuple(StyleTrait(name, 0.5) for name in WIZARD_TRAIT_NAMES)


def average_trait_tuples(
    per_source: tuple[tuple[StyleTrait, ...], ...],
) -> tuple[StyleTrait, ...]:
    """Element-wise mean across a non-empty tuple of canonical 4-trait tuples.

    Both call sites (the audio folder path and the SysEx folder path) filter
    out the empty case BEFORE invoking this helper, so the contract is "at
    least one tuple in"; this keeps the branch surface minimal. The result is
    re-clamped to ``[0.0, 1.0]`` so callers that pass un-clamped per-source
    tuples (e.g. the audio path's post-projection averaging) still get a
    unit-interval output.
    """

    count = len(per_source)
    sums: dict[str, float] = dict.fromkeys(WIZARD_TRAIT_NAMES, 0.0)
    for traits in per_source:
        for trait in traits:
            sums[trait.name] = sums.get(trait.name, 0.0) + trait.value
    return tuple(StyleTrait(name, clamp_unit(sums[name] / count)) for name in WIZARD_TRAIT_NAMES)


def build_canonical_traits(
    rolling: float,
    metallic: float,
    hats: float,
    motion: float,
) -> tuple[StyleTrait, ...]:
    """Build the canonical 4-trait tuple in deterministic order.

    Inputs are clamped to ``[0.0, 1.0]`` per trait so callers do not need
    to re-clamp before constructing. The output is always in
    :data:`WIZARD_TRAIT_NAMES` order so consumers can rely on positional
    layout when convenient.
    """

    return (
        StyleTrait("rolling_low_end", clamp_unit(rolling)),
        StyleTrait("metallic_tension", clamp_unit(metallic)),
        StyleTrait("hat_density", clamp_unit(hats)),
        StyleTrait("filter_motion", clamp_unit(motion)),
    )


__all__ = [
    "average_trait_tuples",
    "build_canonical_traits",
    "clamp_unit",
    "neutral_traits",
]
