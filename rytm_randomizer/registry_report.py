"""Passive in-memory reports for the unified registry view."""

from copy import deepcopy
import sys

from .registry import build_registry, list_registry_sections, summarize_registry


SAFETY_BOUNDARIES = (
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

UNSUPPORTED_SCOPE = (
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

ACTIVE_BEHAVIOR_STATUS = {
    "executes_commands": False,
    "dispatches_commands": False,
    "sends_midi": False,
    "opens_ports": False,
    "mutates_hardware": False,
    "writes_sysex": False,
}


def build_registry_report():
    """Return a copied, in-memory report for passive registry inspection."""
    registry_summary = summarize_registry()
    return {
        "title": "RytmRandomizer Passive Registry Report",
        "sections": tuple(list_registry_sections()),
        "section_counts": deepcopy(registry_summary["section_counts"]),
        "known_sections": ("commands", "scenes", "group_profiles"),
        "safety_boundaries": SAFETY_BOUNDARIES,
        "unsupported_scope": UNSUPPORTED_SCOPE,
        "active_behavior": deepcopy(ACTIVE_BEHAVIOR_STATUS),
        "source": {
            "registry_module": "rytm_randomizer.registry",
            "sections": tuple(build_registry().keys()),
            "in_memory_only": True,
        },
    }


def summarize_registry_report(report=None):
    """Return a compact copied summary for a registry report."""
    source_report = build_registry_report() if report is None else report
    return {
        "title": source_report["title"],
        "section_count": len(source_report["sections"]),
        "total_items": sum(source_report["section_counts"].values()),
        "sections": tuple(source_report["sections"]),
        "active_behavior": deepcopy(source_report["active_behavior"]),
    }


def format_registry_report(report=None):
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

    lines.append("Source: rytm_randomizer.registry")
    lines.append("In-memory only: True")
    return lines


def main(argv=None):
    """Print the passive registry report for explicit module execution."""
    _ = [] if argv is None else list(argv)
    sys.stdout.write("\n".join(format_registry_report()))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
