"""Command registry for scaffold-level guardrails."""

from .constants import GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
from .scenes import SCENE_COMMANDS

COMMANDS = {
    **{command: {"type": "scene"} for command in SCENE_COMMANDS},
    **{
        command: {"type": "guarded_depth"}
        for command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
    },
}


def is_guarded_main_prompt_depth(command):
    """Return True when a bare main prompt depth command must send no MIDI."""
    return command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
