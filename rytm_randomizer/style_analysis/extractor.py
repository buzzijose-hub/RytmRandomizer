"""Layer 1 extractor entry points - audio, description, partial.

This module exposes the three :class:`~rytm_randomizer.style_analysis.
feature_report.FeatureReport`-producing functions called out in
``GUARDRAILS_DESIGN_SPEC.md`` section 6.2:

* :func:`extract_from_audio` -- full deterministic extraction; confidence
  HIGH; requires the ``style`` optional extra (``librosa``).
* :func:`extract_from_description` -- description-only path; confidence
  LOW; no audio dependency.
* :func:`extract_from_partial` -- mixed audio + notes; confidence MEDIUM;
  requires the ``style`` optional extra.

Determinism guarantee: the audio paths use librosa's deterministic
algorithms (``librosa.onset.onset_detect``, ``librosa.feature.spectral_centroid``,
RMS, onset rate). Same audio in -> same :class:`FeatureReport` out. The
non-audio path is deterministic by construction (it never reads audio).

Lazy-import discipline: ``librosa`` and ``numpy`` are imported INSIDE
function bodies, never at module top level. This matters because
``tests/architecture/test_no_side_effects.py`` runs subprocess imports
across the package and asserts no heavy deps land in ``sys.modules``.
"""

from __future__ import annotations

import hashlib
import math
import statistics
import string
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import (
    ClassVar,
    Final,
    Literal,
    Protocol,
    SupportsFloat,
    TypedDict,
    cast,
)

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.observability.errors import DataError

from .feature_report import FeatureReport, compute_feature_report_hash
from .runtime_types import require_runtime_type

_AUDIO_SAMPLE_RATE: Final[int] = 22_050
_AUDIO_HOP_LENGTH: Final[int] = 512


class FeatureMeasurements(TypedDict):
    """Measured feature subset shared by single-file and library analysis."""

    bpm: float
    tempo_stability: float
    kick_density: float
    percussion_density: float
    low_end_weight: float
    spectral_brightness: float
    texture_noise: float
    energy_arc: tuple[float, ...]


class AudioMeasurements(FeatureMeasurements):
    """Complete deterministic measurement payload for one audio source."""

    duration: float
    attack: float
    decay: float
    sustain: float
    tail: float
    spectral_flatness: float
    noise: float
    harmonicity: float
    transient: float
    modulation: float
    dominant_frequency_hz: float
    pitch_confidence: float
    tonal_stability: float
    spectral_movement: float


def _require_path_list(value: object) -> list[Path]:
    if not isinstance(value, list):
        raise TypeError("paths must be a list of Path objects")
    raw_paths = cast(list[object], value)
    for path in raw_paths:
        if not isinstance(path, Path):
            raise TypeError("every entry in paths must be a pathlib.Path")
    return cast(list[Path], raw_paths)


_ScalarFeatureName = Literal[
    "bpm",
    "tempo_stability",
    "kick_density",
    "percussion_density",
    "low_end_weight",
    "spectral_brightness",
    "texture_noise",
]


class _ArrayResult(Protocol):
    reshape: Callable[..., _ArrayResult]
    tolist: Callable[[], object]


class _NumpyApi(Protocol):
    abs: Callable[..., object]
    asarray: Callable[..., _ArrayResult]


class _OnsetApi(Protocol):
    onset_strength: Callable[..., object]
    onset_detect: Callable[..., object]


class _FeatureApi(Protocol):
    spectral_centroid: Callable[..., object]
    spectral_flatness: Callable[..., object]
    rms: Callable[..., object]
    zero_crossing_rate: Callable[..., object]


class _LibrosaApi(Protocol):
    onset: _OnsetApi
    feature: _FeatureApi
    load: Callable[..., tuple[object, int]]
    stft: Callable[..., object]
    fft_frequencies: Callable[..., object]


