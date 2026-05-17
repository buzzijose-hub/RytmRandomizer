"""Passive performance-mode metadata for future live snapshot behavior.

This module is intentionally read-only and hardware-free. It records the
startup mode semantics that future runtime work will wire into the interactive
shell, but importing it must never open MIDI ports, import real MIDI backends,
send messages, request SysEx data, or touch hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PerformanceModeKey = Literal["safe_anchors", "live_snapshot"]
CaptureStatus = Literal["not_requested", "capturing", "captured", "failed", "partial"]


@dataclass(frozen=True)
class PerformanceMode:
    """Operator-facing startup mode metadata."""

    key: PerformanceModeKey
    label: str
    menu_number: str
    description: str
    baseline_source: str
    return_target: str
    expected_pad_count: int
    requires_hardware_capture: bool
    continuous_tracking: bool


@dataclass(frozen=True)
class SnapshotState:
    """Small immutable readiness view for snapshot-backed mutation."""

    mode: PerformanceModeKey
    capture_status: CaptureStatus
    expected_pad_count: int
    captured_pad_count: int


@dataclass(frozen=True)
class MutationReadiness:
    """Whether mutation is allowed for the selected performance mode."""

    ready: bool
    reason: str


_PERFORMANCE_MODES: tuple[PerformanceMode, ...] = (
    PerformanceMode(
        key="safe_anchors",
        label="Safe Anchors",
        menu_number="1",
        description="Load validated app anchors, then mutate from them.",
        baseline_source="validated_app_anchors",
        return_target="validated_app_anchors",
        expected_pad_count=4,
        requires_hardware_capture=False,
        continuous_tracking=False,
    ),
    PerformanceMode(
        key="live_snapshot",
        label="Live Snapshot",
        menu_number="2",
        description="Capture the currently loaded Rytm kit, then mutate from that snapshot.",
        baseline_source="captured_loaded_kit",
        return_target="captured_loaded_kit",
        expected_pad_count=12,
        requires_hardware_capture=True,
        continuous_tracking=False,
    ),
)


def list_performance_modes() -> tuple[PerformanceMode, ...]:
    """Return the deterministic startup mode order."""

    return _PERFORMANCE_MODES


def format_performance_mode_prompt() -> list[str]:
    """Return the startup mode prompt lines from the design checkpoint."""

    lines = ["Select performance mode:"]
    for mode in _PERFORMANCE_MODES:
        lines.extend(("", f"{mode.menu_number} = {mode.label}", f"    {mode.description}"))
    lines.extend(("", "Mode:"))
    return lines


def evaluate_mutation_readiness(state: SnapshotState) -> MutationReadiness:
    """Return whether mutation may run for the current baseline state."""

    if state.mode == "safe_anchors":
        return MutationReadiness(True, "safe_anchors_ready")

    if state.capture_status == "failed":
        return MutationReadiness(False, "snapshot_capture_failed")

    if state.capture_status in ("not_requested", "capturing"):
        return MutationReadiness(False, "snapshot_not_captured")

    if state.capture_status == "partial" or state.captured_pad_count < state.expected_pad_count:
        return MutationReadiness(False, "snapshot_incomplete")

    if state.capture_status == "captured":
        return MutationReadiness(True, "snapshot_ready")

    return MutationReadiness(False, "snapshot_incomplete")


__all__ = [
    "CaptureStatus",
    "MutationReadiness",
    "PerformanceMode",
    "PerformanceModeKey",
    "SnapshotState",
    "evaluate_mutation_readiness",
    "format_performance_mode_prompt",
    "list_performance_modes",
]
