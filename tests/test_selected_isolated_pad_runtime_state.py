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


def test_importing_selected_isolated_pad_runtime_state_prints_nothing():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import rytm_randomizer.selected_isolated_pad_runtime_state",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_uninitialized_runtime_state_is_safe_and_deterministic():
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_uninitialized_selected_isolated_pad_runtime_state,
    )

    result = build_uninitialized_selected_isolated_pad_runtime_state()

    assert result.runtime_state == "uninitialized"
    assert result.target_pad is None
    assert result.target_state == ""
    assert result.anchor_pad is None
    assert result.anchor_state == ""
    assert result.target_anchor_status == "unavailable"
    assert result.operation_kind == "selected_isolated_pad_runtime_validation"
    assert result.supported is False
    assert result.stale is False
    assert result.valid is False
    assert result.reason == "selected_isolated_pad_runtime_uninitialized"
    assert result.safe_failure_code == "selected_isolated_pad_runtime_uninitialized"
    assert result.pz_ready is False
    assert result.pz_executed is False
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
    assert result.metadata["runtime_state"] == "uninitialized"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert result.metadata["opens_ports"] is False


def test_passive_default_runtime_state_keeps_anchor_unavailable_safely():
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_passive_default_selected_isolated_pad_runtime_state,
    )

    result = build_passive_default_selected_isolated_pad_runtime_state()

    assert result.runtime_state == "passive-default"
    assert result.target_pad == 3
    assert result.target_state == "defaulted"
    assert result.target_source == "passive_default"
    assert result.target_command_key == "L"
    assert result.anchor_pad is None
    assert result.anchor_state == "unknown"
    assert result.anchor_source == ""
    assert result.anchor_identity == ""
    assert result.target_anchor_status == "anchor-unavailable"
    assert result.supported is False
    assert result.valid is False
    assert result.reason == "anchor_unavailable_for_selected_target"
    assert result.safe_failure_code == "anchor_unavailable_for_selected_target"
    assert result.pz_ready is False
    assert result.pz_executed is False
    assert result.selected_pad_switch_executed is False
    assert result.anchor_return_executed is False
    assert result.dispatches_command is False
    assert result.sends_real_midi is False
    assert result.opens_ports is False
    assert result.hardware_required is False
    assert result.metadata["target_pad"] == 3
    assert result.metadata["target_anchor_status"] == "anchor-unavailable"


def test_missing_selected_target_fails_safely():
    from rytm_randomizer.anchor_state import build_unknown_anchor_state
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_missing_selected_target_runtime_state,
    )

    result = build_missing_selected_target_runtime_state(
        anchor_state=build_unknown_anchor_state()
    )

    assert result.runtime_state == "invalid"
    assert result.target_anchor_status == "target-missing"
    assert result.reason == "missing_selected_target_state"
    assert result.safe_failure_code == "missing_selected_target_state"
    assert result.valid is False
    assert result.pz_ready is False
    assert result.dispatches_command is False
    assert result.opens_ports is False
    assert result.sends_real_midi is False


def test_missing_anchor_fails_safely():
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_missing_anchor_runtime_state,
    )
    from rytm_randomizer.selected_target_state import (
        build_default_selected_target_state,
    )

    result = build_missing_anchor_runtime_state(
        selected_target_state=build_default_selected_target_state()
    )

    assert result.runtime_state == "invalid"
    assert result.target_pad == 3
    assert result.target_anchor_status == "anchor-missing"
    assert result.reason == "missing_anchor_state"
    assert result.safe_failure_code == "missing_anchor_state"
    assert result.valid is False
    assert result.pz_ready is False
    assert result.dispatches_command is False
    assert result.opens_ports is False
    assert result.sends_real_midi is False


def test_unsupported_selected_target_fails_safely():
    from rytm_randomizer.anchor_state import build_unknown_anchor_state
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_selected_isolated_pad_runtime_state,
    )
    from rytm_randomizer.selected_target_state import (
        build_unsupported_selected_target_state,
    )

    result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_unsupported_selected_target_state(5),
        anchor_state=build_unknown_anchor_state(),
    )

    assert result.runtime_state == "unsupported"
    assert result.target_pad == 5
    assert result.target_anchor_status == "target-unsupported"
    assert result.reason == "unsupported_selected_target"
    assert result.safe_failure_code == "unsupported_selected_target"
    assert result.supported is False
    assert result.valid is False
    assert result.pz_ready is False


def test_unsupported_anchor_fails_safely():
    from rytm_randomizer.anchor_state import build_unsupported_anchor_state
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_selected_isolated_pad_runtime_state,
    )
    from rytm_randomizer.selected_target_state import (
        build_default_selected_target_state,
    )

    result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_default_selected_target_state(),
        anchor_state=build_unsupported_anchor_state(anchor_pad=5),
    )

    assert result.runtime_state == "unsupported"
    assert result.target_pad == 3
    assert result.anchor_pad == 5
    assert result.target_anchor_status == "anchor-unsupported"
    assert result.reason == "unsupported_anchor"
    assert result.safe_failure_code == "unsupported_anchor"
    assert result.supported is False
    assert result.valid is False
    assert result.pz_ready is False


