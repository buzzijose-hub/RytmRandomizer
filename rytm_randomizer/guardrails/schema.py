"""Typed Guardrail Profile contract (the WS-W leaf module).

This module defines the data contract that ties the four-layer guardrails
system together: WS-V (style analysis) produces a draft ``GuardrailProfile``
conforming to this schema; later WS-W modules (``validation``, ``store``,
``resolver``) validate, persist, and consume it.

By design, this module is a **leaf**: it imports only from the standard
library. It must not import anything from ``rytm_randomizer/`` (not ``data``,
not ``state``, not anything). The architecture tests in WS-T enforce that
import direction so the schema can be reused as the shared contract by both
WS-V and the rest of WS-W without creating cycles.

Scope notes (see ``GUARDRAILS_DESIGN_SPEC.md`` Part B, sections 13-14):

* This module defines **types only**. No validation logic lives here -
  ``validation.py`` (a later workstream) is responsible for structural,
  semantic, and safety-floor enforcement. A ``GuardrailProfile`` instance can
  be constructed with any field values; whether it is *valid* is a separate
  concern.
* No file I/O. Persistence is ``store.py``'s job.

Everything is frozen, matching the established house style in
``rytm_randomizer/mock_midi.py`` and ``rytm_randomizer/state/anchor.py``:
``@dataclass(frozen=True)``, ``MappingProxyType`` for nested maps, ``tuple``
in place of ``list``, and full type annotations under
``from __future__ import annotations``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


SCHEMA_VERSION: str = "1.0"
"""Current Guardrail Profile schema version.

Stamped onto every :class:`GuardrailProfile` so the store can detect schema
drift and the resolver can confirm what it is running. Bump on any
backwards-incompatible field change.
"""


# ---------------------------------------------------------------------------
# Closed enums (spec section 14)
# ---------------------------------------------------------------------------


class GuardrailClass(Enum):
    """The risk-tiered class assigned to each mutation bound (spec section 5.1)."""

    LIVE_SAFE = "LIVE_SAFE"
    STUDIO_DISCOVERY = "STUDIO_DISCOVERY"
    EXPERIMENTAL = "EXPERIMENTAL"
    LOCKED_DEFAULT = "LOCKED_DEFAULT"
    FORBIDDEN = "FORBIDDEN"


class RiskTier(Enum):
    """Per-parameter intrinsic risk tier (spec section 5.2 - the safety floor)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class SourceType(Enum):
    """Provenance of the reference material a profile was derived from."""

    SINGLE_TRACK = "SINGLE_TRACK"
    FOLDER_LIBRARY = "FOLDER_LIBRARY"
    REFERENCE_PLAYLIST = "REFERENCE_PLAYLIST"
    USER_RELEASE_LIBRARY = "USER_RELEASE_LIBRARY"
    LIVE_RECORDING = "LIVE_RECORDING"
    FACTORY_SOUND_STUDY = "FACTORY_SOUND_STUDY"
    STYLE_DESCRIPTION_ONLY = "STYLE_DESCRIPTION_ONLY"