@dataclass(frozen=True)
class AudioSynthesisFeatures:
    """Reusable normalized synthesis measurements from one audio decode."""

    audio_sha256: str
    duration: float
    attack: float
    decay: float
    sustain: float
    tail: float
    brightness: float
    spectral_flatness: float
    noise: float
    low_end: float
    harmonicity: float
    transient: float
    modulation: float

    def __post_init__(self) -> None:
        if len(self.audio_sha256) != 64 or any(
            character not in string.hexdigits for character in self.audio_sha256
        ):
            raise ValueError("audio_sha256 must be a 64-character hexadecimal digest")
        values = (
            self.duration,
            self.attack,
            self.decay,
            self.sustain,
            self.tail,
            self.brightness,
            self.spectral_flatness,
            self.noise,
            self.low_end,
            self.harmonicity,
            self.transient,
            self.modulation,
        )
        if any(not 0.0 <= value <= 1.0 for value in values):
            raise ValueError("audio feature values must be normalized to 0.0..1.0")


class AudioSynthesisFeaturesPayload(TypedDict):
    audio_sha256: str
    duration: float
    attack: float
    decay: float
    sustain: float
    tail: float
    brightness: float
    spectral_flatness: float
    noise: float
    low_end: float
    harmonicity: float
    transient: float
    modulation: float


@dataclass(frozen=True)
class AudioDnaEvidence:
    """Human-readable pitch and spectral evidence from one audio decode."""

    dominant_frequency_hz: float | None
    dominant_note: str | None
    pitch_confidence: float
    tonal_stability: float
    spectral_movement: float

    def __post_init__(self) -> None:
        if self.dominant_frequency_hz is not None and (
            not math.isfinite(self.dominant_frequency_hz) or self.dominant_frequency_hz <= 0.0
        ):
            raise ValueError("dominant_frequency_hz must be finite and positive")
        if self.dominant_note is not None and not self.dominant_note.strip():
            raise ValueError("dominant_note must be non-empty")
        normalized_values = (
            self.pitch_confidence,
            self.tonal_stability,
            self.spectral_movement,
        )
        if any(not 0.0 <= value <= 1.0 for value in normalized_values):
            raise ValueError("audio DNA evidence values must be normalized to 0.0..1.0")


class AudioDnaEvidencePayload(TypedDict):
    dominant_frequency_hz: float | None
    dominant_note: str | None
    pitch_confidence: float
    tonal_stability: float
    spectral_movement: float


EMPTY_AUDIO_DNA_EVIDENCE: Final[AudioDnaEvidence] = AudioDnaEvidence(
    dominant_frequency_hz=None,
    dominant_note=None,
    pitch_confidence=0.0,
    tonal_stability=0.0,
    spectral_movement=0.0,
)


@dataclass(frozen=True)
class AudioFeatureAnalysis:
    """One shared audio decode with report and synthesis-facing measurements."""

    feature_report: FeatureReport
    synthesis_features: AudioSynthesisFeatures
    dna_evidence: AudioDnaEvidence = EMPTY_AUDIO_DNA_EVIDENCE

    @property
    def audio_sha256(self) -> str:
        return self.synthesis_features.audio_sha256

    @property
    def duration(self) -> float:
        return self.synthesis_features.duration

    @property
    def attack(self) -> float:
        return self.synthesis_features.attack

    @property
    def decay(self) -> float:
        return self.synthesis_features.decay

    @property
    def sustain(self) -> float:
        return self.synthesis_features.sustain

    @property
    def tail(self) -> float:
        return self.synthesis_features.tail

    @property
    def brightness(self) -> float:
        return self.synthesis_features.brightness

    @property
    def spectral_flatness(self) -> float:
        return self.synthesis_features.spectral_flatness

    @property
    def noise(self) -> float:
        return self.synthesis_features.noise

    @property
    def low_end(self) -> float:
        return self.synthesis_features.low_end

    @property
    def harmonicity(self) -> float:
        return self.synthesis_features.harmonicity

    @property
    def transient(self) -> float:
        return self.synthesis_features.transient

    @property
    def modulation(self) -> float:
        return self.synthesis_features.modulation


def audio_synthesis_features_to_dict(
    features: AudioSynthesisFeatures,
) -> AudioSynthesisFeaturesPayload:
    """Return the stable JSON payload for reusable synthesis measurements."""

    validated_features = require_runtime_type(
        features,
        AudioSynthesisFeatures,
        "features must be AudioSynthesisFeatures",
    )
    return {
        "audio_sha256": validated_features.audio_sha256,
        "duration": validated_features.duration,
        "attack": validated_features.attack,
        "decay": validated_features.decay,
        "sustain": validated_features.sustain,
        "tail": validated_features.tail,
        "brightness": validated_features.brightness,
        "spectral_flatness": validated_features.spectral_flatness,
        "noise": validated_features.noise,
        "low_end": validated_features.low_end,
        "harmonicity": validated_features.harmonicity,
        "transient": validated_features.transient,
        "modulation": validated_features.modulation,
    }


