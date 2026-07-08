"""Passive Analog Four patch capture-corpus report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, register
from ..guardrails.schema import Confidence, SourceType
from ..style_analysis import (
    StyleAnalysisDependencyError,
    extract_from_audio,
    extract_from_description,
)
from ..style_analysis.analog_four_patch_corpus import (
    ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX,
    ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN,
    ANALOG_FOUR_PATCH_CORPUS_SAFETY,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchCorpusEntry,
    AnalogFourPatchCorpusMatch,
    AnalogFourPatchCorpusMatchPacket,
    analog_four_patch_corpus_match_packet_to_dict,
    build_analog_four_patch_corpus_entry,
    build_analog_four_patch_corpus_match_packet,
    build_starter_analog_four_patch_corpus_entries,
)
from ..style_analysis.feature_report import FeatureReport
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive Analog Four patch capture corpus"
SOURCE_MODULE: Final[str] = "reports.analog_four_patch_corpus"
SAFETY_LINES: Final[tuple[str, ...]] = ANALOG_FOUR_PATCH_CORPUS_SAFETY
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-patch-corpus-report "
    "(--description <text>|--audio <path>) [--track N] [--limit N] "
    "[--corpus-file <path>] [--json]"
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class AnalogFourPatchCorpusReport:
    """Operator-facing report wrapper for passive A4 patch-corpus matching."""

    source_label: str
    source_value: str
    corpus_file: Path | None
    packet: AnalogFourPatchCorpusMatchPacket


def build_analog_four_patch_corpus_report(
    feature_report: FeatureReport,
    *,
    source_label: str,
    source_value: str,
    track: int,
    limit: int,
    corpus_file: Path | None,
) -> AnalogFourPatchCorpusReport:
    """Build a passive A4 patch-corpus report from a measured feature report."""

    entries = (
        _load_corpus_entries(corpus_file, default_track=track)
        if corpus_file is not None
        else build_starter_analog_four_patch_corpus_entries(track=track)
    )
    packet = build_analog_four_patch_corpus_match_packet(
        feature_report,
        entries=entries,
        limit=limit,
    )
    return AnalogFourPatchCorpusReport(
        source_label=source_label,
        source_value=source_value,
        corpus_file=corpus_file,
        packet=packet,
    )


def build_analog_four_patch_corpus_report_from_source(
    source_flag: str,
    source_value: str,
    *,
    track: int,
    limit: int,
    corpus_file: Path | None,
) -> AnalogFourPatchCorpusReport:
    """Build a passive corpus report from a description or audio-file source."""

    if source_flag == "--description":
        feature_report = extract_from_description(source_value)
    elif source_flag == "--audio":
        feature_report = extract_from_audio(Path(source_value))
    else:
        raise ValueError("source_flag must be --description or --audio")
    return build_analog_four_patch_corpus_report(
        feature_report,
        source_label=source_flag.removeprefix("--"),
        source_value=source_value,
        track=track,
        limit=limit,
        corpus_file=corpus_file,
    )


def format_analog_four_patch_corpus_report(
    report: AnalogFourPatchCorpusReport,
) -> list[str]:
    """Return deterministic operator-facing corpus-match lines."""

    packet = report.packet
    summary = packet.match_summary
    lines: list[str] = [
        "Summary:",
        f"- Source: {report.source_label}",
        f"- Source confidence: {packet.source_confidence}",
        f"- Source hash: {packet.source_hash}",
        f"- Corpus file: {_corpus_file_label(report.corpus_file)}",
        f"- Selected track: {packet.selected_track}",
        f"- Corpus readiness: {summary.readiness}",
        f"- Corpus entries: {summary.total_entries} total, "
        f"{summary.captured_count} captured, {summary.synthetic_count} synthetic",
        f"- Match count: {packet.match_count}",
        f"- Recommended candidate: {packet.recommended_candidate} / {packet.recommended_label}",
        "Nearest corpus matches:",
    ]
    lines.extend(_match_line(match) for match in packet.matches)
    lines.append("Calibration gaps:")
    lines.extend(f"- {gap}" for gap in packet.calibration_gaps)
    lines.append(SAFETY_SECTION_HEADER)
    lines.extend(f"- {line}" for line in packet.safety)
    return passive_report_lines(_HEADER, lines)


def build_analog_four_patch_corpus_payload(
    report: AnalogFourPatchCorpusReport,
) -> dict[str, object]:
    """Return deterministic machine-readable report payload."""

    return {
        "source": {
            "type": report.source_label,
            "value": report.source_value,
        },
        "selected_track": report.packet.selected_track,
        "corpus_file": str(report.corpus_file) if report.corpus_file is not None else None,
        "match_packet": analog_four_patch_corpus_match_packet_to_dict(report.packet),
        "safety": list(report.packet.safety),
    }


def _load_corpus_entries(
    path: Path,
    *,
    default_track: int,
) -> tuple[AnalogFourPatchCorpusEntry, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    root = _expect_mapping(payload, "corpus file")
    entries_value = root.get("entries")
    if not isinstance(entries_value, list):
        raise ValueError("corpus file must contain an entries list")
    return tuple(
        _corpus_entry_from_payload(_expect_mapping(item, "corpus entry"), default_track)
        for item in entries_value
    )


def _corpus_entry_from_payload(
    payload: Mapping[str, object],
    default_track: int,
) -> AnalogFourPatchCorpusEntry:
    feature_payload = _expect_mapping(payload.get("feature_report"), "feature_report")
    return build_analog_four_patch_corpus_entry(
        entry_id=_required_str(payload, "entry_id"),
        label=_required_str(payload, "label"),
        source_kind=_required_str(payload, "source_kind"),
        feature_report=_feature_report_from_payload(feature_payload),
        track=_optional_int(payload, "track", default_track),
        selected_candidate=_required_int(payload, "selected_candidate"),
        capture_notes=_optional_str_tuple(payload, "capture_notes"),
    )


def _feature_report_from_payload(payload: Mapping[str, object]) -> FeatureReport:
    return FeatureReport(
        source_type=SourceType(_required_str(payload, "source_type")),
        confidence=Confidence(_required_str(payload, "confidence")),
        bpm=_required_float(payload, "bpm"),
        tempo_stability=_required_float(payload, "tempo_stability"),
        kick_density=_required_float(payload, "kick_density"),
        percussion_density=_required_float(payload, "percussion_density"),
        low_end_weight=_required_float(payload, "low_end_weight"),
        spectral_brightness=_required_float(payload, "spectral_brightness"),
        texture_noise=_required_float(payload, "texture_noise"),
        energy_arc=_required_float_tuple(payload, "energy_arc"),
        content_hash=_optional_str(payload, "content_hash", ""),
        derived_at=_required_str(payload, "derived_at"),
    )


def _corpus_file_label(path: Path | None) -> str:
    if path is None:
        return "synthetic starter templates"
    return str(path)


def _match_line(match: AnalogFourPatchCorpusMatch) -> str:
    return (
        f"- {match.rank}. {match.entry_id} / {match.label} | {match.source_kind} | "
        f"candidate {match.selected_candidate} / {match.selected_label} | "
        f"similarity {match.similarity}% | bpm delta {match.bpm_delta} | "
        f"brightness delta {match.brightness_delta} | noise delta {match.noise_delta}"
    )


def _expect_mapping(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be an object")
    return value


def _required_str(payload: Mapping[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _optional_str(payload: Mapping[str, object], key: str, default: str) -> str:
    value = payload.get(key, default)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _required_int(payload: Mapping[str, object], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _optional_int(payload: Mapping[str, object], key: str, default: int) -> int:
    value = payload.get(key, default)
    if not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _required_float(payload: Mapping[str, object], key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, (int, float)):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _required_float_tuple(payload: Mapping[str, object], key: str) -> tuple[float, ...]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    floats: list[float] = []
    for item in value:
        if not isinstance(item, (int, float)):
            raise ValueError(f"{key} entries must be numeric")
        floats.append(float(item))
    return tuple(floats)


def _optional_str_tuple(payload: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    out: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{key} entries must be strings")
        out.append(item)
    return tuple(out)


def _parse_patch_corpus_int(value: str, *, option: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{option} must be an integer") from exc


def _validate_patch_corpus_range(
    value: int,
    *,
    option: str,
    minimum: int,
    maximum: int,
) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"{option} must be in {minimum}..{maximum}")


def _parse_analog_four_patch_corpus_args(argv: Sequence[str]) -> dict[str, object]:
    json_output = False
    track = 1
    limit = 4
    corpus_file: Path | None = None
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
            track = _parse_patch_corpus_int(argv[index + 1], option=option)
            index += 2
            continue
        if option == "--limit":
            if index + 1 >= len(argv):
                raise ValueError("--limit requires a value")
            limit = _parse_patch_corpus_int(argv[index + 1], option=option)
            index += 2
            continue
        if option == "--corpus-file":
            if index + 1 >= len(argv):
                raise ValueError("--corpus-file requires a value")
            corpus_file = Path(argv[index + 1])
            index += 2
            continue
        raise ValueError(f"unknown argument: {option}")

    if len(sources) != 1:
        raise ValueError(
            "analog-four-patch-corpus-report requires exactly one source: "
            "--description or --audio"
        )
    _validate_patch_corpus_range(
        track,
        option="--track",
        minimum=ANALOG_FOUR_TRACK_MIN,
        maximum=ANALOG_FOUR_TRACK_MAX,
    )
    _validate_patch_corpus_range(
        limit,
        option="--limit",
        minimum=ANALOG_FOUR_PATCH_CORPUS_LIMIT_MIN,
        maximum=ANALOG_FOUR_PATCH_CORPUS_LIMIT_MAX,
    )
    source_flag, source_value = sources[0]
    return {
        "source_flag": source_flag,
        "source_value": source_value,
        "track": track,
        "limit": limit,
        "corpus_file": corpus_file,
        "json_output": json_output,
    }


def _format_patch_corpus_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


def _handle_analog_four_patch_corpus_report(
    source_flag: str,
    source_value: str,
    track: int,
    limit: int,
    corpus_file: Path | None,
    json_output: bool = False,
) -> int:
    try:
        report = build_analog_four_patch_corpus_report_from_source(
            source_flag,
            source_value,
            track=track,
            limit=limit,
            corpus_file=corpus_file,
        )
    except (StyleAnalysisDependencyError, ValueError, TypeError, KeyError, OSError) as exc:
        sys.stderr.write(f"{_format_patch_corpus_error(exc)}\n")
        return 2

    if json_output:
        sys.stdout.write(
            json.dumps(
                build_analog_four_patch_corpus_payload(report),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0

    sys.stdout.write("\n".join(format_analog_four_patch_corpus_report(report)))
    sys.stdout.write("\n")
    return 0


ANALOG_FOUR_PATCH_CORPUS_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="analog-four-patch-corpus-report",
    summary=(
        "Rank reference audio or text against passive Analog Four patch " "capture-corpus examples."
    ),
    args_parser=_parse_analog_four_patch_corpus_args,
    handler=_handle_analog_four_patch_corpus_report,
    error_formatter=_format_patch_corpus_error,
)

register(ANALOG_FOUR_PATCH_CORPUS_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_CORPUS_CLI_COMMAND",
    "AnalogFourPatchCorpusReport",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "build_analog_four_patch_corpus_payload",
    "build_analog_four_patch_corpus_report",
    "build_analog_four_patch_corpus_report_from_source",
    "format_analog_four_patch_corpus_report",
]
