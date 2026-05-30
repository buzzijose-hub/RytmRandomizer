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

import random
import subprocess
import sys
import types
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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
    result = run_python("""
import sys
import rytm_randomizer.app as app
import rytm_randomizer.real_midi_adapter as adapter
import rytm_randomizer.mido_provider as provider

assert app.__name__ == "rytm_randomizer.app"
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

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
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main([])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
# Default mode must not import the monolith either.
assert "rytm_hybrid_randomizer_v134" not in sys.modules
""")

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


def test_app_main_dry_run_accepts_operator_profile_then_quit(monkeypatch, capsys):
    """A real dry-run operator flow must not crash after profile selection."""

    _seed()
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        sys.modules.pop(module_name, None)

    from rytm_randomizer import app

    scripted_inputs = iter(["1", "1", "Q"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Selected profile: My BD Hard" in captured.out
    assert "Dry-run complete." in captured.out
    assert captured.err == ""
    for module_name in ("mido", "rtmidi", "pythonrtmidi"):
        assert module_name not in sys.modules, module_name


def test_app_main_dry_run_imports_no_real_midi_library():
    result = run_python("""
import sys
from rytm_randomizer import app
exit_code = app.main(["--dry-run"])
assert exit_code == 0, exit_code
for module_name in ("mido", "rtmidi", "pythonrtmidi"):
    assert module_name not in sys.modules, module_name
""")

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

    result = run_python("""
import sys
import rytm_randomizer.mido_provider as mp


assert "mido" not in sys.modules, "mido imported at module load time"
provider = mp.build_mido_midi_port_provider()
assert isinstance(provider, mp.MidoMidiPortProvider)
# Still no mido until a method that needs it is called.
assert "mido" not in sys.modules, "mido imported by provider construction"
""")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


# ---------------------------------------------------------------------------
# Additional coverage for ``rytm_randomizer.app`` (--arm port-open path,
# ``_choose_arm_port_name`` defensive branches, --dry-run EOF/Ctrl-C
# swallowing, and argparse-level flag conflicts).
# ---------------------------------------------------------------------------


class _FakeOutputPort:
    """Duck-types a ``mido`` output port with ``send`` + ``close``."""

    def __init__(self) -> None:
        self.sent: list = []
        self.closed = False

    def send(self, message) -> None:
        self.sent.append(message)

    def close(self) -> None:
        self.closed = True


class _FakeInputPort:
    """Duck-types a ``mido`` input port with ``iter_pending`` + ``close``."""

    def __init__(self, messages) -> None:
        self._messages = tuple(messages)
        self.closed = False

    def iter_pending(self):
        return iter(self._messages)

    def close(self) -> None:
        self.closed = True


def _restore_provider_methods(saved):
    """Helper to restore previously monkey-patched provider class attributes."""

    from rytm_randomizer import mido_provider

    for name, value in saved.items():
        setattr(mido_provider.MidoMidiPortProvider, name, value)


def test_app_main_a4_soft_capture_requires_arm(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-soft-capture requires --arm" in captured.err


def test_app_main_rytm_cc_observe_requires_arm(capsys):
    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--rytm-cc-observe"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-cc-observe requires --arm" in captured.err


def test_app_main_arm_rytm_cc_observe_opens_only_input_and_reports(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    message = types.SimpleNamespace(
        type="control_change",
        channel=1,
        control=20,
        value=25,
    )
    fake_input = _FakeInputPort((message,))

    def fake_list_input_names(self):
        return ("Fake Rytm In",)

    def fake_open_input(self, port_name):
        assert port_name == "Fake Rytm In"
        return fake_input

    def fail_output_call(self, *_args):
        raise AssertionError("Rytm CC observe must not touch MIDI outputs")

    scripted_inputs = iter(["0", ""])
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        fake_list_input_names,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fake_open_input)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        fail_output_call,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_output_call)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(["--arm", "--rytm-cc-observe"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_input.closed is True
    assert "Rytm CC observe" in captured.out
    assert "Input: Fake Rytm In" in captured.out
    assert "Opened output: False" in captured.out
    assert "Sent MIDI: False" in captured.out
    assert "- Pad 2 (channel 1) CC20 value 25" in captured.out
    assert "machine:dual_vco:Osc 2 Detune" in captured.out
    assert captured.err == ""


def test_app_main_rytm_cc_observe_rejects_validate_one_cc_before_output(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("flag conflict must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_input_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--rytm-cc-observe",
            "--validate-one-cc",
            "--channel",
            "1",
            "--control",
            "20",
            "--value",
            "25",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--rytm-cc-observe cannot be combined with --validate-one-cc" in captured.err


def test_app_main_arm_a4_soft_capture_opens_only_input_and_reports(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    message = types.SimpleNamespace(
        type="control_change",
        channel=0,
        control=72,
        value=96,
    )
    fake_input = _FakeInputPort((message,))

    def fake_list_input_names(self):
        return ("Fake A4 In",)

    def fake_open_input(self, port_name):
        assert port_name == "Fake A4 In"
        return fake_input

    def fail_output_call(self, *_args):
        raise AssertionError("A4 soft capture must not touch MIDI outputs")

    scripted_inputs = iter(["0", ""])
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        fake_list_input_names,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fake_open_input)
    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_output_names",
        fail_output_call,
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_output_call)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(scripted_inputs))

    exit_code = app.main(["--arm", "--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert fake_input.closed is True
    assert "A4 soft live capture" in captured.out
    assert "Input: Fake A4 In" in captured.out
    assert "Opened output: False" in captured.out
    assert "Sent MIDI: False" in captured.out
    assert "Track 1: 1 observed params" in captured.out
    assert "- OSC1 Pulsewidth: 96" in captured.out
    assert captured.err == ""


def test_app_main_arm_a4_soft_capture_no_input_ports_returns_one(monkeypatch, capsys):
    _seed()
    from rytm_randomizer import app, mido_provider

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda _self: (),
    )

    exit_code = app.main(["--arm", "--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "no real MIDI input ports available" in captured.err


def test_app_main_arm_a4_soft_capture_invalid_input_choice_returns_one(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    def fail_open_input(self, *_args):
        raise AssertionError("invalid choice must not open input")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda _self: ("Fake A4 In",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fail_open_input)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")

    exit_code = app.main(["--arm", "--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid MIDI input choice" in captured.err


def test_app_main_arm_a4_soft_capture_negative_input_choice_returns_one(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    def fail_open_input(self, *_args):
        raise AssertionError("negative choice must not open input")

    monkeypatch.setattr(
        mido_provider.MidoMidiPortProvider,
        "list_input_names",
        lambda _self: ("Fake A4 In",),
    )
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fail_open_input)
    monkeypatch.setattr("builtins.input", lambda _prompt="": "-1")

    exit_code = app.main(["--arm", "--a4-soft-capture"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid MIDI input choice" in captured.err


def test_app_main_a4_soft_capture_rejects_validate_one_cc_before_output(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("flag conflict must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_input_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--a4-soft-capture",
            "--validate-one-cc",
            "--channel",
            "0",
            "--control",
            "72",
            "--value",
            "96",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-soft-capture cannot be combined with --validate-one-cc" in captured.err


def test_app_main_a4_soft_capture_rejects_a4_send_param_before_output(
    monkeypatch,
    capsys,
):
    _seed()
    from rytm_randomizer import app, mido_provider

    def fail_midi_call(self, *_args):
        raise AssertionError("flag conflict must not touch MIDI ports")

    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_input_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_input", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "list_output_names", fail_midi_call)
    monkeypatch.setattr(mido_provider.MidoMidiPortProvider, "open_output", fail_midi_call)

    exit_code = app.main(
        [
            "--arm",
            "--a4-soft-capture",
            "--a4-send-param",
            "--parameter",
            "OSC1 PWM Depth",
            "--channel",
            "0",
            "--value",
            "32",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "--a4-soft-capture cannot be combined with --a4-send-param" in captured.err


def test_app_main_arm_list_output_names_dependency_error_exits_one(capsys):
    """``--arm`` must exit cleanly with code 1 if list_output_names raises
    ``RealMidiDependencyError`` (covers the early ``except`` arm)."""

    _seed()
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiDependencyError

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def raise_dep(self):
        raise RealMidiDependencyError("mido_not_installed")

    mido_provider.MidoMidiPortProvider.list_output_names = raise_dep
    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "mido_not_installed" in captured.err


def test_app_main_arm_list_output_names_port_error_exits_one(capsys):
    """``--arm`` must exit cleanly with code 1 if list_output_names raises
    ``RealMidiPortError`` (covers the second branch of the same except)."""

    _seed()
    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def raise_port(self):
        raise RealMidiPortError("midi_output_discovery_failed")

    mido_provider.MidoMidiPortProvider.list_output_names = raise_port
    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "midi_output_discovery_failed" in captured.err


def test_app_main_arm_production_path_opens_port_and_runs_shell(monkeypatch, capsys):
    """``--arm`` production path: choose a port, open it, run the package
    shell, then close the port in the ``finally`` block. No real MIDI
    library, no real ``input()`` -- the provider methods and ``build_shell``
    are both faked at the boundary."""

    _seed()
    # Guarantee no test fake monolith lingers, so the production hook fires.
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer import shell as shellmod

    saved = {
        "list_output_names": mido_provider.MidoMidiPortProvider.list_output_names,
        "open_output": mido_provider.MidoMidiPortProvider.open_output,
    }

    fake_port = _FakeOutputPort()
    opened: dict = {}

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_open(self, port_name):
        opened["port_name"] = port_name
        return fake_port

    class _StubShell:
        def __init__(self, port) -> None:
            self.port = port

        def run(self) -> int:
            # The shell would normally drive the menu; emulate a clean quit.
            return 0

    def fake_build_shell(port, **_kwargs):
        return _StubShell(port)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    # The arm path prompts for an output index via ``input``.
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")
    monkeypatch.setattr(shellmod, "build_shell", fake_build_shell)

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 0
    assert opened["port_name"] == "Fake Rytm Out"
    # The fake port was passed through ``finally`` and closed best-effort.
    assert fake_port.closed is True
    assert "real MIDI provider ready" in captured.out
    assert "Opening MIDI output: Fake Rytm Out" in captured.out


def test_app_main_arm_open_output_failure_exits_one(monkeypatch, capsys):
    """If ``open_output`` raises ``RealMidiPortError`` after a valid choice,
    ``--arm`` must exit with code 1 and print the failure to stderr."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider
    from rytm_randomizer.real_midi_adapter import RealMidiPortError

    saved = {
        "list_output_names": mido_provider.MidoMidiPortProvider.list_output_names,
        "open_output": mido_provider.MidoMidiPortProvider.open_output,
    }

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_open(self, port_name):
        raise RealMidiPortError(f"unavailable_midi_output_port: {port_name}")

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fake_open
    monkeypatch.setattr("builtins.input", lambda _prompt="": "0")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "--arm failed" in captured.err
    assert "unavailable_midi_output_port" in captured.err


def test_app_main_arm_port_choice_eof_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch EOFError on stdin and return None
    so ``--arm`` exits with code 1 instead of crashing."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fake_input(_prompt=""):
        raise EOFError

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", fake_input)

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "no MIDI output choice provided" in captured.err
    # The available outputs list must still have printed before the prompt.
    assert "0: Fake Rytm Out" in captured.out


def test_app_main_arm_port_choice_invalid_input_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch ValueError on non-numeric input
    and return None so ``--arm`` exits with code 1."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", lambda _prompt="": "not-a-number")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_arm_port_choice_out_of_range_returns_one(monkeypatch, capsys):
    """``_choose_arm_port_name`` must catch IndexError when the chosen
    number is past the end of the output names list."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {"list_output_names": mido_provider.MidoMidiPortProvider.list_output_names}

    def fake_list(self):
        return ("Fake Rytm Out",)

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    monkeypatch.setattr("builtins.input", lambda _prompt="": "42")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_arm_port_choice_negative_input_returns_one(monkeypatch, capsys):
    """Negative output choices must not select from the end of the port list."""

    _seed()
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app, mido_provider

    saved = {
        "list_output_names": mido_provider.MidoMidiPortProvider.list_output_names,
        "open_output": mido_provider.MidoMidiPortProvider.open_output,
    }

    def fake_list(self):
        return ("Fake Rytm Out",)

    def fail_open(self, *_args):
        raise AssertionError("negative output choice must not open output")

    mido_provider.MidoMidiPortProvider.list_output_names = fake_list
    mido_provider.MidoMidiPortProvider.open_output = fail_open
    monkeypatch.setattr("builtins.input", lambda _prompt="": "-1")

    try:
        exit_code = app.main(["--arm"])
    finally:
        _restore_provider_methods(saved)

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "invalid MIDI output choice" in captured.err


def test_app_main_dry_run_swallows_eof_from_shell(monkeypatch, capsys):
    """If the shell's input raises EOFError after the dry-run boot, the
    --dry-run handler must swallow it and report a clean exit with the
    final ``Dry-run complete.`` summary line. Covers the EOF/KeyboardInterrupt
    arm of ``_run_dry_run``."""

    _seed()
    # Defensive: make sure no test fake monolith intercepts the path.
    sys.modules.pop("rytm_hybrid_randomizer_v134", None)

    from rytm_randomizer import app
    from rytm_randomizer import shell as shellmod

    class _RaisingShell:
        def __init__(self, sender) -> None:
            self.sender = sender

        def run(self) -> int:
            raise EOFError

    def fake_build_shell(sender, **_kwargs):
        return _RaisingShell(sender)

    monkeypatch.setattr(shellmod, "build_shell", fake_build_shell)

    exit_code = app.main(["--dry-run"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Dry-run complete." in captured.out
    assert "0 message(s)" in captured.out


def test_app_main_arm_and_dry_run_are_mutually_exclusive(capsys):
    """argparse must reject ``--arm --dry-run`` with SystemExit code 2."""

    import pytest

    from rytm_randomizer import app

    with pytest.raises(SystemExit) as exc_info:
        app.main(["--arm", "--dry-run"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    # argparse writes its conflict message to stderr.
    assert "not allowed with argument" in captured.err or "--dry-run" in captured.err


def test_app_main_unknown_flag_is_rejected_by_argparse(capsys):
    """Unknown CLI flags trigger argparse's normal error exit (code 2)."""

    import pytest

    from rytm_randomizer import app

    with pytest.raises(SystemExit) as exc_info:
        app.main(["--nope"])

    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "unrecognized arguments" in captured.err or "--nope" in captured.err


def test_app_main_passive_with_debug_and_log_json_flags(capsys):
    """``--debug --log-json`` must be accepted in the default/passive mode
    and configure the logger without crashing. The user-visible passive
    menu still prints to stdout."""

    _seed()
    from rytm_randomizer import app

    exit_code = app.main(["--debug", "--log-json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "passive menu" in captured.out


if __name__ == "__main__":
    test_app_module_import_is_side_effect_free_and_silent()
    test_app_main_no_flag_imports_no_real_midi_library()
    test_app_main_dry_run_imports_no_real_midi_library()
    test_app_main_dry_run_exercises_mock_sender_boundary()
    test_mido_provider_imports_mido_lazily_not_at_module_load()
