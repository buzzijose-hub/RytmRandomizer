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


def test_importing_selected_target_state_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.state.selected_target_validation"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_unset_selected_target_state_is_safe_and_deterministic():
    from rytm_randomizer.state.selected_target_validation import build_unset_selected_target_state

    result = build_unset_selected_target_state()

    assert result.target_pad is None
    assert result.target_state == "unset"
    assert result.target_source == ""
    assert result.command_key == ""
    assert result.source_scope == ""
    assert result.defaulted is False
    assert result.explicit is False
    assert result.supported is False
    assert result.stale is False
    assert result.valid is False
    assert result.reason == "selected_target_unset"
    assert result.safe_failure_code == "selected_target_unset"
    assert result.selected_pad_switch_executed is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.state_changed is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["target_state"] == "unset"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False


def test_default_selected_target_state_uses_passive_pad_3_context():
    from rytm_randomizer.state.selected_target_validation import (
        DEFAULT_SELECTED_TARGET_PAD,
        SELECTED_TARGET_DEFAULT_COMMAND_KEY,
        build_default_selected_target_state,
    )

    result = build_default_selected_target_state()

    assert DEFAULT_SELECTED_TARGET_PAD == 3
    assert SELECTED_TARGET_DEFAULT_COMMAND_KEY == "L"
    assert result.target_pad == 3
    assert result.target_state == "defaulted"
    assert result.target_source == "passive_default"
    assert result.command_key == "L"
    assert result.source_scope == "isolated_pad_target"
    assert result.defaulted is True
    assert result.explicit is False
    assert result.supported is True
    assert result.stale is False
    assert result.valid is True
    assert result.reason == "defaulted_selected_isolated_pad_target"
    assert result.safe_failure_code == ""
    assert result.selected_pad_switch_executed is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.state_changed is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["source"] == "ISOLATED_PAD_UTILITY_COMMANDS"
    assert result.metadata["command_key"] == "L"
    assert result.metadata["target_pad"] == 3
    assert result.metadata["target_state"] == "defaulted"
    assert result.metadata["mock_only"] is True


def test_unsupported_selected_target_fails_safely():
    from rytm_randomizer.state.selected_target_validation import (
        build_unsupported_selected_target_state,
    )

    result = build_unsupported_selected_target_state(5)

    assert result.target_pad == 5
    assert result.target_state == "unsupported"
    assert result.target_source == "unsupported"
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "unsupported_selected_target"
    assert result.safe_failure_code == "unsupported_selected_target"
    assert result.selected_pad_switch_executed is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["target_pad"] == 5
    assert result.metadata["supported"] is False


def test_stale_selected_target_fails_safely():
    from rytm_randomizer.state.selected_target_validation import build_stale_selected_target_state

    result = build_stale_selected_target_state(target_pad=3, command_key="L")

    assert result.target_pad == 3
    assert result.command_key == "L"
    assert result.target_state == "stale"
    assert result.stale is True
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "stale_selected_target"
    assert result.safe_failure_code == "stale_selected_target"
    assert result.selected_pad_switch_executed is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_invalid_selected_target_fails_safely():
    from rytm_randomizer.state.selected_target_validation import build_invalid_selected_target_state

    result = build_invalid_selected_target_state(
        target_pad=None,
        reason="invalid_selected_target",
    )

    assert result.target_pad is None
    assert result.target_state == "invalid"
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "invalid_selected_target"
    assert result.safe_failure_code == "invalid_selected_target"
    assert result.selected_pad_switch_executed is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_selected_target_metadata_is_copied_and_immutable():
    from rytm_randomizer.state.selected_target_validation import build_default_selected_target_state

    result = build_default_selected_target_state()

    try:
        result.metadata["target_pad"] = 99
    except TypeError:
        pass

    fresh_result = build_default_selected_target_state()
    assert fresh_result.metadata["target_pad"] == 3


def test_repeated_selected_target_state_evaluations_are_deterministic():
    from rytm_randomizer.state.selected_target_validation import (
        build_default_selected_target_state,
        build_unset_selected_target_state,
    )

    assert build_default_selected_target_state() == build_default_selected_target_state()
    assert build_unset_selected_target_state() == build_unset_selected_target_state()


def test_selected_target_state_exposes_no_active_command_names():
    import rytm_randomizer.state.selected_target_validation as selected_target_state

    exported_names = set(selected_target_state.__all__)

    assert "execute_command" not in exported_names
    assert "send_command" not in exported_names
    assert "hardware_test" not in exported_names
    assert "open_port" not in exported_names
    assert "send_midi" not in exported_names


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "L")

    assert result.returncode == 0
    assert "Command: L" in result.stdout
    assert "Label: select isolated single-pad mutation target, default Pad 3" in (result.stdout)
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.state.selected_target_validation  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
