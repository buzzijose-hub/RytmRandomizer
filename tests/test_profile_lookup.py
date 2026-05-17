import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.constants import OUT_OF_SCOPE_PADS
from rytm_randomizer.profile_lookup import describe_group_profile
from rytm_randomizer.profiles import GROUP_PROFILE_METADATA


def test_describe_group_profile_returns_existing_metadata_values():
    expected = {
        "2": ("My BD Hard", 0, 1),
        "3": ("My BD Classic", 1, 2),
        "4": ("My BD Acoustic", 30, 4),
        "5": ("Pad 3 SY Raw Mid Bass", 32, 3),
    }

    for profile_key, (name, machine_value, group_pad) in expected.items():
        report = describe_group_profile(profile_key)

        assert report["exists"] is True
        assert report["profile_key"] == profile_key
        assert report["name"] == name
        assert report["machine_value"] == machine_value
        assert report["group_pad"] == group_pad
        assert report["metadata"] == GROUP_PROFILE_METADATA[profile_key]


def test_unknown_group_profile_returns_passive_not_found_result():
    assert describe_group_profile("UNKNOWN") == {
        "exists": False,
        "profile_key": "UNKNOWN",
        "metadata": None,
    }


def test_group_profile_lookup_does_not_expose_pads_5_to_12():
    for profile_key in GROUP_PROFILE_METADATA:
        report = describe_group_profile(profile_key)

        assert report["group_pad"] not in OUT_OF_SCOPE_PADS
        assert "Pad 5" not in report["name"]
        assert "Pad 6" not in report["name"]
        assert "Pad 7" not in report["name"]
        assert "Pad 8" not in report["name"]
        assert "Pad 9" not in report["name"]
        assert "Pad 10" not in report["name"]
        assert "Pad 11" not in report["name"]
        assert "Pad 12" not in report["name"]


def test_describe_group_profile_returns_metadata_copy():
    report = describe_group_profile("2")

    report["metadata"]["name"] = "mutated test name"

    assert GROUP_PROFILE_METADATA["2"]["name"] == "My BD Hard"


if __name__ == "__main__":
    test_describe_group_profile_returns_existing_metadata_values()
    test_unknown_group_profile_returns_passive_not_found_result()
    test_group_profile_lookup_does_not_expose_pads_5_to_12()
    test_describe_group_profile_returns_metadata_copy()