def audio_dna_evidence_to_dict(evidence: AudioDnaEvidence) -> AudioDnaEvidencePayload:
    """Return the stable JSON payload for readable audio DNA evidence."""

    validated_evidence = require_runtime_type(
        evidence,
        AudioDnaEvidence,
        "evidence must be AudioDnaEvidence",
    )
    return {
        "dominant_frequency_hz": validated_evidence.dominant_frequency_hz,
        "dominant_note": validated_evidence.dominant_note,
        "pitch_confidence": validated_evidence.pitch_confidence,
        "tonal_stability": validated_evidence.tonal_stability,
        "spectral_movement": validated_evidence.spectral_movement,
    }


class StyleAnalysisDependencyError(DataError, RuntimeError):
    """Raised when an audio-extraction call needs ``librosa`` but it is missing.

    Multi-inheritance via ``DataError`` (the RytmRandomizerError taxonomy
    branch for missing-dependency / malformed-data conditions) keeps existing
    ``except RuntimeError`` callers working AND makes this a recognized
    taxonomy member for the observability conformance tests.

    The package's core install does not require ``librosa`` -- the ``style``
    optional extra does (``pip install -e ".[style,dev]"``). The
    description-only path
    (:func:`extract_from_description`) never raises this; only the audio
    paths do.
    """

    fingerprint: ClassVar[str] = "style.analysis.dependency_missing"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _now_iso() -> str:
    """Return an ISO 8601 timestamp string in UTC (``Z``-suffixed)."""

    # ``datetime.now(timezone.utc)`` is deterministic in shape (always
    # microsecond-precision); only its value is "now". Test paths that
    # need determinism construct reports directly with a fixed timestamp.
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _finalize(report_without_hash: FeatureReport) -> FeatureReport:
    """Compute the content hash and return a settled report.

    Two-pass construction so the hash describes the *content* of the
    report (everything except the hash field itself); identical to the
    pattern in
    :func:`rytm_randomizer.guardrails.schema.compute_content_hash`.
    """

    import dataclasses

    digest = compute_feature_report_hash(report_without_hash)
    return dataclasses.replace(report_without_hash, content_hash=digest)


def _require_librosa() -> tuple[_LibrosaApi, _NumpyApi]:
    """Lazy-import ``librosa`` + ``numpy``; raise if either is missing.

    Returns the modules so callers can use them without a second
    ``import`` statement. The import lives inside this function so
    ``import rytm_randomizer.style_analysis.extractor`` never pulls
    librosa into ``sys.modules``.
    """

    try:
        import librosa  # type: ignore[import-not-found]
        import numpy  # type: ignore[import-not-found]
    except ImportError as exc:
        raise StyleAnalysisDependencyError(
            "Audio feature extraction requires the 'style' optional extra. "
            'Install it with: pip install -e ".[style,dev]"'
        ) from exc
    return cast(_LibrosaApi, librosa), cast(_NumpyApi, numpy)


def require_audio_analysis_dependencies() -> None:
    """Validate that the optional audio-analysis dependencies are available."""

    _require_librosa()


def _flat_float_values(numpy: _NumpyApi, value: object) -> list[float]:
    raw = numpy.asarray(value).reshape(-1).tolist()
    if not isinstance(raw, list):
        raise TypeError("audio analysis array must serialize to a list")
    return [float(cast(SupportsFloat, item)) for item in cast(list[object], raw)]


def _matrix_float_values(numpy: _NumpyApi, value: object) -> list[list[float]]:
    raw = numpy.asarray(value).tolist()
    if not isinstance(raw, list):
        raise TypeError("audio analysis matrix must serialize to a list")
    rows: list[list[float]] = []
    for raw_row in cast(list[object], raw):
        if not isinstance(raw_row, list):
            raise TypeError("audio analysis matrix row must be a list")
        rows.append([float(cast(SupportsFloat, item)) for item in cast(list[object], raw_row)])
    return rows


