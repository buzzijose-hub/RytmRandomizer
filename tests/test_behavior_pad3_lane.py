import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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


def test_importing_behavior_pad3_lane_prints_nothing():
    code = "import rytm_randomizer.behavior.pad_lane"
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


def test_p3a_returns_read_only_pad3_sy_raw_home_anchor_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3A")

    assert result.command_key == "P3A"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_mid_bass_home_anchor_intent"
    assert result.label == "return Pad 3 to SY Raw Mid Bass anchor / home"
    assert result.behavior_family == "pad3-lane/sy-raw-mid-bass-home-anchor"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "return_pad3_sy_raw_mid_bass_home_anchor"
    assert result.intent_kind == "anchor_return"
    assert result.anchor_concept == "Pad 3 SY Raw Mid Bass home anchor"
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
        "P3A: return Pad 3 to SY Raw Mid Bass anchor / home",
        "Read-only Pad 3 SY Raw Mid Bass home anchor intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: return_pad3_sy_raw_mid_bass_home_anchor",
        "Pad 3 SY Raw Mid Bass home anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p3a_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3A")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "anchor_return"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-mid-bass-home-anchor"
    assert result.metadata["lane_action"] == "return_pad3_sy_raw_mid_bass_home_anchor"
    assert result.metadata["intent_kind"] == "anchor_return"
    assert result.metadata["anchor_concept"] == "Pad 3 SY Raw Mid Bass home anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_sa_returns_read_only_pad3_sy_raw_anchor_return_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SA")

    assert result.command_key == "SA"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_anchor_return_intent"
    assert result.label == "return Pad 3 SY Raw to anchor"
    assert result.behavior_family == "pad3-lane/sy-raw-anchor-return"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "return_pad3_sy_raw_anchor"
    assert result.intent_kind == "anchor_return"
    assert result.anchor_concept == "Pad 3 SY Raw anchor"
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
        "SA: return Pad 3 SY Raw to anchor",
        "Read-only Pad 3 SY Raw anchor return intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: return_pad3_sy_raw_anchor",
        "Pad 3 SY Raw anchor dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_sa_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SA")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "anchor_return"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-anchor-return"
    assert result.metadata["lane_action"] == "return_pad3_sy_raw_anchor"
    assert result.metadata["intent_kind"] == "anchor_return"
    assert result.metadata["anchor_concept"] == "Pad 3 SY Raw anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_sl_returns_read_only_pad3_sy_raw_lp1_bassline_mode_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SL")

    assert result.command_key == "SL"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_lp1_bassline_mode_intent"
    assert result.label == "Pad 3 SY Raw LP1 bassline mode"
    assert result.behavior_family == "pad3-lane/sy-raw-lp1-bassline-mode"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "load_pad3_sy_raw_lp1_bassline_mode"
    assert result.intent_kind == "mode_load"
    assert result.mode_concept == "Pad 3 SY Raw LP1 bassline mode"
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
        "SL: Pad 3 SY Raw LP1 bassline mode",
        "Read-only Pad 3 SY Raw LP1 bassline mode-load intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: load_pad3_sy_raw_lp1_bassline_mode",
        "Pad 3 SY Raw LP1 bassline mode dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_sl_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SL")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-lp1-bassline-mode"
    assert result.metadata["lane_action"] == "load_pad3_sy_raw_lp1_bassline_mode"
    assert result.metadata["intent_kind"] == "mode_load"
    assert result.metadata["mode_concept"] == "Pad 3 SY Raw LP1 bassline mode"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_sb_returns_read_only_pad3_sy_raw_bandpass_mid_bass_mode_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SB")

    assert result.command_key == "SB"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_bandpass_mid_bass_mode_intent"
    assert result.label == "Pad 3 SY Raw Bandpass mid-bass mode"
    assert result.behavior_family == "pad3-lane/sy-raw-bandpass-mid-bass-mode"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "load_pad3_sy_raw_bandpass_mid_bass_mode"
    assert result.intent_kind == "mode_load"
    assert result.mode_concept == "Pad 3 SY Raw Bandpass mid-bass mode"
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
        "SB: Pad 3 SY Raw Bandpass mid-bass mode",
        "Read-only Pad 3 SY Raw Bandpass mid-bass mode-load intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: load_pad3_sy_raw_bandpass_mid_bass_mode",
        "Pad 3 SY Raw Bandpass mid-bass mode dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_sb_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SB")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-bandpass-mid-bass-mode"
    assert result.metadata["lane_action"] == "load_pad3_sy_raw_bandpass_mid_bass_mode"
    assert result.metadata["intent_kind"] == "mode_load"
    assert result.metadata["mode_concept"] == "Pad 3 SY Raw Bandpass mid-bass mode"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_sx_returns_read_only_pad3_sy_raw_sci_fi_motion_accent_mode_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SX")

    assert result.command_key == "SX"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_sci_fi_motion_accent_mode_intent"
    assert result.label == "Pad 3 SY Raw sci-fi motion accent mode"
    assert result.behavior_family == "pad3-lane/sy-raw-sci-fi-motion-accent-mode"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "load_pad3_sy_raw_sci_fi_motion_accent_mode"
    assert result.intent_kind == "mode_load"
    assert result.mode_concept == "Pad 3 SY Raw sci-fi motion accent mode"
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
        "SX: Pad 3 SY Raw sci-fi motion accent mode",
        "Read-only Pad 3 SY Raw sci-fi motion accent mode-load intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: load_pad3_sy_raw_sci_fi_motion_accent_mode",
        "Pad 3 SY Raw sci-fi motion accent mode dependency is recorded only.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_sx_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SX")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "load"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-sci-fi-motion-accent-mode"
    assert result.metadata["lane_action"] == "load_pad3_sy_raw_sci_fi_motion_accent_mode"
    assert result.metadata["intent_kind"] == "mode_load"
    assert result.metadata["mode_concept"] == "Pad 3 SY Raw sci-fi motion accent mode"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_sw_returns_read_only_pad3_sy_raw_wave_balance_discovery_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SW")

    assert result.command_key == "SW"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_wave_balance_discovery_intent"
    assert result.label == "Pad 3 SY Raw Wave + Balance discovery"
    assert result.behavior_family == "pad3-lane/sy-raw-wave-balance-discovery"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "describe_pad3_sy_raw_wave_balance_discovery_intent"
    assert result.intent_kind == "discovery"
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
        "SW: Pad 3 SY Raw Wave + Balance discovery",
        "Read-only Pad 3 SY Raw Wave + Balance discovery intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: describe_pad3_sy_raw_wave_balance_discovery_intent",
        "Discovery concept: Pad 3 SY Raw Wave + Balance discovery",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_sw_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("SW")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-wave-balance-discovery"
    assert result.metadata["lane_action"] == "describe_pad3_sy_raw_wave_balance_discovery_intent"
    assert result.metadata["intent_kind"] == "discovery"
    assert result.metadata["discovery_concept"] == "Pad 3 SY Raw Wave + Balance discovery"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p3r_returns_read_only_pad3_sy_raw_mode_rotation_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3R")

    assert result.command_key == "P3R"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_mode_rotation_intent"
    assert result.label == "rotate Pad 3 through SY Raw behavior modes"
    assert result.behavior_family == "pad3-lane/sy-raw-mode-rotation"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "describe_pad3_sy_raw_mode_rotation_intent"
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
        "P3R: rotate Pad 3 through SY Raw behavior modes",
        "Read-only Pad 3 SY Raw behavior mode rotation intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: describe_pad3_sy_raw_mode_rotation_intent",
        "Rotation concept: Pad 3 SY Raw behavior mode rotation",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p3r_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3R")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "rotation"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-mode-rotation"
    assert result.metadata["lane_action"] == "describe_pad3_sy_raw_mode_rotation_intent"
    assert result.metadata["intent_kind"] == "rotation"
    assert result.metadata["rotation_concept"] == "Pad 3 SY Raw behavior mode rotation"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_p3x_returns_read_only_pad3_current_mode_safe_mutation_intent():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3X")

    assert result.command_key == "P3X"
    assert result.accepted is True
    assert result.reason == "supported_pad3_sy_raw_current_mode_safe_mutation_intent"
    assert result.label == "safely mutate the currently loaded Pad 3 mode"
    assert result.behavior_family == "pad3-lane/sy-raw-current-mode-safe-mutation"
    assert result.target_pad == 3
    assert result.lane == "Pad 3 SY Raw lane"
    assert result.lane_action == "describe_pad3_sy_raw_current_mode_safe_mutation_intent"
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
        "P3X: safely mutate the currently loaded Pad 3 mode",
        "Read-only Pad 3 SY Raw current mode safe mutation intent.",
        "Target pad: 3",
        "Lane: Pad 3 SY Raw lane",
        "Lane action: describe_pad3_sy_raw_current_mode_safe_mutation_intent",
        "Mutation concept: Pad 3 SY Raw current mode safe mutation",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No lane state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p3x_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3X")

    assert result.metadata["source"] == "PAD3_COMMANDS"
    assert result.metadata["command_type"] == "mutation"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["lane"] == "pad_3_sy_raw_lane"
    assert result.metadata["behavior_family"] == "pad3-lane/sy-raw-current-mode-safe-mutation"
    assert (
        result.metadata["lane_action"] == "describe_pad3_sy_raw_current_mode_safe_mutation_intent"
    )
    assert result.metadata["intent_kind"] == "mutation"
    assert result.metadata["mutation_concept"] == "Pad 3 SY Raw current mode safe mutation"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_pad3_lane_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("P3A")

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_pad3_lane_behavior("P3A")
    assert fresh_result.metadata["source"] == "PAD3_COMMANDS"

    sa_result = evaluate_pad3_lane_behavior("SA")

    try:
        sa_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_sa_result = evaluate_pad3_lane_behavior("SA")
    assert fresh_sa_result.metadata["source"] == "PAD3_COMMANDS"

    sl_result = evaluate_pad3_lane_behavior("SL")

    try:
        sl_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_sl_result = evaluate_pad3_lane_behavior("SL")
    assert fresh_sl_result.metadata["source"] == "PAD3_COMMANDS"

    sb_result = evaluate_pad3_lane_behavior("SB")

    try:
        sb_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_sb_result = evaluate_pad3_lane_behavior("SB")
    assert fresh_sb_result.metadata["source"] == "PAD3_COMMANDS"

    sx_result = evaluate_pad3_lane_behavior("SX")

    try:
        sx_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_sx_result = evaluate_pad3_lane_behavior("SX")
    assert fresh_sx_result.metadata["source"] == "PAD3_COMMANDS"

    sw_result = evaluate_pad3_lane_behavior("SW")

    try:
        sw_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_sw_result = evaluate_pad3_lane_behavior("SW")
    assert fresh_sw_result.metadata["source"] == "PAD3_COMMANDS"

    p3r_result = evaluate_pad3_lane_behavior("P3R")

    try:
        p3r_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_p3r_result = evaluate_pad3_lane_behavior("P3R")
    assert fresh_p3r_result.metadata["source"] == "PAD3_COMMANDS"

    p3x_result = evaluate_pad3_lane_behavior("P3X")

    try:
        p3x_result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_p3x_result = evaluate_pad3_lane_behavior("P3X")
    assert fresh_p3x_result.metadata["source"] == "PAD3_COMMANDS"


