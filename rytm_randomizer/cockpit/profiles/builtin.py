"""Seven developer-curated built-in Scenes.

Each scene is a frozen ``ProfileModel`` with ``kind="scene"`` and a
deterministic ``profile_id`` (``scene-<name>``) so the cockpit can refer
to it across restarts without ULID drift. Per-pad weights are tuned for a
4-pad reference layout:

* **Pad 1** — BD / kick
* **Pad 2** — SD / snare
* **Pad 3** — SY / synth
* **Pad 4** — FX / filter

The scenes are constructed at module import time and exposed as a frozen
``Final`` tuple ``BUILTIN_SCENES``. The registry treats them as read-only;
they are never written to disk.

See ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"ProfileModel" for the data shape, and the plan §"WS-C" for the chosen
trait set per scene.
"""

from __future__ import annotations

from typing import Final

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight

_MODEL_VERSION: Final[str] = "1.0.0"
"""Built-in scenes ship at engine-format 1.0.0; bumped only by deliberate WSes."""


def _scene_id(name: str) -> str:
    """Deterministic profile_id for a built-in scene (no ULID drift)."""

    return f"scene-{name}"


# ---------------------------------------------------------------------------
# industrial — metallic, harsh, mid-emphasis
# ---------------------------------------------------------------------------

_INDUSTRIAL = ProfileModel(
    profile_id=_scene_id("industrial"),
    name="industrial",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="metallic_tension", value=0.85),
        StyleTrait(name="mid_grit", value=0.80),
        StyleTrait(name="distortion", value=0.70),
    ),
    pad_mappings=(
        TraitPadWeight(trait="metallic_tension", pad_id=1, weight=0.30),
        TraitPadWeight(trait="metallic_tension", pad_id=2, weight=0.75),
        TraitPadWeight(trait="metallic_tension", pad_id=3, weight=0.40),
        TraitPadWeight(trait="metallic_tension", pad_id=4, weight=0.55),
        TraitPadWeight(trait="mid_grit", pad_id=1, weight=0.45),
        TraitPadWeight(trait="mid_grit", pad_id=2, weight=0.70),
        TraitPadWeight(trait="mid_grit", pad_id=3, weight=0.65),
        TraitPadWeight(trait="mid_grit", pad_id=4, weight=0.60),
        TraitPadWeight(trait="distortion", pad_id=1, weight=0.55),
        TraitPadWeight(trait="distortion", pad_id=2, weight=0.65),
        TraitPadWeight(trait="distortion", pad_id=3, weight=0.50),
        TraitPadWeight(trait="distortion", pad_id=4, weight=0.70),
    ),
    transition_curve="progressive",
    source_summary="Built-in scene · metallic, harsh, mid-emphasis",
)

# ---------------------------------------------------------------------------
# hypnotic — drone-y, sparse, repetitive
# ---------------------------------------------------------------------------

_HYPNOTIC = ProfileModel(
    profile_id=_scene_id("hypnotic"),
    name="hypnotic",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="rolling_low_end", value=0.80),
        StyleTrait(name="dry_space", value=0.85),
        StyleTrait(name="sparse_percussion", value=0.75),
    ),
    pad_mappings=(
        TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.85),
        TraitPadWeight(trait="rolling_low_end", pad_id=2, weight=0.20),
        TraitPadWeight(trait="rolling_low_end", pad_id=3, weight=0.40),
        TraitPadWeight(trait="rolling_low_end", pad_id=4, weight=0.30),
        TraitPadWeight(trait="dry_space", pad_id=1, weight=0.60),
        TraitPadWeight(trait="dry_space", pad_id=2, weight=0.70),
        TraitPadWeight(trait="dry_space", pad_id=3, weight=0.80),
        TraitPadWeight(trait="dry_space", pad_id=4, weight=0.65),
        TraitPadWeight(trait="sparse_percussion", pad_id=1, weight=0.40),
        TraitPadWeight(trait="sparse_percussion", pad_id=2, weight=0.80),
        TraitPadWeight(trait="sparse_percussion", pad_id=3, weight=0.55),
        TraitPadWeight(trait="sparse_percussion", pad_id=4, weight=0.50),
    ),
    transition_curve="progressive",
    source_summary="Built-in scene · drone-y, sparse, repetitive",
)

