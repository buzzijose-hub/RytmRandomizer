from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import (
    COMMANDS,
    FORBIDDEN_ACTIONS,
    GROUP_COMMANDS,
    MAIN_PROMPT_DEPTH_GUARDRAIL,
    MENU_COMMANDS,
    PAD1_COMMANDS,
    PAD2_COMMANDS,
    PAD3_COMMANDS,
    PAD4_COMMANDS,
    UTILITY_COMMANDS,
    is_guarded_main_prompt_depth,
)
from rytm_randomizer.constants import (
    DEFAULT_MIDI_CHANNEL,
    DEFAULT_TARGET_PAD,
    MACHINE_CC,
    OUT_OF_SCOPE_PAD_GUARDRAIL,
    OUT_OF_SCOPE_PADS,
    PAD1_DEFAULT_HOME,
    PAD_SELECTION_LABELS,
    PAD_TO_MIDI_CHANNEL,
    SUPPORTED_PADS,
)
from rytm_randomizer.profiles import (
    GROUP_LAYOUT,
    GROUP_PROFILE_METADATA,
    PAD_1_DEFAULT_PROFILE,
    PAD_3_SY_RAW_CC_MAP,
    PAD_PROFILES,
)
from rytm_randomizer.scenes import SCENE_COMMANDS


FORBIDDEN_EXECUTION_FIELDS = {"handler", "callable", "execute", "function", "callback"}


def assert_no_execution_fields(metadata):
    assert FORBIDDEN_EXECUTION_FIELDS.isdisjoint(metadata)


def assert_sends_no_midi(metadata):
    assert metadata["sends_midi"] is False


def assert_protocol_command_metadata(metadata):
    assert metadata["executable"] is False
    assert metadata["v134_reference_command"] is True
    assert metadata["scaffold_only"] is True
    assert_no_execution_fields(metadata)


def assert_no_out_of_scope_pad_keys(mapping):
    assert not any(pad in mapping for pad in OUT_OF_SCOPE_PADS)


def assert_pad_command_metadata_only(metadata, pad):
    assert metadata["pad"] == pad
    assert metadata["scope"] == f"pad_{pad}"
    assert_protocol_command_metadata(metadata)
    assert "Pad 5" not in metadata["label"]
    assert "Pad 6" not in metadata["label"]
    assert "Pad 7" not in metadata["label"]
    assert "Pad 8" not in metadata["label"]
    assert "Pad 9" not in metadata["label"]
    assert "Pad 10" not in metadata["label"]
    assert "Pad 11" not in metadata["label"]
    assert "Pad 12" not in metadata["label"]


def test_pads_1_to_4_only_are_supported():
    assert SUPPORTED_PADS == (1, 2, 3, 4)
    assert OUT_OF_SCOPE_PADS == (5, 6, 7, 8, 9, 10, 11, 12)


def test_pads_5_to_12_are_explicitly_out_of_scope():
    assert OUT_OF_SCOPE_PAD_GUARDRAIL["pads"] == OUT_OF_SCOPE_PADS
    assert OUT_OF_SCOPE_PAD_GUARDRAIL["status"] == "out_of_scope"
    assert OUT_OF_SCOPE_PAD_GUARDRAIL["allowed_in_scaffold"] is False
    assert "Pads 5-12 expansion" in OUT_OF_SCOPE_PAD_GUARDRAIL["reason"]
    assert set(OUT_OF_SCOPE_PAD_GUARDRAIL["pads"]).isdisjoint(SUPPORTED_PADS)


def test_pads_5_to_12_are_absent_from_scaffold_surfaces():
    assert_no_out_of_scope_pad_keys(PAD_TO_MIDI_CHANNEL)
    assert_no_out_of_scope_pad_keys(PAD_SELECTION_LABELS)
    assert_no_out_of_scope_pad_keys(GROUP_LAYOUT)
    assert not any(
        profile["group_pad"] in OUT_OF_SCOPE_PADS
        for profile in GROUP_PROFILE_METADATA.values()
    )


def test_default_target_pad_and_channel_match_v134():
    assert DEFAULT_TARGET_PAD == 1
    assert DEFAULT_MIDI_CHANNEL == 0


