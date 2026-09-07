from __future__ import annotations

import dataclasses
import math
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    FavoriteRecapture,
    HardwareSaveAttestation,
    RetainedSysexArtifact,
    ShowBank,
    ShowKitCapture,
    ShowKitEvidence,
    ShowKitFavorite,
    ShowKitRecipe,
    ShowKitScope,
    ShowKitSysex,
    ShowTimePreflight,
)

from ._support import (
    A4_SEMANTIC_FINGERPRINT,
    A4_SOURCE_SEMANTIC_FINGERPRINT,
    LATER,
    NOW,
    PREFLIGHT_CAPTURED_AT,
    PREFLIGHT_CHECKED_AT,
    RECORDED_AT,
    RYTM_SEMANTIC_FINGERPRINT,
    RYTM_SOURCE_SEMANTIC_FINGERPRINT,
    SAVE_AT,
    candidate,
    recapture,
    source_entry,
    sysex,
)

pytestmark = pytest.mark.fast


def _bank(entry=None, *, revision: int = 0) -> ShowBank:
    entries = () if entry is None else (entry,)
    return ShowBank(
        bank_id="bank",
        name="Bank",
        description="",
        revision=revision,
        entries=entries,
        notes=(),
        evidence=(),
        created_at=NOW,
        updated_at=NOW,
    )


def _candidate_entry():
    return dataclasses.replace(
        source_entry(),
        candidates=(candidate(),),
        selected_candidate_id="candidate-one",
    )


def _favorite_entry():
    return dataclasses.replace(
        _candidate_entry(),
        favorite=ShowKitFavorite(candidate_id="candidate-one", selected_at=NOW),
    )


def _save(device_id: str) -> HardwareSaveAttestation:
    return HardwareSaveAttestation(
        device_id=device_id,  # type: ignore[arg-type]
        hardware_slot=64,
        attested_at=SAVE_AT,
        note="manual save",
    )


def _favorite_recapture(device_id: str) -> FavoriteRecapture:
    fingerprint = (
        RYTM_SEMANTIC_FINGERPRINT
        if device_id == RYTM_SHOW_KIT_DEVICE_ID
        else A4_SEMANTIC_FINGERPRINT
    )
    return FavoriteRecapture(
        device_id=device_id,  # type: ignore[arg-type]
        expected_semantic_fingerprint=fingerprint,
        source_semantic_fingerprint=(
            RYTM_SOURCE_SEMANTIC_FINGERPRINT
            if device_id == RYTM_SHOW_KIT_DEVICE_ID
            else A4_SOURCE_SEMANTIC_FINGERPRINT
        ),
        observed_semantic_fingerprint=fingerprint,
        capture=recapture(device_id),
        recorded_at=RECORDED_AT,
        matches_candidate=True,
        matches_source=False,
        comparison_reason="semantic fields match",
    )


