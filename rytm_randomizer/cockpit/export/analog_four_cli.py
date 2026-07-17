"""Operator CLI for guarded Analog Four MKII saved-kit file export."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final

from ...cli_registry import CliCommand, register
from ...devices.strategies.analog_four_saved_kit_writer import (
    AnalogFourSavedKitMutation,
)
from .analog_four_kit import (
    AnalogFourSavedKitExportResult,
    export_analog_four_saved_kit,
)

COMMAND_NAME: Final[str] = "analog-four-saved-kit-export"
FILTER2_RESONANCE_PARAMETER: Final[str] = "Filter2 Resonance"
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-saved-kit-export "
    "--source <kit.syx> --output <kit.syx> "
    "--filter2-resonance <track:value> [--filter2-resonance <track:value> ...] "
    "[--overwrite] [--json]"
)


def _pop_a4_cli_value(remaining: list[str], option: str) -> str:
    if not remaining:
        raise ValueError(f"{option} requires a value")
    return remaining.pop(0)


def _parse_resonance_assignment(value: str) -> AnalogFourSavedKitMutation:
    track_text, separator, screen_value = value.partition(":")
    if not separator or not track_text or not screen_value:
        raise ValueError("--filter2-resonance must use TRACK:VALUE, for example 1:64")
    try:
        track = int(track_text)
        parsed_value = int(screen_value)
    except ValueError as exc:
        raise ValueError("--filter2-resonance track and value must be decimal integers") from exc
    if str(track) != track_text or not 1 <= track <= 4:
        raise ValueError("--filter2-resonance track must be an integer from 1 to 4")
    if str(parsed_value) != screen_value or not 0 <= parsed_value <= 127:
        raise ValueError("--filter2-resonance value must be an integer from 0 to 127")
    return AnalogFourSavedKitMutation(
        parameter=FILTER2_RESONANCE_PARAMETER,
        track=track,
        screen_value=screen_value,
    )


def parse_analog_four_saved_kit_export_args(args: Sequence[str]) -> dict[str, object]:
    """Parse the registered command's argv tail into handler keyword args."""

    source_path: Path | None = None
    output_path: Path | None = None
    mutations: list[AnalogFourSavedKitMutation] = []
    overwrite = False
    json_output = False
    remaining = list(args)

    while remaining:
        option = remaining.pop(0)
        if option == "--source":
            source_path = Path(_pop_a4_cli_value(remaining, option))
        elif option == "--output":
            output_path = Path(_pop_a4_cli_value(remaining, option))
        elif option == "--filter2-resonance":
            mutations.append(_parse_resonance_assignment(_pop_a4_cli_value(remaining, option)))
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}")

    if source_path is None:
        raise ValueError("--source is required")
    if output_path is None:
        raise ValueError("--output is required")
    if not mutations:
        raise ValueError("at least one --filter2-resonance TRACK:VALUE is required")
    return {
        "source_path": source_path,
        "output_path": output_path,
        "mutations": tuple(mutations),
        "overwrite": overwrite,
        "json_output": json_output,
    }


def _payload_from_result(result: AnalogFourSavedKitExportResult) -> dict[str, object]:
    return {
        "ok": True,
        "kit_name": result.render.kit_name,
        "output_path": str(result.write.path),
        "bytes_written": result.write.bytes_written,
        "overwrote_existing": result.write.overwrote_existing,
        "sha256": result.render.sha256,
        "mutations": [
            {
                "parameter": mutation.parameter,
                "track": mutation.track,
                "screen_value": mutation.screen_value,
                "unpacked_offset": mutation.unpacked_offset,
                "rendered_unpacked_value": mutation.rendered_unpacked_value,
            }
            for mutation in result.render.applied_mutations
        ],
    }


def _format_a4_saved_kit_text(result: AnalogFourSavedKitExportResult) -> str:
    lines = [
        "ok: true",
        f"kit_name: {result.render.kit_name}",
        f"output_path: {result.write.path}",
        f"bytes_written: {result.write.bytes_written}",
        f"overwrote_existing: {str(result.write.overwrote_existing).lower()}",
        f"sha256: {result.render.sha256}",
    ]
    for mutation in result.render.applied_mutations:
        lines.append(
            "mutation: "
            f"T{mutation.track} {mutation.parameter}="
            f"{mutation.screen_value} @ unpacked[{mutation.unpacked_offset}]"
        )
    return "\n".join(lines) + "\n"


def handle_analog_four_saved_kit_export(
    *,
    source_path: Path,
    output_path: Path,
    mutations: Sequence[AnalogFourSavedKitMutation],
    overwrite: bool = False,
    json_output: bool = False,
) -> int:
    """Render, write, and acknowledge one guarded A4 saved-kit export."""

    try:
        result = export_analog_four_saved_kit(
            source_path=source_path,
            output_path=output_path,
            mutations=mutations,
            overwrite=overwrite,
        )
    except (KeyError, ValueError, TypeError, OSError) as exc:
        if json_output:
            sys.stdout.write(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            sys.stdout.write("\n")
        else:
            sys.stderr.write(f"{USAGE}\nError: {exc}\n")
        return 2

    payload = _payload_from_result(result)
    if json_output:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_a4_saved_kit_text(result))
    return 0


def _format_a4_saved_kit_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError: {exc}"


ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Render hardware-validated Analog Four values into a saved-kit SysEx file.",
    args_parser=parse_analog_four_saved_kit_export_args,
    handler=handle_analog_four_saved_kit_export,
    error_formatter=_format_a4_saved_kit_cli_error,
)

register(ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND",
    "COMMAND_NAME",
    "FILTER2_RESONANCE_PARAMETER",
    "USAGE",
    "handle_analog_four_saved_kit_export",
    "parse_analog_four_saved_kit_export_args",
]
