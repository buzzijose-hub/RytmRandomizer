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
singleton accessor used by MIDI, WebSocket, export, and analysis boundaries.
Callers record only bounded categorical labels and cumulative durations; this
module performs no I/O and does not import any hardware-facing dependency.

**Counter shapes:**

* ``cc_sent_by_channel`` -- one increment per CC accepted at the MIDI boundary,
  keyed by the MIDI channel (``0..15``). ``midi_io.send_cc`` records it only
  after the actual ``send`` call returns.
* ``cc_blocked_by_guardrail_by_pad`` -- one increment per CC that
  ``engines/_runtime._send_param`` decides not to send because the guardrail's
  ``clamped`` returned ``None`` (the value lies outside the per-pad allowed
  range). Keyed by pad index (``1..12``).
* ``errors_by_kind`` -- one increment per categorized error at any operator
  boundary. Keyed by a short, human-readable kind string (e.g.
  ``"port_open"``, ``"profile_load"``, ``"guardrail_lookup"``).
* ``a4_patch_inference_*``, ``a4_patch_publication_*``,
  ``a4_patch_render_rank_*``, and ``a4_patch_send_*`` -- RED metrics for the
  Analog Four audio feedback loop, each with a typed finite error-code
  vocabulary and cumulative latency.

One-shot A4 boundaries attach a current snapshot to their structured completion
or failure log through :meth:`MidiMetrics.format_summary`. Other callers can
snapshot the same in-process surface explicitly::

    from rytm_randomizer.observability.metrics import get_metrics

    summary = get_metrics().format_summary()
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Final, Literal, TypeAlias, TypeVar

__all__ = [
    "AnalogFourActiveErrorCode",
    "AnalogFourActiveOperation",
    "AnalogFourPatchInferenceErrorCode",
    "AnalogFourPatchBatchReadErrorCode",
    "AnalogFourPatchPublicationErrorCode",
    "AnalogFourPatchPublicationOperation",
    "AnalogFourPatchRenderRankErrorCode",
    "AnalogFourPatchSendErrorCode",
    "MidiMetrics",
    "PersistedStateRefusalCode",
    "get_metrics",
    "reset_metrics",
]


# Schema version for the in-process metrics surface. Bump on a
# backward-incompatible change to the counter keys / summary format so a
# future operator-side dumper can branch on it. ``Final`` per Gate 12.
_METRICS_VERSION: Final[int] = 1

AnalogFourActiveOperation: TypeAlias = Literal[
    "a4_cc_param_send",
    "a4_kit_recipe_send",
    "a4_nrpn_param_send",
    "a4_patch_send_plan_send",
    "a4_soft_capture",
]
"""Bounded operation names for one-shot armed Analog Four workflows."""

AnalogFourActiveErrorCode: TypeAlias = Literal[
    "arm_required",
    "capture_failed",
    "interrupted",
    "mapping_missing",
    "no_input_ports",
    "no_output_ports",
    "parameter_required",
    "port_close",
    "port_close_interrupted",
    "port_list",
    "port_open",
    "port_selection",
    "recipe_required",
    "recipe_unknown",
    "send_failed",
    "validation",
]
"""Bounded failures for one-shot armed Analog Four workflows."""

AnalogFourPatchInferenceErrorCode: TypeAlias = Literal[
    "audio_read_failed",
    "dependency_missing",
    "inference_failed",
    "interrupted",
    "validation",
]
"""Bounded failure categories for direct Analog Four patch inference."""

AnalogFourPatchBatchReadErrorCode: TypeAlias = Literal[
    "artifact_validation",
    "input_read_failed",
    "interrupted",
    "validation",
]
"""Bounded failure categories for verified A4 batch candidate loading."""

AnalogFourPatchRenderRankErrorCode: TypeAlias = Literal[
    "artifact_validation",
    "dependency_missing",
    "input_read_failed",
    "interrupted",
    "rank_failed",
    "reference_mismatch",
    "validation",
]
"""Bounded failure categories for recorded A4 render ranking."""

