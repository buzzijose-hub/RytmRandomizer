"""Characterization + parity tests for the Pad 4 BD Acoustic engine (Wave 4 / WS-M).

These tests lock in the V1.34 monolith's CURRENT behavior for the ~12 Pad-4
functions, then prove the extracted
:class:`rytm_randomizer.engines.pad4.Pad4Engine` reproduces it byte-identically:
same printed output, same MIDI message stream, same resulting state
dictionaries.

Pad 4 is the dedicated BD Acoustic body / accent lane. Its dedicated commands
all run through the monolith ``require_group_for_single_pad`` guard, which
insists the full 4-pad group has been loaded first (``group_current_states`` has
4 entries). The subprocess harness therefore offers an optional ``load`` setup
step that runs the monolith ``load_group_anchors`` once, and seeds the engine
with copies of the exact group dicts the monolith produced -- so the parity
comparison starts from an identical, honest baseline.

Isolation rules (matching ``tests/test_engines_pad3.py``):

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
# relevant state dicts, and asserts byte-parity. ``steps`` is a list of
# (fn_name, args) tuples; if the first element is the literal string "load",
# the monolith's ``load_group_anchors`` runs first (and the engine is seeded
# from the exact group dicts it produced) so the 4-pad-group guard is satisfied
# identically. The worker loop appended by ``tests/_parity_worker.py`` calls
# ``assert_parity`` once per JSON request line.
_HARNESS = '''
import io, contextlib, random
import rytm_hybrid_randomizer_v134 as m
from rytm_randomizer import midi_io, randomization
from rytm_randomizer.data import PROFILES
from rytm_randomizer.engines.pad4 import Pad4Engine

midi_io.time.sleep = lambda *_: None
randomization.time.sleep = lambda *_: None


class Out:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append((msg.type, msg.channel, msg.control, msg.value))


# Monolith Pad-4 functions that are pure status/guard helpers and take NO
# ``out`` argument (the engine versions are likewise argument-free methods).
_NO_OUT = {
    "require_pad4_bd_acoustic_context",
    "show_pad4_tools",
}


def _reset_monolith():
    """Restore the monolith globals the Pad-4 functions touch to cold start."""
    m.active_profile = None
    m.anchor_state = {}
    m.current_state = {}
    m.previous_state = None
    m.target_pad = 1
    m.channel = 0
    m.group_anchor_states = {}
    m.group_current_states = {}
    m.group_previous_states = {}
    m.isolated_pad = 3
    m.pad4_current_mode_key = "anchor"


def _make_engine(out):
    """Cold-start Pad4Engine: matches the freshly imported monolith."""
    return Pad4Engine(out, sleep=lambda *_: None)


def _snapshot_monolith():
    return {
        "active": m.active_profile["name"] if m.active_profile else None,
        "current": dict(m.current_state),
        "previous": dict(m.previous_state) if m.previous_state else m.previous_state,
        "target_pad": m.target_pad,
        "channel": m.channel,
        "isolated_pad": m.isolated_pad,
        "mode_key": m.pad4_current_mode_key,
        "gcur": {k: dict(v) for k, v in m.group_current_states.items()},
        "gprev": {
            k: (dict(v) if v else v) for k, v in m.group_previous_states.items()
        },
        "ganc": {k: dict(v) for k, v in m.group_anchor_states.items()},
    }


def _snapshot_engine(eng):
    return {
        "active": eng.active_profile["name"] if eng.active_profile else None,
        "current": dict(eng.current_state),
        "previous": (
            dict(eng.previous_state) if eng.previous_state else eng.previous_state
        ),
        "target_pad": eng.target_pad,
        "channel": eng.channel,
        "isolated_pad": eng.isolated_pad,
        "mode_key": eng.pad4_current_mode_key,
        "gcur": {k: dict(v) for k, v in eng.group_current_states.items()},
        "gprev": {
            k: (dict(v) if v else v) for k, v in eng.group_previous_states.items()
        },
        "ganc": {k: dict(v) for k, v in eng.group_anchor_states.items()},
    }


def run_monolith(seed, steps):
    """Drive a sequence of monolith Pad-4 calls.

    Returns ``(stdout, msgs, state, baseline)``. The optional ``load`` setup
    step (``load_group_anchors``) runs *before* stdout/MIDI capture starts --
    its output is group-level plumbing, not Pad-4 behavior, and the engine has
    no equivalent method. Only the Pad-4 calls themselves are captured and
    compared for parity.

    ``baseline`` is a snapshot of the monolith's globals taken immediately
    *after* the load step but *before* any Pad-4 call mutates them -- so the
    engine run can be seeded from a pristine, identical starting point (the
    monolith run itself goes on to mutate ``m.group_*`` in place).
    """
    _reset_monolith()
    out = Out()
    do_load = bool(steps) and steps[0] == "load"
    real_steps = steps[1:] if do_load else steps
    if do_load:
        # Uncaptured: seeds m.group_* so the 4-pad-group guard passes.
        with contextlib.redirect_stdout(io.StringIO()):
            m.load_group_anchors(out)
        out.sent.clear()
    baseline = _snapshot_monolith()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        random.seed(seed)
        for fn_name, args in real_steps:
            if fn_name in _NO_OUT:
                getattr(m, fn_name)(*args)
            else:
                getattr(m, fn_name)(out, *args)
    return buf.getvalue(), out.sent, _snapshot_monolith(), baseline


def run_engine(seed, steps, baseline):
    """Drive the same sequence on a Pad4Engine; return (stdout, msgs, state).

    When the run uses the ``load`` setup step the engine cannot call
    ``load_group_anchors`` itself (that is a group-level function, not a Pad-4
    function), so it is constructed seeded from ``baseline`` -- the pristine
    post-load snapshot of the monolith globals captured before any Pad-4 call
    ran. This mirrors the monolith's uncaptured setup step: no output, no MIDI,
    just identical starting state.
    """
    out = Out()
    do_load = bool(steps) and steps[0] == "load"
    real_steps = steps[1:] if do_load else steps
    if do_load:
        eng = Pad4Engine(
            out,
            sleep=lambda *_: None,
            target_pad=baseline["target_pad"],
            channel=baseline["channel"],
            isolated_pad=baseline["isolated_pad"],
            pad4_current_mode_key=baseline["mode_key"],
            current_state=dict(baseline["current"]),
            previous_state=(
                dict(baseline["previous"])
                if baseline["previous"]
                else baseline["previous"]
            ),
            group_anchor_states={
                k: dict(v) for k, v in baseline["ganc"].items()
            },
            group_current_states={
                k: dict(v) for k, v in baseline["gcur"].items()
            },
            group_previous_states={
                k: (dict(v) if v else v)
                for k, v in baseline["gprev"].items()
            },
        )
        # The monolith's post-load active_profile points at the last pad; mirror
        # it by name lookup so the engine baseline matches without re-importing
        # the monolith's profile object.
        if baseline["active"] is not None:
            for prof in PROFILES.values():
                if prof["name"] == baseline["active"]:
                    eng.active_profile = prof
                    break
        eng.anchor_state = dict(baseline["current"])
    else:
        eng = _make_engine(out)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        random.seed(seed)
        for fn_name, args in real_steps:
            getattr(eng, fn_name)(*args)
    return buf.getvalue(), out.sent, _snapshot_engine(eng)


def assert_parity(seed, steps):
    # The monolith run happens first; it captures a pristine post-load baseline
    # *before* its own Pad-4 calls mutate m.group_* in place, and that baseline
    # seeds the engine run for an honest, identical starting point.
    mo, mm, ms, baseline = run_monolith(seed, steps)
    eo, em, es = run_engine(seed, steps, baseline)
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


# ---------------------------------------------------------------------------
# In-process helpers: build an engine with the full 4-pad group "loaded".
# ---------------------------------------------------------------------------

def _loaded_group_dicts():
    """Return (ganc, gcur, gprev) dicts mimicking a full group load.

    Pad 4 is seeded with the BD Acoustic anchor; the other pads only need
    *presence* so the ``require_group_for_single_pad`` length check passes.
    """

    from rytm_randomizer.data import PROFILES

    ganc: dict = {}
    gcur: dict = {}
    gprev: dict = {}
    layout = {1: "2", 2: "3", 3: "5", 4: "4"}
    for pad, key in layout.items():
        anchor = dict(PROFILES[key]["anchor"])
        ganc[pad] = dict(anchor)
        gcur[pad] = dict(anchor)
        gprev[pad] = None
    return ganc, gcur, gprev


def _make_loaded_engine(out, **kwargs):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    ganc, gcur, gprev = _loaded_group_dicts()
    return Pad4Engine(
        out,
        sleep=_no_sleep,
        group_anchor_states=ganc,
        group_current_states=gcur,
        group_previous_states=gprev,
        **kwargs,
    )


# ===========================================================================
# In-process import-safety + smoke
# ===========================================================================

def test_import_is_silent_and_mido_free(capsys):
    """Importing the engine module opens no ports and pulls in no mido."""

    sys.modules.pop("rytm_randomizer.engines.pad4", None)
    sys.modules.pop("mido", None)
    import rytm_randomizer.engines.pad4 as pad4  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules


def test_engine_constructs_with_monolith_cold_start_defaults():
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)

    assert eng.active_profile is None
    assert eng.current_state == {}
    assert eng.previous_state is None
    assert eng.target_pad == 1
    assert eng.channel == 0
    assert eng.isolated_pad == 3
    assert eng.pad4_current_mode_key == "anchor"
    assert eng.group_current_states == {}


# ===========================================================================
# In-process behavior coverage (fake mido) -- every method + every branch
# ===========================================================================

def test_require_context_blocks_when_group_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    assert eng.require_pad4_bd_acoustic_context() is False
    assert "Load the full 4-pad group first" in capsys.readouterr().out


def test_require_context_passes_when_group_loaded(capsys):
    eng = _make_loaded_engine(RecordingOut())
    assert eng.require_pad4_bd_acoustic_context() is True
    assert eng.target_pad == 4
    assert eng.channel == 3
    assert eng.active_profile is not None
    capsys.readouterr()


def test_show_pad4_tools_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    eng.show_pad4_tools()
    text = capsys.readouterr().out
    assert "Pad 4 BD Acoustic Body / Accent Tools - V1.34" in text
    assert "< current" in text  # anchor is the cold-start current mode
    assert "not loaded yet" in text


def test_show_pad4_tools_loaded_snapshot(capsys):
    eng = _make_loaded_engine(RecordingOut())
    eng.show_pad4_tools()
    text = capsys.readouterr().out
    assert "Current Pad 4 state snapshot:" in text
    # FLT Type renders with the filter-type name when present.
    assert "FLT Type:" in text


def test_show_pad4_tools_unknown_mode_key(capsys):
    """An unknown pad4_current_mode_key hits the 'Unknown' label fallback."""

    eng = _make_loaded_engine(RecordingOut(), pad4_current_mode_key="bogus")
    eng.show_pad4_tools()
    text = capsys.readouterr().out
    assert "Unknown" in text


def test_show_pad4_tools_partial_state_skips_absent(capsys):
    """A sparse group_current_states[4] exercises the snapshot loop's
    absent-name skip branch in ``show_pad4_tools``."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    ganc, gcur, gprev = _loaded_group_dicts()
    gcur[4] = {"SRC Tune": 51}  # deliberately sparse, no FLT Type
    eng = Pad4Engine(
        RecordingOut(),
        sleep=_no_sleep,
        group_anchor_states=ganc,
        group_current_states=gcur,
        group_previous_states=gprev,
    )
    eng.show_pad4_tools()
    text = capsys.readouterr().out
    assert "SRC Tune: 51" in text
    assert "FLT Type:" not in text


