"""Characterization tests for the randomization core.

These tests lock in the behavior of ``rytm_randomizer.randomization``. All
randomness is made deterministic via injected ``random.Random`` instances.

The V1.34 ``rytm_hybrid_randomizer_v134`` monolith that previously served as
the live byte-for-byte reference (driven through subprocess parity checks for
each helper) has been retired; its frozen reference behavior now lives as the
captured-engine-output JSON goldens under ``tests/fixtures/v134_parity/``
(asserted by the parity test files). The in-process tests below provide
behavior coverage for every branch of the randomization helpers.

In-process package tests that reach ``send_param`` (and therefore ``mido``)
inject a *fake* ``mido``; an autouse fixture snapshots and restores
``sys.modules`` so nothing leaks between tests.
"""

from __future__ import annotations

import random
import subprocess
import sys
from pathlib import Path

import pytest

# WS-M4: shared fixture classes from tests/conftest.py
from conftest import RecordingOut, _no_sleep

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

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


# ===========================================================================
# get_depth
# ===========================================================================


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
# random_value_around_anchor -- in-process coverage (pure, no mido).
# ===========================================================================


def test_random_value_around_anchor_in_process_all_branches():
    """In-process branch coverage of every special-case branch (no mido)."""
    from rytm_randomizer.randomization import random_value_around_anchor

    # normal branch
    profile = {"safe": {"P": (0, 100)}, "deltas": {"groove": {"P": 5}}}
    val = random_value_around_anchor(
        "P",
        "groove",
        profile=profile,
        anchor_state={"P": 50},
        rng=random.Random(1),
    )
    assert 45 <= val <= 55

    # transient downward-only branch
    tick_profile = {
        "safe": {"SRC Tick Level": (0, 127)},
        "deltas": {"groove": {"SRC Tick Level": 10}},
    }
    tval = random_value_around_anchor(
        "SRC Tick Level",
        "groove",
        profile=tick_profile,
        anchor_state={"SRC Tick Level": 120},
        rng=random.Random(2),
    )
    assert 110 <= tval <= 120

    # AMP Hold upward-only branch
    amp_profile = {
        "safe": {"AMP Hold": (0, 127)},
        "deltas": {"groove": {"AMP Hold": 8}},
    }
    aval = random_value_around_anchor(
        "AMP Hold",
        "groove",
        profile=amp_profile,
        anchor_state={"AMP Hold": 0},
        rng=random.Random(3),
    )
    assert 0 <= aval <= 8

    # swap branch (negative delta)
    swap_profile = {"safe": {"P": (0, 100)}, "deltas": {"groove": {"P": -10}}}
    sval = random_value_around_anchor(
        "P",
        "groove",
        profile=swap_profile,
        anchor_state={"P": 50},
        rng=random.Random(4),
    )
    assert 40 <= sval <= 60

    # default RNG path (rng=None)
    dval = random_value_around_anchor(
        "P",
        "groove",
        profile=profile,
        anchor_state={"P": 50},
    )
    assert 45 <= dval <= 55


# ===========================================================================
# random_hp2_filter_pair -- in-process coverage
# ===========================================================================


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
                    "groove",
                    profile=profile,
                    anchor_state=anchor,
                    rng=random.Random(seed),
                )
                assert freq_safe[0] <= freq <= freq_safe[1]
                assert 0 <= res <= 100

    # freq swap branch
    swap_profile = hp2_profile("hard", (0, 100), (0, 100), fd=-10)
    random_hp2_filter_pair(
        "groove",
        profile=swap_profile,
        anchor_state={"FLT Frequency": 30, "FLT Resonance": 50},
        rng=random.Random(1),
    )

    # resonance fallback branch
    fallback_profile = hp2_profile("classic", (0, 10), (0, 5), rd=1)
    _, res = random_hp2_filter_pair(
        "groove",
        profile=fallback_profile,
        anchor_state={"FLT Frequency": 5, "FLT Resonance": 2},
        rng=random.Random(1),
    )
    assert 0 <= res <= 5

    # default RNG path (rng=None)
    random_hp2_filter_pair(
        "groove",
        profile=hp2_profile("hard", (20, 26), (0, 100)),
        anchor_state={"FLT Frequency": 23, "FLT Resonance": 50},
    )


