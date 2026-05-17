"""Passive 12-pad Rytm engine-cycle planner.

This module ranks style-driven Rytm machine candidates and captures a mock-only
CC15 stream for the top candidate on each pad. It does not import MIDI
libraries, open ports, send real MIDI, receive SysEx, write SysEx, or mutate
hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from .data import MACHINE_CC
from .machine_catalog import MachineCandidate, build_essence_role_plan
from .mock_midi import MockMidiSender, build_cc_message
from .style_intent_profiles import build_style_intent_request

MAX_CANDIDATES_PER_PAD = 4


@dataclass(frozen=True)
class RytmEngineCycleCandidate:
    """One ranked Rytm machine candidate for a 12-pad engine cycle."""

    rank: int
    machine_key: str
    machine_label: str
    machine_value: int
    family: str
    support_status: str
    score: float
    matched_tags: tuple[str, ...]


@dataclass(frozen=True)
class RytmEngineCyclePadPlan:
    """Engine-cycle candidates for one Analog Rytm pad."""

    pad: int
    midi_channel: int
    wire_channel: int
    role_key: str
    role_label: str
    candidates: tuple[RytmEngineCycleCandidate, ...]

    @property
    def top_candidate(self) -> RytmEngineCycleCandidate:
        if not self.candidates:
            raise ValueError("pad has no engine-cycle candidates")
        return self.candidates[0]


@dataclass(frozen=True)
class RytmEngineCyclePlan:
    """Passive style-driven engine-cycle plan for all 12 Rytm pads."""

    style_prompt: str
    matched_profile_labels: tuple[str, ...]
    essence_tags: tuple[str, ...]
    discovery: float
    pads: tuple[RytmEngineCyclePadPlan, ...]

    @property
    def pad_count(self) -> int:
        return len(self.pads)

    @property
    def top_candidate_count(self) -> int:
        return sum(1 for pad in self.pads if pad.candidates)

    @property
    def no_candidate_count(self) -> int:
        return sum(1 for pad in self.pads if not pad.candidates)

    @property
    def mock_message_count(self) -> int:
        return self.top_candidate_count


def build_rytm_engine_cycle_plan(
    style_prompt: str,
    *,
    discovery: float | None = None,
) -> RytmEngineCyclePlan:
    """Build a passive engine-cycle plan from a style prompt."""

    request = build_style_intent_request(style_prompt, discovery=discovery)
    role_plan = build_essence_role_plan(
        essence_tags=request.tags,
        discovery=request.discovery,
        candidates_per_role=MAX_CANDIDATES_PER_PAD,
        include_machine_selectable=True,
        ensure_mutable_fallback=False,
    )
    return RytmEngineCyclePlan(
        style_prompt=request.prompt,
        matched_profile_labels=tuple(profile.label for profile in request.matched_profiles),
        essence_tags=request.tags,
        discovery=request.discovery,
        pads=tuple(_build_pad_plan(assignment) for assignment in role_plan),
    )


def capture_rytm_engine_cycle_mock_messages(plan: RytmEngineCyclePlan) -> MockMidiSender:
    """Capture one mock CC15 engine-cycle event per planned pad."""

    if not isinstance(plan, RytmEngineCyclePlan):
        raise TypeError("plan must be a RytmEngineCyclePlan")

    sender = MockMidiSender()
    for pad in plan.pads:
        if not pad.candidates:
            continue
        candidate = pad.top_candidate
        sender.send(
            build_cc_message(
                channel=pad.wire_channel,
                control=MACHINE_CC,
                value=candidate.machine_value,
                metadata={
                    "source_kind": "rytm_engine_cycle_plan",
                    "device": "Analog Rytm MKII",
                    "pad": pad.pad,
                    "midi_channel": pad.midi_channel,
                    "role_key": pad.role_key,
                    "role_label": pad.role_label,
                    "event_role": "engine_cycle_top_candidate",
                    "machine_key": candidate.machine_key,
                    "machine_label": candidate.machine_label,
                    "support_status": candidate.support_status,
                    "mock_only": True,
                    "sends_real_midi": False,
                },
            )
        )
    return sender


def format_rytm_engine_cycle_plan_report(
    plan: RytmEngineCyclePlan,
    sender: MockMidiSender | None = None,
) -> list[str]:
    """Format a deterministic passive engine-cycle plan report."""

    if sender is None:
        sender = capture_rytm_engine_cycle_mock_messages(plan)

    lines = [
        "RytmRandomizer passive Rytm Engine Cycle Plan Report",
        f"Style prompt: {plan.style_prompt}",
        f"Matched profiles: {_format_labels(plan.matched_profile_labels)}",
        f"Essence tags: {_format_labels(plan.essence_tags)}",
        f"Discovery: {plan.discovery:.2f}",
        f"Pad counts: planned {plan.top_candidate_count} / no-candidate {plan.no_candidate_count}",
        f"Mock CC15 top-candidate stream: {len(sender.sent_messages)} message(s)",
        "Engine-cycle candidates:",
    ]
    for pad in plan.pads:
        lines.append(_format_pad_candidates(pad))
    lines.append("Mock MIDI stream:")
    if sender.sent_messages:
        for message in sender.sent_messages:
            lines.append(
                "- Pad "
                f"{message.metadata['pad']} ch {message.metadata['midi_channel']} "
                f"wire {message.channel} CC{message.control} -> {message.value} / "
                f"{message.metadata['machine_label']}"
            )
    else:
        lines.append("- no mock messages")
    lines.extend(
        [
            "Cycle policy:",
            "- top candidate per pad is emitted as mock CC15 only",
            "- mutable_v134 means engine switch plus tuned anchor/mutation support exists",
            "- machine_selectable means engine switch only; tuned anchors are pending",
            "- snapshot essence hardware send remains unchanged",
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


def format_rytm_engine_cycle_plan_error(message: str) -> list[str]:
    """Format deterministic passive engine-cycle plan errors."""

    return [
        "RytmRandomizer passive Rytm Engine Cycle Plan Report",
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


def _build_pad_plan(assignment) -> RytmEngineCyclePadPlan:
    midi_channel = assignment.pad
    return RytmEngineCyclePadPlan(
        pad=assignment.pad,
        midi_channel=midi_channel,
        wire_channel=midi_channel - 1,
        role_key=assignment.role.key,
        role_label=assignment.role.label,
        candidates=tuple(
            _candidate_from_machine_candidate(index, candidate)
            for index, candidate in enumerate(assignment.candidates, start=1)
            if candidate.machine.machine_value is not None
        ),
    )


def _candidate_from_machine_candidate(
    rank: int,
    candidate: MachineCandidate,
) -> RytmEngineCycleCandidate:
    machine_value = candidate.machine.machine_value
    if machine_value is None:
        raise ValueError("engine-cycle candidates must have machine values")
    return RytmEngineCycleCandidate(
        rank=rank,
        machine_key=candidate.machine.key,
        machine_label=candidate.machine.label,
        machine_value=machine_value,
        family=candidate.machine.family,
        support_status=candidate.machine.support_status,
        score=candidate.score,
        matched_tags=candidate.matched_tags,
    )


def _format_pad_candidates(pad: RytmEngineCyclePadPlan) -> str:
    if not pad.candidates:
        return f"- Pad {pad.pad} / {pad.role_label}: no engine-cycle candidates"
    candidates = "; ".join(_format_candidate(candidate) for candidate in pad.candidates)
    return f"- Pad {pad.pad} / {pad.role_label}: {candidates}"


def _format_candidate(candidate: RytmEngineCycleCandidate) -> str:
    tags = ", ".join(candidate.matched_tags) if candidate.matched_tags else "no tag match"
    return (
        f"{candidate.rank}. {candidate.machine_label} CC15 -> {candidate.machine_value} "
        f"[{candidate.support_status}] tags {tags}"
    )


def _format_labels(labels: tuple[str, ...]) -> str:
    return ", ".join(labels) if labels else "none"


__all__ = [
    "RytmEngineCycleCandidate",
    "RytmEngineCyclePadPlan",
    "RytmEngineCyclePlan",
    "build_rytm_engine_cycle_plan",
    "capture_rytm_engine_cycle_mock_messages",
    "format_rytm_engine_cycle_plan_error",
    "format_rytm_engine_cycle_plan_report",
]
