"""Three-layer validator for the Guardrail Profile contract (WS-W Layer 3).

This module turns an *untrusted* draft :class:`GuardrailProfile` -- the artifact
produced by WS-V's interpretation agent -- into a ``VALIDATED`` profile carrying
a content hash, OR raises a :class:`ProfileRejectedError` (a member of the
:class:`~rytm_randomizer.observability.errors.BoundaryError` family) naming the
specific reason.

The three rule layers run in order, short-circuiting on the first failure:

1. **Structural** -- required sections present, field types correct,
   ``schema_version`` is a version this validator understands. A malformed
   draft fails here. Cheap; runs first.
2. **Semantic** -- the draft is well-formed but could still be wrong against
   the hardware:

   * Every :class:`GuardrailBound`'s ``[low, high]`` must fit inside that
     parameter's physical range from :mod:`rytm_randomizer.data` (per the
     pad's profile).
   * The ``pad`` + ``parameter`` must actually exist on the target machine
     (i.e. ``parameter`` is in the profile's ``params``/``safe`` table).
   * No parameter can appear in both a mutating class and ``forbidden``.
   * Every parameter that has a :class:`GuardrailBound` must have a role in
     :class:`RoleMapping` first.
3. **Safety floor** -- the non-negotiable part, **rewrites rather than
   rejects**. If the draft puts a high-risk parameter into a mutating
   class, the validator **forces it to ``LOCKED_DEFAULT``** (or
   ``FORBIDDEN`` for the truly destructive subset) and records that it did
   so. The agent *cannot* author an unsafe profile -- the unsafe part gets
   neutralized.

Output: a frozen :class:`GuardrailProfile` in :class:`ProfileState.VALIDATED`
state with ``content_hash`` populated. Rewrites are logged at ``INFO`` via the
package logger.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, ClassVar

from ..data import PROFILES
from ..observability.errors import BoundaryError
from ..observability.logging import get_logger
from .schema import (
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileState,
    Provenance,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
)

__all__ = [
    "DESTRUCTIVE_HIGH_RISK_PARAMETERS",
    "HIGH_RISK_PARAMETERS",
    "KNOWN_SCHEMA_VERSIONS",
    "MUTATING_CLASSES",
    "PAD_PROFILE_KEY",
    "ProfileRejectedError",
    "validate",
]


_logger = get_logger(__name__)


KNOWN_SCHEMA_VERSIONS: frozenset[str] = frozenset({SCHEMA_VERSION})
"""Schema versions this validator understands."""


MUTATING_CLASSES: frozenset[GuardrailClass] = frozenset(
    {
        GuardrailClass.LIVE_SAFE,
        GuardrailClass.STUDIO_DISCOVERY,
        GuardrailClass.EXPERIMENTAL,
    }
)
"""Classes that actually mutate a parameter -- the safety floor checks these."""


HIGH_RISK_PARAMETERS: frozenset[str] = frozenset(
    {
        # Track / master / mix volume: a spike or dip is destructive to mix
        # balance and unsafe at performance volumes.
        "track_volume",
        "master_volume",
        "AMP Level",
        # Clock / transport / timing: changing these mid-performance breaks
        # synchronization with everything else on stage.
        "clock",
        "transport",
        "tempo",
        # Pattern / program / project change: yanks the whole device into a
        # different state without warning.
        "pattern_change",
        "program_change",
        "project_change",
        # Kit save / clear: destructive to the operator's preset library.
        "kit_save",
        "kit_clear",
        # Extreme oscillator tuning beyond the safe envelope.
        "extreme_tuning",
        # Unvalidated SysEx + live machine switching -- a profile must never
        # author either of these as a mutation.
        "sysex_unvalidated",
        "live_machine_switch",
    }
)
"""High-risk parameters the validator forces out of mutating classes.

