"""Characterization + parity tests for the Pad 1 BD engine (Wave 4 / WS-M).

These tests lock in the V1.34 monolith's CURRENT behavior for the ~27 Pad-1
functions, then prove the extracted :class:`rytm_randomizer.engines.pad1.Pad1Engine`
reproduces it byte-identically: same printed output, same MIDI message stream,
same resulting state dictionaries.

Isolation rules (matching ``tests/test_midi_io.py`` / ``tests/test_data_layer.py``):

* Anything that imports the monolith (which does ``import mido`` at module
  scope) runs in a *subprocess*, so real ``mido`` never lands in this test
  process's ``sys.modules`` -- the package import-safety tests depend on that.
* That subprocess is a single **warm worker** reused across every parity check
  in this file (see ``tests/_parity_worker.py``): it cold-imports the monolith
  + package once, then services one parity request per stdin line. The worker
  seeds the stdlib ``random`` module identically before driving the monolith
  function and the engine method, captures stdout + the recorded MIDI messages
  for each, and asserts equality *inside* the worker; ``_parity_subprocess``
  just ships one JSON request and asserts the check passed.
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
        return isinstance(other, _FakeMessage) and (
            self.type,
            self.channel,
            self.control,
            self.value,
        ) == (other.type, other.channel, other.control, other.value)

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
from rytm_randomizer.engines.pad1 import Pad1Engine, default_group_layout

midi_io.time.sleep = lambda *_: None
randomization.time.sleep = lambda *_: None


class Out:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append((msg.type, msg.channel, msg.control, msg.value))


# Monolith Pad-1 functions that are pure status/guard helpers and take NO
# ``out`` argument (the engine versions are likewise argument-free methods).
_NO_OUT = {
    "show_bd_engine_tools",
    "show_bd_fm_tools",
    "show_bd_plastic_tools",
    "show_bd_silky_tools",
    "show_bd_rotation_status",
    "require_pad1_bd_fm_context",
    "require_pad1_bd_plastic_context",
    "require_pad1_bd_silky_context",
}


def _reset_monolith():
    """Restore the monolith globals the Pad-1 functions touch to cold start."""
    m.active_profile = None
    m.anchor_state = {}
    m.current_state = {}
    m.previous_state = None
    m.target_pad = 1
    m.channel = 0
    m.group_anchor_states = {}
    m.group_current_states = {}
    m.group_previous_states = {}
    m.GROUP_LAYOUT = {pad: dict(cfg) for pad, cfg in default_group_layout().items()}


def run_monolith(seed, steps):
    """Drive a sequence of monolith Pad-1 calls; return (stdout, msgs, state)."""
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
        "layout1": dict(m.GROUP_LAYOUT[1]),
        "gcur": {k: dict(v) for k, v in m.group_current_states.items()},
        "gprev": {
            k: (dict(v) if v else v) for k, v in m.group_previous_states.items()
        },
        "ganc": {k: dict(v) for k, v in m.group_anchor_states.items()},
    }
    return buf.getvalue(), out.sent, state


def run_engine(seed, steps):
    """Drive the same sequence on a Pad1Engine; return (stdout, msgs, state)."""
    out = Out()
    eng = Pad1Engine(out, sleep=lambda *_: None)
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
        "layout1": dict(eng.group_layout[1]),
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

    sys.modules.pop("rytm_randomizer.engines.pad1", None)
    sys.modules.pop("mido", None)
    import rytm_randomizer.engines.pad1 as pad1  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules


def test_engine_constructs_with_monolith_cold_start_defaults():
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine, default_group_layout

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)

    assert eng.active_profile is None
    assert eng.current_state == {}
    assert eng.previous_state is None
    assert eng.target_pad == 1
    assert eng.channel == 0
    assert eng.group_current_states == {}
    assert eng.group_layout == default_group_layout()
    # Monolith cold-start Pad 1 layout: My BD Hard.
    assert eng.group_layout[1]["profile"] == "2"


def test_default_group_layout_is_a_fresh_mutable_copy():
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import default_group_layout

    a = default_group_layout()
    b = default_group_layout()
    a[1]["profile"] = "MUTATED"
    assert b[1]["profile"] == "2"


# ===========================================================================
# In-process behavior coverage (fake mido) -- every method + every branch
# ===========================================================================


def test_load_pad1_bd_profile_unknown_key(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile("does-not-exist")
    out = capsys.readouterr().out

    assert "Unknown profile key: does-not-exist" in out
    assert eng.active_profile is None


def test_load_pad1_bd_profile_loads_anchor_and_records_group_state(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile("6")  # BD FM
    text = capsys.readouterr().out

    assert "Loading Pad 1 profiled BD engine: BD FM Metallic Kick" in text
    assert eng.group_layout[1]["profile"] == "6"
    assert eng.group_layout[1]["role"] == "Main kick / BD FM Metallic Kick"
    assert eng.group_layout[1]["zone"] == "full"
    assert eng.group_layout[1]["depth"] == "micro"
    assert eng.target_pad == 1
    assert eng.channel == 0
    assert 1 in eng.group_current_states
    assert eng.group_previous_states[1] is None
    assert 1 in eng.group_anchor_states
    # The machine CC switch went out.
    assert any(msg.control == 15 for msg in out.sent)


def test_switch_pad1_extra_bd_machine_only_unknown_command(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    # BD_EXTRA_MACHINES ships empty, so every key hits the unknown branch.
    eng.switch_pad1_extra_bd_machine_only("ZZ")
    text = capsys.readouterr().out

    assert "Unknown BD engine command: ZZ" in text
    assert out.sent == []


def test_switch_pad1_extra_bd_machine_only_known_command(capsys):
    """Cover the populated branch by injecting a fake BD_EXTRA_MACHINES entry."""

    _install_fake_mido()
    from rytm_randomizer.data import BD_EXTRA_MACHINES
    from rytm_randomizer.engines.pad1 import Pad1Engine

    fake_machine = {"name": "BD Test", "role": "test role", "machine_value": 99}
    BD_EXTRA_MACHINES["TT"] = fake_machine
    try:
        out = RecordingOut()
        eng = Pad1Engine(out, sleep=_no_sleep)
        eng.switch_pad1_extra_bd_machine_only("TT")
        text = capsys.readouterr().out
    finally:
        del BD_EXTRA_MACHINES["TT"]

    assert "Switching Pad 1 to BD Test" in text
    assert "Role: test role" in text
    assert "Machine CC15 -> 99" in text
    assert eng.target_pad == 1
    assert eng.channel == 0
    assert [m.control for m in out.sent] == [15]
    assert out.sent[0].value == 99


def test_show_bd_engine_tools_runs(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.show_bd_engine_tools()
    text = capsys.readouterr().out

    assert "BD Engine Tools - V1.34" in text
    assert "Pad 1 BD Engine Rotation - V1.34" in text  # show_bd_rotation_status


def test_show_bd_rotation_status_not_loaded_vs_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.show_bd_rotation_status()
    assert "not loaded yet" in capsys.readouterr().out

    eng.load_pad1_bd_profile("2")
    capsys.readouterr()
    eng.show_bd_rotation_status()
    text = capsys.readouterr().out
    assert "Current Pad 1 loaded state: My BD Hard" in text
    assert "< current" in text


@pytest.mark.parametrize(
    "show_method",
    ["show_bd_fm_tools", "show_bd_plastic_tools", "show_bd_silky_tools"],
)
def test_show_tools_not_loaded_branch(show_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    getattr(eng, show_method)()
    assert "not loaded yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    "profile_key,show_method,snapshot_marker",
    [
        ("6", "show_bd_fm_tools", "SRC FM Tune"),
        ("7", "show_bd_plastic_tools", "SRC Mod Type"),
        ("8", "show_bd_silky_tools", "SRC VCO Click"),
    ],
)
def test_show_tools_loaded_snapshot_branch(profile_key, show_method, snapshot_marker, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    capsys.readouterr()
    getattr(eng, show_method)()
    text = capsys.readouterr().out
    assert "Current Pad 1 state snapshot:" in text


@pytest.mark.parametrize(
    "show_method",
    ["show_bd_fm_tools", "show_bd_plastic_tools", "show_bd_silky_tools"],
)
def test_show_tools_loaded_with_partial_state_skips_absent_names(show_method, capsys):
    """When ``group_current_states[1]`` is missing some snapshot names, the
    snapshot loop skips them (the absent-name branch of ``if name in current``)."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    # Seed Pad 1 as "loaded" but with a deliberately sparse state dict so most
    # of the fixed snapshot-name list is absent.
    eng = Pad1Engine(
        RecordingOut(),
        sleep=_no_sleep,
        group_current_states={1: {"SRC Tune": 60}},
    )
    getattr(eng, show_method)()
    text = capsys.readouterr().out

    assert "Current Pad 1 state snapshot:" in text
    assert "SRC Tune: 60" in text
    # A name that is NOT in the sparse dict must have been skipped.
    assert "FLT Type:" not in text


