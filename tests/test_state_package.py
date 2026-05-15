"""Characterization + parity tests for the rytm_randomizer.state package.

These tests capture the monolith's CURRENT state-transition behavior for the
~12 mutable module-level globals WS-L extracts, then prove the per-domain
frozen-dataclass state objects reproduce the same transitions.

The monolith does ``import mido`` at module scope, and the package's
import-safety tests assert real ``mido`` is absent from ``sys.modules``. So,
following the established ``test_midi_io`` pattern, the monolith's cold-start
globals are captured in a *subprocess* (never importing the monolith into this
test process) and an autouse fixture restores ``sys.modules`` after every test.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import MappingProxyType

import pytest

from rytm_randomizer.state import anchor, group, pad_mode, scene, selection

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot ``sys.modules`` and restore it after every test.

    Keeps the monolith (and its real ``mido``) from leaking between tests.
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


def _monolith_global_defaults() -> dict:
    """Capture the monolith's cold-start globals via a fresh subprocess.

    Importing the monolith here would pull real ``mido`` into this process's
    ``sys.modules`` and break the package's import-safety tests, so the
    snapshot is taken out-of-process.
    """

    code = (
        "import json\n"
        "import rytm_hybrid_randomizer_v134 as m\n"
        "print(json.dumps({\n"
        "    'active_profile': m.active_profile,\n"
        "    'anchor_state': m.anchor_state,\n"
        "    'current_state': m.current_state,\n"
        "    'previous_state': m.previous_state,\n"
        "    'group_anchor_states': m.group_anchor_states,\n"
        "    'group_current_states': m.group_current_states,\n"
        "    'group_previous_states': m.group_previous_states,\n"
        "    'target_pad': m.target_pad,\n"
        "    'channel': m.channel,\n"
        "    'isolated_pad': m.isolated_pad,\n"
        "    'current_scene_name': m.current_scene_name,\n"
        "    'pad2_current_profile_key': m.pad2_current_profile_key,\n"
        "    'pad3_current_mode_key': m.pad3_current_mode_key,\n"
        "    'pad4_current_mode_key': m.pad4_current_mode_key,\n"
        "}))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# Monolith default characterization: snapshot the cold-start global values.
# ---------------------------------------------------------------------------


def test_monolith_global_defaults_snapshot():
    """Lock the monolith's documented cold-start globals (captured out-of-process)."""

    defaults = _monolith_global_defaults()

    assert defaults["active_profile"] is None
    assert defaults["anchor_state"] == {}
    assert defaults["current_state"] == {}
    assert defaults["previous_state"] is None
    assert defaults["group_anchor_states"] == {}
    assert defaults["group_current_states"] == {}
    assert defaults["group_previous_states"] == {}
    assert defaults["target_pad"] == 1
    assert defaults["channel"] == 0
    assert defaults["isolated_pad"] == 3
    assert defaults["current_scene_name"] == "None"
    assert defaults["pad2_current_profile_key"] == "3"
    assert defaults["pad3_current_mode_key"] == "anchor"
    assert defaults["pad4_current_mode_key"] == "anchor"


def test_package_initial_states_match_monolith_defaults():
    """Each domain's initial state object reproduces the monolith defaults."""

    defaults = _monolith_global_defaults()

    a = anchor.initial_anchor_runtime_state()
    assert a.active_profile is defaults["active_profile"]
    assert dict(a.anchor_state) == defaults["anchor_state"]
    assert dict(a.current_state) == defaults["current_state"]
    assert a.previous_state == defaults["previous_state"]

    g = group.initial_group_runtime_state()
    assert dict(g.group_anchor_states) == defaults["group_anchor_states"]
    assert dict(g.group_current_states) == defaults["group_current_states"]
    assert dict(g.group_previous_states) == defaults["group_previous_states"]
    assert g.loaded is False

    s = selection.initial_selection_state()
    assert (s.target_pad, s.channel, s.isolated_pad) == (
        defaults["target_pad"],
        defaults["channel"],
        defaults["isolated_pad"],
    )

    pm = pad_mode.initial_pad_mode_state()
    assert pm.pad2_current_profile_key == defaults["pad2_current_profile_key"]
    assert pm.pad3_current_mode_key == defaults["pad3_current_mode_key"]
    assert pm.pad4_current_mode_key == defaults["pad4_current_mode_key"]

    sc = scene.initial_scene_state()
    assert sc.current_scene_name == defaults["current_scene_name"]


# ---------------------------------------------------------------------------
# Frozen / immutability guarantees.
# ---------------------------------------------------------------------------


