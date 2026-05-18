"""Passive readiness gate for dual-machine Live Snapshot bridge previews.

This module inspects inert dual-machine mock bridge messages and reports which
devices are mapping-ready for a future active sender. It does not import MIDI
libraries, open ports, send MIDI, request or receive SysEx, write SysEx, or
mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dual_machine_mock_bridge import (
    DualMachineMockBridge,
    capture_dual_machine_mock_messages,
)


@dataclass(frozen=True)
class DualMachineDeviceReadiness:
    """Per-device readiness within a dual-machine Live Snapshot preview."""

    device_key: str
    label: str
    active: bool
    source: str
    status: str
    reason: str
    message_count: int
    mapped_cc_count: int
    candidate_event_count: int


@dataclass(frozen=True)
class DualMachineLiveSnapshotReadiness:
    """Overall passive readiness for a dual-machine Live Snapshot preview."""

    target: str
    ready: bool
    reason: str
    combined_message_count: int
    ready_device_count: int
    blocked_device_count: int
    untouched_device_count: int
    devices: tuple[DualMachineDeviceReadiness, ...]


DEVICE_ORDER = (
    ("analog_rytm", "Analog Rytm MKII"),
    ("analog_four", "Analog Four MKII"),
)


def evaluate_dual_machine_live_snapshot_readiness(
    bridge: DualMachineMockBridge,
) -> DualMachineLiveSnapshotReadiness:
    """Evaluate mapping readiness for an existing passive bridge preview."""

    if not isinstance(bridge, DualMachineMockBridge):
        raise TypeError("bridge must be a DualMachineMockBridge")

    messages = capture_dual_machine_mock_messages(bridge).sent_messages
    devices = tuple(
        _device_readiness(bridge, messages, device_key, label) for device_key, label in DEVICE_ORDER
    )
    ready_devices = sum(1 for device in devices if device.status.startswith("ready"))
    blocked_devices = sum(1 for device in devices if device.status.startswith("blocked"))
    untouched_devices = sum(1 for device in devices if device.status == "untouched")
    ready = blocked_devices == 0 and any(device.active for device in devices)
    return DualMachineLiveSnapshotReadiness(
        target=bridge.target_plan.canonical_target,
        ready=ready,
        reason=_overall_reason(ready, devices),
        combined_message_count=len(messages),
        ready_device_count=ready_devices,
        blocked_device_count=blocked_devices,
        untouched_device_count=untouched_devices,
        devices=devices,
    )


def format_dual_machine_live_snapshot_readiness_report(
    readiness: DualMachineLiveSnapshotReadiness,
) -> list[str]:
    """Format a deterministic passive dual-machine readiness report."""

    lines = [
        "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report",
        f"Target: {readiness.target}",
        f"Ready: {readiness.ready}",
        f"Reason: {readiness.reason}",
        f"Combined mock messages: {readiness.combined_message_count}",
        (
            "Device counts: "
            f"ready {readiness.ready_device_count} / "
            f"blocked {readiness.blocked_device_count} / "
            f"untouched {readiness.untouched_device_count}"
        ),
        "Device readiness:",
    ]
    lines.extend(_format_device_line(device) for device in readiness.devices)
    lines.extend(
        [
            "Mapping policy:",
            "- readiness gate only",
            "- mapped CC mock messages may proceed only through a separate active sender gate",
            "- saved-offset candidate events block hardware sending",
            "- candidate_unverified events do not claim CC mappings",
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


def format_dual_machine_live_snapshot_readiness_error(message: str) -> list[str]:
    """Format deterministic passive dual-machine readiness errors."""

    return [
        "RytmRandomizer passive Dual-Machine Live Snapshot Readiness Report",
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


def _device_readiness(
    bridge: DualMachineMockBridge,
    messages,
    device_key: str,
    label: str,
) -> DualMachineDeviceReadiness:
    active = device_key in bridge.target_plan.active_device_keys
    source = bridge.rytm_source if device_key == "analog_rytm" else bridge.analog_four_source
    device_messages = tuple(message for message in messages if message.metadata["device"] == label)
    mapped_cc_count = sum(1 for message in device_messages if message.type == "cc")
    candidate_count = sum(
        1 for message in device_messages if message.type == "saved_offset_candidate"
    )

    if not active:
        return _readiness(
            device_key,
            label,
            active,
            source,
            "untouched",
            "target_scope_leave_alone",
            0,
            0,
            0,
        )
    if candidate_count:
        return _readiness(
            device_key,
            label,
            active,
            source,
            "blocked_candidate_unverified",
            "candidate_unverified_no_cc_mapping",
            len(device_messages),
            mapped_cc_count,
            candidate_count,
        )
    if not device_messages:
        return _readiness(
            device_key,
            label,
            active,
            source,
            "blocked_no_mapped_messages",
            "no_mapped_messages_available",
            0,
            0,
            0,
        )
    if device_key == "analog_four" and source == "safe starter CC plan":
        return _readiness(
            device_key,
            label,
            active,
            source,
            "ready_safe_starter_cc",
            "validated_smoke_ccs",
            len(device_messages),
            mapped_cc_count,
            candidate_count,
        )
    return _readiness(
        device_key,
        label,
        active,
        source,
        "ready_mapped_cc",
        "mapped_snapshot_cc_plan",
        len(device_messages),
        mapped_cc_count,
        candidate_count,
    )


def _readiness(
    device_key: str,
    label: str,
    active: bool,
    source: str,
    status: str,
    reason: str,
    message_count: int,
    mapped_cc_count: int,
    candidate_event_count: int,
) -> DualMachineDeviceReadiness:
    return DualMachineDeviceReadiness(
        device_key=device_key,
        label=label,
        active=active,
        source=source,
        status=status,
        reason=reason,
        message_count=message_count,
        mapped_cc_count=mapped_cc_count,
        candidate_event_count=candidate_event_count,
    )


def _overall_reason(
    ready: bool,
    devices: tuple[DualMachineDeviceReadiness, ...],
) -> str:
    if ready:
        return "all_active_devices_mapping_ready"
    if any(device.status == "blocked_candidate_unverified" for device in devices):
        return "blocked_by_unverified_candidates"
    return "blocked_by_missing_mapped_messages"


def _format_device_line(device: DualMachineDeviceReadiness) -> str:
    scope = "active" if device.active else "untouched"
    return (
        f"- {device.label}: {scope} / {device.source} / {device.status} / "
        f"messages {device.message_count} / mapped CC {device.mapped_cc_count} / "
        f"candidate events {device.candidate_event_count} ({device.reason})"
    )


__all__ = [
    "DualMachineDeviceReadiness",
    "DualMachineLiveSnapshotReadiness",
    "evaluate_dual_machine_live_snapshot_readiness",
    "format_dual_machine_live_snapshot_readiness_error",
    "format_dual_machine_live_snapshot_readiness_report",
]
