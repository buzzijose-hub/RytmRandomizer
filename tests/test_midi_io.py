"""Characterization tests for MIDI I/O primitives.

These tests lock in the behavior of ``rytm_randomizer.midi_io`` against the
V1.34 reference. The reference used to be the live ``rytm_hybrid_randomizer_v134``
monolith driven via subprocess parity; the monolith has been retired and the
captured per-call goldens for engine/runner behavior now live under
``tests/fixtures/v134_parity/`` (see ``tests/_parity_worker.py``).

Isolation rule still applies: in-process package tests that exercise
``send_cc`` (which lazily imports ``mido``) inject a *fake* ``mido`` module;
an autouse fixture snapshots and restores ``sys.modules`` so nothing leaks
between tests.
"""

from __future__ import annotations

import subprocess
import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# Isolation helpers
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot ``sys.modules`` and restore it after every test.

    Keeps real / fake ``mido`` from leaking between tests.
    """

    snapshot = dict(sys.modules)
    try:
        yield
    finally:
        for name in list(sys.modules):
            if name not in snapshot:
                del sys.modules[name]
        for name, module in snapshot.items():
            sys.modules[name] = module


class _FakeMessage:
    """Records the same fields a ``mido.Message`` would expose."""

    def __init__(self, message_type, *, channel, control, value):
        self.type = message_type
        self.channel = channel
        self.control = control
        self.value = value

    def __eq__(self, other):
        return isinstance(other, _FakeMessage) and (
            self.type,
            self.channel,
            self.control,
            self.value,
        ) == (other.type, other.channel, other.control, other.value)


def _install_fake_mido():
    """Install an inert fake ``mido`` so ``send_cc`` builds no real message."""

    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    return fake


class RecordingOut:
    """Minimal stand-in for a mido output port; records sent messages."""

    def __init__(self) -> None:
        self.sent: list[object] = []

    def send(self, message: object) -> None:
        self.sent.append(message)


def _no_sleep(_seconds: float) -> None:
    return None


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    """Run a snippet in a fresh interpreter (keeps this process mido-free)."""

    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _sample_profile() -> dict:
    from rytm_randomizer.data import PROFILES

    profile = dict(PROFILES["2"])  # My BD Hard
    profile["anchor"] = dict(profile["anchor"])
    return profile


# ===========================================================================
# clamp -- pure, no mido, safe to compare in-process via subprocess parity
# ===========================================================================


def test_clamp_pure_values():
    from rytm_randomizer.midi_io import clamp

    assert clamp(5, 0, 10) == 5
    assert clamp(-3, 0, 10) == 0
    assert clamp(99, 0, 10) == 10
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10
    assert clamp(7, 7, 7) == 7


# ===========================================================================
# send_cc -- in-process with a FAKE mido, plus subprocess parity vs monolith
# ===========================================================================


def test_send_cc_builds_cc_message_and_sleeps():
    _install_fake_mido()
    from rytm_randomizer.midi_io import send_cc

    out = RecordingOut()
    sleeps: list[float] = []
    send_cc(out, 15, 64, channel=0, sleep=sleeps.append)

    assert len(out.sent) == 1
    msg = out.sent[0]
    assert msg.type == "control_change"
    assert msg.channel == 0
    assert msg.control == 15
    assert msg.value == 64
    assert sleeps == [0.02]


def test_send_cc_respects_injected_channel():
    _install_fake_mido()
    from rytm_randomizer.midi_io import send_cc

    out = RecordingOut()
    send_cc(out, 20, 100, channel=3, sleep=_no_sleep)

    assert out.sent[0].channel == 3


# ===========================================================================
# send_machine / send_param / apply_state -- in-process branch coverage with
# a fake mido (capsys captures the printed output for assertions).
# ===========================================================================


def test_send_machine_in_process(capsys):
    _install_fake_mido()
    from rytm_randomizer.midi_io import send_machine

    profile = _sample_profile()
    out = RecordingOut()
    send_machine(out, profile, channel=0, sleep=_no_sleep)
    output = capsys.readouterr().out

    assert "Switching Rytm machine to" in output
    assert "Machine CC15 ->" in output
    assert len(out.sent) == 1


def test_send_param_in_process(capsys):
    _install_fake_mido()
    from rytm_randomizer.midi_io import send_param

    profile = _sample_profile()
    name = profile["order"][0]
    out = RecordingOut()
    send_param(out, profile, name, 42, channel=0, sleep=_no_sleep)
    output = capsys.readouterr().out

    assert f"{name}: CC" in output
    assert out.sent[0].value == 42


# --- apply_state ----------------------------------------------------------


def test_apply_state_basic_smoke(capsys):
    """Cold-state ``apply_state``: every step in the state dict is emitted."""
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = dict.fromkeys(pkg_profile["order"][:3], 10)

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        pkg_profile,
        state,
        "Test Apply",
        anchor_state=dict(pkg_profile["anchor"]),
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
    )
    pkg_output = capsys.readouterr().out

    assert result.applied is True
    assert result.current_state == state
    assert result.previous_state is None
    # Three params were applied. The label appears as a header in the printed log.
    assert len(pkg_out.sent) == 3
    assert "Test Apply:" in pkg_output
    for name in pkg_profile["order"][:3]:
        assert f"{name}: CC" in pkg_output


def test_apply_state_set_anchor(capsys):
    """``set_anchor=True`` writes the supplied state into the profile anchor."""
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = dict.fromkeys(pkg_profile["order"][:2], 20)

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        pkg_profile,
        state,
        "Anchor Apply",
        anchor_state=dict(pkg_profile["anchor"]),
        current_state={},
        previous_state=None,
        set_anchor=True,
        channel=0,
        sleep=_no_sleep,
    )
    capsys.readouterr()

    assert result.anchor_state == state
    assert pkg_profile["anchor"] == state


def test_apply_state_switch_machine_first(capsys):
    """``switch_machine_first=True`` emits the CC15 machine switch before params."""
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = dict.fromkeys(pkg_profile["order"][:1], 5)

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        pkg_profile,
        state,
        "Switch Apply",
        anchor_state=dict(pkg_profile["anchor"]),
        current_state={},
        previous_state=None,
        switch_machine_first=True,
        channel=0,
        sleep=_no_sleep,
    )
    capsys.readouterr()

    assert result.applied is True
    assert pkg_out.sent[0].control == 15


def test_apply_state_previous_state_carry(capsys):
    """When current_state is non-empty it is copied into previous_state."""
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    name0 = pkg_profile["order"][0]
    state = {name0: 30}
    seeded_current = {name0: 99}

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        pkg_profile,
        state,
        "Carry Apply",
        anchor_state=dict(pkg_profile["anchor"]),
        current_state=dict(seeded_current),
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
    )
    capsys.readouterr()

    assert result.previous_state == seeded_current
    assert result.current_state == state


def test_apply_state_without_profile_returns_not_applied(capsys):
    from rytm_randomizer.midi_io import apply_state

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        None,
        {},
        "No Profile",
        anchor_state={},
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
    )
    output = capsys.readouterr().out

    assert result.applied is False
    assert pkg_out.sent == []
    assert "Select a profile first with P." in output


def test_apply_state_set_anchor_with_immutable_profile(capsys):
    """set_anchor on a read-only (non-MutableMapping) profile still updates the
    returned anchor_state without trying to write into the profile."""
    from types import MappingProxyType

    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    base = _sample_profile()
    immutable_profile = MappingProxyType(base)
    state = dict.fromkeys(base["order"][:2], 15)

    pkg_out = RecordingOut()
    result = apply_state(
        pkg_out,
        immutable_profile,
        state,
        "Immutable Anchor",
        anchor_state=dict(base["anchor"]),
        current_state={},
        previous_state=None,
        set_anchor=True,
        channel=0,
        sleep=_no_sleep,
    )
    output = capsys.readouterr().out

    assert result.applied is True
    assert result.anchor_state == state
    assert "  Anchor updated." in output


# ===========================================================================
# import safety
# ===========================================================================


def test_importing_midi_io_prints_nothing():
    result = _run_python("import rytm_randomizer.midi_io")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_midi_io_does_not_import_mido():
    """Importing the module must not pull in a real MIDI library."""

    result = _run_python(
        "import sys\n"
        "import rytm_randomizer.midi_io\n"
        "assert 'mido' not in sys.modules\n"
        "assert 'rtmidi' not in sys.modules\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"
