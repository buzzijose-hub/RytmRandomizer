"""Pure passive Analog Four control-change capture state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Protocol

from .message_values import coerce_int as _coerce_int

SOURCE: Final[str] = "passive_cc_observation"
UNKNOWN_POLICY: Final[str] = "unknown_parameters_untouched"
TRACK_COUNT: Final[int] = 4

_CONTROL_CHANGE_TYPE: Final[str] = "control_change"
_UNKNOWN_CONTROL_REASON: Final[str] = "unknown_cc"
_EMPTY_PARAMETERS: Final[Mapping[str, ObservedA4Parameter]] = MappingProxyType({})


class A4CaptureCcMapping(Protocol):
    parameter: str
    section: str


@dataclass(frozen=True)
class ObservedA4Parameter:
    track: int
    parameter: str
    section: str
    cc: int
    value: int
    observed_at: float


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
class A4SoftCaptureSnapshot:
    tracks: tuple[A4ObservedTrackState, ...]
    source: str = SOURCE
    unknown_policy: str = UNKNOWN_POLICY
    unknown_controls: tuple[UnknownA4Control, ...] = ()
    ignored_message_count: int = 0
    out_of_scope_message_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "tracks", tuple(self.tracks))
        object.__setattr__(self, "unknown_controls", tuple(self.unknown_controls))

    @property
    def known_parameter_count(self) -> int:
        return sum(len(track.parameters) for track in self.tracks)


def empty_a4_soft_capture_snapshot() -> A4SoftCaptureSnapshot:
    return A4SoftCaptureSnapshot(tracks=_empty_tracks())


def observe_a4_message(
    snapshot: A4SoftCaptureSnapshot,
    message: object,
    *,
    observed_at: float,
    cc_lookup: Mapping[int, A4CaptureCcMapping],
) -> A4SoftCaptureSnapshot:
    if getattr(message, "type", None) != _CONTROL_CHANGE_TYPE:
        return A4SoftCaptureSnapshot(
            tracks=_ensure_four_tracks(snapshot.tracks),
            source=snapshot.source,
            unknown_policy=snapshot.unknown_policy,
            unknown_controls=snapshot.unknown_controls,
            ignored_message_count=snapshot.ignored_message_count + 1,
            out_of_scope_message_count=snapshot.out_of_scope_message_count,
        )

    channel = _coerce_int(getattr(message, "channel", None))
    control = _coerce_int(getattr(message, "control", None))
    value = _coerce_int(getattr(message, "value", None))
    tracks = _ensure_four_tracks(snapshot.tracks)

    if channel not in range(TRACK_COUNT):
        return A4SoftCaptureSnapshot(
            tracks=tracks,
            source=snapshot.source,
            unknown_policy=snapshot.unknown_policy,
            unknown_controls=snapshot.unknown_controls,
            ignored_message_count=snapshot.ignored_message_count,
            out_of_scope_message_count=snapshot.out_of_scope_message_count + 1,
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
        return A4SoftCaptureSnapshot(
            tracks=tracks,
            source=snapshot.source,
            unknown_policy=snapshot.unknown_policy,
            unknown_controls=(*snapshot.unknown_controls, unknown),
            ignored_message_count=snapshot.ignored_message_count,
            out_of_scope_message_count=snapshot.out_of_scope_message_count,
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
    return A4SoftCaptureSnapshot(
        tracks=next_tracks,
        source=snapshot.source,
        unknown_policy=snapshot.unknown_policy,
        unknown_controls=snapshot.unknown_controls,
        ignored_message_count=snapshot.ignored_message_count,
        out_of_scope_message_count=snapshot.out_of_scope_message_count,
    )


def _empty_tracks() -> tuple[A4ObservedTrackState, ...]:
    return tuple(A4ObservedTrackState(track=track) for track in range(1, TRACK_COUNT + 1))


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


__all__ = [
    "SOURCE",
    "UNKNOWN_POLICY",
    "TRACK_COUNT",
    "A4CaptureCcMapping",
    "ObservedA4Parameter",
    "UnknownA4Control",
    "A4ObservedTrackState",
    "A4SoftCaptureSnapshot",
    "empty_a4_soft_capture_snapshot",
    "observe_a4_message",
]
