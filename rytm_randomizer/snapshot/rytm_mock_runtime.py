"""Passive mock MIDI bridge for Rytm saved-snapshot mutation plans.

This module converts already-built snapshot mutation plans into inert
``MockMidiSender`` messages only. It does not import MIDI libraries, open
ports, send real MIDI, request or write SysEx, or mutate hardware.
"""

from __future__ import annotations

from pathlib import Path

from ..mock_midi import MockMidiSender, build_cc_message
from .rytm_mutation_planner import (
    SnapshotMutationPlan,
    build_snapshot_mutation_plan_from_file,
    format_snapshot_mutation_plan_error,
    format_snapshot_readiness_summary,
)


def build_snapshot_mock_runtime_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
) -> SnapshotMutationPlan:
    """Build a captured-value mutation plan for mock runtime preview."""

    return build_snapshot_mutation_plan_from_file(path, slot=slot, depth=depth)


def capture_snapshot_mutation_mock_messages(plan: SnapshotMutationPlan) -> MockMidiSender:
    """Capture planned snapshot CC changes into an inert in-memory sender."""

    if not isinstance(plan, SnapshotMutationPlan):
        raise TypeError("plan must be a SnapshotMutationPlan")

    sender = MockMidiSender()
    for pad in plan.pads:
        for change in pad.changes:
            sender.send(
                build_cc_message(
                    channel=change.midi_channel - 1,
                    control=change.cc,
                    value=change.planned_value,
                    metadata={
                        "source_kind": "snapshot_mutation_plan",
                        "device": "Analog Rytm MKII",
                        "pad": change.pad,
                        "midi_channel": change.midi_channel,
                        "machine_label": change.machine_label,
                        "parameter": change.parameter_name,
                        "baseline_value": change.baseline_value,
                        "planned_value": change.planned_value,
                        "delta": change.delta,
                        "parameter_source": change.source,
                        "mock_only": True,
                        "sends_real_midi": False,
                    },
                )
            )
    return sender


def format_snapshot_mock_runtime_report(
    path: str | Path,
    plan: SnapshotMutationPlan,
    sender: MockMidiSender,
) -> list[str]:
    """Format a deterministic passive snapshot mock runtime report."""

    lines = [
        "RytmRandomizer passive Snapshot Mock Runtime Report",
        f"Source path: {path}",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Snapshot parameter map: {plan.snapshot_parameter_map_status}",
        f"Planned pads: {plan.planned_pad_count} / {plan.scanned_pad_count}",
        f"Blocked pads: {plan.blocked_pad_count} / {plan.scanned_pad_count}",
        format_snapshot_readiness_summary(plan),
        f"Planned changes: {plan.planned_change_count}",
        f"Mock sender captured: {len(sender.sent_messages)} message(s)",
        "Pad plans:",
    ]
    for pad in plan.pads:
        lines.append(
            f"- Pad {pad.pad} / MIDI channel {pad.midi_channel}: "
            f"{pad.machine_label} / {pad.baseline_status} / "
            f"{len(pad.changes)} mock message(s)"
        )

    if sender.sent_messages:
        lines.append("Mock MIDI stream:")
        lines.extend(_format_mock_message(message) for message in sender.sent_messages)

    lines.extend(
        [
            "Mutation policy:",
            "- captured-value relative",
            "- bounded deterministic deltas",
            "- no anchor loading",
            "- no machine switching",
            "Safety:",
            "- passive/read-only",
            "- mock sender only",
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


def format_snapshot_mock_runtime_error(path: str | Path, message: str) -> list[str]:
    """Format a deterministic passive snapshot mock runtime error."""

    lines = format_snapshot_mutation_plan_error(path, message)
    lines[0] = "RytmRandomizer passive Snapshot Mock Runtime Report"
    return lines


def _format_mock_message(message) -> str:
    metadata = message.metadata
    return (
        f"- Pad {metadata['pad']} ch {metadata['midi_channel']} wire {message.channel} "
        f"{metadata['machine_label']} / {metadata['parameter']}: "
        f"CC{message.control} -> {message.value} "
        f"(baseline {metadata['baseline_value']} / delta {metadata['delta']:+d})"
    )


__all__ = [
    "build_snapshot_mock_runtime_from_file",
    "capture_snapshot_mutation_mock_messages",
    "format_snapshot_mock_runtime_error",
    "format_snapshot_mock_runtime_report",
]