@pytest.mark.parametrize(
    "require_method",
    [
        "require_pad1_bd_fm_context",
        "require_pad1_bd_plastic_context",
        "require_pad1_bd_silky_context",
    ],
)
def test_require_context_not_loaded(require_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    assert getattr(eng, require_method)() is False
    assert "not loaded yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    "loaded_key,require_method,wrong_msg",
    [
        ("2", "require_pad1_bd_fm_context", "not currently using BD FM"),
        ("2", "require_pad1_bd_plastic_context", "not currently using BD Plastic"),
        ("2", "require_pad1_bd_silky_context", "not currently using BD Silky"),
    ],
)
def test_require_context_wrong_profile(loaded_key, require_method, wrong_msg, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile(loaded_key)  # loads BD Hard, not the discovery engine
    capsys.readouterr()
    assert getattr(eng, require_method)() is False
    assert wrong_msg in capsys.readouterr().out


@pytest.mark.parametrize(
    "profile_key,require_method",
    [
        ("6", "require_pad1_bd_fm_context"),
        ("7", "require_pad1_bd_plastic_context"),
        ("8", "require_pad1_bd_silky_context"),
    ],
)
def test_require_context_correct_profile(profile_key, require_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    capsys.readouterr()
    assert getattr(eng, require_method)() is True


@pytest.mark.parametrize(
    "profile_key,apply_method",
    [
        ("6", "apply_pad1_bd_fm_partial"),
        ("7", "apply_pad1_bd_plastic_partial"),
        ("8", "apply_pad1_bd_silky_partial"),
    ],
)
def test_apply_partial_guard_blocks_when_not_loaded(profile_key, apply_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    getattr(eng, apply_method)({"SRC Tune": 60}, "Guarded")
    # require_*_context failed -> nothing sent, no completion line.
    assert out.sent == []
    assert "discovery command complete" not in capsys.readouterr().out


@pytest.mark.parametrize(
    "profile_key,apply_method",
    [
        ("6", "apply_pad1_bd_fm_partial"),
        ("7", "apply_pad1_bd_plastic_partial"),
        ("8", "apply_pad1_bd_silky_partial"),
    ],
)
def test_apply_partial_skips_unknown_parameter(profile_key, apply_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    capsys.readouterr()
    getattr(eng, apply_method)({"NOT A REAL PARAM": 50}, "Unknown Param Test")
    text = capsys.readouterr().out
    assert "Skipping unknown" in text
    assert "discovery command complete" in text


@pytest.mark.parametrize(
    "profile_key,apply_method",
    [
        ("6", "apply_pad1_bd_fm_partial"),
        ("7", "apply_pad1_bd_plastic_partial"),
        ("8", "apply_pad1_bd_silky_partial"),
    ],
)
def test_apply_partial_ensure_machine_false_branch(profile_key, apply_method, capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    out.sent.clear()
    capsys.readouterr()
    getattr(eng, apply_method)({"SRC Tune": 60}, "No Machine", ensure_machine=False)
    # ensure_machine=False -> no CC15 machine switch in the message stream.
    assert all(msg.control != 15 for msg in out.sent)
    assert eng.previous_state is not None


@pytest.mark.parametrize(
    "profile_key,discovery_method",
    [
        ("6", "bd_fm_tone_discovery"),
        ("6", "bd_fm_kick_body_discovery"),
        ("6", "bd_fm_grit_discovery"),
        ("7", "bd_plastic_tone_discovery"),
        ("7", "bd_plastic_kick_body_discovery"),
        ("7", "bd_plastic_rubber_discovery"),
        ("8", "bd_silky_smooth_tone_discovery"),
        ("8", "bd_silky_kick_body_discovery"),
        ("8", "bd_silky_click_dust_discovery"),
    ],
)
def test_discovery_method_sends_params_and_records_state(profile_key, discovery_method, capsys):
    """Each discovery helper, called directly, mutates state and emits CCs."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    out.sent.clear()
    capsys.readouterr()

    random.seed(123)
    getattr(eng, discovery_method)()
    text = capsys.readouterr().out

    assert "discovery command complete" in text
    assert out.sent  # parameter CCs (and the machine CC) were emitted
    assert eng.previous_state is not None
    assert eng.group_current_states[1] == eng.current_state
    assert eng.group_previous_states[1] == eng.previous_state


def test_return_helpers_reload_their_profiles(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.return_pad1_bd_fm_to_anchor()
    assert eng.group_layout[1]["profile"] == "6"
    eng.return_pad1_bd_plastic_to_anchor()
    assert eng.group_layout[1]["profile"] == "7"
    eng.return_pad1_bd_silky_to_anchor()
    assert eng.group_layout[1]["profile"] == "8"
    capsys.readouterr()


def test_rotate_from_unprofiled_returns_to_bd_hard(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    # Force Pad 1 onto a profile key not in the rotation order.
    eng.group_layout[1]["profile"] = "5"
    eng.rotate_pad1_bd_engine()
    text = capsys.readouterr().out
    assert "not currently on a profiled BD engine" in text
    assert eng.group_layout[1]["profile"] == "2"  # BD Hard


def test_rotate_advances_through_rotation_order(capsys):
    _install_fake_mido()
    from rytm_randomizer.data import PAD1_BD_ROTATION_ORDER
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile("2")  # BD Hard, index 0
    capsys.readouterr()
    eng.rotate_pad1_bd_engine()
    expected = PAD1_BD_ROTATION_ORDER[1]
    assert eng.group_layout[1]["profile"] == expected


def test_rotate_wraps_at_end_of_rotation_order(capsys):
    _install_fake_mido()
    from rytm_randomizer.data import PAD1_BD_ROTATION_ORDER
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile(PAD1_BD_ROTATION_ORDER[-1])
    capsys.readouterr()
    eng.rotate_pad1_bd_engine()
    assert eng.group_layout[1]["profile"] == PAD1_BD_ROTATION_ORDER[0]


def test_mutate_current_engine_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.mutate_current_pad1_bd_engine()
    assert "not loaded yet" in capsys.readouterr().out


def test_mutate_current_engine_unprofiled_key(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()
    # Loaded, but force the layout onto a non-rotation key.
    eng.group_layout[1]["profile"] = "5"
    eng.mutate_current_pad1_bd_engine()
    assert "not currently on a profiled BD engine" in capsys.readouterr().out


@pytest.mark.parametrize("profile_key", ["6", "7", "8"])
def test_mutate_current_engine_discovery_branches(profile_key, capsys):
    """profile keys 6/7/8 route into the dedicated discovery sub-mode picker."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    out.sent.clear()
    capsys.readouterr()
    random.seed(7)
    eng.mutate_current_pad1_bd_engine()
    text = capsys.readouterr().out
    assert "Pad 1 Current BD Engine Mutation - V1.26" in text
    assert "discovery command complete" in text


@pytest.mark.parametrize("profile_key", ["2", "1", "3", "4"])
def test_mutate_current_engine_generic_branch(profile_key, capsys):
    """Older profiled engines (2/1/3/4) take the generic mutate_zone path."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile(profile_key)
    out.sent.clear()
    capsys.readouterr()
    random.seed(3)
    eng.mutate_current_pad1_bd_engine()
    text = capsys.readouterr().out
    assert "Mutation plan:" in text
    assert "current BD engine mutation complete" in text
    assert 1 in eng.group_current_states


def test_mutate_generic_branch_records_none_previous_when_falsy(capsys):
    """When previous_state is falsy, group_previous_states[1] is set to None."""

    _install_fake_mido()
    import random

    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = RecordingOut()
    eng = Pad1Engine(out, sleep=_no_sleep)
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()
    # Right after a fresh load, previous_state context can carry over; force the
    # falsy path explicitly so the ``else`` branch is exercised.
    eng.previous_state = None
    eng.group_layout[1]["profile"] = "2"
    random.seed(1)
    eng.mutate_current_pad1_bd_engine()
    capsys.readouterr()
    assert 1 in eng.group_previous_states


def test_apply_state_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_apply_state`` with no active profile is a
    no-op write-back (mirrors the monolith ``require_profile`` guard)."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)
    before_anchor = dict(eng.anchor_state)

    eng._apply_state({"SRC Tune": 60}, "No Profile")

    assert eng.current_state == before_current
    assert eng.anchor_state == before_anchor
    assert eng.previous_state is None
    assert "Select a profile first" in capsys.readouterr().out


def test_mutate_zone_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_mutate_zone`` with no active profile leaves
    current/previous state untouched."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)

    eng._mutate_zone("body", "micro")

    assert eng.current_state == before_current
    assert eng.previous_state is None
    capsys.readouterr()


# ===========================================================================
# Subprocess parity vs the committed monolith -- byte-identical behavior
# ===========================================================================


def test_parity_load_each_profiled_engine():
    for key in ["2", "1", "3", "4", "6", "7", "8", "5"]:
        _parity_subprocess(f"[('load_pad1_bd_profile', ({key!r},))]")


def test_parity_load_unknown_profile_key():
    _parity_subprocess("[('load_pad1_bd_profile', ('nope',))]")


def test_parity_switch_extra_machine_unknown():
    _parity_subprocess("[('switch_pad1_extra_bd_machine_only', ('ZZ',))]")


def test_parity_show_menus_cold():
    for fn in [
        "show_bd_engine_tools",
        "show_bd_fm_tools",
        "show_bd_plastic_tools",
        "show_bd_silky_tools",
        "show_bd_rotation_status",
    ]:
        _parity_subprocess(f"[({fn!r}, ())]")


def test_parity_show_menus_after_load():
    _parity_subprocess("[('load_pad1_bd_profile', ('6',)), ('show_bd_fm_tools', ())]")
    _parity_subprocess("[('load_pad1_bd_profile', ('7',)), ('show_bd_plastic_tools', ())]")
    _parity_subprocess("[('load_pad1_bd_profile', ('8',)), ('show_bd_silky_tools', ())]")
    _parity_subprocess("[('load_pad1_bd_profile', ('2',)), ('show_bd_rotation_status', ())]")


def test_parity_require_context_paths():
    # not-loaded guard
    _parity_subprocess("[('require_pad1_bd_fm_context', ())]")
    # wrong-profile guard
    _parity_subprocess("[('load_pad1_bd_profile', ('2',)), ('require_pad1_bd_fm_context', ())]")
    _parity_subprocess(
        "[('load_pad1_bd_profile', ('2',)), " "('require_pad1_bd_plastic_context', ())]"
    )
    _parity_subprocess(
        "[('load_pad1_bd_profile', ('2',)), " "('require_pad1_bd_silky_context', ())]"
    )
    # correct profile
    _parity_subprocess("[('load_pad1_bd_profile', ('6',)), ('require_pad1_bd_fm_context', ())]")


def test_parity_fm_discovery_commands():
    for fn in [
        "bd_fm_tone_discovery",
        "bd_fm_kick_body_discovery",
        "bd_fm_grit_discovery",
    ]:
        _parity_subprocess(f"[('load_pad1_bd_profile', ('6',)), ({fn!r}, ())]")


def test_parity_plastic_discovery_commands():
    for fn in [
        "bd_plastic_tone_discovery",
        "bd_plastic_kick_body_discovery",
        "bd_plastic_rubber_discovery",
    ]:
        _parity_subprocess(f"[('load_pad1_bd_profile', ('7',)), ({fn!r}, ())]")


def test_parity_silky_discovery_commands():
    for fn in [
        "bd_silky_smooth_tone_discovery",
        "bd_silky_kick_body_discovery",
        "bd_silky_click_dust_discovery",
    ]:
        _parity_subprocess(f"[('load_pad1_bd_profile', ('8',)), ({fn!r}, ())]")


def test_parity_discovery_guard_when_not_loaded():
    # apply_*_partial driven straight through their public discovery helpers
    # while Pad 1 is not loaded -> the require_*_context guard blocks both.
    _parity_subprocess("[('bd_fm_tone_discovery', ())]")
    _parity_subprocess("[('bd_plastic_tone_discovery', ())]")
    _parity_subprocess("[('bd_silky_smooth_tone_discovery', ())]")


def test_parity_discovery_wrong_profile_guard():
    # Load BD Hard, then fire a BD FM discovery: the guard should block it.
    _parity_subprocess("[('load_pad1_bd_profile', ('2',)), ('bd_fm_tone_discovery', ())]")


def test_parity_return_helpers():
    _parity_subprocess("[('return_pad1_bd_fm_to_anchor', ())]")
    _parity_subprocess("[('return_pad1_bd_plastic_to_anchor', ())]")
    _parity_subprocess("[('return_pad1_bd_silky_to_anchor', ())]")


def test_parity_rotation():
    # from cold start (BD Hard)
    _parity_subprocess("[('rotate_pad1_bd_engine', ())]")
    # full walk around the rotation ring
    _parity_subprocess(
        "[('rotate_pad1_bd_engine', ()), ('rotate_pad1_bd_engine', ()), "
        "('rotate_pad1_bd_engine', ()), ('rotate_pad1_bd_engine', ()), "
        "('rotate_pad1_bd_engine', ()), ('rotate_pad1_bd_engine', ()), "
        "('rotate_pad1_bd_engine', ())]"
    )


def test_parity_mutate_current_engine_not_loaded():
    _parity_subprocess("[('mutate_current_pad1_bd_engine', ())]")


@pytest.mark.parametrize("key", ["6", "7", "8"])
@pytest.mark.parametrize("seed", [1, 2, 5, 11, 42])
def test_parity_mutate_current_engine_discovery_modes(key, seed):
    """One parity call per (key, seed) so xdist can fan the 15 cases across
    workers (was a single ~23s test before the split)."""

    _parity_subprocess(
        f"[('load_pad1_bd_profile', ({key!r},)), " "('mutate_current_pad1_bd_engine', ())]",
        seed=seed,
    )


@pytest.mark.parametrize("key", ["2", "1", "3", "4"])
@pytest.mark.parametrize("seed", [1, 2, 5, 11, 42])
def test_parity_mutate_current_engine_generic_modes(key, seed):
    """One parity call per (key, seed) so xdist can fan the 20 cases across
    workers (was a single ~29s test before the split)."""

    _parity_subprocess(
        f"[('load_pad1_bd_profile', ({key!r},)), " "('mutate_current_pad1_bd_engine', ())]",
        seed=seed,
    )


@pytest.mark.parametrize("seed", [1, 7, 99, 2024])
def test_parity_long_interactive_session(seed):
    """A realistic multi-step Pad 1 session: load, discover, rotate, mutate.

    One parity call per seed so xdist can fan the 4 cases across workers
    (was a single ~26s test before the split). The *sequence* is ordered,
    but the four seeds are independent parity checks."""

    steps = (
        "["
        "('load_pad1_bd_profile', ('6',)), "
        "('bd_fm_tone_discovery', ()), "
        "('bd_fm_grit_discovery', ()), "
        "('mutate_current_pad1_bd_engine', ()), "
        "('rotate_pad1_bd_engine', ()), "
        "('show_bd_rotation_status', ()), "
        "('return_pad1_bd_silky_to_anchor', ()), "
        "('bd_silky_kick_body_discovery', ()), "
        "('rotate_pad1_bd_engine', ()), "
        "('mutate_current_pad1_bd_engine', ())"
        "]"
    )
    _parity_subprocess(steps, seed=seed)
