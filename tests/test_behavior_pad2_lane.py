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


def test_importing_behavior_pad2_lane_prints_nothing():
    code = "import rytm_randomizer.behavior_pad_lane"
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


def test_p2b_returns_read_only_pad2_home_anchor_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2B")

    assert result.command_key == "P2B"
    assert result.accepted is True
    assert result.reason == "supported_pad2_bd_classic_home_anchor_intent"
    assert result.label == "load Pad 2 BD Classic rolling low percussion / home"
    assert result.behavior_family == "pad2-lane/bd-classic-home-anchor"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "load_pad2_bd_classic_home_anchor"
    assert result.intent_kind == "anchor_load"
    assert result.anchor_concept == "Pad 2 BD Classic home anchor"
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
        "P2B: load Pad 2 BD Classic rolling low percussion / home",
        "Read-only Pad 2 BD Classic home anchor intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: load_pad2_bd_classic_home_anchor",
        "Pad 2 BD Classic home anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2b_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2B")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["intent_kind"] == "anchor_load"
    assert result.metadata["anchor_concept"] == "Pad 2 BD Classic home anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2h_returns_read_only_pad2_sd_hard_anchor_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2H")

    assert result.command_key == "P2H"
    assert result.accepted is True
    assert result.reason == "supported_pad2_sd_hard_anchor_intent"
    assert result.label == "load Pad 2 SD Hard pressure snare"
    assert result.behavior_family == "pad2-lane/sd-hard-anchor"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "load_pad2_sd_hard_anchor"
    assert result.intent_kind == "anchor_load"
    assert result.anchor_concept == "Pad 2 SD Hard anchor"
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
        "P2H: load Pad 2 SD Hard pressure snare",
        "Read-only Pad 2 SD Hard anchor intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: load_pad2_sd_hard_anchor",
        "Pad 2 SD Hard anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2h_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2H")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/sd-hard-anchor"
    assert result.metadata["lane_action"] == "load_pad2_sd_hard_anchor"
    assert result.metadata["intent_kind"] == "anchor_load"
    assert result.metadata["anchor_concept"] == "Pad 2 SD Hard anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2c_returns_read_only_pad2_sd_classic_anchor_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2C")

    assert result.command_key == "P2C"
    assert result.accepted is True
    assert result.reason == "supported_pad2_sd_classic_anchor_intent"
    assert result.label == "load Pad 2 SD Classic rolling snare"
    assert result.behavior_family == "pad2-lane/sd-classic-anchor"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "load_pad2_sd_classic_anchor"
    assert result.intent_kind == "anchor_load"
    assert result.anchor_concept == "Pad 2 SD Classic anchor"
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
        "P2C: load Pad 2 SD Classic rolling snare",
        "Read-only Pad 2 SD Classic anchor intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: load_pad2_sd_classic_anchor",
        "Pad 2 SD Classic anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2c_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2C")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/sd-classic-anchor"
    assert result.metadata["lane_action"] == "load_pad2_sd_classic_anchor"
    assert result.metadata["intent_kind"] == "anchor_load"
    assert result.metadata["anchor_concept"] == "Pad 2 SD Classic anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2f_returns_read_only_pad2_sd_fm_anchor_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2F")

    assert result.command_key == "P2F"
    assert result.accepted is True
    assert result.reason == "supported_pad2_sd_fm_anchor_intent"
    assert result.label == "load Pad 2 SD FM metallic snare"
    assert result.behavior_family == "pad2-lane/sd-fm-anchor"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "load_pad2_sd_fm_anchor"
    assert result.intent_kind == "anchor_load"
    assert result.anchor_concept == "Pad 2 SD FM anchor"
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
        "P2F: load Pad 2 SD FM metallic snare",
        "Read-only Pad 2 SD FM anchor intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: load_pad2_sd_fm_anchor",
        "Pad 2 SD FM anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2f_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2F")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/sd-fm-anchor"
    assert result.metadata["lane_action"] == "load_pad2_sd_fm_anchor"
    assert result.metadata["intent_kind"] == "anchor_load"
    assert result.metadata["anchor_concept"] == "Pad 2 SD FM anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2t_returns_read_only_pad2_tone_snap_discovery_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2T")

    assert result.command_key == "P2T"
    assert result.accepted is True
    assert result.reason == "supported_pad2_tone_snap_discovery_intent"
    assert result.label == "Pad 2 tone / snap discovery"
    assert result.behavior_family == "pad2-lane/tone-snap-discovery"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_tone_snap_discovery_intent"
    assert result.intent_kind == "discovery_intent"
    assert result.anchor_concept == ""
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
        "P2T: Pad 2 tone / snap discovery",
        "Read-only Pad 2 tone/snap discovery intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_tone_snap_discovery_intent",
        "Discovery concept: Pad 2 tone/snap discovery",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2t_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2T")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/tone-snap-discovery"
    assert result.metadata["lane_action"] == "describe_pad2_tone_snap_discovery_intent"
    assert result.metadata["intent_kind"] == "discovery_intent"
    assert result.metadata["discovery_concept"] == "Pad 2 tone/snap discovery"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2p_returns_read_only_pad2_pressure_body_discovery_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2P")

    assert result.command_key == "P2P"
    assert result.accepted is True
    assert result.reason == "supported_pad2_pressure_body_discovery_intent"
    assert result.label == "Pad 2 pressure / body discovery"
    assert result.behavior_family == "pad2-lane/pressure-body-discovery"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_pressure_body_discovery_intent"
    assert result.intent_kind == "discovery_intent"
    assert result.anchor_concept == ""
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
        "P2P: Pad 2 pressure / body discovery",
        "Read-only Pad 2 pressure/body discovery intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_pressure_body_discovery_intent",
        "Discovery concept: Pad 2 pressure/body discovery",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2p_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2P")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/pressure-body-discovery"
    assert result.metadata["lane_action"] == "describe_pad2_pressure_body_discovery_intent"
    assert result.metadata["intent_kind"] == "discovery_intent"
    assert result.metadata["discovery_concept"] == "Pad 2 pressure/body discovery"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2g_returns_read_only_pad2_grit_noise_discovery_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2G")

    assert result.command_key == "P2G"
    assert result.accepted is True
    assert result.reason == "supported_pad2_grit_noise_discovery_intent"
    assert result.label == "Pad 2 grit / noise discovery"
    assert result.behavior_family == "pad2-lane/grit-noise-discovery"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_grit_noise_discovery_intent"
    assert result.intent_kind == "discovery_intent"
    assert result.anchor_concept == ""
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
        "P2G: Pad 2 grit / noise discovery",
        "Read-only Pad 2 grit/noise discovery intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_grit_noise_discovery_intent",
        "Discovery concept: Pad 2 grit/noise discovery",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2g_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2G")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/grit-noise-discovery"
    assert result.metadata["lane_action"] == "describe_pad2_grit_noise_discovery_intent"
    assert result.metadata["intent_kind"] == "discovery_intent"
    assert result.metadata["discovery_concept"] == "Pad 2 grit/noise discovery"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2r_returns_read_only_pad2_profile_rotation_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2R")

    assert result.command_key == "P2R"
    assert result.accepted is True
    assert result.reason == "supported_pad2_profile_rotation_intent"
    assert result.label == "rotate Pad 2 through profiled secondary-lane engines"
    assert result.behavior_family == "pad2-lane/profile-rotation"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_profile_rotation_intent"
    assert result.intent_kind == "rotation_intent"
    assert result.anchor_concept == ""
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
        "P2R: rotate Pad 2 through profiled secondary-lane engines",
        "Read-only Pad 2 profile rotation intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_profile_rotation_intent",
        "Rotation concept: Pad 2 profiled secondary-lane engine rotation",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2r_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2R")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "rotation"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == "pad2-lane/profile-rotation"
    assert result.metadata["lane_action"] == "describe_pad2_profile_rotation_intent"
    assert result.metadata["intent_kind"] == "rotation_intent"
    assert (
        result.metadata["rotation_concept"]
        == "Pad 2 profiled secondary-lane engine rotation"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2x_returns_read_only_pad2_current_profile_safe_mutation_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2X")

    assert result.command_key == "P2X"
    assert result.accepted is True
    assert result.reason == "supported_pad2_current_profile_safe_mutation_intent"
    assert result.label == "safely mutate the currently loaded Pad 2 profile"
    assert result.behavior_family == "pad2-lane/current-profile-safe-mutation"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_current_profile_safe_mutation_intent"
    assert result.intent_kind == "mutation_intent"
    assert result.anchor_concept == ""
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
        "P2X: safely mutate the currently loaded Pad 2 profile",
        "Read-only Pad 2 current-profile safe mutation intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_current_profile_safe_mutation_intent",
        "Mutation concept: Pad 2 current-profile safe mutation",
        "Selected-profile dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2x_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2X")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == (
        "pad2-lane/current-profile-safe-mutation"
    )
    assert result.metadata["lane_action"] == (
        "describe_pad2_current_profile_safe_mutation_intent"
    )
    assert result.metadata["intent_kind"] == "mutation_intent"
    assert (
        result.metadata["mutation_concept"]
        == "Pad 2 current-profile safe mutation"
    )
    assert (
        result.metadata["selected_profile_dependency"]
        == "current_pad2_profile_state"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p2z_returns_read_only_pad2_current_profile_anchor_return_intent():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2Z")

    assert result.command_key == "P2Z"
    assert result.accepted is True
    assert result.reason == "supported_pad2_current_profile_anchor_return_intent"
    assert result.label == "return current Pad 2 profile to anchor"
    assert result.behavior_family == "pad2-lane/current-profile-anchor-return"
    assert result.target_pad == 2
    assert result.lane == "Pad 2 secondary lane"
    assert result.lane_action == "describe_pad2_current_profile_anchor_return_intent"
    assert result.intent_kind == "anchor_return_intent"
    assert result.anchor_concept == "Pad 2 current-profile anchor return"
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
        "P2Z: return current Pad 2 profile to anchor",
        "Read-only Pad 2 current-profile anchor return intent.",
        "Target pad: 2",
        "Lane: Pad 2 secondary lane",
        "Lane action: describe_pad2_current_profile_anchor_return_intent",
        "Anchor return concept: Pad 2 current-profile anchor return",
        "Selected-profile dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p2z_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2Z")

    assert result.metadata["source"] == "PAD2_COMMANDS"
    assert result.metadata["command_type"] == "anchor_return"
    assert result.metadata["target_pad"] == 2
    assert result.metadata["lane"] == "pad_2_secondary_lane"
    assert result.metadata["behavior_family"] == (
        "pad2-lane/current-profile-anchor-return"
    )
    assert result.metadata["lane_action"] == (
        "describe_pad2_current_profile_anchor_return_intent"
    )
    assert result.metadata["intent_kind"] == "anchor_return_intent"
    assert (
        result.metadata["anchor_return_concept"]
        == "Pad 2 current-profile anchor return"
    )
    assert (
        result.metadata["selected_profile_dependency"]
        == "current_pad2_profile_state"
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_pad2_lane_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("P2B")

    try:
        result.metadata["source"] = "changed"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")

    fresh_result = evaluate_pad2_lane_behavior("P2B")

    assert fresh_result.metadata["source"] == "PAD2_COMMANDS"
    assert fresh_result.metadata["anchor_concept"] == "Pad 2 BD Classic home anchor"


def test_deferred_packet_6_pad2_lane_keys_fail_safely():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    for command_key in ("P2M",):
        result = evaluate_pad2_lane_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "unsupported_pad2_lane_command"
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_pad_lane import evaluate_pad2_lane_behavior

    result = evaluate_pad2_lane_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_packet_1_p2m_menu_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("P2M")

    assert result.accepted is True
    assert result.reason == "supported_menu_status_behavior"
    assert result.label == "show Pad 2 snare / secondary percussion menu"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "P2B")

    assert result.returncode == 0
    assert "Command: P2B" in result.stdout
    assert "Label: load Pad 2 BD Classic rolling low percussion / home" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_pad_lane  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_packaging_uses_pyproject_not_legacy_setup():
    # WS-A introduced PEP 621 packaging. The project ships pyproject.toml as the
    # single source of packaging truth; legacy setup.py / setup.cfg must not be used.
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for legacy in ("setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / legacy).exists()


def test_behavior_pad2_lane_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_pad_lane as behavior_pad2_lane

    exposed_names = set(dir(behavior_pad2_lane))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_pad_lane as behavior_pad2_lane

    module_text = "\n".join(
        [
            behavior_pad2_lane.__doc__ or "",
            behavior_pad2_lane.evaluate_pad2_lane_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_pad2_lane_prints_nothing()
    test_p2b_returns_read_only_pad2_home_anchor_intent()
    test_p2b_metadata_contains_expected_passive_sources()
    test_p2h_returns_read_only_pad2_sd_hard_anchor_intent()
    test_p2h_metadata_contains_expected_passive_sources()
    test_p2c_returns_read_only_pad2_sd_classic_anchor_intent()
    test_p2c_metadata_contains_expected_passive_sources()
    test_p2f_returns_read_only_pad2_sd_fm_anchor_intent()
    test_p2f_metadata_contains_expected_passive_sources()
    test_p2t_returns_read_only_pad2_tone_snap_discovery_intent()
    test_p2t_metadata_contains_expected_passive_sources()
    test_p2p_returns_read_only_pad2_pressure_body_discovery_intent()
    test_p2p_metadata_contains_expected_passive_sources()
    test_p2g_returns_read_only_pad2_grit_noise_discovery_intent()
    test_p2g_metadata_contains_expected_passive_sources()
    test_p2r_returns_read_only_pad2_profile_rotation_intent()
    test_p2r_metadata_contains_expected_passive_sources()
    test_p2x_returns_read_only_pad2_current_profile_safe_mutation_intent()
    test_p2x_metadata_contains_expected_passive_sources()
    test_p2z_returns_read_only_pad2_current_profile_anchor_return_intent()
    test_p2z_metadata_contains_expected_passive_sources()
    test_pad2_lane_metadata_is_copied_and_immutable()
    test_deferred_packet_6_pad2_lane_keys_fail_safely()
    test_unknown_keys_fail_safely()
    test_packet_1_p2m_menu_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_packaging_uses_pyproject_not_legacy_setup()
    test_behavior_pad2_lane_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
