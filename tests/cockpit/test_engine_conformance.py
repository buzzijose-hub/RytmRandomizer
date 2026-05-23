"""Engine conformance corpus — drives 50+ byte-frozen fixture comparisons.

Every fixture under ``tests/cockpit/fixtures/engine_conformance/*.json``
encodes a ``(snapshot, profile, depth, seed)`` tuple and the expected
``MutationCandidate.to_dict()`` output (with ``candidate_id`` stripped,
since that field is non-deterministic by design).

The fixtures are generated programmatically by the
``regenerate`` helper in this file when invoked as a module-level
script, then committed. The test reads every fixture at test time and
asserts byte-equality with a fresh call to ``mutate(...)``. A C99 / Rust
port that satisfies every fixture is *by construction* conformant.

To regenerate after an intentional spec change::

    "$PYTHON" -m tests.cockpit.test_engine_conformance regenerate

The regen path lives behind a CLI guard so a stray test invocation can
never silently rewrite the locked corpus.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import (
    PadState,
    ProfileModel,
    Snapshot,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.engine.mutate import mutate

pytestmark = pytest.mark.fast

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "engine_conformance"


# ---------------------------------------------------------------------------
# Fixture construction recipes — used by both the test and the regenerator
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Case:
    """One conformance case: inputs + filename."""

    name: str
    snapshot: Snapshot
    profile: ProfileModel
    depth: float
    seed: int


_DT = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


def _trait(name: str, value: float) -> StyleTrait:
    return StyleTrait(name=name, value=value)


def _map(trait: str, pad_id: int, weight: float) -> TraitPadWeight:
    return TraitPadWeight(trait=trait, pad_id=pad_id, weight=weight)


def _pad(pad_id: int, machine: str, params: dict[str, int]) -> PadState:
    return PadState(pad_id=pad_id, machine=machine, params=params)


def _snap(snap_id: str, pads: tuple[PadState, ...]) -> Snapshot:
    return Snapshot(
        snapshot_id=snap_id,
        device="rytm_mk2",
        captured_at=_DT,
        pads=pads,
        scene_slot=None,
        bpm=128.0,
    )


def _prof(
    profile_id: str,
    traits: tuple[StyleTrait, ...],
    mappings: tuple[TraitPadWeight, ...],
    *,
    kind: str = "user",
) -> ProfileModel:
    return ProfileModel(
        profile_id=profile_id,
        name=f"profile_{profile_id}",
        kind=kind,  # type: ignore[arg-type]
        model_version="1.0",
        traits=traits,
        pad_mappings=mappings,
        transition_curve="linear",
        source_summary="conformance fixture",
    )


def _build_cases() -> list[_Case]:
    """Build the canonical fixture set: 50+ (snapshot, profile, depth, seed) tuples.

    The cases sweep:

    * Pad counts: 1, 2, 4, 8.
    * Param counts: 1, 4, 8.
    * Bias mappings: none, one trait, two traits with multiple pad-mappings.
    * Depths: 0.10, 0.30, 0.45, 0.65, 0.90 (one per safety bucket border).
    * Seeds: 1, 7, 42, 12345, 0xDEADBEEF, 0 (the substitute branch).
    * Edge values: pads at 0, pads at 127, mixed.
    """

    cases: list[_Case] = []

    # ---- Snapshots ------------------------------------------------------
    snap_1pad_mid = _snap("SNAP_1PAD_MID", (_pad(1, "bd", {"a": 64, "b": 64}),))
    snap_2pad_basic = _snap(
        "SNAP_2PAD_BASIC",
        (
            _pad(1, "bd_classic", {"tun": 60, "dec": 40, "lev": 100}),
            _pad(2, "sd_classic", {"tun": 50, "dec": 80, "lev": 90}),
        ),
    )
    snap_4pad = _snap(
        "SNAP_4PAD",
        (
            _pad(1, "bd_classic", {"tun": 60, "dec": 40}),
            _pad(2, "sd_classic", {"tun": 50, "dec": 80}),
            _pad(3, "hh_classic", {"tun": 30, "dec": 20}),
            _pad(4, "cp_classic", {"tun": 70, "dec": 90}),
        ),
    )
    snap_8pad = _snap(
        "SNAP_8PAD",
        tuple(
            _pad(i, f"machine_{i}", {f"k{j}": 20 + 10 * i + j for j in range(4)})
            for i in range(1, 9)
        ),
    )
    snap_extremes = _snap(
        "SNAP_EXTREMES",
        (
            _pad(1, "bd", {"low": 0, "high": 127, "mid": 64}),
            _pad(2, "sd", {"low": 0, "high": 127, "mid": 64}),
        ),
    )
    snap_one_key = _snap("SNAP_ONE_KEY", (_pad(1, "bd", {"k": 64}),))
    snap_eight_keys = _snap(
        "SNAP_EIGHT_KEYS",
        (_pad(1, "bd", {f"p{i}": 32 + i * 5 for i in range(8)}),),
    )

    # ---- Profiles -------------------------------------------------------
    prof_empty = _prof("PROF_EMPTY", (_trait("dummy", 0.5),), ())
    prof_one_trait_pad1 = _prof(
        "PROF_ONE_TRAIT_PAD1",
        (_trait("low_end", 0.8),),
        (_map("low_end", 1, 0.9),),
    )
    prof_dual_traits = _prof(
        "PROF_DUAL_TRAITS",
        (_trait("low_end", 0.8), _trait("texture", 0.3)),
        (_map("low_end", 1, 0.9), _map("texture", 2, 0.5)),
    )
    prof_all_pads_mapped = _prof(
        "PROF_ALL_PADS",
        (_trait("energy", 0.7), _trait("grit", 0.4)),
        tuple(_map("energy", pid, 0.5) for pid in range(1, 9))
        + tuple(_map("grit", pid, 0.3) for pid in range(1, 9)),
    )
    prof_scene = _prof(
        "PROF_SCENE",
        (_trait("rolling", 0.85), _trait("bass", 0.7), _trait("space", 0.2)),
        (
            _map("rolling", 1, 0.9),
            _map("bass", 2, 0.7),
            _map("space", 3, 0.4),
            _map("rolling", 4, 0.5),
        ),
        kind="scene",
    )

    # ---- Sweep ----------------------------------------------------------
    depth_grid = [0.10, 0.30, 0.45, 0.65, 0.90]
    seeds = [1, 7, 42, 12345, 0xDEADBEEF, 0]

    # Case 1: 1-pad small snapshots, all depths, all seeds
    for d in depth_grid:
        for s in seeds:
            cases.append(
                _Case(
                    name=f"one_pad_one_trait_d{int(d * 100):02d}_s{s:x}",
                    snapshot=snap_1pad_mid,
                    profile=prof_one_trait_pad1,
                    depth=d,
                    seed=s,
                )
            )
    # Case 2: 2-pad with dual traits, all depths, two seeds
    for d in depth_grid:
        for s in (42, 12345):
            cases.append(
                _Case(
                    name=f"two_pad_dual_traits_d{int(d * 100):02d}_s{s:x}",
                    snapshot=snap_2pad_basic,
                    profile=prof_dual_traits,
                    depth=d,
                    seed=s,
                )
            )
    # Case 3: 4-pad with scene-profile, two depths, two seeds
    for d in (0.30, 0.65):
        for s in (1, 0xDEADBEEF):
            cases.append(
                _Case(
                    name=f"four_pad_scene_d{int(d * 100):02d}_s{s:x}",
                    snapshot=snap_4pad,
                    profile=prof_scene,
                    depth=d,
                    seed=s,
                )
            )
    # Case 4: 8-pad with all_pads_mapped, two depths
    for d in (0.10, 0.90):
        cases.append(
            _Case(
                name=f"eight_pad_all_mapped_d{int(d * 100):02d}_s42",
                snapshot=snap_8pad,
                profile=prof_all_pads_mapped,
                depth=d,
                seed=42,
            )
        )
    # Case 5: extremes — clamping behavior at edge values
    for d in (0.45, 0.90):
        for s in (1, 42):
            cases.append(
                _Case(
                    name=f"extremes_d{int(d * 100):02d}_s{s:x}",
                    snapshot=snap_extremes,
                    profile=prof_dual_traits,
                    depth=d,
                    seed=s,
                )
            )
    # Case 6: empty profile (no mappings) — bias=0 path
    for s in (1, 42, 12345):
        cases.append(
            _Case(
                name=f"empty_profile_d050_s{s:x}",
                snapshot=snap_2pad_basic,
                profile=prof_empty,
                depth=0.5,
                seed=s,
            )
        )
    # Case 7: one-key pad sweep — minimal draws
    for s in (1, 7, 42, 12345, 0xDEADBEEF):
        cases.append(
            _Case(
                name=f"one_key_pad_d050_s{s:x}",
                snapshot=snap_one_key,
                profile=prof_one_trait_pad1,
                depth=0.5,
                seed=s,
            )
        )
    # Case 8: eight-key pad — exercises a longer per-pad draw sequence
    for s in (1, 42):
        cases.append(
            _Case(
                name=f"eight_key_pad_d050_s{s:x}",
                snapshot=snap_eight_keys,
                profile=prof_one_trait_pad1,
                depth=0.5,
                seed=s,
            )
        )
    # Case 9: the worked example from spec.md
    cases.append(
        _Case(
            name="worked_example_seed42_depth050",
            snapshot=_snap(
                "SNAP1",
                (
                    _pad(1, "bd_classic", {"tun": 60, "dec": 40}),
                    _pad(2, "sd_classic", {"tun": 50, "dec": 80}),
                ),
            ),
            profile=_prof(
                "PROF1",
                (_trait("low_end", 0.8), _trait("texture", 0.3)),
                (_map("low_end", 1, 0.9), _map("texture", 2, 0.5)),
            ),
            depth=0.5,
            seed=42,
        )
    )

    return cases


def _build_fixture_dict(case: _Case) -> dict[str, object]:
    """Compute the JSON-encodable fixture dict for a case."""

    candidate = mutate(case.snapshot, case.profile, case.depth, case.seed)
    expected = candidate.to_dict()
    # Exclude candidate_id; it's a fresh ULID per call and intentionally
    # excluded from byte-equality.
    expected.pop("candidate_id", None)
    return {
        "name": case.name,
        "snapshot": case.snapshot.to_dict(),
        "profile": case.profile.to_dict(),
        "depth": case.depth,
        "seed": case.seed,
        "expected": expected,
    }


# ---------------------------------------------------------------------------
# Regenerator (CLI-only)
# ---------------------------------------------------------------------------


def regenerate() -> int:
    """Write every conformance fixture to disk. Returns the count."""

    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    cases = _build_cases()
    for case in cases:
        payload = _build_fixture_dict(case)
        out = FIXTURE_DIR / f"{case.name}.json"
        out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return len(cases)


# ---------------------------------------------------------------------------
# Conformance loader + assertion (pytest path)
# ---------------------------------------------------------------------------


def _iter_fixture_files() -> Iterable[Path]:
    """Yield every committed fixture file."""

    if not FIXTURE_DIR.exists():
        return []
    return sorted(FIXTURE_DIR.glob("*.json"))


def _load_fixture(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


_FIXTURE_FILES = list(_iter_fixture_files())


def test_conformance_corpus_size_meets_threshold() -> None:
    """Spec calls for 50+ fixtures locking the algorithm."""

    assert len(_FIXTURE_FILES) >= 50, (
        f"Engine conformance corpus has {len(_FIXTURE_FILES)} fixtures; "
        f"spec requires at least 50. Run "
        f"`python -m tests.cockpit.test_engine_conformance regenerate`."
    )


@pytest.mark.parametrize(
    "fixture_path",
    _FIXTURE_FILES,
    ids=lambda p: p.stem,
)
def test_engine_matches_conformance_fixture(fixture_path: Path) -> None:
    """Every fixture must replay byte-identical to a fresh `mutate(...)` call."""

    data = _load_fixture(fixture_path)
    snap = Snapshot.from_dict(data["snapshot"])  # type: ignore[arg-type]
    prof = ProfileModel.from_dict(data["profile"])  # type: ignore[arg-type]
    depth = float(data["depth"])  # type: ignore[arg-type]
    seed = int(data["seed"])  # type: ignore[arg-type]
    expected = data["expected"]

    candidate = mutate(snap, prof, depth, seed)
    actual = candidate.to_dict()
    actual.pop("candidate_id", None)
    assert actual == expected, f"Conformance regression in {fixture_path.name}"


# ---------------------------------------------------------------------------
# Self-check: regenerator runs cleanly (covers the CLI branch in tests)
# ---------------------------------------------------------------------------


def test_regenerator_emits_expected_case_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run the regenerator in a temp dir and assert it writes every case.

    Also covers the regenerate() function's branch coverage requirement
    without disturbing the committed corpus."""

    monkeypatch.setattr(
        sys.modules[__name__],
        "FIXTURE_DIR",
        tmp_path / "engine_conformance",
    )
    count = regenerate()
    assert count == len(_build_cases())
    written = sorted((tmp_path / "engine_conformance").glob("*.json"))
    assert len(written) == count


# ---------------------------------------------------------------------------
# CLI entry point — `python -m tests.cockpit.test_engine_conformance regenerate`
# ---------------------------------------------------------------------------


if __name__ == "__main__":  # pragma: no cover - CLI entry only
    if len(sys.argv) >= 2 and sys.argv[1] == "regenerate":
        n = regenerate()
        print(f"Wrote {n} conformance fixtures to {FIXTURE_DIR}")
    else:
        print(
            "Usage: python -m tests.cockpit.test_engine_conformance regenerate",
            file=sys.stderr,
        )
        sys.exit(1)
