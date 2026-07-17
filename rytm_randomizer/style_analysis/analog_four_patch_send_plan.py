"""Passive Analog Four patch live-dial send-plan compiler.

The compiler bridges the passive audio-to-patch learning packet to an explicit
transport plan. It does not open MIDI ports, send messages, or write SysEx.
It only separates the selected patch DNA into ordered CC/NRPN events that an
armed caller may send later and any rows that still require front-panel work.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Final, TypedDict

from ..data.analog_four_display import (
    TRANSPORT_CC_READY,
    TRANSPORT_NRPN_READY,
    TRANSPORT_SCREEN_ONLY,
    TRANSPORT_SCREEN_ONLY_NRPN,
    AnalogFourPatchValue,
)
from .analog_four_patch_genome import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_FOUR_PATCH_CANDIDATE_MAX,
    ANALOG_FOUR_PATCH_CANDIDATE_MIN,
    ANALOG_FOUR_TRACK_MAX,
    ANALOG_FOUR_TRACK_MIN,
    AnalogFourPatchGene,
    AnalogFourPatchGenome,
    build_analog_four_patch_genome,
)
from .analog_four_patch_inference import build_analog_four_audio_patch_genome
from .analog_four_patch_learning import (
    AnalogFourPatchLearningPacket,
    AnalogFourPatchLearningPacketPayload,
    analog_four_patch_learning_packet_to_dict,
    build_analog_four_patch_learning_packet_from_genome,
)
from .extractor import extract_from_description
from .feature_report import FeatureReport

ANALOG_FOUR_PATCH_SEND_PLAN_VERSION: Final[str] = "analog-four-patch-send-plan-v1"
ANALOG_FOUR_PATCH_SEND_PLAN_MODE: Final[str] = "single-sound-live-dial"
ANALOG_FOUR_PATCH_SEND_KIND_CC: Final[str] = "cc"
ANALOG_FOUR_PATCH_SEND_KIND_NRPN: Final[str] = "nrpn"
ANALOG_FOUR_PATCH_SEND_PLAN_SAFETY: Final[tuple[str, ...]] = (
    "passive read-only patch send plan",
    "preview before armed send",
    "no MIDI port opened",
    "no MIDI sent",
    "no SysEx written",
    "armed app path requires --confirm-a4-patch-send-plan",
    "unknown destination labels fail closed instead of sending guessed values",
)
_SENDABLE_STATUSES: Final[frozenset[str]] = frozenset({TRANSPORT_CC_READY, TRANSPORT_NRPN_READY})
_MANUAL_STATUSES: Final[frozenset[str]] = frozenset(
    {TRANSPORT_SCREEN_ONLY_NRPN, TRANSPORT_SCREEN_ONLY}
)


@dataclass(frozen=True)
class AnalogFourPatchSendEvent:
    """One sendable A4 patch target as a concrete CC or NRPN event."""

    sequence: int
    track: int
    channel: int
    parameter: str
    section: str
    encoder: str
    screen_value: str
    midi_value: int
    message_kind: str
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_address: tuple[int, int] | None
    transport_status: str
    dial_direction: str
    rationale: str
    confidence: str


@dataclass(frozen=True)
class AnalogFourPatchManualEvent:
    """One selected patch row that is deliberately skipped by live dial-in."""

    sequence: int
    track: int
    parameter: str
    section: str
    encoder: str
    screen_value: str
    transport_status: str
    skip_reason: str
    dial_direction: str
    rationale: str
    confidence: str


@dataclass(frozen=True)
class AnalogFourPatchSendSummary:
    """Compact readiness totals for the selected patch send plan."""

    total_rows: int
    sendable_count: int
    manual_count: int
    cc_event_count: int
    nrpn_event_count: int
    transport_message_count: int
    ready_percentage: int
    live_dial_path: str
    blocking_reason: str


@dataclass(frozen=True)
class AnalogFourPatchSendPlan:
    """Transport send plan for one selected Analog Four patch candidate."""

    version: str
    device_id: str
    mode: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    source_confidence: str
    learning_packet: AnalogFourPatchLearningPacket
    send_events: tuple[AnalogFourPatchSendEvent, ...]
    manual_events: tuple[AnalogFourPatchManualEvent, ...]
    summary: AnalogFourPatchSendSummary
    ready: bool
    readiness_reason: str
    safety: tuple[str, ...]


@dataclass(frozen=True)
class AnalogFourPatchSendPlanSource:
    """Resolved A4 patch send plan plus source labels."""

    source_label: str
    source_value: str
    plan: AnalogFourPatchSendPlan


class AnalogFourPatchSendSummaryPayload(TypedDict):
    total_rows: int
    sendable_count: int
    manual_count: int
    cc_event_count: int
    nrpn_event_count: int
    transport_message_count: int
    ready_percentage: int
    live_dial_path: str
    blocking_reason: str


class AnalogFourPatchSendEventPayload(TypedDict):
    sequence: int
    track: int
    channel: int
    parameter: str
    section: str
    encoder: str
    screen_value: str
    midi_value: int
    message_kind: str
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_address: list[int] | None
    transport_status: str
    dial_direction: str
    rationale: str
    confidence: str


class AnalogFourPatchManualEventPayload(TypedDict):
    sequence: int
    track: int
    parameter: str
    section: str
    encoder: str
    screen_value: str
    transport_status: str
    skip_reason: str
    dial_direction: str
    rationale: str
    confidence: str


class AnalogFourPatchSendPlanPayload(TypedDict):
    version: str
    device_id: str
    mode: str
    selected_track: int
    selected_candidate: int
    selected_label: str
    source_hash: str
    source_confidence: str
    summary: AnalogFourPatchSendSummaryPayload
    ready: bool
    readiness_reason: str
    send_events: list[AnalogFourPatchSendEventPayload]
    manual_events: list[AnalogFourPatchManualEventPayload]
    learning_packet: AnalogFourPatchLearningPacketPayload
    safety: list[str]


def build_analog_four_patch_send_plan(
    report: FeatureReport,
    *,
    track: int = ANALOG_FOUR_TRACK_MIN,
    selected_candidate: int = ANALOG_FOUR_PATCH_CANDIDATE_MIN,
) -> AnalogFourPatchSendPlan:
    """Build a passive A4 patch send plan from a measured reference."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    genome = build_analog_four_patch_genome(report, track=track)
    return build_analog_four_patch_send_plan_from_genome(
        report,
        genome,
        selected_candidate=selected_candidate,
    )


