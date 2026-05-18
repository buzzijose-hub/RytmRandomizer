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


def test_importing_behavior_undo_commit_state_prints_nothing():
    code = "import rytm_randomizer.behavior.undo_commit_state"
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


def test_b_returns_read_only_current_anchor_return_intent():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("B")

    assert result.command_key == "B"
    assert result.accepted is True
    assert result.reason == "supported_current_anchor_return_intent"
    assert result.label == "back to current anchor"
    assert result.behavior_family == "undo-commit-state/current-anchor-return"
    assert result.target_scope == "current_anchor"
    assert result.state_action == "describe_current_anchor_return_intent"
    assert result.intent_kind == "anchor_return"
    assert result.anchor_concept == "current anchor"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "B: back to current anchor",
        "Read-only current-anchor return intent.",
        "Target scope: current_anchor",
        "State action: describe_current_anchor_return_intent",
        "Anchor concept: current anchor",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_b_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("B")

    assert result.metadata["source"] == "STATE_UTILITY_COMMANDS"
    assert result.metadata["command_type"] == "anchor_state"
    assert result.metadata["target_scope"] == "current_anchor"
    assert result.metadata["behavior_family"] == "undo-commit-state/current-anchor-return"
    assert result.metadata["state_action"] == "describe_current_anchor_return_intent"
    assert result.metadata["intent_kind"] == "anchor_return"
    assert result.metadata["anchor_concept"] == "current anchor"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_e_returns_read_only_current_state_anchor_commit_intent():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("E")

    assert result.command_key == "E"
    assert result.accepted is True
    assert result.reason == "supported_current_state_anchor_commit_intent"
    assert result.label == "commit current state as new anchor"
    assert result.behavior_family == "undo-commit-state/current-state-anchor-commit"
    assert result.target_scope == "current_anchor_state"
    assert result.state_action == "describe_current_state_anchor_commit_intent"
    assert result.intent_kind == "anchor_commit"
    assert result.anchor_concept == "current state as new anchor"
    assert result.lifecycle_effect == "described_only"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "E: commit current state as new anchor",
        "Read-only current-state anchor commit intent.",
        "Target scope: current_anchor_state",
        "State action: describe_current_state_anchor_commit_intent",
        "Anchor concept: current state as new anchor",
        "Lifecycle effect: described_only",
        "No prompt would run.",
        "No state would change.",
        "No anchor would be committed.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_e_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("E")

    assert result.metadata["source"] == "STATE_UTILITY_COMMANDS"
    assert result.metadata["command_type"] == "anchor_state"
    assert result.metadata["target_scope"] == "current_anchor_state"
    assert result.metadata["behavior_family"] == "undo-commit-state/current-state-anchor-commit"
    assert result.metadata["state_action"] == "describe_current_state_anchor_commit_intent"
    assert result.metadata["intent_kind"] == "anchor_commit"
    assert result.metadata["anchor_concept"] == "current state as new anchor"
    assert result.metadata["lifecycle_effect"] == "described_only"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_w_returns_read_only_waveform_exploration_intent():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("W")

    assert result.command_key == "W"
    assert result.accepted is True
    assert result.reason == "supported_waveform_exploration_intent"
    assert result.label == "waveform exploration only"
    assert result.behavior_family == "undo-commit-state/waveform-exploration"
    assert result.target_scope == "waveform_exploration"
    assert result.state_action == "describe_waveform_exploration_intent"
    assert result.intent_kind == "waveform_exploration"
    assert result.exploration_concept == "waveform exploration only"
    assert result.lifecycle_effect == "described_only"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "W: waveform exploration only",
        "Read-only waveform exploration intent.",
        "Target scope: waveform_exploration",
        "State action: describe_waveform_exploration_intent",
        "Exploration concept: waveform exploration only",
        "Lifecycle effect: described_only",
        "No prompt would run.",
        "No state would change.",
        "No waveform would be selected.",
        "No waveform would be randomized.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_w_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("W")

    assert result.metadata["source"] == "STATE_UTILITY_COMMANDS"
    assert result.metadata["command_type"] == "exploration"
    assert result.metadata["source_scope"] == "waveform"
    assert result.metadata["target_scope"] == "waveform_exploration"
    assert result.metadata["behavior_family"] == "undo-commit-state/waveform-exploration"
    assert result.metadata["state_action"] == "describe_waveform_exploration_intent"
    assert result.metadata["intent_kind"] == "waveform_exploration"
    assert result.metadata["exploration_concept"] == "waveform exploration only"
    assert result.metadata["lifecycle_effect"] == "described_only"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_u_returns_read_only_state_history_undo_intent():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("U")

    assert result.command_key == "U"
    assert result.accepted is True
    assert result.reason == "supported_state_history_undo_intent"
    assert result.label == "undo previous script-generated state"
    assert result.behavior_family == "undo-commit-state/script-generated-state-undo"
    assert result.target_scope == "script_generated_state_history"
    assert result.state_action == "describe_previous_script_generated_state_undo_intent"
    assert result.intent_kind == "state_history_undo"
    assert result.history_concept == "previous script-generated state"
    assert result.lifecycle_effect == "described_only"
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.display_lines == (
        "U: undo previous script-generated state",
        "Read-only previous script-generated state undo intent.",
        "Target scope: script_generated_state_history",
        "State action: describe_previous_script_generated_state_undo_intent",
        "History concept: previous script-generated state",
        "Lifecycle effect: described_only",
        "No prompt would run.",
        "No state would change.",
        "No undo stack would be inspected.",
        "No undo stack would be mutated.",
        "No undo would execute.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_u_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("U")

    assert result.metadata["source"] == "STATE_UTILITY_COMMANDS"
    assert result.metadata["command_type"] == "state_history"
    assert result.metadata["source_scope"] == "script_generated_state"
    assert result.metadata["target_scope"] == "script_generated_state_history"
    assert result.metadata["behavior_family"] == "undo-commit-state/script-generated-state-undo"
    assert result.metadata["state_action"] == "describe_previous_script_generated_state_undo_intent"
    assert result.metadata["intent_kind"] == "state_history_undo"
    assert result.metadata["history_concept"] == "previous script-generated state"
    assert result.metadata["lifecycle_effect"] == "described_only"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_undo_commit_state_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("B")

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_undo_commit_state_behavior("B")
    assert fresh_result.metadata["source"] == "STATE_UTILITY_COMMANDS"


def test_deferred_packet_9_undo_commit_state_keys_fail_safely():
    from rytm_randomizer.behavior.undo_commit_state import (
        DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS,
        PACKET_9B_UNDO_COMMIT_STATE_KEYS,
        PACKET_9C_UNDO_COMMIT_STATE_KEYS,
        PACKET_9D_UNDO_COMMIT_STATE_KEYS,
        evaluate_undo_commit_state_behavior,
    )

    assert PACKET_9B_UNDO_COMMIT_STATE_KEYS == ("E",)
    assert PACKET_9C_UNDO_COMMIT_STATE_KEYS == ("W",)
    assert PACKET_9D_UNDO_COMMIT_STATE_KEYS == ("U",)
    assert DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS == ()

    for command_key in DEFERRED_PACKET_9_UNDO_COMMIT_STATE_KEYS:
        result = evaluate_undo_commit_state_behavior(command_key)

        assert result.command_key == command_key
        assert result.accepted is False
        assert result.reason == "unsupported_packet_9_undo_commit_state_key"
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
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    result = evaluate_undo_commit_state_behavior("NOPE")

    assert result.command_key == "NOPE"
    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["source"] == "unknown"


def test_packet_1_h_and_r_menu_behavior_remain_unchanged():
    from rytm_randomizer.behavior.menu_utility import evaluate_menu_utility_behavior

    h_result = evaluate_menu_utility_behavior("H")
    r_result = evaluate_menu_utility_behavior("R")

    assert h_result.accepted is True
    assert h_result.reason == "supported_menu_status_behavior"
    assert h_result.label == "show current anchor"
    assert h_result.sends_real_midi is False
    assert h_result.opens_ports is False
    assert h_result.hardware_required is False

    assert r_result.accepted is True
    assert r_result.reason == "supported_menu_status_behavior"
    assert r_result.label == "print current script state"
    assert r_result.sends_real_midi is False
    assert r_result.opens_ports is False
    assert r_result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "B")

    assert result.returncode == 0
    assert "Command: B" in result.stdout
    assert "Label: back to current anchor" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior.undo_commit_state  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_packaging_uses_pyproject_not_legacy_setup():
    # WS-A introduced PEP 621 packaging. The project ships pyproject.toml as the
    # single source of packaging truth; legacy setup.py / setup.cfg must not be used.
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for legacy in ("setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / legacy).exists()


def test_behavior_undo_commit_state_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior.undo_commit_state as behavior_undo_commit_state

    exposed_names = set(dir(behavior_undo_commit_state))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior.undo_commit_state as behavior_undo_commit_state

    module_text = "\n".join(
        [
            behavior_undo_commit_state.__doc__ or "",
            behavior_undo_commit_state.evaluate_undo_commit_state_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_undo_commit_state_prints_nothing()
    test_b_returns_read_only_current_anchor_return_intent()
    test_b_metadata_contains_expected_passive_sources()
    test_e_returns_read_only_current_state_anchor_commit_intent()
    test_e_metadata_contains_expected_passive_sources()
    test_w_returns_read_only_waveform_exploration_intent()
    test_w_metadata_contains_expected_passive_sources()
    test_u_returns_read_only_state_history_undo_intent()
    test_u_metadata_contains_expected_passive_sources()
    test_undo_commit_state_metadata_is_copied_and_immutable()
    test_deferred_packet_9_undo_commit_state_keys_fail_safely()
    test_unknown_keys_fail_safely()
    test_packet_1_h_and_r_menu_behavior_remain_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_packaging_uses_pyproject_not_legacy_setup()
    test_behavior_undo_commit_state_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
