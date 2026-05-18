"""Passive 12-pad Analog Rytm runtime contract from style intent.

This module wraps the existing Rytm engine-cycle and starter-profile planners
into one runtime-facing mock plan. It does not import MIDI libraries, open
ports, send real MIDI, receive SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..mock_midi import MockMidiSender, build_cc_message
from .rytm_engine_cycle_plan import build_rytm_engine_cycle_plan
from .rytm_engine_cycle_starter_profiles import (
    RytmEngineCycleStarterEvent,
    RytmEngineCycleStarterPlan,
    build_rytm_engine_cycle_starter_plan,
)


@dataclass(frozen=True)
class TwelvePadRytmRuntimeEvent:
    """One passive runtime CC event for a Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    machine_key: str
    machine_label: str
    machine_value: int
    support_status: str
    event_role: str
    parameter_name: str
    cc: int
    value: int
    source: str
    sends_real_midi: bool = False


@dataclass(frozen=True)
class TwelvePadRytmRuntimePadPlan:
    """Runtime event plan for one Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    machine_key: str
    machine_label: str
    machine_value: int
    support_status: str
    source_starter_status: str
    events: tuple[TwelvePadRytmRuntimeEvent, ...]


@dataclass(frozen=True)
class TwelvePadRytmRuntimePlan:
    """Passive 12-pad Rytm runtime plan from style intent."""

    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    starter_profile_key: str
    starter_profile_label: str
    starter_profile_description: str
    include_engine_source_starters: bool
    pads: tuple[TwelvePadRytmRuntimePadPlan, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def blocked_pad_count(self) -> int:
        return 0

    @property
    def source_starter_covered_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.source_starter_status == "covered")

    @property
    def source_starter_skipped_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.source_starter_status != "covered")

    @property
    def event_count(self) -> int:
        return sum(len(pad.events) for pad in self.pads)

    @property
    def machine_select_event_count(self) -> int:
        return self._count_role("machine_select")

    @property
    def engine_source_event_count(self) -> int:
        return self._count_role("engine_source_parameter")

    @property
    def starter_parameter_event_count(self) -> int:
        return self._count_role("starter_parameter")

    def _count_role(self, event_role: str) -> int:
        return sum(
            1 for pad in self.pads for event in pad.events if event.event_role == event_role
        )


def build_twelve_pad_rytm_runtime_plan(
    style_prompt: str,
    *,
    discovery: float | None = None,
    profile: str | None = "auto",
    include_engine_source_starters: bool = True,
) -> TwelvePadRytmRuntimePlan:
    """Build a passive 12-pad Rytm runtime plan from style intent."""

    engine_plan = build_rytm_engine_cycle_plan(style_prompt, discovery=discovery)
    starter_plan = build_rytm_engine_cycle_starter_plan(
        engine_plan,
        profile=profile,
        include_engine_source_starters=include_engine_source_starters,
    )
    return _runtime_plan_from_starter_plan(
        starter_plan,
        include_engine_source_starters=include_engine_source_starters,
    )


def capture_twelve_pad_rytm_runtime_mock_messages(
    plan: TwelvePadRytmRuntimePlan,
) -> MockMidiSender:
    """Capture the runtime plan into an inert in-memory mock sender."""

    if not isinstance(plan, TwelvePadRytmRuntimePlan):
        raise TypeError("plan must be a TwelvePadRytmRuntimePlan")

    sender = MockMidiSender()
    for pad in plan.pads:
        for event in pad.events:
            sender.send(
                build_cc_message(
                    channel=event.wire_channel,
                    control=event.cc,
                    value=event.value,
                    metadata={
                        "source_kind": "twelve_pad_rytm_runtime",
                        "source": event.source,
                        "device": "Analog Rytm MKII",
                        "style_prompt": plan.style_prompt,
                        "discovery": plan.discovery,
                        "pad": event.pad,
                        "midi_channel": event.midi_channel,
                        "role_key": event.role_key,
                        "role_label": event.role_label,
                        "event_role": event.event_role,
                        "parameter": event.parameter_name,
                        "machine_key": event.machine_key,
                        "machine_label": event.machine_label,
                        "machine_value": event.machine_value,
                        "support_status": event.support_status,
                        "source_starter_status": pad.source_starter_status,
                        "starter_profile_key": plan.starter_profile_key,
                        "starter_profile_label": plan.starter_profile_label,
                        "mock_only": True,
                        "sends_real_midi": False,
                    },
                )
            )
    return sender


def format_twelve_pad_rytm_runtime_report(
    plan: TwelvePadRytmRuntimePlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive 12-pad Rytm runtime report."""

    if sender is None:
        sender = capture_twelve_pad_rytm_runtime_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Twelve Pad Rytm Runtime Report",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Starter profile: {plan.starter_profile_label} / {plan.starter_profile_key}",
        f"Profile behavior: {plan.starter_profile_description}",
        f"Planned pads: {plan.pad_count}",
        f"Blocked pads: {plan.blocked_pad_count}",
        f"Machine-select messages: {plan.machine_select_event_count}",
        f"Engine-source parameter messages: {plan.engine_source_event_count}",
        f"Starter parameter messages: {plan.starter_parameter_event_count}",
        f"Runtime messages: {len(sender.sent_messages)}",
        f"Source-starter covered pads: {plan.source_starter_covered_pad_count}",
        f"Source-starter skipped pads: {plan.source_starter_skipped_pad_count}",
        "Pad runtime plans:",
    ]
    for pad in plan.pads:
        lines.append(
            f"- Pad {pad.pad} / {pad.role_label} / {pad.machine_label}: "
            f"{len(pad.events)} message(s), source starters {pad.source_starter_status}"
        )
    lines.append("Mock MIDI stream:")
    if sender.sent_messages:
        lines.extend(_format_message_preview(message) for message in sender.sent_messages)
    else:
        lines.append("- no mock messages")
    lines.extend(
        [
            "Runtime policy:",
            "- machine select first, source starters second, common starters third",
            "- engine-source starters are enabled by default for this runtime report",
            "- generic SRC Slot labels are used where official source names are pending",
            "- existing guarded and armed engine-cycle senders are unchanged",
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


def format_twelve_pad_rytm_runtime_error(message: str) -> list[str]:
    """Format deterministic passive 12-pad Rytm runtime errors."""

    return [
        "RytmRandomizer passive Twelve Pad Rytm Runtime Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
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


def _runtime_plan_from_starter_plan(
    starter_plan: RytmEngineCycleStarterPlan,
    *,
    include_engine_source_starters: bool,
) -> TwelvePadRytmRuntimePlan:
    return TwelvePadRytmRuntimePlan(
        style_prompt=starter_plan.style_prompt,
        matched_profile_labels=starter_plan.matched_profile_labels,
        essence_tags=starter_plan.essence_tags,
        discovery=starter_plan.discovery,
        starter_profile_key=starter_plan.starter_profile_key,
        starter_profile_label=starter_plan.starter_profile_label,
        starter_profile_description=starter_plan.starter_profile_description,
        include_engine_source_starters=include_engine_source_starters,
        pads=tuple(
            _runtime_pad_from_starter_pad(
                pad,
                include_engine_source_starters=include_engine_source_starters,
            )
            for pad in starter_plan.pads
        ),
    )


def _runtime_pad_from_starter_pad(
    pad,
    *,
    include_engine_source_starters: bool,
) -> TwelvePadRytmRuntimePadPlan:
    return TwelvePadRytmRuntimePadPlan(
        pad=pad.pad,
        midi_channel=pad.midi_channel,
        wire_channel=pad.wire_channel,
        role_key=pad.role_key,
        role_label=pad.role_label,
        machine_key=pad.machine_key,
        machine_label=pad.machine_label,
        machine_value=pad.machine_value,
        support_status=pad.support_status,
        source_starter_status=_source_starter_status(
            pad,
            include_engine_source_starters=include_engine_source_starters,
        ),
        events=tuple(_runtime_event_from_starter_event(event) for event in pad.events),
    )


def _runtime_event_from_starter_event(
    event: RytmEngineCycleStarterEvent,
) -> TwelvePadRytmRuntimeEvent:
    return TwelvePadRytmRuntimeEvent(
        pad=event.pad,
        midi_channel=event.midi_channel,
        wire_channel=event.wire_channel,
        role_key=event.role_key,
        role_label=event.role_label,
        machine_key=event.machine_key,
        machine_label=event.machine_label,
        machine_value=event.machine_value,
        support_status=event.support_status,
        event_role=event.event_role,
        parameter_name=event.parameter_name,
        cc=event.cc,
        value=event.value,
        source=event.source,
    )


def _format_message_preview(message) -> str:
    metadata = message.metadata
    role = str(metadata["event_role"])
    if role == "machine_select":
        detail = f"CC{message.control} -> {message.value} / {metadata['machine_label']}"
    elif role in {"starter_parameter", "engine_source_parameter"}:
        detail = f"{metadata['parameter']} CC{message.control} -> {message.value}"
    else:
        detail = f"CC{message.control} -> {message.value}"
    return (
        f"- Pad {metadata['pad']} / ch {metadata['midi_channel']} "
        f"wire {message.channel} / {role} / {detail}"
    )


def _source_starter_status(
    pad,
    *,
    include_engine_source_starters: bool,
) -> str:
    if not include_engine_source_starters:
        return "disabled"
    if any(event.event_role == "engine_source_parameter" for event in pad.events):
        return "covered"
    return "not mapped"


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "TwelvePadRytmRuntimeEvent",
    "TwelvePadRytmRuntimePadPlan",
    "TwelvePadRytmRuntimePlan",
    "build_twelve_pad_rytm_runtime_plan",
    "capture_twelve_pad_rytm_runtime_mock_messages",
    "format_twelve_pad_rytm_runtime_error",
    "format_twelve_pad_rytm_runtime_report",
]
