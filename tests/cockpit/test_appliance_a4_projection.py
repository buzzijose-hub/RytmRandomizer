"""Saved-state A4 values retain every native fractional bit without live authority."""

from dataclasses import replace
from decimal import localcontext
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.appliance_capabilities import parameter_capabilities
from rytm_randomizer.cockpit.capture import appliance_a4 as projection
from rytm_randomizer.cockpit.capture.appliance_a4 import (
    A4ApplianceFieldEncoding,
    appliance_a4_parameter_encoding,
    appliance_a4_parameter_encodings,
    appliance_snapshot_from_a4_capture,
)
from rytm_randomizer.cockpit.capture.service import KitCaptureResult, decode_kit_capture_frame
from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.devices.strategies.analog_four_kit_fields import A4Kit
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from rytm_randomizer.devices.strategies.analog_four_snapshot_decoder import AnalogFourKitSnapshot


@pytest.fixture
def saved_a4() -> KitCaptureResult:
    frame = (Path(__file__).parents[1] / "fixtures/rio145/A4_Test1_Init_Kit.syx").read_bytes()
    return decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, frame)


def _field(name: str) -> A4ApplianceFieldEncoding:
    return next(row for row in appliance_a4_parameter_encodings() if row.field == name)


def _recapture(source: KitCaptureResult, kit: A4Kit) -> KitCaptureResult:
    decoded = decode_analog_four_saved_kit_payload(source.frame[1:-1], require_trailer=True)
    encoded = encode_analog_four_saved_kit_payload(decoded.prefix, kit.to_bytes())
    return decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, b"\xf0" + encoded.payload + b"\xf7")


def test_saved_kit_projection_reads_all_tracks_and_never_changes_retained_bytes(
    saved_a4: KitCaptureResult,
) -> None:
    source = saved_a4.snapshot
    assert isinstance(source, AnalogFourKitSnapshot)
    original_frame, original_body = saved_a4.frame, source.unpacked
    snapshot = appliance_snapshot_from_a4_capture(saved_a4)
    encodings = appliance_a4_parameter_encodings()
    assert len(encodings) == 98
    assert snapshot.device == ANALOG_FOUR_DEVICE_ID
    assert snapshot.captured_at == saved_a4.captured_at
    assert [pad.pad_id for pad in snapshot.pads] == [1, 2, 3, 4]
    for track, pad in enumerate(snapshot.pads):
        assert pad.machine == "A4 CAPTURED SAVED KIT"
        assert pad.params == {
            row.parameter_id: row.read(A4Kit.from_bytes(original_body).sound(track))
            for row in encodings
        }
    assert saved_a4.frame == original_frame
    assert saved_a4.snapshot.unpacked == original_body
    assert not saved_a4.sent_midi
    assert len(snapshot.pads[0].params) < len(parameter_capabilities(ANALOG_FOUR_DEVICE_ID))


def test_native_fraction_and_hidden_pitch_precision_are_preserved(
    saved_a4: KitCaptureResult,
) -> None:
    assert isinstance(saved_a4.snapshot, AnalogFourKitSnapshot)
    kit = A4Kit.from_bytes(saved_a4.snapshot.unpacked)
    sound = kit.sound(0)
    sound.set_fixed_8_8_raw("filter1_frequency", 0x4013)
    sound.set_fixed_8_8_raw("filter2_frequency", 0x7FFF)
    sound.set_mod_depth("env2_depth_a", -1 / 128)
    sound.set_oscillator_pitch_raw(1, 0x4003)
    sound.set_oscillator_pitch_raw(2, 0x3FFD)
    sound.set_bipolar("osc1_detune", -17)
    sound.set_bipolar("osc2_detune", 23)
    kit.replace_sound(0, sound)
    captured = _recapture(saved_a4, kit)
    snapshot = appliance_snapshot_from_a4_capture(captured)
    expected = {
        "filter1_frequency": 0x4013,
        "filter2_frequency": 0x7FFF,
        "env2_depth_a": 0x3FFF,
        "osc1_tune": 0x4003,
        "osc2_tune": 0x3FFD,
        "osc1_fine": 1,
        "osc2_fine": -2,
        "osc1_detune": -17,
        "osc2_detune": 23,
    }
    for name, value in expected.items():
        assert snapshot.pads[0].params[_field(name).parameter_id] == value
    assert captured.snapshot.unpacked == kit.to_bytes()


@pytest.mark.parametrize(
    "field,raw,display",
    [
        ("filter1_frequency", 0x4013, "64.07421875"),
        ("filter2_frequency", 0x7FFF, "127.99609375"),
        ("env2_depth_a", 0x3FFF, "-0.0078125"),
        ("env2_depth_a", 0x4000, "0"),
        ("osc1_tune", 0x4003, "0.01171875"),
        ("osc2_tune", 0x3FFD, "-0.01171875"),
        ("osc1_detune", -17, "-17"),
        ("osc1_waveform", 7, "OFF"),
        ("envf_destination_a", 96, "NONE"),
    ],
)
def test_display_is_exact_even_under_low_decimal_precision(
    field: str, raw: int, display: str
) -> None:
    with localcontext() as context:
        context.prec = 1
        assert _field(field).format_display(raw) == display


