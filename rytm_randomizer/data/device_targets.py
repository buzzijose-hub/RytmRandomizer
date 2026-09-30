"""Canonical device IDs for human-facing dual-machine target aliases."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final, Literal

DualMachineDeviceId = Literal["analog_rytm_mk2", "analog_four_mk2"]

DUAL_MACHINE_TARGET_IDS: Final[Mapping[str, tuple[DualMachineDeviceId, ...]]] = MappingProxyType(
    {
        "rytm": ("analog_rytm_mk2",),
        "rytm-only": ("analog_rytm_mk2",),
        "a4": ("analog_four_mk2",),
        "a4-only": ("analog_four_mk2",),
        "both": ("analog_rytm_mk2", "analog_four_mk2"),
    }
)
