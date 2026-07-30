"""Canonical measured-audio model facts for Analog Four patch inference."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, get_args

from .analog_four_patch_templates import ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES

AnalogFourInferenceScale = Literal["unipolar", "bipolar"]
AnalogFourInferenceFeatureKey = Literal[
    "animation",
    "attack",
    "brightness",
    "decay",
    "duration",
    "harmonicity",
    "low_end",
    "noise",
    "sustain",
    "tail",
    "transient",
]
AnalogFourInferenceParameter = Literal[
    "Delay Send Level",
    "EnvA Attack Time",
    "EnvA Decay Time",
    "EnvA Release Time",
    "EnvA Sustain Level",
    "EnvF Attack Time",
    "EnvF Decay Time",
    "EnvF Release Time",
    "EnvF Sustain Level",
    "Filter Overdrive",
    "Filter1 Envelope Amount",
    "Filter1 Frequency",
    "Filter1 Resonance",
    "Filter2 Envelope Amount",
    "Filter2 Frequency",
    "Filter2 Resonance",
    "LFO1 Depth A",
    "LFO1 Depth B",
    "LFO1 Speed",
    "Noise Fade",
    "Noise Level",
    "OSC1 Level",
    "OSC1 Pulsewidth",
    "OSC2 Level",
    "OSC2 Pulsewidth",
    "Reverb Send Level",
    "Sync Amount",
    "Volume",
]

A4_AUDIO_INFERENCE_UNIPOLAR: Final[AnalogFourInferenceScale] = "unipolar"
A4_AUDIO_INFERENCE_BIPOLAR: Final[AnalogFourInferenceScale] = "bipolar"
ANALOG_FOUR_INFERENCE_FEATURE_KEYS: Final[frozenset[str]] = frozenset(
    get_args(AnalogFourInferenceFeatureKey)
)
ANALOG_FOUR_INFERENCE_PARAMETERS: Final[frozenset[str]] = frozenset(
    get_args(AnalogFourInferenceParameter)
)
_ANALOG_FOUR_CANDIDATE_PARAMETERS: Final[frozenset[str]] = frozenset(
    gene.parameter
    for candidate in ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES
    for gene in candidate.genes
)


@dataclass(frozen=True)
class AnalogFourAudioInferenceTerm:
    """One weighted feature product in a deterministic inference equation."""

    feature_keys: tuple[AnalogFourInferenceFeatureKey, ...]
    coefficient: float

    def __post_init__(self) -> None:
        if not self.feature_keys:
            raise ValueError("A4 inference terms require at least one feature key")
        unknown = {
            feature_key
            for feature_key in self.feature_keys
            if feature_key not in ANALOG_FOUR_INFERENCE_FEATURE_KEYS
        }
        if unknown:
            raise ValueError(f"unknown A4 inference feature keys: {sorted(unknown)!r}")


@dataclass(frozen=True)
class AnalogFourAudioInferenceSpec:
    """One equation shared by one or more canonical A4 parameters."""

    parameters: tuple[AnalogFourInferenceParameter, ...]
    scale: AnalogFourInferenceScale
    intercept: float
    terms: tuple[AnalogFourAudioInferenceTerm, ...]
    output_multiplier: float = 1.0

    def __post_init__(self) -> None:
        if not self.parameters:
            raise ValueError("A4 inference specs require at least one parameter")
        if len(set(self.parameters)) != len(self.parameters):
            raise ValueError("A4 inference spec parameters must be unique")
        unknown = {
            parameter
            for parameter in self.parameters
            if parameter not in ANALOG_FOUR_INFERENCE_PARAMETERS
            or parameter not in _ANALOG_FOUR_CANDIDATE_PARAMETERS
        }
        if unknown:
            raise ValueError(f"unknown A4 inference parameters: {sorted(unknown)!r}")
        if not self.terms:
            raise ValueError("A4 inference specs require at least one weighted term")


def _term(
    coefficient: float,
    *feature_keys: AnalogFourInferenceFeatureKey,
) -> AnalogFourAudioInferenceTerm:
    return AnalogFourAudioInferenceTerm(feature_keys=feature_keys, coefficient=coefficient)


_ANALOG_FOUR_AUDIO_INFERENCE_SPECS: Final[tuple[AnalogFourAudioInferenceSpec, ...]] = (
    AnalogFourAudioInferenceSpec(
        ("OSC1 Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        70.0,
        (_term(38.0, "harmonicity"), _term(18.0, "low_end"), _term(-12.0, "noise")),
    ),
    AnalogFourAudioInferenceSpec(
        ("OSC2 Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        22.0,
        (
            _term(54.0, "brightness"),
            _term(22.0, "harmonicity"),
            _term(-8.0, "low_end"),
        ),
    ),
    AnalogFourAudioInferenceSpec(
        ("Noise Level",), A4_AUDIO_INFERENCE_UNIPOLAR, 8.0, (_term(106.0, "noise"),)
    ),
    AnalogFourAudioInferenceSpec(
        ("Noise Fade",), A4_AUDIO_INFERENCE_UNIPOLAR, 10.0, (_term(96.0, "tail"),)
    ),
    AnalogFourAudioInferenceSpec(
        ("OSC1 Pulsewidth", "OSC2 Pulsewidth"),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (
            _term(28.0, "brightness"),
            _term(12.0, "harmonicity"),
            _term(-8.0, "low_end"),
        ),
        -1.0,
    ),
    AnalogFourAudioInferenceSpec(
        ("Sync Amount",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(82.0, "brightness"), _term(34.0, "harmonicity")),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvA Attack Time", "EnvF Attack Time"),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(112.0, "attack"),),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvA Decay Time",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        8.0,
        (_term(82.0, "decay"), _term(30.0, "duration")),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvF Decay Time",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        10.0,
        (_term(72.0, "decay"), _term(34.0, "transient")),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvA Sustain Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(112.0, "sustain"),),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvF Sustain Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(92.0, "sustain"),),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvA Release Time",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(100.0, "tail"), _term(18.0, "duration")),
    ),
    AnalogFourAudioInferenceSpec(
        ("EnvF Release Time",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(92.0, "tail"), _term(22.0, "decay")),
    ),
    AnalogFourAudioInferenceSpec(
        ("LFO1 Speed",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (_term(48.0, "animation"), _term(8.0, "transient")),
    ),
    AnalogFourAudioInferenceSpec(
        ("LFO1 Depth A",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (_term(24.0, "animation"), _term(8.0, "noise")),
    ),
    AnalogFourAudioInferenceSpec(
        ("LFO1 Depth B",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (_term(18.0, "animation", "noise"),),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter1 Frequency",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        24.0,
        (_term(92.0, "brightness"), _term(-18.0, "low_end")),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter2 Frequency",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        46.0,
        (_term(76.0, "brightness"), _term(-12.0, "low_end")),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter1 Resonance",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        8.0,
        (_term(38.0, "harmonicity"), _term(22.0, "transient")),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter2 Resonance",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        6.0,
        (_term(30.0, "harmonicity"), _term(20.0, "brightness")),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter Overdrive",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (
            _term(0.35, "harmonicity"),
            _term(0.35, "noise"),
            _term(0.30, "low_end"),
        ),
        34.0,
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter1 Envelope Amount",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (
            _term(46.0, "transient"),
            _term(10.0, "decay"),
            _term(-6.0, "sustain"),
        ),
    ),
    AnalogFourAudioInferenceSpec(
        ("Filter2 Envelope Amount",),
        A4_AUDIO_INFERENCE_BIPOLAR,
        0.0,
        (
            _term(34.0, "transient"),
            _term(10.0, "animation"),
            _term(-5.0, "sustain"),
        ),
    ),
    AnalogFourAudioInferenceSpec(
        ("Delay Send Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (_term(42.0, "animation"), _term(35.0, "tail")),
    ),
    AnalogFourAudioInferenceSpec(
        ("Reverb Send Level",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        0.0,
        (
            _term(58.0, "tail"),
            _term(28.0, "sustain"),
            _term(20.0, "noise"),
        ),
    ),
    AnalogFourAudioInferenceSpec(
        ("Volume",),
        A4_AUDIO_INFERENCE_UNIPOLAR,
        88.0,
        (_term(16.0, "harmonicity"), _term(-8.0, "noise")),
    ),
)

ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER: Final[
    Mapping[AnalogFourInferenceParameter, AnalogFourAudioInferenceSpec]
] = MappingProxyType(
    {
        parameter: spec
        for spec in _ANALOG_FOUR_AUDIO_INFERENCE_SPECS
        for parameter in spec.parameters
    }
)

__all__ = [
    "A4_AUDIO_INFERENCE_BIPOLAR",
    "A4_AUDIO_INFERENCE_UNIPOLAR",
    "ANALOG_FOUR_AUDIO_INFERENCE_BY_PARAMETER",
    "ANALOG_FOUR_INFERENCE_FEATURE_KEYS",
    "ANALOG_FOUR_INFERENCE_PARAMETERS",
    "AnalogFourAudioInferenceSpec",
    "AnalogFourAudioInferenceTerm",
    "AnalogFourInferenceFeatureKey",
    "AnalogFourInferenceParameter",
]
