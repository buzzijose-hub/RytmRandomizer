"""Passive target scope model for Live Snapshot performance mode.

This module models which machine is selected for future snapshot capture,
mutation, and restore. It does not import MIDI libraries, open ports, send
messages, request SysEx, receive live SysEx, write SysEx, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..observability.errors import DataError


class PerformanceSnapshotTargetError(DataError, ValueError):
    """Raised when a performance snapshot target cannot be normalized."""


@dataclass(frozen=True)
class PerformanceSnapshotDeviceScope:
    """One device's role within a future Live Snapshot target selection."""

    key: str
    label: str
    capture_enabled: bool
    mutation_enabled: bool
    restore_enabled: bool
    leave_alone: bool


@dataclass(frozen=True)
class PerformanceSnapshotTargetPlan:
    """Passive scope plan for Rytm-only, Analog-Four-only, or both targets."""

    mode: str
    canonical_target: str
    active_devices: tuple[PerformanceSnapshotDeviceScope, ...]
    untouched_devices: tuple[PerformanceSnapshotDeviceScope, ...]

    @property
    def active_device_keys(self) -> tuple[str, ...]:
        return tuple(device.key for device in self.active_devices)

    @property
    def untouched_device_keys(self) -> tuple[str, ...]:
        return tuple(device.key for device in self.untouched_devices)

    @property
    def active_device_labels(self) -> tuple[str, ...]:
        return tuple(device.label for device in self.active_devices)

    @property
    def untouched_device_labels(self) -> tuple[str, ...]:
        return tuple(device.label for device in self.untouched_devices)


DEVICE_LABELS = {
    "analog_rytm": "Analog Rytm MKII",
    "analog_four": "Analog Four MKII",
}

TARGET_ALIASES = {
    "rytm": "rytm",
    "analog-rytm": "rytm",
    "analog_rytm": "rytm",
    "analogrytm": "rytm",
    "a4": "analog-four",
    "analog-four": "analog-four",
    "analog_four": "analog-four",
    "analog4": "analog-four",
    "four": "analog-four",
    "both": "both",
    "all": "both",
}

ACTIVE_DEVICE_KEYS = {
    "rytm": ("analog_rytm",),
    "analog-four": ("analog_four",),
    "both": ("analog_rytm", "analog_four"),
}

ALL_DEVICE_KEYS = ("analog_rytm", "analog_four")


def build_performance_snapshot_target_plan(target: str) -> PerformanceSnapshotTargetPlan:
    """Build a passive target-scope plan for a future Live Snapshot session."""

    canonical_target = _normalize_target(target)
    active_keys = ACTIVE_DEVICE_KEYS[canonical_target]
    untouched_keys = tuple(key for key in ALL_DEVICE_KEYS if key not in active_keys)
    return PerformanceSnapshotTargetPlan(
        mode="live_snapshot",
        canonical_target=canonical_target,
        active_devices=tuple(_active_device(key) for key in active_keys),
        untouched_devices=tuple(_untouched_device(key) for key in untouched_keys),
    )


def format_performance_snapshot_target_report(
    plan: PerformanceSnapshotTargetPlan,
) -> list[str]:
    """Format a deterministic passive target-scope report."""

    lines = [
        "RytmRandomizer passive Performance Snapshot Target Report",
        f"Mode: {plan.mode}",
        f"Requested target: {plan.canonical_target}",
        f"Active devices: {_format_labels(plan.active_device_labels)}",
        f"Untouched devices: {_format_labels(plan.untouched_device_labels)}",
        "Device actions:",
    ]
    for device in plan.active_devices:
        lines.append(
            f"- {device.label}: capture enabled / mutation enabled / "
            "restore target captured snapshot"
        )
    for device in plan.untouched_devices:
        lines.append(f"- {device.label}: untouched / no capture / no mutation / no restore")
    lines.extend(
        [
            "Target policy:",
            "- only active devices may be captured",
            "- only active devices may receive planned mutations",
            "- untouched devices receive no capture request, no CC messages, and no restore",
            "Safety:",
            "- passive/read-only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_performance_snapshot_target_error(message: str) -> list[str]:
    """Format a deterministic passive target-scope error."""

    return [
        "RytmRandomizer passive Performance Snapshot Target Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _normalize_target(target: str) -> str:
    normalized = str(target).strip().lower()
    try:
        return TARGET_ALIASES[normalized]
    except KeyError as exc:
        raise PerformanceSnapshotTargetError("target must be rytm, analog-four, or both") from exc


def _active_device(key: str) -> PerformanceSnapshotDeviceScope:
    return PerformanceSnapshotDeviceScope(
        key=key,
        label=DEVICE_LABELS[key],
        capture_enabled=True,
        mutation_enabled=True,
        restore_enabled=True,
        leave_alone=False,
    )


def _untouched_device(key: str) -> PerformanceSnapshotDeviceScope:
    return PerformanceSnapshotDeviceScope(
        key=key,
        label=DEVICE_LABELS[key],
        capture_enabled=False,
        mutation_enabled=False,
        restore_enabled=False,
        leave_alone=True,
    )


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "PerformanceSnapshotDeviceScope",
    "PerformanceSnapshotTargetError",
    "PerformanceSnapshotTargetPlan",
    "build_performance_snapshot_target_plan",
    "format_performance_snapshot_target_error",
    "format_performance_snapshot_target_report",
]
