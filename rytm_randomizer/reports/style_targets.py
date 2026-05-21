"""Passive style target vector reports for techno design intent."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_targets import (
    STYLE_TARGET_VECTOR_AXES,
    STYLE_TARGET_VECTORS,
    StyleTargetVector,
)
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive style target vector report"
INSPECT_TITLE: Final[str] = "RytmRandomizer passive style target vector inspection"
SOURCE_MODULE: Final[str] = "reports.style_targets"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_INSPECT_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=INSPECT_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class StyleTargetCatalogReport:
    """Passive catalog report for all style target vectors."""

    target_count: int
    targets_by_key: Mapping[str, StyleTargetVector]


def _safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _style_targets_by_key() -> Mapping[str, StyleTargetVector]:
    return MappingProxyType(dict(STYLE_TARGET_VECTORS))


def build_style_target_catalog_report() -> StyleTargetCatalogReport:
    """Return passive catalog data for all style target vectors."""

    targets_by_key = _style_targets_by_key()
    return StyleTargetCatalogReport(
        target_count=len(targets_by_key),
        targets_by_key=targets_by_key,
    )


def _axis_line(axis: str, value: int) -> str:
    return f"{axis}: {value}"


def _target_lines(target: StyleTargetVector) -> list[str]:
    mapping = target.as_mapping()
    return [
        f"Key: {target.key}",
        "Axes:",
        *[_axis_line(axis, mapping[axis]) for axis in STYLE_TARGET_VECTOR_AXES],
    ]


def format_style_target_report(
    report: StyleTargetCatalogReport | None = None,
) -> list[str]:
    """Return deterministic catalog lines for all style target vectors."""

    source_report = build_style_target_catalog_report() if report is None else report
    lines = [
        "Summary:",
        "- Purpose: numeric style intent for future snapshot mutation planning",
        f"- Targets: {source_report.target_count}",
        "Targets:",
    ]
    for key in sorted(source_report.targets_by_key):
        target = source_report.targets_by_key[key]
        mapping = target.as_mapping()
        strongest_axes = sorted(mapping.items(), key=lambda item: (-item[1], item[0]))[:3]
        strongest_text = ", ".join(f"{axis}={value}" for axis, value in strongest_axes)
        lines.append(f"- {target.key}: {strongest_text}")
    lines.extend(_safety_lines())
    return passive_report_lines(_HEADER, lines)


def format_style_target_inspection(key: str) -> list[str]:
    """Return deterministic detail lines for one style target vector."""

    normalized_key = str(key).lower()
    target = STYLE_TARGET_VECTORS.get(normalized_key)
    if target is None:
        lines = [
            f"Key: {normalized_key}",
            "Found: False",
            "Message: Style target not found. No MIDI was sent. No command executed.",
        ]
        lines.extend(_safety_lines())
        return passive_report_lines(_INSPECT_HEADER, lines)

    lines = [
        f"Key: {target.key}",
        "Found: True",
        *_target_lines(target)[1:],
    ]
    lines.extend(_safety_lines())
    return passive_report_lines(_INSPECT_HEADER, lines)


def _parse_no_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("command takes no arguments")
    return {}


def _parse_key(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one key")
    return {"key": argv[0]}


def _write_lines(lines: Sequence[str]) -> int:
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _handle_style_target_report() -> int:
    return _write_lines(format_style_target_report())


def _handle_style_target_inspection(key: str) -> int:
    lines = format_style_target_inspection(key)
    output = "\n".join(lines)
    if "Found: True" in lines:
        sys.stdout.write(f"{output}\n")
        return 0
    sys.stderr.write(f"{output}\n")
    return 1


STYLE_TARGET_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-target-report",
    summary="Print the passive style target vector report.",
    args_parser=_parse_no_args,
    handler=_handle_style_target_report,
)
INSPECT_STYLE_TARGET_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="inspect-style-target",
    summary="Inspect passive style target vector metadata by key.",
    args_parser=_parse_key,
    handler=_handle_style_target_inspection,
)

register(STYLE_TARGET_REPORT_CLI_COMMAND)
register(INSPECT_STYLE_TARGET_CLI_COMMAND)

__all__ = [
    "INSPECT_STYLE_TARGET_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "STYLE_TARGET_REPORT_CLI_COMMAND",
    "StyleTargetCatalogReport",
    "build_style_target_catalog_report",
    "format_style_target_inspection",
    "format_style_target_report",
]