def _verified_entry():
    return dataclasses.replace(
        _favorite_entry(),
        rytm_hardware_save=_save(RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_hardware_save=_save(A4_SHOW_KIT_DEVICE_ID),
        rytm_recapture=_favorite_recapture(RYTM_SHOW_KIT_DEVICE_ID),
        analog_four_recapture=_favorite_recapture(A4_SHOW_KIT_DEVICE_ID),
    )


def _preflight(*, ready: bool = True) -> ShowTimePreflight:
    return ShowTimePreflight(
        expected_rytm_fingerprint="aaaaaaaa",
        observed_rytm_fingerprint="aaaaaaaa" if ready else "cccccccc",
        observed_rytm_capture_id="rytm-preflight",
        observed_rytm_captured_at=PREFLIGHT_CAPTURED_AT,
        rytm_matches=ready,
        expected_a4_fingerprint="bbbbbbbb",
        observed_a4_fingerprint="bbbbbbbb",
        observed_a4_capture_id="a4-preflight",
        observed_a4_captured_at=PREFLIGHT_CAPTURED_AT,
        a4_matches=True,
        checked_at=PREFLIGHT_CHECKED_AT,
        reason="fresh exact recaptures",
    )


def test_untrusted_scalar_and_collection_decoding_is_strict() -> None:
    with pytest.raises(TypeError, match="object"):
        ShowBank.from_dict([])  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="keys"):
        ShowBank.from_dict({1: "bad"})  # type: ignore[arg-type]

    raw = _bank().to_dict()
    raw.pop("name")
    with pytest.raises(ValueError, match="is incomplete"):
        ShowBank.from_dict(raw)

    for key, bad in (("name", 1), ("revision", True), ("entries", {}), ("notes", [1])):
        raw = _bank().to_dict()
        raw[key] = bad  # type: ignore[literal-required]
        with pytest.raises((TypeError, ValueError)):
            ShowBank.from_dict(raw)

    capture_raw = source_entry().rytm_source.to_dict()
    capture_raw["snapshot_id"] = 1
    with pytest.raises(TypeError, match="string or null"):
        ShowKitCapture.from_dict(capture_raw)
    capture_raw = source_entry().rytm_source.to_dict()
    capture_raw["hardware_slot"] = True
    with pytest.raises(TypeError, match="integer or null"):
        ShowKitCapture.from_dict(capture_raw)
    capture_raw = source_entry().rytm_source.to_dict()
    capture_raw["round_trip_verified"] = "true"
    with pytest.raises(TypeError, match="boolean"):
        ShowKitCapture.from_dict(capture_raw)
    capture_raw = source_entry().rytm_source.to_dict()
    capture_raw["captured_at"] = "not-a-date"
    with pytest.raises(ValueError, match="ISO-8601"):
        ShowKitCapture.from_dict(capture_raw)

    entry_raw = source_entry().to_dict()
    entry_raw["rytm_live_auditioned_at"] = "not-a-date"
    with pytest.raises(ValueError, match="ISO-8601"):
        type(source_entry()).from_dict(entry_raw)
    entry_raw = source_entry().to_dict()
    entry_raw["energy_level"] = True
    with pytest.raises(TypeError, match="integer or null"):
        type(source_entry()).from_dict(entry_raw)

    recipe_raw = candidate().recipe.to_dict()
    recipe_raw["depth"] = "deep"
    with pytest.raises(TypeError, match="numeric"):
        ShowKitRecipe.from_dict(recipe_raw)
    recipe_raw = candidate().recipe.to_dict()
    recipe_raw["depth"] = math.nan
    with pytest.raises(ValueError, match="finite"):
        ShowKitRecipe.from_dict(recipe_raw)

    scope_raw = candidate().recipe.rytm_scope.to_dict()
    scope_raw["target_ids"] = ["one"]
    with pytest.raises(TypeError, match="integer"):
        ShowKitScope.from_dict(scope_raw)


def test_common_identifier_text_hash_fingerprint_and_note_bounds() -> None:
    with pytest.raises(ValueError, match="filename-safe"):
        dataclasses.replace(source_entry(), entry_id="Bad ID")
    with pytest.raises(ValueError, match="length"):
        ShowKitEvidence(
            evidence_id="proof",
            status="blocked",
            source="",
            observed_at=NOW,
        )
    with pytest.raises(ValueError, match="length"):
        dataclasses.replace(_bank(), description="x" * 513)
    with pytest.raises(ValueError, match="SHA-256"):
        dataclasses.replace(source_entry().rytm_source.sysex, frame_sha256="bad")
    with pytest.raises(ValueError, match="fingerprint"):
        dataclasses.replace(source_entry().rytm_source, fingerprint="bad")
    with pytest.raises(ValueError, match="at most"):
        dataclasses.replace(source_entry(), audition_notes=tuple("x" for _ in range(33)))