# ---------------------------------------------------------------------------
# garage — snappy, swing, mid-bass
# ---------------------------------------------------------------------------

_GARAGE = ProfileModel(
    profile_id=_scene_id("garage"),
    name="garage",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="snap_attack", value=0.75),
        StyleTrait(name="swing_emphasis", value=0.65),
        StyleTrait(name="mid_bass", value=0.70),
    ),
    pad_mappings=(
        TraitPadWeight(trait="snap_attack", pad_id=1, weight=0.55),
        TraitPadWeight(trait="snap_attack", pad_id=2, weight=0.85),
        TraitPadWeight(trait="snap_attack", pad_id=3, weight=0.40),
        TraitPadWeight(trait="snap_attack", pad_id=4, weight=0.35),
        TraitPadWeight(trait="swing_emphasis", pad_id=1, weight=0.50),
        TraitPadWeight(trait="swing_emphasis", pad_id=2, weight=0.75),
        TraitPadWeight(trait="swing_emphasis", pad_id=3, weight=0.60),
        TraitPadWeight(trait="swing_emphasis", pad_id=4, weight=0.45),
        TraitPadWeight(trait="mid_bass", pad_id=1, weight=0.80),
        TraitPadWeight(trait="mid_bass", pad_id=2, weight=0.35),
        TraitPadWeight(trait="mid_bass", pad_id=3, weight=0.65),
        TraitPadWeight(trait="mid_bass", pad_id=4, weight=0.40),
    ),
    transition_curve="progressive",
    source_summary="Built-in scene · snappy, swing, mid-bass",
)

# ---------------------------------------------------------------------------
# peak_time — high-energy, full-spectrum
# ---------------------------------------------------------------------------

_PEAK_TIME = ProfileModel(
    profile_id=_scene_id("peak_time"),
    name="peak_time",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="energy", value=0.90),
        StyleTrait(name="full_spectrum", value=0.85),
        StyleTrait(name="drive", value=0.80),
    ),
    pad_mappings=(
        TraitPadWeight(trait="energy", pad_id=1, weight=0.85),
        TraitPadWeight(trait="energy", pad_id=2, weight=0.85),
        TraitPadWeight(trait="energy", pad_id=3, weight=0.80),
        TraitPadWeight(trait="energy", pad_id=4, weight=0.75),
        TraitPadWeight(trait="full_spectrum", pad_id=1, weight=0.80),
        TraitPadWeight(trait="full_spectrum", pad_id=2, weight=0.80),
        TraitPadWeight(trait="full_spectrum", pad_id=3, weight=0.85),
        TraitPadWeight(trait="full_spectrum", pad_id=4, weight=0.80),
        TraitPadWeight(trait="drive", pad_id=1, weight=0.75),
        TraitPadWeight(trait="drive", pad_id=2, weight=0.70),
        TraitPadWeight(trait="drive", pad_id=3, weight=0.75),
        TraitPadWeight(trait="drive", pad_id=4, weight=0.80),
    ),
    transition_curve="linear",
    source_summary="Built-in scene · high-energy, full-spectrum",
)

# ---------------------------------------------------------------------------
# rolling — continuous low-end, sub-bass
# ---------------------------------------------------------------------------

_ROLLING = ProfileModel(
    profile_id=_scene_id("rolling"),
    name="rolling",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="rolling_low_end", value=0.90),
        StyleTrait(name="sub_bass", value=0.85),
        StyleTrait(name="continuous", value=0.80),
    ),
    pad_mappings=(
        TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.90),
        TraitPadWeight(trait="rolling_low_end", pad_id=2, weight=0.30),
        TraitPadWeight(trait="rolling_low_end", pad_id=3, weight=0.55),
        TraitPadWeight(trait="rolling_low_end", pad_id=4, weight=0.45),
        TraitPadWeight(trait="sub_bass", pad_id=1, weight=0.85),
        TraitPadWeight(trait="sub_bass", pad_id=2, weight=0.20),
        TraitPadWeight(trait="sub_bass", pad_id=3, weight=0.40),
        TraitPadWeight(trait="sub_bass", pad_id=4, weight=0.35),
        TraitPadWeight(trait="continuous", pad_id=1, weight=0.75),
        TraitPadWeight(trait="continuous", pad_id=2, weight=0.45),
        TraitPadWeight(trait="continuous", pad_id=3, weight=0.70),
        TraitPadWeight(trait="continuous", pad_id=4, weight=0.65),
    ),
    transition_curve="progressive",
    source_summary="Built-in scene · continuous low-end, sub-bass",
)

