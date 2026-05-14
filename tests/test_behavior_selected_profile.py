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


def test_importing_behavior_selected_profile_prints_nothing():
    code = "import rytm_randomizer.behavior_selected_profile"
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


def test_p_returns_read_only_profile_selection_machine_change_intent():
    from rytm_randomizer.behavior_selected_profile import (
        evaluate_selected_profile_behavior,
    )

    result = evaluate_selected_profile_behavior("P")

    assert result.command_key == "P"
    assert result.accepted is True
    assert result.reason == "supported_profile_selection_machine_change_intent"
    assert result.label == "select/switch profile and change Rytm machine"
    assert result.behavior_family == "selected-profile-workflow/profile-selection"
    assert result.source_scope == "profile_machine"
    assert result.workflow_action == "describe_profile_selection_machine_change_intent"
    assert result.intent_kind == "profile_machine_selection"
    assert result.selects_profile is True
    assert result.machine_change_intent is True
    assert result.uses_selected_profile is False
    assert result.selected_profile_runtime_state_exists is False
    assert result.machine_change_executed is False
    assert result.anchor_load_executed is False
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
        "P: select/switch profile and change Rytm machine",
        "Read-only selected-profile workflow intent.",
        "Source scope: profile_machine",
        "Workflow action: describe_profile_selection_machine_change_intent",
        "Intent kind: profile_machine_selection",
        "Profile selection is described only.",
        "Machine change is described only.",
        "No selected-profile state would be created.",
        "No machine would change.",
        "No anchor would load.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_p_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_selected_profile import (
        evaluate_selected_profile_behavior,
    )

    result = evaluate_selected_profile_behavior("P")

    assert result.metadata["source"] == "PROFILE_WORKFLOW_COMMANDS"
    assert result.metadata["command_type"] == "selection"
    assert result.metadata["source_scope"] == "profile_machine"
    assert (
        result.metadata["behavior_family"]
        == "selected-profile-workflow/profile-selection"
    )
    assert (
        result.metadata["workflow_action"]
        == "describe_profile_selection_machine_change_intent"
    )
    assert result.metadata["intent_kind"] == "profile_machine_selection"
    assert result.metadata["selects_profile"] is True
    assert result.metadata["machine_change_intent"] is True
    assert result.metadata["uses_selected_profile"] is False
    assert result.metadata["selected_profile_runtime_state_exists"] is False
    assert result.metadata["machine_change_executed"] is False
    assert result.metadata["anchor_load_executed"] is False
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_selected_profile_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_selected_profile import (
        evaluate_selected_profile_behavior,
    )

    result = evaluate_selected_profile_behavior("P")

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_selected_profile_behavior("P")
    assert fresh_result.metadata["source"] == "PROFILE_WORKFLOW_COMMANDS"


