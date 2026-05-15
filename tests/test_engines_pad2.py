"""Characterization + parity tests for the Pad 2 engine (Wave 4 / WS-M).

These tests lock in the V1.34 monolith's CURRENT behavior for the ~9 Pad-2
functions, then prove the extracted :class:`rytm_randomizer.engines.pad2.Pad2Engine`
reproduces it byte-identically: same printed output, same MIDI message stream,
same resulting state dictionaries.

Isolation rules (matching ``tests/test_engines_pad1.py``):

* Anything that imports the monolith (which does ``import mido`` at module
  scope) runs in a *subprocess*, so real ``mido`` never lands in this test
  process's ``sys.modules``.
* That subprocess is a single **warm worker** reused across every parity check
  in this file (see ``tests/_parity_worker.py``): it cold-imports the monolith
  + package once, then services one parity request per stdin line. It seeds
  the stdlib ``random`` module identically before driving the monolith
  function and the engine method, captures stdout + the recorded MIDI messages
  for each, and asserts equality *inside* the worker.
* In-process tests exercise the engine with a *fake* ``mido`` module; an autouse
  fixture snapshots/restores ``sys.modules`` so nothing leaks.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# pytest puts this file's directory (``tests/``) on ``sys.path`` (prepend import
# mode, no ``tests/__init__.py``), so the shared helper imports as a top-level
# module without needing a package.
from _parity_worker import make_parity_subprocess, parse_steps  # noqa: E402


# ---------------------------------------------------------------------------
# Isolation helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot ``sys.modules`` and restore it after every test."""

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

    def __repr__(self):  # pragma: no cover - debugging aid only
        return (
            f"_FakeMessage({self.type!r}, channel={self.channel}, "
            f"control={self.control}, value={self.value})"
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


# Harness run once at warm-worker startup: imports the monolith + package, then
# defines ``assert_parity(seed, steps)`` which builds a monolith run and an
# engine run from the same RNG seed, captures stdout + MIDI messages + the
# relevant state dicts, and asserts byte-parity. The worker loop appended by
# ``tests/_parity_worker.py`` calls this once per JSON request line.
_HARNESS = '''
import io, contextlib, random
import rytm_hybrid_randomizer_v134 as m
from rytm_randomizer import midi_io, randomization
from rytm_randomizer.engines.pad2 import Pad2Engine, DEFAULT_PAD2_PROFILE_KEY

midi_io.time.sleep = lambda *_: None
randomization.time.sleep = lambda *_: None


class Out:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append((msg.type, msg.channel, msg.control, msg.value))


# Monolith Pad-2 functions that are pure status helpers and take NO ``out``
# argument (the engine versions are likewise argument-free methods).
_NO_OUT = {"show_pad2_tools"}


def _reset_monolith():
    """Restore the monolith globals the Pad-2 functions touch to cold start."""
    m.active_profile = None
    m.anchor_state = {}
    m.current_state = {}
    m.previous_state = None
    m.target_pad = 1
    m.channel = 0
    m.group_anchor_states = {}
    m.group_current_states = {}
    m.group_previous_states = {}
    m.pad2_current_profile_key = DEFAULT_PAD2_PROFILE_KEY


def run_monolith(seed, steps):
    """Drive a sequence of monolith Pad-2 calls; return (stdout, msgs, state)."""
    _reset_monolith()
    out = Out()
    random.seed(seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for fn_name, args in steps:
            if fn_name in _NO_OUT:
                getattr(m, fn_name)(*args)
            else:
                getattr(m, fn_name)(out, *args)
    state = {
        "active": m.active_profile["name"] if m.active_profile else None,
        "current": dict(m.current_state),
        "previous": dict(m.previous_state) if m.previous_state else m.previous_state,
        "target_pad": m.target_pad,
        "channel": m.channel,
        "key": m.pad2_current_profile_key,
        "gcur": {k: dict(v) for k, v in m.group_current_states.items()},
        "gprev": {
            k: (dict(v) if v else v) for k, v in m.group_previous_states.items()
        },
        "ganc": {k: dict(v) for k, v in m.group_anchor_states.items()},
    }
    return buf.getvalue(), out.sent, state


def run_engine(seed, steps):
    """Drive the same sequence on a Pad2Engine; return (stdout, msgs, state)."""
    out = Out()
    eng = Pad2Engine(out, sleep=lambda *_: None)
    random.seed(seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for fn_name, args in steps:
            getattr(eng, fn_name)(*args)
    state = {
        "active": eng.active_profile["name"] if eng.active_profile else None,
        "current": dict(eng.current_state),
        "previous": (
            dict(eng.previous_state) if eng.previous_state else eng.previous_state
        ),
        "target_pad": eng.target_pad,
        "channel": eng.channel,
        "key": eng.pad2_current_profile_key,
        "gcur": {k: dict(v) for k, v in eng.group_current_states.items()},
        "gprev": {
            k: (dict(v) if v else v) for k, v in eng.group_previous_states.items()
        },
        "ganc": {k: dict(v) for k, v in eng.group_anchor_states.items()},
    }
    return buf.getvalue(), out.sent, state


def assert_parity(seed, steps):
    mo, mm, ms = run_monolith(seed, steps)
    eo, em, es = run_engine(seed, steps)
    assert mo == eo, "stdout mismatch:\\n--MONOLITH--\\n" + mo + "\\n--ENGINE--\\n" + eo
    assert mm == em, "midi mismatch:\\n" + repr(mm) + "\\n" + repr(em)
    assert ms == es, "state mismatch:\\n" + repr(ms) + "\\n" + repr(es)
'''


# The warm worker for this file: ``_parity_worker`` is a module-scoped autouse
# fixture that launches/owns it and tears it down at module teardown;
# ``_run_parity`` ships one JSON request to it and asserts the parity check
# passed (a mismatch re-raises the worker's diff as an AssertionError -- same
# failure semantics as the old "fresh interpreter per call" version).
_parity_worker, _run_parity = make_parity_subprocess(_HARNESS)


def _parity_subprocess(steps_repr: str, seed: int = 12345) -> None:
    """Run the harness against ``steps`` on the warm worker; assert parity.

    ``steps_repr`` is still a Python source repr of the steps list (exactly as
    every ``test_parity_*`` function builds it). ``parse_steps`` turns that same
    literal -- the one the old code string-concatenated into
    ``assert_parity(seed, <steps_repr>)`` -- into the real object, which is then
    shipped as JSON so the warm worker receives structured data instead of
    source text.
    """

    _run_parity({"seed": seed, "steps": parse_steps(steps_repr)})


# ===========================================================================
# In-process import-safety + smoke
# ===========================================================================

def test_import_is_silent_and_mido_free(capsys):
    """Importing the engine module opens no ports and pulls in no mido."""

    sys.modules.pop("rytm_randomizer.engines.pad2", None)
    sys.modules.pop("mido", None)
    import rytm_randomizer.engines.pad2 as pad2  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules


def test_engine_constructs_with_monolith_cold_start_defaults():
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import DEFAULT_PAD2_PROFILE_KEY, Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)

    assert eng.active_profile is None
    assert eng.current_state == {}
    assert eng.previous_state is None
    assert eng.target_pad == 1
    assert eng.channel == 0
    assert eng.group_current_states == {}
    # Monolith cold-start Pad 2 profile: BD Classic rolling low percussion.
    assert eng.pad2_current_profile_key == "3"
    assert DEFAULT_PAD2_PROFILE_KEY == "3"


