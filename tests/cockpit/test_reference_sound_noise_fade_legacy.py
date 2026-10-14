"""Frozen b9 candidate bytes, explicit inference versions and legacy replay."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import struct
import wave
from dataclasses import replace
from pathlib import Path
from threading import Event
from typing import Final

import pytest

from rytm_randomizer.cockpit.export import reference_sound_candidates as renderer
from rytm_randomizer.cockpit.export import reference_sound_session as session
from rytm_randomizer.cockpit.export.reference_sound_store import (
    ReferenceSoundStore,
    reference_sound_digest,
    reference_sound_json,
)
from rytm_randomizer.data import (
    A4_REFERENCE_NOISE_FADE_V1_SOURCE_REVISION,
    A4_REFERENCE_NOISE_FADE_V1_SPEC,
    A4_WORKING_KIT_OBJECT_BYTE,
    REFERENCE_SOUND_INFERENCE_VERSION,
    REFERENCE_SOUND_VERSIONED_A4_PARAMETER,
)
from rytm_randomizer.devices.strategies.elektron_kit_common import ElektronKitFieldError
from rytm_randomizer.observability.errors import BoundaryError
from rytm_randomizer.snapshot.elektron_native_object import ElektronNativeObjectMessage
from rytm_randomizer.style_analysis.reference_sound_analysis import (
    sound_analysis_from_dict,
    sound_features_from_dict,
)

pytestmark = pytest.mark.fast
_FIXTURES: Final[Path] = Path(__file__).parents[1] / "fixtures"
_LEGACY: Final[Path] = _FIXTURES / "audio_inference/noise_fade_b9_legacy_session.json"
_LEGACY_SHA256: Final[str] = "d933273f248fa0606384768128016d26a6c2d2a32a60fdfad3f6734740287e37"


def _legacy_fixture() -> dict:
    raw = _LEGACY.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == _LEGACY_SHA256
    return json.loads(raw)


def _source(fixture: dict) -> bytes:
    source = (_FIXTURES / fixture["source"]["fixture"]).read_bytes()
    assert hashlib.sha256(source).hexdigest() == fixture["source"]["sha256"]
    return source


def _synthetic_wav(recipe: dict) -> bytes:
    half = recipe["period_frames"] // 2
    pcm = b"".join(
        struct.pack(
            "<h",
            recipe["amplitude"]
            * (half - abs(2 * (index % recipe["period_frames"]) - recipe["period_frames"]))
            // half,
        )
        for index in range(recipe["frame_count"])
    )
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(recipe["sample_rate"])
        audio.writeframes(pcm)
    raw = buffer.getvalue()
    assert hashlib.sha256(raw).hexdigest() == recipe["sha256"]
    return raw


def test_v1_replays_genuine_b9_eight_directions_refinement_and_favorite_bytes(
    offline_hardware_denied: None,
) -> None:
    fixture = _legacy_fixture()
    assert fixture["provenance"]["revision"] == A4_REFERENCE_NOISE_FADE_V1_SOURCE_REVISION
    assert fixture["provenance"]["hardware_verified"] is False
    assert len(fixture["provenance"]["modules"]) == 4
    assert REFERENCE_SOUND_INFERENCE_VERSION == 2
    assert REFERENCE_SOUND_VERSIONED_A4_PARAMETER == "noise_fade"
    assert A4_REFERENCE_NOISE_FADE_V1_SPEC.scale == "unipolar"
    assert A4_REFERENCE_NOISE_FADE_V1_SPEC.intercept == 10.0
    assert A4_REFERENCE_NOISE_FADE_V1_SPEC.terms[0].coefficient == 96.0
    source = _source(fixture)
    payload = fixture["manifest"]
    context = payload["context"]
    assert "inference_version" not in context
    analysis = sound_analysis_from_dict(payload["analysis"])
    candidates = renderer.render_reference_sound_candidates(
        source,
        context["device_id"],
        context["target"],
        analysis,
        tuple(context["parameters"]),
        tuple(context["locks"]),
        context["strength"],
        inference_version=1,
    )
    assert len(candidates) == 8
    assert (
        json.loads(json.dumps([candidate.to_dict() for candidate in candidates]))
        == payload["candidates"][:8]
    )
    refined_features = sound_features_from_dict(payload["refinements"][0]["features"])
    refined = renderer.render_refined_reference_sound_candidate(
        source,
        context["device_id"],
        context["target"],
        replace(analysis, synthesis_features=refined_features),
        tuple(context["parameters"]),
        tuple(context["locks"]),
        context["strength"],
        inference_version=1,
    )
    assert json.loads(json.dumps(refined.to_dict())) == payload["candidates"][8]
    for candidate in (*candidates, refined):
        digest = hashlib.sha256(candidate.frame).hexdigest()
        frozen = base64.b64decode(fixture["framed_sysex_base64"][digest + ".syx"], validate=True)
        assert candidate.frame == frozen
        assert candidate.roundtrip_redecoded and not candidate.hardware_send_validated
        fade = next(c for c in candidate.changes if c.parameter == "noise_fade")
        assert -64 <= int(fade.proposed_display) <= 63
        assert fade.proposed_value == int(fade.proposed_display) + 64
    assert set(payload["favorites"]) == {candidates[0].candidate_id, refined.candidate_id}
    assert payload["selected_candidate_id"] == refined.candidate_id


def _restore_legacy_store(tmp_path: Path) -> tuple[dict, dict[str, bytes]]:
    fixture = _legacy_fixture()
    payload = fixture["manifest"]
    for name, encoded in fixture["framed_sysex_base64"].items():
        raw = base64.b64decode(encoded, validate=True)
        assert hashlib.sha256(raw).hexdigest() + ".syx" == name
        (tmp_path / name).write_bytes(raw)
    for recipe in fixture["wav_recipes"]:
        (tmp_path / (recipe["sha256"] + ".wav")).write_bytes(_synthetic_wav(recipe))
    manifest_path = tmp_path / (payload["session_id"] + ".sound.json")
    document = {**payload, "content_sha256": reference_sound_digest(reference_sound_json(payload))}
    manifest_path.write_bytes(reference_sound_json(document))
    before = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    return payload, before


def test_frozen_legacy_session_reopens_with_v1_renderer_without_reanalysis(
    tmp_path: Path,
    offline_hardware_denied: None,
) -> None:
    payload, before = _restore_legacy_store(tmp_path)

    def no_analysis(*_args, **_kwargs):
        pytest.fail("legacy reopen must use retained measurements, not an analyzer")

    workspace = session.ReferenceSoundWorkspace(ReferenceSoundStore(tmp_path), analyzer=no_analysis)
    assert workspace.reopen(payload["session_id"]) == payload
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before
    assert len(payload["favorites"]) == 2 and len(payload["refinements"]) == 1


def test_frozen_legacy_noise_fade_session_holds_fresh_refinement_without_changes(
    tmp_path: Path,
    offline_hardware_denied: None,
) -> None:
    payload, before = _restore_legacy_store(tmp_path)
    workspace = session.ReferenceSoundWorkspace(ReferenceSoundStore(tmp_path))
    with pytest.raises(BoundaryError) as error:
        workspace.refine(
            payload["session_id"],
            payload["recordings"][0]["candidate_id"],
            correction_gain=0.3,
            cancel=Event(),
        )
    assert error.value.context["error_code"] == "legacy_inference_requires_regeneration"
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == before


def test_current_noise_fade_generation_is_separate_v2_session_preserving_legacy(
    tmp_path: Path,
    offline_hardware_denied: None,
) -> None:
    payload, before = _restore_legacy_store(tmp_path)
    fixture = _legacy_fixture()
    analysis = sound_analysis_from_dict(payload["analysis"])
    audio = _synthetic_wav(fixture["wav_recipes"][0])
    context = payload["context"]

    def retained_analysis(path: Path, _cancel: Event):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == analysis.audio_sha256
        return analysis

    workspace = session.ReferenceSoundWorkspace(
        ReferenceSoundStore(tmp_path), analyzer=retained_analysis
    )
    imported = workspace.import_reference(audio, "Current Noise Fade generation")
    prepared = workspace.generate(
        imported["session_id"],
        source_frame=_source(fixture),
        device_id=context["device_id"],
        target=context["target"],
        parameters=tuple(context["parameters"]),
        locks=tuple(context["locks"]),
        strength=context["strength"],
        cancel=Event(),
    )
    current = workspace.commit(prepared)
    assert current["context"]["inference_version"] == REFERENCE_SOUND_INFERENCE_VERSION
    assert current["session_id"] != payload["session_id"]
    assert len(current["candidates"]) == 8
    assert current["context"]["source_sha256"] == context["source_sha256"]
    assert workspace.reopen(current["session_id"]) == current
    assert workspace.reopen(payload["session_id"]) == payload
    assert all((tmp_path / name).read_bytes() == raw for name, raw in before.items())


def test_v2_default_changes_only_noise_fade_not_other_equations_or_dto_fields() -> None:
    fixture = _legacy_fixture()
    source = _source(fixture)
    context = fixture["manifest"]["context"]
    analysis = sound_analysis_from_dict(fixture["manifest"]["analysis"])
    args = (
        source,
        context["device_id"],
        context["target"],
        analysis,
        tuple(context["parameters"]),
        tuple(context["locks"]),
        context["strength"],
    )
    old = renderer.render_reference_sound_candidates(*args, inference_version=1)
    new = renderer.render_reference_sound_candidates(*args)
    assert new == renderer.render_reference_sound_candidates(*args, inference_version=2)
    assert any(a.candidate_id != b.candidate_id for a, b in zip(old, new, strict=True))
    for original, current in zip(old, new, strict=True):
        assert [c for c in original.changes if c.parameter != "noise_fade"] == [
            c for c in current.changes if c.parameter != "noise_fade"
        ]
        assert original.limitations == current.limitations
        assert original.audio_features == current.audio_features
        old_body = ElektronNativeObjectMessage.from_bytes(original.frame).payload
        new_body = ElektronNativeObjectMessage.from_bytes(current.frame).payload
        offsets = {
            i for i, pair in enumerate(zip(old_body, new_body, strict=True)) if pair[0] != pair[1]
        }
        fade = next(c for c in current.changes if c.parameter == "noise_fade")
        assert offsets <= set(fade.offsets)


@pytest.mark.parametrize("scope", ["none", "narrow", "locked"])
def test_v1_and_v2_preserve_identical_none_narrow_and_locked_hashes(scope: str) -> None:
    fixture = _legacy_fixture()
    context = fixture["manifest"]["context"]
    analysis = sound_analysis_from_dict(fixture["manifest"]["analysis"])
    parameters = () if scope == "none" else ("osc1_level", "filter1_frequency")
    locks = ()
    if scope == "locked":
        parameters += ("noise_fade",)
        locks = ("noise_fade",)
    args = (_source(fixture), context["device_id"], context["target"], analysis, parameters, locks)
    for render in (
        renderer.render_reference_sound_candidates,
        renderer.render_refined_reference_sound_candidate,
    ):
        assert render(*args, inference_version=1) == render(*args, inference_version=2)


@pytest.mark.parametrize(
    "render",
    [renderer.render_reference_sound_candidates, renderer.render_refined_reference_sound_candidate],
)
@pytest.mark.parametrize("invalid", [True, False, 0, 3, -1, 1.0, 2.0, "1", None])
def test_inference_version_rejects_nonintegers_and_unknown_versions_before_decode(
    render,
    invalid,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_decode(*_args, **_kwargs):
        pytest.fail("invalid inference version must be rejected before source decode")

    monkeypatch.setattr(renderer, "require_reference_sound_generation_source", no_decode)
    with pytest.raises(ValueError, match="inference_version must be integer 1 or 2"):
        render(b"", "analog_four_mk2", 1, object(), (), (), inference_version=invalid)


@pytest.mark.parametrize(
    "render",
    [renderer.render_reference_sound_candidates, renderer.render_refined_reference_sound_candidate],
)
def test_v1_illegal_historical_target_is_refused_not_clamped_or_reencoded(render) -> None:
    measured = json.loads(
        (_FIXTURES / "audio_inference/untitled_first8_measurements.json").read_text()
    )
    analysis = sound_analysis_from_dict(measured["analysis"])
    args = (_source(_legacy_fixture()), "analog_four_mk2", 1, analysis, ("noise_fade",), ())
    with pytest.raises(ElektronKitFieldError, match=r"bipolar value must be in -64\.\.63, got 69"):
        render(*args, inference_version=1)
    render(*args, inference_version=2)


@pytest.mark.parametrize("inference_version", [1, 2])
@pytest.mark.parametrize(
    "render",
    [renderer.render_reference_sound_candidates, renderer.render_refined_reference_sound_candidate],
)
def test_both_inference_versions_refuse_working_source_even_when_fully_locked(
    render,
    inference_version: int,
    offline_hardware_denied: None,
) -> None:
    fixture = _legacy_fixture()
    working = bytearray(_source(fixture))
    working[6] = A4_WORKING_KIT_OBJECT_BYTE
    analysis = sound_analysis_from_dict(fixture["manifest"]["analysis"])
    with pytest.raises(BoundaryError) as error:
        render(
            bytes(working),
            "analog_four_mk2",
            1,
            analysis,
            ("noise_fade",),
            ("noise_fade",),
            inference_version=inference_version,
        )
    assert error.value.context["error_code"] == "working_kit_read_only"
