"""Passive Cockpit handoff metadata for future controller-brain runtimes."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .controller_brain_live_feedback_rehearsal import (
    FEEDBACK_REHEARSAL_STATUS,
    FEEDBACK_REHEARSAL_VERSION,
    ControllerBrainFeedbackFrame,
    build_controller_brain_live_feedback_rehearsal_report,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain live Cockpit handoff"
SOURCE_MODULE: Final[str] = "reports.controller_brain_live_cockpit_handoff"
COCKPIT_HANDOFF_VERSION: Final[str] = "controller-brain-live-cockpit-handoff-v1"
COCKPIT_HANDOFF_STATUS: Final[str] = "cockpit-handoff-passive"
SOURCE_FEEDBACK_REHEARSAL_REPORT: Final[str] = "controller-brain-live-feedback-rehearsal-report"
BASE_SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "controller-brain Cockpit handoff metadata only",
    "composes controller-brain feedback rehearsal only",
    "handoff cards are GUI-ready metadata only",
    "Cockpit panels are metadata only",
    "disabled controls are metadata only",
    "JSON/stdout only",
    "no controller input",
    "no runtime reducer execution",
    "no WebSocket dispatch",
    "no WebSocket feedback dispatch",
    "no controller feedback emission",
    "no MIDI controller output",
    "no MIDI sending",
    "no port opening",
    "no snapshot mutation",
    "no hardware mutation",
    "no hardware required",
)
BASE_BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open controller input adapter",
    "execute live state reducer",
    "dispatch Cockpit WebSocket commands",
    "open controller output adapter",
    "emit controller feedback",
    "open MIDI output",
    "mutate a snapshot",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report",
    "python -m rytm_randomizer.cli controller-brain-live-cockpit-handoff-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-feedback-rehearsal-report --json",
    "python -m rytm_randomizer.cli controller-brain-live-dispatch-rehearsal-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class ControllerBrainCockpitHandoffCard:
    """One GUI-ready passive handoff card for a future Cockpit controller view."""

    card_key: str
    order: int
    source_frame_key: str
    panel_key: str
    display_title: str
    display_line: str
    feedback_zone: str
    led_state: str
    encoder_ring: str
    control_state: str
    action_status: str
    disabled_control: str
    passive: bool
    evidence: str
    blocked_action: str


@dataclass(frozen=True)
class ControllerBrainCockpitPanel:
    """One passive Cockpit panel summary for the controller-brain handoff."""

    panel_key: str
    label: str
    card_count: int
    status: str
    disabled: bool
    evidence: str
    blocked_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainCockpitBlockedControl:
    """One disabled Cockpit control for a future controller bridge."""

    control_key: str
    label: str
    status: str
    disabled: bool
    evidence: str
    blocked_action: str
    operator_action: str
    safety_note: str


@dataclass(frozen=True)
class ControllerBrainLiveCockpitHandoffReport:
    """Passive Cockpit handoff derived from controller-feedback rehearsal."""

    title: str
    cockpit_handoff_version: str
    cockpit_handoff_status: str
    session_label: str
    source_report: str
    source_feedback_rehearsal_version: str
    source_feedback_rehearsal_status: str
    source_feedback_frame_count: int
    handoff_cards: tuple[ControllerBrainCockpitHandoffCard, ...]
    cockpit_panels: tuple[ControllerBrainCockpitPanel, ...]
    blocked_controls: tuple[ControllerBrainCockpitBlockedControl, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]

    @property
    def handoff_card_count(self) -> int:
        """Return handoff card count for summaries and JSON."""

        return _cockpit_handoff_count(self.handoff_cards)

    @property
    def cockpit_panel_count(self) -> int:
        """Return panel count for summaries and JSON."""

        return _cockpit_handoff_count(self.cockpit_panels)

    @property
    def blocked_control_count(self) -> int:
        """Return blocked control count for summaries and JSON."""

        return _cockpit_handoff_count(self.blocked_controls)


def _cockpit_handoff_unique_tuple(*groups: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    values: list[str] = []
    for group in groups:
        for value in group:
            if value in seen:
                continue
            seen.add(value)
            values.append(value)
    return tuple(values)


def _cockpit_handoff_slug(value: str) -> str:
    return value.replace(".", "-").replace("_", "-")


def _cockpit_handoff_count(values: Sequence[object]) -> int:
    return len(values)


def _cockpit_title_from_suffix(value: str) -> str:
    return " ".join(part.capitalize() for part in value.replace("_", "-").split("-"))


def _card_suffix_from_frame(frame: ControllerBrainFeedbackFrame) -> str:
    return frame.frame_key.removeprefix("feedback.frame.")


def _card_title_from_frame(frame: ControllerBrainFeedbackFrame) -> str:
    leaf = _card_suffix_from_frame(frame).split(".", maxsplit=1)[-1]
    return _cockpit_title_from_suffix(leaf)


def _handoff_card_from_frame(
    frame: ControllerBrainFeedbackFrame,
) -> ControllerBrainCockpitHandoffCard:
    suffix = _card_suffix_from_frame(frame)
    return ControllerBrainCockpitHandoffCard(
        card_key=f"cockpit.card.{suffix}",
        order=frame.order,
        source_frame_key=frame.frame_key,
        panel_key="controller-feedback-preview",
        display_title=_card_title_from_frame(frame),
        display_line=frame.display_line,
        feedback_zone=frame.feedback_zone,
        led_state=frame.led_state,
        encoder_ring=frame.encoder_ring,
        control_state="disabled-preview-only",
        action_status="blocked-passive-handoff",
        disabled_control="Emit Feedback",
        passive=True,
        evidence=f"{frame.frame_key} is exposed to Cockpit as disabled handoff metadata",
        blocked_action=frame.blocked_action,
    )


def _handoff_cards(
    frames: Sequence[ControllerBrainFeedbackFrame],
) -> tuple[ControllerBrainCockpitHandoffCard, ...]:
    return tuple(_handoff_card_from_frame(frame) for frame in frames)


def _panel_count(
    cards: Sequence[ControllerBrainCockpitHandoffCard],
    panel_key: str,
) -> int:
    return _cockpit_handoff_count(tuple(card for card in cards if card.panel_key == panel_key))


def _cockpit_panels(
    cards: Sequence[ControllerBrainCockpitHandoffCard],
    output_gate_count: int,
    blocked_action_count: int,
) -> tuple[ControllerBrainCockpitPanel, ...]:
    return (
        ControllerBrainCockpitPanel(
            panel_key="controller-feedback-preview",
            label="Controller Feedback Preview",
            card_count=_panel_count(cards, "controller-feedback-preview"),
            status="disabled-preview-only",
            disabled=True,
            evidence="feedback frames are visible as Cockpit preview cards only",
            blocked_action="emit controller feedback",
            safety_note="preview cards do not write controller feedback",
        ),
        ControllerBrainCockpitPanel(
            panel_key="controller-output-gates",
            label="Controller Output Gates",
            card_count=output_gate_count,
            status="blocked-output-review",
            disabled=True,
            evidence="feedback output gates stay blocked in the handoff model",
            blocked_action="open controller output adapter",
            safety_note="output gates are review metadata only",
        ),
        ControllerBrainCockpitPanel(
            panel_key="blocked-runtime-controls",
            label="Blocked Runtime Controls",
            card_count=blocked_action_count,
            status="blocked-runtime-review",
            disabled=True,
            evidence="runtime controls are listed but disabled",
            blocked_action="execute live state reducer",
            safety_note="runtime controls do not execute reducers or WebSockets",
        ),
        ControllerBrainCockpitPanel(
            panel_key="operator-replay",
            label="Operator Replay",
            card_count=_cockpit_handoff_count(REPLAY_COMMANDS),
            status="copy-ready-passive",
            disabled=False,
            evidence="replay commands are passive CLI inspection commands",
            blocked_action="send hardware MIDI",
            safety_note="replay commands open no ports and send no MIDI",
        ),
    )


def _cockpit_blocked_controls() -> tuple[ControllerBrainCockpitBlockedControl, ...]:
    return (
        ControllerBrainCockpitBlockedControl(
            control_key="controller-input",
            label="Open Controller Input",
            status="blocked",
            disabled=True,
            evidence="controller input stays outside this Cockpit handoff",
            blocked_action="open controller input adapter",
            operator_action="approve controller input before reading hardware gestures",
            safety_note="this report opens no controller input",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="runtime-reducer",
            label="Execute Live Reducer",
            status="blocked",
            disabled=True,
            evidence="handoff cards do not execute runtime reducers",
            blocked_action="execute live state reducer",
            operator_action="implement reducers behind a separate active bridge gate",
            safety_note="this report executes no reducers",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="websocket-dispatch",
            label="Dispatch WebSocket",
            status="blocked",
            disabled=True,
            evidence="Cockpit WebSocket dispatch is not performed",
            blocked_action="dispatch Cockpit WebSocket commands",
            operator_action="define acknowledgements before WebSocket dispatch",
            safety_note="this report dispatches no WebSocket commands",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="controller-output",
            label="Open Controller Output",
            status="blocked",
            disabled=True,
            evidence="controller output adapter is not opened",
            blocked_action="open controller output adapter",
            operator_action="approve controller output before LED/ring/display writes",
            safety_note="this report opens no controller output adapter",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="controller-feedback",
            label="Emit Controller Feedback",
            status="blocked",
            disabled=True,
            evidence="LED, ring, and display feedback remains metadata only",
            blocked_action="emit controller feedback",
            operator_action="emit feedback only through a separately approved output path",
            safety_note="this report emits no controller feedback",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="midi-output",
            label="Open MIDI Output",
            status="blocked",
            disabled=True,
            evidence="MIDI output remains outside the passive CLI surface",
            blocked_action="open MIDI output",
            operator_action="use an explicit armed path for real MIDI output",
            safety_note="this report opens no MIDI output",
        ),
        ControllerBrainCockpitBlockedControl(
            control_key="snapshot-mutation",
            label="Mutate Snapshot",
            status="blocked",
            disabled=True,
            evidence="snapshot mutation remains outside this handoff model",
            blocked_action="mutate a snapshot",
            operator_action="mutate snapshots only through approved armed shell flows",
            safety_note="this report mutates no snapshots",
        ),
    )


def build_controller_brain_live_cockpit_handoff_report(
    *,
    session_label: str = "Live Session",
) -> ControllerBrainLiveCockpitHandoffReport:
    """Build passive GUI-ready handoff metadata from feedback rehearsal."""

    feedback = build_controller_brain_live_feedback_rehearsal_report(session_label=session_label)
    cards = _handoff_cards(feedback.feedback_frames)
    controls = _cockpit_blocked_controls()
    panels = _cockpit_panels(
        cards,
        feedback.output_gate_count,
        _cockpit_handoff_count(feedback.blocked_actions),
    )
    return ControllerBrainLiveCockpitHandoffReport(
        title=REPORT_TITLE,
        cockpit_handoff_version=COCKPIT_HANDOFF_VERSION,
        cockpit_handoff_status=COCKPIT_HANDOFF_STATUS,
        session_label=session_label,
        source_report=SOURCE_FEEDBACK_REHEARSAL_REPORT,
        source_feedback_rehearsal_version=FEEDBACK_REHEARSAL_VERSION,
        source_feedback_rehearsal_status=FEEDBACK_REHEARSAL_STATUS,
        source_feedback_frame_count=feedback.feedback_frame_count,
        handoff_cards=cards,
        cockpit_panels=panels,
        blocked_controls=controls,
        blocked_actions=_cockpit_handoff_unique_tuple(
            BASE_BLOCKED_ACTIONS,
            feedback.blocked_actions,
        ),
        safety_lines=_cockpit_handoff_unique_tuple(
            BASE_SAFETY_LINES,
            feedback.safety_lines,
        ),
        replay_commands=REPLAY_COMMANDS,
    )


def _handoff_card_to_payload(card: ControllerBrainCockpitHandoffCard) -> dict[str, object]:
    return {
        "card_key": card.card_key,
        "order": card.order,
        "source_frame_key": card.source_frame_key,
        "panel_key": card.panel_key,
        "display_title": card.display_title,
        "display_line": card.display_line,
        "feedback_zone": card.feedback_zone,
        "led_state": card.led_state,
        "encoder_ring": card.encoder_ring,
        "control_state": card.control_state,
        "action_status": card.action_status,
        "disabled_control": card.disabled_control,
        "passive": card.passive,
        "evidence": card.evidence,
        "blocked_action": card.blocked_action,
    }


def _cockpit_panel_to_payload(panel: ControllerBrainCockpitPanel) -> dict[str, object]:
    return {
        "panel_key": panel.panel_key,
        "label": panel.label,
        "card_count": panel.card_count,
        "status": panel.status,
        "disabled": panel.disabled,
        "evidence": panel.evidence,
        "blocked_action": panel.blocked_action,
        "safety_note": panel.safety_note,
    }


def _blocked_control_to_payload(
    control: ControllerBrainCockpitBlockedControl,
) -> dict[str, object]:
    return {
        "control_key": control.control_key,
        "label": control.label,
        "status": control.status,
        "disabled": control.disabled,
        "evidence": control.evidence,
        "blocked_action": control.blocked_action,
        "operator_action": control.operator_action,
        "safety_note": control.safety_note,
    }


def build_controller_brain_live_cockpit_handoff_payload(
    *,
    session_label: str = "Live Session",
) -> dict[str, object]:
    """Return JSON-ready passive Cockpit handoff metadata."""

    report = build_controller_brain_live_cockpit_handoff_report(session_label=session_label)
    return {
        "controller_brain_live_cockpit_handoff": {
            "title": report.title,
            "cockpit_handoff_version": report.cockpit_handoff_version,
            "cockpit_handoff_status": report.cockpit_handoff_status,
            "session_label": report.session_label,
            "source_report": report.source_report,
            "source_feedback_rehearsal_version": (report.source_feedback_rehearsal_version),
            "source_feedback_rehearsal_status": report.source_feedback_rehearsal_status,
            "source_feedback_frame_count": report.source_feedback_frame_count,
            "handoff_card_count": report.handoff_card_count,
            "cockpit_panel_count": report.cockpit_panel_count,
            "blocked_control_count": report.blocked_control_count,
            "handoff_cards": [_handoff_card_to_payload(card) for card in report.handoff_cards],
            "cockpit_panels": [_cockpit_panel_to_payload(panel) for panel in report.cockpit_panels],
            "blocked_controls": [
                _blocked_control_to_payload(control) for control in report.blocked_controls
            ],
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def _format_cockpit_handoff_body(
    report: ControllerBrainLiveCockpitHandoffReport,
) -> list[str]:
    lines = [
        "Controller brain live Cockpit handoff:",
        f"- version: {report.cockpit_handoff_version}",
        f"- status: {report.cockpit_handoff_status}",
        f"- session: {report.session_label}",
        f"- source feedback: {report.source_report}",
        f"- source feedback version: {report.source_feedback_rehearsal_version}",
        f"- source feedback status: {report.source_feedback_rehearsal_status}",
        f"- source feedback frames: {report.source_feedback_frame_count}",
        f"- handoff cards: {report.handoff_card_count}",
        f"- Cockpit panels: {report.cockpit_panel_count}",
        f"- blocked controls: {report.blocked_control_count}",
        "GUI-ready handoff cards:",
    ]
    for card in report.handoff_cards:
        lines.append(f"- {card.card_key}: {card.panel_key} / {card.action_status}")
        lines.append(f"  source: {card.source_frame_key}")
        lines.append(f"  title: {card.display_title}")
        lines.append(f"  display: {card.display_line}")
        lines.append(f"  led: {card.led_state}")
        lines.append(f"  ring: {card.encoder_ring}")
        lines.append(f"  disabled control: {card.disabled_control}")
        lines.append(f"  evidence: {card.evidence}")
        lines.append(f"  blocked: {card.blocked_action}")
    lines.append("Cockpit panels:")
    for panel in report.cockpit_panels:
        lines.append(f"- {panel.panel_key}: {panel.card_count} card(s)")
        lines.append(f"  label: {panel.label}")
        lines.append(f"  status: {panel.status}")
        lines.append(f"  disabled: {panel.disabled}")
        lines.append(f"  blocked: {panel.blocked_action}")
        lines.append(f"  safety: {panel.safety_note}")
    lines.append("Disabled Cockpit controls:")
    for control in report.blocked_controls:
        lines.append(f"- {control.control_key}: {control.status} / disabled={control.disabled}")
        lines.append(f"  label: {control.label}")
        lines.append(f"  evidence: {control.evidence}")
        lines.append(f"  operator action: {control.operator_action}")
        lines.append(f"  blocked: {control.blocked_action}")
        lines.append(f"  safety: {control.safety_note}")
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_actions)
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in report.safety_lines)
    return lines


def format_controller_brain_live_cockpit_handoff_report(
    report: ControllerBrainLiveCockpitHandoffReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing Cockpit handoff text."""

    source = build_controller_brain_live_cockpit_handoff_report() if report is None else report
    return passive_report_lines(_HEADER, _format_cockpit_handoff_body(source))


CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-live-cockpit-handoff-report",
    "Print the passive controller-brain live Cockpit handoff contract.",
    format_lines=lambda: format_controller_brain_live_cockpit_handoff_report(),
    build_payload=build_controller_brain_live_cockpit_handoff_payload,
)

register(CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND)

__all__ = (
    "BASE_BLOCKED_ACTIONS",
    "BASE_SAFETY_LINES",
    "COCKPIT_HANDOFF_STATUS",
    "COCKPIT_HANDOFF_VERSION",
    "CONTROLLER_BRAIN_LIVE_COCKPIT_HANDOFF_CLI_COMMAND",
    "ControllerBrainCockpitBlockedControl",
    "ControllerBrainCockpitHandoffCard",
    "ControllerBrainCockpitPanel",
    "ControllerBrainLiveCockpitHandoffReport",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SOURCE_FEEDBACK_REHEARSAL_REPORT",
    "SOURCE_MODULE",
    "build_controller_brain_live_cockpit_handoff_payload",
    "build_controller_brain_live_cockpit_handoff_report",
    "format_controller_brain_live_cockpit_handoff_report",
)
