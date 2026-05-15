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
algorithms (``librosa.beat.beat_track``, ``librosa.feature.spectral_centroid``,
RMS, onset rate). Same audio in -> same :class:`FeatureReport` out. The
non-audio path is deterministic by construction (it never reads audio).

Lazy-import discipline: ``librosa`` and ``numpy`` are imported INSIDE
function bodies, never at module top level. This matters because
``tests/architecture/test_no_side_effects.py`` runs subprocess imports
across the package and asserts no heavy deps land in ``sys.modules``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rytm_randomizer.guardrails.schema import Confidence, SourceType

from .feature_report import FeatureReport, compute_feature_report_hash


class StyleAnalysisDependencyError(RuntimeError):
    """Raised when an audio-extraction call needs ``librosa`` but it is missing.

    The package's core install does not require ``librosa`` -- the ``style``
    optional extra does (``pip install -e ".[style,dev]"``). The
    description-only path
    (:func:`extract_from_description`) never raises this; only the audio
    paths do.
    """


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


def _require_librosa() -> tuple[object, object]:
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
            "Install it with: pip install -e \".[style,dev]\""
        ) from exc
    return librosa, numpy  # pragma: no cover - requires librosa


def _normalize_unit(value: float) -> float:
    """Clamp ``value`` into ``[0.0, 1.0]`` so downstream code can trust the range."""

    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return float(value)