def _normalize_unit(value: float) -> float:
    """Clamp ``value`` into ``[0.0, 1.0]`` so downstream code can trust the range."""

    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _audio_mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _audio_standard_deviation(values: list[float], mean: float) -> float:
    if not values:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return variance**0.5


def _audio_safe_ratio(numerator: float, denominator: float) -> float:
    if denominator <= 0.0:
        return 0.0
    return _normalize_unit(numerator / denominator)


def _audio_decay_frames(rms: list[float], peak_index: int, peak_rms: float) -> int:
    threshold = peak_rms * 0.37
    for index in range(peak_index, len(rms)):
        if rms[index] <= threshold:
            return index - peak_index
    return max(0, len(rms) - peak_index - 1)


def _audio_window_level(
    rms: list[float],
    peak_rms: float,
    start_fraction: float,
    end_fraction: float,
) -> float:
    if not rms or peak_rms <= 0.0:
        return 0.0
    start = min(len(rms) - 1, int(len(rms) * start_fraction))
    end = max(start + 1, min(len(rms), int(len(rms) * end_fraction)))
    return _normalize_unit(_audio_mean(rms[start:end]) / peak_rms)


def _first_finite(values: list[float]) -> float:
    return values[0] if values and math.isfinite(values[0]) else 0.0


def _tempo_stability(beats: list[float]) -> float:
    if len(beats) < 3:
        return 0.0
    intervals = [beats[index + 1] - beats[index] for index in range(len(beats) - 1)]
    mean_interval = _audio_mean(intervals)
    coefficient = (
        _audio_standard_deviation(intervals, mean_interval) / mean_interval
        if mean_interval > 0.0
        else 1.0
    )
    return _normalize_unit(1.0 - coefficient)


def _tempo_from_onsets(onsets: list[float], sample_rate: int) -> float:
    """Estimate a bounded tempo from median onset spacing."""

    if len(onsets) < 2 or sample_rate <= 0:
        return 0.0
    intervals = [
        (right - left) * _AUDIO_HOP_LENGTH / float(sample_rate)
        for left, right in zip(onsets, onsets[1:])
        if right > left
    ]
    if not intervals:
        return 0.0
    ordered = sorted(intervals)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    bpm = 60.0 / median
    while bpm > 200.0:
        bpm /= 2.0
    while 0.0 < bpm < 60.0:
        bpm *= 2.0
    return bpm


def _spectral_weights(
    magnitude: list[list[float]],
    frequencies: list[float],
    *,
    onset_count: int,
    percussion_density: float,
) -> tuple[float, float]:
    total_energy = sum(sum(row) for row in magnitude)
    if total_energy <= 0.0:
        return 0.0, 0.0
    low_energy = sum(
        sum(row)
        for frequency, row in zip(frequencies, magnitude, strict=False)
        if frequency < 200.0
    )
    low_end_weight = _normalize_unit(low_energy / total_energy)
    kick_density = (
        _normalize_unit(percussion_density * low_end_weight * 2.0) if onset_count > 0 else 0.0
    )
    return low_end_weight, kick_density


def _energy_arc(rms: list[float]) -> tuple[float, ...]:
    if len(rms) < 8:
        return tuple(rms[index] if index < len(rms) else 0.0 for index in range(8))
    indices = tuple(int(index * (len(rms) - 1) / 7) for index in range(8))
    peak = max(rms)
    if peak <= 0.0:
        return tuple(0.0 for _ in range(8))
    return tuple(_normalize_unit(rms[index] / peak) for index in indices)


def _dominant_frequency(
    magnitude: list[list[float]], frequencies: list[float]
) -> tuple[float, float]:
    candidates = tuple(
        (frequency, sum(row))
        for frequency, row in zip(frequencies, magnitude, strict=False)
        if 40.0 <= frequency <= 4_000.0
    )
    total_energy = sum(energy for _, energy in candidates)
    if total_energy <= 0.0:
        return 0.0, 0.0
    frequency, peak_energy = max(candidates, key=lambda candidate: candidate[1])
    return frequency, _normalize_unit(peak_energy / total_energy * 8.0)


