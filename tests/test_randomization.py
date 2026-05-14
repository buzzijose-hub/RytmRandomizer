"""Characterization + parity tests for the randomization core.

These tests lock in the monolith's CURRENT behavior, then prove the extracted
``rytm_randomizer.randomization`` module reproduces it byte-identically. All
randomness is made deterministic via injected ``random.Random`` instances.

Isolation rules match ``tests/test_data_layer.py`` / ``tests/test_midi_io.py``:

* Anything that imports the monolith (which does ``import mido`` at the top)
  runs in a *subprocess* so real ``mido`` never lands in this process's
  ``sys.modules``.
* In-process package tests that reach ``send_param`` (and therefore
  ``mido``) inject a *fake* ``mido``; an autouse fixture snapshots and
  restores ``sys.modules`` so nothing leaks between tests.
"""

from __future__ import annotations

import json
import random
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
    def __init__(self, message_type, *, channel, control, value):
        self.type = message_type
        self.channel = channel
        self.control = control
        self.value = value


def _install_fake_mido():
    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    return fake


class RecordingOut:
    def __init__(self) -> None:
        self.sent: list[object] = []

    def send(self, message: object) -> None:
        self.sent.append(message)


def _no_sleep(_seconds: float) -> None:
    return None


def _run_python(code: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _sample_profile(key: str = "2") -> dict:
    from rytm_randomizer.data import PROFILES

    profile = dict(PROFILES[key])
    profile["anchor"] = dict(profile["anchor"])
    return profile


# Shared subprocess preamble: defines Out, silences sleep, and exposes a
# `drive(...)` helper. The `PROFILE_SETUP` placeholder is filled per-test.
_PREAMBLE = (
    "import json, io, contextlib, random\n"
    "import rytm_hybrid_randomizer_v134 as m\n"
    "from rytm_randomizer import midi_io, randomization\n"
    "midi_io.time.sleep = lambda *_: None\n"
    "randomization.time.sleep = lambda *_: None\n"
    "from rytm_randomizer.data import PROFILES\n"
    "class Out:\n"
    "    def __init__(self): self.sent = []\n"
    "    def send(self, msg): self.sent.append(msg)\n"
)


# ===========================================================================
# get_depth
# ===========================================================================

def test_get_depth_parity_all_branches():
    """Subprocess parity across every depth-input branch."""

    code = (
        "import rytm_hybrid_randomizer_v134 as m\n"
        "from rytm_randomizer import randomization\n"
        "import io, contextlib, builtins\n"
        "cases = {'1':'micro','2':'groove','3':'strong','x':'groove','':'groove'}\n"
        "ok = True\n"
        "for raw, expected in cases.items():\n"
        "    builtins.input = lambda _p='', _r=raw: _r\n"
        "    buf_a = io.StringIO()\n"
        "    with contextlib.redirect_stdout(buf_a):\n"
        "        ra = m.get_depth()\n"
        "    buf_b = io.StringIO()\n"
        "    with contextlib.redirect_stdout(buf_b):\n"
        "        rb = randomization.get_depth()\n"
        "    assert ra == rb == expected, (raw, ra, rb)\n"
        "    assert buf_a.getvalue() == buf_b.getvalue()\n"
        "print('OK')\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def test_get_depth_in_process_branches(capsys):
    """In-process branch coverage of get_depth via injected prompt_func."""
    from rytm_randomizer.randomization import get_depth

    assert get_depth(prompt_func=lambda _p: "1") == "micro"
    assert get_depth(prompt_func=lambda _p: "2") == "groove"
    assert get_depth(prompt_func=lambda _p: "3") == "strong"
    assert get_depth(prompt_func=lambda _p: "x") == "groove"
    output = capsys.readouterr().out
    assert "Invalid depth. Using groove." in output


def test_get_depth_default_uses_builtin_input(monkeypatch):
    """With no prompt_func, get_depth resolves builtins.input lazily."""
    import builtins

    from rytm_randomizer.randomization import get_depth

    monkeypatch.setattr(builtins, "input", lambda _p="": "2")
    assert get_depth() == "groove"


# ===========================================================================
# random_value_around_anchor -- subprocess parity (monolith) + in-process
# coverage (package only; pure, no mido).
# ===========================================================================

def _rvaa_parity(profile_repr, anchor_repr, name, depth, seeds):
    code = (
        _PREAMBLE
        + f"profile = {profile_repr}\n"
        + f"anchor = {anchor_repr}\n"
        + f"for seed in {seeds!r}:\n"
        "    m.active_profile = profile\n"
        "    m.anchor_state = dict(anchor)\n"
        "    m.random = random.Random(seed)\n"
        f"    mono = m.random_value_around_anchor({name!r}, {depth!r})\n"
        f"    pkg = randomization.random_value_around_anchor({name!r}, {depth!r},"
        "        profile=profile, anchor_state=dict(anchor),"
        "        rng=random.Random(seed))\n"
        "    assert mono == pkg, (seed, mono, pkg)\n"
        "print('OK')\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def test_random_value_around_anchor_parity_normal_branch():
    profile = _sample_profile()
    _rvaa_parity(
        "dict(PROFILES['2'], anchor=dict(PROFILES['2']['anchor']))",
        repr(dict(profile["anchor"])),
        "FLT Frequency",
        "groove",
        list(range(20)),
    )


def test_random_value_around_anchor_parity_tick_branch():
    """Profile 1 (BD Sharp) carries SRC Tick Level; drive the downward-only
    transient branch with a maxed anchor."""
    profile = _sample_profile("1")
    assert "SRC Tick Level" in profile["safe"]
    anchor = dict(profile["anchor"])
    anchor["SRC Tick Level"] = 120
    _rvaa_parity(
        "dict(PROFILES['1'], anchor=dict(PROFILES['1']['anchor']))",
        repr(anchor),
        "SRC Tick Level",
        "groove",
        list(range(15)),
    )


def test_random_value_around_anchor_parity_src_impact_branch():
    """Profile 4 (BD Acoustic) carries SRC Impact; drive the transient branch."""
    profile = _sample_profile("4")
    assert "SRC Impact" in profile["safe"]
    anchor = dict(profile["anchor"])
    anchor["SRC Impact"] = 115
    _rvaa_parity(
        "dict(PROFILES['4'], anchor=dict(PROFILES['4']['anchor']))",
        repr(anchor),
        "SRC Impact",
        "groove",
        list(range(15)),
    )


def test_random_value_around_anchor_parity_amp_hold_branch():
    """Profile 1 (BD Sharp) carries AMP Hold; drive the upward-only branch."""
    profile = _sample_profile("1")
    assert "AMP Hold" in profile["safe"]
    anchor = dict(profile["anchor"])
    anchor["AMP Hold"] = 0
    _rvaa_parity(
        "dict(PROFILES['1'], anchor=dict(PROFILES['1']['anchor']))",
        repr(anchor),
        "AMP Hold",
        "groove",
        list(range(15)),
    )


def test_random_value_around_anchor_parity_swap_branch():
    """A negative delta forces ``low > high`` -> the defensive swap path."""
    profile = {"safe": {"P": (0, 100)}, "deltas": {"groove": {"P": -10}}}
    anchor = {"P": 50}
    _rvaa_parity(repr(profile), repr(anchor), "P", "groove", list(range(8)))


def test_random_value_around_anchor_in_process_all_branches():
    """In-process branch coverage of every special-case branch (no mido)."""
    from rytm_randomizer.randomization import random_value_around_anchor

    # normal branch
    profile = {"safe": {"P": (0, 100)}, "deltas": {"groove": {"P": 5}}}
    val = random_value_around_anchor(
        "P", "groove", profile=profile, anchor_state={"P": 50},
        rng=random.Random(1),
    )
    assert 45 <= val <= 55

    # transient downward-only branch
    tick_profile = {
        "safe": {"SRC Tick Level": (0, 127)},
        "deltas": {"groove": {"SRC Tick Level": 10}},
    }
    tval = random_value_around_anchor(
        "SRC Tick Level", "groove", profile=tick_profile,
        anchor_state={"SRC Tick Level": 120}, rng=random.Random(2),
    )
    assert 110 <= tval <= 120

    # AMP Hold upward-only branch
    amp_profile = {
        "safe": {"AMP Hold": (0, 127)},
        "deltas": {"groove": {"AMP Hold": 8}},
    }
    aval = random_value_around_anchor(
        "AMP Hold", "groove", profile=amp_profile,
        anchor_state={"AMP Hold": 0}, rng=random.Random(3),
    )
    assert 0 <= aval <= 8

    # swap branch (negative delta)
    swap_profile = {"safe": {"P": (0, 100)}, "deltas": {"groove": {"P": -10}}}
    sval = random_value_around_anchor(
        "P", "groove", profile=swap_profile, anchor_state={"P": 50},
        rng=random.Random(4),
    )
    assert 40 <= sval <= 60

    # default RNG path (rng=None)
    dval = random_value_around_anchor(
        "P", "groove", profile=profile, anchor_state={"P": 50},
    )
    assert 45 <= dval <= 55


# ===========================================================================
# random_hp2_filter_pair -- subprocess parity + in-process coverage
# ===========================================================================

def _hp2_parity(profile_repr, anchor_repr, depth, seeds):
    code = (
        _PREAMBLE
        + f"profile = {profile_repr}\n"
        + f"anchor = {anchor_repr}\n"
        + f"for seed in {seeds!r}:\n"
        "    m.active_profile = profile\n"
        "    m.anchor_state = dict(anchor)\n"
        "    m.random = random.Random(seed)\n"
        f"    mono = m.random_hp2_filter_pair({depth!r})\n"
        f"    pkg = randomization.random_hp2_filter_pair({depth!r},"
        "        profile=profile, anchor_state=dict(anchor),"
        "        rng=random.Random(seed))\n"
        "    assert mono == pkg, (seed, mono, pkg)\n"
        "print('OK')\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"


def _hp2_profile_repr(filter_mode, freq_safe, res_safe, freq_delta=50, res_delta=50):
    return repr(
        {
            "filter_mode": filter_mode,
            "safe": {"FLT Frequency": freq_safe, "FLT Resonance": res_safe},
            "deltas": {
                "groove": {
                    "FLT Frequency": freq_delta,
                    "FLT Resonance": res_delta,
                }
            },
        }
    )


def test_random_hp2_filter_pair_parity_every_mode_and_subrange():
    """Cover every ``filter_mode`` AND every ``freq <= N`` sub-branch."""
    mode_freq_ranges = {
        "sharp": [(20, 25), (28, 30), (33, 40)],
        "hard": [(20, 26), (29, 31), (34, 40)],
        "classic": [(20, 25), (28, 30), (33, 40)],
        "fm": [(20, 26), (30, 32), (35, 40)],
        "acoustic": [(20, 25), (28, 30), (33, 40)],
    }
    for mode, ranges in mode_freq_ranges.items():
        for freq_safe in ranges:
            profile_repr = _hp2_profile_repr(mode, freq_safe, (0, 100))
            anchor = {
                "FLT Frequency": (freq_safe[0] + freq_safe[1]) // 2,
                "FLT Resonance": 50,
            }
            _hp2_parity(profile_repr, repr(anchor), "groove", list(range(10)))


def test_random_hp2_filter_pair_parity_freq_swap_branch():
    """Negative freq delta forces ``freq_low > freq_high`` -> swap path."""
    profile_repr = _hp2_profile_repr("hard", (0, 100), (0, 100), freq_delta=-10)
    anchor = {"FLT Frequency": 30, "FLT Resonance": 50}
    _hp2_parity(profile_repr, repr(anchor), "groove", list(range(8)))


def test_random_hp2_filter_pair_parity_res_fallback_branch():
    """An empty intersected resonance band falls back to the safe limits."""
    profile_repr = _hp2_profile_repr("classic", (0, 10), (0, 5), res_delta=1)
    anchor = {"FLT Frequency": 5, "FLT Resonance": 2}
    _hp2_parity(profile_repr, repr(anchor), "groove", list(range(8)))


def test_random_hp2_filter_pair_parity_real_profile_micro_strong():
    profile = _sample_profile("2")
    for depth in ("micro", "strong"):
        _hp2_parity(
            "dict(PROFILES['2'], anchor=dict(PROFILES['2']['anchor']))",
            repr(dict(profile["anchor"])),
            depth,
            list(range(20)),
        )


def test_random_hp2_filter_pair_in_process_all_branches():
    """In-process branch coverage: every filter mode, sub-range, swap and
    fallback path (pure, no mido)."""
    from rytm_randomizer.randomization import random_hp2_filter_pair

    def hp2_profile(mode, freq_safe, res_safe, fd=50, rd=50):
        return {
            "filter_mode": mode,
            "safe": {"FLT Frequency": freq_safe, "FLT Resonance": res_safe},
            "deltas": {"groove": {"FLT Frequency": fd, "FLT Resonance": rd}},
        }

    mode_ranges = {
        "sharp": [(20, 25), (28, 30), (33, 40)],
        "hard": [(20, 26), (29, 31), (34, 40)],
        "classic": [(20, 25), (28, 30), (33, 40)],
        "fm": [(20, 26), (30, 32), (35, 40)],
        "acoustic": [(20, 25), (28, 30), (33, 40)],
    }
    for mode, ranges in mode_ranges.items():
        for freq_safe in ranges:
            profile = hp2_profile(mode, freq_safe, (0, 100))
            anchor = {
                "FLT Frequency": (freq_safe[0] + freq_safe[1]) // 2,
                "FLT Resonance": 50,
            }
            for seed in range(6):
                freq, res = random_hp2_filter_pair(
                    "groove", profile=profile, anchor_state=anchor,
                    rng=random.Random(seed),
                )
                assert freq_safe[0] <= freq <= freq_safe[1]
                assert 0 <= res <= 100

    # freq swap branch
    swap_profile = hp2_profile("hard", (0, 100), (0, 100), fd=-10)
    random_hp2_filter_pair(
        "groove", profile=swap_profile,
        anchor_state={"FLT Frequency": 30, "FLT Resonance": 50},
        rng=random.Random(1),
    )

    # resonance fallback branch
    fallback_profile = hp2_profile("classic", (0, 10), (0, 5), rd=1)
    _, res = random_hp2_filter_pair(
        "groove", profile=fallback_profile,
        anchor_state={"FLT Frequency": 5, "FLT Resonance": 2},
        rng=random.Random(1),
    )
    assert 0 <= res <= 5

    # default RNG path (rng=None)
    random_hp2_filter_pair(
        "groove", profile=hp2_profile("hard", (20, 26), (0, 100)),
        anchor_state={"FLT Frequency": 23, "FLT Resonance": 50},
    )


# ===========================================================================
# random_waveform -- subprocess parity + in-process coverage
# ===========================================================================

def _drive_monolith_random_waveform(profile_key, current_repr, seed):
    code = (
        _PREAMBLE
        + f"profile = dict(PROFILES[{profile_key!r}], "
        f"anchor=dict(PROFILES[{profile_key!r}]['anchor']))\n"
        "m.active_profile = profile\n"
        "m.anchor_state = dict(profile['anchor'])\n"
        f"m.current_state = {current_repr}\n"
        "m.previous_state = None\n"
        f"m.random = random.Random({seed})\n"
        "out = Out(); buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        "    m.random_waveform(out)\n"
        "print(json.dumps({\n"
        "    'output': buf.getvalue(),\n"
        "    'sent': [(x.control, x.value) for x in out.sent],\n"
        "    'current_state': m.current_state,\n"
        "    'previous_state': m.previous_state,\n"
        "}))\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_random_waveform_parity_seeded_current(capsys):
    _install_fake_mido()
    from rytm_randomizer.randomization import random_waveform

    profile = _sample_profile()
    seeded = {"SRC Waveform": 1}

    for seed in range(8):
        mono = _drive_monolith_random_waveform("2", repr(dict(seeded)), seed)

        pkg_out = RecordingOut()
        result = random_waveform(
            pkg_out,
            profile=profile,
            anchor_state=dict(profile["anchor"]),
            current_state=dict(seeded),
            previous_state=None,
            channel=0,
            sleep=_no_sleep,
            rng=random.Random(seed),
        )
        pkg_output = capsys.readouterr().out

        assert pkg_output == mono["output"]
        assert result.applied is True
        assert [(m.control, m.value) for m in pkg_out.sent] == [
            tuple(p) for p in mono["sent"]
        ]
        assert result.current_state == mono["current_state"]
        assert result.previous_state == mono["previous_state"]


def test_random_waveform_parity_empty_current(capsys):
    """When current_state is empty it is seeded from anchor_state."""
    _install_fake_mido()
    from rytm_randomizer.randomization import random_waveform

    profile = _sample_profile()

    mono = _drive_monolith_random_waveform("2", "{}", 5)

    pkg_out = RecordingOut()
    result = random_waveform(
        pkg_out,
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(5),
    )
    pkg_output = capsys.readouterr().out

    assert pkg_output == mono["output"]
    assert [(m.control, m.value) for m in pkg_out.sent] == [
        tuple(p) for p in mono["sent"]
    ]
    assert result.current_state == mono["current_state"]
    assert result.previous_state == mono["previous_state"]


def test_random_waveform_without_profile(capsys):
    from rytm_randomizer.randomization import random_waveform

    pkg_out = RecordingOut()
    result = random_waveform(
        pkg_out,
        profile=None,
        anchor_state={},
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(1),
    )
    output = capsys.readouterr().out

    assert result.applied is False
    assert pkg_out.sent == []
    assert "Select a profile first with P." in output


def test_random_waveform_default_rng(capsys):
    """Cover the rng=None default-RNG path."""
    _install_fake_mido()
    from rytm_randomizer.randomization import random_waveform

    profile = _sample_profile()
    pkg_out = RecordingOut()
    result = random_waveform(
        pkg_out,
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={"SRC Waveform": 0},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
    )
    capsys.readouterr()
    low, high = profile["waveform_range"]
    assert low <= result.current_state["SRC Waveform"] <= high


# ===========================================================================
# mutate_zone -- subprocess parity + in-process coverage
# ===========================================================================

def _drive_monolith_mutate_zone(profile_repr, current_repr, zone, depth, seed):
    code = (
        _PREAMBLE
        + f"profile = {profile_repr}\n"
        "m.active_profile = profile\n"
        "m.anchor_state = dict(profile['anchor'])\n"
        f"m.current_state = {current_repr}\n"
        "m.previous_state = None\n"
        f"m.random = random.Random({seed})\n"
        "out = Out(); buf = io.StringIO()\n"
        "with contextlib.redirect_stdout(buf):\n"
        f"    m.mutate_zone(out, {zone!r}, {depth!r})\n"
        "print(json.dumps({\n"
        "    'output': buf.getvalue(),\n"
        "    'sent': [(x.control, x.value) for x in out.sent],\n"
        "    'current_state': m.current_state,\n"
        "    'previous_state': m.previous_state,\n"
        "}))\n"
    )
    result = _run_python(code)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


_REAL_PROFILE_2 = "dict(PROFILES['2'], anchor=dict(PROFILES['2']['anchor']))"


def test_mutate_zone_parity_filter_zone(capsys):
    """Filter zone exercises the FLT Frequency/Resonance pair path."""
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    for seed in range(8):
        mono = _drive_monolith_mutate_zone(
            _REAL_PROFILE_2, "{}", "filter", "groove", seed
        )

        pkg_out = RecordingOut()
        result = mutate_zone(
            pkg_out,
            "filter",
            "groove",
            profile=profile,
            anchor_state=dict(profile["anchor"]),
            current_state={},
            previous_state=None,
            channel=0,
            sleep=_no_sleep,
            rng=random.Random(seed),
        )
        pkg_output = capsys.readouterr().out

        assert pkg_output == mono["output"]
        assert [(m.control, m.value) for m in pkg_out.sent] == [
            tuple(p) for p in mono["sent"]
        ]
        assert result.applied is True
        assert result.current_state == mono["current_state"]
        assert result.previous_state == mono["previous_state"]


def test_mutate_zone_parity_full_zone_seeded_current(capsys):
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    seeded = dict(profile["anchor"])

    for seed in range(6):
        mono = _drive_monolith_mutate_zone(
            _REAL_PROFILE_2, repr(dict(seeded)), "full", "strong", seed
        )

        pkg_out = RecordingOut()
        result = mutate_zone(
            pkg_out,
            "full",
            "strong",
            profile=profile,
            anchor_state=dict(profile["anchor"]),
            current_state=dict(seeded),
            previous_state=None,
            channel=0,
            sleep=_no_sleep,
            rng=random.Random(seed),
        )
        pkg_output = capsys.readouterr().out

        assert pkg_output == mono["output"]
        assert [(m.control, m.value) for m in pkg_out.sent] == [
            tuple(p) for p in mono["sent"]
        ]
        assert result.current_state == mono["current_state"]
        assert result.previous_state == mono["previous_state"]


def test_mutate_zone_parity_src_zone(capsys):
    """A non-filter zone covers the plain random_value_around_anchor path."""
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    for seed in range(6):
        mono = _drive_monolith_mutate_zone(
            _REAL_PROFILE_2, "{}", "src", "micro", seed
        )

        pkg_out = RecordingOut()
        result = mutate_zone(
            pkg_out,
            "src",
            "micro",
            profile=profile,
            anchor_state=dict(profile["anchor"]),
            current_state={},
            previous_state=None,
            channel=0,
            sleep=_no_sleep,
            rng=random.Random(seed),
        )
        pkg_output = capsys.readouterr().out

        assert pkg_output == mono["output"]
        assert [(m.control, m.value) for m in pkg_out.sent] == [
            tuple(p) for p in mono["sent"]
        ]
        assert result.current_state == mono["current_state"]


def test_mutate_zone_parity_skips_param_absent_from_depth_deltas(capsys):
    """A zone param missing from ``deltas[depth]`` is skipped (continue path)."""
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = {
        "name": "Hand Built",
        "params": {"P_IN": 10, "P_OUT": 11},
        "zones": {"z": ["P_IN", "P_OUT"]},
        # P_OUT deliberately absent from the groove deltas -> skipped.
        "deltas": {"groove": {"P_IN": 4}},
        "safe": {"P_IN": (0, 100)},
    }
    profile["anchor"] = {"P_IN": 50, "P_OUT": 60}

    mono = _drive_monolith_mutate_zone(repr(profile), "{}", "z", "groove", 9)

    pkg_out = RecordingOut()
    result = mutate_zone(
        pkg_out,
        "z",
        "groove",
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(9),
    )
    pkg_output = capsys.readouterr().out

    assert pkg_output == mono["output"]
    assert [(m.control, m.value) for m in pkg_out.sent] == [
        tuple(p) for p in mono["sent"]
    ]
    # Only P_IN (cc 10) was sent; P_OUT was skipped.
    assert all(m.control == 10 for m in pkg_out.sent)
    assert result.current_state == mono["current_state"]


def test_mutate_zone_resonance_after_pair_is_skipped(capsys):
    """Once the FLT pair is handled, a standalone FLT Resonance is skipped."""
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    pkg_out = RecordingOut()
    result = mutate_zone(
        pkg_out,
        "filter",
        "groove",
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(0),
    )
    capsys.readouterr()

    res_cc = profile["params"]["FLT Resonance"]
    sent_res = [m for m in pkg_out.sent if m.control == res_cc]
    assert len(sent_res) == 1
    assert result.applied is True


def test_mutate_zone_without_profile(capsys):
    from rytm_randomizer.randomization import mutate_zone

    pkg_out = RecordingOut()
    result = mutate_zone(
        pkg_out,
        "full",
        "groove",
        profile=None,
        anchor_state={},
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(1),
    )
    output = capsys.readouterr().out

    assert result.applied is False
    assert pkg_out.sent == []
    assert "Select a profile first with P." in output


def test_mutate_zone_default_rng(capsys):
    """Cover the rng=None default-RNG path for mutate_zone."""
    _install_fake_mido()
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    pkg_out = RecordingOut()
    result = mutate_zone(
        pkg_out,
        "src",
        "micro",
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state={},
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
    )
    capsys.readouterr()
    assert result.applied is True


# ===========================================================================
# import safety
# ===========================================================================

def test_importing_randomization_prints_nothing():
    result = _run_python("import rytm_randomizer.randomization")

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_importing_randomization_does_not_import_mido():
    result = _run_python(
        "import sys\n"
        "import rytm_randomizer.randomization\n"
        "assert 'mido' not in sys.modules\n"
        "assert 'rtmidi' not in sys.modules\n"
        "print('OK')\n"
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"
