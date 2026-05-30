"""Passive Analog Rytm CC observation report formatting."""

from __future__ import annotations

from typing import Final

from ..state.rytm_cc_observe import (
    ObservedRytmControl,
    ObservedRytmNrpn,
    RytmCcObserveSnapshot,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "Rytm CC observe"
SOURCE_MODULE: Final[str] = "reports.rytm_cc_observe"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


def format_rytm_cc_observe_report(
    snapshot: RytmCcObserveSnapshot,
    *,
    input_name: str,
) -> list[str]:
    """Return deterministic passive report lines for Rytm CC observations."""

    return passive_report_lines(_HEADER, _body_lines(snapshot, input_name=input_name))


def _body_lines(snapshot: RytmCcObserveSnapshot, *, input_name: str) -> list[str]:
    lines = [
        f"Input: {input_name}",
        "Opened output: False",
        "Sent MIDI: False",
        f"Observed CC messages: {snapshot.observed_cc_count}",
    ]

    for observation in snapshot.observations:
        lines.extend(_observation_lines(observation))

    lines.append(f"Observed NRPN messages: {snapshot.observed_nrpn_count}")
    for nrpn in snapshot.nrpn_observations:
        lines.extend(_nrpn_lines(nrpn))

    lines.extend(
        [
            f"Unknown CC observations: {snapshot.unknown_cc_count}",
            f"Ignored non-CC messages: {snapshot.ignored_message_count}",
            f"Out-of-scope channel messages: {snapshot.out_of_scope_message_count}",
        ]
    )
    return lines


def _nrpn_lines(nrpn: ObservedRytmNrpn) -> list[str]:
    value = str(nrpn.value_msb)
    if nrpn.value_lsb is not None:
        value = f"{value}:{nrpn.value_lsb}"
    lines = [
        (
            f"- Pad {nrpn.pad} (channel {nrpn.channel}) "
            f"NRPN {nrpn.nrpn_msb}:{nrpn.nrpn_lsb} value {value}"
        )
    ]
    labels = nrpn.label_names
    if labels:
        lines.append("  labels: " + "; ".join(labels))
    else:
        lines.append("  labels: unknown")
    return lines


def _observation_lines(observation: ObservedRytmControl) -> list[str]:
    lines = [
        (
            f"- Pad {observation.pad} (channel {observation.channel}) "
            f"CC{observation.control} value {observation.value}"
        )
    ]
    labels = observation.label_names
    if labels:
        lines.append("  labels: " + "; ".join(labels))
    else:
        lines.append("  labels: unknown")
    return lines


__all__ = [
    "REPORT_TITLE",
    "SOURCE_MODULE",
    "format_rytm_cc_observe_report",
]