def _frequency_to_note(frequency: float) -> str | None:
    if frequency <= 0.0 or not math.isfinite(frequency):
        return None
    midi_note = int(round(69.0 + 12.0 * math.log2(frequency / 440.0)))
    names = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
    return f"{names[midi_note % 12]}{midi_note // 12 - 1}"


def _spectral_movement(centroid: list[float], nyquist: float) -> float:
    if len(centroid) < 2 or nyquist <= 0.0:
        return 0.0
    differences = [abs(right - left) for left, right in zip(centroid, centroid[1:])]
    return _normalize_unit(_audio_mean(differences) / nyquist * 8.0)


def _measure_audio_features(source: Path | BytesIO) -> AudioMeasurements:
    """Return the raw measurement dict for a single audio file.

    Pulled out so :func:`extract_from_audio`, :func:`extract_from_partial`,
    and :func:`analyze_library` share the same deterministic measurement
    core. The function lazy-imports librosa via :func:`_require_librosa`.

    Coverage note: this function is gated on the optional ``style`` extra
    (librosa). It is exercised end-to-end by the
    ``test_extract_from_audio_runs_on_synthetic_signal`` tests when
    librosa is installed; in the librosa-less core install the
    :func:`_require_librosa` call raises before the rest runs, which is
    why the body carries a ``pragma: no cover`` marker.
    """

    librosa, numpy = _require_librosa()

    # ``mono=True`` and an explicit sample rate keep the measurement
    # deterministic across machines / librosa versions.
    decode_source = str(source) if isinstance(source, Path) else source
    y, sr = librosa.load(decode_source, sr=_AUDIO_SAMPLE_RATE, mono=True)
    samples = _flat_float_values(numpy, y)

    if not samples or sr <= 0:
        # Empty audio file -- defensive zero defaults.
        return {
            "bpm": 0.0,
            "tempo_stability": 0.0,
            "kick_density": 0.0,
            "percussion_density": 0.0,
            "low_end_weight": 0.0,
            "spectral_brightness": 0.0,
            "texture_noise": 0.0,
            "energy_arc": tuple(0.0 for _ in range(8)),
            "duration": 0.0,
            "attack": 0.0,
            "decay": 0.0,
            "sustain": 0.0,
            "tail": 0.0,
            "spectral_flatness": 0.0,
            "noise": 0.0,
            "harmonicity": 0.0,
            "transient": 0.0,
            "modulation": 0.0,
            "dominant_frequency_hz": 0.0,
            "pitch_confidence": 0.0,
            "tonal_stability": 0.0,
            "spectral_movement": 0.0,
        }

    # Onset spacing -> bounded tempo/stability. This avoids librosa's native
    # beat tracker, which is unstable for broadband noise on some Windows
    # scientific-Python builds.
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onset_values = _flat_float_values(numpy, onset_env)
    onsets = _flat_float_values(
        numpy,
        librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr),
    )
    bpm = _tempo_from_onsets(onsets, sr)
    tempo_stability = _tempo_stability(onsets)

    # Onset rate -> percussion density. Kick density is the share of
    # onset energy concentrated in the sub band (40-120Hz).
    duration = len(samples) / float(sr)
    # Onsets per second; ~8 onsets/sec is "very dense" in techno.
    onsets_per_sec = float(len(onsets)) / duration
    percussion_density = _normalize_unit(onsets_per_sec / 8.0)

    # Spectral centroid -> brightness. Normalised against Nyquist.
    centroid = _flat_float_values(numpy, librosa.feature.spectral_centroid(y=y, sr=sr))
    centroid_mean = _audio_mean(centroid)
    nyquist = float(sr) / 2.0
    spectral_brightness = _normalize_unit(centroid_mean / nyquist if nyquist > 0 else 0.0)

    # Low-end weight from an STFT power band.
    stft = _matrix_float_values(numpy, numpy.abs(librosa.stft(y)))
    freqs = _flat_float_values(numpy, librosa.fft_frequencies(sr=sr))
    low_end_weight, kick_density = _spectral_weights(
        stft,
        freqs,
        onset_count=len(onsets),
        percussion_density=percussion_density,
    )

    # Texture / noise: spectral flatness near 1.0 means broadband noise.
    flatness = _flat_float_values(numpy, librosa.feature.spectral_flatness(y=y))
    flatness_mean = _audio_mean(flatness)
    texture_noise = _normalize_unit(flatness_mean)

    # Energy arc: 8 evenly-spaced RMS samples across the track. Captures
    # flat vs. building vs. peaked-and-dropped shape without storing the
    # full envelope.
    rms = _flat_float_values(numpy, librosa.feature.rms(y=y))
    arc = _energy_arc(rms)

    rms_values = rms
    peak_rms = max(rms_values, default=0.0)
    peak_index = rms_values.index(peak_rms) if peak_rms > 0.0 else 0
    attack_seconds = peak_index * _AUDIO_HOP_LENGTH / float(sr)
    decay_seconds = (
        _audio_decay_frames(rms_values, peak_index, peak_rms) * _AUDIO_HOP_LENGTH / float(sr)
    )
    sustain = _audio_window_level(rms_values, peak_rms, 0.40, 0.75)
    tail = _audio_window_level(rms_values, peak_rms, 0.80, 1.00)
    zero_crossings = _flat_float_values(numpy, librosa.feature.zero_crossing_rate(y))
    zero_crossing_mean = _audio_mean(zero_crossings)
    noise = _normalize_unit(flatness_mean * 0.75 + zero_crossing_mean * 0.25)
    # Spectral concentration is a stable proxy for harmonicity and avoids
    # native HPSS code paths that can terminate the process on broadband noise.
    harmonicity = _normalize_unit(1.0 - flatness_mean)
    dominant_frequency_hz, pitch_confidence = _dominant_frequency(stft, freqs)
    spectral_movement = _spectral_movement(centroid, nyquist)
    tonal_stability = _normalize_unit(harmonicity * (1.0 - spectral_movement))
    transient = _audio_safe_ratio(
        _audio_mean(onset_values),
        max(onset_values, default=0.0),
    )
    rms_mean = _audio_mean(rms_values)
    modulation = _normalize_unit(
        _audio_standard_deviation(rms_values, rms_mean) / max(rms_mean, 1e-12) / 2.0
    )

    return {
        "bpm": bpm,
        "tempo_stability": tempo_stability,
        "kick_density": kick_density,
        "percussion_density": percussion_density,
        "low_end_weight": low_end_weight,
        "spectral_brightness": spectral_brightness,
        "texture_noise": texture_noise,
        "energy_arc": arc,
        "duration": _normalize_unit(duration / 8.0),
        "attack": _normalize_unit(attack_seconds / 2.0),
        "decay": _normalize_unit(decay_seconds / 4.0),
        "sustain": sustain,
        "tail": tail,
        "spectral_flatness": flatness_mean,
        "noise": noise,
        "harmonicity": harmonicity,
        "transient": transient,
        "modulation": modulation,
        "dominant_frequency_hz": dominant_frequency_hz,
        "pitch_confidence": pitch_confidence,
        "tonal_stability": tonal_stability,
        "spectral_movement": spectral_movement,
    }