Spec section 5.2: any of these in a mutating class is rewritten to
``LOCKED_DEFAULT`` (or ``FORBIDDEN`` if it lands in
:data:`DESTRUCTIVE_HIGH_RISK_PARAMETERS`). Profiles cannot author them
into a mutating class even with intent.
"""


DESTRUCTIVE_HIGH_RISK_PARAMETERS: frozenset[str] = frozenset(
    {
        # The "truly destructive" subset: these get FORBIDDEN, not just
        # LOCKED_DEFAULT, because they can break the operator's preset
        # library or the device's state machine.
        "kit_save",
        "kit_clear",
        "project_change",
        "sysex_unvalidated",
        "live_machine_switch",
    }
)
"""Subset of :data:`HIGH_RISK_PARAMETERS` rewritten to ``FORBIDDEN``."""


PAD_PROFILE_KEY: Mapping[int, str] = {
    1: "2",  # Pad 1 default: My BD Hard (the protected kick foundation).
    2: "3",  # Pad 2 default: My BD Classic / SD profiles share param shape.
    3: "5",  # Pad 3 default: Pad 3 SY Raw mid-bass.
    4: "4",  # Pad 4 default: My BD Acoustic (body / impact / accent).
}
"""Default ``PROFILES`` key per pad.

This mapping is the validator's lookup table for "what is the hardware envelope
of pad N?" -- it points at the profile whose ``safe`` table is the physical
range the validator intersects bound ranges against. The resolver uses the same
mapping when it intersects per-bound.
"""


class ProfileRejectedError(BoundaryError):
    """A draft profile failed validation and cannot be promoted.

    Raised by :func:`validate` when a structural or semantic check fails.
    The ``context`` mapping (see
    :class:`~rytm_randomizer.observability.errors.RytmRandomizerError`)
    carries the specific reason and the offending field so a calling agent
    can surface a precise correction prompt.
    """

    fingerprint: ClassVar[str] = "guardrail.profile.validation_failed"


# ---------------------------------------------------------------------------
# Layer 1 -- structural checks
# ---------------------------------------------------------------------------


def _check_structural(draft: GuardrailProfile) -> None:
    """Raise :class:`ProfileRejectedError` if the draft is structurally invalid.

    Cheap, runs first. Walks each field, asserts type and -- where the schema
    closes the value space -- the enum membership. ``isinstance`` checks
    catch the obvious "the agent emitted a string where an int belongs"
    case; the enum check catches "the agent emitted ``'studio'`` instead
    of ``GuardrailClass.STUDIO_DISCOVERY``".
    """

    if not isinstance(draft, GuardrailProfile):
        raise ProfileRejectedError(
            "draft is not a GuardrailProfile instance",
            context={"layer": "structural", "got": type(draft).__name__},
        )

    if draft.schema_version not in KNOWN_SCHEMA_VERSIONS:
        raise ProfileRejectedError(
            "unknown schema_version",
            context={
                "layer": "structural",
                "schema_version": draft.schema_version,
                "known": sorted(KNOWN_SCHEMA_VERSIONS),
            },
        )

    # Provenance
    if not isinstance(draft.provenance, Provenance):
        raise ProfileRejectedError(
            "provenance is not a Provenance",
            context={"layer": "structural", "field": "provenance"},
        )
    prov = draft.provenance
    if not isinstance(prov.profile_name, str) or not prov.profile_name:
        raise ProfileRejectedError(
            "provenance.profile_name must be a non-empty string",
            context={"layer": "structural", "field": "provenance.profile_name"},
        )
    if not isinstance(prov.source_type, SourceType):
        raise ProfileRejectedError(
            "provenance.source_type must be a SourceType enum",
            context={
                "layer": "structural",
                "field": "provenance.source_type",
                "got": type(prov.source_type).__name__,
            },
        )
    if not isinstance(prov.confidence, Confidence):
        raise ProfileRejectedError(
            "provenance.confidence must be a Confidence enum",
            context={
                "layer": "structural",
                "field": "provenance.confidence",
                "got": type(prov.confidence).__name__,
            },
        )
    if not isinstance(prov.feature_report_hash, str):
        raise ProfileRejectedError(
            "provenance.feature_report_hash must be a string",
            context={
                "layer": "structural",
                "field": "provenance.feature_report_hash",
            },
        )
    if not isinstance(prov.derived_at, str):
        raise ProfileRejectedError(
            "provenance.derived_at must be a string",
            context={"layer": "structural", "field": "provenance.derived_at"},
        )

    # Musical character
    if not isinstance(draft.character, MusicalCharacter):
        raise ProfileRejectedError(
            "character is not a MusicalCharacter",
            context={"layer": "structural", "field": "character"},
        )
    char = draft.character
    if not isinstance(char.style_tags, tuple):
        raise ProfileRejectedError(
            "character.style_tags must be a tuple",
            context={"layer": "structural", "field": "character.style_tags"},
        )
    if not isinstance(char.bpm_range, tuple) or len(char.bpm_range) != 2:
        raise ProfileRejectedError(
            "character.bpm_range must be a (low, high) tuple",
            context={"layer": "structural", "field": "character.bpm_range"},
        )
    low_bpm, high_bpm = char.bpm_range
    if not isinstance(low_bpm, int) or not isinstance(high_bpm, int):
        raise ProfileRejectedError(
            "character.bpm_range entries must be integers",
            context={"layer": "structural", "field": "character.bpm_range"},
        )
    if low_bpm > high_bpm:
        raise ProfileRejectedError(
            "character.bpm_range low must be <= high",
            context={
                "layer": "structural",
                "field": "character.bpm_range",
                "low": low_bpm,
                "high": high_bpm,
            },
        )

    # Role mapping
    if not isinstance(draft.role_mapping, RoleMapping):
        raise ProfileRejectedError(
            "role_mapping is not a RoleMapping",
            context={"layer": "structural", "field": "role_mapping"},
        )

    # Bounds tuple
    if not isinstance(draft.bounds, tuple):
        raise ProfileRejectedError(
            "bounds must be a tuple",
            context={"layer": "structural", "field": "bounds"},
        )
    for idx, bound in enumerate(draft.bounds):
        if not isinstance(bound, GuardrailBound):
            raise ProfileRejectedError(
                "bounds entry is not a GuardrailBound",
                context={
                    "layer": "structural",
                    "field": f"bounds[{idx}]",
                    "got": type(bound).__name__,
                },
            )
        if not isinstance(bound.guardrail_class, GuardrailClass):
            raise ProfileRejectedError(
                "bound.guardrail_class is not a GuardrailClass enum",
                context={
                    "layer": "structural",
                    "field": f"bounds[{idx}].guardrail_class",
                    "got": type(bound.guardrail_class).__name__,
                },
            )
        if not isinstance(bound.low, int) or not isinstance(bound.high, int):
            raise ProfileRejectedError(
                "bound.low / bound.high must be integers",
                context={
                    "layer": "structural",
                    "field": f"bounds[{idx}]",
                },
            )
        if bound.low > bound.high:
            raise ProfileRejectedError(
                "bound.low must be <= bound.high",
                context={
                    "layer": "structural",
                    "field": f"bounds[{idx}]",
                    "parameter": bound.parameter,
                    "low": bound.low,
                    "high": bound.high,
                },
            )

    # Locked / forbidden
    if not isinstance(draft.locked_default, tuple):
        raise ProfileRejectedError(
            "locked_default must be a tuple",
            context={"layer": "structural", "field": "locked_default"},
        )
    if not isinstance(draft.forbidden, tuple):
        raise ProfileRejectedError(
            "forbidden must be a tuple",
            context={"layer": "structural", "field": "forbidden"},
        )

    # Scenes
    if not isinstance(draft.scenes, tuple):
        raise ProfileRejectedError(
            "scenes must be a tuple",
            context={"layer": "structural", "field": "scenes"},
        )
    for idx, scene in enumerate(draft.scenes):
        if not isinstance(scene, SceneGuardrail):
            raise ProfileRejectedError(
                "scenes entry is not a SceneGuardrail",
                context={
                    "layer": "structural",
                    "field": f"scenes[{idx}]",
                    "got": type(scene).__name__,
                },
            )

    # State must be an enum value
    if not isinstance(draft.state, ProfileState):
        raise ProfileRejectedError(
            "state must be a ProfileState enum",
            context={
                "layer": "structural",
                "field": "state",
                "got": type(draft.state).__name__,
            },
        )


# ---------------------------------------------------------------------------
# Layer 2 -- semantic checks
# ---------------------------------------------------------------------------


def _hardware_range_for(pad: int, parameter: str) -> tuple[int, int] | None:
    """Return the physical ``(low, high)`` range for ``(pad, parameter)``.

    Returns ``None`` when either the pad is not in :data:`PAD_PROFILE_KEY` or
    the parameter does not exist on that pad's profile.
    """

    profile_key = PAD_PROFILE_KEY.get(pad)
    if profile_key is None:
        return None
    profile = PROFILES.get(profile_key)
    if profile is None:  # pragma: no cover - defensive
        return None
    safe: Mapping[str, tuple[int, int]] = profile["safe"]
    return safe.get(parameter)


def _check_semantic(draft: GuardrailProfile) -> None:
    """Cross-check the draft against the hardware ranges in ``data/``.

    Specifically:

    * Every :class:`GuardrailBound`'s ``[low, high]`` must fit inside the
      physical range :func:`_hardware_range_for` returns.
    * The bound's ``pad`` must be in :data:`PAD_PROFILE_KEY` and the
      ``parameter`` must exist on that pad's profile.
    * No parameter can appear in both a mutating ``GuardrailBound`` and the
      ``forbidden`` tuple.
    * Every parameter that has a ``GuardrailBound`` must have a role in
      ``role_mapping`` first (the "map to role before deriving ranges"
      rule).
    """

    forbidden_set: frozenset[str] = frozenset(draft.forbidden)
    role_assignments = draft.role_mapping.assignments

    for idx, bound in enumerate(draft.bounds):
        if bound.pad not in PAD_PROFILE_KEY:
            raise ProfileRejectedError(
                "bound references a pad that is not configured",
                context={
                    "layer": "semantic",
                    "parameter": bound.parameter,
                    "pad": bound.pad,
                    "configured_pads": sorted(PAD_PROFILE_KEY),
                },
            )

        hardware = _hardware_range_for(bound.pad, bound.parameter)
        if hardware is None:
            raise ProfileRejectedError(
                "bound references a parameter that does not exist on the pad",
                context={
                    "layer": "semantic",
                    "parameter": bound.parameter,
                    "pad": bound.pad,
                },
            )

        hw_low, hw_high = hardware
        if bound.low < hw_low or bound.high > hw_high:
            raise ProfileRejectedError(
                "bound range exceeds the hardware envelope",
                context={
                    "layer": "semantic",
                    "parameter": bound.parameter,
                    "pad": bound.pad,
                    "bound_range": (bound.low, bound.high),
                    "hardware_range": (hw_low, hw_high),
                },
            )

        if bound.guardrail_class in MUTATING_CLASSES and bound.parameter in forbidden_set:
            raise ProfileRejectedError(
                "parameter is both in a mutating class and in forbidden",
                context={
                    "layer": "semantic",
                    "parameter": bound.parameter,
                    "guardrail_class": bound.guardrail_class.value,
                },
            )

        if bound.guardrail_class in MUTATING_CLASSES and bound.pad not in role_assignments:
            raise ProfileRejectedError(
                "mutated bound references a pad without a role mapping",
                context={
                    "layer": "semantic",
                    "parameter": bound.parameter,
                    "pad": bound.pad,
                    "bound_index": idx,
                },
            )


# ---------------------------------------------------------------------------
# Layer 3 -- safety floor (rewrites)
# ---------------------------------------------------------------------------


def _apply_safety_floor(
    draft: GuardrailProfile,
) -> tuple[tuple[GuardrailBound, ...], tuple[str, ...], tuple[str, ...]]:
    """Force every high-risk parameter out of a mutating class.

    Returns the rewritten ``(bounds, locked_default, forbidden)`` triple. The
    rewrite is in-memory: the input ``draft`` is **not** mutated -- we return
    new tuples. Each rewrite is logged at ``INFO`` so the operator can audit
    what the safety floor changed.
    """

    new_bounds: list[GuardrailBound] = []
    locked_default = list(draft.locked_default)
    forbidden = list(draft.forbidden)
    locked_seen = set(locked_default)
    forbidden_seen = set(forbidden)

    for bound in draft.bounds:
        if bound.parameter in HIGH_RISK_PARAMETERS and bound.guardrail_class in MUTATING_CLASSES:
            if bound.parameter in DESTRUCTIVE_HIGH_RISK_PARAMETERS:
                target_class = GuardrailClass.FORBIDDEN
                if bound.parameter not in forbidden_seen:
                    forbidden.append(bound.parameter)
                    forbidden_seen.add(bound.parameter)
            else:
                target_class = GuardrailClass.LOCKED_DEFAULT
                if bound.parameter not in locked_seen:
                    locked_default.append(bound.parameter)
                    locked_seen.add(bound.parameter)

            _logger.info(
                "guardrails.safety_floor rewrite",
                extra={
                    "kind": "safety_floor_rewrite",
                    "parameter": bound.parameter,
                    "pad": bound.pad,
                    "original_class": bound.guardrail_class.value,
                    "rewritten_class": target_class.value,
                },
            )
            new_bounds.append(dataclasses.replace(bound, guardrail_class=target_class))
        else:
            new_bounds.append(bound)

    return tuple(new_bounds), tuple(locked_default), tuple(forbidden)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def validate(draft: GuardrailProfile) -> GuardrailProfile:
    """Validate ``draft`` and return a frozen, hashed ``VALIDATED`` profile.

    The three layers run in order:

    1. Structural -- raise :class:`ProfileRejectedError` on the first
       malformed field.
    2. Semantic -- raise :class:`ProfileRejectedError` on the first
       hardware-/contract-incompatible bound.
    3. Safety floor -- *rewrite* any high-risk parameter in a mutating
       class to ``LOCKED_DEFAULT`` (or ``FORBIDDEN`` for the destructive
       subset). Never rejects -- rewriting keeps the 95%-good intent.

    The returned profile is a NEW :class:`GuardrailProfile`:

    * ``state`` flipped to :class:`ProfileState.VALIDATED`,
    * ``bounds`` / ``locked_default`` / ``forbidden`` rewritten per the
      safety floor,
    * ``content_hash`` computed via :func:`compute_content_hash`.

    The input ``draft`` is not mutated.
    """

    _check_structural(draft)
    _check_semantic(draft)

    new_bounds, new_locked, new_forbidden = _apply_safety_floor(draft)

    # Build the to-be-validated profile with state flipped and bounds rewritten,
    # then compute its content hash and inline it.
    intermediate = dataclasses.replace(
        draft,
        bounds=new_bounds,
        locked_default=new_locked,
        forbidden=new_forbidden,
        state=ProfileState.VALIDATED,
        content_hash="",
    )
    digest = compute_content_hash(intermediate)
    validated: GuardrailProfile = dataclasses.replace(intermediate, content_hash=digest)

    _logger.info(
        "guardrails.validate",
        extra={
            "kind": "guardrails_validate",
            "profile_name": draft.provenance.profile_name,
            "content_hash": digest,
            "rewrote_bounds": sum(
                1
                for a, b in zip(draft.bounds, new_bounds)
                if a.guardrail_class is not b.guardrail_class
            ),
        },
    )

    # Keep mypy/static-analysis honest: ``validated`` is a GuardrailProfile.
    _: Any = validated
    return validated
