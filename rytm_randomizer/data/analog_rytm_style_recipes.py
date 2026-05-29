"""Curated full-kit style recipes for the Analog Rytm MKII."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

from .analog_rytm_midi import (
    ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER,
    MutationStatus,
    RiskTier,
    get_machine_src_mappings,
)
from .rytm_machine_catalog import get_rytm_machine_profile, is_machine_allowed_on_pad

RenderedStyleSource: TypeAlias = Literal["machine", "machine_src", "manual"]


@dataclass(frozen=True)
class AnalogRytmStyleParameter:
    """One desired parameter value inside a curated Rytm style recipe."""

    section: str
    parameter: str
    value: int
    intent: str


@dataclass(frozen=True)
class AnalogRytmStylePad:
    """One pad's machine choice and parameter targets for a style recipe."""

    pad: int
    machine_key: str
    parameters: tuple[AnalogRytmStyleParameter, ...]


@dataclass(frozen=True)
class AnalogRytmStyleRecipe:
    """A deterministic full-12-pad Rytm kit style."""

    name: str
    label: str
    description: str
    pads: tuple[AnalogRytmStylePad, ...]


@dataclass(frozen=True)
class AnalogRytmRenderedStyleEvent:
    """A concrete CC MSB event produced by a style recipe."""

    pad: int
    channel: int
    machine_key: str
    section: str
    parameter: str
    cc_msb: int
    value: int
    risk: RiskTier
    mutation_status: MutationStatus
    source: RenderedStyleSource
    intent: str


_EXCLUDED_PARAMETERS: Final[frozenset[str]] = frozenset(
    {
        "Amp Volume",
        "Level",
        "LFO Destination",
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
        "Sample Slot",
        "Sample Level",
        "Track Level",
        "Track Mute (seq. mute)",
        "Track Solo (seq. mute)",
    }
)
_EXCLUDED_SECTIONS: Final[frozenset[str]] = frozenset({"SAMPLE", "PERFORMANCE"})


def _src(parameter: str, value: int, intent: str) -> AnalogRytmStyleParameter:
    return AnalogRytmStyleParameter("SRC", parameter, value, intent)


def _manual(section: str, parameter: str, value: int, intent: str) -> AnalogRytmStyleParameter:
    return AnalogRytmStyleParameter(section, parameter, value, intent)


def _pad(
    pad: int,
    machine_key: str,
    *parameters: AnalogRytmStyleParameter,
) -> AnalogRytmStylePad:
    return AnalogRytmStylePad(pad=pad, machine_key=machine_key, parameters=parameters)


def _recipe(
    name: str,
    label: str,
    description: str,
    *pads: AnalogRytmStylePad,
) -> AnalogRytmStyleRecipe:
    return AnalogRytmStyleRecipe(
        name=name,
        label=label,
        description=description,
        pads=pads,
    )