def measure_audio_features(source: Path | BytesIO) -> AudioMeasurements:
    """Measure one audio source through the shared deterministic extractor."""

    return _measure_audio_features(source)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def _audio_feature_report(measurements: AudioMeasurements) -> FeatureReport:
    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=measurements["bpm"],
        tempo_stability=measurements["tempo_stability"],
        kick_density=measurements["kick_density"],
        percussion_density=measurements["percussion_density"],
        low_end_weight=measurements["low_end_weight"],
        spectral_brightness=measurements["spectral_brightness"],
        texture_noise=measurements["texture_noise"],
        energy_arc=measurements["energy_arc"],
        content_hash="",
        derived_at=_now_iso(),
    )
    return _finalize(report)


def _audio_feature_analysis(
    *,
    audio_sha256: str,
    measurements: AudioMeasurements,
) -> AudioFeatureAnalysis:
    dominant_frequency_hz = measurements.get("dominant_frequency_hz", 0.0)
    return AudioFeatureAnalysis(
        feature_report=_audio_feature_report(measurements),
        synthesis_features=AudioSynthesisFeatures(
            audio_sha256=audio_sha256,
            duration=measurements["duration"],
            attack=measurements["attack"],
            decay=measurements["decay"],
            sustain=measurements["sustain"],
            tail=measurements["tail"],
            brightness=measurements["spectral_brightness"],
            spectral_flatness=measurements["spectral_flatness"],
            noise=measurements["noise"],
            low_end=measurements["low_end_weight"],
            harmonicity=measurements["harmonicity"],
            transient=measurements["transient"],
            modulation=measurements["modulation"],
        ),
        dna_evidence=AudioDnaEvidence(
            dominant_frequency_hz=(dominant_frequency_hz if dominant_frequency_hz > 0.0 else None),
            dominant_note=_frequency_to_note(dominant_frequency_hz),
            pitch_confidence=measurements.get("pitch_confidence", 0.0),
            tonal_stability=measurements.get("tonal_stability", 0.0),
            spectral_movement=measurements.get("spectral_movement", 0.0),
        ),
    )


