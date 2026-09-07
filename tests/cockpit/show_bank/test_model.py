from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    SHOW_BANK_SCHEMA_VERSION,
    AnalogFourCandidateValue,
    AnalogFourOfflineCandidate,
    FavoriteRecapture,
    HardwareSaveAttestation,
    OxiShowMetadata,
    RetainedSysexArtifact,
    ShowBank,
    ShowKitEvidence,
    ShowKitScope,
    ShowKitSysex,
    ShowTimePreflight,
    narrow_show_kit_depth_preset,
    narrow_show_kit_device_id,
    narrow_show_kit_evidence_status,
    narrow_show_kit_lifecycle_status,
)

from ._support import (
    LATER,
    NOW,
    PREFLIGHT_CAPTURED_AT,
    PREFLIGHT_CHECKED_AT,
    RECORDED_AT,
    RYTM_SEMANTIC_FINGERPRINT,
    RYTM_SOURCE_SEMANTIC_FINGERPRINT,
    candidate,
    recapture,
    source_entry,
    sysex,
)

pytestmark = pytest.mark.fast


def test_complete_bank_round_trip_preserves_exact_nested_rytm_candidate() -> None:
    entry = dataclasses.replace(
        source_entry(),
        candidates=(candidate(),),
        selected_candidate_id="candidate-one",
    )
    bank = ShowBank(
        bank_id="fall-show",
        name="Fall Show",
        description="Paired favorites",
        revision=3,
        entries=(entry,),
        notes=("OXI remains the sequencer.",),
        evidence=(
            ShowKitEvidence(
                evidence_id="capture-proof",
                status="round-trip-verified",
                source="operator capture",
                observed_at=NOW,
            ),
        ),
        created_at=NOW,
        updated_at=LATER,
    )

    restored = ShowBank.from_dict(bank.to_dict())

    assert restored == bank
    assert restored.entries[0].selected_candidate is not None
    assert restored.entries[0].selected_candidate.rytm_candidate == candidate().rytm_candidate
    assert restored.entries[0].energy_level == 3
    assert restored.status == "candidate"
    with pytest.raises(dataclasses.FrozenInstanceError):
        restored.name = "changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    ("narrow", "valid", "invalid", "message"),
    [
        (narrow_show_kit_device_id, RYTM_SHOW_KIT_DEVICE_ID, "other", "invalid show-kit device id"),
        (
            narrow_show_kit_lifecycle_status,
            "verified",
            "almost",
            "invalid show-kit lifecycle status",
        ),
        (narrow_show_kit_depth_preset, "custom", "huge", "invalid show-kit depth preset"),
        (narrow_show_kit_evidence_status, "blocked", "maybe", "invalid show-kit evidence status"),
    ],
)
def test_literal_narrowing_validates_untrusted_strings(
    narrow, valid: str, invalid: str, message: str
) -> None:
    assert narrow(valid) == valid
    with pytest.raises(ValueError, match=message):
        narrow(invalid)


def test_scope_uses_include_minus_locks_and_rejects_wrong_domain() -> None:
    scope = ShowKitScope(
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        target_ids=(3, 1, 2),
        locked_ids=(2,),
    )
    assert scope.target_ids == (1, 2, 3)
    assert scope.effective_ids == (1, 3)
    assert ShowKitScope(
        device_id=A4_SHOW_KIT_DEVICE_ID,
        locked_ids=(1,),
    ).effective_ids == (2, 3, 4)
    with pytest.raises(ValueError, match="unavailable"):
        ShowKitScope(device_id=A4_SHOW_KIT_DEVICE_ID, target_ids=(5,))
    with pytest.raises(ValueError, match="target_ids must contain positive integer ids"):
        ShowKitScope(device_id=RYTM_SHOW_KIT_DEVICE_ID, target_ids=(True,))


def test_exact_sysex_and_capture_invariants() -> None:
    base = sysex("source-frame", 9)
    retained = RetainedSysexArtifact(
        artifact_name=f"{base.frame_sha256}.syx",
        sha256=base.frame_sha256,
        byte_count=base.frame_bytes,
    )
    assert (
        ShowKitSysex.from_dict(dataclasses.replace(base, retained=retained).to_dict()).retained
        == retained
    )
    with pytest.raises(ValueError, match="does not match"):
        dataclasses.replace(base, retained=dataclasses.replace(retained, byte_count=4))
    with pytest.raises(ValueError, match="round-trip"):
        dataclasses.replace(source_entry().rytm_source, round_trip_verified=False)
    with pytest.raises(ValueError, match="1..128"):
        dataclasses.replace(source_entry().rytm_source, hardware_slot=0)
    with pytest.raises(ValueError, match="timezone-aware"):
        dataclasses.replace(source_entry().rytm_source, captured_at=datetime(2026, 1, 1))


