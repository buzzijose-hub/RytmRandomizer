"""Tests for ``rytm_randomizer.cockpit.data.mutation_candidate``.

A ``MutationCandidate`` is the deterministic output of
``mutate(snapshot, profile, depth, seed)``. The UI's preview ghost renders
against it; SEND fires it. The dataclass MUST be frozen and round-trip
through ``to_dict`` / ``from_dict``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from rytm_randomizer.cockpit.data.mutation_candidate import (
    MutationCandidate,
    PadDelta,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_pad_delta(
    *,
    pad_id: int = 1,
    proposed_params: dict[str, int] | None = None,
    changed_keys: frozenset[str] | None = None,
) -> PadDelta:
    return PadDelta(
        pad_id=pad_id,
        proposed_params=proposed_params if proposed_params is not None else {"tun": 30, "dec": 60},
        changed_keys=changed_keys if changed_keys is not None else frozenset({"tun"}),
    )


def _make_candidate(
    *,
    depth: float = 0.45,
    pad_deltas: tuple[PadDelta, ...] | None = None,
    safety_status: str = "safe",
) -> MutationCandidate:
    return MutationCandidate(
        candidate_id="01HXY5Q9PJM0123456789ABCD0",
        source_snapshot_id="01HXY5Q9PJM0123456789ABCD1",
        profile_id="01HXY5Q9PJM0123456789ABCD2",
        depth=depth,
        seed=42,
        pad_deltas=pad_deltas if pad_deltas is not None else (_make_pad_delta(),),
        safety_status=safety_status,  # type: ignore[arg-type]
        estimated_midi_msgs=12,
    )


# ---------------------------------------------------------------------------
# PadDelta
# ---------------------------------------------------------------------------


def test_pad_delta_is_frozen() -> None:
    delta = _make_pad_delta()
    with pytest.raises(FrozenInstanceError):
        delta.pad_id = 99  # type: ignore[misc]


def test_pad_delta_changed_keys_must_be_subset_of_proposed_params() -> None:
    """``changed_keys`` is the diff against the source snapshot; every changed
    key must exist in the proposed params (else the delta is malformed)."""

    with pytest.raises(ValueError, match="changed_keys"):
        PadDelta(
            pad_id=1,
            proposed_params={"tun": 30},
            changed_keys=frozenset({"dec"}),
        )


def test_pad_delta_accepts_empty_changed_keys() -> None:
    """An "all params equal source" delta is legal (e.g. a locked pad)."""

    delta = _make_pad_delta(changed_keys=frozenset())
    assert delta.changed_keys == frozenset()


@pytest.mark.parametrize("pad_id", [0, 13])
def test_pad_delta_rejects_out_of_range_pad_id(pad_id: int) -> None:
    with pytest.raises(ValueError, match="pad_id"):
        PadDelta(pad_id=pad_id, proposed_params={}, changed_keys=frozenset())


def test_pad_delta_to_dict_round_trip() -> None:
    delta = _make_pad_delta(
        proposed_params={"tun": 30, "dec": 60, "lev": 100},
        changed_keys=frozenset({"tun", "dec"}),
    )
    restored = PadDelta.from_dict(delta.to_dict())
    assert restored == delta


def test_pad_delta_changed_keys_serializes_as_sorted_list_for_stability() -> None:
    """Sorted serialization makes the dict reproducible across runs."""

    delta = _make_pad_delta(
        proposed_params={"tun": 1, "dec": 2, "lev": 3},
        changed_keys=frozenset({"lev", "tun", "dec"}),
    )
    data = delta.to_dict()
    assert data["changed_keys"] == ["dec", "lev", "tun"]


# ---------------------------------------------------------------------------
# MutationCandidate
# ---------------------------------------------------------------------------


def test_mutation_candidate_is_frozen() -> None:
    cand = _make_candidate()
    with pytest.raises(FrozenInstanceError):
        cand.depth = 0.9  # type: ignore[misc]


def test_mutation_candidate_pad_deltas_is_tuple() -> None:
    cand = _make_candidate()
    assert isinstance(cand.pad_deltas, tuple)


@pytest.mark.parametrize("depth", [0.10, 0.45, 0.90])
def test_mutation_candidate_accepts_in_range_depth(depth: float) -> None:
    cand = _make_candidate(depth=depth)
    assert cand.depth == depth


@pytest.mark.parametrize("depth", [0.0, 0.09, 0.91, 1.0, -0.5, 1.5])
def test_mutation_candidate_rejects_out_of_range_depth(depth: float) -> None:
    with pytest.raises(ValueError, match="depth"):
        _make_candidate(depth=depth)


@pytest.mark.parametrize("status", ["safe", "armed", "high_risk"])
def test_mutation_candidate_accepts_canonical_status(status: str) -> None:
    cand = _make_candidate(safety_status=status)
    assert cand.safety_status == status


def test_mutation_candidate_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="safety_status"):
        _make_candidate(safety_status="dangerous")


def test_mutation_candidate_rejects_negative_estimated_msgs() -> None:
    with pytest.raises(ValueError, match="estimated_midi_msgs"):
        MutationCandidate(
            candidate_id="01H",
            source_snapshot_id="01I",
            profile_id="01J",
            depth=0.5,
            seed=0,
            pad_deltas=(),
            safety_status="safe",
            estimated_midi_msgs=-1,
        )


def test_mutation_candidate_rejects_empty_candidate_id() -> None:
    with pytest.raises(ValueError, match="candidate_id"):
        MutationCandidate(
            candidate_id="",
            source_snapshot_id="01I",
            profile_id="01J",
            depth=0.5,
            seed=0,
            pad_deltas=(),
            safety_status="safe",
            estimated_midi_msgs=0,
        )


def test_mutation_candidate_rejects_empty_source_snapshot_id() -> None:
    with pytest.raises(ValueError, match="source_snapshot_id"):
        MutationCandidate(
            candidate_id="01H",
            source_snapshot_id="",
            profile_id="01J",
            depth=0.5,
            seed=0,
            pad_deltas=(),
            safety_status="safe",
            estimated_midi_msgs=0,
        )


def test_mutation_candidate_rejects_empty_profile_id() -> None:
    with pytest.raises(ValueError, match="profile_id"):
        MutationCandidate(
            candidate_id="01H",
            source_snapshot_id="01I",
            profile_id="",
            depth=0.5,
            seed=0,
            pad_deltas=(),
            safety_status="safe",
            estimated_midi_msgs=0,
        )


def test_mutation_candidate_to_dict_round_trip_minimal() -> None:
    cand = _make_candidate(pad_deltas=())
    restored = MutationCandidate.from_dict(cand.to_dict())
    assert restored == cand


def test_mutation_candidate_to_dict_round_trip_full() -> None:
    cand = _make_candidate(
        pad_deltas=(
            _make_pad_delta(pad_id=1, proposed_params={"tun": 30}, changed_keys=frozenset({"tun"})),
            _make_pad_delta(pad_id=3, proposed_params={"dec": 80}, changed_keys=frozenset({"dec"})),
        ),
    )
    restored = MutationCandidate.from_dict(cand.to_dict())
    assert restored == cand


def test_pad_delta_from_dict_rejects_non_mapping_proposed_params() -> None:
    bad = {
        "pad_id": 1,
        "proposed_params": ["not", "a", "dict"],
        "changed_keys": [],
    }
    with pytest.raises(TypeError, match="proposed_params"):
        PadDelta.from_dict(bad)


def test_pad_delta_from_dict_rejects_non_iterable_changed_keys() -> None:
    bad = {
        "pad_id": 1,
        "proposed_params": {"tun": 1},
        "changed_keys": 12,  # int, not iterable
    }
    with pytest.raises(TypeError, match="changed_keys"):
        PadDelta.from_dict(bad)


def test_mutation_candidate_from_dict_rejects_non_iterable_pad_deltas() -> None:
    bad = {
        "candidate_id": "01H",
        "source_snapshot_id": "01I",
        "profile_id": "01J",
        "depth": 0.5,
        "seed": 0,
        "pad_deltas": {"not": "a list"},
        "safety_status": "safe",
        "estimated_midi_msgs": 0,
    }
    with pytest.raises(TypeError, match="pad_deltas"):
        MutationCandidate.from_dict(bad)


def test_mutation_candidate_to_dict_key_set_is_stable() -> None:
    cand = _make_candidate()
    data = cand.to_dict()
    assert set(data.keys()) == {
        "candidate_id",
        "source_snapshot_id",
        "profile_id",
        "depth",
        "seed",
        "pad_deltas",
        "safety_status",
        "estimated_midi_msgs",
    }
