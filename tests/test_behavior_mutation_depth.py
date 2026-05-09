from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


GUARDED_DEPTH_KEYS = ("1", "2", "3")
DEFERRED_PACKET_3_KEYS = (
    "M1",
    "M2",
    "M3",
    "S",
    "F",
    "A",
    "G",
    "K",
    "PM",
    "PS",
    "PF",
    "PA",
    "PL",
    "PO",
    "PB",
    "PG",
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_importing_behavior_mutation_depth_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.behavior_mutation_depth"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_guarded_numeric_inputs_return_read_only_results():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    for command_key in GUARDED_DEPTH_KEYS:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is True
        assert result.command_key == command_key
        assert result.behavior_family == "mutation-depth/guarded-input"
        assert result.depth_value == int(command_key)
        assert result.guarded_input is True
        assert result.requires_depth_prompt_context is True
        assert result.prompt_available is False
        assert result.state_changed is False
        assert result.prompt_required is False
        assert result.dispatches_command is False
        assert result.executes_command is False
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.display_lines


def test_guarded_numeric_input_1_has_expected_display_and_metadata():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    result = evaluate_mutation_depth_behavior("1")

    assert result.accepted is True
    assert result.label == "guarded depth input 1, requires lane/mode prefix"
    assert result.reason == "supported_guarded_depth_input"
    assert result.display_lines == (
        "1: guarded depth input 1, requires lane/mode prefix",
        "Read-only guarded numeric input intent.",
        "Depth value: 1",
        "Bare main-prompt use remains guarded.",
        "Valid only inside a future depth prompt context.",
        "No active depth prompt exists now.",
        "No prompt would run.",
        "No state would change.",
        "No command would dispatch.",
        "No command would execute.",
        "No MIDI would be sent.",
        "No ports would be opened.",
    )
    assert result.metadata["source"] == "MAIN_PROMPT_DEPTH_GUARDRAIL"
    assert result.metadata["source_command_type"] == "guarded_depth"
    assert result.metadata["depth_prompt_context"] == (
        "Use a command that asks for depth before entering 1, 2, or 3."
    )
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["mutates_runtime_state"] is False


def test_repeated_mutation_depth_evaluations_are_deterministic():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    for command_key in GUARDED_DEPTH_KEYS:
        assert evaluate_mutation_depth_behavior(command_key) == (
            evaluate_mutation_depth_behavior(command_key)
        )


def test_mutation_depth_metadata_is_copied_and_immutable():
    from rytm_randomizer.behavior_mutation_depth import MutationDepthBehaviorResult

    metadata = {"source": "test"}
    result = MutationDepthBehaviorResult(command_key="1", metadata=metadata)

    metadata["source"] = "changed"

    assert result.metadata["source"] == "test"

    try:
        result.metadata["source"] = "mutated"
    except TypeError:
        pass
    else:
        raise AssertionError("metadata should be immutable")


def test_unknown_keys_fail_safely():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    result = evaluate_mutation_depth_behavior("DOES_NOT_EXIST")

    assert result.accepted is False
    assert result.reason == "unknown_command"
    assert result.display_lines == ()
    assert result.depth_value is None
    assert result.guarded_input is False
    assert result.requires_depth_prompt_context is False
    assert result.prompt_available is False
    assert result.state_changed is False
    assert result.prompt_required is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False


def test_deferred_packet_3_keys_fail_safely():
    from rytm_randomizer.behavior_mutation_depth import (
        evaluate_mutation_depth_behavior,
    )

    for command_key in DEFERRED_PACKET_3_KEYS:
        result = evaluate_mutation_depth_behavior(command_key)

        assert result.accepted is False
        assert result.reason == "deferred_mutation_depth_command"
        assert result.sends_real_midi is False
        assert result.opens_ports is False
        assert result.hardware_required is False
        assert result.active_behavior is False
        assert result.metadata["source"] == "COMMANDS"


def test_packet_1_menu_utility_behavior_remains_unchanged():
    from rytm_randomizer.behavior_menu_utility import evaluate_menu_utility_behavior

    result = evaluate_menu_utility_behavior("BD")

    assert result.accepted is True
    assert result.label == "show BD engine tools"
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_packet_2_anchor_profile_behavior_remains_unchanged():
    from rytm_randomizer.behavior_anchor_profile import (
        evaluate_anchor_profile_behavior,
    )

    result = evaluate_anchor_profile_behavior("BH")

    assert result.accepted is True
    assert result.label == "load Pad 1 BD Hard anchor, primary default"
    assert result.profile_key == "2"
    assert result.machine_value == 0
    assert result.sends_real_midi is False
    assert result.active_behavior is False


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "1")

    assert result.returncode == 0
    assert "Command: 1" in result.stdout
    assert "Label: guarded depth input 1, requires lane/mode prefix" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.behavior_mutation_depth  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_package_metadata_files_are_introduced():
    for filename in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg"):
        assert not (PROJECT_ROOT / filename).exists()


def test_behavior_mutation_depth_exposes_no_active_behavior_names():
    import rytm_randomizer.behavior_mutation_depth as behavior_mutation_depth

    exposed_names = set(dir(behavior_mutation_depth))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.behavior_mutation_depth as behavior_mutation_depth

    module_text = "\n".join(
        [
            behavior_mutation_depth.__doc__ or "",
            behavior_mutation_depth.evaluate_mutation_depth_behavior.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


if __name__ == "__main__":
    test_importing_behavior_mutation_depth_prints_nothing()
    test_guarded_numeric_inputs_return_read_only_results()
    test_guarded_numeric_input_1_has_expected_display_and_metadata()
    test_repeated_mutation_depth_evaluations_are_deterministic()
    test_mutation_depth_metadata_is_copied_and_immutable()
    test_unknown_keys_fail_safely()
    test_deferred_packet_3_keys_fail_safely()
    test_packet_1_menu_utility_behavior_remains_unchanged()
    test_packet_2_anchor_profile_behavior_remains_unchanged()
    test_passive_cli_behavior_remains_unchanged()
    test_no_real_midi_library_is_imported()
    test_no_package_metadata_files_are_introduced()
    test_behavior_mutation_depth_exposes_no_active_behavior_names()
    test_no_out_of_scope_support_is_exposed()
