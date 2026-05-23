"""Tests for ``rytm_randomizer.cockpit.history.store`` — :class:`HistoryStore`.

The store is the write-side state machine for the cockpit's history strip:
bootstrap an initial snapshot, append after a SEND/REGEN/LOAD/IMPORT, walk
back one step via UNDO, jump to any past entry via LOAD, and promote the
current entry to ``"saved"``.

The dataclass tests live in ``test_data_history.py`` — these tests cover
the state machine's behavior (transitions, error cases, idempotence,
parent-chain integrity) and target 100% branch coverage on
``cockpit/history/**``.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import History, HistoryEntry, PadState, Snapshot
from rytm_randomizer.cockpit.history import HistoryStore

pytestmark = pytest.mark.fast


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_snap(snap_id: str, tun: int = 30) -> Snapshot:
    """Build a minimal valid :class:`Snapshot` with a stable id."""

    return Snapshot(
        snapshot_id=snap_id,
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": tun}),),
        scene_slot=None,
        bpm=None,
    )


# Distinct, valid-shaped ULIDs for chain tests (Crockford alphabet, 26 chars).
SNAP_A = "01HXY5Q9PJM0123456789ABCDA0"
SNAP_B = "01HXY5Q9PJM0123456789ABCDB0"
SNAP_C = "01HXY5Q9PJM0123456789ABCDC0"
SNAP_D = "01HXY5Q9PJM0123456789ABCDD0"


# ---------------------------------------------------------------------------
# Empty store
# ---------------------------------------------------------------------------


def test_empty_store_has_no_entries() -> None:
    store = HistoryStore()
    assert store.has_entries is False


def test_empty_store_current_is_empty_history() -> None:
    store = HistoryStore()
    h = store.current
    assert h == History(entries=(), current_id="")


def test_empty_store_cannot_undo() -> None:
    store = HistoryStore()
    assert store.can_undo is False


def test_undo_on_empty_store_raises() -> None:
    store = HistoryStore()
    with pytest.raises(ValueError, match="no parent"):
        store.undo()


def test_append_post_send_without_initial_raises() -> None:
    store = HistoryStore()
    with pytest.raises(RuntimeError, match="initial"):
        store.append_post_send(_make_snap(SNAP_A), via="send")


def test_load_on_empty_store_raises_key_error() -> None:
    store = HistoryStore()
    with pytest.raises(KeyError, match=SNAP_A):
        store.load(SNAP_A)


def test_promote_on_empty_store_raises() -> None:
    store = HistoryStore()
    with pytest.raises(RuntimeError, match="current entry"):
        store.promote_current_to_saved("anything")


# ---------------------------------------------------------------------------
# initial()
# ---------------------------------------------------------------------------


def test_initial_records_root_entry() -> None:
    store = HistoryStore()
    snap = _make_snap(SNAP_A)
    result = store.initial(snap)

    assert store.has_entries is True
    assert result.current_id == SNAP_A
    assert len(result.entries) == 1
    root = result.entries[0]
    assert root.snapshot is snap
    assert root.kind == "auto"
    assert root.parent_id is None
    assert root.via is None
    assert root.label is None


def test_initial_returns_same_history_as_current_property() -> None:
    store = HistoryStore()
    snap = _make_snap(SNAP_A)
    returned = store.initial(snap)
    assert returned == store.current


def test_initial_called_twice_raises() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    with pytest.raises(RuntimeError, match="only be called once"):
        store.initial(_make_snap(SNAP_B))


def test_initial_alone_does_not_allow_undo() -> None:
    """Root entry has parent_id=None, so undo is not allowed."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    assert store.can_undo is False
    with pytest.raises(ValueError, match="no parent"):
        store.undo()


# ---------------------------------------------------------------------------
# append_post_send()
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("via", ["send", "regen", "load", "import"])
def test_append_post_send_accepts_every_canonical_via(via: str) -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    result = store.append_post_send(_make_snap(SNAP_B), via=via)  # type: ignore[arg-type]
    assert result.entries[-1].via == via


def test_append_post_send_advances_current_id() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    assert store.current.current_id == SNAP_B


