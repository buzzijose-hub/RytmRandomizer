"""Scene command metadata for the modular scaffold.

This registry mirrors the V1.34 scene command names, descriptions, and actions
as data only. It does not execute scenes or send MIDI.

The name / description / action of every scene is derived from the shared data
layer (:data:`rytm_randomizer.data.SCENE_PRESETS`) so there is exactly one copy
of those values and the package can never drift from the monolith. The
scaffold-only metadata fields (``scope``, ``executable``,
``v134_reference_command``, ``scaffold_only``) are added here because they are
package-scaffold concerns that do not exist in the monolith.
"""

from __future__ import annotations

from types import MappingProxyType

from .data import SCENE_PRESETS

# Scaffold-only metadata attached to every scene command. These flags describe
# the modular scaffold's relationship to the V1.34 monolith; they are not part
# of the canonical scene data.
_SCAFFOLD_METADATA = {
    "scope": "four_pad_group",
    "executable": False,
    "v134_reference_command": True,
    "scaffold_only": True,
}


def _build_scene_commands() -> dict[str, dict[str, object]]:
    """Derive SCENE_COMMANDS from the shared SCENE_PRESETS data.

    Monolith preset keys are lower-case (``s0``); the scaffold registry uses
    upper-case command keys (``S0``). Order is preserved.
    """

    commands: dict[str, dict[str, object]] = {}
    for preset_key, preset in SCENE_PRESETS.items():
        command_key = preset_key.upper()
        commands[command_key] = {
            "name": preset["name"],
            "description": preset["description"],
            "action": preset["action"],
            **_SCAFFOLD_METADATA,
        }
    return commands


SCENE_COMMANDS = _build_scene_commands()

__all__ = ["SCENE_COMMANDS"]
