"""Pure passive Analog Four CC and NRPN capture state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Final, Protocol

from .message_values import coerce_int as _coerce_int

SOURCE: Final[str] = "passive_cc_nrpn_observation"
UNKNOWN_POLICY: Final[str] = "unknown_parameters_untouched"
TRACK_COUNT: Final[int] = 4

_CONTROL_CHANGE_TYPE: Final[str] = "control_change"
_UNKNOWN_CONTROL_REASON: Final[str] = "unknown_cc"
_UNKNOWN_NRPN_REASON: Final[str] = "unknown_nrpn"
_INCOMPLETE_NRPN_REASON: Final[str] = "incomplete_nrpn_address"
_NRPN_PARAMETER_MSB_CC: Final[int] = 99
_NRPN_PARAMETER_LSB_CC: Final[int] = 98
_NRPN_DATA_MSB_CC: Final[int] = 6
_EMPTY_PARAMETERS: Final[Mapping[str, ObservedA4Parameter]] = MappingProxyType({})
_EMPTY_NRPN_LOOKUP: Final[Mapping[tuple[int, int], A4CaptureCcMapping]] = MappingProxyType({})


class A4CaptureCcMapping(Protocol):
    @property
    def parameter(self) -> str: ...  # pragma: no cover - typing protocol

    @property
    def section(self) -> str: ...  # pragma: no cover - typing protocol


@dataclass(frozen=True)
class ObservedA4Parameter:
    track: int
    parameter: str
    section: str
    cc: int
    value: int
    observed_at: float
    transport: str = "cc"
    nrpn_address: tuple[int, int] | None = None


@dataclass(frozen=True)
class UnknownA4Control:
    channel: int
    control: int
    value: int
    observed_at: float
    reason: str


@dataclass(frozen=True)
class A4ObservedTrackState:
    track: int
    parameters: Mapping[str, ObservedA4Parameter] = field(default_factory=lambda: _EMPTY_PARAMETERS)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "parameters",
            MappingProxyType(dict(self.parameters)),
        )


@dataclass(frozen=True)
class A4NrpnSelector:
    """Most recently observed NRPN address bytes for one synth track."""

    msb: int | None = None
    lsb: int | None = None

    @property
    def address(self) -> tuple[int, int] | None:
        if self.msb is None or self.lsb is None:
            return None
        return (self.msb, self.lsb)


@dataclass(frozen=True)
class A4SoftCaptureSnapshot:
    tracks: tuple[A4ObservedTrackState, ...]
    nrpn_selectors: tuple[A4NrpnSelector, ...] = ()
    source: str = SOURCE
    unknown_policy: str = UNKNOWN_POLICY
    unknown_controls: tuple[UnknownA4Control, ...] = ()
    ignored_message_count: int = 0
    out_of_scope_message_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", tuple(self.tracks))
        object.__setattr__(self, "nrpn_selectors", tuple(self.nrpn_selectors))
        object.__setattr__(self, "unknown_controls", tuple(self.unknown_controls))

    @property
    def known_parameter_count(self) -> int:
        return sum(len(track.parameters) for track in self.tracks)


def empty_a4_soft_capture_snapshot() -> A4SoftCaptureSnapshot:
    return A4SoftCaptureSnapshot(
        tracks=_empty_tracks(),
        nrpn_selectors=_empty_nrpn_selectors(),
    )


def observe_a4_message(
    snapshot: A4SoftCaptureSnapshot,
    message: object,
    *,
    observed_at: float,
    cc_lookup: Mapping[int, A4CaptureCcMapping],
    nrpn_lookup: Mapping[tuple[int, int], A4CaptureCcMapping] = _EMPTY_NRPN_LOOKUP,
) -> A4SoftCaptureSnapshot:
    if getattr(message, "type", None) != _CONTROL_CHANGE_TYPE:
        return replace(
            snapshot,
            tracks=_ensure_four_tracks(snapshot.tracks),
            nrpn_selectors=_ensure_four_nrpn_selectors(snapshot.nrpn_selectors),
            ignored_message_count=snapshot.ignored_message_count + 1,
        )

    channel = _coerce_int(getattr(message, "channel", None))
    control = _coerce_int(getattr(message, "control", None))
    value = _coerce_int(getattr(message, "value", None))
    tracks = _ensure_four_tracks(snapshot.tracks)
    nrpn_selectors = _ensure_four_nrpn_selectors(snapshot.nrpn_selectors)

    if channel not in range(TRACK_COUNT):
        return replace(
            snapshot,
            tracks=tracks,
            nrpn_selectors=nrpn_selectors,
            out_of_scope_message_count=snapshot.out_of_scope_message_count + 1,
        )

    if control in {_NRPN_PARAMETER_MSB_CC, _NRPN_PARAMETER_LSB_CC}:
        return _observe_nrpn_selector(
            snapshot,
            tracks=tracks,
            selectors=nrpn_selectors,
            channel=channel,
            control=control,
            value=value,
        )

    if control == _NRPN_DATA_MSB_CC:
        return _observe_nrpn_data(
            snapshot,
            tracks=tracks,
            selectors=nrpn_selectors,
            channel=channel,
            value=value,
            observed_at=observed_at,
            nrpn_lookup=nrpn_lookup,
        )

    mapping = cc_lookup.get(control)
    if mapping is None:
        unknown = UnknownA4Control(
            channel=channel,
            control=control,
            value=value,
            observed_at=observed_at,
            reason=_UNKNOWN_CONTROL_REASON,
        )
        return replace(
            snapshot,
            tracks=tracks,
            nrpn_selectors=nrpn_selectors,
            unknown_controls=(*snapshot.unknown_controls, unknown),
        )

    track_index = channel
    track = tracks[track_index]
    observed = ObservedA4Parameter(
        track=track.track,
        parameter=mapping.parameter,
        section=mapping.section,
        cc=control,
        value=value,
        observed_at=observed_at,
    )
    parameters = dict(track.parameters)
    parameters[mapping.parameter] = observed
    next_track = A4ObservedTrackState(track=track.track, parameters=MappingProxyType(parameters))
    next_tracks = (
        *tracks[:track_index],
        next_track,
        *tracks[track_index + 1 :],
    )
    return replace(
        snapshot,
        tracks=next_tracks,
        nrpn_selectors=nrpn_selectors,
    )


def _observe_nrpn_selector(
    snapshot: A4SoftCaptureSnapshot,
    *,
    tracks: tuple[A4ObservedTrackState, ...],
    selectors: tuple[A4NrpnSelector, ...],
    channel: int,
    control: int,
    value: int,
) -> A4SoftCaptureSnapshot:
    selector = selectors[channel]
    if control == _NRPN_PARAMETER_MSB_CC:
        next_selector = replace(selector, msb=value)
    else:
        next_selector = replace(selector, lsb=value)
    next_selectors = (*selectors[:channel], next_selector, *selectors[channel + 1 :])
    return replace(
        snapshot,
        tracks=tracks,
        nrpn_selectors=next_selectors,
    )


def _observe_nrpn_data(
    snapshot: A4SoftCaptureSnapshot,
    *,
    tracks: tuple[A4ObservedTrackState, ...],
    selectors: tuple[A4NrpnSelector, ...],
    channel: int,
    value: int,
    observed_at: float,
    nrpn_lookup: Mapping[tuple[int, int], A4CaptureCcMapping],
) -> A4SoftCaptureSnapshot:
    address = selectors[channel].address
    mapping = None if address is None else nrpn_lookup.get(address)
    if mapping is None:
        unknown = UnknownA4Control(
            channel=channel,
            control=_NRPN_DATA_MSB_CC,
            value=value,
            observed_at=observed_at,
            reason=_INCOMPLETE_NRPN_REASON if address is None else _UNKNOWN_NRPN_REASON,
        )
        return replace(
            snapshot,
            tracks=tracks,
            nrpn_selectors=selectors,
            unknown_controls=(*snapshot.unknown_controls, unknown),
        )

    track = tracks[channel]
    observed = ObservedA4Parameter(
        track=track.track,
        parameter=mapping.parameter,
        section=mapping.section,
        cc=_NRPN_DATA_MSB_CC,
        value=value,
        observed_at=observed_at,
        transport="nrpn",
        nrpn_address=address,
    )
    parameters = dict(track.parameters)
    parameters[mapping.parameter] = observed
    next_track = A4ObservedTrackState(track=track.track, parameters=parameters)
    next_tracks = (*tracks[:channel], next_track, *tracks[channel + 1 :])
    return replace(
        snapshot,
        tracks=next_tracks,
        nrpn_selectors=selectors,
    )


def _empty_tracks() -> tuple[A4ObservedTrackState, ...]:
    return tuple(A4ObservedTrackState(track=track) for track in range(1, TRACK_COUNT + 1))


def _empty_nrpn_selectors() -> tuple[A4NrpnSelector, ...]:
    return tuple(A4NrpnSelector() for _ in range(TRACK_COUNT))


def _ensure_four_tracks(
    tracks: tuple[A4ObservedTrackState, ...],
) -> tuple[A4ObservedTrackState, ...]:
    if len(tracks) == TRACK_COUNT:
        return tracks

    by_track = {track.track: track for track in tracks}
    return tuple(
        by_track.get(track, A4ObservedTrackState(track=track))
        for track in range(1, TRACK_COUNT + 1)
    )


def _ensure_four_nrpn_selectors(
    selectors: tuple[A4NrpnSelector, ...],
) -> tuple[A4NrpnSelector, ...]:
    if len(selectors) == TRACK_COUNT:
        return selectors
    return tuple(
        selectors[index] if index < len(selectors) else A4NrpnSelector()
        for index in range(TRACK_COUNT)
    )


__all__ = [
    "SOURCE",
    "UNKNOWN_POLICY",
    "TRACK_COUNT",
    "A4CaptureCcMapping",
    "ObservedA4Parameter",
    "UnknownA4Control",
    "A4ObservedTrackState",
    "A4NrpnSelector",
    "A4SoftCaptureSnapshot",
    "empty_a4_soft_capture_snapshot",
    "observe_a4_message",
]
