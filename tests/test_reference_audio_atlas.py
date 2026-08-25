"""Tests for bounded long-form reference-audio atlas analysis."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.style_analysis import FeatureReport
from rytm_randomizer.style_analysis.reference_audio_atlas import (
    AudioDurationReader,
    AudioWindowExtractor,
    ReferenceAudioAtlasConfig,
    _build_window_specs,
    _select_distinct_windows,
    build_reference_audio_atlas,
    reference_audio_atlas_to_dict,
)

pytestmark = pytest.mark.fast


def _report(
    *,
    bpm: float = 120.0,
    low_end: float = 0.25,
    brightness: float = 0.25,
    texture: float = 0.25,
    derived_at: str = "2026-08-24T12:00:00Z",
    content_hash: str = "a" * 64,
) -> FeatureReport:
    return replace(
        analog_four_reference_feature_report(derived_at=derived_at),
        bpm=bpm,
        low_end_weight=low_end,
        spectral_brightness=brightness,
        texture_noise=texture,
        content_hash=content_hash,
    )


def test_atlas_decodes_bounded_windows_sequentially_and_honors_cap() -> None:
    calls: list[tuple[float, float]] = []

    def extract_window(
        _path: Path,
        *,
        offset_seconds: float,
        duration_seconds: float,
    ) -> FeatureReport:
        calls.append((offset_seconds, duration_seconds))
        return _report(bpm=120.0 + offset_seconds)

    atlas = build_reference_audio_atlas(
        Path("long-mix.wav"),
        config=ReferenceAudioAtlasConfig(
            window_seconds=20.0,
            hop_seconds=20.0,
            max_windows=3,
            max_moments=2,
            min_novelty=0.0,
        ),
        window_extractor=extract_window,
        duration_reader=lambda _path: 200.0,
    )

    assert calls == [(0.0, 20.0), (20.0, 20.0), (40.0, 20.0)]
    assert atlas.analyzed_windows == 3
    assert atlas.truncated is True
    assert len(atlas.moments) == 2


def test_atlas_selects_materially_distinct_windows_then_orders_them_by_time() -> None:
    reports = {
        0.0: _report(),
        30.0: _report(bpm=121.0, low_end=0.26),
        60.0: _report(bpm=180.0, low_end=0.95, brightness=0.9, texture=0.8),
    }

    def extract_window(
        _path: Path,
        *,
        offset_seconds: float,
        duration_seconds: float,
    ) -> FeatureReport:
        assert duration_seconds == 30.0
        return reports[offset_seconds]

    atlas = build_reference_audio_atlas(
        Path("long-mix.wav"),
        config=ReferenceAudioAtlasConfig(max_moments=2, min_novelty=0.08),
        window_extractor=extract_window,
        duration_reader=lambda _path: 90.0,
    )

    assert [moment.window_index for moment in atlas.moments] == [0, 2]
    assert [moment.sequence for moment in atlas.moments] == [1, 2]
    assert atlas.moments[0].novelty == 0.0
    assert atlas.moments[1].novelty >= 0.08
    assert atlas.moments[1].patch_genome.candidate_count == 4
    assert atlas.moments[1].blueprint.source_hash == reports[60.0].content_hash


def test_flat_audio_reduces_to_one_moment_at_positive_novelty_threshold() -> None:
    atlas = build_reference_audio_atlas(
        Path("steady-loop.wav"),
        config=ReferenceAudioAtlasConfig(max_moments=8, min_novelty=0.01),
        window_extractor=lambda _path, **_kwargs: _report(),
        duration_reader=lambda _path: 120.0,
    )

    assert atlas.analyzed_windows == 4
    assert len(atlas.moments) == 1


def test_analysis_id_ignores_provenance_time_and_hash_but_tracks_measurements() -> None:
    def build(*, derived_at: str, content_hash: str, bpm: float) -> str:
        atlas = build_reference_audio_atlas(
            Path("same-audio.wav"),
            window_extractor=lambda _path, **_kwargs: _report(
                bpm=bpm,
                derived_at=derived_at,
                content_hash=content_hash,
            ),
            duration_reader=lambda _path: 30.0,
        )
        return atlas.analysis_id

    first = build(
        derived_at="2026-08-24T12:00:00Z",
        content_hash="a" * 64,
        bpm=120.0,
    )
    second = build(
        derived_at="2026-08-24T13:00:00Z",
        content_hash="b" * 64,
        bpm=120.0,
    )
    changed = build(
        derived_at="2026-08-24T13:00:00Z",
        content_hash="b" * 64,
        bpm=121.0,
    )

    assert first == second
    assert first != changed


def test_atlas_payload_preserves_honest_scope_and_candidate_evidence() -> None:
    atlas = build_reference_audio_atlas(
        Path("reference.wav"),
        config=ReferenceAudioAtlasConfig(candidate_count=2),
        window_extractor=lambda _path, **_kwargs: _report(),
        duration_reader=lambda _path: 30.0,
    )

    payload = reference_audio_atlas_to_dict(atlas)
    moment = payload["moments"][0]

    assert payload["source_path"] == "reference.wav"
    assert payload["analysis_id"] == atlas.analysis_id
    assert "not stem separation" in " ".join(payload["safety"])
    assert moment["analog_four_patch_genome"]["candidate_count"] == 2
    assert moment["dual_device_blueprint"]["source_hash"] == "a" * 64


@pytest.mark.parametrize(
    ("overrides", "exception"),
    [
        ({"window_seconds": 4.9}, ValueError),
        ({"window_seconds": 121.0}, ValueError),
        ({"window_seconds": "30"}, TypeError),
        ({"hop_seconds": float("inf")}, ValueError),
        ({"max_windows": 0}, ValueError),
        ({"max_windows": True}, TypeError),
        ({"max_moments": 9}, ValueError),
        ({"min_novelty": -0.01}, ValueError),
        ({"track": 5}, ValueError),
        ({"candidate_count": 0}, ValueError),
    ],
)
def test_atlas_config_rejects_unbounded_or_invalid_values(
    overrides: dict[str, object],
    exception: type[Exception],
) -> None:
    with pytest.raises(exception):
        ReferenceAudioAtlasConfig(**overrides)


def test_atlas_rejects_short_audio_and_invalid_window_results() -> None:
    with pytest.raises(ValueError, match="at least 5 seconds"):
        build_reference_audio_atlas(
            Path("short.wav"),
            duration_reader=lambda _path: 4.99,
        )

    with pytest.raises(TypeError, match="window 0 at 0 seconds"):
        build_reference_audio_atlas(
            Path("bad.wav"),
            window_extractor=lambda _path, **_kwargs: object(),
            duration_reader=lambda _path: 30.0,
        )


def test_atlas_requires_typed_path_and_config() -> None:
    with pytest.raises(TypeError, match="path must be"):
        build_reference_audio_atlas("reference.wav")  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="config must be"):
        build_reference_audio_atlas(
            Path("reference.wav"),
            config=object(),  # type: ignore[arg-type]
        )

    with pytest.raises(TypeError, match="atlas must be"):
        reference_audio_atlas_to_dict(object())  # type: ignore[arg-type]


def test_atlas_internal_guards_reject_empty_window_sets() -> None:
    with pytest.raises(ValueError, match="no eligible analysis windows"):
        _build_window_specs(4.0, ReferenceAudioAtlasConfig())

    with pytest.raises(ValueError, match="windows must not be empty"):
        _select_distinct_windows((), max_moments=1, min_novelty=0.0)


def test_atlas_protocol_contract_bodies_are_passive_placeholders() -> None:
    assert (
        AudioWindowExtractor.__call__(
            object(),
            Path("reference.wav"),
            offset_seconds=0.0,
            duration_seconds=30.0,
        )
        is None
    )
    assert AudioDurationReader.__call__(object(), Path("reference.wav")) is None