def test_m_returns_read_only_selected_profile_anchor_load_intent():
    from rytm_randomizer.behavior_selected_profile import (
        DEFERRED_PACKET_10_SELECTED_PROFILE_KEYS,
        PACKET_10A_SELECTED_PROFILE_KEYS,
        PACKET_10B_SELECTED_PROFILE_KEYS,
        evaluate_selected_profile_behavior,
    )

    assert PACKET_10A_SELECTED_PROFILE_KEYS == ("P",)
    assert PACKET_10B_SELECTED_PROFILE_KEYS == ("M",)
    assert DEFERRED_PACKET_10_SELECTED_PROFILE_KEYS == ()

    result = evaluate_selected_profile_behavior("M")

    assert result.command_key == "M"
    assert result.accepted is True
    assert result.reason == "supported_selected_profile_anchor_load_intent"
    assert result.label == "load selected profile anchor"
    assert (
        result.behavior_family
        == "selected-profile-workflow/selected-profile-anchor-load"
    )
    assert result.source_scope == "selected_profile"
    assert result.workflow_action == "describe_selected_profile_anchor_load_intent"
    assert result.intent_kind == "selected_profile_anchor_load"
    assert result.selects_profile is False
    assert result.machine_change_intent is False
    assert result.uses_selected_profile is True
    assert result.selected_profile_dependency == "current_selected_profile_state"
    assert result.anchor_load_intent is True
    assert result.selected_profile_runtime_state_exists is False
    assert result.machine_change_executed is False
    assert result.anchor_load_executed is False
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
        "M: load selected profile anchor",
        "Read-only selected-profile anchor-load intent.",
        "Source scope: selected_profile",
        "Workflow action: describe_selected_profile_anchor_load_intent",
        "Intent kind: selected_profile_anchor_load",
        "Selected-profile dependency: current_selected_profile_state",
        "Selected-profile anchor load is described only.",
        "No selected-profile state would be read.",
        "No selected-profile state would be created.",
        "No anchor would load.",
        "No machine would change.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_m_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_selected_profile import (
        evaluate_selected_profile_behavior,
    )

    result = evaluate_selected_profile_behavior("M")

    assert result.metadata["source"] == "PROFILE_WORKFLOW_COMMANDS"
    assert result.metadata["command_type"] == "anchor_load"
    assert result.metadata["source_scope"] == "selected_profile"
    assert (
        result.metadata["behavior_family"]
        == "selected-profile-workflow/selected-profile-anchor-load"
    )
    assert (
        result.metadata["workflow_action"]
        == "describe_selected_profile_anchor_load_intent"
    )
    assert result.metadata["intent_kind"] == "selected_profile_anchor_load"
    assert result.metadata["selects_profile"] is False
    assert result.metadata["machine_change_intent"] is False
    assert result.metadata["uses_selected_profile"] is True
    assert (
        result.metadata["selected_profile_dependency"]
        == "current_selected_profile_state"
    )
    assert result.metadata["anchor_load_intent"] is True
    assert result.metadata["selected_profile_runtime_state_exists"] is False
    assert result.metadata["machine_change_executed"] is False
    assert result.metadata["anchor_load_executed"] is False
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_selected_profile import (
        evaluate_selected_profile_behavior,
    )

    result = evaluate_selected_profile_behavior("NOPE")

    assert result.command_key == "NOPE"
    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["source"] == "unknown"


def test_packet_2_anchor_profile_behavior_remains_unchanged():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BH")

    assert result.accepted is True
    assert result.reason == "supported_anchor_profile_intent"
    assert result.profile_key == "2"
    assert result.machine_value == 0
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_packet_3_legacy_single_profile_behavior_remains_unchanged():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    result = evaluate_mutation_depth_behavior("M1")

    assert result.accepted is True
    assert result.reason == "supported_legacy_single_profile_mutation_intent"
    assert result.scope == "selected_profile"
    assert result.uses_selected_profile is True
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_packet_9_undo_commit_state_behavior_remains_unchanged():
    from rytm_randomizer.behavior_undo_commit_state import (
        evaluate_undo_commit_state_behavior,
    )

    result = evaluate_undo_commit_state_behavior("B")

    assert result.accepted is True
    assert result.reason == "supported_current_anchor_return_intent"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "P")

    assert result.returncode == 0
    assert "Command: P" in result.stdout
    assert "Label: select/switch profile and change Rytm machine" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_selected_profile  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_packaging_uses_pyproject_not_legacy_setup():
    # WS-A introduced PEP 621 packaging. The project ships pyproject.toml as the
    # single source of packaging truth; legacy setup.py / setup.cfg must not be used.
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for legacy in ("setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / legacy).exists()


def test_behavior_selected_profile_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_selected_profile as behavior_selected_profile

    exposed_names = set(dir(behavior_selected_profile))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_selected_profile as behavior_selected_profile

    module_text = "\n".join(
        [
            behavior_selected_profile.__doc__ or "",
            behavior_selected_profile.evaluate_selected_profile_behavior.__doc__
            or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_selected_profile_prints_nothing()
    test_p_returns_read_only_profile_selection_machine_change_intent()
    test_p_metadata_contains_expected_passive_sources()
    test_selected_profile_metadata_is_copied_and_immutable()
    test_m_returns_read_only_selected_profile_anchor_load_intent()
    test_m_metadata_contains_expected_passive_sources()
    test_unknown_keys_fail_safely()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_packet_3_legacy_single_profile_behavior_remains_unchanged()
    test_packet_9_undo_commit_state_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_packaging_uses_pyproject_not_legacy_setup()
    test_behavior_selected_profile_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
