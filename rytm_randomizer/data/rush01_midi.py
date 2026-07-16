"""Ordered semantic bindings for the RUSH01 device-assisted MIDI compiler."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal, TypeAlias

Rush01ConversionKind: TypeAlias = Literal[
    "direct_7bit",
    "bipolar_7bit",
    "verified_enum",
    "unverified_enum",
    "unverified_boolean",
    "unverified_high_resolution",
    "unverified_conversion",
    "unmapped",
]


@dataclass(frozen=True)
class Rush01RytmCommonBinding:
    """One fixed Rytm YAML key to manual-catalog parameter binding."""

    spec_key: str
    section: str
    parameter: str


@dataclass(frozen=True)
class Rush01A4Binding:
    """One ordered A4 semantic field and its verified conversion policy."""

    section_key: str
    field_key: str
    parameter: str | None
    conversion: Rush01ConversionKind


RUSH01_RYTM_TRACK_ORDER: Final[tuple[str, ...]] = (
    "BD",
    "SD",
    "RS",
    "CP",
    "BT",
    "LT",
    "MT",
    "HT",
    "CH",
    "OH",
    "CY",
    "CB",
)

RUSH01_A4_TRACK_ORDER: Final[tuple[str, ...]] = ("T1", "T2", "T3", "T4")

RUSH01_RYTM_FILTER_BINDINGS: Final[tuple[Rush01RytmCommonBinding, ...]] = (
    Rush01RytmCommonBinding("ATK", "FILTER", "Filter Attack Time"),
    Rush01RytmCommonBinding("DEC", "FILTER", "Filter Decay Time"),
    Rush01RytmCommonBinding("SUS", "FILTER", "Filter Sustain Level"),
    Rush01RytmCommonBinding("REL", "FILTER", "Filter Release Time"),
    Rush01RytmCommonBinding("FRQ", "FILTER", "Filter Frequency"),
    Rush01RytmCommonBinding("RES", "FILTER", "Filter Resonance"),
    Rush01RytmCommonBinding("TYPE", "FILTER", "Filter Mode"),
    Rush01RytmCommonBinding("ENV", "FILTER", "Filter Env Depth"),
)

RUSH01_RYTM_AMP_BINDINGS: Final[tuple[Rush01RytmCommonBinding, ...]] = (
    Rush01RytmCommonBinding("ATK", "AMP", "Amp Attack Time"),
    Rush01RytmCommonBinding("HLD", "AMP", "Amp Hold Time"),
    Rush01RytmCommonBinding("DEC", "AMP", "Amp Decay Time"),
    Rush01RytmCommonBinding("OVR", "AMP", "Amp Overdrive"),
    Rush01RytmCommonBinding("DEL", "AMP", "Amp Delay Send"),
    Rush01RytmCommonBinding("REV", "AMP", "Amp Reverb Send"),
    Rush01RytmCommonBinding("PAN", "AMP", "Amp Pan"),
    Rush01RytmCommonBinding("VOL", "AMP", "Amp Volume"),
)

RUSH01_A4_BINDINGS: Final[tuple[Rush01A4Binding, ...]] = (
    Rush01A4Binding(
        "oscillator_1", "coarse_tune_semitones", "OSC1 Pitch", "unverified_high_resolution"
    ),
    Rush01A4Binding("oscillator_1", "fine_tune_cents", "OSC1 Pitch", "unverified_high_resolution"),
    Rush01A4Binding("oscillator_1", "linear_detune_hz", "OSC1 Detune", "unverified_conversion"),
    Rush01A4Binding("oscillator_1", "keytrack", "OSC1 Keytracking", "unverified_boolean"),
    Rush01A4Binding("oscillator_1", "level", "OSC1 Level", "direct_7bit"),
    Rush01A4Binding("oscillator_1", "waveform", "OSC1 Waveform", "unverified_enum"),
    Rush01A4Binding("oscillator_1", "sub_oscillator", "OSC1 Sub Oscillator", "unverified_enum"),
    Rush01A4Binding("oscillator_1", "pulse_width", "OSC1 Pulsewidth", "bipolar_7bit"),
    Rush01A4Binding("oscillator_1", "pwm_speed", "OSC1 PWM Speed", "bipolar_7bit"),
    Rush01A4Binding("oscillator_1", "pwm_depth", "OSC1 PWM Depth", "bipolar_7bit"),
    Rush01A4Binding(
        "oscillator_2", "coarse_tune_semitones", "OSC2 Pitch", "unverified_high_resolution"
    ),
    Rush01A4Binding("oscillator_2", "fine_tune_cents", "OSC2 Pitch", "unverified_high_resolution"),
    Rush01A4Binding("oscillator_2", "linear_detune_hz", "OSC2 Detune", "unverified_conversion"),
    Rush01A4Binding("oscillator_2", "keytrack", "OSC2 Keytracking", "unverified_boolean"),
    Rush01A4Binding("oscillator_2", "level", "OSC2 Level", "direct_7bit"),
    Rush01A4Binding("oscillator_2", "waveform", "OSC2 Waveform", "unverified_enum"),
    Rush01A4Binding("oscillator_2", "sub_oscillator", "OSC2 Sub Oscillator", "unverified_enum"),
    Rush01A4Binding("oscillator_2", "pulse_width", "OSC2 Pulsewidth", "bipolar_7bit"),
    Rush01A4Binding("oscillator_2", "pwm_speed", "OSC2 PWM Speed", "bipolar_7bit"),
    Rush01A4Binding("oscillator_2", "pwm_depth", "OSC2 PWM Depth", "bipolar_7bit"),
    Rush01A4Binding("oscillator_common", "osc1_am", "OSC1 AM", "unverified_boolean"),
    Rush01A4Binding("oscillator_common", "sync_mode", "Sync Mode", "unverified_enum"),
    Rush01A4Binding("oscillator_common", "sync_amount", "Sync Amount", "direct_7bit"),
    Rush01A4Binding("oscillator_common", "bend_depth", "Bend Amount", "bipolar_7bit"),
    Rush01A4Binding("oscillator_common", "note_slide_time", "Slide Time", "direct_7bit"),
    Rush01A4Binding("oscillator_common", "osc2_am", "OSC2 AM", "unverified_boolean"),
    Rush01A4Binding("oscillator_common", "oscillator_retrigger", "Note Sync", "unverified_boolean"),
    Rush01A4Binding("oscillator_common", "vibrato_fade", "Vibrato Fade", "direct_7bit"),
    Rush01A4Binding("oscillator_common", "vibrato_speed", "Vibrato Speed", "direct_7bit"),
    Rush01A4Binding("oscillator_common", "vibrato_depth", "Vibrato Depth", "bipolar_7bit"),
    Rush01A4Binding("noise", "sample_and_hold", "Noise S&H", "direct_7bit"),
    Rush01A4Binding("noise", "color", None, "unmapped"),
    Rush01A4Binding("noise", "fade", "Noise Fade", "direct_7bit"),
    Rush01A4Binding("noise", "level", "Noise Level", "direct_7bit"),
    Rush01A4Binding("filter_1", "frequency", "Filter1 Frequency", "unverified_high_resolution"),
    Rush01A4Binding("filter_1", "resonance", "Filter1 Resonance", "direct_7bit"),
    Rush01A4Binding("filter_1", "overdrive", "Filter Overdrive", "bipolar_7bit"),
    Rush01A4Binding("filter_1", "keytrack", "Filter1 Keytracking", "direct_7bit"),
    Rush01A4Binding("filter_1", "envelope_depth", "Filter1 Envelope Amount", "bipolar_7bit"),
    Rush01A4Binding("filter_2", "frequency", "Filter2 Frequency", "unverified_high_resolution"),
    Rush01A4Binding("filter_2", "resonance", "Filter2 Resonance", "direct_7bit"),
    Rush01A4Binding("filter_2", "type", "Filter2 Type", "verified_enum"),
    Rush01A4Binding("filter_2", "keytrack", "Filter2 Keytracking", "direct_7bit"),
    Rush01A4Binding("filter_2", "envelope_depth", "Filter2 Envelope Amount", "bipolar_7bit"),
    Rush01A4Binding("amp", "attack", "EnvA Attack Time", "direct_7bit"),
    Rush01A4Binding("amp", "decay", "EnvA Decay Time", "direct_7bit"),
    Rush01A4Binding("amp", "sustain", "EnvA Sustain Level", "direct_7bit"),
    Rush01A4Binding("amp", "release", "EnvA Release Time", "direct_7bit"),
    Rush01A4Binding("amp", "envelope_shape", "EnvA Env Shape", "verified_enum"),
    Rush01A4Binding("amp", "chorus_send", "Chorus Send Level", "direct_7bit"),
    Rush01A4Binding("amp", "delay_send", "Delay Send Level", "direct_7bit"),
    Rush01A4Binding("amp", "reverb_send", "Reverb Send Level", "direct_7bit"),
    Rush01A4Binding("amp", "pan", "Pan", "bipolar_7bit"),
    Rush01A4Binding("amp", "volume", "Volume", "direct_7bit"),
    Rush01A4Binding("filter_envelope", "attack", "EnvF Attack Time", "direct_7bit"),
    Rush01A4Binding("filter_envelope", "decay", "EnvF Decay Time", "direct_7bit"),
    Rush01A4Binding("filter_envelope", "sustain", "EnvF Sustain Level", "direct_7bit"),
    Rush01A4Binding("filter_envelope", "release", "EnvF Release Time", "direct_7bit"),
    Rush01A4Binding("filter_envelope", "envelope_shape", "EnvF Env Shape", "verified_enum"),
    Rush01A4Binding("filter_envelope", "gate_length", "EnvF Gate Length", "verified_enum"),
)

__all__ = [
    "RUSH01_A4_BINDINGS",
    "RUSH01_A4_TRACK_ORDER",
    "RUSH01_RYTM_AMP_BINDINGS",
    "RUSH01_RYTM_FILTER_BINDINGS",
    "RUSH01_RYTM_TRACK_ORDER",
    "Rush01A4Binding",
    "Rush01ConversionKind",
    "Rush01RytmCommonBinding",
]
