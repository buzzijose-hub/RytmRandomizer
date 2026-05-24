"""Free-text reference analyzer (Phase 2 stub).

When the operator types just an artist / album / scene name (mode
``"reference"``), there is no file to measure -- the wizard needs a
sensible starting profile derived purely from the text. This module ships
a small, curated lookup table that maps ~20 well-known reference handles
(Surgeon, Daniel Avery, Drone Logic, "Birmingham techno", ...) to a tuple
of :class:`~rytm_randomizer.cockpit.data.profile_model.StyleTrait` s.

A real audio-fingerprint lookup (think AcoustID-for-style) is on the
Phase 3+ roadmap; until then this stub keeps the wizard's reference path
working end-to-end and gives the operator a non-zero starting point they
can refine.

Matching rules (see :func:`lookup_traits`):

* Case-insensitive: ``"SURGEON"`` matches ``"surgeon"``.
* Whitespace-trimmed on both ends of the input.
* Prefix-matched against the lookup keys: ``"birmingham techno"`` matches
  the ``"birmingham"`` entry because the entry's text starts the user's
  text (i.e. the user typed *more* specific text than the table holds).
* If multiple keys match, the longest matching key wins (so
  ``"daniel avery"`` beats a hypothetical ``"daniel"`` entry).
* If nothing matches, :func:`lookup_traits` returns the neutral profile:
  four traits at ``0.5`` each.

The four canonical wizard traits are ``metallic_tension``,
``rolling_low_end``, ``hat_density``, ``filter_motion`` -- the same set
the :mod:`sysex_analyzer` produces and that the
:class:`~rytm_randomizer.cockpit.wizard.builder.ProfileBuilder` (WS-C)
expects.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from ..data.profile_model import StyleTrait

# ---------------------------------------------------------------------------
# Canonical wizard trait names
# ---------------------------------------------------------------------------

#: Names of the four canonical wizard traits, in deterministic display order.
WIZARD_TRAIT_NAMES: Final[tuple[str, ...]] = (
    "rolling_low_end",
    "metallic_tension",
    "hat_density",
    "filter_motion",
)


def _profile(
    rolling_low_end: float,
    metallic_tension: float,
    hat_density: float,
    filter_motion: float,
) -> tuple[StyleTrait, ...]:
    """Build the canonical 4-trait tuple in deterministic order."""

    return (
        StyleTrait("rolling_low_end", rolling_low_end),
        StyleTrait("metallic_tension", metallic_tension),
        StyleTrait("hat_density", hat_density),
        StyleTrait("filter_motion", filter_motion),
    )


# ---------------------------------------------------------------------------
# Built-in lookup table (Phase 2 curated set)
# ---------------------------------------------------------------------------

#: Curated artist / album / scene -> :class:`StyleTrait` tuple lookup.
#:
#: Keys are lowercase; values are immutable 4-tuples of
#: :class:`StyleTrait`. Wrapped in :class:`types.MappingProxyType` so the
#: module-level constant is read-only at runtime (no module-level mutable
#: globals -- per ``.claude/rules/architecture.md`` house style).
_REFERENCE_LOOKUP: Final[Mapping[str, tuple[StyleTrait, ...]]] = MappingProxyType(
    {
        # Industrial / Birmingham techno
        "surgeon": _profile(0.85, 0.78, 0.55, 0.65),
        "regis": _profile(0.80, 0.82, 0.50, 0.60),
        "birmingham": _profile(0.75, 0.85, 0.45, 0.55),
        "british murder boys": _profile(0.82, 0.86, 0.50, 0.60),
        "industrial": _profile(0.70, 0.90, 0.55, 0.50),
        "schranz": _profile(0.78, 0.88, 0.70, 0.45),
        # Hypnotic / dub techno
        "daniel avery": _profile(0.65, 0.45, 0.55, 0.75),
        "drone logic": _profile(0.60, 0.50, 0.50, 0.80),
        "hypnotic": _profile(0.70, 0.40, 0.45, 0.85),
        "basic channel": _profile(0.72, 0.30, 0.35, 0.90),
        # Garage / breakbeat textures
        "garage": _profile(0.55, 0.45, 0.75, 0.50),
        "burial": _profile(0.60, 0.40, 0.70, 0.65),
        "two-step": _profile(0.50, 0.40, 0.80, 0.55),
        # Peak-time / club
        "peak-time": _profile(0.80, 0.60, 0.65, 0.55),
        "berghain": _profile(0.85, 0.65, 0.60, 0.55),
        "rolling": _profile(0.90, 0.50, 0.55, 0.60),
        # Acid / 303-driven
        "acid": _profile(0.65, 0.55, 0.60, 0.85),
        "hardfloor": _profile(0.75, 0.65, 0.60, 0.80),
        # Detroit / minimal
        "detroit": _profile(0.60, 0.55, 0.65, 0.65),
        "minimal": _profile(0.50, 0.45, 0.55, 0.70),
    }
)

#: Sorted longest-first so :func:`lookup_traits` can short-circuit on first hit.
_KEYS_BY_LENGTH_DESC: Final[tuple[str, ...]] = tuple(
    sorted(_REFERENCE_LOOKUP, key=len, reverse=True)
)


def lookup_traits(text: str) -> tuple[StyleTrait, ...]:
    """Return the curated :class:`StyleTrait` tuple matching ``text``.

    Matching is case-insensitive and prefix-based against the curated
    :data:`_REFERENCE_LOOKUP` table. Whitespace at either end of ``text``
    is stripped. When several entries match (e.g. the user types
    ``"birmingham techno"`` and the table has both ``"birmingham"`` and
    a hypothetical ``"birmingham techno"``), the longest matching key
    wins.

    Unknown handles return the neutral 4-trait profile (every trait at
    ``0.5``). The wizard treats that as "we have no opinion -- the
    operator can dial the bars in by hand".
    """

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    needle = text.strip().lower()
    if not needle:
        return _neutral_profile()

    # Iterate keys longest-first so the first hit IS the longest match;
    # this collapses the "longest wins" rule into a single linear scan with
    # no inner-loop branch on the running best.
    for key in _KEYS_BY_LENGTH_DESC:
        if needle.startswith(key):
            return _REFERENCE_LOOKUP[key]
    return _neutral_profile()


def _neutral_profile() -> tuple[StyleTrait, ...]:
    """Return the neutral fallback: every canonical trait at ``0.5``."""

    return _profile(0.5, 0.5, 0.5, 0.5)


__all__ = [
    "WIZARD_TRAIT_NAMES",
    "lookup_traits",
]
