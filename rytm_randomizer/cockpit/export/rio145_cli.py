"""Passive CLI commands for the target-return-validated RIO145 evidence."""

from __future__ import annotations

import json
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Final, Literal

from ...cli_registry import CliCommand, register
from .rio145_codec import (
    Rio145OfflineError,
    build_a4_kit,
    build_rytm_kit,
    diff_sysex,
    export_oxi_manifest,
    inspect_sysex,
    validate_a4_return,
    validate_roundtrip,
    validate_rytm_return,
)

Action = Literal[
    "inspect",
    "diff",
    "roundtrip",
    "build_a4",
    "build_rytm",
    "validate_a4_return",
    "validate_rytm_return",
    "export_oxi",
]

_USAGE: Final[Mapping[Action, str]] = {
    "inspect": "Usage: rio145-inspect-sysex --input <file.syx>",
    "diff": "Usage: rio145-diff-sysex --left <file.syx> --right <file.syx>",
    "roundtrip": "Usage: rio145-validate-roundtrip --input <file.syx>",
    "build_a4": (
        "Usage: rio145-build-a4-kit --reference <file.syx> --recipe <recipe.json> "
        "--destination-slot <0..127> --output <file.syx> [--overwrite]"
    ),
    "build_rytm": (
        "Usage: rio145-build-rytm-kit --reference <file.syx> --recipe <recipe.json> "
        "--destination-slot <0..127> --output <file.syx> [--overwrite]"
    ),
    "validate_a4_return": (
        "Usage: rio145-validate-a4-return --reference <file.syx> "
        "--recipe <recipe.json> --returned <file.syx>"
    ),
    "validate_rytm_return": (
        "Usage: rio145-validate-rytm-return --reference <file.syx> "
        "--recipe <recipe.json> --returned <file.syx>"
    ),
    "export_oxi": (
        "Usage: rio145-export-oxi-manifest --manifest <manifest.json> "
        "--events <events.csv> --output <evidence.json> [--overwrite]"
    ),
}

_REQUIRED_OPTIONS: Final[Mapping[Action, tuple[str, ...]]] = {
    "inspect": ("--input",),
    "diff": ("--left", "--right"),
    "roundtrip": ("--input",),
    "build_a4": ("--reference", "--recipe", "--destination-slot", "--output"),
    "build_rytm": ("--reference", "--recipe", "--destination-slot", "--output"),
    "validate_a4_return": ("--reference", "--recipe", "--returned"),
    "validate_rytm_return": ("--reference", "--recipe", "--returned"),
    "export_oxi": ("--manifest", "--events", "--output"),
}

_OVERWRITE_ACTIONS: Final[frozenset[Action]] = frozenset({"build_a4", "build_rytm", "export_oxi"})


def _parse_action(action: Action, args: Sequence[str]) -> dict[str, object]:
    if tuple(args) == ("--help",):
        return {"action": action, "options": {}, "help_requested": True}
    if not args:
        raise ValueError("arguments are required")

    required = _REQUIRED_OPTIONS[action]
    allowed = set(required)
    options: dict[str, object] = {}
    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        if option == "--overwrite" and action in _OVERWRITE_ACTIONS:
            if "overwrite" in options:
                raise ValueError("--overwrite may be specified only once")
            options["overwrite"] = True
            continue
        if option not in allowed:
            raise ValueError(f"unknown option {option!r}")
        key = option[2:].replace("-", "_")
        if key in options:
            raise ValueError(f"{option} may be specified only once")
        if not remaining or remaining[0].startswith("--"):
            raise ValueError(f"{option} requires a value")
        raw_value = remaining.pop(0)
        if option == "--destination-slot":
            try:
                slot = int(raw_value)
            except ValueError as exc:
                raise ValueError("--destination-slot must be a decimal integer") from exc
            if str(slot) != raw_value or not 0 <= slot <= 127:
                raise ValueError("--destination-slot must be in the range 0..127")
            options[key] = slot
        else:
            options[key] = Path(raw_value)

    missing = [option for option in required if option[2:].replace("-", "_") not in options]
    if missing:
        raise ValueError(f"missing required option {missing[0]}")
    options.setdefault("overwrite", False)
    return {"action": action, "options": options, "help_requested": False}


def _parser(action: Action) -> Callable[[Sequence[str]], dict[str, object]]:
    def parse(args: Sequence[str]) -> dict[str, object]:
        return _parse_action(action, args)

    return parse


def _path(options: Mapping[str, object], key: str) -> Path:
    value = options.get(key)
    if not isinstance(value, Path):
        raise Rio145OfflineError(f"internal command option {key!r} is missing")
    return value


def _rio145_slot(options: Mapping[str, object]) -> int:
    value = options.get("destination_slot")
    if isinstance(value, bool) or not isinstance(value, int):
        raise Rio145OfflineError("internal destination-slot option is missing")
    return value


