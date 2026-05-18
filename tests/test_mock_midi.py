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


def test_importing_mock_midi_prints_nothing():
    result = subprocess.run(
        [sys.executable, "-c", "import rytm_randomizer.mock_midi"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_midi_message_can_represent_intended_cc_message():
    from rytm_randomizer.mock_midi import MidiMessage, build_cc_message

    direct_message = MidiMessage(
        message_type="cc",
        channel=1,
        control=15,
        value=0,
        metadata={"command": "BH", "pad": 1},
    )
    helper_message = build_cc_message(
        channel=1,
        control=15,
        value=0,
        metadata={"command": "BH", "pad": 1},
    )

    assert direct_message == helper_message
    assert direct_message.message_type == "cc"
    assert direct_message.channel == 1
    assert direct_message.control == 15
    assert direct_message.value == 0
    assert direct_message.metadata == {"command": "BH", "pad": 1}


def test_mock_midi_sender_starts_empty():
    from rytm_randomizer.mock_midi import MockMidiSender

    sender = MockMidiSender()

    assert sender.sent_messages == ()
    assert sender.messages == ()


def test_send_records_one_message_in_memory_only():
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    sender = MockMidiSender()
    message = build_cc_message(channel=1, control=15, value=0)

    sender.send(message)

    assert sender.sent_messages == (message,)
    assert sender.messages == (message,)


def test_send_many_records_messages_in_order():
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    sender = MockMidiSender()
    first = build_cc_message(channel=1, control=15, value=0, metadata={"step": 1})
    second = build_cc_message(channel=1, control=16, value=64, metadata={"step": 2})

    sender.send_many([first, second])

    assert sender.sent_messages == (first, second)


def test_clear_removes_recorded_messages():
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    sender = MockMidiSender()
    sender.send(build_cc_message(channel=1, control=15, value=0))

    sender.clear()

    assert sender.sent_messages == ()


def test_recorded_messages_are_isolated_from_source_metadata_mutation():
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    sender = MockMidiSender()
    metadata = {"command": "BH", "pad": 1}
    message = build_cc_message(channel=1, control=15, value=0, metadata=metadata)

    sender.send(message)
    metadata["pad"] = 5

    assert sender.sent_messages[0].metadata == {"command": "BH", "pad": 1}


def test_no_real_midi_library_is_imported():
    import rytm_randomizer.mock_midi  # noqa: F401

    assert "mido" not in sys.modules
    assert "rtmidi" not in sys.modules


def test_invalid_message_values_fail_deterministically():
    from rytm_randomizer.mock_midi import build_cc_message

    try:
        build_cc_message(channel="1", control=15, value=0)
    except TypeError as exc:
        assert "channel must be an integer" in str(exc)
    else:
        raise AssertionError("non-integer channel should fail")


def test_passive_cli_report_behavior_remains_unchanged():
    result = run_cli("report")

    assert result.returncode == 0
    assert normalize_newlines(result.stdout) == fixture_text("registry_report_expected.txt")
    assert result.stderr == ""


def test_no_out_of_scope_support_is_exposed():
    import rytm_randomizer.mock_midi as mock_midi

    module_text = "\n".join(
        [
            mock_midi.__doc__ or "",
            mock_midi.MidiMessage.__doc__ or "",
            mock_midi.MockMidiSender.__doc__ or "",
        ]
    )

    assert "Analog Four support" not in module_text
    assert "Pads 5-12 support" not in module_text


def test_mock_midi_module_exposes_no_active_behavior_names():
    import rytm_randomizer.mock_midi as mock_midi

    exposed_names = set(dir(mock_midi))

    assert "execute_command" not in exposed_names
    assert "send_command" not in exposed_names
    assert "hardware_test" not in exposed_names


if __name__ == "__main__":
    test_importing_mock_midi_prints_nothing()
    test_midi_message_can_represent_intended_cc_message()
    test_mock_midi_sender_starts_empty()
    test_send_records_one_message_in_memory_only()
    test_send_many_records_messages_in_order()
    test_clear_removes_recorded_messages()
    test_recorded_messages_are_isolated_from_source_metadata_mutation()
    test_no_real_midi_library_is_imported()
    test_invalid_message_values_fail_deterministically()
    test_passive_cli_report_behavior_remains_unchanged()
    test_no_out_of_scope_support_is_exposed()
    test_mock_midi_module_exposes_no_active_behavior_names()
