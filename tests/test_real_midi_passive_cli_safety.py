import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CLI_SOURCE = PROJECT_ROOT / "rytm_randomizer" / "cli.py"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PASSIVE_CLI_COMMANDS = (
    ("--help",),
    ("report",),
    ("mock-mapper-report",),
    ("active-boundary-report",),
    ("rytm-12-pad-machine-matrix-report",),
    ("inspect-group-profile", "2"),
    ("preview-group-profile", "2"),
)
PASSIVE_CLI_SWEEP_COMMANDS = (
    ("--help",),
    ("report",),
    ("list-commands",),
    ("list-scenes",),
    ("list-group-profiles",),
    ("search-commands", "BD"),
    ("search-scenes", "Wild"),
    ("search-group-profiles", "BD"),
    ("inspect-command", "J"),
    ("inspect-scene", "S1A"),
    ("inspect-group-profile", "2"),
    ("preview-command", "J"),
    ("preview-scene", "S1A"),
    ("preview-group-profile", "2"),
    ("mock-mapper-report",),
    ("active-boundary-report",),
    ("rytm-12-pad-machine-matrix-report",),
)
FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)

FORBIDDEN_CLI_SOURCE_TOKENS = (
    "MockMidiSender(",
    "RealMidiPortProvider",
    "RealMidiSender(",
    "build_real_midi_sender",
    "real_midi_adapter",
    "evaluate_mock_active_boundary",
    "open_output",
    "open_input",
    "get_output_names",
    "get_input_names",
    "open_midi_port",
    "send_midi",
    "execute-command",
    "send-command",
    "hardware-test",
)

FORBIDDEN_CLI_OUTPUT_TOKENS = (
    "execute-command",
    "send-command",
    "hardware-test",
    "--armed",
    "--port",
    "mido",
)


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_in_process_and_check_no_real_midi(*args):
    code = f"""
import sys
from rytm_randomizer import cli
exit_code = cli.main({list(args)!r})
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def run_cli_in_process_and_check_no_real_midi_or_adapter_modules(*args):
    code = f"""
import sys
from rytm_randomizer import cli
import pytest

exit_code = cli.main({list(args)!r})
assert exit_code == 0, exit_code
for module_name in {FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES!r}:
    assert module_name not in sys.modules, module_name
"""
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_representative_passive_cli_commands_do_not_import_real_midi_libraries():
    for command in PASSIVE_CLI_COMMANDS:
        result = run_cli_in_process_and_check_no_real_midi(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""


def test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules():
    for command in PASSIVE_CLI_SWEEP_COMMANDS:
        result = run_cli_in_process_and_check_no_real_midi_or_adapter_modules(*command)

        assert result.returncode == 0, (command, result.stderr)
        assert result.stderr == ""


def test_passive_cli_sweep_exposes_no_active_or_port_commands():
    for command in PASSIVE_CLI_SWEEP_COMMANDS:
        result = run_cli(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""
        for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
            assert token not in result.stdout, (command, token)


def test_passive_cli_source_does_not_construct_senders_or_evaluate_boundary():
    source = CLI_SOURCE.read_text(encoding="utf-8")

    for token in FORBIDDEN_CLI_SOURCE_TOKENS:
        assert token not in source, token


def test_top_level_help_exposes_no_active_or_port_commands():
    result = run_cli("--help")

    assert result.returncode == 0
    assert result.stderr == ""
    for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
        assert token not in result.stdout, token


def test_passive_report_outputs_expose_no_active_or_port_commands():
    for command in (
        ("report",),
        ("mock-mapper-report",),
        ("active-boundary-report",),
    ):
        result = run_cli(*command)

        assert result.returncode == 0, command
        assert result.stderr == ""
        for token in FORBIDDEN_CLI_OUTPUT_TOKENS:
            assert token not in result.stdout, (command, token)


if __name__ == "__main__":
    test_representative_passive_cli_commands_do_not_import_real_midi_libraries()
    test_passive_cli_sweep_does_not_import_real_midi_or_adapter_modules()
    test_passive_cli_sweep_exposes_no_active_or_port_commands()
    test_passive_cli_source_does_not_construct_senders_or_evaluate_boundary()
    test_top_level_help_exposes_no_active_or_port_commands()
    test_passive_report_outputs_expose_no_active_or_port_commands()