def test_nested_evidence_artifact_sysex_and_capture_bounds() -> None:
    evidence = ShowKitEvidence(
        evidence_id="proof",
        status="blocked",
        source="operator",
        observed_at=NOW,
        notes=("note",),
    )
    assert ShowKitEvidence.from_dict(evidence.to_dict()) == evidence
    with pytest.raises(ValueError, match="unsupported"):
        dataclasses.replace(evidence, status="other")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at most"):
        dataclasses.replace(evidence, notes=tuple("x" for _ in range(33)))

    digest = "a" * 64
    artifact = RetainedSysexArtifact(f"{digest}.syx", digest, 3)
    assert RetainedSysexArtifact.from_dict(artifact.to_dict()) == artifact
    with pytest.raises(ValueError, match="artifact name"):
        dataclasses.replace(artifact, artifact_name="other.syx")
    with pytest.raises(ValueError, match="byte_count"):
        dataclasses.replace(artifact, byte_count=0)

    identity = ShowKitSysex("frame", digest, 3)
    assert ShowKitSysex.from_dict(identity.to_dict()) == identity
    with pytest.raises(ValueError, match="frame_bytes"):
        dataclasses.replace(identity, frame_bytes=0)
    with pytest.raises(ValueError, match="does not match"):
        dataclasses.replace(
            identity, retained=RetainedSysexArtifact(f"{'b' * 64}.syx", "b" * 64, 3)
        )

    base = source_entry().rytm_source
    enriched = dataclasses.replace(base, hardware_slot=None, snapshot_id=None, evidence=(evidence,))
    assert ShowKitCapture.from_dict(enriched.to_dict()) == enriched
    with pytest.raises(ValueError, match="unsupported"):
        dataclasses.replace(base, device_id="other")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="at most"):
        dataclasses.replace(base, evidence=tuple(evidence for _ in range(33)))


def test_recipe_and_candidate_cross_reference_validation() -> None:
    base_recipe = candidate().recipe
    a4_scope = base_recipe.analog_four_scope
    rytm_scope = base_recipe.rytm_scope
    for changes in (
        {"depth_preset": "other"},
        {"depth": 0.09},
        {"seed": True},
        {"seed": 7.0},
        {"rytm_scope": a4_scope},
        {"analog_four_scope": rytm_scope},
    ):
        with pytest.raises(ValueError):
            dataclasses.replace(base_recipe, **changes)

    base = candidate()
    with pytest.raises(ValueError, match="at most"):
        dataclasses.replace(
            base,
            evidence=tuple(ShowKitEvidence("proof", "blocked", "source", NOW) for _ in range(33)),
        )
    for field in ("profile_id", "depth", "seed"):
        value = "different" if field == "profile_id" else (0.6 if field == "depth" else 8)
        with pytest.raises(ValueError, match="deterministic recipe"):
            dataclasses.replace(
                base, rytm_candidate=dataclasses.replace(base.rytm_candidate, **{field: value})
            )
    with pytest.raises(ValueError, match="source fingerprint"):
        dataclasses.replace(
            base,
            analog_four_candidate=dataclasses.replace(
                base.analog_four_candidate, source_fingerprint="99999999"
            ),
        )
    outside_delta = dataclasses.replace(base.rytm_candidate.pad_deltas[0], pad_id=3)
    with pytest.raises(ValueError, match="untargeted"):
        dataclasses.replace(
            base,
            rytm_candidate=dataclasses.replace(base.rytm_candidate, pad_deltas=(outside_delta,)),
        )
    outside_value = dataclasses.replace(
        base.analog_four_candidate.values[0], track_id=3, unpacked_offset=828
    )
    with pytest.raises(ValueError, match="untargeted"):
        dataclasses.replace(
            base,
            analog_four_candidate=dataclasses.replace(
                base.analog_four_candidate, values=(outside_value,)
            ),
        )
    with pytest.raises(ValueError, match="unsupported A4"):
        dataclasses.replace(base.analog_four_candidate, evidence_status="other")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="unsupported show-kit scope"):
        ShowKitScope(device_id="other")  # type: ignore[arg-type]


def test_favorite_save_recapture_and_preflight_validation() -> None:
    favorite = ShowKitFavorite("candidate-one", NOW, ("keeper",))
    assert ShowKitFavorite.from_dict(favorite.to_dict()) == favorite
    with pytest.raises(ValueError, match="filename-safe"):
        dataclasses.replace(favorite, candidate_id="Bad")

    save = _save(RYTM_SHOW_KIT_DEVICE_ID)
    with pytest.raises(ValueError, match="unsupported"):
        dataclasses.replace(save, device_id="other")  # type: ignore[arg-type]

    favorite_capture = _favorite_recapture(RYTM_SHOW_KIT_DEVICE_ID)
    with pytest.raises(ValueError, match="unsupported"):
        dataclasses.replace(favorite_capture, device_id="other")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="captured device"):
        dataclasses.replace(favorite_capture, capture=recapture(A4_SHOW_KIT_DEVICE_ID))
    unequal = dataclasses.replace(
        favorite_capture,
        observed_semantic_fingerprint="99999999",
        matches_candidate=False,
    )
    assert FavoriteRecapture.from_dict(unequal.to_dict()) == unequal

    not_ready = _preflight(ready=False)
    assert not not_ready.ready
    with pytest.raises(ValueError, match="reason"):
        dataclasses.replace(not_ready, reason="")


