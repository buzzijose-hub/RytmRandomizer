"""Tests for passive audio-to-Analog-Rytm recipe proposals."""

from __future__ import annotations

import json
import math

import pytest

from rytm_randomizer.data.al16_rytm import AL16_PAD_ROLES, AL16_RYTM_WRITABLE_FIELDS
from rytm_randomizer.data.rytm_machine_catalog import is_machine_allowed_on_pad
from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis.extractor import (
    AudioDnaEvidence,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
)
from rytm_randomizer.style_analysis.feature_report import FeatureReport

pytestmark = pytest.mark.fast


def _analysis(
    *,
    brightness: float = 0.58,
    noise: float = 0.16,
    low_end: float = 0.44,
    decay: float = 0.32,
    dominant_note: str | None = "F2",
    pitch_confidence: float = 0.91,
    tonal_stability: float = 0.84,
) -> AudioFeatureAnalysis:
    report = FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=138.0,
        tempo_stability=0.94,
        kick_density=0.18,
        percussion_density=0.41,
        low_end_weight=low_end,
        spectral_brightness=brightness,
        texture_noise=noise,
        energy_arc=(0.12, 0.82, 0.64, 0.48, 0.35, 0.24, 0.16, 0.08),
        content_hash="audio-rytm-test-report",
        derived_at="2026-08-24T12:00:00Z",
    )
    features = AudioSynthesisFeatures(
        audio_sha256="a" * 64,
        duration=0.38,
        attack=0.05,
        decay=decay,
        sustain=0.18,
        tail=0.24,
        brightness=brightness,
        spectral_flatness=0.12,
        noise=noise,
        low_end=low_end,
        harmonicity=0.76,
        transient=0.82,
        modulation=0.22,
    )
    evidence = AudioDnaEvidence(
        dominant_frequency_hz=87.31 if dominant_note is not None else None,
        dominant_note=dominant_note,
        pitch_confidence=pitch_confidence,
        tonal_stability=tonal_stability,
        spectral_movement=0.28,
    )
    return AudioFeatureAnalysis(
        feature_report=report,
        synthesis_features=features,
        dna_evidence=evidence,
    )


def _fields_by_path(payload: dict[str, object]) -> dict[str, dict[str, object]]:
    tracks = payload["tracks"]
    assert isinstance(tracks, list)
    fields: dict[str, dict[str, object]] = {}
    for track in tracks:
        assert isinstance(track, dict)
        track_fields = track["fields"]
        assert isinstance(track_fields, list)
        for field in track_fields:
            assert isinstance(field, dict)
            path = field["path"]
            assert isinstance(path, str)
            fields[path] = field
    return fields


def test_proposal_is_deterministic_passive_and_explicitly_not_compile_ready() -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        analog_rytm_audio_recipe_proposal_to_dict,
        build_analog_rytm_audio_recipe_proposal,
    )

    first = build_analog_rytm_audio_recipe_proposal(_analysis())
    second = build_analog_rytm_audio_recipe_proposal(_analysis())
    payload = analog_rytm_audio_recipe_proposal_to_dict(first)

    assert first == second
    assert len(first.recipe_id) == 64
    assert payload["status"] == "proposal_only"
    assert payload["hardware_verified"] is False
    assert payload["codec_ready"] is False
    assert payload["render_required"] is True
    assert payload["midi_sent"] is False
    assert payload["preserved_pads"] == [2, 4, 5, 7, 8, 10, 11, 12]
    assert payload["writable_field_count"] == 44
    assert payload["mapping_required_count"] == 9
    assert json.loads(json.dumps(payload)) == payload


def test_proposal_uses_stable_roles_and_only_legal_machine_hypotheses() -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        build_analog_rytm_audio_recipe_proposal,
    )

    proposal = build_analog_rytm_audio_recipe_proposal(_analysis())
    expected_machines = {
        1: "bd_classic",
        3: "rs_classic",
        6: "xt_classic",
        9: "ch_classic",
    }
    assert [track.pad for track in proposal.tracks] == [1, 3, 6, 9]
    for track in proposal.tracks:
        assert track.role == AL16_PAD_ROLES[track.pad]
        assert track.machine_key == expected_machines[track.pad]
        assert is_machine_allowed_on_pad(track.pad, track.machine_key)
        assert track.machine_status == "compatible_mapping_required"


def test_writable_fields_reuse_positive_layout_facts_and_values_are_bounded() -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        analog_rytm_audio_recipe_proposal_to_dict,
        build_analog_rytm_audio_recipe_proposal,
    )

    payload = analog_rytm_audio_recipe_proposal_to_dict(
        build_analog_rytm_audio_recipe_proposal(_analysis())
    )
    fields = _fields_by_path(payload)
    assert len(fields) == 48
    for path, field in fields.items():
        value = field["requested_value"]
        if isinstance(value, int):
            assert 0 <= value <= 127
        relative_path = ".".join(path.split(".")[2:])
        if field["status"] == "writable_proposal":
            fact = AL16_RYTM_WRITABLE_FIELDS[relative_path]
            assert field["converter"] == fact.converter
        else:
            assert relative_path == "amp.vol"
            assert field["converter"] is None