# ===========================================================================
# In-process behavior coverage (fake mido) -- every method + every branch
# ===========================================================================

def test_load_pad2_profile_unknown_key(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad2_profile("does-not-exist")
    out = capsys.readouterr().out

    assert "Unknown Pad 2 profile key: does-not-exist" in out
    assert eng.active_profile is None


def test_load_pad2_profile_unassigned_key(capsys):
    """A real profile that is not in the Pad 2 foundation lane is rejected."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    # "2" (My BD Hard) is a real profile but not a PAD2_PROFILE_KEYS member.
    eng.load_pad2_profile("2")
    out = capsys.readouterr().out

    assert "is not assigned to the Pad 2 foundation lane" in out
    assert eng.active_profile is None


@pytest.mark.parametrize("profile_key", ["3", "9", "10", "11"])
def test_load_pad2_profile_loads_anchor_and_records_group_state(
    profile_key, capsys
):
    _install_fake_mido()
    from rytm_randomizer.data import PROFILES
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile(profile_key)
    text = capsys.readouterr().out

    assert (
        f"Loading Pad 2 profiled engine: {PROFILES[profile_key]['name']}"
        in text
    )
    assert eng.pad2_current_profile_key == profile_key
    assert eng.target_pad == 2
    assert eng.channel == 1
    assert 2 in eng.group_current_states
    assert eng.group_previous_states[2] is None
    assert 2 in eng.group_anchor_states
    # The machine CC switch went out.
    assert any(msg.control == 15 for msg in out.sent)


def test_show_pad2_tools_cold(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.show_pad2_tools()
    text = capsys.readouterr().out

    assert "Pad 2 Snare / Secondary Percussion Tools - V1.34" in text
    assert " < current" in text  # the default key is in the rotation order
    assert "not loaded yet" in text  # group_current_states is empty


def test_show_pad2_tools_loaded_snapshot(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad2_profile("9")
    capsys.readouterr()
    eng.show_pad2_tools()
    text = capsys.readouterr().out

    assert "Current Pad 2 state snapshot:" in text


def test_show_pad2_tools_unknown_key(capsys):
    """When ``pad2_current_profile_key`` is not a real profile, the
    'Unknown' branch of the current-profile block runs."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key="nope"
    )
    eng.show_pad2_tools()
    text = capsys.readouterr().out

    assert "Unknown. Use P2B, P2H, P2C, or P2F." in text


