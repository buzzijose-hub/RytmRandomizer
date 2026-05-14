"""Behavior tests for the armed package entry point ``rytm_randomizer.app``.

These tests verify the WS-H convergence wiring:

* no flag -> passive menu, no MIDI port opened, no real MIDI library imported;
* ``--dry-run`` -> interactive logic runs against the in-memory mock sender,
  still no port opened and no real MIDI library imported;
* ``--arm`` -> the concrete ``mido``-backed real MIDI provider is constructed
  and asked for ports (verified without hardware by faking the ``mido``
  boundary).

Randomness is seeded so every test is deterministic.
"""

from pathlib import Path
import random
import subprocess
import sys
import types

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def _seed() -> None:
    random.seed(1734)


def run_python(code: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_app_module_import_is_side_effect_free_and_silent():
    result = run_python(
        """
import sys
import rytm_randomizer.app as app
import rytm_randomizer.real_midi_adapter as adapter
import rytm_randomizer.mido_provider as provider

assert app.__name__ == "rytm_randomizer.app"
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_app_main_no_flag_shows_passive_menu_and_opens_no_port(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "passive menu" in captured.out
    assert "no MIDI port opened" in captured.out
    assert "no MIDI sent" in captured.out
    # The passive menu reuses the read-only CLI machinery.
    assert "preview-group-profile" in captured.out
    assert "RytmRandomizer Project Status Summary" in captured.out
    # Active modes are advertised but not entered.
    assert "--arm" in captured.out
    assert "--dry-run" in captured.out
    assert captured.err == ""


def test_app_main_no_flag_imports_no_real_midi_library():
    result = run_python(
        """
import sys
from rytm_randomizer import app
exit_code = app.main([])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
# Default mode must not import the monolith either.
assert "rytm_hybrid_randomizer_v134" not in sys.modules
"""
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_dry_run_runs_against_mock_and_opens_no_port(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "MockMidiSender" in captured.out
    assert "no hardware, no port opened" in captured.out
    assert captured.err == ""


def test_app_main_dry_run_imports_no_real_midi_library():
    result = run_python(
        """
import sys
from rytm_randomizer import app
exit_code = app.main(["--dry-run"])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
"""
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_app_main_dry_run_exercises_mock_sender_boundary():
    """The dry-run path constructs a MockMidiSender and runs interactive logic.

    The monolith may expose ``run_with_sender`` (Wave 4+); when it does, the
    dry-run path must route the mock sender through it. We verify the wiring
    by injecting a fake monolith module so the test stays hardware-free and
    deterministic.
    """

    _seed()
    from rytm_randomizer import app
    from rytm_randomizer.mock_midi import MockMidiSender, build_cc_message

    seen = {}

    def fake_run_with_sender(sender):
        assert isinstance(sender, MockMidiSender)
        sender.send(build_cc_message(channel=0, control=16, value=0))
        seen["sender"] = sender
        return 0

    fake_module = types.ModuleType("rytm_hybrid_randomizer_v134")
    fake_module.run_with_sender = fake_run_with_sender
    original = sys.modules.get("rytm_hybrid_randomizer_v134")
    sys.modules["rytm_hybrid_randomizer_v134"] = fake_module
    try:
        exit_code = app.main(["--dry-run"])
    finally:
        if original is not None:
            sys.modules["rytm_hybrid_randomizer_v134"] = original
        else:
            sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    assert exit_code == 0
    assert isinstance(seen["sender"], MockMidiSender)
    assert len(seen["sender"].sent_messages) == 1


def test_app_main_arm_constructs_real_provider_and_requests_ports(capsys):
    """``--arm`` must construct the concrete mido-backed provider and ask it
    for output ports. We fake the ``mido`` boundary so no hardware is needed.
    """

    _seed()
    from rytm_randomizer import app, mido_provider

    requested = {"list_output_names": 0}
    real_list = mido_provider.MidoMidiPortProvider.list_output_names

    def fake_list(self):
        requested["list_output_names"] += 1
        return ("Fake Rytm Out",)

    fake_monolith = types.ModuleType("rytm_hybrid_randomizer_v134")

    def fake_main():
        return 0

    fake_monolith.main = fake_main

    original_monolith = sys.modules.get("rytm_hybrid_randomizer_v134")
    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    sys.modules["rytm_hybrid_randomizer_v134"] = fake_monolith
    try:
        exit_code = app.main(["--arm"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list
        if original_monolith is not None:
            sys.modules["rytm_hybrid_randomizer_v134"] = original_monolith
        else:
            sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert requested["list_output_names"] == 1
    assert "real MIDI provider ready" in captured.out
    assert "Fake Rytm Out" in captured.out


def test_app_main_arm_fails_safely_when_no_ports_available(capsys):
    """``--arm`` must fail with a non-zero exit code -- not crash -- when the
    real provider reports no available output ports."""

    _seed()
    from rytm_randomizer import app, mido_provider

    real_list = mido_provider.MidoMidiPortProvider.list_output_names

    def fake_empty_list(self):
        return ()

    mido_provider.MidoMidiPortProvider.list_output_names = fake_empty_list
    try:
        exit_code = app.main(["--arm"])
    finally:
        mido_provider.MidoMidiPortProvider.list_output_names = real_list

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no real MIDI output ports available" in captured.err


def test_mido_provider_imports_mido_lazily_not_at_module_load():
    """Importing ``mido_provider`` must not import ``mido``; the import is
    lazy and only happens when a provider method actually needs it."""

    result = run_python(
        """
import sys
import rytm_randomizer.mido_provider as mp

assert "mido" not in sys.modules, "mido imported at module load time"
provider = mp.build_mido_midi_port_provider()
assert isinstance(provider, mp.MidoMidiPortProvider)
# Still no mido until a method that needs it is called.
assert "mido" not in sys.modules, "mido imported by provider construction"
"""
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


if __name__ == "__main__":
    test_app_module_import_is_side_effect_free_and_silent()
    test_app_main_no_flag_imports_no_real_midi_library()
    test_app_main_dry_run_imports_no_real_midi_library()
    test_app_main_dry_run_exercises_mock_sender_boundary()
    test_mido_provider_imports_mido_lazily_not_at_module_load()
