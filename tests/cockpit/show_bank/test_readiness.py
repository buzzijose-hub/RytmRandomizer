from __future__ import annotations

import dataclasses
from collections.abc import Callable
from copy import copy
from datetime import datetime

import pytest

from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    RetainedSysexArtifact,
    ShowBank,
    ShowKitEvidence,
)
from rytm_randomizer.cockpit.show_bank.readiness import (
    add_candidate,
    add_entry,
    attach_retained_sysex,
    attest_hardware_save,
    create_show_bank,
    duplicate_entry,
    is_catalog_only_show_bank,
    mark_favorite,
    normalize_catalog_import,
    record_recapture,
    record_rytm_live_audition,
    record_show_time_preflight,
    remove_entry,
    reorder_entries,
    return_to_source,
    select_candidate,
    show_bank_readiness,
    update_bank_metadata,
    update_entry_metadata,
    utc_now,
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
    SECOND_PREFLIGHT_CAPTURED_AT,
    SECOND_PREFLIGHT_CHECKED_AT,
    candidate,
    recapture,
    source_entry,
)

pytestmark = pytest.mark.fast


def clock() -> datetime:
    return LATER


def clock_at(value: datetime) -> Callable[[], datetime]:
    return lambda: value


def fresh_bank() -> ShowBank:
    bank = create_show_bank(bank_id="show", name="Show", clock=lambda: NOW)
    return add_entry(bank, source_entry(), clock=clock)


def verified_bank() -> ShowBank:
    bank = add_candidate(fresh_bank(), "entry-one", candidate(), select=True, clock=clock)
    bank = mark_favorite(bank, "entry-one", clock=clock)
    bank = attest_hardware_save(
        bank,
        "entry-one",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        hardware_slot=64,
        note="Saved on Rytm",
        clock=clock_at(SAVE_AT),
    )
    bank = attest_hardware_save(
        bank,
        "entry-one",
        device_id=A4_SHOW_KIT_DEVICE_ID,
        hardware_slot=64,
        note="Saved on A4",
        clock=clock_at(SAVE_AT),
    )
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(RYTM_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        comparison_reason="Rytm mapped fields matched",
        clock=clock_at(RECORDED_AT),
    )
    return record_recapture(
        bank,
        "entry-one",
        recapture(A4_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=A4_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=A4_SEMANTIC_FINGERPRINT,
        comparison_reason="A4 Filter1 Frequency matched",
        clock=clock_at(RECORDED_AT),
    )


def test_lifecycle_keeps_selection_live_favorite_save_and_verification_distinct() -> None:
    bank = fresh_bank()
    assert bank.status == "source"
    bank = add_candidate(bank, "entry-one", candidate(), clock=clock)
    assert bank.status == "candidate"
    assert bank.entry("entry-one").selected_candidate_id is None
    bank = select_candidate(bank, "entry-one", "candidate-one", clock=clock)
    assert bank.entry("entry-one").favorite is None
    bank = record_rytm_live_audition(bank, "entry-one", clock=clock)
    live = bank.entry("entry-one")
    assert live.rytm_live_auditioned_candidate_id == "candidate-one"
    assert live.rytm_live_auditioned_at == LATER
    assert live.status == "candidate"
    bank = mark_favorite(bank, "entry-one", notes=("Keeper",), clock=clock)
    assert bank.status == "favorite"
    bank = attest_hardware_save(
        bank,
        "entry-one",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        hardware_slot=64,
        note="manual save",
        clock=clock_at(SAVE_AT),
    )
    assert bank.status == "favorite"
    bank = attest_hardware_save(
        bank,
        "entry-one",
        device_id=A4_SHOW_KIT_DEVICE_ID,
        hardware_slot=64,
        note="manual save",
        clock=clock_at(SAVE_AT),
    )
    assert bank.status == "hardware-saved"
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(RYTM_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
        comparison_reason="semantic match",
        clock=clock_at(RECORDED_AT),
    )
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(A4_SHOW_KIT_DEVICE_ID),
        source_semantic_fingerprint=A4_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=A4_SEMANTIC_FINGERPRINT,
        comparison_reason="semantic match",
        clock=clock_at(RECORDED_AT),
    )
    assert bank.status == "verified"


