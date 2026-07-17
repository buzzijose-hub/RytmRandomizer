"""Verified reader for immutable Analog Four audio-patch batch candidates."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

from ...style_analysis.analog_four_patch_send_plan import (
    ANALOG_FOUR_PATCH_SEND_KIND_CC,
    ANALOG_FOUR_PATCH_SEND_KIND_NRPN,
    ANALOG_FOUR_PATCH_SEND_PLAN_VERSION,
    AnalogFourPatchManualEvent,
    AnalogFourPatchSendEvent,
    AnalogFourPatchSendSummary,
)
from .analog_four_patch_batch import BATCH_SCHEMA_VERSION, CANDIDATE_SCHEMA_VERSION

_SHA256_LENGTH: Final[int] = 64
_VALID_MESSAGE_KINDS: Final[frozenset[str]] = frozenset(
    {ANALOG_FOUR_PATCH_SEND_KIND_CC, ANALOG_FOUR_PATCH_SEND_KIND_NRPN}
)


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

    if not isinstance(manifest_path, Path):
        raise TypeError("manifest_path must be a Path")
    if not isinstance(candidate, int):
        raise TypeError("candidate must be an int")

    resolved_manifest = manifest_path.resolve()
    manifest_bytes = resolved_manifest.read_bytes()
    manifest = _json_object(manifest_bytes, label="batch manifest")
    _expect_equal(manifest, "schema_version", BATCH_SCHEMA_VERSION, "batch manifest")
    generation_id = _string(manifest, "generation_id", "batch manifest")
    track = _batch_reader_bounded_int(manifest, "track", "batch manifest", low=1, high=4)
    audio_source = _object_field(manifest, "audio_source", "batch manifest")
    audio_sha256 = _sha256_field(audio_source, "sha256", "batch manifest audio source")
    feature_report_hash = _sha256_field(manifest, "feature_report_hash", "batch manifest")
    candidates = _object_list(manifest, "candidates", "batch manifest")
    if _batch_reader_bounded_int(
        manifest, "candidate_count", "batch manifest", low=1, high=4
    ) != len(candidates):
        raise ValueError("batch manifest candidate_count does not match candidates")

    selected = _select_candidate(candidates, candidate)
    sidecar_name = _safe_filename(selected, "sidecar_filename", "manifest candidate")
    sidecar_path = (resolved_manifest.parent / sidecar_name).resolve()
    if sidecar_path.parent != resolved_manifest.parent:  # pragma: no cover - symlink defense
        raise ValueError("manifest candidate sidecar escapes the batch directory")
    sidecar_bytes = sidecar_path.read_bytes()
    sidecar_sha256 = _batch_reader_sha256(sidecar_bytes)
    if sidecar_sha256 != _sha256_field(selected, "sidecar_sha256", "manifest candidate"):
        raise ValueError("candidate sidecar SHA-256 does not match the batch manifest")

    sidecar = _json_object(sidecar_bytes, label="candidate sidecar")
    _expect_equal(sidecar, "schema_version", CANDIDATE_SCHEMA_VERSION, "candidate sidecar")
    _expect_equal(sidecar, "generation_id", generation_id, "candidate sidecar")
    dna = _object_field(sidecar, "candidate_dna", "candidate sidecar")
    plan_payload = _object_field(sidecar, "dynamic_send_plan", "candidate sidecar")
    hashes = _object_field(sidecar, "hashes", "candidate sidecar")
    _verify_payload_hash(dna, hashes, "candidate_dna_sha256", "candidate DNA")
    _verify_payload_hash(plan_payload, hashes, "send_plan_sha256", "send plan")
    _expect_equal(hashes, "audio_sha256", audio_sha256, "candidate hashes")
    _expect_equal(plan_payload, "source_hash", feature_report_hash, "send plan")

    label = _string(selected, "label", "manifest candidate")
    _expect_equal(selected, "column", candidate, "manifest candidate")
    _expect_equal(dna, "column", candidate, "candidate DNA")
    _expect_equal(dna, "label", label, "candidate DNA")
    _expect_equal(plan_payload, "version", ANALOG_FOUR_PATCH_SEND_PLAN_VERSION, "send plan")
    _expect_equal(plan_payload, "selected_track", track, "send plan")
    _expect_equal(plan_payload, "selected_candidate", candidate, "send plan")
    _expect_equal(plan_payload, "selected_label", label, "send plan")

    plan = _parse_plan(plan_payload, track=track, candidate=candidate, label=label)
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
        event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC for event in send_events
    ):
        raise ValueError("send-plan CC count does not match stored events")
    if summary.nrpn_event_count != sum(
        event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_NRPN for event in send_events
    ):
        raise ValueError("send-plan NRPN count does not match stored events")
    expected_messages = sum(
        1 if event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC else 3 for event in send_events
    )
    if summary.transport_message_count != expected_messages:
        raise ValueError("send-plan transport message count does not match stored events")
    if tuple(event.sequence for event in (*send_events, *manual_events)) != tuple(
        sorted(event.sequence for event in (*send_events, *manual_events))
    ):
        raise ValueError("send-plan event sequences are not ordered")
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
    event_track = _batch_reader_bounded_int(row, "track", "send event", low=1, high=4)
    if (
        event_track != track
        or _batch_reader_bounded_int(row, "channel", "send event", low=0, high=3) != track - 1
    ):
        raise ValueError("send event track/channel does not match the selected track")
    cc_msb = _optional_midi_int(row, "cc_msb", "send event")
    cc_lsb = _optional_midi_int(row, "cc_lsb", "send event")
    nrpn_address = _optional_nrpn_address(row, "nrpn_address", "send event")
    if message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC and cc_msb is None:
        raise ValueError("CC send event is missing cc_msb")
    if message_kind == ANALOG_FOUR_PATCH_SEND_KIND_NRPN and nrpn_address is None:
        raise ValueError("NRPN send event is missing nrpn_address")
    return AnalogFourPatchSendEvent(
        sequence=_batch_reader_positive_int(row, "sequence", "send event"),
        track=event_track,
        channel=track - 1,
        parameter=_string(row, "parameter", "send event"),
        section=_string(row, "section", "send event"),
        encoder=_string(row, "encoder", "send event"),
        screen_value=_string(row, "screen_value", "send event"),
        midi_value=_batch_reader_bounded_int(row, "midi_value", "send event", low=0, high=127),
        message_kind=message_kind,
        cc_msb=cc_msb,
        cc_lsb=cc_lsb,
        nrpn_address=nrpn_address,
        transport_status=_string(row, "transport_status", "send event"),
        dial_direction=_string(row, "dial_direction", "send event"),
        rationale=_string(row, "rationale", "send event"),
        confidence=_string(row, "confidence", "send event"),
    )


def _parse_manual_event(row: Mapping[str, object], *, track: int) -> AnalogFourPatchManualEvent:
    event_track = _batch_reader_bounded_int(row, "track", "manual event", low=1, high=4)
    if event_track != track:
        raise ValueError("manual event track does not match the selected track")
    return AnalogFourPatchManualEvent(
        sequence=_batch_reader_positive_int(row, "sequence", "manual event"),
        track=event_track,
        parameter=_string(row, "parameter", "manual event"),
        section=_string(row, "section", "manual event"),
        encoder=_string(row, "encoder", "manual event"),
        screen_value=_string(row, "screen_value", "manual event"),
        transport_status=_string(row, "transport_status", "manual event"),
        skip_reason=_string(row, "skip_reason", "manual event"),
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


def _verify_coverage(
    candidate: Mapping[str, object],
    sidecar: Mapping[str, object],
    summary: AnalogFourPatchSendSummary,
) -> None:
    manifest_counts = _object_field(candidate, "coverage_counts", "manifest candidate")
    sidecar_counts = _object_field(sidecar, "coverage_counts", "candidate sidecar")
    for key, expected in (
        ("dna_row_count", summary.total_rows),
        ("sendable_row_count", summary.sendable_count),
        ("manual_row_count", summary.manual_count),
    ):
        if _nonnegative_int(manifest_counts, key, "manifest coverage") != expected:
            raise ValueError(f"manifest coverage {key} does not match the send plan")
        if _nonnegative_int(sidecar_counts, key, "sidecar coverage") != expected:
            raise ValueError(f"sidecar coverage {key} does not match the send plan")


def _select_candidate(
    candidates: list[Mapping[str, object]], candidate: int
) -> Mapping[str, object]:
    matches = [row for row in candidates if row.get("column") == candidate]
    if len(matches) != 1:
        raise ValueError(f"batch manifest does not contain exactly one candidate {candidate}")
    return matches[0]


def _json_object(data: bytes, *, label: str) -> Mapping[str, object]:
    try:
        decoded = cast(object, json.loads(data.decode("utf-8")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not valid UTF-8 JSON") from exc
    return _as_object(decoded, label)


def _as_object(value: object, label: str) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{label} must be a JSON object")
    return cast(Mapping[str, object], value)


def _object_field(row: Mapping[str, object], key: str, label: str) -> Mapping[str, object]:
    return _as_object(row.get(key), f"{label}.{key}")


def _object_list(row: Mapping[str, object], key: str, label: str) -> list[Mapping[str, object]]:
    value = row.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{label}.{key} must be a JSON array")
    return [_as_object(item, f"{label}.{key} item") for item in value]


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
    if (
        not isinstance(value, list)
        or len(value) != 2
        or any(not isinstance(part, int) or isinstance(part, bool) for part in value)
        or any(part < 0 or part > 127 for part in value)
    ):
        raise ValueError(f"{label}.{key} must be two MIDI bytes or null")
    return (value[0], value[1])


def _safe_filename(row: Mapping[str, object], key: str, label: str) -> str:
    value = _string(row, key, label)
    if Path(value).name != value or Path(value).is_absolute():
        raise ValueError(f"{label}.{key} must be a plain filename")
    return value


def _batch_reader_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_field(row: Mapping[str, object], key: str, label: str) -> str:
    value = _string(row, key, label)
    if len(value) != _SHA256_LENGTH or any(char not in "0123456789abcdef" for char in value):
        raise ValueError(f"{label}.{key} must be a lowercase SHA-256 digest")
    return value


def _verify_payload_hash(
    payload: Mapping[str, object],
    hashes: Mapping[str, object],
    key: str,
    label: str,
) -> None:
    encoded = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if _batch_reader_sha256(encoded) != _sha256_field(hashes, key, "candidate hashes"):
        raise ValueError(f"{label} SHA-256 does not match the candidate sidecar")


__all__ = [
    "AnalogFourPatchBatchSelection",
    "StoredAnalogFourPatchSendPlan",
    "load_analog_four_patch_batch_candidate",
]
