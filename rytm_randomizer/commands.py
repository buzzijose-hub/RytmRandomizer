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

FORBIDDEN_ACTIONS = {
    "master_volume": {
        "label": "Master volume",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "track_volume": {
        "label": "Track volume",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "clock": {
        "label": "Clock",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "transport": {
        "label": "Transport",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "pattern_change": {
        "label": "Pattern change",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "program_change": {
        "label": "Program change",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "project_change": {
        "label": "Project change",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "kit_save_clear": {
        "label": "Kit save/clear",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "system_commands": {
        "label": "System commands",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
    "unvalidated_sysex_writes": {
        "label": "Unvalidated SysEx writes",
        "status": "forbidden_by_default",
        "sends_midi": False,
        "source": "CONTROLLED_MUTATION_ROADMAP",
    },
}

GROUP_COMMANDS = {
    "O": {
        "type": "load",
        "scope": "four_pad_group",
        "label": "load full 4-pad group anchors",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "X": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "balanced four-lane mutate full 4-pad group",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "D": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "deeper four-lane mutation, Pads 2-4 pushed harder",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "I": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "intense / controlled chaos four-lane mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "4": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "harder / wild four-lane mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "Y": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "lane-aware SRC/morph mutation on all 4 group pads",
        "command_family": "lane_aware_page",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "V": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "lane-aware filter mutation on all 4 group pads",
        "command_family": "lane_aware_page",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "N": {
        "type": "mutation",
        "scope": "four_pad_group",
        "label": "lane-aware grit mutation on all 4 group pads",
        "command_family": "lane_aware_page",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "Z": {
        "type": "anchor_return",
        "scope": "four_pad_group",
        "label": "return all 4 group pads to anchors",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

COMMANDS = {
    **{command: {"type": "scene"} for command in SCENE_COMMANDS},
    **MENU_COMMANDS,
    **GROUP_COMMANDS,
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
