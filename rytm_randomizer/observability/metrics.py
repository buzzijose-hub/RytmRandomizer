"""Lightweight in-process MIDI metrics for the RytmRandomizer package (WS-S9).

This module owns a single, lazy, in-process counter surface that the hot path
can use to record per-decision telemetry without bloating the MIDI boundary.
It is the "metrics" leg of the observability tripod (the other two being
:mod:`rytm_randomizer.observability.logging` and
:mod:`rytm_randomizer.observability.tracing`), and it intentionally mirrors
those modules' conventions:

* a leaf module -- imports nothing from ``rytm_randomizer/`` -- so the
  architecture-conformance tests keep the dependency graph one-directional;
* a single module-level singleton accessed via :func:`get_metrics` so callers
  on the hot path do not pay an allocation or a service-locator round-trip
  per CC send;
* a :func:`reset_metrics` escape hatch for tests so the counter does not leak
  state between cases;
* `from __future__ import annotations` at the top per project house-style
  (``ruff FA100``); module-level constants annotated with :class:`typing.Final`
  per Plan-Requirements Gate 12.

**What this module does (now):** it provides the counter dataclass and the
singleton accessor. Nothing in the package currently increments the counters
-- that adoption work (adding ``get_metrics().record_cc_sent(...)`` calls in
``engines/_runtime.py``, ``engines/pad{1-4}.py``, ``randomization.py``,
``scene_runner.py``, ``group_runner.py``) is the deferred follow-up tracked
by WS-S9's hot-path adoption phase. Keeping this WS to the metrics surface
alone lets reviewers focus on the data model (counter keys, summary format,
singleton lifecycle) without churning hot-path files in the same change set.

**Counter shapes:**

* ``cc_sent_by_channel`` -- one increment per CC sent at the MIDI boundary,
  keyed by the MIDI channel (``0..15``). Future adoption: incremented from
  ``rytm_randomizer.midi_io.send_cc`` after the actual ``send`` call returns.
* ``cc_blocked_by_guardrail_by_pad`` -- one increment per CC that
  ``engines/_runtime._send_param`` decides not to send because the guardrail's
  ``clamped`` returned ``None`` (the value lies outside the per-pad allowed
  range). Keyed by pad index (``1..12``).
* ``errors_by_kind`` -- one increment per categorized error at any operator
  boundary. Keyed by a short, human-readable kind string (e.g.
  ``"port_open"``, ``"profile_load"``, ``"guardrail_lookup"``).

Operator-facing usage at shell exit::

    from rytm_randomizer.observability.metrics import get_metrics

    # ... after shell.run() returns ...
    print(get_metrics().format_summary(), file=sys.stderr)
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Final

__all__ = [
    "MidiMetrics",
    "get_metrics",
    "reset_metrics",
]


# Schema version for the in-process metrics surface. Bump on a
# backward-incompatible change to the counter keys / summary format so a
# future operator-side dumper can branch on it. ``Final`` per Gate 12.
_METRICS_VERSION: Final[int] = 1


@dataclass
class MidiMetrics:
    """Lazy in-process counters for the hot-path MIDI surface.

    Three :class:`collections.Counter` fields cover the decisions the hot
    path makes today: a CC was sent, a CC was suppressed by a guardrail, or
    an operator-visible error happened. Each ``record_*`` method is a thin
    wrapper over ``Counter[key] += 1`` -- callers on the hot path pay one
    attribute lookup and one dict increment per event, which is cheap enough
    to leave in place even in ``--arm`` mode without measuring.

    The dataclass is intentionally mutable and uses ``field(default_factory=Counter)``
    rather than ``frozen=True`` because :class:`Counter` mutation is the whole
    point -- a frozen wrapper would force every recorder to rebuild a new
    counter per increment. The escape hatch for tests is
    :func:`reset_metrics`, which zeroes the singleton's counters in place
    rather than swapping the singleton object.
    """

    cc_sent_by_channel: Counter[int] = field(default_factory=Counter)
    cc_blocked_by_guardrail_by_pad: Counter[int] = field(default_factory=Counter)
    errors_by_kind: Counter[str] = field(default_factory=Counter)

    # OBS O2 — RED metrics per WS command. The dispatcher in
    # ``cockpit/ws/handlers.py`` increments these via
    # ``record_ws_command_*`` on each handler invocation. Keys are the
    # command-type strings from the wire (``"send"``, ``"wizard_save"``,
    # etc.); values are accumulated counts. Together these give a
    # per-command Rate (count), Errors (errors_by_code), and Duration
    # (total ms / count = average; full histograms are deferred to a
    # future OpenTelemetry shim per OBSERVABILITY_REVIEW.md PR O5).
    ws_command_count: Counter[str] = field(default_factory=Counter)
    ws_command_errors_by_code: Counter[str] = field(default_factory=Counter)
    ws_command_duration_ms_total: Counter[str] = field(default_factory=Counter)

    # OBS O2 — RED metrics per export pipeline run.
    export_count: int = 0
    export_errors_by_code: Counter[str] = field(default_factory=Counter)
    export_duration_ms_total: float = 0.0

    def record_cc_sent(self, channel: int) -> None:
        """Increment the per-channel CC-sent counter for ``channel``.

        ``channel`` is the MIDI channel index (``0..15``). No validation is
        performed: the hot path already validates the channel before the
        ``send_cc`` call, and a defensive check here would add a branch on
        every send for a condition the caller has already enforced.
        """

        self.cc_sent_by_channel[channel] += 1

    def record_guardrail_block(self, pad: int) -> None:
        """Increment the guardrail-block counter for ``pad``.

        Called from ``engines/_runtime._send_param`` whenever the guardrail's
        ``clamped`` returns ``None`` -- i.e. the requested value lies outside
        the allowed range for the pad's machine and the CC is suppressed.
        ``pad`` is the 1-based pad index (``1..12``).
        """

        self.cc_blocked_by_guardrail_by_pad[pad] += 1

    def record_error(self, kind: str) -> None:
        """Increment the error-by-kind counter for ``kind``.

        ``kind`` is a short, human-readable label such as ``"port_open"``,
        ``"profile_load"``, or ``"guardrail_lookup"``. Use a small, stable
        vocabulary so the resulting histogram is meaningful at a glance --
        a free-form string would defeat the purpose of a categorized counter.
        """

        self.errors_by_kind[kind] += 1

    def record_ws_command(
        self,
        cmd_type: str,
        duration_ms: float,
        *,
        error_code: str | None = None,
    ) -> None:
        """Record one WS command invocation for RED metrics.

        Called by the WS dispatcher in ``cockpit/ws/handlers.py`` after each
        handler returns (or raises). ``cmd_type`` is the command-type string
        from the wire (``"send"``, ``"wizard_save"``, etc.); ``duration_ms``
        is wall-clock handler runtime in milliseconds; ``error_code`` is the
        categorical ack code (``ERR_*``) when the handler produced an error
        envelope, ``None`` on success.

        Together these three counters give per-command Rate (count), Errors
        (errors_by_code), and Duration (total / count = average). Full
        histograms are deferred to a future OpenTelemetry shim per
        OBSERVABILITY_REVIEW.md PR O5.
        """

        self.ws_command_count[cmd_type] += 1
        self.ws_command_duration_ms_total[cmd_type] += int(duration_ms)
        if error_code is not None:
            self.ws_command_errors_by_code[error_code] += 1

    def record_export(
        self,
        duration_ms: float,
        *,
        error_code: str | None = None,
    ) -> None:
        """Record one export pipeline run for RED metrics.

        Called from ``cockpit/export/cli.py`` after the export pipeline
        completes (success or failure). ``duration_ms`` is wall-clock
        pipeline runtime; ``error_code`` is a categorical label such as
        ``"profile_load"`` / ``"pack_failed"`` / ``"write_failed"`` on
        failure, ``None`` on success.
        """

        self.export_count += 1
        self.export_duration_ms_total += duration_ms
        if error_code is not None:
            self.export_errors_by_code[error_code] += 1

    def format_summary(self) -> str:
        """Return a multi-line human-readable summary of every counter.

        The summary lists each counter on its own line with a deterministic
        ``key:count`` ordering (sorted by key) so output is stable across
        runs and diffable in regression tests. Empty counters render as
        ``{}`` rather than being elided, so an operator scanning the summary
        can tell the difference between "nothing recorded" and "the section
        was omitted".
        """

        return (
            "MidiMetrics: "
            f"cc_sent={_format_counter(self.cc_sent_by_channel)}, "
            f"blocked={_format_counter(self.cc_blocked_by_guardrail_by_pad)}, "
            f"errors={_format_counter(self.errors_by_kind)}, "
            f"ws_cmd_count={_format_counter(self.ws_command_count)}, "
            f"ws_cmd_errors={_format_counter(self.ws_command_errors_by_code)}, "
            f"ws_cmd_duration_ms={_format_counter(self.ws_command_duration_ms_total)}, "
            f"export_count={self.export_count}, "
            f"export_errors={_format_counter(self.export_errors_by_code)}, "
            f"export_duration_ms={self.export_duration_ms_total:.1f}"
        )


def _format_counter(counter: Counter[object]) -> str:
    """Render a :class:`Counter` as a deterministic ``{k:v, ...}`` string.

    Keys are sorted (using their natural ordering) so the output is stable
    across runs. Empty counters render as ``{}`` rather than being elided.
    """

    if not counter:
        return "{}"
    items = ", ".join(f"{key}:{counter[key]}" for key in sorted(counter))
    return "{" + items + "}"


# Module-level singleton. Allocated at import time -- a :class:`Counter` with
# no entries is essentially free, and the singleton-creation cost is one-shot
# at first ``import rytm_randomizer.observability.metrics``.
_METRICS: MidiMetrics = MidiMetrics()


def get_metrics() -> MidiMetrics:
    """Return the process-wide :class:`MidiMetrics` singleton.

    Every call returns the *same* object identity, so a caller can safely
    cache the reference at module top level (e.g.
    ``_metrics = get_metrics()``) and increment via the cached reference
    rather than re-resolving the singleton on every send.
    """

    return _METRICS


def reset_metrics() -> None:
    """Zero every counter on the singleton; preserve singleton identity.

    Intended for tests so a previous test's recorded events do not leak into
    the next case. We clear the counters *in place* rather than replacing the
    ``_METRICS`` object so any caller that already cached
    ``get_metrics()`` keeps seeing the zeroed counters instead of pointing
    at a stale instance.
    """

    _METRICS.cc_sent_by_channel.clear()
    _METRICS.cc_blocked_by_guardrail_by_pad.clear()
    _METRICS.errors_by_kind.clear()
    _METRICS.ws_command_count.clear()
    _METRICS.ws_command_errors_by_code.clear()
    _METRICS.ws_command_duration_ms_total.clear()
    _METRICS.export_count = 0
    _METRICS.export_errors_by_code.clear()
    _METRICS.export_duration_ms_total = 0.0