def test_show_pad2_tools_loaded_partial_state_skips_absent(capsys):
    """When ``group_current_states[2]`` lacks some ordered names, the snapshot
    loop skips them (the absent-name branch of ``if name in state``)."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(),
        sleep=_no_sleep,
        pad2_current_profile_key="3",
        group_current_states={2: {"SRC Tune": 60}},
    )
    eng.show_pad2_tools()
    text = capsys.readouterr().out

    assert "Current Pad 2 state snapshot:" in text
    assert "SRC Tune: 60" in text


def test_mutate_current_pad2_profile_no_valid_profile(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(
        out, sleep=_no_sleep, pad2_current_profile_key="not-a-profile"
    )
    eng.mutate_current_pad2_profile("body", "groove", "Test")
    text = capsys.readouterr().out

    assert "No valid Pad 2 profile selected" in text
    assert out.sent == []


def test_mutate_current_pad2_profile_unsupported_zone(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep, pad2_current_profile_key="3")
    eng.mutate_current_pad2_profile(
        "not-a-real-zone", "groove", "Bad Zone Test"
    )
    text = capsys.readouterr().out

    assert "does not support zone: not-a-real-zone" in text
    assert out.sent == []


def test_mutate_current_pad2_profile_runs_and_records_state(capsys):
    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("3")
    out.sent.clear()
    capsys.readouterr()

    random.seed(99)
    eng.mutate_current_pad2_profile("body", "groove", "Body Test")
    text = capsys.readouterr().out

    assert "Pad 2 Body Test" in text
    assert "discovery command complete" in text
    assert out.sent  # machine CC + parameter CCs
    assert eng.group_current_states[2] == eng.current_state


def test_mutate_current_pad2_profile_grit_triggers_floor(capsys):
    """The grit zone path runs ``enforce_pad2_grit_floor`` after mutation."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("9")  # SD Hard has a grit zone
    capsys.readouterr()

    # Force overdrive below the anchor so the floor correction fires.
    profile_anchor_od = eng.active_profile["anchor"].get("AMP Overdrive")
    if profile_anchor_od is not None:
        eng.current_state["AMP Overdrive"] = 0
        eng.group_current_states[2]["AMP Overdrive"] = 0

    out.sent.clear()
    random.seed(5)
    eng.mutate_current_pad2_profile("grit", "groove", "Grit Test")
    text = capsys.readouterr().out

    assert "discovery command complete" in text