ANALOG_RYTM_STYLE_RECIPES: Final[Mapping[str, AnalogRytmStyleRecipe]] = MappingProxyType(
    {
        "detroit-deep": _recipe(
            "detroit-deep",
            "Detroit Deep",
            "Warm, restrained 12-pad kit with woody percussion and controlled space.",
            _pad(
                1,
                "bd_hard",
                _src("Tune", 52, "grounded low fundamental"),
                _src("Decay", 72, "long but contained kick body"),
                _src("Sweep Depth", 34, "soft analog knock"),
                _manual("FILTER", "Filter Frequency", 25, "preserve kick sub weight"),
            ),
            _pad(
                2,
                "sd_classic",
                _src("Tune", 58, "low-mid snare pitch"),
                _src("Decay", 48, "short backbeat body"),
                _src("Noise Level", 44, "muted paper edge"),
                _manual("AMP", "Amp Reverb Send", 18, "small room tail"),
            ),
            _pad(
                3,
                "rs_classic",
                _src("Tune Osc 1", 64, "rim tuned near center"),
                _src("Decay", 34, "tight rim body"),
                _src("Noise Level", 30, "soft noise edge"),
                _manual("AMP", "Amp Reverb Send", 22, "distant rim air"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 68, "open clap tone"),
                _src("Noise Decay", 40, "short clap cloud"),
                _src("Clap Decay", 46, "deep but controlled clap"),
                _manual("AMP", "Amp Reverb Send", 28, "classic room send"),
            ),
            _pad(
                5,
                "bt_classic",
                _src("Tune", 48, "low tom support"),
                _src("Decay", 58, "rounded bass tom"),
                _src("Noise Level", 24, "barely audible skin"),
                _manual("FILTER", "Filter Frequency", 70, "warm tom focus"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 46, "low auxiliary tom"),
                _src("Decay", 52, "short rolling tail"),
                _src("Sweep Depth", 20, "gentle pitch motion"),
                _manual("AMP", "Amp Reverb Send", 16, "subtle tom room"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 58, "mid tom response"),
                _src("Decay", 46, "controlled body"),
                _src("Noise Level", 18, "soft attack noise"),
                _manual("AMP", "Amp Delay Send", 10, "tiny echo support"),
            ),
            _pad(
                8,
                "xt_classic",
                _src("Tune", 72, "high tom accent"),
                _src("Decay", 40, "short high tom"),
                _src("Noise Tone", 58, "rounded attack tone"),
                _manual("FILTER", "Filter Resonance", 18, "mild ring"),
            ),
            _pad(
                9,
                "ch_classic",
                _src("Tune", 74, "closed hat body"),
                _src("Decay", 24, "tight closed hat"),
                _src("Color", 44, "dusty metal color"),
                _manual("AMP", "Amp Pan", 54, "slight left placement"),
            ),
            _pad(
                10,
                "oh_classic",
                _src("Tune", 70, "open hat pitch"),
                _src("Decay", 44, "controlled open tail"),
                _src("Color", 50, "warm open metal"),
                _manual("AMP", "Amp Reverb Send", 24, "open hat air"),
            ),
            _pad(
                11,
                "cy_ride",
                _src("Tune", 62, "ride sits behind hats"),
                _src("Tail Decay", 50, "medium ride tail"),
                _src("Hit Decay", 30, "short stick click"),
                _manual("FILTER", "Filter Frequency", 84, "soften ride top"),
            ),
            _pad(
                12,
                "cb_classic",
                _src("Tune", 66, "muted cowbell pitch"),
                _src("Decay Time", 32, "short bell tail"),
                _src("Detune", 22, "slight analog wobble"),
                _manual("AMP", "Amp Delay Send", 14, "small syncopated echo"),
            ),
        ),
        "deeper-rolling": _recipe(
            "deeper-rolling",
            "Deeper Rolling",
            "Tunneling, rolling kit with low tom movement and smeared edges.",
            _pad(
                1,
                "bd_silky",
                _src("Tune", 48, "deep kick root"),
                _src("Decay", 82, "rolling low body"),
                _src("Dust Level", 34, "soft air"),
                _manual("FILTER", "Filter Frequency", 25, "preserve rolling kick sub"),
            ),
            _pad(
                2,
                "sd_natural",
                _src("Tune", 54, "natural low snare"),
                _src("Body Decay", 46, "soft shell body"),
                _src("Noise Decay", 36, "short noise tail"),
                _manual("AMP", "Amp Reverb Send", 26, "dub room"),
            ),
            _pad(
                3,
                "rs_hard",
                _src("Tune", 58, "low rim click"),
                _src("Decay", 28, "tight rim"),
                _src("Noise Level", 34, "grain layer"),
                _manual("AMP", "Amp Delay Send", 18, "rolling echo"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 58, "dark clap"),
                _src("Noise Decay", 50, "wide clap noise"),
                _src("Clap Rate", 48, "slow flam"),
                _manual("AMP", "Amp Reverb Send", 34, "deeper clap space"),
            ),
            _pad(
                5,
                "bt_classic",
                _src("Tune", 42, "sub tom roll"),
                _src("Decay", 70, "long bass tom"),
                _src("Sweep Depth", 18, "minimal bend"),
                _manual("AMP", "Amp Delay Send", 20, "rolling low echo"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 50, "low-mid roll"),
                _src("Decay", 64, "moving tom tail"),
                _src("Noise Decay", 28, "soft skin noise"),
                _manual("FILTER", "Filter Frequency", 68, "rounded tom"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 62, "mid roll answer"),
                _src("Decay", 56, "medium tom"),
                _src("Sweep Time", 36, "slow bend"),
                _manual("AMP", "Amp Reverb Send", 18, "tom room"),
            ),
            _pad(
                8,
                "xt_classic",
                _src("Tune", 76, "high roll accent"),
                _src("Decay", 48, "short high tom"),
                _src("Noise Level", 22, "attack fuzz"),
                _manual("AMP", "Amp Delay Send", 16, "small rolling tap"),
            ),
            _pad(
                9,
                "hh_basic",
                _src("Tune", 68, "soft hat pitch"),
                _src("Decay Time", 20, "tight tick"),
                _src("Tone", 42, "muted hat tone"),
                _manual("AMP", "Amp Pan", 50, "left-center pulse"),
            ),
            _pad(
                10,
                "oh_classic",
                _src("Tune", 66, "dark open hat"),
                _src("Decay", 52, "rolling open wash"),
                _src("Color", 42, "muted metal"),
                _manual("AMP", "Amp Reverb Send", 30, "wash into room"),
            ),
            _pad(
                11,
                "cy_classic",
                _src("Tune", 60, "low cymbal bed"),
                _src("Decay", 44, "medium cymbal tail"),
                _src("Color", 38, "dark cymbal color"),
                _manual("FILTER", "Filter Frequency", 76, "rolled off shimmer"),
            ),
            _pad(
                12,
                "cb_metallic",
                _src("Tune", 64, "metallic bell pulse"),
                _src("Decay Time", 28, "short metallic tail"),
                _src("Detune", 30, "narrow beating"),
                _manual("AMP", "Amp Delay Send", 22, "echo punctuation"),
            ),
        ),
        "hard-groove": _recipe(
            "hard-groove",
            "Hard Groove",
            "Punchy rolling groove with aggressive mid percussion and tight hats.",
            _pad(
                1,
                "bd_sharp",
                _src("Tune", 54, "assertive kick root"),
                _src("Decay", 66, "tight but heavy body"),
                _src("Tick Level", 54, "front edge"),
                _manual("AMP", "Amp Overdrive", 34, "pushed kick grit"),
            ),
            _pad(
                2,
                "sd_hard",
                _src("Tune", 62, "snappy snare pitch"),
                _src("Decay", 38, "tight snare body"),
                _src("Tick Level", 54, "hard snap"),
                _manual("AMP", "Amp Reverb Send", 18, "small room slap"),
            ),
            _pad(
                3,
                "rs_hard",
                _src("Tune", 68, "hard rim pitch"),
                _src("Decay", 22, "short rim"),
                _src("Tick Level", 58, "rim attack"),
                _manual("AMP", "Amp Delay Send", 12, "groove echo"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 74, "bright clap"),
                _src("Clap Rate", 70, "fast flam"),
                _src("Random Claps", 42, "loose human edge"),
                _manual("AMP", "Amp Reverb Send", 22, "club room"),
            ),
            _pad(
                5,
                "bt_classic",
                _src("Tune", 50, "groove low tom"),
                _src("Decay", 44, "short low tom"),
                _src("Snap Type", 70, "hard tom attack"),
                _manual("AMP", "Amp Overdrive", 22, "tom bite"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 56, "low tom bounce"),
                _src("Decay", 42, "short bounce"),
                _src("Sweep Depth", 42, "groove pitch hit"),
                _manual("FILTER", "Filter Resonance", 26, "percussive ring"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 68, "mid tom answer"),
                _src("Decay", 38, "short answer"),
                _src("Noise Level", 32, "skin attack"),
                _manual("AMP", "Amp Delay Send", 10, "tight repeat"),
            ),
            _pad(
                8,
                "xt_classic",
                _src("Tune", 82, "high tom stab"),
                _src("Decay", 34, "quick high tom"),
                _src("Noise Tone", 72, "bright attack"),
                _manual("AMP", "Amp Pan", 76, "right-side accent"),
            ),
            _pad(
                9,
                "ch_metallic",
                _src("Tune", 80, "bright closed hat"),
                _src("Decay Time", 16, "very tight hat"),
                _manual("FILTER", "Filter Frequency", 100, "open hat top"),
                _manual("AMP", "Amp Pan", 46, "left hat lane"),
            ),
            _pad(
                10,
                "oh_metallic",
                _src("Tune", 78, "bright open hat"),
                _src("Decay Time", 42, "tight open hat"),
                _manual("FILTER", "Filter Frequency", 104, "cut through"),
                _manual("AMP", "Amp Reverb Send", 16, "short bright tail"),
            ),
            _pad(
                11,
                "cy_metallic",
                _src("Tune", 72, "metallic cymbal hit"),
                _src("Decay Time", 36, "quick cymbal"),
                _src("Tone", 76, "forward tone"),
                _manual("AMP", "Amp Delay Send", 8, "short accent echo"),
            ),
            _pad(
                12,
                "cb_classic",
                _src("Tune", 76, "classic bell groove"),
                _src("Decay Time", 24, "tight bell"),
                _src("Detune", 34, "wide enough to move"),
                _manual("AMP", "Amp Pan", 82, "right bell lane"),
            ),
        ),
        "banging-warehouse": _recipe(
            "banging-warehouse",
            "Banging Warehouse",
            "Heavy, direct warehouse kit with hard attacks and controlled grit.",
            _pad(
                1,
                "bd_fm",
                _src("Tune", 50, "heavy FM kick root"),
                _src("Decay", 76, "big kick body"),
                _src("FM Amount", 42, "industrial bite"),
                _manual("AMP", "Amp Overdrive", 48, "warehouse pressure"),
            ),
            _pad(
                2,
                "sd_fm",
                _src("Tune", 60, "hard snare root"),
                _src("Decay", 42, "short snare slam"),
                _src("FM Amount", 50, "metal snare edge"),
                _manual("FILTER", "Filter Resonance", 34, "snare ring"),
            ),
            _pad(
                3,
                "rs_hard",
                _src("Tune", 72, "hard rim"),
                _src("Decay", 26, "fast rim"),
                _src("Symmetry", 70, "asymmetric edge"),
                _manual("AMP", "Amp Delay Send", 16, "warehouse slap"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 86, "bright clap noise"),
                _src("Noise Decay", 46, "wide clap"),
                _src("Clap Number", 86, "dense clap hits"),
                _manual("AMP", "Amp Reverb Send", 28, "large room send"),
            ),
            _pad(
                5,
                "ut_noise",
                _src("LP Frequency", 72, "noise body"),
                _src("Decay", 34, "short noise burst"),
                _src("Sweep Depth", 58, "noise stab motion"),
                _manual("AMP", "Amp Overdrive", 38, "dirty utility hit"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 48, "low tom hammer"),
                _src("Decay", 48, "controlled low tail"),
                _src("Sweep Depth", 52, "warehouse tom bend"),
                _manual("AMP", "Amp Pan", 42, "left tom lane"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 66, "mid tom hammer"),
                _src("Decay", 44, "short mid tail"),
                _src("Noise Level", 42, "hard skin noise"),
                _manual("AMP", "Amp Overdrive", 28, "tom grit"),
            ),
            _pad(
                8,
                "xt_classic",
                _src("Tune", 86, "high tom stab"),
                _src("Decay", 34, "fast high hit"),
                _src("Noise Tone", 84, "bright hit"),
                _manual("AMP", "Amp Delay Send", 12, "fast repeat"),
            ),
            _pad(
                9,
                "hh_lab",
                _src("Tune 1", 84, "lab hat top"),
                _src("Decay Time", 14, "razor hat"),
                _src("Tune 3", 92, "clustered metallicity"),
                _manual("FILTER", "Filter Frequency", 110, "sharp hat"),
            ),
            _pad(
                10,
                "oh_metallic",
                _src("Tune", 84, "metallic open hat"),
                _src("Decay Time", 38, "short open blast"),
                _manual("AMP", "Amp Reverb Send", 22, "warehouse air"),
                _manual("AMP", "Amp Pan", 72, "right open lane"),
            ),
            _pad(
                11,
                "cy_metallic",
                _src("Tune", 82, "bright crash hit"),
                _src("Decay Time", 42, "controlled crash"),
                _src("Transient Decay", 24, "hard transient"),
                _manual("FILTER", "Filter Frequency", 112, "cutting cymbal"),
            ),
            _pad(
                12,
                "cb_metallic",
                _src("Tune", 86, "high metal bell"),
                _src("Decay Time", 26, "short bell"),
                _src("Detune", 48, "warehouse clang"),
                _manual("AMP", "Amp Delay Send", 18, "metal repeat"),
            ),
        ),
        "flow-shift": _recipe(
            "flow-shift",
            "Flow Shift",
            "Machine-switch discovery kit with acoustic kick weight and synth-engine motion.",
            _pad(
                1,
                "bd_acoustic",
                _src("Tune", 50, "round acoustic low root"),
                _src("Decay", 78, "longer acoustic body"),
                _src("Impact", 86, "front-loaded knock"),
                _manual("FILTER", "Filter Frequency", 25, "preserve acoustic kick low end"),
            ),
            _pad(
                2,
                "sd_acoustic",
                _src("Tune", 56, "lower acoustic snare pitch"),
                _src("Decay", 42, "tight shell body"),
                _src("Noise Level", 52, "paper noise layer"),
                _manual("AMP", "Amp Reverb Send", 24, "small live-room tail"),
            ),
            _pad(
                3,
                "dual_vco",
                _src("Osc 1 Tune", 38, "low synth percussion root"),
                _src("Balance", 58, "second oscillator presence"),
                _src("Bend", 22, "subtle tonal movement"),
                _manual("FILTER", "Filter Frequency", 66, "hold synth below the hats"),
            ),
            _pad(
                4,
                "sy_chip",
                _src("Tune", 74, "digital percussion pitch"),
                _src("Decay", 30, "short chip transient"),
                _src("Speed", 86, "animated chip rate"),
                _manual("AMP", "Amp Delay Send", 18, "small digital echo"),
            ),
            _pad(
                5,
                "bt_classic",
                _src("Tune", 44, "bass tom undercurrent"),
                _src("Decay", 62, "rolling low tom"),
                _src("Sweep Depth", 26, "gentle downward bend"),
                _manual("FILTER", "Filter Frequency", 66, "rounded low tom"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 52, "low-mid tom answer"),
                _src("Decay", 50, "short rolling tail"),
                _src("Sweep Time", 42, "slower pitch move"),
                _manual("AMP", "Amp Pan", 46, "left tom placement"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 66, "mid tom response"),
                _src("Decay", 42, "controlled mid body"),
                _src("Noise Level", 26, "skin attack noise"),
                _manual("AMP", "Amp Delay Send", 14, "syncopated repeat"),
            ),
            _pad(
                8,
                "ut_impulse",
                _src("Attack", 6, "sharp impulse edge"),
                _src("Decay", 24, "short utility click"),
                _src("Polarity", 90, "forward impulse shape"),
                _manual("AMP", "Amp Pan", 80, "right-side accent"),
            ),
            _pad(
                9,
                "hh_lab",
                _src("Tune 1", 78, "lab hat top"),
                _src("Decay Time", 18, "tight hat clock"),
                _src("Tune 5", 92, "upper partial shimmer"),
                _manual("FILTER", "Filter Frequency", 104, "bright but controlled hat"),
            ),
            _pad(
                10,
                "oh_metallic",
                _src("Tune", 72, "metallic open hat pitch"),
                _src("Decay Time", 40, "short open wash"),
                _manual("AMP", "Amp Reverb Send", 22, "club air"),
                _manual("AMP", "Amp Pan", 70, "right open lane"),
            ),
            _pad(
                11,
                "cy_ride",
                _src("Tune", 60, "ride behind the groove"),
                _src("Tail Decay", 44, "contained ride tail"),
                _src("Hit Decay", 24, "short stick click"),
                _manual("FILTER", "Filter Frequency", 78, "soften cymbal top"),
            ),
            _pad(
                12,
                "cb_metallic",
                _src("Tune", 78, "metal bell punctuation"),
                _src("Decay Time", 24, "short bell tail"),
                _src("Detune", 38, "controlled metallic beating"),
                _manual("AMP", "Amp Delay Send", 16, "small bell echo"),
            ),
        ),
        "hypnotic-pressure": _recipe(
            "hypnotic-pressure",
            "Hypnotic Pressure",
            "Reduced, tunneling pressure kit with tonal repetition and restrained tops.",
            _pad(
                1,
                "bd_classic",
                _src("Tune", 46, "low classic pulse"),
                _src("Decay", 80, "steady sub pressure"),
                _src("Sweep Time", 34, "slow kick bend"),
                _manual("FILTER", "Filter Frequency", 25, "preserve hypnotic kick low end"),
            ),
            _pad(
                2,
                "sd_classic",
                _src("Tune", 50, "low snare ghost"),
                _src("Decay", 36, "short ghost body"),
                _src("Osc Balance", 42, "rounded oscillator body"),
                _manual("AMP", "Amp Reverb Send", 20, "background air"),
            ),
            _pad(
                3,
                "dual_vco",
                _src("Osc 1 Tune", 40, "low tonal tick"),
                _src("Balance", 54, "balanced oscillators"),
                _src("Bend", 18, "subtle tonal drift"),
                _manual("FILTER", "Filter Frequency", 64, "buried synth tick"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 48, "dark clap ghost"),
                _src("Noise Decay", 34, "short clap ghost"),
                _src("Random Claps", 26, "small variation"),
                _manual("AMP", "Amp Reverb Send", 24, "distant pulse"),
            ),
            _pad(
                5,
                "ut_impulse",
                _src("Attack", 8, "tiny impulse click"),
                _src("Decay", 30, "short impulse body"),
                _src("Polarity", 64, "center polarity"),
                _manual("AMP", "Amp Delay Send", 18, "repeating impulse"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 44, "low hypnotic tom"),
                _src("Decay", 60, "rolling tom body"),
                _src("Sweep Time", 44, "slow movement"),
                _manual("FILTER", "Filter Resonance", 30, "narrow ring"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 62, "mid hypnotic tom"),
                _src("Decay", 40, "short tom pulse"),
                _src("Sweep Depth", 24, "small repeating bend"),
                _manual("AMP", "Amp Delay Send", 24, "hypnotic repeat"),
            ),
            _pad(
                8,
                "xt_classic",
                _src("Tune", 76, "high hypnotic tap"),
                _src("Decay", 32, "short tap"),
                _src("Sweep Depth", 28, "small pitch motion"),
                _manual("AMP", "Amp Pan", 78, "right tap"),
            ),
            _pad(
                9,
                "ch_classic",
                _src("Tune", 62, "low closed hat"),
                _src("Decay", 18, "needle hat"),
                _src("Color", 34, "muted metal"),
                _manual("FILTER", "Filter Frequency", 86, "tucked top"),
            ),
            _pad(
                10,
                "oh_classic",
                _src("Tune", 60, "dark open hat"),
                _src("Decay", 36, "short open breath"),
                _src("Color", 30, "reduced metal"),
                _manual("AMP", "Amp Reverb Send", 18, "short room"),
            ),
            _pad(
                11,
                "cy_classic",
                _src("Tune", 54, "low cymbal pulse"),
                _src("Decay", 30, "short cymbal"),
                _src("Tone", 42, "muted tone"),
                _manual("FILTER", "Filter Frequency", 72, "subdued cymbal"),
            ),
            _pad(
                12,
                "cb_classic",
                _src("Tune", 58, "low bell motif"),
                _src("Decay Time", 22, "short motif"),
                _src("Detune", 18, "stable bell"),
                _manual("AMP", "Amp Delay Send", 26, "motif repeat"),
            ),
        ),
        "mills-drive": _recipe(
            "mills-drive",
            "Mills Drive",
            "Fast, urgent, stripped kit with sharp transients and little excess.",
            _pad(
                1,
                "bd_sharp",
                _src("Tune", 58, "fast kick pitch"),
                _src("Decay", 54, "short urgent body"),
                _src("Tick Level", 72, "needle transient"),
                _manual("AMP", "Amp Overdrive", 30, "tight drive"),
            ),
            _pad(
                2,
                "sd_hard",
                _src("Tune", 66, "high tight snare"),
                _src("Decay", 26, "very short snare"),
                _src("Tick Level", 70, "snap transient"),
                _manual("FILTER", "Filter Frequency", 92, "forward snare"),
            ),
            _pad(
                3,
                "rs_hard",
                _src("Tune", 76, "rim urgency"),
                _src("Decay", 18, "needle rim"),
                _src("Tick Level", 76, "hard rim tick"),
                _manual("AMP", "Amp Pan", 44, "left rim lane"),
            ),
            _pad(
                4,
                "cp_classic",
                _src("Noise Tone", 82, "bright thin clap"),
                _src("Clap Rate", 82, "tight flam"),
                _src("Noise Decay", 24, "short clap noise"),
                _manual("AMP", "Amp Reverb Send", 12, "minimal space"),
            ),
            _pad(
                5,
                "bt_classic",
                _src("Tune", 56, "fast low tom"),
                _src("Decay", 34, "short tom"),
                _src("Snap Type", 84, "clicky tom attack"),
                _manual("AMP", "Amp Delay Send", 8, "tiny repeat"),
            ),
            _pad(
                6,
                "xt_classic",
                _src("Tune", 64, "fast low-mid tom"),
                _src("Decay", 30, "tight tom"),
                _src("Sweep Depth", 46, "quick bend"),
                _manual("AMP", "Amp Pan", 52, "center tom"),
            ),
            _pad(
                7,
                "xt_classic",
                _src("Tune", 76, "fast mid tom"),
                _src("Decay", 28, "short response"),
                _src("Noise Level", 36, "attack noise"),
                _manual("AMP", "Amp Delay Send", 10, "machine repeat"),
            ),
            _pad(
                8,
                "ut_impulse",
                _src("Attack", 4, "instant impulse"),
                _src("Decay", 18, "tiny impulse"),
                _src("Polarity", 96, "forward click"),
                _manual("AMP", "Amp Pan", 84, "right impulse"),
            ),
            _pad(
                9,
                "hh_lab",
                _src("Tune 1", 92, "high clock hat"),
                _src("Decay Time", 10, "micro hat"),
                _src("Tune 5", 106, "upper partial"),
                _manual("FILTER", "Filter Frequency", 116, "sharp top"),
            ),
            _pad(
                10,
                "ch_metallic",
                _src("Tune", 88, "alternate tight hat"),
                _src("Decay Time", 12, "short alternate hat"),
                _manual("AMP", "Amp Pan", 74, "right hat lane"),
                _manual("FILTER", "Filter Resonance", 20, "thin edge"),
            ),
            _pad(
                11,
                "cy_metallic",
                _src("Tune", 88, "thin metallic hit"),
                _src("Decay Time", 24, "short metal hit"),
                _src("Tone", 92, "bright transient"),
                _manual("AMP", "Amp Reverb Send", 10, "small space"),
            ),
            _pad(
                12,
                "cb_classic",
                _src("Tune", 92, "urgent bell"),
                _src("Decay Time", 18, "short bell"),
                _src("Detune", 26, "focused beat"),
                _manual("AMP", "Amp Delay Send", 12, "tight clock echo"),
            ),
        ),
    }
)


