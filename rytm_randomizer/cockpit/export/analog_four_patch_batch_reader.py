"""Verified reader for immutable Analog Four audio-patch batch candidates."""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from ...behavior.midi_event_plan import (
    validate_cc_nrpn_event,
    validate_cc_nrpn_event_plan,
)
from ...data.analog_four_display import (
    A4_MIDI_MAX,
    A4_MIDI_MIN,
    TRANSPORT_CC_READY,
    TRANSPORT_NRPN_READY,
    TRANSPORT_SCREEN_ONLY,
    TRANSPORT_SCREEN_ONLY_NRPN,
)
from ...data.analog_four_midi import ANALOG_FOUR_MANUAL_CC, ANALOG_FOUR_SYNTH_TRACK_NRPN
from ...data.midi_event_kinds import (
    MIDI_EVENT_KIND_CC,
    MIDI_EVENT_KIND_NRPN,
    MIDI_EVENT_SKIP_NOT_READY,
    MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED,
    MidiEventKind,
)
from ...observability.logging import get_logger
from ...observability.metrics import (
    AnalogFourPatchBatchReadErrorCode,
    get_metrics,
)
from ...observability.tracing import operation
from ...style_analysis.analog_four_patch_genome import (
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
)
from ...style_analysis.analog_four_patch_send_plan import (
    ANALOG_FOUR_PATCH_SEND_PLAN_VERSION,
    AnalogFourPatchManualEvent,
    AnalogFourPatchSendEvent,
    AnalogFourPatchSendSummary,
)
from .analog_four_patch_batch_codec import (
    BATCH_SCHEMA_VERSION,
    CANDIDATE_SCHEMA_VERSION,
    analog_four_patch_batch_payload_sha256,
    analog_four_patch_batch_sha256,
    decode_analog_four_patch_batch_json,
    validate_analog_four_patch_batch_sha256,
)

_VALID_MESSAGE_KINDS: Final[frozenset[MidiEventKind]] = frozenset(
    {MIDI_EVENT_KIND_CC, MIDI_EVENT_KIND_NRPN}
)
_SEND_STATUS_BY_KIND: Final[Mapping[MidiEventKind, str]] = MappingProxyType(
    {
        MIDI_EVENT_KIND_CC: TRANSPORT_CC_READY,
        MIDI_EVENT_KIND_NRPN: TRANSPORT_NRPN_READY,
    }
)
_MANUAL_TRANSPORT_STATUSES: Final[frozenset[str]] = frozenset(
    {TRANSPORT_SCREEN_ONLY, TRANSPORT_SCREEN_ONLY_NRPN}
)
_BATCH_READ_FAILURE_FINGERPRINT: Final[str] = "a4.patch_batch.read_failed"
_logger = get_logger(__name__)


@dataclass(frozen=True)
class StoredAnalogFourPatchSendPlan:
    """Minimal immutable transport plan reconstructed from a verified sidecar."""

    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    send_events: tuple[AnalogFourPatchSendEvent, ...]
    manual_events: tuple[AnalogFourPatchManualEvent, ...]
    summary: AnalogFourPatchSendSummary


@dataclass(frozen=True)
class AnalogFourPatchBatchSelection:
    """One verified candidate selected from a committed batch generation."""

    manifest_path: Path
    sidecar_path: Path
    generation_id: str
    audio_sha256: str
    manifest_sha256: str
    sidecar_sha256: str
    plan: StoredAnalogFourPatchSendPlan