def test_entry_rejects_conflated_or_cross_referenced_lifecycle_evidence() -> None:
    source = source_entry()
    selected = _candidate_entry()
    favorite = _favorite_entry()
    makers = (
        lambda: dataclasses.replace(source, cue_index=0),
        lambda: dataclasses.replace(source, rytm_source=source.analog_four_source),
        lambda: dataclasses.replace(source, analog_four_source=source.rytm_source),
        lambda: dataclasses.replace(
            source, candidates=tuple(candidate(candidate_id=f"c-{i}") for i in range(65))
        ),
        lambda: dataclasses.replace(selected, candidates=(candidate(), candidate())),
        lambda: dataclasses.replace(
            selected,
            candidates=(dataclasses.replace(candidate(), source_rytm_fingerprint="99999999"),),
        ),
        lambda: dataclasses.replace(
            selected,
            candidates=(
                dataclasses.replace(
                    candidate(),
                    rytm_candidate=dataclasses.replace(
                        candidate().rytm_candidate, source_snapshot_id="other"
                    ),
                ),
            ),
        ),
        lambda: dataclasses.replace(selected, selected_candidate_id="missing"),
        lambda: dataclasses.replace(selected, rytm_live_auditioned_candidate_id="candidate-one"),
        lambda: dataclasses.replace(
            selected,
            rytm_live_auditioned_candidate_id="missing",
            rytm_live_auditioned_at=NOW,
        ),
        lambda: dataclasses.replace(selected, favorite=ShowKitFavorite("missing", NOW)),
        lambda: dataclasses.replace(source, rytm_hardware_save=_save(RYTM_SHOW_KIT_DEVICE_ID)),
        lambda: dataclasses.replace(source, updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc)),
        lambda: dataclasses.replace(favorite, show_ready_at=LATER),
        lambda: dataclasses.replace(favorite, show_time_preflight=_preflight()),
        lambda: dataclasses.replace(favorite, rytm_hardware_save=_save(A4_SHOW_KIT_DEVICE_ID)),
        lambda: dataclasses.replace(
            favorite,
            rytm_recapture=_favorite_recapture(RYTM_SHOW_KIT_DEVICE_ID),
        ),
    )
    for make in makers:
        with pytest.raises(ValueError):
            make()


def test_entry_requires_live_audition_to_match_current_selection() -> None:
    with pytest.raises(ValueError, match="must match the selected"):
        dataclasses.replace(
            source_entry(),
            candidates=(candidate(), candidate(candidate_id="candidate-two")),
            selected_candidate_id="candidate-one",
            rytm_live_auditioned_candidate_id="candidate-two",
            rytm_live_auditioned_at=NOW,
        )


def test_entry_requires_recapture_slot_and_strict_save_chronology() -> None:
    verified = _verified_entry()
    rytm_recapture = verified.rytm_recapture
    assert rytm_recapture is not None

    wrong_slot = dataclasses.replace(
        rytm_recapture,
        capture=dataclasses.replace(rytm_recapture.capture, hardware_slot=65),
    )
    with pytest.raises(ValueError, match="slot must match"):
        dataclasses.replace(verified, rytm_recapture=wrong_slot)

    not_newer = dataclasses.replace(
        rytm_recapture,
        capture=dataclasses.replace(rytm_recapture.capture, captured_at=SAVE_AT),
    )
    with pytest.raises(ValueError, match="newer than its save"):
        dataclasses.replace(verified, rytm_recapture=not_newer)


def test_entry_requires_preflight_captures_newer_than_recapture_evidence() -> None:
    verified = _verified_entry()
    preflight = dataclasses.replace(
        _preflight(),
        observed_rytm_captured_at=RECORDED_AT,
    )
    with pytest.raises(ValueError, match="newer than the favorite recaptures"):
        dataclasses.replace(verified, show_time_preflight=preflight)


