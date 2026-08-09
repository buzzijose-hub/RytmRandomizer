"""Fixture-backed tests for the RIO145 kit-object field views."""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.devices.strategies.analog_four_kit_fields import (
    A4_SOUND_SIZE,
    A4_TRACK_OFFSETS,
    A4Destination,
    A4Kit,
    A4Sound,
    A4Waveform,
    decode_a4_mod_depth,
    decode_a4_pitch_components,
    decode_a4_pitch_semitones,
    decode_bipolar,
    encode_a4_mod_depth,
    encode_a4_pitch_raw,
    encode_bipolar,
    wire_address_to_track_raw_offset,
)
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from rytm_randomizer.devices.strategies.analog_rytm_kit_fields import (
    RYTM_SOUND_SIZE,
    RytmKit,
    RytmMachine,
    RytmSound,
    decode_rytm_mod_depth,
    encode_rytm_mod_depth,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from rytm_randomizer.snapshot import ElektronNativeObjectMessage, extract_sysex_payloads
from rytm_randomizer.snapshot.elektron_native_object import (
    ElektronNativeObjectError,
    pack_elektron_native_object,
    unpack_elektron_native_object,
)

pytestmark = pytest.mark.fast

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "rio145"


def _a4_fixture(name: str) -> tuple[bytes, A4Kit]:
    frame = (_FIXTURE_DIR / name).read_bytes()
    decoded = ElektronNativeObjectMessage.from_bytes(frame)
    return frame, A4Kit.from_bytes(decoded.payload)


def _rytm_fixture(name: str) -> tuple[bytes, RytmKit]:
    frame = (_FIXTURE_DIR / name).read_bytes()
    decoded = ElektronNativeObjectMessage.from_bytes(frame)
    return frame, RytmKit.from_bytes(decoded.payload)


@pytest.mark.parametrize(
    "fixture_name",
    [
        "A4_Test1_Init_Kit.syx",
        "A4_RIO145_CORE_RETURN_Kit.syx",
        "RYTM_Test1_Init_Kit.syx",
        "RYTM_RIO145_AR_CORE_RETURN_Kit.syx",
    ],
)
def test_native_object_fixture_reencodes_byte_identically(fixture_name: str) -> None:
    frame = (_FIXTURE_DIR / fixture_name).read_bytes()

    assert ElektronNativeObjectMessage.from_bytes(frame).to_bytes() == frame


@pytest.mark.parametrize(
    "fixture_name",
    ["A4_Test1_Init_Kit.syx", "A4_RIO145_CORE_RETURN_Kit.syx"],
)
def test_a4_fixture_reencodes_byte_identically(fixture_name: str) -> None:
    frame = (_FIXTURE_DIR / fixture_name).read_bytes()
    payload = extract_sysex_payloads(frame)[0]
    decoded = decode_analog_four_saved_kit_payload(payload, require_trailer=True)

    encoded = encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked)

    assert bytes((0xF0,)) + encoded.payload + bytes((0xF7,)) == frame


@pytest.mark.parametrize(
    "fixture_name",
    ["RYTM_Test1_Init_Kit.syx", "RYTM_RIO145_AR_CORE_RETURN_Kit.syx"],
)
def test_rytm_fixture_reencodes_byte_identically(fixture_name: str) -> None:
    frame = (_FIXTURE_DIR / fixture_name).read_bytes()
    decoded = decode_analog_rytm_saved_kit_frame(frame)

    assert encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked) == frame


def test_initialized_a4_tracks_and_public_offset_alignment() -> None:
    _, kit = _a4_fixture("A4_Test1_Init_Kit.syx")

    assert [sound.name for sound in kit.iter_sounds()] == [
        "SOUND 1",
        "SOUND 2",
        "SOUND 3",
        "SOUND 4",
    ]
    sound = kit.sound(0)
    assert sound.get_u7("osc1_tune") == 0x40
    assert sound.get_u7("osc2_tune") == 0x40
    assert sound.get_u7("osc1_tracking") == 1
    assert sound.get_u7("osc2_tracking") == 1
    assert sound.get_u7("osc1_level") == 100
    assert sound.get_fixed_8_8("filter1_frequency") == 127.0
    assert sound.get_fixed_8_8("filter2_frequency") == 0.0
    assert wire_address_to_track_raw_offset(43) == 0x1C
    assert wire_address_to_track_raw_offset(45) == 0x1E
    assert wire_address_to_track_raw_offset(120) == 0x60
    assert all(0 <= offset < 350 for offset in A4_TRACK_OFFSETS.values())


