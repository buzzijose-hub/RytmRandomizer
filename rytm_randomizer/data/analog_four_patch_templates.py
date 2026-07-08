"""Passive Analog Four patch-genome candidate fact tables."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

ANALOG_FOUR_PATCH_FAMILY_OSCILLATORS: Final[str] = "Oscillators"
ANALOG_FOUR_PATCH_FAMILY_MODULATION: Final[str] = "Envelope and LFO"
ANALOG_FOUR_PATCH_FAMILY_EFFECTS: Final[str] = "Filter and effects"
ANALOG_FOUR_PATCH_HIGH_CONFIDENCE: Final[str] = "manual-map + feature-trait"
ANALOG_FOUR_PATCH_SCREEN_CONFIDENCE: Final[str] = "front-panel target; ordinal capture pending"


@dataclass(frozen=True)
class AnalogFourPatchGeneTemplateSpec:
    """One static A4 patch-template gene."""

    parameter: str
    screen_target: int | str
    family: str
    rationale: str
    confidence: str = ANALOG_FOUR_PATCH_HIGH_CONFIDENCE


@dataclass(frozen=True)
class AnalogFourPatchCandidateTemplateSpec:
    """One static A4 patch-template candidate."""

    column: int
    label: str
    role: str
    closeness: int
    genes: tuple[AnalogFourPatchGeneTemplateSpec, ...]


_OSC = ANALOG_FOUR_PATCH_FAMILY_OSCILLATORS
_MOD = ANALOG_FOUR_PATCH_FAMILY_MODULATION
_FX = ANALOG_FOUR_PATCH_FAMILY_EFFECTS
_SCREEN = ANALOG_FOUR_PATCH_SCREEN_CONFIDENCE
_G = AnalogFourPatchGeneTemplateSpec
_C = AnalogFourPatchCandidateTemplateSpec


ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES: Final[tuple[AnalogFourPatchCandidateTemplateSpec, ...]] = (
    _C(
        column=1,
        label="Closest reference",
        role="compact metallic techno stab",
        closeness=94,
        genes=(
            _G("OSC1 Level", 96, _OSC, "lead oscillator carries the audible reference body"),
            _G(
                "OSC1 Pulsewidth",
                -16,
                _OSC,
                "narrowed pulse adds the organic animated edge",
            ),
            _G(
                "OSC2 Level",
                54,
                _OSC,
                "second oscillator stays supportive instead of washing out the stab",
            ),
            _G(
                "OSC2 Pulsewidth",
                -22,
                _OSC,
                "offset width keeps oscillator B thinner and more synthetic",
            ),
            _G(
                "Sync Amount",
                64,
                _OSC,
                "moderate sync supplies the bright bite heard in the reference",
            ),
            _G("EnvA Attack Time", 0, _MOD, "instant attack preserves the percussive onset"),
            _G(
                "EnvA Decay Time",
                28,
                _MOD,
                "short amp decay keeps the phrase clipped and sequencer-friendly",
            ),
            _G(
                "EnvA Sustain Level",
                0,
                _MOD,
                "zero sustain makes the sound a stab rather than a pad",
            ),
            _G(
                "EnvA Release Time",
                8,
                _MOD,
                "brief release avoids clicks without smearing the groove",
            ),
            _G(
                "EnvA Env Shape",
                "triangle",
                _MOD,
                "neutral amp shape matches the manual front-panel triangle target",
            ),
            _G("EnvF Attack Time", 0, _MOD, "filter movement starts with the note transient"),
            _G(
                "EnvF Decay Time",
                38,
                _MOD,
                "filter closes quickly enough to create the compact sweep",
            ),
            _G("EnvF Sustain Level", 0, _MOD, "filter sustain stays off for the plucked shape"),
            _G(
                "EnvF Release Time",
                12,
                _MOD,
                "filter release follows the short amp tail without hanging open",
            ),
            _G(
                "EnvF Env Shape",
                "triangle",
                _MOD,
                "neutral filter-envelope shape is the safest starting point",
            ),
            _G(
                "EnvF Gate Length",
                "NOTE",
                _MOD,
                "front-panel note gate keeps the envelope tied to the trig",
                _SCREEN,
            ),
            _G(
                "EnvF Destination A",
                "OFF",
                _MOD,
                "leave filter envelope destination A unused until auditioned",
                _SCREEN,
            ),
            _G(
                "EnvF Depth A",
                0,
                _MOD,
                "center depth prevents an unverified destination from moving",
            ),
            _G(
                "EnvF Destination B",
                "OFF",
                _MOD,
                "leave filter envelope destination B unused until auditioned",
                _SCREEN,
            ),
            _G(
                "EnvF Depth B",
                0,
                _MOD,
                "center depth prevents an unverified destination from moving",
            ),
            _G(
                "LFO1 Speed",
                18,
                _MOD,
                "slow positive LFO rate gives barely moving techno pressure",
            ),
            _G(
                "LFO1 Speed Multiplier",
                "x1",
                _MOD,
                "x1 keeps the motion playable and not audio-rate",
            ),
            _G("LFO1 Mode", "TRG", _MOD, "triggered motion restarts predictably on each note"),
            _G(
                "LFO1 Waveform",
                "triangle",
                _MOD,
                "triangle movement mirrors smooth organic modulation",
            ),
            _G(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "manual dial-in target for subtle filter drift",
                _SCREEN,
            ),
            _G(
                "LFO1 Depth A",
                3,
                _MOD,
                "small positive depth keeps the modulation audible but close",
            ),
            _G(
                "LFO1 Destination B",
                "OFF",
                _MOD,
                "second destination is held back for a focused starting point",
                _SCREEN,
            ),
            _G("LFO1 Depth B", 0, _MOD, "center depth keeps destination B inactive"),
            _G(
                "Filter1 Frequency",
                74,
                _FX,
                "filter 1 stays open enough for the bright sync edge",
            ),
            _G(
                "Filter1 Resonance",
                34,
                _FX,
                "moderate resonance outlines the acid/techno contour",
            ),
            _G(
                "Filter Overdrive",
                10,
                _FX,
                "slight right-of-off drive adds body without flattening the transient",
            ),
            _G(
                "Filter1 Envelope Amount",
                12,
                _FX,
                "small positive envelope amount creates the opening snap",
            ),
            _G(
                "Filter2 Frequency",
                88,
                _FX,
                "high second filter cutoff preserves the upper harmonic bite",
            ),
            _G(
                "Filter2 Resonance",
                24,
                _FX,
                "filter 2 resonance is included explicitly for manual review",
            ),
            _G(
                "Filter2 Type",
                "HP2",
                _FX,
                "HP2 trims low-mid smear while keeping the stab cutting",
            ),
            _G(
                "Filter2 Envelope Amount",
                8,
                _FX,
                "small positive amount keeps HP2 movement from becoming hollow",
            ),
            _G(
                "Delay Send Level",
                15,
                _FX,
                "short delay send suggests space without turning into an echo patch",
            ),
            _G(
                "Reverb Send Level",
                22,
                _FX,
                "light reverb tail approximates the sampled room around the stab",
            ),
            _G("Volume", 94, _FX, "track volume leaves headroom for manual A/B matching"),
        ),
    ),
    _C(
        column=2,
        label="Brighter sync",
        role="more metallic oscillator pressure",
        closeness=88,
        genes=(
            _G("OSC1 Level", 100, _OSC, "stronger oscillator A body"),
            _G("OSC1 Pulsewidth", -24, _OSC, "narrower pulse increases buzz"),
            _G("OSC2 Level", 62, _OSC, "louder oscillator B raises sync color"),
            _G("OSC2 Pulsewidth", -30, _OSC, "offset width creates sharper beating"),
            _G("Sync Amount", 78, _OSC, "higher sync pushes metallic edge"),
            _G("EnvA Attack Time", 0, _MOD, "instant attack keeps bite"),
            _G("EnvA Decay Time", 24, _MOD, "shorter decay tightens the stab"),
            _G("EnvA Sustain Level", 0, _MOD, "zero sustain keeps it percussive"),
            _G("EnvA Release Time", 6, _MOD, "short release avoids wash"),
            _G("EnvA Env Shape", "triangle", _MOD, "neutral amp curve"),
            _G("EnvF Attack Time", 0, _MOD, "filter opens immediately"),
            _G("EnvF Decay Time", 34, _MOD, "compact filter sweep"),
            _G("EnvF Sustain Level", 0, _MOD, "zero sustain closes the filter"),
            _G("EnvF Release Time", 10, _MOD, "short filter tail"),
            _G("EnvF Env Shape", "triangle", _MOD, "neutral filter curve"),
            _G("LFO1 Speed", 22, _MOD, "slightly quicker filter motion"),
            _G("LFO1 Speed Multiplier", "x1", _MOD, "keeps movement musical"),
            _G("LFO1 Waveform", "triangle", _MOD, "smooth repeating motion"),
            _G(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN,
            ),
            _G("LFO1 Depth A", 5, _MOD, "more audible filter animation"),
            _G("Filter1 Frequency", 82, _FX, "brighter first filter"),
            _G("Filter1 Resonance", 40, _FX, "more pronounced peak"),
            _G("Filter Overdrive", 14, _FX, "extra harmonic bite"),
            _G("Filter1 Envelope Amount", 16, _FX, "snappier filter envelope"),
            _G("Filter2 Frequency", 96, _FX, "keeps top end open"),
            _G("Filter2 Resonance", 28, _FX, "clearer HP contour"),
            _G(
                "Filter2 Type",
                "HP2",
                _FX,
                "same high-pass contour as the closest candidate",
            ),
            _G("Filter2 Envelope Amount", 10, _FX, "small HP2 movement"),
            _G("Delay Send Level", 18, _FX, "slightly wider echo space"),
            _G("Reverb Send Level", 18, _FX, "less verb for a sharper front edge"),
            _G("Volume", 92, _FX, "headroom for the brighter patch"),
        ),
    ),
    _C(
        column=3,
        label="Noisy texture",
        role="grain and movement emphasis",
        closeness=82,
        genes=(
            _G("OSC1 Level", 88, _OSC, "slightly lower oscillator body"),
            _G("Noise Level", 26, _OSC, "adds controlled broadband texture"),
            _G("Noise Fade", 18, _OSC, "noise decays into the stab tail"),
            _G("OSC1 Pulsewidth", -12, _OSC, "less narrow pulse leaves room for noise"),
            _G("OSC2 Level", 48, _OSC, "keeps oscillator B behind the texture"),
            _G("Sync Amount", 58, _OSC, "moderate sync under noise layer"),
            _G("EnvA Attack Time", 0, _MOD, "instant texture onset"),
            _G("EnvA Decay Time", 34, _MOD, "longer decay lets texture breathe"),
            _G("EnvA Sustain Level", 0, _MOD, "still a stab, not a pad"),
            _G("EnvA Release Time", 12, _MOD, "slightly longer release for grit"),
            _G("EnvA Env Shape", "triangle", _MOD, "neutral amp shape"),
            _G("EnvF Attack Time", 0, _MOD, "filter movement starts immediately"),
            _G("EnvF Decay Time", 44, _MOD, "longer sweep exposes texture"),
            _G("EnvF Sustain Level", 0, _MOD, "filter closes after the hit"),
            _G("EnvF Release Time", 16, _MOD, "filter release follows the noisy tail"),
            _G("EnvF Env Shape", "triangle", _MOD, "neutral filter curve"),
            _G("LFO1 Speed", 14, _MOD, "slower wobble reads as drifting texture"),
            _G("LFO1 Speed Multiplier", "x1", _MOD, "keeps the movement slow"),
            _G(
                "LFO1 Waveform",
                "random",
                _MOD,
                "manual target for less periodic texture",
            ),
            _G(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN,
            ),
            _G("LFO1 Depth A", 4, _MOD, "subtle drift"),
            _G("Filter1 Frequency", 68, _FX, "slightly darker first filter"),
            _G("Filter1 Resonance", 30, _FX, "less peaky to let noise through"),
            _G("Filter Overdrive", 8, _FX, "light saturation for grain"),
            _G("Filter1 Envelope Amount", 10, _FX, "small opening gesture"),
            _G(
                "Filter2 Frequency",
                78,
                _FX,
                "lower HP2 trims body but preserves texture",
            ),
            _G("Filter2 Resonance", 20, _FX, "less resonance avoids whistling"),
            _G("Filter2 Type", "HP2", _FX, "high-pass texture contour"),
            _G("Filter2 Envelope Amount", 6, _FX, "light second-filter motion"),
            _G("Delay Send Level", 22, _FX, "delay catches noisy grains"),
            _G("Reverb Send Level", 30, _FX, "more space around texture"),
            _G("Volume", 90, _FX, "headroom for noise and effects"),
        ),
    ),
    _C(
        column=4,
        label="Rounder bass",
        role="warmer low-mid translation",
        closeness=78,
        genes=(
            _G("OSC1 Level", 104, _OSC, "fuller oscillator A body"),
            _G("OSC1 Pulsewidth", -6, _OSC, "wider pulse gives a rounder core"),
            _G(
                "OSC2 Level",
                44,
                _OSC,
                "quieter oscillator B lowers metallic pressure",
            ),
            _G("OSC2 Pulsewidth", -10, _OSC, "less offset keeps the sound smoother"),
            _G("Sync Amount", 46, _OSC, "less sync for a rounder timbre"),
            _G("EnvA Attack Time", 0, _MOD, "keeps onset tight"),
            _G("EnvA Decay Time", 42, _MOD, "slightly longer body"),
            _G("EnvA Sustain Level", 0, _MOD, "still one-shot shaped"),
            _G("EnvA Release Time", 14, _MOD, "rounder tail without pad smear"),
            _G("EnvA Env Shape", "triangle", _MOD, "neutral amp shape"),
            _G("EnvF Attack Time", 0, _MOD, "filter starts with transient"),
            _G(
                "EnvF Decay Time",
                48,
                _MOD,
                "slower closure keeps low-mid warmth",
            ),
            _G("EnvF Sustain Level", 0, _MOD, "filter eventually closes"),
            _G("EnvF Release Time", 18, _MOD, "warmer filter tail"),
            _G("EnvF Env Shape", "triangle", _MOD, "neutral filter curve"),
            _G("LFO1 Speed", 10, _MOD, "slower movement for bass support"),
            _G("LFO1 Speed Multiplier", "x1", _MOD, "keeps movement controlled"),
            _G("LFO1 Waveform", "triangle", _MOD, "smooth tonal drift"),
            _G(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN,
            ),
            _G("LFO1 Depth A", 2, _MOD, "tiny movement keeps bass stable"),
            _G("Filter1 Frequency", 58, _FX, "darker filter for warmer body"),
            _G("Filter1 Resonance", 26, _FX, "less peak for bass smoothness"),
            _G("Filter Overdrive", 6, _FX, "mild saturation without harshness"),
            _G("Filter1 Envelope Amount", 8, _FX, "small pluck remains audible"),
            _G(
                "Filter2 Frequency",
                70,
                _FX,
                "HP2 sits lower for weight control",
            ),
            _G("Filter2 Resonance", 18, _FX, "subtle second-filter definition"),
            _G(
                "Filter2 Type",
                "HP2",
                _FX,
                "same high-pass cleanup, warmer setting",
            ),
            _G("Filter2 Envelope Amount", 4, _FX, "minimal HP movement"),
            _G("Delay Send Level", 10, _FX, "keeps bass candidate dry"),
            _G(
                "Reverb Send Level",
                14,
                _FX,
                "minimal space for live low-end clarity",
            ),
            _G("Volume", 96, _FX, "slightly louder warm candidate"),
        ),
    ),
)


__all__ = [
    "ANALOG_FOUR_PATCH_CANDIDATE_TEMPLATES",
    "AnalogFourPatchCandidateTemplateSpec",
    "AnalogFourPatchGeneTemplateSpec",
]