def _overwrite(options: Mapping[str, object]) -> bool:
    value = options.get("overwrite", False)
    if not isinstance(value, bool):
        raise Rio145OfflineError("internal overwrite option is invalid")
    return value


def _execute(action: Action, options: Mapping[str, object]) -> dict[str, object]:
    if action == "inspect":
        return inspect_sysex(_path(options, "input"))
    if action == "diff":
        return diff_sysex(_path(options, "left"), _path(options, "right"))
    if action == "roundtrip":
        return validate_roundtrip(_path(options, "input"))
    if action == "build_a4":
        return build_a4_kit(
            reference_path=_path(options, "reference"),
            recipe_path=_path(options, "recipe"),
            destination_slot=_rio145_slot(options),
            output_path=_path(options, "output"),
            overwrite=_overwrite(options),
        )
    if action == "build_rytm":
        return build_rytm_kit(
            reference_path=_path(options, "reference"),
            recipe_path=_path(options, "recipe"),
            destination_slot=_rio145_slot(options),
            output_path=_path(options, "output"),
            overwrite=_overwrite(options),
        )
    if action == "validate_a4_return":
        return validate_a4_return(
            reference_path=_path(options, "reference"),
            recipe_path=_path(options, "recipe"),
            returned_path=_path(options, "returned"),
        )
    if action == "validate_rytm_return":
        return validate_rytm_return(
            reference_path=_path(options, "reference"),
            recipe_path=_path(options, "recipe"),
            returned_path=_path(options, "returned"),
        )
    return export_oxi_manifest(
        manifest_path=_path(options, "manifest"),
        events_path=_path(options, "events"),
        output_path=_path(options, "output"),
        overwrite=_overwrite(options),
    )


def handle_rio145_command(
    *,
    action: Action,
    options: Mapping[str, object],
    help_requested: bool = False,
) -> int:
    """Run one passive RIO145 file command and emit stable JSON."""

    if help_requested:
        sys.stdout.write(_USAGE[action] + "\n")
        return 0
    try:
        payload = _execute(action, options)
    except (Rio145OfflineError, OSError, TypeError, ValueError) as exc:
        sys.stderr.write(f"{_USAGE[action]}\nError [offline_validation]: {exc}\n")
        return 2
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return 0


def _rio145_format_error(action: Action) -> Callable[[Exception], str]:
    def format_error(exc: Exception) -> str:
        return f"{_USAGE[action]}\nError [invalid_input]: {exc}"

    return format_error


def _command(name: str, action: Action, summary: str) -> CliCommand:
    command = CliCommand(
        name=name,
        summary=summary,
        args_parser=_parser(action),
        handler=handle_rio145_command,
        error_formatter=_rio145_format_error(action),
    )
    register(command)
    return command


RIO145_INSPECT_SYSEX_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-inspect-sysex", "inspect", "Inspect native Elektron SysEx files offline."
)
RIO145_DIFF_SYSEX_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-diff-sysex", "diff", "Compare native Elektron SysEx files offline."
)
RIO145_VALIDATE_ROUNDTRIP_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-validate-roundtrip", "roundtrip", "Validate byte-identical SysEx roundtrips."
)
RIO145_BUILD_A4_KIT_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-build-a4-kit", "build_a4", "Compile one Analog Four KIT file offline."
)
RIO145_BUILD_RYTM_KIT_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-build-rytm-kit", "build_rytm", "Compile one Analog Rytm KIT file offline."
)
RIO145_VALIDATE_A4_RETURN_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-validate-a4-return",
    "validate_a4_return",
    "Validate an Analog Four target return offline.",
)
RIO145_VALIDATE_RYTM_RETURN_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-validate-rytm-return",
    "validate_rytm_return",
    "Validate an Analog Rytm target return offline.",
)
RIO145_EXPORT_OXI_MANIFEST_CLI_COMMAND: Final[CliCommand] = _command(
    "rio145-export-oxi-manifest", "export_oxi", "Validate and export OXI evidence offline."
)


__all__ = [
    "RIO145_BUILD_A4_KIT_CLI_COMMAND",
    "RIO145_BUILD_RYTM_KIT_CLI_COMMAND",
    "RIO145_DIFF_SYSEX_CLI_COMMAND",
    "RIO145_EXPORT_OXI_MANIFEST_CLI_COMMAND",
    "RIO145_INSPECT_SYSEX_CLI_COMMAND",
    "RIO145_VALIDATE_A4_RETURN_CLI_COMMAND",
    "RIO145_VALIDATE_ROUNDTRIP_CLI_COMMAND",
    "RIO145_VALIDATE_RYTM_RETURN_CLI_COMMAND",
    "handle_rio145_command",
]
