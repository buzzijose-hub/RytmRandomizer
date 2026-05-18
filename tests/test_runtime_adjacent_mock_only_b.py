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
        capture_output=True,
        text=True,
        check=False,
    )


def assert_b_intent_is_inert(result):
    assert result.command_key == "B"
    assert result.accepted is True
    assert result.reason == "supported_current_anchor_return_intent"
    assert result.intent_kind == "anchor_return"
    assert result.anchor_concept == "current anchor"
    assert result.state_changed is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["mock_only"] is True
    assert result.metadata["dispatches_command"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False


def assert_anchor_context_fails_safely(anchor_state, *, reason):
    if anchor_state.command_key:
        assert anchor_state.command_key == "B"
    assert anchor_state.supported is False
    assert anchor_state.valid is False
    assert anchor_state.reason == reason
    assert anchor_state.safe_failure_code == reason
    assert anchor_state.anchor_return_executed is False
    assert anchor_state.selected_pad_switch_executed is False
    assert anchor_state.state_changed is False
    assert anchor_state.dispatches_command is False
    assert anchor_state.executes_command is False
    assert anchor_state.mutates_runtime_state is False
    assert anchor_state.sends_real_midi is False
    assert anchor_state.opens_ports is False
    assert anchor_state.hardware_required is False
    assert anchor_state.active_behavior is False
    assert anchor_state.metadata["mock_only"] is True
    assert anchor_state.metadata["anchor_return_executed"] is False
    assert anchor_state.metadata["dispatches_command"] is False
    assert anchor_state.metadata["mutates_runtime_state"] is False
    assert anchor_state.metadata["sends_real_midi"] is False
    assert anchor_state.metadata["opens_ports"] is False
    assert anchor_state.metadata["hardware_required"] is False
    assert anchor_state.metadata["active_behavior"] is False


def test_importing_runtime_adjacent_b_modules_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import rytm_randomizer.behavior.undo_commit_state; "
                "import rytm_randomizer.state.anchor_validation; "
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


def test_b_current_anchor_context_defaults_to_safe_failure_without_mock_messages():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    intent = evaluate_undo_commit_state_behavior("B")
    anchor_context = build_unknown_anchor_state(command_key="B")

    assert_b_intent_is_inert(intent)
    assert_anchor_context_fails_safely(anchor_context, reason="anchor_unknown")
    assert anchor_context.anchor_state == "unknown"
    assert sender.sent_messages == ()


def test_unsupported_stale_and_invalid_b_anchor_contexts_fail_safely():
    from rytm_randomizer.state.anchor_validation import (
        build_invalid_anchor_state,
        build_stale_anchor_state,
        build_unsupported_anchor_state,
    )
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    intent = evaluate_undo_commit_state_behavior("B")
    cases = (
        (
            build_unsupported_anchor_state(
                anchor_pad=1,
                command_key="B",
                anchor_identity="current anchor",
            ),
            "unsupported_anchor",
        ),
        (
            build_stale_anchor_state(
                anchor_pad=1,
                command_key="B",
                anchor_identity="current anchor",
            ),
            "stale_anchor",
        ),
        (
            build_invalid_anchor_state(anchor_pad=1, reason="invalid_anchor"),
            "invalid_anchor",
        ),
    )

    assert_b_intent_is_inert(intent)

    for anchor_context, reason in cases:
        assert_anchor_context_fails_safely(anchor_context, reason=reason)

    assert sender.sent_messages == ()


def test_runtime_adjacent_b_checks_are_deterministic_and_copy_safe():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state
    from rytm_randomizer.behavior.undo_commit_state import evaluate_undo_commit_state_behavior

    first = evaluate_undo_commit_state_behavior("B")
    second = evaluate_undo_commit_state_behavior("B")
    first_anchor = build_unknown_anchor_state(command_key="B")
    second_anchor = build_unknown_anchor_state(command_key="B")

    assert first == second
    assert first_anchor == second_anchor

    try:
        first.metadata["mock_only"] = False
    except TypeError:
        pass

    try:
        first_anchor.metadata["mock_only"] = False
    except TypeError:
        pass

    fresh_intent = evaluate_undo_commit_state_behavior("B")
    fresh_anchor = build_unknown_anchor_state(command_key="B")
    assert fresh_intent.metadata["mock_only"] is True
    assert fresh_anchor.metadata["mock_only"] is True


def test_passive_cli_preview_b_remains_read_only():
    result = run_cli("preview-command", "B")

    assert result.returncode == 0
    assert "Command: B" in result.stdout
    assert "No MIDI would be sent." in result.stdout
    assert "No hardware would be mutated." in result.stdout
    assert result.stderr == ""


def test_runtime_adjacent_b_imports_no_real_midi_and_exposes_no_active_names():
    import rytm_randomizer.state.anchor_validation as anchor_state
    import rytm_randomizer.behavior.undo_commit_state as state_behavior
    import rytm_randomizer.mock_midi  # noqa: F401

    exposed_names = set(dir(state_behavior)) | set(anchor_state.__all__)

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules
    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "execute_b" not in exposed_names
    assert "return_current_anchor" not in exposed_names
    assert "open_port" not in exposed_names
    assert "send_midi" not in exposed_names


def test_closeout_includes_runtime_adjacent_b_label():
    closeout_text = (PROJECT_ROOT / "Scripts" / "closeout_check.ps1").read_text()

    assert "=== Test: Runtime-Adjacent Mock-Only B ===" in closeout_text
    assert "test_runtime_adjacent_mock_only_b.py" in closeout_text


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