def test_append_post_send_sets_parent_id_to_previous_current() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    result = store.append_post_send(_make_snap(SNAP_B), via="send")
    assert result.entries[-1].parent_id == SNAP_A


def test_append_post_send_records_kind_auto() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    result = store.append_post_send(_make_snap(SNAP_B), via="send")
    assert result.entries[-1].kind == "auto"
    assert result.entries[-1].label is None


def test_append_post_send_preserves_chronological_order() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    ids = [e.snapshot.snapshot_id for e in store.current.entries]
    assert ids == [SNAP_A, SNAP_B, SNAP_C]


def test_append_post_send_rejects_duplicate_snapshot_id() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    with pytest.raises(ValueError, match="already present"):
        store.append_post_send(_make_snap(SNAP_A), via="send")


# ---------------------------------------------------------------------------
# Parent-chain integrity
# ---------------------------------------------------------------------------


def test_parent_chain_links_each_entry_to_its_predecessor() -> None:
    """A → B → C: every non-root entry's parent_id is its predecessor."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    entries = store.current.entries
    assert entries[0].parent_id is None
    assert entries[1].parent_id == SNAP_A
    assert entries[2].parent_id == SNAP_B


def test_parent_chain_after_load_then_append_is_from_loaded_entry() -> None:
    """LOAD sets current_id; the next SEND parents off the loaded snapshot."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    store.load(SNAP_A)
    store.append_post_send(_make_snap(SNAP_D), via="send")
    last = store.current.entries[-1]
    assert last.snapshot.snapshot_id == SNAP_D
    assert last.parent_id == SNAP_A


# ---------------------------------------------------------------------------
# undo()
# ---------------------------------------------------------------------------


def test_undo_walks_back_one_step() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    result = store.undo()
    assert result.current_id == SNAP_A


def test_undo_multiple_steps() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    store.append_post_send(_make_snap(SNAP_D), via="send")
    assert store.current.current_id == SNAP_D
    store.undo()
    assert store.current.current_id == SNAP_C
    store.undo()
    assert store.current.current_id == SNAP_B
    store.undo()
    assert store.current.current_id == SNAP_A


def test_undo_to_root_then_undo_raises() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.undo()
    assert store.current.current_id == SNAP_A
    with pytest.raises(ValueError, match="no parent"):
        store.undo()


def test_undo_does_not_remove_entries() -> None:
    """UNDO is non-destructive — entries remain available for LOAD."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    store.undo()
    store.undo()
    assert [e.snapshot.snapshot_id for e in store.current.entries] == [SNAP_A, SNAP_B, SNAP_C]


def test_can_undo_true_when_current_has_parent() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    assert store.can_undo is True


def test_can_undo_false_after_walking_to_root() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.undo()
    assert store.can_undo is False


# ---------------------------------------------------------------------------
# load()
# ---------------------------------------------------------------------------


def test_load_sets_current_to_arbitrary_known_entry() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    result = store.load(SNAP_A)
    assert result.current_id == SNAP_A


def test_load_to_current_is_idempotent() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    before = store.current
    result = store.load(SNAP_B)
    assert result == before


def test_load_unknown_id_raises_key_error() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    with pytest.raises(KeyError, match=SNAP_B):
        store.load(SNAP_B)


def test_load_after_undo_can_jump_forward() -> None:
    """UNDO + LOAD lets the operator visit any past snapshot in any order."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    store.undo()  # back to B
    store.undo()  # back to A
    store.load(SNAP_C)  # forward to C
    assert store.current.current_id == SNAP_C


# ---------------------------------------------------------------------------
# promote_current_to_saved()
# ---------------------------------------------------------------------------


def test_promote_changes_kind_and_sets_label() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    result = store.promote_current_to_saved("industrial-peak")
    promoted = result.entries[-1]
    assert promoted.kind == "saved"
    assert promoted.label == "industrial-peak"


def test_promote_with_none_label() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    result = store.promote_current_to_saved(None)
    assert result.entries[-1].label is None
    assert result.entries[-1].kind == "saved"