def test_show_time_preflight_grants_and_revokes_using_full_capture_identity() -> None:
    bank = verified_bank()
    mismatch = record_show_time_preflight(
        bank,
        "entry-one",
        current_rytm_capture=recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            matching_full=False,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-preflight-one",
        ),
        current_analog_four_capture=recapture(
            A4_SHOW_KIT_DEVICE_ID,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="a4-preflight-one",
        ),
        reason="fresh preflight",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    entry = mismatch.entry("entry-one")
    assert entry.status == "verified"
    assert entry.show_time_preflight is not None
    assert not entry.show_time_preflight.ready
    assert entry.show_time_preflight.observed_rytm_capture_id == "rytm-preflight-one"
    assert entry.show_time_preflight.observed_a4_capture_id == "a4-preflight-one"
    assert entry.show_time_preflight.observed_rytm_captured_at == PREFLIGHT_CAPTURED_AT
    assert entry.show_time_preflight.observed_a4_captured_at == PREFLIGHT_CAPTURED_AT
    assert entry.show_ready_at is None
    ready = record_show_time_preflight(
        mismatch,
        "entry-one",
        current_rytm_capture=recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            captured_at=SECOND_PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-preflight-two",
        ),
        current_analog_four_capture=recapture(
            A4_SHOW_KIT_DEVICE_ID,
            captured_at=SECOND_PREFLIGHT_CAPTURED_AT,
            capture_id="a4-preflight-two",
        ),
        reason="fresh preflight matched",
        clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
    )
    assert ready.status == "show-ready"
    assert show_bank_readiness(ready).ready

    returned = return_to_source(
        ready,
        "entry-one",
        clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
    )
    returned_entry = returned.entry("entry-one")
    assert returned_entry.selected_candidate_id is None
    assert returned_entry.rytm_live_auditioned_at is None
    assert returned_entry.favorite == ready.entry("entry-one").favorite
    assert returned_entry.rytm_recapture == ready.entry("entry-one").rytm_recapture
    assert returned_entry.show_ready_at is None
    assert returned.status == "verified"


def test_duplicate_clears_transient_state_but_preserves_durable_favorite_evidence() -> None:
    bank = record_rytm_live_audition(
        verified_bank(),
        "entry-one",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    bank = record_show_time_preflight(
        bank,
        "entry-one",
        current_rytm_capture=recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            captured_at=SECOND_PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-current",
        ),
        current_analog_four_capture=recapture(
            A4_SHOW_KIT_DEVICE_ID,
            captured_at=SECOND_PREFLIGHT_CAPTURED_AT,
            capture_id="a4-current",
        ),
        reason="fresh captures match",
        clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
    )
    original = bank.entry("entry-one")

    duplicated = duplicate_entry(
        bank,
        "entry-one",
        "entry-copy",
        clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
    ).entry("entry-copy")

    assert duplicated.selected_candidate_id is None
    assert duplicated.rytm_live_auditioned_candidate_id is None
    assert duplicated.rytm_live_auditioned_at is None
    assert duplicated.show_time_preflight is None
    assert duplicated.show_ready_at is None
    assert duplicated.favorite == original.favorite
    assert duplicated.rytm_hardware_save == original.rytm_hardware_save
    assert duplicated.analog_four_hardware_save == original.analog_four_hardware_save
    assert duplicated.rytm_recapture == original.rytm_recapture
    assert duplicated.analog_four_recapture == original.analog_four_recapture
    assert duplicated.status == "verified"


