"""Passive controller-feedback rehearsal for future controller-brain runtimes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_dispatch_rehearsal import (
    DISPATCH_REHEARSAL_STATUS,
    DISPATCH_REHEARSAL_VERSION,
    ControllerBrainDispatchDecision,
    build_controller_brain_live_dispatch_rehearsal_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live feedback rehearsal"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_feedback_rehearsal"
FEEDBACK_REHEARSAL_VERSION: Final[str] = "controller-brain-live-feedback-rehearsal-v1"
FEEDBACK_REHEARSAL_STATUS: Final[str] = "feedback-output-blocked"
SOURCE_DISPATCH_REHEARSAL_REPORT: Final[str] = "controller-brain-live-dispatch-rehearsal-report"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain feedback rehearsal metadata only",
    "composes controller-brain dispatch rehearsal only",
    "feedback frames are metadata only",
    "output gates are metadata only",
    "JSON/stdout only",
    "no MIDI controller output",
    "no controller feedback emission",
    "no WebSocket feedback dispatch",
    "no runtime reducer execution",
    "no MIDI sending",
    "no port opening",
    "no snapshot mutation",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open controller output adapter",
    "emit controller feedback",
    "write controller LED state",
    "write controller encoder ring state",
    "write controller display text",
    "dispatch Cockpit WebSocket feedback",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report",
    "python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-bridge-readiness-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainFeedbackFrame:
    """One passive controller-feedback frame for a future output adapter."""

    frame_key: str
    order: int
    source_decision_key: str
    feedback_zone: str
    led_state: str
    encoder_ring: str
    display_line: str
    output_status: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainFeedbackZone:
    """One passive summary of feedback frames by future controller zone."""

    name: str
    frame_count: int
    led_state: str
    encoder_ring: str
    output_status: str
    blocked_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainFeedbackOutputGate:
    """One passive output gate that keeps controller feedback blocked."""

    name: str
    status: str
    blocked: bool
    evidence: str
    blocked_action: str
    operator_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainLiveFeedbackRehearsalReport:
    """Passive controller-feedback rehearsal derived from dispatch metadata."""

    title: str
    feedback_rehearsal_version: str
    feedback_rehearsal_status: str
    session_label: str
    source_report: str
    source_dispatch_rehearsal_version: str
    source_dispatch_rehearsal_status: str
    source_dispatch_decision_count: int
    feedback_frames: tuple[ControllerBrainFeedbackFrame, ...]
    feedback_zones: tuple[ControllerBrainFeedbackZone, ...]
    output_gates: tuple[ControllerBrainFeedbackOutputGate, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def feedback_frame_count(self) -> int:
        """Return feedback frame count for summaries and JSON."""

        return _feedback_rehearsal_count(self.feedback_frames)

    @property
    def feedback_zone_count(self) -> int:
        """Return feedback zone count for summaries and JSON."""

        return _feedback_rehearsal_count(self.feedback_zones)

    @property
    def output_gate_count(self) -> int:
        """Return output gate count for summaries and JSON."""

        return _feedback_rehearsal_count(self.output_gates)

    @property
    def blocked_output_gate_count(self) -> int:
        """Return blocked output gate count for summaries and JSON."""

        return _feedback_rehearsal_count(tuple(gate for gate in self.output_gates if gate.blocked))


def _feedback_rehearsal_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _feedback_rehearsal_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _feedback_rehearsal_count(values: Sequence[object]) -> int:
    return len(values)


def _feedback_label_from_suffix(value: str) -> str:
    return value.replace("-", " ").replace("_", " ")


def _feedback_suffix_from_decision(decision: ControllerBrainDispatchDecision) -> str:
    return decision.decision_key.removeprefix("dispatch.decision.")


def _feedback_leaf_from_suffix(value: str) -> str:
    return value.split(".", maxsplit=1)[-1]


def _led_state_for_group(group: str) -> str:
    if group == "queue-reducer":
        return "queued-armed"
    if group == "audit-ledger":
        return "audit-muted"
    return "safe-ready"


def _encoder_ring_for_suffix(value: str) -> str:
    leaf = _feedback_leaf_from_suffix(value)
    if "preview-depth" in leaf:
        return "preview-depth"
    if "panic" in leaf:
        return "panic"
    parts = leaf.split("-")
    return "-".join(parts[-2:]) if len(parts) > 1 else leaf


def _feedback_frame_from_decision(
    decision: ControllerBrainDispatchDecision,
) -> ControllerBrainFeedbackFrame:
    suffix = _feedback_suffix_from_decision(decision)
    leaf = _feedback_leaf_from_suffix(suffix)
    label = _feedback_label_from_suffix(leaf)
    return ControllerBrainFeedbackFrame(
        frame_key=f"feedback.frame.{suffix}",
        order=decision.order,
        source_decision_key=decision.decision_key,
        feedback_zone=decision.dispatch_group,
        led_state=_led_state_for_group(decision.dispatch_group),
        encoder_ring=_encoder_ring_for_suffix(suffix),
        display_line=f"{label} -> blocked shadow {decision.dispatch_group}",
        output_status="blocked-metadata-only",
        passive=True,
        evidence=f"{decision.decision_key} rehearses controller feedback without output",
        blocked_action="emit controller feedback",
    )


def _feedback_frames(
    decisions: Sequence[ControllerBrainDispatchDecision],
) -> tuple[ControllerBrainFeedbackFrame, ...]:
    return tuple(_feedback_frame_from_decision(decision) for decision in decisions)


def _feedback_zones(
    frames: Sequence[ControllerBrainFeedbackFrame],
) -> tuple[ControllerBrainFeedbackZone, ...]:
    zones: list[ControllerBrainFeedbackZone] = []
    for name, blocked_action in (
        ("state-reducer", "write controller LED state"),
        ("queue-reducer", "write controller encoder ring state"),
        ("audit-ledger", "write controller display text"),
    ):
        group_frames = tuple(frame for frame in frames if frame.feedback_zone == name)
        first_frame = group_frames[0]
        zones.append(
            ControllerBrainFeedbackZone(
                name=name,
                frame_count=_feedback_rehearsal_count(group_frames),
                led_state=first_frame.led_state,
                encoder_ring=first_frame.encoder_ring,
                output_status="blocked-metadata-only",
                blocked_action=blocked_action,
                safety_note=f"{name} feedback stays passive metadata only",
            )
        )
    return tuple(zones)


def _output_gates() -> tuple[ControllerBrainFeedbackOutputGate, ...]:
    return (
        ControllerBrainFeedbackOutputGate(
            name="controller-output",
            status="blocked",
            blocked=True,
            evidence="no controller output adapter is opened",
            blocked_action="open controller output adapter",
            operator_action="approve an output adapter before feedback emission",
            safety_note="this report opens no controller output adapter",
        ),
        ControllerBrainFeedbackOutputGate(
            name="led-output",
            status="blocked",
            blocked=True,
            evidence="LED states are rendered as metadata only",
            blocked_action="write controller LED state",
            operator_action="define LED semantics before writing controller LEDs",
            safety_note="this report writes no LEDs",
        ),
        ControllerBrainFeedbackOutputGate(
            name="ring-output",
            status="blocked",
            blocked=True,
            evidence="encoder ring states are rendered as metadata only",
            blocked_action="write controller encoder ring state",
            operator_action="define ring scaling before writing controller rings",
            safety_note="this report writes no encoder rings",
        ),
        ControllerBrainFeedbackOutputGate(
            name="display-output",
            status="blocked",
            blocked=True,
            evidence="display text is rendered as metadata only",
            blocked_action="write controller display text",
            operator_action="define display layout before writing controller displays",
            safety_note="this report writes no controller displays",
        ),
        ControllerBrainFeedbackOutputGate(
            name="websocket-feedback",
            status="blocked",
            blocked=True,
            evidence="no Cockpit WebSocket feedback packet is dispatched",
            blocked_action="dispatch Cockpit WebSocket feedback",
            operator_action="define feedback acknowledgements before dispatch",
            safety_note="this report dispatches no WebSocket feedback",
        ),
        ControllerBrainFeedbackOutputGate(
            name="hardware-feedback",
            status="blocked",
            blocked=True,
            evidence="hardware output remains outside this passive rehearsal",
            blocked_action="emit controller feedback",
            operator_action="emit feedback only through a separately approved armed path",
            safety_note="this report emits no controller feedback",
        ),
    )


def build_controller_brain_live_feedback_rehearsal_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveFeedbackRehearsalReport:
    """Build passive controller-feedback metadata from dispatch decisions."""

    dispatch = build_controller_brain_live_dispatch_rehearsal_report(session_label=session_label)
    frames = _feedback_frames(dispatch.dispatch_decisions)
    zones = _feedback_zones(frames)
    gates = _output_gates()
    return ControllerBrainLiveFeedbackRehearsalReport(
        title=REPORT_TITLE,
        feedback_rehearsal_version=FEEDBACK_REHEARSAL_VERSION,
        feedback_rehearsal_status=FEEDBACK_REHEARSAL_STATUS,
        session_label=session_label,
        source_report=SOURCE_DISPATCH_REHEARSAL_REPORT,
        source_dispatch_rehearsal_version=DISPATCH_REHEARSAL_VERSION,
        source_dispatch_rehearsal_status=DISPATCH_REHEARSAL_STATUS,
        source_dispatch_decision_count=dispatch.dispatch_decision_count,
        feedback_frames=frames,
        feedback_zones=zones,
        output_gates=gates,
        blocked_actions=_feedback_rehearsal_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            dispatch.blocked_actions,
        ),
        safety_lines=_feedback_rehearsal_unique_tuple(
            BASE_SAFETY_LINES,
            dispatch.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _feedback_frame_to_payload(frame: ControllerBrainFeedbackFrame) -> dict[str, object]:
    return {
        "frame_key": frame.frame_key,
        "order": frame.order,
        "source_decision_key": frame.source_decision_key,
        "feedback_zone": frame.feedback_zone,
        "led_state": frame.led_state,
        "encoder_ring": frame.encoder_ring,
        "display_line": frame.display_line,
        "output_status": frame.output_status,
        "passive": frame.passive,
        "evidence": frame.evidence,
        "blocked_action": frame.blocked_action,
    }


def _feedback_zone_to_payload(zone: ControllerBrainFeedbackZone) -> dict[str, object]:
    return {
        "name": zone.name,
        "frame_count": zone.frame_count,
        "led_state": zone.led_state,
        "encoder_ring": zone.encoder_ring,
        "output_status": zone.output_status,
        "blocked_action": zone.blocked_action,
        "safety_note": zone.safety_note,
    }


def _output_gate_to_payload(gate: ControllerBrainFeedbackOutputGate) -> dict[str, object]:
    return {
        "name": gate.name,
        "status": gate.status,
        "blocked": gate.blocked,
        "evidence": gate.evidence,
        "blocked_action": gate.blocked_action,
        "operator_action": gate.operator_action,
        "safety_note": gate.safety_note,
    }


def build_controller_brain_live_feedback_rehearsal_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive feedback rehearsal metadata."""

    report = build_controller_brain_live_feedback_rehearsal_report(session_label=session_label)
    return {
        "controller_brain_live_feedback_rehearsal": {
            "title": report.title,
            "feedback_rehearsal_version": report.feedback_rehearsal_version,
            "feedback_rehearsal_status": report.feedback_rehearsal_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_dispatch_rehearsal_version": (report.source_dispatch_rehearsal_version),
            "source_dispatch_rehearsal_status": report.source_dispatch_rehearsal_status,
            "source_dispatch_decision_count": report.source_dispatch_decision_count,
            "feedback_frame_count": report.feedback_frame_count,
            "feedback_zone_count": report.feedback_zone_count,
            "output_gate_count": report.output_gate_count,
            "blocked_output_gate_count": report.blocked_output_gate_count,
            "feedback_frames": [
                _feedback_frame_to_payload(frame) for frame in report.feedback_frames
            ],
            "feedback_zones": [_feedback_zone_to_payload(zone) for zone in report.feedback_zones],
            "output_gates": [_output_gate_to_payload(gate) for gate in report.output_gates],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_feedback_rehearsal_body(
    report: ControllerBrainLiveFeedbackRehearsalReport,
) -> list[str]:
    lines = [
        "Controller brain live feedback rehearsal:",
        f"- version: {report.feedback_rehearsal_version}",
        f"- status: {report.feedback_rehearsal_status}",
        f"- session: {report.session_label}",
        f"- source dispatch: {report.source_report}",
        f"- source dispatch version: {report.source_dispatch_rehearsal_version}",
        f"- source dispatch status: {report.source_dispatch_rehearsal_status}",
        f"- source dispatch decisions: {report.source_dispatch_decision_count}",
        f"- feedback frames: {report.feedback_frame_count}",
        f"- feedback zones: {report.feedback_zone_count}",
        f"- output gates: {report.output_gate_count}",
        f"- blocked output gates: {report.blocked_output_gate_count}",
        "Feedback frames:",
    ]
    for frame in report.feedback_frames:
        lines.append(f"- {frame.frame_key}: {frame.feedback_zone} / {frame.output_status}")
        lines.append(f"  source: {frame.source_decision_key}")
        lines.append(f"  led: {frame.led_state}")
        lines.append(f"  ring: {frame.encoder_ring}")
        lines.append(f"  display: {frame.display_line}")
        lines.append(f"  evidence: {frame.evidence}")
        lines.append(f"  blocked: {frame.blocked_action}")
    lines.append("Feedback zones:")
    for zone in report.feedback_zones:
        lines.append(f"- {zone.name}: {zone.frame_count} frame(s)")
        lines.append(f"  led: {zone.led_state}")
        lines.append(f"  ring: {zone.encoder_ring}")
        lines.append(f"  status: {zone.output_status}")
        lines.append(f"  blocked: {zone.blocked_action}")
        lines.append(f"  safety: {zone.safety_note}")
    lines.append("Output gates:")
    for gate in report.output_gates:
        lines.append(f"- {gate.name}: {gate.status} / blocked={gate.blocked}")
        lines.append(f"  evidence: {gate.evidence}")
        lines.append(f"  operator action: {gate.operator_action}")
        lines.append(f"  blocked: {gate.blocked_action}")
        lines.append(f"  safety: {gate.safety_note}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_feedback_rehearsal_report(
    report: ControllerBrainLiveFeedbackRehearsalReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing feedback rehearsal text."""

    source = build_controller_brain_live_feedback_rehearsal_report() if report is None else report
    return passive_report_lines(_HEADER, _format_feedback_rehearsal_body(source))


CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND: Final[CliCommand] = (
    make_passive_report_command(
        "controller-brain-live-feedback-rehearsal-report",
        "Print the passive controller-brain live feedback rehearsal contract.",
        format_lines=lambda: format_controller_brain_live_feedback_rehearsal_report(),
        build_payload=build_controller_brain_live_feedback_rehearsal_payload,
    )
)

register(CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "CONTROLLER_BRAIN_LIVE_FEEDBACK_REHEARSAL_CLI_COMMAND",
    "ControllerBrainFeedbackFrame",
    "ControllerBrainFeedbackOutputGate",
    "ControllerBrainFeedbackZone",
    "ControllerBrainLiveFeedbackRehearsalReport",
    "FEEDBACK_REHEARSAL_STATUS",
    "FEEDBACK_REHEARSAL_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_DISPATCH_REHEARSAL_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_feedback_rehearsal_payload",
    "build_controller_brain_live_feedback_rehearsal_report",
    "format_controller_brain_live_feedback_rehearsal_report",
)
