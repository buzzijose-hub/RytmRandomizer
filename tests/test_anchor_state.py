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


def test_importing_anchor_state_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.anchor_state"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_unknown_anchor_state_is_safe_and_deterministic():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state

    result = build_unknown_anchor_state()

    assert result.anchor_pad is None
    assert result.anchor_state == "unknown"
    assert result.anchor_source == ""
    assert result.anchor_identity == ""
    assert result.command_key == ""
    assert result.source_scope == ""
    assert result.source_profile_key == ""
    assert result.source_profile_name == ""
    assert result.source_machine_value is None
    assert result.static is False
    assert result.software_known is False
    assert result.soft_captured is False
    assert result.supported is False
    assert result.stale is False
    assert result.valid is False
    assert result.reason == "anchor_unknown"
    assert result.safe_failure_code == "anchor_unknown"
    assert result.anchor_return_executed is False
    assert result.selected_pad_switch_executed is False
    assert result.selected_target_state_exists is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.state_changed is False
    assert result.dispatches_command is False
    assert result.executes_command is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.active_behavior is False
    assert result.metadata["anchor_state"] == "unknown"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False


def test_unsupported_anchor_state_fails_safely():
    from rytm_randomizer.state.anchor_validation import build_unsupported_anchor_state

    result = build_unsupported_anchor_state(
        anchor_pad=5,
        command_key="PZ",
        anchor_identity="Pad 5 anchor",
    )

    assert result.anchor_pad == 5
    assert result.anchor_state == "unsupported"
    assert result.anchor_source == "unsupported"
    assert result.anchor_identity == "Pad 5 anchor"
    assert result.command_key == "PZ"
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "unsupported_anchor"
    assert result.safe_failure_code == "unsupported_anchor"
    assert result.anchor_return_executed is False
    assert result.selected_pad_switch_executed is False
    assert result.selected_target_state_exists is False
    assert result.selected_isolated_pad_runtime_state_exists is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["anchor_pad"] == 5
    assert result.metadata["anchor_identity"] == "Pad 5 anchor"
    assert result.metadata["supported"] is False


def test_stale_anchor_state_fails_safely():
    from rytm_randomizer.state.anchor_validation import build_stale_anchor_state

    result = build_stale_anchor_state(
        anchor_pad=3,
        command_key="PZ",
        anchor_identity="Pad 3 stale anchor",
    )

    assert result.anchor_pad == 3
    assert result.command_key == "PZ"
    assert result.anchor_state == "stale"
    assert result.anchor_source == "stale"
    assert result.anchor_identity == "Pad 3 stale anchor"
    assert result.stale is True
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "stale_anchor"
    assert result.safe_failure_code == "stale_anchor"
    assert result.anchor_return_executed is False
    assert result.selected_pad_switch_executed is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_invalid_anchor_state_fails_safely():
    from rytm_randomizer.state.anchor_validation import build_invalid_anchor_state

    result = build_invalid_anchor_state(
        anchor_pad=None,
        reason="invalid_anchor",
    )

    assert result.anchor_pad is None
    assert result.anchor_state == "invalid"
    assert result.anchor_source == "invalid"
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "invalid_anchor"
    assert result.safe_failure_code == "invalid_anchor"
    assert result.anchor_return_executed is False
    assert result.selected_pad_switch_executed is False
    assert result.mutates_runtime_state is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False


def test_anchor_state_metadata_is_copied_and_immutable():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state

    result = build_unknown_anchor_state()

    try:
        result.metadata["anchor_state"] = "mutated"
    except TypeError:
        pass

    fresh_result = build_unknown_anchor_state()
    assert fresh_result.metadata["anchor_state"] == "unknown"


def test_repeated_anchor_state_evaluations_are_deterministic():
    from rytm_randomizer.state.anchor_validation import (
        build_invalid_anchor_state,
        build_stale_anchor_state,
        build_unknown_anchor_state,
        build_unsupported_anchor_state,
    )

    assert build_unknown_anchor_state() == build_unknown_anchor_state()
    assert build_unsupported_anchor_state(5) == build_unsupported_anchor_state(5)
    assert build_stale_anchor_state(3) == build_stale_anchor_state(3)
    assert build_invalid_anchor_state() == build_invalid_anchor_state()


def test_anchor_state_exposes_no_selected_target_or_runtime_state_objects():
    from rytm_randomizer.state.anchor_validation import build_unknown_anchor_state

    result = build_unknown_anchor_state()

    assert hasattr(result, "selected_target_state") is False
    assert hasattr(result, "selected_isolated_pad_runtime_state") is False
    assert result.metadata["selected_target_state_exists"] is False
    assert result.metadata["selected_isolated_pad_runtime_state_exists"] is False


def test_anchor_state_exposes_no_active_command_names():
    import rytm_randomizer.state.anchor_validation as anchor_state

    exported_names = set(anchor_state.__all__)

    assert "execute_command" not in exported_names
    assert "send_command" not in exported_names
    assert "hardware_test" not in exported_names
    assert "open_port" not in exported_names
    assert "send_midi" not in exported_names
    assert "execute_anchor_return" not in exported_names
    assert "PZ" not in exported_names


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("inspect-command", "PZ")

    assert result.returncode == 0
    assert "Command: PZ" in result.stdout
    assert "Label: return selected isolated pad to anchor only" in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.state.anchor_validation  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
