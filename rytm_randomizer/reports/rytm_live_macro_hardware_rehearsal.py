"""Passive hardware-rehearsal packet for Rytm live macro testing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..engines.analog_rytm_snapshot_macros import (
    SNAPSHOT_LIVE_MACROS,
    SnapshotLiveMacroSpec,
)
from .oxi_live_macro_catalog import _affected_pads as _macro_affected_pads

REPORT_TITLE: Final[str] = "RytmRandomizer passive Rytm live macro hardware rehearsal"
RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_COMMAND_NAME: Final[str] = (
    "rytm-live-macro-hardware-rehearsal-report"
)
LAUNCH_COMMAND: Final[str] = (
    "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell --confirm-rytm-snapshot-shell-send"
)
MACRO_CHECKPOINTS: Final[tuple[str, ...]] = (
    "capture anchor first",
    "run changes before send",
    "listen for musicality",
    "recover with home",
)
STUDIO_WORKFLOW: Final[tuple[str, ...]] = (
    "Capture the current Rytm kit with KIT SysEx before changing anything.",
    "Use `kit` or `resnapshot` whenever the hardware kit changes.",
    "Run `changes` before `send` or `go`.",
    "Fire one macro at a time and write musical notes before moving on.",
    "Keep OXI handling notes, triggers, mutes, and pattern motion.",
)
RECOVERY_CHECKS: Final[tuple[str, ...]] = (
    "`home` then `send` returns to the captured safe kit.",
    "`Z` then `send` is still the emergency return-to-anchor path.",
    "If anything sounds wrong, stop sending and reload the saved Rytm kit.",
)
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only report",
    "does not open MIDI ports",
    "does not send MIDI",
    "operator must run the armed shell manually",
)


@dataclass(frozen=True)
class PadLaneCheck:
    """Operator-facing note for a pad group to inspect during rehearsal."""

    pads: tuple[int, ...]
    summary: str
    expected_motion: str
    warning: str


@dataclass(frozen=True)
class RytmLiveMacroRehearsalCard:
    """Single macro checklist card for the next Rytm hardware session."""

    name: str
    label: str
    risk_label: str
    recovery_action: str
    affected_pads: tuple[int, ...]
    summary: str
    checkpoints: tuple[str, ...]


@dataclass(frozen=True)
class RytmLiveMacroHardwareRehearsalReport:
    """Passive report that prepares the next operator-present Rytm test."""

    title: str
    launch_command: str
    studio_workflow: tuple[str, ...]
    macros: tuple[RytmLiveMacroRehearsalCard, ...]
    pad_lane_checks: tuple[PadLaneCheck, ...]
    recovery_checks: tuple[str, ...]
    safety: tuple[str, ...]


PAD_LANE_CHECKS: Final[tuple[PadLaneCheck, ...]] = (
    PadLaneCheck(
        pads=(5, 9, 10, 11),
        summary="Pads 5, 9, 10, 11: SRC stays important",
        expected_motion="source movement plus overdrive, delay, and reverb; filter/LFO remain restrained",
        warning="Flag any macro that forgets SRC or pushes filter/LFO movement too hard.",
    ),
    PadLaneCheck(
        pads=(6, 7, 8),
        summary="Pads 6-8: tom/source movement",
        expected_motion="useful tom/source discovery with light filter movement and no LFO craziness",
        warning="Flag any XT/tom lane that loses its drum identity or gets too animated.",
    ),
    PadLaneCheck(
        pads=(2, 3, 4),
        summary="Pads 2-4: proven discovery lanes",
        expected_motion="wide discovery is acceptable as long as Pad 1 remains the kick anchor",
        warning="Listen for Dual VCO detune behavior and any non-recovering hardware display issue.",
    ),
    PadLaneCheck(
        pads=(12,),
        summary="Pad 12: supported but not Jose-critical",
        expected_motion="may move for users who rely on it, but it should never be required for Jose's core flow",
        warning="Do not remove Pad 12 from the product just because this setup rarely uses it.",
    ),
)


def _macro_card(macro: SnapshotLiveMacroSpec) -> RytmLiveMacroRehearsalCard:
    return RytmLiveMacroRehearsalCard(
        name=macro.name,
        label=macro.label,
        risk_label=macro.risk_label,
        recovery_action=macro.recovery_action,
        affected_pads=_macro_affected_pads(macro.pad_policies),
        summary=macro.summary,
        checkpoints=MACRO_CHECKPOINTS,
    )


def build_rytm_live_macro_hardware_rehearsal_report() -> RytmLiveMacroHardwareRehearsalReport:
    """Build the deterministic passive rehearsal packet."""

    return RytmLiveMacroHardwareRehearsalReport(
        title=REPORT_TITLE,
        launch_command=LAUNCH_COMMAND,
        studio_workflow=STUDIO_WORKFLOW,
        macros=tuple(_macro_card(macro) for macro in SNAPSHOT_LIVE_MACROS.values()),
        pad_lane_checks=PAD_LANE_CHECKS,
        recovery_checks=RECOVERY_CHECKS,
        safety=SAFETY_LINES,
    )


def format_rytm_live_macro_hardware_rehearsal_report(
    report: RytmLiveMacroHardwareRehearsalReport,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable text."""

    lines = [
        report.title,
        "",
        f"Launch command: {report.launch_command}",
        "",
        "Studio workflow:",
    ]
    lines.extend(f"- {step}" for step in report.studio_workflow)
    lines.extend(("", "Macro rehearsal cards:"))
    for macro in report.macros:
        pads = ", ".join(str(pad) for pad in macro.affected_pads)
        lines.append(
            f"- {macro.name} | {macro.risk_label} | "
            f"recovery={macro.recovery_action} | pads={pads}"
        )
        lines.append(f"  {macro.summary}")
        lines.append(f"  checkpoints: {', '.join(macro.checkpoints)}")
    lines.extend(("", "Pad lane checks:"))
    for lane in report.pad_lane_checks:
        pads = ", ".join(str(pad) for pad in lane.pads)
        lines.append(f"- {lane.summary} (pads {pads})")
        lines.append(f"  expect: {lane.expected_motion}")
        lines.append(f"  watch: {lane.warning}")
    lines.extend(("", "Recovery checks:"))
    lines.extend(f"- {check}" for check in report.recovery_checks)
    lines.extend(("", "Safety:"))
    lines.extend(f"- {line}" for line in report.safety)
    return tuple(lines)


