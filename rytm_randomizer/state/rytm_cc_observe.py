"""Pure passive Analog Rytm control-change observation state."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Protocol

from .message_values import coerce_int as _coerce_int

SOURCE: Final[str] = "passive_rytm_cc_observation"
UNKNOWN_POLICY: Final[str] = "unknown_controls_reported_only"
TRACK_COUNT: Final[int] = 12

_CONTROL_CHANGE_TYPE: Final[str] = "control_change"


class RytmObserveCcMapping(Protocol):
    # Read-only property members so frozen-dataclass fact rows (e.g.
    # ``data.AnalogRytmCcMapping``) satisfy the protocol — a plain
    # attribute member would demand writability the frozen rows refuse.
    #
    # ``pragma: no cover`` on each stub: a Protocol property body is a
    # structural-typing declaration that is never executed (concrete
    # implementers provide the real accessor), yet coverage records the
    # ``...`` as a half-covered branch. Justified per
    # docs/ARCHITECTURE.md §8 — declaration-only surface with no live
    # caller. Removing the properties is not an option: they are what lets
    # frozen fact rows satisfy the protocol under strict Pyright.
    @property
    def section(self) -> str: ...  # pragma: no cover - protocol declaration

    @property
    def parameter(self) -> str: ...  # pragma: no cover - protocol declaration

    @property
    def cc_msb(self) -> int: ...  # pragma: no cover - protocol declaration

    @property
    def nrpn_msb(self) -> int | None: ...  # pragma: no cover - protocol declaration

    @property
    def nrpn_lsb(self) -> int | None: ...  # pragma: no cover - protocol declaration

    @property
    def scope(self) -> str: ...  # pragma: no cover - protocol declaration


class RytmObserveExactEvent(Protocol):
    channel: int
    machine_key: str
    section: str
    parameter: str
    cc_msb: int
    source: str


class RytmObserveAnchorEvent(RytmObserveExactEvent, Protocol):
    pad: int
    value: int


@dataclass(frozen=True)
class RytmCcLabel:
    section: str
    parameter: str
    scope: str
    machine_key: str | None = None
    nrpn_msb: int | None = None
    nrpn_lsb: int | None = None

    @property
    def display_name(self) -> str:
        if self.machine_key is not None:
            return f"machine:{self.machine_key}:{self.parameter}"
        return f"{self.section}:{self.parameter}"


@dataclass(frozen=True)
class ObservedRytmControl:
    channel: int
    pad: int
    control: int
    value: int
    observed_at: float
    labels: tuple[RytmCcLabel, ...] = ()

    @property
    def label_names(self) -> tuple[str, ...]:
        return tuple(label.display_name for label in self.labels)


@dataclass(frozen=True)
class RytmDualVcoDetuneAnchor:
    pad: int
    channel: int
    control: int
    anchor_value: int


@dataclass(frozen=True)
class ObservedRytmNrpn:
    channel: int
    pad: int
    nrpn_msb: int
    nrpn_lsb: int
    value_msb: int
    observed_at: float
    value_lsb: int | None = None
    labels: tuple[RytmCcLabel, ...] = ()

    @property
    def label_names(self) -> tuple[str, ...]:
        return tuple(label.display_name for label in self.labels)


@dataclass(frozen=True)
class RytmCcObserveSnapshot:
    observations: tuple[ObservedRytmControl, ...]
    nrpn_observations: tuple[ObservedRytmNrpn, ...] = ()
    source: str = SOURCE
    unknown_policy: str = UNKNOWN_POLICY
    ignored_message_count: int = 0
    out_of_scope_message_count: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(self, "observations", tuple(self.observations))
        object.__setattr__(self, "nrpn_observations", tuple(self.nrpn_observations))

    @property
    def observed_cc_count(self) -> int:
        return len(self.observations)

    @property
    def observed_nrpn_count(self) -> int:
        return len(self.nrpn_observations)

    @property
    def unknown_cc_count(self) -> int:
        return sum(1 for observation in self.observations if not observation.labels)


def empty_rytm_cc_observe_snapshot() -> RytmCcObserveSnapshot:
    return RytmCcObserveSnapshot(observations=())


def build_rytm_cc_label_lookup(
    mappings: Iterable[RytmObserveCcMapping],
) -> Mapping[int, tuple[RytmCcLabel, ...]]:
    grouped: dict[int, list[RytmCcLabel]] = {}
    for mapping in mappings:
        machine_key = _machine_key_for(mapping)
        label = RytmCcLabel(
            section=mapping.section,
            parameter=mapping.parameter,
            scope=mapping.scope,
            machine_key=machine_key,
            nrpn_msb=mapping.nrpn_msb,
            nrpn_lsb=mapping.nrpn_lsb,
        )
        grouped.setdefault(mapping.cc_msb, []).append(label)

    return MappingProxyType(
        {
            control: tuple(sorted(labels, key=_label_sort_key))
            for control, labels in sorted(grouped.items())
        }
    )


def build_rytm_cc_exact_label_lookup(
    events: Iterable[RytmObserveExactEvent],
) -> Mapping[tuple[int, int], tuple[RytmCcLabel, ...]]:
    grouped: dict[tuple[int, int], list[RytmCcLabel]] = {}
    for event in events:
        nrpn_msb, nrpn_lsb = _nrpn_address_for_exact_event(event)
        label = RytmCcLabel(
            section=event.section,
            parameter=event.parameter,
            scope=event.source,
            machine_key=(event.machine_key if event.source == "machine_src" else None),
            nrpn_msb=nrpn_msb,
            nrpn_lsb=nrpn_lsb,
        )
        grouped.setdefault((event.channel, event.cc_msb), []).append(label)

    return MappingProxyType(
        {key: tuple(sorted(labels, key=_label_sort_key)) for key, labels in sorted(grouped.items())}
    )


def build_rytm_dual_vco_detune_anchor_lookup(
    events: Iterable[RytmObserveAnchorEvent],
) -> Mapping[tuple[int, int], RytmDualVcoDetuneAnchor]:
    """Return exact Dual VCO detune anchors keyed by ``(channel, CC)``."""

    anchors: dict[tuple[int, int], RytmDualVcoDetuneAnchor] = {}
    for event in events:
        if not _is_dual_vco_detune_event(event):
            continue
        anchors[(event.channel, event.cc_msb)] = RytmDualVcoDetuneAnchor(
            pad=event.pad,
            channel=event.channel,
            control=event.cc_msb,
            anchor_value=event.value,
        )
    return MappingProxyType(dict(sorted(anchors.items())))


def observe_rytm_cc_message(
    snapshot: RytmCcObserveSnapshot,
    message: object,
    *,
    observed_at: float,
    cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]],
    exact_cc_lookup: Mapping[tuple[int, int], tuple[RytmCcLabel, ...]] | None = None,
) -> RytmCcObserveSnapshot:
    if getattr(message, "type", None) != _CONTROL_CHANGE_TYPE:
        return RytmCcObserveSnapshot(
            observations=snapshot.observations,
            nrpn_observations=snapshot.nrpn_observations,
            source=snapshot.source,
            unknown_policy=snapshot.unknown_policy,
            ignored_message_count=snapshot.ignored_message_count + 1,
            out_of_scope_message_count=snapshot.out_of_scope_message_count,
        )

    channel = _coerce_int(getattr(message, "channel", None))
    control = _coerce_int(getattr(message, "control", None))
    value = _coerce_int(getattr(message, "value", None))

    if channel not in range(TRACK_COUNT):
        return RytmCcObserveSnapshot(
            observations=snapshot.observations,
            nrpn_observations=snapshot.nrpn_observations,
            source=snapshot.source,
            unknown_policy=snapshot.unknown_policy,
            ignored_message_count=snapshot.ignored_message_count,
            out_of_scope_message_count=snapshot.out_of_scope_message_count + 1,
        )

    observed = ObservedRytmControl(
        channel=channel,
        pad=channel + 1,
        control=control,
        value=value,
        observed_at=observed_at,
        labels=_labels_for_control(
            cc_lookup,
            exact_cc_lookup,
            channel=channel,
            control=control,
        ),
    )
    next_observations = (*snapshot.observations, observed)
    next_nrpn_observations = _next_nrpn_observations(
        snapshot.nrpn_observations,
        next_observations,
        observed,
        cc_lookup,
        exact_cc_lookup,
    )
    return RytmCcObserveSnapshot(
        observations=next_observations,
        nrpn_observations=next_nrpn_observations,
        source=snapshot.source,
        unknown_policy=snapshot.unknown_policy,
        ignored_message_count=snapshot.ignored_message_count,
        out_of_scope_message_count=snapshot.out_of_scope_message_count,
    )


def _next_nrpn_observations(
    previous_nrpn: tuple[ObservedRytmNrpn, ...],
    observations: tuple[ObservedRytmControl, ...],
    observed: ObservedRytmControl,
    cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]],
    exact_cc_lookup: Mapping[tuple[int, int], tuple[RytmCcLabel, ...]] | None,
) -> tuple[ObservedRytmNrpn, ...]:
    if observed.control == 6:
        nrpn_msb = _latest_control_value(observations, observed.channel, 99)
        nrpn_lsb = _latest_control_value(observations, observed.channel, 98)
        if nrpn_msb is None or nrpn_lsb is None:
            return previous_nrpn
        return (
            *previous_nrpn,
            ObservedRytmNrpn(
                channel=observed.channel,
                pad=observed.pad,
                nrpn_msb=nrpn_msb,
                nrpn_lsb=nrpn_lsb,
                value_msb=observed.value,
                observed_at=observed.observed_at,
                labels=_labels_for_nrpn(
                    cc_lookup,
                    exact_cc_lookup,
                    channel=observed.channel,
                    nrpn_msb=nrpn_msb,
                    nrpn_lsb=nrpn_lsb,
                ),
            ),
        )

    if observed.control == 38:
        return _attach_value_lsb(previous_nrpn, observed)

    return previous_nrpn


def _labels_for_control(
    cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]],
    exact_cc_lookup: Mapping[tuple[int, int], tuple[RytmCcLabel, ...]] | None,
    *,
    channel: int,
    control: int,
) -> tuple[RytmCcLabel, ...]:
    if exact_cc_lookup is not None:
        exact_labels = exact_cc_lookup.get((channel, control), ())
        if exact_labels:
            return exact_labels
    return cc_lookup.get(control, ())


def _latest_control_value(
    observations: tuple[ObservedRytmControl, ...],
    channel: int,
    control: int,
) -> int | None:
    for observation in reversed(observations):
        if observation.channel == channel and observation.control == control:
            return observation.value
    return None


def _attach_value_lsb(
    nrpn_observations: tuple[ObservedRytmNrpn, ...],
    observed: ObservedRytmControl,
) -> tuple[ObservedRytmNrpn, ...]:
    for index in range(len(nrpn_observations) - 1, -1, -1):
        nrpn = nrpn_observations[index]
        if nrpn.channel == observed.channel and nrpn.value_lsb is None:
            updated = ObservedRytmNrpn(
                channel=nrpn.channel,
                pad=nrpn.pad,
                nrpn_msb=nrpn.nrpn_msb,
                nrpn_lsb=nrpn.nrpn_lsb,
                value_msb=nrpn.value_msb,
                value_lsb=observed.value,
                observed_at=nrpn.observed_at,
                labels=nrpn.labels,
            )
            return (
                *nrpn_observations[:index],
                updated,
                *nrpn_observations[index + 1 :],
            )
    return nrpn_observations


def _labels_for_nrpn(
    cc_lookup: Mapping[int, tuple[RytmCcLabel, ...]],
    exact_cc_lookup: Mapping[tuple[int, int], tuple[RytmCcLabel, ...]] | None,
    *,
    channel: int,
    nrpn_msb: int,
    nrpn_lsb: int,
) -> tuple[RytmCcLabel, ...]:
    labels_by_name: dict[str, RytmCcLabel] = {}
    if exact_cc_lookup is not None:
        for key, labels in exact_cc_lookup.items():
            label_channel, _control = key
            if label_channel != channel:
                continue
            for label in labels:
                if label.nrpn_msb == nrpn_msb and label.nrpn_lsb == nrpn_lsb:
                    labels_by_name.setdefault(label.display_name, label)
        if labels_by_name:
            return tuple(sorted(labels_by_name.values(), key=_label_sort_key))

    for labels in cc_lookup.values():
        for label in labels:
            if label.nrpn_msb == nrpn_msb and label.nrpn_lsb == nrpn_lsb:
                labels_by_name.setdefault(label.display_name, label)
    return tuple(sorted(labels_by_name.values(), key=_label_sort_key))


def _nrpn_address_for_exact_event(event: RytmObserveExactEvent) -> tuple[int | None, int | None]:
    if event.source == "machine_src" and 16 <= event.cc_msb <= 23:
        return 1, event.cc_msb - 16
    return None, None


def _is_dual_vco_detune_event(event: RytmObserveExactEvent) -> bool:
    return (
        event.source == "machine_src"
        and event.machine_key == "dual_vco"
        and event.parameter == "Osc 2 Detune"
    )


def _machine_key_for(mapping: RytmObserveCcMapping) -> str | None:
    machine_key = getattr(mapping, "machine_key", None)
    if isinstance(machine_key, str):
        return machine_key
    return None


def _label_sort_key(label: RytmCcLabel) -> tuple[int, str, str, str]:
    if label.machine_key is None:
        return (0, label.section, "", label.parameter)
    return (1, label.machine_key, label.section, label.parameter)


__all__ = [
    "SOURCE",
    "UNKNOWN_POLICY",
    "TRACK_COUNT",
    "RytmObserveCcMapping",
    "RytmObserveAnchorEvent",
    "RytmObserveExactEvent",
    "RytmDualVcoDetuneAnchor",
    "RytmCcLabel",
    "ObservedRytmControl",
    "ObservedRytmNrpn",
    "RytmCcObserveSnapshot",
    "empty_rytm_cc_observe_snapshot",
    "build_rytm_dual_vco_detune_anchor_lookup",
    "build_rytm_cc_label_lookup",
    "build_rytm_cc_exact_label_lookup",
    "observe_rytm_cc_message",
]
