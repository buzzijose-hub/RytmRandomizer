"""Tests for bounded audio-window extraction primitives."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.style_analysis import extractor
from rytm_randomizer.style_analysis.extractor import AudioMeasurements

pytestmark = pytest.mark.fast


def _measurements() -> AudioMeasurements:
    return {
        "bpm": 138.0,
        "tempo_stability": 0.9,
        "kick_density": 0.4,
        "percussion_density": 0.7,
        "low_end_weight": 0.6,
        "spectral_brightness": 0.5,
        "texture_noise": 0.3,
        "energy_arc": (0.2, 0.4, 0.6),
        "duration": 1.0,
        "attack": 0.1,
        "decay": 0.2,
        "sustain": 0.5,
        "tail": 0.3,
        "spectral_flatness": 0.2,
        "noise": 0.3,
        "harmonicity": 0.8,
        "transient": 0.7,
        "modulation": 0.2,
        "dominant_frequency_hz": 87.31,
        "pitch_confidence": 0.8,
        "tonal_stability": 0.75,
        "spectral_movement": 0.15,
    }


def test_extract_audio_window_reuses_shared_measurement_core(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[Path, float, float | None]] = []

    def measure(
        source: Path,
        *,
        offset_seconds: float = 0.0,
        duration_seconds: float | None = None,
    ) -> AudioMeasurements:
        calls.append((source, offset_seconds, duration_seconds))
        return _measurements()

    monkeypatch.setattr(extractor, "_measure_audio_features", measure)

    report = extractor.extract_audio_window(
        Path("mix.wav"),
        offset_seconds=90.0,
        duration_seconds=30.0,
    )

    assert calls == [(Path("mix.wav"), 90.0, 30.0)]
    assert report.bpm == 138.0
    assert report.content_hash


def test_measurement_core_passes_bounded_decode_options_and_handles_empty_audio(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[object, dict[str, object]]] = []

    class FakeLibrosa:
        @staticmethod
        def load(source: object, **options: object) -> tuple[list[float], int]:
            calls.append((source, options))
            return [], 48_000

    monkeypatch.setattr(
        extractor,
        "_require_librosa",
        lambda: (cast(extractor._LibrosaApi, FakeLibrosa()), object()),
    )
    monkeypatch.setattr(extractor, "_flat_float_values", lambda *_args: [])

    measurements = extractor._measure_audio_features(
        Path("mix.wav"),
        offset_seconds=90.0,
        duration_seconds=30.0,
    )

    assert calls == [
        (
            "mix.wav",
            {"sr": 22_050, "mono": True, "offset": 90.0, "duration": 30.0},
        )
    ]
    assert measurements["duration"] == 0.0
    assert measurements["energy_arc"] == (0.0,) * 8


def test_get_audio_duration_uses_metadata_path_and_validates_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    class FakeLibrosa:
        @staticmethod
        def get_duration(*, path: str) -> float:
            calls.append(path)
            return 7_200.5

    monkeypatch.setattr(
        extractor,
        "_require_librosa",
        lambda: (cast(extractor._LibrosaApi, FakeLibrosa()), object()),
    )

    assert extractor.get_audio_duration(Path("mix.wav")) == 7_200.5
    assert calls == ["mix.wav"]


@pytest.mark.parametrize("duration", [0.0, -1.0, float("nan")])
def test_get_audio_duration_rejects_invalid_metadata(
    monkeypatch: pytest.MonkeyPatch,
    duration: float,
) -> None:
    class FakeLibrosa:
        @staticmethod
        def get_duration(*, path: str) -> float:
            del path
            return duration

    monkeypatch.setattr(
        extractor,
        "_require_librosa",
        lambda: (cast(extractor._LibrosaApi, FakeLibrosa()), object()),
    )

    with pytest.raises(ValueError, match="finite and positive"):
        extractor.get_audio_duration(Path("mix.wav"))


@pytest.mark.parametrize(
    ("offset", "duration", "message"),
    [
        (-1.0, 10.0, "offset_seconds"),
        (float("inf"), 10.0, "offset_seconds"),
        (0.0, 0.0, "duration_seconds"),
        (0.0, float("nan"), "duration_seconds"),
    ],
)
def test_measurement_core_rejects_invalid_window_bounds_before_importing_librosa(
    monkeypatch: pytest.MonkeyPatch,
    offset: float,
    duration: float,
    message: str,
) -> None:
    def unexpected_import() -> object:
        raise AssertionError("librosa must not be imported for invalid bounds")

    monkeypatch.setattr(extractor, "_require_librosa", unexpected_import)

    with pytest.raises(ValueError, match=message):
        extractor._measure_audio_features(
            Path("mix.wav"),
            offset_seconds=offset,
            duration_seconds=duration,
        )