def _measure_audio_features(path: Path) -> dict[str, object]:  # pragma: no cover - requires librosa
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
    y, sr = librosa.load(str(path), sr=22050, mono=True)

    if len(y) == 0:
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
        }

    # Tempo + stability.
    # ``beat_track`` returns the global tempo + the per-frame beat indices;
    # the std-dev of the inter-beat interval is our stability proxy.
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo) if numpy.isfinite(tempo) else 0.0
    if len(beats) >= 3:
        ibi = numpy.diff(beats).astype(float)
        # Coefficient of variation (std / mean) -> tempo wobble. Lower is
        # steadier. We invert + clamp so the field reads "stability".
        mean_ibi = float(numpy.mean(ibi))
        if mean_ibi > 0:
            cv = float(numpy.std(ibi)) / mean_ibi
        else:
            cv = 1.0
        tempo_stability = _normalize_unit(1.0 - cv)
    else:
        tempo_stability = 0.0

    # Onset rate -> percussion density. Kick density is the share of
    # onset energy concentrated in the sub band (40-120Hz).
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    onsets = librosa.onset.onset_detect(onset_envelope=onset_env, sr=sr)
    duration = float(len(y)) / float(sr) if sr else 0.0
    if duration > 0:
        # Onsets per second; ~8 onsets/sec is "very dense" in techno.
        onsets_per_sec = float(len(onsets)) / duration
        percussion_density = _normalize_unit(onsets_per_sec / 8.0)
    else:
        percussion_density = 0.0

    # Spectral centroid -> brightness. Normalised against Nyquist.
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    centroid_mean = float(numpy.mean(centroid)) if centroid.size else 0.0
    nyquist = float(sr) / 2.0
    spectral_brightness = _normalize_unit(
        centroid_mean / nyquist if nyquist > 0 else 0.0
    )

    # Low-end weight from an STFT power band.
    stft = numpy.abs(librosa.stft(y))
    freqs = librosa.fft_frequencies(sr=sr)
    low_mask = freqs < 200.0
    total_energy = float(numpy.sum(stft))
    if total_energy > 0:
        low_energy = float(numpy.sum(stft[low_mask]))
        low_end_weight = _normalize_unit(low_energy / total_energy)
    else:
        low_end_weight = 0.0

    # Kick density: share of onsets that have strong sub-band content.
    if total_energy > 0 and len(onsets) > 0:
        # Coarse proxy: scale percussion density by low-end weight.
        kick_density = _normalize_unit(percussion_density * low_end_weight * 2.0)
    else:
        kick_density = 0.0

    # Texture / noise: spectral flatness near 1.0 means broadband noise.
    flatness = librosa.feature.spectral_flatness(y=y)
    flatness_mean = float(numpy.mean(flatness)) if flatness.size else 0.0
    texture_noise = _normalize_unit(flatness_mean)

    # Energy arc: 8 evenly-spaced RMS samples across the track. Captures
    # flat vs. building vs. peaked-and-dropped shape without storing the
    # full envelope.
    rms = librosa.feature.rms(y=y)[0]
    if rms.size >= 8:
        # Pick 8 evenly-spaced indices.
        idxs = numpy.linspace(0, rms.size - 1, num=8).astype(int)
        peak = float(numpy.max(rms))
        if peak > 0:
            arc = tuple(_normalize_unit(float(rms[i]) / peak) for i in idxs)
        else:
            arc = tuple(0.0 for _ in range(8))
    else:
        # Very short audio: pad with zeros so the shape stays stable.
        arc = tuple(
            float(rms[i]) if i < rms.size else 0.0 for i in range(8)
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
    }


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def extract_from_audio(path: Path) -> FeatureReport:
    """Extract a HIGH-confidence :class:`FeatureReport` from an audio file.

    Uses librosa for beat tracking, onset detection, spectral centroid,
    STFT-based low-end share, spectral flatness, and RMS energy arc. The
    measurement is deterministic across calls on the same file.

    Raises :class:`StyleAnalysisDependencyError` if ``librosa`` is not
    installed -- the ``style`` optional extra brings it in
    (``pip install -e ".[style,dev]"``).
    """

    if not isinstance(path, Path):
        raise TypeError("path must be a pathlib.Path")

    measurements = _measure_audio_features(path)
    report = FeatureReport(  # pragma: no cover - requires librosa
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=float(measurements["bpm"]),
        tempo_stability=float(measurements["tempo_stability"]),
        kick_density=float(measurements["kick_density"]),
        percussion_density=float(measurements["percussion_density"]),
        low_end_weight=float(measurements["low_end_weight"]),
        spectral_brightness=float(measurements["spectral_brightness"]),
        texture_noise=float(measurements["texture_noise"]),
        energy_arc=tuple(measurements["energy_arc"]),  # type: ignore[arg-type]
        content_hash="",
        derived_at=_now_iso(),
    )
    return _finalize(report)  # pragma: no cover - requires librosa


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

    if not isinstance(text, str):
        raise TypeError("text must be a string")
    if not isinstance(source_type, SourceType):
        raise TypeError("source_type must be a SourceType enum member")

    report = FeatureReport(
        source_type=source_type,
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


def extract_from_partial(
    paths: list[Path], notes: str
) -> FeatureReport:
    """Mix audio measurements with user notes -> MEDIUM confidence.

    Aggregates per-file features by deterministic median across
    ``paths``; ``notes`` is recorded as the documentation trail (the
    Layer 2 agent reads them when interpreting). If ``paths`` is empty,
    falls back to a description-only report tagged
    :attr:`Confidence.MEDIUM` rather than :attr:`Confidence.LOW`, since
    the user has nominated this as a partial-audio source.
    """

    if not isinstance(paths, list):
        raise TypeError("paths must be a list of Path objects")
    if not isinstance(notes, str):
        raise TypeError("notes must be a string")
    for p in paths:
        if not isinstance(p, Path):
            raise TypeError("every entry in paths must be a pathlib.Path")

    if not paths:
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
    _, numpy = _require_librosa()
    per_file = [_measure_audio_features(p) for p in paths]  # pragma: no cover - requires librosa
    aggregated = _aggregate_measurements(per_file, numpy)  # pragma: no cover - requires librosa

    report = FeatureReport(  # pragma: no cover - requires librosa
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.MEDIUM,
        bpm=float(aggregated["bpm"]),
        tempo_stability=float(aggregated["tempo_stability"]),
        kick_density=float(aggregated["kick_density"]),
        percussion_density=float(aggregated["percussion_density"]),
        low_end_weight=float(aggregated["low_end_weight"]),
        spectral_brightness=float(aggregated["spectral_brightness"]),
        texture_noise=float(aggregated["texture_noise"]),
        energy_arc=tuple(aggregated["energy_arc"]),  # type: ignore[arg-type]
        content_hash="",
        derived_at=_now_iso(),
    )
    return _finalize(report)  # pragma: no cover - requires librosa


def _aggregate_measurements(  # pragma: no cover - requires librosa-derived inputs
    per_file: list[dict[str, object]], numpy: object
) -> dict[str, object]:
    """Aggregate a list of per-file measurement dicts into one.

    Uses median across files for the scalar fields (deterministic,
    robust to outliers); element-wise mean for the energy arc so the
    library-level arc still shows shape.

    Coverage note: the aggregator is only ever called with measurements
    produced by :func:`_measure_audio_features`, which itself requires
    librosa -- hence the pragma. The librosa-gated tests exercise this
    function end-to-end on synthetic-signal fixtures.
    """

    # ``numpy`` here is the lazy-imported module from ``_require_librosa``.
    np = numpy

    scalar_fields = (
        "bpm",
        "tempo_stability",
        "kick_density",
        "percussion_density",
        "low_end_weight",
        "spectral_brightness",
        "texture_noise",
    )
    aggregated: dict[str, object] = {}
    for field_name in scalar_fields:
        values = [float(item[field_name]) for item in per_file]  # type: ignore[arg-type]
        aggregated[field_name] = float(np.median(values)) if values else 0.0

    # Element-wise mean of the energy arcs (they are length-8 tuples).
    arc_length = 8
    sums = [0.0] * arc_length
    count = max(1, len(per_file))
    for item in per_file:
        arc = item["energy_arc"]  # tuple[float, ...]
        for i in range(arc_length):
            sums[i] += float(arc[i])  # type: ignore[index]
    aggregated["energy_arc"] = tuple(sums[i] / count for i in range(arc_length))
    return aggregated


__all__ = [
    "StyleAnalysisDependencyError",
    "extract_from_audio",
    "extract_from_description",
    "extract_from_partial",
]
