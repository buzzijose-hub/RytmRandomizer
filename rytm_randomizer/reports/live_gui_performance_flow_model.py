"""Passive live GUI performance flow model."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, TypedDict

from ..cli_registry import CliCommand, make_passive_report_command, register
from .analog_four_oxi_macro_set_planner import (
    AnalogFourOxiSetPlannerReport,
    build_analog_four_oxi_macro_set_planner_report,
)

REPORT_TITLE: Final[str] = "RytmRandomizer passive live GUI performance flow model"
SOURCE_MODULE: Final[str] = "reports.live_gui_performance_flow_model"
MODEL_VERSION: Final[str] = "live-gui-performance-flow-model-v1"
FLOW_ID: Final[str] = "oxi-rytm-a4-performance-flow"
FLOW_STATUS: Final[str] = "mock-safe"
CURRENT_STEP_KEY: Final[str] = "capture-anchor"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "GUI performance flow metadata only",
    "Rytm OXI macro command labels only",
    "Analog Four review-only actions stay candidate metadata.",
    "JSON/stdout only",
    "no GUI launch",
    "no file writing",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "a4_outbound_macro_send",
    "unattended_hardware_behavior",
    "open_midi_port_without_arm",
    "send_without_dry_run",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli live-gui-performance-flow-model-report --json",
    "python -m rytm_randomizer.cli oxi-live-macro-catalog-report",
    "python -m rytm_randomizer.cli analog-four-oxi-macro-report --json",
    "python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json",
    "python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report "
    "hard-groove --seed 0 --intensity 4 --limit 4",
)
A4_MACRO_READINESS_COMMAND: Final[str] = (
    "python -m rytm_randomizer.cli analog-four-oxi-macro-readiness-report "
    "hard-groove --seed 0 --intensity 4 --limit 4"
)


@dataclass(frozen=True)
class LiveGuiPerformanceFlowStep:
    """One GUI-ready Rytm/A4 live performance flow step."""

    key: str
    order: int
    label: str
    phase: str
    rytm_command: str
    analog_four_action: str
    send_policy: str
    recovery_action: str
    status: str


class LiveGuiPerformanceFlowStepDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiPerformanceFlowStep`."""

    key: str
    order: int
    label: str
    phase: str
    rytm_command: str
    analog_four_action: str
    send_policy: str
    recovery_action: str
    status: str


@dataclass(frozen=True)
class LiveGuiAnalogFourReadiness:
    """GUI-ready A4 macro readiness summary for the passive flow model."""

    readiness: str
    command: str
    summary: str
    blocked_active_actions: tuple[str, ...]


class LiveGuiAnalogFourReadinessDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalogFourReadiness`."""

    readiness: str
    command: str
    summary: str
    blocked_active_actions: tuple[str, ...]


@dataclass(frozen=True)
class LiveGuiAnalogFourSetPlan:
    """GUI-ready A4 macro set-plan summary for the passive flow model."""

    set_name: str
    current_macro: str
    up_next_macros: tuple[str, ...]
    step_count: int
    replay_command: str
    summary: str
    blocked_active_actions: tuple[str, ...]


class LiveGuiAnalogFourSetPlanDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiAnalogFourSetPlan`."""

    set_name: str
    current_macro: str
    up_next_macros: tuple[str, ...]
    step_count: int
    replay_command: str
    summary: str
    blocked_active_actions: tuple[str, ...]


def _analog_four_set_plan_from_report(
    report: AnalogFourOxiSetPlannerReport,
) -> LiveGuiAnalogFourSetPlan:
    up_next_macros = tuple(step.macro_name for step in report.up_next)
    return LiveGuiAnalogFourSetPlan(
        set_name=report.set_name,
        current_macro=report.current_step.macro_name,
        up_next_macros=up_next_macros,
        step_count=len(report.steps),
        replay_command=report.replay_command,
        summary=(
            f"{report.set_name} stages {len(report.steps)} A4 macro moves; "
            f"current {report.current_step.macro_name}; full macro SEND remains blocked."
        ),
        blocked_active_actions=report.blocked_active_actions,
    )


DEFAULT_ANALOG_FOUR_READINESS: Final[LiveGuiAnalogFourReadiness] = LiveGuiAnalogFourReadiness(
    readiness="review-ready",
    command=A4_MACRO_READINESS_COMMAND,
    summary=(
        "A4 macro rows are CC-ready for operator-present validation; "
        "full macro SEND remains blocked."
    ),
    blocked_active_actions=("a4_outbound_macro_send",),
)

DEFAULT_ANALOG_FOUR_SET_PLAN: Final[LiveGuiAnalogFourSetPlan] = _analog_four_set_plan_from_report(
    build_analog_four_oxi_macro_set_planner_report()
)


@dataclass(frozen=True)
class LiveGuiPerformanceFlowModel:
    """Passive cockpit performance flow packet for future GUI consumers."""

    model_version: str
    source_module: str
    flow_id: str
    flow_status: str
    current_step_key: str
    steps: tuple[LiveGuiPerformanceFlowStep, ...]
    analog_four_readiness: LiveGuiAnalogFourReadiness
    analog_four_set_plan: LiveGuiAnalogFourSetPlan
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


class LiveGuiPerformanceFlowModelDict(TypedDict):
    """JSON-ready contract for :class:`LiveGuiPerformanceFlowModel`."""

    model_version: str
    source_module: str
    flow_id: str
    flow_status: str
    current_step_key: str
    steps: tuple[LiveGuiPerformanceFlowStepDict, ...]
    analog_four_readiness: LiveGuiAnalogFourReadinessDict
    analog_four_set_plan: LiveGuiAnalogFourSetPlanDict
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


DEFAULT_STEPS: Final[tuple[LiveGuiPerformanceFlowStep, ...]] = (
    LiveGuiPerformanceFlowStep(
        key="capture-anchor",
        order=1,
        label="Capture Anchor",
        phase="setup",
        rytm_command="kit/resnapshot",
        analog_four_action="A4 soft-capture reference",
        send_policy="receive-only",
        recovery_action="Z + send",
        status="safe",
    ),
    LiveGuiPerformanceFlowStep(
        key="kit-core",
        order=2,
        label="Kit Core",
        phase="foundation",
        rytm_command="kit-core",
        analog_four_action="review bass/stab candidates",
        send_policy="stage-review-send",
        recovery_action="home",
        status="staged",
    ),
    LiveGuiPerformanceFlowStep(
        key="hard-groove",
        order=3,
        label="Hard Groove",
        phase="pressure",
        rytm_command="hard-groove",
        analog_four_action="review rhythmic contour",
        send_policy="stage-review-send",
        recovery_action="home",
        status="staged",
    ),
    LiveGuiPerformanceFlowStep(
        key="industrial",
        order=4,
        label="Industrial",
        phase="texture",
        rytm_command="industrial",
        analog_four_action="review texture motion",
        send_policy="stage-review-send",
        recovery_action="home",
        status="staged",
    ),
    LiveGuiPerformanceFlowStep(
        key="dub-pressure",
        order=5,
        label="Dub Pressure",
        phase="space",
        rytm_command="dub-pressure",
        analog_four_action="review delay/reverb space",
        send_policy="stage-review-send",
        recovery_action="home",
        status="staged",
    ),
    LiveGuiPerformanceFlowStep(
        key="transition",
        order=6,
        label="Transition",
        phase="handoff",
        rytm_command="transition",
        analog_four_action="review bridge candidate",
        send_policy="dry-run-only",
        recovery_action="home",
        status="review",
    ),
    LiveGuiPerformanceFlowStep(
        key="home",
        order=7,
        label="Home",
        phase="recovery",
        rytm_command="Z + send",
        analog_four_action="keep A4 review-only",
        send_policy="restore-anchor",
        recovery_action="kit/resnapshot",
        status="safe",
    ),
)


def build_live_gui_performance_flow_model(
    *,
    steps: Sequence[LiveGuiPerformanceFlowStep] = DEFAULT_STEPS,
    analog_four_readiness: LiveGuiAnalogFourReadiness = DEFAULT_ANALOG_FOUR_READINESS,
    analog_four_set_plan: LiveGuiAnalogFourSetPlan = DEFAULT_ANALOG_FOUR_SET_PLAN,
    current_step_key: str = CURRENT_STEP_KEY,
) -> LiveGuiPerformanceFlowModel:
    """Build the deterministic passive live GUI performance flow model."""

    return LiveGuiPerformanceFlowModel(
        model_version=MODEL_VERSION,
        source_module=SOURCE_MODULE,
        flow_id=FLOW_ID,
        flow_status=FLOW_STATUS,
        current_step_key=current_step_key,
        steps=tuple(steps),
        analog_four_readiness=analog_four_readiness,
        analog_four_set_plan=analog_four_set_plan,
        blocked_actions=BLOCKED_ACTIONS,
        safety_lines=SAFETY_LINES,
        replay_commands=REPLAY_COMMANDS,
    )


def _live_gui_performance_flow_step_payload(
    step: LiveGuiPerformanceFlowStep,
) -> dict[str, object]:
    return {
        "key": step.key,
        "order": step.order,
        "label": step.label,
        "phase": step.phase,
        "rytm_command": step.rytm_command,
        "analog_four_action": step.analog_four_action,
        "send_policy": step.send_policy,
        "recovery_action": step.recovery_action,
        "status": step.status,
    }


def _live_gui_analog_four_readiness_payload(
    readiness: LiveGuiAnalogFourReadiness,
) -> dict[str, object]:
    return {
        "readiness": readiness.readiness,
        "command": readiness.command,
        "summary": readiness.summary,
        "blocked_active_actions": list(readiness.blocked_active_actions),
    }


def _live_gui_analog_four_set_plan_payload(
    set_plan: LiveGuiAnalogFourSetPlan,
) -> dict[str, object]:
    return {
        "set_name": set_plan.set_name,
        "current_macro": set_plan.current_macro,
        "up_next_macros": list(set_plan.up_next_macros),
        "step_count": set_plan.step_count,
        "replay_command": set_plan.replay_command,
        "summary": set_plan.summary,
        "blocked_active_actions": list(set_plan.blocked_active_actions),
    }


def live_gui_performance_flow_model_payload(
    model: LiveGuiPerformanceFlowModel,
) -> dict[str, object]:
    """Return deterministic JSON-ready performance flow model payload."""

    return {
        "live_gui_performance_flow_model": {
            "model_version": model.model_version,
            "source_module": model.source_module,
            "flow_id": model.flow_id,
            "flow_status": model.flow_status,
            "current_step_key": model.current_step_key,
            "steps": [_live_gui_performance_flow_step_payload(step) for step in model.steps],
            "analog_four_readiness": _live_gui_analog_four_readiness_payload(
                model.analog_four_readiness
            ),
            "analog_four_set_plan": _live_gui_analog_four_set_plan_payload(
                model.analog_four_set_plan
            ),
            "blocked_actions": list(model.blocked_actions),
            "safety_lines": list(model.safety_lines),
            "replay_commands": list(model.replay_commands),
        }
    }


def _live_gui_performance_flow_position(
    *,
    step: LiveGuiPerformanceFlowStep,
    current_step_key: str,
) -> str:
    if step.key == current_step_key:
        return "current"
    if step.order == 1:
        return "anchor"
    return "next"


def format_live_gui_performance_flow_model_report(
    model: LiveGuiPerformanceFlowModel,
) -> tuple[str, ...]:
    """Return deterministic operator-readable performance flow lines."""

    lines: list[str] = [
        REPORT_TITLE,
        "",
        f"Flow: {model.flow_id} / {model.flow_status}",
        f"Current step: {model.current_step_key}",
        "",
        "Performance flow:",
    ]
    for step in model.steps:
        position = _live_gui_performance_flow_position(
            step=step,
            current_step_key=model.current_step_key,
        )
        lines.append(
            f"- {position}: {step.key} | {step.rytm_command} | "
            f"{step.send_policy} | {step.status}"
        )
        lines.append(
            f"  {step.label} / {step.phase}; A4: {step.analog_four_action}; "
            f"recovery: {step.recovery_action}"
        )
    lines.extend(("", "A4 macro readiness:"))
    lines.append(f"- readiness: {model.analog_four_readiness.readiness}")
    lines.append(f"- command: {model.analog_four_readiness.command}")
    lines.append(f"- summary: {model.analog_four_readiness.summary}")
    lines.append(
        "- blocked active actions: "
        f"{', '.join(model.analog_four_readiness.blocked_active_actions)}"
    )
    lines.extend(("", "A4 set plan:"))
    lines.append(f"- set: {model.analog_four_set_plan.set_name}")
    lines.append(f"- current macro: {model.analog_four_set_plan.current_macro}")
    lines.append(f"- up next: {', '.join(model.analog_four_set_plan.up_next_macros)}")
    lines.append(f"- replay: {model.analog_four_set_plan.replay_command}")
    lines.append(f"- summary: {model.analog_four_set_plan.summary}")
    lines.append(
        "- blocked active actions: "
        f"{', '.join(model.analog_four_set_plan.blocked_active_actions)}"
    )
    lines.extend(("", "Replay commands:"))
    lines.extend(f"- {command}" for command in model.replay_commands)
    lines.extend(("", "Passive safety:"))
    lines.extend(f"- {line}" for line in model.safety_lines)
    lines.extend(("", "Blocked actions:"))
    lines.extend(f"- {action}" for action in model.blocked_actions)
    return tuple(lines)


LIVE_GUI_PERFORMANCE_FLOW_MODEL_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "live-gui-performance-flow-model-report",
    "Print the passive live GUI performance flow model.",
    format_lines=lambda: format_live_gui_performance_flow_model_report(
        build_live_gui_performance_flow_model()
    ),
    build_payload=lambda: live_gui_performance_flow_model_payload(
        build_live_gui_performance_flow_model()
    ),
)

register(LIVE_GUI_PERFORMANCE_FLOW_MODEL_CLI_COMMAND)


__all__ = [
    "BLOCKED_ACTIONS",
    "CURRENT_STEP_KEY",
    "DEFAULT_STEPS",
    "FLOW_ID",
    "FLOW_STATUS",
    "DEFAULT_ANALOG_FOUR_READINESS",
    "DEFAULT_ANALOG_FOUR_SET_PLAN",
    "LIVE_GUI_PERFORMANCE_FLOW_MODEL_CLI_COMMAND",
    "LiveGuiAnalogFourReadiness",
    "LiveGuiAnalogFourReadinessDict",
    "LiveGuiAnalogFourSetPlan",
    "LiveGuiAnalogFourSetPlanDict",
    "LiveGuiPerformanceFlowModel",
    "LiveGuiPerformanceFlowModelDict",
    "LiveGuiPerformanceFlowStep",
    "LiveGuiPerformanceFlowStepDict",
    "MODEL_VERSION",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_live_gui_performance_flow_model",
    "format_live_gui_performance_flow_model_report",
    "live_gui_performance_flow_model_payload",
]
