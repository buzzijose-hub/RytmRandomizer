"""Passive Analog Four patch genome compiler.

The compiler translates a :class:`FeatureReport` into four front-panel Analog
Four MKII patch candidates. It deliberately stops at DNA/report metadata: no
MIDI ports are opened, no messages are sent, and NRPN-only destination rows
remain screen-only until their exact ordinals are captured.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Final

from ..data.analog_four_display import AnalogFourPatchValue, make_a4_patch_value
from ..guardrails.schema import Confidence
from .blueprint import ReferenceTrait, build_reference_style_blueprint
from .feature_report import FeatureReport, compute_feature_report_hash

ANALOG_FOUR_PATCH_GENOME_VERSION: Final[str] = "analog-four-patch-genome-v1"
ANALOG_FOUR_DEVICE_ID: Final[str] = "analog_four_mk2"
ANALOG_FOUR_PATCH_MODE: Final[str] = "single-sound"
ANALOG_FOUR_TRACK_MIN: Final[int] = 1
ANALOG_FOUR_TRACK_MAX: Final[int] = 4
ANALOG_FOUR_PATCH_FAMILY_ORDER: Final[tuple[str, ...]] = (
    "Oscillators",
    "Envelope and LFO",
    "Filter and effects",
)
ANALOG_FOUR_PATCH_SAFETY: Final[tuple[str, ...]] = (
    "passive read-only patch genome",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "manual front-panel DNA only",
    "NRPN-only destinations require ordinal capture before live dial-in",
)


@dataclass(frozen=True)
class AnalogFourPatchGene:
    """One A4 patch parameter row for the selected track."""

    track: int
    family: str
    value: AnalogFourPatchValue
    rationale: str
    confidence: str


@dataclass(frozen=True)
class AnalogFourPatchCandidate:
    """One candidate column in the patch genome."""

    column: int
    label: str
    role: str
    closeness: int
    genes: tuple[AnalogFourPatchGene, ...]


@dataclass(frozen=True)
class AnalogFourPatchGenome:
    """Four-column passive A4 patch genome for one single-sound track."""

    version: str
    device_id: str
    mode: str
    selected_track: int
    source_hash: str
    source_confidence: Confidence
    candidate_count: int
    traits: tuple[ReferenceTrait, ...]
    candidates: tuple[AnalogFourPatchCandidate, ...]
    safety: tuple[str, ...]


@dataclass(frozen=True)
class _PatchGeneTemplate:
    parameter: str
    screen_target: int | str
    family: str
    rationale: str
    confidence: str


@dataclass(frozen=True)
class _CandidateTemplate:
    column: int
    label: str
    role: str
    closeness: int
    genes: tuple[_PatchGeneTemplate, ...]


_OSC: Final[str] = "Oscillators"
_MOD: Final[str] = "Envelope and LFO"
_FX: Final[str] = "Filter and effects"
_HIGH_CONFIDENCE: Final[str] = "manual-map + feature-trait"
_SCREEN_CONFIDENCE: Final[str] = "front-panel target; ordinal capture pending"


_CANDIDATE_TEMPLATES: Final[tuple[_CandidateTemplate, ...]] = (
    _CandidateTemplate(
        column=1,
        label="Closest reference",
        role="compact metallic techno stab",
        closeness=94,
        genes=(
            _PatchGeneTemplate(
                "OSC1 Level",
                96,
                _OSC,
                "lead oscillator carries the audible reference body",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "OSC1 Pulsewidth",
                -16,
                _OSC,
                "narrowed pulse adds the Synplant-like animated edge",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "OSC2 Level",
                54,
                _OSC,
                "second oscillator stays supportive instead of washing out the stab",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "OSC2 Pulsewidth",
                -22,
                _OSC,
                "offset width keeps oscillator B thinner and more synthetic",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Sync Amount",
                64,
                _OSC,
                "moderate sync supplies the bright bite heard in the reference",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvA Attack Time",
                0,
                _MOD,
                "instant attack preserves the percussive onset",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvA Decay Time",
                28,
                _MOD,
                "short amp decay keeps the phrase clipped and sequencer-friendly",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvA Sustain Level",
                0,
                _MOD,
                "zero sustain makes the sound a stab rather than a pad",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvA Release Time",
                8,
                _MOD,
                "brief release avoids clicks without smearing the groove",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvA Env Shape",
                "triangle",
                _MOD,
                "neutral amp shape matches the manual front-panel triangle target",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Attack Time",
                0,
                _MOD,
                "filter movement starts with the note transient",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Decay Time",
                38,
                _MOD,
                "filter closes quickly enough to create the compact sweep",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Sustain Level",
                0,
                _MOD,
                "filter sustain stays off for the plucked shape",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Release Time",
                12,
                _MOD,
                "filter release follows the short amp tail without hanging open",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Env Shape",
                "triangle",
                _MOD,
                "neutral filter-envelope shape is the safest starting point",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Gate Length",
                "NOTE",
                _MOD,
                "front-panel note gate keeps the envelope tied to the trig",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Destination A",
                "OFF",
                _MOD,
                "leave filter envelope destination A unused until auditioned",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Depth A",
                0,
                _MOD,
                "center depth prevents an unverified destination from moving",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Destination B",
                "OFF",
                _MOD,
                "leave filter envelope destination B unused until auditioned",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Depth B",
                0,
                _MOD,
                "center depth prevents an unverified destination from moving",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Speed",
                18,
                _MOD,
                "slow positive LFO rate gives barely moving techno pressure",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Speed Multiplier",
                "x1",
                _MOD,
                "x1 keeps the motion playable and not audio-rate",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Mode",
                "TRG",
                _MOD,
                "triggered motion restarts predictably on each note",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Waveform",
                "triangle",
                _MOD,
                "triangle movement mirrors the smooth Synplant-style modulation",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "manual dial-in target for subtle filter drift",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Depth A",
                3,
                _MOD,
                "small positive depth keeps the modulation audible but close",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Destination B",
                "OFF",
                _MOD,
                "second destination is held back for a focused starting point",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Depth B",
                0,
                _MOD,
                "center depth keeps destination B inactive",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter1 Frequency",
                74,
                _FX,
                "filter 1 stays open enough for the bright sync edge",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter1 Resonance",
                34,
                _FX,
                "moderate resonance outlines the acid/techno contour",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter Overdrive",
                10,
                _FX,
                "slight right-of-off drive adds body without flattening the transient",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter1 Envelope Amount",
                12,
                _FX,
                "small positive envelope amount creates the opening snap",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Frequency",
                88,
                _FX,
                "high second filter cutoff preserves the upper harmonic bite",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Resonance",
                24,
                _FX,
                "filter 2 resonance is included explicitly for manual review",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Type",
                "HP2",
                _FX,
                "HP2 trims low-mid smear while keeping the stab cutting",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Envelope Amount",
                8,
                _FX,
                "small positive amount keeps HP2 movement from becoming hollow",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Delay Send Level",
                15,
                _FX,
                "short delay send suggests space without turning into an echo patch",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Reverb Send Level",
                22,
                _FX,
                "light reverb tail approximates the sampled room around the stab",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Volume",
                94,
                _FX,
                "track volume leaves headroom for manual A/B matching",
                _HIGH_CONFIDENCE,
            ),
        ),
    ),
    _CandidateTemplate(
        column=2,
        label="Brighter sync",
        role="more metallic oscillator pressure",
        closeness=88,
        genes=(
            _PatchGeneTemplate(
                "OSC1 Level", 100, _OSC, "stronger oscillator A body", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC1 Pulsewidth", -24, _OSC, "narrower pulse increases buzz", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC2 Level", 62, _OSC, "louder oscillator B raises sync color", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC2 Pulsewidth",
                -30,
                _OSC,
                "offset width creates sharper beating",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Sync Amount", 78, _OSC, "higher sync pushes metallic edge", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Attack Time", 0, _MOD, "instant attack keeps bite", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Decay Time", 24, _MOD, "shorter decay tightens the stab", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Sustain Level", 0, _MOD, "zero sustain keeps it percussive", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Release Time", 6, _MOD, "short release avoids wash", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Env Shape", "triangle", _MOD, "neutral amp curve", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Attack Time", 0, _MOD, "filter opens immediately", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Decay Time", 34, _MOD, "compact filter sweep", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Sustain Level", 0, _MOD, "zero sustain closes the filter", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Release Time", 10, _MOD, "short filter tail", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Env Shape", "triangle", _MOD, "neutral filter curve", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed", 22, _MOD, "slightly quicker filter motion", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed Multiplier", "x1", _MOD, "keeps movement musical", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Waveform", "triangle", _MOD, "smooth repeating motion", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Depth A", 5, _MOD, "more audible filter animation", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Frequency", 82, _FX, "brighter first filter", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Resonance", 40, _FX, "more pronounced peak", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter Overdrive", 14, _FX, "extra harmonic bite", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Envelope Amount", 16, _FX, "snappier filter envelope", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Frequency", 96, _FX, "keeps top end open", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Resonance", 28, _FX, "clearer HP contour", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Type",
                "HP2",
                _FX,
                "same high-pass contour as the closest candidate",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Envelope Amount", 10, _FX, "small HP2 movement", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Delay Send Level", 18, _FX, "slightly wider echo space", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Reverb Send Level", 18, _FX, "less verb for a sharper front edge", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Volume", 92, _FX, "headroom for the brighter patch", _HIGH_CONFIDENCE
            ),
        ),
    ),
    _CandidateTemplate(
        column=3,
        label="Noisy texture",
        role="grain and movement emphasis",
        closeness=82,
        genes=(
            _PatchGeneTemplate(
                "OSC1 Level", 88, _OSC, "slightly lower oscillator body", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Noise Level", 26, _OSC, "adds controlled broadband texture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Noise Fade", 18, _OSC, "noise decays into the stab tail", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC1 Pulsewidth",
                -12,
                _OSC,
                "less narrow pulse leaves room for noise",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "OSC2 Level", 48, _OSC, "keeps oscillator B behind the texture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Sync Amount", 58, _OSC, "moderate sync under noise layer", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Attack Time", 0, _MOD, "instant texture onset", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Decay Time", 34, _MOD, "longer decay lets texture breathe", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Sustain Level", 0, _MOD, "still a stab, not a pad", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Release Time", 12, _MOD, "slightly longer release for grit", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Env Shape", "triangle", _MOD, "neutral amp shape", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Attack Time", 0, _MOD, "filter movement starts immediately", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Decay Time", 44, _MOD, "longer sweep exposes texture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Sustain Level", 0, _MOD, "filter closes after the hit", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Release Time",
                16,
                _MOD,
                "filter release follows the noisy tail",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "EnvF Env Shape", "triangle", _MOD, "neutral filter curve", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed", 14, _MOD, "slower wobble reads as drifting texture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed Multiplier", "x1", _MOD, "keeps the movement slow", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Waveform",
                "random",
                _MOD,
                "manual target for less periodic texture",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate("LFO1 Depth A", 4, _MOD, "subtle drift", _HIGH_CONFIDENCE),
            _PatchGeneTemplate(
                "Filter1 Frequency", 68, _FX, "slightly darker first filter", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Resonance", 30, _FX, "less peaky to let noise through", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter Overdrive", 8, _FX, "light saturation for grain", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Envelope Amount", 10, _FX, "small opening gesture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Frequency",
                78,
                _FX,
                "lower HP2 trims body but preserves texture",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Resonance", 20, _FX, "less resonance avoids whistling", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Type", "HP2", _FX, "high-pass texture contour", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Envelope Amount", 6, _FX, "light second-filter motion", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Delay Send Level", 22, _FX, "delay catches noisy grains", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Reverb Send Level", 30, _FX, "more space around texture", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Volume", 90, _FX, "headroom for noise and effects", _HIGH_CONFIDENCE
            ),
        ),
    ),
    _CandidateTemplate(
        column=4,
        label="Rounder bass",
        role="warmer low-mid translation",
        closeness=78,
        genes=(
            _PatchGeneTemplate(
                "OSC1 Level", 104, _OSC, "fuller oscillator A body", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC1 Pulsewidth", -6, _OSC, "wider pulse gives a rounder core", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "OSC2 Level",
                44,
                _OSC,
                "quieter oscillator B lowers metallic pressure",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "OSC2 Pulsewidth",
                -10,
                _OSC,
                "less offset keeps the sound smoother",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Sync Amount", 46, _OSC, "less sync for a rounder timbre", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate("EnvA Attack Time", 0, _MOD, "keeps onset tight", _HIGH_CONFIDENCE),
            _PatchGeneTemplate(
                "EnvA Decay Time", 42, _MOD, "slightly longer body", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Sustain Level", 0, _MOD, "still one-shot shaped", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Release Time", 14, _MOD, "rounder tail without pad smear", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvA Env Shape", "triangle", _MOD, "neutral amp shape", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Attack Time", 0, _MOD, "filter starts with transient", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Decay Time", 48, _MOD, "slower closure keeps low-mid warmth", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Sustain Level", 0, _MOD, "filter eventually closes", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Release Time", 18, _MOD, "warmer filter tail", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "EnvF Env Shape", "triangle", _MOD, "neutral filter curve", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed", 10, _MOD, "slower movement for bass support", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Speed Multiplier", "x1", _MOD, "keeps movement controlled", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Waveform", "triangle", _MOD, "smooth tonal drift", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "LFO1 Destination A",
                "Filter1 Frequency",
                _MOD,
                "front-panel filter target",
                _SCREEN_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "LFO1 Depth A", 2, _MOD, "tiny movement keeps bass stable", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Frequency", 58, _FX, "darker filter for warmer body", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Resonance", 26, _FX, "less peak for bass smoothness", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter Overdrive", 6, _FX, "mild saturation without harshness", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter1 Envelope Amount", 8, _FX, "small pluck remains audible", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Frequency", 70, _FX, "HP2 sits lower for weight control", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Resonance", 18, _FX, "subtle second-filter definition", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Filter2 Type",
                "HP2",
                _FX,
                "same high-pass cleanup, warmer setting",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Filter2 Envelope Amount", 4, _FX, "minimal HP movement", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Delay Send Level", 10, _FX, "keeps bass candidate dry", _HIGH_CONFIDENCE
            ),
            _PatchGeneTemplate(
                "Reverb Send Level",
                14,
                _FX,
                "minimal space for live low-end clarity",
                _HIGH_CONFIDENCE,
            ),
            _PatchGeneTemplate(
                "Volume", 96, _FX, "slightly louder warm candidate", _HIGH_CONFIDENCE
            ),
        ),
    ),
)


def build_analog_four_patch_genome(
    report: FeatureReport,
    *,
    track: int = 1,
    candidate_count: int = 4,
) -> AnalogFourPatchGenome:
    """Build a deterministic passive Analog Four patch genome."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    if track < ANALOG_FOUR_TRACK_MIN or track > ANALOG_FOUR_TRACK_MAX:
        raise ValueError("track must be in 1..4")
    if candidate_count < 1 or candidate_count > len(_CANDIDATE_TEMPLATES):
        raise ValueError("candidate_count must be in 1..4")

    settled_report = _settle_patch_genome_report_hash(report)
    blueprint = build_reference_style_blueprint(settled_report)
    candidates = tuple(
        _build_candidate(template, track=track)
        for template in _CANDIDATE_TEMPLATES[:candidate_count]
    )
    return AnalogFourPatchGenome(
        version=ANALOG_FOUR_PATCH_GENOME_VERSION,
        device_id=ANALOG_FOUR_DEVICE_ID,
        mode=ANALOG_FOUR_PATCH_MODE,
        selected_track=track,
        source_hash=settled_report.content_hash,
        source_confidence=settled_report.confidence,
        candidate_count=len(candidates),
        traits=blueprint.traits,
        candidates=candidates,
        safety=ANALOG_FOUR_PATCH_SAFETY,
    )


