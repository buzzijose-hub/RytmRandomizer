"""Passive registry report.

Extracted from the former monolithic ``rytm_randomizer.reports`` module when
it reached the 1500-LOC comprehensibility cap (see
``tests/architecture/test_reports_max_module_size.py``). The public names are
re-exported from ``rytm_randomizer.reports`` so every existing import keeps
working.

**Typing note.** The report is a plain ``dict`` on the wire (callers index it
and hand it to ``json.dumps``), but its key set is fixed and known. Declaring
that as a ``TypedDict`` — rather than ``dict[str, object]`` — is what makes
this module strict-clean: the type checker knows ``report["sections"]`` is a
``tuple[str, ...]`` without any runtime narrowing helper. This mirrors the
pattern already used by the newer ``reports/live_gui_*_model.py`` modules.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Final, TypedDict

from ..formatter import passive_footer_lines


class RegistrySourceDict(TypedDict):
    """Provenance block for the registry report."""

    registry_module: str
    sections: tuple[str, ...]
    in_memory_only: bool


class RegistryReportDict(TypedDict):
    """Fixed shape of :func:`build_registry_report`."""

    title: str
    sections: tuple[str, ...]
    section_counts: dict[str, int]
    known_sections: tuple[str, ...]
    safety_boundaries: tuple[str, ...]
    unsupported_scope: tuple[str, ...]
    active_behavior: dict[str, bool]
    source: RegistrySourceDict


class RegistrySummaryDict(TypedDict):
    """Fixed shape of :func:`summarize_registry_report`."""

    title: str
    section_count: int
    total_items: int
    sections: tuple[str, ...]
    active_behavior: dict[str, bool]


SAFETY_BOUNDARIES: Final[tuple[str, ...]] = (
    "no MIDI sending",
    "no port opening",
    "no runtime dispatch",
    "no command execution",
    "no hardware mutation",
    "no SysEx writes",
    "no GUI",
    "no capture",
    "no Analog Four support",
    "no Pads 5-12 support",
)

UNSUPPORTED_SCOPE: Final[tuple[str, ...]] = (
    "MIDI sending",
    "MIDI port opening",
    "runtime dispatch",
    "command execution",
    "hardware state mutation",
    "SysEx writes",
    "GUI",
    "capture",
    "Analog Four",
    "Pads 5-12",
)

ACTIVE_BEHAVIOR_STATUS: Final[dict[str, bool]] = {
    "executes_commands": False,
    "dispatches_commands": False,
    "sends_midi": False,
    "opens_ports": False,
    "mutates_hardware": False,
    "writes_sysex": False,
}


def build_registry_report() -> RegistryReportDict:
    """Return a copied, in-memory report for passive registry inspection."""
    from ...registry import build_registry, list_registry_sections, summarize_registry

    registry_summary = summarize_registry()
    section_counts: dict[str, int] = {
        str(key): int(value) for key, value in dict(registry_summary["section_counts"]).items()
    }
    return {
        "title": "RytmRandomizer Passive Registry Report",
        "sections": tuple(str(section) for section in list_registry_sections()),
        "section_counts": section_counts,
        "known_sections": ("commands", "scenes", "group_profiles"),
        "safety_boundaries": SAFETY_BOUNDARIES,
        "unsupported_scope": UNSUPPORTED_SCOPE,
        "active_behavior": deepcopy(ACTIVE_BEHAVIOR_STATUS),
        "source": {
            "registry_module": "rytm_randomizer.registry",
            "sections": tuple(str(key) for key in build_registry()),
            "in_memory_only": True,
        },
    }


def summarize_registry_report(report: RegistryReportDict | None = None) -> RegistrySummaryDict:
    """Return a compact copied summary for a registry report."""
    source_report = build_registry_report() if report is None else report
    return {
        "title": source_report["title"],
        "section_count": len(source_report["sections"]),
        "total_items": sum(source_report["section_counts"].values()),
        "sections": tuple(source_report["sections"]),
        "active_behavior": deepcopy(source_report["active_behavior"]),
    }


def format_registry_report(report: RegistryReportDict | None = None) -> list[str]:
    """Return a deterministic human-readable report as a list of strings."""
    source_report = build_registry_report() if report is None else report
    lines = [
        source_report["title"],
        "Sections:",
    ]

    for section in source_report["sections"]:
        count = source_report["section_counts"][section]
        lines.append(f"- {section}: {count}")

    lines.extend(
        [
            "Safety Boundaries:",
            *[f"- {boundary}" for boundary in source_report["safety_boundaries"]],
            "Unsupported Scope:",
            *[f"- {scope}" for scope in source_report["unsupported_scope"]],
            "Active Behavior:",
        ]
    )

    for key in sorted(source_report["active_behavior"]):
        lines.append(f"- {key}: {source_report['active_behavior'][key]}")

    lines.extend(passive_footer_lines("registry"))
    return lines
