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


def assert_pz_safe_failure(result, *, reason, target_anchor_status):
    assert result.command_key == "PZ"
    assert result.accepted is False
    assert result.reason == reason
    assert result.anchor_return_intent is True
    assert result.selected_isolated_pad_runtime_state_exists is True
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
    assert result.metadata["pz_ready"] is False
    assert result.metadata["pz_executed"] is False
    assert result.metadata["selected_pad_switch_executed"] is False
    assert result.metadata["anchor_return_executed"] is False
    assert result.metadata["dispatches_command"] is False
    assert result.metadata["mutates_runtime_state"] is False
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False
    assert result.metadata["hardware_required"] is False
    assert result.metadata["active_behavior"] is False
    assert result.metadata["safe_failure_code"] == reason
    assert result.metadata["target_anchor_status"] == target_anchor_status


def test_importing_runtime_adjacent_pz_modules_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import rytm_randomizer.behavior.selected_isolated_pad; "
                "import rytm_randomizer.selected_isolated_pad_runtime_state; "
                "import rytm_randomizer.selected_target_state; "
                "import rytm_randomizer.anchor_state; "
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


def test_default_pz_readiness_fails_safely_without_mock_messages():
    from rytm_randomizer.behavior.selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    result = evaluate_selected_isolated_pad_behavior("PZ")

    assert_pz_safe_failure(
        result,
        reason="anchor_unavailable_for_selected_target",
        target_anchor_status="anchor-unavailable",
    )
    assert result.target_pad == 3
    assert result.metadata["runtime_state"] == "passive-default"
    assert result.metadata["target_state"] == "defaulted"
    assert result.metadata["anchor_state"] == "unknown"
    assert sender.sent_messages == ()


def test_missing_target_and_missing_anchor_contexts_fail_safely():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state
    from rytm_randomizer.behavior.selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.state.selected_isolated_pad_validation import (
        build_missing_anchor_runtime_state,
        build_missing_selected_target_runtime_state,
    )
    from rytm_randomizer.state.selected_target_validation import build_default_selected_target_state

    sender = MockMidiSender()
    cases = (
        (
            build_missing_selected_target_runtime_state(anchor_state=build_unknown_anchor_state()),
            "missing_selected_target_state",
            "target-missing",
        ),
        (
            build_missing_anchor_runtime_state(
                selected_target_state=build_default_selected_target_state()
            ),
            "missing_anchor_state",
            "anchor-missing",
        ),
    )

    for runtime_state, reason, target_anchor_status in cases:
        result = evaluate_selected_isolated_pad_behavior("PZ", runtime_state=runtime_state)

        assert_pz_safe_failure(
            result,
            reason=reason,
            target_anchor_status=target_anchor_status,
        )

    assert sender.sent_messages == ()


def test_unsupported_stale_and_invalid_contexts_fail_safely():
    from rytm_randomizer.state.anchor_validation import (
        build_invalid_anchor_state,
        build_stale_anchor_state,
        build_unknown_anchor_state,
        build_unsupported_anchor_state,
    )
    from rytm_randomizer.behavior.selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.state.selected_isolated_pad_validation import (
        build_selected_isolated_pad_runtime_state,
    )
    from rytm_randomizer.state.selected_target_validation import (
        build_default_selected_target_state,
        build_invalid_selected_target_state,
        build_stale_selected_target_state,
        build_unsupported_selected_target_state,
    )

    sender = MockMidiSender()
    cases = (
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_unsupported_selected_target_state(5),
                anchor_state=build_unknown_anchor_state(),
            ),
            "unsupported_selected_target",
            "target-unsupported",
        ),
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_default_selected_target_state(),
                anchor_state=build_unsupported_anchor_state(anchor_pad=3),
            ),
            "unsupported_anchor",
            "anchor-unsupported",
        ),
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_stale_selected_target_state(3),
                anchor_state=build_unknown_anchor_state(),
            ),
            "stale_selected_target",
            "target-stale",
        ),
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_default_selected_target_state(),
                anchor_state=build_stale_anchor_state(anchor_pad=3),
            ),
            "stale_anchor",
            "anchor-stale",
        ),
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_invalid_selected_target_state(),
                anchor_state=build_unknown_anchor_state(),
            ),
            "invalid_selected_target",
            "target-invalid",
        ),
        (
            build_selected_isolated_pad_runtime_state(
                selected_target_state=build_default_selected_target_state(),
                anchor_state=build_invalid_anchor_state(),
            ),
            "invalid_anchor",
            "anchor-invalid",
        ),
    )

    for runtime_state, reason, target_anchor_status in cases:
        result = evaluate_selected_isolated_pad_behavior("PZ", runtime_state=runtime_state)

        assert_pz_safe_failure(
            result,
            reason=reason,
            target_anchor_status=target_anchor_status,
        )

    assert sender.sent_messages == ()


def test_runtime_adjacent_pz_checks_are_deterministic_and_copy_safe():
    from rytm_randomizer.behavior.selected_isolated_pad import (
        evaluate_selected_isolated_pad_behavior,
    )

    first = evaluate_selected_isolated_pad_behavior("PZ")
    second = evaluate_selected_isolated_pad_behavior("PZ")

    assert first == second

    try:
        first.metadata["runtime_state"] = "mutated"
    except TypeError:
        pass

    fresh_result = evaluate_selected_isolated_pad_behavior("PZ")
    assert fresh_result.metadata["runtime_state"] == "passive-default"


def test_passive_cli_preview_pz_remains_read_only():
    result = run_cli("preview-command", "PZ")

    assert result.returncode == 0
    assert "Command: PZ" in result.stdout
    assert "No MIDI would be sent." in result.stdout
    assert "No hardware would be mutated." in result.stdout
    assert result.stderr == ""


def test_runtime_adjacent_pz_imports_no_real_midi_and_exposes_no_active_names():
    import rytm_randomizer.behavior.selected_isolated_pad as selected_behavior
    import rytm_randomizer.mock_midi  # noqa: F401
    import rytm_randomizer.state.selected_isolated_pad_validation as runtime_state

    exposed_names = set(dir(selected_behavior)) | set(runtime_state.__all__)

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules
    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "execute_pz" not in exposed_names
    assert "open_port" not in exposed_names
    assert "send_midi" not in exposed_names


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
