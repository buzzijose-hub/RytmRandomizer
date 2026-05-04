from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import COMMANDS, is_guarded_main_prompt_depth
from rytm_randomizer.constants import OUT_OF_SCOPE_PADS, SUPPORTED_PADS
from rytm_randomizer.profiles import PAD_1_DEFAULT_PROFILE, PAD_3_SY_RAW_CC_MAP
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


def test_scene_variants_exist():
    expected = {"S1A", "S1B", "S2A", "S2B", "S3A", "S3B", "S4A", "S4B"}
    assert expected.issubset(SCENE_COMMANDS)
    assert expected.issubset(COMMANDS)


def test_bare_main_prompt_depth_numbers_are_guarded():
    for command in ("1", "2", "3"):
        assert is_guarded_main_prompt_depth(command)
        assert COMMANDS[command]["type"] == "guarded_depth"