def test_equations_respond_to_audio_evidence_without_changing_recipe_shape() -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        analog_rytm_audio_recipe_proposal_to_dict,
        build_analog_rytm_audio_recipe_proposal,
    )

    dark = analog_rytm_audio_recipe_proposal_to_dict(
        build_analog_rytm_audio_recipe_proposal(
            _analysis(brightness=0.10, noise=0.05, low_end=0.20, decay=0.12)
        )
    )
    bright = analog_rytm_audio_recipe_proposal_to_dict(
        build_analog_rytm_audio_recipe_proposal(
            _analysis(brightness=0.90, noise=0.75, low_end=0.80, decay=0.78)
        )
    )
    dark_fields = _fields_by_path(dark)
    bright_fields = _fields_by_path(bright)

    assert dark_fields.keys() == bright_fields.keys()
    assert (
        bright_fields["tracks.9.filter.frq"]["requested_value"]
        > dark_fields["tracks.9.filter.frq"]["requested_value"]
    )
    assert (
        bright_fields["tracks.3.amp.ovr"]["requested_value"]
        > dark_fields["tracks.3.amp.ovr"]["requested_value"]
    )
    assert (
        bright_fields["tracks.1.amp.dec"]["requested_value"]
        > dark_fields["tracks.1.amp.dec"]["requested_value"]
    )
    assert dark["recipe_id"] != bright["recipe_id"]


def test_measured_pitch_never_becomes_an_unapproved_raw_tune() -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        build_analog_rytm_audio_recipe_proposal,
    )

    proposal = build_analog_rytm_audio_recipe_proposal(_analysis())
    tuning = next(track.tuning for track in proposal.tracks if track.pad == 6)

    assert tuning is not None
    assert tuning.target_note == "F2"
    assert tuning.status == "mapping_required"
    assert tuning.raw_tune is None
    assert "no approved XT Classic" in tuning.reason


@pytest.mark.parametrize(
    ("dominant_note", "pitch_confidence", "tonal_stability"),
    ((None, 0.0, 0.0), ("F2", 0.74, 0.90), ("F2", 0.90, 0.59)),
)
def test_uncertain_pitch_is_preserved_instead_of_forced(
    dominant_note: str | None,
    pitch_confidence: float,
    tonal_stability: float,
) -> None:
    from rytm_randomizer.style_analysis.analog_rytm_recipe_inference import (
        build_analog_rytm_audio_recipe_proposal,
    )

    proposal = build_analog_rytm_audio_recipe_proposal(
        _analysis(
            dominant_note=dominant_note,
            pitch_confidence=pitch_confidence,
            tonal_stability=tonal_stability,
        )
    )
    tuning = next(track.tuning for track in proposal.tracks if track.pad == 6)
    assert tuning is not None
    assert tuning.status == "mapping_required"
    assert tuning.raw_tune is None
    assert "not stable enough" in tuning.reason


def test_future_approved_machine_tuning_can_resolve_without_changing_equations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.style_analysis import analog_rytm_recipe_inference as inference

    monkeypatch.setattr(inference, "AL16_RYTM_APPROVED_TUNING", {("xt_classic", "F2"): 46})
    proposal = inference.build_analog_rytm_audio_recipe_proposal(_analysis())
    tuning = next(track.tuning for track in proposal.tracks if track.pad == 6)
    assert tuning is not None
    assert tuning.status == "approved_tuning"
    assert tuning.raw_tune == 46
    assert proposal.mapping_required_count == 8


def test_fail_closed_runtime_and_internal_validation_paths() -> None:
    from rytm_randomizer.style_analysis import analog_rytm_recipe_inference as inference

    with pytest.raises(TypeError, match="analysis must be"):
        inference.build_analog_rytm_audio_recipe_proposal("not-analysis")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="proposal must be"):
        inference.analog_rytm_audio_recipe_proposal_to_dict("not-proposal")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="finite"):
        inference._to_7bit(math.nan)
    assert inference._to_7bit(-1.0) == 0
    assert inference._to_7bit(2.0) == 127
    with pytest.raises(ValueError, match="not legal"):
        inference._track(pad=1, machine_key="ch_classic", fields=())


def test_default_mapping_gap_reason_and_none_tuning_payload_are_explicit() -> None:
    from rytm_randomizer.style_analysis import analog_rytm_recipe_inference as inference

    field = inference._field(
        pad=1,
        field_path="source.unverified",
        requested_value=12,
        evidence=(),
        equation="test-only equation",
    )
    assert field.status == "mapping_required"
    assert field.reason == "No approved saved-kit field mapping exists."
    assert inference._tuning_payload(None) is None