def test_enforce_pad2_grit_floor_no_active_profile():
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.active_profile = None
    eng.enforce_pad2_grit_floor()
    assert out.sent == []


def test_enforce_pad2_grit_floor_param_not_in_params():
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    # A profile whose params dict has no "AMP Overdrive".
    eng.active_profile = {"params": {}, "anchor": {}, "safe": {}}
    eng.enforce_pad2_grit_floor()
    assert out.sent == []


def test_enforce_pad2_grit_floor_param_not_in_anchor():
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    # "AMP Overdrive" is in params but absent from anchor.
    eng.active_profile = {
        "params": {"AMP Overdrive": 16},
        "anchor": {},
        "safe": {},
    }
    eng.enforce_pad2_grit_floor()
    assert out.sent == []


def test_enforce_pad2_grit_floor_current_at_or_above_anchor():
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.active_profile = {
        "params": {"AMP Overdrive": 16},
        "anchor": {"AMP Overdrive": 40},
        "safe": {},
    }
    # current >= anchor -> no correction.
    eng.current_state = {"AMP Overdrive": 50}
    eng.enforce_pad2_grit_floor()
    assert out.sent == []


def test_enforce_pad2_grit_floor_corrects_below_anchor():
    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.active_profile = {
        "params": {"AMP Overdrive": 16},
        "anchor": {"AMP Overdrive": 40},
        "safe": {"AMP Overdrive": (0, 127)},
    }
    eng.current_state = {"AMP Overdrive": 5}
    random.seed(1)
    eng.enforce_pad2_grit_floor()

    assert len(out.sent) == 1
    assert out.sent[0].control == 16
    assert eng.current_state["AMP Overdrive"] >= 40


