"""Characterization + parity tests for MIDI I/O primitives.

These tests lock in the monolith's CURRENT behavior, then prove the extracted
``rytm_randomizer.midi_io`` module reproduces it byte-identically.

Two isolation rules (matching ``tests/test_data_layer.py``):

* Anything that imports the monolith (which does ``import mido`` at the top)
  is run in a *subprocess* so real ``mido`` never lands in this test
  process's ``sys.modules`` -- the package's import-safety tests depend on
  that staying clean.
* In-process package tests that exercise ``send_cc`` (which lazily imports
  ``mido``) inject a *fake* ``mido`` module; an autouse fixture snapshots and
  restores ``sys.modules`` so nothing leaks between tests.
"""

from __future__ import annotations

import sys
import subprocess
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

    Keeps real / fake ``mido`` (and the monolith) from leaking between tests.
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
        return (
            isinstance(other, _FakeMessage)
            and (self.type, self.channel, self.control, self.value)
            == (other.type, other.channel, other.control, other.value)
        )


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


def test_clamp_parity_with_monolith():
    """Subprocess parity: the monolith's clamp == the package's clamp."""

    result = _run_python(
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer.midi_io import clamp\n"
        "cases = [(5,0,10),(-3,0,10),(99,0,10),(0,0,10),(10,0,10),(7,7,7),"
        "(50,0,100),(-100,-10,-1)]\n"
        "assert all(m.clamp(*c) == clamp(*c) for c in cases)\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


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


def test_send_cc_parity_with_monolith():
    """Subprocess parity: monolith.send_cc and package send_cc agree on the
    constructed message fields (driven against the real ``mido``)."""

    result = _run_python(
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer import midi_io\n"
        "midi_io.time.sleep = lambda *_: None\n"
        "class Out:\n"
        "    def __init__(self): self.sent = []\n"
        "    def send(self, msg): self.sent.append(msg)\n"
        "a, b = Out(), Out()\n"
        "m.send_cc(a, 15, 64)\n"
        "midi_io.send_cc(b, 15, 64, channel=0)\n"
        "ma, mb = a.sent[0], b.sent[0]\n"
        "assert (ma.type, ma.channel, ma.control, ma.value) == "
        "(mb.type, mb.channel, mb.control, mb.value) == "
        "('control_change', 0, 15, 64)\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


# ===========================================================================
# send_machine / send_param -- subprocess parity (need monolith + real mido)
# ===========================================================================

def test_send_machine_parity_with_monolith():
    result = _run_python(
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer import midi_io\n"
        "from rytm_randomizer.data import PROFILES\n"
        "midi_io.time.sleep = lambda *_: None\n"
        "import io, contextlib\n"
        "class Out:\n"
        "    def __init__(self): self.sent = []\n"
        "    def send(self, msg): self.sent.append(msg)\n"
        "profile = dict(PROFILES['2']); profile['anchor'] = dict(profile['anchor'])\n"
        "m.active_profile = profile\n"
        "a = Out()\n"
        "buf_a = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf_a):\n"
        "    m.send_machine(a)\n"
        "b = Out()\n"
        "buf_b = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf_b):\n"
        "    midi_io.send_machine(b, profile, channel=0)\n"
        "assert buf_a.getvalue() == buf_b.getvalue()\n"
        "assert [(x.control, x.value) for x in a.sent] == "
        "[(x.control, x.value) for x in b.sent]\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def test_send_param_parity_with_monolith():
    result = _run_python(
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer import midi_io\n"
        "from rytm_randomizer.data import PROFILES\n"
        "midi_io.time.sleep = lambda *_: None\n"
        "import io, contextlib\n"
        "class Out:\n"
        "    def __init__(self): self.sent = []\n"
        "    def send(self, msg): self.sent.append(msg)\n"
        "profile = dict(PROFILES['2']); profile['anchor'] = dict(profile['anchor'])\n"
        "name = profile['order'][0]\n"
        "m.active_profile = profile\n"
        "a = Out(); buf_a = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf_a):\n"
        "    m.send_param(a, name, 42)\n"
        "b = Out(); buf_b = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf_b):\n"
        "    midi_io.send_param(b, profile, name, 42, channel=0)\n"
        "assert buf_a.getvalue() == buf_b.getvalue()\n"
        "assert [(x.control, x.value) for x in a.sent] == "
        "[(x.control, x.value) for x in b.sent]\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


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

def _monolith_apply_state_via_subprocess(state_repr, label, kwargs_repr):
    """Run the monolith's apply_state in a subprocess and return its result.

    Prints a repr dict the parent parses; keeps real mido out of this process.
    """

    code = (
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer import midi_io\n"
        "from rytm_randomizer.data import PROFILES\n"
        "midi_io.time.sleep = lambda *_: None\n"
        "import io, contextlib\n"
        "class Out:\n"
        "    def __init__(self): self.sent = []\n"
        "    def send(self, msg): self.sent.append(msg)\n"
        "profile = dict(PROFILES['2']); profile['anchor'] = dict(profile['anchor'])\n"
        "m.active_profile = profile\n"
        "m.anchor_state = dict(profile['anchor'])\n"
        "m.current_state = {}\n"
        "m.previous_state = None\n"
        f"state = {state_repr}\n"
        "out = Out()\n"
        "buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        f"    m.apply_state(out, state, {label!r}, **{kwargs_repr})\n"
        "import json\n"
        "print(json.dumps({\n"
        "    'output': buf.getvalue(),\n"
        "    'sent': [(x.control, x.value) for x in out.sent],\n"
        "    'anchor_state': m.anchor_state,\n"
        "    'current_state': m.current_state,\n"
        "    'previous_state': m.previous_state,\n"
        "    'profile_anchor': dict(m.active_profile['anchor']),\n"
        "}))\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    import json

    return json.loads(result.stdout)


def test_apply_state_parity_basic(capsys):
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = {name: 10 for name in pkg_profile["order"][:3]}

    mono = _monolith_apply_state_via_subprocess(repr(state), "Test Apply", "{}")

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

    assert pkg_output == mono["output"]
    assert [(m.control, m.value) for m in pkg_out.sent] == [
        tuple(pair) for pair in mono["sent"]
    ]
    assert result.applied is True
    assert result.current_state == mono["current_state"]
    assert result.previous_state == mono["previous_state"]
    assert result.anchor_state == mono["anchor_state"]


def test_apply_state_parity_set_anchor(capsys):
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = {name: 20 for name in pkg_profile["order"][:2]}

    mono = _monolith_apply_state_via_subprocess(
        repr(state), "Anchor Apply", "{'set_anchor': True}"
    )

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
    pkg_output = capsys.readouterr().out

    assert pkg_output == mono["output"]
    assert result.anchor_state == mono["anchor_state"] == state
    assert pkg_profile["anchor"] == mono["profile_anchor"] == state


def test_apply_state_parity_switch_machine_first(capsys):
    _install_fake_mido()
    from rytm_randomizer.midi_io import apply_state

    pkg_profile = _sample_profile()
    state = {name: 5 for name in pkg_profile["order"][:1]}

    mono = _monolith_apply_state_via_subprocess(
        repr(state), "Switch Apply", "{'switch_machine_first': True}"
    )

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
    pkg_output = capsys.readouterr().out

    assert pkg_output == mono["output"]
    assert [(m.control, m.value) for m in pkg_out.sent] == [
        tuple(pair) for pair in mono["sent"]
    ]
    assert result.applied is True


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
    state = {name: 15 for name in base["order"][:2]}

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


def test_monolith_apply_state_without_profile_parity():
    """The monolith prints the same require-profile message when no profile."""

    result = _run_python(
        "import rytm_hybrid_randomizer_v134 as m\n"
        "import io, contextlib\n"
        "class Out:\n"
        "    def __init__(self): self.sent = []\n"
        "    def send(self, msg): self.sent.append(msg)\n"
        "m.active_profile = None\n"
        "out = Out(); buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        "    m.apply_state(out, {}, 'No Profile')\n"
        "assert 'Select a profile first with P.' in buf.getvalue()\n"
        "assert out.sent == []\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


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
