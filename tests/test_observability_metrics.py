"""Targeted coverage tests for ``rytm_randomizer.observability.metrics`` (WS-S9).

The metrics module is the third leg of the observability tripod
(``logging`` + ``tracing`` + ``metrics``). It owns a single mutable
:class:`MidiMetrics` dataclass plus a module-level singleton accessed via
:func:`get_metrics`. These tests cover the full public surface:

* importability of the three public names;
* default-empty counters on a fresh ``MidiMetrics()``;
* each ``record_*`` method increments the right counter;
* :func:`format_summary` includes every recorded count;
* :func:`get_metrics` returns the same singleton across calls;
* :func:`reset_metrics` zeroes every counter on the singleton.

Every test that touches the singleton uses the ``reset_metrics_around_test``
autouse fixture so a previous test's recorded events never leak into the
next case -- the singleton is process-wide, so a leak here would otherwise
break test independence as soon as the tests are reordered.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator

import pytest

from rytm_randomizer.observability.metrics import (
    MidiMetrics,
    get_metrics,
    reset_metrics,
)

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixture: prevent test-to-test state leakage on the module-level singleton.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_metrics_around_test() -> Iterator[None]:
    """Reset the singleton before and after every test in this module.

    The metrics singleton is process-wide -- tests that record events on
    ``get_metrics()`` would otherwise leak counts into later cases. We
    reset on both sides of the yield so a test that fails partway through
    does not poison the next test's setup.
    """

    reset_metrics()
    try:
        yield
    finally:
        reset_metrics()


# ---------------------------------------------------------------------------
# Public-surface importability.
# ---------------------------------------------------------------------------


def test_public_surface_is_importable() -> None:
    """``MidiMetrics``, ``get_metrics``, and ``reset_metrics`` are exported.

    A typo on any of the three would either break this import or the
    callable / class assertions below.
    """

    assert isinstance(MidiMetrics, type)
    assert callable(get_metrics)
    assert callable(reset_metrics)


# ---------------------------------------------------------------------------
# Default state of a fresh MidiMetrics instance.
# ---------------------------------------------------------------------------


def test_midi_metrics_defaults_to_empty_counters() -> None:
    """A freshly constructed ``MidiMetrics()`` has three empty counters.

    Each field defaults via ``field(default_factory=Counter)`` so two
    instances must not share counter state; we verify both the emptiness
    and the per-instance isolation.
    """

    metrics_a = MidiMetrics()
    metrics_b = MidiMetrics()

    assert isinstance(metrics_a.cc_sent_by_channel, Counter)
    assert isinstance(metrics_a.cc_blocked_by_guardrail_by_pad, Counter)
    assert isinstance(metrics_a.errors_by_kind, Counter)
    assert len(metrics_a.cc_sent_by_channel) == 0
    assert len(metrics_a.cc_blocked_by_guardrail_by_pad) == 0
    assert len(metrics_a.errors_by_kind) == 0

    # Per-instance isolation: mutating one must not touch the other.
    metrics_a.record_cc_sent(0)
    assert metrics_b.cc_sent_by_channel[0] == 0


# ---------------------------------------------------------------------------
# record_* methods.
# ---------------------------------------------------------------------------


def test_record_cc_sent_increments_per_channel_counter() -> None:
    """``record_cc_sent(0)`` increments ``cc_sent_by_channel[0]`` by one.

    Repeated calls accumulate; a different channel goes to its own bucket.
    """

    metrics = MidiMetrics()

    metrics.record_cc_sent(0)
    metrics.record_cc_sent(0)
    metrics.record_cc_sent(1)

    assert metrics.cc_sent_by_channel[0] == 2
    assert metrics.cc_sent_by_channel[1] == 1


def test_record_guardrail_block_increments_per_pad_counter() -> None:
    """``record_guardrail_block(2)`` increments ``cc_blocked_by_guardrail_by_pad[2]``."""

    metrics = MidiMetrics()

    metrics.record_guardrail_block(2)
    metrics.record_guardrail_block(2)
    metrics.record_guardrail_block(5)

    assert metrics.cc_blocked_by_guardrail_by_pad[2] == 2
    assert metrics.cc_blocked_by_guardrail_by_pad[5] == 1


def test_record_error_increments_per_kind_counter() -> None:
    """``record_error("port_open")`` increments ``errors_by_kind["port_open"]``."""

    metrics = MidiMetrics()

    metrics.record_error("port_open")
    metrics.record_error("port_open")
    metrics.record_error("profile_load")

    assert metrics.errors_by_kind["port_open"] == 2
    assert metrics.errors_by_kind["profile_load"] == 1


# ---------------------------------------------------------------------------
# format_summary.
# ---------------------------------------------------------------------------


def test_format_summary_includes_recorded_counts() -> None:
    """``format_summary`` mentions every counter with the recorded values.

    The exact layout is stable but not asserted character-for-character --
    we want operator-visible counts to render, not lock down the prose.
    """

    metrics = MidiMetrics()
    metrics.record_cc_sent(0)
    metrics.record_cc_sent(0)
    metrics.record_cc_sent(1)
    metrics.record_guardrail_block(2)
    metrics.record_error("port_open")

    summary = metrics.format_summary()

    assert summary.startswith("MidiMetrics:")
    assert "0:2" in summary  # channel 0, two sends
    assert "1:1" in summary  # channel 1, one send
    assert "2:1" in summary  # pad 2, one block
    assert "port_open:1" in summary
    assert "cc_sent=" in summary
    assert "blocked=" in summary
    assert "errors=" in summary


def test_format_summary_renders_empty_counters_as_braces() -> None:
    """Empty counters render as ``{}`` rather than being elided.

    The operator should be able to tell ``"nothing recorded"`` apart from
    ``"the section was omitted from the summary"``.
    """

    summary = MidiMetrics().format_summary()

    assert "cc_sent={}" in summary
    assert "blocked={}" in summary
    assert "errors={}" in summary


# ---------------------------------------------------------------------------
# get_metrics singleton + reset_metrics.
# ---------------------------------------------------------------------------


def test_get_metrics_returns_singleton_identity() -> None:
    """Two calls to :func:`get_metrics` return the *same* object.

    Callers cache the reference at module top level on the hot path; a
    different object per call would silently throw their increments away.
    """

    assert get_metrics() is get_metrics()


def test_reset_metrics_clears_singleton_counters_in_place() -> None:
    """``reset_metrics`` zeroes the singleton's counters but keeps identity.

    Identity preservation matters because hot-path callers may cache
    ``get_metrics()`` at module load and would otherwise hold a stale
    reference after a reset.
    """

    metrics = get_metrics()
    metrics.record_cc_sent(0)
    metrics.record_guardrail_block(3)
    metrics.record_error("profile_load")

    assert metrics.cc_sent_by_channel[0] == 1
    assert metrics.cc_blocked_by_guardrail_by_pad[3] == 1
    assert metrics.errors_by_kind["profile_load"] == 1

    reset_metrics()

    assert get_metrics() is metrics
    assert len(metrics.cc_sent_by_channel) == 0
    assert len(metrics.cc_blocked_by_guardrail_by_pad) == 0
    assert len(metrics.errors_by_kind) == 0
