from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import (
    COMMANDS,
    MAIN_PROMPT_DEPTH_GUARDRAIL,
    is_guarded_main_prompt_depth,
)
from rytm_randomizer.constants import OUT_OF_SCOPE_PADS, SUPPORTED_PADS
from rytm_randomizer.profiles import (
    GROUP_LAYOUT,
    PAD_1_DEFAULT_PROFILE,
    PAD_3_SY_RAW_CC_MAP,
)
from rytm_randomizer.scenes import SCENE_COMMANDS


def test_pads_1_to_4_only_are_supported():
    assert SUPPORTED_PADS == (1, 2, 3, 4)
    assert OUT_OF_SCOPE_PADS == (5, 6, 7, 8, 9, 10, 11, 12)


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