def test_apply_partial_blocked_when_group_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    out = RecordingOut()
    eng = Pad4Engine(out, sleep=_no_sleep)
    eng.apply_pad4_bd_acoustic_partial({"SRC Tune": 51}, "Guarded")
    assert out.sent == []
    assert "discovery command complete" not in capsys.readouterr().out


def test_apply_partial_pad4_state_absent_branch(capsys):
    """Group has 4 pads but pad 4 is absent: hits the second guard branch."""

    _install_fake_mido()
    from rytm_randomizer.data import PROFILES
    from rytm_randomizer.engines.pad4 import Pad4Engine

    # 4 pads present (passes length check) but pad 4 key missing -- use pads
    # 1,2,3 plus a stand-in 5 so len()==4 yet 4 not in group_current_states.
    gcur = {1: {}, 2: {}, 3: {}, 5: {}}
    out = RecordingOut()
    eng = Pad4Engine(
        out,
        sleep=_no_sleep,
        group_current_states=gcur,
        group_anchor_states={4: dict(PROFILES["4"]["anchor"])},
    )
    eng.apply_pad4_bd_acoustic_partial({"SRC Tune": 51}, "No Pad4 State")
    text = capsys.readouterr().out
    assert "Pad 4 state is not loaded yet" in text
    assert out.sent == []


