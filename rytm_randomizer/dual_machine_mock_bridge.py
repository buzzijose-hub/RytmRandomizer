"""Passive Rytm + Analog Four mock performance bridge.

This module combines the Rytm saved-snapshot mutation planner with either a
conservative Analog Four safe-starter CC plan or unverified Analog Four
saved-snapshot candidates. It captures intended messages into ``MockMidiSender``
only. It does not import MIDI libraries, open ports, send real MIDI, request or
write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .analog_four_snapshot_mutation_planner import (
    AnalogFourSnapshotMutationPlan,
    build_analog_four_snapshot_mutation_plan_from_file,
)
from .analog_four_starter_profiles import (
    BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY,
    AnalogFourStarterProfile,
    get_analog_four_starter_profile,
)
from .mock_midi import MidiMessage, MockMidiSender, build_cc_message
from .performance_snapshot_target import (
    PerformanceSnapshotTargetPlan,
    build_performance_snapshot_target_plan,
)
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
class AnalogFourSnapshotBridgeChange:
    """One unverified A4 saved-offset change for mock bridge planning."""

    track: int
    midi_channel: int
    wire_channel: int
    track_name: str
    relative_offset: int
    word_index: int
    baseline_value: int
    planned_value: int
    delta: int
    mapping_status: str
    source: str


AnalogFourBridgeChange = AnalogFourStarterChange | AnalogFourSnapshotBridgeChange


@dataclass(frozen=True)
class AnalogFourTrackPlan:
    """Mock-only A4 plan for one track."""

    track: int
    midi_channel: int
    wire_channel: int
    role_label: str
    changes: tuple[AnalogFourBridgeChange, ...]


@dataclass(frozen=True)
class DualMachineMockBridge:
    """Combined passive bridge for Rytm snapshot changes and A4 mock changes."""

    rytm_source_path: str
    rytm_source: str
    analog_four_source: str
    depth: str
    rytm_plan: SnapshotMutationPlan
    analog_four_tracks: tuple[AnalogFourTrackPlan, ...]
    target_plan: PerformanceSnapshotTargetPlan
    analog_four_source_path: str | None = None
    analog_four_slot: int | None = None
    analog_four_kit_name: str | None = None
    analog_four_mapping_status: str | None = None
    analog_four_starter_profile_key: str | None = None
    analog_four_starter_profile_label: str | None = None

    @property
    def rytm_message_count(self) -> int:
        if not _is_device_active(self, "analog_rytm"):
            return 0
        return self.rytm_plan.planned_change_count

    @property
    def analog_four_track_count(self) -> int:
        if not _is_device_active(self, "analog_four"):
            return 0
        return len(self.analog_four_tracks)

    @property
    def analog_four_message_count(self) -> int:
        if not _is_device_active(self, "analog_four"):
            return 0
        return sum(len(track.changes) for track in self.analog_four_tracks)

    @property
    def combined_message_count(self) -> int:
        return self.rytm_message_count + self.analog_four_message_count


def build_dual_machine_mock_bridge(
    rytm_sysex_path: str | Path,
    *,
    slot: int,
    depth: str,
    target: str = "both",
    analog_four_sysex_path: str | Path | None = None,
    analog_four_slot: int | None = None,
    analog_four_profile: str | None = "balanced",
) -> DualMachineMockBridge:
    """Build the passive combined mock bridge from a saved Rytm kit."""

    if analog_four_sysex_path is None and analog_four_slot is not None:
        raise ValueError("Analog Four slot requires an Analog Four path")
    if analog_four_sysex_path is not None and analog_four_slot is None:
        raise ValueError("Analog Four path requires an Analog Four slot")

    target_plan = build_performance_snapshot_target_plan(target)
    rytm_plan = build_snapshot_mutation_plan_from_file(
        rytm_sysex_path,
        slot=slot,
        depth=depth,
    )
    starter_profile = get_analog_four_starter_profile(analog_four_profile)
    analog_four_source = "safe starter CC plan"
    analog_four_tracks = build_analog_four_safe_starter_plan(starter_profile.key)
    analog_four_kit_name = None
    analog_four_mapping_status = None
    analog_four_starter_profile_key = starter_profile.key
    analog_four_starter_profile_label = starter_profile.label
    if analog_four_sysex_path is not None:
        if starter_profile.key != BALANCED_ANALOG_FOUR_STARTER_PROFILE_KEY:
            raise ValueError(
                "Analog Four starter profile cannot be combined with Analog Four " "snapshot path"
            )
        analog_four_plan = build_analog_four_snapshot_mutation_plan_from_file(
            analog_four_sysex_path,
            slot=analog_four_slot,
            depth=depth,
        )
        analog_four_source = "saved-kit snapshot candidates"
        analog_four_tracks = build_analog_four_snapshot_bridge_plan(analog_four_plan)
        analog_four_kit_name = analog_four_plan.kit_name
        analog_four_mapping_status = "candidate_unverified"
        analog_four_starter_profile_key = None
        analog_four_starter_profile_label = None

    return DualMachineMockBridge(
        rytm_source_path=str(rytm_sysex_path),
        rytm_source="saved-kit snapshot",
        analog_four_source=analog_four_source,
        depth=depth,
        rytm_plan=rytm_plan,
        analog_four_tracks=analog_four_tracks,
        target_plan=target_plan,
        analog_four_source_path=str(analog_four_sysex_path) if analog_four_sysex_path else None,
        analog_four_slot=analog_four_slot,
        analog_four_kit_name=analog_four_kit_name,
        analog_four_mapping_status=analog_four_mapping_status,
        analog_four_starter_profile_key=analog_four_starter_profile_key,
        analog_four_starter_profile_label=analog_four_starter_profile_label,
    )


def build_analog_four_safe_starter_plan(
    profile: str | AnalogFourStarterProfile | None = "balanced",
) -> tuple[AnalogFourTrackPlan, ...]:
    """Build a conservative A4 Track 1-4 CC starter plan."""

    starter_profile = (
        profile
        if isinstance(profile, AnalogFourStarterProfile)
        else get_analog_four_starter_profile(profile)
    )
    tracks = []
    for track_profile in starter_profile.tracks:
        midi_channel = track_profile.track
        wire_channel = track_profile.track - 1
        changes = tuple(
            AnalogFourStarterChange(
                track=track_profile.track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=track_profile.role_label,
                parameter_name=parameter.parameter_name,
                cc=parameter.cc,
                value=parameter.value,
            )
            for parameter in track_profile.parameters
        )
        tracks.append(
            AnalogFourTrackPlan(
                track=track_profile.track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=track_profile.role_label,
                changes=changes,
            )
        )
    return tuple(tracks)


def build_analog_four_snapshot_bridge_plan(
    plan: AnalogFourSnapshotMutationPlan,
) -> tuple[AnalogFourTrackPlan, ...]:
    """Build mock-only A4 bridge plans from saved-snapshot candidates."""

    tracks = []
    for track in plan.tracks:
        changes = tuple(
            AnalogFourSnapshotBridgeChange(
                track=change.track,
                midi_channel=change.midi_channel,
                wire_channel=change.wire_channel,
                track_name=track.name,
                relative_offset=change.relative_offset,
                word_index=change.word_index,
                baseline_value=change.baseline_value,
                planned_value=change.planned_value,
                delta=change.delta,
                mapping_status=change.mapping_status,
                source=change.source,
            )
            for change in track.changes
        )
        tracks.append(
            AnalogFourTrackPlan(
                track=track.track,
                midi_channel=track.midi_channel,
                wire_channel=track.wire_channel,
                role_label=track.name or "<blank>",
                changes=changes,
            )
        )
    return tuple(tracks)


def capture_dual_machine_mock_messages(bridge: DualMachineMockBridge) -> MockMidiSender:
    """Capture the combined bridge stream in an inert mock sender."""

    sender = MockMidiSender()
    if _is_device_active(bridge, "analog_rytm"):
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
    if _is_device_active(bridge, "analog_four"):
        for track in bridge.analog_four_tracks:
            for change in track.changes:
                if isinstance(change, AnalogFourSnapshotBridgeChange):
                    sender.send(_build_analog_four_snapshot_message(change))
                else:
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
                                "starter_profile_key": (bridge.analog_four_starter_profile_key),
                                "starter_profile_label": (bridge.analog_four_starter_profile_label),
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
        f"Target: {bridge.target_plan.canonical_target}",
        f"Active devices: {_format_labels(bridge.target_plan.active_device_labels)}",
        f"Untouched devices: {_format_labels(bridge.target_plan.untouched_device_labels)}",
        f"Rytm planned pads: {_targeted_rytm_planned_pad_count(bridge)} / {PAD_COUNT}",
        f"Rytm mock messages: {bridge.rytm_message_count}",
        f"Analog Four source: {bridge.analog_four_source}",
        *(_analog_four_starter_profile_lines(bridge)),
        *(_analog_four_snapshot_header_lines(bridge)),
        f"Analog Four tracks: {bridge.analog_four_track_count} / {A4_TRACK_COUNT}",
        f"Analog Four mock messages: {bridge.analog_four_message_count}",
        f"Combined mock messages: {bridge.combined_message_count}",
        "Device plans:",
    ]
    if _is_device_active(bridge, "analog_rytm"):
        for pad in bridge.rytm_plan.pads:
            if not pad.changes:
                continue
            lines.append(
                f"- Rytm Pad {pad.pad} / {pad.machine_label}: " f"{len(pad.changes)} message(s)"
            )
    if _is_device_active(bridge, "analog_four"):
        for track in bridge.analog_four_tracks:
            lines.append(
                f"- Analog Four Track {track.track} / {track.role_label}: "
                f"{len(track.changes)} message(s)"
            )
    for device in bridge.target_plan.untouched_devices:
        lines.append(f"- {device.label}: untouched / no mock messages")
    lines.append("Mock message preview:")
    for message in capture_dual_machine_mock_messages(bridge).sent_messages:
        lines.append(_format_message_preview(message))
    if bridge.analog_four_mapping_status:
        lines.extend(
            [
                "Analog Four snapshot policy:",
                "- saved-offset candidate events only",
                f"- {bridge.analog_four_mapping_status}",
                "- no parameter names claimed",
                "- no CC mapping claimed",
            ]
        )
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
    if message.type == "saved_offset_candidate":
        return (
            f"- Analog Four Track {metadata['track']} / {metadata['role']} / "
            f"Offset +{metadata['saved_offset']}: "
            f"{metadata['baseline_value']} -> {metadata['planned_value']} "
            f"(delta {metadata['delta']:+d}), {metadata['mapping_status']}"
        )
    return (
        f"- Analog Four Track {metadata['track']} / {metadata['role']} / "
        f"{metadata['parameter']}: CC{message.control} -> {message.value}"
    )


def _build_analog_four_snapshot_message(
    change: AnalogFourSnapshotBridgeChange,
) -> MidiMessage:
    return MidiMessage(
        message_type="saved_offset_candidate",
        channel=change.wire_channel,
        control=change.relative_offset,
        value=change.planned_value,
        metadata={
            "device": "Analog Four MKII",
            "track": change.track,
            "midi_channel": change.midi_channel,
            "wire_channel": change.wire_channel,
            "role": change.track_name or "<blank>",
            "track_name": change.track_name,
            "saved_offset": change.relative_offset,
            "word_index": change.word_index,
            "baseline_value": change.baseline_value,
            "planned_value": change.planned_value,
            "delta": change.delta,
            "mapping_status": change.mapping_status,
            "parameter_source": change.source,
            "mock_only": True,
            "cc_mapping_claimed": False,
            "sends_real_midi": False,
        },
    )


def _analog_four_snapshot_header_lines(bridge: DualMachineMockBridge) -> list[str]:
    if not bridge.analog_four_source_path:
        return []
    return [
        f"Analog Four source path: {bridge.analog_four_source_path}",
        f"Analog Four slot: {bridge.analog_four_slot}",
        f"Analog Four kit: {bridge.analog_four_kit_name or '<blank>'}",
        f"Analog Four mapping: {bridge.analog_four_mapping_status}",
    ]


def _analog_four_starter_profile_lines(bridge: DualMachineMockBridge) -> list[str]:
    if bridge.analog_four_starter_profile_key is None:
        return []
    return [
        "Analog Four starter profile: "
        f"{bridge.analog_four_starter_profile_label} / "
        f"{bridge.analog_four_starter_profile_key}"
    ]


def _is_device_active(bridge: DualMachineMockBridge, device_key: str) -> bool:
    return device_key in bridge.target_plan.active_device_keys


def _targeted_rytm_planned_pad_count(bridge: DualMachineMockBridge) -> int:
    if not _is_device_active(bridge, "analog_rytm"):
        return 0
    return bridge.rytm_plan.planned_pad_count


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "AnalogFourSnapshotBridgeChange",
    "AnalogFourStarterChange",
    "AnalogFourTrackPlan",
    "DualMachineMockBridge",
    "build_analog_four_safe_starter_plan",
    "build_analog_four_snapshot_bridge_plan",
    "build_dual_machine_mock_bridge",
    "capture_dual_machine_mock_messages",
    "format_dual_machine_mock_bridge_error",
    "format_dual_machine_mock_bridge_report",
]
