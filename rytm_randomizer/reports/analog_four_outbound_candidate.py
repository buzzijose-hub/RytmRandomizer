"""Passive Analog Four outbound-candidate validation report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four outbound candidate"
SOURCE_MODULE: Final[str] = "reports.analog_four_outbound_candidate"
STATUS: Final[str] = "candidate-only"
CANDIDATE_PARAMETER: Final[str] = "OSC1 PWM Depth"
CANDIDATE_VALUE: Final[int] = 32
TRACKS: Final[tuple[int, ...]] = (1, 2, 3, 4)
BLOCKED_ACTIVE_ACTIONS: Final[tuple[str, ...]] = (
    "A4 outbound CC send",
    "A4 outbound macro send",
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "candidate-only A4 outbound validation visibility",
    "manual-backed A4 Appendix D table",
    "no real MIDI rendering",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
REPLAY_COMMANDS: Final[tuple[str, ...]] = (
    "python -m rytm_randomizer.cli analog-four-outbound-candidate-report",
    "python -m rytm_randomizer.cli analog-four-outbound-candidate-report --json",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_USAGE: Final[str] = "analog-four-outbound-candidate-report usage: [--json]"


@dataclass(frozen=True)
class AnalogFourOutboundCandidate:
    """One passive A4 outbound candidate row for manual validation."""

    track: int
    mido_channel: int
    parameter: str
    section: str
    encoder: str
    cc_msb: int
    value: int
    source: str
    readiness: str


@dataclass(frozen=True)
class AnalogFourValidationGate:
    """One ordered validation gate before active A4 sends are promoted."""

    name: str
    operator_action: str
    expected_evidence: str
    promotion_rule: str


@dataclass(frozen=True)
class AnalogFourOutboundCandidateReport:
    """Passive A4 candidate packet for operator and GUI review."""

    title: str
    status: str
    candidate_rows: tuple[AnalogFourOutboundCandidate, ...]
    validation_ladder: tuple[AnalogFourValidationGate, ...]
    blocked_active_actions: tuple[str, ...]
    replay_commands: tuple[str, ...]
    safety: tuple[str, ...]
    opens_ports: bool
    sends_midi: bool
    hardware_required: bool
    source_module: str


def _candidate_row(track: int) -> AnalogFourOutboundCandidate:
    mapping = ANALOG_FOUR_SYNTH_TRACK_CC[CANDIDATE_PARAMETER]
    if mapping.cc_msb is None:
        raise ValueError(f"candidate parameter {CANDIDATE_PARAMETER!r} has no CC MSB")
    return AnalogFourOutboundCandidate(
        track=track,
        mido_channel=track - 1,
        parameter=mapping.parameter,
        section=mapping.section,
        encoder=mapping.encoder,
        cc_msb=mapping.cc_msb,
        value=CANDIDATE_VALUE,
        source="manual-backed A4 Appendix D table",
        readiness="blocked pending manual hardware validation",
    )


def _validation_ladder() -> tuple[AnalogFourValidationGate, ...]:
    return (
        AnalogFourValidationGate(
            name="passive-input-observation",
            operator_action=(
                "Open A4 input only and observe the hardware-emitted CC row "
                "for OSC1 PWM Depth on tracks 1-4."
            ),
            expected_evidence="observed direct CC74 rows match the manual-backed mapping",
            promotion_rule="continue only if no output port opens and no MIDI is sent",
        ),
        AnalogFourValidationGate(
            name="mock-candidate-proof",
            operator_action="Render the candidate rows through a mock sender only.",
            expected_evidence="mock messages match track channels 0-3, CC74, value 32",
            promotion_rule="continue only after deterministic mock proof is committed",
        ),
        AnalogFourValidationGate(
            name="dry-run-helper",
            operator_action="Add an explicit dry-run helper for this candidate row.",
            expected_evidence="dry-run transcript shows candidate messages without port opening",
            promotion_rule="continue only after passive CLI safety sweep covers the helper",
        ),
        AnalogFourValidationGate(
            name="manual-armed-validation",
            operator_action=(
                "With Jose present, arm one explicit A4 output validation and "
                "send exactly one candidate CC."
            ),
            expected_evidence="operator confirms the A4 changed as expected and restored cleanly",
            promotion_rule="active macro sends remain blocked until this passes",
        ),
    )


def build_analog_four_outbound_candidate_report() -> AnalogFourOutboundCandidateReport:
    """Return a deterministic passive A4 outbound-candidate report."""

    return AnalogFourOutboundCandidateReport(
        title=REPORT_TITLE,
        status=STATUS,
        candidate_rows=tuple(_candidate_row(track) for track in TRACKS),
        validation_ladder=_validation_ladder(),
        blocked_active_actions=BLOCKED_ACTIVE_ACTIONS,
        replay_commands=REPLAY_COMMANDS,
        safety=SAFETY_LINES,
        opens_ports=False,
        sends_midi=False,
        hardware_required=False,
        source_module=SOURCE_MODULE,
    )


def _candidate_line(candidate: AnalogFourOutboundCandidate) -> str:
    return (
        f"- Track {candidate.track} | mido channel {candidate.mido_channel} | "
        f"{candidate.parameter} | CC{candidate.cc_msb} -> {candidate.value} | "
        f"{candidate.section}/{candidate.encoder} | {candidate.readiness}"
    )


def _gate_line(index: int, gate: AnalogFourValidationGate) -> str:
    return (
        f"- Gate {index}: {gate.name} | action: {gate.operator_action} | "
        f"evidence: {gate.expected_evidence} | promotion: {gate.promotion_rule}"
    )


def _analog_four_outbound_candidate_body_lines(
    report: AnalogFourOutboundCandidateReport,
) -> list[str]:
    lines = [
        f"Analog Four outbound status: {report.status}",
        "Candidate rows:",
    ]
    lines.extend(_candidate_line(candidate) for candidate in report.candidate_rows)
    lines.append("Validation ladder:")
    lines.extend(
        _gate_line(index, gate) for index, gate in enumerate(report.validation_ladder, start=1)
    )
    lines.append("Blocked active actions:")
    lines.extend(f"- {action}" for action in report.blocked_active_actions)
    lines.append("blocked active actions: " + ", ".join(report.blocked_active_actions))
    lines.append("Replay commands:")
    lines.extend(f"- {command}" for command in report.replay_commands)
    lines.extend(
        [
            "Safety flags:",
            f"- opens_ports: {report.opens_ports}",
            f"- sends_midi: {report.sends_midi}",
            f"- hardware_required: {report.hardware_required}",
            SAFETY_SECTION_HEADER,
        ]
    )
    lines.extend(f"- {line}" for line in report.safety)
    return lines


def format_analog_four_outbound_candidate_report(
    report: AnalogFourOutboundCandidateReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing A4 outbound-candidate lines."""

    resolved_report = (
        report if report is not None else build_analog_four_outbound_candidate_report()
    )
    return passive_report_lines(
        _HEADER,
        _analog_four_outbound_candidate_body_lines(resolved_report),
    )


