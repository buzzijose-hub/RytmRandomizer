"""Offline source-preservation and request-scope tests for both device paths."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.cockpit.export import reference_sound_candidates as renderer
from rytm_randomizer.cockpit.export.reference_sound_candidates import (
    list_reference_sound_controls,
    render_reference_sound_candidates,
    render_refined_reference_sound_candidate,
)
from rytm_randomizer.data import (
    A4_REFERENCE_INFERENCE_BINDINGS,
    REFERENCE_SOUND_LIMITATIONS,
    RYTM_REFERENCE_FEATURE_TERMS,
)
from rytm_randomizer.data.analog_four_kit_fields import A4_TRACK_OFFSETS
from rytm_randomizer.data.analog_rytm_kit_fields import RYTM_SOUND_U7_FIELDS
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
    analog_rytm_track_sound_offset,
)
from rytm_randomizer.devices import (
    get_analog_four_native_field_capability,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    analog_rytm_saved_kit_checksum,
)
from rytm_randomizer.snapshot.elektron_native_object import ElektronNativeObjectMessage
from rytm_randomizer.style_analysis.audio_patch_dna import build_audio_patch_dna_workspace
from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

pytestmark = pytest.mark.fast
_FIXTURES = Path(__file__).parents[1] / "fixtures" / "rio145"


@pytest.fixture(params=[ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID])
def source(request: pytest.FixtureRequest) -> tuple[bytes, str, int, tuple[str, ...]]:
    device_id = request.param
    if device_id == ANALOG_RYTM_DEVICE_ID:
        return (
            (_FIXTURES / "RYTM_RIO145_AR_CORE_RETURN_Kit.syx").read_bytes(),
            device_id,
            2,
            ("filter_frequency", "amp_decay", "amp_overdrive"),
        )
    return (
        (_FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes(),
        device_id,
        3,
        ("filter1_frequency", "filter2_resonance", "noise_level"),
    )


def test_eight_candidates_are_deterministic_source_preserving_and_redecoded(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    tmp_path: Path,
) -> None:
    frame, device_id, target, parameters = source
    candidates = render_reference_sound_candidates(
        frame, device_id, target, audio_patch_dna_analysis, parameters, ()
    )
    assert candidates == render_reference_sound_candidates(
        frame, device_id, target, audio_patch_dna_analysis, parameters, ()
    )
    assert len(candidates) == 8
    workspace = build_audio_patch_dna_workspace(audio_patch_dna_analysis)
    assert [c.direction for c in candidates] == [c.key for c in workspace.candidates]
    before = ElektronNativeObjectMessage.from_bytes(frame)
    for candidate, direction in zip(candidates, workspace.candidates, strict=True):
        assert candidate.audio_features == direction.audio_features
        assert candidate.changes
        assert candidate.output_authority == "local-file-only"
        assert candidate.hardware_send_validated is False
        assert candidate.roundtrip_redecoded is True
        assert candidate.frame is candidate.frame_bytes
        assert candidate.features is candidate.audio_features
        payload = json.loads(json.dumps(candidate.to_dict()))
        assert payload["candidate_id"] == candidate.candidate_id
        assert payload["frame_size"] == len(candidate.frame)
        assert {c.parameter for c in candidate.changes}.issubset(parameters)
        assert set(candidate.changed_unpacked_offsets).issubset(candidate.intended_unpacked_offsets)
        after = ElektronNativeObjectMessage.from_bytes(candidate.frame_bytes)
        assert after.to_bytes() == candidate.frame_bytes
        assert replace(after, payload=before.payload) == before
        changed = tuple(
            i
            for i, pair in enumerate(zip(before.payload, after.payload, strict=True))
            if pair[0] != pair[1]
        )
        assert changed == candidate.changed_unpacked_offsets
        for change in candidate.changes:
            assert change.rationale
            assert change.units
            assert change.rendered_value != change.source_value
        output = tmp_path / f"{device_id}-{candidate.direction}.syx"
        output.write_bytes(candidate.frame_bytes)
        assert ElektronNativeObjectMessage.from_bytes(output.read_bytes()) == after
    assert len({c.candidate_id for c in candidates}) == 8
    with pytest.raises(FrozenInstanceError):
        candidates[0].target = 1  # type: ignore[misc]


@pytest.mark.parametrize("mode", ["zero", "locked", "empty"])
def test_noop_is_exact_framed_source_clone(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    mode: str,
) -> None:
    frame, device_id, target, parameters = source
    candidates = render_reference_sound_candidates(
        frame,
        device_id,
        target,
        audio_patch_dna_analysis,
        () if mode == "empty" else parameters,
        parameters if mode == "locked" else (),
        0.0 if mode == "zero" else 1.0,
    )
    assert all(c.frame_bytes == frame for c in candidates)
    assert all(
        c.changes == c.changed_unpacked_offsets == c.changed_wire_offsets == () for c in candidates
    )
    assert all("exact source clone" in c.limitations[-1] for c in candidates)


def test_partial_lock_wins_and_strength_blends_on_exact_native_grid(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    frame, device_id, target, parameters = source
    candidate = render_refined_reference_sound_candidate(
        frame,
        device_id,
        target,
        audio_patch_dna_analysis,
        parameters,
        (parameters[0],),
        0.25,
    )
    assert candidate.direction == "refined"
    assert candidate.audio_features == audio_patch_dna_analysis.synthesis_features
    assert any("parameter_locked" in text for text in candidate.limitations)
    controls = {c.parameter: c for c in list_reference_sound_controls(frame, device_id, target)}
    for change in candidate.changes:
        assert change.parameter != parameters[0]
        domain = controls[change.parameter].domain
        assert domain is not None
        start, end = domain.index_of(change.source_value), domain.index_of(change.proposed_value)
        assert change.rendered_value == domain.value_at(round(start + 0.25 * (end - start)))


@pytest.mark.parametrize("value", [-0.1, 1.1, float("nan"), float("inf"), True, "1", None])
def test_invalid_strength_is_refused(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    value: object,
) -> None:
    frame, device_id, target, parameters = source
    with pytest.raises(ValueError, match="strength"):
        render_reference_sound_candidates(frame, device_id, target, audio_patch_dna_analysis, parameters, (), value)  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [True, 0, 13, "2", None])
def test_invalid_target_is_refused(
    source: tuple[bytes, str, int, tuple[str, ...]], value: object
) -> None:
    frame, device_id, _, _ = source
    with pytest.raises(ValueError, match="target"):
        list_reference_sound_controls(frame, device_id, value)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "selection",
    [("unknown",), ("filter_frequency", "filter_frequency"), ["filter_frequency"], (False,)],
)
def test_invalid_scope_is_refused_before_inference(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    selection: object,
) -> None:
    frame, device_id, target, _ = source
    with pytest.raises((TypeError, ValueError)):
        render_reference_sound_candidates(frame, device_id, target, audio_patch_dna_analysis, selection, ())  # type: ignore[arg-type]
    with pytest.raises((TypeError, ValueError)):
        render_reference_sound_candidates(frame, device_id, target, audio_patch_dna_analysis, (), selection)  # type: ignore[arg-type]


def test_wrong_family_corrupt_and_nonbytes_sources_are_refused(
    source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    frame, device_id, target, _ = source
    other = ANALOG_FOUR_DEVICE_ID if device_id == ANALOG_RYTM_DEVICE_ID else ANALOG_RYTM_DEVICE_ID
    for bad in (frame[:-1], frame + frame, b"", frame[:50] + bytes((frame[50] ^ 1,)) + frame[51:]):
        with pytest.raises(ValueError):
            list_reference_sound_controls(bad, device_id, target)
    with pytest.raises(ValueError):
        list_reference_sound_controls(frame, other, target)
    with pytest.raises(TypeError, match="bytes"):
        list_reference_sound_controls(bytearray(frame), device_id, target)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported"):
        list_reference_sound_controls(frame, "foreign", target)


def test_rytm_rejects_unknown_and_wrong_pad_machine_without_masking(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    original = ElektronNativeObjectMessage.from_bytes(
        (_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes()
    )
    for machine in (0xFF, 25):
        raw = bytearray(original.payload)
        raw[analog_rytm_track_sound_offset(2, RYTM_SOUND_MACHINE_TYPE_OFFSET)] = machine
        with pytest.raises(ValueError, match="machine"):
            render_reference_sound_candidates(
                original.with_payload(bytes(raw)).to_bytes(),
                ANALOG_RYTM_DEVICE_ID,
                2,
                audio_patch_dna_analysis,
                ("filter_frequency",),
                (),
            )


def test_rytm_synthetic_unknown_bytes_companion_precision_and_other_pads_survive(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    original = ElektronNativeObjectMessage.from_bytes(
        (_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes()
    )
    raw = bytearray(original.payload)
    offset = analog_rytm_track_sound_offset(2, RYTM_SOUND_U7_FIELDS["filter_frequency"])
    raw[offset + 1] = 0xA5
    raw[-19:] = bytes(range(201, 220))
    frame = original.with_payload(bytes(raw)).to_bytes()
    candidate = render_refined_reference_sound_candidate(
        frame,
        ANALOG_RYTM_DEVICE_ID,
        2,
        audio_patch_dna_analysis,
        ("filter_frequency", "sample_number", "amp_volume"),
        (),
    )
    result = ElektronNativeObjectMessage.from_bytes(candidate.frame_bytes).payload
    assert result[offset] == round(127 * audio_patch_dna_analysis.synthesis_features.brightness)
    assert result[offset + 1] == 0xA5
    assert result[:offset] == bytes(raw[:offset])
    assert result[offset + 1 :] == bytes(raw[offset + 1 :])
    assert {c.parameter for c in candidate.changes} == {"filter_frequency"}
    assert any("sample_number preserved" in text for text in candidate.limitations)
    assert any("amp_volume preserved" in text for text in candidate.limitations)


def test_a4_native_fraction_oxi_and_unknown_selectors_survive(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    original = (_FIXTURES / "A4_RIO145_CORE_RETURN_Kit.syx").read_bytes()
    capability = get_analog_four_native_field_capability()
    readback = capability.read_native_fields(original)
    from rytm_randomizer.devices.strategies.analog_four_native_fields import (
        AnalogFourNativeMutation,
    )

    modified = capability.render_native_fields(
        original, (AnalogFourNativeMutation("filter1_frequency", 3, 0x5001),)
    ).framed_sysex
    message = ElektronNativeObjectMessage.from_bytes(modified)
    raw = bytearray(message.payload)
    selector = readback.value("osc1_waveform", 3).unpacked_offsets[0]
    raw[selector] = 0x7F
    frame = message.with_payload(bytes(raw)).to_bytes()
    candidate = render_refined_reference_sound_candidate(
        frame,
        ANALOG_FOUR_DEVICE_ID,
        3,
        audio_patch_dna_analysis,
        ("filter1_frequency", "amp_attack", "osc1_waveform", "osc1_fine"),
        (),
        0.25,
    )
    after = capability.read_native_fields(candidate.frame_bytes)
    change = candidate.changes[0]
    assert change.parameter == "filter1_frequency"
    assert change.rendered_value == round(0x5001 + 0.25 * (change.proposed_value - 0x5001))
    assert after.value("osc1_waveform", 3).encoded_native == 0x7F
    assert any("oxi_amp_protection" in text for text in candidate.limitations)
    assert any("independently_unsafe_fine" in text for text in candidate.limitations)


def test_inventory_bindings_reference_existing_facts_and_expose_reasons(
    source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    frame, device_id, target, _ = source
    controls = list_reference_sound_controls(frame, device_id, target)
    assert len({c.parameter for c in controls}) == len(controls)
    assert any(c.mutable for c in controls)
    assert any(c.reasons for c in controls)
    assert json.loads(json.dumps(controls[0].to_dict()))["parameter"] == controls[0].parameter
    assert all(c.to_dict()["send_supported"] is False for c in controls)
    assert set(A4_REFERENCE_INFERENCE_BINDINGS).issubset(A4_TRACK_OFFSETS)
    assert set(RYTM_REFERENCE_FEATURE_TERMS).issubset(RYTM_SOUND_U7_FIELDS)
    assert "no live eligibility" in REFERENCE_SOUND_LIMITATIONS[0]


def test_invalid_analysis_is_refused(
    source: tuple[bytes, str, int, tuple[str, ...]], audio_patch_dna_analysis: AudioFeatureAnalysis
) -> None:
    frame, device_id, target, parameters = source
    with pytest.raises(TypeError, match="analysis"):
        render_reference_sound_candidates(frame, device_id, target, None, parameters, ())  # type: ignore[arg-type]
    bad = replace(audio_patch_dna_analysis, synthesis_features=None)  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="measured"):
        render_reference_sound_candidates(frame, device_id, target, bad, parameters, ())


def test_all_expressible_controls_render_and_redecode_on_both_devices(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    frame, device_id, target, _ = source
    parameters = tuple(
        c.parameter for c in list_reference_sound_controls(frame, device_id, target) if c.mutable
    )
    candidate = render_refined_reference_sound_candidate(
        frame, device_id, target, audio_patch_dna_analysis, parameters, ()
    )
    assert candidate.changes
    assert (
        ElektronNativeObjectMessage.from_bytes(candidate.frame_bytes).to_bytes()
        == candidate.frame_bytes
    )
    assert all(c.parameter in parameters for c in candidate.changes)
    assert len(fields(candidate)) > 10


def _noncanonical_rytm_frame() -> bytes:
    frame = bytearray((_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes())
    frame[-12] |= 1  # Unused bit in the last MSB-first packing mask.
    checksum = analog_rytm_saved_kit_checksum(bytes(frame[10:-5]))
    frame[-5], frame[-4] = checksum >> 7, checksum & 0x7F
    return bytes(frame)


def test_noncanonical_source_padding_is_refused() -> None:
    with pytest.raises(ValueError, match="round-trip"):
        list_reference_sound_controls(_noncanonical_rytm_frame(), ANALOG_RYTM_DEVICE_ID, 2)


def test_out_of_domain_source_native_cell_stays_immutable(
    audio_patch_dna_analysis: AudioFeatureAnalysis,
) -> None:
    original = ElektronNativeObjectMessage.from_bytes(
        (_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes()
    )
    raw = bytearray(original.payload)
    raw[analog_rytm_track_sound_offset(2, RYTM_SOUND_U7_FIELDS["filter_frequency"])] = 0xFE
    frame = original.with_payload(bytes(raw)).to_bytes()
    candidate = render_refined_reference_sound_candidate(
        frame, ANALOG_RYTM_DEVICE_ID, 2, audio_patch_dna_analysis, ("filter_frequency",), ()
    )
    assert candidate.frame == frame
    assert any("source_value_outside_verified_domain" in text for text in candidate.limitations)


def test_bool_measurement_is_rejected(audio_patch_dna_analysis: AudioFeatureAnalysis) -> None:
    bad = replace(
        audio_patch_dna_analysis,
        synthesis_features=replace(audio_patch_dna_analysis.synthesis_features, attack=True),
    )
    frame = (_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes()
    with pytest.raises(ValueError, match="normalized measurements"):
        render_refined_reference_sound_candidate(frame, ANALOG_RYTM_DEVICE_ID, 2, bad, (), ())


def test_diff_proof_rejects_source_header_and_unselected_byte_changes(
    source: tuple[bytes, str, int, tuple[str, ...]],
) -> None:
    frame, device_id, _, _ = source
    message = ElektronNativeObjectMessage.from_bytes(frame)
    with pytest.raises(ValueError, match="header"):
        renderer._verify_diff(
            frame, message.with_slot((message.slot + 1) % 128).to_bytes(), device_id, ()
        )
    raw = bytearray(message.payload)
    raw[-1] ^= 1
    with pytest.raises(ValueError, match="outside selected"):
        renderer._verify_diff(frame, message.with_payload(bytes(raw)).to_bytes(), device_id, ())


def test_wire_footprint_refuses_encoder_padding_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    frame = (_FIXTURES / "RYTM_Test1_Init_Kit.syx").read_bytes()
    changed = _noncanonical_rytm_frame()
    codec = resolve_saved_kit_capture_capability(ANALOG_RYTM_DEVICE_ID).capability
    monkeypatch.setattr(type(codec), "encode_saved_kit_capture", lambda self, decoded: changed)
    with pytest.raises(ValueError, match="wire bytes outside"):
        renderer._verify_diff(frame, changed, ANALOG_RYTM_DEVICE_ID, ())


def test_readback_must_match_exact_requested_value(
    source: tuple[bytes, str, int, tuple[str, ...]],
    audio_patch_dna_analysis: AudioFeatureAnalysis,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame, device_id, target, parameters = source
    controls = list_reference_sound_controls(frame, device_id, target)
    monkeypatch.setattr(renderer, "list_reference_sound_controls", lambda *args: controls)
    with pytest.raises(ValueError, match="readback disagrees"):
        render_refined_reference_sound_candidate(
            frame, device_id, target, audio_patch_dna_analysis, parameters, ()
        )
