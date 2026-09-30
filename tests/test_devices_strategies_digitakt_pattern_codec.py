"""Digitakt PATTERN codec, proven against real Digitakt MK1 dumps.

These are the promotion evidence ``.claude/rules/targeted-mutation-safety.md``
#6 asks for, for exactly one field (track 1 filter frequency): exact
envelope, checksum, byte isolation, and a byte-exact re-encode.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.data.digitakt_saved_kit_layout import (
    DIGITAKT_II_FAMILY_BYTE,
    DIGITAKT_MK1_PATTERN_FRAMED_SIZE,
    DIGITAKT_MK1_PATTERN_UNPACKED_SIZE,
    DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET,
    DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0,
)
from rytm_randomizer.devices.strategies.digitakt_pattern_codec import (
    DIGITAKT_MK1_PATTERN_LAYOUT,
    DigitaktPatternCodecError,
    DigitaktPatternLayout,
    decode_digitakt_pattern_payload,
    encode_digitakt_pattern_payload,
    is_digitakt_pattern_payload,
)
from rytm_randomizer.snapshot.envelope import Elektron7BitMaskOrder, unpack_elektron_7bit
from rytm_randomizer.snapshot.sysex_file import extract_sysex_payloads

pytestmark = pytest.mark.fast

_FIXTURES: Final[Path] = Path(__file__).resolve().parent / "fixtures" / "digitakt_saved_kit"
_LOW: Final[Path] = _FIXTURES / "digitakt_mk1_kit_filter_low.syx"
_HIGH: Final[Path] = _FIXTURES / "digitakt_mk1_kit_filter_high.syx"
_KIT_MARKER: Final[bytes] = bytes.fromhex("beefbace")


def _payload(path: Path) -> bytes:
    framed = path.read_bytes()
    assert len(framed) == DIGITAKT_MK1_PATTERN_FRAMED_SIZE
    (payload,) = extract_sysex_payloads(framed)
    return payload


@pytest.mark.parametrize("path", [_LOW, _HIGH], ids=["low", "high"])
def test_real_pattern_decodes_and_re_encodes_byte_for_byte(path: Path) -> None:
    payload = _payload(path)
    decoded = decode_digitakt_pattern_payload(payload, DIGITAKT_MK1_PATTERN_LAYOUT)

    assert len(decoded.unpacked) == DIGITAKT_MK1_PATTERN_UNPACKED_SIZE
    assert (
        encode_digitakt_pattern_payload(
            decoded.prefix, decoded.unpacked, DIGITAKT_MK1_PATTERN_LAYOUT
        )
        == payload
    )


def test_the_captures_differ_in_exactly_the_promoted_byte() -> None:
    low = decode_digitakt_pattern_payload(_payload(_LOW), DIGITAKT_MK1_PATTERN_LAYOUT)
    high = decode_digitakt_pattern_payload(_payload(_HIGH), DIGITAKT_MK1_PATTERN_LAYOUT)

    changed = [
        i for i, (a, b) in enumerate(zip(low.unpacked, high.unpacked, strict=True)) if a != b
    ]
    assert changed == [DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET]
    assert low.unpacked[DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET] == 0
    assert high.unpacked[DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET] == 127


def test_writing_the_promoted_byte_reproduces_the_other_real_capture() -> None:
    """The strongest check available offline: edit low -> exactly high, trailer included."""

    low = decode_digitakt_pattern_payload(_payload(_LOW), DIGITAKT_MK1_PATTERN_LAYOUT)
    body = bytearray(low.unpacked)
    body[DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET] = 127

    rebuilt = encode_digitakt_pattern_payload(low.prefix, bytes(body), DIGITAKT_MK1_PATTERN_LAYOUT)
    assert rebuilt == _payload(_HIGH)


def test_msb_first_is_the_only_mask_order_that_reveals_the_kit_marker() -> None:
    packed = decode_digitakt_pattern_payload(_payload(_LOW), DIGITAKT_MK1_PATTERN_LAYOUT).packed
    msb = unpack_elektron_7bit(packed, mask_order=Elektron7BitMaskOrder.MSB_FIRST)
    lsb = unpack_elektron_7bit(packed, mask_order=Elektron7BitMaskOrder.LSB_FIRST)
    assert msb.count(_KIT_MARKER) == 8
    assert lsb.count(_KIT_MARKER) == 0


def test_unverified_stride_observation_is_recorded_not_promoted() -> None:
    """Evidence for step 2, deliberately NOT a fact in data/.

    Eight named sound blocks sit 160 bytes apart; 68 bytes into each is 127
    (the default open filter) except track 1, which the verifier turned to 0.
    A matched capture on another track is what promotes a stride.
    """

    unpacked = decode_digitakt_pattern_payload(_payload(_LOW), DIGITAKT_MK1_PATTERN_LAYOUT).unpacked
    blocks = [25136 + 160 * track for track in range(8)]
    assert [unpacked[b : b + 7] for b in blocks] == [f"SOUND {n}".encode() for n in range(1, 9)]
    assert [unpacked[b + 68] for b in blocks] == [0, 127, 127, 127, 127, 127, 127, 127]
    assert blocks[0] + 68 == DIGITAKT_MK1_TRACK1_FILTER_FREQUENCY_OFFSET


# ---------------------------------------------------------------------------
# Refusals
# ---------------------------------------------------------------------------


def test_is_pattern_payload_checks_manufacturer_family_and_object() -> None:
    payload = _payload(_LOW)
    assert is_digitakt_pattern_payload(payload, DIGITAKT_MK1_PATTERN_LAYOUT)
    assert not is_digitakt_pattern_payload(payload[:5], DIGITAKT_MK1_PATTERN_LAYOUT)
    assert not is_digitakt_pattern_payload(
        b"\x00\x00\x41" + payload[3:], DIGITAKT_MK1_PATTERN_LAYOUT
    )
    other_object = payload[:5] + b"\x51" + payload[6:]
    assert not is_digitakt_pattern_payload(other_object, DIGITAKT_MK1_PATTERN_LAYOUT)
    ii = DigitaktPatternLayout(family_byte=DIGITAKT_II_FAMILY_BYTE, packed_size=1, unpacked_size=1)
    assert not is_digitakt_pattern_payload(payload, ii)


def test_decode_refuses_a_payload_of_the_wrong_size() -> None:
    with pytest.raises(DigitaktPatternCodecError, match="expected 31611"):
        decode_digitakt_pattern_payload(_payload(_LOW)[:-1], DIGITAKT_MK1_PATTERN_LAYOUT)


def test_decode_refuses_a_foreign_header() -> None:
    payload = bytearray(_payload(_LOW))
    payload[5] = 0x51
    with pytest.raises(DigitaktPatternCodecError, match="not a Digitakt pattern header"):
        decode_digitakt_pattern_payload(bytes(payload), DIGITAKT_MK1_PATTERN_LAYOUT)


@pytest.mark.parametrize("index,match", [(-5, "checksum"), (-2, "length")])
def test_decode_refuses_a_corrupted_trailer(index: int, match: str) -> None:
    payload = bytearray(_payload(_LOW))
    payload[index] ^= 0x01
    with pytest.raises(DigitaktPatternCodecError, match=match):
        decode_digitakt_pattern_payload(bytes(payload), DIGITAKT_MK1_PATTERN_LAYOUT)


def test_decode_refuses_a_non_7_bit_body_byte() -> None:
    payload = bytearray(_payload(_LOW))
    payload[DIGITAKT_PATTERN_HEADER_SIZE_WITHOUT_F0 + 1] = 0x80
    with pytest.raises(DigitaktPatternCodecError):
        decode_digitakt_pattern_payload(bytes(payload), DIGITAKT_MK1_PATTERN_LAYOUT)


def test_decode_refuses_a_layout_whose_unpacked_size_disagrees() -> None:
    wrong = DigitaktPatternLayout(
        family_byte=DIGITAKT_MK1_PATTERN_LAYOUT.family_byte,
        packed_size=DIGITAKT_MK1_PATTERN_LAYOUT.packed_size,
        unpacked_size=DIGITAKT_MK1_PATTERN_UNPACKED_SIZE + 1,
    )
    with pytest.raises(DigitaktPatternCodecError, match="unpacks to 27648 bytes"):
        decode_digitakt_pattern_payload(_payload(_LOW), wrong)


def test_encode_refuses_a_wrong_prefix_or_body_size() -> None:
    decoded = decode_digitakt_pattern_payload(_payload(_LOW), DIGITAKT_MK1_PATTERN_LAYOUT)
    with pytest.raises(DigitaktPatternCodecError, match="not a Digitakt pattern header"):
        encode_digitakt_pattern_payload(
            decoded.prefix[:-1], decoded.unpacked, DIGITAKT_MK1_PATTERN_LAYOUT
        )
    with pytest.raises(DigitaktPatternCodecError, match="body is 27647 bytes"):
        encode_digitakt_pattern_payload(
            decoded.prefix, decoded.unpacked[:-1], DIGITAKT_MK1_PATTERN_LAYOUT
        )