def test_bipolar_detune_is_not_a_pitch_word_and_shared_fine_is_immutable() -> None:
    for name in ("osc1_detune", "osc2_detune"):
        row = _field(name)
        assert row.encoding == "bipolar"
        assert (row.raw_minimum, row.raw_maximum) == (-64, 63)
        assert row.offline_mutable
    for name in ("osc1_fine", "osc2_fine"):
        row = _field(name)
        assert not row.offline_mutable
        assert row.blockers == ("shared_pitch_component_requires_pair_edit",)
    assert not _field("osc1_tracking").offline_mutable
    assert _field("osc1_tracking").blockers == ("legal_values_unproven",)


@pytest.mark.parametrize(
    "encoding", appliance_a4_parameter_encodings(), ids=lambda row: row.parameter_id
)
def test_metadata_lookup_domains_and_live_authority(encoding: A4ApplianceFieldEncoding) -> None:
    assert appliance_a4_parameter_encoding(encoding.parameter_id) == encoding
    document = encoding.to_dict()
    assert document["raw_minimum"] == encoding.raw_minimum
    assert document["raw_maximum"] == encoding.raw_maximum
    assert document["baseline_coverage"] == "saved_state_only"
    assert document["live_send_supported"] is False
    assert document["hardware_restore_supported"] is False
    assert encoding.validate_raw(encoding.raw_minimum) == encoding.raw_minimum
    assert encoding.validate_raw(encoding.raw_maximum) == encoding.raw_maximum


@pytest.mark.parametrize("value", [True, 1.0, "1", None, -1, 32768])
def test_invalid_native_values_refuse_without_quantization(value: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _field("filter2_frequency").validate_raw(value)


def test_enum_holes_and_documented_only_rows_remain_unsupported() -> None:
    with pytest.raises(ValueError, match="legal enum"):
        _field("envf_destination_a").validate_raw(37)
    assert appliance_a4_parameter_encoding("not-a-parameter") is None
    documented = next(
        row for row in parameter_capabilities(ANALOG_FOUR_DEVICE_ID) if not row.native_fields
    )
    assert appliance_a4_parameter_encoding(documented.parameter_id) is None


@pytest.mark.parametrize(
    "change,error,match",
    [
        ("family", ValueError, "Analog Four"),
        ("verified", ValueError, "round-trip"),
        ("type", TypeError, "AnalogFourKitSnapshot"),
        ("layout", ValueError, "saved-KIT layout"),
        ("fingerprint", ValueError, "canonical frame"),
        ("payload", ValueError, "canonical frame"),
    ],
)
def test_capture_identity_and_exact_source_must_match(
    saved_a4: KitCaptureResult, change: str, error: type[Exception], match: str
) -> None:
    assert isinstance(saved_a4.snapshot, AnalogFourKitSnapshot)
    if change == "family":
        altered = replace(saved_a4, device_id=ANALOG_RYTM_DEVICE_ID)
    elif change == "verified":
        altered = replace(saved_a4, round_trip_verified=False)
    elif change == "type":
        rytm_frame = (
            Path(__file__).parents[1] / "fixtures/rio145/RYTM_Test1_Init_Kit.syx"
        ).read_bytes()
        altered = replace(
            saved_a4, snapshot=decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_frame).snapshot
        )
    elif change == "layout":
        altered = replace(
            saved_a4, snapshot=replace(saved_a4.snapshot, snapshot_layout="candidate")
        )
    elif change == "fingerprint":
        altered = replace(saved_a4, fingerprint="f" * 16)
    else:
        altered = replace(
            saved_a4,
            snapshot=replace(saved_a4.snapshot, unpacked=saved_a4.snapshot.unpacked[:-1] + b"\xaa"),
        )
    with pytest.raises(error, match=match):
        appliance_snapshot_from_a4_capture(altered)


def test_canonical_decoder_cannot_be_replaced_by_another_family(
    saved_a4: KitCaptureResult, monkeypatch: pytest.MonkeyPatch
) -> None:
    rytm_frame = (
        Path(__file__).parents[1] / "fixtures/rio145/RYTM_Test1_Init_Kit.syx"
    ).read_bytes()
    other = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, rytm_frame)
    monkeypatch.setattr(projection, "decode_kit_capture_frame", lambda *_args: other)
    with pytest.raises(ValueError, match="canonical frame"):
        appliance_snapshot_from_a4_capture(saved_a4)


def test_invalid_mapped_domain_does_not_silently_clip_capture(saved_a4: KitCaptureResult) -> None:
    assert isinstance(saved_a4.snapshot, AnalogFourKitSnapshot)
    kit = A4Kit.from_bytes(saved_a4.snapshot.unpacked)
    sound = kit.sound(0)
    sound.set_u7("osc1_waveform", 127)
    kit.replace_sound(0, sound)
    captured = _recapture(saved_a4, kit)
    with pytest.raises(ValueError, match="supported domain"):
        appliance_snapshot_from_a4_capture(captured)
    assert captured.snapshot.unpacked == kit.to_bytes()