def test_enforce_pad2_grit_floor_current_param_absent_uses_anchor():
    """When ``current_state`` has no overdrive value it defaults to the anchor,
    so ``current_od >= anchor_od`` holds and nothing is sent."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.active_profile = {
        "params": {"AMP Overdrive": 16},
        "anchor": {"AMP Overdrive": 40},
        "safe": {},
    }
    eng.current_state = {}
    eng.enforce_pad2_grit_floor()
    assert out.sent == []


def test_rotate_pad2_profile_from_unprofiled_returns_home(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key="5"
    )
    eng.rotate_pad2_profile()
    text = capsys.readouterr().out

    assert "not currently on a profiled secondary-lane engine" in text
    assert eng.pad2_current_profile_key == "3"


def test_rotate_pad2_profile_advances(capsys):
    _install_fake_mido()
    from rytm_randomizer.data import PAD2_PROFILE_KEYS
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad2_profile("3")  # index 0
    capsys.readouterr()
    eng.rotate_pad2_profile()
    assert eng.pad2_current_profile_key == PAD2_PROFILE_KEYS[1]


def test_rotate_pad2_profile_wraps(capsys):
    _install_fake_mido()
    from rytm_randomizer.data import PAD2_PROFILE_KEYS
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad2_profile(PAD2_PROFILE_KEYS[-1])
    capsys.readouterr()
    eng.rotate_pad2_profile()
    assert eng.pad2_current_profile_key == PAD2_PROFILE_KEYS[0]


def test_mutate_current_pad2_rotation_profile_no_valid_profile(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key="nope"
    )
    eng.mutate_current_pad2_rotation_profile()
    assert "No valid Pad 2 profile selected" in capsys.readouterr().out


def test_mutate_current_pad2_rotation_profile_no_plan(capsys):
    """A real profile with no PAD2_MUTATION_PLANS entry hits the no-plan branch."""

    _install_fake_mido()
    from rytm_randomizer.data import PAD2_MUTATION_PLANS, PROFILES
    from rytm_randomizer.engines.pad2 import Pad2Engine

    # Find a real profile key that is not in PAD2_MUTATION_PLANS.
    no_plan_key = next(
        k for k in PROFILES if k not in PAD2_MUTATION_PLANS
    )
    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key=no_plan_key
    )
    eng.mutate_current_pad2_rotation_profile()
    assert "does not have a P2X mutation plan yet" in capsys.readouterr().out


def test_mutate_current_pad2_rotation_profile_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key="3"
    )
    # Valid profile with a plan, but Pad 2 state never loaded.
    eng.mutate_current_pad2_rotation_profile()
    assert "Pad 2 state is not loaded yet" in capsys.readouterr().out


def test_mutate_current_pad2_rotation_profile_runs(capsys):
    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("3")
    out.sent.clear()
    capsys.readouterr()
    random.seed(3)
    eng.mutate_current_pad2_rotation_profile()
    text = capsys.readouterr().out

    assert "Pad 2 Current Profile Mutation - V1.26" in text
    assert "discovery command complete" in text


@pytest.mark.parametrize(
    "discovery_method",
    [
        "pad2_tone_discovery",
        "pad2_pressure_body_discovery",
        "pad2_grit_noise_discovery",
    ],
)
def test_discovery_helpers_run(discovery_method, capsys):
    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("9")  # SD Hard supports snap/body/grit
    out.sent.clear()
    capsys.readouterr()
    random.seed(7)
    getattr(eng, discovery_method)()
    text = capsys.readouterr().out

    assert "discovery command complete" in text
    assert out.sent


def test_pad2_tone_discovery_falls_back_to_src_zone(capsys):
    """When the current profile has no ``snap`` zone, tone discovery uses
    the ``src`` zone instead."""

    _install_fake_mido()
    import random

    from rytm_randomizer.data import PROFILES
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("3")  # BD Classic -- no "snap" zone
    assert "snap" not in PROFILES["3"]["zones"]
    out.sent.clear()
    capsys.readouterr()
    random.seed(11)
    eng.pad2_tone_discovery()
    text = capsys.readouterr().out

    assert "Mutation plan: src / groove" in text


def test_return_pad2_to_current_anchor_no_valid_profile(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(
        RecordingOut(), sleep=_no_sleep, pad2_current_profile_key="nope"
    )
    eng.return_pad2_to_current_anchor()
    assert "No valid Pad 2 profile selected" in capsys.readouterr().out


def test_return_pad2_to_current_anchor_runs(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("3")
    out.sent.clear()
    capsys.readouterr()
    eng.return_pad2_to_current_anchor()
    text = capsys.readouterr().out

    assert "Returning Pad 2 current profile to anchor:" in text
    assert "Pad 2 returned to current profile anchor" in text
    assert 2 in eng.group_current_states
    assert eng.group_previous_states[2] is None
    assert any(msg.control == 15 for msg in out.sent)


def test_mutate_records_none_previous_when_falsy(capsys):
    """``mutate_current_pad2_profile`` stores ``None`` when previous_state is
    falsy (the ``else`` arm of the previous-state write-back)."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad2 import Pad2Engine

    out = RecordingOut()
    eng = Pad2Engine(out, sleep=_no_sleep)
    eng.load_pad2_profile("3")
    capsys.readouterr()
    eng.previous_state = None
    eng.group_previous_states[2] = None
    random.seed(1)
    eng.mutate_current_pad2_profile("body", "groove", "Falsy Prev Test")
    capsys.readouterr()
    assert 2 in eng.group_previous_states


def test_apply_state_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_apply_state`` with no active profile is a
    no-op write-back (mirrors the monolith ``require_profile`` guard)."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)
    before_anchor = dict(eng.anchor_state)

    eng._apply_state({"SRC Tune": 60}, "No Profile")

    assert eng.current_state == before_current
    assert eng.anchor_state == before_anchor
    assert eng.previous_state is None
    capsys.readouterr()


def test_mutate_zone_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_mutate_zone`` with no active profile leaves
    current/previous state untouched."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad2 import Pad2Engine

    eng = Pad2Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)

    eng._mutate_zone("body", "micro")

    assert eng.current_state == before_current
    assert eng.previous_state is None
    capsys.readouterr()


