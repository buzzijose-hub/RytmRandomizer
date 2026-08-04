"""Passive CLI for offline AL16 Analog Rytm mapping evidence."""

from __future__ import annotations

import sys
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict, cast

from ...cli_registry import CliCommand, register
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from .al16_rytm_mapping_closure import (
    analyze_mapping_capture_files,
    render_mapping_capture_report,
)
from .cli_options import pop_required_cli_value
from .file_export_contracts import (
    LocalFileExportPhase,
    classify_local_file_export_error,
    safe_local_file_export_artifact_name,
    validate_distinct_local_file_export_paths,
    validate_local_file_export_artifact_path,
)
from .writer import atomic_write

COMMAND_NAME: Final[str] = "al16-rytm-mapping-evidence"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli al16-rytm-mapping-evidence "
    "--reference <baseline.syx> --configured <configured.syx> "
    "--recipe <recipe.yaml> --gap-manifest <manifest.json> --report <report.json>"
)
_OPERATION: Final[str] = "al16_rytm_mapping_evidence"
_FAILURE_FINGERPRINT: Final[str] = "al16.rytm_mapping_evidence.failed"
_logger = get_logger(__name__)


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
            raise ValueError("unknown option")
        if key in values:
            raise ValueError(f"{option} may be supplied only once")
        values[key] = Path(pop_required_cli_value(remaining, option=option))

    for option, key in option_keys.items():
        if key not in values:
            raise ValueError(f"{option} is required")
    return cast(Al16RytmMappingEvidenceArgs, values)


def _parse_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    return dict(parse_al16_rytm_mapping_evidence_args(args))


def handle_al16_rytm_mapping_evidence(
    *,
    reference_path: Path,
    configured_path: Path,
    recipe_path: Path,
    gap_manifest_path: Path,
    report_path: Path,
) -> int:
    """Analyze two local frames and atomically publish review-only evidence."""

    metrics = get_metrics()
    started_at = time.perf_counter()
    export_phase: LocalFileExportPhase = "validation"
    operation_id = ""
    reference_name = safe_local_file_export_artifact_name(
        reference_path,
        fallback="reference.syx",
    )
    configured_name = safe_local_file_export_artifact_name(
        configured_path,
        fallback="configured.syx",
    )
    recipe_name = safe_local_file_export_artifact_name(
        recipe_path,
        fallback="recipe.yaml",
    )
    gap_manifest_name = safe_local_file_export_artifact_name(
        gap_manifest_path,
        fallback="manifest.json",
    )
    report_name = safe_local_file_export_artifact_name(
        report_path,
        fallback="mapping-evidence.json",
    )
    try:
        with operation(
            _OPERATION,
            logger=_logger,
            reference_name=reference_name,
            configured_name=configured_name,
            recipe_name=recipe_name,
            gap_manifest_name=gap_manifest_name,
            report_name=report_name,
        ) as operation_id:
            for path, label in (
                (reference_path, "reference_path"),
                (configured_path, "configured_path"),
                (recipe_path, "recipe_path"),
                (gap_manifest_path, "gap_manifest_path"),
                (report_path, "report_path"),
            ):
                validate_local_file_export_artifact_path(path, label=label)
            validate_distinct_local_file_export_paths(
                {
                    "reference input": reference_path,
                    "configured input": configured_path,
                    "recipe input": recipe_path,
                    "gap-manifest input": gap_manifest_path,
                    "report artifact": report_path,
                }
            )
            export_phase = "source_read"
            report = analyze_mapping_capture_files(
                reference_path=reference_path,
                configured_path=configured_path,
                recipe_path=recipe_path,
                gap_manifest_path=gap_manifest_path,
            )
            payload = render_mapping_capture_report(report).encode("utf-8")
            export_phase = "output_write"
            result = atomic_write(report_path, payload)
    except (KeyError, OSError, TypeError, ValueError, KeyboardInterrupt, SystemExit) as exc:
        error_code = classify_local_file_export_error(exc, phase=export_phase)
        duration_ms = (time.perf_counter() - started_at) * 1000.0
        metrics.record_export(duration_ms, error_code=error_code)
        _logger.warning(
            "AL16 Rytm mapping evidence failed",
            extra={
                "op_id": operation_id,
                "operation": _OPERATION,
                "outcome": "failed",
                "error_code": error_code,
                "failure_phase": export_phase,
                "fingerprint": _FAILURE_FINGERPRINT,
                "reference_name": reference_name,
                "configured_name": configured_name,
                "recipe_name": recipe_name,
                "gap_manifest_name": gap_manifest_name,
                "report_name": report_name,
                "error_type": type(exc).__name__,
                "duration_ms": duration_ms,
                "metrics_summary": metrics.format_summary(),
            },
        )
        sys.stderr.write(
            f"{USAGE}\nError [{error_code}]: "
            f"could not produce {report_name} ({type(exc).__name__}).\n"
        )
        return 130 if error_code == "interrupted" else 2

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics.record_export(duration_ms)
    _logger.info(
        "AL16 Rytm mapping evidence completed",
        extra={
            "op_id": operation_id,
            "operation": _OPERATION,
            "outcome": "completed",
            "report_name": result.path.name,
            "mapping_gap_count": report.mapping_gap_count,
            "candidate_changed_count": report.candidate_changed_count,
            "unresolved_location_count": report.unresolved_location_count,
            "promotion_status": report.promotion_status,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    sys.stdout.write(
        "AL16 Rytm mapping evidence written\n"
        f"report: {result.path.name}\n"
        f"mapping_gaps: {report.mapping_gap_count}\n"
        f"candidate_locations_changed: {report.candidate_changed_count}\n"
        f"unresolved_locations: {report.unresolved_location_count}\n"
        f"other_changed_unpacked_offsets: {len(report.other_changed_unpacked_offsets)}\n"
        f"promotion_status: {report.promotion_status}\n"
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
