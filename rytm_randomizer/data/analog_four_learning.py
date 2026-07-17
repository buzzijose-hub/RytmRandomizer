"""Passive Analog Four patch-learning fact tables.

The constants here describe device-learning knowledge, not runtime behavior.
They are used by the patch-learning compiler to explain how measured musical
traits map onto Analog Four MKII parameter families and which passive capture
steps would help train future audio-to-patch matching.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .analog_four_display import (
    TRANSPORT_CC_READY,
    TRANSPORT_NRPN_READY,
    TRANSPORT_SCREEN_ONLY,
    TRANSPORT_SCREEN_ONLY_NRPN,
)


@dataclass(frozen=True)
class AnalogFourLearningRouteSpec:
    """One reference-trait to Analog Four parameter route."""

    trait_key: str
    parameter_focus: tuple[str, ...]
    learning_question: str
    rationale: str


@dataclass(frozen=True)
class AnalogFourLearningCaptureSpec:
    """One passive capture target for future A4 empirical learning."""

    step_id: str
    note_name: str
    midi_note: int
    velocity: int
    gate_ms: int
    repeat_count: int
    focus: str
    expected_evidence: tuple[str, ...]


ANALOG_FOUR_LEARNING_TRAIT_ROUTES: Final[tuple[AnalogFourLearningRouteSpec, ...]] = (
    AnalogFourLearningRouteSpec(
        trait_key="low_end_pressure",
        parameter_focus=(
            "Filter2 Type",
            "Filter2 Frequency",
            "Filter2 Resonance",
            "Volume",
            "OSC1 Level",
            "OSC2 Level",
        ),
        learning_question="Which HP2/base-level balance preserves body without masking the stab?",
        rationale="Low-end pressure is translated through level balance and Filter 2 shape.",
    ),
    AnalogFourLearningRouteSpec(
        trait_key="groove_density",
        parameter_focus=(
            "EnvA Decay Time",
            "EnvA Release Time",
            "EnvF Decay Time",
            "EnvF Release Time",
            "Delay Send Level",
        ),
        learning_question="How short can the amp and filter envelopes stay while the groove remains legible?",
        rationale="Dense references need compact envelopes and restrained delay spill.",
    ),
    AnalogFourLearningRouteSpec(
        trait_key="metallic_pressure",
        parameter_focus=(
            "Sync Amount",
            "OSC1 Pulsewidth",
            "OSC2 Pulsewidth",
            "Filter1 Frequency",
            "Filter1 Resonance",
            "Filter Overdrive",
        ),
        learning_question="How much sync, pulse narrowing, resonance, and overdrive creates the metallic edge?",
        rationale="Metallic pressure is the main oscillator and first-filter bite route.",
    ),
    AnalogFourLearningRouteSpec(
        trait_key="texture_noise",
        parameter_focus=(
            "Noise Level",
            "Noise Fade",
            "Chorus Send Level",
            "Reverb Send Level",
            "LFO1 Depth A",
        ),
        learning_question="How much noise and space can be added before the patch stops reading as a tight stab?",
        rationale="Texture is learned through noise amount, ambience sends, and subtle drift.",
    ),
    AnalogFourLearningRouteSpec(
        trait_key="arrangement_energy",
        parameter_focus=(
            "Filter1 Envelope Amount",
            "Filter2 Envelope Amount",
            "Filter Overdrive",
            "LFO1 Destination A",
            "LFO1 Depth A",
        ),
        learning_question="Which modulation rows should carry phrase pressure without changing the core tone?",
        rationale="Energy is routed through envelope depth, overdrive, and validated modulation rows.",
    ),
    AnalogFourLearningRouteSpec(
        trait_key="tempo_drive",
        parameter_focus=(
            "LFO1 Speed",
            "LFO1 Speed Multiplier",
            "LFO1 Waveform",
            "LFO1 Mode",
            "LFO1 Fade",
        ),
        learning_question="What slow motion rate locks to the reference tempo without sounding like a wobble?",
        rationale="Tempo drive informs LFO rate, multiplier, waveform, and retrigger behavior.",
    ),
)

ANALOG_FOUR_LEARNING_CAPTURE_MATRIX: Final[tuple[AnalogFourLearningCaptureSpec, ...]] = (
    AnalogFourLearningCaptureSpec(
        step_id="a4-root-short",
        note_name="C2",
        midi_note=36,
        velocity=96,
        gate_ms=120,
        repeat_count=1,
        focus="root transient and low body",
        expected_evidence=("attack shape", "pitch center", "low-end tail"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-mid-short",
        note_name="C3",
        midi_note=48,
        velocity=96,
        gate_ms=120,
        repeat_count=1,
        focus="main reference register",
        expected_evidence=("oscillator body", "filter bite", "envelope closure"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-high-short",
        note_name="C4",
        midi_note=60,
        velocity=96,
        gate_ms=120,
        repeat_count=1,
        focus="brightness and key tracking",
        expected_evidence=("brightness", "key follow", "alias-free edge"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-soft-velocity",
        note_name="C3",
        midi_note=48,
        velocity=48,
        gate_ms=120,
        repeat_count=1,
        focus="velocity sensitivity",
        expected_evidence=("attack variation", "filter response", "level change"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-held-tail",
        note_name="C3",
        midi_note=48,
        velocity=100,
        gate_ms=900,
        repeat_count=1,
        focus="release, ambience, and modulation tail",
        expected_evidence=("release length", "delay/reverb trail", "slow LFO motion"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-retrigger-grid",
        note_name="C3",
        midi_note=48,
        velocity=104,
        gate_ms=90,
        repeat_count=4,
        focus="sequenced retrigger behavior",
        expected_evidence=("envelope reset", "groove density", "filter recovery"),
    ),
    AnalogFourLearningCaptureSpec(
        step_id="a4-bright-pressure",
        note_name="G3",
        midi_note=55,
        velocity=118,
        gate_ms=180,
        repeat_count=2,
        focus="metallic pressure at performance velocity",
        expected_evidence=("sync bite", "filter peak", "overdrive saturation"),
    ),
)

ANALOG_FOUR_LEARNING_TRANSPORT_STATUS_WEIGHTS: Final[Mapping[str, int]] = MappingProxyType(
    {
        TRANSPORT_CC_READY: 4,
        TRANSPORT_NRPN_READY: 3,
        TRANSPORT_SCREEN_ONLY_NRPN: 1,
        TRANSPORT_SCREEN_ONLY: 0,
    }
)


__all__ = [
    "ANALOG_FOUR_LEARNING_CAPTURE_MATRIX",
    "ANALOG_FOUR_LEARNING_TRAIT_ROUTES",
    "ANALOG_FOUR_LEARNING_TRANSPORT_STATUS_WEIGHTS",
    "AnalogFourLearningCaptureSpec",
    "AnalogFourLearningRouteSpec",
]
