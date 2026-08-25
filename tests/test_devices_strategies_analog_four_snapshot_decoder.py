"""Tests for Analog Four snapshot decoder Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.snapshot import Elektron7BitMaskOrder, pack_elektron_7bit

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _a4_kit_payload(name: bytes = b"A4KIT") -> bytes:
    """Build a minimal A4 kit-dump-like body for decoder tests."""

    padded_name = name[:16].ljust(16, b"\x00")
    return bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02, 0x03])


def _a4_saved_kit_payload(
    name: bytes = b"REAL A4",
    *,
    kit_object_byte: int | None = None,
) -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_FAMILY_BYTE,
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_KIT_OBJECT_BYTE,
    )
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    object_byte = A4_KIT_OBJECT_BYTE if kit_object_byte is None else kit_object_byte
    prefix = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE, 0x00, object_byte, 0x01, 0x01, 0x00])
    unpacked = bytearray(A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH + 8)
    unpacked[A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH] = name[
        :A4_KIT_NAME_LENGTH
    ].ljust(A4_KIT_NAME_LENGTH, b"\x00")
    return prefix + pack_elektron_7bit(
        bytes(unpacked),
        mask_order=Elektron7BitMaskOrder.MSB_FIRST,
    )


def test_decode_returns_analog_four_kit_snapshot_with_slot_and_name() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot, AnalogFourSnapshotDecoder
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_SNAPSHOT_LAYOUT_CANDIDATE,
    )

    snapshot = AnalogFourSnapshotDecoder().decode(_a4_kit_payload(b"FOUR01"), slot=2)

    assert isinstance(snapshot, AnalogFourKitSnapshot)
    assert snapshot.slot == 2
    assert snapshot.kit_name == "FOUR01"
    assert snapshot.raw == _a4_kit_payload(b"FOUR01")
    assert snapshot.unpacked == _a4_kit_payload(b"FOUR01")
    assert snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_CANDIDATE
    assert snapshot.offsets_promoted is False


def test_decode_real_saved_kit_frame_unpacks_name_and_keeps_offsets_candidate() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot, AnalogFourSnapshotDecoder
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_SNAPSHOT_LAYOUT_SAVED_KIT,
    )

    payload = _a4_saved_kit_payload(b"REALKIT")

    snapshot = AnalogFourSnapshotDecoder().decode(payload, slot=5)

    assert isinstance(snapshot, AnalogFourKitSnapshot)
    assert snapshot.slot == 5
    assert snapshot.kit_name == "REALKIT"
    assert snapshot.raw == payload
    assert snapshot.unpacked[
        A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH
    ].startswith(b"REALKIT")
    assert snapshot.snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT
    assert snapshot.offsets_promoted is False


def test_decode_hardware_saved_kit_strips_checksum_and_length_trailer() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder
    from rytm_randomizer.snapshot import extract_sysex_payloads

    payload = extract_sysex_payloads(analog_four_saved_kit_frame())[0]

    snapshot = AnalogFourSnapshotDecoder().decode(payload, slot=0)

    assert snapshot.kit_name == "KIT 1"
    assert len(snapshot.unpacked) == 2410


def test_decode_real_saved_kit_cleans_internal_nul_name_padding() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = _a4_saved_kit_payload(b"KIT\x00 1")

    snapshot = AnalogFourSnapshotDecoder().decode(payload, slot=0)

    assert snapshot.kit_name == "KIT 1"


def test_decode_real_saved_kit_preserves_intentional_name_spacing() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = _a4_saved_kit_payload(b"A  B")

    snapshot = AnalogFourSnapshotDecoder().decode(payload, slot=0)

    assert snapshot.kit_name == "A  B"


def test_decode_rejects_negative_slot() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    with pytest.raises(ValueError, match="slot must be non-negative"):
        AnalogFourSnapshotDecoder().decode(_a4_kit_payload(), slot=-1)


def test_decode_rejects_payload_without_elektron_prefix() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = bytes([0x7E, 0x7E, 0x7E, 0x07]) + bytes(24)

    with pytest.raises(ValueError, match="Elektron manufacturer id"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_rejects_payload_too_short_for_kit_name() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + bytes(3)

    with pytest.raises(ValueError, match="payload too short"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_rejects_prefix_only_payload_without_index_error() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    with pytest.raises(ValueError, match="payload too short for family/type byte"):
        AnalogFourSnapshotDecoder().decode(ELEKTRON_MFR_ID, slot=0)


def test_decode_rejects_wrong_candidate_kit_type_byte() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = bytes([0x00, 0x20, 0x3C, 0x08]) + b"A4".ljust(16, b"\x00")

    with pytest.raises(ValueError, match="candidate kit type byte"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_real_saved_kit_rejects_wrong_object_byte() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = _a4_saved_kit_payload(b"BADOBJ", kit_object_byte=0x53)

    with pytest.raises(ValueError, match="object is not a saved kit"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_is_deterministic_for_same_input() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    decoder = AnalogFourSnapshotDecoder()
    payload = _a4_kit_payload(b"DET")

    assert decoder.decode(payload, slot=1) == decoder.decode(payload, slot=1)


def test_snapshot_payload_fingerprint_prefers_unpacked_and_falls_back_to_raw() -> None:
    from hashlib import sha256

    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot
    from rytm_randomizer.devices.strategies.analog_four_snapshot_decoder import (
        analog_four_snapshot_payload_fingerprint,
    )

    unpacked = AnalogFourKitSnapshot(slot=0, kit_name="A", raw=b"raw", unpacked=b"body")
    raw_only = AnalogFourKitSnapshot(slot=0, kit_name="B", raw=b"raw")

    assert analog_four_snapshot_payload_fingerprint(unpacked) == sha256(b"body").hexdigest()[:16]
    assert analog_four_snapshot_payload_fingerprint(raw_only) == sha256(b"raw").hexdigest()[:16]


def test_candidate_decoder_helper_rejects_wrong_type_byte() -> None:
    from rytm_randomizer.devices.strategies.analog_four_snapshot_decoder import (
        _decode_candidate_payload,
    )

    payload = bytes([0x00, 0x20, 0x3C, 0x06]) + bytes(16)

    with pytest.raises(ValueError, match="candidate kit type byte"):
        _decode_candidate_payload(payload, slot=0)