def test_deferred_packet_7_pad3_lane_keys_fail_safely():
    from rytm_randomizer.behavior.pad_lane import (
        DEFERRED_PACKET_7_PAD3_LANE_KEYS,
        evaluate_pad3_lane_behavior,
    )

    assert DEFERRED_PACKET_7_PAD3_LANE_KEYS == ("P3M",)

    for command_key in DEFERRED_PACKET_7_PAD3_LANE_KEYS:
        result = evaluate_pad3_lane_behavior(command_key)

        assert result.command_key == command_key
        assert result.accepted is False
        assert result.reason == "unsupported_packet_7_pad3_lane_key"
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
    from rytm_randomizer.behavior.pad_lane import evaluate_pad3_lane_behavior

    result = evaluate_pad3_lane_behavior("NOPE")

    assert result.command_key == "NOPE"
    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["source"] == "unknown"


def test_packet_1_p3m_menu_behavior_remains_unchanged():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("P3M")

    assert result.accepted is True
    assert result.reason == "supported_menu_status_behavior"
    assert result.label == "show Pad 3 SY Raw bass / synth-percussion menu"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "P3A")

    assert result.returncode == 0
    assert "Command: P3A" in result.stdout
    assert "Label: return Pad 3 to SY Raw Mid Bass anchor / home" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior.pad_lane  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_packaging_uses_pyproject_not_legacy_setup():
    # WS-A introduced PEP 621 packaging. The project ships pyproject.toml as the
    # single source of packaging truth; legacy setup.py / setup.cfg must not be used.
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for legacy in ("setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / legacy).exists()


def test_behavior_pad3_lane_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior.pad_lane as behavior_pad3_lane

    exposed_names = set(dir(behavior_pad3_lane))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior.pad_lane as behavior_pad3_lane

    module_text = "\n".join(
        [
            behavior_pad3_lane.__doc__ or "",
            behavior_pad3_lane.evaluate_pad3_lane_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_pad3_lane_prints_nothing()
    test_p3a_returns_read_only_pad3_sy_raw_home_anchor_intent()
    test_p3a_metadata_contains_expected_passive_sources()
    test_sa_returns_read_only_pad3_sy_raw_anchor_return_intent()
    test_sa_metadata_contains_expected_passive_sources()
    test_sl_returns_read_only_pad3_sy_raw_lp1_bassline_mode_intent()
    test_sl_metadata_contains_expected_passive_sources()
    test_sb_returns_read_only_pad3_sy_raw_bandpass_mid_bass_mode_intent()
    test_sb_metadata_contains_expected_passive_sources()
    test_sx_returns_read_only_pad3_sy_raw_sci_fi_motion_accent_mode_intent()
    test_sx_metadata_contains_expected_passive_sources()
    test_sw_returns_read_only_pad3_sy_raw_wave_balance_discovery_intent()
    test_sw_metadata_contains_expected_passive_sources()
    test_p3r_returns_read_only_pad3_sy_raw_mode_rotation_intent()
    test_p3r_metadata_contains_expected_passive_sources()
    test_p3x_returns_read_only_pad3_current_mode_safe_mutation_intent()
    test_p3x_metadata_contains_expected_passive_sources()
    test_pad3_lane_metadata_is_copied_and_immutable()
    test_deferred_packet_7_pad3_lane_keys_fail_safely()
    test_unknown_keys_fail_safely()
    test_packet_1_p3m_menu_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_packaging_uses_pyproject_not_legacy_setup()
    test_behavior_pad3_lane_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
