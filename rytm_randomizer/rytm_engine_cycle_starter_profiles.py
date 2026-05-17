"""Passive Rytm engine-cycle starter-shaping profiles.

This module layers deterministic common filter/amp CC starter values onto the
existing 12-pad Rytm engine-cycle plan. It is mock-only planning code: it does
not import MIDI libraries, open ports, send MIDI, receive SysEx, write SysEx,
or mutate hardware.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .data import MACHINE_CC
from .mock_midi import MockMidiSender, build_cc_message
from .rytm_engine_cycle_plan import RytmEngineCyclePlan

COMMON_STARTER_PARAMETER_CCS: tuple[tuple[str, int], ...] = (
    ("FLT Frequency", 74),
    ("FLT Resonance", 75),
    ("FLT Type", 76),
    ("AMP Decay", 80),
    ("AMP Overdrive", 81),
    ("AMP Pan", 10),
)


@dataclass(frozen=True)
class RytmStarterParameter:
    """One common mapped CC/value pair for a Rytm starter profile."""

    parameter_name: str
    cc: int
    value: int


@dataclass(frozen=True)
class RytmStarterPadProfile:
    """One pad role inside a Rytm starter profile."""

    pad: int
    role_label: str
    parameters: tuple[RytmStarterParameter, ...]


@dataclass(frozen=True)
class RytmStarterProfile:
    """One named passive Rytm starter-shaping profile."""

    key: str
    label: str
    aliases: tuple[str, ...]
    description: str
    pads: tuple[RytmStarterPadProfile, ...]


@dataclass(frozen=True)
class RytmEngineCycleStarterEvent:
    """One planned mock CC event in the starter-shaping stream."""

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


@dataclass(frozen=True)
class RytmEngineCycleStarterPadPlan:
    """Starter-shaping plan for one Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    machine_key: str
    machine_label: str
    machine_value: int
    support_status: str
    events: tuple[RytmEngineCycleStarterEvent, ...]


