"""Passive CLI for bounded Analog Four patch render refinement."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict

from ...cli_registry import CliCommand, register
from ...data.analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
    ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
)
from ...observability.errors import BoundaryError
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
)
from .analog_four_patch_refinement import (
    ANALOG_FOUR_PATCH_REFINEMENT_SAFETY,
    AnalogFourPatchRefinementResult,
)
from .analog_four_patch_render_rank import (
    analog_four_patch_render_rank_error_code,
)
from .cli_options import parse_bounded_float, parse_bounded_integer, pop_required_cli_value

COMMAND_NAME: Final[str] = "analog-four-audio-patch-refine"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-audio-patch-refine "
    "--reference <audio> --manifest <batch.json> --candidate <1-4> "
    "--render <audio> --output-dir <dir> [--gain <0.0-1.0>] "
    "[--accept-similarity <0-100>] [--source-kit <kit.syx>] "
    "[--overwrite] [--json]"
)


class AnalogFourPatchRefinementArgs(TypedDict):
    reference_audio_path: Path
    manifest_path: Path
    candidate: int
    render_audio_path: Path
    output_dir: Path
    correction_gain: float
    accept_similarity: int
    source_kit_path: Path | None
    overwrite: bool
    json_output: bool


def parse_analog_four_patch_refinement_args(
    args: Sequence[str],
) -> AnalogFourPatchRefinementArgs:
    """Parse the passive render-feedback refinement command."""

    reference_audio_path: Path | None = None
    manifest_path: Path | None = None
    candidate: int | None = None
    render_audio_path: Path | None = None
    output_dir: Path | None = None
    correction_gain = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT
    accept_similarity = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT
    source_kit_path: Path | None = None
    overwrite = False
    json_output = False
    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        if option == "--reference":
            reference_audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--manifest":
            manifest_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--candidate":
            candidate = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
                upper=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
            )
        elif option == "--render":
            render_audio_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--output-dir":
            output_dir = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--gain":
            correction_gain = parse_bounded_float(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MIN,
                upper=ANALOG_FOUR_PATCH_REFINEMENT_GAIN_MAX,
            )
        elif option == "--accept-similarity":
            accept_similarity = parse_bounded_integer(
                pop_required_cli_value(remaining, option=option),
                option=option,
                lower=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MIN,
                upper=ANALOG_FOUR_PATCH_REFINEMENT_SIMILARITY_MAX,
            )
        elif option == "--source-kit":
            source_kit_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")
    if reference_audio_path is None:
        raise ValueError("--reference is required")
    if manifest_path is None:
        raise ValueError("--manifest is required")
    if candidate is None:
        raise ValueError("--candidate is required")
    if render_audio_path is None:
        raise ValueError("--render is required")
    if output_dir is None:
        raise ValueError("--output-dir is required")
    return {
        "reference_audio_path": reference_audio_path,
        "manifest_path": manifest_path,
        "candidate": candidate,
        "render_audio_path": render_audio_path,
        "output_dir": output_dir,
        "correction_gain": correction_gain,
        "accept_similarity": accept_similarity,
        "source_kit_path": source_kit_path,
        "overwrite": overwrite,
        "json_output": json_output,
    }


def _parse_refinement_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    try:
        parsed = parse_analog_four_patch_refinement_args(args)
    except ValueError as exc:
        if "--json" not in args:
            raise
        return {
            "reference_audio_path": Path(),
            "manifest_path": Path(),
            "candidate": ANALOG_FOUR_PATCH_CANDIDATE_MIN,
            "render_audio_path": Path(),
            "output_dir": Path(),
            "correction_gain": ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
            "accept_similarity": ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
            "source_kit_path": None,
            "overwrite": False,
            "json_output": True,
            "parse_error": str(exc),
        }
    return {**parsed, "parse_error": None}


def _refine(  # noqa: PLR0913 - mirrors the explicit service boundary
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    candidate: int,
    render_audio_path: Path,
    output_dir: Path,
    correction_gain: float,
    accept_similarity: int,
    source_kit_path: Path | None,
    overwrite: bool,
) -> AnalogFourPatchRefinementResult:
    from .analog_four_patch_refinement import export_analog_four_patch_refinement

    return export_analog_four_patch_refinement(
        reference_audio_path=reference_audio_path,
        manifest_path=manifest_path,
        candidate=candidate,
        render_audio_path=render_audio_path,
        output_dir=output_dir,
        correction_gain=correction_gain,
        accept_similarity=accept_similarity,
        source_kit_path=source_kit_path,
        overwrite=overwrite,
    )


def _format_refinement_text(result: AnalogFourPatchRefinementResult) -> str:
    payload = result.payload
    selection = payload["selection"]
    plan = payload["plan"]
    lines = [
        "ok: true",
        f"action: {plan['action']}",
        f"similarity: {plan['similarity']}",
        f"accept_similarity: {plan['accept_similarity']}",
        f"candidate: {selection['candidate']}",
        f"label: {selection['label']}",
        f"track: {selection['track']}",
        f"json_path: {result.json_path}",
        f"markdown_path: {result.markdown_path}",
    ]
    next_export = payload["next_export"]
    if next_export is None:
        lines.append("next_export: none")
    else:
        lines.extend(
            (
                f"next_sysex_path: {next_export['sysex_path']}",
                f"next_sidecar_path: {next_export['sidecar_path']}",
            )
        )
    lines.extend(("safety:", *(f"- {line}" for line in payload["safety"])))
    return "\n".join(lines) + "\n"


def handle_analog_four_patch_refinement(  # noqa: PLR0913 - CLI contract
    *,
    reference_audio_path: Path,
    manifest_path: Path,
    candidate: int,
    render_audio_path: Path,
    output_dir: Path,
    correction_gain: float = ANALOG_FOUR_PATCH_REFINEMENT_GAIN_DEFAULT,
    accept_similarity: int = ANALOG_FOUR_PATCH_REFINEMENT_ACCEPT_SIMILARITY_DEFAULT,
    source_kit_path: Path | None = None,
    overwrite: bool = False,
    json_output: bool = False,
    parse_error: str | None = None,
) -> int:
    """Run one offline bounded refinement pass."""

    if parse_error is not None:
        return _report_refinement_error(ValueError(parse_error), json_output=True)
    try:
        result = _refine(
            reference_audio_path=reference_audio_path,
            manifest_path=manifest_path,
            candidate=candidate,
            render_audio_path=render_audio_path,
            output_dir=output_dir,
            correction_gain=correction_gain,
            accept_similarity=accept_similarity,
            source_kit_path=source_kit_path,
            overwrite=overwrite,
        )
    except (KeyboardInterrupt, SystemExit) as exc:
        return _report_refinement_error(exc, json_output=json_output)
    except (
        BoundaryError,
        ImportError,
        KeyError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as exc:
        return _report_refinement_error(exc, json_output=json_output)
    if json_output:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": True,
                    **result.payload,
                    "json_path": str(result.json_path),
                    "markdown_path": str(result.markdown_path),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    else:
        sys.stdout.write(_format_refinement_text(result))
    return 0


def _report_refinement_error(exc: BaseException, *, json_output: bool) -> int:
    error_code = analog_four_patch_render_rank_error_code(exc)
    if json_output:
        sys.stdout.write(
            json.dumps(
                {
                    "ok": False,
                    "error": str(exc),
                    "error_code": error_code,
                    "safety": list(ANALOG_FOUR_PATCH_REFINEMENT_SAFETY),
                },
                sort_keys=True,
            )
            + "\n"
        )
    else:
        sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
    return 130 if error_code == "interrupted" else 2


def _format_refinement_cli_error(exc: Exception) -> str:
    error_code = analog_four_patch_render_rank_error_code(exc)
    return f"{USAGE}\nError [{error_code}]: {exc}"


ANALOG_FOUR_PATCH_REFINEMENT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Refine one A4 candidate from a measured hardware render.",
    args_parser=_parse_refinement_args_for_registry,
    handler=handle_analog_four_patch_refinement,
    error_formatter=_format_refinement_cli_error,
)

register(ANALOG_FOUR_PATCH_REFINEMENT_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_PATCH_REFINEMENT_CLI_COMMAND",
    "COMMAND_NAME",
    "USAGE",
    "handle_analog_four_patch_refinement",
    "parse_analog_four_patch_refinement_args",
]