def load_analog_four_patch_batch_candidate(
    manifest_path: Path,
    *,
    candidate: int,
) -> AnalogFourPatchBatchSelection:
    """Load one batch candidate only after all stored hashes and identities agree."""

    started_at = time.perf_counter()
    manifest_name = _batch_candidate_manifest_name(manifest_path)
    candidate_label = _batch_candidate_number(candidate)
    request_validated = False
    operation_id = ""
    try:
        with operation(
            "a4_patch_batch_candidate_read",
            logger=_logger,
            manifest_name=manifest_name,
            candidate=candidate_label,
        ) as operation_id:
            manifest_path, candidate = _validate_batch_candidate_request(
                manifest_path,
                candidate=candidate,
            )
            request_validated = True
            selection = _load_analog_four_patch_batch_candidate(
                manifest_path,
                candidate=candidate,
            )
    except (KeyboardInterrupt, SystemExit) as exc:
        _record_batch_read_failure(
            started_at=started_at,
            manifest_name=manifest_name,
            candidate=candidate_label,
            operation_id=operation_id,
            error_code="interrupted",
            exc=exc,
        )
        raise
    except OSError as exc:
        _record_batch_read_failure(
            started_at=started_at,
            manifest_name=manifest_name,
            candidate=candidate_label,
            operation_id=operation_id,
            error_code="input_read_failed",
            exc=exc,
        )
        raise
    except TypeError as exc:
        _record_batch_read_failure(
            started_at=started_at,
            manifest_name=manifest_name,
            candidate=candidate_label,
            operation_id=operation_id,
            error_code="validation",
            exc=exc,
        )
        raise
    except ValueError as exc:
        _record_batch_read_failure(
            started_at=started_at,
            manifest_name=manifest_name,
            candidate=candidate_label,
            operation_id=operation_id,
            error_code="artifact_validation" if request_validated else "validation",
            exc=exc,
        )
        raise

    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_a4_patch_batch_read(duration_ms)
    _logger.info(
        "Analog Four patch batch candidate verified",
        extra={
            "op_id": operation_id,
            "operation": "a4_patch_batch_candidate_read",
            "outcome": "verified",
            "manifest_name": manifest_name,
            "candidate": candidate,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )
    return selection


def _record_batch_read_failure(
    *,
    started_at: float,
    manifest_name: str,
    candidate: int | None,
    operation_id: str,
    error_code: AnalogFourPatchBatchReadErrorCode,
    exc: BaseException,
) -> None:
    duration_ms = (time.perf_counter() - started_at) * 1000.0
    metrics = get_metrics()
    metrics.record_a4_patch_batch_read(duration_ms, error_code=error_code)
    _logger.warning(
        "Analog Four patch batch candidate verification failed",
        extra={
            "op_id": operation_id,
            "operation": "a4_patch_batch_candidate_read",
            "outcome": "failed",
            "manifest_name": manifest_name,
            "candidate": candidate,
            "error_code": error_code,
            "error_type": type(exc).__name__,
            "fingerprint": _BATCH_READ_FAILURE_FINGERPRINT,
            "duration_ms": duration_ms,
            "metrics_summary": metrics.format_summary(),
        },
    )


def _validate_batch_candidate_request(
    manifest_path: object,
    *,
    candidate: object,
) -> tuple[Path, int]:
    if not isinstance(manifest_path, Path):
        raise TypeError("manifest_path must be a Path")
    if isinstance(candidate, bool) or not isinstance(candidate, int):
        raise TypeError("candidate must be an int")
    if not ANALOG_FOUR_PATCH_CANDIDATE_MIN <= candidate <= ANALOG_FOUR_PATCH_CANDIDATE_MAX:
        raise ValueError(
            "candidate must be in "
            f"{ANALOG_FOUR_PATCH_CANDIDATE_MIN}..{ANALOG_FOUR_PATCH_CANDIDATE_MAX}"
        )
    return manifest_path, candidate


def _batch_candidate_manifest_name(manifest_path: object) -> str:
    return manifest_path.name if isinstance(manifest_path, Path) else "<invalid>"


def _batch_candidate_number(candidate: object) -> int | None:
    if isinstance(candidate, int) and not isinstance(candidate, bool):
        return candidate
    return None


def _load_analog_four_patch_batch_candidate(
    manifest_path: Path,
    *,
    candidate: int,
) -> AnalogFourPatchBatchSelection:
    _validate_batch_candidate_request(manifest_path, candidate=candidate)

    resolved_manifest = manifest_path.resolve()
    manifest_bytes = resolved_manifest.read_bytes()
    manifest = _json_object(manifest_bytes, label="batch manifest")
    _expect_equal(manifest, "schema_version", BATCH_SCHEMA_VERSION, "batch manifest")
    generation_id = _string(manifest, "generation_id", "batch manifest")
    track = _batch_reader_bounded_int(
        manifest,
        "track",
        "batch manifest",
        low=ANALOG_FOUR_TRACK_MIN,
        high=ANALOG_FOUR_TRACK_MAX,
    )
    audio_source = _object_field(manifest, "audio_source", "batch manifest")
    audio_filename = _safe_filename(
        audio_source,
        "filename",
        "batch manifest audio source",
    )
    audio_sha256 = _sha256_field(audio_source, "sha256", "batch manifest audio source")
    source_kit = _object_field(manifest, "source_kit", "batch manifest")
    source_kit_filename = _safe_filename(
        source_kit,
        "filename",
        "batch manifest source kit",
    )
    source_kit_sha256 = _sha256_field(
        source_kit,
        "sha256",
        "batch manifest source kit",
    )
    _sha256_field(manifest, "feature_report_hash", "batch manifest")
    genome = _object_field(manifest, "genome", "batch manifest")
    genome_sha256 = _sha256_field(manifest, "genome_sha256", "batch manifest")
    if analog_four_patch_batch_payload_sha256(genome) != genome_sha256:
        raise ValueError("genome SHA-256 does not match the batch manifest")
    candidates = _object_list(manifest, "candidates", "batch manifest")
    candidate_count = _batch_reader_bounded_int(
        manifest,
        "candidate_count",
        "batch manifest",
        low=ANALOG_FOUR_PATCH_CANDIDATE_MIN,
        high=ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    )
    if candidate_count != len(candidates):
        raise ValueError("batch manifest candidate_count does not match candidates")
    _verify_manifest_coverage_counts(manifest, candidates)
    _verify_manifest_genome(
        genome,
        track=track,
        candidate_count=candidate_count,
        audio_sha256=audio_sha256,
    )

    selected = _select_candidate(candidates, candidate)
    sysex_path = _batch_artifact_path(
        resolved_manifest,
        selected,
        key="sysex_filename",
        artifact="SysEx",
    )
    sysex_sha256 = _batch_reader_sha256(sysex_path.read_bytes())
    if sysex_sha256 != _sha256_field(selected, "sysex_sha256", "manifest candidate"):
        raise ValueError("candidate SysEx SHA-256 does not match the batch manifest")
    sidecar_path = _batch_artifact_path(
        resolved_manifest,
        selected,
        key="sidecar_filename",
        artifact="sidecar",
    )
    sidecar_bytes = sidecar_path.read_bytes()
    sidecar_sha256 = _batch_reader_sha256(sidecar_bytes)
    if sidecar_sha256 != _sha256_field(selected, "sidecar_sha256", "manifest candidate"):
        raise ValueError("candidate sidecar SHA-256 does not match the batch manifest")

    sidecar = _json_object(sidecar_bytes, label="candidate sidecar")
    _expect_equal(sidecar, "schema_version", CANDIDATE_SCHEMA_VERSION, "candidate sidecar")
    _expect_equal(sidecar, "generation_id", generation_id, "candidate sidecar")
    _expect_equal(
        _object_field(sidecar, "audio_source", "candidate sidecar"),
        "filename",
        audio_filename,
        "candidate audio source",
    )
    _expect_equal(
        _object_field(sidecar, "source_kit", "candidate sidecar"),
        "filename",
        source_kit_filename,
        "candidate source kit",
    )
    _expect_equal(
        _object_field(sidecar, "audio_features", "candidate sidecar"),
        "audio_sha256",
        audio_sha256,
        "candidate audio features",
    )
    dna = _object_field(sidecar, "candidate_dna", "candidate sidecar")
    plan_payload = _object_field(sidecar, "dynamic_send_plan", "candidate sidecar")
    hardware_export = _object_field(sidecar, "hardware_export", "candidate sidecar")
    hashes = _object_field(sidecar, "hashes", "candidate sidecar")
    _verify_payload_hash(dna, hashes, "candidate_dna_sha256", "candidate DNA")
    _verify_payload_hash(plan_payload, hashes, "send_plan_sha256", "send plan")
    _expect_equal(hashes, "audio_sha256", audio_sha256, "candidate hashes")
    _expect_equal(hashes, "source_kit_sha256", source_kit_sha256, "candidate hashes")
    _expect_equal(hashes, "genome_sha256", genome_sha256, "candidate hashes")
    _expect_equal(hashes, "sysex_sha256", sysex_sha256, "candidate hashes")
    _expect_equal(
        hardware_export,
        "sysex_filename",
        sysex_path.name,
        "candidate hardware export",
    )
    _expect_equal(plan_payload, "source_hash", audio_sha256, "send plan")

    label = _string(selected, "label", "manifest candidate")
    _expect_equal(selected, "column", candidate, "manifest candidate")
    _expect_equal(dna, "column", candidate, "candidate DNA")
    _expect_equal(dna, "label", label, "candidate DNA")
    _expect_equal(plan_payload, "version", ANALOG_FOUR_PATCH_SEND_PLAN_VERSION, "send plan")
    _expect_equal(plan_payload, "selected_track", track, "send plan")
    _expect_equal(plan_payload, "selected_candidate", candidate, "send plan")
    _expect_equal(plan_payload, "selected_label", label, "send plan")

    plan = _parse_plan(plan_payload, dna=dna, track=track, candidate=candidate, label=label)
    genome_candidate = _select_candidate(
        _object_list(genome, "candidates", "batch manifest genome"),
        candidate,
        label="batch manifest genome",
    )
    if dna != genome_candidate:
        raise ValueError("candidate DNA does not match the batch manifest genome")
    _verify_coverage(selected, sidecar, plan.summary)
    return AnalogFourPatchBatchSelection(
        manifest_path=resolved_manifest,
        sidecar_path=sidecar_path,
        generation_id=generation_id,
        audio_sha256=audio_sha256,
        manifest_sha256=_batch_reader_sha256(manifest_bytes),
        sidecar_sha256=sidecar_sha256,
        plan=plan,
    )


def _parse_plan(
    payload: Mapping[str, object],
    *,
    dna: Mapping[str, object],
    track: int,
    candidate: int,
    label: str,
) -> StoredAnalogFourPatchSendPlan:
    send_events = tuple(
        _parse_send_event(row, track=track)
        for row in _object_list(payload, "send_events", "send plan")
    )
    manual_events = tuple(
        _parse_manual_event(row, track=track)
        for row in _object_list(payload, "manual_events", "send plan")
    )
    summary = _parse_summary(_object_field(payload, "summary", "send plan"))
    if summary.total_rows != len(send_events) + len(manual_events):
        raise ValueError("send-plan total_rows does not match stored events")
    if summary.sendable_count != len(send_events) or summary.manual_count != len(manual_events):
        raise ValueError("send-plan summary counts do not match stored events")
    if summary.cc_event_count != sum(
        event.message_kind == MIDI_EVENT_KIND_CC for event in send_events
    ):
        raise ValueError("send-plan CC count does not match stored events")
    if summary.nrpn_event_count != sum(
        event.message_kind == MIDI_EVENT_KIND_NRPN for event in send_events
    ):
        raise ValueError("send-plan NRPN count does not match stored events")
    expected_messages = validate_cc_nrpn_event_plan(send_events)
    if summary.transport_message_count != expected_messages:
        raise ValueError("send-plan transport message count does not match stored events")
    if any(
        tuple(event.sequence for event in events)
        != tuple(sorted(event.sequence for event in events))
        for events in (send_events, manual_events)
    ):
        raise ValueError("send-plan event sequences are not ordered")
    _verify_plan_against_candidate_dna(
        dna,
        track=track,
        send_events=send_events,
        manual_events=manual_events,
    )
    return StoredAnalogFourPatchSendPlan(
        selected_track=track,
        selected_candidate=candidate,
        selected_label=label,
        source_hash=_sha256_field(payload, "source_hash", "send plan"),
        send_events=send_events,
        manual_events=manual_events,
        summary=summary,
    )


def _parse_send_event(row: Mapping[str, object], *, track: int) -> AnalogFourPatchSendEvent:
    message_kind = _string(row, "message_kind", "send event")
    if message_kind not in _VALID_MESSAGE_KINDS:
        raise ValueError(f"send event has unsupported message_kind {message_kind!r}")
    typed_message_kind = message_kind
    event_track = _batch_reader_bounded_int(
        row,
        "track",
        "send event",
        low=ANALOG_FOUR_TRACK_MIN,
        high=ANALOG_FOUR_TRACK_MAX,
    )
    if (
        event_track != track
        or _batch_reader_bounded_int(
            row,
            "channel",
            "send event",
            low=ANALOG_FOUR_TRACK_MIN - 1,
            high=ANALOG_FOUR_TRACK_MAX - 1,
        )
        != track - 1
    ):
        raise ValueError("send event track/channel does not match the selected track")
    cc_msb = _optional_midi_int(row, "cc_msb", "send event")
    cc_lsb = _optional_midi_int(row, "cc_lsb", "send event")
    nrpn_address = _optional_nrpn_address(row, "nrpn_address", "send event")
    transport_status = _string(row, "transport_status", "send event")
    if transport_status != _SEND_STATUS_BY_KIND[typed_message_kind]:
        raise ValueError("send event transport_status does not match message_kind")
    event = AnalogFourPatchSendEvent(
        sequence=_batch_reader_positive_int(row, "sequence", "send event"),
        track=event_track,
        channel=track - 1,
        parameter=_string(row, "parameter", "send event"),
        section=_string(row, "section", "send event"),
        encoder=_string(row, "encoder", "send event"),
        screen_value=_string(row, "screen_value", "send event"),
        midi_value=_batch_reader_bounded_int(
            row,
            "midi_value",
            "send event",
            low=A4_MIDI_MIN,
            high=A4_MIDI_MAX,
        ),
        message_kind=typed_message_kind,
        cc_msb=cc_msb,
        cc_lsb=cc_lsb,
        nrpn_address=nrpn_address,
        transport_status=transport_status,
        dial_direction=_string(row, "dial_direction", "send event"),
        rationale=_string(row, "rationale", "send event"),
        confidence=_string(row, "confidence", "send event"),
    )
    validate_cc_nrpn_event(event)
    return event


def _parse_manual_event(row: Mapping[str, object], *, track: int) -> AnalogFourPatchManualEvent:
    event_track = _batch_reader_bounded_int(
        row,
        "track",
        "manual event",
        low=ANALOG_FOUR_TRACK_MIN,
        high=ANALOG_FOUR_TRACK_MAX,
    )
    if event_track != track:
        raise ValueError("manual event track does not match the selected track")
    transport_status = _string(row, "transport_status", "manual event")
    skip_code_raw = _string(row, "skip_code", "manual event")
    if skip_code_raw not in (
        MIDI_EVENT_SKIP_NOT_READY,
        MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED,
    ):
        raise ValueError("manual event has an unknown skip_code")
    skip_code = skip_code_raw
    skip_reason = _string(row, "skip_reason", "manual event")
    if (
        transport_status not in _MANUAL_TRANSPORT_STATUSES
        and transport_status != TRANSPORT_CC_READY
    ):
        raise ValueError("manual event has sendable or unknown transport_status")
    if skip_code == MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED and transport_status != TRANSPORT_CC_READY:
        raise ValueError("paired-CC manual event must use CC-ready transport_status")
    return AnalogFourPatchManualEvent(
        sequence=_batch_reader_positive_int(row, "sequence", "manual event"),
        track=event_track,
        parameter=_string(row, "parameter", "manual event"),
        section=_string(row, "section", "manual event"),
        encoder=_string(row, "encoder", "manual event"),
        screen_value=_string(row, "screen_value", "manual event"),
        transport_status=transport_status,
        skip_code=skip_code,
        skip_reason=skip_reason,
        dial_direction=_string(row, "dial_direction", "manual event"),
        rationale=_string(row, "rationale", "manual event"),
        confidence=_string(row, "confidence", "manual event"),
    )


def _parse_summary(row: Mapping[str, object]) -> AnalogFourPatchSendSummary:
    return AnalogFourPatchSendSummary(
        total_rows=_nonnegative_int(row, "total_rows", "send-plan summary"),
        sendable_count=_nonnegative_int(row, "sendable_count", "send-plan summary"),
        manual_count=_nonnegative_int(row, "manual_count", "send-plan summary"),
        cc_event_count=_nonnegative_int(row, "cc_event_count", "send-plan summary"),
        nrpn_event_count=_nonnegative_int(row, "nrpn_event_count", "send-plan summary"),
        transport_message_count=_nonnegative_int(
            row, "transport_message_count", "send-plan summary"
        ),
        ready_percentage=_batch_reader_bounded_int(
            row, "ready_percentage", "send-plan summary", low=0, high=100
        ),
        live_dial_path=_string(row, "live_dial_path", "send-plan summary"),
        blocking_reason=_string(row, "blocking_reason", "send-plan summary"),
    )


def _verify_plan_against_candidate_dna(
    dna: Mapping[str, object],
    *,
    track: int,
    send_events: tuple[AnalogFourPatchSendEvent, ...],
    manual_events: tuple[AnalogFourPatchManualEvent, ...],
) -> None:
    genes = _object_list(dna, "genes", "candidate DNA")
    events = (*send_events, *manual_events)
    if len(genes) != len(events):
        raise ValueError("candidate DNA gene count does not match stored send-plan events")
    events_by_sequence = {event.sequence: event for event in events}
    if len(events_by_sequence) != len(events):
        raise ValueError("send-plan event sequences must be unique")

    for sequence, gene in enumerate(genes, start=1):
        event = events_by_sequence.get(sequence)
        if event is None:
            raise ValueError("send-plan event sequences do not cover candidate DNA order")
        _expect_equal(gene, "track", track, "candidate DNA gene")
        value = _object_field(gene, "value", "candidate DNA gene")
        for key, expected in (
            ("parameter", event.parameter),
            ("section", event.section),
            ("encoder", event.encoder),
            ("screen_value", event.screen_value),
            ("transport_status", event.transport_status),
            ("dial_direction", event.dial_direction),
        ):
            _expect_equal(value, key, expected, "candidate DNA gene value")
        _expect_equal(gene, "rationale", event.rationale, "candidate DNA gene")
        _expect_equal(gene, "confidence", event.confidence, "candidate DNA gene")

        if isinstance(event, AnalogFourPatchSendEvent):
            _expect_equal(value, "midi_value", event.midi_value, "candidate DNA gene value")
            if event.message_kind == MIDI_EVENT_KIND_CC:
                _expect_equal(value, "cc_msb", event.cc_msb, "candidate DNA gene value")
                _expect_equal(value, "cc_lsb", event.cc_lsb, "candidate DNA gene value")
            else:
                expected_nrpn = list(event.nrpn_address) if event.nrpn_address is not None else None
                _expect_equal(value, "nrpn_address", expected_nrpn, "candidate DNA gene value")
            _verify_canonical_transport(event)
        else:
            expected_skip_code = (
                MIDI_EVENT_SKIP_PAIRED_CC_UNVERIFIED
                if value.get("cc_msb") is not None and value.get("cc_lsb") is not None
                else MIDI_EVENT_SKIP_NOT_READY
            )
            if event.skip_code != expected_skip_code:
                raise ValueError(
                    "manual event skip_code does not match candidate DNA transport shape"
                )


def _verify_canonical_transport(event: AnalogFourPatchSendEvent) -> None:
    if event.message_kind == MIDI_EVENT_KIND_CC:
        mapping = ANALOG_FOUR_MANUAL_CC.get(event.parameter)
        if mapping is None or mapping.cc_msb is None:
            raise ValueError(f"send event parameter {event.parameter!r} has no canonical A4 CC")
        if mapping.cc_lsb is not None:
            raise ValueError(
                f"send event parameter {event.parameter!r} requires unverified paired-CC transport"
            )
        if (event.cc_msb, event.cc_lsb) != (mapping.cc_msb, mapping.cc_lsb):
            raise ValueError("send event CC address does not match the canonical A4 parameter map")
        return

    mapping = ANALOG_FOUR_SYNTH_TRACK_NRPN.get(event.parameter)
    if mapping is None or mapping.nrpn_msb is None or mapping.nrpn_lsb is None:
        raise ValueError(f"send event parameter {event.parameter!r} has no canonical A4 NRPN")
    if event.nrpn_address != (mapping.nrpn_msb, mapping.nrpn_lsb):
        raise ValueError("send event NRPN address does not match the canonical A4 parameter map")


def _verify_coverage(
    candidate: Mapping[str, object],
    sidecar: Mapping[str, object],
    summary: AnalogFourPatchSendSummary,
) -> None:
    manifest_counts = _object_field(candidate, "coverage_counts", "manifest candidate")
    sidecar_counts = _object_field(sidecar, "coverage_counts", "candidate sidecar")
    hardware_rows = _object_list(sidecar, "hardware_applied_rows", "candidate sidecar")
    deferred_rows = _object_list(sidecar, "deferred_rows", "candidate sidecar")
    for key, expected in (
        ("dna_row_count", summary.total_rows),
        ("sysex_encoded_row_count", len(hardware_rows)),
        ("deferred_row_count", len(deferred_rows)),
        ("sendable_row_count", summary.sendable_count),
        ("manual_row_count", summary.manual_count),
    ):
        if _nonnegative_int(manifest_counts, key, "manifest coverage") != expected:
            raise ValueError(f"manifest coverage {key} does not match the send plan")
        if _nonnegative_int(sidecar_counts, key, "sidecar coverage") != expected:
            raise ValueError(f"sidecar coverage {key} does not match the send plan")
    if len(hardware_rows) + len(deferred_rows) != summary.total_rows:
        raise ValueError("candidate encoded and deferred rows do not cover the complete DNA")


def _verify_manifest_coverage_counts(
    manifest: Mapping[str, object],
    candidates: list[Mapping[str, object]],
) -> None:
    aggregate = _object_field(manifest, "coverage_counts", "batch manifest")
    for key in (
        "dna_row_count",
        "sysex_encoded_row_count",
        "deferred_row_count",
        "sendable_row_count",
        "manual_row_count",
    ):
        candidate_total = sum(
            _nonnegative_int(
                _object_field(candidate, "coverage_counts", "manifest candidate"),
                key,
                "manifest candidate coverage",
            )
            for candidate in candidates
        )
        if _nonnegative_int(aggregate, key, "manifest aggregate coverage") != candidate_total:
            raise ValueError(f"manifest aggregate coverage {key} does not match candidates")


def _select_candidate(
    candidates: list[Mapping[str, object]],
    candidate: int,
    *,
    label: str = "batch manifest",
) -> Mapping[str, object]:
    matches = [row for row in candidates if row.get("column") == candidate]
    if len(matches) != 1:
        raise ValueError(f"{label} does not contain exactly one candidate {candidate}")
    return matches[0]


def _verify_manifest_genome(
    genome: Mapping[str, object],
    *,
    track: int,
    candidate_count: int,
    audio_sha256: str,
) -> None:
    _expect_equal(genome, "selected_track", track, "batch manifest genome")
    _expect_equal(genome, "source_hash", audio_sha256, "batch manifest genome")
    _expect_equal(genome, "candidate_count", candidate_count, "batch manifest genome")
    genome_candidates = _object_list(genome, "candidates", "batch manifest genome")
    if len(genome_candidates) != candidate_count:
        raise ValueError("batch manifest genome candidate_count does not match candidates")


def _batch_artifact_path(
    manifest_path: Path,
    row: Mapping[str, object],
    *,
    key: str,
    artifact: str,
) -> Path:
    filename = _safe_filename(row, key, "manifest candidate")
    path = (manifest_path.parent / filename).resolve()
    if path.parent != manifest_path.parent:
        raise ValueError(f"manifest candidate {artifact} escapes the batch directory")
    return path


def _json_object(data: bytes, *, label: str) -> Mapping[str, object]:
    return decode_analog_four_patch_batch_json(data, label=label)


def _as_object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    payload = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in payload):
        raise ValueError(f"{label} must be a JSON object")
    return cast(Mapping[str, object], payload)


