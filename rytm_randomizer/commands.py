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

MENU_COMMANDS = {
    "BD": {
        "type": "menu",
        "sends_midi": False,
        "label": "show BD engine tools",
    },
    "FM": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD FM menu/status",
    },
    "PD": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD Plastic menu/status",
    },
    "SM": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD Silky menu/status",
    },
    "P2M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 2 snare / secondary percussion menu",
    },
    "J": {
        "type": "print",
        "sends_midi": False,
        "label": "show 4-pad group layout",
    },
    "GM": {
        "type": "menu",
        "sends_midi": False,
        "label": "show global 4-pad mutation tools",
    },
    "SCN": {
        "type": "menu",
        "sends_midi": False,
        "label": "show scene / preset tools",
    },
    "PR": {
        "type": "print",
        "sends_midi": False,
        "label": "show selected isolated pad",
    },
    "SR": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show Pad 3 SY Raw discovery menu/status",
    },
    "P3M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 3 SY Raw bass / synth-percussion menu",
    },
    "P4M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 4 BD Acoustic body / accent menu",
    },
    "H": {
        "type": "print",
        "sends_midi": False,
        "label": "show current anchor",
    },
    "R": {
        "type": "print",
        "sends_midi": False,
        "label": "print current script state",
    },
}

COMMANDS = {
    **{command: {"type": "scene"} for command in SCENE_COMMANDS},
    **MENU_COMMANDS,
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