@dataclass(frozen=True)
class RytmEngineCycleStarterPlan:
    """Passive engine-cycle starter-shaping plan for all 12 Rytm pads."""

    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    starter_profile_key: str
    starter_profile_label: str
    starter_profile_description: str
    pads: tuple[RytmEngineCycleStarterPadPlan, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def event_count(self) -> int:
        return sum(len(pad.events) for pad in self.pads)

    @property
    def machine_select_event_count(self) -> int:
        return sum(
            1
            for pad in self.pads
            for event in pad.events
            if event.event_role == "machine_select"
        )

    @property
    def starter_parameter_event_count(self) -> int:
        return sum(
            1
            for pad in self.pads
            for event in pad.events
            if event.event_role == "starter_parameter"
        )


def _parameter(name: str, cc: int, value: int) -> RytmStarterParameter:
    if not 0 <= value <= 127:
        raise ValueError(f"{name} value must be 0..127")
    return RytmStarterParameter(parameter_name=name, cc=cc, value=value)


def _pad(
    pad: int,
    role_label: str,
    values: tuple[int, int, int, int, int, int],
) -> RytmStarterPadProfile:
    return RytmStarterPadProfile(
        pad=pad,
        role_label=role_label,
        parameters=tuple(
            _parameter(name, cc, value)
            for (name, cc), value in zip(COMMON_STARTER_PARAMETER_CCS, values)
        ),
    )


def _pads(values_by_pad: tuple[tuple[int, int, int, int, int, int], ...]):
    role_labels = (
        "main kick foundation",
        "low percussion pressure",
        "metallic motif",
        "body accent",
        "closed hat pulse",
        "open hat wash",
        "rim click motion",
        "snare clap pressure",
        "tonal bell accent",
        "rolling percussion",
        "atmosphere texture",
        "wild discovery",
    )
    return tuple(
        _pad(pad, role_labels[pad - 1], values)
        for pad, values in enumerate(values_by_pad, start=1)
    )


RYTM_STARTER_PROFILES: tuple[RytmStarterProfile, ...] = (
    RytmStarterProfile(
        key="balanced",
        label="Balanced",
        aliases=("balanced", "default", "safe", "starter", "safe-starter"),
        description="Conservative all-purpose 12-pad common filter/amp starter values.",
        pads=_pads(
            (
                (42, 38, 4, 86, 20, 64),
                (50, 28, 4, 76, 18, 62),
                (92, 10, 2, 52, 20, 66),
                (48, 24, 4, 74, 16, 68),
                (112, 12, 1, 34, 10, 58),
                (116, 10, 1, 60, 10, 70),
                (104, 18, 1, 44, 14, 60),
                (82, 22, 3, 62, 20, 68),
                (98, 12, 2, 62, 14, 56),
                (74, 18, 3, 58, 16, 72),
                (118, 8, 1, 82, 8, 64),
                (112, 18, 1, 50, 22, 74),
            )
        ),
    ),
    RytmStarterProfile(
        key="birmingham-dark",
        label="Birmingham Dark",
        aliases=(
            "birmingham-dark",
            "birmingham_dark",
            "birmingham",
            "birmingham-techno",
            "dark-techno",
        ),
        description="Cold industrial pressure with tight hats and darker body lanes.",
        pads=_pads(
            (
                (28, 50, 4, 86, 22, 64),
                (32, 32, 4, 80, 20, 62),
                (96, 8, 2, 44, 24, 66),
                (36, 30, 4, 76, 18, 68),
                (108, 18, 1, 34, 14, 58),
                (112, 16, 1, 58, 12, 70),
                (102, 20, 1, 42, 18, 60),
                (78, 24, 3, 58, 22, 68),
                (98, 12, 2, 62, 16, 56),
                (64, 18, 3, 56, 18, 72),
                (116, 10, 1, 84, 10, 64),
                (118, 20, 1, 48, 24, 74),
            )
        ),
    ),
    RytmStarterProfile(
        key="detroit-classic",
        label="Detroit Classic",
        aliases=(
            "detroit-classic",
            "detroit_classic",
            "detroit",
            "classic-detroit",
            "classic-detroit-techno",
        ),
        description="More open percussion and bell lanes for classic machine funk.",
        pads=_pads(
            (
                (54, 26, 4, 88, 18, 64),
                (68, 20, 4, 78, 16, 60),
                (104, 8, 2, 62, 16, 70),
                (72, 18, 3, 76, 14, 66),
                (118, 10, 1, 38, 8, 58),
                (122, 8, 1, 66, 8, 72),
                (112, 12, 1, 48, 12, 60),
                (92, 18, 3, 66, 16, 68),
                (112, 8, 2, 78, 12, 56),
                (86, 14, 3, 64, 14, 72),
                (120, 6, 1, 94, 8, 64),
                (118, 14, 1, 58, 18, 74),
            )
        ),
    ),
    RytmStarterProfile(
        key="peak-time",
        label="Peak Time",
        aliases=("peak-time", "peak_time", "peak time", "peak", "big-room"),
        description="Brighter, punchier, and wider common shaping for high-energy sets.",
        pads=_pads(
            (
                (46, 42, 4, 90, 24, 64),
                (62, 34, 4, 82, 24, 60),
                (108, 14, 2, 50, 26, 68),
                (60, 28, 4, 80, 22, 70),
                (120, 18, 1, 30, 18, 58),
                (124, 16, 1, 56, 16, 70),
                (116, 20, 1, 38, 20, 60),
                (96, 24, 3, 56, 24, 68),
                (118, 12, 2, 64, 18, 56),
                (96, 20, 3, 54, 20, 72),
                (122, 10, 1, 78, 12, 64),
                (124, 22, 1, 44, 28, 74),
            )
        ),
    ),
)


def list_rytm_starter_profiles() -> tuple[RytmStarterProfile, ...]:
    """Return deterministic Rytm engine-cycle starter profiles."""

    return RYTM_STARTER_PROFILES


def get_rytm_starter_profile(key: str | None) -> RytmStarterProfile:
    """Resolve a starter profile key or alias."""

    normalized = _normalize_profile_key(key)
    for profile in RYTM_STARTER_PROFILES:
        aliases = tuple(_normalize_profile_key(alias) for alias in profile.aliases)
        if normalized == profile.key or normalized in aliases:
            return profile
    choices = ", ".join(profile.key for profile in RYTM_STARTER_PROFILES)
    raise ValueError(f"Unknown Rytm starter profile: {key}. Valid choices: {choices}")


def build_rytm_engine_cycle_starter_plan(
    engine_plan: RytmEngineCyclePlan,
    *,
    profile: str | RytmStarterProfile | None = "balanced",
) -> RytmEngineCycleStarterPlan:
    """Add common starter-shaping CC events to an engine-cycle plan."""

    if not isinstance(engine_plan, RytmEngineCyclePlan):
        raise TypeError("engine_plan must be a RytmEngineCyclePlan")
    starter_profile = (
        profile if isinstance(profile, RytmStarterProfile) else get_rytm_starter_profile(profile)
    )
    starter_pads = {pad.pad: pad for pad in starter_profile.pads}
    pads = []
    for pad_plan in engine_plan.pads:
        if not pad_plan.candidates:
            raise ValueError(f"Pad {pad_plan.pad} has no engine-cycle candidate")
        profile_pad = starter_pads.get(pad_plan.pad)
        if profile_pad is None:
            raise ValueError(
                f"Starter profile {starter_profile.key} has no Pad {pad_plan.pad} values"
            )
        candidate = pad_plan.top_candidate
        events = [
            RytmEngineCycleStarterEvent(
                pad=pad_plan.pad,
                midi_channel=pad_plan.midi_channel,
                wire_channel=pad_plan.wire_channel,
                role_key=pad_plan.role_key,
                role_label=pad_plan.role_label,
                machine_key=candidate.machine_key,
                machine_label=candidate.machine_label,
                machine_value=candidate.machine_value,
                support_status=candidate.support_status,
                event_role="machine_select",
                parameter_name="Machine Select",
                cc=MACHINE_CC,
                value=candidate.machine_value,
                source="engine cycle top candidate",
            )
        ]
        events.extend(
            RytmEngineCycleStarterEvent(
                pad=pad_plan.pad,
                midi_channel=pad_plan.midi_channel,
                wire_channel=pad_plan.wire_channel,
                role_key=pad_plan.role_key,
                role_label=pad_plan.role_label,
                machine_key=candidate.machine_key,
                machine_label=candidate.machine_label,
                machine_value=candidate.machine_value,
                support_status=candidate.support_status,
                event_role="starter_parameter",
                parameter_name=parameter.parameter_name,
                cc=parameter.cc,
                value=parameter.value,
                source="Rytm starter profile",
            )
            for parameter in profile_pad.parameters
        )
        pads.append(
            RytmEngineCycleStarterPadPlan(
                pad=pad_plan.pad,
                midi_channel=pad_plan.midi_channel,
                wire_channel=pad_plan.wire_channel,
                role_key=pad_plan.role_key,
                role_label=pad_plan.role_label,
                machine_key=candidate.machine_key,
                machine_label=candidate.machine_label,
                machine_value=candidate.machine_value,
                support_status=candidate.support_status,
                events=tuple(events),
            )
        )
    return RytmEngineCycleStarterPlan(
        style_prompt=engine_plan.style_prompt,
        matched_profile_labels=engine_plan.matched_profile_labels,
        essence_tags=engine_plan.essence_tags,
        discovery=engine_plan.discovery,
        starter_profile_key=starter_profile.key,
        starter_profile_label=starter_profile.label,
        starter_profile_description=starter_profile.description,
        pads=tuple(pads),
    )


def capture_rytm_engine_cycle_starter_mock_messages(
    plan: RytmEngineCycleStarterPlan,
) -> MockMidiSender:
    """Capture the starter-shaping stream in an inert mock sender."""

    if not isinstance(plan, RytmEngineCycleStarterPlan):
        raise TypeError("plan must be a RytmEngineCycleStarterPlan")

    sender = MockMidiSender()
    for pad in plan.pads:
        for event in pad.events:
            sender.send(
                build_cc_message(
                    channel=event.wire_channel,
                    control=event.cc,
                    value=event.value,
                    metadata={
                        "source_kind": "rytm_engine_cycle_starter_plan",
                        "source": event.source,
                        "device": "Analog Rytm MKII",
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
                        "starter_profile_key": plan.starter_profile_key,
                        "starter_profile_label": plan.starter_profile_label,
                        "mock_only": True,
                        "sends_real_midi": False,
                    },
                )
            )
    return sender


def format_rytm_engine_cycle_starter_plan_report(
    plan: RytmEngineCycleStarterPlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive starter-shaping plan report."""

    if sender is None:
        sender = capture_rytm_engine_cycle_starter_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Rytm Engine Cycle Starter Plan Report",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Starter profile: {plan.starter_profile_label} / {plan.starter_profile_key}",
        f"Profile behavior: {plan.starter_profile_description}",
        f"Planned pads: {plan.pad_count}",
        f"Machine-select messages: {plan.machine_select_event_count}",
        f"Starter parameter messages: {plan.starter_parameter_event_count}",
        f"Starter messages: {len(sender.sent_messages)}",
        "Pad starter plans:",
    ]
    for pad in plan.pads:
        lines.append(
            f"- Pad {pad.pad} / {pad.role_label} / {pad.machine_label}: "
            f"{len(pad.events)} message(s)"
        )
    lines.append("Mock MIDI stream:")
    if sender.sent_messages:
        for message in sender.sent_messages:
            lines.append(_format_message_preview(message))
    else:
        lines.append("- no mock messages")
    lines.extend(
        [
            "Starter policy:",
            "- machine select first, starter shaping second",
            "- common filter/amp starter values only",
            "- no engine-specific SRC tuning claimed yet",
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


def format_rytm_engine_cycle_starter_plan_error(message: str) -> list[str]:
    """Format deterministic passive starter-shaping plan errors."""

    return [
        "RytmRandomizer passive Rytm Engine Cycle Starter Plan Report",
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


def _format_message_preview(message) -> str:
    metadata = message.metadata
    role = str(metadata["event_role"])
    if role == "machine_select":
        detail = f"CC{message.control} -> {message.value} / {metadata['machine_label']}"
    else:
        detail = f"{metadata['parameter']} CC{message.control} -> {message.value}"
    return (
        f"- Pad {metadata['pad']} / ch {metadata['midi_channel']} "
        f"wire {message.channel} / {role} / {detail}"
    )


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


def _normalize_profile_key(key: str | None) -> str:
    if key is None:
        return "balanced"
    normalized = str(key).strip().lower()
    normalized = re.sub(r"[\s_]+", "-", normalized)
    return normalized


__all__ = [
    "COMMON_STARTER_PARAMETER_CCS",
    "RYTM_STARTER_PROFILES",
    "RytmEngineCycleStarterEvent",
    "RytmEngineCycleStarterPadPlan",
    "RytmEngineCycleStarterPlan",
    "RytmStarterPadProfile",
    "RytmStarterParameter",
    "RytmStarterProfile",
    "build_rytm_engine_cycle_starter_plan",
    "capture_rytm_engine_cycle_starter_mock_messages",
    "format_rytm_engine_cycle_starter_plan_error",
    "format_rytm_engine_cycle_starter_plan_report",
    "get_rytm_starter_profile",
    "list_rytm_starter_profiles",
]
