"""``StyleTrait``, ``TraitPadWeight``, and ``ProfileModel`` frozen dataclasses.

The ``ProfileModel`` is the deployable intelligence — the operator's musical
taste captured as a tree of style traits + per-pad bias weights. **The
same dataclass is used for developer-curated built-in Scenes and for
user-authored Profiles**; the only difference is the ``kind`` field.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"ProfileModel" for the authoritative shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Self

from .types import (
    KIND_VALUES,
    TRANSITION_CURVE_VALUES,
    Kind,
    TransitionCurve,
    narrow_kind,
    narrow_transition_curve,
)

_PAD_ID_MIN: Final[int] = 1
_PAD_ID_MAX: Final[int] = 12
_UNIT_MIN: Final[float] = 0.0
_UNIT_MAX: Final[float] = 1.0


def _check_unit_interval(name: str, value: float) -> None:
    """Validate that ``value`` lies inside the closed unit interval [0.0, 1.0]."""

    if value < _UNIT_MIN or value > _UNIT_MAX:
        raise ValueError(f"{name} must lie in [{_UNIT_MIN}, {_UNIT_MAX}]; got {value}")


@dataclass(frozen=True)
class StyleTrait:
    """A named, unit-interval-bounded style dimension.

    Example: ``StyleTrait("rolling_low_end", 0.85)`` means "this profile
    leans strongly toward rolling low-end energy" (0.0 = absent,
    1.0 = maximum).
    """

    name: str
    value: float

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must be a non-empty string")
        _check_unit_interval("value", self.value)

    def to_dict(self) -> dict[str, object]:
        return {"name": self.name, "value": self.value}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        return cls(
            name=str(data["name"]),
            value=float(data["value"]),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class TraitPadWeight:
    """How strongly a given style trait influences a given pad.

    Pairs a trait name (which must match an existing ``StyleTrait.name`` on
    the same profile) with a pad and a unit-interval weight.
    """

    trait: str
    pad_id: int
    weight: float

    def __post_init__(self) -> None:
        if not self.trait:
            raise ValueError("trait must be a non-empty string")
        if not (_PAD_ID_MIN <= self.pad_id <= _PAD_ID_MAX):
            raise ValueError(f"pad_id must be in [{_PAD_ID_MIN}, {_PAD_ID_MAX}]; got {self.pad_id}")
        _check_unit_interval("weight", self.weight)

    def to_dict(self) -> dict[str, object]:
        return {"trait": self.trait, "pad_id": self.pad_id, "weight": self.weight}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        return cls(
            trait=str(data["trait"]),
            pad_id=int(data["pad_id"]),  # type: ignore[arg-type]
            weight=float(data["weight"]),  # type: ignore[arg-type]
        )


@dataclass(frozen=True)
class ProfileModel:
    """The deployable intelligence — operator taste expressed as a model.

    The same shape carries built-in Scenes (``kind="scene"``) and
    user-authored Profiles (``kind="user"``); the engine treats them
    identically. Round-trip-serializable so the export pipeline (WS-G)
    can pack the same instance into a portable binary the embedded
    runtime will eventually load.
    """

    profile_id: str
    name: str
    kind: Kind
    model_version: str
    traits: tuple[StyleTrait, ...]
    pad_mappings: tuple[TraitPadWeight, ...]
    transition_curve: TransitionCurve
    source_summary: str

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id must be a non-empty string")
        if not self.name:
            raise ValueError("name must be a non-empty string")
        if not self.model_version:
            raise ValueError("model_version must be a non-empty string")
        if self.kind not in KIND_VALUES:
            raise ValueError(f"kind must be one of {KIND_VALUES}; got {self.kind!r}")
        if self.transition_curve not in TRANSITION_CURVE_VALUES:
            raise ValueError(
                "transition_curve must be one of "
                f"{TRANSITION_CURVE_VALUES}; got {self.transition_curve!r}"
            )
        known_trait_names = {t.name for t in self.traits}
        for mapping in self.pad_mappings:
            if mapping.trait not in known_trait_names:
                raise ValueError(f"pad_mapping references unknown trait {mapping.trait!r}")

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "name": self.name,
            "kind": self.kind,
            "model_version": self.model_version,
            "traits": [t.to_dict() for t in self.traits],
            "pad_mappings": [m.to_dict() for m in self.pad_mappings],
            "transition_curve": self.transition_curve,
            "source_summary": self.source_summary,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        traits_obj = data["traits"]
        mappings_obj = data["pad_mappings"]
        if not isinstance(traits_obj, (list, tuple)):
            raise TypeError(f"traits must be a list/tuple; got {type(traits_obj).__name__}")
        if not isinstance(mappings_obj, (list, tuple)):
            raise TypeError(f"pad_mappings must be a list/tuple; got {type(mappings_obj).__name__}")
        return cls(
            profile_id=str(data["profile_id"]),
            name=str(data["name"]),
            kind=narrow_kind(str(data["kind"])),
            model_version=str(data["model_version"]),
            traits=tuple(StyleTrait.from_dict(t) for t in traits_obj),
            pad_mappings=tuple(TraitPadWeight.from_dict(m) for m in mappings_obj),
            transition_curve=narrow_transition_curve(str(data["transition_curve"])),
            source_summary=str(data["source_summary"]),
        )


__all__ = ["ProfileModel", "StyleTrait", "TraitPadWeight"]
