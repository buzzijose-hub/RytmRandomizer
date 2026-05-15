"""Scene / preset orchestration -- extracted from the V1.34 monolith
(Wave 4 / WS-N).

The V1.34 scene layer is a thin set of performance shortcuts built *on top of*
the validated four-lane global mutation layer. It introduces no new parameter
ranges: every scene either loads/returns the four-pad anchors or runs one of the
intensity plans through :class:`rytm_randomizer.group_runner.GroupRunner`.

This module owns the monolith's ``show_scene_tools`` and ``run_scene`` plus the
14 scene definitions S0-S5 (with A/B variants). The scene *data* is the single
source of truth :data:`rytm_randomizer.data.SCENE_PRESETS`; this module only
orchestrates it.

:class:`SceneRunner` COMPOSES a :class:`GroupRunner` -- the scene actions
delegate straight into ``load_group_anchors`` / ``return_group_to_anchors`` /
``ensure_group_anchors_loaded`` / ``mutate_group_intensity``. The MIDI ``out``
sender and the other runtime dependencies live on the wrapped ``GroupRunner``;
nothing here opens ports or imports ``mido``. ``import
rytm_randomizer.scene_runner`` is silent and inert.

Behavior is byte-identical to the monolith: ``show_scene_tools`` and
``run_scene`` mirror each monolith function's control flow, printed output, MIDI
message order and ``current_scene_name`` bookkeeping exactly.
"""

from __future__ import annotations

from .data import SCENE_PRESETS
from .group_runner import GroupRunner

__all__ = ["SceneRunner"]

# The monolith's cold-start ``current_scene_name`` global.
DEFAULT_SCENE_NAME = "None"


class SceneRunner:
    """Stateful scene / preset orchestrator wrapping a :class:`GroupRunner`.

    The wrapped ``GroupRunner`` carries the four-pad runtime state and the
    injected ``out`` / ``rng`` / ``sleep`` / ``input`` dependencies, so the
    scene layer stays a pure shortcut over the validated global mutation layer
    -- exactly as the monolith built it.
    """

    def __init__(
        self,
        group_runner: GroupRunner,
        *,
        current_scene_name: str = DEFAULT_SCENE_NAME,
    ) -> None:
        self.group = group_runner
        self.current_scene_name = current_scene_name

    def show_scene_tools(self) -> None:
        """Mirror the monolith ``show_scene_tools`` menu/status view.

        This is the ``SCN`` command: it only prints. It sends no MIDI and does
        not load anchors -- a key V1.34 guardrail.
        """

        print("\nScene / Preset Tools - V1.34")
        print(
            "  These are performance shortcuts built from the validated "
            "four-lane system."
        )
        print(
            "  They do not introduce new parameter ranges; they call the "
            "existing safe global layer."
        )
        print("\nScene commands:")
        print("  SCN = show this scene / preset menu")
        print("  S0  = Home / Clean anchors")
        print("  S1  = Rolling scene")
        print("  S1A = Rolling Light")
        print("  S1B = Rolling Push")
        print("  S2  = Deeper scene")
        print("  S2A = Deeper Groove")
        print("  S2B = Deeper Pressure")
        print("  S3  = Intense scene")
        print("  S3A = Intense Motion")
        print("  S3B = Intense Grit")
        print("  S4  = Wild scene")
        print("  S4A = Wild Controlled")
        print("  S4B = Wild Maximum")
        print("  S5  = Back to Clean anchors")
        print("\nScene behavior:")
        print(
            "  SCN only displays this menu/status; it does not send MIDI or "
            "load anchors."
        )
        print(
            "  S0 loads the full four-pad anchor state if needed, or returns "
            "all pads to anchors if already loaded."
        )
        print(
            "  S1-S4 and S1A-S4B now auto-load the four-pad anchors first if "
            "needed, then run the scene."
        )
        print("  S5 returns all four pads to the validated anchors.")
        print("\nCurrent scene:")
        print(f"  {self.current_scene_name}")
        if len(self.group.group_current_states) >= 4:
            print("  Four-pad state: loaded")
        else:
            print(
                "  Four-pad state: not loaded yet. This is normal before O, "
                "S0, or the first scene command."
            )

    def run_scene(self, scene_key: str) -> None:
        """Mirror the monolith ``run_scene``: dispatch one scene command.

        ``home`` / ``clean`` actions load or return the four-pad anchors; every
        other action auto-loads anchors then runs the matching intensity plan
        through the wrapped :class:`GroupRunner`. ``current_scene_name`` is
        updated to the scene's name on success.
        """

        if scene_key not in SCENE_PRESETS:
            print(f"\nUnknown scene command: {scene_key.upper()}")
            self.show_scene_tools()
            return

        scene = SCENE_PRESETS[scene_key]
        action = scene["action"]

        print(f"\nScene / Preset - V1.34: {scene['name']}")
        print(f"  {scene['description']}")

        if action == "home":
            if len(self.group.group_current_states) < 4:
                print(
                    "  Four-pad state not loaded yet. Loading validated "
                    "anchors now."
                )
                self.group.load_group_anchors()
            else:
                print("  Returning all four pads to validated anchors.")
                self.group.return_group_to_anchors()
            self.current_scene_name = scene["name"]
            print(f"\nScene active: {self.current_scene_name}")
            return

        if action == "clean":
            if len(self.group.group_current_states) < 4:
                print(
                    "  Four-pad state not loaded yet. Loading validated "
                    "anchors now."
                )
                self.group.load_group_anchors()
            else:
                print("  Returning all four pads to validated anchors.")
                self.group.return_group_to_anchors()
            self.current_scene_name = scene["name"]
            print(f"\nScene active: {self.current_scene_name}")
            return

        self.group.ensure_group_anchors_loaded(f"Scene {scene_key.upper()}")

        print(
            "  Applying scene through the validated global four-lane mutation "
            "layer."
        )
        self.group.mutate_group_intensity(action)
        self.current_scene_name = scene["name"]
        print(f"\nScene active: {self.current_scene_name}")
