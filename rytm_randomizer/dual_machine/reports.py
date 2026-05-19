"""Operator-facing reports for dual-machine target selection."""

from __future__ import annotations

from .targets import resolve_target_devices


def target_report(target: str) -> str:
    """Return a passive report for the selected target alias."""

    devices = resolve_target_devices(target)
    lines = [f"Target: {target}", "Devices:"]
    for device_id, device in devices.items():
        lines.append(f"- {device_id}: {device.display_name} ({device.track_count} tracks/pads)")
    return "\n".join(lines)
