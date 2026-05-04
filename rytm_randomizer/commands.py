"""Command registry for scaffold-level guardrails."""

from .constants import GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
from .scenes import SCENE_COMMANDS

MAIN_PROMPT_DEPTH_GUARDRAIL = {
    "commands": GUARDED_MAIN_PROMPT_DEPTH_COMMANDS,
    "sends_midi": False,
    "message": "Depth number entered at the main Command prompt. No MIDI was sent.",
    "depth_prompt_context": (
        "Use a command that asks for depth before entering 1, 2, or 3."
    ),
}

COMMANDS = {
    **{command: {"type": "scene"} for command in SCENE_COMMANDS},
    **{
        command: {
            "type": "guarded_depth",
            "sends_midi": MAIN_PROMPT_DEPTH_GUARDRAIL["sends_midi"],
        }
        for command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
    },
}


def is_guarded_main_prompt_depth(command):
    """Return True when a bare main prompt depth command must send no MIDI."""
    return command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
