"""Passive Essence Plan report formatting.

This module previews how future analyzer tags can map onto 12 Analog Rytm pad
roles and candidate engines. It is metadata-only: no audio analysis, MIDI,
SysEx, port access, command execution, or hardware mutation.
"""

from __future__ import annotations

from .machine_catalog import MachineCandidate, build_essence_role_plan


def parse_essence_tags(raw: str) -> tuple[str, ...]:
    """Normalize a comma-separated essence tag string."""

    return tuple(tag.strip().lower() for tag in str(raw).split(",") if tag.strip())


def parse_discovery_value(raw: str) -> float:
    """Parse and validate a Reference/Discovery value."""

    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValueError("Discovery must be a number") from None
    if value < 0.0 or value > 1.0:
        raise ValueError("Discovery must be between 0.0 and 1.0")
    return value


def format_essence_plan_report(
    *,
    tags: tuple[str, ...],
    discovery: float,
) -> list[str]:
    """Format a deterministic passive 12-pad essence plan preview."""

    role_plan = build_essence_role_plan(essence_tags=tags, discovery=discovery)
    lines = [
        "RytmRandomizer passive Essence Plan Report",
        f"Essence tags: {_format_tags(tags)}",
        f"Discovery: {discovery:.2f}",
        f"Candidate mode: {_candidate_mode(discovery)}",
        "12-pad role plan:",
    ]

    for assignment in role_plan:
        candidate_text = ", ".join(
            _format_candidate(candidate) for candidate in assignment.candidates
        )
        lines.append(f"- Pad {assignment.pad} / {assignment.role.label}: {candidate_text}")

    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- no audio file analysis",
            "- no MIDI sending",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no SysEx writes",
            "- no Pads 5-12 runtime mutation",
            "- no hardware required",
        ]
    )
    return lines


def format_essence_plan_error(message: str) -> list[str]:
    """Format a deterministic passive Essence Plan error report."""

    return [
        "RytmRandomizer passive Essence Plan Report",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- no MIDI sending",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _format_tags(tags: tuple[str, ...]) -> str:
    return ", ".join(tags) if tags else "none"


def _candidate_mode(discovery: float) -> str:
    if discovery >= 0.75:
        return "mapped engines plus future inventory candidates"
    return "mapped mutable engines only"


def _format_candidate(candidate: MachineCandidate) -> str:
    marker = "mutable" if candidate.machine.support_status == "mutable_v134" else "future"
    return f"{candidate.machine.label} [{marker}]"