def test_apply_partial_skips_unknown_parameter(capsys):
    eng = _make_loaded_engine(RecordingOut())
    eng.apply_pad4_bd_acoustic_partial({"NOT A REAL PARAM": 50}, "Unknown Param")
    text = capsys.readouterr().out
    assert "Skipping unknown BD Acoustic parameter" in text
    assert "discovery command complete" in text


def test_apply_partial_ensure_machine_false_branch(capsys):
    out = RecordingOut()
    eng = _make_loaded_engine(out)
    eng.apply_pad4_bd_acoustic_partial(
        {"SRC Tune": 51}, "No Machine", ensure_machine=False
    )
    capsys.readouterr()
    # ensure_machine=False -> no CC15 machine switch in the message stream.
    assert all(msg.control != 15 for msg in out.sent)
    assert eng.previous_state is not None


@pytest.mark.parametrize(
    "discovery_method,expected_mode",
    [
        ("pad4_tight_body_hit_mode", "tight"),
        ("pad4_long_boom_accent_mode", "long"),
        ("pad4_filtered_punch_accent_mode", "filter"),
        ("pad4_impact_grit_accent_mode", "impact"),
    ],
)
def test_discovery_methods_send_params_and_set_mode(
    discovery_method, expected_mode, capsys
):
    import random

    out = RecordingOut()
    eng = _make_loaded_engine(out)
    capsys.readouterr()
    random.seed(123)
    getattr(eng, discovery_method)()
    text = capsys.readouterr().out

    assert "discovery command complete" in text
    assert out.sent
    assert eng.pad4_current_mode_key == expected_mode
    assert eng.group_current_states[4] == eng.current_state


