from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def normalize_newlines(text):
    return text.replace("\r\n", "\n").replace("\r", "\n").rstrip("\n")


def fixture_text(filename):
    return normalize_newlines((FIXTURES_DIR / filename).read_text(encoding="utf-8"))


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def assert_raises(expected_exception, func, *args, **kwargs):
    try:
        func(*args, **kwargs)
    except expected_exception:
        return
    raise AssertionError(f"expected {expected_exception.__name__}")


def assert_mapping_is_immutable(mapping):
    try:
        mapping["mutation_attempt"] = "blocked"
    except TypeError:
        return
    raise AssertionError("mapping should be immutable")


def message_signature(messages):
    return tuple(
        (
            message.message_type,
            message.channel,
            message.control,
            message.value,
            tuple(sorted(message.metadata.items())),
        )
        for message in messages
    )


def test_importing_active_boundary_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.active_boundary"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_missing_arming_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=False,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_arming"
    assert result.emitted_messages == ()
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert sender.sent_messages == ()


def test_missing_dry_run_confirmation_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=False,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "missing_dry_run_confirmation"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_unknown_key_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="DOES_NOT_EXIST",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_4_remains_parked_and_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="4",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_request_metadata_is_copied_and_immutable():
    from rytm_randomizer.active_boundary import ActiveBoundaryRequest

    metadata = {"operator_intent": "original"}
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        metadata=metadata,
    )

    metadata["operator_intent"] = "changed"

    assert request.metadata["operator_intent"] == "original"
    assert_mapping_is_immutable(request.metadata)


def test_result_metadata_is_copied_and_immutable():
    from rytm_randomizer.active_boundary import ActiveBoundaryResult

    metadata = {"source_key": "2"}
    result = ActiveBoundaryResult(
        accepted=True,
        emitted_messages=(),
        reason="manual_test",
        metadata=metadata,
    )

    metadata["source_key"] = "changed"

    assert result.metadata["source_key"] == "2"
    assert_mapping_is_immutable(result.metadata)


def test_accepted_result_metadata_includes_target_and_is_immutable():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock-target-only",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is True
    assert result.metadata["source_kind"] == "group_profile"
    assert result.metadata["source_key"] == "2"
    assert result.metadata["target"] == "mock-target-only"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert_mapping_is_immutable(result.metadata)


def test_failure_result_metadata_records_mock_only_safety():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="DOES_NOT_EXIST",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, MockMidiSender())

    assert result.accepted is False
    assert result.metadata["source_kind"] == "group_profile"
    assert result.metadata["source_key"] == "DOES_NOT_EXIST"
    assert result.metadata["mock_only"] is True
    assert result.metadata["sends_real_midi"] is False
    assert_mapping_is_immutable(result.metadata)


def test_request_source_key_is_normalized_to_string_before_evaluation():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key=2,
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert request.source_key == "2"
    assert result.accepted is True
    assert result.metadata["source_key"] == "2"
    assert result.emitted_messages[0].metadata["source_key"] == "2"


def test_request_metadata_does_not_leak_into_emitted_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
        metadata={"operator_intent": "private dry-run note"},
    )

    result = evaluate_mock_active_boundary(request, MockMidiSender())

    assert result.accepted is True
    assert "operator_intent" not in result.emitted_messages[0].metadata


def test_accepted_evaluation_does_not_mutate_request_metadata_object():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    metadata = {"operator_intent": "unchanged"}
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
        metadata=metadata,
    )

    evaluate_mock_active_boundary(request, MockMidiSender())

    assert metadata == {"operator_intent": "unchanged"}
    assert request.metadata["operator_intent"] == "unchanged"


def test_accepted_evaluation_does_not_mutate_source_mock_mapper_output():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MockMidiSender

    before = message_signature(map_group_profile_to_mock_messages("2"))
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    evaluate_mock_active_boundary(request, MockMidiSender())
    after = message_signature(map_group_profile_to_mock_messages("2"))

    assert after == before


def test_unsupported_source_kind_emits_no_messages():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="scene",
        source_key="S1A",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_source_kind"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_source_kind_matching_is_exact():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    for source_kind in ("GROUP_PROFILE", "group_profiles", " group_profile "):
        sender = MockMidiSender()
        request = ActiveBoundaryRequest(
            source_kind=source_kind,
            source_key="2",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        )

        result = evaluate_mock_active_boundary(request, sender)

        assert result.accepted is False
        assert result.reason == "unsupported_source_kind"
        assert result.emitted_messages == ()
        assert sender.sent_messages == ()


def test_profile_3_is_not_active_boundary_supported():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="3",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is False
    assert result.reason == "unsupported_or_unknown_key"
    assert result.emitted_messages == ()
    assert sender.sent_messages == ()


def test_profile_2_emits_mock_messages_only_when_armed_and_confirmed():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
        metadata={"operator_intent": "mock-only candidate proof"},
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is True
    assert result.reason == "accepted_mock_only"
    assert result.mock_only is True
    assert result.sends_real_midi is False
    assert result.emitted_messages == sender.sent_messages
    assert len(result.emitted_messages) == 1
    assert result.emitted_messages[0].metadata["source_key"] == "2"
    assert result.emitted_messages[0].metadata["mock_only"] is True
    assert result.emitted_messages[0].metadata["sends_real_midi"] is False