@pytest.mark.parametrize(
    ("changes", "message"),
    [
        ({"parameter": "Amp Attack"}, "support only Filter1 Frequency"),
        ({"track_id": 5}, "A4 candidate track_id must be in"),
        ({"encoded_unsigned_8_8": 0x7F01}, "encoded_unsigned_8_8 must be in"),
        ({"unpacked_offset": -1}, "unpacked_offset must equal the verified"),
    ],
)
def test_a4_candidate_values_are_narrowly_bounded(changes: dict[str, object], message: str) -> None:
    value = candidate().analog_four_candidate.values[0]
    with pytest.raises(ValueError, match=message):
        dataclasses.replace(value, **changes)


def test_a4_candidate_is_offline_only_and_unique() -> None:
    offline = candidate().analog_four_candidate
    with pytest.raises(ValueError, match="offline-only"):
        dataclasses.replace(offline, evidence_status="hardware-write-validated")
    assert dataclasses.replace(offline, values=()).values == ()
    with pytest.raises(ValueError, match="duplicate"):
        dataclasses.replace(offline, values=(offline.values[0], offline.values[0]))
    assert AnalogFourOfflineCandidate.from_dict(offline.to_dict()) == offline
    assert AnalogFourCandidateValue.from_dict(offline.values[0].to_dict()) == offline.values[0]


def test_rytm_candidate_identity_cardinality_counts_and_maps_are_defensive() -> None:
    base = candidate()
    inner = base.rytm_candidate
    delta = inner.pad_deltas[0]

    with pytest.raises(ValueError, match="paired candidate id"):
        dataclasses.replace(
            base,
            rytm_candidate=dataclasses.replace(inner, candidate_id="other-candidate"),
        )
    with pytest.raises(ValueError, match="unique pad ids"):
        dataclasses.replace(
            base,
            rytm_candidate=dataclasses.replace(
                inner,
                pad_deltas=(delta, delta),
                estimated_midi_msgs=2,
            ),
        )
    with pytest.raises(ValueError, match="at most 12"):
        dataclasses.replace(
            base,
            rytm_candidate=dataclasses.replace(
                inner,
                pad_deltas=(delta,) * 13,
                estimated_midi_msgs=13,
            ),
        )
    with pytest.raises(ValueError, match="changed-key count"):
        dataclasses.replace(
            base,
            rytm_candidate=dataclasses.replace(inner, estimated_midi_msgs=2),
        )

    proposed = {"filter_frequency": 72}
    mutable_delta = dataclasses.replace(delta, proposed_params=proposed)
    immutable = dataclasses.replace(
        base,
        rytm_candidate=dataclasses.replace(inner, pad_deltas=(mutable_delta,)),
    )
    proposed["filter_frequency"] = 99
    assert immutable.rytm_candidate.pad_deltas[0].proposed_params == {"filter_frequency": 72}
    with pytest.raises(TypeError):
        immutable.rytm_candidate.pad_deltas[0].proposed_params["filter_frequency"] = 80


def test_recapture_separates_semantic_match_from_full_capture_identity() -> None:
    capture = recapture(RYTM_SHOW_KIT_DEVICE_ID)
    result = FavoriteRecapture(
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        expected_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        capture=capture,
        recorded_at=RECORDED_AT,
        matches_candidate=True,
        matches_source=False,
        comparison_reason="mapped semantic fields matched",
    )
    assert result.capture.fingerprint == "aaaaaaaa"
    assert result.capture.fingerprint != result.expected_semantic_fingerprint
    assert FavoriteRecapture.from_dict(result.to_dict()) == result
    with pytest.raises(ValueError, match="semantic comparison"):
        dataclasses.replace(result, matches_candidate=False)
    with pytest.raises(ValueError, match="source-match"):
        dataclasses.replace(result, matches_source=True)
    source_match = dataclasses.replace(
        result,
        observed_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        matches_candidate=False,
        matches_source=True,
    )
    assert source_match.matches_source
    assert not source_match.matches_candidate
    unsupported = dataclasses.replace(
        result,
        observed_semantic_fingerprint=None,
        matches_candidate=False,
        matches_source=False,
        comparison_reason="semantic compare unsupported",
    )
    assert not unsupported.matches_candidate
    assert not unsupported.matches_source
    with pytest.raises(ValueError, match="source semantic fingerprint"):
        dataclasses.replace(result, source_semantic_fingerprint="bad")
    with pytest.raises(ValueError, match="cannot precede"):
        dataclasses.replace(result, recorded_at=NOW)