def build_rytm_live_macro_hardware_rehearsal_payload() -> dict[str, object]:
    """Return a JSON-ready deterministic payload for GUI and docs consumers."""

    report = build_rytm_live_macro_hardware_rehearsal_report()
    return {
        "title": report.title,
        "launch_command": report.launch_command,
        "studio_workflow": list(report.studio_workflow),
        "macros": [
            {
                "name": macro.name,
                "label": macro.label,
                "risk_label": macro.risk_label,
                "recovery_action": macro.recovery_action,
                "affected_pads": list(macro.affected_pads),
                "summary": macro.summary,
                "checkpoints": list(macro.checkpoints),
            }
            for macro in report.macros
        ],
        "pad_lane_checks": [
            {
                "pads": list(lane.pads),
                "summary": lane.summary,
                "expected_motion": lane.expected_motion,
                "warning": lane.warning,
            }
            for lane in report.pad_lane_checks
        ],
        "recovery_checks": list(report.recovery_checks),
        "safety": list(report.safety),
    }


RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_COMMAND_NAME,
    "Print the passive Rytm live macro hardware rehearsal checklist.",
    format_lines=lambda: format_rytm_live_macro_hardware_rehearsal_report(
        build_rytm_live_macro_hardware_rehearsal_report()
    ),
    build_payload=build_rytm_live_macro_hardware_rehearsal_payload,
)

register(RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND)


__all__ = (
    "LAUNCH_COMMAND",
    "MACRO_CHECKPOINTS",
    "PAD_LANE_CHECKS",
    "RECOVERY_CHECKS",
    "REPORT_TITLE",
    "RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_CLI_COMMAND",
    "RYTM_LIVE_MACRO_HARDWARE_REHEARSAL_COMMAND_NAME",
    "RytmLiveMacroHardwareRehearsalReport",
    "RytmLiveMacroRehearsalCard",
    "SAFETY_LINES",
    "STUDIO_WORKFLOW",
    "PadLaneCheck",
    "build_rytm_live_macro_hardware_rehearsal_payload",
    "build_rytm_live_macro_hardware_rehearsal_report",
    "format_rytm_live_macro_hardware_rehearsal_report",
)
