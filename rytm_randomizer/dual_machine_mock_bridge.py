"""Passive Rytm + Analog Four mock performance bridge.

This module combines the Rytm saved-snapshot mutation planner with a conservative
Analog Four safe-starter CC plan. It captures intended messages into
``MockMidiSender`` only. It does not import MIDI libraries, open ports, send
real MIDI, request or write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .mock_midi import MockMidiSender, build_cc_message
from .snapshot_mutation_planner import (
    SnapshotMutationPlan,
    build_snapshot_mutation_plan_from_file,
    format_snapshot_mutation_plan_error,
)

PAD_COUNT = 12
A4_TRACK_COUNT = 4


@dataclass(frozen=True)
class AnalogFourStarterChange:
    """One safe-starter Analog Four CC change for mock planning."""

    track: int
    midi_channel: int
    wire_channel: int
    role_label: str
    parameter_name: str
    cc: int
    value: int


@dataclass(frozen=True)
class AnalogFourTrackPlan:
    """Mock-only A4 starter plan for one track."""

    track: int
    midi_channel: int
    wire_channel: int
    role_label: str
    changes: tuple[AnalogFourStarterChange, ...]


@dataclass(frozen=True)
class DualMachineMockBridge:
    """Combined passive bridge for Rytm snapshot changes and A4 starter changes."""

    rytm_source_path: str
    rytm_source: str
    analog_four_source: str
    depth: str
    rytm_plan: SnapshotMutationPlan
    analog_four_tracks: tuple[AnalogFourTrackPlan, ...]

    @property
    def rytm_message_count(self) -> int:
        return self.rytm_plan.planned_change_count

    @property
    def analog_four_track_count(self) -> int:
        return len(self.analog_four_tracks)

    @property
    def analog_four_message_count(self) -> int:
        return sum(len(track.changes) for track in self.analog_four_tracks)

    @property
    def combined_message_count(self) -> int:
        return self.rytm_message_count + self.analog_four_message_count


def build_dual_machine_mock_bridge(
    rytm_sysex_path: str | Path,
    *,
    slot: int,
    depth: str,
) -> DualMachineMockBridge:
    """Build the passive combined mock bridge from a saved Rytm kit."""

    rytm_plan = build_snapshot_mutation_plan_from_file(
        rytm_sysex_path,
        slot=slot,
        depth=depth,
    )
    return DualMachineMockBridge(
        rytm_source_path=str(rytm_sysex_path),
        rytm_source="saved-kit snapshot",
        analog_four_source="safe starter CC plan",
        depth=depth,
        rytm_plan=rytm_plan,
        analog_four_tracks=build_analog_four_safe_starter_plan(),
    )


def build_analog_four_safe_starter_plan() -> tuple[AnalogFourTrackPlan, ...]:
    """Build a conservative A4 Track 1-4 CC starter plan."""

    roles = {
        1: "bass / low tonal anchor",
        2: "stab / sequence pressure",
        3: "pad / drone / atmosphere",
        4: "FX / noise / transition",
    }
    filter_values = {
        1: 112,
        2: 104,
        3: 96,
        4: 88,
    }
    tracks = []
    for track in range(1, A4_TRACK_COUNT + 1):
        midi_channel = track
        wire_channel = track - 1
        role_label = roles[track]
        changes = (
            AnalogFourStarterChange(
                track=track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=role_label,
                parameter_name="Filter 1 Frequency",
                cc=18,
                value=filter_values[track],
            ),
            AnalogFourStarterChange(
                track=track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=role_label,
                parameter_name="Amp Pan",
                cc=10,
                value=64,
            ),
        )
        tracks.append(
            AnalogFourTrackPlan(
                track=track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=role_label,
                changes=changes,
            )
        )
    return tuple(tracks)


def capture_dual_machine_mock_messages(bridge: DualMachineMockBridge) -> MockMidiSender:
    """Capture the combined bridge stream in an inert mock sender."""

    sender = MockMidiSender()
    for pad in bridge.rytm_plan.pads:
        for change in pad.changes:
            sender.send(
                build_cc_message(
                    channel=change.midi_channel - 1,
                    control=change.cc,
                    value=change.planned_value,
                    metadata={
                        "device": "Analog Rytm MKII",
                        "pad": change.pad,
                        "midi_channel": change.midi_channel,
                        "machine": change.machine_label,
                        "parameter": change.parameter_name,
                        "baseline_value": change.baseline_value,
                        "planned_value": change.planned_value,
                        "delta": change.delta,
                        "source": "saved-kit snapshot",
                    },
                )
            )
    for track in bridge.analog_four_tracks:
        for change in track.changes:
            sender.send(
                build_cc_message(
                    channel=change.wire_channel,
                    control=change.cc,
                    value=change.value,
                    metadata={
                        "device": "Analog Four MKII",
                        "track": change.track,
                        "midi_channel": change.midi_channel,
                        "role": change.role_label,
                        "parameter": change.parameter_name,
                        "baseline_type": "safe_starter",
                        "planned_value": change.value,
                        "source": "safe starter CC plan",
                    },
                )
            )
    return sender


def format_dual_machine_mock_bridge_report(bridge: DualMachineMockBridge) -> list[str]:
    """Format a deterministic passive dual-machine bridge report."""

    lines = [
        "RytmRandomizer passive Dual-Machine Mock Bridge Report",
        f"Rytm source path: {bridge.rytm_source_path}",
        f"Rytm source: {bridge.rytm_source}",
        f"Rytm kit: {bridge.rytm_plan.kit_name or '<blank>'}",
        f"Rytm slot: {bridge.rytm_plan.slot_number}",
        f"Depth: {bridge.depth}",
        f"Rytm planned pads: {bridge.rytm_plan.planned_pad_count} / {PAD_COUNT}",
        f"Rytm mock messages: {bridge.rytm_message_count}",
        f"Analog Four source: {bridge.analog_four_source}",
        f"Analog Four tracks: {bridge.analog_four_track_count} / {A4_TRACK_COUNT}",
        f"Analog Four mock messages: {bridge.analog_four_message_count}",
        f"Combined mock messages: {bridge.combined_message_count}",
        "Device plans:",
    ]
    for pad in bridge.rytm_plan.pads:
        if not pad.changes:
            continue
        lines.append(
            f"- Rytm Pad {pad.pad} / {pad.machine_label}: "
            f"{len(pad.changes)} message(s)"
        )
    for track in bridge.analog_four_tracks:
        lines.append(
            f"- Analog Four Track {track.track} / {track.role_label}: "
            f"{len(track.changes)} message(s)"
        )
    lines.append("Mock message preview:")
    for message in capture_dual_machine_mock_messages(bridge).sent_messages:
        lines.append(_format_message_preview(message))
    lines.extend(
        [
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


def format_dual_machine_mock_bridge_error(path: str | Path, message: str) -> list[str]:
    """Format a deterministic passive dual-machine bridge error."""

    lines = format_snapshot_mutation_plan_error(path, message)
    lines[0] = "RytmRandomizer passive Dual-Machine Mock Bridge Report"
    return lines


def _format_message_preview(message) -> str:
    metadata = message.metadata
    if metadata.get("device") == "Analog Rytm MKII":
        return (
            f"- Rytm Pad {metadata['pad']} / {metadata['machine']} / "
            f"{metadata['parameter']}: CC{message.control} -> {message.value}"
        )
    return (
        f"- Analog Four Track {metadata['track']} / {metadata['role']} / "
        f"{metadata['parameter']}: CC{message.control} -> {message.value}"
    )


__all__ = [
    "AnalogFourStarterChange",
    "AnalogFourTrackPlan",
    "DualMachineMockBridge",
    "build_analog_four_safe_starter_plan",
    "build_dual_machine_mock_bridge",
    "capture_dual_machine_mock_messages",
    "format_dual_machine_mock_bridge_error",
    "format_dual_machine_mock_bridge_report",
]
