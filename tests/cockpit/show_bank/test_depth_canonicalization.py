"""Normalized depth must survive canonical persistence, including integer endpoints."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace

from .conftest import build_show_bank_harness, generate_show_bank_candidates

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("depth", [True, False])
def test_boolean_depth_is_not_coerced_into_a_numeric_recipe(tmp_path: Path, depth: bool) -> None:
    harness = build_show_bank_harness(tmp_path)
    recipe = generate_show_bank_candidates(harness, count=1)[0].recipe
    before = recipe.to_dict()
    with pytest.raises(ValueError, match="depth must be numeric"):
        replace(recipe, depth=depth)
    assert recipe.to_dict() == before


@pytest.mark.parametrize("depth", [0, 0.0, 0.5, 0.9])
def test_numeric_depth_candidate_favorite_reopens_with_exact_canonical_identity(
    tmp_path: Path, depth: float
) -> None:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    (candidate,) = workspace.generate_candidates(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        profile=harness.profile,
        depth_preset="small",
        depth=depth,
        seed=91,
        candidate_count=1,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(),
        analog_four_locks=(1, 2, 3, 4),
        offline_only=True,
    )
    favorite = workspace.mark_favorite(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        workspace.bank(harness.bank_id).revision,
        offline_only=True,
    )
    bank = workspace.bank(harness.bank_id)
    restarted = ShowKitForgeWorkspace(harness.store, clock=harness.clock)
    assert restarted.bank(harness.bank_id) == bank
    assert restarted.bank(harness.bank_id).entry(harness.entry_id).favorite == favorite.favorite
    context = restarted.recall_candidate(
        harness.bank_id,
        harness.entry_id,
        candidate.candidate_id,
        bank.revision,
        offline_only=True,
    )
    assert context.candidate.candidate_id == candidate.candidate_id
    assert context.candidate.recipe.to_dict() == candidate.recipe.to_dict()
    assert context.analog_four_frame == harness.analog_four.frame
    assert type(candidate.recipe.depth) is float
    assert type(candidate.rytm_candidate.depth) is float
    assert candidate.recipe.depth == float(depth)
