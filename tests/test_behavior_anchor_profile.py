from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_anchor_profile_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_anchor_profile"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_bh_returns_read_only_bd_hard_anchor_profile_intent():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BH")

    assert result.accepted is True
    assert result.command_key == "BH"
    assert result.label == "load Pad 1 BD Hard anchor, primary default"
    assert result.behavior_family == "anchor/profile"
    assert result.reason == "supported_anchor_profile_intent"
    assert result.target_pad == 1
    assert result.anchor_name == "BD Hard"
    assert result.profile_key == "2"
    assert result.machine_value == 0
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "BH: load Pad 1 BD Hard anchor, primary default",
        "Read-only anchor/profile intent.",
        "Target pad: 1",
        "Anchor: BD Hard",
        "Profile key: 2",
        "No prompt would run.",
        "No state would change.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_bc_returns_read_only_bd_classic_anchor_profile_intent():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BC")

    assert result.accepted is True
    assert result.command_key == "BC"
    assert result.label == "load Pad 1 BD Classic anchor"
    assert result.behavior_family == "anchor/profile"
    assert result.reason == "supported_anchor_profile_intent"
    assert result.target_pad == 1
    assert result.anchor_name == "BD Classic"
    assert result.profile_key == "3"
    assert result.machine_value == 1
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "BC: load Pad 1 BD Classic anchor",
        "Read-only anchor/profile intent.",
        "Target pad: 1",
        "Anchor: BD Classic",
        "Profile key: 3",
        "No prompt would run.",
        "No state would change.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_bs_returns_read_only_bd_sharp_anchor_profile_intent_without_profile_metadata():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BS")

    assert result.accepted is True
    assert result.command_key == "BS"
    assert result.label == "load Pad 1 BD Sharp anchor"
    assert result.behavior_family == "anchor/profile"
    assert result.reason == "supported_anchor_profile_intent"
    assert result.target_pad == 1
    assert result.anchor_name == "BD Sharp"
    assert result.profile_key == ""
    assert result.machine_value is None
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "BS: load Pad 1 BD Sharp anchor",
        "Read-only anchor/profile intent.",
        "Target pad: 1",
        "Anchor: BD Sharp",
        "Profile metadata: absent",
        "No prompt would run.",
        "No state would change.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_anchor_profile_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_anchor_profile import AnchorProfileBehaviorResult

    metadata = {"source": "test"}
    result = AnchorProfileBehaviorResult(command_key="BH", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_bh_and_bc_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    expected = {
        "BH": {
            "source": "PAD1_COMMANDS",
            "source_profile_key": "2",
            "source_profile_name": "My BD Hard",
            "source_profile_group_pad": 1,
            "target": "Pad 1 / BD Hard",
            "machine_value": 0,
        },
        "BC": {
            "source": "PAD1_COMMANDS",
            "source_profile_key": "3",
            "source_profile_name": "My BD Classic",
            "source_profile_group_pad": 2,
            "target": "Pad 1 / BD Classic",
            "machine_value": 1,
        },
    }

    for command_key, expected_metadata in expected.items():
        result = evaluate_anchor_profile_behavior(command_key)

        for key, value in expected_metadata.items():
            assert result.metadata[key] == value
        assert result.metadata["mock_only"] is True
        assert result.metadata["sends_real_midi"] is False
        assert result.metadata["opens_ports"] is False
        assert result.metadata["hardware_required"] is False
        assert result.metadata["active_behavior"] is False
        assert result.metadata["mutates_runtime_state"] is False


def test_bs_metadata_records_absent_group_profile_without_inventing_values():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BS")

    assert result.metadata["source"] == "PAD1_COMMANDS"
    assert result.metadata["source_command_type"] == "load"
    assert result.metadata["source_profile_key"] == ""
    assert result.metadata["source_profile_name"] == ""
    assert result.metadata["source_profile_group_pad"] is None
    assert result.metadata["group_profile_metadata_exists"] is False
    assert result.metadata["target"] == "Pad 1 / BD Sharp"
    assert result.metadata["machine_value"] is None
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_anchor_profile_evaluations_are_deterministic():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    assert evaluate_anchor_profile_behavior("BH") == evaluate_anchor_profile_behavior("BH")
    assert evaluate_anchor_profile_behavior("BC") == evaluate_anchor_profile_behavior("BC")
    assert evaluate_anchor_profile_behavior("BS") == evaluate_anchor_profile_behavior("BS")


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_deferred_anchor_profile_keys_fail_safely():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    for command_key in ("BA", "BR", "P", "M", "O", "Z", "P2B", "P3A", "P4A"):
        result = evaluate_anchor_profile_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "unsupported_anchor_profile_command"
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "BH")

    assert result.returncode == 0
    assert "Command: BH" in result.stdout
    assert "Label: load Pad 1 BD Hard anchor, primary default" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_anchor_profile  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_package_metadata_files_are_introduced():
    for filename in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_anchor_profile_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_anchor_profile as behavior_anchor_profile

    exposed_names = set(dir(behavior_anchor_profile))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_anchor_profile as behavior_anchor_profile

    module_text = "\n".join(
        [
            behavior_anchor_profile.__doc__ or "",
            behavior_anchor_profile.evaluate_anchor_profile_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_anchor_profile_prints_nothing()
    test_bh_returns_read_only_bd_hard_anchor_profile_intent()
    test_bc_returns_read_only_bd_classic_anchor_profile_intent()
    test_bs_returns_read_only_bd_sharp_anchor_profile_intent_without_profile_metadata()
    test_anchor_profile_metadata_is_copied_and_immutable()
    test_bh_and_bc_metadata_contains_expected_passive_sources()
    test_bs_metadata_records_absent_group_profile_without_inventing_values()
    test_repeated_anchor_profile_evaluations_are_deterministic()
    test_unknown_keys_fail_safely()
    test_deferred_anchor_profile_keys_fail_safely()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_anchor_profile_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
