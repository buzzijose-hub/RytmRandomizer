"""Focused tests for the shared Elektron packed-payload contract."""

from __future__ import annotations

import pytest
from pytest import MonkeyPatch

from rytm_randomizer.snapshot import elektron_packed_payload as payload_contract
from rytm_randomizer.snapshot.elektron_packed_payload import (
    ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
    ElektronPackedPayloadError,
    elektron_packed_payload_checksum,
    encode_elektron_packed_payload,
    split_elektron_packed_payload_body,
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
        expected_trailer_size=ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
        device_label=_LABEL,
    )

    assert validated == encoded
    assert encoded.checksum == sum(_PACKED[1:]) & 0x3FFF
    assert encoded.encoded_length == len(_PACKED) + 5


def test_checksum_rejects_negative_device_slice() -> None:
    with pytest.raises(ElektronPackedPayloadError, match="checksum start"):
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
    with pytest.raises(ElektronPackedPayloadError, match="repacking changed"):
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
    with pytest.raises(ElektronPackedPayloadError, match=message):
        validate_elektron_packed_payload(
            packed,
            trailer,
            checksum_start=0,
            length_adjustment=0,
            expected_packed_size=len(_PACKED),
            expected_trailer_size=ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
            device_label=_LABEL,
        )


def test_packed_payload_body_split_uses_explicit_device_sizes() -> None:
    split = split_elektron_packed_payload_body(
        b"HEAD" + _PACKED + b"TAIL",
        header_size=4,
        trailer_size=4,
        device_label=_LABEL,
    )

    assert split.header == b"HEAD"
    assert split.packed == _PACKED
    assert split.trailer == b"TAIL"


@pytest.mark.parametrize(
    ("header_size", "trailer_size", "message"),
    [
        (-1, 4, "header size"),
        (0, 0, "trailer size"),
        (4, 4, "too short"),
    ],
)
def test_packed_payload_body_split_rejects_invalid_device_sizes(
    header_size: int,
    trailer_size: int,
    message: str,
) -> None:
    with pytest.raises(ElektronPackedPayloadError, match=message):
        split_elektron_packed_payload_body(
            b"short",
            header_size=header_size,
            trailer_size=trailer_size,
            device_label=_LABEL,
        )


def test_validator_rejects_a_noncanonical_expected_trailer_size() -> None:
    with pytest.raises(ElektronPackedPayloadError, match="expected trailer size"):
        validate_elektron_packed_payload(
            _PACKED,
            bytes(4),
            checksum_start=0,
            length_adjustment=0,
            expected_packed_size=len(_PACKED),
            expected_trailer_size=3,
            device_label=_LABEL,
        )


def test_validator_translates_invalid_u14_integrity_values(
    monkeypatch: MonkeyPatch,
) -> None:
    def fail_u14_decoder(_high: int, _low: int) -> int:
        raise ValueError("invalid u14")

    monkeypatch.setattr(payload_contract, "decode_elektron_u14", fail_u14_decoder)

    with pytest.raises(ElektronPackedPayloadError, match="invalid 14-bit value"):
        validate_elektron_packed_payload(
            _PACKED,
            bytes(ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE),
            checksum_start=0,
            length_adjustment=0,
            expected_packed_size=len(_PACKED),
            expected_trailer_size=ELEKTRON_CHECKSUM_LENGTH_TRAILER_SIZE,
            device_label=_LABEL,
        )
