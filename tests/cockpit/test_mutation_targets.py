"""First-class include-list mutation target semantics."""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.mutation_targets import MutationTargets

pytestmark = pytest.mark.fast


def test_empty_targets_preserve_default_scope_then_subtract_locks() -> None:
    targets = MutationTargets()

    assert targets.effective_rytm_pads(range(1, 5), {2}) == frozenset({1, 3, 4})
    assert targets.effective_a4_tracks(range(1, 5), {4}) == frozenset({1, 2, 3})
    assert targets.effective_rytm_pads(locked_pad_ids={12}) == frozenset(range(1, 12))
    assert targets.effective_a4_tracks(locked_track_ids={4}) == frozenset({1, 2, 3})


def test_explicit_targets_are_include_lists_and_locks_remain_deny_lists() -> None:
    targets = MutationTargets(
        rytm_pad_targets=frozenset({1, 3, 9}),
        a4_track_targets=frozenset({2, 4}),
    )

    assert targets.effective_rytm_pads(range(1, 7), {3}) == frozenset({1})
    assert targets.effective_a4_tracks(range(1, 5), {4}) == frozenset({2})


@pytest.mark.parametrize(
    ("field", "value"),
    [("rytm_pad_targets", 13), ("a4_track_targets", 5)],
)
def test_target_model_rejects_out_of_range_ids(field: str, value: int) -> None:
    with pytest.raises(ValueError, match=field):
        MutationTargets(**{field: frozenset({value})})  # type: ignore[arg-type]


def test_target_model_wire_round_trip_is_stably_sorted() -> None:
    targets = MutationTargets(
        rytm_pad_targets=frozenset({12, 1}),
        a4_track_targets=frozenset({4, 2}),
    )

    payload = targets.to_dict()

    assert payload == {"rytm_pad_targets": [1, 12], "a4_track_targets": [2, 4]}
    assert MutationTargets.from_dict(payload) == targets


@pytest.mark.parametrize("bad_id", [True, 1.5, "1"])
def test_target_model_rejects_non_integer_ids(bad_id: object) -> None:
    with pytest.raises(ValueError, match="rytm_pad_targets"):
        MutationTargets(rytm_pad_targets=frozenset({bad_id}))  # type: ignore[arg-type]
