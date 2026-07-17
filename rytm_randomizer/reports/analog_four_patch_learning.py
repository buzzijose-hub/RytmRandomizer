"""Passive Analog Four patch learning report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_four_display import AnalogFourPatchValue
from ..style_analysis import (
    StyleAnalysisDependencyError,
    extract_from_audio,
    extract_from_description,
)
from ..style_analysis.analog_four_patch_learning import (
    ANALOG_FOUR_PATCH_LEARNING_SAFETY,
    AnalogFourPatchLearningPacket,
    analog_four_patch_learning_packet_to_dict,
    build_analog_four_patch_learning_packet,
)
from ..style_analysis.feature_report import FeatureReport
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four patch learning"
SOURCE_MODULE: Final[str] = "reports.analog_four_patch_learning"
SAFETY_LINES: Final[tuple[str, ...]] = ANALOG_FOUR_PATCH_LEARNING_SAFETY
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-patch-learning-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class AnalogFourPatchLearningReport:
    """Operator-facing report wrapper for passive A4 patch learning."""

    source_label: str
    source_value: str
    packet: AnalogFourPatchLearningPacket


def build_analog_four_patch_learning_report(
    feature_report: FeatureReport,
    *,
    source_label: str,
    source_value: str,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchLearningReport:
    """Build a passive A4 patch-learning report from a measured feature report."""

    packet = build_analog_four_patch_learning_packet(
        feature_report,
        track=track,
        selected_candidate=selected_candidate,
    )
    return AnalogFourPatchLearningReport(
        source_label=source_label,
        source_value=source_value,
        packet=packet,
    )


def build_analog_four_patch_learning_report_from_source(
    source_flag: str,
    source_value: str,
    *,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchLearningReport:
    """Build a passive learning report from a description or audio-file source."""

    if source_flag == "--description":
        feature_report = extract_from_description(source_value)
    elif source_flag == "--audio":
        feature_report = extract_from_audio(Path(source_value))
    else:
        raise ValueError("source_flag must be --description or --audio")
    return build_analog_four_patch_learning_report(
        feature_report,
        source_label=source_flag.removeprefix("--"),
        source_value=source_value,
        track=track,
        selected_candidate=selected_candidate,
    )


def format_analog_four_patch_learning_report(
    report: AnalogFourPatchLearningReport,
) -> list[str]:
    """Return deterministic operator-facing patch-learning lines."""

    packet = report.packet
    readiness = packet.live_dial_readiness
    lines: list[str] = [
        "Summary:",
        f"- Source: {report.source_label}",
        f"- Source confidence: {packet.source_confidence}",
        f"- Source hash: {packet.source_hash}",
        f"- Learning mode: {packet.mode}",
        f"- Selected track: {packet.selected_track}",
        f"- Candidate count: {packet.genome.candidate_count}",
        f"- Selected candidate: {packet.selected_candidate} / {packet.selected_label}",
        "Candidate ranking:",
    ]
    lines.extend(
        f"- {score.rank}. Column {score.column} / {score.label}: "
        f"learning {score.learning_score}%, closeness {score.closeness}%, "
        f"trait-fit {score.trait_fit}%, transport {score.transport_readiness}%"
        for score in sorted(packet.candidate_scores, key=lambda item: item.rank)
    )
    lines.append("Knowledge acquisition routes:")
    lines.extend(
        f"- {route.trait_label} -> {_learning_route_targets(route.selected_parameters, route.parameter_focus)} "
        f"| intensity {route.intensity}% | {route.learning_question}"
        for route in packet.trait_routes
    )
    lines.append("Capture matrix:")
    lines.extend(
        f"- {step.step_id} | {step.note_name} | velocity {step.velocity} | "
        f"gate {step.gate_ms} ms | x{step.repeat_count} | {step.focus}"
        for step in packet.capture_steps
    )
    lines.extend(
        [
            "Live dial-in readiness:",
            f"- Path: {readiness.live_dial_path}",
            f"- Ready: {readiness.ready_count} / "
            f"{readiness.ready_count + readiness.pending_count} "
            f"({readiness.ready_percentage}%)",
            f"- Transport counts: cc-ready {readiness.cc_ready_count}, "
            f"nrpn-ready {readiness.nrpn_ready_count}, "
            f"screen-only-nrpn {readiness.screen_only_nrpn_count}, "
            f"screen-only {readiness.screen_only_count}",
            f"- Pending rows: {_learning_join_or_none(readiness.pending_parameters)}",
            f"- Blocker: {readiness.blocking_reason}",
            "Selected patch DNA:",
        ]
    )
    lines.extend(
        _learning_gene_line(gene.value, gene.rationale) for gene in packet.selected_patch.genes
    )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in packet.safety)
    return passive_report_lines(_HEADER, lines)


def build_analog_four_patch_learning_payload(
    report: AnalogFourPatchLearningReport,
) -> dict[str, object]:
    """Return deterministic machine-readable report payload."""

    return {
        "source": {
            "type": report.source_label,
            "value": report.source_value,
        },
        "selected_candidate": report.packet.selected_candidate,
        "selected_track": report.packet.selected_track,
        "learning_packet": analog_four_patch_learning_packet_to_dict(report.packet),
        "safety": list(report.packet.safety),
    }


def _learning_route_targets(
    selected_parameters: tuple[str, ...],
    parameter_focus: tuple[str, ...],
) -> str:
    targets = selected_parameters if selected_parameters else parameter_focus
    return ", ".join(targets)


def _learning_join_or_none(values: tuple[str, ...]) -> str:
    if not values:
        return "none"
    return ", ".join(values)


def _learning_gene_line(value: AnalogFourPatchValue, rationale: str) -> str:
    return (
        f"- {value.section} {value.encoder} {value.parameter} | "
        f"screen {value.screen_value} | {_learning_transport_phrase(value)} | "
        f"{value.transport_status} | {value.dial_direction} | {rationale}"
    )


def _learning_transport_phrase(value: AnalogFourPatchValue) -> str:
    parts: list[str] = []
    if value.cc_msb is not None and value.midi_value is not None:
        parts.append(f"MIDI CC{value.cc_msb} -> {value.midi_value}")
    if value.nrpn_address is not None:
        address = f"NRPN {value.nrpn_address[0]}:{value.nrpn_address[1]}"
        if value.cc_msb is None and value.midi_value is not None:
            parts.append(f"{address} -> {value.midi_value}")
        else:
            parts.append(address)
    if not parts:
        parts.append("front-panel only")
    return " | ".join(parts)


def _parse_patch_learning_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _validate_patch_learning_range(
    value: int,
    *,
    option: str,
    minimum: int,
    maximum: int,
) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"{option} must be in {minimum}..{maximum}")


def _parse_analog_four_patch_learning_args(argv: Sequence[str]) -> dict[str, object]:
    json_output = False
    track = 1
    selected_candidate = 1
    sources: list[tuple[str, str]] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option in ("--description", "--audio"):
            if index + 1 >= len(argv):
                raise ValueError(f"{option} requires a value")
            sources.append((option, argv[index + 1]))
            index += 2
            continue
        if option == "--track":
            if index + 1 >= len(argv):
                raise ValueError("--track requires a value")
            track = _parse_patch_learning_int(argv[index + 1], option=option)
            index += 2
            continue
        if option == "--candidate":
            if index + 1 >= len(argv):
                raise ValueError("--candidate requires a value")
            selected_candidate = _parse_patch_learning_int(argv[index + 1], option=option)
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")

    if len(sources) != 1:
        raise ValueError(
            "analog-four-patch-learning-report requires exactly one source: "
            "--description or --audio"
        )
    _validate_patch_learning_range(track, option="--track", minimum=1, maximum=4)
    _validate_patch_learning_range(
        selected_candidate,
        option="--candidate",
        minimum=1,
        maximum=4,
    )
    source_flag, source_value = sources[0]
    return {
        "source_flag": source_flag,
        "source_value": source_value,
        "track": track,
        "selected_candidate": selected_candidate,
        "json_output": json_output,
    }


def _format_patch_learning_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_analog_four_patch_learning_report(
    source_flag: str,
    source_value: str,
    track: int,
    selected_candidate: int,
    json_output: bool = False,
) -> int:
    try:
        report = build_analog_four_patch_learning_report_from_source(
            source_flag,
            source_value,
            track=track,
            selected_candidate=selected_candidate,
        )
    except (StyleAnalysisDependencyError, ValueError, TypeError, KeyError) as exc:
        sys.stderr.write(f"{_format_patch_learning_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                build_analog_four_patch_learning_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_analog_four_patch_learning_report(report)))
    sys.stdout.write("\n")
    return 0


ANALOG_FOUR_PATCH_LEARNING_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-patch-learning-report",
    summary=(
        "Generate passive Analog Four patch learning, ranking, and live-dial "
        "readiness from audio or text."
    ),
    args_parser=_parse_analog_four_patch_learning_args,
    handler=_handle_analog_four_patch_learning_report,
    error_formatter=_format_patch_learning_error,
)

register(ANALOG_FOUR_PATCH_LEARNING_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_LEARNING_CLI_COMMAND",
    "AnalogFourPatchLearningReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "build_analog_four_patch_learning_payload",
    "build_analog_four_patch_learning_report",
    "build_analog_four_patch_learning_report_from_source",
    "format_analog_four_patch_learning_report",
]
