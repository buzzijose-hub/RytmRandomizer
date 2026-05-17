import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLOSEOUT_SCRIPT = PROJECT_ROOT / "Scripts" / "closeout_check.ps1"
V134_REFERENCE = PROJECT_ROOT / "rytm_hybrid_randomizer_v134.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PASSIVE_MODULES = (
    "rytm_randomizer.cli",
    "rytm_randomizer.mock_midi",
    "rytm_randomizer.mock_message_mapper",
    "rytm_randomizer.active_boundary",
    "rytm_randomizer.reports",
)

PASSIVE_CLI_COMMANDS = (
    ("report",),
    ("mock-mapper-report",),
    ("active-boundary-report",),
    ("preview-group-profile", "2"),
)

PASSIVE_SOURCE_FILES = (
    PROJECT_ROOT / "rytm_randomizer" / "cli.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_midi.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_message_mapper.py",
    PROJECT_ROOT / "rytm_randomizer" / "active_boundary.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports.py",
)

FORBIDDEN_SOURCE_TOKENS = (
    "rytm_randomizer.real_midi_adapter",
    "RealMidi",
    "MidiPortProvider",
    "open_output",
    "open_input",
    "get_output_names",
    "get_input_names",
    "execute-command",
    "send-command",
    "hardware-test",
)