def test_entry_preflight_and_semantic_links_are_exact() -> None:
    verified = _verified_entry()
    with pytest.raises(ValueError, match="wrong candidate"):
        dataclasses.replace(
            verified,
            rytm_recapture=dataclasses.replace(
                verified.rytm_recapture,
                expected_semantic_fingerprint="99999999",
                observed_semantic_fingerprint="99999999",
            ),
        )
    with pytest.raises(ValueError, match="wrong recaptures"):
        dataclasses.replace(
            verified,
            show_time_preflight=dataclasses.replace(
                _preflight(), expected_rytm_fingerprint="cccccccc", rytm_matches=False
            ),
        )
    ready = dataclasses.replace(
        verified,
        show_time_preflight=_preflight(),
        show_ready_at=PREFLIGHT_CHECKED_AT,
    )
    assert ready.status == "show-ready"
    assert ready.favorite_candidate == candidate()
    assert source_entry().selected_candidate is None
    assert {capture.capture_id for capture in _bank(ready).captures()} >= {
        "rytm-favorite-capture",
        "a4-favorite-capture",
    }
    assert "candidate-one-a4-frame" in {
        identity.artifact_id for identity in _bank(_candidate_entry()).sysex_artifacts()
    }
    assert type(ready).from_dict(ready.to_dict()) == ready
    raw = ready.to_dict()
    raw["status"] = "source"
    with pytest.raises(ValueError, match="persisted entry status"):
        type(ready).from_dict(raw)


def test_bank_bounds_and_shared_identity_conflicts() -> None:
    empty = _bank()
    assert empty.status == "source"
    with pytest.raises(ValueError, match="schema"):
        dataclasses.replace(empty, schema_version="other")
    with pytest.raises(ValueError, match="revision"):
        dataclasses.replace(empty, revision=True)
    with pytest.raises(ValueError, match="at most"):
        dataclasses.replace(
            empty,
            entries=tuple(None for _ in range(257)),  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="duplicate entry"):
        dataclasses.replace(
            empty,
            entries=(source_entry(), dataclasses.replace(source_entry(), cue_index=2)),
        )
    with pytest.raises(ValueError, match="evidence"):
        dataclasses.replace(
            empty,
            evidence=tuple(ShowKitEvidence(f"e-{i}", "blocked", "source", NOW) for i in range(33)),
        )
    with pytest.raises(ValueError, match="precede"):
        dataclasses.replace(empty, updated_at=datetime(2025, 1, 1, tzinfo=timezone.utc))

    first = source_entry()
    conflicting_capture = dataclasses.replace(
        source_entry(entry_id="entry-two", cue_index=2),
        rytm_source=dataclasses.replace(first.rytm_source, kit_name="Different"),
    )
    with pytest.raises(ValueError, match="capture_id"):
        dataclasses.replace(empty, entries=(first, conflicting_capture))

    conflicting_artifact = dataclasses.replace(
        source_entry(entry_id="entry-two", cue_index=2),
        rytm_source=dataclasses.replace(
            first.rytm_source,
            capture_id="other-capture",
            sysex=sysex(first.rytm_source.sysex.artifact_id, 9),
        ),
    )
    with pytest.raises(ValueError, match="artifact_id"):
        dataclasses.replace(empty, entries=(first, conflicting_artifact))

    first_candidate = dataclasses.replace(first, candidates=(candidate(),))
    second_candidate_value = candidate(candidate_id="candidate-two")
    second_candidate_value = dataclasses.replace(
        second_candidate_value,
        analog_four_candidate=dataclasses.replace(
            second_candidate_value.analog_four_candidate,
            sysex=sysex(candidate().analog_four_candidate.sysex.artifact_id, 9),
        ),
    )
    second_candidate = dataclasses.replace(
        source_entry(entry_id="entry-two", cue_index=2),
        candidates=(second_candidate_value,),
    )
    with pytest.raises(ValueError, match="artifact_id"):
        dataclasses.replace(empty, entries=(first_candidate, second_candidate))

    mixed = dataclasses.replace(
        empty,
        entries=(
            source_entry(),
            dataclasses.replace(_candidate_entry(), entry_id="entry-two", cue_index=2),
        ),
    )
    assert mixed.status == "source"
    with pytest.raises(ValueError, match="filename-safe"):
        mixed.entry("Bad")
    with pytest.raises(ValueError, match="filename-safe"):
        mixed.sysex_artifact("Bad")