def build_analog_four_outbound_candidate_payload(
    report: AnalogFourOutboundCandidateReport | None = None,
) -> dict[str, object]:
    """Return deterministic GUI-ready A4 outbound-candidate payload data."""

    resolved_report = (
        report if report is not None else build_analog_four_outbound_candidate_report()
    )
    return {
        "title": resolved_report.title,
        "status": resolved_report.status,
        "candidate_rows": [asdict(candidate) for candidate in resolved_report.candidate_rows],
        "validation_ladder": [asdict(gate) for gate in resolved_report.validation_ladder],
        "blocked_active_actions": list(resolved_report.blocked_active_actions),
        "replay_commands": list(resolved_report.replay_commands),
        "safety": list(resolved_report.safety),
        "opens_ports": resolved_report.opens_ports,
        "sends_midi": resolved_report.sends_midi,
        "hardware_required": resolved_report.hardware_required,
        "source_module": resolved_report.source_module,
    }


def _parse_analog_four_outbound_candidate_args(argv: Sequence[str]) -> dict[str, bool]:
    if not argv:
        return {"json_output": False}
    if list(argv) == ["--json"]:
        return {"json_output": True}
    raise ValueError(_USAGE)


def _handle_analog_four_outbound_candidate_report(*, json_output: bool) -> int:
    report = build_analog_four_outbound_candidate_report()
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_analog_four_outbound_candidate_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    sys.stdout.write("\n".join(format_analog_four_outbound_candidate_report(report)))
    sys.stdout.write("\n")
    return 0


def _format_analog_four_outbound_candidate_error(exc: Exception) -> str:
    return f"Error: {exc}"


ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-outbound-candidate-report",
    summary="Print passive Analog Four outbound validation candidate metadata.",
    args_parser=_parse_analog_four_outbound_candidate_args,
    handler=_handle_analog_four_outbound_candidate_report,
    error_formatter=_format_analog_four_outbound_candidate_error,
)

register(ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_OUTBOUND_CANDIDATE_CLI_COMMAND",
    "AnalogFourOutboundCandidate",
    "AnalogFourOutboundCandidateReport",
    "AnalogFourValidationGate",
    "BLOCKED_ACTIVE_ACTIONS",
    "CANDIDATE_PARAMETER",
    "CANDIDATE_VALUE",
    "REPORT_TITLE",
    "REPLAY_COMMANDS",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STATUS",
    "build_analog_four_outbound_candidate_payload",
    "build_analog_four_outbound_candidate_report",
    "format_analog_four_outbound_candidate_report",
]
