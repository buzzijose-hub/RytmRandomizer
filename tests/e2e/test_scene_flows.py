"""End-to-end scene-flow tests (WS-R).

These tests parameterize over the 14 V1.34 scenes (S0-S5, including A/B
variants S1A/S1B/S2A/S2B/S3A/S3B/S4A/S4B) and verify that for every scene:

* The flow ``SCN -> <scene> -> S5 -> Q`` exits cleanly with code 0.
* The scene emits a **non-empty** sequence of MIDI messages (i.e. it
  actually mutates the four-pad group; a scene that silently sent zero
  messages would be a real regression).
* The trailing ``S5`` returns every pad to its validated anchor state.

The 14 scenes are read straight from
:data:`rytm_randomizer.data.scenes.SCENE_PRESETS` so adding a new scene to
the canonical data automatically gets E2E coverage.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.data import SCENE_PRESETS

from .conftest import CapturedMessage, run_canonical_dry_run

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast


def _final_state_by_channel_control(
    messages: tuple[CapturedMessage, ...],
) -> dict[tuple[int, int], int]:
    """Effective device state: last value for each ``(channel, control)``."""

    final: dict[tuple[int, int], int] = {}
    for msg in messages:
        final[(msg.channel, msg.control)] = msg.value
    return final


# The full V1.34 scene roster, sorted for deterministic test-id order.
SCENE_KEYS: tuple[str, ...] = tuple(sorted(SCENE_PRESETS.keys()))


def test_scene_roster_matches_v134_doc() -> None:
    """Cheap sanity check: the V1.34 docs call out 14 scenes (S0-S5 plus
    A/B variants on S1-S4). The data layer must agree.
    """

    expected = {
        "s0",
        "s1",
        "s1a",
        "s1b",
        "s2",
        "s2a",
        "s2b",
        "s3",
        "s3a",
        "s3b",
        "s4",
        "s4a",
        "s4b",
        "s5",
    }
    assert set(SCENE_KEYS) == expected, (
        "V1.34 scene roster drifted from the documented 14-scene set. "
        f"Got {set(SCENE_KEYS)}, expected {expected}."
    )


@pytest.mark.parametrize("scene_key", SCENE_KEYS)
def test_scene_flow_dispatches_via_real_entry_point(
    scene_key: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Drive ``SCN -> <scene> -> S5 -> Q`` for every V1.34 scene.

    Asserts:

    1. The entry point exits cleanly (code 0).
    2. The scene command itself caused MIDI to flow (every scene either
       loads anchors -- S0 -- or auto-loads anchors then runs an
       intensity plan, so the stream is always non-empty).
    3. Every one of the four channels ``0..3`` appears in the stream
       (the four-pad group is genuinely being driven, not just one pad).
    """

    commands = ("SCN", scene_key.upper(), "S5", "Q")
    result = run_canonical_dry_run(commands, capsys=capsys)

    assert result.exit_code == 0, (
        f"Scene flow {scene_key.upper()} returned non-zero exit code "
        f"{result.exit_code}: {result.stderr}"
    )
    assert result.captured, (
        f"Scene {scene_key.upper()} emitted ZERO MIDI messages. "
        "Every documented V1.34 scene either loads the four-pad anchors "
        "or runs an intensity plan -- a silent scene is a regression."
    )

    channels_used = {msg.channel for msg in result.captured}
    assert channels_used == {0, 1, 2, 3}, (
        f"Scene {scene_key.upper()} only used MIDI channels "
        f"{sorted(channels_used)}; expected all of 0-3 (one per pad). "
        "A scene that misses a pad is a real regression."
    )


@pytest.mark.parametrize("scene_key", SCENE_KEYS)
def test_scene_flow_ends_at_anchors_after_s5(
    scene_key: str,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """For every scene, ``SCN -> <scene> -> S5`` must end at anchors.

    Compares the final per-(channel, control) state of ``S0 -> Q`` against
    the final state of ``SCN -> <scene> -> S5 -> Q``: every CC the cold
    anchor load wrote must end at the same value after S5.
    """

    anchor_only = run_canonical_dry_run(("S0", "Q"), capsys=capsys)
    assert anchor_only.exit_code == 0, anchor_only.stderr

    flow = run_canonical_dry_run(
        ("SCN", scene_key.upper(), "S5", "Q"),
        capsys=capsys,
    )
    assert flow.exit_code == 0, flow.stderr

    anchor_state = _final_state_by_channel_control(anchor_only.captured)
    flow_state = _final_state_by_channel_control(flow.captured)

    # Every (channel, control) the anchor load wrote must end at the same
    # value in the scene+S5 flow. (The scene+S5 flow can also write CCs
    # the cold load did not -- e.g. scene-specific extras -- those are
    # tolerated; we only check the anchor positions.)
    drift: list[str] = []
    for key, expected_value in anchor_state.items():
        actual = flow_state.get(key)
        if actual != expected_value:
            drift.append(f"  ch{key[0]} CC{key[1]}: anchor={expected_value} " f"post-S5={actual}")

    assert not drift, (
        f"Scene {scene_key.upper()} -> S5 did not return the four pads "
        "to their validated anchors. Drift detected on:\n" + "\n".join(drift)
    )


def test_all_scene_variants_are_distinguishable(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Distinct scenes should produce distinct MIDI streams.

    With a deterministic seed, two different scene actions should not
    coincidentally produce the same byte-for-byte stream. We sample three
    non-anchor scenes to keep the test cheap.
    """

    streams: dict[str, tuple[CapturedMessage, ...]] = {}
    for scene_key in ("s1a", "s3a", "s4b"):
        result = run_canonical_dry_run(
            ("SCN", scene_key.upper(), "Q"),
            capsys=capsys,
        )
        assert result.exit_code == 0
        streams[scene_key] = result.captured

    # Pairwise: each captured stream must differ from the others.
    keys = list(streams)
    for i, a in enumerate(keys):
        for b in keys[i + 1 :]:
            assert streams[a] != streams[b], (
                f"Scenes {a.upper()} and {b.upper()} produced identical "
                "MIDI streams under the seeded RNG. Either the scene data "
                "drifted into a degenerate state or the dispatch is wrong."
            )
