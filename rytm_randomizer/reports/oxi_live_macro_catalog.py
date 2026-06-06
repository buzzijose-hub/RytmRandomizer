"""Passive OXI live macro catalog for Cockpit and operator review."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..engines.analog_rytm_snapshot_macros import SNAPSHOT_LIVE_MACROS

REPORT_TITLE: Final[str] = "RytmRandomizer OXI live macro catalog"
_A4_BLOCKED_ACTIONS: Final[tuple[str, ...]] = ("A4 outbound macro send",)
_A4_CANDIDATE_TRACKS: Final[tuple[int, ...]] = (1, 2, 3, 4)


@dataclass(frozen=True)
class OxiLiveMacroCard:
    """Single passive card describing one snapshot-shell macro."""

    name: str
    label: str
    risk_label: str
    affected_pads: tuple[int, ...]
    recovery_action: str
    summary: str


@dataclass(frozen=True)
class AnalogFourMacroRunway:
    """Analog Four runway state for this bundle."""

    status: str
    tracks: tuple[int, ...]
    summary: str


@dataclass(frozen=True)
class OxiLivePerformanceStep:
    """Passive step in the OXI-style live performance flow."""

    order: int
    name: str
    command: str
    send_policy: str
    recovery_action: str
    intent: str


@dataclass(frozen=True)
class OxiLiveMacroCatalogReport:
    """Passive report surface for Rytm macros plus A4 runway boundaries."""

    title: str
    rytm_macros: tuple[OxiLiveMacroCard, ...]
    performance_flow: tuple[OxiLivePerformanceStep, ...]
    analog_four: AnalogFourMacroRunway
    blocked_active_actions: tuple[str, ...]


_LIVE_PERFORMANCE_FLOW: Final[tuple[OxiLivePerformanceStep, ...]] = (
    OxiLivePerformanceStep(
        order=1,
        name="capture-anchor",
        command="kit/resnapshot",
        send_policy="receive-only",
        recovery_action="captured-anchor",
        intent="Capture the current Rytm kit as the safe anchor.",
    ),
    OxiLivePerformanceStep(
        order=2,
        name="kit-core",
        command="kit-core",
        send_policy="stage-review-send",
        recovery_action="home",
        intent="Normalize live guardrails and stage the first full-kit idea.",
    ),
    OxiLivePerformanceStep(
        order=3,
        name="hard-groove",
        command="hard-groove",
        send_policy="stage-review-send",
        recovery_action="home",
        intent="Push source-first rhythm movement while the kick stays protected.",
    ),
    OxiLivePerformanceStep(
        order=4,
        name="industrial",
        command="industrial",
        send_policy="stage-review-send",
        recovery_action="home",
        intent="Raise grit, pressure, and texture inside the live-safe guardrails.",
    ),
    OxiLivePerformanceStep(
        order=5,
        name="dub-pressure",
        command="dub-pressure",
        send_policy="stage-review-send",
        recovery_action="home",
        intent="Pull the kit toward space, delay, reverb, and lower-end pressure.",
    ),
    OxiLivePerformanceStep(
        order=6,
        name="transition",
        command="transition",
        send_policy="stage-review-send",
        recovery_action="home",
        intent="Create a short bridge or fill lane before returning to the groove.",
    ),
    OxiLivePerformanceStep(
        order=7,
        name="home",
        command="home",
        send_policy="restore-anchor",
        recovery_action="captured-anchor",
        intent="Return the staged plan to the captured safe kit.",
    ),
)


def _affected_pads(pad_policies: Mapping[int, object]) -> tuple[int, ...]:
    if not pad_policies:
        return tuple(range(1, 13))
    pads = sorted(pad_policies)
    if 12 not in pads:
        pads.append(12)
    return tuple(pads)


def build_oxi_live_macro_catalog_report() -> OxiLiveMacroCatalogReport:
    """Build the deterministic passive OXI live macro catalog report."""

    cards = tuple(
        OxiLiveMacroCard(
            name=macro.name,
            label=macro.label,
            risk_label=macro.risk_label,
            affected_pads=_affected_pads(macro.pad_policies),
            recovery_action=macro.recovery_action,
            summary=macro.summary,
        )
        for macro in SNAPSHOT_LIVE_MACROS.values()
    )
    return OxiLiveMacroCatalogReport(
        title=REPORT_TITLE,
        rytm_macros=cards,
        performance_flow=_LIVE_PERFORMANCE_FLOW,
        analog_four=AnalogFourMacroRunway(
            status="candidate-only",
            tracks=_A4_CANDIDATE_TRACKS,
            summary="A4 macro planning is passive/mock-only until hardware validation.",
        ),
        blocked_active_actions=_A4_BLOCKED_ACTIONS,
    )


def format_oxi_live_macro_catalog_report(
    report: OxiLiveMacroCatalogReport,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable lines."""

    lines = [report.title, "", "Rytm macros:"]
    for card in report.rytm_macros:
        pads = ", ".join(str(pad) for pad in card.affected_pads)
        lines.append(
            f"- {card.name} | {card.risk_label} | " f"recovery={card.recovery_action} | pads={pads}"
        )
        lines.append(f"  {card.summary}")
    lines.extend(("", "Live performance flow:"))
    for step in report.performance_flow:
        lines.append(
            f"- {step.order}. {step.name} | command={step.command} | "
            f"send={step.send_policy} | recovery={step.recovery_action}"
        )
        lines.append(f"  {step.intent}")
    lines.extend(
        (
            "",
            f"Analog Four runway: {report.analog_four.status}",
            f"  tracks: {', '.join(str(track) for track in report.analog_four.tracks)}",
            f"  {report.analog_four.summary}",
            "",
            "blocked active actions: " + ", ".join(report.blocked_active_actions),
        )
    )
    return tuple(lines)


def build_oxi_live_macro_catalog_payload() -> dict[str, object]:
    """Return a JSON-ready deterministic payload for GUI consumers."""

    report = build_oxi_live_macro_catalog_report()
    return {
        "title": report.title,
        "rytm_macros": [
            {
                "name": card.name,
                "label": card.label,
                "risk_label": card.risk_label,
                "affected_pads": list(card.affected_pads),
                "recovery_action": card.recovery_action,
                "summary": card.summary,
            }
            for card in report.rytm_macros
        ],
        "performance_flow": [
            {
                "order": step.order,
                "name": step.name,
                "command": step.command,
                "send_policy": step.send_policy,
                "recovery_action": step.recovery_action,
                "intent": step.intent,
            }
            for step in report.performance_flow
        ],
        "analog_four": {
            "status": report.analog_four.status,
            "tracks": list(report.analog_four.tracks),
            "summary": report.analog_four.summary,
        },
        "blocked_active_actions": list(report.blocked_active_actions),
    }


OXI_LIVE_MACRO_CATALOG_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "oxi-live-macro-catalog-report",
    "Print the passive OXI live macro catalog and candidate-only A4 runway.",
    format_lines=lambda: format_oxi_live_macro_catalog_report(
        build_oxi_live_macro_catalog_report()
    ),
    json_flag=False,
    error_formatter=None,
)

register(OXI_LIVE_MACRO_CATALOG_CLI_COMMAND)


__all__ = (
    "AnalogFourMacroRunway",
    "OxiLiveMacroCard",
    "OxiLiveMacroCatalogReport",
    "OxiLivePerformanceStep",
    "OXI_LIVE_MACRO_CATALOG_CLI_COMMAND",
    "REPORT_TITLE",
    "build_oxi_live_macro_catalog_payload",
    "build_oxi_live_macro_catalog_report",
    "format_oxi_live_macro_catalog_report",
)
