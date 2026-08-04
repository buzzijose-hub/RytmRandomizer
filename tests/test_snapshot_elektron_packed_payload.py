"""Focused tests for the shared Elektron packed-payload contract."""

from __future__ import annotations

import pytest

from rytm_randomizer.snapshot.elektron_packed_payload import (
    elektron_packed_payload_checksum,
    encode_elektron_packed_payload,
    validate_elektron_packed_payload,
)
from rytm_randomizer.snapshot.elektron_u14 import encode_elektron_u14
from rytm_randomizer.snapshot.envelope import pack_elektron_7bit

pytestmark = pytest.mark.fast

_LABEL = "Test Elektron object"
_UNPACKED = bytes((0x80, 0x01, 0x7F, 0xFF, 0x00, 0x40, 0x20, 0x10))
_PACKED = pack_elektron_7bit(_UNPACKED)


def test_packed_payload_contract_round_trips_device_facts() -> None:
    encoded = encode_elektron_packed_payload(
        _UNPACKED,
        checksum_start=1,
        length_adjustment=5,
        expected_packed_size=len(_PACKED),
        device_label=_LABEL,
    )

    validated = validate_elektron_packed_payload(
        encoded.packed,
        encoded.trailer,
        checksum_start=1,
        length_adjustment=5,
        expected_packed_size=len(_PACKED),
        device_label=_LABEL,
    )

    assert validated == encoded
    assert encoded.checksum == sum(_PACKED[1:]) & 0x3FFF
    assert encoded.encoded_length == len(_PACKED) + 5


def test_checksum_rejects_negative_device_slice() -> None:
    with pytest.raises(ValueError, match="checksum start"):
        elektron_packed_payload_checksum(
            _PACKED,
            checksum_start=-1,
            device_label=_LABEL,
        )


def test_checksum_preserves_empty_slice_behavior_for_short_payloads() -> None:
    assert (
        elektron_packed_payload_checksum(
            _PACKED,
            checksum_start=len(_PACKED) + 1,
            device_label=_LABEL,
        )
        == 0
    )


def test_encoder_rejects_unexpected_device_packed_size() -> None:
    with pytest.raises(ValueError, match="repacking changed"):
        encode_elektron_packed_payload(
            _UNPACKED,
            checksum_start=0,
            length_adjustment=0,
            expected_packed_size=len(_PACKED) + 1,
            device_label=_LABEL,
        )


@pytest.mark.parametrize(
    ("packed", "trailer", "message"),
    [
        (_PACKED[:-1], bytes(4), "packed payload"),
        (_PACKED, bytes(3), "integrity trailer"),
        (
            _PACKED,
            encode_elektron_u14(1) + encode_elektron_u14(len(_PACKED)),
            "checksum",
        ),
        (
            _PACKED,
            encode_elektron_u14(sum(_PACKED) & 0x3FFF) + encode_elektron_u14(len(_PACKED) + 1),
            "packed length",
        ),
    ],
)
def test_validator_rejects_integrity_mismatches(
    packed: bytes,
    trailer: bytes,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_elektron_packed_payload(
            packed,
            trailer,
            checksum_start=0,
            length_adjustment=0,
            expected_packed_size=len(_PACKED),
            device_label=_LABEL,
        )
