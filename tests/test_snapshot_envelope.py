"""WS-S6 tests: generic Elektron SysEx envelope + decoder/planner/runtime Protocols.

The :mod:`rytm_randomizer.snapshot` subpackage is the shared base every
Elektron-device snapshot decoder lands on. PR #21 (codex's Analog Four
bridge) currently duplicates these helpers per device; this WS centralises
them so the PR #21 module count collapses from 8 files to 1.

Test naming: ``test_<unit>_<behavior>_when_<condition>`` per Gate 8.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Helper: a hand-written 7-bit packer mirroring the unpack contract so the
# round-trip test can express "pack then unpack returns identity" without
# depending on a real Elektron SysEx capture.
# ---------------------------------------------------------------------------


def _pack_elektron_7bit(payload: bytes) -> bytes:
    """Inverse of ``unpack_elektron_7bit``. Test-local helper only.

    Wraps the payload using Elektron's "MSB header" encoding: every group
    of up to 7 input bytes becomes (1 header byte) + (up to 7 data
    bytes) where the header's low-7 bits carry the bit-7 of each data
    byte, in order.
    """

    out = bytearray()
    for group_start in range(0, len(payload), 7):
        group = payload[group_start : group_start + 7]
        header = 0
        for bit_index, byte in enumerate(group):
            header |= ((byte >> 7) & 0x01) << bit_index
        out.append(header)
        out.extend(byte & 0x7F for byte in group)
    return bytes(out)


def _codec_spec(**overrides: object):
    from rytm_randomizer.snapshot import ElektronKitEnvelopeSpec

    values = {
        "label": "Synthetic Elektron kit",
        "required_header_prefix": b"\x00\x20\x3c\x55",
        "header_size_without_f0": 4,
        "unpacked_size": 9,
        "checksum_packed_start": 0,
        "length_adjustment": 0,
        "required_unpacked_prefix": b"\x52",
    }
    values.update(overrides)
    return ElektronKitEnvelopeSpec(**values)


def _codec_frame(spec, unpacked: bytes = b"\x52\x80\x01\x02\x03\x04\x05\x06\x07") -> bytes:
    from rytm_randomizer.snapshot import encode_elektron_u14, pack_elektron_7bit

    header = spec.required_header_prefix.ljust(spec.header_size_without_f0, b"\x00")
    packed = pack_elektron_7bit(unpacked)
    checksum = sum(packed[spec.checksum_packed_start :]) & 0x3FFF
    length = len(packed) + spec.length_adjustment
    return (
        b"\xf0"
        + header
        + packed
        + encode_elektron_u14(checksum)
        + encode_elektron_u14(length)
        + b"\xf7"
    )


# ---------------------------------------------------------------------------
# 1. Subpackage surface
# ---------------------------------------------------------------------------


def test_snapshot_subpackage_exports_expected_public_names() -> None:
    import rytm_randomizer.snapshot as snapshot

    expected = {
        "ELEKTRON_MFR_ID",
        "BaseMockRuntime",
        "MockRuntime",
        "MutationPlanner",
        "SnapshotDecoder",
        "DecodedElektronKitFrame",
        "ElektronKitCodec",
        "ElektronKitEnvelopeSpec",
        "decode_elektron_u14",
        "encode_elektron_u14",
        "find_kit_record",
        "format_manufacturer_id",
        "pack_elektron_7bit",
        "read_ascii_name",
        "unpack_elektron_7bit",
    }
    assert expected.issubset(set(snapshot.__all__))


# ---------------------------------------------------------------------------
# 2. ELEKTRON_MFR_ID constant
# ---------------------------------------------------------------------------


def test_elektron_mfr_id_matches_documented_three_byte_value() -> None:
    """Elektron's manufacturer ID is 00:20:3C (documented in every MIDI spec)."""

    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

    assert bytes([0x00, 0x20, 0x3C]) == ELEKTRON_MFR_ID
    assert len(ELEKTRON_MFR_ID) == 3


