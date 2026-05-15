"""Characterization + parity tests for the scene / preset orchestrator
(Wave 4 / WS-N).

These tests lock in the V1.34 monolith's CURRENT behavior for ``show_scene_tools``
and ``run_scene`` (the 14 scene commands S0-S5 with A/B variants), then prove the
extracted :class:`rytm_randomizer.scene_runner.SceneRunner` reproduces it
byte-identically: same printed output, same MIDI message stream, same resulting
four-pad state and ``current_scene_name``.

The most important parity targets are the documented validation flow
``SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5`` and the SCN guardrail (``SCN``
must send NO MIDI and must NOT load anchors).

Isolation rules match ``tests/test_group_runner.py`` / ``tests/test_engines_pad1.py``:
monolith-touching code runs in a subprocess. That subprocess is a single
**warm worker** reused across every parity check in this file (see
``tests/_parity_worker.py``) -- it cold-imports the monolith + package once,
then services one parity request per stdin line. In-process tests use a fake
``mido``.
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

    Guards the in-process tests against leaked in-place mutation of the shared
    package data dicts (subprocess parity tests run in a separate interpreter
    and are unaffected).
    """

    from rytm_randomizer.data import GROUP_LAYOUT, PROFILES

    profile_anchors = {key: dict(profile["anchor"]) for key, profile in PROFILES.items()}
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
# defines ``assert_parity(seed, scene_steps)`` which builds a monolith scene run
# and a SceneRunner run from the same RNG seed, captures stdout + MIDI + the
# four-pad state + current_scene_name, and asserts byte-parity. The worker loop
# appended by ``tests/_parity_worker.py`` calls it once per JSON request line.
_HARNESS = '''
import io, contextlib, random
import rytm_hybrid_randomizer_v134 as m
from rytm_randomizer import midi_io, randomization
from rytm_randomizer.group_runner import GroupRunner, default_group_layout
from rytm_randomizer.scene_runner import SceneRunner

midi_io.time.sleep = lambda *_: None
randomization.time.sleep = lambda *_: None


class Out:
    def __init__(self):
        self.sent = []

    def send(self, msg):
        self.sent.append((msg.type, msg.channel, msg.control, msg.value))


def _reset_monolith():
    """Restore the monolith globals the scene functions touch to cold start."""
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
    m.current_scene_name = "None"
    m.GROUP_LAYOUT = {pad: dict(cfg) for pad, cfg in default_group_layout().items()}


def _state(scene_name, gcur, gprev, ganc):
    return {
        "scene": scene_name,
        "gcur": {k: dict(v) for k, v in gcur.items()},
        "gprev": {k: (dict(v) if v else v) for k, v in gprev.items()},
        "ganc": {k: dict(v) for k, v in ganc.items()},
    }


def run_monolith(seed, scene_steps):
    """scene_steps: list of ('scn'|'gm'|scene_key)."""
    _reset_monolith()
    out = Out()
    random.seed(seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for step in scene_steps:
            if step == "scn":
                m.show_scene_tools()
            elif step == "gm":
                m.show_global_mutation_tools()
            else:
                m.run_scene(out, step)
    state = _state(
        m.current_scene_name, m.group_current_states,
        m.group_previous_states, m.group_anchor_states,
    )
    return buf.getvalue(), out.sent, state


def run_runner(seed, scene_steps):
    out = Out()
    group = GroupRunner(out, sleep=lambda *_: None)
    runner = SceneRunner(group)
    random.seed(seed)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        for step in scene_steps:
            if step == "scn":
                runner.show_scene_tools()
            elif step == "gm":
                group.show_global_mutation_tools()
            else:
                runner.run_scene(step)
    state = _state(
        runner.current_scene_name, group.group_current_states,
        group.group_previous_states, group.group_anchor_states,
    )
    return buf.getvalue(), out.sent, state


def assert_parity(seed, scene_steps):
    mo, mm, ms = run_monolith(seed, scene_steps)
    eo, em, es = run_runner(seed, scene_steps)
    assert mo == eo, "stdout mismatch:\\n--MONOLITH--\\n" + mo + "\\n--RUNNER--\\n" + eo
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
    """Run the harness against ``scene_steps`` on the warm worker; assert parity.

    ``steps_repr`` is still a Python source repr of the scene-steps list
    (exactly as every ``test_parity_*`` function builds it). ``parse_steps``
    turns that same literal -- the one the old code string-concatenated into
    ``assert_parity(seed, <steps_repr>)`` -- into the real object, shipped as
    JSON under the ``scene_steps`` key so the warm worker's
    ``assert_parity(seed, scene_steps)`` receives it positionally-by-name.
    """

    _run_parity({"seed": seed, "scene_steps": parse_steps(steps_repr)})


# ===========================================================================
# In-process import-safety + smoke
# ===========================================================================


def test_import_is_silent_and_mido_free(capsys):
    """Importing the scene runner module opens no ports and pulls in no mido."""

    sys.modules.pop("rytm_randomizer.scene_runner", None)
    sys.modules.pop("mido", None)
    import rytm_randomizer.scene_runner as scene_runner  # noqa: F401

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert "mido" not in sys.modules


def _scene_runner(**group_kwargs):
    _install_fake_mido()
    from rytm_randomizer.group_runner import GroupRunner
    from rytm_randomizer.scene_runner import SceneRunner

    group = GroupRunner(RecordingOut(), sleep=_no_sleep, **group_kwargs)
    return SceneRunner(group), group


def test_scene_runner_constructs_with_default_scene_name():
    runner, _group = _scene_runner()
    assert runner.current_scene_name == "None"


def test_scene_runner_accepts_explicit_scene_name():
    _install_fake_mido()
    from rytm_randomizer.group_runner import GroupRunner
    from rytm_randomizer.scene_runner import SceneRunner

    group = GroupRunner(RecordingOut(), sleep=_no_sleep)
    runner = SceneRunner(group, current_scene_name="Rolling")
    assert runner.current_scene_name == "Rolling"


# ===========================================================================
# In-process behavior coverage (fake mido) -- every branch
# ===========================================================================


def test_show_scene_tools_not_loaded_branch(capsys):
    runner, _group = _scene_runner()
    runner.show_scene_tools()
    out = capsys.readouterr().out
    assert "Scene / Preset Tools - V1.34" in out
    assert "Four-pad state: not loaded yet" in out


def test_show_scene_tools_loaded_branch(capsys):
    runner, group = _scene_runner()
    group.load_group_anchors()
    capsys.readouterr()
    runner.show_scene_tools()
    assert "Four-pad state: loaded" in capsys.readouterr().out


def test_show_scene_tools_sends_no_midi_and_does_not_load(capsys):
    """SCN guardrail: it only prints -- no MIDI, no anchor load."""

    runner, group = _scene_runner()
    runner.show_scene_tools()
    capsys.readouterr()
    assert group.out.sent == []
    assert group.group_current_states == {}


def test_run_scene_unknown_key(capsys):
    runner, _group = _scene_runner()
    runner.run_scene("s99")
    out = capsys.readouterr().out
    assert "Unknown scene command: S99" in out
    # Falls through to show_scene_tools.
    assert "Scene / Preset Tools - V1.34" in out


def test_run_scene_home_cold_loads_anchors(capsys):
    runner, group = _scene_runner()
    runner.run_scene("s0")
    out = capsys.readouterr().out
    assert "Four-pad state not loaded yet. Loading validated anchors now." in out
    assert runner.current_scene_name == "Home / Clean"
    assert set(group.group_current_states) == {1, 2, 3, 4}


def test_run_scene_home_warm_returns_to_anchors(capsys):
    runner, group = _scene_runner()
    group.load_group_anchors()
    capsys.readouterr()
    runner.run_scene("s0")
    out = capsys.readouterr().out
    assert "Returning all four pads to validated anchors." in out
    assert runner.current_scene_name == "Home / Clean"


def test_run_scene_clean_cold_loads_anchors(capsys):
    runner, group = _scene_runner()
    runner.run_scene("s5")
    out = capsys.readouterr().out
    assert "Four-pad state not loaded yet. Loading validated anchors now." in out
    assert runner.current_scene_name == "Back to Clean"


def test_run_scene_clean_warm_returns_to_anchors(capsys):
    runner, group = _scene_runner()
    group.load_group_anchors()
    capsys.readouterr()
    runner.run_scene("s5")
    assert "Returning all four pads to validated anchors." in capsys.readouterr().out


def test_run_scene_intensity_autoloads_then_mutates(capsys):
    runner, group = _scene_runner()
    runner.run_scene("s1")
    out = capsys.readouterr().out
    assert "Applying scene through the validated global four-lane mutation layer." in out
    assert runner.current_scene_name == "Rolling"
    assert set(group.group_current_states) == {1, 2, 3, 4}


def test_run_scene_intensity_warm_no_autoload_message(capsys):
    runner, group = _scene_runner()
    group.load_group_anchors()
    capsys.readouterr()
    runner.run_scene("s3a")
    out = capsys.readouterr().out
    assert "four-pad state is not loaded yet" not in out
    assert runner.current_scene_name == "Intense Motion"


@pytest.mark.parametrize(
    "scene_key,expected_name",
    [
        ("s0", "Home / Clean"),
        ("s1", "Rolling"),
        ("s1a", "Rolling Light"),
        ("s1b", "Rolling Push"),
        ("s2", "Deeper"),
        ("s2a", "Deeper Groove"),
        ("s2b", "Deeper Pressure"),
        ("s3", "Intense"),
        ("s3a", "Intense Motion"),
        ("s3b", "Intense Grit"),
        ("s4", "Wild"),
        ("s4a", "Wild Controlled"),
        ("s4b", "Wild Maximum"),
        ("s5", "Back to Clean"),
    ],
)
def test_run_scene_every_command_sets_scene_name(scene_key, expected_name, capsys):
    runner, _group = _scene_runner()
    runner.run_scene(scene_key)
    capsys.readouterr()
    assert runner.current_scene_name == expected_name


# ===========================================================================
# Subprocess parity vs the committed monolith -- byte-identical behavior
# ===========================================================================


def test_parity_show_scene_tools_cold():
    _parity_subprocess("['scn']")


def test_parity_show_scene_tools_after_load():
    _parity_subprocess("['s0', 'scn']")


def test_parity_run_scene_unknown_key():
    _parity_subprocess("['s99']")


@pytest.mark.parametrize(
    "key",
    [
        "s0",
        "s1",
        "s1a",
        "s1b",
        "s2",
        "s2a",
        "s2b",
        "s3",
        "s3a",
        "s3b",
        "s4",
        "s4a",
        "s4b",
        "s5",
    ],
)
@pytest.mark.parametrize("seed", [1, 42])
def test_parity_every_scene_command_cold(key, seed):
    """One parity call per (key, seed) so xdist can fan the 28 cases across
    workers (was a single ~129s test before the split). Each scene command
    is a self-contained cold-start parity check."""

    _parity_subprocess(f"[{key!r}]", seed=seed)


def test_parity_home_warm_vs_cold():
    _parity_subprocess("['s0']")  # cold -> load
    _parity_subprocess("['s0', 's0']")  # second time -> return
    _parity_subprocess("['s1', 's5']")  # warm clean -> return


@pytest.mark.parametrize("seed", [1, 7, 99, 2024, 12345])
def test_parity_documented_validation_flow(seed):
    """The documented V1.34 scene validation flow must reproduce exactly.

    One parity call per seed so xdist can fan the 5 cases across workers
    (was a single ~58s test before the split)."""

    flow = "['scn', 'gm', 's1a', 's3a', 's3b', 's4b', 's5']"
    _parity_subprocess(flow, seed=seed)


@pytest.mark.parametrize("seed", [3, 88, 2024])
def test_parity_full_scene_walk(seed):
    """Walk every scene command in sequence from a single cold start.

    One parity call per seed so xdist can fan the 3 cases across workers
    (was a single ~60s test before the split)."""

    walk = (
        "['scn', 's0', 's1', 's1a', 's1b', 's2', 's2a', 's2b', "
        "'s3', 's3a', 's3b', 's4', 's4a', 's4b', 's5', 'scn']"
    )
    _parity_subprocess(walk, seed=seed)
