"""Pure Rytm LFO Depth value-stage helpers from its own static evidence.

Screen text is signed truncation, not the existing mathematical mod-depth
value and not an inverse native identifier. Parsed inputs propose values only:
no parser, call resolver, queue, commit, frame codec or MIDI I/O is implemented.
"""

from __future__ import annotations

from dataclasses import dataclass

from ...data.rytm_lfo_depth_contract import RYTM_LFO_DEPTH_CONTRACT as _CONTRACT


@dataclass(frozen=True)
class RytmLfoDepthObservation:
    """Inclusive possible source words from one scoped outgoing value.

    Bounds are deliberately not an exact native scalar. They prove neither
    current-state availability/coherence nor commit or installed firmware.
    Combining partial events requires separate binding/order evidence.
    """

    native_min: int
    native_max: int


def _integer(value: int, maximum: int, name: str) -> int:
    if type(value) is not int:
        raise TypeError(f"{name} must be an integer, not bool")
    if not _CONTRACT.native_min <= value <= maximum:
        raise ValueError(f"{name} outside 0..{maximum}")
    return value


def rytm_lfo_depth_native_to_screen(native: int) -> str:
    """Forward device label; retain exact center and signed near-zero text."""

    delta = _integer(native, _CONTRACT.native_max, "native") - _CONTRACT.native_center
    if delta == 0:
        return "(0)"
    hundredths = abs(delta) * _CONTRACT.decimal_scale // _CONTRACT.units_per_whole
    sign = "-" if delta < 0 else "+"
    return (
        f"{sign}{hundredths // _CONTRACT.decimal_scale}.{hundredths % _CONTRACT.decimal_scale:02d}"
    )


def rytm_lfo_depth_native_to_nrpn14(native: int) -> int:
    """Inert outgoing value; odd native words lose bit 0."""

    return _integer(native, _CONTRACT.native_max, "native") >> _CONTRACT.fine_shift


def rytm_lfo_depth_parsed_nrpn14_to_native(value: int) -> int:
    """Propose an even word from an already parsed value, not a raw NRPN row."""

    return _integer(value, _CONTRACT.nrpn_value_max, "NRPN value") << _CONTRACT.fine_shift


def rytm_lfo_depth_cc_proposal(
    control: int, value: int, *, current_or_pending: int | None = None
) -> int:
    """Propose a word: coarse resets all low bits; fine needs a valid baseline.

    A baseline must come from an independently available current/pending source,
    not an unavailable getter's zero fallback. Coarse needs no baseline read.
    Sequentially feeding proposals models arithmetic order, not queue commits.
    """

    control = _integer(control, _CONTRACT.cc_value_max, "control")
    value = _integer(value, _CONTRACT.cc_value_max, "CC value")
    if control == _CONTRACT.midi_mapping.cc_msb:
        return value << _CONTRACT.coarse_shift
    if control != _CONTRACT.midi_mapping.cc_lsb:
        raise ValueError("control is not an LFO Depth coarse/fine CC")
    if current_or_pending is None:
        raise ValueError("fine CC requires an available current/pending baseline")
    baseline = _integer(current_or_pending, _CONTRACT.native_max, "baseline")
    return (baseline & _CONTRACT.high_byte_mask) | (value << _CONTRACT.fine_shift)


def rytm_lfo_depth_stock_cc_notification(native: int, channel: int) -> tuple[int, int, int]:
    """Inert bytes for notifier 0x400a60ac with this coarse mapping present.

    Only CC109 is emitted in this selected path. This says nothing about fine
    CC118 output by other, unsearched producers or actual hardware delivery.
    """

    native = _integer(native, _CONTRACT.native_max, "native")
    channel = _integer(channel, _CONTRACT.channel_max, "channel")
    return (
        _CONTRACT.cc_status | channel,
        _CONTRACT.midi_mapping.cc_msb,
        native >> _CONTRACT.coarse_shift,
    )


def decode_rytm_lfo_depth_coupled_word(word: bytes) -> int:
    """Strict two-byte big-endian word at coupled Sound+0x6c, not a frame."""

    if type(word) is not bytes or len(word) != _CONTRACT.word_size:
        raise ValueError("exactly two stored bytes required")
    return _integer(int.from_bytes(word, "big"), _CONTRACT.native_max, "stored native word")


def observe_rytm_lfo_depth_stock_cc(value: int) -> RytmLfoDepthObservation:
    """Possible words before coarse-only output, not an incoming CC proposal."""

    value = _integer(value, _CONTRACT.cc_value_max, "CC value")
    return RytmLfoDepthObservation(
        native_min=value << _CONTRACT.coarse_shift,
        native_max=((value + 1) << _CONTRACT.coarse_shift) - 1,
    )


def observe_rytm_lfo_depth_outgoing_nrpn14(value: int) -> RytmLfoDepthObservation:
    """Two possible pre-output native words, not the receiver's even proposal."""

    native_min = rytm_lfo_depth_parsed_nrpn14_to_native(value)
    return RytmLfoDepthObservation(native_min=native_min, native_max=native_min + 1)


__all__ = (
    "RytmLfoDepthObservation",
    "decode_rytm_lfo_depth_coupled_word",
    "observe_rytm_lfo_depth_outgoing_nrpn14",
    "observe_rytm_lfo_depth_stock_cc",
    "rytm_lfo_depth_cc_proposal",
    "rytm_lfo_depth_native_to_nrpn14",
    "rytm_lfo_depth_native_to_screen",
    "rytm_lfo_depth_parsed_nrpn14_to_native",
    "rytm_lfo_depth_stock_cc_notification",
)
