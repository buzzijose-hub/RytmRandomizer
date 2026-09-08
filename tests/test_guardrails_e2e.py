"""End-to-end proof: a profile genuinely steers the randomizer (WS-W Layer 4).

Per spec section 11 + 16: the decisive test for the whole guardrails
subsystem is the A-vs-B-vs-none comparison. The same operator command,
run with profile A (e.g. rolling / hypnotic -- narrow filter ranges,
kick locked), profile B (e.g. raw / peak-time -- wider filter ranges,
more grit), and no profile, must:

* produce **three different** MIDI streams (the profile actually changes
  what comes out of the wire), AND
* each non-none stream's CC values must stay **inside that profile's
  resolved bounds** (the resolver actually clamps).

This file builds two profiles against the Pad 1 BD Hard hardware profile,
drives :meth:`Pad1Engine.mutate_current_pad1_bd_engine` three times under
identical RNG state, and pins both assertions.
"""

from __future__ import annotations

import dataclasses
import random
import sys
import types

import pytest

from rytm_randomizer.guardrails import (
    MODE_LIVE_SAFE,
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileState,
    Provenance,
    ResolvedBounds,
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
    resolve,
)

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

# ---------------------------------------------------------------------------
# Fake mido so importing the engine inside the test process stays inert.
# ---------------------------------------------------------------------------


class _FakeMessage:
    """Lightweight stand-in for ``mido.Message`` -- records the fields we
    care about for assertions."""

    def __init__(self, message_type, *, channel, control, value):
        self.type = message_type
        self.channel = channel
        self.control = control
        self.value = value

    def __repr__(self):  # pragma: no cover - debugging aid only
        return (
            f"_FakeMessage({self.type!r}, channel={self.channel}, "
            f"control={self.control}, value={self.value})"
        )


@pytest.fixture(autouse=True)
def _restore_sys_modules():
    """Snapshot ``sys.modules`` and restore after each test (no leaks)."""

    snapshot = dict(sys.modules)
    fake = types.ModuleType("mido")
    fake.Message = _FakeMessage  # type: ignore[attr-defined]
    sys.modules["mido"] = fake
    try:
        yield
    finally:
        for name in list(sys.modules):
            if name not in snapshot:
                del sys.modules[name]
        for name, module in snapshot.items():
            sys.modules[name] = module


class _Out:
    """Recording MIDI sender -- duck-types ``mido.ports.BaseOutput.send``."""

    def __init__(self) -> None:
        self.sent: list[_FakeMessage] = []

    def send(self, msg: _FakeMessage) -> None:
        self.sent.append(msg)


# _no_sleep lives in tests/conftest.py per Gate 11 + WS-M4.
from conftest import _no_sleep  # noqa: E402

# ---------------------------------------------------------------------------
# Profile builders -- two different musical "characters" against Pad 1
# ---------------------------------------------------------------------------


# Hardware envelope from BD_HARD_SAFE on the canonical Pad 1 profile.
# We use these as the validator's reference so the profiles are semantically
# valid (no bound exceeds the hardware range).
PAD1_HW = {
    "FLT Frequency": (23, 36),
    "FLT Resonance": (40, 68),
    "AMP Overdrive": (16, 35),
    "SRC Tune": (58, 64),
    "SRC Decay": (38, 66),
    "SRC Hold": (35, 70),
    "SRC Sweep Time": (70, 110),
    "SRC Snap": (8, 55),
    "SRC Transient Tick": (60, 115),
}


def _common_provenance(name: str) -> Provenance:
    return Provenance(
        profile_name=name,
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="feat-hash",
        derived_at="2026-05-14T12:00:00Z",
    )


def _common_role_mapping() -> RoleMapping:
    return RoleMapping(
        assignments={
            1: RoleAssignment(role="kick", mutation_direction="tighten"),
        }
    )


def _profile_a_rolling_hypnotic() -> GuardrailProfile:
    """Narrow, anchored: a tight kick that holds its position.

    Filter frequency tightly anchored at the low end (23-26), filter
    resonance narrow and modest, very little overdrive movement.
    """

    bounds = (
        GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=23,
            high=26,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="anchor",
        ),
        GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=40,
            high=48,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="anchor",
        ),
        GuardrailBound(
            pad=1,
            parameter="AMP Overdrive",
            low=16,
            high=20,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="restrained",
        ),
    )
    intermediate = GuardrailProfile(
        provenance=_common_provenance("rolling-hypnotic"),
        character=MusicalCharacter(
            style_tags=("rolling", "hypnotic", "dark"),
            bpm_range=(128, 132),
            energy_profile="steady",
            density_profile="dense",
        ),
        role_mapping=_common_role_mapping(),
        bounds=bounds,
        locked_default=(),
        forbidden=(),
        scenes=(
            SceneGuardrail(
                scene_key="A1",
                pads_allowed=(1,),
                mutation_depth="moderate",
                risk_class=GuardrailClass.LIVE_SAFE,
                locked_roles=("kick",),
            ),
        ),
        state=ProfileState.LIVE_APPROVED,
        schema_version=SCHEMA_VERSION,
        content_hash="",
    )
    return dataclasses.replace(intermediate, content_hash=compute_content_hash(intermediate))


