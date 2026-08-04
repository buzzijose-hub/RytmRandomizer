"""Operator CLI for fail-closed AL16 Analog Rytm saved-kit export."""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TypedDict

from ...cli_registry import CliCommand, register
from .al16_rytm_kit import Al16BuildResult, build_al16_rytm_kit
from .cli_options import pop_required_cli_value
from .file_export_contracts import (
    local_file_export_error_context,
    safe_local_file_export_artifact_name,
)

COMMAND_NAME: Final[str] = "al16-rytm-kit-export"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli al16-rytm-kit-export "
    "--reference <kit.syx> --recipe <recipe.yaml> --destination-slot <0..127> "
    "--output <kit.syx>"
)


class Al16RytmKitExportArgs(TypedDict):
    """Parsed keyword arguments for one offline AL16 build attempt."""

    reference_path: Path
    recipe_path: Path
    destination_slot: int
    output_path: Path


def _parse_destination_slot(value: str) -> int:
    try:
        slot = int(value)
    except ValueError as exc:
        raise ValueError("--destination-slot must be a decimal integer from 0 to 127") from exc
    if str(slot) != value or not 0 <= slot <= 127:
        raise ValueError("--destination-slot must be a decimal integer from 0 to 127")
    return slot


def parse_al16_rytm_kit_export_args(args: Sequence[str]) -> Al16RytmKitExportArgs:
    """Parse the registered command's argv tail into handler keyword args."""

    reference_path: Path | None = None
    recipe_path: Path | None = None
    destination_slot: int | None = None
    output_path: Path | None = None
    remaining = list(args)

    while remaining:
        option = remaining.pop(0)
        if option == "--reference":
            reference_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--recipe":
            recipe_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--destination-slot":
            destination_slot = _parse_destination_slot(
                pop_required_cli_value(remaining, option=option)
            )
        elif option == "--output":
            output_path = Path(pop_required_cli_value(remaining, option=option))
        else:
            raise ValueError(f"unknown option {option!r}")

    if reference_path is None:
        raise ValueError("--reference is required")
    if recipe_path is None:
        raise ValueError("--recipe is required")
    if destination_slot is None:
        raise ValueError("--destination-slot is required")
    if output_path is None:
        raise ValueError("--output is required")
    return {
        "reference_path": reference_path,
        "recipe_path": recipe_path,
        "destination_slot": destination_slot,
        "output_path": output_path,
    }


def _parse_al16_rytm_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    return dict(parse_al16_rytm_kit_export_args(args))


def _format_al16_rytm_result(result: Al16BuildResult) -> str:
    output_emitted = result.output_sha256 is not None
    lines = [
        f"build_status: {result.status}",
        f"output_path: {result.output_path}",
        f"output_emitted: {str(output_emitted).lower()}",
        f"output_sha256: {result.output_sha256 or 'none'}",
        f"reference_sha256: {result.reference_sha256}",
        f"manifest: {result.manifest_path}",
        f"validation: {result.validation_path}",
        f"byte_diff: {result.byte_diff_path}",
        f"critical_mapping_gaps: {len(result.gaps)}",
    ]
    lines.extend(f"mapping_gap: {gap.semantic_path}: {gap.reason}" for gap in result.gaps)
    return "\n".join(lines) + "\n"


def handle_al16_rytm_kit_export(
    *,
    reference_path: Path,
    recipe_path: Path,
    destination_slot: int,
    output_path: Path,
) -> int:
    """Run one passive AL16 build attempt and print its evidence paths."""

    try:
        result = build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=recipe_path,
            destination_slot=destination_slot,
            output_path=output_path,
        )
    except KeyboardInterrupt:
        sys.stderr.write(f"{USAGE}\nError [interrupted]: AL16 kit export interrupted.\n")
        return 130
    except (KeyError, ValueError, TypeError, OSError) as exc:
        error_context = local_file_export_error_context(exc)
        if error_context is None:
            error_code = "offline_build_failed"
            output_name = safe_local_file_export_artifact_name(
                output_path,
                fallback="output.syx",
            )
            detail = f"AL16 offline build failed for {output_name}."
        else:
            error_code = error_context.error_code
            detail = (
                f"Passive export failed during {error_context.phase} "
                f"for {error_context.artifact_name}."
            )
        sys.stderr.write(f"{USAGE}\nError [{error_code}]: {detail}\n")
        return 2

    sys.stdout.write(_format_al16_rytm_result(result))
    return 0 if result.status == "built" else 2


def _format_al16_rytm_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError [invalid_input]: {exc}"


AL16_RYTM_KIT_EXPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Compile an AL16 Analog Rytm recipe offline or emit mapping-gap evidence.",
    args_parser=_parse_al16_rytm_args_for_registry,
    handler=handle_al16_rytm_kit_export,
    error_formatter=_format_al16_rytm_cli_error,
)

register(AL16_RYTM_KIT_EXPORT_CLI_COMMAND)

__all__ = [
    "AL16_RYTM_KIT_EXPORT_CLI_COMMAND",
    "Al16RytmKitExportArgs",
    "COMMAND_NAME",
    "USAGE",
    "handle_al16_rytm_kit_export",
    "parse_al16_rytm_kit_export_args",
]