AnalogFourPatchPublicationOperation: TypeAlias = Literal[
    "artifact_publish",
    "lock_acquire",
    "lock_owner_check",
    "lock_release",
]
"""Bounded operation names for immutable A4 batch publication."""

AnalogFourPatchPublicationErrorCode: TypeAlias = Literal[
    "artifact_collision",
    "interrupted",
    "lock_exists",
    "read_failed",
    "release_failed",
    "write_failed",
]
"""Bounded failure categories for immutable A4 batch publication."""

AnalogFourPatchSendErrorCode: TypeAlias = Literal[
    "interrupted",
    "no_output_ports",
    "partial_send",
    "port_list",
    "port_open",
    "port_selection",
    "send_count_mismatch",
    "send_failed",
    "validation",
]
"""Bounded failure categories for armed A4 patch-plan delivery."""

PersistedStateRefusalCode: TypeAlias = Literal[
    "migration_failed",
    "schema_newer_than_app",
    "unknown_shape",
    "unknown_store",
    "unreadable",
]
"""Bounded refusal reasons for a persisted operator-state load (spec §11).

Mirrors the refusing half of
:data:`rytm_randomizer.data.persisted_state.PersistedStateCode` with the
shared ``persisted_state.`` prefix stripped — the prefix is implied by
the counter name, and the bare code keeps the ``format_summary`` line
readable. The two accepting outcomes are not refusals and are counted by
``record_persisted_state_migration`` (``migrated``) or not at all
(``ok`` — the uneventful path needs no counter).
"""

_CounterKey = TypeVar("_CounterKey", int, str)


