"""Canonical mode / intensity / page / mutation-kind string constants (WS-M3).

Single source of truth for the load-bearing string-equality dispatch values
that are currently duplicated across ``shell.py``, ``group_runner.py``,
``randomization.py``, ``behavior/scene_group.py``, and ``behavior/pad_lane.py``.

Each concept is exported in two forms:

* a ``Literal[...]`` type alias for static typing at function boundaries, and
* a ``Final`` tuple of the canonical strings in their canonical order for
  iteration, membership checks, and documentation.

Per Gate 10 of ``docs/PLAN_REQUIREMENTS.md`` (string-literal dispatch hygiene),
no module outside ``rytm_randomizer/data/modes.py`` may introduce new
string-equality dispatch on these values. The architecture test
``tests/architecture/test_no_string_literal_mode_dispatch.py`` (landing in the
WS-S8 sweep) enforces this rule by grepping for any of these strings inside
``==`` comparisons elsewhere in the package.

Per Gate 12 (module-level constants use ``Final``), every tuple here is
annotated ``Final[tuple[..., ...]]`` so a typo or unintended mutation is
caught by ``pyright --strict``.

This module is intentionally pure-data: no imports from the rest of the
package, no runtime logic, no module-level side effects.
"""

from __future__ import annotations

from typing import Final, Literal

# --- Intensity --------------------------------------------------------------
# Selects the per-pad mutation plan in ``data/plans.py::INTENSITY_PLANS``.
# Used today by ``shell.py``, ``group_runner.py``, ``behavior/scene_group.py``.
IntensityMode = Literal["balanced", "deeper", "intense", "harder"]

INTENSITY_MODES: Final[tuple[IntensityMode, ...]] = (
    "balanced",
    "deeper",
    "intense",
    "harder",
)

# --- Page -------------------------------------------------------------------
# Selects which Analog Rytm page (group of parameters) is targeted by a page
# command. Used today by ``shell.py`` and ``group_runner.py``.
PageMode = Literal["src", "filter", "amp", "lfo", "morph", "body", "grit"]

PAGE_MODES: Final[tuple[PageMode, ...]] = (
    "src",
    "filter",
    "amp",
    "lfo",
    "morph",
    "body",
    "grit",
)

# --- Mutation kind ----------------------------------------------------------
# Discriminator between a fresh discovery (free exploration within guardrails)
# and an incremental mutation (small move from current state). Used today by
# ``behavior/pad_lane.py`` in ~20 dispatch sites.
MutationKind = Literal["discovery", "mutation"]

MUTATION_KINDS: Final[tuple[MutationKind, ...]] = (
    "discovery",
    "mutation",
)

# --- Pad-1 machine ----------------------------------------------------------
# Selects which BD machine the Pad 1 isolated commands operate on. Used today
# by ``randomization.py``.
Pad1Mode = Literal["sharp", "hard", "classic", "fm"]

PAD1_MODES: Final[tuple[Pad1Mode, ...]] = (
    "sharp",
    "hard",
    "classic",
    "fm",
)

# --- Zones ------------------------------------------------------------------
# Canonical zone names used by the depth-prompt flow added in WS-S3 and by
# every per-pad mutation plan in ``data/plans.py``. Not every machine exposes
# every zone; the zone tables in ``data/param_maps.py`` are the source of truth
# for per-machine zone availability. This tuple is the *naming* convention.
ZoneName = Literal["src", "filter", "amp", "grit", "body"]

ZONE_NAMES: Final[tuple[ZoneName, ...]] = (
    "src",
    "filter",
    "amp",
    "grit",
    "body",
)


__all__ = [
    "IntensityMode",
    "INTENSITY_MODES",
    "PageMode",
    "PAGE_MODES",
    "MutationKind",
    "MUTATION_KINDS",
    "Pad1Mode",
    "PAD1_MODES",
    "ZoneName",
    "ZONE_NAMES",
]
