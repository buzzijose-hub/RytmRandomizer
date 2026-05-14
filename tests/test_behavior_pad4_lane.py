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
        text=True,
        capture_output=True,
        check=False,
    )


def test_importing_behavior_pad4_lane_prints_nothing():
    code = "import rytm_randomizer.behavior_pad4_lane"
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_p4a_returns_read_only_pad4_bd_acoustic_home_anchor_intent():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4A")

    assert result.command_key == "P4A"
    assert result.accepted is True
    assert result.reason == "supported_pad4_bd_acoustic_home_anchor_intent"
    assert result.label == "return Pad 4 to BD Acoustic body/accent anchor / home"
    assert result.behavior_family == "pad4-lane/bd-acoustic-body-accent-home-anchor"
    assert result.target_pad == 4
    assert result.lane == "Pad 4 BD Acoustic lane"
    assert result.lane_action == "return_pad4_bd_acoustic_body_accent_home_anchor"
    assert result.intent_kind == "anchor_return"
    assert result.anchor_concept == "Pad 4 BD Acoustic body/accent home anchor"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_lane_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "P4A: return Pad 4 to BD Acoustic body/accent anchor / home",
        "Read-only Pad 4 BD Acoustic body/accent home anchor intent.",
        "Target pad: 4",
        "Lane: Pad 4 BD Acoustic lane",
        "Lane action: return_pad4_bd_acoustic_body_accent_home_anchor",
        "Pad 4 BD Acoustic body/accent home anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p4a_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4A")

    assert result.metadata["source"] == "PAD4_COMMANDS"
    assert result.metadata["command_type"] == "anchor_return"
    assert result.metadata["target_pad"] == 4
    assert result.metadata["lane"] == "pad_4_bd_acoustic_lane"
    assert (
        result.metadata["behavior_family"]
        == "pad4-lane/bd-acoustic-body-accent-home-anchor"
    )
    assert (
        result.metadata["lane_action"]
        == "return_pad4_bd_acoustic_body_accent_home_anchor"
    )
    assert result.metadata["intent_kind"] == "anchor_return"
    assert (
        result.metadata["anchor_concept"]
        == "Pad 4 BD Acoustic body/accent home anchor"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p4r_returns_read_only_pad4_bd_acoustic_mode_rotation_intent():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4R")

    assert result.command_key == "P4R"
    assert result.accepted is True
    assert result.reason == "supported_pad4_bd_acoustic_mode_rotation_intent"
    assert result.label == "rotate Pad 4 through BD Acoustic behavior modes"
    assert result.behavior_family == "pad4-lane/bd-acoustic-mode-rotation"
    assert result.target_pad == 4
    assert result.lane == "Pad 4 BD Acoustic lane"
    assert result.lane_action == "describe_pad4_bd_acoustic_mode_rotation_intent"
    assert result.intent_kind == "rotation"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_lane_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "P4R: rotate Pad 4 through BD Acoustic behavior modes",
        "Read-only Pad 4 BD Acoustic behavior mode rotation intent.",
        "Target pad: 4",
        "Lane: Pad 4 BD Acoustic lane",
        "Lane action: describe_pad4_bd_acoustic_mode_rotation_intent",
        "Rotation concept: Pad 4 BD Acoustic behavior mode rotation",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p4r_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4R")

    assert result.metadata["source"] == "PAD4_COMMANDS"
    assert result.metadata["command_type"] == "rotation"
    assert result.metadata["target_pad"] == 4
    assert result.metadata["lane"] == "pad_4_bd_acoustic_lane"
    assert result.metadata["behavior_family"] == "pad4-lane/bd-acoustic-mode-rotation"
    assert (
        result.metadata["lane_action"]
        == "describe_pad4_bd_acoustic_mode_rotation_intent"
    )
    assert result.metadata["intent_kind"] == "rotation"
    assert (
        result.metadata["rotation_concept"]
        == "Pad 4 BD Acoustic behavior mode rotation"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p4x_returns_read_only_pad4_bd_acoustic_current_mode_safe_mutation_intent():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4X")

    assert result.command_key == "P4X"
    assert result.accepted is True
    assert result.reason == "supported_pad4_bd_acoustic_current_mode_safe_mutation_intent"
    assert result.label == "safely mutate the currently loaded Pad 4 mode"
    assert (
        result.behavior_family
        == "pad4-lane/bd-acoustic-current-mode-safe-mutation"
    )
    assert result.target_pad == 4
    assert result.lane == "Pad 4 BD Acoustic lane"
    assert (
        result.lane_action
        == "describe_pad4_bd_acoustic_current_mode_safe_mutation_intent"
    )
    assert result.intent_kind == "mutation"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_lane_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "P4X: safely mutate the currently loaded Pad 4 mode",
        "Read-only Pad 4 BD Acoustic current mode safe mutation intent.",
        "Target pad: 4",
        "Lane: Pad 4 BD Acoustic lane",
        "Lane action: describe_pad4_bd_acoustic_current_mode_safe_mutation_intent",
        "Mutation concept: Pad 4 BD Acoustic current mode safe mutation",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p4x_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4X")

    assert result.metadata["source"] == "PAD4_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 4
    assert result.metadata["lane"] == "pad_4_bd_acoustic_lane"
    assert (
        result.metadata["behavior_family"]
        == "pad4-lane/bd-acoustic-current-mode-safe-mutation"
    )
    assert (
        result.metadata["lane_action"]
        == "describe_pad4_bd_acoustic_current_mode_safe_mutation_intent"
    )
    assert result.metadata["intent_kind"] == "mutation"
    assert (
        result.metadata["mutation_concept"]
        == "Pad 4 BD Acoustic current mode safe mutation"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_pad4_lane_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("P4A")

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_pad4_lane_behavior("P4A")
    assert fresh_result.metadata["source"] == "PAD4_COMMANDS"

    p4r_result = evaluate_pad4_lane_behavior("P4R")

    try:
        p4r_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_p4r_result = evaluate_pad4_lane_behavior("P4R")
    assert fresh_p4r_result.metadata["source"] == "PAD4_COMMANDS"

    p4x_result = evaluate_pad4_lane_behavior("P4X")

    try:
        p4x_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_p4x_result = evaluate_pad4_lane_behavior("P4X")
    assert fresh_p4x_result.metadata["source"] == "PAD4_COMMANDS"


def test_deferred_packet_8_pad4_lane_keys_fail_safely():
    from rytm_randomizer.behavior_pad4_lane import (
        DEFERRED_PACKET_8_PAD4_LANE_KEYS,
        evaluate_pad4_lane_behavior,
    )

    assert DEFERRED_PACKET_8_PAD4_LANE_KEYS == ("P4M",)

    for command_key in DEFERRED_PACKET_8_PAD4_LANE_KEYS:
        result = evaluate_pad4_lane_behavior(command_key)

        assert result.command_key == command_key
        assert result.accepted is False
        assert result.reason == "unsupported_packet_8_pad4_lane_key"
        assert result.state_changed is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["mock_only"] is True
        assert result.metadata["sends_real_midi"] is False


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_pad4_lane import evaluate_pad4_lane_behavior

    result = evaluate_pad4_lane_behavior("NOPE")

    assert result.command_key == "NOPE"
    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["source"] == "unknown"


def test_packet_1_p4m_menu_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("P4M")

    assert result.accepted is True
    assert result.reason == "supported_menu_status_behavior"
    assert result.label == "show Pad 4 BD Acoustic body / accent menu"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "P4A")

    assert result.returncode == 0
    assert "Command: P4A" in result.stdout
    assert "Label: return Pad 4 to BD Acoustic body/accent anchor / home" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_pad4_lane  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_package_metadata_files_are_introduced():
    for filename in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_pad4_lane_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_pad4_lane as behavior_pad4_lane

    exposed_names = set(dir(behavior_pad4_lane))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_behavior_pad4_lane_exposes_explicit_public_api():
    import rytm_randomizer.behavior_pad4_lane as behavior_pad4_lane

    assert behavior_pad4_lane.__all__ == [
        "DEFERRED_PACKET_8_PAD4_LANE_KEYS",
        "PACKET_8A_PAD4_LANE_KEYS",
        "PACKET_8B_PAD4_LANE_KEYS",
        "PACKET_8C_PAD4_LANE_KEYS",
        "Pad4LaneBehaviorResult",
        "evaluate_pad4_lane_behavior",
    ]


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_pad4_lane as behavior_pad4_lane

    module_text = "\n".join(
        [
            behavior_pad4_lane.__doc__ or "",
            behavior_pad4_lane.evaluate_pad4_lane_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_pad4_lane_prints_nothing()
    test_p4a_returns_read_only_pad4_bd_acoustic_home_anchor_intent()
    test_p4a_metadata_contains_expected_passive_sources()
    test_p4r_returns_read_only_pad4_bd_acoustic_mode_rotation_intent()
    test_p4r_metadata_contains_expected_passive_sources()
    test_p4x_returns_read_only_pad4_bd_acoustic_current_mode_safe_mutation_intent()
    test_p4x_metadata_contains_expected_passive_sources()
    test_pad4_lane_metadata_is_copied_and_immutable()
    test_deferred_packet_8_pad4_lane_keys_fail_safely()
    test_unknown_keys_fail_safely()
    test_packet_1_p4m_menu_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_pad4_lane_exposes_no_active_behavior_names()
    test_behavior_pad4_lane_exposes_explicit_public_api()
    test_no_out_of_scope_support_is_exposed()
