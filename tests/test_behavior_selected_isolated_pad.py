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


def test_importing_behavior_selected_isolated_pad_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_selected_isolated_pad"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_l_returns_read_only_selected_isolated_pad_target_intent():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS,
        PACKET_11A_SELECTED_ISOLATED_PAD_KEYS,
        PACKET_11B_SELECTED_ISOLATED_PAD_KEYS,
        SUPPORTED_SELECTED_ISOLATED_PAD_KEYS,
        evaluate_selected_isolated_pad_behavior,
    )

    assert PACKET_11A_SELECTED_ISOLATED_PAD_KEYS == ("L",)
    assert PACKET_11B_SELECTED_ISOLATED_PAD_KEYS == ("PZ",)
    assert DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS == ()
    assert SUPPORTED_SELECTED_ISOLATED_PAD_KEYS == ("L", "PZ")

    result = evaluate_selected_isolated_pad_behavior("L")

    assert result.command_key == "L"
    assert result.accepted is True
    assert result.reason == "supported_selected_isolated_pad_target_intent"
    assert result.label == "select isolated single-pad mutation target, default Pad 3"
    assert result.behavior_family == "selected-isolated-pad/target-selection"
    assert result.source_scope == "isolated_pad_target"
    assert result.utility_action == "describe_selected_isolated_pad_target_intent"
    assert result.intent_kind == "selected_isolated_pad_target_selection"
    assert result.default_pad == 3
    assert result.target_pad == 3
    assert result.selects_isolated_pad is True
    assert result.anchor_return_intent is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.selected_pad_switch_executed is False
    assert result.anchor_return_executed is False
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
        "L: select isolated single-pad mutation target, default Pad 3",
        "Read-only selected isolated pad target intent.",
        "Source scope: isolated_pad_target",
        "Utility action: describe_selected_isolated_pad_target_intent",
        "Intent kind: selected_isolated_pad_target_selection",
        "Default target pad: 3",
        "Selected isolated pad target is described only.",
        "No selected isolated pad state would be created.",
        "No selected pad switch would execute.",
        "No anchor would return.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No runtime state would mutate.",
        "No MIDI would be sent.",
        "No ports would be opened.",
        "No hardware would be required.",
    )


def test_l_metadata_contains_expected_passive_sources():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    result = evaluate_selected_isolated_pad_behavior("L")

    assert result.metadata["source"] == "ISOLATED_PAD_UTILITY_COMMANDS"
    assert result.metadata["command_type"] == "selection"
    assert result.metadata["source_scope"] == "isolated_pad_target"
    assert (
        result.metadata["behavior_family"]
        == "selected-isolated-pad/target-selection"
    )
    assert (
        result.metadata["utility_action"]
        == "describe_selected_isolated_pad_target_intent"
    )
    assert result.metadata["intent_kind"] == "selected_isolated_pad_target_selection"
    assert result.metadata["default_pad"] == 3
    assert result.metadata["target_pad"] == 3
    assert result.metadata["selects_isolated_pad"] is True
    assert result.metadata["anchor_return_intent"] is False
    assert result.metadata["selected_isolated_pad_runtime_state_exists"] is False
    assert result.metadata["selected_pad_switch_executed"] is False
    assert result.metadata["anchor_return_executed"] is False
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["dispatches_command"] is False


def test_selected_isolated_pad_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    result = evaluate_selected_isolated_pad_behavior("L")

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_selected_isolated_pad_behavior("L")
    assert fresh_result.metadata["source"] == "ISOLATED_PAD_UTILITY_COMMANDS"


def test_repeated_selected_isolated_pad_evaluations_are_deterministic():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    assert evaluate_selected_isolated_pad_behavior("L") == (
        evaluate_selected_isolated_pad_behavior("L")
    )
    assert evaluate_selected_isolated_pad_behavior("PZ") == (
        evaluate_selected_isolated_pad_behavior("PZ")
    )


