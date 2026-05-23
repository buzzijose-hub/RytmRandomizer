"""Tests for ``rytm_randomizer.cockpit.data.snapshot`` — PadState + Snapshot.

A ``Snapshot`` is the whole device's parameter state at a point in time. It
is the atomic unit the cockpit history walks and the mutation engine reads.
The dataclass MUST be:

* frozen (immutable),
* round-trip-serializable through ``to_dict`` / ``from_dict``,
* type-safe (every field annotated, mappings are read-only).
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from types import MappingProxyType

import pytest

from rytm_randomizer.cockpit.data.snapshot import PadState, Snapshot

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


def _make_pad(pad_id: int = 1, machine: str = "BD Hard") -> PadState:
    return PadState(
        pad_id=pad_id,
        machine=machine,
        params={"tun": 28, "dec": 80, "lev": 110},
    )


def _make_snapshot(
    *,
    pads: tuple[PadState, ...] | None = None,
    scene_slot: str | None = "A01",
    bpm: float | None = 124.5,
) -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0123456789ABCD0",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=pads if pads is not None else (_make_pad(1), _make_pad(2, "SD Acoustic")),
        scene_slot=scene_slot,
        bpm=bpm,
    )


# ---------------------------------------------------------------------------
# PadState: immutability + params mapping is read-only.
# ---------------------------------------------------------------------------


def test_pad_state_is_frozen() -> None:
    pad = _make_pad()
    with pytest.raises(FrozenInstanceError):
        pad.pad_id = 99  # type: ignore[misc]


def test_pad_state_params_is_a_mappingproxy() -> None:
    """``params`` is stored as a read-only proxy; outsiders can't mutate it."""

    pad = _make_pad()
    assert isinstance(pad.params, MappingProxyType)
    with pytest.raises(TypeError):
        pad.params["tun"] = 0  # type: ignore[index]


def test_pad_state_params_copy_isolates_caller_mutation() -> None:
    """Caller-supplied ``params`` dict must not leak through (no aliasing)."""

    src = {"tun": 28}
    pad = PadState(pad_id=1, machine="BD Hard", params=src)
    src["tun"] = 999  # mutate the caller's dict
    assert pad.params["tun"] == 28  # snapshot retained the captured value


def test_pad_state_to_dict_round_trip() -> None:
    pad = _make_pad()
    restored = PadState.from_dict(pad.to_dict())
    assert restored == pad


def test_pad_state_equality_value_based() -> None:
    """Two pads with the same content compare equal (dataclass default)."""

    assert _make_pad() == _make_pad()


# ---------------------------------------------------------------------------
# PadState: field validation.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pad_id", [0, 13, -1])
def test_pad_state_rejects_out_of_range_pad_id(pad_id: int) -> None:
    with pytest.raises(ValueError, match="pad_id"):
        PadState(pad_id=pad_id, machine="BD Hard", params={})


def test_pad_state_rejects_empty_machine_name() -> None:
    with pytest.raises(ValueError, match="machine"):
        PadState(pad_id=1, machine="", params={})


# ---------------------------------------------------------------------------
# Snapshot: immutability + tuple of pads sorted by pad_id.
# ---------------------------------------------------------------------------


def test_snapshot_is_frozen() -> None:
    snap = _make_snapshot()
    with pytest.raises(FrozenInstanceError):
        snap.device = "analog_four"  # type: ignore[misc]


def test_snapshot_pads_are_stored_as_tuple() -> None:
    snap = _make_snapshot()
    assert isinstance(snap.pads, tuple)


def test_snapshot_rejects_pads_not_sorted_by_pad_id() -> None:
    """Pads must arrive ordered by ``pad_id`` (spec §"Snapshot")."""

    out_of_order = (_make_pad(2, "SD"), _make_pad(1, "BD"))
    with pytest.raises(ValueError, match="pad_id"):
        Snapshot(
            snapshot_id="01HXY5Q9PJM0123456789ABCD1",
            device="analog_rytm_mk2",
            captured_at=_FIXED_TS,
            pads=out_of_order,
            scene_slot=None,
            bpm=None,
        )


def test_snapshot_rejects_duplicate_pad_ids() -> None:
    dupes = (_make_pad(1, "BD A"), _make_pad(1, "BD B"))
    with pytest.raises(ValueError, match="duplicate"):
        Snapshot(
            snapshot_id="01HXY5Q9PJM0123456789ABCD2",
            device="analog_rytm_mk2",
            captured_at=_FIXED_TS,
            pads=dupes,
            scene_slot=None,
            bpm=None,
        )


def test_snapshot_allows_empty_pads_tuple() -> None:
    snap = _make_snapshot(pads=())
    assert snap.pads == ()


def test_snapshot_rejects_empty_device_name() -> None:
    with pytest.raises(ValueError, match="device"):
        Snapshot(
            snapshot_id="01HXY5Q9PJM0123456789ABCD3",
            device="",
            captured_at=_FIXED_TS,
            pads=(),
            scene_slot=None,
            bpm=None,
        )


def test_snapshot_rejects_empty_snapshot_id() -> None:
    with pytest.raises(ValueError, match="snapshot_id"):
        Snapshot(
            snapshot_id="",
            device="analog_rytm_mk2",
            captured_at=_FIXED_TS,
            pads=(),
            scene_slot=None,
            bpm=None,
        )


# ---------------------------------------------------------------------------
# Snapshot: round-trip serialization.
# ---------------------------------------------------------------------------


def test_snapshot_to_dict_round_trip_full() -> None:
    snap = _make_snapshot()
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored == snap


def test_snapshot_to_dict_round_trip_none_optional_fields() -> None:
    snap = _make_snapshot(scene_slot=None, bpm=None)
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored == snap
    assert restored.scene_slot is None
    assert restored.bpm is None


def test_snapshot_to_dict_round_trip_empty_pads() -> None:
    snap = _make_snapshot(pads=())
    restored = Snapshot.from_dict(snap.to_dict())
    assert restored == snap
    assert restored.pads == ()


def test_pad_state_from_dict_rejects_non_mapping_params() -> None:
    """``from_dict`` raises ``TypeError`` if ``params`` isn't a mapping."""

    bad = {"pad_id": 1, "machine": "BD Hard", "params": ["not", "a", "dict"]}
    with pytest.raises(TypeError, match="params"):
        PadState.from_dict(bad)


def test_snapshot_from_dict_rejects_non_iterable_pads() -> None:
    """``from_dict`` raises ``TypeError`` if ``pads`` isn't a list/tuple."""

    bad = {
        "snapshot_id": "01HXY5Q9PJM0123456789ABCD0",
        "device": "analog_rytm_mk2",
        "captured_at": _FIXED_TS.isoformat(),
        "pads": {"not": "a list"},  # dict, not list/tuple
        "scene_slot": None,
        "bpm": None,
    }
    with pytest.raises(TypeError, match="pads"):
        Snapshot.from_dict(bad)


def test_snapshot_to_dict_keys_are_stable() -> None:
    """``to_dict`` returns a deterministic key set so serializers depend on it."""

    snap = _make_snapshot()
    data = snap.to_dict()
    assert set(data.keys()) == {
        "snapshot_id",
        "device",
        "captured_at",
        "pads",
        "scene_slot",
        "bpm",
    }
    # captured_at must be ISO 8601 so downstream JSON layers don't need a custom encoder.
    assert isinstance(data["captured_at"], str)
    assert data["captured_at"] == _FIXED_TS.isoformat()