# ===========================================================================
# random_waveform -- in-process coverage
# ===========================================================================


def test_random_waveform_seeds_current_from_anchor_when_empty(capsys, fake_mido_session):
    """When current_state is empty it is seeded from anchor_state before the
    waveform pick is recorded, exactly as the V1.34 reference behaved."""
    from rytm_randomizer.randomization import random_waveform

    profile = _sample_profile()
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
    capsys.readouterr()

    assert result.applied is True
    # The previous_state must reflect the seeded anchor (NOT a {} carry-over),
    # because the empty current_state was filled before the new value landed.
    assert "SRC Waveform" in result.previous_state
    low, high = profile["waveform_range"]
    assert low <= result.current_state["SRC Waveform"] <= high


def test_random_waveform_carries_previous_state(capsys, fake_mido_session):
    """A non-empty current_state copies into previous_state when the new
    waveform is applied."""
    from rytm_randomizer.randomization import random_waveform

    profile = _sample_profile()
    seeded = {"SRC Waveform": 1}

    pkg_out = RecordingOut()
    result = random_waveform(
        pkg_out,
        profile=profile,
        anchor_state=dict(profile["anchor"]),
        current_state=dict(seeded),
        previous_state=None,
        channel=0,
        sleep=_no_sleep,
        rng=random.Random(0),
    )
    capsys.readouterr()

    assert result.applied is True
    assert result.previous_state == seeded


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


def test_random_waveform_default_rng(capsys, fake_mido_session):
    """Cover the rng=None default-RNG path."""
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
# mutate_zone -- in-process coverage
# ===========================================================================


def test_mutate_zone_filter_zone_emits_freq_and_resonance(capsys, fake_mido_session):
    """Filter zone exercises the FLT Frequency/Resonance pair path."""
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
        rng=random.Random(1),
    )
    capsys.readouterr()

    assert result.applied is True
    sent_ccs = {m.control for m in pkg_out.sent}
    assert profile["params"]["FLT Frequency"] in sent_ccs
    assert profile["params"]["FLT Resonance"] in sent_ccs


def test_mutate_zone_full_zone_seeded_current(capsys, fake_mido_session):
    """Full-zone mutation copies the seeded current state into previous_state."""
    from rytm_randomizer.randomization import mutate_zone

    profile = _sample_profile()
    seeded = dict(profile["anchor"])

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
        rng=random.Random(0),
    )
    capsys.readouterr()

    assert result.applied is True
    assert result.previous_state == seeded


def test_mutate_zone_src_zone(capsys, fake_mido_session):
    """A non-filter zone covers the plain random_value_around_anchor path."""
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
        rng=random.Random(0),
    )
    capsys.readouterr()

    assert result.applied is True
    for name in profile["zones"]["src"]:
        if name in profile["deltas"]["micro"]:
            assert name in result.current_state


def test_mutate_zone_skips_param_absent_from_depth_deltas(capsys, fake_mido_session):
    """A zone param missing from ``deltas[depth]`` is skipped (continue path)."""
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
    capsys.readouterr()

    # Only P_IN (cc 10) was sent; P_OUT was skipped because no delta exists.
    assert all(m.control == 10 for m in pkg_out.sent)
    assert "P_IN" in result.current_state
    # P_OUT carries through from the anchor unchanged; only its CC must not have
    # been emitted (already asserted above).
    assert result.current_state["P_OUT"] == 60


def test_mutate_zone_resonance_after_pair_is_skipped(capsys, fake_mido_session):
    """Once the FLT pair is handled, a standalone FLT Resonance is skipped."""
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


def test_mutate_zone_default_rng(capsys, fake_mido_session):
    """Cover the rng=None default-RNG path for mutate_zone."""
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