def test_existing_v134_constants_are_preserved():
    assert MACHINE_CC == 15
    assert PAD1_DEFAULT_HOME == "BD Hard"


def test_pad_to_midi_channel_uses_zero_indexed_values_for_pads_1_to_4():
    assert PAD_TO_MIDI_CHANNEL == {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
    }
    assert_no_out_of_scope_pad_keys(PAD_TO_MIDI_CHANNEL)


def test_pad_selection_labels_match_v134_for_pads_1_to_4_only():
    assert PAD_SELECTION_LABELS == {
        1: "Pad 1 / BD slot",
        2: "Pad 2 / SD slot, flexible BD/SD/SY/UT pool",
        3: "Pad 3 / RS slot, flexible BD/SD/RS/CP/SY/UT pool",
        4: "Pad 4 / CP slot, flexible BD/SD/RS/CP/SY/UT pool",
    }
    assert_no_out_of_scope_pad_keys(PAD_SELECTION_LABELS)


def test_pad_1_default_home_is_bd_hard():
    assert PAD_1_DEFAULT_PROFILE["pad"] == 1
    assert PAD_1_DEFAULT_PROFILE["name"] == PAD1_DEFAULT_HOME
    assert PAD_1_DEFAULT_PROFILE["role"] == "default/home"


def test_pad_3_sy_raw_cc_mapping_is_preserved():
    assert PAD_3_SY_RAW_CC_MAP["SRC Noise Level"] == 19
    assert PAD_3_SY_RAW_CC_MAP["SRC Balance"] == 23


def test_pad_profiles_include_only_known_scaffold_profiles():
    assert set(PAD_PROFILES) == {1, 3}
    assert_no_out_of_scope_pad_keys(PAD_PROFILES)
    assert PAD_PROFILES[1] is PAD_1_DEFAULT_PROFILE
    assert PAD_PROFILES[3]["pad"] == 3
    assert PAD_PROFILES[3]["name"] == "SY Raw"
    assert PAD_PROFILES[3]["cc_map"] is PAD_3_SY_RAW_CC_MAP


def test_group_layout_contains_only_pads_1_to_4():
    assert set(GROUP_LAYOUT) == {1, 2, 3, 4}
    assert_no_out_of_scope_pad_keys(GROUP_LAYOUT)


def test_group_layout_matches_v134_metadata():
    assert GROUP_LAYOUT[1] == {
        "role": "Main kick / BD Hard default",
        "profile": "2",
        "zone": "full",
        "depth": "micro",
    }
    assert GROUP_LAYOUT[2] == {
        "role": "Secondary kick / rolling low percussion",
        "profile": "3",
        "zone": "body",
        "depth": "groove",
    }
    assert GROUP_LAYOUT[3] == {
        "role": "SY Raw midrange bass / synth-percussion",
        "profile": "5",
        "zone": "lfo",
        "depth": "groove",
    }
    assert GROUP_LAYOUT[4] == {
        "role": "Body hit / accent layer",
        "profile": "4",
        "zone": "body",
        "depth": "micro",
    }


def test_group_profile_metadata_contains_only_v134_group_profiles():
    assert set(GROUP_PROFILE_METADATA) == {"2", "3", "4", "5"}
    assert GROUP_PROFILE_METADATA["2"] == {
        "name": "My BD Hard",
        "machine_value": 0,
        "group_pad": 1,
    }
    assert GROUP_PROFILE_METADATA["3"] == {
        "name": "My BD Classic",
        "machine_value": 1,
        "group_pad": 2,
    }
    assert GROUP_PROFILE_METADATA["4"] == {
        "name": "My BD Acoustic",
        "machine_value": 30,
        "group_pad": 4,
    }
    assert GROUP_PROFILE_METADATA["5"] == {
        "name": "Pad 3 SY Raw Mid Bass",
        "machine_value": 32,
        "group_pad": 3,
    }


def test_group_layout_profiles_are_known_metadata_only_profiles():
    for pad, layout in GROUP_LAYOUT.items():
        profile = GROUP_PROFILE_METADATA[layout["profile"]]
        assert profile["group_pad"] == pad
        assert profile["group_pad"] not in OUT_OF_SCOPE_PADS