def test_show_time_preflight_compares_full_recapture_fingerprints() -> None:
    ready = ShowTimePreflight(
        expected_rytm_fingerprint="aaaaaaaa",
        observed_rytm_fingerprint="aaaaaaaa",
        observed_rytm_capture_id="rytm-preflight",
        observed_rytm_captured_at=PREFLIGHT_CAPTURED_AT,
        rytm_matches=True,
        expected_a4_fingerprint="bbbbbbbb",
        observed_a4_fingerprint="bbbbbbbb",
        observed_a4_capture_id="a4-preflight",
        observed_a4_captured_at=PREFLIGHT_CAPTURED_AT,
        a4_matches=True,
        checked_at=PREFLIGHT_CHECKED_AT,
        reason="fresh captures match catalog",
    )
    assert ready.ready
    assert ShowTimePreflight.from_dict(ready.to_dict()) == ready
    with pytest.raises(ValueError, match="Rytm preflight"):
        dataclasses.replace(ready, observed_rytm_fingerprint="cccccccc")
    with pytest.raises(ValueError, match="A4 preflight"):
        dataclasses.replace(ready, observed_a4_fingerprint="dddddddd")
    with pytest.raises(ValueError, match="filename-safe"):
        dataclasses.replace(ready, observed_rytm_capture_id="Bad capture")
    with pytest.raises(ValueError, match="timezone-aware"):
        dataclasses.replace(
            ready,
            observed_a4_captured_at=datetime(2026, 9, 4, 12, 5),
        )
    with pytest.raises(ValueError, match="checked before"):
        dataclasses.replace(ready, checked_at=NOW)


def test_operator_metadata_and_save_attestation_are_bounded() -> None:
    assert OxiShowMetadata.from_dict(OxiShowMetadata().to_dict()) == OxiShowMetadata()
    save = HardwareSaveAttestation(
        device_id=A4_SHOW_KIT_DEVICE_ID,
        hardware_slot=128,
        attested_at=NOW,
        note="Saved manually on the A4.",
    )
    assert HardwareSaveAttestation.from_dict(save.to_dict()) == save
    with pytest.raises(ValueError, match="1..128"):
        dataclasses.replace(save, hardware_slot=129)
    with pytest.raises(ValueError, match="OXI project contains surrounding or control whitespace"):
        OxiShowMetadata(project=" x")


@pytest.mark.parametrize("energy_level", [None, 1, 5])
def test_entry_energy_level_round_trips_supported_values(energy_level: int | None) -> None:
    entry = dataclasses.replace(source_entry(), energy_level=energy_level)
    assert type(entry).from_dict(entry.to_dict()) == entry


@pytest.mark.parametrize("energy_level", [True, 0, 6])
def test_entry_energy_level_rejects_invalid_values(energy_level: object) -> None:
    with pytest.raises(ValueError, match="energy_level"):
        dataclasses.replace(source_entry(), energy_level=energy_level)


@pytest.mark.parametrize("source_name", ["rytm_source", "analog_four_source"])
def test_entry_and_import_require_operator_source_slots(source_name: str) -> None:
    entry = source_entry()
    source = dataclasses.replace(getattr(entry, source_name), hardware_slot=None)
    with pytest.raises(ValueError, match="source hardware_slot must be in 1..128"):
        dataclasses.replace(entry, **{source_name: source})

    raw = entry.to_dict()
    raw[source_name]["hardware_slot"] = None
    with pytest.raises(ValueError, match="source hardware_slot must be in 1..128"):
        type(entry).from_dict(raw)


def test_bank_rejects_noncanonical_structure_and_persisted_status() -> None:
    entry = source_entry()
    with pytest.raises(ValueError, match="contiguous"):
        ShowBank(
            bank_id="bank",
            name="Bank",
            description="",
            revision=0,
            entries=(dataclasses.replace(entry, cue_index=2),),
            notes=(),
            evidence=(),
            created_at=NOW,
            updated_at=NOW,
        )
    bank = ShowBank(
        bank_id="bank",
        name="Bank",
        description="",
        revision=0,
        entries=(entry,),
        notes=(),
        evidence=(),
        created_at=NOW,
        updated_at=NOW,
    )
    raw = bank.to_dict()
    raw["status"] = "favorite"
    with pytest.raises(ValueError, match="persisted bank status"):
        ShowBank.from_dict(raw)
    assert bank.schema_version == SHOW_BANK_SCHEMA_VERSION
    assert bank.entry("entry-one") == entry
    with pytest.raises(ValueError, match="unknown"):
        bank.entry("missing")
    with pytest.raises(ValueError, match="unknown"):
        bank.sysex_artifact("missing")