def test_pz_reports_read_only_anchor_return_readiness_for_default_context():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    result = evaluate_selected_isolated_pad_behavior("PZ")

    assert result.command_key == "PZ"
    assert result.accepted is False
    assert result.reason == "anchor_unavailable_for_selected_target"
    assert result.label == "return selected isolated pad to anchor only"
    assert result.behavior_family == "selected-isolated-pad/anchor-return-readiness"
    assert result.source_scope == "selected_isolated_pad"
    assert result.utility_action == "describe_selected_isolated_pad_anchor_return_readiness"
    assert result.intent_kind == "selected_isolated_pad_anchor_return_readiness"
    assert result.target_pad == 3
    assert result.anchor_return_intent is True
    assert result.anchor_return_executed is False
    assert result.selected_isolated_pad_runtime_state_exists is True
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["source"] == "ISOLATED_PAD_UTILITY_COMMANDS"
    assert result.metadata["behavior_family"] == (
        "selected-isolated-pad/anchor-return-readiness"
    )
    assert result.metadata["utility_action"] == (
        "describe_selected_isolated_pad_anchor_return_readiness"
    )
    assert result.metadata["intent_kind"] == (
        "selected_isolated_pad_anchor_return_readiness"
    )
    assert result.metadata["runtime_state_source"] == (
        "selected_isolated_pad_runtime_state"
    )
    assert result.metadata["runtime_state"] == "passive-default"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["target_state"] == "defaulted"
    assert result.metadata["target_anchor_status"] == "anchor-unavailable"
    assert result.metadata["anchor_state"] == "unknown"
    assert result.metadata["reason"] == "anchor_unavailable_for_selected_target"
    assert result.metadata["safe_failure_code"] == (
        "anchor_unavailable_for_selected_target"
    )
    assert result.metadata["pz_ready"] is False
    assert result.metadata["pz_executed"] is False
    assert result.metadata["anchor_return_intent"] is True
    assert result.metadata["anchor_return_executed"] is False
    assert result.metadata["mock_only"] is True


def test_pz_consumes_injected_runtime_state_without_mutating_it():
    from rytm_randomizer.anchor_state import build_unknown_anchor_state
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_missing_selected_target_runtime_state,
    )

    runtime_state = build_missing_selected_target_runtime_state(
        anchor_state=build_unknown_anchor_state()
    )
    result = evaluate_selected_isolated_pad_behavior("PZ", runtime_state=runtime_state)

    assert runtime_state.target_anchor_status == "target-missing"
    assert runtime_state.pz_executed is False
    assert runtime_state.state_changed is False
    assert result.accepted is False
    assert result.reason == "missing_selected_target_state"
    assert result.target_pad is None
    assert result.selected_isolated_pad_runtime_state_exists is True
    assert result.anchor_return_intent is True
    assert result.anchor_return_executed is False
    assert result.state_changed is False
    assert result.mutates_runtime_state is False
    assert result.dispatches_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.metadata["runtime_state"] == "invalid"
    assert result.metadata["target_anchor_status"] == "target-missing"
    assert result.metadata["safe_failure_code"] == "missing_selected_target_state"


def test_pz_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    result = evaluate_selected_isolated_pad_behavior("PZ")

    try:
        result.metadata["runtime_state"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_selected_isolated_pad_behavior("PZ")
    assert fresh_result.metadata["runtime_state"] == "passive-default"


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    result = evaluate_selected_isolated_pad_behavior("NOPE")

    assert result.command_key == "NOPE"
    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["source"] == "unknown"


def test_packet_1_selected_pad_status_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("PR")

    assert result.accepted is True
    assert result.reason == "supported_menu_status_behavior"
    assert result.label == "show selected isolated pad"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_packet_3_selected_isolated_pad_mutation_behavior_remains_unchanged():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    result = evaluate_mutation_depth_behavior("PM")

    assert result.accepted is True
    assert result.reason == "supported_selected_isolated_pad_mutation_intent"
    assert result.scope == "selected_isolated_pad"
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "L")

    assert result.returncode == 0
    assert "Command: L" in result.stdout
    assert "Label: select isolated single-pad mutation target, default Pad 3" in (
        result.stdout
    )
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_selected_isolated_pad  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_package_metadata_is_declared_without_legacy_setup_files():
    assert (PROJECT_ROOT / "pyproject.toml").exists()
    for filename in ("requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_selected_isolated_pad_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_selected_isolated_pad as behavior_selected_isolated_pad

    exposed_names = set(dir(behavior_selected_isolated_pad))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_selected_isolated_pad as behavior_selected_isolated_pad

    module_text = "\n".join(
        [
            behavior_selected_isolated_pad.__doc__ or "",
            behavior_selected_isolated_pad.evaluate_selected_isolated_pad_behavior.__doc__
            or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_selected_isolated_pad_prints_nothing()
    test_l_returns_read_only_selected_isolated_pad_target_intent()
    test_l_metadata_contains_expected_passive_sources()
    test_selected_isolated_pad_metadata_is_copied_and_immutable()
    test_repeated_selected_isolated_pad_evaluations_are_deterministic()
    test_pz_reports_read_only_anchor_return_readiness_for_default_context()
    test_pz_consumes_injected_runtime_state_without_mutating_it()
    test_pz_metadata_is_copied_and_immutable()
    test_unknown_keys_fail_safely()
    test_packet_1_selected_pad_status_behavior_remains_unchanged()
    test_packet_3_selected_isolated_pad_mutation_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_package_metadata_is_declared_without_legacy_setup_files()
    test_behavior_selected_isolated_pad_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