def test_stale_target_and_stale_anchor_fail_safely():
    from rytm_randomizer.anchor_state import build_stale_anchor_state
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_selected_isolated_pad_runtime_state,
    )
    from rytm_randomizer.selected_target_state import (
        build_default_selected_target_state,
        build_stale_selected_target_state,
    )

    stale_target_result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_stale_selected_target_state(3),
        anchor_state=build_stale_anchor_state(anchor_pad=3),
    )
    stale_anchor_result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_default_selected_target_state(),
        anchor_state=build_stale_anchor_state(anchor_pad=3),
    )

    assert stale_target_result.runtime_state == "stale"
    assert stale_target_result.target_anchor_status == "target-stale"
    assert stale_target_result.reason == "stale_selected_target"
    assert stale_target_result.safe_failure_code == "stale_selected_target"
    assert stale_target_result.stale is True
    assert stale_target_result.pz_ready is False

    assert stale_anchor_result.runtime_state == "stale"
    assert stale_anchor_result.target_anchor_status == "anchor-stale"
    assert stale_anchor_result.reason == "stale_anchor"
    assert stale_anchor_result.safe_failure_code == "stale_anchor"
    assert stale_anchor_result.stale is True
    assert stale_anchor_result.pz_ready is False


def test_invalid_target_and_invalid_anchor_fail_safely():
    from rytm_randomizer.anchor_state import (
        build_invalid_anchor_state,
        build_unknown_anchor_state,
    )
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_selected_isolated_pad_runtime_state,
    )
    from rytm_randomizer.selected_target_state import (
        build_default_selected_target_state,
        build_invalid_selected_target_state,
    )

    invalid_target_result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_invalid_selected_target_state(),
        anchor_state=build_unknown_anchor_state(),
    )
    invalid_anchor_result = build_selected_isolated_pad_runtime_state(
        selected_target_state=build_default_selected_target_state(),
        anchor_state=build_invalid_anchor_state(),
    )

    assert invalid_target_result.runtime_state == "invalid"
    assert invalid_target_result.target_anchor_status == "target-invalid"
    assert invalid_target_result.reason == "invalid_selected_target"
    assert invalid_target_result.safe_failure_code == "invalid_selected_target"
    assert invalid_target_result.valid is False
    assert invalid_target_result.pz_ready is False

    assert invalid_anchor_result.runtime_state == "invalid"
    assert invalid_anchor_result.target_anchor_status == "anchor-invalid"
    assert invalid_anchor_result.reason == "invalid_anchor"
    assert invalid_anchor_result.safe_failure_code == "invalid_anchor"
    assert invalid_anchor_result.valid is False
    assert invalid_anchor_result.pz_ready is False


def test_runtime_state_metadata_is_copied_and_immutable():
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_uninitialized_selected_isolated_pad_runtime_state,
    )

    result = build_uninitialized_selected_isolated_pad_runtime_state()

    try:
        result.metadata["runtime_state"] = "mutated"
    except TypeError:
        pass

    fresh_result = build_uninitialized_selected_isolated_pad_runtime_state()
    assert fresh_result.metadata["runtime_state"] == "uninitialized"


def test_repeated_runtime_state_evaluations_are_deterministic():
    from rytm_randomizer.selected_isolated_pad_runtime_state import (
        build_passive_default_selected_isolated_pad_runtime_state,
        build_uninitialized_selected_isolated_pad_runtime_state,
    )

    assert (
        build_uninitialized_selected_isolated_pad_runtime_state()
        == build_uninitialized_selected_isolated_pad_runtime_state()
    )
    assert (
        build_passive_default_selected_isolated_pad_runtime_state()
        == build_passive_default_selected_isolated_pad_runtime_state()
    )


def test_runtime_state_exposes_no_active_command_names():
    import rytm_randomizer.selected_isolated_pad_runtime_state as runtime_state

    exported_names = set(runtime_state.__all__)

    assert "execute_command" not in exported_names
    assert "send_command" not in exported_names
    assert "hardware_test" not in exported_names
    assert "open_port" not in exported_names
    assert "send_midi" not in exported_names
    assert "execute_pz" not in exported_names
    assert "PZ" not in exported_names


def test_passive_cli_behavior_remains_unchanged():
    result = run_cli("preview-command", "PZ")

    assert result.returncode == 0
    assert "Command: PZ" in result.stdout
    assert "No MIDI would be sent." in result.stdout
    assert "No hardware would be mutated." in result.stdout
    assert result.stderr == ""


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.selected_isolated_pad_runtime_state  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def _run_tests():
    current_module = sys.modules[__name__]
    for name, value in sorted(vars(current_module).items()):
        if name.startswith("test_") and callable(value):
            value()


if __name__ == "__main__":
    _run_tests()
