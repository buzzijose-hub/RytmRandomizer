"""Passive mock runtime for Analog Four saved-snapshot mutation plans.

This module converts unverified Analog Four saved-offset mutation candidates
into inert ``MockMidiSender`` events only. These events are not sendable CC
messages and do not claim a parameter mapping. The module does not import MIDI
libraries, open ports, send messages, request SysEx, receive live SysEx, write
SysEx, or mutate hardware.
"""

from __future__ import annotations

from pathlib import Path

from ..mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .snapshot_mutation_planner import (
    AnalogFourSnapshotMutationPlan,
    build_analog_four_snapshot_mutation_plan_from_file,
    format_analog_four_snapshot_mutation_plan_error,
)


def build_analog_four_snapshot_mock_runtime_from_file(
    path: str | Path,
    *,
    slot: int,
    depth: str,
) -> AnalogFourSnapshotMutationPlan:
    """Build a captured-value A4 mutation plan for mock runtime preview."""

    return build_analog_four_snapshot_mutation_plan_from_file(path, slot=slot, depth=depth)


def capture_analog_four_snapshot_mock_messages(
    plan: AnalogFourSnapshotMutationPlan,
) -> MockMidiSender:
    """Capture planned A4 saved-offset candidates into an inert mock sender."""

    if not isinstance(plan, AnalogFourSnapshotMutationPlan):
        raise TypeError("plan must be an AnalogFourSnapshotMutationPlan")

    sender = MockMidiSender()
    for track in plan.tracks:
        for change in track.changes:
            if change.cc is not None and change.parameter_name is not None:
                sender.send(
                    build_cc_message(
                        channel=change.wire_channel,
                        control=change.cc,
                        value=change.planned_value,
                        metadata={
                            **_base_change_metadata(track.name, change),
                            "parameter": change.parameter_name,
                            "cc_mapping_claimed": True,
                        },
                    )
                )
                continue
            sender.send(
                MidiMessage(
                    message_type="saved_offset_candidate",
                    channel=change.wire_channel,
                    control=change.relative_offset,
                    value=change.planned_value,
                    metadata={
                        **_base_change_metadata(track.name, change),
                        "cc_mapping_claimed": False,
                    },
                )
            )
    return sender


def format_analog_four_snapshot_mock_runtime_report(
    path: str | Path,
    plan: AnalogFourSnapshotMutationPlan,
    sender: MockMidiSender,
) -> list[str]:
    """Format a deterministic passive A4 snapshot mock-runtime report."""

    lines = [
        "RytmRandomizer passive Analog Four Snapshot Mock Runtime Report",
        f"Source path: {path}",
        f"Source slot: {plan.slot_number}",
        f"Kit: {plan.kit_name or '<blank>'}",
        f"Depth: {plan.depth}",
        f"Planned tracks: {plan.planned_track_count} / {plan.scanned_track_count}",
        f"Blocked tracks: {plan.blocked_track_count} / {plan.scanned_track_count}",
        f"Planned changes: {plan.planned_change_count}",
        f"Mock sender captured: {len(sender.sent_messages)} message(s)",
        "Track plans:",
    ]
    for track in plan.tracks:
        lines.append(
            f"- Track {track.track} / MIDI channel {track.midi_channel}: "
            f"{track.name or '<blank>'} / {track.mapping_status} / "
            f"{len(track.changes)} mock candidate event(s)"
        )

    if sender.sent_messages:
        lines.append("Mock saved-offset event stream:")
        lines.extend(_format_mock_message(message) for message in sender.sent_messages)

    lines.extend(
        [
            "Mutation policy:",
            "- captured-value relative",
            "- bounded deterministic deltas",
            *(_mapping_policy_lines(sender)),
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


def format_analog_four_snapshot_mock_runtime_error(
    path: str | Path,
    message: str,
) -> list[str]:
    """Format deterministic passive A4 snapshot mock-runtime errors."""

    lines = format_analog_four_snapshot_mutation_plan_error(path, message)
    lines[0] = "RytmRandomizer passive Analog Four Snapshot Mock Runtime Report"
    return lines


def _format_mock_message(message: MidiMessage) -> str:
    metadata = message.metadata
    if message.type == "cc":
        return (
            f"- Track {metadata['track']} ch {metadata['midi_channel']} "
            f"wire {metadata['wire_channel']} {metadata['track_name'] or '<blank>'} / "
            f"{metadata['parameter']}: CC{message.control} -> {message.value} "
            f"from offset +{metadata['saved_offset']} "
            f"({metadata['mapping_status']})"
        )
    return (
        f"- Track {metadata['track']} ch {metadata['midi_channel']} "
        f"wire {metadata['wire_channel']} {metadata['track_name'] or '<blank>'} / "
        f"Offset +{metadata['saved_offset']}: "
        f"{metadata['baseline_value']} -> {metadata['planned_value']} "
        f"(delta {metadata['delta']:+d}), {metadata['mapping_status']}"
    )


def _base_change_metadata(track_name: str, change) -> dict[str, object]:
    return {
        "source_kind": "analog_four_snapshot_mutation_plan",
        "device": "Analog Four MKII",
        "track": change.track,
        "midi_channel": change.midi_channel,
        "wire_channel": change.wire_channel,
        "track_name": track_name,
        "saved_offset": change.relative_offset,
        "word_index": change.word_index,
        "baseline_value": change.baseline_value,
        "planned_value": change.planned_value,
        "delta": change.delta,
        "mapping_status": change.mapping_status,
        "parameter_source": change.source,
        "mock_only": True,
        "sends_real_midi": False,
    }


def _mapping_policy_lines(sender: MockMidiSender) -> list[str]:
    has_cc = any(message.type == "cc" for message in sender.sent_messages)
    has_candidates = any(
        message.type == "saved_offset_candidate" for message in sender.sent_messages
    )
    if has_cc and has_candidates:
        return [
            "- verified saved offsets emit mapped CC mock events",
            "- unverified saved offsets remain candidate_unverified",
        ]
    if has_cc:
        return ["- verified saved offsets emit mapped CC mock events"]
    return [
        "- saved-offset candidate events only",
        "- candidate_unverified",
        "- no parameter names claimed",
        "- no CC mapping claimed",
    ]


__all__ = [
    "build_analog_four_snapshot_mock_runtime_from_file",
    "capture_analog_four_snapshot_mock_messages",
    "format_analog_four_snapshot_mock_runtime_error",
    "format_analog_four_snapshot_mock_runtime_report",
]
