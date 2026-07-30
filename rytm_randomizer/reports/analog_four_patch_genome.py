"""Passive Analog Four patch genome report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.analog_four_display import AnalogFourPatchValue
from ..observability.errors import BoundaryError
from ..style_analysis import (
    StyleAnalysisDependencyError,
    extract_from_description,
)
from ..style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_SAFETY,
    AnalogFourPatchCandidate,
    AnalogFourPatchGenome,
    analog_four_patch_candidate_to_dict,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from ..style_analysis.analog_four_patch_inference import (
    build_analog_four_audio_patch_genome_isolated,
)
from ..style_analysis.feature_report import FeatureReport
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four patch genome"
SOURCE_MODULE: Final[str] = "reports.analog_four_patch_genome"
SAFETY_LINES: Final[tuple[str, ...]] = ANALOG_FOUR_PATCH_SAFETY
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-patch-genome-report "
    "(--description <text>|--audio <path>) [--track N] [--candidate N] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class AnalogFourPatchGenomeReport:
    """Operator-facing report wrapper for a selected A4 patch candidate."""

    source_label: str
    source_value: str
    genome: AnalogFourPatchGenome
    selected_candidate: int

    @property
    def selected(self) -> AnalogFourPatchCandidate:
        """Return the selected 1-based candidate."""

        return self.genome.candidates[self.selected_candidate - 1]


def build_analog_four_patch_genome_report(
    feature_report: FeatureReport,
    *,
    source_label: str,
    source_value: str,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchGenomeReport:
    """Build a passive A4 patch-genome report from a measured feature report."""

    genome = build_analog_four_patch_genome(feature_report, track=track)
    _validate_selected_candidate(selected_candidate, genome=genome)
    return AnalogFourPatchGenomeReport(
        source_label=source_label,
        source_value=source_value,
        genome=genome,
        selected_candidate=selected_candidate,
    )


def build_analog_four_patch_genome_report_from_source(
    source_flag: str,
    source_value: str,
    *,
    track: int,
    selected_candidate: int,
) -> AnalogFourPatchGenomeReport:
    """Build a passive report from a description or audio-file source."""

    if source_flag == "--description":
        feature_report = extract_from_description(source_value)
        return build_analog_four_patch_genome_report(
            feature_report,
            source_label="description",
            source_value=source_value,
            track=track,
            selected_candidate=selected_candidate,
        )
    if source_flag == "--audio":
        audio_genome = build_analog_four_audio_patch_genome_isolated(
            Path(source_value),
            track=track,
        )
        _validate_selected_candidate(selected_candidate, genome=audio_genome.genome)
        return AnalogFourPatchGenomeReport(
            source_label="audio",
            source_value=source_value,
            genome=audio_genome.genome,
            selected_candidate=selected_candidate,
        )
    raise ValueError("source_flag must be --description or --audio")


def format_analog_four_patch_genome_report(
    report: AnalogFourPatchGenomeReport,
) -> list[str]:
    """Return deterministic operator-facing patch DNA lines."""

    selected = report.selected
    genome = report.genome
    lines: list[str] = [
        "Summary:",
        f"- Source: {report.source_label}",
        f"- Source confidence: {genome.source_confidence.value}",
        f"- Source hash: {genome.source_hash}",
        f"- Selected track: {genome.selected_track}",
        f"- Candidate count: {genome.candidate_count}",
        f"- Selected candidate: {report.selected_candidate} / {selected.label}",
        "Reference traits:",
    ]
    lines.extend(
        f"- {trait.label}: {trait.intensity}% ({', '.join(trait.evidence)})"
        for trait in genome.traits
    )
    lines.append("Candidate columns:")
    lines.extend(
        f"- {candidate.column} / {candidate.label}: {candidate.role}; "
        f"closeness {candidate.closeness}%"
        for candidate in genome.candidates
    )
    lines.append("Patch DNA:")
    lines.extend(_gene_line(gene.value, gene.rationale) for gene in selected.genes)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in genome.safety)
    return passive_report_lines(_HEADER, lines)


def build_analog_four_patch_genome_payload(
    report: AnalogFourPatchGenomeReport,
) -> dict[str, object]:
    """Return deterministic machine-readable report payload."""

    return {
        "source": {
            "type": report.source_label,
            "value": report.source_value,
        },
        "selected_candidate": report.selected_candidate,
        "selected_track": report.genome.selected_track,
        "selected": analog_four_patch_candidate_to_dict(report.selected),
        "genome": analog_four_patch_genome_to_dict(report.genome),
        "safety": list(report.genome.safety),
    }


def _gene_line(value: AnalogFourPatchValue, rationale: str) -> str:
    return (
        f"- {value.section} {value.encoder} {value.parameter} | "
        f"screen {value.screen_value} | {_transport_phrase(value)} | "
        f"{value.transport_status} | {value.dial_direction} | {rationale}"
    )


def _transport_phrase(value: AnalogFourPatchValue) -> str:
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


def _validate_selected_candidate(
    selected_candidate: int,
    *,
    genome: AnalogFourPatchGenome,
) -> None:
    if selected_candidate < 1 or selected_candidate > genome.candidate_count:
        raise ValueError(f"candidate must be in 1..{genome.candidate_count}")


def _parse_patch_genome_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _validate_range(value: int, *, option: str, minimum: int, maximum: int) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"{option} must be in {minimum}..{maximum}")


def _parse_analog_four_patch_genome_args(argv: Sequence[str]) -> dict[str, object]:
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
            track = _parse_patch_genome_int(argv[index + 1], option=option)
            index += 2
            continue
        if option == "--candidate":
            if index + 1 >= len(argv):
                raise ValueError("--candidate requires a value")
            selected_candidate = _parse_patch_genome_int(argv[index + 1], option=option)
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")

    if len(sources) != 1:
        raise ValueError(
            "analog-four-patch-genome-report requires exactly one source: "
            "--description or --audio"
        )
    _validate_range(track, option="--track", minimum=1, maximum=4)
    _validate_range(selected_candidate, option="--candidate", minimum=1, maximum=4)
    source_flag, source_value = sources[0]
    return {
        "source_flag": source_flag,
        "source_value": source_value,
        "track": track,
        "selected_candidate": selected_candidate,
        "json_output": json_output,
    }


def _format_patch_genome_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_analog_four_patch_genome_report(
    source_flag: str,
    source_value: str,
    track: int,
    selected_candidate: int,
    json_output: bool = False,
) -> int:
    try:
        report = build_analog_four_patch_genome_report_from_source(
            source_flag,
            source_value,
            track=track,
            selected_candidate=selected_candidate,
        )
    except (
        BoundaryError,
        StyleAnalysisDependencyError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        sys.stderr.write(f"{_format_patch_genome_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                build_analog_four_patch_genome_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_analog_four_patch_genome_report(report)))
    sys.stdout.write("\n")
    return 0


ANALOG_FOUR_PATCH_GENOME_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-patch-genome-report",
    summary="Generate four passive Analog Four patch DNA candidates from audio or text.",
    args_parser=_parse_analog_four_patch_genome_args,
    handler=_handle_analog_four_patch_genome_report,
    error_formatter=_format_patch_genome_error,
)

register(ANALOG_FOUR_PATCH_GENOME_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_GENOME_CLI_COMMAND",
    "AnalogFourPatchGenomeReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "build_analog_four_patch_genome_payload",
    "build_analog_four_patch_genome_report",
    "build_analog_four_patch_genome_report_from_source",
    "format_analog_four_patch_genome_report",
]