def _object_field(row: Mapping[str, object], key: str, label: str) -> Mapping[str, object]:
    return _as_object(row.get(key), f"{label}.{key}")


def _object_list(row: Mapping[str, object], key: str, label: str) -> list[Mapping[str, object]]:
    value = row.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{label}.{key} must be a JSON array")
    return [_as_object(item, f"{label}.{key} item") for item in cast(list[object], value)]


def _string(row: Mapping[str, object], key: str, label: str) -> str:
    value = row.get(key)
    if not isinstance(value, str) or value == "":
        raise ValueError(f"{label}.{key} must be a non-empty string")
    return value


def _expect_equal(row: Mapping[str, object], key: str, expected: object, label: str) -> None:
    if row.get(key) != expected:
        raise ValueError(f"{label}.{key} does not match the committed batch")


def _batch_reader_bounded_int(
    row: Mapping[str, object], key: str, label: str, *, low: int, high: int
) -> int:
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
        raise ValueError(f"{label}.{key} must be an integer in [{low}, {high}]")
    return value


def _batch_reader_positive_int(row: Mapping[str, object], key: str, label: str) -> int:
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 1:
        raise ValueError(f"{label}.{key} must be a positive integer")
    return value


def _nonnegative_int(row: Mapping[str, object], key: str, label: str) -> int:
    value = row.get(key)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label}.{key} must be a nonnegative integer")
    return value


