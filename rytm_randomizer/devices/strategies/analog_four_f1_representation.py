"""Pure scoped F1 value/observation model, never a sender or commit receipt.

Inputs are already parsed bytes and caller-resolved synth-track context. The
caller owns current/pending binding validity and lifetime; no channel routing,
atomicity, queue drain, physical Hz or runtime validation is inferred here.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum, auto

from ...data.analog_four_f1_contract import (
    A4_F1_BASELINE_CURRENT,
    A4_F1_BASELINE_PENDING,
    A4_F1_BASELINE_UNKNOWN,
    A4_F1_DATA_BYTE_MAX,
    A4_F1_DISPLAY_SCALE,
    A4_F1_HIGH_BYTE_MASK,
    A4_F1_LOW_BYTE_MASK,
    A4_F1_MAPPING,
    A4_F1_NATIVE_MAX,
    A4_F1_NATIVE_SCALE,
    A4_F1_NRPN_DATA_LSB_CC,
    A4_F1_NRPN_NULL_ADDRESS_HALF,
    A4_F1_WIRE14_MAX,
    F1BaselineSource,
)
from ...data.analog_four_midi import (
    ANALOG_FOUR_NRPN_DATA_MSB_CC,
    ANALOG_FOUR_NRPN_PARAMETER_LSB_CC,
    ANALOG_FOUR_NRPN_PARAMETER_MSB_CC,
)
from ...data.analog_four_saved_kit_layout import A4_KIT_SYNTH_TRACK_COUNT
from ...guardrails.input_validation import require_int
from ...snapshot.elektron_u14 import decode_elektron_u14, encode_elektron_u14


def _require_f1_value(value: object, maximum: int, name: str) -> int:
    result = require_int(value, name)
    if not 0 <= result <= maximum:
        raise ValueError(f"{name} outside 0..{maximum}")
    return result


def native_to_screen(native: int) -> str:
    """Forward two-decimal F1 label, with truncation and no unique inverse."""
    native = _require_f1_value(native, A4_F1_NATIVE_MAX, "native")
    hundredths = native * A4_F1_DISPLAY_SCALE // A4_F1_NATIVE_SCALE
    return f"{hundredths // A4_F1_DISPLAY_SCALE}.{hundredths % A4_F1_DISPLAY_SCALE:02d}"


def native_to_wire14(native: int) -> int:
    """Stock precision-one wire conversion discards the low native bit."""
    return _require_f1_value(native, A4_F1_NATIVE_MAX, "native") >> 1


def parsed_wire14_to_native(wire14: int) -> int:
    """Parsed NRPN value-stage candidate; it does not acknowledge a commit."""
    return _require_f1_value(wire14, A4_F1_WIRE14_MAX, "wire14") << 1


def split_wire14(wire14: int) -> tuple[int, int]:
    """Split a validated fourteen-bit scalar into two inert data bytes."""
    wire14 = _require_f1_value(wire14, A4_F1_WIRE14_MAX, "wire14")
    encoded = encode_elektron_u14(wire14)
    return encoded[0], encoded[1]


def join_parsed_bytes(msb: int, lsb: int) -> int:
    """Concatenate parsed bytes; this alone is not a native parser model."""
    return decode_elektron_u14(
        _require_f1_value(msb, A4_F1_DATA_BYTE_MAX, "msb"),
        _require_f1_value(lsb, A4_F1_DATA_BYTE_MAX, "lsb"),
    )


@dataclass(frozen=True)
class AnalogFourF1Representation:
    native: int
    screen: str
    wire14: int
    msb: int
    lsb: int
    lost_native_lsb: int

    @property
    def exact_wire_roundtrip(self) -> bool:
        return self.lost_native_lsb == 0


def represent(native: int) -> AnalogFourF1Representation:
    """Keep the exact word distinct from its lossy label and wire value."""
    wire14 = native_to_wire14(native)
    msb, lsb = split_wire14(wire14)
    return AnalogFourF1Representation(
        native, native_to_screen(native), wire14, msb, lsb, native & 1
    )


def _require_f1_cc(control: int, value: int) -> None:
    _require_f1_value(control, A4_F1_DATA_BYTE_MAX, "control")
    _require_f1_value(value, A4_F1_DATA_BYTE_MAX, "value")
    if control not in (A4_F1_MAPPING.cc_msb, A4_F1_MAPPING.cc_lsb):
        raise ValueError("control is not F1 CC18 or CC50")


def apply_parsed_cc_half(baseline: int, control: int, value: int) -> int:
    """Preserve/replace the native low byte, then apply the F1 queue bound."""
    baseline = _require_f1_value(baseline, A4_F1_NATIVE_MAX, "baseline")
    _require_f1_cc(control, value)
    if control == A4_F1_MAPPING.cc_msb:
        proposed = (value << 8) | (baseline & A4_F1_LOW_BYTE_MASK)
    else:
        proposed = (baseline & A4_F1_HIGH_BYTE_MASK) | (value << 1)
    return min(A4_F1_NATIVE_MAX, proposed)


def stock_cc_samples(coarse_sample: int, fine_sample: int) -> tuple[int, int]:
    """Model separate getter samples, without asserting snapshot coherence."""
    coarse_sample = _require_f1_value(coarse_sample, A4_F1_NATIVE_MAX, "coarse sample")
    fine_sample = _require_f1_value(fine_sample, A4_F1_NATIVE_MAX, "fine sample")
    return coarse_sample >> 8, (fine_sample >> 1) & A4_F1_DATA_BYTE_MAX


@dataclass(frozen=True)
class AnalogFourF1CcObservation:
    track_index: int | None
    control: int
    value: int
    baseline_source: F1BaselineSource
    baseline_native: int | None
    candidate_native: int | None


def observe_parsed_cc_half(
    *,
    track_index: int | None,
    current_native: int | None,
    pending_native: int | None,
    control: int,
    value: int,
) -> AnalogFourF1CcObservation:
    """Prefer caller-supplied pending state; incomplete context stays partial."""
    _require_f1_cc(control, value)
    if track_index is not None:
        _require_f1_value(track_index, A4_KIT_SYNTH_TRACK_COUNT - 1, "resolved track index")
    for sample in (current_native, pending_native):
        if sample is not None:
            _require_f1_value(sample, A4_F1_NATIVE_MAX, "baseline")
    baseline = pending_native if pending_native is not None else current_native
    source = A4_F1_BASELINE_UNKNOWN
    if pending_native is not None:
        source = A4_F1_BASELINE_PENDING
    elif current_native is not None:
        source = A4_F1_BASELINE_CURRENT
    candidate = None
    if track_index is not None and baseline is not None:
        candidate = apply_parsed_cc_half(baseline, control, value)
    return AnalogFourF1CcObservation(track_index, control, value, source, baseline, candidate)


class NrpnObservationStatus(Enum):
    ADDRESS_SELECTED = auto()
    OUTSIDE_SCOPE = auto()
    UNKNOWN_CONTEXT = auto()
    PARTIAL = auto()
    NULL_ADDRESS = auto()
    DISPATCH_OBSERVED = auto()


@dataclass(frozen=True)
class AnalogFourF1NrpnDispatch:
    """An observed submission, not fresh/atomic/applied device state."""

    track_index: int
    parameter14: int
    value14: int
    candidate_native: int | None


@dataclass(frozen=True)
class AnalogFourF1NrpnRow:
    """One caller-scoped row; native initialization leaves data halves unknown."""

    track_index: int | None = None
    parameter_msb: int | None = A4_F1_NRPN_NULL_ADDRESS_HALF
    parameter_lsb: int | None = A4_F1_NRPN_NULL_ADDRESS_HALF
    value_msb: int | None = None
    value_lsb: int | None = None

    def __post_init__(self) -> None:
        if self.track_index is not None:
            _require_f1_value(
                self.track_index, A4_KIT_SYNTH_TRACK_COUNT - 1, "resolved track index"
            )
        for half in (self.parameter_msb, self.parameter_lsb, self.value_msb, self.value_lsb):
            if half is not None:
                _require_f1_value(half, A4_F1_DATA_BYTE_MAX, "cached half")

    def receive(self, control: int, value: int) -> AnalogFourF1NrpnTransition:
        """99/98 clear both data halves; 6/38 dispatch independently; 121 is inert."""
        _require_f1_value(control, A4_F1_DATA_BYTE_MAX, "control")
        _require_f1_value(value, A4_F1_DATA_BYTE_MAX, "value")
        if control == ANALOG_FOUR_NRPN_PARAMETER_MSB_CC:
            row = replace(self, parameter_msb=value, value_msb=0, value_lsb=0)
            return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.ADDRESS_SELECTED)
        if control == ANALOG_FOUR_NRPN_PARAMETER_LSB_CC:
            row = replace(self, parameter_lsb=value, value_msb=0, value_lsb=0)
            return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.ADDRESS_SELECTED)
        if control == ANALOG_FOUR_NRPN_DATA_MSB_CC:
            row = replace(self, value_msb=value)
        elif control == A4_F1_NRPN_DATA_LSB_CC:
            row = replace(self, value_lsb=value)
        else:
            return AnalogFourF1NrpnTransition(self, None, NrpnObservationStatus.OUTSIDE_SCOPE)
        return _observe_nrpn_dispatch(row)


@dataclass(frozen=True)
class AnalogFourF1NrpnTransition:
    row: AnalogFourF1NrpnRow
    dispatch: AnalogFourF1NrpnDispatch | None
    status: NrpnObservationStatus


def _observe_nrpn_dispatch(row: AnalogFourF1NrpnRow) -> AnalogFourF1NrpnTransition:
    if row.track_index is None:
        return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.UNKNOWN_CONTEXT)
    if None in (row.parameter_msb, row.parameter_lsb):
        return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.PARTIAL)
    if A4_F1_NRPN_NULL_ADDRESS_HALF in (row.parameter_msb, row.parameter_lsb):
        return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.NULL_ADDRESS)
    if None in (row.value_msb, row.value_lsb):
        return AnalogFourF1NrpnTransition(row, None, NrpnObservationStatus.PARTIAL)
    parameter14 = join_parsed_bytes(
        require_int(row.parameter_msb, "parameter msb"),
        require_int(row.parameter_lsb, "parameter lsb"),
    )
    value14 = join_parsed_bytes(
        require_int(row.value_msb, "value msb"), require_int(row.value_lsb, "value lsb")
    )
    candidate = None
    if (row.parameter_msb, row.parameter_lsb) == (
        A4_F1_MAPPING.nrpn_msb,
        A4_F1_MAPPING.nrpn_lsb,
    ):
        candidate = parsed_wire14_to_native(value14)
    dispatch = AnalogFourF1NrpnDispatch(row.track_index, parameter14, value14, candidate)
    return AnalogFourF1NrpnTransition(row, dispatch, NrpnObservationStatus.DISPATCH_OBSERVED)
