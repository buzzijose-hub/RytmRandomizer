from __future__ import annotations

import os
from pathlib import Path

import pytest
from pytest import MonkeyPatch

from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_PACKED_SIZE,
    RYTM_KIT_RAW_SIZE,
)
from rytm_randomizer.devices.strategies import analog_rytm_saved_kit_codec as codec
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from rytm_randomizer.snapshot.elektron_u14 import (
    decode_elektron_u14,
    encode_elektron_u14,
)

pytestmark = pytest.mark.fast

_HEADER = bytes((0x00, 0x20, 0x3C, 0x07, 0x00, 0x52, 0x01, 0x01, 0x00))


def _synthetic_raw() -> bytes:
    return bytes(((index * 37) + 193) & 0xFF for index in range(RYTM_KIT_RAW_SIZE))


def test_analog_rytm_saved_kit_frame_round_trips_byte_identically() -> None:
    frame = encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw())

    decoded = decode_analog_rytm_saved_kit_frame(frame)

    assert decoded.header == _HEADER
    assert decoded.unpacked == _synthetic_raw()
    assert encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked) == frame
    assert frame[0] == 0xF0
    assert frame[-1] == 0xF7
    assert all(value < 0x80 for value in frame[1:-1])


def test_analog_rytm_saved_kit_frame_rejects_checksum_corruption() -> None:
    frame = bytearray(encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw()))
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
    frame = encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw())
    mutate = mutation
    assert callable(mutate)

    with pytest.raises(ValueError, match=message):
        decode_analog_rytm_saved_kit_frame(mutate(frame))


def test_analog_rytm_saved_kit_header_requires_exact_length() -> None:
    with pytest.raises(ValueError, match="header has an unexpected length"):
        codec._validate_header(_HEADER[:-1])


def test_analog_rytm_saved_kit_frame_rejects_wrong_encoded_length() -> None:
    frame = bytearray(encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw()))
    frame[-2] ^= 1

    with pytest.raises(ValueError, match="encoded length"):
        decode_analog_rytm_saved_kit_frame(bytes(frame))


def test_analog_rytm_saved_kit_frame_checks_packed_and_unpacked_sizes(
    monkeypatch: MonkeyPatch,
) -> None:
    frame = encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw())
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
        encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw()[:-1])

    monkeypatch.setattr(codec, "RYTM_KIT_PACKED_SIZE", RYTM_KIT_PACKED_SIZE + 1)
    with pytest.raises(ValueError, match="repacking changed"):
        encode_analog_rytm_saved_kit_frame(_HEADER, _synthetic_raw())


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