def test_state_objects_are_frozen():
    """All five dataclasses reject attribute assignment."""

    for obj, attr in (
        (anchor.initial_anchor_runtime_state(), "active_profile"),
        (group.initial_group_runtime_state(), "group_anchor_states"),
        (selection.initial_selection_state(), "target_pad"),
        (pad_mode.initial_pad_mode_state(), "pad2_current_profile_key"),
        (scene.initial_scene_state(), "current_scene_name"),
    ):
        with pytest.raises(Exception):
            setattr(obj, attr, "mutated")


def test_anchor_mappings_are_immutable():
    """Anchor state dict-like fields are MappingProxyType (read-only)."""

    a = anchor.AnchorRuntimeState(
        active_profile={"name": "p", "anchor": {}},
        anchor_state={"x": 1},
        current_state={"y": 2},
        previous_state={"z": 3},
    )
    assert isinstance(a.anchor_state, MappingProxyType)
    assert isinstance(a.current_state, MappingProxyType)
    assert isinstance(a.previous_state, MappingProxyType)
    assert isinstance(a.active_profile, MappingProxyType)
    with pytest.raises(TypeError):
        a.anchor_state["x"] = 99
    with pytest.raises(TypeError):
        a.current_state["y"] = 99
    with pytest.raises(TypeError):
        a.previous_state["z"] = 99


def test_group_mappings_are_immutable():
    """Group pad-keyed mappings and their nested dicts are read-only."""

    g = group.GroupRuntimeState(
        group_anchor_states={1: {"a": 1}},
        group_current_states={2: {"b": 2}},
        group_previous_states={3: {"c": 3}},
    )
    assert isinstance(g.group_anchor_states, MappingProxyType)
    with pytest.raises(TypeError):
        g.group_anchor_states[1] = {}
    with pytest.raises(TypeError):
        g.group_anchor_states[1]["a"] = 99


def test_anchor_state_input_dicts_are_copied():
    """Mutating the source dict after construction does not leak into state."""

    src = {"x": 1}
    a = anchor.AnchorRuntimeState(anchor_state=src)
    src["x"] = 999
    assert dict(a.anchor_state) == {"x": 1}


def test_group_state_input_dicts_are_copied():
    """Mutating source pad dicts after construction does not leak into state."""

    nested = {"a": 1}
    g = group.GroupRuntimeState(group_anchor_states={1: nested})
    nested["a"] = 999
    assert dict(g.group_anchor_states[1]) == {"a": 1}


# ---------------------------------------------------------------------------
# Anchor domain: parity with monolith select_profile / undo / commit.
# ---------------------------------------------------------------------------


def _monolith_select_profile(profile):
    """Reproduce the monolith select_profile global moves (no I/O)."""

    return {
        "active_profile": profile,
        "anchor_state": profile["anchor"].copy(),
        "current_state": {},
        "previous_state": None,
    }


def test_select_profile_parity():
    """Package select_profile matches the monolith's global moves."""

    profile = {"name": "BD Hard", "anchor": {"tune": 10, "decay": 64}, "order": []}
    expected = _monolith_select_profile(profile)

    state = anchor.select_profile(anchor.initial_anchor_runtime_state(), profile)

    assert state.active_profile is not None
    assert dict(state.active_profile) == profile
    assert dict(state.anchor_state) == expected["anchor_state"]
    assert dict(state.current_state) == expected["current_state"]
    assert state.previous_state == expected["previous_state"]


def test_select_profile_resets_current_and_previous():
    """select_profile from a populated state still resets current/previous."""

    profile = {"name": "p", "anchor": {"tune": 5}}
    populated = anchor.AnchorRuntimeState(
        active_profile={"name": "old", "anchor": {}},
        anchor_state={"old": 1},
        current_state={"old": 2},
        previous_state={"old": 3},
    )
    state = anchor.select_profile(populated, profile)
    assert dict(state.anchor_state) == {"tune": 5}
    assert dict(state.current_state) == {}
    assert state.previous_state is None


def test_apply_state_result_writeback():
    """apply_state_result copies back anchor/current/previous, keeps profile."""

    profile = {"name": "p", "anchor": {}}
    base = anchor.AnchorRuntimeState(active_profile=profile)
    state = anchor.apply_state_result(
        base,
        anchor_state={"a": 1},
        current_state={"c": 2},
        previous_state={"p": 3},
    )
    assert dict(state.active_profile) == profile
    assert dict(state.anchor_state) == {"a": 1}
    assert dict(state.current_state) == {"c": 2}
    assert dict(state.previous_state) == {"p": 3}


