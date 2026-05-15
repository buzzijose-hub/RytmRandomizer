"""Characterization + parity tests for the group / isolated-pad orchestrator
(Wave 4 / WS-N).

These tests lock in the V1.34 monolith's CURRENT behavior for the group,
isolated single-pad and selected-profile glue functions, then prove the
extracted :class:`rytm_randomizer.group_runner.GroupRunner` reproduces it
byte-identically: same printed output, same MIDI message stream, same resulting
state dictionaries.

Isolation rules (matching ``tests/test_engines_pad1.py``):

* Anything that imports the monolith (which does ``import mido`` at module
  scope) runs in a *subprocess*, so real ``mido`` never lands in this test
  process's ``sys.modules``.
* That subprocess is a single **warm worker** reused across every parity check
  in this file (see ``tests/_parity_worker.py``): it cold-imports the monolith
  + package once, then services one parity request per stdin line. It seeds
  the stdlib ``random`` module identically before driving the monolith
  function and the runner method, patches ``builtins.input`` with a scripted
  answer queue (shipped per-request), captures stdout + the recorded MIDI
  messages for each, and asserts equality *inside* the worker.
* In-process tests exercise the runner with a *fake* ``mido`` module; an autouse
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


@pytest.fixture(autouse=True)
def _restore_shared_profile_data():
    """Snapshot and restore the shared ``PROFILES`` / ``GROUP_LAYOUT`` dicts.

    ``commit_current_as_anchor`` mutates ``active_profile['anchor']`` in place
    (byte-parity with the monolith), and a few in-process tests load profiled
    BD engines that rewrite ``GROUP_LAYOUT`` entries. Both target the *shared*
    package data dicts, so without this restore the mutation leaks into later
    tests in the full suite. Subprocess parity tests are unaffected (separate
    interpreter); this only guards the in-process tests.
    """

    from rytm_randomizer.data import GROUP_LAYOUT, PROFILES

    profile_anchors = {
        key: dict(profile["anchor"]) for key, profile in PROFILES.items()
    }
    layout_snapshot = {pad: dict(cfg) for pad, cfg in GROUP_LAYOUT.items()}
    try:
        yield
    finally:
        for key, anchor in profile_anchors.items():
            PROFILES[key]["anchor"] = dict(anchor)
        for pad, cfg in layout_snapshot.items():
            GROUP_LAYOUT[pad].clear()
            GROUP_LAYOUT[pad].update(cfg)


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
# defines ``assert_parity(seed, steps, answers=())`` which builds a monolith run
# and a runner run from the same RNG seed and the same scripted ``input``
# answers, captures stdout + MIDI messages + the relevant state, and asserts
# byte-parity. The worker loop appended by ``tests/_parity_worker.py`` calls it
# once per JSON request line.
_HARNESS = '''
import builtins, io, contextlib, random
import rytm_hybrid_randomizer_v134 as m
from rytm_randomizer import midi_io, randomization
from rytm_randomizer.group_runner import GroupRunner, default_group_layout

midi_io.time.sleep = lambda *_: None
randomization.time.sleep = lambda *_: None


class Out:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append((msg.type, msg.channel, msg.control, msg.value))


class _Answers:
    """Scripted ``input`` queue; raises if it runs dry (parity bug signal)."""

    def __init__(self, answers):
        self._answers = list(answers)

    def __call__(self, _prompt=""):
        return self._answers.pop(0)


# Monolith group/isolated/profile functions that take NO ``out`` argument.
_NO_OUT = {
    "require_profile",
    "choose_target_pad",
    "commit_current_as_anchor",
    "show_anchor",
    "show_current",
    "set_group_context",
    "show_group_layout",
    "show_global_mutation_tools",
    "choose_isolated_pad",
    "require_group_for_single_pad",
    "show_isolated_pad",
}


def _reset_monolith():
    """Restore the monolith globals these functions touch to cold start."""
    m.active_profile = None
    m.anchor_state = {}
    m.current_state = {}
    m.previous_state = None
    m.target_pad = 1
    m.channel = 0
    m.isolated_pad = 3
    m.group_anchor_states = {}
    m.group_current_states = {}
    m.group_previous_states = {}
    m.GROUP_LAYOUT = {pad: dict(cfg) for pad, cfg in default_group_layout().items()}


def _state(active, current, previous, target_pad, channel, isolated_pad,
           layout, gcur, gprev, ganc):
    return {
        "active": active["name"] if active else None,
        "current": dict(current),
        "previous": dict(previous) if previous else previous,
        "target_pad": target_pad,
        "channel": channel,
        "isolated_pad": isolated_pad,
        "layout": {p: dict(c) for p, c in layout.items()},
        "gcur": {k: dict(v) for k, v in gcur.items()},
        "gprev": {k: (dict(v) if v else v) for k, v in gprev.items()},
        "ganc": {k: dict(v) for k, v in ganc.items()},
    }


def run_monolith(seed, steps, answers):
    _reset_monolith()
    out = Out()
    random.seed(seed)
    real_input = builtins.input
    builtins.input = _Answers(answers)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            results = []
            for fn_name, args in steps:
                if fn_name in _NO_OUT:
                    results.append(getattr(m, fn_name)(*args))
                else:
                    results.append(getattr(m, fn_name)(out, *args))
    finally:
        builtins.input = real_input
    state = _state(
        m.active_profile, m.current_state, m.previous_state, m.target_pad,
        m.channel, m.isolated_pad, m.GROUP_LAYOUT, m.group_current_states,
        m.group_previous_states, m.group_anchor_states,
    )
    return buf.getvalue(), out.sent, state, results


def run_runner(seed, steps, answers):
    out = Out()
    runner = GroupRunner(
        out, sleep=lambda *_: None, input_func=_Answers(answers)
    )
    random.seed(seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        results = []
        for fn_name, args in steps:
            results.append(getattr(runner, fn_name)(*args))
    state = _state(
        runner.active_profile, runner.current_state, runner.previous_state,
        runner.target_pad, runner.channel, runner.isolated_pad,
        runner.group_layout, runner.group_current_states,
        runner.group_previous_states, runner.group_anchor_states,
    )
    return buf.getvalue(), out.sent, state, results


def assert_parity(seed, steps, answers=()):
    mo, mm, ms, mr = run_monolith(seed, steps, answers)
    eo, em, es, er = run_runner(seed, steps, answers)
    assert mo == eo, "stdout mismatch:\\n--MONOLITH--\\n" + mo + "\\n--RUNNER--\\n" + eo
    assert mm == em, "midi mismatch:\\n" + repr(mm) + "\\n" + repr(em)
    assert ms == es, "state mismatch:\\n" + repr(ms) + "\\n" + repr(es)
    assert mr == er, "return mismatch:\\n" + repr(mr) + "\\n" + repr(er)
'''


# The warm worker for this file: ``_parity_worker`` is a module-scoped autouse
# fixture that launches/owns it and tears it down at module teardown;
# ``_run_parity`` ships one JSON request to it and asserts the parity check
# passed (a mismatch re-raises the worker's diff as an AssertionError -- same
# failure semantics as the old "fresh interpreter per call" version).
_parity_worker, _run_parity = make_parity_subprocess(_HARNESS)


def _parity_subprocess(
    steps_repr: str, answers_repr: str = "()", seed: int = 12345
) -> None:
    """Run the harness against ``steps`` on the warm worker; assert parity.

    ``steps_repr`` and ``answers_repr`` are still Python source reprs (exactly
    as every ``test_parity_*`` function builds them). ``parse_steps`` turns
    those same literals -- the ones the old code string-concatenated into
    ``assert_parity(seed, <steps_repr>, <answers_repr>)`` -- into real objects,
    shipped as JSON under the ``steps`` and ``answers`` keys so the warm
    worker's ``assert_parity(seed, steps, answers)`` receives them by name. The
    scripted ``input`` answer queue is rebuilt fresh inside the worker for
    every request, so each parity check is independent.
    """

    _run_parity(
        {
            "seed": seed,
            "steps": parse_steps(steps_repr),
            "answers": parse_steps(answers_repr),
        }
    )


# ===========================================================================
# In-process import-safety + smoke
# ===========================================================================

def test_import_is_silent_and_mido_free(capsys):
    """Importing the runner module opens no ports and pulls in no mido."""

    sys.modules.pop("rytm_randomizer.group_runner", None)
    sys.modules.pop("mido", None)
    import rytm_randomizer.group_runner as group_runner  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules


def test_runner_constructs_with_monolith_cold_start_defaults():
    _install_fake_mido()
    from rytm_randomizer.group_runner import GroupRunner, default_group_layout

    runner = GroupRunner(RecordingOut(), sleep=_no_sleep)

    assert runner.active_profile is None
    assert runner.current_state == {}
    assert runner.previous_state is None
    assert runner.target_pad == 1
    assert runner.channel == 0
    assert runner.isolated_pad == 3
    assert runner.group_current_states == {}
    assert runner.group_layout == default_group_layout()


def test_default_group_layout_is_a_fresh_mutable_copy():
    _install_fake_mido()
    from rytm_randomizer.group_runner import default_group_layout

    a = default_group_layout()
    b = default_group_layout()
    a[1]["profile"] = "MUTATED"
    assert b[1]["profile"] != "MUTATED"


# ===========================================================================
# In-process behavior coverage (fake mido) -- every method + every branch
# ===========================================================================

def _runner(**kwargs):
    _install_fake_mido()
    from rytm_randomizer.group_runner import GroupRunner

    return GroupRunner(RecordingOut(), sleep=_no_sleep, **kwargs)


# --- selected-profile / single-pad glue -----------------------------------

def test_select_profile_valid_choice(capsys):
    runner = _runner(input_func=lambda _p: "1")
    assert runner.select_profile() is True
    out = capsys.readouterr().out
    assert "Selected profile: My BD Hard" in out
    assert runner.active_profile is not None
    assert runner.current_state == {}
    assert runner.previous_state is None
    # send_machine emitted the CC15 switch.
    assert any(getattr(m, "control", None) == 15 for m in runner.out.sent)


def test_select_profile_invalid_choice(capsys):
    runner = _runner(input_func=lambda _p: "999")
    assert runner.select_profile() is False
    assert "Invalid profile." in capsys.readouterr().out
    assert runner.active_profile is None
    assert runner.out.sent == []


def test_require_profile_without_profile(capsys):
    runner = _runner()
    assert runner.require_profile() is False
    assert "Select a profile first with P." in capsys.readouterr().out


def test_require_profile_with_profile():
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    assert runner.require_profile() is True


def test_choose_target_pad_valid(capsys):
    runner = _runner(input_func=lambda _p: "3")
    assert runner.choose_target_pad() is True
    out = capsys.readouterr().out
    assert "Targeting Pad 3 / MIDI Channel 3" in out
    assert "shared/choke voice area" in out  # pad 3/4 branch
    assert runner.target_pad == 3
    assert runner.channel == 2


def test_choose_target_pad_pad1_no_choke_note(capsys):
    runner = _runner(input_func=lambda _p: "1")
    assert runner.choose_target_pad() is True
    assert "shared/choke voice area" not in capsys.readouterr().out


def test_choose_target_pad_invalid(capsys):
    runner = _runner(input_func=lambda _p: "9")
    assert runner.choose_target_pad() is False
    assert "Invalid pad. Keeping current target." in capsys.readouterr().out
    assert runner.target_pad == 1


def test_undo_without_profile(capsys):
    runner = _runner()
    runner.undo()
    assert "Select a profile first" in capsys.readouterr().out


def test_undo_without_previous_state(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    capsys.readouterr()
    runner.undo()
    assert "No previous script-generated state stored yet." in capsys.readouterr().out


def test_undo_restores_previous_state(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    # Seed a previous state so undo has something to restore.
    runner.previous_state = {"SRC Tune": 60}
    capsys.readouterr()
    runner.undo()
    out = capsys.readouterr().out
    assert "Undo: restoring previous script-generated state:" in out
    assert runner.current_state == {"SRC Tune": 60}
    assert runner.previous_state is None


def test_commit_current_as_anchor_without_profile(capsys):
    runner = _runner()
    runner.commit_current_as_anchor()
    assert "Select a profile first" in capsys.readouterr().out


def test_commit_current_as_anchor_without_current_state(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    capsys.readouterr()
    runner.commit_current_as_anchor()
    assert "No current state to commit." in capsys.readouterr().out


def test_commit_current_as_anchor_commits(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    runner.current_state = {"SRC Tune": 70}
    capsys.readouterr()
    runner.commit_current_as_anchor()
    assert "Current state committed as new anchor." in capsys.readouterr().out
    assert runner.anchor_state == {"SRC Tune": 70}


def test_show_anchor_without_profile(capsys):
    runner = _runner()
    runner.show_anchor()
    assert "Select a profile first" in capsys.readouterr().out


def test_show_anchor_with_profile(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    capsys.readouterr()
    runner.show_anchor()
    assert "Current anchor: My BD Hard" in capsys.readouterr().out


def test_show_anchor_skips_order_names_absent_from_anchor_state(capsys):
    """A param in the profile ``order`` but missing from ``anchor_state`` is
    skipped (the false branch of ``if name in self.anchor_state``)."""

    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    # Sparse anchor: only one of the profile's ``order`` params is present.
    first = runner.active_profile["order"][0]
    runner.anchor_state = {first: 42}
    capsys.readouterr()
    runner.show_anchor()
    out = capsys.readouterr().out
    assert f"{first}: 42" in out
    # A later order name absent from the sparse dict must have been skipped.
    assert len(runner.active_profile["order"]) > 1


def test_show_current_without_profile(capsys):
    runner = _runner()
    runner.show_current()
    assert "Select a profile first" in capsys.readouterr().out


def test_show_current_no_current_state(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    capsys.readouterr()
    runner.show_current()
    assert "No current state yet. Use M first." in capsys.readouterr().out


def test_show_current_with_current_state(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.select_profile()
    runner.current_state = {"SRC Tune": 64}
    capsys.readouterr()
    runner.show_current()
    out = capsys.readouterr().out
    assert "Current script state: My BD Hard" in out
    assert "SRC Tune: 64" in out


# --- group orchestration ---------------------------------------------------

def test_set_group_context_fallback_to_profile_anchor():
    runner = _runner()
    runner.set_group_context(2, "3")
    assert runner.target_pad == 2
    assert runner.channel == 1
    assert runner.active_profile is not None
    # No group state seeded -> current_state falls back to a copy of the anchor.
    assert runner.current_state == runner.anchor_state
    assert runner.previous_state is None


def test_set_group_context_uses_seeded_group_state():
    runner = _runner(
        group_anchor_states={2: {"SRC Tune": 10}},
        group_current_states={2: {"SRC Tune": 20}},
        group_previous_states={2: {"SRC Tune": 5}},
    )
    runner.set_group_context(2, "3")
    assert runner.anchor_state == {"SRC Tune": 10}
    assert runner.current_state == {"SRC Tune": 20}
    assert runner.previous_state == {"SRC Tune": 5}


def test_set_group_context_none_previous_state():
    runner = _runner(group_previous_states={2: None})
    runner.set_group_context(2, "3")
    assert runner.previous_state is None


def test_show_group_layout(capsys):
    runner = _runner()
    runner.show_group_layout()
    out = capsys.readouterr().out
    assert "4-pad group layout:" in out
    assert "Pad 1:" in out and "Pad 4:" in out


def test_load_group_anchors_loads_all_four_pads(capsys):
    runner = _runner()
    runner.load_group_anchors()
    out = capsys.readouterr().out
    assert "Loading full 4-pad group anchors:" in out
    assert "Full 4-pad group anchors loaded." in out
    assert set(runner.group_current_states) == {1, 2, 3, 4}
    assert set(runner.group_anchor_states) == {1, 2, 3, 4}
    assert all(v is None for v in runner.group_previous_states.values())


def test_return_group_to_anchors_guard_when_not_loaded(capsys):
    runner = _runner()
    runner.return_group_to_anchors()
    assert "No full group anchor state loaded yet. Use O first." in capsys.readouterr().out


def test_return_group_to_anchors_after_load(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.return_group_to_anchors()
    out = capsys.readouterr().out
    assert "Returning all 4 pads to group anchors:" in out
    assert "All 4 pads returned to anchors." in out


def test_ensure_group_anchors_loaded_autoloads(capsys):
    runner = _runner()
    assert runner.ensure_group_anchors_loaded("test caller") is True
    out = capsys.readouterr().out
    assert "test caller: four-pad state is not loaded yet." in out
    assert set(runner.group_current_states) == {1, 2, 3, 4}


def test_ensure_group_anchors_loaded_noop_when_loaded(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    assert runner.ensure_group_anchors_loaded("test caller") is True
    assert "not loaded yet" not in capsys.readouterr().out


def test_mutate_group_pad_records_state(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    cfg = runner.group_layout[2]
    runner.mutate_group_pad(2, cfg, cfg["zone"], cfg["depth"])
    out = capsys.readouterr().out
    assert "Group zone:" in out
    assert 2 in runner.group_current_states


def test_mutate_group_pad_records_none_previous_when_falsy(capsys):
    """When ``_mutate_zone`` leaves ``previous_state`` falsy, ``mutate_group_pad``
    stores ``None`` (the ``else`` branch of its ``if self.previous_state``).

    This mirrors the monolith's defensive ``if previous_state:`` guard. In
    practice the shared mutation engine always produces a non-empty previous
    state, so the falsy path is forced here by stubbing ``_mutate_zone`` to
    leave ``previous_state`` falsy -- exactly the condition the guard exists
    for.
    """

    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    cfg = runner.group_layout[2]

    def _stub_mutate_zone(_zone, _depth):
        runner.previous_state = None  # falsy -> exercises the else branch

    runner._mutate_zone = _stub_mutate_zone  # type: ignore[method-assign]
    runner.mutate_group_pad(2, cfg, cfg["zone"], cfg["depth"])
    capsys.readouterr()
    assert runner.group_previous_states[2] is None


def test_apply_state_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_apply_state`` with no active profile is a
    no-op write-back (mirrors the monolith ``require_profile`` guard)."""

    runner = _runner()
    runner.active_profile = None
    before_current = dict(runner.current_state)
    before_anchor = dict(runner.anchor_state)

    runner._apply_state({"SRC Tune": 60}, "No Profile")

    assert runner.current_state == before_current
    assert runner.anchor_state == before_anchor
    assert runner.previous_state is None
    assert "Select a profile first" in capsys.readouterr().out


