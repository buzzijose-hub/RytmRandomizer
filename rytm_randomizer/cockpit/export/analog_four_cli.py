"""Operator CLI for guarded Analog Four MKII saved-kit file export."""

from __future__ import annotations

import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, Literal, TypedDict

from ...cli_registry import CliCommand, register
from ...data.analog_four_sysex_calibration import (
    A4_FILTER2_RESONANCE_PARAMETER,
    A4_SYNTH_TRACK_MAX,
    A4_SYNTH_TRACK_MIN,
)
from ...devices.analog_four import AnalogFourSavedKitMutation
from .analog_four_export_contracts import (
    AnalogFourExportErrorCode,
    analog_four_export_error_code,
)
from .analog_four_kit import (
    AnalogFourSavedKitExportResult,
    export_analog_four_saved_kit,
)
from .cli_options import pop_required_cli_value

COMMAND_NAME: Final[str] = "analog-four-saved-kit-export"
FILTER2_RESONANCE_PARAMETER: Final[str] = A4_FILTER2_RESONANCE_PARAMETER
USAGE: Final[str] = (
    "Usage: python -m rytm_randomizer.cli analog-four-saved-kit-export "
    "--source <kit.syx> --output <kit.syx> "
    "--filter2-resonance <track:value> [--filter2-resonance <track:value> ...] "
    "[--overwrite] [--json]"
)


class AnalogFourSavedKitExportArgs(TypedDict):
    """Parsed keyword arguments for one guarded saved-kit export."""

    source_path: Path
    output_path: Path
    mutations: tuple[AnalogFourSavedKitMutation, ...]
    overwrite: bool
    json_output: bool


class AnalogFourSavedKitMutationPayload(TypedDict):
    """Stable JSON record for one applied saved-kit mutation."""

    parameter: str
    track: int
    screen_value: str
    unpacked_offset: int
    rendered_unpacked_value: int


class AnalogFourSavedKitExportPayload(TypedDict):
    """Stable successful JSON response from the saved-kit export CLI."""

    ok: Literal[True]
    kit_name: str
    output_path: str
    bytes_written: int
    overwrote_existing: bool
    sha256: str
    mutations: list[AnalogFourSavedKitMutationPayload]


class AnalogFourSavedKitExportErrorPayload(TypedDict):
    """Stable failed JSON response from the saved-kit export CLI."""

    ok: Literal[False]
    error_code: AnalogFourExportErrorCode
    error: str


def _saved_kit_cli_error_code(exc: Exception) -> AnalogFourExportErrorCode:
    classified_code = analog_four_export_error_code(exc)
    if classified_code is not None:
        return classified_code
    if isinstance(exc, FileNotFoundError):
        return "input_not_found"
    if isinstance(exc, PermissionError):
        return "permission_denied"
    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        return "write_failed"
    return "validation"


def _parse_resonance_assignment(value: str) -> AnalogFourSavedKitMutation:
    track_text, separator, screen_value = value.partition(":")
    if not separator or not track_text or not screen_value:
        raise ValueError("--filter2-resonance must use TRACK:VALUE, for example 1:64")
    try:
        track = int(track_text)
        parsed_value = int(screen_value)
    except ValueError as exc:
        raise ValueError("--filter2-resonance track and value must be decimal integers") from exc
    if str(track) != track_text or not A4_SYNTH_TRACK_MIN <= track <= A4_SYNTH_TRACK_MAX:
        raise ValueError(
            "--filter2-resonance track must be an integer from "
            f"{A4_SYNTH_TRACK_MIN} to {A4_SYNTH_TRACK_MAX}"
        )
    if str(parsed_value) != screen_value or not 0 <= parsed_value <= 127:
        raise ValueError("--filter2-resonance value must be an integer from 0 to 127")
    return AnalogFourSavedKitMutation(
        parameter=FILTER2_RESONANCE_PARAMETER,
        track=track,
        screen_value=screen_value,
    )


def parse_analog_four_saved_kit_export_args(
    args: Sequence[str],
) -> AnalogFourSavedKitExportArgs:
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
            source_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--output":
            output_path = Path(pop_required_cli_value(remaining, option=option))
        elif option == "--filter2-resonance":
            mutations.append(
                _parse_resonance_assignment(pop_required_cli_value(remaining, option=option))
            )
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


def _parse_saved_kit_args_for_registry(args: Sequence[str]) -> dict[str, object]:
    """Adapt the precise public parser shape to the generic CLI registry."""

    try:
        parsed = parse_analog_four_saved_kit_export_args(args)
    except ValueError as exc:
        if "--json" not in args:
            raise
        return {
            "source_path": Path(),
            "output_path": Path(),
            "mutations": (),
            "overwrite": False,
            "json_output": True,
            "parse_error": str(exc),
        }
    return {**parsed, "parse_error": None}


def _payload_from_result(
    result: AnalogFourSavedKitExportResult,
) -> AnalogFourSavedKitExportPayload:
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
    parse_error: str | None = None,
) -> int:
    """Render, write, and acknowledge one guarded A4 saved-kit export."""

    if parse_error is not None:
        error_payload: AnalogFourSavedKitExportErrorPayload = {
            "ok": False,
            "error_code": "invalid_input",
            "error": parse_error,
        }
        sys.stdout.write(json.dumps(error_payload, sort_keys=True))
        sys.stdout.write("\n")
        return 2

    try:
        result = export_analog_four_saved_kit(
            source_path=source_path,
            output_path=output_path,
            mutations=mutations,
            overwrite=overwrite,
        )
    except KeyboardInterrupt as exc:
        if json_output:
            error_payload: AnalogFourSavedKitExportErrorPayload = {
                "ok": False,
                "error_code": "interrupted",
                "error": str(exc) or "operator interrupted saved-kit export",
            }
            sys.stdout.write(json.dumps(error_payload, sort_keys=True))
            sys.stdout.write("\n")
        else:
            sys.stderr.write(f"{USAGE}\nError [interrupted]: saved-kit export interrupted.\n")
        return 130
    except (KeyError, ValueError, TypeError, OSError) as exc:
        error_code = _saved_kit_cli_error_code(exc)
        if json_output:
            error_payload: AnalogFourSavedKitExportErrorPayload = {
                "ok": False,
                "error_code": error_code,
                "error": str(exc),
            }
            sys.stdout.write(json.dumps(error_payload, sort_keys=True))
            sys.stdout.write("\n")
        else:
            sys.stderr.write(f"{USAGE}\nError [{error_code}]: {exc}\n")
        return 2

    payload = _payload_from_result(result)
    if json_output:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
    else:
        sys.stdout.write(_format_a4_saved_kit_text(result))
    return 0


def _format_a4_saved_kit_cli_error(exc: Exception) -> str:
    return f"{USAGE}\nError [invalid_input]: {exc}"


ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=COMMAND_NAME,
    summary="Render hardware-validated Analog Four values into a saved-kit SysEx file.",
    args_parser=_parse_saved_kit_args_for_registry,
    handler=handle_analog_four_saved_kit_export,
    error_formatter=_format_a4_saved_kit_cli_error,
)

register(ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND)

__all__ = [
    "ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND",
    "AnalogFourSavedKitExportArgs",
    "AnalogFourSavedKitExportErrorPayload",
    "AnalogFourSavedKitExportPayload",
    "AnalogFourSavedKitMutationPayload",
    "COMMAND_NAME",
    "FILTER2_RESONANCE_PARAMETER",
    "USAGE",
    "handle_analog_four_saved_kit_export",
    "parse_analog_four_saved_kit_export_args",
]
