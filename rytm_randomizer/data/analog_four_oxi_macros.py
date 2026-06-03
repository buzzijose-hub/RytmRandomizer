"""Passive Analog Four OXI-style macro facts.

This module is data-only. It uses the existing manual-backed Analog Four CC
catalog as its parameter vocabulary and does not render, send, or open MIDI.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class AnalogFourOxiMacroEventSpec:
    """One manual-backed target range for a passive A4 OXI-style macro."""

    track: int
    role: str
    lane: str
    parameter: str
    value_min: int
    value_max: int
    intent: str


@dataclass(frozen=True)
class AnalogFourOxiMacroSpec:
    """A four-track Analog Four macro recipe for passive preview generation."""

    name: str
    label: str
    summary: str
    energy: int
    events: tuple[AnalogFourOxiMacroEventSpec, ...]

    @property
    def track_count(self) -> int:
        """Return the number of unique A4 tracks targeted by this macro."""

        return len(frozenset(event.track for event in self.events))


DEFAULT_ANALOG_FOUR_OXI_MACRO: Final[str] = "hard-groove"

ANALOG_FOUR_OXI_MACROS: Final[Mapping[str, AnalogFourOxiMacroSpec]] = MappingProxyType(
    {
        "home": AnalogFourOxiMacroSpec(
            name="home",
            label="Home",
            summary="Gentle four-track reset-adjacent motion for a stable live anchor.",
            energy=2,
            events=(
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="bass foundation",
                    lane="oscillator balance",
                    parameter="OSC1 Level",
                    value_min=84,
                    value_max=112,
                    intent="keep the bass present without stealing the mix",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="bass foundation",
                    lane="filter shade",
                    parameter="Filter1 Frequency",
                    value_min=38,
                    value_max=62,
                    intent="park the low voice in a controlled pocket",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="soft stab",
                    lane="filter shade",
                    parameter="Filter1 Resonance",
                    value_min=24,
                    value_max=54,
                    intent="add a touch of contour without peak-time bite",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="soft stab",
                    lane="space send",
                    parameter="Reverb Send Level",
                    value_min=18,
                    value_max=50,
                    intent="leave air around the chord lane",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="motion accent",
                    lane="lfo motion",
                    parameter="LFO1 Depth A",
                    value_min=10,
                    value_max=32,
                    intent="keep movement subtle and predictable",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="motion accent",
                    lane="amp shape",
                    parameter="EnvA Decay Time",
                    value_min=28,
                    value_max=58,
                    intent="preserve short rhythmic punctuation",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="air layer",
                    lane="noise texture",
                    parameter="Noise Level",
                    value_min=0,
                    value_max=28,
                    intent="add a barely-there top layer",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="air layer",
                    lane="space send",
                    parameter="Delay Send Level",
                    value_min=12,
                    value_max=38,
                    intent="keep delays tucked behind the groove",
                ),
            ),
        ),
        "hard-groove": AnalogFourOxiMacroSpec(
            name="hard-groove",
            label="Hard Groove",
            summary="OXI-style four-track pressure for bass, stab, motion, and air lanes.",
            energy=5,
            events=(
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="bass foundation",
                    lane="oscillator drive",
                    parameter="OSC1 Level",
                    value_min=92,
                    value_max=122,
                    intent="push the bass voice forward",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="bass foundation",
                    lane="filter pressure",
                    parameter="Filter Overdrive",
                    value_min=34,
                    value_max=78,
                    intent="add controlled grit to the low lane",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="bass foundation",
                    lane="amp shape",
                    parameter="EnvA Decay Time",
                    value_min=32,
                    value_max=72,
                    intent="shape tight pressure around the kick",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="stab pressure",
                    lane="oscillator color",
                    parameter="OSC2 Level",
                    value_min=54,
                    value_max=96,
                    intent="blend a second oscillator into the stab lane",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="stab pressure",
                    lane="filter bite",
                    parameter="Filter1 Resonance",
                    value_min=36,
                    value_max=82,
                    intent="make the stab answer the groove",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="stab pressure",
                    lane="space send",
                    parameter="Delay Send Level",
                    value_min=20,
                    value_max=66,
                    intent="stage rhythmic repeats without washing out",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="motion accent",
                    lane="pulse motion",
                    parameter="OSC1 PWM Depth",
                    value_min=18,
                    value_max=76,
                    intent="move the accent lane with OXI-like pulse animation",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="motion accent",
                    lane="lfo motion",
                    parameter="LFO1 Speed",
                    value_min=18,
                    value_max=86,
                    intent="let the accent breathe against the sequence",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="motion accent",
                    lane="lfo depth",
                    parameter="LFO1 Depth A",
                    value_min=18,
                    value_max=78,
                    intent="scale motion without losing pad identity",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="air and noise",
                    lane="noise texture",
                    parameter="Noise Level",
                    value_min=10,
                    value_max=66,
                    intent="give the top lane industrial dust",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="air and noise",
                    lane="filter shade",
                    parameter="Filter2 Frequency",
                    value_min=44,
                    value_max=96,
                    intent="tilt the air lane without becoming harsh",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="air and noise",
                    lane="space send",
                    parameter="Reverb Send Level",
                    value_min=16,
                    value_max=56,
                    intent="give the high layer a controlled room",
                ),
            ),
        ),
        "dub-pressure": AnalogFourOxiMacroSpec(
            name="dub-pressure",
            label="Dub Pressure",
            summary="Delay/reverb-led A4 macro for cavernous but controlled hypnosis.",
            energy=4,
            events=(
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="sub anchor",
                    lane="filter shade",
                    parameter="Filter1 Frequency",
                    value_min=30,
                    value_max=58,
                    intent="keep the sub lane rounded and steady",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="sub anchor",
                    lane="space send",
                    parameter="Delay Send Level",
                    value_min=8,
                    value_max=34,
                    intent="add only short ghost repeats under the bass",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="dub stab",
                    lane="amp shape",
                    parameter="EnvA Release Time",
                    value_min=34,
                    value_max=82,
                    intent="let the stab bloom into the delay",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="dub stab",
                    lane="space send",
                    parameter="Delay Send Level",
                    value_min=54,
                    value_max=110,
                    intent="make the delay lane the main dub gesture",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="ripple motion",
                    lane="lfo motion",
                    parameter="LFO2 Speed",
                    value_min=20,
                    value_max=72,
                    intent="move the secondary modulation in slow waves",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="ripple motion",
                    lane="lfo depth",
                    parameter="LFO2 Depth A",
                    value_min=14,
                    value_max=58,
                    intent="keep modulation audible but not chaotic",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="wash layer",
                    lane="noise texture",
                    parameter="Noise Fade",
                    value_min=32,
                    value_max=88,
                    intent="fade noise into the tail of the groove",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="wash layer",
                    lane="space send",
                    parameter="Reverb Send Level",
                    value_min=58,
                    value_max=118,
                    intent="build the wide dub room without touching hardware",
                ),
            ),
        ),
        "industrial-transition": AnalogFourOxiMacroSpec(
            name="industrial-transition",
            label="Industrial Transition",
            summary="Tense four-track riser macro for transitions and breakdown pressure.",
            energy=7,
            events=(
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="pressure bass",
                    lane="oscillator tension",
                    parameter="OSC2 Pitch",
                    value_min=48,
                    value_max=76,
                    intent="lean the bass into a tense transition color",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=1,
                    role="pressure bass",
                    lane="filter pressure",
                    parameter="Filter Overdrive",
                    value_min=54,
                    value_max=112,
                    intent="increase controlled industrial pressure",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="metallic stab",
                    lane="oscillator edge",
                    parameter="Sync Amount",
                    value_min=28,
                    value_max=92,
                    intent="turn the stab lane into metallic movement",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=2,
                    role="metallic stab",
                    lane="filter bite",
                    parameter="Filter2 Resonance",
                    value_min=34,
                    value_max=90,
                    intent="add narrow peak-time bite",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="machine motion",
                    lane="pulse motion",
                    parameter="OSC2 PWM Depth",
                    value_min=22,
                    value_max=104,
                    intent="animate the machine lane for rising tension",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=3,
                    role="machine motion",
                    lane="lfo motion",
                    parameter="LFO1 Speed Multiplier",
                    value_min=1,
                    value_max=20,
                    intent="accelerate modulation without guessing a port",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="noise sweep",
                    lane="noise texture",
                    parameter="Noise Level",
                    value_min=32,
                    value_max=108,
                    intent="raise industrial air for a transition",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="noise sweep",
                    lane="filter shade",
                    parameter="Filter2 Frequency",
                    value_min=58,
                    value_max=118,
                    intent="open the top layer as the transition builds",
                ),
                AnalogFourOxiMacroEventSpec(
                    track=4,
                    role="noise sweep",
                    lane="space send",
                    parameter="Reverb Send Level",
                    value_min=30,
                    value_max=96,
                    intent="stretch the transition tail safely",
                ),
            ),
        ),
    }
)

__all__ = [
    "ANALOG_FOUR_OXI_MACROS",
    "DEFAULT_ANALOG_FOUR_OXI_MACRO",
    "AnalogFourOxiMacroEventSpec",
    "AnalogFourOxiMacroSpec",
]
