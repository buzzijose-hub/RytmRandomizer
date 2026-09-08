from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from rytm_randomizer.cockpit.data.mutation_candidate import MutationCandidate, PadDelta
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    AnalogFourCandidateValue,
    AnalogFourOfflineCandidate,
    OxiShowMetadata,
    ShowBankEntry,
    ShowKitCandidate,
    ShowKitCapture,
    ShowKitRecipe,
    ShowKitScope,
    ShowKitSysex,
)

NOW = datetime(2026, 9, 4, 12, 0, tzinfo=timezone.utc)
LATER = datetime(2026, 9, 4, 12, 1, tzinfo=timezone.utc)
SAVE_AT = datetime(2026, 9, 4, 12, 2, tzinfo=timezone.utc)
RECAPTURED_AT = datetime(2026, 9, 4, 12, 3, tzinfo=timezone.utc)
RECORDED_AT = datetime(2026, 9, 4, 12, 4, tzinfo=timezone.utc)
PREFLIGHT_CAPTURED_AT = datetime(2026, 9, 4, 12, 5, tzinfo=timezone.utc)
PREFLIGHT_CHECKED_AT = datetime(2026, 9, 4, 12, 6, tzinfo=timezone.utc)
SECOND_PREFLIGHT_CAPTURED_AT = datetime(2026, 9, 4, 12, 7, tzinfo=timezone.utc)
SECOND_PREFLIGHT_CHECKED_AT = datetime(2026, 9, 4, 12, 8, tzinfo=timezone.utc)

RYTM_SOURCE_FINGERPRINT = "11111111"
A4_SOURCE_FINGERPRINT = "22222222"
RYTM_SEMANTIC_FINGERPRINT = "33333333"
A4_SEMANTIC_FINGERPRINT = "44444444"
A4_ARTIFACT_FINGERPRINT = "55555555"
RYTM_SOURCE_SEMANTIC_FINGERPRINT = "66666666"
A4_SOURCE_SEMANTIC_FINGERPRINT = "77777777"


def frame(marker: int) -> bytes:
    return bytes((0xF0, marker, 0xF7))


def sysex(artifact_id: str, marker: int) -> ShowKitSysex:
    payload = frame(marker)
    return ShowKitSysex(
        artifact_id=artifact_id,
        frame_sha256=hashlib.sha256(payload).hexdigest(),
        frame_bytes=len(payload),
    )


def capture(
    *,
    capture_id: str,
    device_id: str,
    fingerprint: str,
    marker: int,
    slot: int = 20,
    captured_at: datetime = NOW,
) -> ShowKitCapture:
    return ShowKitCapture(
        capture_id=capture_id,
        device_id=device_id,  # type: ignore[arg-type]
        kit_name=f"Kit {capture_id}",
        hardware_slot=slot,
        fingerprint=fingerprint,
        snapshot_id="snapshot-one" if device_id == RYTM_SHOW_KIT_DEVICE_ID else None,
        captured_at=captured_at,
        sysex=sysex(f"{capture_id}-frame", marker),
    )


def source_entry(*, entry_id: str = "entry-one", cue_index: int = 1) -> ShowBankEntry:
    return ShowBankEntry(
        entry_id=entry_id,
        cue_index=cue_index,
        name="Opening pressure",
        description="Paired source anchors",
        rytm_source=capture(
            capture_id="rytm-source",
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            fingerprint=RYTM_SOURCE_FINGERPRINT,
            marker=1,
        ),
        analog_four_source=capture(
            capture_id="a4-source",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            fingerprint=A4_SOURCE_FINGERPRINT,
            marker=2,
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
        oxi=OxiShowMetadata(project="Show", pattern="A1", chapter="Opening"),
        audition_notes=("Listen against the transition.",),
        energy_level=3,
        energy_notes=("Medium pressure.",),
        transition_notes=("Eight-bar blend.",),
        recovery_notes=("Reload both cataloged source slots.",),
        created_at=NOW,
        updated_at=NOW,
    )


def candidate(*, candidate_id: str = "candidate-one") -> ShowKitCandidate:
    recipe = ShowKitRecipe(
        profile_id="profile-one",
        depth_preset="medium",
        depth=0.5,
        seed=7,
        rytm_scope=ShowKitScope(
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            target_ids=(1, 2),
            locked_ids=(2,),
        ),
        analog_four_scope=ShowKitScope(
            device_id=A4_SHOW_KIT_DEVICE_ID,
            target_ids=(1, 2),
            locked_ids=(2,),
        ),
    )
    rytm_candidate = MutationCandidate(
        candidate_id=candidate_id,
        source_snapshot_id="snapshot-one",
        profile_id="profile-one",
        depth=0.5,
        seed=7,
        pad_deltas=(
            PadDelta(
                pad_id=1,
                proposed_params={"filter_frequency": 64},
                changed_keys=frozenset({"filter_frequency"}),
            ),
        ),
        safety_status="safe",
        estimated_midi_msgs=1,
    )
    a4_candidate = AnalogFourOfflineCandidate(
        artifact_fingerprint=A4_ARTIFACT_FINGERPRINT,
        semantic_fingerprint=A4_SEMANTIC_FINGERPRINT,
        source_fingerprint=A4_SOURCE_FINGERPRINT,
        sysex=sysex(f"{candidate_id}-a4-frame", 3),
        values=(
            AnalogFourCandidateValue(
                track_id=1,
                parameter="Filter1 Frequency",
                screen_value="63.50",
                encoded_unsigned_8_8=0x3F80,
                unpacked_offset=128,
            ),
        ),
        evidence_status="offline-captured-kit-mutation-validated",
    )
    return ShowKitCandidate(
        candidate_id=candidate_id,
        source_rytm_fingerprint=RYTM_SOURCE_FINGERPRINT,
        source_a4_fingerprint=A4_SOURCE_FINGERPRINT,
        rytm_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        recipe=recipe,
        rytm_candidate=rytm_candidate,
        analog_four_candidate=a4_candidate,
        created_at=NOW,
    )


def recapture(
    device_id: str,
    *,
    matching_full: bool = True,
    captured_at: datetime = RECAPTURED_AT,
    capture_id: str | None = None,
    slot: int = 64,
) -> ShowKitCapture:
    if device_id == RYTM_SHOW_KIT_DEVICE_ID:
        return capture(
            capture_id=capture_id or "rytm-favorite-capture",
            device_id=device_id,
            fingerprint="aaaaaaaa" if matching_full else "cccccccc",
            marker=4,
            slot=slot,
            captured_at=captured_at,
        )
    return capture(
        capture_id=capture_id or "a4-favorite-capture",
        device_id=device_id,
        fingerprint="bbbbbbbb" if matching_full else "dddddddd",
        marker=5,
        slot=slot,
        captured_at=captured_at,
    )