def _require_cc_value(value: int, *, recipe_name: str, pad: int, parameter: str) -> None:
    if value < 0 or value > 127:
        raise ValueError(
            f"Rytm style {recipe_name!r} pad {pad} parameter {parameter!r} "
            "must have value in [0, 127]"
        )


def _reject_excluded_mapping(section: str, parameter: str, *, recipe_name: str, pad: int) -> None:
    if section in _EXCLUDED_SECTIONS or parameter in _EXCLUDED_PARAMETERS:
        raise ValueError(
            f"Rytm style {recipe_name!r} pad {pad} uses excluded parameter "
            f"{section}:{parameter}"
        )


def _machine_select_event(
    recipe: AnalogRytmStyleRecipe,
    pad_plan: AnalogRytmStylePad,
) -> AnalogRytmRenderedStyleEvent:
    if not is_machine_allowed_on_pad(pad_plan.pad, pad_plan.machine_key):
        raise ValueError(
            f"Rytm style {recipe.name!r} uses illegal machine "
            f"{pad_plan.machine_key!r} on pad {pad_plan.pad}"
        )

    profile = get_rytm_machine_profile(pad_plan.machine_key)
    mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[("COMMON", "Track Machine Type")]
    return AnalogRytmRenderedStyleEvent(
        pad=pad_plan.pad,
        channel=pad_plan.pad - 1,
        machine_key=pad_plan.machine_key,
        section=mapping.section,
        parameter=mapping.parameter,
        cc_msb=mapping.cc_msb,
        value=profile.machine_value,
        risk=mapping.risk,
        mutation_status=mapping.mutation_status,
        source="machine",
        intent=f"select {profile.label}",
    )


