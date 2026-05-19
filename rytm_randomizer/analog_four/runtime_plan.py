"""Passive Analog Four MKII runtime plan from safe starter profiles.

This module turns the manual-backed Analog Four starter profile data into an
inert mock runtime stream. It does not import MIDI libraries, open ports, send
MIDI, receive SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..mock_midi import MockMidiSender, build_cc_message
from .reference import get_analog_four_reference_source
from .starter_profiles import get_analog_four_starter_profile


@dataclass(frozen=True)
class AnalogFourRuntimeEvent:
    """One passive CC event for an Analog Four track."""

    track: int
    midi_channel: int
    wire_channel: int
    role_label: str
    parameter_name: str
    cc: int
    value: int
    sends_real_midi: bool = False


@dataclass(frozen=True)
class AnalogFourRuntimeTrack:
    """Runtime event plan for one Analog Four synth track."""

    track: int
    midi_channel: int
    wire_channel: int
    role_label: str
    events: tuple[AnalogFourRuntimeEvent, ...]


@dataclass(frozen=True)
class AnalogFourRuntimePlan:
    """Passive Analog Four runtime plan from a safe starter profile."""

    device: str
    source_url: str
    manual_path: str
    manual_os: str
    manual_midi_pages: str
    starter_profile_key: str
    starter_profile_label: str
    runtime_status: str
    tracks: tuple[AnalogFourRuntimeTrack, ...]

    @property
    def track_count(self) -> int:
        return len(self.tracks)

    @property
    def event_count(self) -> int:
        return sum(len(track.events) for track in self.tracks)


def build_analog_four_runtime_plan(profile: str | None = "balanced") -> AnalogFourRuntimePlan:
    """Build a passive Analog Four runtime plan from a named starter profile."""

    source = get_analog_four_reference_source()
    starter_profile = get_analog_four_starter_profile(profile)
    tracks = tuple(
        _build_runtime_track(track_profile) for track_profile in starter_profile.tracks
    )

    return AnalogFourRuntimePlan(
        device=source.device,
        source_url=source.url,
        manual_path=source.manual_path,
        manual_os=source.manual_os,
        manual_midi_pages=source.manual_midi_pages,
        starter_profile_key=starter_profile.key,
        starter_profile_label=starter_profile.label,
        runtime_status="passive_mock_ready",
        tracks=tracks,
    )


def capture_analog_four_runtime_mock_messages(
    plan: AnalogFourRuntimePlan,
) -> MockMidiSender:
    """Capture an Analog Four runtime plan into an inert in-memory sender."""

    if not isinstance(plan, AnalogFourRuntimePlan):
        raise TypeError("plan must be an AnalogFourRuntimePlan")

    sender = MockMidiSender()
    for track in plan.tracks:
        for event in track.events:
            sender.send(
                build_cc_message(
                    channel=event.wire_channel,
                    control=event.cc,
                    value=event.value,
                    metadata={
                        "source_kind": "analog_four_runtime_plan",
                        "device": plan.device,
                        "track": event.track,
                        "midi_channel": event.midi_channel,
                        "wire_channel": event.wire_channel,
                        "role": event.role_label,
                        "parameter": event.parameter_name,
                        "starter_profile_key": plan.starter_profile_key,
                        "starter_profile_label": plan.starter_profile_label,
                        "runtime_status": plan.runtime_status,
                        "mock_only": True,
                        "sends_real_midi": False,
                    },
                )
            )
    return sender


def format_analog_four_runtime_report(
    plan: AnalogFourRuntimePlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive Analog Four runtime report."""

    if sender is None:
        sender = capture_analog_four_runtime_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Analog Four Runtime Plan Report",
        f"Device: {plan.device}",
        f"Source: {plan.source_url}",
        f"Manual: {plan.manual_path}",
        f"Manual OS: {plan.manual_os}",
        f"Manual MIDI pages: {plan.manual_midi_pages}",
        f"Starter profile: {plan.starter_profile_label} / {plan.starter_profile_key}",
        f"Runtime status: {plan.runtime_status}",
        f"Tracks planned: {plan.track_count}",
        f"Runtime events: {plan.event_count}",
        f"Mock sender captured: {len(sender.sent_messages)} message(s)",
        "Track plans:",
    ]
    for track in plan.tracks:
        lines.append(
            f"- Track {track.track} / {track.role_label}: {len(track.events)} event(s)"
        )

    lines.append("Mock CC stream:")
    if sender.sent_messages:
        lines.extend(_format_message_preview(message) for message in sender.sent_messages)
    else:
        lines.append("- no mock messages")

    lines.extend(_safety_lines())
    return lines


def format_analog_four_runtime_error(message: str) -> list[str]:
    """Format deterministic passive Analog Four runtime errors."""

    return [
        "RytmRandomizer passive Analog Four Runtime Plan Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        *_safety_lines(),
    ]


def _build_runtime_track(track_profile) -> AnalogFourRuntimeTrack:
    midi_channel = track_profile.track
    wire_channel = midi_channel - 1
    return AnalogFourRuntimeTrack(
        track=track_profile.track,
        midi_channel=midi_channel,
        wire_channel=wire_channel,
        role_label=track_profile.role_label,
        events=tuple(
            AnalogFourRuntimeEvent(
                track=track_profile.track,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                role_label=track_profile.role_label,
                parameter_name=parameter.parameter_name,
                cc=parameter.cc,
                value=parameter.value,
            )
            for parameter in track_profile.parameters
        ),
    )


def _format_message_preview(message) -> str:
    metadata = message.metadata
    return (
        f"- Track {metadata['track']} ch {metadata['midi_channel']} "
        f"wire {metadata['wire_channel']} / {metadata['parameter']} "
        f"CC{message.control} -> {message.value}"
    )


def _safety_lines() -> list[str]:
    return [
        "Safety:",
        "- passive/read-only",
        "- passive/mock A4 runtime planning only",
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


__all__ = [
    "AnalogFourRuntimeEvent",
    "AnalogFourRuntimePlan",
    "AnalogFourRuntimeTrack",
    "build_analog_four_runtime_plan",
    "capture_analog_four_runtime_mock_messages",
    "format_analog_four_runtime_error",
    "format_analog_four_runtime_report",
]
