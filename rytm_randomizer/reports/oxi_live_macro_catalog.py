"""Passive OXI live macro catalog for Cockpit and operator review."""

from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final

from ..cli_registry import CliCommand, register
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
class OxiLiveMacroCatalogReport:
    """Passive report surface for Rytm macros plus A4 runway boundaries."""

    title: str
    rytm_macros: tuple[OxiLiveMacroCard, ...]
    analog_four: AnalogFourMacroRunway
    blocked_active_actions: tuple[str, ...]


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
            f"- {card.name} | {card.risk_label} | "
            f"recovery={card.recovery_action} | pads={pads}"
        )
        lines.append(f"  {card.summary}")
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
        "analog_four": {
            "status": report.analog_four.status,
            "tracks": list(report.analog_four.tracks),
            "summary": report.analog_four.summary,
        },
        "blocked_active_actions": list(report.blocked_active_actions),
    }


def _parse_oxi_live_macro_catalog_args(args: Sequence[str]) -> dict[str, object]:
    if args:
        raise ValueError("oxi-live-macro-catalog-report does not accept arguments")
    return {}


def _handle_oxi_live_macro_catalog_report() -> int:
    report = build_oxi_live_macro_catalog_report()
    sys.stdout.write("\n".join(format_oxi_live_macro_catalog_report(report)))
    sys.stdout.write("\n")
    return 0


OXI_LIVE_MACRO_CATALOG_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="oxi-live-macro-catalog-report",
    summary="Print the passive OXI live macro catalog and candidate-only A4 runway.",
    args_parser=_parse_oxi_live_macro_catalog_args,
    handler=_handle_oxi_live_macro_catalog_report,
)

register(OXI_LIVE_MACRO_CATALOG_CLI_COMMAND)


__all__ = (
    "AnalogFourMacroRunway",
    "OxiLiveMacroCard",
    "OxiLiveMacroCatalogReport",
    "OXI_LIVE_MACRO_CATALOG_CLI_COMMAND",
    "REPORT_TITLE",
    "build_oxi_live_macro_catalog_payload",
    "build_oxi_live_macro_catalog_report",
    "format_oxi_live_macro_catalog_report",
)