def test_scene_variants_exist():
    expected = {"S1A", "S1B", "S2A", "S2B", "S3A", "S3B", "S4A", "S4B"}
    assert expected.issubset(SCENE_COMMANDS)
    assert expected.issubset(COMMANDS)


def test_v134_scene_registry_contains_only_known_scene_commands():
    expected = {
        "S0",
        "S1",
        "S1A",
        "S1B",
        "S2",
        "S2A",
        "S2B",
        "S3",
        "S3A",
        "S3B",
        "S4",
        "S4A",
        "S4B",
        "S5",
    }
    assert set(SCENE_COMMANDS) == expected
    assert SCENE_COMMANDS["S0"]["name"] == "Home / Clean"
    assert SCENE_COMMANDS["S0"]["action"] == "home"
    assert SCENE_COMMANDS["S4B"]["name"] == "Wild Maximum"
    assert SCENE_COMMANDS["S4B"]["action"] == "wild_maximum"
    assert SCENE_COMMANDS["S5"]["name"] == "Back to Clean"
    assert SCENE_COMMANDS["S5"]["action"] == "clean"


def test_scene_command_descriptions_match_v134_examples():
    assert (
        SCENE_COMMANDS["S0"]["description"]
        == "Load or return all four pads to the validated anchors."
    )
    assert (
        SCENE_COMMANDS["S2B"]["description"]
        == "More filter/grit pressure on the secondary lanes while Pad 1 stays bounded."
    )
    assert (
        SCENE_COMMANDS["S4B"]["description"]
        == "The maximum V1.34 discovery scene, using the existing wild guardrails."
    )


def test_scene_commands_are_scaffold_only_and_not_executable():
    for metadata in SCENE_COMMANDS.values():
        assert metadata["scope"] == "four_pad_group"
        assert_protocol_command_metadata(metadata)
        assert "5" not in metadata["description"]
        assert "6" not in metadata["description"]
        assert "7" not in metadata["description"]
        assert "8" not in metadata["description"]
        assert "9" not in metadata["description"]
        assert "10" not in metadata["description"]
        assert "11" not in metadata["description"]
        assert "12" not in metadata["description"]


def test_commands_preserve_full_scene_metadata():
    for command, metadata in SCENE_COMMANDS.items():
        assert COMMANDS[command] == {
            **metadata,
            "type": "scene",
        }


def test_bare_main_prompt_depth_numbers_are_guarded():
    expected_labels = {
        "1": "guarded depth input 1, requires lane/mode prefix",
        "2": "guarded depth input 2, requires lane/mode prefix",
        "3": "guarded depth input 3, requires lane/mode prefix",
    }

    for command in ("1", "2", "3"):
        assert is_guarded_main_prompt_depth(command)
        assert COMMANDS[command]["type"] == "guarded_depth"
        assert COMMANDS[command]["label"] == expected_labels[command]
        assert_sends_no_midi(COMMANDS[command])
        assert_protocol_command_metadata(COMMANDS[command])


def test_main_prompt_depth_guardrail_metadata_matches_v134():
    assert MAIN_PROMPT_DEPTH_GUARDRAIL["commands"] == ("1", "2", "3")
    assert_sends_no_midi(MAIN_PROMPT_DEPTH_GUARDRAIL)
    assert "main Command prompt" in MAIN_PROMPT_DEPTH_GUARDRAIL["message"]
    assert "No MIDI was sent" in MAIN_PROMPT_DEPTH_GUARDRAIL["message"]


def test_menu_status_commands_match_v134_metadata_only_set():
    expected = {
        "BD",
        "FM",
        "PD",
        "SM",
        "P2M",
        "J",
        "GM",
        "SCN",
        "PR",
        "SR",
        "P3M",
        "P4M",
        "H",
        "R",
    }
    assert set(MENU_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_menu_status_commands_do_not_send_midi_or_define_execution():
    for command, metadata in MENU_COMMANDS.items():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)
        assert "5" not in metadata["label"]
        assert "6" not in metadata["label"]
        assert "7" not in metadata["label"]
        assert "8" not in metadata["label"]
        assert "9" not in metadata["label"]
        assert "10" not in metadata["label"]
        assert "11" not in metadata["label"]
        assert "12" not in metadata["label"]


