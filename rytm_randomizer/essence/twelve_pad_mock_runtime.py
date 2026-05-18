"""Mock-only 12-pad runtime contract for style-driven kit planning.

This module is passive and inert. It builds intended mock MIDI messages from
existing mapped V1.34 profile anchors only. It does not import MIDI libraries,
open ports, send real MIDI, request SysEx, write SysEx, or mutate hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..data import MACHINE_CC, PROFILES
from ..mock_midi import MockMidiSender, build_cc_message
from .machine_catalog import MachineCandidate, RoleAssignment, build_essence_role_plan
from .style_intent_profiles import StyleIntentRequest, build_style_intent_request


@dataclass(frozen=True)
class MockAnchorMessage:
    """One inert CC event in the mock 12-pad stream."""

    pad: int
    midi_channel: int
    wire_channel: int
    label: str
    control: int
    value: int
    message_role: str


@dataclass(frozen=True)
class TwelvePadMockPadPlan:
    """Mock runtime plan for one pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    preferred_machine_label: str
    preferred_machine_support: str
    selected_machine_key: str
    selected_machine_label: str
    selected_machine_support: str
    profile_key: str
    machine_value: int | None
    selection_status: str
    selection_reason: str
    messages: tuple[MockAnchorMessage, ...]


@dataclass(frozen=True)
class TwelvePadMockRuntimePlan:
    """Resolved mock 12-pad runtime plan for a style prompt."""

    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    pads: tuple[TwelvePadMockPadPlan, ...]

    @property
    def planned_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.selection_status != "blocked")

    @property
    def blocked_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.selection_status == "blocked")

    @property
    def fallback_pad_count(self) -> int:
        return sum(1 for pad in self.pads if pad.selection_status == "mapped_fallback")

    @property
    def message_count(self) -> int:
        return sum(len(pad.messages) for pad in self.pads)


MACHINE_PROFILE_KEYS: dict[str, str] = {
    "bd_sharp": "1",
    "bd_hard": "2",
    "bd_classic": "3",
    "bd_acoustic": "4",
    "sy_raw": "5",
    "bd_fm": "6",
    "bd_plastic": "7",
    "bd_silky": "8",
    "sd_hard": "9",
    "sd_classic": "10",
    "sd_fm": "11",
}


def build_twelve_pad_mock_runtime_plan(
    style_prompt: str,
    *,
    discovery: float | None = None,
) -> TwelvePadMockRuntimePlan:
    """Build a mapped-only mock runtime plan from broad style intent."""

    request = build_style_intent_request(style_prompt, discovery=discovery)
    role_plan = build_essence_role_plan(
        essence_tags=request.tags,
        discovery=request.discovery,
        candidates_per_role=8,
    )
    pads = tuple(_build_pad_plan(request, assignment) for assignment in role_plan)
    return TwelvePadMockRuntimePlan(
        style_prompt=request.prompt,
        matched_profile_labels=tuple(profile.label for profile in request.matched_profiles),
        essence_tags=request.tags,
        discovery=request.discovery,
        pads=pads,
    )


def capture_twelve_pad_mock_messages(plan: TwelvePadMockRuntimePlan) -> MockMidiSender:
    """Capture the mock runtime stream in an inert in-memory sender."""

    sender = MockMidiSender()
    for pad in plan.pads:
        for message in pad.messages:
            sender.send(
                build_cc_message(
                    channel=message.wire_channel,
                    control=message.control,
                    value=message.value,
                    metadata={
                        "pad": message.pad,
                        "midi_channel": message.midi_channel,
                        "role": pad.role_key,
                        "role_label": pad.role_label,
                        "machine": pad.selected_machine_key,
                        "machine_label": pad.selected_machine_label,
                        "message_role": message.message_role,
                        "parameter": "" if message.message_role == "machine" else message.label,
                    },
                )
            )
    return sender


def format_twelve_pad_mock_runtime_report(plan: TwelvePadMockRuntimePlan) -> list[str]:
    """Format a deterministic passive 12-pad mock runtime report."""

    lines = [
        "RytmRandomizer passive Twelve Pad Mock Runtime Report",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        (
            "Pad counts: "
            f"planned {plan.planned_pad_count} / "
            f"blocked {plan.blocked_pad_count} / "
            f"fallback {plan.fallback_pad_count}"
        ),
        f"Mock sender captured: {plan.message_count} message(s)",
        "12-pad mock runtime plan:",
    ]
    for pad in plan.pads:
        fallback_text = ""
        if pad.selection_status == "mapped_fallback":
            fallback_text = (
                f" / preferred {pad.preferred_machine_label} "
                f"[{pad.preferred_machine_support}] -> selected "
                f"{pad.selected_machine_label} [{pad.selected_machine_support}]"
            )
        lines.append(
            f"- Pad {pad.pad} / MIDI channel {pad.midi_channel} / "
            f"{pad.role_label}: {pad.selected_machine_label} "
            f"(machine CC15 -> {pad.machine_value})"
            f"{fallback_text}"
        )
    lines.append("Mock MIDI stream:")
    for pad in plan.pads:
        lines.extend(_format_mock_message(message) for message in pad.messages)
    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- mock sender only",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_twelve_pad_mock_runtime_error(message: str) -> list[str]:
    """Format a deterministic passive mock runtime error."""

    return [
        "RytmRandomizer passive Twelve Pad Mock Runtime Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- mock sender only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no hardware required",
    ]