# ---------------------------------------------------------------------------
# birmingham — acidic, hard, fast-attack
# ---------------------------------------------------------------------------

_BIRMINGHAM = ProfileModel(
    profile_id=_scene_id("birmingham"),
    name="birmingham",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="acid", value=0.80),
        StyleTrait(name="hard_attack", value=0.85),
        StyleTrait(name="fast_decay", value=0.75),
    ),
    pad_mappings=(
        TraitPadWeight(trait="acid", pad_id=1, weight=0.45),
        TraitPadWeight(trait="acid", pad_id=2, weight=0.55),
        TraitPadWeight(trait="acid", pad_id=3, weight=0.85),
        TraitPadWeight(trait="acid", pad_id=4, weight=0.70),
        TraitPadWeight(trait="hard_attack", pad_id=1, weight=0.80),
        TraitPadWeight(trait="hard_attack", pad_id=2, weight=0.85),
        TraitPadWeight(trait="hard_attack", pad_id=3, weight=0.70),
        TraitPadWeight(trait="hard_attack", pad_id=4, weight=0.60),
        TraitPadWeight(trait="fast_decay", pad_id=1, weight=0.55),
        TraitPadWeight(trait="fast_decay", pad_id=2, weight=0.80),
        TraitPadWeight(trait="fast_decay", pad_id=3, weight=0.70),
        TraitPadWeight(trait="fast_decay", pad_id=4, weight=0.65),
    ),
    transition_curve="linear",
    source_summary="Built-in scene · acidic, hard, fast-attack",
)

# ---------------------------------------------------------------------------
# drone — atmospheric, slow, evolving
# ---------------------------------------------------------------------------

_DRONE = ProfileModel(
    profile_id=_scene_id("drone"),
    name="drone",
    kind="scene",
    model_version=_MODEL_VERSION,
    traits=(
        StyleTrait(name="atmospheric", value=0.85),
        StyleTrait(name="slow_evolution", value=0.80),
        StyleTrait(name="long_tail", value=0.75),
    ),
    pad_mappings=(
        TraitPadWeight(trait="atmospheric", pad_id=1, weight=0.55),
        TraitPadWeight(trait="atmospheric", pad_id=2, weight=0.45),
        TraitPadWeight(trait="atmospheric", pad_id=3, weight=0.85),
        TraitPadWeight(trait="atmospheric", pad_id=4, weight=0.80),
        TraitPadWeight(trait="slow_evolution", pad_id=1, weight=0.50),
        TraitPadWeight(trait="slow_evolution", pad_id=2, weight=0.40),
        TraitPadWeight(trait="slow_evolution", pad_id=3, weight=0.80),
        TraitPadWeight(trait="slow_evolution", pad_id=4, weight=0.75),
        TraitPadWeight(trait="long_tail", pad_id=1, weight=0.60),
        TraitPadWeight(trait="long_tail", pad_id=2, weight=0.55),
        TraitPadWeight(trait="long_tail", pad_id=3, weight=0.75),
        TraitPadWeight(trait="long_tail", pad_id=4, weight=0.80),
    ),
    transition_curve="progressive_w_release",
    source_summary="Built-in scene · atmospheric, slow, evolving",
)


BUILTIN_SCENES: Final[tuple[ProfileModel, ...]] = (
    _BIRMINGHAM,
    _DRONE,
    _GARAGE,
    _HYPNOTIC,
    _INDUSTRIAL,
    _PEAK_TIME,
    _ROLLING,
)
"""All seven built-in scenes, pre-sorted by ``name``."""


__all__ = ["BUILTIN_SCENES"]