@pytest.mark.parametrize(
    "discovery_method",
    [
        "pad4_tight_body_hit_mode",
        "pad4_long_boom_accent_mode",
        "pad4_filtered_punch_accent_mode",
        "pad4_impact_grit_accent_mode",
    ],
)
def test_discovery_methods_blocked_when_group_not_loaded(
    discovery_method, capsys
):
    """The discovery modes set the mode key, then go via the guarded
    ``apply_pad4_bd_acoustic_partial`` which blocks when the group is absent."""

    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    out = RecordingOut()
    eng = Pad4Engine(out, sleep=_no_sleep)
    getattr(eng, discovery_method)()
    assert "Load the full 4-pad group first" in capsys.readouterr().out
    assert out.sent == []


def test_return_pad4_bd_acoustic_to_anchor_restores_isolated_pad(capsys):
    out = RecordingOut()
    eng = _make_loaded_engine(out, isolated_pad=2)
    eng.return_pad4_bd_acoustic_to_anchor()
    text = capsys.readouterr().out
    assert "Returning isolated pad to anchor:" in text
    assert eng.pad4_current_mode_key == "anchor"
    # isolated_pad restored to its previous value after the return.
    assert eng.isolated_pad == 2
    assert eng.group_previous_states[4] is None


def test_return_pad4_bd_acoustic_to_anchor_blocked_when_group_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep, isolated_pad=4)
    eng.return_pad4_bd_acoustic_to_anchor()
    assert "Load the full 4-pad group first" in capsys.readouterr().out
    # mode key still set, isolated_pad still restored even on the guard path.
    assert eng.pad4_current_mode_key == "anchor"
    assert eng.isolated_pad == 4


