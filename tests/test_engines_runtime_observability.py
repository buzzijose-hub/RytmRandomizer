"""Targeted coverage tests for ``rytm_randomizer.engines._runtime``.

These tests exercise the WS-S9 hot-path observability hook landed in
``PadRuntimeMixin._send_param`` (lines 252-264). When the resolved
guardrail bounds clamp a value to ``None`` (i.e. the parameter is
``LOCKED_DEFAULT`` or ``FORBIDDEN``), the engine records a
``record_guardrail_block`` metric and short-circuits the CC send.

Also exercises the ``_clamp_state`` collapse-to-anchor branch (line
236-237 / 292) so a parameter pinned by the resolver flows through the
state-application path without emitting an out-of-bounds value.

Test naming: ``test_<unit>_<behavior>_when_<condition>`` per Gate 8.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path
from types import MappingProxyType

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(autouse=True)
def reset_metrics_singleton() -> Iterator[None]:
    """Reset the WS-S9 metrics singleton so tests are independent."""

    from rytm_randomizer.observability.metrics import reset_metrics

    reset_metrics()
    yield
    reset_metrics()


def _make_locked_resolved_bounds(pad: int, parameter: str):
    """Build a minimal :class:`ResolvedBounds` that LOCKs one parameter on ``pad``.

    The smallest fixture that drives ``_send_param`` into its
    ``clamped is None`` branch: one entry in the table whose
    ``guardrail_class`` is ``LOCKED_DEFAULT``.
    """

    from rytm_randomizer.guardrails.resolver import (
        GuardrailClass,
        ResolvedBound,
        ResolvedBounds,
    )

    bound = ResolvedBound(
        low=0,
        high=0,
        guardrail_class=GuardrailClass.LOCKED_DEFAULT,
    )
    table = MappingProxyType({(pad, parameter): bound})
    return ResolvedBounds(by_pad_param=table, mode="live")


def _make_unlocked_resolved_bounds(pad: int, parameter: str, low: int, high: int):
    """Build a :class:`ResolvedBounds` with one LIVE_SAFE entry, no lock."""

    from rytm_randomizer.guardrails.resolver import (
        GuardrailClass,
        ResolvedBound,
        ResolvedBounds,
    )

    bound = ResolvedBound(
        low=low,
        high=high,
        guardrail_class=GuardrailClass.LIVE_SAFE,
    )
    table = MappingProxyType({(pad, parameter): bound})
    return ResolvedBounds(by_pad_param=table, mode="live")


class _RecordingOut:
    """Minimal mido-port stand-in that captures sent messages.

    (We re-define a local recorder here because the tests construct one
    inside helper calls. ``_no_sleep`` and the canonical ``RecordingOut``
    live in ``tests/conftest.py`` per Gate 11.)
    """

    def __init__(self) -> None:
        self.sent: list[object] = []

    def send(self, message: object) -> None:
        self.sent.append(message)


# ---------------------------------------------------------------------------
# 1. _send_param: LOCKED_DEFAULT clamp -> None -> record + short-circuit
# ---------------------------------------------------------------------------


def test_send_param_locked_default_records_guardrail_block_and_skips_send(
    fake_mido_session, capsys, no_sleep
) -> None:
    """When the resolver classifies a parameter as LOCKED_DEFAULT,
    ``_send_param`` must:

    1. NOT emit any CC to the port (the V1.34-parity stdout banner stays
       silent because ``send_param`` never runs).
    2. Increment ``MidiMetrics.cc_blocked_by_guardrail_by_pad[self.target_pad]``.
    """

    from rytm_randomizer.engines.pad1 import Pad1Engine
    from rytm_randomizer.observability.metrics import get_metrics

    locked = _make_locked_resolved_bounds(pad=1, parameter="FLT Frequency")
    out = _RecordingOut()
    eng = Pad1Engine(out, sleep=no_sleep, resolved_bounds=locked)
    # Load a real profile so ``send_param`` has a CC table to resolve
    # against; the LOCKED clamp short-circuits before that lookup, so we
    # are testing the early-return contract specifically.
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()  # discard load_pad1_bd_profile's banner
    out.sent.clear()

    eng._send_param("FLT Frequency", 50)

    assert out.sent == []
    assert get_metrics().cc_blocked_by_guardrail_by_pad[1] == 1


def test_send_param_locked_parameter_records_one_block_per_call(
    fake_mido_session, capsys, no_sleep
) -> None:
    """Repeated LOCKED hits should increment the per-pad counter cumulatively."""

    from rytm_randomizer.engines.pad1 import Pad1Engine
    from rytm_randomizer.observability.metrics import get_metrics

    locked = _make_locked_resolved_bounds(pad=1, parameter="FLT Frequency")
    out = _RecordingOut()
    eng = Pad1Engine(out, sleep=no_sleep, resolved_bounds=locked)
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()
    out.sent.clear()

    eng._send_param("FLT Frequency", 50)
    eng._send_param("FLT Frequency", 99)
    eng._send_param("FLT Frequency", 0)

    assert out.sent == []
    assert get_metrics().cc_blocked_by_guardrail_by_pad[1] == 3


def test_send_param_unlocked_parameter_does_not_record_guardrail_block(
    fake_mido_session, capsys, no_sleep
) -> None:
    """A LIVE_SAFE parameter must NOT touch the guardrail-block counter."""

    from rytm_randomizer.engines.pad1 import Pad1Engine
    from rytm_randomizer.observability.metrics import get_metrics

    unlocked = _make_unlocked_resolved_bounds(pad=1, parameter="FLT Frequency", low=20, high=80)
    out = _RecordingOut()
    eng = Pad1Engine(out, sleep=no_sleep, resolved_bounds=unlocked)
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()

    eng._send_param("FLT Frequency", 50)

    assert get_metrics().cc_blocked_by_guardrail_by_pad.get(1, 0) == 0


def test_send_param_no_resolved_bounds_skips_metric_entirely(
    fake_mido_session, capsys, no_sleep
) -> None:
    """``resolved_bounds=None`` is the legacy / unconfigured path; no metric."""

    from rytm_randomizer.engines.pad1 import Pad1Engine
    from rytm_randomizer.observability.metrics import get_metrics

    out = _RecordingOut()
    eng = Pad1Engine(out, sleep=no_sleep, resolved_bounds=None)
    eng.load_pad1_bd_profile("2")
    capsys.readouterr()

    eng._send_param("FLT Frequency", 50)

    assert get_metrics().cc_blocked_by_guardrail_by_pad == {}


# ---------------------------------------------------------------------------
# 2. _clamp_state: LOCKED_DEFAULT drops the parameter from the returned dict
# ---------------------------------------------------------------------------


def test_clamp_state_drops_locked_parameter(fake_mido_session, no_sleep) -> None:
    """``_clamp_state`` returns a copy without the LOCKED key."""

    from rytm_randomizer.engines.pad1 import Pad1Engine

    locked = _make_locked_resolved_bounds(pad=1, parameter="FLT Frequency")
    eng = Pad1Engine(_RecordingOut(), sleep=no_sleep, resolved_bounds=locked)

    clamped = eng._clamp_state({"FLT Frequency": 50, "AMP Overdrive": 16})

    assert "FLT Frequency" not in clamped
    assert clamped["AMP Overdrive"] == 16


def test_clamp_state_passthrough_when_no_resolved_bounds(fake_mido_session, no_sleep) -> None:
    """``resolved_bounds=None`` returns the input mapping unchanged (byte parity)."""

    from rytm_randomizer.engines.pad1 import Pad1Engine

    eng = Pad1Engine(_RecordingOut(), sleep=no_sleep, resolved_bounds=None)

    state = {"FLT Frequency": 50, "AMP Overdrive": 16}
    assert eng._clamp_state(state) is state
