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
from typing import get_args

import pytest

from rytm_randomizer.observability.metrics import (
    AnalogFourPatchInferenceErrorCode,
    AnalogFourPatchRenderRankErrorCode,
    AnalogFourPatchSendErrorCode,
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
    """The metrics class, lifecycle functions, and A4 error type are exported.

    A typo on any of the three would either break this import or the
    callable / class assertions below.
    """

    assert isinstance(MidiMetrics, type)
    assert get_args(AnalogFourPatchInferenceErrorCode)
    assert get_args(AnalogFourPatchRenderRankErrorCode)
    assert get_args(AnalogFourPatchSendErrorCode)
    assert callable(get_metrics)
    assert callable(reset_metrics)


def test_a4_patch_inference_error_codes_are_bounded() -> None:
    """Direct inference failures use a finite, type-checkable vocabulary."""

    assert frozenset(get_args(AnalogFourPatchInferenceErrorCode)) == frozenset(
        {
            "audio_read_failed",
            "dependency_missing",
            "inference_failed",
            "validation",
        }
    )


def test_a4_patch_send_error_codes_are_bounded() -> None:
    assert frozenset(get_args(AnalogFourPatchSendErrorCode)) == frozenset(
        {
            "interrupted",
            "no_output_ports",
            "partial_send",
            "port_list",
            "port_open",
            "port_selection",
            "send_count_mismatch",
            "send_failed",
            "validation",
        }
    )


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


# ---------------------------------------------------------------------------
# OBS O2 — RED metrics for WS commands.
# ---------------------------------------------------------------------------


def test_record_ws_command_success_increments_count_and_duration() -> None:
    """A successful WS command bumps count + duration; not errors_by_code."""

    metrics = MidiMetrics()

    metrics.record_ws_command("send", duration_ms=12.4)
    metrics.record_ws_command("send", duration_ms=8.1)
    metrics.record_ws_command("save", duration_ms=42.0)

    assert metrics.ws_command_count["send"] == 2
    assert metrics.ws_command_count["save"] == 1
    # ``int(...)`` per cumulative-counter contract; floats are accumulated
    # only on the export side where the cardinality is far lower.
    assert metrics.ws_command_duration_ms_total["send"] == 12 + 8
    assert metrics.ws_command_duration_ms_total["save"] == 42
    # No error_code passed → errors_by_code remains untouched.
    assert len(metrics.ws_command_errors_by_code) == 0


def test_record_ws_command_with_error_code_bumps_error_bucket() -> None:
    """When ``error_code`` is set the same call increments errors_by_code."""

    metrics = MidiMetrics()

    metrics.record_ws_command("send", 1.0)  # success
    metrics.record_ws_command("send", 3.0, error_code="ERR_INTERNAL")
    metrics.record_ws_command("send", 4.0, error_code="ERR_VALIDATION")
    metrics.record_ws_command("send", 2.0, error_code="ERR_INTERNAL")

    # count + duration include EVERY call regardless of outcome.
    assert metrics.ws_command_count["send"] == 4
    assert metrics.ws_command_duration_ms_total["send"] == 1 + 3 + 4 + 2
    # errors_by_code is keyed on the categorical code, not the command.
    assert metrics.ws_command_errors_by_code["ERR_INTERNAL"] == 2
    assert metrics.ws_command_errors_by_code["ERR_VALIDATION"] == 1


def test_record_export_success_path() -> None:
    """A successful export bumps count + duration; not errors_by_code."""

    metrics = MidiMetrics()

    metrics.record_export(duration_ms=120.5)
    metrics.record_export(duration_ms=89.25)

    assert metrics.export_count == 2
    # Float accumulation here (low cardinality, single bucket).
    assert metrics.export_duration_ms_total == pytest.approx(209.75)
    assert len(metrics.export_errors_by_code) == 0


def test_record_export_error_path() -> None:
    """A failed export bumps count + duration + errors_by_code together."""

    metrics = MidiMetrics()

    metrics.record_export(20.0, error_code="write_failed")
    metrics.record_export(30.0, error_code="write_failed")
    metrics.record_export(40.0, error_code="pack_failed")
    metrics.record_export(50.0)  # success interleaved

    assert metrics.export_count == 4
    assert metrics.export_duration_ms_total == pytest.approx(140.0)
    assert metrics.export_errors_by_code["write_failed"] == 2
    assert metrics.export_errors_by_code["pack_failed"] == 1


def test_record_a4_patch_inference_success_path() -> None:
    """Successful direct inference records count and latency without an error."""

    metrics = MidiMetrics()

    metrics.record_a4_patch_inference(125.5)
    metrics.record_a4_patch_inference(74.25)

    assert metrics.a4_patch_inference_count == 2
    assert metrics.a4_patch_inference_duration_ms_total == pytest.approx(199.75)
    assert not metrics.a4_patch_inference_errors_by_code


def test_record_a4_patch_inference_error_path() -> None:
    """Failed direct inference records count, latency, and its bounded category."""

    metrics = MidiMetrics()

    metrics.record_a4_patch_inference(20.0, error_code="audio_read_failed")
    metrics.record_a4_patch_inference(30.0, error_code="dependency_missing")
    metrics.record_a4_patch_inference(40.0, error_code="inference_failed")
    metrics.record_a4_patch_inference(50.0, error_code="validation")

    assert metrics.a4_patch_inference_count == 4
    assert metrics.a4_patch_inference_duration_ms_total == pytest.approx(140.0)
    assert metrics.a4_patch_inference_errors_by_code == Counter(
        {
            "audio_read_failed": 1,
            "dependency_missing": 1,
            "inference_failed": 1,
            "validation": 1,
        }
    )


def test_record_a4_render_rank_and_patch_send_red_metrics() -> None:
    metrics = MidiMetrics()

    metrics.record_a4_patch_render_rank(12.5)
    metrics.record_a4_patch_render_rank(7.5, error_code="reference_mismatch")
    metrics.record_a4_patch_send(30.0)
    metrics.record_a4_patch_send(20.0, error_code="partial_send")

    assert metrics.a4_patch_render_rank_count == 2
    assert metrics.a4_patch_render_rank_duration_ms_total == pytest.approx(20.0)
    assert metrics.a4_patch_render_rank_errors_by_code["reference_mismatch"] == 1
    assert metrics.a4_patch_send_count == 2
    assert metrics.a4_patch_send_duration_ms_total == pytest.approx(50.0)
    assert metrics.a4_patch_send_errors_by_code["partial_send"] == 1


def test_format_summary_includes_red_metrics_sections() -> None:
    """``format_summary`` exposes every RED counter and the export scalars.

    Operators grep this string at shell exit; the section labels are part
    of the operator-facing contract and shouldn't drift silently.
    """

    metrics = MidiMetrics()
    metrics.record_ws_command("send", 12.0)
    metrics.record_ws_command("send", 8.0, error_code="ERR_INTERNAL")
    metrics.record_export(100.0)
    metrics.record_export(50.0, error_code="write_failed")
    metrics.record_a4_patch_inference(75.0)
    metrics.record_a4_patch_inference(25.0, error_code="dependency_missing")
    metrics.record_a4_patch_render_rank(20.0, error_code="reference_mismatch")
    metrics.record_a4_patch_send(15.0, error_code="partial_send")

    summary = metrics.format_summary()

    assert "ws_cmd_count=" in summary
    assert "ws_cmd_errors=" in summary
    assert "ws_cmd_duration_ms=" in summary
    assert "export_count=2" in summary
    assert "export_errors=" in summary
    assert "export_duration_ms=150.0" in summary
    assert "send:2" in summary
    assert "ERR_INTERNAL:1" in summary
    assert "write_failed:1" in summary
    assert "a4_inference_count=2" in summary
    assert "a4_inference_errors=" in summary
    assert "a4_inference_duration_ms=100.0" in summary
    assert "dependency_missing:1" in summary
    assert "a4_render_rank_count=1" in summary
    assert "a4_render_rank_errors=" in summary
    assert "a4_render_rank_duration_ms=20.0" in summary
    assert "reference_mismatch:1" in summary
    assert "a4_patch_send_count=1" in summary
    assert "a4_patch_send_errors=" in summary
    assert "a4_patch_send_duration_ms=15.0" in summary
    assert "partial_send:1" in summary


def test_format_summary_red_metrics_empty_render_as_braces_and_zeros() -> None:
    """Empty RED counters render as ``{}`` / ``0`` rather than being elided."""

    summary = MidiMetrics().format_summary()

    assert "ws_cmd_count={}" in summary
    assert "ws_cmd_errors={}" in summary
    assert "ws_cmd_duration_ms={}" in summary
    assert "export_count=0" in summary
    assert "export_errors={}" in summary
    assert "export_duration_ms=0.0" in summary
    assert "a4_inference_count=0" in summary
    assert "a4_inference_errors={}" in summary
    assert "a4_inference_duration_ms=0.0" in summary
    assert "a4_render_rank_count=0" in summary
    assert "a4_render_rank_errors={}" in summary
    assert "a4_render_rank_duration_ms=0.0" in summary
    assert "a4_patch_send_count=0" in summary
    assert "a4_patch_send_errors={}" in summary
    assert "a4_patch_send_duration_ms=0.0" in summary


def test_reset_metrics_clears_red_metric_counters() -> None:
    """``reset_metrics`` also zeros the OBS O2 counters in place."""

    metrics = get_metrics()
    metrics.record_ws_command("send", 10.0, error_code="ERR_INTERNAL")
    metrics.record_export(50.0, error_code="write_failed")
    metrics.record_a4_patch_inference(25.0, error_code="inference_failed")
    metrics.record_a4_patch_render_rank(15.0, error_code="artifact_validation")
    metrics.record_a4_patch_send(10.0, error_code="validation")

    assert metrics.ws_command_count["send"] == 1
    assert metrics.ws_command_errors_by_code["ERR_INTERNAL"] == 1
    assert metrics.ws_command_duration_ms_total["send"] == 10
    assert metrics.export_count == 1
    assert metrics.export_duration_ms_total == pytest.approx(50.0)
    assert metrics.export_errors_by_code["write_failed"] == 1
    assert metrics.a4_patch_inference_count == 1
    assert metrics.a4_patch_inference_duration_ms_total == pytest.approx(25.0)
    assert metrics.a4_patch_inference_errors_by_code["inference_failed"] == 1
    assert metrics.a4_patch_render_rank_errors_by_code["artifact_validation"] == 1
    assert metrics.a4_patch_send_errors_by_code["validation"] == 1

    reset_metrics()

    # Identity preserved across reset (hot-path callers may cache it).
    assert get_metrics() is metrics
    assert len(metrics.ws_command_count) == 0
    assert len(metrics.ws_command_errors_by_code) == 0
    assert len(metrics.ws_command_duration_ms_total) == 0
    assert metrics.export_count == 0
    assert metrics.export_duration_ms_total == 0.0
    assert len(metrics.export_errors_by_code) == 0
    assert metrics.a4_patch_inference_count == 0
    assert metrics.a4_patch_inference_duration_ms_total == 0.0
    assert len(metrics.a4_patch_inference_errors_by_code) == 0
    assert metrics.a4_patch_render_rank_count == 0
    assert metrics.a4_patch_render_rank_duration_ms_total == 0.0
    assert len(metrics.a4_patch_render_rank_errors_by_code) == 0
    assert metrics.a4_patch_send_count == 0
    assert metrics.a4_patch_send_duration_ms_total == 0.0
    assert len(metrics.a4_patch_send_errors_by_code) == 0
