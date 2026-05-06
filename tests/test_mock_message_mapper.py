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


def test_importing_mock_message_mapper_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.mock_message_mapper"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_group_profile_2_maps_to_deterministic_mock_message():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MidiMessage

    first = map_group_profile_to_mock_messages("2")
    second = map_group_profile_to_mock_messages("2")

    assert first == second
    assert len(first) == 1
    assert isinstance(first[0], MidiMessage)
    assert first[0].message_type == "mock_group_profile"
    assert first[0].channel == 1
    assert first[0].control == 0
    assert first[0].value == 0


def test_group_profile_2_message_contains_expected_metadata():
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


def test_mapped_messages_can_be_recorded_by_mock_sender_in_order():
    from rytm_randomizer.mock_message_mapper import map_group_profile_to_mock_messages
    from rytm_randomizer.mock_midi import MockMidiSender

    messages = map_group_profile_to_mock_messages("2")
    sender = MockMidiSender()

    sender.send_many(messages)

    assert sender.sent_messages == tuple(messages)


def test_unknown_group_profile_fails_safely():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )

    try:
        map_group_profile_to_mock_messages("DOES_NOT_EXIST")
    except MockMessageMappingError as exc:
        assert "Group profile 'DOES_NOT_EXIST' was not found" in str(exc)
    else:
        raise AssertionError("unknown group profile should fail safely")


def test_existing_but_unsupported_group_profile_fails_safely():
    from rytm_randomizer.mock_message_mapper import (
        MockMessageMappingError,
        map_group_profile_to_mock_messages,
    )

    try:
        map_group_profile_to_mock_messages("3")
    except MockMessageMappingError as exc:
        assert "Group profile '3' is not supported by the mock mapper" in str(exc)
    else:
        raise AssertionError("unsupported group profile should fail safely")


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.mock_message_mapper  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.mock_message_mapper as mapper

    module_text = "\n".join(
        [
            mapper.__doc__ or "",
            mapper.map_group_profile_to_mock_messages.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


def test_mock_message_mapper_exposes_no_active_behavior_names():
    import rytm_randomizer.mock_message_mapper as mapper

    exposed_names = set(dir(mapper))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


if __name__ == "__main__":
    test_importing_mock_message_mapper_prints_nothing()
    test_group_profile_2_maps_to_deterministic_mock_message()
    test_group_profile_2_message_contains_expected_metadata()
    test_mapped_messages_can_be_recorded_by_mock_sender_in_order()
    test_unknown_group_profile_fails_safely()
    test_existing_but_unsupported_group_profile_fails_safely()
    test_no_real_midi_library_is_imported()
    test_passive_cli_report_behavior_remains_unchanged()
    test_no_out_of_scope_support_is_exposed()
    test_mock_message_mapper_exposes_no_active_behavior_names()