def test_apply_state_result_none_previous():
    """apply_state_result handles a None previous_state (monolith parity)."""

    state = anchor.apply_state_result(
        anchor.initial_anchor_runtime_state(),
        anchor_state={"a": 1},
        current_state={"c": 2},
        previous_state=None,
    )
    assert state.previous_state is None


def test_mutate_result_keeps_anchor_and_profile():
    """mutate_result only replaces current/previous (monolith mutate_zone shim)."""

    profile = {"name": "p", "anchor": {}}
    base = anchor.AnchorRuntimeState(
        active_profile=profile, anchor_state={"a": 1}, current_state={"c": 0}
    )
    state = anchor.mutate_result(base, current_state={"c": 9}, previous_state={"c": 0})
    assert dict(state.anchor_state) == {"a": 1}
    assert dict(state.active_profile) == profile
    assert dict(state.current_state) == {"c": 9}
    assert dict(state.previous_state) == {"c": 0}


def test_mutate_result_none_previous():
    """mutate_result handles a None previous_state."""

    state = anchor.mutate_result(
        anchor.initial_anchor_runtime_state(),
        current_state={"c": 1},
        previous_state=None,
    )
    assert state.previous_state is None


def test_undo_parity_with_previous():
    """undo restores previous into current and clears previous."""

    base = anchor.AnchorRuntimeState(
        active_profile={"name": "p", "anchor": {}},
        anchor_state={"a": 1},
        current_state={"c": 9},
        previous_state={"c": 0},
    )
    # Monolith: restore_state = previous_state.copy(); current = restore_state.copy();
    # previous_state = None
    state = anchor.undo(base)
    assert dict(state.current_state) == {"c": 0}
    assert state.previous_state is None
    assert dict(state.anchor_state) == {"a": 1}


def test_undo_no_previous_is_noop():
    """undo with no previous state returns the state unchanged (monolith early return)."""

    base = anchor.AnchorRuntimeState(current_state={"c": 1})
    assert anchor.undo(base) is base


def test_commit_current_as_anchor_parity():
    """commit_current_as_anchor copies current into anchor."""

    base = anchor.AnchorRuntimeState(
        active_profile={"name": "p", "anchor": {}},
        anchor_state={"a": 1},
        current_state={"c": 9},
    )
    state = anchor.commit_current_as_anchor(base)
    assert dict(state.anchor_state) == {"c": 9}
    assert dict(state.current_state) == {"c": 9}


def test_commit_current_as_anchor_no_current_is_noop():
    """commit with no current state returns the state unchanged (monolith early return)."""

    base = anchor.AnchorRuntimeState(anchor_state={"a": 1})
    assert anchor.commit_current_as_anchor(base) is base


# ---------------------------------------------------------------------------
# Group domain: parity with load_group_anchors / mutate_group_pad.
# ---------------------------------------------------------------------------


def test_set_group_anchor_current_previous():
    """The three per-pad setters each write one dict and leave the rest intact."""

    g0 = group.initial_group_runtime_state()
    g1 = group.set_group_anchor(g0, 1, {"a": 1})
    g2 = group.set_group_current(g1, 1, {"c": 2})
    g3 = group.set_group_previous(g2, 1, {"p": 3})
    assert dict(g3.group_anchor_states[1]) == {"a": 1}
    assert dict(g3.group_current_states[1]) == {"c": 2}
    assert dict(g3.group_previous_states[1]) == {"p": 3}
    # Earlier objects untouched.
    assert dict(g0.group_anchor_states) == {}
    assert dict(g1.group_current_states) == {}


def test_record_group_mutation_with_previous():
    """record_group_mutation sets current and previous when previous is truthy."""

    g = group.record_group_mutation(
        group.initial_group_runtime_state(),
        2,
        current_state={"c": 1},
        previous_state={"p": 0},
    )
    assert dict(g.group_current_states[2]) == {"c": 1}
    assert dict(g.group_previous_states[2]) == {"p": 0}


def test_record_group_mutation_without_previous():
    """record_group_mutation skips previous when it is falsy (monolith `if previous_state`)."""

    for falsy in (None, {}):
        g = group.record_group_mutation(
            group.initial_group_runtime_state(),
            3,
            current_state={"c": 1},
            previous_state=falsy,
        )
        assert dict(g.group_current_states[3]) == {"c": 1}
        assert 3 not in g.group_previous_states