class Confidence(Enum):
    """Confidence in the measurement that produced a profile (spec section 6.2)."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ProfileState(Enum):
    """Lifecycle state of a profile (spec section 4.3)."""

    DRAFT = "DRAFT"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    STUDIO_TESTED = "STUDIO_TESTED"
    LIVE_APPROVED = "LIVE_APPROVED"
    ARCHIVED = "ARCHIVED"


# ---------------------------------------------------------------------------
# Frozen dataclasses (spec section 14)
# ---------------------------------------------------------------------------


def _freeze_str_str(mapping: Mapping[str, str]) -> Mapping[str, str]:
    """Return a read-only ``MappingProxyType`` over a shallow copy of ``mapping``."""

    return MappingProxyType(dict(mapping))


@dataclass(frozen=True)
class Provenance:
    """Where a profile came from and how confident the derivation was.

    The ``feature_report_hash`` ties the profile to exactly the WS-V
    ``FeatureReport`` it was derived from so the full traceability chain -
    profile -> measurement -> source audio - can be reconstructed.
    """

    profile_name: str
    source_type: SourceType
    confidence: Confidence
    feature_report_hash: str
    derived_at: str
    """ISO 8601 timestamp string (e.g. ``"2026-05-14T12:34:56Z"``)."""


@dataclass(frozen=True)
class MusicalCharacter:
    """The behavioral character measured from the reference material.

    ``musical_findings`` is a frozen ``Mapping[str, str]`` covering the
    measurement axes called out in spec section 4.1: ``tempo_groove``,
    ``low_end_behavior``, ``percussion_density``, ``bass_tonal_movement``,
    ``texture_noise``, ``fx_space``, ``arrangement_energy_arc``.

    The schema does not enforce which keys appear (that is validation's job);
    it only guarantees the mapping is read-only.
    """

    style_tags: tuple[str, ...]
    """3-8 behavioral tags. Behavioral, not marketing - per spec section 4.1."""

    bpm_range: tuple[int, int]
    """``(low_bpm, high_bpm)``."""

    energy_profile: str
    density_profile: str
    musical_findings: Mapping[str, str] = field(
        default_factory=lambda: MappingProxyType({})
    )

    def __post_init__(self) -> None:
        # Freeze the nested mapping so callers can hold a reference safely.
        object.__setattr__(
            self, "musical_findings", _freeze_str_str(self.musical_findings)
        )


@dataclass(frozen=True)
class RoleAssignment:
    """The per-pad payload of :class:`RoleMapping`.

    Bundles the role string (e.g. ``"kick"``) with the derived mutation
    direction (e.g. ``"tighten"``). Kept as a frozen dataclass rather than a
    raw tuple so future additions (e.g. a confidence tag per pad) do not break
    the contract.
    """

    role: str
    mutation_direction: str


@dataclass(frozen=True)
class RoleMapping:
    """Per-pad role + mutation-direction mapping (spec section 14).

    Wraps a frozen ``Mapping[int, RoleAssignment]`` so the role table is
    addressable by pad number and immutable once constructed.
    """

    assignments: Mapping[int, RoleAssignment]

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "assignments", MappingProxyType(dict(self.assignments))
        )


@dataclass(frozen=True)
class GuardrailBound:
    """The atom of a guardrail profile (spec section 14).

    One ``pad`` + one ``parameter`` + a ``[low, high]`` mutation range + the
    :class:`GuardrailClass` it lives in + a textual ``direction`` that
    captures the qualitative intent ("tighten", "open", "modulate
    mid-energy", ...). The resolver works bound-by-bound, which is why
    per-parameter fail-loud (drop one bound to ``LOCKED_DEFAULT`` rather
    than rejecting the profile) is natural.
    """

    pad: int
    parameter: str
    low: int
    high: int
    guardrail_class: GuardrailClass
    direction: str


@dataclass(frozen=True)
class SceneGuardrail:
    """Per-scene behavioral constraints (spec section 14).

    A scene runs at a coarser grain than individual bounds: it gates which
    pads may move at all (``pads_allowed``), how aggressively
    (``mutation_depth``), under which class, and which roles are locked
    against any change inside the scene.
    """

    scene_key: str
    pads_allowed: tuple[int, ...]
    mutation_depth: str
    risk_class: GuardrailClass
    locked_roles: tuple[str, ...]


@dataclass(frozen=True)
class GuardrailProfile:
    """The top-level Guardrail Profile artifact (spec section 14).

    A validated instance is the unit of intelligence that flows from WS-V
    through the validator into the resolver and the engines. ``content_hash``
    + ``schema_version`` make the artifact tamper-evident and
    schema-evolution-survivable.

    The schema deliberately has **no field for a melody, an arrangement, or a
    patch**. The copyright-safety guarantee from spec section 7.3 is
    structural: there is simply nowhere in the contract to put a replica.
    """

    provenance: Provenance
    character: MusicalCharacter
    role_mapping: RoleMapping
    bounds: tuple[GuardrailBound, ...]
    locked_default: tuple[str, ...]
    forbidden: tuple[str, ...]
    scenes: tuple[SceneGuardrail, ...]
    state: ProfileState
    schema_version: str
    content_hash: str


# ---------------------------------------------------------------------------
# Canonical serialization + content hashing
# ---------------------------------------------------------------------------


def _to_canonical(value: object) -> object:
    """Convert an arbitrary schema value into a JSON-canonical primitive.

    Used by :func:`compute_content_hash` to produce a deterministic
    representation of a profile. The transformation is recursive and total:

    * :class:`Enum` instances become their ``.value`` (a string for every
      enum in this module).
    * Dataclasses become ``dict``\\s of their public fields, recursively
      canonicalized. The ``content_hash`` field of :class:`GuardrailProfile`
      is intentionally excluded so the hash describes *content* and is
      stable across a recompute-after-construction.
    * :class:`~collections.abc.Mapping` (including ``MappingProxyType``)
      becomes a plain ``dict`` with stringified keys.
    * Tuples and lists become lists.
    * Primitives (``str``, ``int``, ``float``, ``bool``, ``None``) pass
      through unchanged.
    """

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for f in fields(value):
            if isinstance(value, GuardrailProfile) and f.name == "content_hash":
                # Exclude the hash field from its own hash input.
                continue
            result[f.name] = _to_canonical(getattr(value, f.name))
        return result
    if isinstance(value, Mapping):
        return {str(k): _to_canonical(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_canonical(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(
        f"_to_canonical: unsupported value type {type(value).__name__!r}"
    )


def compute_content_hash(profile_without_hash: GuardrailProfile) -> str:
    """Return the deterministic SHA-256 of ``profile_without_hash``.

    The hash is computed over the canonical JSON representation of the
    profile with the ``content_hash`` field excluded - so a profile can be
    constructed with an empty hash, the hash computed, and a second profile
    constructed with the hash inlined without the act of inlining changing
    the hash.

    Canonicalization rules (so independent implementations agree):

    * ``json.dumps(..., sort_keys=True, separators=(",", ":"))`` -
      lexicographically sorted keys, no whitespace.
    * Enums collapse to their ``.value``.
    * Tuples become JSON arrays.
    * Read-only mappings (``MappingProxyType``) become plain JSON objects
      with string keys.

    The returned digest is a lowercase 64-character hex string.
    """

    canonical = _to_canonical(profile_without_hash)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "SCHEMA_VERSION",
    "Confidence",
    "GuardrailBound",
    "GuardrailClass",
    "GuardrailProfile",
    "MusicalCharacter",
    "ProfileState",
    "Provenance",
    "RiskTier",
    "RoleAssignment",
    "RoleMapping",
    "SceneGuardrail",
    "SourceType",
    "compute_content_hash",
]