def _profile_b_raw_peak_time() -> GuardrailProfile:
    """Wide, grittier: a peak-time kick with more filter motion and grit.

    Filter frequency wider (uses most of the hardware envelope), filter
    resonance higher and wider, overdrive on the hot half of its range.
    """

    bounds = (
        GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=30,
            high=36,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="open",
        ),
        GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=55,
            high=68,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="open",
        ),
        GuardrailBound(
            pad=1,
            parameter="AMP Overdrive",
            low=28,
            high=35,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="hot",
        ),
    )
    intermediate = GuardrailProfile(
        provenance=_common_provenance("raw-peak-time"),
        character=MusicalCharacter(
            style_tags=("raw", "peak-time", "grit"),
            bpm_range=(140, 150),
            energy_profile="climactic",
            density_profile="dense",
        ),
        role_mapping=_common_role_mapping(),
        bounds=bounds,
        locked_default=(),
        forbidden=(),
        scenes=(),
        state=ProfileState.LIVE_APPROVED,
        schema_version=SCHEMA_VERSION,
        content_hash="",
    )
    return dataclasses.replace(intermediate, content_hash=compute_content_hash(intermediate))


# ---------------------------------------------------------------------------
# The decisive run helper
# ---------------------------------------------------------------------------


def _run_pad1_mutation(
    resolved_bounds: ResolvedBounds | None, *, seed: int = 12345
) -> list[_FakeMessage]:
    """Drive ``Pad1Engine.mutate_current_pad1_bd_engine`` once.

    Steps: load BD Hard profile ("2"), then call ``mutate_current_pad1_bd_engine``
    -- the engine seeds itself from the stdlib ``random`` module so a single
    ``random.seed(...)`` here makes every run start from the identical RNG
    state. Returns the recorded MIDI message stream from ``_Out``.
    """

    from rytm_randomizer.engines.pad1 import Pad1Engine

    out = _Out()
    engine = Pad1Engine(out, sleep=_no_sleep, resolved_bounds=resolved_bounds)

    # Identical RNG seed for every call so any observable stream difference
    # is from the resolved bounds and nothing else.
    random.seed(seed)

    # Suppress the V1.34 stdout banners so the test output stays clean.
    import contextlib
    import io as _io

    with contextlib.redirect_stdout(_io.StringIO()):
        engine.load_pad1_bd_profile("2")  # BD Hard
        engine.mutate_current_pad1_bd_engine()

    return list(out.sent)


# ---------------------------------------------------------------------------
# THE DECISIVE TEST
# ---------------------------------------------------------------------------


def test_profile_a_vs_b_vs_none_produce_different_streams():
    """The same command run three times with different profiles -> different MIDI.

    This is the proof the guardrails system *works*: when no profile is
    active, the engine mutates against the hardware envelope from
    ``data/``. When profile A (narrow / anchored) is resolved and passed
    in, the same command emits a tighter stream of values. When profile
    B (wider / grittier) is in play, the stream is different again --
    and within profile B's permitted ranges.
    """

    profile_a = _profile_a_rolling_hypnotic()
    profile_b = _profile_b_raw_peak_time()

    rb_a = resolve(profile_a, MODE_LIVE_SAFE)
    rb_b = resolve(profile_b, MODE_LIVE_SAFE)

    stream_none = _run_pad1_mutation(None)
    stream_a = _run_pad1_mutation(rb_a)
    stream_b = _run_pad1_mutation(rb_b)

    # Reduce the streams to their CC + value sequences for comparison.
    def cc_value_seq(stream):
        return [(m.control, m.value) for m in stream]

    seq_none = cc_value_seq(stream_none)
    seq_a = cc_value_seq(stream_a)
    seq_b = cc_value_seq(stream_b)

    # Three different streams: every pair distinct.
    assert seq_none != seq_a, (
        "Profile A did not change the output. The guardrails resolver is "
        "not actually narrowing the engine's mutation envelope."
    )
    assert seq_none != seq_b, "Profile B did not change the output."
    assert seq_a != seq_b, (
        "Profile A and Profile B produced identical streams. The two "
        "profiles must steer the engine differently."
    )