def test_a4_sound_edit_is_confined_to_selected_track() -> None:
    _, kit = _a4_fixture("A4_Test1_Init_Kit.syx")
    original = kit.to_bytes()
    sound = kit.sound(1)
    sound.name = "RIO F STAB"
    sound.set_u7("osc1_waveform", int(A4Waveform.TRP))
    sound.set_u7("osc2_waveform", int(A4Waveform.SAW))
    sound.set_destination("env2_destination_a", A4Destination.OSC2_PITCH)
    sound.set_integer_mod_depth("env2_depth_a", 7)
    kit.replace_sound(1, sound)

    changed_offsets = [
        index
        for index, (before, after) in enumerate(zip(original, kit.to_bytes(), strict=True))
        if before != after
    ]

    assert changed_offsets
    assert all(0x20 + 350 <= offset < 0x20 + 700 for offset in changed_offsets)


def test_a4_os151c_controlled_capture_encodings() -> None:
    _, baseline = _a4_fixture("A4_Test1_Init_Kit.syx")
    _, fine_plus = _a4_fixture("A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    _, fine_minus = _a4_fixture("A4_Test3_T1_OSC1_FIN_M1_Kit.syx")
    _, depth_plus = _a4_fixture("A4_Test4_T1_ENV2_DEPA_P1_Kit.syx")
    _, depth_minus = _a4_fixture("A4_Test5_T1_ENV2_DEPA_M1_Kit.syx")

    assert baseline.sound(0).get_oscillator_pitch_raw(1) == 0x4000
    assert fine_plus.sound(0).get_oscillator_tune_fine(1) == (0, 1)
    assert fine_minus.sound(0).get_oscillator_tune_fine(1) == (0, -1)
    assert depth_plus.sound(0).get_mod_depth("env2_depth_a") == 1.0
    assert depth_minus.sound(0).get_mod_depth("env2_depth_a") == -1.0


def test_initialized_rytm_tracks_and_signatures() -> None:
    _, kit = _rytm_fixture("RYTM_Test1_Init_Kit.syx")

    assert [sound.name for sound in kit.iter_sounds()] == [
        f"SOUND {index}" for index in range(1, 13)
    ]
    assert all(sound.to_bytes()[:4] == bytes.fromhex("be ef ba ce") for sound in kit.iter_sounds())


def test_rytm_sound_edit_is_confined_to_selected_track() -> None:
    _, kit = _rytm_fixture("RYTM_Test1_Init_Kit.syx")
    original = kit.to_bytes()
    sound = kit.sound(0)
    sound.machine = RytmMachine.BD_SHARP
    sound.name = "TEST KICK"
    sound.set_machine_parameter_bipolar(2, -5)
    sound.set_u7("filter_frequency", 23)
    kit.replace_sound(0, sound)

    changed_offsets = [
        index
        for index, (before, after) in enumerate(zip(original, kit.to_bytes(), strict=True))
        if before != after
    ]

    assert changed_offsets
    assert all(0x002E <= offset < 0x002E + 162 for offset in changed_offsets)


def test_rytm_field_module_exposes_no_native_pattern_model() -> None:
    import rytm_randomizer.devices.strategies.analog_rytm_kit_fields as fields

    assert not hasattr(fields, "RytmPattern")
    assert not hasattr(fields, "RytmTrigFlag")


@pytest.mark.parametrize(
    "native",
    [b"\x00", b"\x80", bytes(range(16)), bytes((0xFF, 0x80, 0x7F, 0x01))],
)
def test_native_object_packing_round_trips_native_bytes(native: bytes) -> None:
    packed = pack_elektron_native_object(native)

    assert all(value <= 0x7F for value in packed)
    assert unpack_elektron_native_object(packed) == native


@pytest.mark.parametrize("packed", [b"\x80\x00", b"\x00"])
def test_native_object_unpack_rejects_malformed_groups(packed: bytes) -> None:
    with pytest.raises(ElektronNativeObjectError):
        unpack_elektron_native_object(packed)


def test_native_object_message_rejects_invalid_envelope_and_headers() -> None:
    frame = bytearray((_FIXTURE_DIR / "A4_Test1_Init_Kit.syx").read_bytes())
    variants = [
        b"\xf0\xf7",
        bytes((0x00,)) + bytes(frame[1:]),
        bytes(frame[:-1]) + bytes((0x00,)),
        bytes(frame[:1]) + b"\x01\x02\x03" + bytes(frame[4:]),
        bytes(frame[:10]) + b"\x80" + bytes(frame[11:]),
        bytes(frame[:-5]) + bytes((frame[-5] ^ 1,)) + bytes(frame[-4:]),
        bytes(frame[:-3]) + bytes((frame[-3] ^ 1,)) + bytes(frame[-2:]),
    ]

    for variant in variants:
        with pytest.raises(ElektronNativeObjectError):
            ElektronNativeObjectMessage.from_bytes(variant)

    decoded = ElektronNativeObjectMessage.from_bytes(bytes(frame))
    invalid_header = ElektronNativeObjectMessage(
        product_id=128,
        device_id=decoded.device_id,
        command=decoded.command,
        format_version=decoded.format_version,
        format_revision=decoded.format_revision,
        slot=decoded.slot,
        payload=decoded.payload,
    )
    with pytest.raises(ValueError, match="header values"):
        invalid_header.to_bytes()
    with pytest.raises(ValueError, match="slot"):
        decoded.with_slot(128)
    assert decoded.with_payload(b"test").payload == b"test"
    assert decoded.with_slot(7).slot == 7


def test_a4_value_converters_cover_boundaries_and_fail_closed() -> None:
    assert [encode_bipolar(value) for value in (-64, 0, 63)] == [0, 64, 127]
    assert [decode_bipolar(value) for value in (0, 64, 127)] == [-64, 0, 63]
    for value in (-65, 64):
        with pytest.raises(ValueError, match="bipolar"):
            encode_bipolar(value)

    for tune, fine, hidden in [(-63, -1, 0), (0, 0, 0), (12, 19, 1), (63, 0, 0)]:
        raw = encode_a4_pitch_raw(tune, fine, hidden_half_step=hidden)
        assert decode_a4_pitch_components(raw)[:3] == (tune, fine, hidden)
        assert decode_a4_pitch_semitones(raw) == (raw - 0x4000) / 256

    for args in [(-65, 0, 0), (64, 0, 0), (0, -65, 0), (0, 64, 0), (0, 0, 2)]:
        with pytest.raises(ValueError):
            encode_a4_pitch_raw(args[0], args[1], hidden_half_step=args[2])
    for raw in (-1, 0x8000):
        with pytest.raises(ValueError, match="raw oscillator pitch"):
            decode_a4_pitch_components(raw)
        with pytest.raises(ValueError, match="raw oscillator pitch"):
            decode_a4_pitch_semitones(raw)
    with pytest.raises(ValueError, match="outside native range"):
        encode_a4_pitch_raw(-64, -64)

    for value in (-128.0, -1.0, 0.0, 1.0, 127.9921875):
        assert decode_a4_mod_depth(encode_a4_mod_depth(value)) == value
    for value in (-128.01, 128.0, 0.001):
        with pytest.raises(ValueError, match="modulation depth"):
            encode_a4_mod_depth(value)
    for raw in (-1, 0x8000):
        with pytest.raises(ValueError, match="raw modulation depth"):
            decode_a4_mod_depth(raw)


def test_a4_sound_and_kit_guards_cover_unknown_fields_and_ranges() -> None:
    _, kit = _a4_fixture("A4_Test1_Init_Kit.syx")
    sound = kit.sound(0)
    sound.name = "12345678901234567"
    assert sound.name == "1234567890123456"

    with pytest.raises(ValueError, match="350 bytes"):
        A4Sound.from_bytes(bytes(A4_SOUND_SIZE - 1))
    malformed = bytearray(sound.to_bytes())
    malformed[:4] = b"nope"
    with pytest.raises(ValueError, match="signature"):
        A4Sound.from_bytes(malformed)
    malformed = bytearray(sound.to_bytes())
    malformed[4:8] = bytes(4)
    with pytest.raises(ValueError, match="format marker"):
        A4Sound.from_bytes(malformed)

    with pytest.raises(KeyError, match="Unknown mapped"):
        sound.offset("unknown")
    for value in (-1, 256):
        with pytest.raises(ValueError, match="0..255"):
            sound.set_raw_u8("osc1_waveform", value)
    for value in (-1, 128):
        with pytest.raises(ValueError, match="0..127"):
            sound.set_u7("osc1_waveform", value)
    sound._data[sound.offset("osc1_waveform")] = 255
    with pytest.raises(ValueError, match="8-bit raw"):
        sound.get_u7("osc1_waveform")

    for method in (sound.get_bipolar, sound.set_bipolar):
        with pytest.raises(ValueError, match="not registered"):
            method("osc1_waveform", 0) if method == sound.set_bipolar else method("osc1_waveform")
    sound.set_bipolar("osc1_detune", -4)
    assert sound.get_bipolar("osc1_detune") == -4
    for oscillator in (0, 3):
        with pytest.raises(ValueError, match="oscillator"):
            sound.get_oscillator_pitch_raw(oscillator)
    for raw in (-1, 0x8000):
        with pytest.raises(ValueError, match="raw oscillator"):
            sound.set_oscillator_pitch_raw(1, raw)
    sound.set_oscillator_pitch_raw(1, encode_a4_pitch_raw(0, 0))
    assert sound.get_oscillator_pitch_raw(1) == 0x4000
    assert sound.get_oscillator_pitch_components(1) == (0, 0, 0, 0)
    assert sound.get_oscillator_tune(1) == 0
    assert sound.get_oscillator_fine(1) == 0
    assert sound.get_oscillator_fine_hidden_half_step(1) == 0
    assert sound.get_oscillator_fine_native_residual(1) == 0
    sound.set_oscillator_tune(1, 12)
    sound.set_oscillator_fine(1, 19)
    assert sound.get_oscillator_tune_fine(1) == (12, 19)
    sound.set_oscillator_tune_fine(1, -12, -19, hidden_half_step=1)
    assert sound.get_oscillator_pitch_components(1)[:3] == (-12, -19, 1)
    assert (
        sound.get_oscillator_pitch_semitones(1)
        == (sound.get_oscillator_pitch_raw(1) - 0x4000) / 256
    )
    for field in ("osc1_waveform", "unknown"):
        with pytest.raises(ValueError, match="8.8"):
            sound.get_fixed_8_8(field)
        with pytest.raises(ValueError, match="8.8"):
            sound.set_fixed_8_8(field, 1.0)
    for value in (-0.01, 128.0):
        with pytest.raises(ValueError, match="8.8 display"):
            sound.set_fixed_8_8("filter1_frequency", value)
    sound.set_fixed_8_8("filter1_frequency", 63.5)
    assert sound.get_fixed_8_8("filter1_frequency") == 63.5
    for operation in (sound.get_mod_depth_raw, sound.set_mod_depth):
        with pytest.raises(ValueError, match="modulation-depth"):
            operation("unknown", 0.0) if operation == sound.set_mod_depth else operation("unknown")

    for track in (-1, 6):
        with pytest.raises(ValueError, match="track level"):
            kit.track_level(track)
        with pytest.raises(ValueError, match="track level"):
            kit.set_track_level(track, 0)
    with pytest.raises(ValueError, match="0..127"):
        kit.set_track_level(0, 128)
    with pytest.raises(ValueError, match="kit object"):
        A4Kit.from_bytes(bytes(len(kit.to_bytes()) - 1))
    kit.name = "RIO145 TEST KIT NAME"
    assert kit.name == "RIO145 TEST KIT"
    kit.set_track_level(0, 100)
    assert kit.track_level(0) == 100
    for track in (-1, 4):
        with pytest.raises(ValueError, match="synth track"):
            kit.sound(track)
        with pytest.raises(ValueError, match="synth track"):
            kit.replace_sound(track, sound)


def test_rytm_value_converters_and_field_views_fail_closed() -> None:
    for value in (-128.0, -1.0, 0.0, 1.0, 127.9921875):
        assert decode_rytm_mod_depth(encode_rytm_mod_depth(value)) == value
    for value in (-128.01, 128.0, 0.001):
        with pytest.raises(ValueError, match="modulation depth"):
            encode_rytm_mod_depth(value)
    for raw in (-1, 0x8000):
        with pytest.raises(ValueError, match="raw Rytm modulation"):
            decode_rytm_mod_depth(raw)

    _, kit = _rytm_fixture("RYTM_Test1_Init_Kit.syx")
    sound = kit.sound(0)
    sound.name = "1234567890123456"
    assert sound.name == "123456789012345"
    with pytest.raises(ValueError, match="162 bytes"):
        RytmSound.from_bytes(bytes(RYTM_SOUND_SIZE - 1))
    malformed = bytearray(sound.to_bytes())
    malformed[:4] = b"nope"
    with pytest.raises(ValueError, match="signature"):
        RytmSound.from_bytes(malformed)

    for index in (0, 9):
        with pytest.raises(ValueError, match="1..8"):
            sound.machine_parameter_name(index)
        with pytest.raises(ValueError, match="1..8"):
            sound.get_machine_parameter_raw16(index)
        with pytest.raises(ValueError, match="1..8"):
            sound.set_machine_parameter_raw16(index, 0)
    with pytest.raises(ValueError, match="16-bit"):
        sound.set_machine_parameter_raw16(1, 0x10000)
    with pytest.raises(ValueError, match="0..127"):
        sound.set_machine_parameter_u7(1, 128)
    assert sound.machine == RytmMachine.BD_HARD
    assert sound.machine_parameter_name(1) is None
    sound.set_machine_parameter_raw16(1, 0x1234)
    assert sound.get_machine_parameter_raw16(1) == 0x1234
    sound.set_machine_parameter_u7(1, 7, clear_lsb=False)
    assert sound.get_machine_parameter_u7(1) == 7
    sound.set_machine_parameter_bipolar(1, -5)
    assert sound.get_machine_parameter_bipolar(1) == -5
    with pytest.raises(ValueError, match="bipolar"):
        sound.set_machine_parameter_bipolar(1, -65)

    for operation in (sound.get_u7, sound.set_u7):
        with pytest.raises(KeyError, match="Unknown Rytm sound"):
            operation("unknown", 0) if operation == sound.set_u7 else operation("unknown")
    with pytest.raises(ValueError, match="unknown Rytm sound"):
        sound.u7_field_offset("unknown")
    sound.set_u7("amp_volume", 100, clear_lsb=False)
    assert sound.get_u7("amp_volume") == 100
    sound.set_bipolar("amp_pan", -3)
    assert sound.get_bipolar("amp_pan") == -3
    sound.sample_start_raw16 = 0x1234
    sound.sample_end_raw16 = 0x5678
    sound.lfo_depth = -1.5
    assert (sound.sample_start_raw16, sound.sample_end_raw16, sound.lfo_depth) == (
        0x1234,
        0x5678,
        -1.5,
    )

    for track in (-1, 13):
        with pytest.raises(ValueError, match="track index"):
            kit.track_level(track)
        with pytest.raises(ValueError, match="track index"):
            kit.set_track_level(track, 0)
    with pytest.raises(ValueError, match="kit object"):
        RytmKit.from_bytes(bytes(len(kit.to_bytes()) - 1))
    kit.name = "RIO145 AR TEST KIT"
    assert kit.name == "RIO145 AR TEST"
    kit.set_track_level(0, 96)
    assert kit.track_level(0) == 96
    for track in (-1, 12):
        with pytest.raises(ValueError, match="drum track"):
            kit.sound(track)
        with pytest.raises(ValueError, match="drum track"):
            kit.replace_sound(track, sound)
    for operation in (kit.get_fx_u7, kit.set_fx_u7):
        with pytest.raises(KeyError, match="Unknown Rytm FX"):
            operation("unknown", 0) if operation == kit.set_fx_u7 else operation("unknown")
    kit.set_fx_u7("delay_time", 77, clear_lsb=False)
    assert kit.get_fx_u7("delay_time") == 77
    kit.set_fx_bipolar("distortion_symmetry", -4)
    kit.fx_lfo_depth = 2.5
    assert kit.get_fx_bipolar("distortion_symmetry") == -4
    assert kit.fx_lfo_depth == 2.5


@pytest.mark.parametrize("address", [9, 10, 411])
def test_a4_wire_address_translation_rejects_non_fields(address: int) -> None:
    with pytest.raises(ValueError):
        wire_address_to_track_raw_offset(address)
