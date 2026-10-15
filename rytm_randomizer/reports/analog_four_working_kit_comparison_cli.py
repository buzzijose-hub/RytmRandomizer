"""Passive JSON CLI for six operator-supplied A4 experiment files.

Manual baseline is pre-edit indexed 0x52 B. Indexed baseline is the queried
0x52 retained AFTER the unsaved panel edit and BEFORE SAVE, expected to remain
B while working 0x58 contains U. An initial queried 0x52 is optional additional
manual evidence, not a required seventh input. Files do not verify chronology.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from ..cli_registry import CliCommand, make_parsed_cli_command, register
from ..data.analog_four_saved_kit_layout import A4_KIT_SYNTH_TRACK_COUNT
from ..devices.strategies.analog_four_working_kit_comparison import (
    AnalogFourExperimentEvidenceOrigin,
)
from .analog_four_working_kit_comparison import (
    AnalogFourWorkingKitFiles,
    build_analog_four_working_kit_comparison_report,
    to_analog_four_working_kit_comparison_json,
)

USAGE: Final[str] = (
    "Usage: a4-working-kit-compare --manual-baseline FILE --indexed-baseline FILE "
    "--working-first FILE --working-repeat FILE --post-save FILE --recovered FILE "
    "--track {1,2,3,4} --evidence-origin {synthetic,operator_supplied_files} "
    "[--baseline-label LABEL] [--changed-label LABEL]\n"
    "Manual baseline: pre-edit indexed 0x52 B. Indexed baseline: post-unsaved-edit, "
    "pre-SAVE queried 0x52 expected to remain B. Chronology is operator-supplied, "
    "not verified by files. Output is JSON inspection only."
)
_ARGUMENT_ERROR: Final[str] = "Error: invalid a4-working-kit-compare arguments."
_INPUT_ERROR: Final[str] = "Error: a4-working-kit-compare input comparison failed."
_REQUIRED: Final[frozenset[str]] = frozenset(
    (
        "--manual-baseline",
        "--indexed-baseline",
        "--working-first",
        "--working-repeat",
        "--post-save",
        "--recovered",
        "--track",
        "--evidence-origin",
    )
)
_OPTIONS: Final[frozenset[str]] = _REQUIRED | frozenset(("--baseline-label", "--changed-label"))
_TRACKS: Final[frozenset[str]] = frozenset(
    str(track) for track in range(1, A4_KIT_SYNTH_TRACK_COUNT + 1)
)
_ORIGINS: Final[frozenset[str]] = frozenset(
    origin.value for origin in AnalogFourExperimentEvidenceOrigin
)


@dataclass(frozen=True)
class AnalogFourWorkingKitComparisonCliArguments:
    """Validated options; baseline file roles retain the operator's declared sequence."""

    files: AnalogFourWorkingKitFiles
    track: int
    evidence_origin: AnalogFourExperimentEvidenceOrigin
    baseline_label: str | None
    changed_label: str | None


def _parse_working_compare_options(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        return {"arguments": None}
    values: dict[str, str] = {}
    index = 0
    while index < len(argv):
        option = argv[index]
        if option not in _OPTIONS or option in values:
            raise ValueError(_ARGUMENT_ERROR)
        if index + 1 >= len(argv):
            raise ValueError(_ARGUMENT_ERROR)
        value = argv[index + 1]
        if not value.strip() or value.startswith("--"):
            raise ValueError(_ARGUMENT_ERROR)
        values[option] = value
        index += 2
    if not _REQUIRED.issubset(values):
        raise ValueError(_ARGUMENT_ERROR)
    if values["--track"] not in _TRACKS or values["--evidence-origin"] not in _ORIGINS:
        raise ValueError(_ARGUMENT_ERROR)
    arguments = AnalogFourWorkingKitComparisonCliArguments(
        files=AnalogFourWorkingKitFiles(
            Path(values["--manual-baseline"]),
            Path(values["--indexed-baseline"]),
            Path(values["--working-first"]),
            Path(values["--working-repeat"]),
            Path(values["--post-save"]),
            Path(values["--recovered"]),
        ),
        track=int(values["--track"]),
        evidence_origin=AnalogFourExperimentEvidenceOrigin(values["--evidence-origin"]),
        baseline_label=values.get("--baseline-label"),
        changed_label=values.get("--changed-label"),
    )
    return {"arguments": arguments}


def _format_argument_error(_exc: Exception) -> str:
    return _ARGUMENT_ERROR


def _handle_report(arguments: AnalogFourWorkingKitComparisonCliArguments | None) -> int:
    if arguments is None:
        sys.stdout.write(USAGE + "\n")
        return 0
    try:
        report = build_analog_four_working_kit_comparison_report(
            arguments.files,
            track=arguments.track,
            evidence_origin=arguments.evidence_origin,
            baseline_label=arguments.baseline_label,
            changed_label=arguments.changed_label,
        )
    except (OSError, ValueError):
        sys.stderr.write(f"{_INPUT_ERROR}\n")
        return 2
    sys.stdout.write(to_analog_four_working_kit_comparison_json(report))
    sys.stdout.write("\n")
    return 0


ANALOG_FOUR_WORKING_KIT_COMPARISON_CLI_COMMAND: Final[CliCommand] = make_parsed_cli_command(
    name="a4-working-kit-compare",
    summary="Compare pre-edit manual B, post-edit indexed B and working U from supplied files; chronology unverified.",
    args_parser=_parse_working_compare_options,
    handler=_handle_report,
    error_formatter=_format_argument_error,
)
register(ANALOG_FOUR_WORKING_KIT_COMPARISON_CLI_COMMAND)

__all__ = (
    "ANALOG_FOUR_WORKING_KIT_COMPARISON_CLI_COMMAND",
    "AnalogFourWorkingKitComparisonCliArguments",
    "USAGE",
)
