"""Passive numeric style target vectors for snapshot-routing planners."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .style_profiles import STYLE_PROFILES

STYLE_TARGET_VECTOR_AXES: Final[tuple[str, ...]] = (
    "low_end_weight",
    "transient_density",
    "attack_sharpness",
    "decay_tail",
    "darkness",
    "metallicity",
    "noise_grit",
    "drive_pressure",
    "space_depth",
    "motion_amount",
    "repetition_hypnosis",
    "percussive_density",
    "tonal_center_weight",
    "industrial_edge",
    "minimal_restraint",
    "warehouse_intensity",
)


@dataclass(frozen=True)
class StyleTargetVector:
    """Bounded 0-100 style target vector for passive planning."""

    key: str
    low_end_weight: int
    transient_density: int
    attack_sharpness: int
    decay_tail: int
    darkness: int
    metallicity: int
    noise_grit: int
    drive_pressure: int
    space_depth: int
    motion_amount: int
    repetition_hypnosis: int
    percussive_density: int
    tonal_center_weight: int
    industrial_edge: int
    minimal_restraint: int
    warehouse_intensity: int

    def as_mapping(self) -> Mapping[str, int]:
        """Return axis values in stable report order."""

        return MappingProxyType(
            {
                "low_end_weight": self.low_end_weight,
                "transient_density": self.transient_density,
                "attack_sharpness": self.attack_sharpness,
                "decay_tail": self.decay_tail,
                "darkness": self.darkness,
                "metallicity": self.metallicity,
                "noise_grit": self.noise_grit,
                "drive_pressure": self.drive_pressure,
                "space_depth": self.space_depth,
                "motion_amount": self.motion_amount,
                "repetition_hypnosis": self.repetition_hypnosis,
                "percussive_density": self.percussive_density,
                "tonal_center_weight": self.tonal_center_weight,
                "industrial_edge": self.industrial_edge,
                "minimal_restraint": self.minimal_restraint,
                "warehouse_intensity": self.warehouse_intensity,
            }
        )


def _target(
    key: str,
    *,
    low_end_weight: int,
    transient_density: int,
    attack_sharpness: int,
    decay_tail: int,
    darkness: int,
    metallicity: int,
    noise_grit: int,
    drive_pressure: int,
    space_depth: int,
    motion_amount: int,
    repetition_hypnosis: int,
    percussive_density: int,
    tonal_center_weight: int,
    industrial_edge: int,
    minimal_restraint: int,
    warehouse_intensity: int,
) -> StyleTargetVector:
    return StyleTargetVector(
        key=key,
        low_end_weight=low_end_weight,
        transient_density=transient_density,
        attack_sharpness=attack_sharpness,
        decay_tail=decay_tail,
        darkness=darkness,
        metallicity=metallicity,
        noise_grit=noise_grit,
        drive_pressure=drive_pressure,
        space_depth=space_depth,
        motion_amount=motion_amount,
        repetition_hypnosis=repetition_hypnosis,
        percussive_density=percussive_density,
        tonal_center_weight=tonal_center_weight,
        industrial_edge=industrial_edge,
        minimal_restraint=minimal_restraint,
        warehouse_intensity=warehouse_intensity,
    )


_STYLE_TARGET_VECTOR_ITEMS: Final[tuple[StyleTargetVector, ...]] = (
    _target(
        "detroit_minimal",
        low_end_weight=70,
        transient_density=55,
        attack_sharpness=65,
        decay_tail=30,
        darkness=40,
        metallicity=35,
        noise_grit=20,
        drive_pressure=35,
        space_depth=25,
        motion_amount=35,
        repetition_hypnosis=90,
        percussive_density=45,
        tonal_center_weight=45,
        industrial_edge=15,
        minimal_restraint=95,
        warehouse_intensity=50,
    ),
    _target(
        "mills_hypnotic",
        low_end_weight=65,
        transient_density=75,
        attack_sharpness=85,
        decay_tail=35,
        darkness=50,
        metallicity=85,
        noise_grit=45,
        drive_pressure=70,
        space_depth=60,
        motion_amount=90,
        repetition_hypnosis=100,
        percussive_density=70,
        tonal_center_weight=55,
        industrial_edge=45,
        minimal_restraint=55,
        warehouse_intensity=80,
    ),
    _target(
        "hood_stripped",
        low_end_weight=80,
        transient_density=45,
        attack_sharpness=80,
        decay_tail=25,
        darkness=50,
        metallicity=35,
        noise_grit=35,
        drive_pressure=65,
        space_depth=15,
        motion_amount=25,
        repetition_hypnosis=90,
        percussive_density=35,
        tonal_center_weight=50,
        industrial_edge=25,
        minimal_restraint=100,
        warehouse_intensity=65,
    ),
    _target(
        "ur_machine_funk",
        low_end_weight=70,
        transient_density=70,
        attack_sharpness=75,
        decay_tail=35,
        darkness=40,
        metallicity=55,
        noise_grit=45,
        drive_pressure=60,
        space_depth=35,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=75,
        tonal_center_weight=60,
        industrial_edge=35,
        minimal_restraint=55,
        warehouse_intensity=65,
    ),
    _target(
        "hardgroove_percussive",
        low_end_weight=75,
        transient_density=85,
        attack_sharpness=75,
        decay_tail=40,
        darkness=40,
        metallicity=45,
        noise_grit=55,
        drive_pressure=70,
        space_depth=30,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=95,
        tonal_center_weight=45,
        industrial_edge=35,
        minimal_restraint=40,
        warehouse_intensity=75,
    ),
    _target(
        "birmingham_pressure",
        low_end_weight=85,
        transient_density=80,
        attack_sharpness=85,
        decay_tail=25,
        darkness=85,
        metallicity=65,
        noise_grit=90,
        drive_pressure=95,
        space_depth=20,
        motion_amount=65,
        repetition_hypnosis=90,
        percussive_density=75,
        tonal_center_weight=35,
        industrial_edge=95,
        minimal_restraint=45,
        warehouse_intensity=95,
    ),
    _target(
        "industrial_dark",
        low_end_weight=80,
        transient_density=80,
        attack_sharpness=80,
        decay_tail=45,
        darkness=100,
        metallicity=90,
        noise_grit=100,
        drive_pressure=90,
        space_depth=35,
        motion_amount=70,
        repetition_hypnosis=75,
        percussive_density=80,
        tonal_center_weight=30,
        industrial_edge=100,
        minimal_restraint=30,
        warehouse_intensity=90,
    ),
    _target(
        "deep_dark_hypnosis",
        low_end_weight=85,
        transient_density=45,
        attack_sharpness=45,
        decay_tail=70,
        darkness=95,
        metallicity=35,
        noise_grit=45,
        drive_pressure=55,
        space_depth=85,
        motion_amount=65,
        repetition_hypnosis=100,
        percussive_density=45,
        tonal_center_weight=65,
        industrial_edge=35,
        minimal_restraint=65,
        warehouse_intensity=60,
    ),
    _target(
        "warehouse_peak",
        low_end_weight=90,
        transient_density=90,
        attack_sharpness=90,
        decay_tail=35,
        darkness=65,
        metallicity=65,
        noise_grit=70,
        drive_pressure=85,
        space_depth=55,
        motion_amount=85,
        repetition_hypnosis=85,
        percussive_density=85,
        tonal_center_weight=45,
        industrial_edge=65,
        minimal_restraint=35,
        warehouse_intensity=100,
    ),
    _target(
        "jose_core_techno",
        low_end_weight=90,
        transient_density=85,
        attack_sharpness=85,
        decay_tail=35,
        darkness=85,
        metallicity=80,
        noise_grit=85,
        drive_pressure=95,
        space_depth=45,
        motion_amount=85,
        repetition_hypnosis=95,
        percussive_density=85,
        tonal_center_weight=45,
        industrial_edge=90,
        minimal_restraint=60,
        warehouse_intensity=95,
    ),
)

STYLE_TARGET_VECTORS: Final[Mapping[str, StyleTargetVector]] = MappingProxyType(
    {target.key: target for target in _STYLE_TARGET_VECTOR_ITEMS}
)

if set(STYLE_TARGET_VECTORS) != set(STYLE_PROFILES):
    raise ValueError("style target vectors must cover every style profile")

__all__ = [
    "STYLE_TARGET_VECTOR_AXES",
    "STYLE_TARGET_VECTORS",
    "StyleTargetVector",
]
