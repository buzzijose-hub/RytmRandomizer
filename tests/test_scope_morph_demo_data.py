"""Drift guard: the cockpit scope/morph demo fixtures track the Python engines.

The interactive scope/morph cockpit panels ship a small committed JSON fixture
(``desktop/web/src/cockpit/panels/scopeMorphDemoData.json``) plus an expected
plan fixture (``desktop/web/tests/cockpit/fixtures/scope_morph_expected.json``)
so the TypeScript client preview matches the Python reference byte-for-byte.
These tests re-derive both from the live engines and fail loudly if a profile
or engine change makes them stale — regenerate the fixtures in the same PR.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.behavior import morph, scope

pytestmark = pytest.mark.fast

REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
DEMO_DATA_PATH: Final[Path] = (
    REPO_ROOT / "desktop" / "web" / "src" / "cockpit" / "panels" / "scopeMorphDemoData.json"
)
EXPECTED_PLAN_PATH: Final[Path] = (
    REPO_ROOT / "desktop" / "web" / "tests" / "cockpit" / "fixtures" / "scope_morph_expected.json"
)

_SCOPE_TRACKS: Final[tuple[tuple[int, str], ...]] = ((1, "1"), (2, "6"))
_MORPH_TRACKS: Final[tuple[tuple[int, str, str], ...]] = ((1, "1", "3"),)
_GROUPS: Final[frozenset[str]] = frozenset({"src", "filter"})
_DEPTH: Final[float] = 0.5
_AMOUNT: Final[float] = 0.5


def _scope_track_data(track: int, key: str) -> dict[str, object]:
    ts = scope.build_track_scope(track, key)
    groups = [[g, list(ps)] for g, ps in ts.groups.items() if g in _GROUPS]
    names = [n for _, ps in groups for n in ps]
    return {
        "track": track,
        "profileName": ts.profile_name,
        "groups": groups,
        "anchor": {n: ts.anchor[n] for n in names if n in ts.anchor},
        "safe": {n: list(ts.safe[n]) for n in names if n in ts.safe},
    }


def _morph_track_data(track: int, source_key: str, target_key: str) -> dict[str, object]:
    mt = morph.build_morph_track(track, source_key, target_key)
    groups = [[g, list(ps)] for g, ps in mt.groups.items() if g in _GROUPS]
    names = [n for _, ps in groups for n in ps]
    return {
        "track": track,
        "sourceName": mt.source_name,
        "targetName": mt.target_name,
        "groups": groups,
        "source": {n: mt.source[n] for n in names if n in mt.source},
        "target": {n: mt.target[n] for n in names if n in mt.target},
    }


def _build_demo_data() -> dict[str, object]:
    return {
        "scopeTracks": [_scope_track_data(track, key) for track, key in _SCOPE_TRACKS],
        "morphTracks": [_morph_track_data(track, s, t) for track, s, t in _MORPH_TRACKS],
    }


def _build_expected_plans() -> dict[str, object]:
    scopes = [scope.build_track_scope(track, key) for track, key in _SCOPE_TRACKS]
    mask = scope.ScopeMask(frozenset(track for track, _ in _SCOPE_TRACKS), _GROUPS)
    sp = scope.plan_scope(scopes, mask, _DEPTH)
    scope_plan = {
        "depth": sp.depth,
        "totalChanged": sp.total_changed,
        "ready": sp.ready,
        "readinessReason": sp.readiness_reason,
        "tracks": [
            {
                "track": tp.track,
                "changedCount": tp.changed_count,
                "deltas": [
                    {
                        "name": d.name,
                        "group": d.group,
                        "anchor": d.anchor,
                        "planned": d.planned,
                        "delta": d.delta,
                    }
                    for d in tp.deltas
                ],
            }
            for tp in sp.track_plans
        ],
    }
    tracks = [morph.build_morph_track(track, s, t) for track, s, t in _MORPH_TRACKS]
    mp = morph.plan_morph(tracks, _GROUPS, _AMOUNT)
    morph_plan = {
        "amount": mp.amount,
        "totalMoved": mp.total_moved,
        "ready": mp.ready,
        "readinessReason": mp.readiness_reason,
        "tracks": [
            {
                "track": tp.track,
                "movedCount": tp.moved_count,
                "unmatched": list(tp.unmatched),
                "params": [
                    {
                        "name": p.name,
                        "group": p.group,
                        "source": p.source,
                        "target": p.target,
                        "interpolated": p.interpolated,
                        "discrete": p.discrete,
                        "moved": p.moved,
                    }
                    for p in tp.params
                ],
            }
            for tp in mp.track_plans
        ],
    }
    return {"scope": scope_plan, "morph": morph_plan}


def test_demo_data_fixture_matches_engines() -> None:
    committed = json.loads(DEMO_DATA_PATH.read_text(encoding="utf-8"))
    assert committed == _build_demo_data(), (
        "scopeMorphDemoData.json is stale. Regenerate it from the Python "
        "engines (see the module docstring) in the same PR."
    )


def test_expected_plan_fixture_matches_engines() -> None:
    committed = json.loads(EXPECTED_PLAN_PATH.read_text(encoding="utf-8"))
    assert committed == _build_expected_plans(), (
        "scope_morph_expected.json is stale. Regenerate it from the Python "
        "engines (see the module docstring) in the same PR."
    )
