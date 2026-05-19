"""Tests for Analog Four snapshot decoder Strategy."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _a4_kit_payload(name: bytes = b"A4KIT") -> bytes:
    """Build a minimal A4 kit-dump-like body for decoder tests."""

    padded_name = name[:16].ljust(16, b"\x00")
    return bytes([0x00, 0x20, 0x3C, 0x07]) + padded_name + bytes([0x01, 0x02, 0x03])


def test_decode_returns_analog_four_kit_snapshot_with_slot_and_name() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    snapshot = AnalogFourSnapshotDecoder().decode(_a4_kit_payload(b"FOUR01"), slot=2)

    assert isinstance(snapshot, AnalogFourKitSnapshot)
    assert snapshot.slot == 2
    assert snapshot.kit_name == "FOUR01"
    assert snapshot.raw == _a4_kit_payload(b"FOUR01")
    assert snapshot.offsets_promoted is False


def test_decode_rejects_negative_slot() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    with pytest.raises(ValueError, match="slot must be non-negative"):
        AnalogFourSnapshotDecoder().decode(_a4_kit_payload(), slot=-1)


def test_decode_rejects_payload_without_elektron_prefix() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    payload = bytes([0x7E, 0x7E, 0x7E, 0x07]) + bytes(24)

    with pytest.raises(ValueError, match="Elektron manufacturer id"):
        AnalogFourSnapshotDecoder().decode(payload, slot=0)


def test_decode_is_deterministic_for_same_input() -> None:
    from rytm_randomizer.devices.strategies import AnalogFourSnapshotDecoder

    decoder = AnalogFourSnapshotDecoder()
    payload = _a4_kit_payload(b"DET")

    assert decoder.decode(payload, slot=1) == decoder.decode(payload, slot=1)
