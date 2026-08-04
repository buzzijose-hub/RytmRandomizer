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

from conftest import pack_elektron_7bit, rytm_real_layout_kit_payload

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

    return _real_layout_kit_payload(name=name)


def _real_layout_kit_payload(name: bytes = b"KIT 1") -> bytes:
    """Build a packed Rytm kit body that matches the observed real dump header."""

    return rytm_real_layout_kit_payload(name=name)


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


def test_decode_extracts_kit_name_from_real_layout_offset() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_real_layout_kit_payload(name=b"KIT 12"), slot=11)

    assert snap.kit_name == "KIT 12"


def test_decode_removes_embedded_nuls_from_operator_kit_name() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_real_layout_kit_payload(name=b"KIT\x00 1"), slot=0)

    assert snap.kit_name == "KIT 1"


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
    """``snapshot.unpacked`` must be the decoded raw kit payload."""

    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    decoder = AnalogRytmSnapshotDecoder()
    snap = decoder.decode(_kit_payload(name=b"X"), slot=0)

    assert len(snap.unpacked) == 0x0A32
    assert snap.unpacked[4:5] == b"X"


def test_snapshot_exports_machine_fact_types() -> None:
    from rytm_randomizer.devices.strategies import (
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    fact = RytmSnapshotMachineFact(
        pad=1,
        raw_machine_value=0,
        decoded_machine_value=0,
        promoted=True,
        reason="promoted",
    )
    facts = RytmSnapshotMachineFacts(facts_by_pad={1: fact}, promoted=False)

    assert facts.facts_by_pad[1] is fact
    assert facts.promoted is False


def test_decode_extracts_candidate_machine_facts_from_real_layout() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    payload = _real_layout_kit_payload(name=b"LIVE")
    snap = AnalogRytmSnapshotDecoder().decode(payload, slot=0)

    assert snap.machine_facts.facts_by_pad[1].raw_machine_value == 0
    assert snap.machine_facts.facts_by_pad[2].raw_machine_value == 2
    assert snap.machine_facts.facts_by_pad[3].raw_machine_value == 4
    assert snap.machine_facts.facts_by_pad[10].raw_machine_value == 10
    assert snap.machine_facts.facts_by_pad[12].raw_machine_value == 12
    assert snap.machine_facts.promoted is False


def test_decode_marks_tom_pads_candidate_only_until_verified() -> None:
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    snap = AnalogRytmSnapshotDecoder().decode(_real_layout_kit_payload(), slot=0)

    for pad in (6, 7, 8):
        fact = snap.machine_facts.facts_by_pad[pad]
        assert fact.promoted is False
        assert "candidate-only" in fact.reason


def test_snapshot_decoder_strips_legacy_embedded_kit_header() -> None:
    from rytm_randomizer.data.analog_rytm_kit_layout import (
        RYTM_KIT_DUMP_ID,
        RYTM_KIT_NAME_OFFSET,
        RYTM_KIT_RAW_SIZE,
    )
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder
    from rytm_randomizer.devices.strategies.analog_rytm_snapshot_decoder import (
        RYTM_KIT_TYPE_BYTE,
    )
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

    unpacked = bytearray(RYTM_KIT_RAW_SIZE)
    unpacked[RYTM_KIT_NAME_OFFSET : RYTM_KIT_NAME_OFFSET + 11] = b"LEGACY TEST"
    embedded_header = bytes([RYTM_KIT_DUMP_ID, 0x01, 0x01, 0x00])
    raw = (
        ELEKTRON_MFR_ID
        + b"\x00"
        + bytes([RYTM_KIT_TYPE_BYTE])
        + pack_elektron_7bit(embedded_header + bytes(unpacked))
    )

    snapshot = AnalogRytmSnapshotDecoder().decode(raw, slot=4)

    assert snapshot.slot == 4
    assert snapshot.kit_name == "LEGACY TEST"
    assert snapshot.unpacked == bytes(unpacked)


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


def test_decode_rejects_full_kit_dump_with_wrong_unpacked_size() -> None:
    from rytm_randomizer.data.analog_rytm_kit_layout import (
        RYTM_KIT_DUMP_ID,
        RYTM_SYSEX_PRODUCT_ID,
    )
    from rytm_randomizer.devices.strategies import AnalogRytmSnapshotDecoder

    header = bytes(
        [
            0x00,
            0x20,
            0x3C,
            RYTM_SYSEX_PRODUCT_ID,
            0x00,
            RYTM_KIT_DUMP_ID,
            0x01,
            0x01,
            0x00,
        ]
    )
    truncated_packed_payload = pack_elektron_7bit(bytes([0x00] * 32))
    zeroed_checksum_and_size = bytes([0x00, 0x00, 0x00, 0x00])

    payload = header + truncated_packed_payload + zeroed_checksum_and_size

    with pytest.raises(ValueError, match="decoded kit payload has 32 byte"):
        AnalogRytmSnapshotDecoder().decode(payload, slot=0)


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
