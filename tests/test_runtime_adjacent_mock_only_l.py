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


def assert_l_intent_is_inert(result):
    assert result.command_key == "L"
    assert result.accepted is True
    assert result.reason == "supported_selected_isolated_pad_target_intent"
    assert result.intent_kind == "selected_isolated_pad_target_selection"
    assert result.target_pad == 3
    assert result.selects_isolated_pad is True
    assert result.anchor_return_intent is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.selected_pad_switch_executed is False
    assert result.anchor_return_executed is False
    assert result.state_changed is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["mock_only"] is True
    assert result.metadata["target_pad"] == 3
    assert result.metadata["selected_pad_switch_executed"] is False
    assert result.metadata["selected_isolated_pad_runtime_state_exists"] is False
    assert result.metadata["dispatches_command"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False


def assert_selected_target_context_fails_safely(target_state, *, reason):
    assert target_state.supported is False
    assert target_state.valid is False
    assert target_state.reason == reason
    assert target_state.safe_failure_code == reason
    assert target_state.selected_pad_switch_executed is False
    assert target_state.selected_isolated_pad_runtime_state_exists is False
    assert target_state.state_changed is False
    assert target_state.dispatches_command is False
    assert target_state.executes_command is False
    assert target_state.mutates_runtime_state is False
    assert target_state.sends_real_midi is False
    assert target_state.opens_ports is False
    assert target_state.hardware_required is False
    assert target_state.active_behavior is False
    assert target_state.metadata["mock_only"] is True
    assert target_state.metadata["selected_pad_switch_executed"] is False
    assert target_state.metadata["selected_isolated_pad_runtime_state_exists"] is False
    assert target_state.metadata["dispatches_command"] is False
    assert target_state.metadata["mutates_runtime_state"] is False
    assert target_state.metadata["sends_real_midi"] is False
    assert target_state.metadata["opens_ports"] is False
    assert target_state.metadata["hardware_required"] is False
    assert target_state.metadata["active_behavior"] is False


def test_importing_runtime_adjacent_l_modules_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import rytm_randomizer.behavior_selected_isolated_pad; "
                "import rytm_randomizer.selected_target_state; "
                "import rytm_randomizer.selected_isolated_pad_runtime_state; "
                "import rytm_randomizer.mock_midi"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_l_target_intent_defaults_to_pad_3_without_switching_pads():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = evaluate_selected_isolated_pad_behavior("L")

    assert_l_intent_is_inert(result)
    assert "No selected pad switch would execute." in result.display_lines
    assert "No MIDI would be sent." in result.display_lines
    assert sender.sent_messages == ()


def test_unset_unsupported_stale_and_invalid_l_target_contexts_fail_safely():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.selected_target_state import (
        build_invalid_selected_target_state,
        build_stale_selected_target_state,
        build_unsupported_selected_target_state,
        build_unset_selected_target_state,
    )

    sender = MockMidiSender()
    cases = (
        (build_unset_selected_target_state(), "selected_target_unset"),
        (
            build_unsupported_selected_target_state(target_pad=5, command_key="L"),
            "unsupported_selected_target",
        ),
        (
            build_stale_selected_target_state(target_pad=3, command_key="L"),
            "stale_selected_target",
        ),
        (
            build_invalid_selected_target_state(
                target_pad=None,
                reason="invalid_selected_target",
            ),
            "invalid_selected_target",
        ),
    )

    for selected_target, reason in cases:
        assert_selected_target_context_fails_safely(selected_target, reason=reason)

    assert sender.sent_messages == ()


def test_runtime_adjacent_l_checks_are_deterministic_and_copy_safe():
    from rytm_randomizer.behavior_selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.selected_target_state import (
        build_default_selected_target_state,
    )

    first = evaluate_selected_isolated_pad_behavior("L")
    second = evaluate_selected_isolated_pad_behavior("L")
    first_target = build_default_selected_target_state()
    second_target = build_default_selected_target_state()

    assert first == second
    assert first_target == second_target

    try:
        first.metadata["target_pad"] = 99
    except TypeError:
        pass

    try:
        first_target.metadata["target_pad"] = 99
    except TypeError:
        pass

    fresh_intent = evaluate_selected_isolated_pad_behavior("L")
    fresh_target = build_default_selected_target_state()
    assert fresh_intent.metadata["target_pad"] == 3
    assert fresh_target.metadata["target_pad"] == 3


def test_passive_cli_preview_l_remains_read_only():
    result = run_cli("preview-command", "L")

    assert result.returncode == 0
    assert "Command: L" in result.stdout
    assert "No MIDI would be sent." in result.stdout
    assert "No hardware would be mutated." in result.stdout
    assert result.stderr == ""


def test_runtime_adjacent_l_imports_no_real_midi_and_exposes_no_active_names():
    import rytm_randomizer.behavior_selected_isolated_pad as selected_behavior
    import rytm_randomizer.mock_midi  # noqa: F401
    import rytm_randomizer.selected_target_state as selected_target_state

    exposed_names = set(dir(selected_behavior)) | set(selected_target_state.__all__)

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules
    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "execute_l" not in exposed_names
    assert "switch_selected_pad" not in exposed_names
    assert "open_port" not in exposed_names
    assert "send_midi" not in exposed_names


def test_closeout_includes_runtime_adjacent_l_label():
    closeout_text = (PROJECT_ROOT / "Scripts" / "closeout_check.ps1").read_text()

    assert "=== Test: Runtime-Adjacent Mock-Only L ===" in closeout_text
    assert "test_runtime_adjacent_mock_only_l.py" in closeout_text


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