@dataclass
class MidiMetrics:
    """Lazy in-process counters for the hot-path MIDI surface.

    Counter fields cover MIDI decisions and categorized failures; scalar
    fields cover low-cardinality pipeline counts and cumulative durations.
    Each ``record_*`` method performs only in-process increments, which are
    cheap enough to leave in place even in ``--arm`` mode.

    The dataclass is intentionally mutable and uses ``field(default_factory=Counter)``
    rather than ``frozen=True`` because :class:`Counter` mutation is the whole
    point -- a frozen wrapper would force every recorder to rebuild a new
    counter per increment. The escape hatch for tests is
    :func:`reset_metrics`, which zeroes the singleton's counters in place
    rather than swapping the singleton object.
    """

    cc_sent_by_channel: Counter[int] = field(default_factory=lambda: Counter[int]())
    cc_blocked_by_guardrail_by_pad: Counter[int] = field(default_factory=lambda: Counter[int]())
    errors_by_kind: Counter[str] = field(default_factory=lambda: Counter[str]())

    # OBS O2 — RED metrics per WS command. The dispatcher in
    # ``cockpit/ws/handlers.py`` increments these via
    # ``record_ws_command_*`` on each handler invocation. Keys are the
    # command-type strings from the wire (``"send"``, ``"wizard_save"``,
    # etc.); values are accumulated counts. Together these give a
    # per-command Rate (count), Errors (errors_by_code), and Duration
    # (total ms / count = average; full histograms are deferred to a
    # future OpenTelemetry shim per OBSERVABILITY_REVIEW.md PR O5).
    ws_command_count: Counter[str] = field(default_factory=lambda: Counter[str]())
    ws_command_errors_by_code: Counter[str] = field(default_factory=lambda: Counter[str]())
    ws_command_duration_ms_total: Counter[str] = field(default_factory=lambda: Counter[str]())

    # OBS O2 — RED metrics per export pipeline run.
    export_count: int = 0
    export_errors_by_code: Counter[str] = field(default_factory=lambda: Counter[str]())
    export_duration_ms_total: float = 0.0

    # Direct Analog Four audio inference is separately observable from the
    # export that may invoke it. ``None`` is success; failures use the bounded
    # ``AnalogFourPatchInferenceErrorCode`` vocabulary above.
    a4_patch_inference_count: int = 0
    a4_patch_inference_errors_by_code: Counter[AnalogFourPatchInferenceErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourPatchInferenceErrorCode]()
    )
    a4_patch_inference_duration_ms_total: float = 0.0

    a4_patch_batch_read_count: int = 0
    a4_patch_batch_read_errors_by_code: Counter[AnalogFourPatchBatchReadErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourPatchBatchReadErrorCode]()
    )
    a4_patch_batch_read_duration_ms_total: float = 0.0

    a4_patch_publication_count: Counter[AnalogFourPatchPublicationOperation] = field(
        default_factory=lambda: Counter[AnalogFourPatchPublicationOperation]()
    )
    a4_patch_publication_errors_by_code: Counter[AnalogFourPatchPublicationErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourPatchPublicationErrorCode]()
    )
    a4_patch_publication_errors_by_operation_and_code: Counter[str] = field(
        default_factory=lambda: Counter[str]()
    )
    a4_patch_publication_duration_ms_total: dict[AnalogFourPatchPublicationOperation, float] = (
        field(
            default_factory=lambda: dict[
                AnalogFourPatchPublicationOperation,
                float,
            ]()
        )
    )

    a4_patch_render_rank_count: int = 0
    a4_patch_render_rank_errors_by_code: Counter[AnalogFourPatchRenderRankErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourPatchRenderRankErrorCode]()
    )
    a4_patch_render_rank_duration_ms_total: float = 0.0

    a4_active_operation_count: Counter[AnalogFourActiveOperation] = field(
        default_factory=lambda: Counter[AnalogFourActiveOperation]()
    )
    a4_active_operation_errors_by_code: Counter[AnalogFourActiveErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourActiveErrorCode]()
    )
    a4_active_operation_duration_ms_total: dict[AnalogFourActiveOperation, float] = field(
        default_factory=lambda: dict[AnalogFourActiveOperation, float]()
    )

    a4_patch_send_count: int = 0
    a4_patch_send_errors_by_code: Counter[AnalogFourPatchSendErrorCode] = field(
        default_factory=lambda: Counter[AnalogFourPatchSendErrorCode]()
    )
    a4_patch_send_duration_ms_total: float = 0.0

    # Spec §11 Contract A — persisted operator state surviving a binary
    # swap. ``persisted_state_migrations`` is keyed ``"<store>:<from>-><to>"``
    # so an operator can see exactly which store moved which way; the
    # refusal counter is keyed by the bounded reason code. Both are
    # deliberately path-free — store ids, integers, and codes only.
    persisted_state_migrations: Counter[str] = field(default_factory=lambda: Counter[str]())
    persisted_state_refusals_by_code: Counter[str] = field(default_factory=lambda: Counter[str]())

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

        Called from the profile-model CLI and Analog Four saved-kit exporter
        after an export pipeline completes. ``duration_ms`` is wall-clock
        runtime; ``error_code`` is a stable category such as ``"profile_load"``,
        ``"source_read_failed"``, ``"overwrite_refused"``, or
        ``"write_failed"`` on failure and ``None`` on success.
        """

        self.export_count += 1
        self.export_duration_ms_total += duration_ms
        if error_code is not None:
            self.export_errors_by_code[error_code] += 1

    def record_a4_patch_inference(
        self,
        duration_ms: float,
        *,
        error_code: AnalogFourPatchInferenceErrorCode | None = None,
    ) -> None:
        """Record one direct Analog Four audio-to-patch inference run.

        ``duration_ms`` is the complete inference latency in milliseconds.
        Omit ``error_code`` on success. On failure, pass one stable category:
        ``"audio_read_failed"``, ``"dependency_missing"``,
        ``"inference_failed"``, or ``"validation"``. The ``Literal`` alias
        keeps this label vocabulary finite at type-check time.
        """

        self.a4_patch_inference_count += 1
        self.a4_patch_inference_duration_ms_total += duration_ms
        if error_code is not None:
            self.a4_patch_inference_errors_by_code[error_code] += 1

    def record_a4_patch_render_rank(
        self,
        duration_ms: float,
        *,
        error_code: AnalogFourPatchRenderRankErrorCode | None = None,
    ) -> None:
        """Record one complete recorded-candidate ranking operation."""

        self.a4_patch_render_rank_count += 1
        self.a4_patch_render_rank_duration_ms_total += duration_ms
        if error_code is not None:
            self.a4_patch_render_rank_errors_by_code[error_code] += 1

    def record_a4_patch_batch_read(
        self,
        duration_ms: float,
        *,
        error_code: AnalogFourPatchBatchReadErrorCode | None = None,
    ) -> None:
        """Record one verified A4 batch candidate load attempt."""

        self.a4_patch_batch_read_count += 1
        self.a4_patch_batch_read_duration_ms_total += duration_ms
        if error_code is not None:
            self.a4_patch_batch_read_errors_by_code[error_code] += 1

    def record_a4_patch_publication(
        self,
        operation: AnalogFourPatchPublicationOperation,
        duration_ms: float,
        *,
        error_code: AnalogFourPatchPublicationErrorCode | None = None,
    ) -> None:
        """Record one immutable artifact or cooperative-lock operation."""

        self.a4_patch_publication_count[operation] += 1
        current_duration = self.a4_patch_publication_duration_ms_total.get(operation, 0.0)
        self.a4_patch_publication_duration_ms_total[operation] = current_duration + duration_ms
        if error_code is not None:
            self.a4_patch_publication_errors_by_code[error_code] += 1
            self.a4_patch_publication_errors_by_operation_and_code[f"{operation}:{error_code}"] += 1

    def record_a4_patch_send(
        self,
        duration_ms: float,
        *,
        error_code: AnalogFourPatchSendErrorCode | None = None,
    ) -> None:
        """Record one complete armed A4 patch-plan delivery attempt."""

        self.a4_patch_send_count += 1
        self.a4_patch_send_duration_ms_total += duration_ms
        if error_code is not None:
            self.a4_patch_send_errors_by_code[error_code] += 1

    def record_a4_active_operation(
        self,
        operation: AnalogFourActiveOperation,
        duration_ms: float,
        *,
        error_code: AnalogFourActiveErrorCode | None = None,
    ) -> None:
        """Record one terminal one-shot armed Analog Four outcome."""

        self.a4_active_operation_count[operation] += 1
        current_duration = self.a4_active_operation_duration_ms_total.get(operation, 0.0)
        self.a4_active_operation_duration_ms_total[operation] = current_duration + duration_ms
        if error_code is not None:
            self.a4_active_operation_errors_by_code[error_code] += 1

    def record_a4_active_error(self, error_code: AnalogFourActiveErrorCode) -> None:
        """Record an ancillary active-operation error without a second attempt."""

        self.a4_active_operation_errors_by_code[error_code] += 1

    def record_persisted_state_migration(self, store: str, from_v: int, to_v: int) -> None:
        """Record one persisted-state store migrating forward across an update.

        Called by a store's loader after
        :func:`rytm_randomizer.data.persisted_state.classify_payload`
        returns ``persisted_state.migrated``. ``store`` is the registry
        ``store_id`` (never a path); ``from_v`` / ``to_v`` are the
        on-disk and app schema versions. The composite key keeps every
        distinct hop visible instead of collapsing them into a single
        per-store total.
        """

        self.persisted_state_migrations[f"{store}:{from_v}->{to_v}"] += 1

    def record_persisted_state_refusal(
        self,
        store: str,
        error_code: PersistedStateRefusalCode,
    ) -> None:
        """Record one refused persisted-state load (spec §11 rule: never reset).

        ``error_code`` is the bounded reason the load was refused. The
        ``Literal`` alias keeps the vocabulary finite at type-check time,
        the same discipline the A4 error codes use.
        """

        self.persisted_state_refusals_by_code[f"{store}:{error_code}"] += 1

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
            f"export_duration_ms={self.export_duration_ms_total:.1f}, "
            f"a4_inference_count={self.a4_patch_inference_count}, "
            f"a4_inference_errors={_format_counter(self.a4_patch_inference_errors_by_code)}, "
            f"a4_inference_duration_ms={self.a4_patch_inference_duration_ms_total:.1f}, "
            f"a4_batch_read_count={self.a4_patch_batch_read_count}, "
            f"a4_batch_read_errors={_format_counter(self.a4_patch_batch_read_errors_by_code)}, "
            f"a4_batch_read_duration_ms={self.a4_patch_batch_read_duration_ms_total:.1f}, "
            f"a4_publication_count={_format_counter(self.a4_patch_publication_count)}, "
            f"a4_publication_errors="
            f"{_format_counter(self.a4_patch_publication_errors_by_code)}, "
            f"a4_publication_errors_by_operation="
            f"{_format_counter(self.a4_patch_publication_errors_by_operation_and_code)}, "
            f"a4_publication_duration_ms="
            f"{_format_counter(self.a4_patch_publication_duration_ms_total)}, "
            f"a4_render_rank_count={self.a4_patch_render_rank_count}, "
            f"a4_render_rank_errors={_format_counter(self.a4_patch_render_rank_errors_by_code)}, "
            f"a4_render_rank_duration_ms={self.a4_patch_render_rank_duration_ms_total:.1f}, "
            f"a4_active_count={_format_counter(self.a4_active_operation_count)}, "
            f"a4_active_errors={_format_counter(self.a4_active_operation_errors_by_code)}, "
            f"a4_active_duration_ms="
            f"{_format_counter(self.a4_active_operation_duration_ms_total)}, "
            f"a4_patch_send_count={self.a4_patch_send_count}, "
            f"a4_patch_send_errors={_format_counter(self.a4_patch_send_errors_by_code)}, "
            f"a4_patch_send_duration_ms={self.a4_patch_send_duration_ms_total:.1f}, "
            f"persisted_state_migrations={_format_counter(self.persisted_state_migrations)}, "
            f"persisted_state_refusals="
            f"{_format_counter(self.persisted_state_refusals_by_code)}"
        )


def _format_counter(counter: Mapping[_CounterKey, int | float]) -> str:
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
    _METRICS.a4_patch_inference_count = 0
    _METRICS.a4_patch_inference_errors_by_code.clear()
    _METRICS.a4_patch_inference_duration_ms_total = 0.0
    _METRICS.a4_patch_batch_read_count = 0
    _METRICS.a4_patch_batch_read_errors_by_code.clear()
    _METRICS.a4_patch_batch_read_duration_ms_total = 0.0
    _METRICS.a4_patch_publication_count.clear()
    _METRICS.a4_patch_publication_errors_by_code.clear()
    _METRICS.a4_patch_publication_errors_by_operation_and_code.clear()
    _METRICS.a4_patch_publication_duration_ms_total.clear()
    _METRICS.a4_patch_render_rank_count = 0
    _METRICS.a4_patch_render_rank_errors_by_code.clear()
    _METRICS.a4_patch_render_rank_duration_ms_total = 0.0
    _METRICS.a4_active_operation_count.clear()
    _METRICS.a4_active_operation_errors_by_code.clear()
    _METRICS.a4_active_operation_duration_ms_total.clear()
    _METRICS.a4_patch_send_count = 0
    _METRICS.a4_patch_send_errors_by_code.clear()
    _METRICS.a4_patch_send_duration_ms_total = 0.0
    _METRICS.persisted_state_migrations.clear()
    _METRICS.persisted_state_refusals_by_code.clear()
