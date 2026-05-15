"""Library-level :class:`FeatureReport` aggregation.

A *library* is a directory of audio files (a folder of techno tools, the
user's release archive, a reference playlist). The library-level
:class:`FeatureReport` summarises the distribution of features across all
audio files in the directory using deterministic statistics: median for
each scalar field, element-wise mean for the energy arc.

Why median + element-wise mean: a single noisy outlier track (the
mastering test, the one ambient experiment in a techno set) cannot drag
the library's "typical" measurement off course (the median is robust);
the energy arc preserves the average shape so an interpreter can still
see whether the library leans flat or build-and-drop.

Audio file extensions recognised: ``.wav``, ``.aif``, ``.aiff``,
``.flac``, ``.mp3``. The walk is deterministic (sorted) so the produced
:class:`FeatureReport` is reproducible.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from rytm_randomizer.guardrails.schema import Confidence, SourceType

from .extractor import _aggregate_measurements, _measure_audio_features, _require_librosa
from .feature_report import FeatureReport, compute_feature_report_hash


_AUDIO_EXTENSIONS: tuple[str, ...] = (".wav", ".aif", ".aiff", ".flac", ".mp3")


def _now_iso() -> str:
    """Return an ISO 8601 UTC timestamp string."""

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _collect_audio_files(directory: Path) -> list[Path]:
    """Return every recognised audio file under ``directory``, sorted.

    Sorting makes the walk deterministic across machines / filesystems.
    Non-audio files are silently skipped (the extensions list is the
    filter).
    """

    out: list[Path] = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and path.suffix.lower() in _AUDIO_EXTENSIONS:
            out.append(path)
    return out


def analyze_library(directory: Path) -> FeatureReport:
    """Walk ``directory`` and aggregate per-file features into one report.

    The returned :class:`FeatureReport` carries
    :attr:`SourceType.FOLDER_LIBRARY` and :attr:`Confidence.HIGH` when at
    least one audio file was measured. An empty (or non-existent)
    directory returns a zeroed report tagged :attr:`Confidence.LOW` (we
    have no measurement to ground anything in).

    Raises :class:`~rytm_randomizer.style_analysis.extractor.
    StyleAnalysisDependencyError` (via the lazy import in the extractor)
    when audio files are present but ``librosa`` is missing.
    """

    if not isinstance(directory, Path):
        raise TypeError("directory must be a pathlib.Path")

    audio_files: list[Path] = []
    if directory.is_dir():
        audio_files = _collect_audio_files(directory)

    if not audio_files:
        # Empty library -> LOW-confidence zeroed report. The Layer 2 skill
        # treats this as a no-measurement input.
        report = FeatureReport(
            source_type=SourceType.FOLDER_LIBRARY,
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
        digest = compute_feature_report_hash(report)
        import dataclasses

        return dataclasses.replace(report, content_hash=digest)

    # Measure each file, aggregate.
    _, numpy = _require_librosa()
    per_file = [_measure_audio_features(p) for p in audio_files]  # pragma: no cover - requires librosa
    aggregated = _aggregate_measurements(per_file, numpy)  # pragma: no cover - requires librosa

    report = FeatureReport(  # pragma: no cover - requires librosa
        source_type=SourceType.FOLDER_LIBRARY,
        confidence=Confidence.HIGH,
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
    digest = compute_feature_report_hash(report)  # pragma: no cover - requires librosa
    import dataclasses  # pragma: no cover - requires librosa

    return dataclasses.replace(report, content_hash=digest)  # pragma: no cover - requires librosa


__all__ = ["analyze_library"]