def _render_parameter_event(
    recipe: AnalogRytmStyleRecipe,
    pad_plan: AnalogRytmStylePad,
    target: AnalogRytmStyleParameter,
) -> AnalogRytmRenderedStyleEvent:
    _require_cc_value(
        target.value,
        recipe_name=recipe.name,
        pad=pad_plan.pad,
        parameter=target.parameter,
    )

    if target.section == "SRC":
        source_mappings = {
            mapping.parameter: mapping for mapping in get_machine_src_mappings(pad_plan.machine_key)
        }
        try:
            mapping = source_mappings[target.parameter]
        except KeyError as exc:
            raise KeyError(
                f"Rytm style {recipe.name!r} pad {pad_plan.pad} machine "
                f"{pad_plan.machine_key!r} has no SRC parameter {target.parameter!r}"
            ) from exc
        section = "SRC"
        source: RenderedStyleSource = "machine_src"
    else:
        try:
            mapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[(target.section, target.parameter)]
        except KeyError as exc:
            raise KeyError(
                f"Rytm style {recipe.name!r} pad {pad_plan.pad} has no manual "
                f"parameter {target.section}:{target.parameter}"
            ) from exc
        section = mapping.section
        source = "manual"

    _reject_excluded_mapping(section, mapping.parameter, recipe_name=recipe.name, pad=pad_plan.pad)
    return AnalogRytmRenderedStyleEvent(
        pad=pad_plan.pad,
        channel=pad_plan.pad - 1,
        machine_key=pad_plan.machine_key,
        section=section,
        parameter=mapping.parameter,
        cc_msb=mapping.cc_msb,
        value=target.value,
        risk=mapping.risk,
        mutation_status=mapping.mutation_status,
        source=source,
        intent=target.intent,
    )


