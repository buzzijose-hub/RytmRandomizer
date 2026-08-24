"""Passive long-form reference-audio atlas report."""

from __future__ import annotations

import json
import math
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, make_parsed_cli_command, register
from ..observability.errors import BoundaryError
from ..style_analysis import StyleAnalysisDependencyError
from ..style_analysis.reference_audio_atlas import (
    REFERENCE_AUDIO_ATLAS_SAFETY,
    ReferenceAudioAtlas,
    ReferenceAudioAtlasConfig,
    build_reference_audio_atlas,
    reference_audio_atlas_to_dict,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive reference-audio atlas"
SOURCE_MODULE: Final[str] = "reports.reference_audio_atlas"
SAFETY_LINES: Final[tuple[str, ...]] = REFERENCE_AUDIO_ATLAS_SAFETY
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli reference-audio-atlas-report "
    "--audio <path> [--window-seconds N] [--hop-seconds N] "
    "[--max-windows N] [--moments N] [--min-novelty N] "
    "[--track N] [--candidates N] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


def _require_report_reference_audio_atlas(value: object) -> ReferenceAudioAtlas:
    if not isinstance(value, ReferenceAudioAtlas):
        raise TypeError("atlas must be a ReferenceAudioAtlas")
    return value


def format_reference_audio_atlas_report(atlas: ReferenceAudioAtlas) -> list[str]:
    """Return a concise, chronological operator report."""

    atlas = _require_report_reference_audio_atlas(atlas)
    lines: list[str] = [
        "Summary:",
        f"- Source: {atlas.source_path}",
        f"- Duration: {_timestamp(atlas.duration_seconds)}",
        f"- Window / hop: {atlas.window_seconds:g}s / {atlas.hop_seconds:g}s",
        f"- Windows analyzed: {atlas.analyzed_windows}",
        f"- Analysis truncated by resource cap: {'yes' if atlas.truncated else 'no'}",
        f"- Distinct moments selected: {len(atlas.moments)}",
        f"- Analysis ID: {atlas.analysis_id}",
        "Chronological DNA moments:",
    ]
    for moment in atlas.moments:
        report = moment.feature_report
        candidate_labels = ", ".join(
            candidate.label for candidate in moment.patch_genome.candidates
        )
        trait_labels = ", ".join(trait.label for trait in moment.blueprint.traits)
        lines.extend(
            (
                f"- Moment {moment.sequence}: {_timestamp(moment.start_seconds)} to "
                f"{_timestamp(moment.end_seconds)} | novelty {moment.novelty:.3f}",
                f"  Measurements: {report.bpm:.1f} BPM; low end "
                f"{report.low_end_weight:.2f}; brightness "
                f"{report.spectral_brightness:.2f}; texture {report.texture_noise:.2f}",
                f"  A4 candidate DNA: {candidate_labels}",
                f"  Rytm/A4 blueprint traits: {trait_labels}",
            )
        )
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in atlas.safety)
    return passive_report_lines(_HEADER, lines)


def _parse_reference_audio_atlas_args(argv: Sequence[str]) -> dict[str, object]:
    values: dict[str, str] = {}
    json_output = False
    index = 0
    value_options = {
        "--audio",
        "--window-seconds",
        "--hop-seconds",
        "--max-windows",
        "--moments",
        "--min-novelty",
        "--track",
        "--candidates",
    }
    while index < len(argv):
        option = argv[index]
        if option == "--json":
            json_output = True
            index += 1
            continue
        if option not in value_options:
            raise ValueError(f"unknown argument: {option}")
        if index + 1 >= len(argv):
            raise ValueError(f"{option} requires a value")
        if option in values:
            raise ValueError(f"{option} may be supplied only once")
        values[option] = argv[index + 1]
        index += 2

    if "--audio" not in values:
        raise ValueError("reference-audio-atlas-report requires --audio")
    config = ReferenceAudioAtlasConfig(
        window_seconds=_parse_float(values.get("--window-seconds", "30"), "--window-seconds"),
        hop_seconds=_parse_float(values.get("--hop-seconds", "30"), "--hop-seconds"),
        max_windows=_parse_atlas_int(values.get("--max-windows", "240"), "--max-windows"),
        max_moments=_parse_atlas_int(values.get("--moments", "8"), "--moments"),
        min_novelty=_parse_float(values.get("--min-novelty", "0.08"), "--min-novelty"),
        track=_parse_atlas_int(values.get("--track", "1"), "--track"),
        candidate_count=_parse_atlas_int(values.get("--candidates", "4"), "--candidates"),
    )
    return {
        "audio_path": values["--audio"],
        "config": config,
        "json_output": json_output,
    }


def _parse_float(value: str, option: str) -> float:
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be numeric") from exc
    if not math.isfinite(parsed):
        raise ValueError(f"{option} must be finite")
    return parsed


def _parse_atlas_int(value: str, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _format_reference_audio_atlas_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_reference_audio_atlas_report(
    audio_path: str,
    config: ReferenceAudioAtlasConfig,
    json_output: bool = False,
) -> int:
    try:
        atlas = build_reference_audio_atlas(Path(audio_path), config=config)
    except (
        BoundaryError,
        StyleAnalysisDependencyError,
        OSError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        sys.stderr.write(f"{_format_reference_audio_atlas_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                reference_audio_atlas_to_dict(atlas),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_reference_audio_atlas_report(atlas)))
    sys.stdout.write("\n")
    return 0


def _timestamp(seconds: float) -> str:
    total_seconds = max(0, int(round(seconds)))
    hours, remainder = divmod(total_seconds, 3_600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


REFERENCE_AUDIO_ATLAS_CLI_COMMAND: Final[CliCommand] = make_parsed_cli_command(
    name="reference-audio-atlas-report",
    summary="Analyze bounded windows and report distinct passive patch-DNA moments.",
    args_parser=_parse_reference_audio_atlas_args,
    handler=_handle_reference_audio_atlas_report,
    error_formatter=_format_reference_audio_atlas_error,
)

register(REFERENCE_AUDIO_ATLAS_CLI_COMMAND)

__all__ = [
    "REFERENCE_AUDIO_ATLAS_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "format_reference_audio_atlas_report",
]