# ===========================================================================
# Subprocess parity vs the committed monolith -- byte-identical behavior
# ===========================================================================

def test_parity_load_each_profile():
    for key in ["3", "9", "10", "11"]:
        _parity_subprocess(f"[('load_pad2_profile', ({key!r},))]")


def test_parity_load_unknown_and_unassigned_keys():
    _parity_subprocess("[('load_pad2_profile', ('nope',))]")
    _parity_subprocess("[('load_pad2_profile', ('2',))]")


def test_parity_show_pad2_tools_cold():
    _parity_subprocess("[('show_pad2_tools', ())]")


def test_parity_show_pad2_tools_after_load():
    for key in ["3", "9", "10", "11"]:
        _parity_subprocess(
            f"[('load_pad2_profile', ({key!r},)), ('show_pad2_tools', ())]"
        )


def test_parity_mutate_current_pad2_profile_guards():
    # no valid profile -- never loaded, default key "3" IS valid, so drive it
    # onto an invalid zone instead for the unsupported-zone guard.
    _parity_subprocess(
        "[('mutate_current_pad2_profile', ('not-a-zone', 'groove', 'Z'))]"
    )


def test_parity_discovery_helpers():
    for key in ["3", "9", "10", "11"]:
        for fn in [
            "pad2_tone_discovery",
            "pad2_pressure_body_discovery",
            "pad2_grit_noise_discovery",
        ]:
            for seed in (1, 2, 5, 11, 42):
                _parity_subprocess(
                    f"[('load_pad2_profile', ({key!r},)), ({fn!r}, ())]",
                    seed=seed,
                )


def test_parity_discovery_helpers_cold():
    # Discovery helpers fired before any load: default key "3" is valid, so
    # they actually run against BD Classic from the cold-start key.
    for fn in [
        "pad2_tone_discovery",
        "pad2_pressure_body_discovery",
        "pad2_grit_noise_discovery",
    ]:
        for seed in (1, 7, 42):
            _parity_subprocess(f"[({fn!r}, ())]", seed=seed)


def test_parity_rotation():
    # from cold start (BD Classic home)
    _parity_subprocess("[('rotate_pad2_profile', ())]")
    # full walk around the rotation ring
    _parity_subprocess(
        "[('rotate_pad2_profile', ()), ('rotate_pad2_profile', ()), "
        "('rotate_pad2_profile', ()), ('rotate_pad2_profile', ()), "
        "('rotate_pad2_profile', ())]"
    )


def test_parity_mutate_current_pad2_rotation_profile():
    # not loaded guard (default key valid + has a plan, but no group state)
    _parity_subprocess("[('mutate_current_pad2_rotation_profile', ())]")
    # loaded then mutate
    for key in ["3", "9", "10", "11"]:
        for seed in (1, 2, 5, 11, 42):
            _parity_subprocess(
                f"[('load_pad2_profile', ({key!r},)), "
                "('mutate_current_pad2_rotation_profile', ())]",
                seed=seed,
            )


def test_parity_return_to_anchor():
    for key in ["3", "9", "10", "11"]:
        _parity_subprocess(
            f"[('load_pad2_profile', ({key!r},)), "
            "('return_pad2_to_current_anchor', ())]"
        )


def test_parity_long_interactive_session():
    """A realistic multi-step Pad 2 session: load, discover, rotate, mutate."""

    steps = (
        "["
        "('load_pad2_profile', ('9',)), "
        "('pad2_tone_discovery', ()), "
        "('pad2_grit_noise_discovery', ()), "
        "('mutate_current_pad2_rotation_profile', ()), "
        "('rotate_pad2_profile', ()), "
        "('show_pad2_tools', ()), "
        "('pad2_pressure_body_discovery', ()), "
        "('rotate_pad2_profile', ()), "
        "('return_pad2_to_current_anchor', ()), "
        "('mutate_current_pad2_rotation_profile', ())"
        "]"
    )
    for seed in (1, 7, 99, 2024):
        _parity_subprocess(steps, seed=seed)
