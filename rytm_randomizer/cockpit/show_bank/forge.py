"""Pure paired candidate generation for Show Kit Forge.

The module composes the existing Cockpit Rytm mutation engine with the
narrow, offline-only Analog Four Filter 1 Frequency renderer.  It performs no
filesystem or MIDI I/O.  Full SysEx bytes stay in the in-process result until
an explicit retain/export action hands them to :mod:`.store`.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from ...data.analog_four_sysex_calibration import (
    A4_FILTER1_FREQUENCY_PARAMETER,
    A4_FILTER1_FREQUENCY_RAW_MAX,
    A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET,
    A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE,
    format_analog_four_filter1_frequency_screen_value,
)
from ...devices import (
    AnalogFourFilter1FrequencyCandidateMutation,
    get_analog_four_filter1_frequency_candidate_capability,
    resolve_saved_kit_capture_capability,
)
from ..capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
    cockpit_snapshot_from_rytm_capture,
)
from ..data import MutationCandidate, ProfileModel, Snapshot
from ..data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    AnalogFourCandidateValue,
    AnalogFourOfflineCandidate,
    OxiShowMetadata,
    ShowBankEntry,
    ShowKitCandidate,
    ShowKitCapture,
    ShowKitEvidence,
    ShowKitRecipe,
    ShowKitSysex,
)
from ..engine.mutate import mutate
from ..engine.prng import xorshift32

_UINT32_MAX: Final[int] = (1 << 32) - 1
_UINT32_MIDPOINT: Final[int] = 1 << 31
_A4_PRNG_WARMUP: Final[int] = 8
_A4_PRNG_XOR: Final[int] = 0xA4F1F00D
_SYSEX_START: Final[int] = 0xF0
_SYSEX_END: Final[int] = 0xF7


@dataclass(frozen=True)
class ForgedCandidatePair:
    """One inert paired domain candidate plus its exact local A4 frame."""

    candidate: ShowKitCandidate
    analog_four_frame: bytes


def _show_kit_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fingerprint(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def _artifact_id(device_label: str, digest: str) -> str:
    return f"{device_label}-{digest[:16]}"


def capture_reference(
    result: KitCaptureResult,
    *,
    hardware_slot: int,
    snapshot_id: str | None,
) -> ShowKitCapture:
    """Convert a verified in-memory capture into an immutable source reference."""

    if not result.round_trip_verified or not result.input_only or result.sent_midi:
        raise ValueError(
            "show-bank source capture must be codec round-trip verified and input-only"
        )
    if not result.frame or result.frame[0] != _SYSEX_START or result.frame[-1] != _SYSEX_END:
        raise ValueError("show-bank source capture must retain one framed SysEx message")
    if result.device_id == ANALOG_RYTM_DEVICE_ID:
        device_id = RYTM_SHOW_KIT_DEVICE_ID
        device_label = "rytm"
        if not snapshot_id:
            raise ValueError("Rytm source capture requires its promoted snapshot id")
    elif result.device_id == ANALOG_FOUR_DEVICE_ID:
        device_id = A4_SHOW_KIT_DEVICE_ID
        device_label = "a4"
        if snapshot_id is not None:
            raise ValueError("Analog Four source capture cannot carry a Rytm snapshot id")
    else:  # pragma: no cover - KitCaptureResult narrows this at construction sites
        raise ValueError("unsupported show-bank source device")

    frame_sha256 = _show_kit_sha256(result.frame)
    evidence = ShowKitEvidence(
        evidence_id=f"capture-{device_label}-{result.fingerprint[:16]}",
        status="round-trip-verified",
        source="Cockpit input-only current-KIT capture",
        observed_at=result.captured_at,
        notes=("Exact framed bytes retained in memory; no hardware output occurred.",),
    )
    capture_event = _fingerprint(result.captured_at.isoformat())[:8]
    return ShowKitCapture(
        capture_id=(
            f"capture-{device_label}-{hardware_slot}-" f"{result.fingerprint[:16]}-{capture_event}"
        ),
        device_id=device_id,
        kit_name=result.kit_name,
        hardware_slot=hardware_slot,
        fingerprint=result.fingerprint,
        snapshot_id=snapshot_id,
        captured_at=result.captured_at,
        sysex=ShowKitSysex(
            artifact_id=_artifact_id(device_label, frame_sha256),
            frame_sha256=frame_sha256,
            frame_bytes=len(result.frame),
        ),
        evidence=(evidence,),
    )


def build_source_entry(  # noqa: PLR0913 - typed paired capture identity and cue metadata
    *,
    entry_id: str,
    cue_index: int,
    name: str,
    description: str,
    rytm_capture: KitCaptureResult,
    analog_four_capture: KitCaptureResult,
    rytm_slot: int,
    analog_four_slot: int,
    rytm_snapshot_id: str,
    now: datetime,
) -> ShowBankEntry:
    """Build one paired immutable source entry from current verified captures."""

    return ShowBankEntry(
        entry_id=entry_id,
        cue_index=cue_index,
        name=name,
        description=description,
        rytm_source=capture_reference(
            rytm_capture,
            hardware_slot=rytm_slot,
            snapshot_id=rytm_snapshot_id,
        ),
        analog_four_source=capture_reference(
            analog_four_capture,
            hardware_slot=analog_four_slot,
            snapshot_id=None,
        ),
        candidates=(),
        selected_candidate_id=None,
        rytm_live_auditioned_candidate_id=None,
        rytm_live_auditioned_at=None,
        favorite=None,
        rytm_hardware_save=None,
        analog_four_hardware_save=None,
        rytm_recapture=None,
        analog_four_recapture=None,
        show_time_preflight=None,
        show_ready_at=None,
        oxi=OxiShowMetadata(),
        audition_notes=(),
        energy_notes=(),
        transition_notes=(),
        recovery_notes=(),
        created_at=now,
        updated_at=now,
    )


def _resulting_rytm_snapshot_payload(
    source: Snapshot,
    candidate: MutationCandidate,
) -> list[dict[str, object]]:
    deltas = {delta.pad_id: delta for delta in candidate.pad_deltas}
    result: list[dict[str, object]] = []
    for pad in sorted(source.pads, key=lambda item: item.pad_id):
        delta = deltas.get(pad.pad_id)
        params = dict(pad.params) if delta is None else dict(delta.proposed_params)
        result.append(
            {
                "machine": pad.machine,
                "pad_id": pad.pad_id,
                "params": {key: params[key] for key in sorted(params)},
            }
        )
    return result


def rytm_semantic_fingerprint(source: Snapshot, candidate: MutationCandidate) -> str:
    """Fingerprint the mapped Rytm state expected after applying ``candidate``."""

    return _fingerprint(_resulting_rytm_snapshot_payload(source, candidate))


def rytm_capture_semantic_fingerprint(result: KitCaptureResult) -> str:
    """Fingerprint the mapped semantic state in a fresh Rytm recapture."""

    snapshot = cockpit_snapshot_from_rytm_capture(result)
    return _fingerprint(
        [
            {
                "machine": pad.machine,
                "pad_id": pad.pad_id,
                "params": {key: pad.params[key] for key in sorted(pad.params)},
            }
            for pad in snapshot.pads
        ]
    )


def _deterministic_candidate_id(
    entry: ShowBankEntry,
    recipe: ShowKitRecipe,
    rytm_candidate: MutationCandidate,
    analog_four_sha256: str,
) -> str:
    payload = {
        "analog_four_sha256": analog_four_sha256,
        "entry_id": entry.entry_id,
        "recipe": recipe.to_dict(),
        "rytm": {
            key: value for key, value in rytm_candidate.to_dict().items() if key != "candidate_id"
        },
        "sources": [entry.rytm_source.fingerprint, entry.analog_four_source.fingerprint],
    }
    return f"candidate-{_fingerprint(payload)}"


def _a4_semantic_fingerprint(
    values: tuple[AnalogFourCandidateValue, ...],
) -> str:
    return _fingerprint(
        [
            {
                "parameter": value.parameter,
                "raw_q8_8": value.encoded_unsigned_8_8,
                "track_id": value.track_id,
            }
            for value in sorted(values, key=lambda item: (item.track_id, item.parameter))
        ]
    )


def _clone_candidate_with_id(
    candidate: MutationCandidate,
    candidate_id: str,
) -> MutationCandidate:
    return MutationCandidate(
        candidate_id=candidate_id,
        source_snapshot_id=candidate.source_snapshot_id,
        profile_id=candidate.profile_id,
        depth=candidate.depth,
        seed=candidate.seed,
        pad_deltas=candidate.pad_deltas,
        safety_status=candidate.safety_status,
        estimated_midi_msgs=candidate.estimated_midi_msgs,
    )


def _a4_source_unpacked(frame: bytes) -> bytes:
    resolved = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID)
    return resolved.capability.decode_saved_kit_capture(frame).unpacked


def _a4_mutation_values(
    source_frame: bytes,
    *,
    recipe: ShowKitRecipe,
) -> tuple[AnalogFourFilter1FrequencyCandidateMutation, ...]:
    unpacked = _a4_source_unpacked(source_frame)
    effective_tracks = recipe.analog_four_scope.effective_ids
    state = ((recipe.seed & _UINT32_MAX) ^ _A4_PRNG_XOR) or _A4_PRNG_XOR
    for _ in range(_A4_PRNG_WARMUP):
        _, state = xorshift32(state)

    mutations: list[AnalogFourFilter1FrequencyCandidateMutation] = []
    for track in effective_tracks:
        raw, state = xorshift32(state)
        offset = A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET + (
            (track - 1) * A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE
        )
        source_raw = int.from_bytes(unpacked[offset : offset + 2], "big")
        if not 0 <= source_raw <= A4_FILTER1_FREQUENCY_RAW_MAX:
            raise ValueError(
                f"A4 track {track} Filter 1 Frequency is outside the verified 0.00..127.00 range"
            )
        signed_unit = (raw - _UINT32_MIDPOINT) / _UINT32_MIDPOINT
        delta = int(round(signed_unit * recipe.depth * A4_FILTER1_FREQUENCY_RAW_MAX))
        rendered_raw = min(
            A4_FILTER1_FREQUENCY_RAW_MAX,
            max(0, source_raw + delta),
        )
        screen_value = format_analog_four_filter1_frequency_screen_value(rendered_raw)
        mutations.append(
            AnalogFourFilter1FrequencyCandidateMutation(
                track=track,
                screen_value=screen_value,
            )
        )
    return tuple(mutations)


def forge_candidate_pair(  # noqa: PLR0913 - explicit immutable sources, recipe, and evidence time
    *,
    entry: ShowBankEntry,
    rytm_source_snapshot: Snapshot,
    analog_four_source_frame: bytes,
    profile: ProfileModel,
    recipe: ShowKitRecipe,
    now: datetime,
) -> ForgedCandidatePair:
    """Generate one deterministic paired candidate without touching hardware."""

    if entry.rytm_source.snapshot_id != rytm_source_snapshot.snapshot_id:
        raise ValueError("Rytm source snapshot does not match the immutable show-bank anchor")
    if profile.profile_id != recipe.profile_id:
        raise ValueError("active profile does not match the show-kit recipe")
    if _show_kit_sha256(analog_four_source_frame) != entry.analog_four_source.sysex.frame_sha256:
        raise ValueError("Analog Four source bytes do not match the immutable show-bank anchor")

    generated_rytm = mutate(
        rytm_source_snapshot,
        profile,
        recipe.depth,
        recipe.seed,
        target_pad_ids=frozenset(recipe.rytm_scope.target_ids),
        locked_pad_ids=frozenset(recipe.rytm_scope.locked_ids),
    )
    filter1_capability = get_analog_four_filter1_frequency_candidate_capability()
    rendered_a4 = filter1_capability.render_filter1_frequency_candidate(
        analog_four_source_frame,
        _a4_mutation_values(analog_four_source_frame, recipe=recipe),
    )
    candidate_id = _deterministic_candidate_id(
        entry,
        recipe,
        generated_rytm,
        rendered_a4.sha256,
    )
    rytm_candidate = _clone_candidate_with_id(generated_rytm, candidate_id)
    a4_values = tuple(
        AnalogFourCandidateValue(
            track_id=item.track,
            parameter=A4_FILTER1_FREQUENCY_PARAMETER,
            screen_value=item.redecoded_screen_value,
            encoded_unsigned_8_8=item.redecoded_raw_q8_8,
            unpacked_offset=item.intended_unpacked_offsets[0],
        )
        for item in rendered_a4.applied_mutations
    )
    analog_four_candidate = AnalogFourOfflineCandidate(
        artifact_fingerprint=rendered_a4.sha256[:16],
        semantic_fingerprint=(
            _a4_semantic_fingerprint(a4_values)
            if a4_values
            else entry.analog_four_source.fingerprint
        ),
        source_fingerprint=entry.analog_four_source.fingerprint,
        sysex=ShowKitSysex(
            artifact_id=_artifact_id("a4-candidate", rendered_a4.sha256),
            frame_sha256=rendered_a4.sha256,
            frame_bytes=len(rendered_a4.framed_sysex),
        ),
        values=a4_values,
        evidence_status="offline-captured-kit-mutation-validated",
    )
    evidence = ShowKitEvidence(
        evidence_id=f"forge-{candidate_id.removeprefix('candidate-')}",
        status="pending-physical-outbound-validation",
        source="Show Kit Forge deterministic offline candidate generation",
        observed_at=now,
        notes=(
            "Rytm remains subject to exact ArmedApply plan confirmation.",
            "A4 artifact is local-file-only and grants zero output authority.",
        ),
    )
    candidate = ShowKitCandidate(
        candidate_id=candidate_id,
        source_rytm_fingerprint=entry.rytm_source.fingerprint,
        source_a4_fingerprint=entry.analog_four_source.fingerprint,
        rytm_semantic_fingerprint=rytm_semantic_fingerprint(
            rytm_source_snapshot,
            rytm_candidate,
        ),
        recipe=recipe,
        rytm_candidate=rytm_candidate,
        analog_four_candidate=analog_four_candidate,
        created_at=now,
        evidence=(evidence,),
    )
    return ForgedCandidatePair(
        candidate=candidate,
        analog_four_frame=rendered_a4.framed_sysex,
    )


def analog_four_recapture_semantically_matches(
    result: KitCaptureResult,
    candidate: AnalogFourOfflineCandidate,
) -> bool:
    """Compare only promoted A4 Filter 1 Frequency values in a fresh capture."""

    if result.device_id != ANALOG_FOUR_DEVICE_ID or not result.round_trip_verified:
        return False
    return analog_four_capture_semantic_fingerprint(result, candidate) == (
        candidate.semantic_fingerprint
    )


def analog_four_capture_semantic_fingerprint(
    result: KitCaptureResult,
    candidate: AnalogFourOfflineCandidate,
) -> str | None:
    """Fingerprint the promoted A4 values corresponding to ``candidate``."""

    if result.device_id != ANALOG_FOUR_DEVICE_ID or not result.round_trip_verified:
        return None
    if not candidate.values:
        # A fully locked A4 partner must retain the complete source payload;
        # an empty semantic subset must never make every recapture match.
        return result.fingerprint
    unpacked = _a4_source_unpacked(result.frame)
    observed_values: list[AnalogFourCandidateValue] = []
    for value in candidate.values:
        offset = A4_FILTER1_FREQUENCY_TRACK_1_UNPACKED_OFFSET + (
            (value.track_id - 1) * A4_FILTER1_FREQUENCY_TRACK_UNPACKED_STRIDE
        )
        raw = int.from_bytes(unpacked[offset : offset + 2], "big")
        observed_values.append(
            AnalogFourCandidateValue(
                track_id=value.track_id,
                parameter=A4_FILTER1_FREQUENCY_PARAMETER,
                screen_value=format_analog_four_filter1_frequency_screen_value(raw),
                encoded_unsigned_8_8=raw,
                unpacked_offset=offset,
            )
        )
    return _a4_semantic_fingerprint(tuple(observed_values))


__all__ = [
    "ForgedCandidatePair",
    "analog_four_capture_semantic_fingerprint",
    "analog_four_recapture_semantically_matches",
    "build_source_entry",
    "capture_reference",
    "forge_candidate_pair",
    "rytm_capture_semantic_fingerprint",
    "rytm_semantic_fingerprint",
]