def analog_four_patch_genome_to_dict(
    genome: AnalogFourPatchGenome,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of ``genome``."""

    if not isinstance(genome, AnalogFourPatchGenome):
        raise TypeError("genome must be an AnalogFourPatchGenome")
    return {
        "version": genome.version,
        "device_id": genome.device_id,
        "mode": genome.mode,
        "selected_track": genome.selected_track,
        "source_hash": genome.source_hash,
        "source_confidence": genome.source_confidence.value,
        "candidate_count": genome.candidate_count,
        "traits": [_genome_trait_payload(trait) for trait in genome.traits],
        "candidates": [_candidate_payload(candidate) for candidate in genome.candidates],
        "safety": list(genome.safety),
    }


def analog_four_patch_candidate_to_dict(
    candidate: AnalogFourPatchCandidate,
) -> dict[str, object]:
    """Return a stable JSON-ready representation of ``candidate``."""

    if not isinstance(candidate, AnalogFourPatchCandidate):
        raise TypeError("candidate must be an AnalogFourPatchCandidate")
    return _candidate_payload(candidate)


def _settle_patch_genome_report_hash(report: FeatureReport) -> FeatureReport:
    digest = report.content_hash or compute_feature_report_hash(report)
    if digest == report.content_hash:
        return report
    return replace(report, content_hash=digest)


def _build_candidate(
    template: _CandidateTemplate,
    *,
    track: int,
) -> AnalogFourPatchCandidate:
    genes = tuple(
        sorted(
            (_build_gene(gene_template, track=track) for gene_template in template.genes),
            key=_gene_sort_key,
        )
    )
    return AnalogFourPatchCandidate(
        column=template.column,
        label=template.label,
        role=template.role,
        closeness=template.closeness,
        genes=genes,
    )


def _build_gene(
    template: _PatchGeneTemplate,
    *,
    track: int,
) -> AnalogFourPatchGene:
    return AnalogFourPatchGene(
        track=track,
        family=template.family,
        value=make_a4_patch_value(template.parameter, screen_target=template.screen_target),
        rationale=template.rationale,
        confidence=template.confidence,
    )


def _gene_sort_key(gene: AnalogFourPatchGene) -> tuple[int, str, str, str]:
    return (
        ANALOG_FOUR_PATCH_FAMILY_ORDER.index(gene.family),
        gene.value.section,
        gene.value.encoder,
        gene.value.parameter,
    )


def _genome_trait_payload(trait: ReferenceTrait) -> dict[str, object]:
    return {
        "key": trait.key,
        "label": trait.label,
        "intensity": trait.intensity,
        "evidence": list(trait.evidence),
    }


def _candidate_payload(candidate: AnalogFourPatchCandidate) -> dict[str, object]:
    return {
        "column": candidate.column,
        "label": candidate.label,
        "role": candidate.role,
        "closeness": candidate.closeness,
        "genes": [_gene_payload(gene) for gene in candidate.genes],
    }


def _gene_payload(gene: AnalogFourPatchGene) -> dict[str, object]:
    return {
        "track": gene.track,
        "family": gene.family,
        "rationale": gene.rationale,
        "confidence": gene.confidence,
        "value": _patch_value_payload(gene.value),
    }


def _patch_value_payload(value: AnalogFourPatchValue) -> dict[str, object]:
    return {
        "parameter": value.parameter,
        "section": value.section,
        "encoder": value.encoder,
        "screen_value": value.screen_value,
        "midi_value": value.midi_value,
        "cc_msb": value.cc_msb,
        "cc_lsb": value.cc_lsb,
        "nrpn_address": list(value.nrpn_address) if value.nrpn_address is not None else None,
        "transport_status": value.transport_status,
        "dial_direction": value.dial_direction,
    }


__all__ = [
    "ANALOG_FOUR_DEVICE_ID",
    "ANALOG_FOUR_PATCH_FAMILY_ORDER",
    "ANALOG_FOUR_PATCH_GENOME_VERSION",
    "ANALOG_FOUR_PATCH_MODE",
    "ANALOG_FOUR_PATCH_SAFETY",
    "AnalogFourPatchCandidate",
    "AnalogFourPatchGene",
    "AnalogFourPatchGenome",
    "analog_four_patch_candidate_to_dict",
    "analog_four_patch_genome_to_dict",
    "build_analog_four_patch_genome",
]
