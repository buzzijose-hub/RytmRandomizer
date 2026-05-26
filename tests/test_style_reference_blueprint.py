from __future__ import annotations

import json
from dataclasses import replace

import pytest

from rytm_randomizer.reports import reference_style_blueprint as report_module
from rytm_randomizer.style_analysis import (
    Confidence,
    FeatureReport,
    SourceType,
)
from rytm_randomizer.style_analysis import blueprint as blueprint_module
from rytm_randomizer.style_analysis import (
    build_reference_style_blueprint,
    compute_feature_report_hash,
    reference_style_blueprint_to_dict,
)

pytestmark = pytest.mark.fast


def _report(
    *,
    source_type: SourceType = SourceType.SINGLE_TRACK,
    confidence: Confidence = Confidence.HIGH,
    kick_density: float = 0.72,
    percussion_density: float = 0.78,
    low_end_weight: float = 0.82,
    spectral_brightness: float = 0.74,
    texture_noise: float = 0.68,
    energy_arc: tuple[float, ...] = (0.28, 0.42, 0.71, 0.86),
) -> FeatureReport:
    report = FeatureReport(
        source_type=source_type,
        confidence=confidence,
        bpm=139.4,
        tempo_stability=0.81,
        kick_density=kick_density,
        percussion_density=percussion_density,
        low_end_weight=low_end_weight,
        spectral_brightness=spectral_brightness,
        texture_noise=texture_noise,
        energy_arc=energy_arc,
        content_hash="",
        derived_at="2026-05-26T00:00:00+00:00",
    )
    return replace(report, content_hash=compute_feature_report_hash(report))


def test_reference_style_blueprint_maps_reference_features_to_all_tracks() -> None:
    blueprint = build_reference_style_blueprint(_report())

    assert blueprint.readiness == "mock_safe"
    assert blueprint.source_hash
    assert blueprint.influence_rule == "inspired-starting-point-not-replica"
    assert len(blueprint.traits) >= 5
    assert len(blueprint.rytm_pads) == 12
    assert len(blueprint.analog_four_tracks) == 4
    assert {pad.pad for pad in blueprint.rytm_pads} == set(range(1, 13))
    assert {track.track for track in blueprint.analog_four_tracks} == set(range(1, 5))

    pad_1 = blueprint.rytm_pads[0]
    pad_11 = blueprint.rytm_pads[10]
    track_1 = blueprint.analog_four_tracks[0]
    track_2 = blueprint.analog_four_tracks[1]

    assert pad_1.role == "kick foundation"
    assert pad_1.engine_family == "BD Hard / low-end anchor"
    assert "SRC Tune" in pad_1.parameter_focus
    assert pad_11.engine_family == "SY Raw / metallic texture"
    assert "LFO Depth" in pad_11.parameter_focus
    assert track_1.voice_intent == "sub bass movement"
    assert "Filter 1 Frequency" in track_1.parameter_focus
    assert track_2.voice_intent == "metallic stab"
    assert "Oscillator Sync" in track_2.parameter_focus


def test_reference_style_blueprint_stays_conservative_for_low_confidence_sources() -> None:
    blueprint = build_reference_style_blueprint(
        _report(
            confidence=Confidence.LOW,
            kick_density=0.0,
            percussion_density=0.0,
            low_end_weight=0.0,
            spectral_brightness=0.0,
            texture_noise=0.0,
            energy_arc=(),
        )
    )

    assert blueprint.readiness == "mock_safe_low_confidence"
    assert max(pad.mutation_depth for pad in blueprint.rytm_pads) <= 2
    assert max(track.mutation_depth for track in blueprint.analog_four_tracks) <= 2
    assert "no MIDI port opened" in blueprint.safety
    assert "no MIDI sent" in blueprint.safety
    assert "hardware entrypoint remains locked" in blueprint.safety


def test_reference_style_blueprint_is_deterministic_and_sensitive_to_features() -> None:
    report = _report()
    brighter_report = _report(spectral_brightness=0.92)

    first = build_reference_style_blueprint(report)
    second = build_reference_style_blueprint(report)
    brighter = build_reference_style_blueprint(brighter_report)

    assert first == second
    assert first.blueprint_hash == second.blueprint_hash
    assert first.blueprint_hash != brighter.blueprint_hash

    first_metallic = next(trait for trait in first.traits if trait.key == "metallic_pressure")
    brighter_metallic = next(trait for trait in brighter.traits if trait.key == "metallic_pressure")
    assert brighter_metallic.intensity > first_metallic.intensity


