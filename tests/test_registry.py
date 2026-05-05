from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.commands import COMMANDS
from rytm_randomizer.profiles import GROUP_PROFILE_METADATA
from rytm_randomizer.registry import (
    build_registry,
    get_registry_item,
    get_registry_section,
    list_registry_sections,
    summarize_registry,
)
from rytm_randomizer.scenes import SCENE_COMMANDS


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


def assert_no_forbidden_execution_fields(metadata):
    assert FORBIDDEN_EXECUTION_FIELDS.isdisjoint(metadata)
    assert metadata.get("executable") is not True


def assert_no_out_of_scope_pad_text(metadata):
    metadata_text = " ".join(str(value) for value in metadata.values())
    for pad_text in OUT_OF_SCOPE_PAD_TEXT:
        assert pad_text not in metadata_text


def test_registry_exposes_existing_passive_sections():
    registry = build_registry()

    assert list_registry_sections() == ("commands", "scenes", "group_profiles")
    assert set(registry) == {"commands", "scenes", "group_profiles"}
    assert registry["commands"] == COMMANDS
    assert registry["scenes"] == SCENE_COMMANDS
    assert registry["group_profiles"] == GROUP_PROFILE_METADATA


def test_build_registry_returns_copied_data():
    registry = build_registry()

    registry["commands"]["O"]["label"] = "mutated test label"
    registry["scenes"]["S1A"]["name"] = "mutated test scene"
    registry["group_profiles"]["2"]["name"] = "mutated test profile"

    assert COMMANDS["O"]["label"] == "load full 4-pad group anchors"
    assert SCENE_COMMANDS["S1A"]["name"] == "Rolling Light"
    assert GROUP_PROFILE_METADATA["2"]["name"] == "My BD Hard"


def test_get_registry_section_returns_copied_section():
    report = get_registry_section("commands")

    assert report["exists"] is True
    assert report["section"] == "commands"
    assert report["count"] == len(COMMANDS)
    assert report["items"] == COMMANDS

    report["items"]["O"]["label"] = "mutated test label"

    assert COMMANDS["O"]["label"] == "load full 4-pad group anchors"


def test_unknown_section_returns_passive_not_found_result():
    assert get_registry_section("unknown") == {
        "exists": False,
        "section": "unknown",
        "items": None,
        "count": 0,
    }


def test_get_registry_item_returns_existing_copied_metadata():
    command_report = get_registry_item("commands", "O")
    scene_report = get_registry_item("scenes", "S1A")
    profile_report = get_registry_item("group_profiles", "2")

    assert command_report["exists"] is True
    assert command_report["metadata"] == COMMANDS["O"]
    assert scene_report["exists"] is True
    assert scene_report["metadata"] == SCENE_COMMANDS["S1A"]
    assert profile_report["exists"] is True
    assert profile_report["metadata"] == GROUP_PROFILE_METADATA["2"]

    command_report["metadata"]["label"] = "mutated test label"
    scene_report["metadata"]["name"] = "mutated test scene"
    profile_report["metadata"]["name"] = "mutated test profile"

    assert COMMANDS["O"]["label"] == "load full 4-pad group anchors"
    assert SCENE_COMMANDS["S1A"]["name"] == "Rolling Light"
    assert GROUP_PROFILE_METADATA["2"]["name"] == "My BD Hard"


def test_get_registry_item_normalizes_command_and_scene_keys():
    assert get_registry_item("commands", "p3a")["key"] == "P3A"
    assert get_registry_item("commands", "p3a")["exists"] is True
    assert get_registry_item("scenes", "s1a")["key"] == "S1A"
    assert get_registry_item("scenes", "s1a")["exists"] is True


def test_unknown_item_returns_passive_not_found_result():
    assert get_registry_item("commands", "UNKNOWN") == {
        "exists": False,
        "section_exists": True,
        "section": "commands",
        "key": "UNKNOWN",
        "metadata": None,
    }


def test_unknown_section_item_returns_passive_not_found_result():
    assert get_registry_item("unknown", "O") == {
        "exists": False,
        "section_exists": False,
        "section": "unknown",
        "key": "O",
        "metadata": None,
    }


def test_registry_summary_counts_existing_sections():
    summary = summarize_registry()

    assert summary["sections"] == ("commands", "scenes", "group_profiles")
    assert summary["section_counts"] == {
        "commands": len(COMMANDS),
        "scenes": len(SCENE_COMMANDS),
        "group_profiles": len(GROUP_PROFILE_METADATA),
    }
    assert summary["total_items"] == (
        len(COMMANDS) + len(SCENE_COMMANDS) + len(GROUP_PROFILE_METADATA)
    )


def test_registry_does_not_introduce_execution_fields():
    registry = build_registry()

    for command_metadata in registry["commands"].values():
        assert_no_forbidden_execution_fields(command_metadata)
    for scene_metadata in registry["scenes"].values():
        assert_no_forbidden_execution_fields(scene_metadata)
    for profile_metadata in registry["group_profiles"].values():
        assert_no_forbidden_execution_fields(profile_metadata)


def test_registry_keeps_pads_5_to_12_absent():
    registry = build_registry()

    for section in registry.values():
        for metadata in section.values():
            assert_no_out_of_scope_pad_text(metadata)


def test_registry_uses_existing_passive_metadata_only():
    registry = build_registry()

    assert registry["commands"] == COMMANDS
    assert registry["scenes"] == SCENE_COMMANDS
    assert registry["group_profiles"] == GROUP_PROFILE_METADATA


if __name__ == "__main__":
    test_registry_exposes_existing_passive_sections()
    test_build_registry_returns_copied_data()
    test_get_registry_section_returns_copied_section()
    test_unknown_section_returns_passive_not_found_result()
    test_get_registry_item_returns_existing_copied_metadata()
    test_get_registry_item_normalizes_command_and_scene_keys()
    test_unknown_item_returns_passive_not_found_result()
    test_unknown_section_item_returns_passive_not_found_result()
    test_registry_summary_counts_existing_sections()
    test_registry_does_not_introduce_execution_fields()
    test_registry_keeps_pads_5_to_12_absent()
    test_registry_uses_existing_passive_metadata_only()
