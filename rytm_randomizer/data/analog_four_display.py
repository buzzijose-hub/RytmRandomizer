"""Analog Four MKII front-panel display metadata.

This module layers operator-facing screen values on top of the manual-backed
CC/NRPN facts in :mod:`rytm_randomizer.data.analog_four_midi`. It is passive
data only: no MIDI ports are opened, no messages are sent, and no hardware
state is touched.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_NRPN, AnalogFourCcMapping

A4_SIGNED_SCREEN_MIN: Final[int] = -64
A4_SIGNED_SCREEN_MAX: Final[int] = 63
A4_MIDI_MIN: Final[int] = 0
A4_MIDI_MAX: Final[int] = 127
A4_SIGNED_SCREEN_CENTER: Final[int] = 64

DISPLAY_SCALE_UNIPOLAR: Final[str] = "unipolar"
DISPLAY_SCALE_BIPOLAR: Final[str] = "bipolar"
DISPLAY_SCALE_ENUM: Final[str] = "enum"

TRANSPORT_CC_READY: Final[str] = "cc-ready"
TRANSPORT_NRPN_READY: Final[str] = "nrpn-ready"
TRANSPORT_SCREEN_ONLY_NRPN: Final[str] = "screen-only-nrpn"
TRANSPORT_SCREEN_ONLY: Final[str] = "screen-only"


@dataclass(frozen=True)
class AnalogFourDisplaySpec:
    """Front-panel scale metadata for one Analog Four parameter."""

    display_scale: str
    value_labels: Mapping[int, str] = MappingProxyType({})
    center_label: str | None = None
    transport_ready: bool = True
    value_note: str = ""

    def label_for_value(self, value: int) -> str:
        """Return the front-panel label for ``value`` when one is known."""

        label = self.value_labels.get(value)
        if label is not None:
            return label
        return str(value)

    def value_for_label(self, label: str) -> int | None:
        """Return a MIDI/NRPN value for ``label`` if this spec knows it."""

        normalized = label.casefold()
        for value, candidate in self.value_labels.items():
            if candidate.casefold() == normalized:
                return value
        return None


@dataclass(frozen=True)
class AnalogFourPatchValue:
    """One parameter value in both A4 screen and transport language."""

    parameter: str
    section: str
    encoder: str
    screen_value: str
    midi_value: int | None
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_address: tuple[int, int] | None
    transport_status: str
    dial_direction: str


def _labels(labels: Mapping[int, str]) -> Mapping[int, str]:
    return MappingProxyType(dict(labels))


_FILTER2_TYPE_LABELS: Final[Mapping[int, str]] = _labels(
    {
        0: "LP2",
        1: "LP1",
        2: "BP",
        3: "HP1",
        4: "HP2",
        5: "BS",
        6: "PK",
    }
)
_ENV_SHAPE_LABELS: Final[Mapping[int, str]] = _labels(
    {
        0: "triangle",
        1: "exponential",
        2: "linear",
    }
)
_GATE_LENGTH_LABELS: Final[Mapping[int, str]] = _labels({0: "NOTE"})
_LFO_MODE_LABELS: Final[Mapping[int, str]] = _labels({0: "TRG", 1: "HLD", 2: "ONE"})
_LFO_WAVEFORM_LABELS: Final[Mapping[int, str]] = _labels(
    {
        0: "triangle",
        1: "sine",
        2: "square",
        3: "saw",
        4: "exp",
        5: "random",
    }
)
_LFO_MULTIPLIER_LABELS: Final[Mapping[int, str]] = _labels({64: "x1"})
_OFF_ONLY_LABELS: Final[Mapping[int, str]] = _labels({0: "OFF"})

_BIPOLAR_PARAMETERS: Final[frozenset[str]] = frozenset(
    {
        "OSC1 Pulsewidth",
        "OSC1 PWM Speed",
        "OSC1 PWM Depth",
        "OSC2 Pulsewidth",
        "OSC2 PWM Speed",
        "OSC2 PWM Depth",
        "Bend Amount",
        "Vibrato Depth",
        "Filter Overdrive",
        "Filter1 Envelope Amount",
        "Filter2 Envelope Amount",
        "Pan",
        "EnvF Depth A",
        "EnvF Depth B",
        "Env2 Depth A",
        "Env2 Depth B",
        "LFO1 Speed",
        "LFO1 Depth A",
        "LFO1 Depth B",
        "LFO2 Speed",
        "LFO2 Depth A",
        "LFO2 Depth B",
    }
)

_EXPLICIT_DISPLAY_SPECS: Final[Mapping[str, AnalogFourDisplaySpec]] = MappingProxyType(
    {
        "Filter2 Type": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_FILTER2_TYPE_LABELS,
            value_note="Filter 2 shape; HP2 is the classic 12 dB high-pass option.",
        ),
        "EnvA Env Shape": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_ENV_SHAPE_LABELS,
            value_note="Amp envelope curve shape.",
        ),
        "EnvF Env Shape": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_ENV_SHAPE_LABELS,
            value_note="Filter envelope curve shape.",
        ),
        "EnvF Gate Length": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_GATE_LENGTH_LABELS,
            transport_ready=False,
            value_note="Front-panel gate-length label; ordinal capture remains pending.",
        ),
        "EnvF Destination A": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
            value_note="Destination labels are front-panel safe until full ordinal capture.",
        ),
        "EnvF Destination B": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
            value_note="Destination labels are front-panel safe until full ordinal capture.",
        ),
        "LFO1 Speed Multiplier": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_MULTIPLIER_LABELS,
            value_note="Multiplier row uses the neutral x1 screen target.",
        ),
        "LFO1 Mode": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_MODE_LABELS,
            value_note="LFO trigger/playback mode.",
        ),
        "LFO1 Waveform": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_WAVEFORM_LABELS,
            value_note="LFO waveform shape.",
        ),
        "LFO1 Destination A": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
            value_note="Destination labels are front-panel safe until full ordinal capture.",
        ),
        "LFO1 Destination B": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
            value_note="Destination labels are front-panel safe until full ordinal capture.",
        ),
        "LFO2 Speed Multiplier": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_MULTIPLIER_LABELS,
        ),
        "LFO2 Mode": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_MODE_LABELS,
        ),
        "LFO2 Waveform": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_LFO_WAVEFORM_LABELS,
        ),
        "LFO2 Destination A": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
        ),
        "LFO2 Destination B": AnalogFourDisplaySpec(
            DISPLAY_SCALE_ENUM,
            value_labels=_OFF_ONLY_LABELS,
            transport_ready=False,
        ),
    }
)


def _default_spec_for(parameter: str) -> AnalogFourDisplaySpec:
    if parameter in _BIPOLAR_PARAMETERS:
        center_label = "OFF/0" if parameter == "Filter Overdrive" else None
        return AnalogFourDisplaySpec(DISPLAY_SCALE_BIPOLAR, center_label=center_label)
    return AnalogFourDisplaySpec(DISPLAY_SCALE_UNIPOLAR)


ANALOG_FOUR_PARAMETER_DISPLAY: Final[Mapping[str, AnalogFourDisplaySpec]] = MappingProxyType(
    {
        parameter: _EXPLICIT_DISPLAY_SPECS.get(parameter, _default_spec_for(parameter))
        for parameter in ANALOG_FOUR_SYNTH_TRACK_NRPN
    }
)


def signed_screen_to_a4_midi(screen_value: int) -> int:
    """Map an A4 ``-64..+63`` screen value to the raw ``0..127`` MIDI value."""

    if screen_value < A4_SIGNED_SCREEN_MIN or screen_value > A4_SIGNED_SCREEN_MAX:
        raise ValueError("screen value must be in -64..63 for Analog Four bipolar parameters")
    return screen_value + A4_SIGNED_SCREEN_CENTER


def midi_to_a4_signed_screen(midi_value: int) -> int:
    """Map a raw A4 MIDI value to its ``-64..+63`` front-panel value."""

    _validate_midi_value(midi_value)
    return midi_value - A4_SIGNED_SCREEN_CENTER


def make_a4_patch_value(
    parameter: str,
    *,
    screen_target: int | str,
    transport_value: int | None = None,
) -> AnalogFourPatchValue:
    """Return screen + CC/NRPN metadata for an Analog Four patch target."""

    mapping = _mapping_for(parameter)
    spec = ANALOG_FOUR_PARAMETER_DISPLAY[parameter]
    screen_value, midi_value = _screen_and_midi_value(
        screen_target,
        spec=spec,
        transport_value=transport_value,
    )
    transport_status = _transport_status(mapping, midi_value)
    return AnalogFourPatchValue(
        parameter=parameter,
        section=mapping.section,
        encoder=mapping.encoder,
        screen_value=screen_value,
        midi_value=midi_value,
        cc_msb=mapping.cc_msb,
        cc_lsb=mapping.cc_lsb,
        nrpn_address=_nrpn_address(mapping),
        transport_status=transport_status,
        dial_direction=_dial_direction(screen_target, spec=spec, midi_value=midi_value),
    )


def _mapping_for(parameter: str) -> AnalogFourCcMapping:
    mapping = ANALOG_FOUR_SYNTH_TRACK_NRPN.get(parameter)
    if mapping is None:
        raise KeyError(f"Unknown Analog Four parameter: {parameter}")
    return mapping


def _screen_and_midi_value(
    screen_target: int | str,
    *,
    spec: AnalogFourDisplaySpec,
    transport_value: int | None,
) -> tuple[str, int | None]:
    if isinstance(screen_target, int):
        if spec.display_scale == DISPLAY_SCALE_BIPOLAR:
            return _format_signed_screen(screen_target, spec), signed_screen_to_a4_midi(
                screen_target
            )
        _validate_midi_value(screen_target)
        return spec.label_for_value(screen_target), screen_target

    if not isinstance(screen_target, str):
        raise TypeError("screen_target must be an int or str")

    if transport_value is not None:
        _validate_midi_value(transport_value)
        return screen_target, transport_value
    label_value = spec.value_for_label(screen_target)
    if label_value is None or not spec.transport_ready:
        return screen_target, None
    _validate_midi_value(label_value)
    return screen_target, label_value


def _format_signed_screen(value: int, spec: AnalogFourDisplaySpec) -> str:
    if value == 0 and spec.center_label is not None:
        return spec.center_label
    if value > 0:
        return f"+{value}"
    return str(value)


def _validate_midi_value(value: int) -> None:
    if value < A4_MIDI_MIN or value > A4_MIDI_MAX:
        raise ValueError("MIDI value must be in 0..127")


def _nrpn_address(mapping: AnalogFourCcMapping) -> tuple[int, int] | None:
    if mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
        return None
    return (mapping.nrpn_msb, mapping.nrpn_lsb)


def _transport_status(mapping: AnalogFourCcMapping, midi_value: int | None) -> str:
    if mapping.cc_msb is not None and midi_value is not None:
        return TRANSPORT_CC_READY
    if _nrpn_address(mapping) is not None and midi_value is not None:
        return TRANSPORT_NRPN_READY
    if _nrpn_address(mapping) is not None:
        return TRANSPORT_SCREEN_ONLY_NRPN
    return TRANSPORT_SCREEN_ONLY


def _dial_direction(
    screen_target: int | str,
    *,
    spec: AnalogFourDisplaySpec,
    midi_value: int | None,
) -> str:
    if isinstance(screen_target, str):
        return f"select {screen_target}"
    if spec.display_scale == DISPLAY_SCALE_BIPOLAR:
        center = "OFF/0" if spec.center_label is not None else "0"
        if screen_target > 0:
            return f"turn right from {center}"
        if screen_target < 0:
            return f"turn left from {center}"
        return f"leave at {center}"
    if midi_value is None:
        return f"set to {screen_target}"
    return f"set to {midi_value}"


__all__ = [
    "A4_MIDI_MAX",
    "A4_MIDI_MIN",
    "A4_SIGNED_SCREEN_CENTER",
    "A4_SIGNED_SCREEN_MAX",
    "A4_SIGNED_SCREEN_MIN",
    "ANALOG_FOUR_PARAMETER_DISPLAY",
    "DISPLAY_SCALE_BIPOLAR",
    "DISPLAY_SCALE_ENUM",
    "DISPLAY_SCALE_UNIPOLAR",
    "TRANSPORT_CC_READY",
    "TRANSPORT_NRPN_READY",
    "TRANSPORT_SCREEN_ONLY",
    "TRANSPORT_SCREEN_ONLY_NRPN",
    "AnalogFourDisplaySpec",
    "AnalogFourPatchValue",
    "make_a4_patch_value",
    "midi_to_a4_signed_screen",
    "signed_screen_to_a4_midi",
]
