"""Passive Rytm outbound CC repeatability readiness report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final, Literal, TypeAlias, TypedDict

from ..cli_registry import CliCommand, register
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm outbound CC repeatability report"
SOURCE_MODULE: Final[str] = "reports.rytm_outbound_cc_repeatability"
MODEL_VERSION: Final[str] = "rytm-outbound-cc-repeatability-v1"
DEFAULT_CONTROL: Final[int] = 17
DEFAULT_VALUE: Final[int] = 64
TRACK_COUNT: Final[int] = 12
SOURCE_EVIDENCE_PATH: Final[str] = (
    "docs/hardware-validation/2026-05-26-outbound-12-track-cc-results.md"
)
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report "
    "[--control <0-127>] [--value <0-127>] [--json]"
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "in-memory only",
    "GUI/operator readiness metadata only",
    "does not run the validation",
    "does not choose or open a MIDI port",
    "does not import real MIDI adapters",
    "no MIDI sending",
    "no port opening",
    "no hardware mutation",
    "no hardware required",
)
BLOCKED_ACTIONS: Final[tuple[str, ...]] = (
    "open MIDI port from repeatability report",
    "send MIDI from repeatability report",
    "run unattended hardware loop",
    "test new CC number in repeatability pass",
    "run scene or group mutation",
    "send SysEx",
    "touch Analog Four hardware",
)
STOP_CONDITIONS: Final[tuple[str, ...]] = (
    "any non-target pad changes",
    "target pad does not change",
    "hardware display or audio behaves unexpectedly",
    "wrong MIDI output port is selected",
    "operator cannot observe the result clearly",
)
NEXT_ACTIONS: Final[tuple[str, ...]] = (
    "repeat PR #133's one-CC all-12-track validation exactly",
    "record one observation row per track",
    "stop before testing any new CC number or mutation command",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)

ValidationMode: TypeAlias = Literal["repeatability"]


@dataclass(frozen=True)
class OutboundCcRepeatabilityStep:
    """One declarative manual validation step for a Rytm track."""

    track: int
    mido_channel: int
    control: int
    value: int
    command: str
    expected_result: str


class OutboundCcRepeatabilityStepDict(TypedDict):
    """JSON-ready contract for :class:`OutboundCcRepeatabilityStep`."""

    track: int
    mido_channel: int
    control: int
    value: int
    command: str
    expected_result: str


@dataclass(frozen=True)
class RytmOutboundCcRepeatabilityReport:
    """Passive repeatability packet for the next manual outbound CC pass."""

    model_version: str
    validation_mode: ValidationMode
    track_count: int
    control: int
    value: int
    source_evidence_path: str
    steps: tuple[OutboundCcRepeatabilityStep, ...]
    stop_conditions: tuple[str, ...]
    next_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    safety_lines: tuple[str, ...]
    replay_commands: tuple[str, ...]


class RytmOutboundCcRepeatabilityReportDict(TypedDict):
    """JSON-ready contract for :class:`RytmOutboundCcRepeatabilityReport`."""

    model_version: str
    validation_mode: ValidationMode
    track_count: int
    control: int
    value: int
    source_evidence_path: str
    steps: list[OutboundCcRepeatabilityStepDict]
    stop_conditions: list[str]
    next_actions: list[str]
    blocked_actions: list[str]
    replay_commands: list[str]


def _validate_cc_byte(value: int, *, field: str) -> int:
    if not (0 <= value <= 127):
        raise ValueError(f"{field} must be in [0, 127]; got {value}")
    return value


def _armed_command(*, channel: int, control: int, value: int) -> str:
    return (
        "python -m rytm_randomizer.app --arm --validate-one-cc "
        f"--channel {channel} --control {control} --value {value}"
    )


def _repeatability_report_replay_command(*, control: int, value: int) -> str:
    command = "python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report"
    if control == DEFAULT_CONTROL and value == DEFAULT_VALUE:
        return command
    return f"{command} --control {control} --value {value}"


def _step_for_track(*, track: int, control: int, value: int) -> OutboundCcRepeatabilityStep:
    channel = track - 1
    return OutboundCcRepeatabilityStep(
        track=track,
        mido_channel=channel,
        control=control,
        value=value,
        command=_armed_command(channel=channel, control=control, value=value),
        expected_result=f"Only Track {track} changes",
    )


def build_rytm_outbound_cc_repeatability_report(
    *,
    control: int = DEFAULT_CONTROL,
    value: int = DEFAULT_VALUE,
) -> RytmOutboundCcRepeatabilityReport:
    """Build a deterministic passive repeatability checklist for tracks 1-12."""

    normalized_control = _validate_cc_byte(control, field="control")
    normalized_value = _validate_cc_byte(value, field="value")
    steps = tuple(
        _step_for_track(track=track, control=normalized_control, value=normalized_value)
        for track in range(1, TRACK_COUNT + 1)
    )
    return RytmOutboundCcRepeatabilityReport(
        model_version=MODEL_VERSION,
        validation_mode="repeatability",
        track_count=TRACK_COUNT,
        control=normalized_control,
        value=normalized_value,
        source_evidence_path=SOURCE_EVIDENCE_PATH,
        steps=steps,
        stop_conditions=STOP_CONDITIONS,
        next_actions=NEXT_ACTIONS,
        blocked_actions=BLOCKED_ACTIONS,
        safety_lines=SAFETY_LINES,
        replay_commands=(
            _repeatability_report_replay_command(
                control=normalized_control,
                value=normalized_value,
            ),
        ),
    )


def _step_payload(step: OutboundCcRepeatabilityStep) -> OutboundCcRepeatabilityStepDict:
    return {
        "track": step.track,
        "mido_channel": step.mido_channel,
        "control": step.control,
        "value": step.value,
        "command": step.command,
        "expected_result": step.expected_result,
    }


def to_rytm_outbound_cc_repeatability_json(
    report: RytmOutboundCcRepeatabilityReport,
) -> dict[str, RytmOutboundCcRepeatabilityReportDict | list[str]]:
    """Return a deterministic JSON-ready payload for GUI/manual-test consumers."""

    return {
        "rytm_outbound_cc_repeatability": {
            "model_version": report.model_version,
            "validation_mode": report.validation_mode,
            "track_count": report.track_count,
            "control": report.control,
            "value": report.value,
            "source_evidence_path": report.source_evidence_path,
            "steps": [_step_payload(step) for step in report.steps],
            "stop_conditions": list(report.stop_conditions),
            "next_actions": list(report.next_actions),
            "blocked_actions": list(report.blocked_actions),
            "replay_commands": list(report.replay_commands),
        },
        "safety": list(report.safety_lines),
    }


def format_rytm_outbound_cc_repeatability_report(
    report: RytmOutboundCcRepeatabilityReport,
) -> list[str]:
    """Render the passive repeatability checklist as deterministic text."""

    body_lines = [
        "Summary:",
        f"- Model version: {report.model_version}",
        f"- Validation mode: {report.validation_mode}",
        f"- Tracks: {report.track_count}",
        f"- Control: {report.control}",
        f"- Value: {report.value}",
        f"- Source evidence: {report.source_evidence_path}",
        "Track steps:",
    ]
    body_lines.extend(
        f"- Track {step.track:02d} -> mido channel {step.mido_channel} / "
        f"CC {step.control} / value {step.value}: {step.expected_result}"
        for step in report.steps
    )
    body_lines.append("Stop conditions:")
    body_lines.extend(f"- {condition}" for condition in report.stop_conditions)
    body_lines.append("Next actions:")
    body_lines.extend(f"- {action}" for action in report.next_actions)
    body_lines.append("Blocked active actions:")
    body_lines.extend(f"- {action}" for action in report.blocked_actions)
    body_lines.append("Replay commands:")
    body_lines.extend(f"- {command}" for command in report.replay_commands)
    body_lines.append(SAFETY_SECTION_HEADER)
    body_lines.extend(f"- {line}" for line in report.safety_lines)
    return passive_report_lines(_HEADER, body_lines)


def _parse_int_arg(raw: str, *, option: str) -> int:
    try:
        return int(raw, 10)
    except ValueError as exc:
        raise ValueError(f"{option} requires an integer") from exc


def _parse_rytm_outbound_cc_repeatability_args(argv: Sequence[str]) -> dict[str, object]:
    control = DEFAULT_CONTROL
    value = DEFAULT_VALUE
    json_output = False
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option in ("--control", "--value"):
            if index + 1 >= len(argv):
                raise ValueError(f"{option} requires a value")
            parsed = _parse_int_arg(argv[index + 1], option=option)
            if option == "--control":
                control = parsed
            else:
                value = parsed
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")
    return {"control": control, "value": value, "json_output": json_output}


def _format_repeatability_report_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_rytm_outbound_cc_repeatability_report(
    *,
    control: int = DEFAULT_CONTROL,
    value: int = DEFAULT_VALUE,
    json_output: bool = False,
) -> int:
    try:
        report = build_rytm_outbound_cc_repeatability_report(control=control, value=value)
    except ValueError as exc:
        sys.stderr.write(f"{_format_repeatability_report_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                to_rytm_outbound_cc_repeatability_json(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_rytm_outbound_cc_repeatability_report(report)))
    sys.stdout.write("\n")
    return 0


RYTM_OUTBOUND_CC_REPEATABILITY_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="rytm-outbound-cc-repeatability-report",
    summary="Print a passive all-12-track outbound CC repeatability checklist.",
    args_parser=_parse_rytm_outbound_cc_repeatability_args,
    handler=_handle_rytm_outbound_cc_repeatability_report,
    error_formatter=_format_repeatability_report_error,
)

register(RYTM_OUTBOUND_CC_REPEATABILITY_CLI_COMMAND)


__all__ = [
    "BLOCKED_ACTIONS",
    "DEFAULT_CONTROL",
    "DEFAULT_VALUE",
    "MODEL_VERSION",
    "OutboundCcRepeatabilityStep",
    "OutboundCcRepeatabilityStepDict",
    "REPORT_TITLE",
    "RYTM_OUTBOUND_CC_REPEATABILITY_CLI_COMMAND",
    "RytmOutboundCcRepeatabilityReport",
    "RytmOutboundCcRepeatabilityReportDict",
    "SAFETY_LINES",
    "SOURCE_EVIDENCE_PATH",
    "SOURCE_MODULE",
    "STOP_CONDITIONS",
    "TRACK_COUNT",
    "USAGE",
    "build_rytm_outbound_cc_repeatability_report",
    "format_rytm_outbound_cc_repeatability_report",
    "to_rytm_outbound_cc_repeatability_json",
]