def test_mutate_zone_shim_noop_when_no_profile(capsys):
    """Defensive parity branch: ``_mutate_zone`` with no active profile leaves
    current/previous state untouched."""

    runner = _runner()
    runner.active_profile = None
    before_current = dict(runner.current_state)

    runner._mutate_zone("body", "micro")

    assert runner.current_state == before_current
    assert runner.previous_state is None
    capsys.readouterr()


def test_mutate_group_autoloads_then_mutates(capsys):
    runner = _runner()
    runner.mutate_group()
    out = capsys.readouterr().out
    assert "4-pad group mutation:" in out
    assert "4-pad group mutation complete." in out


def test_mutate_group_skips_unavailable_zone(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    # 'definitely-not-a-zone' is unavailable for every profile -> skip branch.
    runner.mutate_group(zone_override="definitely-not-a-zone")
    out = capsys.readouterr().out
    assert "not available for this profile. Skipping." in out


def test_mutate_group_intensity_unknown_plan(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_group_intensity("does-not-exist")
    assert "Unknown intensity plan: does-not-exist" in capsys.readouterr().out


def test_mutate_group_intensity_known_plan(capsys):
    runner = _runner()
    runner.mutate_group_intensity("balanced")
    out = capsys.readouterr().out
    assert "BALANCED / FOUR-LANE" in out
    assert "mutation complete." in out


def test_mutate_group_intensity_label_fallback(capsys):
    """A plan key without a friendly label uses the ``.upper()`` fallback."""

    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_group_intensity("rolling_light")
    out = capsys.readouterr().out
    assert "ROLLING_LIGHT" in out


def test_mutate_group_intensity_skips_unavailable_zone(capsys, monkeypatch):
    """An intensity plan referencing an unavailable zone hits the skip branch."""

    _install_fake_mido()
    import rytm_randomizer.group_runner as gr

    runner = gr.GroupRunner(RecordingOut(), sleep=_no_sleep)
    runner.load_group_anchors()
    capsys.readouterr()
    monkeypatch.setitem(
        gr.INTENSITY_PLANS, "fake_plan", {1: [("not-a-zone", "micro")]}
    )
    runner.mutate_group_intensity("fake_plan")
    assert "not available for this profile. Skipping." in capsys.readouterr().out


def test_mutate_group_with_depth(capsys):
    runner = _runner(input_func=lambda _p: "1")  # depth choice 1 -> micro
    runner.mutate_group_with_depth("body")
    out = capsys.readouterr().out
    assert "4-pad group mutation:" in out


def test_mutate_global_page_plan_unknown(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_global_page_plan("not-a-page")
    assert "Unknown global page plan: not-a-page" in capsys.readouterr().out


def test_mutate_global_page_plan_known(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.mutate_global_page_plan("src")
    out = capsys.readouterr().out
    assert "lane-aware SRC mutation" in out
    assert "lane-aware SRC mutation complete." in out


def test_mutate_global_page_plan_skips_unavailable_zone(capsys, monkeypatch):
    _install_fake_mido()
    import rytm_randomizer.group_runner as gr

    runner = gr.GroupRunner(
        RecordingOut(), sleep=_no_sleep, input_func=lambda _p: "1"
    )
    runner.load_group_anchors()
    capsys.readouterr()
    monkeypatch.setitem(gr.GLOBAL_PAGE_PLANS, "fake_page", {1: ["not-a-zone"]})
    runner.mutate_global_page_plan("fake_page")
    assert "not available for" in capsys.readouterr().out


def test_show_global_mutation_tools(capsys):
    runner = _runner()
    runner.show_global_mutation_tools()
    assert "Global 4-Pad Mutation Tools - V1.34" in capsys.readouterr().out


# --- isolated single-pad orchestration ------------------------------------

def test_choose_isolated_pad_valid(capsys):
    runner = _runner(input_func=lambda _p: "2")
    assert runner.choose_isolated_pad() is True
    assert runner.isolated_pad == 2
    assert "Isolated mutation target: Pad 2" in capsys.readouterr().out


def test_choose_isolated_pad_invalid(capsys):
    runner = _runner(input_func=lambda _p: "x")
    assert runner.choose_isolated_pad() is False
    assert "Invalid pad. Keeping current isolated pad." in capsys.readouterr().out
    assert runner.isolated_pad == 3


def test_require_group_for_single_pad_guard(capsys):
    runner = _runner()
    assert runner.require_group_for_single_pad() is False
    assert "Load the full 4-pad group first with O." in capsys.readouterr().out


def test_require_group_for_single_pad_ok():
    runner = _runner()
    runner.load_group_anchors()
    assert runner.require_group_for_single_pad() is True


def test_show_isolated_pad_not_loaded(capsys):
    runner = _runner()
    runner.show_isolated_pad()
    out = capsys.readouterr().out
    assert "Selected isolated pad: Pad 3" in out
    assert "not loaded yet" in out


def test_show_isolated_pad_loaded(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.show_isolated_pad()
    assert "Current state: loaded" in capsys.readouterr().out


def test_mutate_isolated_pad_guard(capsys):
    runner = _runner()
    runner.mutate_isolated_pad()
    assert "Load the full 4-pad group first" in capsys.readouterr().out


def test_mutate_isolated_pad_unavailable_zone(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_isolated_pad(zone_name="not-a-zone")
    assert "is not available for" in capsys.readouterr().out


def test_mutate_isolated_pad_default_zone(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_isolated_pad()
    out = capsys.readouterr().out
    assert "Isolated single-pad mutation:" in out
    assert "isolated mutation complete." in out


def test_mutate_isolated_pad_with_depth(capsys):
    runner = _runner(input_func=lambda _p: "1")
    runner.load_group_anchors()
    capsys.readouterr()
    runner.mutate_isolated_pad_with_depth("lfo")
    assert "Isolated single-pad mutation:" in capsys.readouterr().out


def test_return_isolated_pad_to_anchor_guard(capsys):
    runner = _runner()
    runner.return_isolated_pad_to_anchor()
    assert "Load the full 4-pad group first" in capsys.readouterr().out


def test_return_isolated_pad_to_anchor(capsys):
    runner = _runner()
    runner.load_group_anchors()
    capsys.readouterr()
    runner.return_isolated_pad_to_anchor()
    out = capsys.readouterr().out
    assert "Returning isolated pad to anchor:" in out
    assert "returned to anchor." in out


# ===========================================================================
# Subprocess parity vs the committed monolith -- byte-identical behavior
# ===========================================================================

def test_parity_select_profile_all_menu_choices():
    for menu in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"]:
        _parity_subprocess(
            "[('select_profile', ())]", answers_repr=f"[{menu!r}]"
        )


def test_parity_select_profile_invalid():
    _parity_subprocess("[('select_profile', ())]", answers_repr="['999']")


def test_parity_require_profile():
    _parity_subprocess("[('require_profile', ())]")
    _parity_subprocess(
        "[('select_profile', ()), ('require_profile', ())]",
        answers_repr="['1']",
    )


def test_parity_choose_target_pad():
    for pad in ["1", "2", "3", "4", "bad"]:
        _parity_subprocess(
            "[('choose_target_pad', ())]", answers_repr=f"[{pad!r}]"
        )


def test_parity_undo_paths():
    _parity_subprocess("[('undo', ())]")  # no profile
    _parity_subprocess(
        "[('select_profile', ()), ('undo', ())]", answers_repr="['1']"
    )


def test_parity_commit_show_anchor_current():
    _parity_subprocess("[('commit_current_as_anchor', ())]")
    _parity_subprocess("[('show_anchor', ())]")
    _parity_subprocess("[('show_current', ())]")
    _parity_subprocess(
        "[('select_profile', ()), ('show_anchor', ()), ('show_current', ()), "
        "('commit_current_as_anchor', ())]",
        answers_repr="['1']",
    )


def test_parity_set_group_context_and_layout():
    _parity_subprocess("[('set_group_context', (2, '3'))]")
    _parity_subprocess("[('show_group_layout', ())]")


def test_parity_load_and_return_group_anchors():
    _parity_subprocess("[('load_group_anchors', ())]")
    _parity_subprocess("[('return_group_to_anchors', ())]")  # guard
    _parity_subprocess(
        "[('load_group_anchors', ()), ('return_group_to_anchors', ())]"
    )


def test_parity_ensure_group_anchors_loaded():
    _parity_subprocess("[('ensure_group_anchors_loaded', ())]")
    _parity_subprocess(
        "[('load_group_anchors', ()), ('ensure_group_anchors_loaded', ())]"
    )


def test_parity_mutate_group():
    for seed in (1, 7, 42):
        _parity_subprocess("[('mutate_group', ())]", seed=seed)
    _parity_subprocess("[('mutate_group', ('definitely-not-a-zone',))]")


@pytest.mark.parametrize(
    "plan",
    [
        "balanced", "deeper", "intense", "harder", "rolling_light",
        "rolling_push", "deeper_groove", "deeper_pressure", "intense_motion",
        "intense_grit", "wild_controlled", "wild_maximum",
    ],
)
@pytest.mark.parametrize("seed", [1, 11])
def test_parity_mutate_group_intensity(plan, seed):
    """One parity call per (plan, seed) so xdist can fan the 24 cases across
    workers (was a single ~117s test before the split)."""

    _parity_subprocess(
        f"[('mutate_group_intensity', ({plan!r},))]", seed=seed
    )


def test_parity_mutate_group_intensity_unknown_plan():
    """Unknown plan key -- single-call check."""

    _parity_subprocess("[('mutate_group_intensity', ('nope',))]")


def test_parity_mutate_group_with_depth():
    for depth in ["1", "2", "3"]:
        _parity_subprocess(
            "[('mutate_group_with_depth', ('body',))]",
            answers_repr=f"[{depth!r}]",
        )


@pytest.mark.parametrize("page", ["src", "filter", "grit"])
@pytest.mark.parametrize("depth", ["1", "2", "3"])
def test_parity_mutate_global_page_plan(page, depth):
    """One parity call per (page, depth) so xdist can fan the 9 cases across
    workers (was a single ~40s test before the split)."""

    _parity_subprocess(
        f"[('mutate_global_page_plan', ({page!r},))]",
        answers_repr=f"[{depth!r}]",
    )


def test_parity_mutate_global_page_plan_unknown_page():
    """Unknown page key -- single-call check."""

    _parity_subprocess(
        "[('mutate_global_page_plan', ('nope',))]", answers_repr="['1']"
    )


def test_parity_show_global_mutation_tools():
    _parity_subprocess("[('show_global_mutation_tools', ())]")


def test_parity_choose_isolated_pad():
    for pad in ["1", "2", "3", "4", "bad"]:
        _parity_subprocess(
            "[('choose_isolated_pad', ())]", answers_repr=f"[{pad!r}]"
        )


def test_parity_isolated_pad_guards_and_status():
    _parity_subprocess("[('require_group_for_single_pad', ())]")
    _parity_subprocess("[('show_isolated_pad', ())]")
    _parity_subprocess(
        "[('load_group_anchors', ()), ('require_group_for_single_pad', ()), "
        "('show_isolated_pad', ())]"
    )


def test_parity_mutate_isolated_pad():
    _parity_subprocess("[('mutate_isolated_pad', ())]")  # guard
    for seed in (1, 7, 42):
        _parity_subprocess(
            "[('load_group_anchors', ()), ('mutate_isolated_pad', ())]",
            seed=seed,
        )
    _parity_subprocess(
        "[('load_group_anchors', ()), "
        "('mutate_isolated_pad', ('not-a-zone',))]"
    )


def test_parity_mutate_isolated_pad_with_depth():
    for depth in ["1", "2", "3"]:
        _parity_subprocess(
            "[('load_group_anchors', ()), "
            "('mutate_isolated_pad_with_depth', ('lfo',))]",
            answers_repr=f"[{depth!r}]",
        )


def test_parity_return_isolated_pad_to_anchor():
    _parity_subprocess("[('return_isolated_pad_to_anchor', ())]")  # guard
    _parity_subprocess(
        "[('load_group_anchors', ()), ('return_isolated_pad_to_anchor', ())]"
    )


@pytest.mark.parametrize("seed", [1, 7, 99, 2024])
def test_parity_long_interactive_session(seed):
    """A realistic multi-step group session: load, mutate, isolate, return.

    One parity call per seed so xdist can fan the 4 cases across workers (was
    a single ~42s test before the split). The *sequence* itself is ordered,
    but the four seeds are independent parity checks."""

    steps = (
        "["
        "('load_group_anchors', ()), "
        "('mutate_group', ()), "
        "('mutate_group_intensity', ('deeper',)), "
        "('mutate_global_page_plan', ('src',)), "
        "('choose_isolated_pad', ()), "
        "('mutate_isolated_pad', ()), "
        "('mutate_isolated_pad_with_depth', ('filter',)), "
        "('return_isolated_pad_to_anchor', ()), "
        "('return_group_to_anchors', ())"
        "]"
    )
    # answers: choose_isolated_pad -> '2', the two depth prompts -> '2','3'
    _parity_subprocess(steps, answers_repr="['2', '2', '3']", seed=seed)
