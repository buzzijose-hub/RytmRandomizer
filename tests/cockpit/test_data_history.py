"""Tests for ``rytm_randomizer.cockpit.data.history`` — HistoryEntry + History.

A ``History`` is the linear, chronological chain of snapshots with metadata
about how each came to exist. UNDO walks left one step; LOAD jumps to any
past entry; SAVE promotes an ``auto`` entry to ``saved`` with a label.

The dataclasses here are pure-data carriers (frozen, round-trippable). The
write-side state machine (append, undo, promote, load) is WS-D's
``HistoryStore``, not this module.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data.history import History, HistoryEntry
from rytm_randomizer.cockpit.data.snapshot import PadState, Snapshot

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_snap(snap_id: str = "01HXY5Q9PJM0123456789ABCD0") -> Snapshot:
    return Snapshot(
        snapshot_id=snap_id,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 30}),),
        scene_slot=None,
        bpm=None,
    )


def _make_entry(
    *,
    snap_id: str = "01HXY5Q9PJM0123456789ABCD0",
    kind: str = "auto",
    parent_id: str | None = None,
    via: str | None = "send",
    label: str | None = None,
) -> HistoryEntry:
    return HistoryEntry(
        snapshot=_make_snap(snap_id),
        kind=kind,  # type: ignore[arg-type]
        parent_id=parent_id,
        via=via,  # type: ignore[arg-type]
        label=label,
    )


# ---------------------------------------------------------------------------
# HistoryEntry
# ---------------------------------------------------------------------------


def test_history_entry_is_frozen() -> None:
    entry = _make_entry()
    with pytest.raises(FrozenInstanceError):
        entry.label = "foo"  # type: ignore[misc]


@pytest.mark.parametrize("kind", ["auto", "saved"])
def test_history_entry_accepts_canonical_kind(kind: str) -> None:
    entry = _make_entry(kind=kind)
    assert entry.kind == kind


def test_history_entry_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="kind"):
        _make_entry(kind="archived")


@pytest.mark.parametrize("via", ["send", "regen", "load", "import", "capture"])
def test_history_entry_accepts_canonical_via(via: str) -> None:
    entry = _make_entry(via=via)
    assert entry.via == via


def test_history_entry_accepts_none_via_for_root_entry() -> None:
    entry = _make_entry(via=None)
    assert entry.via is None


def test_history_entry_rejects_unknown_via() -> None:
    with pytest.raises(ValueError, match="via"):
        _make_entry(via="copy")


def test_history_entry_to_dict_round_trip_minimal() -> None:
    entry = _make_entry(parent_id=None, via=None, label=None)
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored == entry


def test_history_entry_to_dict_round_trip_full() -> None:
    entry = _make_entry(
        kind="saved",
        parent_id="01HXY5Q9PJM0123456789ABCDP",
        via="send",
        label="industrial-peak",
    )
    restored = HistoryEntry.from_dict(entry.to_dict())
    assert restored == entry


def test_history_entry_to_dict_key_set_is_stable() -> None:
    entry = _make_entry()
    assert set(entry.to_dict().keys()) == {
        "snapshot",
        "kind",
        "parent_id",
        "via",
        "label",
    }


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def test_history_is_frozen() -> None:
    h = History(entries=(_make_entry(),), current_id="01HXY5Q9PJM0123456789ABCD0")
    with pytest.raises(FrozenInstanceError):
        h.current_id = "foo"  # type: ignore[misc]


def test_history_entries_is_tuple() -> None:
    h = History(entries=(_make_entry(),), current_id="01HXY5Q9PJM0123456789ABCD0")
    assert isinstance(h.entries, tuple)


def test_history_rejects_current_id_not_in_entries() -> None:
    with pytest.raises(ValueError, match="current_id"):
        History(
            entries=(_make_entry(snap_id="01HXY5Q9PJM0123456789ABCD0"),),
            current_id="missing",
        )


def test_history_rejects_duplicate_entry_snapshot_ids() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        History(
            entries=(
                _make_entry(snap_id="01HXY5Q9PJM0123456789ABCD0"),
                _make_entry(snap_id="01HXY5Q9PJM0123456789ABCD0"),
            ),
            current_id="01HXY5Q9PJM0123456789ABCD0",
        )


def test_history_accepts_empty_history_when_current_id_is_empty() -> None:
    """A fresh session has zero entries and no current pointer."""

    h = History(entries=(), current_id="")
    assert h.entries == ()
    assert h.current_id == ""


def test_history_rejects_nonempty_current_id_with_empty_entries() -> None:
    with pytest.raises(ValueError, match="current_id"):
        History(entries=(), current_id="01HXY5Q9PJM0123456789ABCD0")


def test_history_to_dict_round_trip_empty() -> None:
    h = History(entries=(), current_id="")
    restored = History.from_dict(h.to_dict())
    assert restored == h


def test_history_to_dict_round_trip_chain() -> None:
    h = History(
        entries=(
            _make_entry(snap_id="01HXY5Q9PJM0123456789ABCD0", via=None),
            _make_entry(
                snap_id="01HXY5Q9PJM0123456789ABCD1",
                parent_id="01HXY5Q9PJM0123456789ABCD0",
                via="send",
            ),
            _make_entry(
                snap_id="01HXY5Q9PJM0123456789ABCD2",
                parent_id="01HXY5Q9PJM0123456789ABCD1",
                via="regen",
                kind="saved",
                label="warehouse-peak",
            ),
        ),
        current_id="01HXY5Q9PJM0123456789ABCD2",
    )
    restored = History.from_dict(h.to_dict())
    assert restored == h


def test_history_entry_from_dict_rejects_non_mapping_snapshot() -> None:
    bad = {
        "snapshot": ["not", "a", "mapping"],
        "kind": "auto",
        "parent_id": None,
        "via": None,
        "label": None,
    }
    with pytest.raises(TypeError, match="snapshot"):
        HistoryEntry.from_dict(bad)


def test_history_from_dict_rejects_non_iterable_entries() -> None:
    bad = {"entries": {"not": "a list"}, "current_id": ""}
    with pytest.raises(TypeError, match="entries"):
        History.from_dict(bad)


def test_history_to_dict_key_set_is_stable() -> None:
    h = History(entries=(_make_entry(),), current_id="01HXY5Q9PJM0123456789ABCD0")
    assert set(h.to_dict().keys()) == {"entries", "current_id"}
