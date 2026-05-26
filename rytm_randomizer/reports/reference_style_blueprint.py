"""Passive reference-style blueprint report."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..style_analysis import (
    ReferenceStyleBlueprint,
    StyleAnalysisDependencyError,
    analyze_library,
    build_reference_style_blueprint,
    extract_from_audio,
    extract_from_description,
    reference_style_blueprint_to_dict,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive reference-style blueprint report"
SOURCE_MODULE: Final[str] = "reports.reference_style_blueprint"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli reference-style-blueprint-report "
    "(--description <text>|--audio <path>|--library <dir>) [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


def build_reference_style_blueprint_from_source(
    source_flag: str,
    source_value: str,
) -> ReferenceStyleBlueprint:
    """Build a passive blueprint from one supported source."""

    if source_flag == "--description":
        report = extract_from_description(source_value)
    elif source_flag == "--audio":
        report = extract_from_audio(Path(source_value))
    elif source_flag == "--library":
        report = analyze_library(Path(source_value))
    else:
        raise ValueError("source_flag must be --description, --audio, or --library")
    return build_reference_style_blueprint(report)


def format_reference_style_blueprint_report(
    blueprint: ReferenceStyleBlueprint,
) -> list[str]:
    """Return deterministic operator-facing blueprint report lines."""

    lines: list[str] = [
        "Summary:",
        f"- Readiness: {blueprint.readiness}",
        f"- Source confidence: {blueprint.source_confidence.value}",
        f"- Source type: {blueprint.source_type.value}",
        f"- Source hash: {blueprint.source_hash}",
        f"- Blueprint hash: {blueprint.blueprint_hash}",
        f"- Analog Rytm pads: {len(blueprint.rytm_pads)}",
        f"- Analog Four tracks: {len(blueprint.analog_four_tracks)}",
        f"- Influence rule: {blueprint.influence_rule}",
        "Reference traits:",
    ]
    lines.extend(
        f"- {trait.label}: {trait.intensity}% " f"(evidence: {', '.join(trait.evidence)})"
        for trait in blueprint.traits
    )
    lines.append("Analog Rytm pad blueprint:")
    lines.extend(
        f"- Pad {pad.pad:02d} / {pad.role}: {pad.engine_family}; "
        f"depth {pad.mutation_depth}; focus {', '.join(pad.parameter_focus)}; "
        f"{pad.safety}"
        for pad in blueprint.rytm_pads
    )
    lines.append("Analog Four track blueprint:")
    lines.extend(
        f"- Track {track.track:02d} / {track.role}: {track.voice_intent}; "
        f"depth {track.mutation_depth}; focus {', '.join(track.parameter_focus)}; "
        f"modulation: {track.modulation}"
        for track in blueprint.analog_four_tracks
    )
    lines.extend(
        [
            SAFETY_SECTION_HEADER,
            *[f"- {line}" for line in blueprint.safety],
        ]
    )
    return passive_report_lines(_HEADER, lines)


def _parse_reference_style_blueprint_args(argv: Sequence[str]) -> dict[str, object]:
    json_output = False
    sources: list[tuple[str, str]] = []
    index = 0
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option in ("--description", "--audio", "--library"):
            if index + 1 >= len(argv):
                raise ValueError(f"{option} requires a value")
            sources.append((option, argv[index + 1]))
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")
    if len(sources) != 1:
        raise ValueError(
            "reference-style-blueprint-report requires exactly one source: "
            "--description, --audio, or --library"
        )
    source_flag, source_value = sources[0]
    return {
        "source_flag": source_flag,
        "source_value": source_value,
        "json_output": json_output,
    }


def _format_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_reference_style_blueprint_report(
    source_flag: str,
    source_value: str,
    json_output: bool = False,
) -> int:
    try:
        blueprint = build_reference_style_blueprint_from_source(source_flag, source_value)
    except (StyleAnalysisDependencyError, ValueError, TypeError) as exc:
        sys.stderr.write(f"{_format_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                reference_style_blueprint_to_dict(blueprint),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_reference_style_blueprint_report(blueprint)))
    sys.stdout.write("\n")
    return 0


REFERENCE_STYLE_BLUEPRINT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="reference-style-blueprint-report",
    summary="Translate a style reference into a passive Rytm plus Analog Four blueprint.",
    args_parser=_parse_reference_style_blueprint_args,
    handler=_handle_reference_style_blueprint_report,
    error_formatter=_format_error,
)

register(REFERENCE_STYLE_BLUEPRINT_CLI_COMMAND)

__all__ = [
    "REFERENCE_STYLE_BLUEPRINT_CLI_COMMAND",
    "REPORT_TITLE",
    "SOURCE_MODULE",
    "USAGE",
    "build_reference_style_blueprint_from_source",
    "format_reference_style_blueprint_report",
]