# ---------------------------------------------------------------------------
# Defensive shim branches: no active profile -> the underlying midi_io /
# randomization primitives return ``applied=False`` and the shim is a no-op.
# Mirrors the equivalent pad1/pad3 coverage tests.
# ---------------------------------------------------------------------------

def test_apply_state_shim_noop_when_no_profile(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)
    before_anchor = dict(eng.anchor_state)

    eng._apply_state({"SRC Tune": 51}, "No Profile")

    assert eng.current_state == before_current
    assert eng.anchor_state == before_anchor
    assert eng.previous_state is None
    capsys.readouterr()


def test_mutate_zone_shim_noop_when_no_profile(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    eng.active_profile = None
    before_current = dict(eng.current_state)

    eng._mutate_zone("body", "groove")

    assert eng.current_state == before_current
    assert eng.previous_state is None
    capsys.readouterr()


def test_set_group_context_falls_back_to_profile_anchor(capsys):
    """``_set_group_context`` for a pad absent from group_anchor_states /
    group_current_states falls back to the profile anchor (the else branches)."""

    _install_fake_mido()
    from rytm_randomizer.data import PROFILES
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    # No group state seeded at all -> both else branches taken.
    eng._set_group_context(4, "4")
    assert eng.target_pad == 4
    assert eng.channel == 3
    assert eng.anchor_state == dict(PROFILES["4"]["anchor"])
    assert eng.current_state == eng.anchor_state
    assert eng.previous_state is None
    capsys.readouterr()


def test_load_pad4_mode_unknown_key(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad4_mode("does-not-exist")
    assert "Unknown Pad 4 mode: does-not-exist" in capsys.readouterr().out


def test_load_pad4_mode_non_anchor_when_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(RecordingOut(), sleep=_no_sleep)
    eng.load_pad4_mode("tight")
    assert "Pad 4 state is not loaded yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    "mode_key", ["anchor", "tight", "long", "filter", "impact"]
)
def test_load_pad4_mode_dispatches_each_mode(mode_key, capsys):
    import random

    out = RecordingOut()
    eng = _make_loaded_engine(out)
    capsys.readouterr()
    random.seed(7)
    eng.load_pad4_mode(mode_key)
    text = capsys.readouterr().out
    assert "Loading Pad 4 BD Acoustic behavior mode:" in text
    if mode_key != "anchor":
        assert eng.pad4_current_mode_key == mode_key


def test_rotate_pad4_mode_from_unknown_returns_to_anchor(capsys):
    out = RecordingOut()
    eng = _make_loaded_engine(out, pad4_current_mode_key="bogus")
    eng.rotate_pad4_mode()
    text = capsys.readouterr().out
    assert "not currently on a known BD Acoustic behavior mode" in text
    assert eng.pad4_current_mode_key == "anchor"


def test_rotate_pad4_mode_advances_and_wraps(capsys):
    import random

    out = RecordingOut()
    eng = _make_loaded_engine(out, pad4_current_mode_key="anchor")
    capsys.readouterr()
    random.seed(3)
    eng.rotate_pad4_mode()  # anchor -> tight
    assert eng.pad4_current_mode_key == "tight"

    eng2 = _make_loaded_engine(RecordingOut(), pad4_current_mode_key="impact")
    random.seed(3)
    eng2.rotate_pad4_mode()  # impact -> wraps to anchor
    assert eng2.pad4_current_mode_key == "anchor"


def test_mutate_current_pad4_mode_unknown_mode(capsys):
    eng = _make_loaded_engine(RecordingOut(), pad4_current_mode_key="bogus")
    eng.mutate_current_pad4_mode()
    assert "does not have a P4X mutation plan" in capsys.readouterr().out


def test_mutate_current_pad4_mode_state_not_loaded(capsys):
    _install_fake_mido()
    from rytm_randomizer.engines.pad4 import Pad4Engine

    eng = Pad4Engine(
        RecordingOut(), sleep=_no_sleep, pad4_current_mode_key="tight"
    )
    eng.mutate_current_pad4_mode()
    assert "Pad 4 state is not loaded yet" in capsys.readouterr().out


@pytest.mark.parametrize(
    "mode_key,seed",
    [
        ("anchor", 1), ("anchor", 2), ("anchor", 5),
        ("tight", 1), ("tight", 2), ("tight", 5),
        ("long", 1), ("long", 2), ("long", 5),
        ("filter", 1), ("filter", 2), ("filter", 5),
        ("impact", 1), ("impact", 2), ("impact", 5),
    ],
)
def test_mutate_current_pad4_mode_all_actions(mode_key, seed, capsys):
    import random

    out = RecordingOut()
    eng = _make_loaded_engine(out, pad4_current_mode_key=mode_key)
    capsys.readouterr()
    random.seed(seed)
    eng.mutate_current_pad4_mode()
    text = capsys.readouterr().out
    assert "Pad 4 Current BD Acoustic Mode Mutation - V1.26" in text


def test_return_pad4_to_anchor(capsys):
    out = RecordingOut()
    eng = _make_loaded_engine(out)
    eng.return_pad4_to_anchor()
    text = capsys.readouterr().out
    assert "Returning Pad 4 to BD Acoustic body/accent anchor / home:" in text
    assert "Returning isolated pad to anchor:" in text


# ===========================================================================
# Subprocess parity vs the committed monolith -- byte-identical behavior
# ===========================================================================

def test_parity_require_context_guard_not_loaded():
    _parity_subprocess("[('require_pad4_bd_acoustic_context', ())]")


def test_parity_require_context_after_group_load():
    _parity_subprocess(
        "['load', ('require_pad4_bd_acoustic_context', ())]"
    )


def test_parity_show_tools_cold():
    _parity_subprocess("[('show_pad4_tools', ())]")


def test_parity_show_tools_after_group_load():
    _parity_subprocess("['load', ('show_pad4_tools', ())]")


def test_parity_apply_partial_guards():
    # group not loaded -> first guard
    _parity_subprocess(
        "[('apply_pad4_bd_acoustic_partial', ({'SRC Tune': 51}, 'Guarded'))]"
    )
    # group loaded -> applies, including an unknown-parameter skip
    _parity_subprocess(
        "['load', ('apply_pad4_bd_acoustic_partial', "
        "({'SRC Tune': 51, 'BOGUS PARAM': 5}, 'Mixed'))]"
    )
    # ensure_machine False branch
    _parity_subprocess(
        "['load', ('apply_pad4_bd_acoustic_partial', "
        "({'SRC Tune': 51}, 'NoMachine', False))]"
    )


@pytest.mark.parametrize(
    "fn",
    [
        "pad4_tight_body_hit_mode",
        "pad4_long_boom_accent_mode",
        "pad4_filtered_punch_accent_mode",
        "pad4_impact_grit_accent_mode",
    ],
)
@pytest.mark.parametrize("seed", [1, 2, 5, 11, 42])
def test_parity_discovery_commands(fn, seed):
    """One parity call per (fn, seed) so xdist can fan the 20 cases across
    workers (was a single ~87s test before the split)."""

    _parity_subprocess(f"['load', ({fn!r}, ())]", seed=seed)


def test_parity_discovery_blocked_when_group_not_loaded():
    # all four modes set the mode key, then go via apply_*_partial's guard.
    _parity_subprocess("[('pad4_tight_body_hit_mode', ())]")
    _parity_subprocess("[('pad4_long_boom_accent_mode', ())]")
    _parity_subprocess("[('pad4_filtered_punch_accent_mode', ())]")
    _parity_subprocess("[('pad4_impact_grit_accent_mode', ())]")


def test_parity_return_to_anchor():
    _parity_subprocess("['load', ('return_pad4_bd_acoustic_to_anchor', ())]")
    _parity_subprocess("['load', ('return_pad4_to_anchor', ())]")
    # guard path: group not loaded
    _parity_subprocess("[('return_pad4_bd_acoustic_to_anchor', ())]")
    _parity_subprocess("[('return_pad4_to_anchor', ())]")


@pytest.mark.parametrize("mode", ["anchor", "tight", "long", "filter", "impact"])
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_parity_load_pad4_mode_each_mode(mode, seed):
    """One parity call per (mode, seed) so xdist can fan the 15 cases across
    workers (was part of a single ~70s test before the split)."""

    _parity_subprocess(
        f"['load', ('load_pad4_mode', ({mode!r},))]", seed=seed
    )


def test_parity_load_pad4_mode_unknown_key():
    """Unknown mode key when group is loaded."""

    _parity_subprocess("['load', ('load_pad4_mode', ('nope',))]")


def test_parity_load_pad4_mode_non_anchor_unloaded():
    """Non-anchor mode when the group is not loaded (guard path)."""

    _parity_subprocess("[('load_pad4_mode', ('tight',))]")


def test_parity_load_pad4_mode_anchor_unloaded():
    """Anchor mode when the group is not loaded -- still allowed by the
    monolith guard."""

    _parity_subprocess("[('load_pad4_mode', ('anchor',))]")


def test_parity_rotate_pad4_mode():
    # from cold-start anchor
    _parity_subprocess("['load', ('rotate_pad4_mode', ())]")
    # full walk around the rotation ring
    _parity_subprocess(
        "['load', ('rotate_pad4_mode', ()), ('rotate_pad4_mode', ()), "
        "('rotate_pad4_mode', ()), ('rotate_pad4_mode', ()), "
        "('rotate_pad4_mode', ()), ('rotate_pad4_mode', ())]"
    )


def test_parity_mutate_current_pad4_mode_guard():
    """Guard: no plan / not loaded -- single-call check."""

    _parity_subprocess("[('mutate_current_pad4_mode', ())]")


@pytest.mark.parametrize(
    "mode_setup",
    [
        "pad4_tight_body_hit_mode",
        "pad4_long_boom_accent_mode",
        "pad4_filtered_punch_accent_mode",
        "pad4_impact_grit_accent_mode",
    ],
)
@pytest.mark.parametrize("seed", [1, 2, 5, 11, 42])
def test_parity_mutate_current_pad4_mode_each_setup(mode_setup, seed):
    """One parity call per (mode_setup, seed) so xdist can fan the 20 cases
    across workers (was part of a single ~118s test before the split)."""

    _parity_subprocess(
        f"['load', ({mode_setup!r}, ()), "
        "('mutate_current_pad4_mode', ())]",
        seed=seed,
    )


@pytest.mark.parametrize("seed", [1, 2, 5, 11, 42])
def test_parity_mutate_current_pad4_mode_anchor(seed):
    """Anchor-mode mutation (generic zone branch). One parity call per seed
    so xdist can fan the 5 cases across workers."""

    _parity_subprocess(
        "['load', ('mutate_current_pad4_mode', ())]", seed=seed
    )


@pytest.mark.parametrize("seed", [1, 7, 99, 2024])
def test_parity_long_interactive_session(seed):
    """A realistic multi-step Pad 4 session: load, discover, rotate, mutate.

    One parity call per seed so xdist can fan the 4 cases across workers (was
    a single ~32s test before the split). Each seed exercises the same
    multi-step sequence -- the *sequence* itself is ordered, but the four
    seeds are independent parity checks."""

    steps = (
        "["
        "'load', "
        "('show_pad4_tools', ()), "
        "('pad4_tight_body_hit_mode', ()), "
        "('pad4_long_boom_accent_mode', ()), "
        "('mutate_current_pad4_mode', ()), "
        "('rotate_pad4_mode', ()), "
        "('pad4_impact_grit_accent_mode', ()), "
        "('return_pad4_to_anchor', ()), "
        "('mutate_current_pad4_mode', ())"
        "]"
    )
    _parity_subprocess(steps, seed=seed)
