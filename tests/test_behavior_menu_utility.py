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


PACKET_1A_KEYS = (
    "BD",
    "FM",
    "PD",
    "SM",
    "P2M",
    "J",
    "GM",
    "SCN",
    "PR",
    "SR",
    "P3M",
    "P4M",
    "H",
    "R",
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_menu_utility_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior.menu_utility"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_packet_1a_supported_keys_return_read_only_results():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    for command_key in PACKET_1A_KEYS:
        result = evaluate_menu_utility_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "menu/status"
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_bd_returns_menu_status_behavior_result():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("BD")

    assert result.accepted is True
    assert result.label == "show BD engine tools"
    assert result.display_lines == (
        "BD: show BD engine tools",
        "Read-only menu/status behavior.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )
    assert result.metadata["source"] == "MENU_COMMANDS"
    assert result.metadata["mock_only"] is True


def test_j_returns_group_layout_display_without_group_mutation():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("J")

    assert result.accepted is True
    assert result.metadata["scope"] == "four_pad_group_display"
    assert result.metadata["executes_group_mutation"] is False
    assert result.state_changed is False
    assert result.sends_real_midi is False


def test_scn_returns_scene_menu_without_scene_execution():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("SCN")

    assert result.accepted is True
    assert result.metadata["scope"] == "scene_menu_display"
    assert result.metadata["executes_scene"] is False
    assert result.state_changed is False
    assert result.sends_real_midi is False


def test_h_and_r_report_state_intent_without_runtime_state_mutation():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    expected_scopes = {
        "H": "current_anchor_report",
        "R": "script_state_report",
    }

    for command_key, scope in expected_scopes.items():
        result = evaluate_menu_utility_behavior(command_key)

        assert result.accepted is True
        assert result.metadata["scope"] == scope
        assert result.metadata["mutates_runtime_state"] is False
        assert result.state_changed is False


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_t_c_and_q_return_utility_session_intent_and_remain_safe():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    for command_key in ("T", "C", "Q"):
        result = evaluate_menu_utility_behavior(command_key)

        assert result.accepted is True
        assert result.reason == "supported_utility_session_intent"
        assert result.command_key == command_key
        assert result.prompt_required is False
        assert result.state_changed is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False


def test_t_returns_target_selection_intent_without_prompt_or_state_change():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("T")

    assert result.behavior_family == "utility/session"
    assert result.label == "select target pad/channel"
    assert result.metadata["source"] == "UTILITY_COMMANDS"
    assert result.metadata["scope"] == "target_selection_intent"
    assert result.metadata["future_prompt"] == "target_pad_channel_selection"
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["mock_only"] is True
    assert result.display_lines == (
        "T: select target pad/channel",
        "Read-only utility/session intent.",
        "No prompt would run.",
        "No state would change.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )


def test_c_returns_channel_selection_intent_without_ports_or_state_change():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("C")

    assert result.behavior_family == "utility/session"
    assert result.label == "change MIDI channel"
    assert result.metadata["source"] == "UTILITY_COMMANDS"
    assert result.metadata["scope"] == "midi_channel_selection_intent"
    assert result.metadata["future_prompt"] == "midi_channel_selection"
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["mock_only"] is True
    assert result.display_lines == (
        "C: change MIDI channel",
        "Read-only utility/session intent.",
        "No prompt would run.",
        "No state would change.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )


def test_q_returns_session_exit_intent_without_process_exit():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("Q")

    assert result.behavior_family == "utility/session"
    assert result.label == "quit"
    assert result.metadata["source"] == "UTILITY_COMMANDS"
    assert result.metadata["scope"] == "session_exit_intent"
    assert result.metadata["would_exit_loop"] is True
    assert result.metadata["exits_process"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["mock_only"] is True
    assert result.display_lines == (
        "Q: quit",
        "Read-only utility/session intent.",
        "No prompt would run.",
        "No process would exit.",
        "No state would change.",
        "No MIDI would be sent.",
    )


def test_result_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior.menu_utility import MenuUtilityBehaviorResult

    metadata = {"source": "test"}
    result = MenuUtilityBehaviorResult(command_key="X", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("list-commands")

    assert result.returncode == 0
    assert "- BD: show BD engine tools" in result.stdout
    assert "- SCN: show scene / preset tools" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior.menu_utility  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_behavior_menu_utility_exposes_no_active_command_names():
    import rytm_randomizer.behavior.menu_utility as behavior_menu_utility

    exposed_names = set(dir(behavior_menu_utility))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


if __name__ == "__main__":
    test_importing_behavior_menu_utility_prints_nothing()
    test_packet_1a_supported_keys_return_read_only_results()
    test_bd_returns_menu_status_behavior_result()
    test_j_returns_group_layout_display_without_group_mutation()
    test_scn_returns_scene_menu_without_scene_execution()
    test_h_and_r_report_state_intent_without_runtime_state_mutation()
    test_unknown_keys_fail_safely()
    test_t_c_and_q_return_utility_session_intent_and_remain_safe()
    test_t_returns_target_selection_intent_without_prompt_or_state_change()
    test_c_returns_channel_selection_intent_without_ports_or_state_change()
    test_q_returns_session_exit_intent_without_process_exit()
    test_result_metadata_is_copied_and_immutable()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_behavior_menu_utility_exposes_no_active_command_names()
