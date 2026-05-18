import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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


def test_first_candidate_profile_2_maps_to_expected_mock_message():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MidiMessage

    messages = map_group_profile_to_mock_messages("2")

    assert len(messages) == 1
    assert isinstance(messages[0], MidiMessage)
    assert messages[0].message_type == "mock_group_profile"
    assert messages[0].channel == 1
    assert messages[0].control == 0
    assert messages[0].value == 0


def test_first_candidate_profile_2_metadata_is_inert_and_explicit():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages

    message = map_group_profile_to_mock_messages("2")[0]

    assert message.metadata == {
        "source_kind": "group_profile",
        "source_key": "2",
        "source_name": "My BD Hard",
        "group_pad": 1,
        "machine_value": 0,
        "target": "Pad 1 / BD Hard",
        "mock_only": True,
        "sends_real_midi": False,
    }


def test_first_candidate_messages_are_deterministic():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages

    first = map_group_profile_to_mock_messages("2")
    second = map_group_profile_to_mock_messages("2")

    assert first == second


def test_first_candidate_records_through_mock_sender_only():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MockMidiSender

    messages = map_group_profile_to_mock_messages("2")
    sender = MockMidiSender()

    sender.send_many(messages)

    assert sender.sent_messages == tuple(messages)


def test_unknown_candidate_key_emits_no_messages():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()

    try:
        sender.send_many(map_group_profile_to_mock_messages("DOES_NOT_EXIST"))
    except MockMessageMappingError as exc:
        assert "was not found" in str(exc)
    else:
        raise AssertionError("unknown candidate key should fail safely")

    assert sender.sent_messages == ()


def test_unsupported_profile_4_emits_no_messages_and_remains_parked():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()

    try:
        sender.send_many(map_group_profile_to_mock_messages("4"))
    except MockMessageMappingError as exc:
        assert "is not supported by the mock mapper" in str(exc)
    else:
        raise AssertionError("profile 4 should remain unsupported")

    assert sender.sent_messages == ()


def test_first_candidate_imports_no_real_midi_libraries():
    import rytm_randomizer.mock_message_mapper  # noqa: F401
    import rytm_randomizer.mock_midi  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_stays_read_only():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_active_behavior_names_are_exposed_by_candidate_modules():
    import rytm_randomizer.mock_message_mapper as mapper
    import rytm_randomizer.mock_midi as mock_midi

    exposed_names = set(dir(mapper)) | set(dir(mock_midi))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names
    assert "open_port" not in exposed_names


if __name__ == "__main__":
    test_first_candidate_profile_2_maps_to_expected_mock_message()
    test_first_candidate_profile_2_metadata_is_inert_and_explicit()
    test_first_candidate_messages_are_deterministic()
    test_first_candidate_records_through_mock_sender_only()
    test_unknown_candidate_key_emits_no_messages()
    test_unsupported_profile_4_emits_no_messages_and_remains_parked()
    test_first_candidate_imports_no_real_midi_libraries()
    test_passive_cli_report_stays_read_only()
    test_no_active_behavior_names_are_exposed_by_candidate_modules()
