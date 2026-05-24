"""Built-in trait-to-pad assignment table for the Profile Wizard (WS-C).

The :class:`ProfileBuilder` (see :mod:`.builder`) consumes
:data:`TRAIT_TO_PAD` to derive each candidate :class:`ProfileModel`'s
``pad_mappings`` from the per-source :class:`StyleTrait` s an analyzer
produced. The mapping is *pinned* for Phase 2 — operator-overridable in a
later iteration, but for now four trait names → four canonical Rytm pads.

Pad layout follows the cockpit's 4-pad reference snapshot (used by the
built-in scene profiles and the integration-test fixture):

* Pad 1 — BD (bass drum / kick) — `"rolling_low_end"`
* Pad 2 — SD (snare drum) — `"metallic_tension"`
* Pad 3 — CH/OH (hats) — `"hat_density"`
* Pad 4 — FX/FLT (filter / FX) — `"filter_motion"`

The mapping is exposed as a read-only :class:`~types.MappingProxyType`
proxy over an underlying dict literal. The :class:`~typing.Final`
annotation tells :mod:`mypy` callers may not rebind the module-level name;
the :class:`MappingProxyType` wrapper makes the in-memory mapping itself
refuse mutation at runtime. Together these two guard against the
"someone monkey-patched the trait table during a test" failure mode the
architecture rules forbid (no mutable module-level state in the package).

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"ProfileBuilder" for the authoritative shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

TRAIT_TO_PAD: Final[Mapping[str, int]] = MappingProxyType(
    {
        "rolling_low_end": 1,  # BD
        "metallic_tension": 2,  # SD
        "hat_density": 3,  # CH/OH
        "filter_motion": 4,  # FX/FLT
    }
)
"""Built-in trait-to-pad assignment for Phase 2 :class:`ProfileBuilder`.

Operator-overridable in a later iteration; pinned for now. Trait names
not present in this mapping produce no :class:`TraitPadWeight` entry on
the candidate :class:`ProfileModel` (silently dropped, not an error).
"""

__all__ = ["TRAIT_TO_PAD"]
