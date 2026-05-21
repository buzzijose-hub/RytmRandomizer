"""Passive style-profile reports for techno design intent."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from ..data.style_profiles import STYLE_PROFILES, StyleProfile, StyleProfileScores
from .formatter import SAFETY_SECTION_HEADER, PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive style profile report"
LIST_TITLE: Final[str] = "RytmRandomizer passive style profile list"
INSPECT_TITLE: Final[str] = "RytmRandomizer passive style profile inspection"
SEARCH_TITLE: Final[str] = "RytmRandomizer passive style profile search"
SOURCE_MODULE: Final[str] = "reports.style_profiles"
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
_LIST_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=LIST_TITLE,
    source_module=SOURCE_MODULE,
)
_INSPECT_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=INSPECT_TITLE,
    source_module=SOURCE_MODULE,
)
_SEARCH_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=SEARCH_TITLE,
    source_module=SOURCE_MODULE,
)


@dataclass(frozen=True)
class StyleProfileCatalogReport:
    """Passive catalog report for all style profiles."""

    profile_count: int
    profiles_by_key: Mapping[str, StyleProfile]


def _join(values: Sequence[str]) -> str:
    return ", ".join(values)


def _score_text(scores: StyleProfileScores) -> str:
    return (
        f"energy={scores.energy}, density={scores.density}, darkness={scores.darkness}, "
        f"grit={scores.grit}, groove={scores.groove}, hypnosis={scores.hypnosis}, "
        f"space={scores.space}"
    )


def _search_text(profile: StyleProfile) -> str:
    values = [
        profile.key,
        profile.name,
        profile.summary,
        *profile.tags,
        *profile.scene_keys,
        *profile.rytm_focus,
        *profile.analog_four_focus,
        *profile.analyzer_targets,
    ]
    return "\n".join(values).lower()


def _safety_lines() -> list[str]:
    return [SAFETY_SECTION_HEADER, *[f"- {line}" for line in SAFETY_LINES]]


def _style_profiles_by_key() -> Mapping[str, StyleProfile]:
    return MappingProxyType(dict(STYLE_PROFILES))


def build_style_profile_catalog_report() -> StyleProfileCatalogReport:
    """Return passive catalog data for all style profiles."""

    profiles_by_key = _style_profiles_by_key()
    return StyleProfileCatalogReport(
        profile_count=len(profiles_by_key),
        profiles_by_key=profiles_by_key,
    )


def _profile_lines(profile: StyleProfile) -> list[str]:
    return [
        f"Key: {profile.key}",
        f"Name: {profile.name}",
        f"Summary: {profile.summary}",
        f"Tags: {_join(profile.tags)}",
        f"Scenes: {_join(profile.scene_keys)}",
        f"Scores: {_score_text(profile.scores)}",
        "Rytm focus:",
        *[f"- {item}" for item in profile.rytm_focus],
        "Analog Four focus:",
        *[f"- {item}" for item in profile.analog_four_focus],
        "Analyzer hooks:",
        *[f"- {item}" for item in profile.analyzer_targets],
    ]


def format_style_profile_report(
    report: StyleProfileCatalogReport | None = None,
) -> list[str]:
    """Return deterministic catalog lines for all style profiles."""

    source_report = build_style_profile_catalog_report() if report is None else report
    lines = [
        "Summary:",
        f"- Profiles: {source_report.profile_count}",
        "- Purpose: passive style intent for later snapshot and audio-analysis routing",
        "Profiles:",
    ]
    for key in sorted(source_report.profiles_by_key):
        profile = source_report.profiles_by_key[key]
        lines.extend(
            [
                f"{profile.key}: {profile.name}",
                f"  Tags: {_join(profile.tags)}",
                f"  Scenes: {_join(profile.scene_keys)}",
                f"  Scores: {_score_text(profile.scores)}",
                f"  Analyzer hooks: {_join(profile.analyzer_targets)}",
                f"  Summary: {profile.summary}",
            ]
        )
    lines.extend(_safety_lines())
    return passive_report_lines(_HEADER, lines)


def format_style_profile_list() -> list[str]:
    """Return deterministic list lines for all style profiles."""

    lines = [
        f"Count: {len(STYLE_PROFILES)}",
        "Items:",
    ]
    for key in sorted(STYLE_PROFILES):
        profile = STYLE_PROFILES[key]
        lines.append(f"- {key}: {profile.name} ({_join(profile.tags)})")
    lines.extend(_safety_lines())
    return passive_report_lines(_LIST_HEADER, lines)


def format_style_profile_inspection(key: str) -> list[str]:
    """Return deterministic detail lines for one style profile key."""

    normalized_key = str(key).lower()
    profile = STYLE_PROFILES.get(normalized_key)
    if profile is None:
        lines = [
            f"Key: {normalized_key}",
            "Found: False",
            "Message: Style profile not found. No MIDI was sent. No command executed.",
        ]
        lines.extend(_safety_lines())
        return passive_report_lines(_INSPECT_HEADER, lines)

    lines = [
        f"Key: {profile.key}",
        "Found: True",
        *_profile_lines(profile)[1:],
    ]
    lines.extend(_safety_lines())
    return passive_report_lines(_INSPECT_HEADER, lines)


def format_style_profile_search(query: str) -> list[str]:
    """Return deterministic search lines for style profile metadata."""

    normalized_query = str(query)
    search_query = normalized_query.lower()
    matches = [
        profile
        for key, profile in sorted(STYLE_PROFILES.items())
        if search_query in _search_text(profile)
    ]
    lines = [
        f"Query: {normalized_query}",
        f"Match count: {len(matches)}",
        "Matches:",
    ]
    if not matches:
        lines.append("- no matches found. No MIDI was sent. No command executed.")
    else:
        for profile in matches:
            lines.append(f"- {profile.key}: {profile.name} ({_join(profile.tags)})")
    lines.extend(_safety_lines())
    return passive_report_lines(_SEARCH_HEADER, lines)


def _parse_no_args(argv: Sequence[str]) -> dict[str, object]:
    if argv:
        raise ValueError("command takes no arguments")
    return {}


def _parse_key(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one key")
    return {"key": argv[0]}


def _parse_query(argv: Sequence[str]) -> dict[str, object]:
    if len(argv) != 1:
        raise ValueError("command requires exactly one query")
    return {"query": argv[0]}


def _write_lines(lines: Sequence[str]) -> int:
    sys.stdout.write("\n".join(lines))
    sys.stdout.write("\n")
    return 0


def _handle_style_profile_report() -> int:
    return _write_lines(format_style_profile_report())


def _handle_style_profile_list() -> int:
    return _write_lines(format_style_profile_list())


def _handle_style_profile_inspection(key: str) -> int:
    lines = format_style_profile_inspection(key)
    output = "\n".join(lines)
    if "Found: True" in lines:
        sys.stdout.write(f"{output}\n")
        return 0
    sys.stderr.write(f"{output}\n")
    return 1


def _handle_style_profile_search(query: str) -> int:
    return _write_lines(format_style_profile_search(query))


STYLE_PROFILE_REPORT_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="style-profile-report",
    summary="Print the passive style profile report.",
    args_parser=_parse_no_args,
    handler=_handle_style_profile_report,
)
LIST_STYLE_PROFILES_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="list-style-profiles",
    summary="List passive style profile keys and names.",
    args_parser=_parse_no_args,
    handler=_handle_style_profile_list,
)
INSPECT_STYLE_PROFILE_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="inspect-style-profile",
    summary="Inspect passive style profile metadata by key.",
    args_parser=_parse_key,
    handler=_handle_style_profile_inspection,
)
SEARCH_STYLE_PROFILES_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="search-style-profiles",
    summary="Search passive style profile metadata.",
    args_parser=_parse_query,
    handler=_handle_style_profile_search,
)

register(STYLE_PROFILE_REPORT_CLI_COMMAND)
register(LIST_STYLE_PROFILES_CLI_COMMAND)
register(INSPECT_STYLE_PROFILE_CLI_COMMAND)
register(SEARCH_STYLE_PROFILES_CLI_COMMAND)

__all__ = [
    "INSPECT_STYLE_PROFILE_CLI_COMMAND",
    "LIST_STYLE_PROFILES_CLI_COMMAND",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SEARCH_STYLE_PROFILES_CLI_COMMAND",
    "SOURCE_MODULE",
    "STYLE_PROFILE_REPORT_CLI_COMMAND",
    "StyleProfileCatalogReport",
    "build_style_profile_catalog_report",
    "format_style_profile_inspection",
    "format_style_profile_list",
    "format_style_profile_report",
    "format_style_profile_search",
]