def get_analog_rytm_style_recipe(recipe_name: str) -> AnalogRytmStyleRecipe | None:
    """Resolve a curated Rytm style recipe by slug or display label."""

    if recipe_name in ANALOG_RYTM_STYLE_RECIPES:
        return ANALOG_RYTM_STYLE_RECIPES[recipe_name]

    normalized = recipe_name.strip().casefold()
    for recipe in ANALOG_RYTM_STYLE_RECIPES.values():
        if recipe.name.casefold() == normalized or recipe.label.casefold() == normalized:
            return recipe
    return None


def render_analog_rytm_style_recipe(
    recipe: AnalogRytmStyleRecipe,
) -> tuple[AnalogRytmRenderedStyleEvent, ...]:
    """Render a curated style recipe into deterministic CC MSB send events."""

    if tuple(pad.pad for pad in recipe.pads) != tuple(range(1, 13)):
        raise ValueError(f"Rytm style {recipe.name!r} must cover pads 1 through 12")

    events: list[AnalogRytmRenderedStyleEvent] = []
    for pad_plan in recipe.pads:
        events.append(_machine_select_event(recipe, pad_plan))
        events.extend(
            _render_parameter_event(recipe, pad_plan, target) for target in pad_plan.parameters
        )
    return tuple(events)


__all__ = [
    "ANALOG_RYTM_STYLE_RECIPES",
    "AnalogRytmRenderedStyleEvent",
    "AnalogRytmStylePad",
    "AnalogRytmStyleParameter",
    "AnalogRytmStyleRecipe",
    "RenderedStyleSource",
    "get_analog_rytm_style_recipe",
    "render_analog_rytm_style_recipe",
]
