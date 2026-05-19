"""Tests for ``rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder``.

Covers the body of :class:`AnalogRytmSnapshotDecoder`: every guard, every
successful decode path, every error path. The strategy is composed into
``AnalogRytmDevice`` via ``snapshot_decoder``, so its correctness is part
of the WS-S5 + Strategy contract.

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Fixtures: build valid Rytm SysEx payloads.
# ---------------------------------------------------------------------------


def _kit_payload(name: bytes = b"") -> bytes:
    """Build a Rytm kit-dump body. ``name`` is up to 16 ASCII bytes for the kit name."""

    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        RYTM_KIT_TYPE_BYTE,
    )

    padded = name.ljust(16, b"\x00")
    # 3 wire groups of (1 header + 7 data) = enough payload for the name field
    # and avoid the lone-trailing-header rejection from the envelope unpacker.
    # Group 1: header=0 + 7 of the padded name.
    # Group 2: header=0 + next 7 of the padded name (8..14).
    # Group 3: header=0 + 7 NUL pad data bytes.
    group_1 = bytes([0x00]) + padded[0:7]
    group_2 = bytes([0x00]) + padded[7:14]
    group_3 = bytes([0x00]) + padded[14:16] + bytes([0x00] * 5)
    return bytes([0x00, 0x20, 0x3C, RYTM_KIT_TYPE_BYTE]) + group_1 + group_2 + group_3


def _bad_prefix_payload() -> bytes:
    """Build a payload that does NOT start with the Elektron manufacturer ID."""

    return bytes([0xFF, 0xFF, 0xFF, 0x07]) + bytes([0x00] * 24)


# ---------------------------------------------------------------------------
# 1. Successful decode path
# ---------------------------------------------------------------------------


def test_decode_returns_rytm_kit_snapshot_with_correct_slot() -> None:
    from rytm_randomizer.devices.strategies import (
        AnalogRytmSnapshotDecoder,
        RytmKitSnapshot,
    )

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_kit_payload(), slot=5)

    assert isinstance(snap, RytmKitSnapshot)
    assert snap.slot == 5


def test_decode_extracts_kit_name_from_payload() -> None:
    """A 4-byte ASCII name ``BD01`` should decode to the operator string ``BD01``."""

    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_kit_payload(name=b"BD01"), slot=0)

    assert snap.kit_name == "BD01"


def test_decode_strips_trailing_nuls_from_kit_name() -> None:
    """Elektron pads kit names with NULs; the decoded string must be clean."""

    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_kit_payload(name=b"KICK_8"), slot=0)

    assert snap.kit_name == "KICK_8"
    assert "\x00" not in snap.kit_name


def test_decode_preserves_raw_payload_on_snapshot() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    payload = _kit_payload(name=b"TEST")
    snap = decoder.decode(payload, slot=0)

    assert snap.raw == payload


def test_decode_unpacks_payload_so_planner_can_slice_it() -> None:
    """``snapshot.unpacked`` must be the 7-bit-unstuffed payload."""

    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_kit_payload(name=b"X"), slot=0)

    # 3 wire groups of 8 bytes = 24 wire bytes -> 21 unpacked data bytes
    # (one header byte per group is consumed).
    assert len(snap.unpacked) == 21


# ---------------------------------------------------------------------------
# 2. Error paths
# ---------------------------------------------------------------------------


def test_decode_rejects_negative_slot() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    with pytest.raises(ValueError, match="slot must be non-negative"):
        decoder.decode(_kit_payload(), slot=-1)


def test_decode_rejects_payload_missing_elektron_prefix() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    with pytest.raises(ValueError, match="Elektron manufacturer id"):
        decoder.decode(_bad_prefix_payload(), slot=0)


def test_decode_rejects_payload_without_rytm_kit_type_byte() -> None:
    """A payload with the Elektron prefix but no 0x07 kit-type byte must fail."""

    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    # Elektron prefix + non-kit type byte 0x05 (not Rytm's 0x07).
    payload = bytes([0x00, 0x20, 0x3C, 0x05]) + bytes([0x00] * 24)

    with pytest.raises(ValueError, match="kit_type_byte 0x07 not"):
        decoder.decode(payload, slot=0)


# ---------------------------------------------------------------------------
# 3. Determinism: same input -> same snapshot
# ---------------------------------------------------------------------------


def test_decode_is_deterministic_for_same_input() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    payload = _kit_payload(name=b"DET")

    snap_a = decoder.decode(payload, slot=4)
    snap_b = decoder.decode(payload, slot=4)

    assert snap_a == snap_b
