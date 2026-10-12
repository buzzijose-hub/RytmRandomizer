"""Independent semantic and source-kind tests for passive A4 KIT responses."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import decode_kit_capture_frame
from rytm_randomizer.devices import get_device
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
)
from rytm_randomizer.snapshot import Elektron7BitMaskOrder, pack_elektron_7bit

pytestmark = pytest.mark.fast

_REFERENCE = Path(__file__).parent / "fixtures/native_representation/a4_init_retained.syx"
_REFERENCE_SHA = "50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e"


def _retained_frame() -> bytes:
    frame = _REFERENCE.read_bytes()
    assert sha256(frame).hexdigest() == _REFERENCE_SHA
    return frame


def _synthetic_response(
    *, command: int = 0x52, changes: tuple[tuple[int, bytes], ...] = ()
) -> bytes:
    frame = _retained_frame()
    decoded = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True)
    body = bytearray(decoded.unpacked)
    for offset, value in changes:
        body[offset : offset + len(value)] = value
    packed = pack_elektron_7bit(bytes(body), mask_order=Elektron7BitMaskOrder.MSB_FIRST)
    checksum = sum(packed) & 0x3FFF
    length = len(packed) + 5
    header = bytearray(frame[:10])
    header[6] = command
    return (
        bytes(header)
        + packed
        + bytes((checksum >> 7, checksum & 127, length >> 7, length & 127, 0xF7))
    )


def test_retained_init_has_four_literal_native_f1_words_and_sound_structures() -> None:
    frame = _retained_frame()
    decoded = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True)
    assert len(decoded.prefix) == 9
    assert len(decoded.unpacked) == 2410
    assert int.from_bytes(decoded.unpacked[:4], "big") == 11
    for index, offset in enumerate((128, 478, 828, 1178)):
        sound = 32 + 350 * index
        assert decoded.unpacked[sound : sound + 4] == bytes.fromhex("beefbaba")
        assert int.from_bytes(decoded.unpacked[sound + 4 : sound + 8], "big") == 6
        assert decoded.unpacked[sound + 346 : sound + 350] == bytes.fromhex("babeface")
        assert decoded.unpacked[offset : offset + 2] == b"\x7f\x00"
    device = get_device("analog_four_mk2")
    assert device.encode_saved_kit_capture(device.decode_saved_kit_capture(frame)) == frame
    assert sha256(_REFERENCE.read_bytes()).hexdigest() == _REFERENCE_SHA


@pytest.mark.parametrize("command,layout", [(0x52, "saved_kit"), (0x58, "working_kit")])
def test_response_kind_is_separate_without_changing_raw_or_decoded_identity(
    command: int, layout: str
) -> None:
    frame = _synthetic_response(command=command)
    result = decode_kit_capture_frame("analog_four_mk2", frame)
    assert result.snapshot_layout == layout
    assert result.frame == frame
    assert result.snapshot.raw == frame[1:-1]
    assert result.fingerprint == sha256(result.snapshot.unpacked).hexdigest()[:16]
    assert result.to_dict()["input_only"] is True
    assert result.to_dict()["sent_midi"] is False
    if command == 0x58:
        assert result.parameter_readiness == "exact_kit_anchor_offsets_candidate"
        assert all(item.status == "captured_mapping_pending" for item in result.layout_items)
        assert all("freshness" in item.detail for item in result.layout_items)


def test_working_and_indexed_same_body_share_coordinates_not_raw_identity() -> None:
    indexed = decode_kit_capture_frame("analog_four_mk2", _synthetic_response())
    working = decode_kit_capture_frame("analog_four_mk2", _synthetic_response(command=0x58))
    assert indexed.snapshot.unpacked == working.snapshot.unpacked
    assert indexed.fingerprint == working.fingerprint
    assert indexed.frame != working.frame
    assert sha256(indexed.frame).digest() != sha256(working.frame).digest()


@pytest.mark.parametrize("header_offset,value", [(5, 1), (7, 2), (8, 2)])
def test_unsupported_device_or_protocol_refuses_even_with_valid_body_integrity(
    header_offset: int, value: int
) -> None:
    frame = bytearray(_retained_frame())
    frame[header_offset] = value
    with pytest.raises(ValueError):
        decode_kit_capture_frame("analog_four_mk2", bytes(frame))


@pytest.mark.parametrize("track", range(4))
@pytest.mark.parametrize(
    "relative,value", [(0, b"\0\0\0\0"), (4, b"\0\0\0\x07"), (346, b"\0\0\0\0")]
)
def test_invalid_sound_binding_structure_refuses_a_checksumming_response(
    track: int, relative: int, value: bytes
) -> None:
    frame = _synthetic_response(changes=((32 + 350 * track + relative, value),))
    with pytest.raises(ValueError):
        decode_kit_capture_frame("analog_four_mk2", frame)


@pytest.mark.parametrize("command", (0x52, 0x58))
def test_unavailable_kit_storage_refuses_instead_of_accepting_zero_fallback(command: int) -> None:
    frame = _synthetic_response(command=command, changes=((0, bytes(2410)),))
    with pytest.raises(ValueError):
        decode_kit_capture_frame("analog_four_mk2", frame)


def test_noncanonical_group_padding_cannot_become_a_passive_source() -> None:
    frame = bytearray(_retained_frame())
    # 2410 = 344 complete groups + two bytes; low five mask bits are unused.
    frame[10 + 344 * 8] |= 1
    checksum = sum(frame[10:-5]) & 0x3FFF
    frame[-5:-3] = bytes((checksum >> 7, checksum & 127))
    with pytest.raises(ValueError):
        decode_kit_capture_frame("analog_four_mk2", bytes(frame))
    with pytest.raises(ValueError, match="padding"):
        decode_analog_four_saved_kit_payload(bytes(frame)[1:-1], require_trailer=True)


def test_working_response_cannot_enter_an_existing_indexed_candidate_writer() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate import (
        validate_analog_four_candidate_source,
    )

    frame = _synthetic_response(command=0x58)
    with pytest.raises(ValueError, match="passive evidence"):
        validate_analog_four_candidate_source(frame)
    inspected = validate_analog_four_candidate_source(frame, allow_working=True)
    assert inspected.unpacked[128:130] == b"\x7f\x00"
    assert inspected.prefix[5] == 0x58


def test_working_response_without_integrity_cannot_claim_source_availability() -> None:
    header = bytearray(_retained_frame()[1:10])
    header[5] = 0x58
    short_body = pack_elektron_7bit(bytes(32), mask_order=Elektron7BitMaskOrder.MSB_FIRST)
    with pytest.raises(ValueError, match="complete integrity validation"):
        decode_analog_four_saved_kit_payload(bytes(header) + short_body, require_trailer=False)


def test_encoder_rejects_non_midi_header_and_candidate_rejects_dependency_reencode_drift(
    monkeypatch,
) -> None:
    from dataclasses import replace

    from rytm_randomizer.devices.strategies import analog_four_saved_kit_candidate as candidate
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    source = _retained_frame()
    decoded = decode_analog_four_saved_kit_payload(source[1:-1], require_trailer=True)
    with pytest.raises(ValueError, match="MIDI data domain"):
        encode_analog_four_saved_kit_payload(decoded.prefix[:-1] + b"\x80", decoded.unpacked)

    def drift(prefix, unpacked):
        encoded = encode_analog_four_saved_kit_payload(prefix, unpacked)
        return replace(encoded, prefix=prefix[:-1] + bytes(((prefix[-1] + 1) % 128,)))

    monkeypatch.setattr(candidate, "encode_analog_four_saved_kit_payload", drift)
    with pytest.raises(ValueError, match="round-trip byte-identically"):
        candidate.validate_analog_four_candidate_source(source)


@pytest.mark.parametrize("track", range(4))
def test_legal_maximum_is_passively_readable_without_broadening_old_mutation_sampling(
    track: int,
) -> None:
    from rytm_randomizer.devices.strategies.analog_four_native_fields import (
        read_analog_four_native_fields,
    )

    frame = _synthetic_response(changes=((128 + 350 * track, b"\x7f\xfe"),))
    value = read_analog_four_native_fields(frame).value("filter1_frequency", track + 1)
    assert value.encoded_native == 32766
    assert value.source_value_known is True
    assert value.device_screen_label == "127.99"
    assert value.screen_value == "127.9921875"
    assert value.mutable is False
    assert value.protection_reason == "outside_existing_f1_mutation_evidence"


@pytest.mark.parametrize("track", range(4))
def test_f1_word32767_is_not_supported_even_if_q8_mathematics_can_format_it(track: int) -> None:
    frame = _synthetic_response(changes=((128 + 350 * track, b"\x7f\xff"),))
    with pytest.raises(ValueError, match="F1 native word"):
        decode_kit_capture_frame("analog_four_mk2", frame)


def test_working_native_inspection_does_not_offer_mutable_cells() -> None:
    from rytm_randomizer.devices.strategies.analog_four_native_fields import (
        read_analog_four_native_fields,
    )

    inspected = read_analog_four_native_fields(_synthetic_response(command=0x58))
    assert all(not cell.mutable for cell in inspected.values)
    assert all(
        cell.protection_reason == "working_kit_freshness_unverified" for cell in inspected.values
    )
    assert inspected.value("filter1_frequency", 1).device_screen_label == "127.00"
