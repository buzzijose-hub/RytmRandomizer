import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.scene_lookup import (
    describe_scene,
    get_scene_action,
    get_scene_name,
    list_scene_keys,
)
from rytm_randomizer.scenes import SCENE_COMMANDS

OUT_OF_SCOPE_PAD_TEXT = (
    "Pad 5",
    "Pad 6",
    "Pad 7",
    "Pad 8",
    "Pad 9",
    "Pad 10",
    "Pad 11",
    "Pad 12",
)


def test_scene_keys_are_existing_v134_metadata_only():
    expected = (
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
    )

    assert list_scene_keys() == expected
    assert tuple(SCENE_COMMANDS) == expected


def test_describe_scene_returns_existing_metadata_values():
    expected = {
        "S0": ("Home / Clean", "home"),
        "S1A": ("Rolling Light", "rolling_light"),
        "S2B": ("Deeper Pressure", "deeper_pressure"),
        "S4B": ("Wild Maximum", "wild_maximum"),
        "S5": ("Back to Clean", "clean"),
    }

    for scene_key, (name, action) in expected.items():
        report = describe_scene(scene_key)

        assert report["exists"] is True
        assert report["scene_key"] == scene_key
        assert report["name"] == name
        assert report["action"] == action
        assert report["scope"] == "four_pad_group"
        assert report["executable"] is False
        assert report["v134_reference_command"] is True
        assert report["scaffold_only"] is True
        assert report["metadata"] == SCENE_COMMANDS[scene_key]


def test_scene_lookup_helpers_return_existing_values_only():
    assert get_scene_name("S1A") == "Rolling Light"
    assert get_scene_name("S4B") == "Wild Maximum"
    assert get_scene_action("S1A") == "rolling_light"
    assert get_scene_action("S4B") == "wild_maximum"


def test_scene_lookup_normalizes_keys_without_executing():
    assert describe_scene("s1a")["scene_key"] == "S1A"
    assert get_scene_name("s1a") == "Rolling Light"


def test_unknown_scene_returns_passive_not_found_result():
    assert describe_scene("UNKNOWN") == {
        "exists": False,
        "scene_key": "UNKNOWN",
        "metadata": None,
    }
    assert get_scene_name("UNKNOWN") is None
    assert get_scene_action("UNKNOWN") is None


def test_scene_lookup_does_not_expose_pads_5_to_12():
    for scene_key in list_scene_keys():
        report = describe_scene(scene_key)
        scene_text = " ".join(
            [
                report["name"],
                report["description"],
                report["action"],
                report["scope"],
            ]
        )

        for pad_text in OUT_OF_SCOPE_PAD_TEXT:
            assert pad_text not in scene_text


def test_describe_scene_returns_metadata_copy():
    report = describe_scene("S1A")

    report["metadata"]["name"] = "mutated test name"

    assert SCENE_COMMANDS["S1A"]["name"] == "Rolling Light"


if __name__ == "__main__":
    test_scene_keys_are_existing_v134_metadata_only()
    test_describe_scene_returns_existing_metadata_values()
    test_scene_lookup_helpers_return_existing_values_only()
    test_scene_lookup_normalizes_keys_without_executing()
    test_unknown_scene_returns_passive_not_found_result()
    test_scene_lookup_does_not_expose_pads_5_to_12()
    test_describe_scene_returns_metadata_copy()
