from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import (
    COMMANDS,
    FORBIDDEN_ACTIONS,
    MAIN_PROMPT_DEPTH_GUARDRAIL,
    MENU_COMMANDS,
    is_guarded_main_prompt_depth,
)
from rytm_randomizer.constants import (
    DEFAULT_MIDI_CHANNEL,
    DEFAULT_TARGET_PAD,
    OUT_OF_SCOPE_PAD_GUARDRAIL,
    OUT_OF_SCOPE_PADS,
    PAD_SELECTION_LABELS,
    PAD_TO_MIDI_CHANNEL,
    SUPPORTED_PADS,
)
from rytm_randomizer.profiles import (
    GROUP_LAYOUT,
    GROUP_PROFILE_METADATA,
    PAD_1_DEFAULT_PROFILE,
    PAD_3_SY_RAW_CC_MAP,
)
from rytm_randomizer.scenes import SCENE_COMMANDS


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
    assert not any(pad in PAD_TO_MIDI_CHANNEL for pad in OUT_OF_SCOPE_PADS)
    assert not any(pad in PAD_SELECTION_LABELS for pad in OUT_OF_SCOPE_PADS)
    assert not any(pad in GROUP_LAYOUT for pad in OUT_OF_SCOPE_PADS)
    assert not any(
        profile["group_pad"] in OUT_OF_SCOPE_PADS
        for profile in GROUP_PROFILE_METADATA.values()
    )


def test_default_target_pad_and_channel_match_v134():
    assert DEFAULT_TARGET_PAD == 1
    assert DEFAULT_MIDI_CHANNEL == 0


def test_pad_to_midi_channel_uses_zero_indexed_values_for_pads_1_to_4():
    assert PAD_TO_MIDI_CHANNEL == {
        1: 0,
        2: 1,
        3: 2,
        4: 3,
    }
    assert not any(pad in PAD_TO_MIDI_CHANNEL for pad in OUT_OF_SCOPE_PADS)


def test_pad_selection_labels_match_v134_for_pads_1_to_4_only():
    assert PAD_SELECTION_LABELS == {
        1: "Pad 1 / BD slot",
        2: "Pad 2 / SD slot, flexible BD/SD/SY/UT pool",
        3: "Pad 3 / RS slot, flexible BD/SD/RS/CP/SY/UT pool",
        4: "Pad 4 / CP slot, flexible BD/SD/RS/CP/SY/UT pool",
    }
    assert not any(pad in PAD_SELECTION_LABELS for pad in OUT_OF_SCOPE_PADS)


def test_pad_1_default_home_is_bd_hard():
    assert PAD_1_DEFAULT_PROFILE["pad"] == 1
    assert PAD_1_DEFAULT_PROFILE["name"] == "BD Hard"
    assert PAD_1_DEFAULT_PROFILE["role"] == "default/home"


def test_pad_3_sy_raw_cc_mapping_is_preserved():
    assert PAD_3_SY_RAW_CC_MAP["SRC Noise Level"] == 19
    assert PAD_3_SY_RAW_CC_MAP["SRC Balance"] == 23


def test_group_layout_contains_only_pads_1_to_4():
    assert set(GROUP_LAYOUT) == {1, 2, 3, 4}
    assert not any(pad in GROUP_LAYOUT for pad in OUT_OF_SCOPE_PADS)


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
    assert SCENE_COMMANDS["S0"] == {"name": "Home / Clean", "action": "home"}
    assert SCENE_COMMANDS["S4B"] == {"name": "Wild Maximum", "action": "wild_maximum"}
    assert SCENE_COMMANDS["S5"] == {"name": "Back to Clean", "action": "clean"}


def test_bare_main_prompt_depth_numbers_are_guarded():
    for command in ("1", "2", "3"):
        assert is_guarded_main_prompt_depth(command)
        assert COMMANDS[command]["type"] == "guarded_depth"
        assert COMMANDS[command]["sends_midi"] is False


def test_main_prompt_depth_guardrail_metadata_matches_v134():
    assert MAIN_PROMPT_DEPTH_GUARDRAIL["commands"] == ("1", "2", "3")
    assert MAIN_PROMPT_DEPTH_GUARDRAIL["sends_midi"] is False
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
    forbidden_fields = {"handler", "callable", "execute", "function", "callback"}
    for command, metadata in MENU_COMMANDS.items():
        assert metadata["sends_midi"] is False
        assert forbidden_fields.isdisjoint(metadata)
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
    }
    assert MENU_COMMANDS["SCN"] == {
        "type": "menu",
        "sends_midi": False,
        "label": "show scene / preset tools",
    }
    assert MENU_COMMANDS["R"] == {
        "type": "print",
        "sends_midi": False,
        "label": "print current script state",
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
    forbidden_fields = {"handler", "callable", "execute", "function", "callback"}
    for metadata in FORBIDDEN_ACTIONS.values():
        assert metadata["status"] == "forbidden_by_default"
        assert metadata["sends_midi"] is False
        assert metadata["source"] == "CONTROLLED_MUTATION_ROADMAP"
        assert forbidden_fields.isdisjoint(metadata)