def test_elektron_mfr_id_matches_devices_subpackage_value() -> None:
    """Sanity check: both subpackages must agree on the constant."""

    from rytm_randomizer.devices.analog_rytm import _ELEKTRON_MFR_ID
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

    assert ELEKTRON_MFR_ID == _ELEKTRON_MFR_ID


# ---------------------------------------------------------------------------
# 3. unpack_elektron_7bit
# ---------------------------------------------------------------------------


def test_unpack_elektron_7bit_round_trip_on_small_fixture() -> None:
    """pack(unpack(x)) == x on a fixture exercising bit-7 in every position."""

    from rytm_randomizer.snapshot import unpack_elektron_7bit

    payload = bytes([0xFF, 0x00, 0x80, 0x01, 0x00, 0xA5, 0xFF])
    packed = _pack_elektron_7bit(payload)
    assert unpack_elektron_7bit(packed) == payload


def test_unpack_elektron_7bit_round_trip_across_group_boundary() -> None:
    """A payload longer than 7 bytes spans multiple header groups."""

    from rytm_randomizer.snapshot import unpack_elektron_7bit

    payload = bytes(range(20))  # 20 bytes -> 2 full groups + a short tail
    packed = _pack_elektron_7bit(payload)
    assert unpack_elektron_7bit(packed) == payload


def test_pack_elektron_7bit_is_exact_inverse_across_group_boundary() -> None:
    from rytm_randomizer.snapshot import pack_elektron_7bit, unpack_elektron_7bit

    payload = bytes([0x00, 0x80, 0x7F, 0xFF, 0x01, 0x81, 0x55, 0xAA, 0x42])

    assert pack_elektron_7bit(payload) == _pack_elektron_7bit(payload)
    assert unpack_elektron_7bit(pack_elektron_7bit(payload)) == payload


def test_pack_elektron_7bit_returns_empty_on_empty_input() -> None:
    from rytm_randomizer.snapshot import pack_elektron_7bit

    assert pack_elektron_7bit(b"") == b""


def test_elektron_u14_round_trip_accepts_full_range() -> None:
    from rytm_randomizer.snapshot import decode_elektron_u14, encode_elektron_u14

    for value in (0, 1, 0x7F, 0x80, 0x3FFF):
        assert decode_elektron_u14(encode_elektron_u14(value)) == value


def test_encode_elektron_u14_rejects_out_of_range_value() -> None:
    from rytm_randomizer.snapshot import encode_elektron_u14

    with pytest.raises(ValueError, match="0..16383"):
        encode_elektron_u14(0x4000)


