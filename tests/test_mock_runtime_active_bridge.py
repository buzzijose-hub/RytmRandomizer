import importlib
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def assert_mapping_is_immutable(mapping):
    try:
        mapping["mutation_attempt"] = "blocked"
    except TypeError:
        return
    raise AssertionError("mapping should be immutable")


def test_importing_mock_runtime_active_bridge_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.mock_runtime_active_bridge"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_bridge_imports_no_real_midi_libraries():
    sys.modules.pop("rytm_randomizer.mock_runtime_active_bridge", None)
    importlib.import_module("rytm_randomizer.mock_runtime_active_bridge")

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_profile_2_bridge_records_mock_messages_only_when_armed_and_confirmed():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is True
    assert result.reason == "accepted_mock_only"
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert result.would_execute is False
    assert result.emitted_messages == sender.sent_messages
    assert len(sender.sent_messages) == 1
    assert sender.sent_messages[0].metadata["source_key"] == "2"
    assert sender.sent_messages[0].metadata["mock_only"] is True
    assert sender.sent_messages[0].metadata["sends_real_midi"] is False


def test_missing_arming_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=False,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_missing_dry_run_confirmation_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=True,
        dry_run_confirmed=False,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_3_remains_runtime_supported_but_bridge_rejected():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="3",
        target="Pad 2 / My BD Classic",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "active_boundary_rejected"
    assert result.metadata["source_key"] == "3"
    assert result.metadata["runtime_supported"] is True
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_4_remains_parked_and_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="4",
        target="Pad 1 / My BD Acoustic",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "profile_4_parked"
    assert result.metadata["parked"] is True
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_unknown_key_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="unknown",
        target="unknown",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_unsupported_source_kind_emits_no_messages():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="scene",
        source_key="S1A",
        target="Rolling Light",
        armed=True,
        dry_run_confirmed=True,
    )

    result = evaluate_mock_runtime_active_bridge(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_source_kind"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_request_metadata_is_copied_and_immutable():
    from rytm_randomizer.mock_runtime_active_bridge import RuntimeActiveBridgeRequest

    metadata = {"operator_intent": "original"}
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        metadata=metadata,
    )

    metadata["operator_intent"] = "changed"

    assert request.metadata["operator_intent"] == "original"
    assert_mapping_is_immutable(request.metadata)


def test_result_metadata_is_copied_and_immutable():
    from rytm_randomizer.mock_runtime_active_bridge import RuntimeActiveBridgeResult

    metadata = {"source_key": "2"}
    result = RuntimeActiveBridgeResult(
        accepted=True,
        reason="manual_test",
        metadata=metadata,
    )

    metadata["source_key"] = "changed"

    assert result.metadata["source_key"] == "2"
    assert_mapping_is_immutable(result.metadata)


def test_invalid_inputs_fail_before_message_emission():
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.mock_runtime_active_bridge import (
        RuntimeActiveBridgeRequest,
        evaluate_mock_runtime_active_bridge,
    )

    sender = MockMidiSender()
    request = RuntimeActiveBridgeRequest(
        source_kind="group_profile",
        source_key="2",
        target="mock-target-only",
        armed=True,
        dry_run_confirmed=True,
    )

    try:
        evaluate_mock_runtime_active_bridge(object(), sender)
    except TypeError as exc:
        assert "RuntimeActiveBridgeRequest" in str(exc)
    else:
        raise AssertionError("invalid request should fail before message emission")

    assert sender.sent_messages == ()

    try:
        evaluate_mock_runtime_active_bridge(request, object())
    except TypeError as exc:
        assert "MockMidiSender" in str(exc)
    else:
        raise AssertionError("invalid sender should fail before message emission")

    assert sender.sent_messages == ()


def test_passive_cli_report_stays_read_only():
    result = subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", "report"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_bridge_exposes_no_active_cli_command_names():
    bridge = importlib.import_module("rytm_randomizer.mock_runtime_active_bridge")

    exposed_names = set(dir(bridge))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


if __name__ == "__main__":
    test_importing_mock_runtime_active_bridge_prints_nothing()
    test_bridge_imports_no_real_midi_libraries()
    test_profile_2_bridge_records_mock_messages_only_when_armed_and_confirmed()
    test_missing_arming_emits_no_messages()
    test_missing_dry_run_confirmation_emits_no_messages()
    test_profile_3_remains_runtime_supported_but_bridge_rejected()
    test_profile_4_remains_parked_and_emits_no_messages()
    test_unknown_key_emits_no_messages()
    test_unsupported_source_kind_emits_no_messages()
    test_request_metadata_is_copied_and_immutable()
    test_result_metadata_is_copied_and_immutable()
    test_invalid_inputs_fail_before_message_emission()
    test_passive_cli_report_stays_read_only()
    test_bridge_exposes_no_active_cli_command_names()
