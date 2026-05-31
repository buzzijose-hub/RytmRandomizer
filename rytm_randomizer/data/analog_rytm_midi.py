"""Manual-backed Analog Rytm MKII OS 1.72 MIDI CC facts."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from .rytm_machine_catalog import RYTM_MACHINE_PROFILES, RYTM_PAD_CAPABILITIES

RiskTier: TypeAlias = Literal["low", "medium", "high"]
MutationStatus: TypeAlias = Literal[
    "validated_runtime", "documented_only", "locked_default", "forbidden"
]
ParameterValueKind: TypeAlias = Literal["continuous", "selector"]
ParameterValueOrientation: TypeAlias = Literal["zero_based", "centered"]


@dataclass(frozen=True)
class AnalogRytmCcMapping:
    """One manual-backed CC/NRPN mapping row for the Analog Rytm MKII."""

    section: str
    parameter: str
    cc_msb: int
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None
    scope: str
    risk: RiskTier
    mutation_status: MutationStatus
    value_min: int = 0
    value_max: int = 127
    value_kind: ParameterValueKind = "continuous"
    value_orientation: ParameterValueOrientation = "zero_based"
    machine_key: str | None = None


@dataclass(frozen=True)
class AnalogRytmNoteTrigger:
    """One MIDI note trigger row from the Analog Rytm MKII manual."""

    note: str
    midi_note: int
    function: str
    cc_msb: None = None


@dataclass(frozen=True)
class AnalogRytmCatalogSummary:
    """Small immutable summary of the passive Rytm MIDI catalog."""

    general_cc_count: int
    machine_src_cc_count: int
    total_cc_count: int
    validated_runtime_count: int
    locked_default_count: int
    documented_only_count: int
    forbidden_count: int
    machine_profile_count: int
    machine_profiles_with_src_count: int
    note_trigger_count: int
    pad_count: int


_VALIDATED_RUNTIME_MACHINE_KEYS: Final[frozenset[str]] = frozenset(
    {
        "bd_hard",
        "bd_classic",
        "bd_fm",
        "bd_plastic",
        "bd_silky",
        "bd_sharp",
        "bd_acoustic",
        "sd_hard",
        "sd_classic",
        "sd_fm",
        "sy_raw",
    }
)

_VALIDATED_RUNTIME_GENERAL_ROWS: Final[frozenset[tuple[str, str]]] = frozenset(
    {
        ("FILTER", "Filter Attack Time"),
        ("FILTER", "Filter Decay Time"),
        ("FILTER", "Filter Sustain Level"),
        ("FILTER", "Filter Release Time"),
        ("FILTER", "Filter Frequency"),
        ("FILTER", "Filter Resonance"),
        ("FILTER", "Filter Mode"),
        ("FILTER", "Filter Env Depth"),
        ("AMP", "Amp Attack Time"),
        ("AMP", "Amp Hold Time"),
        ("AMP", "Amp Decay Time"),
        ("AMP", "Amp Overdrive"),
        ("AMP", "Amp Delay Send"),
        ("AMP", "Amp Reverb Send"),
        ("AMP", "Amp Pan"),
        ("LFO", "LFO Speed"),
        ("LFO", "LFO Multiplier"),
        ("LFO", "LFO Fade In/Out"),
        ("LFO", "LFO Waveform"),
        ("LFO", "LFO Start Phase"),
        ("LFO", "LFO Trig Mode"),
        ("LFO", "LFO Depth"),
    }
)

_LOCKED_PARAMETER_NAMES: Final[frozenset[str]] = frozenset(
    {
        "Active Scene",
        "Amp Volume",
        "Compressor Output Volume",
        "Delay Feedback",
        "Delay Mix Volume",
        "LFO Destination",
        "Level",
        "Performance Parameter 1",
        "Performance Parameter 2",
        "Performance Parameter 3",
        "Performance Parameter 4",
        "Performance Parameter 5",
        "Performance Parameter 6",
        "Performance Parameter 7",
        "Performance Parameter 8",
        "Performance Parameter 9",
        "Performance Parameter 10",
        "Performance Parameter 11",
        "Performance Parameter 12",
        "Reverb Mix Volume",
        "Sample Level",
        "Sample Slot",
        "Track Level",
        "Track Machine Type",
        "Track Mute (seq. mute)",
        "Track Solo (seq. mute)",
    }
)

_MEDIUM_RISK_TOKENS: Final[tuple[str, ...]] = (
    "Balance",
    "Bend",
    "Bit Reduction",
    "Color",
    "Decay",
    "Delay",
    "Depth",
    "Detune",
    "Dist",
    "FM",
    "Feedback",
    "Filter Mode",
    "Highpass",
    "Hold",
    "Loop",
    "Lowpass",
    "Multiplier",
    "Offset",
    "Overdrive",
    "Pan",
    "Pingpong",
    "Ratio",
    "Resonance",
    "Reverb",
    "Sample",
    "Slot",
    "Start",
    "Sweep",
    "Tune",
    "Waveform",
)

_FORBIDDEN_POLICY_NAMES: Final[tuple[str, ...]] = (
    "transport",
    "clock",
    "program change",
    "pattern change",
    "project write",
    "kit save",
    "kit clear",
    "factory reset",
    "calibration",
    "unvalidated sysex write",
)

_GeneralRow: TypeAlias = tuple[str, str, int, int | None, int | None, int | None, str]
_MachineRow: TypeAlias = tuple[str, int]
_ValueMetadataRow: TypeAlias = tuple[
    int,
    int,
    ParameterValueKind,
    ParameterValueOrientation,
]

_DEFAULT_VALUE_METADATA: Final[_ValueMetadataRow] = (
    0,
    127,
    "continuous",
    "zero_based",
)
_VALUE_METADATA_BY_SECTION_AND_PARAMETER: Final[Mapping[tuple[str, str], _ValueMetadataRow]] = (
    MappingProxyType(
        {
            ("COMMON", "Track Machine Type"): (1, 33, "selector", "zero_based"),
            ("FILTER", "Filter Mode"): (0, 6, "selector", "zero_based"),
            ("FILTER", "Filter Env Depth"): (0, 127, "continuous", "centered"),
            ("AMP", "Amp Pan"): (0, 127, "continuous", "centered"),
            ("LFO", "LFO Multiplier"): (0, 23, "selector", "zero_based"),
            ("LFO", "LFO Waveform"): (0, 6, "selector", "zero_based"),
            ("LFO", "LFO Trig Mode"): (0, 4, "selector", "zero_based"),
            ("LFO", "LFO Depth"): (0, 127, "continuous", "centered"),
            ("bd_hard", "Waveform"): (0, 2, "selector", "zero_based"),
            ("bd_classic", "Waveform"): (0, 2, "selector", "zero_based"),
            ("bd_sharp", "Waveform"): (0, 11, "selector", "zero_based"),
            ("bd_acoustic", "Waveform"): (0, 11, "selector", "zero_based"),
            ("dual_vco", "Osc Config"): (0, 79, "selector", "zero_based"),
            ("sy_raw", "Tune"): (0, 127, "continuous", "centered"),
            ("sy_raw", "Osc 2 Detune"): (40, 88, "continuous", "centered"),
            ("sy_raw", "Waveform 1"): (0, 6, "selector", "zero_based"),
            ("sy_raw", "Waveform 2"): (0, 1, "selector", "zero_based"),
            ("sy_raw", "Balance"): (0, 127, "continuous", "centered"),
            ("bt_classic", "Snap Type"): (0, 3, "selector", "zero_based"),
            ("cy_ride", "Cymbal Type"): (0, 3, "selector", "zero_based"),
            ("hh_basic", "Osc Reset"): (0, 1, "selector", "zero_based"),
        }
    )
)

_GENERAL_CC_ROWS: Final[tuple[_GeneralRow, ...]] = (
    ("TRIG PARAMETERS", "Note", 3, None, 3, 0, "trig"),
    ("TRIG PARAMETERS", "Velocity", 4, None, 3, 1, "trig"),
    ("TRIG PARAMETERS", "Length", 5, None, 3, 2, "trig"),
    ("TRIG PARAMETERS", "Synth Trig", 11, None, 3, 3, "trig"),
    ("TRIG PARAMETERS", "Sample Trig", 12, None, 3, 4, "trig"),
    ("TRIG PARAMETERS", "ENV Trig", 13, None, 3, 5, "trig"),
    ("TRIG PARAMETERS", "LFO TRIG", 14, None, 3, 6, "trig"),
    ("EUCLIDEAN", "Pulse Generator 1", 86, None, 3, 8, "sequencer"),
    ("EUCLIDEAN", "Pulse Generator 2", 87, None, 3, 9, "sequencer"),
    ("EUCLIDEAN", "Euclidean on/off", 117, None, 3, 14, "sequencer"),
    ("EUCLIDEAN", "Rotation Generator 1", 89, None, 3, 11, "sequencer"),
    ("EUCLIDEAN", "Rotation Generator 2", 90, None, 3, 12, "sequencer"),
    ("EUCLIDEAN", "Track Rotation", 91, None, 3, 13, "sequencer"),
    ("EUCLIDEAN", "Boolean Operator", 88, None, 3, 10, "sequencer"),
    ("COMMON", "Track Level", 95, None, 1, 100, "kit"),
    ("COMMON", "Track Mute (seq. mute)", 94, None, 1, 101, "kit"),
    ("COMMON", "Track Solo (seq. mute)", 93, None, 1, 102, "kit"),
    ("COMMON", "Track Machine Type", 15, None, 1, 103, "machine"),
    ("COMMON", "Active Scene", 92, None, 1, 104, "scene"),
    ("PERFORMANCE", "Performance Parameter 1", 35, None, 0, 0, "performance"),
    ("PERFORMANCE", "Performance Parameter 2", 36, None, 0, 1, "performance"),
    ("PERFORMANCE", "Performance Parameter 3", 37, None, 0, 2, "performance"),
    ("PERFORMANCE", "Performance Parameter 4", 39, None, 0, 3, "performance"),
    ("PERFORMANCE", "Performance Parameter 5", 40, None, 0, 4, "performance"),
    ("PERFORMANCE", "Performance Parameter 6", 41, None, 0, 5, "performance"),
    ("PERFORMANCE", "Performance Parameter 7", 42, None, 0, 6, "performance"),
    ("PERFORMANCE", "Performance Parameter 8", 43, None, 0, 7, "performance"),
    ("PERFORMANCE", "Performance Parameter 9", 44, None, 0, 8, "performance"),
    ("PERFORMANCE", "Performance Parameter 10", 45, None, 0, 9, "performance"),
    ("PERFORMANCE", "Performance Parameter 11", 46, None, 0, 10, "performance"),
    ("PERFORMANCE", "Performance Parameter 12", 47, None, 0, 11, "performance"),
    ("SYNTH", "Synth Parameter 1", 16, None, 1, 0, "src"),
    ("SYNTH", "Synth Parameter 2", 17, None, 1, 1, "src"),
    ("SYNTH", "Synth Parameter 3", 18, None, 1, 2, "src"),
    ("SYNTH", "Synth Parameter 4", 19, None, 1, 3, "src"),
    ("SYNTH", "Synth Parameter 5", 20, None, 1, 4, "src"),
    ("SYNTH", "Synth Parameter 6", 21, None, 1, 5, "src"),
    ("SYNTH", "Synth Parameter 7", 22, None, 1, 6, "src"),
    ("SYNTH", "Synth Parameter 8", 23, None, 1, 7, "src"),
    ("SAMPLE", "Sample Tune", 24, None, 1, 8, "sample"),
    ("SAMPLE", "Sample Fine tune", 25, None, 1, 9, "sample"),
    ("SAMPLE", "Sample Bit Reduction", 26, None, 1, 10, "sample"),
    ("SAMPLE", "Sample Slot", 27, None, 1, 11, "sample"),
    ("SAMPLE", "Sample Start", 28, None, 1, 12, "sample"),
    ("SAMPLE", "Sample End", 29, None, 1, 13, "sample"),
    ("SAMPLE", "Sample Loop", 30, None, 1, 14, "sample"),
    ("SAMPLE", "Sample Level", 31, None, 1, 15, "sample"),
    ("FILTER", "Filter Attack Time", 70, None, 1, 16, "filter"),
    ("FILTER", "Filter Decay Time", 71, None, 1, 17, "filter"),
    ("FILTER", "Filter Sustain Level", 72, None, 1, 18, "filter"),
    ("FILTER", "Filter Release Time", 73, None, 1, 19, "filter"),
    ("FILTER", "Filter Frequency", 74, None, 1, 20, "filter"),
    ("FILTER", "Filter Resonance", 75, None, 1, 21, "filter"),
    ("FILTER", "Filter Mode", 76, None, 1, 22, "filter"),
    ("FILTER", "Filter Env Depth", 77, None, 1, 23, "filter"),
    ("AMP", "Amp Attack Time", 78, None, 1, 24, "amp"),
    ("AMP", "Amp Hold Time", 79, None, 1, 25, "amp"),
    ("AMP", "Amp Decay Time", 80, None, 1, 26, "amp"),
    ("AMP", "Amp Overdrive", 81, None, 1, 27, "amp"),
    ("AMP", "Amp Delay Send", 82, None, 1, 28, "amp"),
    ("AMP", "Amp Reverb Send", 83, None, 1, 29, "amp"),
    ("AMP", "Amp Pan", 10, None, 1, 30, "amp"),
    ("AMP", "Amp Volume", 7, None, 1, 31, "amp"),
    ("LFO", "LFO Speed", 102, None, 1, 32, "lfo"),
    ("LFO", "LFO Multiplier", 103, None, 1, 33, "lfo"),
    ("LFO", "LFO Fade In/Out", 104, None, 1, 34, "lfo"),
    ("LFO", "LFO Destination", 105, None, 1, 35, "lfo"),
    ("LFO", "LFO Waveform", 106, None, 1, 36, "lfo"),
    ("LFO", "LFO Start Phase", 107, None, 1, 37, "lfo"),
    ("LFO", "LFO Trig Mode", 108, None, 1, 38, "lfo"),
    ("LFO", "LFO Depth", 109, 118, 1, 39, "lfo"),
    ("DELAY", "Delay Time", 16, None, 2, 0, "fx"),
    ("DELAY", "Delay Pingpong", 17, None, 2, 1, "fx"),
    ("DELAY", "Delay Stereo Width", 18, None, 2, 2, "fx"),
    ("DELAY", "Delay Feedback", 19, None, 2, 3, "fx"),
    ("DELAY", "Delay Highpass Filter", 20, None, 2, 4, "fx"),
    ("DELAY", "Delay Lowpass Filter", 21, None, 2, 5, "fx"),
    ("DELAY", "Delay Reverb Send", 22, None, 2, 6, "fx"),
    ("DELAY", "Delay Mix Volume", 23, None, 2, 7, "fx"),
    ("REVERB", "Reverb Predelay", 24, None, 2, 8, "fx"),
    ("REVERB", "Reverb Decay Time", 25, None, 2, 9, "fx"),
    ("REVERB", "Reverb Shelving Freq", 26, None, 2, 10, "fx"),
    ("REVERB", "Reverb Shelving Gain", 27, None, 2, 11, "fx"),
    ("REVERB", "Reverb Highpass Filter", 28, None, 2, 12, "fx"),
    ("REVERB", "Reverb Lowpass Filter", 29, None, 2, 13, "fx"),
    ("REVERB", "Reverb Mix Volume", 31, None, 2, 15, "fx"),
    ("DISTORTION", "Dist Amount", 70, None, 2, 16, "fx"),
    ("DISTORTION", "Dist Symmetry", 71, None, 2, 17, "fx"),
    ("DISTORTION", "Delay Overdrive", 72, None, 2, 18, "fx"),
    ("DISTORTION", "Delay Dist/Comp Routing (pre/post)", 76, None, 2, 22, "fx"),
    ("DISTORTION", "Reverb Dist/Comp Routing (pre/post)", 77, None, 2, 23, "fx"),
    ("COMPRESSOR", "Compressor Threshold", 78, None, 2, 24, "fx"),
    ("COMPRESSOR", "Compressor Attack Time", 79, None, 2, 25, "fx"),
    ("COMPRESSOR", "Compressor Release Time", 80, None, 2, 26, "fx"),
    ("COMPRESSOR", "Compressor Makeup Gain", 81, None, 2, 27, "fx"),
    ("COMPRESSOR", "Compressor Ratio", 82, None, 2, 28, "fx"),
    ("COMPRESSOR", "Compressor Sidechain EQ", 83, None, 2, 29, "fx"),
    ("COMPRESSOR", "Compressor Dry/Wet Mix", 84, None, 2, 30, "fx"),
    ("COMPRESSOR", "Compressor Output Volume", 85, None, 2, 31, "fx"),
)

_MACHINE_SRC_ROWS: Final[Mapping[str, tuple[_MachineRow, ...]]] = MappingProxyType(
    {
        "bd_plastic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("Hold Time", 21),
            ("VCO Click", 22),
            ("Dust Level", 23),
        ),
        "bd_sharp": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("Hold Time", 21),
            ("Tick Level", 22),
            ("Waveform", 23),
        ),
        "bd_hard": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Hold", 19),
            ("Sweep Time", 20),
            ("Sweep Depth", 21),
            ("Waveform", 22),
            ("Transient Tick", 23),
        ),
        "bd_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Hold", 19),
            ("Sweep Time", 20),
            ("Sweep Depth", 21),
            ("Waveform", 22),
            ("Transient Tick", 23),
        ),
        "bd_fm": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("FM Amount", 19),
            ("Sweep Time", 20),
            ("FM Sweep Time", 21),
            ("FM Decay Time", 22),
            ("FM Tune", 23),
        ),
        "bd_silky": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("Hold", 21),
            ("VCO Click", 22),
            ("Dust Level", 23),
        ),
        "bd_acoustic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("Hold Time", 21),
            ("Impact", 22),
            ("Waveform", 23),
        ),
        "sd_natural": (
            ("Level", 16),
            ("Tune", 17),
            ("Body Decay", 18),
            ("Noise Decay", 19),
            ("Noise LPF", 20),
            ("Noise Balance", 21),
            ("Noise Resonance", 22),
            ("Noise HPF", 23),
        ),
        "sd_hard": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Tick Level", 20),
            ("Noise Decay", 21),
            ("Noise Level", 22),
            ("Sweep Time", 23),
        ),
        "sd_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Detune", 19),
            ("Snap Amount", 20),
            ("Noise Decay", 21),
            ("Noise Level", 22),
            ("Osc Balance", 23),
        ),
        "sd_fm": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("FM Tune", 19),
            ("FM Decay Time", 20),
            ("Noise Decay", 21),
            ("Noise Level", 22),
            ("FM Amount", 23),
        ),
        "sd_acoustic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Noise Decay", 19),
            ("Hold Time", 20),
            ("Noise Level", 21),
            ("Impact", 22),
            ("Sweep Depth", 23),
        ),
        "rs_hard": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Tick Level", 20),
            ("Noise Level", 21),
            ("Symmetry", 22),
            ("Sweep Time", 23),
        ),
        "rs_classic": (
            ("Level", 16),
            ("Tune Osc 1", 17),
            ("Decay", 18),
            ("Osc Balance", 19),
            ("Tune Osc 2", 20),
            ("Symmetry", 21),
            ("Noise Level", 22),
            ("Tick Level", 23),
        ),
        "cp_classic": (
            ("Level", 16),
            ("Noise Tone", 17),
            ("Noise Decay", 18),
            ("Clap Number", 19),
            ("Clap Rate", 20),
            ("Noise Level", 21),
            ("Random Claps", 22),
            ("Clap Decay", 23),
        ),
        # Hardware validation for PRs #148/#149 showed that low captured values
        # can put Pad 2/3 Dual VCO Osc 2 Detune in ERR over direct CC20, while
        # centered anchors tolerate a narrow live lane. Keep the manual row for
        # labels/passive planning; the live snapshot shell gates the active
        # send window via _is_live_dual_vco_detune_guarded_event.
        "dual_vco": (
            ("Level", 16),
            ("Osc 1 Tune", 17),
            ("Osc 1 Decay", 18),
            ("Balance", 19),
            ("Osc 2 Detune", 20),
            ("Osc Config", 21),
            ("Osc 2 Decay", 22),
            ("Bend", 23),
        ),
        "sy_chip": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Waveform", 19),
            ("Speed", 20),
            ("Offset 2", 21),
            ("Offset 3", 22),
            ("Offset 4", 23),
        ),
        "sy_raw": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Noise Level", 19),
            ("Osc 2 Detune", 20),
            ("Waveform 1", 21),
            ("Waveform 2", 22),
            ("Balance", 23),
        ),
        "bt_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Noise Level", 20),
            ("Snap Type", 21),
        ),
        "xt_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("Noise Decay", 21),
            ("Noise Level", 22),
            ("Noise Tone", 23),
        ),
        "ch_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Color", 19),
        ),
        "ch_metallic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
        ),
        "oh_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Color", 19),
        ),
        "oh_metallic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
        ),
        "hh_basic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
            ("Tone", 19),
            ("Transient Decay", 20),
            ("Osc Reset", 21),
        ),
        "hh_lab": (
            ("Level", 16),
            ("Tune 1", 17),
            ("Decay Time", 18),
            ("Tune 2", 19),
            ("Tune 3", 20),
            ("Tune 4", 21),
            ("Tune 5", 22),
            ("Tune 6", 23),
        ),
        "cy_metallic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
            ("Tone", 19),
            ("Transient Decay", 20),
        ),
        "cy_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay", 18),
            ("Color", 19),
            ("Tone", 20),
        ),
        "cy_ride": (
            ("Level", 16),
            ("Tune", 17),
            ("Tail Decay", 18),
            ("Hit Decay", 19),
            ("Cymbal Type", 20),
            ("Component 1", 21),
            ("Component 2", 22),
            ("Component 3", 23),
        ),
        "cb_classic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
            ("Detune", 19),
        ),
        "cb_metallic": (
            ("Level", 16),
            ("Tune", 17),
            ("Decay Time", 18),
            ("Detune", 19),
        ),
        "ut_noise": (
            ("Level", 16),
            ("LP Frequency", 17),
            ("Decay", 18),
            ("Sweep Depth", 19),
            ("Sweep Time", 20),
            ("LP Resonance", 21),
            ("HP Frequency", 22),
            ("Attack", 23),
        ),
        "ut_impulse": (
            ("Level", 16),
            ("Attack", 17),
            ("Decay", 18),
            ("Polarity", 19),
        ),
    }
)


def _risk_for(parameter: str) -> RiskTier:
    if parameter in _LOCKED_PARAMETER_NAMES:
        return "high"
    if any(token in parameter for token in _MEDIUM_RISK_TOKENS):
        return "medium"
    return "low"


def _status_for(section: str, parameter: str, machine_key: str | None) -> MutationStatus:
    if parameter in _LOCKED_PARAMETER_NAMES:
        return "locked_default"
    if machine_key is not None:
        if machine_key in _VALIDATED_RUNTIME_MACHINE_KEYS:
            return "validated_runtime"
        return "documented_only"
    if (section, parameter) in _VALIDATED_RUNTIME_GENERAL_ROWS:
        return "validated_runtime"
    return "documented_only"


def _value_metadata_for(section: str, parameter: str) -> _ValueMetadataRow:
    return _VALUE_METADATA_BY_SECTION_AND_PARAMETER.get(
        (section, parameter),
        _DEFAULT_VALUE_METADATA,
    )


def _general_mapping(row: _GeneralRow) -> AnalogRytmCcMapping:
    section, parameter, cc_msb, cc_lsb, nrpn_msb, nrpn_lsb, scope = row
    value_min, value_max, value_kind, value_orientation = _value_metadata_for(
        section,
        parameter,
    )
    return AnalogRytmCcMapping(
        section=section,
        parameter=parameter,
        cc_msb=cc_msb,
        cc_lsb=cc_lsb,
        nrpn_msb=nrpn_msb,
        nrpn_lsb=nrpn_lsb,
        scope=scope,
        risk=_risk_for(parameter),
        mutation_status=_status_for(section, parameter, None),
        value_min=value_min,
        value_max=value_max,
        value_kind=value_kind,
        value_orientation=value_orientation,
    )


def _machine_mapping(machine_key: str, row: _MachineRow) -> AnalogRytmCcMapping:
    parameter, cc_msb = row
    value_min, value_max, value_kind, value_orientation = _value_metadata_for(
        machine_key,
        parameter,
    )
    return AnalogRytmCcMapping(
        section=machine_key,
        parameter=parameter,
        cc_msb=cc_msb,
        cc_lsb=None,
        nrpn_msb=1,
        nrpn_lsb=cc_msb - 16,
        scope="src",
        risk=_risk_for(parameter),
        mutation_status=_status_for(machine_key, parameter, machine_key),
        value_min=value_min,
        value_max=value_max,
        value_kind=value_kind,
        value_orientation=value_orientation,
        machine_key=machine_key,
    )


_GENERAL_CC_MAPPINGS: Final[tuple[AnalogRytmCcMapping, ...]] = tuple(
    _general_mapping(row) for row in _GENERAL_CC_ROWS
)
_MACHINE_SRC_MAPPINGS: Final[Mapping[str, tuple[AnalogRytmCcMapping, ...]]] = MappingProxyType(
    {
        machine_key: tuple(_machine_mapping(machine_key, row) for row in rows)
        for machine_key, rows in _MACHINE_SRC_ROWS.items()
    }
)
_ALL_CC_MAPPINGS: Final[tuple[AnalogRytmCcMapping, ...]] = _GENERAL_CC_MAPPINGS + tuple(
    mapping
    for machine_key in sorted(_MACHINE_SRC_MAPPINGS)
    for mapping in _MACHINE_SRC_MAPPINGS[machine_key]
)
ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER: Final[
    Mapping[tuple[str, str], AnalogRytmCcMapping]
] = MappingProxyType({(row.section, row.parameter): row for row in _ALL_CC_MAPPINGS})

ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER: Final[Mapping[tuple[str, str], AnalogRytmCcMapping]] = (
    MappingProxyType({(row.section, row.parameter): row for row in _GENERAL_CC_MAPPINGS})
)

ANALOG_RYTM_MACHINE_SRC_BY_MACHINE: Final[Mapping[str, tuple[AnalogRytmCcMapping, ...]]] = (
    _MACHINE_SRC_MAPPINGS
)

ANALOG_RYTM_MANUAL_CC: Final[Mapping[str, AnalogRytmCcMapping]] = MappingProxyType(
    {
        **{f"{row.section}:{row.parameter}": row for row in _GENERAL_CC_MAPPINGS},
        **{
            f"machine:{row.machine_key}:{row.parameter}": row
            for machine_rows in _MACHINE_SRC_MAPPINGS.values()
            for row in machine_rows
        },
    }
)

ANALOG_RYTM_VALIDATED_RUNTIME_CC: Final[tuple[AnalogRytmCcMapping, ...]] = tuple(
    row for row in _ALL_CC_MAPPINGS if row.mutation_status == "validated_runtime"
)

ANALOG_RYTM_LOCKED_DEFAULT_CC: Final[tuple[AnalogRytmCcMapping, ...]] = tuple(
    row for row in _ALL_CC_MAPPINGS if row.mutation_status == "locked_default"
)

ANALOG_RYTM_DOCUMENTED_ONLY_CC: Final[tuple[AnalogRytmCcMapping, ...]] = tuple(
    row for row in _ALL_CC_MAPPINGS if row.mutation_status == "documented_only"
)

ANALOG_RYTM_FORBIDDEN_POLICY_NAMES: Final[tuple[str, ...]] = _FORBIDDEN_POLICY_NAMES

ANALOG_RYTM_MANUAL_NOTE_TRIGGERS: Final[tuple[AnalogRytmNoteTrigger, ...]] = (
    AnalogRytmNoteTrigger("C0", 0, "Triggers Sound Track 1"),
    AnalogRytmNoteTrigger("C#0", 1, "Triggers Sound Track 2"),
    AnalogRytmNoteTrigger("D0", 2, "Triggers Sound Track 3"),
    AnalogRytmNoteTrigger("D#0", 3, "Triggers Sound Track 4"),
    AnalogRytmNoteTrigger("E0", 4, "Triggers Sound Track 5"),
    AnalogRytmNoteTrigger("F0", 5, "Triggers Sound Track 6"),
    AnalogRytmNoteTrigger("F#0", 6, "Triggers Sound Track 7"),
    AnalogRytmNoteTrigger("G0", 7, "Triggers Sound Track 8"),
    AnalogRytmNoteTrigger("G#0", 8, "Triggers Sound Track 9"),
    AnalogRytmNoteTrigger("A0", 9, "Triggers Sound Track 10"),
    AnalogRytmNoteTrigger("A#0", 10, "Triggers Sound Track 11"),
    AnalogRytmNoteTrigger("B0", 11, "Triggers Sound Track 12"),
    AnalogRytmNoteTrigger("C1-B4", 12, "Triggers the active track chromatically"),
)


def get_machine_src_mappings(machine_key: str) -> tuple[AnalogRytmCcMapping, ...]:
    """Return manual-backed SRC mappings for a known Rytm machine key."""

    try:
        return ANALOG_RYTM_MACHINE_SRC_BY_MACHINE[machine_key]
    except KeyError as exc:
        raise KeyError(f"Unknown Analog Rytm machine key: {machine_key}") from exc


def get_analog_rytm_catalog_summary() -> AnalogRytmCatalogSummary:
    """Return deterministic counts for the passive Analog Rytm MIDI catalog."""

    machine_profile_count = len(RYTM_MACHINE_PROFILES)
    machine_profiles_with_src_count = sum(
        1 for profile in RYTM_MACHINE_PROFILES if profile.key in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE
    )
    return AnalogRytmCatalogSummary(
        general_cc_count=len(_GENERAL_CC_MAPPINGS),
        machine_src_cc_count=sum(len(rows) for rows in ANALOG_RYTM_MACHINE_SRC_BY_MACHINE.values()),
        total_cc_count=len(ANALOG_RYTM_MANUAL_CC),
        validated_runtime_count=len(ANALOG_RYTM_VALIDATED_RUNTIME_CC),
        locked_default_count=len(ANALOG_RYTM_LOCKED_DEFAULT_CC),
        documented_only_count=len(ANALOG_RYTM_DOCUMENTED_ONLY_CC),
        forbidden_count=len(ANALOG_RYTM_FORBIDDEN_POLICY_NAMES),
        machine_profile_count=machine_profile_count,
        machine_profiles_with_src_count=machine_profiles_with_src_count,
        note_trigger_count=len(ANALOG_RYTM_MANUAL_NOTE_TRIGGERS),
        pad_count=len(RYTM_PAD_CAPABILITIES),
    )


__all__ = [
    "ANALOG_RYTM_ALL_CC_BY_SECTION_AND_PARAMETER",
    "ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER",
    "ANALOG_RYTM_DOCUMENTED_ONLY_CC",
    "ANALOG_RYTM_FORBIDDEN_POLICY_NAMES",
    "ANALOG_RYTM_LOCKED_DEFAULT_CC",
    "ANALOG_RYTM_MACHINE_SRC_BY_MACHINE",
    "ANALOG_RYTM_MANUAL_CC",
    "ANALOG_RYTM_MANUAL_NOTE_TRIGGERS",
    "ANALOG_RYTM_VALIDATED_RUNTIME_CC",
    "AnalogRytmCatalogSummary",
    "AnalogRytmCcMapping",
    "AnalogRytmNoteTrigger",
    "MutationStatus",
    "ParameterValueKind",
    "ParameterValueOrientation",
    "RiskTier",
    "get_analog_rytm_catalog_summary",
    "get_machine_src_mappings",
]
