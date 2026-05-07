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


if __name__ == "__main__":
    test_importing_active_boundary_prints_nothing()
    test_missing_arming_emits_no_messages()
    test_missing_dry_run_confirmation_emits_no_messages()
    test_unknown_key_emits_no_messages()
    test_profile_4_remains_parked_and_emits_no_messages()
    test_profile_2_emits_mock_messages_only_when_armed_and_confirmed()
    test_passive_cli_report_stays_read_only()
    test_no_real_midi_libraries_are_imported()
    test_no_active_cli_command_names_are_exposed()
