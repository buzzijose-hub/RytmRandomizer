"""Current scene / preset name state.

Mirrors the monolith global ``current_scene_name`` -- a plain string with the
default ``"None"``. ``run_scene`` reassigns it to ``scene["name"]`` for every
scene action (home, clean, and the intensity-plan scenes).

Nothing here opens ports, sends MIDI, or touches hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_SCENE_NAME = "None"


@dataclass(frozen=True)
class SceneState:
    """Immutable current-scene-name state."""

    current_scene_name: str = DEFAULT_SCENE_NAME


def initial_scene_state() -> SceneState:
    """Return the monolith's cold-start scene state (``current_scene_name = "None"``)."""

    return SceneState()


def set_scene_name(state: SceneState, scene_name: str) -> SceneState:
    """Apply the monolith ``run_scene`` transition.

    Replaces ``current_scene_name`` with ``scene_name``.
    """

    return SceneState(current_scene_name=str(scene_name))


__all__ = [
    "DEFAULT_SCENE_NAME",
    "SceneState",
    "initial_scene_state",
    "set_scene_name",
]