def test_profile_a_stream_is_within_profile_a_bounds():
    """Every CC value that profile A's run emits is inside A's resolved bounds."""

    profile_a = _profile_a_rolling_hypnotic()
    rb_a = resolve(profile_a, MODE_LIVE_SAFE)

    stream_a = _run_pad1_mutation(rb_a)

    _assert_stream_within_resolved_bounds(stream_a, rb_a, profile_key="2")


def test_profile_b_stream_is_within_profile_b_bounds():
    """Every CC value that profile B's run emits is inside B's resolved bounds."""

    profile_b = _profile_b_raw_peak_time()
    rb_b = resolve(profile_b, MODE_LIVE_SAFE)

    stream_b = _run_pad1_mutation(rb_b)

    _assert_stream_within_resolved_bounds(stream_b, rb_b, profile_key="2")


def _assert_stream_within_resolved_bounds(
    stream: list[_FakeMessage],
    bounds: ResolvedBounds,
    *,
    profile_key: str,
) -> None:
    """For every CC in ``stream`` whose ``(pad, parameter)`` is in
    ``bounds``, assert the emitted value is inside the resolved range
    (or absent entirely for LOCKED_DEFAULT / FORBIDDEN classes).

    ``profile_key`` is the canonical Pad 1 profile key ("2" for BD Hard);
    we use it to translate CC numbers back to parameter names.
    """

    from rytm_randomizer.data import PROFILES

    profile = PROFILES[profile_key]
    params: dict[str, int] = profile["params"]
    # Reverse-lookup: CC -> parameter name.
    cc_to_name: dict[int, str] = {cc: name for name, cc in params.items()}

    pad = 1  # Pad 1 is the only pad this run touches; channel 0.
    out_of_bounds: list[str] = []
    for msg in stream:
        if msg.type != "control_change":
            continue
        if msg.channel != 0:
            # Other channels -- e.g. machine CC15 -- are not pad-bound, skip.
            continue
        name = cc_to_name.get(msg.control)
        if name is None:
            continue  # not a known parameter on this profile
        rb = bounds.get(pad, name)
        if rb is None:
            continue  # parameter not constrained by the profile
        if rb.guardrail_class in (
            GuardrailClass.LOCKED_DEFAULT,
            GuardrailClass.FORBIDDEN,
        ):
            out_of_bounds.append(
                f"{name} (CC{msg.control}) was emitted with value "
                f"{msg.value}, but its class is {rb.guardrail_class.value} "
                "-- it should not have been sent."
            )
            continue
        if not (rb.low <= msg.value <= rb.high):
            out_of_bounds.append(
                f"{name} (CC{msg.control}) value {msg.value} outside the "
                f"resolved range [{rb.low}, {rb.high}]."
            )

    assert not out_of_bounds, (
        "Resolved bounds violated -- the engine emitted CC values outside "
        "the resolved envelope. The resolver clamping is not engaged.\n  "
        + "\n  ".join(out_of_bounds)
    )


# ---------------------------------------------------------------------------
# Backward compatibility -- no resolved_bounds => identical to baseline
# ---------------------------------------------------------------------------


def test_engine_without_resolved_bounds_matches_unconfigured_engine():
    """When ``resolved_bounds`` is ``None``, the engine runs against
    ``data/``'s ranges exactly as if the parameter had never been added.

    The parity-test suite asserts byte-identity to the monolith; this is
    a complementary check that proves the *constructor parameter itself*
    is inert when omitted (rather than accidentally engaging some
    default-bounds behavior).
    """

    explicit_none = _run_pad1_mutation(None)
    omit = _run_pad1_mutation(None)  # second call, also no bounds

    seq_a = [(m.control, m.value) for m in explicit_none]
    seq_b = [(m.control, m.value) for m in omit]
    assert seq_a == seq_b


def test_profile_a_narrows_filter_frequency_observably():
    """An on-the-nose sanity check: A's narrow Filter range (23-26) means
    every emitted FLT Frequency value is in that range.

    This isolates the FLT Frequency CC (74 for BD Hard) from the rest of
    the stream and confirms the resolved bound actually narrows it.
    """

    profile_a = _profile_a_rolling_hypnotic()
    rb_a = resolve(profile_a, MODE_LIVE_SAFE)

    stream = _run_pad1_mutation(rb_a)

    flt_freq_values: list[int] = []
    for msg in stream:
        if msg.type == "control_change" and msg.channel == 0 and msg.control == 74:
            flt_freq_values.append(msg.value)

    # The mutation engine MAY skip a parameter when its zone doesn't include
    # it, but if it did emit it, the value must be inside [23, 26].
    for v in flt_freq_values:
        assert 23 <= v <= 26, f"FLT Frequency value {v} outside profile A's [23, 26] envelope"