def _optional_midi_int(row: Mapping[str, object], key: str, label: str) -> int | None:
    value = row.get(key)
    if value is None:
        return None
    return _batch_reader_bounded_int(row, key, label, low=0, high=127)


def _optional_nrpn_address(
    row: Mapping[str, object], key: str, label: str
) -> tuple[int, int] | None:
    value = row.get(key)
    if value is None:
        return None
    if not isinstance(value, list):
        raise ValueError(f"{label}.{key} must be two MIDI bytes or null")
    values = cast(list[object], value)
    if len(values) != 2:
        raise ValueError(f"{label}.{key} must be two MIDI bytes or null")
    first, second = values
    if (
        not isinstance(first, int)
        or isinstance(first, bool)
        or not isinstance(second, int)
        or isinstance(second, bool)
        or not 0 <= first <= 127
        or not 0 <= second <= 127
    ):
        raise ValueError(f"{label}.{key} must be two MIDI bytes or null")
    return (first, second)


def _safe_filename(row: Mapping[str, object], key: str, label: str) -> str:
    value = _string(row, key, label)
    if Path(value).name != value or Path(value).is_absolute():
        raise ValueError(f"{label}.{key} must be a plain filename")
    return value


def _batch_reader_sha256(data: bytes) -> str:
    return analog_four_patch_batch_sha256(data)


def _sha256_field(row: Mapping[str, object], key: str, label: str) -> str:
    value = _string(row, key, label)
    return validate_analog_four_patch_batch_sha256(value, label=f"{label}.{key}")


def _verify_payload_hash(
    payload: Mapping[str, object],
    hashes: Mapping[str, object],
    key: str,
    label: str,
) -> None:
    if analog_four_patch_batch_payload_sha256(payload) != _sha256_field(
        hashes, key, "candidate hashes"
    ):
        raise ValueError(f"{label} SHA-256 does not match the candidate sidecar")


__all__ = [
    "AnalogFourPatchBatchSelection",
    "StoredAnalogFourPatchSendPlan",
    "load_analog_four_patch_batch_candidate",
]
