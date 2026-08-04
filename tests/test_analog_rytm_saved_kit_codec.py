from __future__ import annotations

import os
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from conftest import (
    ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
    analog_rytm_saved_kit_test_raw,
)
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_PACKED_SIZE,
    RYTM_KIT_RAW_SIZE,
)
from rytm_randomizer.devices.strategies import analog_rytm_saved_kit_codec as codec
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    analog_rytm_saved_kit_checksum,
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from rytm_randomizer.snapshot.elektron_u14 import (
    decode_elektron_u14,
    encode_elektron_u14,
)

pytestmark = pytest.mark.fast

_HEADER = ANALOG_RYTM_SAVED_KIT_TEST_HEADER
_KNOWN_ANSWER_RAW_SIZE = 2610
_KNOWN_ANSWER_PACKED_SIZE = 2983
_KNOWN_ANSWER_FRAME_SHA256 = "ac2df4c38f71c7d9b55fff116d7129109b7693d9be60163415af363fd9850210"
_KNOWN_ANSWER_ZERO_FRAME = (
    b"\xf0" + _HEADER + bytes(_KNOWN_ANSWER_PACKED_SIZE) + bytes.fromhex("0000172c") + b"\xf7"
)


def test_analog_rytm_saved_kit_checksum_matches_independent_sum() -> None:
    packed = bytes((1, 2, 3, 4, 5, 6, 7, 8, 127))

    assert analog_rytm_saved_kit_checksum(packed) == sum(packed) & 0x3FFF


def test_analog_rytm_saved_kit_frame_round_trips_byte_identically() -> None:
    raw = analog_rytm_saved_kit_test_raw()
    frame = encode_analog_rytm_saved_kit_frame(_HEADER, raw)

    decoded = decode_analog_rytm_saved_kit_frame(frame)

    assert decoded.header == _HEADER
    assert decoded.unpacked == raw
    assert encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked) == frame
    assert frame[0] == 0xF0
    assert frame[-1] == 0xF7
    assert all(value < 0x80 for value in frame[1:-1])


def test_analog_rytm_saved_kit_matches_independent_frozen_known_answer() -> None:
    """Pin decoding and encoding to a frame not constructed by production code."""

    import hashlib

    assert RYTM_KIT_RAW_SIZE == _KNOWN_ANSWER_RAW_SIZE
    assert RYTM_KIT_PACKED_SIZE == _KNOWN_ANSWER_PACKED_SIZE
    assert hashlib.sha256(_KNOWN_ANSWER_ZERO_FRAME).hexdigest() == _KNOWN_ANSWER_FRAME_SHA256

    decoded = decode_analog_rytm_saved_kit_frame(_KNOWN_ANSWER_ZERO_FRAME)

    assert decoded.header == _HEADER
    assert decoded.unpacked == bytes(_KNOWN_ANSWER_RAW_SIZE)
    assert (
        encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked)
        == _KNOWN_ANSWER_ZERO_FRAME
    )


def test_analog_rytm_saved_kit_frame_rejects_checksum_corruption() -> None:
    frame = bytearray(encode_analog_rytm_saved_kit_frame(_HEADER, analog_rytm_saved_kit_test_raw()))
    frame[-5] ^= 1

    with pytest.raises(ValueError, match="checksum"):
        decode_analog_rytm_saved_kit_frame(bytes(frame))


@pytest.mark.parametrize(
    ("mutation", "message"),
    [
        (lambda frame: frame[:-1], "frame length"),
        (lambda frame: bytes((0x00,)) + frame[1:], "framing"),
        (lambda frame: frame[:10] + bytes((0x80,)) + frame[11:], "illegal data byte"),
        (lambda frame: frame[:4] + bytes((0x08,)) + frame[5:], "not an Analog Rytm"),
        (lambda frame: frame[:6] + bytes((0x51,)) + frame[7:], "not a kit dump"),
    ],
)
def test_analog_rytm_saved_kit_frame_rejects_invalid_envelopes(
    mutation: object,
    message: str,
) -> None:
    frame = encode_analog_rytm_saved_kit_frame(
        _HEADER,
        analog_rytm_saved_kit_test_raw(),
    )
    mutate = mutation
    assert callable(mutate)

    with pytest.raises(ValueError, match=message):
        decode_analog_rytm_saved_kit_frame(mutate(frame))


def test_analog_rytm_saved_kit_header_requires_exact_length() -> None:
    with pytest.raises(ValueError, match="header has an unexpected length"):
        codec._validate_header(_HEADER[:-1])


def test_analog_rytm_saved_kit_frame_rejects_wrong_encoded_length() -> None:
    frame = bytearray(encode_analog_rytm_saved_kit_frame(_HEADER, analog_rytm_saved_kit_test_raw()))
    frame[-2] ^= 1

    with pytest.raises(ValueError, match="encoded length"):
        decode_analog_rytm_saved_kit_frame(bytes(frame))


def test_analog_rytm_saved_kit_frame_checks_packed_and_unpacked_sizes(
    monkeypatch: MonkeyPatch,
) -> None:
    frame = encode_analog_rytm_saved_kit_frame(
        _HEADER,
        analog_rytm_saved_kit_test_raw(),
    )
    monkeypatch.setattr(codec, "RYTM_KIT_PACKED_SIZE", RYTM_KIT_PACKED_SIZE + 1)
    with pytest.raises(ValueError, match="packed payload"):
        decode_analog_rytm_saved_kit_frame(frame)

    monkeypatch.setattr(codec, "RYTM_KIT_PACKED_SIZE", RYTM_KIT_PACKED_SIZE)
    monkeypatch.setattr(codec, "RYTM_KIT_RAW_SIZE", RYTM_KIT_RAW_SIZE + 1)
    with pytest.raises(ValueError, match="unexpected unpacked length"):
        decode_analog_rytm_saved_kit_frame(frame)


def test_analog_rytm_saved_kit_encoder_rejects_invalid_sizes(
    monkeypatch: MonkeyPatch,
) -> None:
    with pytest.raises(ValueError, match="body has an unexpected unpacked length"):
        encode_analog_rytm_saved_kit_frame(
            _HEADER,
            analog_rytm_saved_kit_test_raw()[:-1],
        )

    monkeypatch.setattr(codec, "RYTM_KIT_PACKED_SIZE", RYTM_KIT_PACKED_SIZE + 1)
    with pytest.raises(ValueError, match="repacking changed"):
        encode_analog_rytm_saved_kit_frame(
            _HEADER,
            analog_rytm_saved_kit_test_raw(),
        )


@pytest.mark.parametrize(("high", "low"), [(-1, 0), (0, 128)])
def test_elektron_u14_decoder_rejects_non_data_bytes(high: int, low: int) -> None:
    with pytest.raises(ValueError, match="range 0..127"):
        decode_elektron_u14(high, low)


@pytest.mark.parametrize("value", [-1, 16384])
def test_elektron_u14_encoder_rejects_out_of_range_values(value: int) -> None:
    with pytest.raises(ValueError, match="outside 0..16383"):
        encode_elektron_u14(value)


def test_local_initialized_reference_round_trips_when_supplied() -> None:
    reference_name = os.environ.get("RYTM_TEST_REFERENCE")
    if reference_name is None:
        pytest.skip("RYTM_TEST_REFERENCE is not supplied; private hardware dump is optional")
    reference = Path(reference_name).read_bytes()

    decoded = decode_analog_rytm_saved_kit_frame(reference)

    assert encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked) == reference
