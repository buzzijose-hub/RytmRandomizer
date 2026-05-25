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

PASSIVE_AND_MOCK_MODULES = (
    "rytm_randomizer.cli",
    "rytm_randomizer.mock_midi",
    "rytm_randomizer.mock_message_mapper",
    "rytm_randomizer.active_boundary",
    "rytm_randomizer.reports",
)

SOURCE_FILES = (
    PROJECT_ROOT / "rytm_randomizer" / "cli.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_midi.py",
    PROJECT_ROOT / "rytm_randomizer" / "mock_message_mapper.py",
    PROJECT_ROOT / "rytm_randomizer" / "active_boundary.py",
    PROJECT_ROOT / "rytm_randomizer" / "reports/__init__.py",
)

FORBIDDEN_REAL_MIDI_TOKENS = (
    "import mido",
    "from mido",
    "import rtmidi",
    "from rtmidi",
    "open_output",
    "open_input",
    "get_output_names",
    "get_input_names",
    "open_midi_port",
    "send_midi",
    "MidiPortProvider",
    "RealMidiSender",
    "execute-command",
    "send-command",
    "hardware-test",
)


def run_python(code):
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_passive_and_mock_imports_print_nothing():
    imports = "\n".join(f"import {module}" for module in PASSIVE_AND_MOCK_MODULES)
    result = run_python(imports)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_passive_and_mock_imports_do_not_import_real_midi_libraries():
    imports = "\n".join(f"import {module}" for module in PASSIVE_AND_MOCK_MODULES)
    code = f"""
import sys
import pytest

{imports}
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""

    result = run_python(code)

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_passive_and_mock_sources_expose_no_real_midi_affordances():
    for path in SOURCE_FILES:
        source = path.read_text(encoding="utf-8")
        for token in FORBIDDEN_REAL_MIDI_TOKENS:
            assert token not in source, f"{token!r} found in {path}"


def test_active_boundary_scope_remains_profile_2_only():
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

    unsupported_3_sender = MockMidiSender()
    unsupported_3 = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="3",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        unsupported_3_sender,
    )

    unsupported_4_sender = MockMidiSender()
    unsupported_4 = evaluate_mock_active_boundary(
        ActiveBoundaryRequest(
            source_kind="group_profile",
            source_key="4",
            armed=True,
            dry_run_confirmed=True,
            target="mock",
        ),
        unsupported_4_sender,
    )

    assert accepted.accepted is True
    assert accepted.emitted_messages != ()
    assert accepted_sender.sent_messages == accepted.emitted_messages
    assert unsupported_3.accepted is False
    assert unsupported_3.emitted_messages == ()
    assert unsupported_3_sender.sent_messages == ()
    assert unsupported_4.accepted is False
    assert unsupported_4.emitted_messages == ()
    assert unsupported_4_sender.sent_messages == ()


if __name__ == "__main__":
    test_passive_and_mock_imports_print_nothing()
    test_passive_and_mock_imports_do_not_import_real_midi_libraries()
    test_passive_and_mock_sources_expose_no_real_midi_affordances()
    test_active_boundary_scope_remains_profile_2_only()
