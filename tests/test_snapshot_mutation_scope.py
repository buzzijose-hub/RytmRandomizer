"""Tests for the canonical snapshot mutation scope value object."""

from __future__ import annotations

import pytest

from rytm_randomizer.snapshot import MutationScope

pytestmark = pytest.mark.fast


def test_device_scope_rejects_unavailable_targets_and_locks() -> None:
    with pytest.raises(ValueError, match="target A4 track"):
        MutationScope(target_ids=frozenset({5})).validated_effective_ids(
            range(1, 5),
            item_label="A4 track",
        )
    with pytest.raises(ValueError, match="locked Rytm pad"):
        MutationScope(locked_ids=frozenset({13})).validated_effective_ids(
            range(1, 13),
            item_label="Rytm pad",
        )


@pytest.mark.parametrize("bad_id", [True, 1.5, "1", 0])
def test_device_scope_rejects_non_positive_integer_ids(bad_id: object) -> None:
    with pytest.raises(ValueError, match="target_ids"):
        MutationScope(target_ids=frozenset({bad_id}))  # type: ignore[arg-type]