def test_decode_elektron_u14_rejects_wrong_width_and_illegal_data() -> None:
    from rytm_randomizer.snapshot import decode_elektron_u14

    with pytest.raises(ValueError, match="exactly two"):
        decode_elektron_u14(b"\x00")
    with pytest.raises(ValueError, match="7-bit"):
        decode_elektron_u14(b"\x00\x80")


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"label": ""}, "label"),
        ({"required_header_prefix": b""}, "required_header_prefix"),
        ({"header_size_without_f0": 3}, "must cover"),
        ({"unpacked_size": 0}, "must be positive"),
        ({"checksum_packed_start": -1}, "must be non-negative"),
        ({"length_adjustment": -1}, "must be non-negative"),
        ({"unpacked_size": 1, "required_unpacked_prefix": b"\x52\x01"}, "exceeds"),
    ),
)
def test_elektron_kit_envelope_spec_rejects_invalid_configuration(
    overrides: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _codec_spec(**overrides)


def test_elektron_kit_codec_round_trip_preserves_reference_header() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    spec = _codec_spec(header_size_without_f0=6)
    frame = _codec_frame(spec)
    decoded = ElektronKitCodec(spec).decode_frame(frame)

    assert decoded.header == b"\x00\x20\x3c\x55\x00\x00"
    assert decoded.unpacked == b"\x52\x80\x01\x02\x03\x04\x05\x06\x07"
    assert ElektronKitCodec(spec).encode_frame(decoded) == frame


def test_elektron_kit_codec_rejects_none_short_and_bad_framing() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    codec = ElektronKitCodec(_codec_spec())
    frame = _codec_frame(codec.spec)

    with pytest.raises(ValueError, match="frame is None"):
        codec.decode_frame(cast(bytes, None))
    with pytest.raises(ValueError, match="minimum"):
        codec.decode_frame(b"\xf0\xf7")
    with pytest.raises(ValueError, match="F0/F7"):
        codec.decode_frame(b"\x00" + frame[1:])
    with pytest.raises(ValueError, match="F0/F7"):
        codec.decode_frame(frame[:-1] + b"\x00")


def test_elektron_kit_codec_rejects_illegal_data_and_wrong_header() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    spec = _codec_spec()
    codec = ElektronKitCodec(spec)
    frame = _codec_frame(spec)
    illegal = bytearray(frame)
    illegal[2] = 0x80
    wrong_header = bytearray(frame)
    wrong_header[4] = 0x54

    with pytest.raises(ValueError, match="outside the 7-bit"):
        codec.decode_frame(bytes(illegal))
    with pytest.raises(ValueError, match="header prefix mismatch"):
        codec.decode_frame(bytes(wrong_header))


def test_elektron_kit_codec_rejects_empty_payload_and_bad_checksum_start() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec, encode_elektron_u14

    spec = _codec_spec()
    empty = (
        b"\xf0"
        + spec.required_header_prefix
        + encode_elektron_u14(0)
        + encode_elektron_u14(0)
        + b"\xf7"
    )
    with pytest.raises(ValueError, match="payload is empty"):
        ElektronKitCodec(spec).decode_frame(empty)

    bad_spec = _codec_spec(checksum_packed_start=99)
    bad_frame = _codec_frame(bad_spec)
    with pytest.raises(ValueError, match="exceeds packed"):
        ElektronKitCodec(bad_spec).decode_frame(bad_frame)


def test_elektron_kit_codec_rejects_checksum_and_length_mismatch() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    spec = _codec_spec()
    codec = ElektronKitCodec(spec)
    frame = bytearray(_codec_frame(spec))
    bad_checksum = bytearray(frame)
    bad_checksum[-5] ^= 0x01
    bad_length = bytearray(frame)
    bad_length[-3] ^= 0x01

    with pytest.raises(ValueError, match="checksum mismatch"):
        codec.decode_frame(bytes(bad_checksum))
    with pytest.raises(ValueError, match="length mismatch"):
        codec.decode_frame(bytes(bad_length))


def test_elektron_kit_codec_rejects_wrong_decoded_size_and_prefix() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    short_spec = _codec_spec(unpacked_size=10)
    with pytest.raises(ValueError, match="expected 10"):
        ElektronKitCodec(short_spec).decode_frame(_codec_frame(short_spec))

    prefix_spec = _codec_spec(required_unpacked_prefix=b"\x53")
    with pytest.raises(ValueError, match="object prefix mismatch"):
        ElektronKitCodec(prefix_spec).decode_frame(_codec_frame(prefix_spec))


def test_elektron_kit_codec_encode_rejects_wrong_spec_and_forged_metadata() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    spec = _codec_spec()
    codec = ElektronKitCodec(spec)
    decoded = codec.decode_frame(_codec_frame(spec))
    other_codec = ElektronKitCodec(_codec_spec(label="Other synthetic kit"))

    with pytest.raises(ValueError, match="different spec"):
        other_codec.encode_frame(decoded)
    with pytest.raises(ValueError, match="metadata does not match"):
        codec.encode_frame(replace(decoded, checksum=decoded.checksum + 1))


def test_elektron_kit_codec_encode_rejects_wrong_object_size_and_prefix() -> None:
    from rytm_randomizer.snapshot import ElektronKitCodec

    spec = _codec_spec()
    codec = ElektronKitCodec(spec)
    decoded = codec.decode_frame(_codec_frame(spec))

    with pytest.raises(ValueError, match="object has 8 byte"):
        codec.encode_frame(decoded, unpacked=decoded.unpacked[:-1])
    with pytest.raises(ValueError, match="object prefix mismatch"):
        codec.encode_frame(decoded, unpacked=b"\x53" + decoded.unpacked[1:])


def test_unpack_elektron_7bit_returns_empty_on_empty_input() -> None:
    from rytm_randomizer.snapshot import unpack_elektron_7bit

    assert unpack_elektron_7bit(b"") == b""


def test_pack_elektron_7bit_round_trips_shared_envelope_payload() -> None:
    from rytm_randomizer.snapshot import pack_elektron_7bit, unpack_elektron_7bit

    payload = bytes([0xFF, 0x00, 0x80, 0x01, 0x00, 0xA5, 0xFF]) + bytes(range(20))

    assert unpack_elektron_7bit(pack_elektron_7bit(payload)) == payload


def test_pack_elektron_7bit_pins_header_bit_order_and_short_tail() -> None:
    from rytm_randomizer.snapshot import pack_elektron_7bit

    unpacked = bytes([0x80, 0x01, 0xFF, 0x7F, 0x00, 0xA5, 0x55, 0x81])

    packed = pack_elektron_7bit(unpacked)

    assert packed == bytes([0x25, 0x00, 0x01, 0x7F, 0x7F, 0x00, 0x25, 0x55, 0x01, 0x01])
    assert all(byte <= 0x7F for byte in packed)


def test_unpack_elektron_7bit_raises_on_non_seven_bit_byte() -> None:
    """An input byte > 0x7F means the payload was not 7-bit MIDI to begin with."""

    from rytm_randomizer.snapshot import unpack_elektron_7bit

    with pytest.raises(ValueError, match="0x80"):
        unpack_elektron_7bit(bytes([0x00, 0x80]))


def test_unpack_elektron_7bit_rejects_lone_nonzero_trailing_header() -> None:
    """A buffer ending on a nonzero header with no following data bytes is malformed."""

    from rytm_randomizer.snapshot import unpack_elektron_7bit

    with pytest.raises(ValueError, match="no data bytes"):
        unpack_elektron_7bit(bytes([0x55]))


def test_unpack_elektron_7bit_rejects_lone_zero_trailing_header() -> None:
    """A lone zero header has no data bytes and is still malformed framing.

    Codex review P2: the prior implementation silently returned ``b""`` for
    ``bytes([0])`` because of a ``header != 0`` carve-out. The spec treats the
    framing the same regardless of header value -- a header with no payload is
    meaningless, and the caller deserves an error rather than a quietly-empty
    decode.
    """

    from rytm_randomizer.snapshot import unpack_elektron_7bit

    with pytest.raises(ValueError, match="no data bytes"):
        unpack_elektron_7bit(bytes([0]))


# ---------------------------------------------------------------------------
# 4. find_kit_record
# ---------------------------------------------------------------------------


def test_find_kit_record_returns_payload_starting_at_type_byte() -> None:
    """The record begins at the first occurrence of ``kit_type_byte``."""

    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    payload = ELEKTRON_MFR_ID + bytes([0x10, 0x11, 0x42, 0x13, 0x14])
    record = find_kit_record(payload, slot=0, kit_type_byte=0x42)
    assert record == bytes([0x42, 0x13, 0x14])


def test_find_kit_record_rejects_payload_missing_manufacturer_prefix() -> None:
    from rytm_randomizer.snapshot import find_kit_record

    with pytest.raises(ValueError, match="manufacturer id"):
        find_kit_record(bytes([0x11, 0x22, 0x33, 0x42]), slot=0, kit_type_byte=0x42)


def test_find_kit_record_rejects_negative_slot() -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    with pytest.raises(ValueError, match="non-negative"):
        find_kit_record(ELEKTRON_MFR_ID + bytes([0x42]), slot=-1, kit_type_byte=0x42)


def test_find_kit_record_rejects_type_byte_outside_byte_range() -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    with pytest.raises(ValueError, match="0x00-0xff"):
        find_kit_record(ELEKTRON_MFR_ID + bytes([0x42]), slot=0, kit_type_byte=0x100)


def test_find_kit_record_rejects_missing_type_byte() -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    with pytest.raises(ValueError, match="not.*present"):
        find_kit_record(ELEKTRON_MFR_ID + bytes([0x10, 0x11, 0x12]), slot=0, kit_type_byte=0x42)


@pytest.mark.parametrize("kit_type_byte", (-1, 0x100))
def test_find_kit_record_rejects_out_of_range_type_byte(kit_type_byte: int) -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    with pytest.raises(ValueError, match="0x00-0xff"):
        find_kit_record(ELEKTRON_MFR_ID, slot=0, kit_type_byte=kit_type_byte)


def test_find_kit_record_rejects_unimplemented_nonzero_slot() -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, find_kit_record

    with pytest.raises(NotImplementedError, match="slot-indexed"):
        find_kit_record(ELEKTRON_MFR_ID + b"\x42", slot=1, kit_type_byte=0x42)


# ---------------------------------------------------------------------------
# 5. read_ascii_name
# ---------------------------------------------------------------------------


def test_read_ascii_name_strips_trailing_null_bytes() -> None:
    from rytm_randomizer.snapshot import read_ascii_name

    record = b"KICK\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
    assert read_ascii_name(record, offset=0, length=16) == "KICK"


def test_read_ascii_name_truncates_to_requested_length() -> None:
    """The slice respects ``length`` even if extra bytes follow."""

    from rytm_randomizer.snapshot import read_ascii_name

    record = b"\x00\x00HATSXX_more_data_here"
    assert read_ascii_name(record, offset=2, length=4) == "HATS"


def test_read_ascii_name_rejects_slice_past_record_end() -> None:
    from rytm_randomizer.snapshot import read_ascii_name

    with pytest.raises(ValueError, match="extends past"):
        read_ascii_name(b"AB", offset=0, length=4)


def test_read_ascii_name_rejects_negative_offset_and_length() -> None:
    from rytm_randomizer.snapshot import read_ascii_name

    with pytest.raises(ValueError, match="offset must be non-negative"):
        read_ascii_name(b"AB", offset=-1, length=1)
    with pytest.raises(ValueError, match="length must be non-negative"):
        read_ascii_name(b"AB", offset=0, length=-1)


# ---------------------------------------------------------------------------
# 6. format_manufacturer_id
# ---------------------------------------------------------------------------


def test_format_manufacturer_id_renders_elektron_id_as_colon_hex() -> None:
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, format_manufacturer_id

    assert format_manufacturer_id(ELEKTRON_MFR_ID) == "00:20:3C"


def test_format_manufacturer_id_renders_single_byte_legacy_id() -> None:
    """Roland's 1-byte short-form ID (0x41) renders without a delimiter."""

    from rytm_randomizer.snapshot import format_manufacturer_id

    assert format_manufacturer_id(bytes([0x41])) == "41"


def test_format_manufacturer_id_returns_empty_on_empty_input() -> None:
    from rytm_randomizer.snapshot import format_manufacturer_id

    assert format_manufacturer_id(b"") == ""


# ---------------------------------------------------------------------------
# 7. Protocol exports (SnapshotDecoder, MutationPlanner, MockRuntime)
# ---------------------------------------------------------------------------


def test_protocol_exports_are_importable() -> None:
    """SnapshotDecoder, MutationPlanner, MockRuntime all import via the subpackage."""

    from rytm_randomizer.snapshot import MockRuntime, MutationPlanner, SnapshotDecoder

    assert SnapshotDecoder is not None
    assert MutationPlanner is not None
    assert MockRuntime is not None


# ---------------------------------------------------------------------------
# 8. PR #21 forward-compat: structural-typing satisfaction
# ---------------------------------------------------------------------------


def test_stub_class_with_decode_satisfies_snapshot_decoder_protocol() -> None:
    """A hand-rolled decoder class structurally satisfies SnapshotDecoder.

    This is the PR #21 acceptance test in miniature: codex's
    ``AnalogFourSnapshotDecoder`` will look like this stub, just with a
    real decode body.
    """

    from rytm_randomizer.snapshot import SnapshotDecoder

    class _StubDecoder:
        def decode(self, raw: bytes, slot: int) -> tuple:
            return ("stub", raw, slot)

    assert isinstance(_StubDecoder(), SnapshotDecoder)


def test_stub_class_with_plan_satisfies_mutation_planner_protocol() -> None:
    from rytm_randomizer.snapshot import MutationPlanner

    class _StubPlanner:
        def plan(self, snapshot: object, depth: int) -> tuple:
            return ("stub_plan", snapshot, depth)

    assert isinstance(_StubPlanner(), MutationPlanner)


def test_stub_class_with_capture_messages_satisfies_mock_runtime_protocol() -> None:
    from rytm_randomizer.snapshot import MockRuntime

    class _StubRuntime:
        def capture_messages(self, plan: object) -> list:
            return []

    assert isinstance(_StubRuntime(), MockRuntime)


# ---------------------------------------------------------------------------
# 9. BaseMockRuntime delegates to device.to_mock_messages
# ---------------------------------------------------------------------------


def test_base_mock_runtime_forwards_messages_from_device_to_outbox() -> None:
    """capture_messages calls device.to_mock_messages then sends each to outbox."""

    from rytm_randomizer.snapshot import BaseMockRuntime

    class _RecordingOutbox:
        def __init__(self) -> None:
            self.sent: list[object] = []

        def send(self, message: object) -> None:
            self.sent.append(message)

    class _FakeDevice:
        device_id = "fake"
        display_name = "Fake"
        default_midi_channel = 0
        track_count = 4
        sysex_manufacturer_id = bytes([0x00, 0x20, 0x3C])

        def decode_snapshot(self, raw: bytes, slot: int) -> object:
            return ("snap", raw, slot)

        def plan_mutation(self, snapshot: object, depth: int) -> object:
            return ("plan", snapshot, depth)

        def to_mock_messages(self, plan: object) -> list[object]:
            return [("msg", 1), ("msg", 2), ("msg", 3)]

        def to_cc_messages(self, plan: object):
            return ()

    outbox = _RecordingOutbox()
    runtime = BaseMockRuntime(outbox)
    device = _FakeDevice()

    returned = runtime.capture_messages(("any_plan",), device=device)

    expected = [("msg", 1), ("msg", 2), ("msg", 3)]
    assert returned == expected
    assert outbox.sent == expected
    assert runtime.outbox is outbox


# ---------------------------------------------------------------------------
# Coverage: defensive None guards on the four helpers.
#
# Each helper has a ``# type: ignore[unreachable]`` defensive ``None``
# check; static typing forbids the call but we want runtime confirmation
# the message is what the caller will see, and the branch is exercised.
# ---------------------------------------------------------------------------


def test_unpack_elektron_7bit_raises_on_none_input() -> None:
    from rytm_randomizer.snapshot import unpack_elektron_7bit

    with pytest.raises(ValueError, match="packed payload is None"):
        unpack_elektron_7bit(cast(bytes, None))


def test_pack_elektron_7bit_raises_on_none_input() -> None:
    from rytm_randomizer.snapshot import pack_elektron_7bit

    with pytest.raises(ValueError, match="unpacked payload is None"):
        pack_elektron_7bit(cast(bytes, None))


def test_find_kit_record_raises_on_none_raw() -> None:
    from rytm_randomizer.snapshot import find_kit_record

    with pytest.raises(ValueError, match="raw payload is None"):
        find_kit_record(cast(bytes, None), slot=0, kit_type_byte=0x00)


def test_read_ascii_name_raises_on_none_record() -> None:
    from rytm_randomizer.snapshot import read_ascii_name

    with pytest.raises(ValueError, match="record is None"):
        read_ascii_name(cast(bytes, None), offset=0, length=4)


def test_format_manufacturer_id_raises_on_none() -> None:
    from rytm_randomizer.snapshot import format_manufacturer_id

    with pytest.raises(ValueError, match="raw is None"):
        format_manufacturer_id(cast(bytes, None))
