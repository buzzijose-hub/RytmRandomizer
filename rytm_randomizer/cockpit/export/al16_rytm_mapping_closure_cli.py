"""Passive CLI for offline AL16 Analog Rytm mapping evidence."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, TypedDict, cast

from ...cli_registry import CliCommand, register
from .al16_rytm_mapping_closure import (
    analyze_mapping_capture_files,
    load_mapping_gap_paths,
    render_mapping_capture_report,
)
from .cli_options import pop_required_cli_value
from .file_export_contracts import safe_local_file_export_artifact_name
from .writer import atomic_write

COMMAND_NAME: Final[str] = "al16-rytm-mapping-evidence"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli al16-rytm-mapping-evidence "
    "--reference <baseline.syx> --configured <configured.syx> "
    "--recipe <recipe.yaml> --gap-manifest <manifest.json> --report <report.json>"
)


class Al16RytmMappingEvidenceArgs(TypedDict):
    """Parsed local-file arguments for one offline comparison."""

    reference_path: Path
    configured_path: Path
    recipe_path: Path
    gap_manifest_path: Path
    report_path: Path


def parse_al16_rytm_mapping_evidence_args(
    args: Sequence[str],
) -> Al16RytmMappingEvidenceArgs:
    """Parse explicit input and report paths for the passive evidence command."""

    values: dict[str, Path] = {}
    option_keys = {
        "--reference": "reference_path",
        "--configured": "configured_path",
        "--recipe": "recipe_path",
        "--gap-manifest": "gap_manifest_path",
        "--report": "report_path",
    }
    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        key = option_keys.get(option)
        if key is None:
            raise ValueError(f"unknown option {option!r}")
        if key in values:
            raise ValueError(f"{option} may be supplied only once")
        values[key] = Path(pop_required_cli_value(remaining, option=option))

    for option, key in option_keys.items():
        if key not in values:
            raise ValueError(f"{option} is required")
    return cast(Al16RytmMappingEvidenceArgs, values)


def _parse_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    return dict(parse_al16_rytm_mapping_evidence_args(args))


def _load_json_mapping(path: Path, *, label: str) -> Mapping[str, object]:
    value = cast(object, json.loads(path.read_text(encoding="utf-8")))
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must contain a JSON object")
    return cast(Mapping[str, object], value)


def handle_al16_rytm_mapping_evidence(
    *,
    reference_path: Path,
    configured_path: Path,
    recipe_path: Path,
    gap_manifest_path: Path,
    report_path: Path,
) -> int:
    """Analyze two local frames and atomically publish review-only evidence."""

    try:
        recipe = _load_json_mapping(recipe_path, label="AL16 recipe")
        manifest = _load_json_mapping(gap_manifest_path, label="AL16 manifest")
        semantic_paths = load_mapping_gap_paths(manifest)
        report = analyze_mapping_capture_files(
            reference_path=reference_path,
            configured_path=configured_path,
            recipe=recipe,
            semantic_paths=semantic_paths,
        )
        payload = render_mapping_capture_report(report).encode("utf-8")
        result = atomic_write(report_path, payload)
    except KeyboardInterrupt:
        sys.stderr.write(f"{USAGE}\nError [interrupted]: comparison interrupted.\n")
        return 130
    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as exc:
        report_name = safe_local_file_export_artifact_name(
            report_path,
            fallback="mapping-evidence.json",
        )
        sys.stderr.write(
            f"{USAGE}\nError [offline_evidence_failed]: "
            f"could not produce {report_name} ({type(exc).__name__}).\n"
        )
        return 2

    changed = sum(
        observation.status == "candidate_changed" for observation in report.candidate_observations
    )
    unresolved = sum(
        observation.status == "not_located" for observation in report.candidate_observations
    )
    sys.stdout.write(
        "AL16 Rytm mapping evidence written\n"
        f"report: {result.path}\n"
        f"mapping_gaps: {len(semantic_paths)}\n"
        f"candidate_locations_changed: {changed}\n"
        f"unresolved_locations: {unresolved}\n"
        f"other_changed_unpacked_offsets: {len(report.other_changed_unpacked_offsets)}\n"
        "promotion_status: review_required\n"
        "midi_ports_opened: 0\n"
    )
    return 0


def _format_mapping_evidence_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError [invalid_input]: {exc}"


AL16_RYTM_MAPPING_EVIDENCE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Compare two local Rytm kits for review-only AL16 mapping evidence.",
    args_parser=_parse_args_for_registry,
    handler=handle_al16_rytm_mapping_evidence,
    error_formatter=_format_mapping_evidence_cli_error,
)

register(AL16_RYTM_MAPPING_EVIDENCE_CLI_COMMAND)

__all__ = [
    "AL16_RYTM_MAPPING_EVIDENCE_CLI_COMMAND",
    "Al16RytmMappingEvidenceArgs",
    "COMMAND_NAME",
    "USAGE",
    "handle_al16_rytm_mapping_evidence",
    "parse_al16_rytm_mapping_evidence_args",
]