def analyze_audio_snapshot(path: Path) -> AudioFeatureAnalysis:
    """Analyze a stable, caller-owned audio snapshot without copying it.

    This entry point exists for process-isolated product workflows. The
    caller must keep ``path`` immutable and alive for the complete call.
    No temporary path is created here, so a native decoder crash cannot
    strand an additional child-owned copy of private audio.
    """

    validated_path = require_runtime_type(
        path,
        Path,
        "path must be a pathlib.Path",
    )

    audio_bytes = validated_path.read_bytes()
    audio_sha256 = hashlib.sha256(audio_bytes).hexdigest()
    return _audio_feature_analysis(
        audio_sha256=audio_sha256,
        measurements=_measure_audio_features(BytesIO(audio_bytes)),
    )


def analyze_audio(path: Path) -> AudioFeatureAnalysis:
    """Decode one audio file into a report and reusable synthesis measurements.

    Uses librosa for beat tracking, onset detection, spectral centroid,
    STFT-based low-end share, spectral flatness, and RMS energy arc. The
    waveform is decoded once and shared by all measurements.

    Raises :class:`StyleAnalysisDependencyError` if ``librosa`` is not
    installed -- the ``style`` optional extra brings it in
    (``pip install -e ".[style,dev]"``).
    """

    validated_path = require_runtime_type(
        path,
        Path,
        "path must be a pathlib.Path",
    )

    audio_bytes = validated_path.read_bytes()
    audio_sha256 = hashlib.sha256(audio_bytes).hexdigest()
    with tempfile.TemporaryDirectory(prefix="style-audio-analysis-") as temp_name:
        snapshot = Path(temp_name) / f"audio{validated_path.suffix or '.bin'}"
        snapshot.write_bytes(audio_bytes)
        measurements = _measure_audio_features(snapshot)
    return _audio_feature_analysis(
        audio_sha256=audio_sha256,
        measurements=measurements,
    )


def extract_from_audio(path: Path) -> FeatureReport:
    """Extract a HIGH-confidence :class:`FeatureReport` from an audio file."""

    return analyze_audio(path).feature_report


def extract_from_description(
    text: str, source_type: SourceType = SourceType.STYLE_DESCRIPTION_ONLY
) -> FeatureReport:
    """Construct a LOW-confidence :class:`FeatureReport` from a description.

    No audio is read; ``librosa`` is NOT required. All numeric fields are
    zeroed placeholders -- the interpretation skill (Layer 2) fills in the
    mutation intent from the description text directly. The
    :attr:`Confidence.LOW` tag tells downstream layers to treat the
    profile conservatively (it cannot reach LIVE_APPROVED without
    hardware validation in lieu of the missing audio measurement).
    """

    require_runtime_type(text, str, "text must be a string")
    validated_source_type = require_runtime_type(
        source_type,
        SourceType,
        "source_type must be a SourceType enum member",
    )

    report = FeatureReport(
        source_type=validated_source_type,
        confidence=Confidence.LOW,
        bpm=0.0,
        tempo_stability=0.0,
        kick_density=0.0,
        percussion_density=0.0,
        low_end_weight=0.0,
        spectral_brightness=0.0,
        texture_noise=0.0,
        energy_arc=tuple(0.0 for _ in range(8)),
        content_hash="",
        derived_at=_now_iso(),
    )
    return _finalize(report)