def test_favorite_replacement_requires_explicit_opt_in() -> None:
    verified = verified_bank()
    same = mark_favorite(
        verified,
        "entry-one",
        notes=("updated note",),
        clock=clock_at(PREFLIGHT_CAPTURED_AT),
    )
    assert same.entry("entry-one").favorite is not None
    assert verified.entry("entry-one").favorite is not None
    assert (
        same.entry("entry-one").favorite.selected_at
        == verified.entry("entry-one").favorite.selected_at
    )
    assert same.entry("entry-one").rytm_recapture == verified.entry("entry-one").rytm_recapture

    selected_other = add_candidate(
        verified,
        "entry-one",
        candidate(candidate_id="candidate-two"),
        select=True,
        clock=clock_at(PREFLIGHT_CAPTURED_AT),
    )
    with pytest.raises(ValueError, match="replace_existing=True"):
        mark_favorite(
            selected_other,
            "entry-one",
            clock=clock_at(PREFLIGHT_CHECKED_AT),
        )
    with pytest.raises(TypeError, match="boolean"):
        mark_favorite(
            selected_other,
            "entry-one",
            replace_existing=1,  # type: ignore[arg-type]
            clock=clock_at(PREFLIGHT_CHECKED_AT),
        )

    replaced = mark_favorite(
        selected_other,
        "entry-one",
        replace_existing=True,
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    ).entry("entry-one")
    assert replaced.favorite is not None
    assert replaced.favorite.candidate_id == "candidate-two"
    assert replaced.rytm_hardware_save is None
    assert replaced.analog_four_hardware_save is None
    assert replaced.rytm_recapture is None
    assert replaced.analog_four_recapture is None


def test_mismatched_or_unsupported_semantic_recapture_fails_closed() -> None:
    bank = verified_bank()
    bank = record_recapture(
        bank,
        "entry-one",
        recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            matching_full=False,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-unmapped-recapture",
        ),
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=None,
        comparison_reason="semantic mapping unsupported",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    assert bank.status == "hardware-saved"
    readiness = show_bank_readiness(bank)
    assert not readiness.ready
    assert any("Rytm recapture" in reason for reason in readiness.blocked_reasons)


def test_recapture_computes_source_match_without_granting_verification() -> None:
    bank = record_recapture(
        verified_bank(),
        "entry-one",
        recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-source-match",
        ),
        source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        observed_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
        comparison_reason="favorite failed; source semantics matched",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    evidence = bank.entry("entry-one").rytm_recapture
    assert evidence is not None
    assert evidence.matches_source
    assert not evidence.matches_candidate
    assert bank.status == "hardware-saved"