FORBIDDEN_IMPORTED_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def run_python(code):
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_real_midi_adapter_import_is_side_effect_free():
    result = run_python("""
import sys
import rytm_randomizer.real_midi_adapter as adapter

assert adapter.__name__ == "rytm_randomizer.real_midi_adapter"
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


class FakeOutputPort:
    def __init__(self):
        self.sent = []

    def send(self, message):
        self.sent.append(message)


def test_build_real_midi_sender_requires_explicit_provider():
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError, build_real_midi_sender

    try:
        build_real_midi_sender(provider=None, port_name="Fake Rytm")
    except RealMidiDependencyError as exc:
        assert str(exc) == "real_midi_provider_required"
    else:
        raise AssertionError("expected RealMidiDependencyError")


def test_real_midi_port_provider_unknown_port_fails_safely():
    from rytm_randomizer.real_midi_adapter import RealMidiPortError, RealMidiPortProvider

    provider = RealMidiPortProvider(output_names=("Fake Rytm",), ports={})

    try:
        provider.open_output("Missing Port")
    except RealMidiPortError as exc:
        assert str(exc) == "unknown_midi_output_port: Missing Port"
    else:
        raise AssertionError("expected RealMidiPortError")


def test_real_midi_port_provider_rejects_configured_port_without_send():
    from rytm_randomizer.real_midi_adapter import RealMidiPortError, RealMidiPortProvider

    provider = RealMidiPortProvider(
        output_names=("Fake Rytm",),
        ports={"Fake Rytm": object()},
    )

    try:
        provider.open_output("Fake Rytm")
    except RealMidiPortError as exc:
        assert str(exc) == "invalid_midi_output_port: Fake Rytm"
    else:
        raise AssertionError("expected RealMidiPortError")


def test_real_midi_sender_records_to_fake_port_only():
    from rytm_randomizer.mock_midi import build_cc_message
    from rytm_randomizer.real_midi_adapter import RealMidiPortProvider, build_real_midi_sender

    fake_port = FakeOutputPort()
    provider = RealMidiPortProvider(
        output_names=("Fake Rytm",),
        ports={"Fake Rytm": fake_port},
    )
    sender = build_real_midi_sender(provider=provider, port_name="Fake Rytm")
    message = build_cc_message(
        channel=0,
        control=16,
        value=0,
        metadata={
            "source_kind": "group_profile",
            "source_key": "2",
            "mock_only": True,
            "sends_real_midi": False,
        },
    )

    result = sender.send_messages([message])

    assert result.port_name == "Fake Rytm"
    assert result.message_count == 1
    assert result.sent_real_midi is False
    assert fake_port.sent == [
        {
            "message_type": "cc",
            "channel": 0,
            "control": 16,
            "value": 0,
            "metadata": dict(message.metadata),
        }
    ]


def test_real_midi_sender_rejects_unsupported_message_type():
    from rytm_randomizer.mock_midi import MidiMessage
    from rytm_randomizer.real_midi_adapter import (
        RealMidiPortProvider,
        RealMidiSendError,
        build_real_midi_sender,
    )

    fake_port = FakeOutputPort()
    provider = RealMidiPortProvider(
        output_names=("Fake Rytm",),
        ports={"Fake Rytm": fake_port},
    )
    sender = build_real_midi_sender(provider=provider, port_name="Fake Rytm")
    message = MidiMessage(message_type="note_on", channel=0, control=16, value=1)

    try:
        sender.send_messages([message])
    except RealMidiSendError as exc:
        assert str(exc) == "unsupported_midi_message_type: note_on"
    else:
        raise AssertionError("expected RealMidiSendError")

    assert fake_port.sent == []


def test_real_midi_adapter_exposes_explicit_public_api():
    import rytm_randomizer.real_midi_adapter as adapter

    assert adapter.__all__ == [
        "RealMidiDependencyError",
        "RealMidiOutputPort",
        "RealMidiPortError",
        "RealMidiPortProvider",
        "RealMidiSendError",
        "RealMidiSendResult",
        "RealMidiSender",
        "build_real_midi_sender",
    ]


def test_passive_imports_do_not_load_adapter_or_real_midi_modules():
    imports = "\n".join(f"import {module}" for module in PASSIVE_MODULES)
    checks = "\n".join(
        f"assert {module_name!r} not in sys.modules, {module_name!r}"
        for module_name in FORBIDDEN_IMPORTED_MODULES
    )
    result = run_python(f"""
import sys
{imports}
{checks}
""")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_passive_cli_commands_do_not_load_adapter_or_real_midi_modules():
    result = run_python(f"""
import sys
from rytm_randomizer import cli
commands = {PASSIVE_CLI_COMMANDS!r}
for command in commands:
    exit_code = cli.main(list(command))
    assert exit_code == 0, command
for module_name in {FORBIDDEN_IMPORTED_MODULES!r}:
    assert module_name not in sys.modules, module_name
""")

    assert result.returncode == 0
    assert result.stderr == ""


def test_passive_sources_do_not_reference_adapter_or_port_affordances():
    for path in PASSIVE_SOURCE_FILES:
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_SOURCE_TOKENS:
            assert token not in source, f"{token!r} found in {path}"


def test_active_boundary_scope_still_rejects_profiles_3_and_4():
    from rytm_randomizer.active_boundary import ActiveBoundaryRequest, evaluate_mock_active_boundary
    from rytm_randomizer.mock_midi import MockMidiSender

    accepted_sender = MockMidiSender()
    accepted = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="2",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        accepted_sender,
    )

    unsupported_results = []
    for key in ("3", "4"):
        sender = MockMidiSender()
        result = evaluate_mock_active_boundary(
            ActiveBoundaryRequest(
                source_kind="group_profile",
                source_key=key,
                armed=True,
                dry_run_confirmed=True,
                target="mock",
            ),
            sender,
        )
        unsupported_results.append((result, sender))

    assert accepted.accepted is True
    assert accepted_sender.sent_messages == accepted.emitted_messages
    for result, sender in unsupported_results:
        assert result.accepted is False
        assert result.emitted_messages == ()
        assert sender.sent_messages == ()


def test_closeout_includes_real_midi_adapter_boundary_label():
    closeout_source = CLOSEOUT_SCRIPT.read_text(encoding="utf-8")

    assert "=== Test: Real MIDI Adapter Boundary ===" in closeout_source
    assert "test_real_midi_adapter_boundary.py" in closeout_source


def test_v134_reference_has_no_working_tree_diff():
    result = subprocess.run(
        ["git", "diff", "--", str(V134_REFERENCE.relative_to(PROJECT_ROOT))],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


if __name__ == "__main__":
    test_real_midi_adapter_import_is_side_effect_free()
    test_build_real_midi_sender_requires_explicit_provider()
    test_real_midi_port_provider_unknown_port_fails_safely()
    test_real_midi_port_provider_rejects_configured_port_without_send()
    test_real_midi_sender_records_to_fake_port_only()
    test_real_midi_sender_rejects_unsupported_message_type()
    test_real_midi_adapter_exposes_explicit_public_api()
    test_passive_imports_do_not_load_adapter_or_real_midi_modules()
    test_passive_cli_commands_do_not_load_adapter_or_real_midi_modules()
    test_passive_sources_do_not_reference_adapter_or_port_affordances()
    test_active_boundary_scope_still_rejects_profiles_3_and_4()
    test_closeout_includes_real_midi_adapter_boundary_label()
    test_v134_reference_has_no_working_tree_diff()