def test_group_loaded_gate_parity():
    """`loaded` becomes True only when all four pads have current state."""

    g = group.initial_group_runtime_state()
    assert g.loaded is False
    for pad in (1, 2, 3):
        g = group.set_group_current(g, pad, {"c": pad})
        assert g.loaded is False
    g = group.set_group_current(g, 4, {"c": 4})
    assert g.loaded is True


# ---------------------------------------------------------------------------
# Selection domain: parity with choose_target_pad / choose_isolated_pad.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pad", [1, 2, 3, 4])
def test_select_target_pad_parity(pad):
    """select_target_pad sets target_pad and channel = pad - 1 (monolith move)."""

    state = selection.select_target_pad(selection.initial_selection_state(), pad)
    assert state.target_pad == pad
    assert state.channel == pad - 1
    assert state.isolated_pad == selection.DEFAULT_ISOLATED_PAD


def test_select_target_pad_keeps_isolated():
    """Changing the target pad does not disturb the isolated pad."""

    base = selection.select_isolated_pad(selection.initial_selection_state(), 2)
    state = selection.select_target_pad(base, 4)
    assert state.isolated_pad == 2


@pytest.mark.parametrize("pad", [1, 2, 3, 4])
def test_select_isolated_pad_parity(pad):
    """select_isolated_pad sets isolated_pad and leaves target_pad/channel intact."""

    base = selection.select_target_pad(selection.initial_selection_state(), 2)
    state = selection.select_isolated_pad(base, pad)
    assert state.isolated_pad == pad
    assert state.target_pad == 2
    assert state.channel == 1


# ---------------------------------------------------------------------------
# Pad-mode domain: parity with load_pad2_profile and Pad 3 / Pad 4 discovery.
# ---------------------------------------------------------------------------


def test_set_pad2_profile_key_parity():
    """set_pad2_profile_key reassigns only the Pad 2 key."""

    state = pad_mode.set_pad2_profile_key(pad_mode.initial_pad_mode_state(), "9")
    assert state.pad2_current_profile_key == "9"
    assert state.pad3_current_mode_key == "anchor"
    assert state.pad4_current_mode_key == "anchor"


def test_set_pad3_mode_key_parity():
    """set_pad3_mode_key reassigns only the Pad 3 key (e.g. SY Raw wave mode)."""

    state = pad_mode.set_pad3_mode_key(pad_mode.initial_pad_mode_state(), "wave")
    assert state.pad3_current_mode_key == "wave"
    assert state.pad2_current_profile_key == "3"
    assert state.pad4_current_mode_key == "anchor"


def test_set_pad4_mode_key_parity():
    """set_pad4_mode_key reassigns only the Pad 4 key."""

    state = pad_mode.set_pad4_mode_key(pad_mode.initial_pad_mode_state(), "body")
    assert state.pad4_current_mode_key == "body"
    assert state.pad2_current_profile_key == "3"
    assert state.pad3_current_mode_key == "anchor"


def test_reset_pad3_to_anchor_parity():
    """reset_pad3_to_anchor restores 'anchor' (monolith return_pad3_sy_raw_to_anchor)."""

    base = pad_mode.set_pad3_mode_key(pad_mode.initial_pad_mode_state(), "wave")
    state = pad_mode.reset_pad3_to_anchor(base)
    assert state.pad3_current_mode_key == "anchor"


def test_reset_pad4_to_anchor_parity():
    """reset_pad4_to_anchor restores 'anchor' (monolith Pad 4 return)."""

    base = pad_mode.set_pad4_mode_key(pad_mode.initial_pad_mode_state(), "accent")
    state = pad_mode.reset_pad4_to_anchor(base)
    assert state.pad4_current_mode_key == "anchor"


# ---------------------------------------------------------------------------
# Scene domain: parity with run_scene.
# ---------------------------------------------------------------------------


def test_set_scene_name_parity():
    """set_scene_name replaces current_scene_name (monolith run_scene move)."""

    state = scene.set_scene_name(scene.initial_scene_state(), "Home Base")
    assert state.current_scene_name == "Home Base"


def test_set_scene_name_coerces_to_str():
    """set_scene_name coerces non-str scene names to str."""

    state = scene.set_scene_name(scene.initial_scene_state(), 123)
    assert state.current_scene_name == "123"


def test_scene_transition_chain():
    """Repeated scene transitions each replace the prior name."""

    s = scene.initial_scene_state()
    s = scene.set_scene_name(s, "A")
    s = scene.set_scene_name(s, "B")
    assert s.current_scene_name == "B"
