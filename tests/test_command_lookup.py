from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.command_lookup import (
    describe_command,
    get_command_label,
    get_command_type,
    list_command_keys,
)
from rytm_randomizer.commands import COMMANDS


FORBIDDEN_EXECUTION_FIELDS = {"handler", "callable", "execute", "function", "callback"}
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


def assert_passive_command_report(report, command_key):
    assert report["exists"] is True
    assert report["command_key"] == command_key
    assert report["executable"] is False
    assert report["v134_reference_command"] is True
    assert report["scaffold_only"] is True
    assert FORBIDDEN_EXECUTION_FIELDS.isdisjoint(report["metadata"])


def test_command_keys_are_existing_v134_metadata_only():
    assert list_command_keys() == tuple(COMMANDS.keys())
    assert "O" in list_command_keys()
    assert "S1A" in list_command_keys()
    assert "BH" in list_command_keys()
    assert "P2B" in list_command_keys()
    assert "P3A" in list_command_keys()
    assert "P4A" in list_command_keys()


def test_known_group_command_lookup_returns_existing_metadata():
    report = describe_command("O")

    assert_passive_command_report(report, "O")
    assert report["type"] == "load"
    assert report["scope"] == "four_pad_group"
    assert report["label"] == "load full 4-pad group anchors"
    assert report["metadata"] == COMMANDS["O"]


def test_known_scene_command_lookup_returns_existing_metadata():
    report = describe_command("S1A")

    assert_passive_command_report(report, "S1A")
    assert report["type"] == "scene"
    assert report["scope"] == "four_pad_group"
    assert report["name"] == "Rolling Light"
    assert report["metadata"] == COMMANDS["S1A"]


def test_known_pad_1_to_4_command_lookups_return_existing_metadata():
    expected = {
        "BH": (1, "pad_1", "load Pad 1 BD Hard anchor, primary default"),
        "P2B": (2, "pad_2", "load Pad 2 BD Classic rolling low percussion / home"),
        "P3A": (3, "pad_3", "return Pad 3 to SY Raw Mid Bass anchor / home"),
        "P4A": (4, "pad_4", "return Pad 4 to BD Acoustic body/accent anchor / home"),
    }

    for command_key, (pad, scope, label) in expected.items():
        report = describe_command(command_key)

        assert_passive_command_report(report, command_key)
        assert report["pad"] == pad
        assert report["scope"] == scope
        assert report["label"] == label
        assert report["metadata"] == COMMANDS[command_key]


def test_command_lookup_helpers_return_existing_values_only():
    assert get_command_type("O") == "load"
    assert get_command_type("S1A") == "scene"
    assert get_command_label("O") == "load full 4-pad group anchors"
    assert get_command_label("S1A") == "Rolling Light"


def test_command_lookup_normalizes_keys_without_executing():
    assert describe_command("s1a")["command_key"] == "S1A"
    assert get_command_label("p3a") == "return Pad 3 to SY Raw Mid Bass anchor / home"


def test_unknown_command_returns_passive_not_found_result():
    assert describe_command("UNKNOWN") == {
        "exists": False,
        "command_key": "UNKNOWN",
        "metadata": None,
    }
    assert get_command_type("UNKNOWN") is None
    assert get_command_label("UNKNOWN") is None


def test_command_lookup_does_not_expose_pads_5_to_12():
    for command_key in list_command_keys():
        report = describe_command(command_key)
        metadata = report["metadata"]
        command_text = " ".join(
            str(metadata.get(field, ""))
            for field in ("label", "name", "description", "scope")
        )

        for pad_text in OUT_OF_SCOPE_PAD_TEXT:
            assert pad_text not in command_text


def test_command_lookup_exposes_no_execution_fields():
    for command_key in list_command_keys():
        report = describe_command(command_key)

        assert FORBIDDEN_EXECUTION_FIELDS.isdisjoint(report)
        assert FORBIDDEN_EXECUTION_FIELDS.isdisjoint(report["metadata"])


def test_describe_command_returns_metadata_copy():
    report = describe_command("O")

    report["metadata"]["label"] = "mutated test label"

    assert COMMANDS["O"]["label"] == "load full 4-pad group anchors"


if __name__ == "__main__":
    test_command_keys_are_existing_v134_metadata_only()
    test_known_group_command_lookup_returns_existing_metadata()
    test_known_scene_command_lookup_returns_existing_metadata()
    test_known_pad_1_to_4_command_lookups_return_existing_metadata()
    test_command_lookup_helpers_return_existing_values_only()
    test_command_lookup_normalizes_keys_without_executing()
    test_unknown_command_returns_passive_not_found_result()
    test_command_lookup_does_not_expose_pads_5_to_12()
    test_command_lookup_exposes_no_execution_fields()
    test_describe_command_returns_metadata_copy()