def extract_from_partial(paths: list[Path], notes: str) -> FeatureReport:
    """Mix audio measurements with user notes -> MEDIUM confidence.

    Aggregates per-file features by deterministic median across
    ``paths``; ``notes`` is recorded as the documentation trail (the
    Layer 2 agent reads them when interpreting). If ``paths`` is empty,
    falls back to a description-only report tagged
    :attr:`Confidence.MEDIUM` rather than :attr:`Confidence.LOW`, since
    the user has nominated this as a partial-audio source.
    """

    validated_paths = _require_path_list(paths)
    require_runtime_type(notes, str, "notes must be a string")

    if not validated_paths:
        report = FeatureReport(
            source_type=SourceType.SINGLE_TRACK,
            confidence=Confidence.MEDIUM,
            bpm=0.0,
            tempo_stability=0.0,
            kick_density=0.0,
            percussion_density=0.0,
            low_end_weight=0.0,
            spectral_brightness=0.0,
            texture_noise=0.0,
            energy_arc=tuple(0.0 for _ in range(8)),
            content_hash="",
            derived_at=_now_iso(),
        )
        return _finalize(report)

    # Audio present -> measure each file, aggregate.
    _require_librosa()
    per_file = [_measure_audio_features(p) for p in validated_paths]
    aggregated = _aggregate_measurements(per_file)

    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=aggregated["bpm"],
        tempo_stability=aggregated["tempo_stability"],
        kick_density=aggregated["kick_density"],
        percussion_density=aggregated["percussion_density"],
        low_end_weight=aggregated["low_end_weight"],
        spectral_brightness=aggregated["spectral_brightness"],
        texture_noise=aggregated["texture_noise"],
        energy_arc=aggregated["energy_arc"],
        content_hash="",
        derived_at=_now_iso(),
    )
    return _finalize(report)


def _aggregate_measurements(
    per_file: list[AudioMeasurements],
) -> FeatureMeasurements:
    """Aggregate a list of per-file measurement dicts into one.

    Uses median across files for the scalar fields (deterministic,
    robust to outliers); element-wise mean for the energy arc so the
    library-level arc still shows shape.

    Coverage note: the aggregator is only ever called with measurements
    produced by :func:`_measure_audio_features`, which itself requires
    librosa -- hence the pragma. The librosa-gated tests exercise this
    function end-to-end on synthetic-signal fixtures.
    """

    def field_median(field_name: _ScalarFeatureName) -> float:
        values = [item[field_name] for item in per_file]
        return float(statistics.median(values)) if values else 0.0

    # Element-wise mean of the energy arcs (they are length-8 tuples).
    arc_length = 8
    sums = [0.0] * arc_length
    count = max(1, len(per_file))
    for item in per_file:
        arc = item["energy_arc"]  # tuple[float, ...]
        for i in range(arc_length):
            sums[i] += float(arc[i])  # type: ignore[index]
    return {
        "bpm": field_median("bpm"),
        "tempo_stability": field_median("tempo_stability"),
        "kick_density": field_median("kick_density"),
        "percussion_density": field_median("percussion_density"),
        "low_end_weight": field_median("low_end_weight"),
        "spectral_brightness": field_median("spectral_brightness"),
        "texture_noise": field_median("texture_noise"),
        "energy_arc": tuple(sums[index] / count for index in range(arc_length)),
    }


def aggregate_audio_measurements(
    per_file: list[AudioMeasurements],
) -> FeatureMeasurements:
    """Aggregate deterministic measurements without exposing private helpers."""

    return _aggregate_measurements(per_file)


def clamp_audio_feature_unit(value: float) -> float:
    """Clamp one normalized audio feature to the closed unit interval."""

    return max(0.0, min(1.0, float(value)))


__all__ = [
    "AudioDnaEvidence",
    "AudioDnaEvidencePayload",
    "AudioMeasurements",
    "AudioFeatureAnalysis",
    "AudioSynthesisFeatures",
    "AudioSynthesisFeaturesPayload",
    "FeatureMeasurements",
    "StyleAnalysisDependencyError",
    "analyze_audio",
    "analyze_audio_snapshot",
    "aggregate_audio_measurements",
    "audio_dna_evidence_to_dict",
    "audio_synthesis_features_to_dict",
    "clamp_audio_feature_unit",
    "extract_from_audio",
    "extract_from_description",
    "extract_from_partial",
    "_first_finite",
    "measure_audio_features",
    "require_audio_analysis_dependencies",
]
