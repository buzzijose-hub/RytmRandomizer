"""Pure state reducer for ordinary CC, CC14, and NRPN observations."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final, Literal, TypeAlias, TypeVar

MidiObservationType: TypeAlias = Literal["CC", "CC14", "NRPN"]

OBSERVATION_CC: Final[MidiObservationType] = "CC"
OBSERVATION_CC14: Final[MidiObservationType] = "CC14"
OBSERVATION_NRPN: Final[MidiObservationType] = "NRPN"

_CHANNEL_COUNT: Final[int] = 16
_CC14_MSB_COUNT: Final[int] = 32
_EMPTY_CC14_MSB: Final[tuple[int | None, ...]] = (None,) * _CC14_MSB_COUNT
_TupleValue = TypeVar("_TupleValue")


@dataclass(frozen=True)
class MidiChannelObservationState:
    """Running controller-selection state for one zero-based MIDI channel."""

    cc14_msb: tuple[int | None, ...] = _EMPTY_CC14_MSB
    nrpn_msb: int | None = None
    nrpn_lsb: int | None = None
    data_entry_msb: int | None = None


@dataclass(frozen=True)
class MidiObservationState:
    """Immutable decoder state for all sixteen MIDI channels."""

    channels: tuple[MidiChannelObservationState, ...]


@dataclass(frozen=True)
class DecodedMidiObservation:
    """One raw or assembled controller observation."""

    message_type: MidiObservationType
    channel: int
    controller: int | None
    controller_lsb: int | None
    nrpn_address: tuple[int, int] | None
    raw_value: int
    value_14bit: int | None
    timestamp: float
    raw_bytes: tuple[int, int, int]


def empty_midi_observation_state() -> MidiObservationState:
    """Return an empty immutable decoder state."""

    return MidiObservationState(
        channels=tuple(MidiChannelObservationState() for _index in range(_CHANNEL_COUNT))
    )


def consume_midi_cc_bytes(
    state: object,
    message: tuple[int, int, int],
    *,
    timestamp: float,
) -> tuple[MidiObservationState, tuple[DecodedMidiObservation, ...]]:
    """Consume one 3-byte CC packet and emit raw plus assembled observations."""

    if not isinstance(state, MidiObservationState):
        raise TypeError("state must be a MidiObservationState")
    if len(message) != 3:
        raise ValueError("MIDI observation requires exactly three bytes")
    status, controller, value = message
    if status & 0xF0 != 0xB0:
        raise ValueError("MIDI observation supports control-change messages only")
    channel_index = status & 0x0F
    _validate_data_byte(controller, label="controller")
    _validate_data_byte(value, label="value")
    if timestamp < 0:
        raise ValueError("timestamp must be non-negative")

    channel_state = state.channels[channel_index]
    raw_observation = DecodedMidiObservation(
        message_type=OBSERVATION_CC,
        channel=channel_index + 1,
        controller=controller,
        controller_lsb=None,
        nrpn_address=None,
        raw_value=value,
        value_14bit=None,
        timestamp=timestamp,
        raw_bytes=message,
    )
    observations: list[DecodedMidiObservation] = [raw_observation]

    if 0 <= controller < _CC14_MSB_COUNT:
        cc14_values = _replace_tuple_value(channel_state.cc14_msb, controller, value)
        channel_state = replace(channel_state, cc14_msb=cc14_values)
    elif _CC14_MSB_COUNT <= controller < _CC14_MSB_COUNT * 2:
        controller_msb = controller - _CC14_MSB_COUNT
        msb_value = channel_state.cc14_msb[controller_msb]
        if msb_value is not None:
            observations.append(
                DecodedMidiObservation(
                    message_type=OBSERVATION_CC14,
                    channel=channel_index + 1,
                    controller=controller_msb,
                    controller_lsb=controller,
                    nrpn_address=None,
                    raw_value=value,
                    value_14bit=(msb_value << 7) | value,
                    timestamp=timestamp,
                    raw_bytes=message,
                )
            )

    if controller == 99:
        channel_state = replace(
            channel_state,
            nrpn_msb=None if value == 127 else value,
            data_entry_msb=None,
        )
    elif controller == 98:
        channel_state = replace(
            channel_state,
            nrpn_lsb=None if value == 127 else value,
            data_entry_msb=None,
        )
    elif controller in (100, 101):
        channel_state = replace(
            channel_state,
            nrpn_msb=None,
            nrpn_lsb=None,
            data_entry_msb=None,
        )
    elif controller == 6:
        channel_state = replace(channel_state, data_entry_msb=value)
        nrpn = _nrpn_observation(channel_state, value=value, timestamp=timestamp, raw_bytes=message)
        if nrpn is not None:
            observations.append(nrpn)
    elif controller == 38 and channel_state.data_entry_msb is not None:
        nrpn = _nrpn_observation(
            channel_state,
            value=value,
            timestamp=timestamp,
            raw_bytes=message,
            value_14bit=(channel_state.data_entry_msb << 7) | value,
        )
        if nrpn is not None:
            observations.append(nrpn)

    new_channels = _replace_tuple_value(state.channels, channel_index, channel_state)
    return MidiObservationState(channels=new_channels), tuple(observations)


def midi_observation_to_dict(observation: object) -> dict[str, object]:
    """Return a stable YAML/JSON-ready observation payload."""

    if not isinstance(observation, DecodedMidiObservation):
        raise TypeError("observation must be a DecodedMidiObservation")
    return {
        "message_type": observation.message_type,
        "channel": observation.channel,
        "controller": observation.controller,
        "controller_lsb": observation.controller_lsb,
        "nrpn_address": (
            list(observation.nrpn_address) if observation.nrpn_address is not None else None
        ),
        "raw_value": observation.raw_value,
        "value_14bit": observation.value_14bit,
        "timestamp": observation.timestamp,
        "raw_bytes": list(observation.raw_bytes),
    }


def format_midi_observation(observation: DecodedMidiObservation) -> str:
    """Format one observation for the input-only learning console."""

    if observation.message_type == OBSERVATION_NRPN:
        address = observation.nrpn_address
        address_text = "?:?" if address is None else f"{address[0]}:{address[1]}"
        target = f"NRPN {address_text}"
    elif observation.message_type == OBSERVATION_CC14:
        target = f"CC14 {observation.controller}/{observation.controller_lsb}"
    else:
        target = f"CC {observation.controller}"
    value_14bit = "" if observation.value_14bit is None else f" value14={observation.value_14bit}"
    return (
        f"t={observation.timestamp:.6f} ch={observation.channel} "
        f"{target} raw={observation.raw_value}{value_14bit}"
    )


def _nrpn_observation(
    state: MidiChannelObservationState,
    *,
    value: int,
    timestamp: float,
    raw_bytes: tuple[int, int, int],
    value_14bit: int | None = None,
) -> DecodedMidiObservation | None:
    if state.nrpn_msb is None or state.nrpn_lsb is None:
        return None
    return DecodedMidiObservation(
        message_type=OBSERVATION_NRPN,
        channel=(raw_bytes[0] & 0x0F) + 1,
        controller=None,
        controller_lsb=None,
        nrpn_address=(state.nrpn_msb, state.nrpn_lsb),
        raw_value=value,
        value_14bit=value_14bit,
        timestamp=timestamp,
        raw_bytes=raw_bytes,
    )


def _replace_tuple_value(
    values: tuple[_TupleValue, ...], index: int, value: _TupleValue
) -> tuple[_TupleValue, ...]:
    return values[:index] + (value,) + values[index + 1 :]


def _validate_data_byte(value: object, *, label: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 127:
        raise ValueError(f"{label} must be an integer in 0..127")


__all__ = [
    "OBSERVATION_CC",
    "OBSERVATION_CC14",
    "OBSERVATION_NRPN",
    "DecodedMidiObservation",
    "MidiChannelObservationState",
    "MidiObservationState",
    "MidiObservationType",
    "consume_midi_cc_bytes",
    "empty_midi_observation_state",
    "format_midi_observation",
    "midi_observation_to_dict",
]
