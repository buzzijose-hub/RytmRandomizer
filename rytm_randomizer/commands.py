"""Command registry for scaffold-level guardrails."""

from .constants import GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
from .scenes import SCENE_COMMANDS

MAIN_PROMPT_DEPTH_GUARDRAIL = {
    "commands": GUARDED_MAIN_PROMPT_DEPTH_COMMANDS,
    "sends_midi": False,
    "message": "Depth number entered at the main Command prompt. No MIDI was sent.",
    "depth_prompt_context": ("Use a command that asks for depth before entering 1, 2, or 3."),
}

MENU_COMMANDS = {
    "BD": {
        "type": "menu",
        "sends_midi": False,
        "label": "show BD engine tools",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "FM": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD FM menu/status",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PD": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD Plastic menu/status",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "SM": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show BD Silky menu/status",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "P2M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 2 snare / secondary percussion menu",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "J": {
        "type": "print",
        "sends_midi": False,
        "label": "show 4-pad group layout",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "GM": {
        "type": "menu",
        "sends_midi": False,
        "label": "show global 4-pad mutation tools",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "SCN": {
        "type": "menu",
        "sends_midi": False,
        "label": "show scene / preset tools",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PR": {
        "type": "print",
        "sends_midi": False,
        "label": "show selected isolated pad",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "SR": {
        "type": "menu/status",
        "sends_midi": False,
        "label": "show Pad 3 SY Raw discovery menu/status",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "P3M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 3 SY Raw bass / synth-percussion menu",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "P4M": {
        "type": "menu",
        "sends_midi": False,
        "label": "show Pad 4 BD Acoustic body / accent menu",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "H": {
        "type": "print",
        "sends_midi": False,
        "label": "show current anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "R": {
        "type": "print",
        "sends_midi": False,
        "label": "print current script state",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

UTILITY_COMMANDS = {
    "T": {
        "type": "selection",
        "scope": "target_pad_channel",
        "sends_midi": False,
        "label": "select target pad/channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "C": {
        "type": "selection",
        "scope": "midi_channel",
        "sends_midi": False,
        "label": "change MIDI channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "Q": {
        "type": "session",
        "scope": "operator_session",
        "sends_midi": False,
        "label": "quit",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

STATE_UTILITY_COMMANDS = {
    "B": {
        "type": "anchor_state",
        "scope": "current_anchor",
        "sends_midi": False,
        "label": "back to current anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "E": {
        "type": "anchor_state",
        "scope": "current_state_anchor",
        "sends_midi": False,
        "label": "commit current state as new anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "W": {
        "type": "exploration",
        "scope": "waveform",
        "sends_midi": False,
        "label": "waveform exploration only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "U": {
        "type": "state_history",
        "scope": "script_generated_state",
        "sends_midi": False,
        "label": "undo previous script-generated state",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

ISOLATED_PAD_UTILITY_COMMANDS = {
    "L": {
        "type": "selection",
        "scope": "isolated_pad_target",
        "sends_midi": False,
        "label": "select isolated single-pad mutation target, default Pad 3",
        "default_pad": 3,
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PZ": {
        "type": "anchor_return",
        "scope": "selected_isolated_pad",
        "sends_midi": False,
        "label": "return selected isolated pad to anchor only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

ISOLATED_PAD_MUTATION_COMMANDS = {
    "PM": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "full",
        "uses_group_default_zone_depth": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad only using its group default zone/depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PS": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "src",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad SRC only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PF": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "filter",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Filter only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PA": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "amp",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Amp only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PL": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "lfo",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad LFO only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PO": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "morph",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Morph only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PB": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "body",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Body only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PG": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "grit",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Grit only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

PROFILE_WORKFLOW_COMMANDS = {
    "P": {
        "type": "selection",
        "scope": "profile_machine",
        "command_family": "profile_workflow",
        "selects_profile": True,
        "machine_change_intent": True,
        "sends_midi": False,
        "label": "select/switch profile and change Rytm machine",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M": {
        "type": "anchor_load",
        "scope": "selected_profile",
        "command_family": "profile_workflow",
        "uses_selected_profile": True,
        "anchor_load_intent": True,
        "sends_midi": False,
        "label": "load selected profile anchor",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS = {
    "M1": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "micro",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full micro mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M2": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "groove",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full groove mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "M3": {
        "type": "mutation",
        "scope": "selected_profile",
        "command_family": "legacy_single_profile_mutation",
        "mutation_area": "full",
        "mutation_depth": "strong",
        "uses_selected_profile": True,
        "sends_midi": False,
        "label": "Legacy single-profile full strong mutation",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}

CURRENT_PROFILE_PAGE_MUTATION_COMMANDS = {
    "S": {
        "type": "mutation",
        "scope": "current_profile",
        "command_family": "generic_current_profile_page_mutation",
        "mutation_area": "src",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "SRC-only mutation, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "F": {
        "type": "mutation",
        "scope": "current_profile",
        "command_family": "generic_current_profile_page_mutation",
        "mutation_area": "filter",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "Filter-only mutation, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "A": {
        "type": "mutation",
        "scope": "current_profile",
        "command_family": "generic_current_profile_page_mutation",
        "mutation_area": "amp",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "Amp-only mutation, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "G": {
        "type": "mutation",
        "scope": "current_profile",
        "command_family": "generic_current_profile_page_mutation",
        "mutation_area": "grit",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "Grit-only mutation, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "K": {
        "type": "mutation",
        "scope": "current_profile",
        "command_family": "generic_current_profile_page_mutation",
        "mutation_area": "kick_body",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "Kick body mutation, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
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

# Scaffold-only metadata shared by every entry in the per-pad command dicts.
# The five fields below were repeated verbatim on every PAD{1..4}_COMMANDS
# entry (~210 redundant fields total). Mirrors the pattern used by
# ``rytm_randomizer.scenes._SCAFFOLD_METADATA`` for the scene registry: each
# command entry now only carries its differentiating fields (``type`` and
# ``label``) plus a ``**_PADN_SCAFFOLD`` spread.
_PAD1_SCAFFOLD = {
    "scope": "pad_1",
    "pad": 1,
    "executable": False,
    "v134_reference_command": True,
    "scaffold_only": True,
}
_PAD2_SCAFFOLD = {
    "scope": "pad_2",
    "pad": 2,
    "executable": False,
    "v134_reference_command": True,
    "scaffold_only": True,
}
_PAD3_SCAFFOLD = {
    "scope": "pad_3",
    "pad": 3,
    "executable": False,
    "v134_reference_command": True,
    "scaffold_only": True,
}
_PAD4_SCAFFOLD = {
    "scope": "pad_4",
    "pad": 4,
    "executable": False,
    "v134_reference_command": True,
    "scaffold_only": True,
}

PAD1_COMMANDS = {
    "BR": {
        "type": "rotation",
        "label": "rotate Pad 1 to the next profiled BD engine",
        **_PAD1_SCAFFOLD,
    },
    "BM": {
        "type": "mutation",
        "label": "safely mutate the currently loaded Pad 1 BD engine",
        **_PAD1_SCAFFOLD,
    },
    "BH": {
        "type": "load",
        "label": "load Pad 1 BD Hard anchor, primary default",
        **_PAD1_SCAFFOLD,
    },
    "BS": {
        "type": "load",
        "label": "load Pad 1 BD Sharp anchor",
        **_PAD1_SCAFFOLD,
    },
    "BC": {
        "type": "load",
        "label": "load Pad 1 BD Classic anchor",
        **_PAD1_SCAFFOLD,
    },
    "BA": {
        "type": "load",
        "label": "load Pad 1 BD Acoustic anchor",
        **_PAD1_SCAFFOLD,
    },
    "BF": {
        "type": "load",
        "label": "load Pad 1 BD FM profiled anchor",
        **_PAD1_SCAFFOLD,
    },
    "FT": {
        "type": "mutation",
        "label": "BD FM tone/FM discovery",
        **_PAD1_SCAFFOLD,
    },
    "FK": {
        "type": "mutation",
        "label": "BD FM kick/body discovery",
        **_PAD1_SCAFFOLD,
    },
    "FG": {
        "type": "mutation",
        "label": "BD FM grit discovery",
        **_PAD1_SCAFFOLD,
    },
    "FZ": {
        "type": "anchor_return",
        "label": "return Pad 1 BD FM to anchor",
        **_PAD1_SCAFFOLD,
    },
    "BP": {
        "type": "load",
        "label": "load Pad 1 BD Plastic profiled anchor",
        **_PAD1_SCAFFOLD,
    },
    "PT": {
        "type": "mutation",
        "label": "BD Plastic tone/modulation discovery",
        **_PAD1_SCAFFOLD,
    },
    "PK": {
        "type": "mutation",
        "label": "BD Plastic kick/body discovery",
        **_PAD1_SCAFFOLD,
    },
    "PX": {
        "type": "mutation",
        "label": "BD Plastic rubber/experimental discovery",
        **_PAD1_SCAFFOLD,
    },
    "PBH": {
        "type": "anchor_return",
        "label": "return Pad 1 BD Plastic to anchor",
        **_PAD1_SCAFFOLD,
    },
    "BI": {
        "type": "load",
        "label": "load Pad 1 BD Silky profiled anchor",
        **_PAD1_SCAFFOLD,
    },
    "ST": {
        "type": "mutation",
        "label": "BD Silky smooth tone discovery",
        **_PAD1_SCAFFOLD,
    },
    "SK": {
        "type": "mutation",
        "label": "BD Silky kick/body discovery",
        **_PAD1_SCAFFOLD,
    },
    "SC": {
        "type": "mutation",
        "label": "BD Silky click/dust discovery",
        **_PAD1_SCAFFOLD,
    },
    "SBH": {
        "type": "anchor_return",
        "label": "return Pad 1 BD Silky to anchor",
        **_PAD1_SCAFFOLD,
    },
}

PAD2_COMMANDS = {
    "P2B": {
        "type": "load",
        "label": "load Pad 2 BD Classic rolling low percussion / home",
        **_PAD2_SCAFFOLD,
    },
    "P2H": {
        "type": "load",
        "label": "load Pad 2 SD Hard pressure snare",
        **_PAD2_SCAFFOLD,
    },
    "P2C": {
        "type": "load",
        "label": "load Pad 2 SD Classic rolling snare",
        **_PAD2_SCAFFOLD,
    },
    "P2F": {
        "type": "load",
        "label": "load Pad 2 SD FM metallic snare",
        **_PAD2_SCAFFOLD,
    },
    "P2T": {
        "type": "mutation",
        "label": "Pad 2 tone / snap discovery",
        **_PAD2_SCAFFOLD,
    },
    "P2P": {
        "type": "mutation",
        "label": "Pad 2 pressure / body discovery",
        **_PAD2_SCAFFOLD,
    },
    "P2G": {
        "type": "mutation",
        "label": "Pad 2 grit / noise discovery",
        **_PAD2_SCAFFOLD,
    },
    "P2R": {
        "type": "rotation",
        "label": "rotate Pad 2 through profiled secondary-lane engines",
        **_PAD2_SCAFFOLD,
    },
    "P2X": {
        "type": "mutation",
        "label": "safely mutate the currently loaded Pad 2 profile",
        **_PAD2_SCAFFOLD,
    },
    "P2Z": {
        "type": "anchor_return",
        "label": "return current Pad 2 profile to anchor",
        **_PAD2_SCAFFOLD,
    },
}

PAD3_COMMANDS = {
    "SW": {
        "type": "mutation",
        "label": "Pad 3 SY Raw Wave + Balance discovery",
        **_PAD3_SCAFFOLD,
    },
    "SL": {
        "type": "load",
        "label": "Pad 3 SY Raw LP1 bassline mode",
        **_PAD3_SCAFFOLD,
    },
    "SB": {
        "type": "load",
        "label": "Pad 3 SY Raw Bandpass mid-bass mode",
        **_PAD3_SCAFFOLD,
    },
    "SX": {
        "type": "load",
        "label": "Pad 3 SY Raw sci-fi motion accent mode",
        **_PAD3_SCAFFOLD,
    },
    "SA": {
        "type": "anchor_return",
        "label": "return Pad 3 SY Raw to anchor",
        **_PAD3_SCAFFOLD,
    },
    "P3R": {
        "type": "rotation",
        "label": "rotate Pad 3 through SY Raw behavior modes",
        **_PAD3_SCAFFOLD,
    },
    "P3X": {
        "type": "mutation",
        "label": "safely mutate the currently loaded Pad 3 mode",
        **_PAD3_SCAFFOLD,
    },
    "P3A": {
        "type": "anchor_return",
        "label": "return Pad 3 to SY Raw Mid Bass anchor / home",
        **_PAD3_SCAFFOLD,
    },
}

PAD4_COMMANDS = {
    "P4R": {
        "type": "rotation",
        "label": "rotate Pad 4 through BD Acoustic behavior modes",
        **_PAD4_SCAFFOLD,
    },
    "P4X": {
        "type": "mutation",
        "label": "safely mutate the currently loaded Pad 4 mode",
        **_PAD4_SCAFFOLD,
    },
    "P4A": {
        "type": "anchor_return",
        "label": "return Pad 4 to BD Acoustic body/accent anchor / home",
        **_PAD4_SCAFFOLD,
    },
}

COMMANDS = {
    **{
        command: {
            **metadata,
            "type": "scene",
        }
        for command, metadata in SCENE_COMMANDS.items()
    },
    **MENU_COMMANDS,
    **UTILITY_COMMANDS,
    **STATE_UTILITY_COMMANDS,
    **ISOLATED_PAD_UTILITY_COMMANDS,
    **ISOLATED_PAD_MUTATION_COMMANDS,
    **PROFILE_WORKFLOW_COMMANDS,
    **LEGACY_SINGLE_PROFILE_MUTATION_COMMANDS,
    **CURRENT_PROFILE_PAGE_MUTATION_COMMANDS,
    **GROUP_COMMANDS,
    **PAD1_COMMANDS,
    **PAD2_COMMANDS,
    **PAD3_COMMANDS,
    **PAD4_COMMANDS,
    **{
        command: {
            "type": "guarded_depth",
            "sends_midi": MAIN_PROMPT_DEPTH_GUARDRAIL["sends_midi"],
            "label": f"guarded depth input {command}, requires lane/mode prefix",
            "executable": False,
            "v134_reference_command": True,
            "scaffold_only": True,
        }
        for command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
    },
}


def is_guarded_main_prompt_depth(command):
    """Return True when a bare main prompt depth command must send no MIDI."""
    return command in GUARDED_MAIN_PROMPT_DEPTH_COMMANDS
