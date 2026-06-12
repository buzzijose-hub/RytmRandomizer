"""Passive Analog Four OXI macro set planner report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_four_oxi_macros import ANALOG_FOUR_OXI_MACROS
from .analog_four_oxi_macro_readiness import (
    build_analog_four_oxi_macro_readiness_report,
)
from .analog_four_oxi_macro_report import build_analog_four_oxi_macro_report
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four OXI macro set planner"
SOURCE_MODULE: Final[str] = "reports.analog_four_oxi_macro_set_planner"
DEFAULT_SET_NAME: Final[str] = "warehouse-arc"
DEFAULT_SEQUENCE: Final[tuple[str, ...]] = (
    "home",
    "hard-groove",
    "dub-pressure",
    "industrial-transition",
    "home",
)
REPLAY_COMMAND: Final[str] = (
    "python -m rytm_randomizer.cli analog-four-oxi-macro-set-planner-report --json"
)
BLOCKED_ACTIVE_ACTIONS: Final[tuple[str, ...]] = (
    "A4 full macro SEND",
    "A4 unattended macro playback",
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "A4 OXI macro set planning only",
    "manual-backed Analog Four CC metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "A4 full macro SEND remains blocked",
)
RECOVERY_ACTION: Final[str] = "reload saved A4 kit or return to home macro"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = (
    "analog-four-oxi-macro-set-planner-report usage: "
    "[--set-name <text>] [--sequence <macro,...>] [--seed N] [--json]"
)


@dataclass(frozen=True)
class AnalogFourOxiSetStep:
    """One passive Analog Four macro step in a set plan."""

    order: int
    macro_name: str
    macro_label: str
    summary: str
    seed: int
    intensity: int
    energy: int
    readiness: str
    event_count: int
    ready_count: int
    review_count: int
    blocked_count: int
    validation_command: str
    recovery_action: str


@dataclass(frozen=True)
class AnalogFourOxiSetPlannerReport:
    """Passive queue-shaped Analog Four OXI macro set plan."""

    title: str
    set_name: str
    steps: tuple[AnalogFourOxiSetStep, ...]
    current_step: AnalogFourOxiSetStep
    up_next: tuple[AnalogFourOxiSetStep, ...]
    opens_ports: bool
    sends_midi: bool
    hardware_required: bool
    blocked_active_actions: tuple[str, ...]
    safety: tuple[str, ...]
    replay_command: str


def _validate_sequence(sequence: Sequence[str]) -> tuple[str, ...]:
    resolved = tuple(macro.strip() for macro in sequence if macro.strip())
    if not resolved:
        raise ValueError("sequence must include at least one macro")
    return resolved


def _macro_intensity(macro_name: str) -> int:
    if macro_name not in ANALOG_FOUR_OXI_MACROS:
        build_analog_four_oxi_macro_report(macro_name)
    return max(0, min(7, ANALOG_FOUR_OXI_MACROS[macro_name].energy))


def _step_validation_command(
    *,
    macro_name: str,
    seed: int,
    intensity: int,
) -> str:
    return (
        "analog-four-oxi-macro-readiness-report "
        f"{macro_name} --seed {seed} --intensity {intensity} --limit 4"
    )


def _build_step(
    *,
    order: int,
    macro_name: str,
    seed: int,
) -> AnalogFourOxiSetStep:
    intensity = _macro_intensity(macro_name)
    macro_report = build_analog_four_oxi_macro_report(
        macro_name,
        seed=seed,
        intensity=intensity,
    )
    readiness = build_analog_four_oxi_macro_readiness_report(
        macro_report.macro_name,
        seed=seed,
        intensity=intensity,
    )
    return AnalogFourOxiSetStep(
        order=order,
        macro_name=macro_report.macro_name,
        macro_label=macro_report.macro_label,
        summary=macro_report.summary,
        seed=seed,
        intensity=intensity,
        energy=macro_report.energy,
        readiness=readiness.readiness,
        event_count=readiness.event_count,
        ready_count=readiness.ready_count,
        review_count=readiness.review_count,
        blocked_count=readiness.blocked_count,
        validation_command=_step_validation_command(
            macro_name=macro_report.macro_name,
            seed=seed,
            intensity=intensity,
        ),
        recovery_action=RECOVERY_ACTION,
    )


def build_analog_four_oxi_macro_set_planner_report(
    *,
    sequence: Sequence[str] = DEFAULT_SEQUENCE,
    set_name: str = DEFAULT_SET_NAME,
    seed: int = 0,
) -> AnalogFourOxiSetPlannerReport:
    """Return a deterministic passive Analog Four OXI macro set plan."""

    resolved_sequence = _validate_sequence(sequence)
    steps = tuple(
        _build_step(order=index + 1, macro_name=macro_name, seed=seed + index)
        for index, macro_name in enumerate(resolved_sequence)
    )
    return AnalogFourOxiSetPlannerReport(
        title=REPORT_TITLE,
        set_name=set_name,
        steps=steps,
        current_step=steps[0],
        up_next=steps[1:],
        opens_ports=False,
        sends_midi=False,
        hardware_required=False,
        blocked_active_actions=BLOCKED_ACTIVE_ACTIONS,
        safety=SAFETY_LINES,
        replay_command=REPLAY_COMMAND,
    )


def _step_line(step: AnalogFourOxiSetStep) -> str:
    return (
        f"{step.order}. {step.macro_name} / {step.macro_label} | "
        f"seed={step.seed} | intensity={step.intensity} | "
        f"energy={step.energy} | readiness={step.readiness} | "
        f"events={step.event_count}"
    )


def _a4_macro_set_planner_body_lines(
    report: AnalogFourOxiSetPlannerReport,
) -> list[str]:
    lines = [
        f"Set: {report.set_name}",
        f"Step count: {len(report.steps)}",
        f"Current: {report.current_step.macro_name} / {report.current_step.macro_label}",
        "Up next: "
        + (", ".join(step.macro_name for step in report.up_next) if report.up_next else "none"),
        "Plan steps:",
    ]
    for step in report.steps:
        lines.extend(
            [
                _step_line(step),
                f"  summary: {step.summary}",
                f"  validation: {step.validation_command}",
                f"  recovery: {step.recovery_action}",
                (
                    "  readiness counts: "
                    f"ready={step.ready_count}, review={step.review_count}, "
                    f"blocked={step.blocked_count}"
                ),
            ]
        )
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_active_actions)
    lines.append(f"Replay command: {report.replay_command}")
    lines.append("Safety flags:")
    lines.extend(
        (
            f"- opens_ports: {report.opens_ports}",
            f"- sends_midi: {report.sends_midi}",
            f"- hardware_required: {report.hardware_required}",
        )
    )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in report.safety)
    return lines


def format_analog_four_oxi_macro_set_planner_report(
    report: AnalogFourOxiSetPlannerReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing A4 macro set planner lines."""

    resolved_report = (
        report if report is not None else build_analog_four_oxi_macro_set_planner_report()
    )
    return passive_report_lines(
        _HEADER,
        _a4_macro_set_planner_body_lines(resolved_report),
    )


