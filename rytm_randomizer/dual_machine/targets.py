"""Human-friendly dual-machine target resolution."""

from __future__ import annotations

from collections.abc import Mapping

from ..data.device_targets import DUAL_MACHINE_TARGET_IDS
from ..devices import Device, all_devices


def resolve_target_devices(
    target: str,
    *,
    registry: Mapping[str, Device] | None = None,
) -> Mapping[str, Device]:
    """Resolve a live-friendly target alias to registered devices."""

    normalized = target.strip().lower()
    if normalized not in DUAL_MACHINE_TARGET_IDS:
        raise ValueError(
            "unknown target "
            f"{target!r}; expected one of {', '.join(sorted(DUAL_MACHINE_TARGET_IDS))}"
        )
    source = all_devices() if registry is None else registry
    return {device_id: source[device_id] for device_id in DUAL_MACHINE_TARGET_IDS[normalized]}