def build_analog_four_patch_send_plan_from_genome(
    report: FeatureReport,
    genome: AnalogFourPatchGenome,
    *,
    selected_candidate: int,
) -> AnalogFourPatchSendPlan:
    """Compile an already-inferred A4 genome into a passive send plan."""

    if not isinstance(report, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    if not isinstance(genome, AnalogFourPatchGenome):
        raise TypeError("genome must be an AnalogFourPatchGenome")
    packet = build_analog_four_patch_learning_packet_from_genome(
        report,
        genome,
        selected_candidate=selected_candidate,
    )
    send_events, manual_events = _split_patch_events(packet.selected_patch.genes)
    summary = _build_send_summary(
        packet,
        send_events=send_events,
        manual_events=manual_events,
    )
    return AnalogFourPatchSendPlan(
        version=ANALOG_FOUR_PATCH_SEND_PLAN_VERSION,
        device_id=ANALOG_FOUR_DEVICE_ID,
        mode=ANALOG_FOUR_PATCH_SEND_PLAN_MODE,
        selected_track=packet.selected_track,
        selected_candidate=packet.selected_candidate,
        selected_label=packet.selected_label,
        source_hash=packet.source_hash,
        source_confidence=packet.source_confidence,
        learning_packet=packet,
        send_events=send_events,
        manual_events=manual_events,
        summary=summary,
        ready=summary.sendable_count > 0,
        readiness_reason="" if summary.sendable_count > 0 else summary.blocking_reason,
        safety=ANALOG_FOUR_PATCH_SEND_PLAN_SAFETY,
    )


def build_analog_four_patch_send_plan_from_source(
    source_flag: str,
    source_value: str,
    *,
    track: int = ANALOG_FOUR_TRACK_MIN,
    selected_candidate: int = ANALOG_FOUR_PATCH_CANDIDATE_MIN,
) -> AnalogFourPatchSendPlanSource:
    """Build a passive send plan from a description or audio source."""

    if source_flag == "--description":
        feature_report = extract_from_description(source_value)
        plan = build_analog_four_patch_send_plan(
            feature_report,
            track=track,
            selected_candidate=selected_candidate,
        )
    elif source_flag == "--audio":
        audio_genome = build_analog_four_audio_patch_genome(
            Path(source_value),
            track=track,
        )
        plan = build_analog_four_patch_send_plan_from_genome(
            audio_genome.feature_report,
            audio_genome.genome,
            selected_candidate=selected_candidate,
        )
    else:
        raise ValueError("source_flag must be --description or --audio")
    return AnalogFourPatchSendPlanSource(
        source_label=source_flag.removeprefix("--"),
        source_value=source_value,
        plan=plan,
    )


def analog_four_patch_send_plan_to_dict(
    plan: AnalogFourPatchSendPlan,
) -> AnalogFourPatchSendPlanPayload:
    """Return a stable JSON-ready representation of ``plan``."""

    if not isinstance(plan, AnalogFourPatchSendPlan):
        raise TypeError("plan must be an AnalogFourPatchSendPlan")
    return {
        "version": plan.version,
        "device_id": plan.device_id,
        "mode": plan.mode,
        "selected_track": plan.selected_track,
        "selected_candidate": plan.selected_candidate,
        "selected_label": plan.selected_label,
        "source_hash": plan.source_hash,
        "source_confidence": plan.source_confidence,
        "summary": _send_summary_payload(plan.summary),
        "ready": plan.ready,
        "readiness_reason": plan.readiness_reason,
        "send_events": [_send_event_payload(event) for event in plan.send_events],
        "manual_events": [_manual_event_payload(event) for event in plan.manual_events],
        "learning_packet": analog_four_patch_learning_packet_to_dict(plan.learning_packet),
        "safety": list(plan.safety),
    }


def _split_patch_events(
    genes: tuple[AnalogFourPatchGene, ...],
) -> tuple[tuple[AnalogFourPatchSendEvent, ...], tuple[AnalogFourPatchManualEvent, ...]]:
    send_events: list[AnalogFourPatchSendEvent] = []
    manual_events: list[AnalogFourPatchManualEvent] = []
    for sequence, gene in enumerate(genes, start=1):
        value = gene.value
        if _is_sendable_value(value):
            send_events.append(_send_event_from_gene(sequence, gene))
        else:
            manual_events.append(_manual_event_from_gene(sequence, gene))
    return tuple(send_events), tuple(manual_events)


def _is_sendable_value(value: AnalogFourPatchValue) -> bool:
    return (
        value.transport_status in _SENDABLE_STATUSES
        and value.midi_value is not None
        and (value.cc_msb is not None or value.nrpn_address is not None)
    )


def _send_event_from_gene(
    sequence: int,
    gene: AnalogFourPatchGene,
) -> AnalogFourPatchSendEvent:
    value = gene.value
    if value.midi_value is None:
        raise ValueError("sendable Analog Four patch value is missing a MIDI value")
    message_kind = _message_kind_for(value)
    return AnalogFourPatchSendEvent(
        sequence=sequence,
        track=gene.track,
        channel=gene.track - 1,
        parameter=value.parameter,
        section=value.section,
        encoder=value.encoder,
        screen_value=value.screen_value,
        midi_value=value.midi_value,
        message_kind=message_kind,
        cc_msb=value.cc_msb,
        cc_lsb=value.cc_lsb,
        nrpn_address=value.nrpn_address,
        transport_status=value.transport_status,
        dial_direction=value.dial_direction,
        rationale=gene.rationale,
        confidence=gene.confidence,
    )


def _message_kind_for(value: AnalogFourPatchValue) -> str:
    if value.cc_msb is not None:
        return ANALOG_FOUR_PATCH_SEND_KIND_CC
    if value.nrpn_address is not None:
        return ANALOG_FOUR_PATCH_SEND_KIND_NRPN
    raise ValueError("sendable Analog Four patch value has no CC or NRPN address")


def _manual_event_from_gene(
    sequence: int,
    gene: AnalogFourPatchGene,
) -> AnalogFourPatchManualEvent:
    value = gene.value
    return AnalogFourPatchManualEvent(
        sequence=sequence,
        track=gene.track,
        parameter=value.parameter,
        section=value.section,
        encoder=value.encoder,
        screen_value=value.screen_value,
        transport_status=value.transport_status,
        skip_reason=_skip_reason(value),
        dial_direction=value.dial_direction,
        rationale=gene.rationale,
        confidence=gene.confidence,
    )


def _skip_reason(value: AnalogFourPatchValue) -> str:
    if value.transport_status == TRANSPORT_SCREEN_ONLY_NRPN:
        return "NRPN destination ordinal capture pending"
    if value.transport_status in _MANUAL_STATUSES:
        return "front-panel-only value pending capture"
    if value.midi_value is None:
        return "transport value pending capture"
    return "transport address pending capture"


def _build_send_summary(
    packet: AnalogFourPatchLearningPacket,
    *,
    send_events: tuple[AnalogFourPatchSendEvent, ...],
    manual_events: tuple[AnalogFourPatchManualEvent, ...],
) -> AnalogFourPatchSendSummary:
    total_rows = len(send_events) + len(manual_events)
    sendable_count = len(send_events)
    manual_count = len(manual_events)
    return AnalogFourPatchSendSummary(
        total_rows=total_rows,
        sendable_count=sendable_count,
        manual_count=manual_count,
        cc_event_count=sum(
            1 for event in send_events if event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC
        ),
        nrpn_event_count=sum(
            1 for event in send_events if event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_NRPN
        ),
        transport_message_count=sum(_transport_message_count(event) for event in send_events),
        ready_percentage=(
            0 if total_rows == 0 else int(round(sendable_count / float(total_rows) * 100.0))
        ),
        live_dial_path=packet.live_dial_readiness.live_dial_path,
        blocking_reason=packet.live_dial_readiness.blocking_reason,
    )


def _transport_message_count(event: AnalogFourPatchSendEvent) -> int:
    if event.message_kind == ANALOG_FOUR_PATCH_SEND_KIND_CC:
        return 1
    return 3


def _send_summary_payload(
    summary: AnalogFourPatchSendSummary,
) -> AnalogFourPatchSendSummaryPayload:
    return {
        "total_rows": summary.total_rows,
        "sendable_count": summary.sendable_count,
        "manual_count": summary.manual_count,
        "cc_event_count": summary.cc_event_count,
        "nrpn_event_count": summary.nrpn_event_count,
        "transport_message_count": summary.transport_message_count,
        "ready_percentage": summary.ready_percentage,
        "live_dial_path": summary.live_dial_path,
        "blocking_reason": summary.blocking_reason,
    }


def _send_event_payload(event: AnalogFourPatchSendEvent) -> AnalogFourPatchSendEventPayload:
    return {
        "sequence": event.sequence,
        "track": event.track,
        "channel": event.channel,
        "parameter": event.parameter,
        "section": event.section,
        "encoder": event.encoder,
        "screen_value": event.screen_value,
        "midi_value": event.midi_value,
        "message_kind": event.message_kind,
        "cc_msb": event.cc_msb,
        "cc_lsb": event.cc_lsb,
        "nrpn_address": list(event.nrpn_address) if event.nrpn_address is not None else None,
        "transport_status": event.transport_status,
        "dial_direction": event.dial_direction,
        "rationale": event.rationale,
        "confidence": event.confidence,
    }


def _manual_event_payload(event: AnalogFourPatchManualEvent) -> AnalogFourPatchManualEventPayload:
    return {
        "sequence": event.sequence,
        "track": event.track,
        "parameter": event.parameter,
        "section": event.section,
        "encoder": event.encoder,
        "screen_value": event.screen_value,
        "transport_status": event.transport_status,
        "skip_reason": event.skip_reason,
        "dial_direction": event.dial_direction,
        "rationale": event.rationale,
        "confidence": event.confidence,
    }


__all__ = [
    "ANALOG_FOUR_PATCH_SEND_KIND_CC",
    "ANALOG_FOUR_PATCH_SEND_KIND_NRPN",
    "ANALOG_FOUR_PATCH_SEND_PLAN_MODE",
    "ANALOG_FOUR_PATCH_SEND_PLAN_SAFETY",
    "ANALOG_FOUR_PATCH_SEND_PLAN_VERSION",
    "ANALOG_FOUR_PATCH_CANDIDATE_MAX",
    "ANALOG_FOUR_PATCH_CANDIDATE_MIN",
    "ANALOG_FOUR_TRACK_MAX",
    "ANALOG_FOUR_TRACK_MIN",
    "AnalogFourPatchManualEvent",
    "AnalogFourPatchManualEventPayload",
    "AnalogFourPatchSendEvent",
    "AnalogFourPatchSendEventPayload",
    "AnalogFourPatchSendPlan",
    "AnalogFourPatchSendPlanPayload",
    "AnalogFourPatchSendPlanSource",
    "AnalogFourPatchSendSummary",
    "AnalogFourPatchSendSummaryPayload",
    "analog_four_patch_send_plan_to_dict",
    "build_analog_four_patch_send_plan",
    "build_analog_four_patch_send_plan_from_genome",
    "build_analog_four_patch_send_plan_from_source",
]