def _build_pad_plan(
    request: StyleIntentRequest,
    assignment: RoleAssignment,
) -> TwelvePadMockPadPlan:
    preferred = assignment.candidates[0]
    selected = _first_mapped_candidate(assignment.candidates)
    if selected is None:
        return _blocked_pad_plan(assignment, preferred)

    selected_profile_key = MACHINE_PROFILE_KEYS[selected.machine.key]
    profile = PROFILES[selected_profile_key]
    selection_status = "planned"
    selection_reason = "preferred_mapped_machine"
    if selected.machine.key != preferred.machine.key:
        selection_status = "mapped_fallback"
        selection_reason = "preferred_future_machine_needs_manual_mapping"

    midi_channel = assignment.pad
    wire_channel = midi_channel - 1
    return TwelvePadMockPadPlan(
        pad=assignment.pad,
        midi_channel=midi_channel,
        wire_channel=wire_channel,
        role_key=assignment.role.key,
        role_label=assignment.role.label,
        preferred_machine_label=preferred.machine.label,
        preferred_machine_support=_support_label(preferred),
        selected_machine_key=selected.machine.key,
        selected_machine_label=selected.machine.label,
        selected_machine_support=_support_label(selected),
        profile_key=selected_profile_key,
        machine_value=profile["machine_value"],
        selection_status=selection_status,
        selection_reason=selection_reason,
        messages=_anchor_messages(assignment, profile),
    )


def _blocked_pad_plan(
    assignment: RoleAssignment,
    preferred: MachineCandidate,
) -> TwelvePadMockPadPlan:
    midi_channel = assignment.pad
    return TwelvePadMockPadPlan(
        pad=assignment.pad,
        midi_channel=midi_channel,
        wire_channel=midi_channel - 1,
        role_key=assignment.role.key,
        role_label=assignment.role.label,
        preferred_machine_label=preferred.machine.label,
        preferred_machine_support=_support_label(preferred),
        selected_machine_key="",
        selected_machine_label="none",
        selected_machine_support="",
        profile_key="",
        machine_value=None,
        selection_status="blocked",
        selection_reason="no_mapped_machine_candidate",
        messages=(),
    )


def _anchor_messages(
    assignment: RoleAssignment,
    profile: dict,
) -> tuple[MockAnchorMessage, ...]:
    midi_channel = assignment.pad
    wire_channel = midi_channel - 1
    messages = [
        MockAnchorMessage(
            pad=assignment.pad,
            midi_channel=midi_channel,
            wire_channel=wire_channel,
            label="machine",
            control=MACHINE_CC,
            value=profile["machine_value"],
            message_role="machine",
        )
    ]
    anchor = profile["anchor"]
    params = profile["params"]
    for name in profile["order"]:
        if name not in anchor:
            continue
        messages.append(
            MockAnchorMessage(
                pad=assignment.pad,
                midi_channel=midi_channel,
                wire_channel=wire_channel,
                label=name,
                control=params[name],
                value=anchor[name],
                message_role="anchor_param",
            )
        )
    return tuple(messages)


def _first_mapped_candidate(
    candidates: tuple[MachineCandidate, ...],
) -> MachineCandidate | None:
    for candidate in candidates:
        if (
            candidate.machine.support_status == "mutable_v134"
            and candidate.machine.key in MACHINE_PROFILE_KEYS
        ):
            return candidate
    return None


def _support_label(candidate: MachineCandidate) -> str:
    return "mutable" if candidate.machine.support_status == "mutable_v134" else "future"


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


def _format_mock_message(message: MockAnchorMessage) -> str:
    return (
        f"- Pad {message.pad} ch {message.midi_channel} wire {message.wire_channel} "
        f"{message.label}: CC{message.control} -> {message.value}"
    )


__all__ = [
    "MockAnchorMessage",
    "TwelvePadMockPadPlan",
    "TwelvePadMockRuntimePlan",
    "build_twelve_pad_mock_runtime_plan",
    "capture_twelve_pad_mock_messages",
    "format_twelve_pad_mock_runtime_error",
    "format_twelve_pad_mock_runtime_report",
]
