"""Bounded, passive analysis of distinct moments in long reference audio."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol

from .analog_four_patch_corpus import feature_distance
from .analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchGenome,
    analog_four_patch_genome_to_dict,
    build_analog_four_patch_genome,
)
from .blueprint import (
    ReferenceStyleBlueprint,
    build_reference_style_blueprint,
    reference_style_blueprint_to_dict,
)
from .extractor import extract_audio_window, get_audio_duration
from .feature_report import FeatureReport

REFERENCE_AUDIO_ATLAS_VERSION: Final[int] = 1
REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS: Final[float] = 5.0
REFERENCE_AUDIO_ATLAS_WINDOW_MAX_SECONDS: Final[float] = 120.0
REFERENCE_AUDIO_ATLAS_MAX_WINDOWS: Final[int] = 240
REFERENCE_AUDIO_ATLAS_MAX_MOMENTS: Final[int] = 8
REFERENCE_AUDIO_ATLAS_SAFETY: Final[tuple[str, ...]] = (
    "Audio is decoded sequentially in bounded windows; the complete waveform is not retained.",
    "This passive workflow does not enumerate or open MIDI ports.",
    "This passive workflow does not send MIDI or SysEx.",
    "Results are measured synthesis directions, not stem separation, forensic reconstruction, "
    "or claims about the original artist's equipment.",
)


class AudioWindowExtractor(Protocol):
    """Callable contract for one bounded audio-window measurement."""

    def __call__(
        self,
        path: Path,
        *,
        offset_seconds: float,
        duration_seconds: float,
    ) -> FeatureReport: ...


class AudioDurationReader(Protocol):
    """Callable contract for reading audio duration without a full decode."""

    def __call__(self, path: Path) -> float: ...


@dataclass(frozen=True)
class ReferenceAudioAtlasConfig:
    """Resource and selection bounds for one atlas analysis."""

    window_seconds: float = 30.0
    hop_seconds: float = 30.0
    max_windows: int = REFERENCE_AUDIO_ATLAS_MAX_WINDOWS
    max_moments: int = REFERENCE_AUDIO_ATLAS_MAX_MOMENTS
    min_novelty: float = 0.08
    track: int = ANALOG_FOUR_TRACK_MIN
    candidate_count: int = ANALOG_FOUR_PATCH_CANDIDATE_MAX

    def __post_init__(self) -> None:
        _require_finite_range(
            self.window_seconds,
            name="window_seconds",
            minimum=REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS,
            maximum=REFERENCE_AUDIO_ATLAS_WINDOW_MAX_SECONDS,
        )
        _require_finite_range(
            self.hop_seconds,
            name="hop_seconds",
            minimum=REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS,
            maximum=REFERENCE_AUDIO_ATLAS_WINDOW_MAX_SECONDS,
        )
        _require_int_range(
            self.max_windows,
            name="max_windows",
            minimum=1,
            maximum=REFERENCE_AUDIO_ATLAS_MAX_WINDOWS,
        )
        _require_int_range(
            self.max_moments,
            name="max_moments",
            minimum=1,
            maximum=REFERENCE_AUDIO_ATLAS_MAX_MOMENTS,
        )
        _require_finite_range(
            self.min_novelty,
            name="min_novelty",
            minimum=0.0,
            maximum=1.0,
        )
        _require_int_range(
            self.track,
            name="track",
            minimum=ANALOG_FOUR_TRACK_MIN,
            maximum=ANALOG_FOUR_TRACK_MAX,
        )
        _require_int_range(
            self.candidate_count,
            name="candidate_count",
            minimum=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
            maximum=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
        )


@dataclass(frozen=True)
class ReferenceAudioWindow:
    """One measured source window before novelty selection."""

    index: int
    start_seconds: float
    duration_seconds: float
    feature_report: FeatureReport


@dataclass(frozen=True)
class ReferenceAudioMoment:
    """One chronologically ordered, materially distinct atlas moment."""

    sequence: int
    window_index: int
    start_seconds: float
    end_seconds: float
    novelty: float
    feature_report: FeatureReport
    patch_genome: AnalogFourPatchGenome
    blueprint: ReferenceStyleBlueprint


@dataclass(frozen=True)
class ReferenceAudioAtlas:
    """Passive source-moment atlas with A4 candidates and dual-device traits."""

    version: int
    source_path: str
    duration_seconds: float
    window_seconds: float
    hop_seconds: float
    analyzed_windows: int
    truncated: bool
    moments: tuple[ReferenceAudioMoment, ...]
    analysis_id: str
    safety: tuple[str, ...]


def _require_atlas_path(value: object) -> Path:
    if not isinstance(value, Path):
        raise TypeError("path must be a pathlib.Path")
    return value


def _require_atlas_config(value: object) -> ReferenceAudioAtlasConfig:
    if not isinstance(value, ReferenceAudioAtlasConfig):
        raise TypeError("config must be a ReferenceAudioAtlasConfig")
    return value


def _require_atlas_feature_report(
    value: object,
    *,
    index: int,
    start_seconds: float,
) -> FeatureReport:
    if not isinstance(value, FeatureReport):
        raise TypeError(
            "window extractor must return a FeatureReport "
            f"for window {index} at {start_seconds:g} seconds"
        )
    return value


def _require_reference_audio_atlas(value: object) -> ReferenceAudioAtlas:
    if not isinstance(value, ReferenceAudioAtlas):
        raise TypeError("atlas must be a ReferenceAudioAtlas")
    return value


def build_reference_audio_atlas(
    path: Path,
    *,
    config: ReferenceAudioAtlasConfig | None = None,
    window_extractor: AudioWindowExtractor = extract_audio_window,
    duration_reader: AudioDurationReader = get_audio_duration,
) -> ReferenceAudioAtlas:
    """Measure bounded windows and build a deterministic distinct-moment atlas."""

    path = _require_atlas_path(path)
    settled_config = _require_atlas_config(config or ReferenceAudioAtlasConfig())

    duration_seconds = float(duration_reader(path))
    if (
        not math.isfinite(duration_seconds)
        or duration_seconds < REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS
    ):
        raise ValueError(
            "audio duration must be finite and at least "
            f"{REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS:.0f} seconds"
        )

    window_specs, truncated = _build_window_specs(duration_seconds, settled_config)
    measured_windows: list[ReferenceAudioWindow] = []
    for index, start_seconds, window_duration in window_specs:
        feature_report = _require_atlas_feature_report(
            window_extractor(
                path,
                offset_seconds=start_seconds,
                duration_seconds=window_duration,
            ),
            index=index,
            start_seconds=start_seconds,
        )
        measured_windows.append(
            ReferenceAudioWindow(
                index=index,
                start_seconds=start_seconds,
                duration_seconds=window_duration,
                feature_report=feature_report,
            )
        )
    windows = tuple(measured_windows)
    selected = _select_distinct_windows(
        windows,
        max_moments=settled_config.max_moments,
        min_novelty=settled_config.min_novelty,
    )
    moments = tuple(
        _build_moment(
            sequence=sequence,
            window=window,
            novelty=novelty,
            config=settled_config,
        )
        for sequence, (window, novelty) in enumerate(selected, start=1)
    )
    analysis_id = _build_analysis_id(
        duration_seconds=duration_seconds,
        config=settled_config,
        windows=windows,
        selected=selected,
    )
    return ReferenceAudioAtlas(
        version=REFERENCE_AUDIO_ATLAS_VERSION,
        source_path=str(path),
        duration_seconds=duration_seconds,
        window_seconds=settled_config.window_seconds,
        hop_seconds=settled_config.hop_seconds,
        analyzed_windows=len(windows),
        truncated=truncated,
        moments=moments,
        analysis_id=analysis_id,
        safety=REFERENCE_AUDIO_ATLAS_SAFETY,
    )


def reference_audio_atlas_to_dict(atlas: ReferenceAudioAtlas) -> dict[str, object]:
    """Return a stable JSON-ready atlas representation."""

    atlas = _require_reference_audio_atlas(atlas)
    return {
        "version": atlas.version,
        "source_path": atlas.source_path,
        "duration_seconds": atlas.duration_seconds,
        "window_seconds": atlas.window_seconds,
        "hop_seconds": atlas.hop_seconds,
        "analyzed_windows": atlas.analyzed_windows,
        "truncated": atlas.truncated,
        "analysis_id": atlas.analysis_id,
        "moments": [_moment_payload(moment) for moment in atlas.moments],
        "safety": list(atlas.safety),
    }


def _build_window_specs(
    duration_seconds: float,
    config: ReferenceAudioAtlasConfig,
) -> tuple[tuple[tuple[int, float, float], ...], bool]:
    minimum_tail = min(
        config.window_seconds,
        REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS,
    )
    specs: list[tuple[int, float, float]] = []
    for index in range(config.max_windows):
        start_seconds = index * config.hop_seconds
        remaining = duration_seconds - start_seconds
        if remaining < minimum_tail:
            break
        specs.append((index, start_seconds, min(config.window_seconds, remaining)))

    next_start = len(specs) * config.hop_seconds
    truncated = duration_seconds - next_start >= minimum_tail
    if not specs:
        raise ValueError("audio produced no eligible analysis windows")
    return tuple(specs), truncated


def _select_distinct_windows(
    windows: tuple[ReferenceAudioWindow, ...],
    *,
    max_moments: int,
    min_novelty: float,
) -> tuple[tuple[ReferenceAudioWindow, float], ...]:
    if not windows:
        raise ValueError("windows must not be empty")

    selected: list[tuple[ReferenceAudioWindow, float]] = [(windows[0], 0.0)]
    remaining = list(windows[1:])
    while remaining and len(selected) < max_moments:
        ranked = [
            (
                min(
                    feature_distance(candidate.feature_report, chosen.feature_report)
                    for chosen, _ in selected
                ),
                candidate,
            )
            for candidate in remaining
        ]
        novelty, candidate = max(ranked, key=lambda item: (item[0], -item[1].index))
        if novelty < min_novelty:
            break
        selected.append((candidate, novelty))
        remaining.remove(candidate)

    return tuple(sorted(selected, key=lambda item: item[0].index))


def _build_moment(
    *,
    sequence: int,
    window: ReferenceAudioWindow,
    novelty: float,
    config: ReferenceAudioAtlasConfig,
) -> ReferenceAudioMoment:
    return ReferenceAudioMoment(
        sequence=sequence,
        window_index=window.index,
        start_seconds=window.start_seconds,
        end_seconds=window.start_seconds + window.duration_seconds,
        novelty=novelty,
        feature_report=window.feature_report,
        patch_genome=build_analog_four_patch_genome(
            window.feature_report,
            track=config.track,
            candidate_count=config.candidate_count,
        ),
        blueprint=build_reference_style_blueprint(window.feature_report),
    )


def _build_analysis_id(
    *,
    duration_seconds: float,
    config: ReferenceAudioAtlasConfig,
    windows: tuple[ReferenceAudioWindow, ...],
    selected: tuple[tuple[ReferenceAudioWindow, float], ...],
) -> str:
    payload = {
        "version": REFERENCE_AUDIO_ATLAS_VERSION,
        "duration_seconds": duration_seconds,
        "config": {
            "window_seconds": config.window_seconds,
            "hop_seconds": config.hop_seconds,
            "max_windows": config.max_windows,
            "max_moments": config.max_moments,
            "min_novelty": config.min_novelty,
            "track": config.track,
            "candidate_count": config.candidate_count,
        },
        "windows": [
            {
                "index": window.index,
                "start_seconds": window.start_seconds,
                "duration_seconds": window.duration_seconds,
                "features": _stable_feature_payload(window.feature_report),
            }
            for window in windows
        ],
        "selected": [
            {"window_index": window.index, "novelty": novelty} for window, novelty in selected
        ],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _moment_payload(moment: ReferenceAudioMoment) -> dict[str, object]:
    return {
        "sequence": moment.sequence,
        "window_index": moment.window_index,
        "start_seconds": moment.start_seconds,
        "end_seconds": moment.end_seconds,
        "novelty": moment.novelty,
        "feature_report": _stable_feature_payload(moment.feature_report),
        "analog_four_patch_genome": analog_four_patch_genome_to_dict(moment.patch_genome),
        "dual_device_blueprint": reference_style_blueprint_to_dict(moment.blueprint),
    }


def _stable_feature_payload(report: FeatureReport) -> dict[str, object]:
    return {
        "source_type": report.source_type.value,
        "confidence": report.confidence.value,
        "bpm": report.bpm,
        "tempo_stability": report.tempo_stability,
        "kick_density": report.kick_density,
        "percussion_density": report.percussion_density,
        "low_end_weight": report.low_end_weight,
        "spectral_brightness": report.spectral_brightness,
        "texture_noise": report.texture_noise,
        "energy_arc": list(report.energy_arc),
    }


def _require_finite_range(
    value: object,
    *,
    name: str,
    minimum: float,
    maximum: float,
) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise TypeError(f"{name} must be numeric")
    if not math.isfinite(float(value)) or value < minimum or value > maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")


def _require_int_range(value: object, *, name: str, minimum: int, maximum: int) -> None:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an integer")
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be in {minimum}..{maximum}")


__all__ = [
    "REFERENCE_AUDIO_ATLAS_MAX_MOMENTS",
    "REFERENCE_AUDIO_ATLAS_MAX_WINDOWS",
    "REFERENCE_AUDIO_ATLAS_SAFETY",
    "REFERENCE_AUDIO_ATLAS_VERSION",
    "REFERENCE_AUDIO_ATLAS_WINDOW_MAX_SECONDS",
    "REFERENCE_AUDIO_ATLAS_WINDOW_MIN_SECONDS",
    "AudioDurationReader",
    "AudioWindowExtractor",
    "ReferenceAudioAtlas",
    "ReferenceAudioAtlasConfig",
    "ReferenceAudioMoment",
    "ReferenceAudioWindow",
    "build_reference_audio_atlas",
    "reference_audio_atlas_to_dict",
]