def test_reference_style_blueprint_dict_is_json_ready() -> None:
    blueprint = build_reference_style_blueprint(_report())
    payload = reference_style_blueprint_to_dict(blueprint)

    encoded = json.dumps(payload, sort_keys=True)

    assert "BD Hard / low-end anchor" in encoded
    assert payload["source_confidence"] == "HIGH"
    assert payload["readiness"] == "mock_safe"
    assert payload["rytm_pads"][0]["pad"] == 1
    assert payload["analog_four_tracks"][0]["track"] == 1


def test_reference_style_blueprint_rejects_invalid_inputs() -> None:
    with pytest.raises(TypeError):
        build_reference_style_blueprint(object())  # type: ignore[arg-type]

    with pytest.raises(TypeError):
        reference_style_blueprint_to_dict(object())  # type: ignore[arg-type]


def test_reference_style_blueprint_settles_missing_source_hash() -> None:
    report = replace(_report(), content_hash="")
    blueprint = build_reference_style_blueprint(report)

    assert blueprint.source_hash == compute_feature_report_hash(report)


def test_reference_style_blueprint_depth_caps_cover_high_and_medium() -> None:
    high_report = _report(
        confidence=Confidence.HIGH,
        kick_density=1.0,
        percussion_density=1.0,
        low_end_weight=1.0,
        spectral_brightness=1.0,
        texture_noise=1.0,
        energy_arc=(1.0, 1.0),
    )
    medium_report = replace(high_report, confidence=Confidence.MEDIUM, content_hash="")
    medium_report = replace(
        medium_report,
        content_hash=compute_feature_report_hash(medium_report),
    )

    high = build_reference_style_blueprint(high_report)
    medium = build_reference_style_blueprint(medium_report)

    assert high.rytm_pads[0].mutation_depth == 6
    assert max(pad.mutation_depth for pad in medium.rytm_pads) <= 4


def test_reference_style_blueprint_numeric_helpers_cover_bounds() -> None:
    assert blueprint_module._average() == 0.0
    assert blueprint_module._arrangement_energy(()) == 0.0
    assert blueprint_module._arrangement_energy((0.5,)) > 0.0
    assert blueprint_module._tempo_drive(0.0) == 0.0
    assert blueprint_module._clamp_unit(-0.1) == 0.0
    assert blueprint_module._clamp_unit(1.1) == 1.0


def test_reference_style_blueprint_report_source_branches(monkeypatch: pytest.MonkeyPatch) -> None:
    audio_report = replace(
        _report(source_type=SourceType.SINGLE_TRACK),
        content_hash="",
    )
    audio_report = replace(audio_report, content_hash=compute_feature_report_hash(audio_report))
    library_report = replace(
        _report(source_type=SourceType.FOLDER_LIBRARY),
        content_hash="",
    )
    library_report = replace(
        library_report,
        content_hash=compute_feature_report_hash(library_report),
    )

    monkeypatch.setattr(report_module, "extract_from_audio", lambda path: audio_report)
    monkeypatch.setattr(report_module, "analyze_library", lambda path: library_report)

    audio = report_module.build_reference_style_blueprint_from_source("--audio", "song.wav")
    library = report_module.build_reference_style_blueprint_from_source("--library", "folder")

    assert audio.source_type is SourceType.SINGLE_TRACK
    assert library.source_type is SourceType.FOLDER_LIBRARY
    with pytest.raises(ValueError):
        report_module.build_reference_style_blueprint_from_source("--bad", "value")


def test_reference_style_blueprint_report_parser_errors() -> None:
    with pytest.raises(ValueError, match="requires a value"):
        report_module._parse_reference_style_blueprint_args(["--audio"])

    with pytest.raises(ValueError, match="unknown argument"):
        report_module._parse_reference_style_blueprint_args(["--unknown"])

    with pytest.raises(ValueError, match="exactly one source"):
        report_module._parse_reference_style_blueprint_args(
            ["--description", "x", "--library", "y"]
        )


def test_reference_style_blueprint_report_handler_formats_errors(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    def _raise_value_error(source_flag: str, source_value: str):
        raise ValueError(f"bad source: {source_flag} {source_value}")

    monkeypatch.setattr(
        report_module,
        "build_reference_style_blueprint_from_source",
        _raise_value_error,
    )

    exit_code = report_module._handle_reference_style_blueprint_report(
        "--description",
        "x",
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "Usage: python -m rytm_randomizer.cli reference-style-blueprint-report" in captured.err
    assert "bad source: --description x" in captured.err