def test_promote_preserves_parent_and_via() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="regen")
    result = store.promote_current_to_saved("label-b")
    promoted = result.entries[-1]
    assert promoted.parent_id == SNAP_A
    assert promoted.via == "regen"
    assert promoted.snapshot.snapshot_id == SNAP_B


def test_promote_is_idempotent_for_already_saved() -> None:
    """Re-promoting an already-saved entry just updates the label."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.promote_current_to_saved("first")
    result = store.promote_current_to_saved("second")
    promoted = result.entries[-1]
    assert promoted.kind == "saved"
    assert promoted.label == "second"


def test_promote_preserves_chain_order_and_count() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    store.load(SNAP_B)  # promote the middle entry
    result = store.promote_current_to_saved("middle")
    ids = [e.snapshot.snapshot_id for e in result.entries]
    assert ids == [SNAP_A, SNAP_B, SNAP_C]
    middle = next(e for e in result.entries if e.snapshot.snapshot_id == SNAP_B)
    assert middle.kind == "saved"
    assert middle.label == "middle"


def test_promote_then_load_returns_saved_entry() -> None:
    """The id index is updated in place after promotion."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.promote_current_to_saved("snapshot-B-saved")
    store.load(SNAP_A)
    result = store.load(SNAP_B)
    promoted = next(e for e in result.entries if e.snapshot.snapshot_id == SNAP_B)
    assert promoted.kind == "saved"
    assert promoted.label == "snapshot-B-saved"


def test_promote_can_undo_after_does_not_change() -> None:
    """Promotion preserves parent_id, so can_undo is unaffected."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    store.append_post_send(_make_snap(SNAP_B), via="send")
    assert store.can_undo is True
    store.promote_current_to_saved("B")
    assert store.can_undo is True
    store.undo()
    assert store.current.current_id == SNAP_A


# ---------------------------------------------------------------------------
# Return-value type / immutability
# ---------------------------------------------------------------------------


def test_current_returns_immutable_history() -> None:
    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))
    snap_a = store.current
    store.append_post_send(_make_snap(SNAP_B), via="send")
    # The previously-returned History is unaffected by later mutations.
    assert snap_a.entries == (
        HistoryEntry(
            snapshot=_make_snap(SNAP_A),
            kind="auto",
            parent_id=None,
            via=None,
            label=None,
        ),
    )
    assert snap_a.current_id == SNAP_A


def test_each_mutator_returns_history_instance() -> None:
    store = HistoryStore()
    assert isinstance(store.initial(_make_snap(SNAP_A)), History)
    assert isinstance(store.append_post_send(_make_snap(SNAP_B), via="send"), History)
    assert isinstance(store.undo(), History)
    assert isinstance(store.load(SNAP_B), History)
    assert isinstance(store.promote_current_to_saved("x"), History)


# ---------------------------------------------------------------------------
# Realistic operator flow (smoke)
# ---------------------------------------------------------------------------


def test_realistic_session_flow_send_undo_load_save() -> None:
    """A → SEND B → SEND C → UNDO (back to B) → LOAD A → SEND D → SAVE D."""

    store = HistoryStore()
    store.initial(_make_snap(SNAP_A))

    store.append_post_send(_make_snap(SNAP_B), via="send")
    store.append_post_send(_make_snap(SNAP_C), via="regen")
    assert store.current.current_id == SNAP_C

    store.undo()
    assert store.current.current_id == SNAP_B

    store.load(SNAP_A)
    assert store.current.current_id == SNAP_A

    store.append_post_send(_make_snap(SNAP_D), via="send")
    assert store.current.current_id == SNAP_D
    # SEND D parents off the loaded A, not the previous chain tip C.
    assert store.current.entries[-1].parent_id == SNAP_A

    final = store.promote_current_to_saved("final-kit")
    saved = final.entries[-1]
    assert saved.snapshot.snapshot_id == SNAP_D
    assert saved.kind == "saved"
    assert saved.label == "final-kit"
    assert [e.snapshot.snapshot_id for e in final.entries] == [SNAP_A, SNAP_B, SNAP_C, SNAP_D]
