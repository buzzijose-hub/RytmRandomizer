"""Human-friendly dual-machine target resolution."""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from ..devices import Device, all_devices

_ALIASES: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType(
    {
        "rytm": ("analog_rytm_mk2",),
        "rytm-only": ("analog_rytm_mk2",),
        "a4": ("analog_four_mk2",),
        "a4-only": ("analog_four_mk2",),
        "both": ("analog_rytm_mk2", "analog_four_mk2"),
    }
)


def resolve_target_devices(
    target: str,
    *,
    registry: Mapping[str, Device] | None = None,
) -> Mapping[str, Device]:
    """Resolve a live-friendly target alias to registered devices."""

    normalized = target.strip().lower()
    if normalized not in _ALIASES:
        raise ValueError(
            "unknown target "
            f"{target!r}; expected one of {', '.join(sorted(_ALIASES))}"
        )
    source = all_devices() if registry is None else registry
    return {device_id: source[device_id] for device_id in _ALIASES[normalized]}