def test_representative_menu_status_labels_match_v134_intent():
    assert MENU_COMMANDS["BD"] == {
        "type": "menu",
        "sends_midi": False,
        "label": "show BD engine tools",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert MENU_COMMANDS["SCN"] == {
        "type": "menu",
        "sends_midi": False,
        "label": "show scene / preset tools",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert MENU_COMMANDS["R"] == {
        "type": "print",
        "sends_midi": False,
        "label": "print current script state",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }


def test_utility_commands_match_v134_metadata_only_set():
    expected = {"T", "C", "Q"}

    assert set(UTILITY_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_utility_commands_are_scaffold_only_and_not_executable():
    for metadata in UTILITY_COMMANDS.values():
        assert_sends_no_midi(metadata)
        assert_protocol_command_metadata(metadata)


def test_representative_utility_command_labels_match_v134_intent():
    assert UTILITY_COMMANDS["T"] == {
        "type": "selection",
        "scope": "target_pad_channel",
        "sends_midi": False,
        "label": "select target pad/channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert UTILITY_COMMANDS["C"] == {
        "type": "selection",
        "scope": "midi_channel",
        "sends_midi": False,
        "label": "change MIDI channel",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }
    assert UTILITY_COMMANDS["Q"] == {
        "type": "session",
        "scope": "operator_session",
        "sends_midi": False,
        "label": "quit",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    }


def test_forbidden_actions_match_controlled_mutation_roadmap():
    expected_labels = {
        "Master volume",
        "Track volume",
        "Clock",
        "Transport",
        "Pattern change",
        "Program change",
        "Project change",
        "Kit save/clear",
        "System commands",
        "Unvalidated SysEx writes",
    }
    assert {metadata["label"] for metadata in FORBIDDEN_ACTIONS.values()} == expected_labels


def test_forbidden_actions_are_metadata_only_no_touch_entries():
    for metadata in FORBIDDEN_ACTIONS.values():
        assert metadata["status"] == "forbidden_by_default"
        assert_sends_no_midi(metadata)
        assert metadata["source"] == "CONTROLLED_MUTATION_ROADMAP"
        assert_no_execution_fields(metadata)


def test_group_commands_match_v134_four_lane_metadata_only_set():
    expected = {"O", "X", "D", "I", "4", "Y", "V", "N", "Z"}
    assert set(GROUP_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_group_commands_are_scaffold_only_and_not_executable():
    for metadata in GROUP_COMMANDS.values():
        assert metadata["scope"] == "four_pad_group"
        assert_protocol_command_metadata(metadata)
        assert "5" not in metadata["label"]
        assert "6" not in metadata["label"]
        assert "7" not in metadata["label"]
        assert "8" not in metadata["label"]
        assert "9" not in metadata["label"]
        assert "10" not in metadata["label"]
        assert "11" not in metadata["label"]
        assert "12" not in metadata["label"]


def test_group_command_4_is_v134_wild_mutation_not_guarded_depth():
    assert "4" in GROUP_COMMANDS
    assert not is_guarded_main_prompt_depth("4")
    assert COMMANDS["4"]["type"] == "mutation"
    assert COMMANDS["4"]["label"] == "harder / wild four-lane mutation"
    assert COMMANDS["4"]["executable"] is False


def test_representative_group_command_labels_match_v134_intent():
    assert GROUP_COMMANDS["O"]["label"] == "load full 4-pad group anchors"
    assert GROUP_COMMANDS["D"]["label"] == "deeper four-lane mutation, Pads 2-4 pushed harder"
    assert GROUP_COMMANDS["Y"]["command_family"] == "lane_aware_page"
    assert GROUP_COMMANDS["V"]["command_family"] == "lane_aware_page"
    assert GROUP_COMMANDS["N"]["command_family"] == "lane_aware_page"
    assert GROUP_COMMANDS["Z"]["label"] == "return all 4 group pads to anchors"


def test_pad1_commands_match_v134_metadata_only_set():
    expected = {
        "BR",
        "BM",
        "BH",
        "BS",
        "BC",
        "BA",
        "BF",
        "FT",
        "FK",
        "FG",
        "FZ",
        "BP",
        "PT",
        "PK",
        "PX",
        "PBH",
        "BI",
        "ST",
        "SK",
        "SC",
        "SBH",
    }
    assert set(PAD1_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_pad1_commands_are_scaffold_only_and_not_executable():
    for metadata in PAD1_COMMANDS.values():
        assert_pad_command_metadata_only(metadata, 1)


def test_representative_pad1_command_labels_match_v134_intent():
    assert PAD1_COMMANDS["BR"]["label"] == "rotate Pad 1 to the next profiled BD engine"
    assert PAD1_COMMANDS["BM"]["label"] == "safely mutate the currently loaded Pad 1 BD engine"
    assert PAD1_COMMANDS["BH"]["label"] == "load Pad 1 BD Hard anchor, primary default"
    assert PAD1_COMMANDS["FZ"]["label"] == "return Pad 1 BD FM to anchor"
    assert PAD1_COMMANDS["PBH"]["label"] == "return Pad 1 BD Plastic to anchor"
    assert PAD1_COMMANDS["SBH"]["label"] == "return Pad 1 BD Silky to anchor"


def test_pad2_commands_match_v134_metadata_only_set():
    expected = {"P2B", "P2H", "P2C", "P2F", "P2T", "P2P", "P2G", "P2R", "P2X", "P2Z"}
    assert set(PAD2_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_pad2_commands_are_scaffold_only_and_not_executable():
    for metadata in PAD2_COMMANDS.values():
        assert_pad_command_metadata_only(metadata, 2)


def test_representative_pad2_command_labels_match_v134_intent():
    assert PAD2_COMMANDS["P2B"]["label"] == "load Pad 2 BD Classic rolling low percussion / home"
    assert PAD2_COMMANDS["P2G"]["label"] == "Pad 2 grit / noise discovery"
    assert PAD2_COMMANDS["P2R"]["label"] == "rotate Pad 2 through profiled secondary-lane engines"
    assert PAD2_COMMANDS["P2Z"]["label"] == "return current Pad 2 profile to anchor"


def test_pad3_commands_match_v134_metadata_only_set():
    expected = {"SW", "SL", "SB", "SX", "SA", "P3R", "P3X", "P3A"}
    assert set(PAD3_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_pad3_commands_are_scaffold_only_and_not_executable():
    for metadata in PAD3_COMMANDS.values():
        assert_pad_command_metadata_only(metadata, 3)


def test_representative_pad3_command_labels_match_v134_intent():
    assert PAD3_COMMANDS["SW"]["label"] == "Pad 3 SY Raw Wave + Balance discovery"
    assert PAD3_COMMANDS["SA"]["label"] == "return Pad 3 SY Raw to anchor"
    assert PAD3_COMMANDS["P3R"]["label"] == "rotate Pad 3 through SY Raw behavior modes"
    assert PAD3_COMMANDS["P3A"]["label"] == "return Pad 3 to SY Raw Mid Bass anchor / home"


def test_pad4_commands_match_v134_metadata_only_set():
    expected = {"P4R", "P4X", "P4A"}
    assert set(PAD4_COMMANDS) == expected
    assert expected.issubset(COMMANDS)


def test_pad4_commands_are_scaffold_only_and_not_executable():
    for metadata in PAD4_COMMANDS.values():
        assert_pad_command_metadata_only(metadata, 4)


def test_representative_pad4_command_labels_match_v134_intent():
    assert PAD4_COMMANDS["P4R"]["label"] == "rotate Pad 4 through BD Acoustic behavior modes"
    assert PAD4_COMMANDS["P4X"]["label"] == "safely mutate the currently loaded Pad 4 mode"
    assert PAD4_COMMANDS["P4A"]["label"] == "return Pad 4 to BD Acoustic body/accent anchor / home"


def test_all_commands_are_non_executable_metadata_without_runtime_hooks():
    for metadata in COMMANDS.values():
        assert metadata["executable"] is False
        assert_no_execution_fields(metadata)


def test_no_out_of_scope_pads_in_command_metadata_labels():
    for metadata in COMMANDS.values():
        label = metadata.get("label", "")
        description = metadata.get("description", "")
        text = f"{label} {description}"
        assert "Pad 5" not in text
        assert "Pad 6" not in text
        assert "Pad 7" not in text
        assert "Pad 8" not in text
        assert "Pad 9" not in text
        assert "Pad 10" not in text
        assert "Pad 11" not in text
        assert "Pad 12" not in text
