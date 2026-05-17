import subprocess
import sys
from pathlib import Path

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _feature_report(**overrides):
    values = {
        "source_type": SourceType.SINGLE_TRACK,
        "confidence": Confidence.HIGH,
        "bpm": 134.0,
        "tempo_stability": 0.92,
        "kick_density": 0.72,
        "percussion_density": 0.82,
        "low_end_weight": 0.78,
        "spectral_brightness": 0.81,
        "texture_noise": 0.64,
        "energy_arc": (0.2, 0.3, 0.4, 0.6, 0.75, 0.8, 0.7, 0.6),
        "content_hash": "hash",
        "derived_at": "2026-05-16T12:00:00Z",
    }
    values.update(overrides)
    return FeatureReport(**values)


def test_importing_essence_tag_adapter_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.essence_tag_adapter; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules; "
                "assert 'librosa' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_description_derives_broad_essence_tags_without_copying_names():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_description

    tags = derive_essence_tags_from_description(
        "The Bells by Jeff Mills: metallic bell pressure, driving repetition, Detroit techno."
    )

    assert tags == (
        "metallic",
        "bell",
        "detroit",
        "driving",
        "pressure",
        "repetition",
    )
    assert "jeff" not in tags
    assert "mills" not in tags
    assert "the bells" not in tags


def test_description_derivation_is_deterministic_and_deduplicated():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_description

    first = derive_essence_tags_from_description("bell bells metallic metal bell")
    second = derive_essence_tags_from_description("metal bell metallic bells")

    assert first == ("metallic", "bell")
    assert second == ("metallic", "bell")


def test_description_derivation_rejects_non_string_input():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_description

    with pytest.raises(TypeError):
        derive_essence_tags_from_description(123)  # type: ignore[arg-type]


def test_feature_report_derives_essence_tags_from_measurements():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_feature_report

    tags = derive_essence_tags_from_feature_report(_feature_report())

    assert tags == (
        "driving",
        "repetition",
        "density",
        "low",
        "bright",
        "noise",
    )


def test_feature_report_and_description_tags_merge_in_stable_order():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_feature_report

    tags = derive_essence_tags_from_feature_report(
        _feature_report(spectral_brightness=0.2, texture_noise=0.1),
        description="raw metallic bell motion",
    )

    assert tags == (
        "metallic",
        "bell",
        "driving",
        "repetition",
        "density",
        "low",
        "raw",
        "motion",
    )


def test_feature_report_derivation_rejects_non_report_input():
    from rytm_randomizer.essence_tag_adapter import derive_essence_tags_from_feature_report

    with pytest.raises(TypeError):
        derive_essence_tags_from_feature_report(object())  # type: ignore[arg-type]