def test_sender_receives_exactly_emitted_messages_and_no_extras():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is True
    assert len(result.emitted_messages) == 1
    assert sender.sent_messages == result.emitted_messages
    assert message_signature(sender.sent_messages) == message_signature(result.emitted_messages)


def test_target_value_remains_metadata_only_and_does_not_select_ports():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="USB Rytm Port 1",
    )

    result = evaluate_mock_active_boundary(request, sender)

    assert result.accepted is True
    assert result.metadata["target"] == "USB Rytm Port 1"
    assert "port" not in result.metadata
    assert "midi_port" not in result.metadata
    assert "device" not in result.metadata
    assert sender.sent_messages[0].metadata["target"] == "Pad 1 / BD Hard"


def test_repeated_profile_2_evaluations_are_deterministic():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )
    first_sender = MockMidiSender()
    second_sender = MockMidiSender()

    first = evaluate_mock_active_boundary(request, first_sender)
    second = evaluate_mock_active_boundary(request, second_sender)

    assert first.accepted is True
    assert second.accepted is True
    assert first.reason == second.reason == "accepted_mock_only"
    assert message_signature(first.emitted_messages) == message_signature(second.emitted_messages)
    assert message_signature(first_sender.sent_messages) == message_signature(second_sender.sent_messages)


def test_repeated_failure_evaluations_are_deterministic():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="DOES_NOT_EXIST",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    first = evaluate_mock_active_boundary(request, MockMidiSender())
    second = evaluate_mock_active_boundary(request, MockMidiSender())

    assert first.accepted is False
    assert second.accepted is False
    assert first.reason == second.reason == "unsupported_or_unknown_key"
    assert first.emitted_messages == second.emitted_messages == ()


def test_failure_paths_leave_sender_empty():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    requests = [
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="2",
            armed=False,
            dry_run_confirmed=True,
            target="mock",
        ),
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="2",
            armed=True,
            dry_run_confirmed=False,
            target="mock",
        ),
        ActiveBoundaryRequest(
            source_kind="scene",
            source_key="S1A",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="3",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="4",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
    ]

    sender = MockMidiSender()
    for request in requests:
        result = evaluate_mock_active_boundary(request, sender)
        assert result.accepted is False
        assert result.emitted_messages == ()
        assert sender.sent_messages == ()


def test_invalid_boundary_inputs_fail_before_message_emission():
    from rytm_randomizer.active_boundary import (
        ActiveBoundaryRequest,
        evaluate_mock_active_boundary,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()
    request = ActiveBoundaryRequest(
        source_kind="group_profile",
        source_key="2",
        armed=True,
        dry_run_confirmed=True,
        target="mock",
    )

    assert_raises(TypeError, evaluate_mock_active_boundary, object(), sender)
    assert sender.sent_messages == ()

    assert_raises(TypeError, evaluate_mock_active_boundary, request, object())
    assert sender.sent_messages == ()


def test_passive_cli_report_stays_read_only():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_real_midi_libraries_are_imported():
    import rytm_randomizer.active_boundary  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_no_active_cli_command_names_are_exposed():
    import rytm_randomizer.active_boundary as boundary

    exposed_names = set(dir(boundary))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names
    assert "open_midi_port" not in exposed_names
    assert "send_midi" not in exposed_names
    assert "MidiPortProvider" not in exposed_names


if __name__ == "__main__":
    test_importing_active_boundary_prints_nothing()
    test_missing_arming_emits_no_messages()
    test_missing_dry_run_confirmation_emits_no_messages()
    test_unknown_key_emits_no_messages()
    test_profile_4_remains_parked_and_emits_no_messages()
    test_request_metadata_is_copied_and_immutable()
    test_result_metadata_is_copied_and_immutable()
    test_accepted_result_metadata_includes_target_and_is_immutable()
    test_failure_result_metadata_records_mock_only_safety()
    test_request_source_key_is_normalized_to_string_before_evaluation()
    test_request_metadata_does_not_leak_into_emitted_messages()
    test_accepted_evaluation_does_not_mutate_request_metadata_object()
    test_accepted_evaluation_does_not_mutate_source_mock_mapper_output()
    test_unsupported_source_kind_emits_no_messages()
    test_source_kind_matching_is_exact()
    test_profile_3_is_not_active_boundary_supported()
    test_profile_2_emits_mock_messages_only_when_armed_and_confirmed()
    test_sender_receives_exactly_emitted_messages_and_no_extras()
    test_target_value_remains_metadata_only_and_does_not_select_ports()
    test_repeated_profile_2_evaluations_are_deterministic()
    test_repeated_failure_evaluations_are_deterministic()
    test_failure_paths_leave_sender_empty()
    test_invalid_boundary_inputs_fail_before_message_emission()
    test_passive_cli_report_stays_read_only()
    test_no_real_midi_libraries_are_imported()
    test_no_active_cli_command_names_are_exposed()