def test_duplicate_reorder_remove_and_metadata_transitions_are_deterministic() -> None:
    bank = verified_bank()
    bank = duplicate_entry(
        bank,
        "entry-one",
        "entry-two",
        name="Second cue",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    duplicate = bank.entry("entry-two")
    assert duplicate.favorite == bank.entry("entry-one").favorite
    assert duplicate.rytm_recapture == bank.entry("entry-one").rytm_recapture
    assert duplicate.rytm_live_auditioned_at is None
    assert duplicate.cue_index == 2
    bank = reorder_entries(
        bank,
        ("entry-two", "entry-one"),
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    assert [entry.entry_id for entry in bank.entries] == ["entry-two", "entry-one"]
    bank = update_entry_metadata(
        bank,
        "entry-two",
        name="Renamed",
        description="Description",
        oxi=duplicate.oxi,
        audition_notes=("a",),
        energy_level=5,
        energy_notes=("e",),
        transition_notes=("t",),
        recovery_notes=("r",),
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    bank = update_bank_metadata(
        bank,
        name="Renamed show",
        description="New description",
        notes=("note",),
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    assert bank.name == "Renamed show"
    assert bank.entry("entry-two").name == "Renamed"
    assert bank.entry("entry-two").energy_level == 5
    bank = remove_entry(bank, "entry-two", clock=clock_at(PREFLIGHT_CHECKED_AT))
    assert tuple(entry.cue_index for entry in bank.entries) == (1,)


@pytest.mark.parametrize(
    "operation",
    [
        lambda bank: select_candidate(bank, "entry-one", "missing", clock=clock),
        lambda bank: mark_favorite(bank, "entry-one", clock=clock),
        lambda bank: record_rytm_live_audition(bank, "entry-one", clock=clock),
        lambda bank: attest_hardware_save(
            bank,
            "entry-one",
            device_id=RYTM_SHOW_KIT_DEVICE_ID,
            hardware_slot=20,
            note="save",
            clock=clock,
        ),
        lambda bank: reorder_entries(bank, ("missing",), clock=clock),
        lambda bank: remove_entry(bank, "missing", clock=clock),
    ],
)
def test_invalid_transitions_leave_the_original_bank_unchanged(operation) -> None:
    bank = fresh_bank()
    with pytest.raises(ValueError):
        operation(bank)
    assert bank.revision == 1
    assert bank.status == "source"


def test_clock_must_be_timezone_aware() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        create_show_bank(
            bank_id="show",
            name="Show",
            clock=lambda: datetime(2026, 9, 4),
        )


def test_empty_bank_readiness_is_explicitly_blocked() -> None:
    bank = create_show_bank(bank_id="show", name="Show", clock=lambda: NOW)
    result = show_bank_readiness(bank)
    assert not result.ready
    assert result.blocked_reasons == ("show bank has no cue entries",)


def test_catalog_import_is_idempotently_marked_and_revokes_runtime_authority() -> None:
    assert utc_now().tzinfo is not None
    bank = record_rytm_live_audition(
        verified_bank(),
        "entry-one",
        clock=clock_at(PREFLIGHT_CAPTURED_AT),
    )
    original_evidence = ShowKitEvidence(
        evidence_id="operator-proof",
        status="operator-attested",
        source="operator",
        observed_at=LATER,
    )
    bank = dataclasses.replace(bank, evidence=(original_evidence,))
    assert not is_catalog_only_show_bank(bank)

    imported = normalize_catalog_import(
        bank,
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    entry = imported.entry("entry-one")
    assert is_catalog_only_show_bank(imported)
    assert entry.selected_candidate_id is None
    assert entry.rytm_live_auditioned_candidate_id is None
    assert entry.show_ready_at is None
    assert entry.favorite == bank.entry("entry-one").favorite
    assert entry.rytm_recapture == bank.entry("entry-one").rytm_recapture
    assert original_evidence in imported.evidence

    marker = next(
        evidence
        for evidence in imported.evidence
        if evidence.evidence_id == "imported-catalog-only"
    )
    normalized_again = normalize_catalog_import(
        dataclasses.replace(imported, evidence=(marker, original_evidence, marker)),
        clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
    )
    assert (
        sum(
            evidence.evidence_id == "imported-catalog-only"
            for evidence in normalized_again.evidence
        )
        == 1
    )


def test_collection_and_revision_guards_are_explicit() -> None:
    bank = fresh_bank()
    with pytest.raises(ValueError, match="duplicate show-bank"):
        add_entry(bank, source_entry(), clock=clock)
    with pytest.raises(ValueError, match="duplicate show-bank"):
        duplicate_entry(bank, "entry-one", "entry-one", clock=clock)
    second = duplicate_entry(bank, "entry-one", "entry-two", clock=clock)
    with pytest.raises(ValueError, match="unique"):
        reorder_entries(second, ("entry-one", "entry-one"), clock=clock)

    with_candidate = add_candidate(bank, "entry-one", candidate(), clock=clock)
    with pytest.raises(ValueError, match="duplicate candidate"):
        add_candidate(with_candidate, "entry-one", candidate(), clock=clock)

    maximum = dataclasses.replace(bank, revision=99_999_999)
    with pytest.raises(ValueError, match="revision limit"):
        remove_entry(maximum, "entry-one", clock=clock)
    with pytest.raises(ValueError, match="revision limit"):
        update_bank_metadata(
            maximum,
            name="Show",
            description="",
            notes=(),
            clock=clock,
        )


def test_recapture_and_preflight_prerequisites_fail_closed() -> None:
    source = fresh_bank()
    with pytest.raises(ValueError, match="requires a favorite"):
        record_recapture(
            source,
            "entry-one",
            recapture(RYTM_SHOW_KIT_DEVICE_ID),
            source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
            observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
            comparison_reason="compare",
            clock=clock,
        )

    favorite = mark_favorite(
        add_candidate(source, "entry-one", candidate(), select=True, clock=clock),
        "entry-one",
        clock=clock,
    )
    with pytest.raises(ValueError, match="Rytm hardware-save"):
        record_recapture(
            favorite,
            "entry-one",
            recapture(RYTM_SHOW_KIT_DEVICE_ID),
            source_semantic_fingerprint=RYTM_SOURCE_SEMANTIC_FINGERPRINT,
            observed_semantic_fingerprint=RYTM_SEMANTIC_FINGERPRINT,
            comparison_reason="compare",
            clock=clock,
        )
    rytm_saved = attest_hardware_save(
        favorite,
        "entry-one",
        device_id=RYTM_SHOW_KIT_DEVICE_ID,
        hardware_slot=1,
        note="saved",
        clock=clock,
    )
    with pytest.raises(ValueError, match="A4 hardware-save"):
        record_recapture(
            rytm_saved,
            "entry-one",
            recapture(A4_SHOW_KIT_DEVICE_ID),
            source_semantic_fingerprint=A4_SOURCE_SEMANTIC_FINGERPRINT,
            observed_semantic_fingerprint=A4_SEMANTIC_FINGERPRINT,
            comparison_reason="compare",
            clock=clock,
        )

    with pytest.raises(ValueError, match="requires a verified"):
        record_show_time_preflight(
            source,
            "entry-one",
            current_rytm_capture=recapture(RYTM_SHOW_KIT_DEVICE_ID),
            current_analog_four_capture=recapture(A4_SHOW_KIT_DEVICE_ID),
            reason="preflight",
            clock=clock,
        )
    verified = verified_bank()
    with pytest.raises(ValueError, match="Rytm capture"):
        record_show_time_preflight(
            verified,
            "entry-one",
            current_rytm_capture=recapture(A4_SHOW_KIT_DEVICE_ID),
            current_analog_four_capture=recapture(A4_SHOW_KIT_DEVICE_ID),
            reason="preflight",
            clock=clock,
        )
    with pytest.raises(ValueError, match="A4 capture"):
        record_show_time_preflight(
            verified,
            "entry-one",
            current_rytm_capture=recapture(RYTM_SHOW_KIT_DEVICE_ID),
            current_analog_four_capture=recapture(RYTM_SHOW_KIT_DEVICE_ID),
            reason="preflight",
            clock=clock,
        )


def test_preflight_requires_fresh_capture_provenance_on_every_run() -> None:
    bank = verified_bank()
    with pytest.raises(ValueError, match="Rytm capture must be newer"):
        record_show_time_preflight(
            bank,
            "entry-one",
            current_rytm_capture=recapture(
                RYTM_SHOW_KIT_DEVICE_ID,
                captured_at=RECORDED_AT,
                capture_id="rytm-stale",
            ),
            current_analog_four_capture=recapture(
                A4_SHOW_KIT_DEVICE_ID,
                captured_at=PREFLIGHT_CAPTURED_AT,
                capture_id="a4-fresh",
            ),
            reason="stale Rytm capture",
            clock=clock_at(PREFLIGHT_CHECKED_AT),
        )

    first = record_show_time_preflight(
        bank,
        "entry-one",
        current_rytm_capture=recapture(
            RYTM_SHOW_KIT_DEVICE_ID,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="rytm-first",
        ),
        current_analog_four_capture=recapture(
            A4_SHOW_KIT_DEVICE_ID,
            captured_at=PREFLIGHT_CAPTURED_AT,
            capture_id="a4-first",
        ),
        reason="first preflight",
        clock=clock_at(PREFLIGHT_CHECKED_AT),
    )
    with pytest.raises(ValueError, match="A4 capture must be newer"):
        record_show_time_preflight(
            first,
            "entry-one",
            current_rytm_capture=recapture(
                RYTM_SHOW_KIT_DEVICE_ID,
                captured_at=SECOND_PREFLIGHT_CAPTURED_AT,
                capture_id="rytm-second",
            ),
            current_analog_four_capture=recapture(
                A4_SHOW_KIT_DEVICE_ID,
                captured_at=PREFLIGHT_CHECKED_AT,
                capture_id="a4-stale",
            ),
            reason="second preflight with stale A4 provenance",
            clock=clock_at(SECOND_PREFLIGHT_CHECKED_AT),
        )


def test_preflight_requires_paired_hardware_slots_even_with_verified_recaptures() -> None:
    bank = verified_bank()
    entry = bank.entry("entry-one")
    assert entry.rytm_hardware_save is not None
    assert entry.analog_four_hardware_save is not None
    rytm_save_without_slot = copy(entry.rytm_hardware_save)
    analog_four_save_without_slot = copy(entry.analog_four_hardware_save)
    object.__setattr__(rytm_save_without_slot, "hardware_slot", None)
    object.__setattr__(analog_four_save_without_slot, "hardware_slot", None)
    without_slots = copy(entry)
    object.__setattr__(without_slots, "rytm_hardware_save", rytm_save_without_slot)
    object.__setattr__(
        without_slots,
        "analog_four_hardware_save",
        analog_four_save_without_slot,
    )
    bank_without_slots = copy(bank)
    object.__setattr__(bank_without_slots, "entries", (without_slots,))

    with pytest.raises(ValueError, match="requires paired hardware slots"):
        record_show_time_preflight(
            bank_without_slots,
            "entry-one",
            current_rytm_capture=recapture(
                RYTM_SHOW_KIT_DEVICE_ID,
                captured_at=PREFLIGHT_CAPTURED_AT,
                capture_id="rytm-fresh",
            ),
            current_analog_four_capture=recapture(
                A4_SHOW_KIT_DEVICE_ID,
                captured_at=PREFLIGHT_CAPTURED_AT,
                capture_id="a4-fresh",
            ),
            reason="preflight without paired source slots",
            clock=clock_at(PREFLIGHT_CHECKED_AT),
        )


def _retained_for(sysex) -> RetainedSysexArtifact:
    return RetainedSysexArtifact(
        artifact_name=f"{sysex.frame_sha256}.syx",
        sha256=sysex.frame_sha256,
        byte_count=sysex.frame_bytes,
    )


def test_attach_retained_sysex_updates_sources_candidates_and_recaptures() -> None:
    bank = verified_bank()
    entry = bank.entry("entry-one")
    assert entry.rytm_recapture is not None
    assert entry.analog_four_recapture is not None
    identities = (
        entry.rytm_source.sysex,
        entry.analog_four_source.sysex,
        entry.candidates[0].analog_four_candidate.sysex,
        entry.rytm_recapture.capture.sysex,
        entry.analog_four_recapture.capture.sysex,
    )
    for identity in identities:
        artifact = _retained_for(identity)
        bank = attach_retained_sysex(
            bank,
            identity.artifact_id,
            artifact,
            clock=clock,
        )
        assert bank.sysex_artifact(identity.artifact_id).retained == artifact

    identity = bank.entry("entry-one").rytm_source.sysex
    artifact = _retained_for(identity)
    assert attach_retained_sysex(bank, identity.artifact_id, artifact, clock=clock) is bank
    with pytest.raises(ValueError, match="already retained"):
        attach_retained_sysex(
            bank,
            identity.artifact_id,
            RetainedSysexArtifact(f"{'b' * 64}.syx", "b" * 64, 3),
            clock=clock,
        )

    fresh = fresh_bank()
    with pytest.raises(ValueError, match="do not match"):
        attach_retained_sysex(
            fresh,
            fresh.entry("entry-one").rytm_source.sysex.artifact_id,
            RetainedSysexArtifact(f"{'b' * 64}.syx", "b" * 64, 3),
            clock=clock,
        )