def _a4_macro_set_planner_step_payload(
    step: AnalogFourOxiSetStep,
) -> dict[str, object]:
    return {
        "order": step.order,
        "macro_name": step.macro_name,
        "macro_label": step.macro_label,
        "summary": step.summary,
        "seed": step.seed,
        "intensity": step.intensity,
        "energy": step.energy,
        "readiness": step.readiness,
        "event_count": step.event_count,
        "ready_count": step.ready_count,
        "review_count": step.review_count,
        "blocked_count": step.blocked_count,
        "validation_command": step.validation_command,
        "recovery_action": step.recovery_action,
    }


def build_analog_four_oxi_macro_set_planner_payload(
    report: AnalogFourOxiSetPlannerReport,
) -> dict[str, object]:
    """Return machine-readable passive A4 macro set planner metadata."""

    return {
        "title": report.title,
        "set_name": report.set_name,
        "step_count": len(report.steps),
        "current_step": _a4_macro_set_planner_step_payload(report.current_step),
        "up_next": [_a4_macro_set_planner_step_payload(step) for step in report.up_next],
        "steps": [_a4_macro_set_planner_step_payload(step) for step in report.steps],
        "opens_ports": report.opens_ports,
        "sends_midi": report.sends_midi,
        "hardware_required": report.hardware_required,
        "blocked_active_actions": list(report.blocked_active_actions),
        "safety": list(report.safety),
        "replay_command": report.replay_command,
    }


def _parse_a4_macro_set_planner_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _pop_a4_macro_set_planner_required_value(
    remaining: list[str],
    *,
    option: str,
) -> str:
    if not remaining:
        raise ValueError(f"{option} requires a value")
    return remaining.pop(0)


def _parse_sequence(value: str) -> tuple[str, ...]:
    return _validate_sequence(value.split(","))


def _parse_set_planner_args(argv: Sequence[str]) -> dict[str, object]:
    set_name = DEFAULT_SET_NAME
    sequence = DEFAULT_SEQUENCE
    seed = 0
    json_output = False
    remaining = list(argv)
    while remaining:
        argument = remaining.pop(0)
        if argument == "--json":
            json_output = True
            continue
        if argument in {"--set-name", "--sequence", "--seed"}:
            value = _pop_a4_macro_set_planner_required_value(
                remaining,
                option=argument,
            )
            if argument == "--set-name":
                set_name = value
            elif argument == "--sequence":
                sequence = _parse_sequence(value)
            else:
                seed = _parse_a4_macro_set_planner_int(value, option=argument)
            continue
        raise ValueError(f"unknown argument: {argument}")
    return {
        "set_name": set_name,
        "sequence": sequence,
        "seed": seed,
        "json_output": json_output,
    }


def _handle_set_planner_report(
    *,
    set_name: str,
    sequence: Sequence[str],
    seed: int,
    json_output: bool,
) -> int:
    try:
        report = build_analog_four_oxi_macro_set_planner_report(
            sequence=sequence,
            set_name=set_name,
            seed=seed,
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    build_analog_four_oxi_macro_set_planner_payload(report),
                    indent=2,
                    sort_keys=True,
                )
            )
            sys.stdout.write("\n")
            return 0
        lines = format_analog_four_oxi_macro_set_planner_report(report)
    except (ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _format_set_planner_error(exc: Exception) -> str:
    return f"Error: {exc}\n{_USAGE}"


ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-oxi-macro-set-planner-report",
    summary="Print passive Analog Four OXI macro set-planner metadata.",
    args_parser=_parse_set_planner_args,
    handler=_handle_set_planner_report,
    error_formatter=_format_set_planner_error,
)

register(ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_OXI_MACRO_SET_PLANNER_CLI_COMMAND",
    "BLOCKED_ACTIVE_ACTIONS",
    "DEFAULT_SEQUENCE",
    "DEFAULT_SET_NAME",
    "RECOVERY_ACTION",
    "REPORT_TITLE",
    "REPLAY_COMMAND",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "AnalogFourOxiSetPlannerReport",
    "AnalogFourOxiSetStep",
    "build_analog_four_oxi_macro_set_planner_payload",
    "build_analog_four_oxi_macro_set_planner_report",
    "format_analog_four_oxi_macro_set_planner_report",
]
