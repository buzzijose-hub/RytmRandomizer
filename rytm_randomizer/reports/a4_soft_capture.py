"""Passive Analog Four soft live capture report formatting."""

from __future__ import annotations

from typing import Final

from ..state.a4_soft_capture import (
    TRACK_COUNT,
    A4ObservedTrackState,
    A4SoftCaptureSnapshot,
    ObservedA4Parameter,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "A4 soft live capture"
SOURCE_MODULE: Final[str] = "reports.a4_soft_capture"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)


def format_a4_soft_capture_report(
    snapshot: A4SoftCaptureSnapshot,
    *,
    input_name: str,
) -> list[str]:
    """Return deterministic passive report lines for an A4 capture snapshot."""

    return passive_report_lines(_HEADER, _body_lines(snapshot, input_name=input_name))


def _body_lines(snapshot: A4SoftCaptureSnapshot, *, input_name: str) -> list[str]:
    lines = [
        f"Input: {input_name}",
        "Opened output: False",
        "Sent MIDI: False",
    ]

    for track in _tracks_by_number(snapshot):
        observed_parameters = sorted(track.parameters.values(), key=_observed_parameter_cc)
        lines.append(f"Track {track.track}: {len(observed_parameters)} observed params")
        lines.extend(_known_parameter_line(parameter) for parameter in observed_parameters)

    lines.extend(
        [
            "Unknown parameters: left untouched",
            f"Unknown raw control observations: {len(snapshot.unknown_controls)}",
            f"Ignored non-CC messages: {snapshot.ignored_message_count}",
            f"Out-of-scope channel messages: {snapshot.out_of_scope_message_count}",
        ]
    )
    return lines


def _tracks_by_number(snapshot: A4SoftCaptureSnapshot) -> tuple[A4ObservedTrackState, ...]:
    tracks_by_number = {track.track: track for track in snapshot.tracks}
    return tuple(
        tracks_by_number.get(track, A4ObservedTrackState(track=track))
        for track in range(1, TRACK_COUNT + 1)
    )


def _observed_parameter_cc(parameter: ObservedA4Parameter) -> tuple[int, int, int]:
    if parameter.nrpn_address is not None:
        return (1, parameter.nrpn_address[0], parameter.nrpn_address[1])
    return (0, parameter.cc, 0)


def _known_parameter_line(parameter: ObservedA4Parameter) -> str:
    if parameter.nrpn_address is not None:
        msb, lsb = parameter.nrpn_address
        return f"- {parameter.parameter}: {parameter.value} (NRPN {msb}:{lsb})"
    return f"- {parameter.parameter}: {parameter.value}"


__all__ = [
    "REPORT_TITLE",
    "SOURCE_MODULE",
    "format_a4_soft_capture_report",
]
