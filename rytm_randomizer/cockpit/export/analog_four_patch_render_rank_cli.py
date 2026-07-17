"""Passive CLI for ranking recorded Analog Four patch candidates."""

from __future__ import annotations

import json
import sys
import time
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Final, TypedDict

from ...cli_registry import CliCommand, register
from ...observability.logging import get_logger
from ...observability.metrics import AnalogFourPatchRenderRankErrorCode, get_metrics
from ...observability.tracing import operation
from ...style_analysis.extractor import StyleAnalysisDependencyError
from .analog_four_patch_render_rank import (
    ANALOG_FOUR_RENDER_RANK_SAFETY,
    AnalogFourPatchRenderRankArtifactError,
    AnalogFourPatchRenderRankPacket,
    AnalogFourPatchRenderRankPayload,
    AnalogFourPatchRenderRankReferenceError,
    analog_four_patch_render_rank_to_dict,
)

COMMAND_NAME: Final[str] = "analog-four-audio-patch-rank"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-audio-patch-rank "
    "--reference <audio> --manifest <batch.json> --render <N=audio> "
    "[--render <N=audio> ...] [--json]"
)
_logger = get_logger(__name__)


class AnalogFourPatchRenderRankArgs(TypedDict):
    reference_audio_path: Path
    manifest_path: Path
    render_paths: Mapping[int, Path]
    json_output: bool


def _value(remaining: list[str], option: str) -> str:
    if not remaining:
        raise ValueError(f"{option} requires a value")
    return remaining.pop(0)


def _render_assignment(value: str) -> tuple[int, Path]:
    candidate_text, separator, path_text = value.partition("=")
    if separator == "" or path_text == "":
        raise ValueError("--render must use N=audio-path format")
    try:
        candidate = int(candidate_text)
    except ValueError as exc:
        raise ValueError("--render candidate must be an integer from 1 to 4") from exc
    if str(candidate) != candidate_text or not 1 <= candidate <= 4:
        raise ValueError("--render candidate must be an integer from 1 to 4")
    return candidate, Path(path_text)


def parse_analog_four_patch_render_rank_args(
    args: Sequence[str],
) -> AnalogFourPatchRenderRankArgs:
    """Parse the passive render-ranking command."""

    reference_audio_path: Path | None = None
    manifest_path: Path | None = None
    render_paths: dict[int, Path] = {}
    json_output = False
    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        if option == "--reference":
            reference_audio_path = Path(_value(remaining, option))
        elif option == "--manifest":
            manifest_path = Path(_value(remaining, option))
        elif option == "--render":
            candidate, path = _render_assignment(_value(remaining, option))
            if candidate in render_paths:
                raise ValueError(f"--render candidate {candidate} was provided more than once")
            render_paths[candidate] = path
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")
    if reference_audio_path is None:
        raise ValueError("--reference is required")
    if manifest_path is None:
        raise ValueError("--manifest is required")
    if not render_paths:
        raise ValueError("at least one --render is required")
    return {
        "reference_audio_path": reference_audio_path,
        "manifest_path": manifest_path,
        "render_paths": render_paths,
        "json_output": json_output,
    }


def _parse_render_rank_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    return dict(parse_analog_four_patch_render_rank_args(args))


def _rank(
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    render_paths: Mapping[int, Path],
) -> AnalogFourPatchRenderRankPacket:
    from .analog_four_patch_render_rank import rank_analog_four_patch_renders

    return rank_analog_four_patch_renders(
        reference_audio_path=reference_audio_path,
        manifest_path=manifest_path,
        render_paths=render_paths,
    )


def _rank_error_code(exc: Exception) -> AnalogFourPatchRenderRankErrorCode:
    if isinstance(exc, AnalogFourPatchRenderRankArtifactError):
        return "artifact_validation"
    if isinstance(exc, AnalogFourPatchRenderRankReferenceError):
        return "reference_mismatch"
    if isinstance(exc, StyleAnalysisDependencyError):
        return "dependency_missing"
    if isinstance(exc, OSError):
        return "input_read_failed"
    if isinstance(exc, (TypeError, ValueError)):
        return "validation"
    return "rank_failed"


def _format_render_rank_text(packet: AnalogFourPatchRenderRankPacket) -> str:
    lines = [
        "ok: true",
        f"generation_id: {packet.generation_id}",
        f"selected_track: {packet.selected_track}",
        f"reference_sha256: {packet.reference_sha256}",
        f"render_count: {packet.render_count}",
        f"recommended_candidate: {packet.recommended_candidate}",
        f"recommended_label: {packet.recommended_label}",
    ]
    lines.extend(
        f"rank: {score.rank} | candidate={score.candidate} | {score.label} | "
        f"similarity={score.similarity} | distance={score.distance:.6f} | "
        f"render={score.render_path}"
        for score in packet.scores
    )
    lines.extend(("safety:", *(f"- {line}" for line in ANALOG_FOUR_RENDER_RANK_SAFETY)))
    return "\n".join(lines) + "\n"


def handle_analog_four_patch_render_rank(
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    render_paths: Mapping[int, Path],
    json_output: bool = False,
) -> int:
    """Analyze and rank local A4 recordings without touching MIDI."""

    metrics = get_metrics()
    started_at = time.perf_counter()
    try:
        with operation(
            "a4_patch_render_rank",
            logger=_logger,
            reference_path=str(reference_audio_path),
            manifest_path=str(manifest_path),
            render_count=len(render_paths),
        ):
            packet = _rank(
                reference_audio_path=reference_audio_path,
                manifest_path=manifest_path,
                render_paths=render_paths,
            )
    except (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError) as exc:
        error_code = _rank_error_code(exc)
        metrics.record_a4_patch_render_rank(
            (time.perf_counter() - started_at) * 1000.0,
            error_code=error_code,
        )
        _logger.warning(
            "Analog Four patch render ranking failed",
            extra={
                "operation": "a4_patch_render_rank",
                "error_code": error_code,
                "reference_path": str(reference_audio_path),
                "manifest_path": str(manifest_path),
            },
        )
        if json_output:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "error": str(exc),
                        "error_code": error_code,
                        "safety": list(ANALOG_FOUR_RENDER_RANK_SAFETY),
                    },
                    sort_keys=True,
                )
                + "\n"
            )
        else:
            sys.stderr.write(f"{USAGE}\nError: {exc}\n")
        return 2

    metrics.record_a4_patch_render_rank((time.perf_counter() - started_at) * 1000.0)
    _logger.info(
        "Analog Four patch render ranking completed",
        extra={
            "operation": "a4_patch_render_rank",
            "generation_id": packet.generation_id,
            "recommended_candidate": packet.recommended_candidate,
        },
    )
    if json_output:
        payload: AnalogFourPatchRenderRankPayload = analog_four_patch_render_rank_to_dict(packet)
        sys.stdout.write(json.dumps({"ok": True, **payload}, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(_format_render_rank_text(packet))
    return 0


def _format_render_rank_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


ANALOG_FOUR_PATCH_RENDER_RANK_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Rank recorded Analog Four candidates against their reference audio.",
    args_parser=_parse_render_rank_args_for_registry,
    handler=handle_analog_four_patch_render_rank,
    error_formatter=_format_render_rank_cli_error,
)

register(ANALOG_FOUR_PATCH_RENDER_RANK_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_RENDER_RANK_CLI_COMMAND",
    "COMMAND_NAME",
    "USAGE",
    "handle_analog_four_patch_render_rank",
    "parse_analog_four_patch_render_rank_args",
]
