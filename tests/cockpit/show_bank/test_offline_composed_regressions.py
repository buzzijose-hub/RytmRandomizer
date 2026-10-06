"""Public native replay and persistence boundaries with retained RIO145 evidence."""

from __future__ import annotations

import asyncio
import hashlib
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest
from test_devices_strategies_analog_four_native_fields import _patch_source

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.a4_preparation import A4PreparationReport
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    AnalogFourCandidateValue,
    AnalogFourNativeCandidateValue,
    ShowBank,
    ShowBankEntry,
    ShowKitCandidate,
)
from rytm_randomizer.cockpit.export import writer as writer_module
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.a4_preparation import (
    A4PreparationContext,
    prepare_a4_audition,
)
from rytm_randomizer.cockpit.show_bank.export import ShowPackService, verify_show_bank_frames
from rytm_randomizer.cockpit.show_bank.forge import (
    analog_four_capture_semantic_fingerprint,
    analog_four_recapture_semantically_matches,
    forge_candidate_pair,
)
from rytm_randomizer.cockpit.show_bank.store import (
    ShowBankStore,
    validate_show_bank_capture_frame,
)
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.data.analog_four_saved_kit_layout import A4_SAVED_KIT_OBJECT_SIZE
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.observability.errors import DataError
from rytm_randomizer.snapshot.mutation_scope import MutationScope

from .test_native_offline_journey import (
    _CORE,
    _RIO,
    _disk,
    _favorite,
    _frame,
    _generate,
    _journey,
    _session,
)
from .test_offline_retention import generate_offline, offline_workspace

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def _review(
    entry: ShowBankEntry, source_frame: bytes, candidate_frame: bytes
) -> A4PreparationReport:
    candidate = entry.selected_candidate
    assert candidate is not None
    scope = candidate.recipe.analog_four_scope
    return prepare_a4_audition(
        entry=entry,
        source_frame=source_frame,
        candidate_frame=candidate_frame,
        context=A4PreparationContext(
            scope=MutationScope(frozenset(scope.target_ids), frozenset(scope.locked_ids)),
            capture_after=entry.updated_at,
            checked_at=entry.updated_at,
            current_capture=None,
            active_candidate_id=candidate.candidate_id,
            session_connected=False,
            candidate_is_local=False,
            source_reloaded=False,
            output_port_name=None,
        ),
    )


def _replace_candidate(bank: ShowBank, candidate: ShowKitCandidate) -> ShowBank:
    entry = bank.entries[0]
    return replace(
        bank,
        entries=(
            replace(
                entry,
                candidates=tuple(
                    candidate if item.candidate_id == candidate.candidate_id else item
                    for item in entry.candidates
                ),
            ),
        ),
    )


@pytest.mark.parametrize(
    "field,value,message",
    [
        ("track_id", True, "registered domain"),
        ("track_id", 0, "registered domain"),
        ("track_id", 5, "registered domain"),
        ("encoded_native", True, "non-boolean integer"),
        ("encoded_native", -1, "non-boolean integer"),
        ("encoded_native", 65536, "non-boolean integer"),
        ("unpacked_offsets", [10], "bounded distinct tuple"),
        ("unpacked_offsets", (), "bounded distinct tuple"),
        ("unpacked_offsets", (10, 11, 12), "bounded distinct tuple"),
        ("unpacked_offsets", (10, 10), "bounded distinct tuple"),
        ("unpacked_offsets", (True,), "bounded distinct tuple"),
        ("unpacked_offsets", (-1,), "bounded distinct tuple"),
        ("unpacked_offsets", (A4_SAVED_KIT_OBJECT_SIZE,), "bounded distinct tuple"),
    ],
)
def test_native_claim_constructor_refuses_noncanonical_scalars_and_offsets(
    field: str, value: object, message: str
) -> None:
    cell = (
        get_analog_four_native_field_capability()
        .read_native_fields((_RIO / _CORE).read_bytes())
        .value("filter2_resonance", 1)
    )
    claim = AnalogFourNativeCandidateValue(
        cell.track,
        cell.parameter,
        cell.screen_value,
        cell.encoded_native,
        cell.metadata.native_encoding.value,
        cell.unpacked_offsets,
    )
    with pytest.raises(ValueError, match=message):
        replace(claim, **{field: value})
    assert AnalogFourNativeCandidateValue.from_dict(claim.to_dict()) == claim


@pytest.mark.parametrize("mismatch", ["snapshot", "profile-id", "profile-content", "a4-source"])
def test_forge_rejects_source_and_retained_profile_mismatch_before_publication(
    tmp_path: Path, mismatch: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    bank = journey.workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    source = journey.workspace.source_snapshot(journey.bank_id, journey.entry_id)
    profile = journey.profile
    a4_source = journey.originals[ANALOG_FOUR_DEVICE_ID]
    if mismatch == "snapshot":
        source = replace(source, snapshot_id="another-source")
        message = "source snapshot does not match"
    elif mismatch == "profile-id":
        profile = replace(profile, profile_id="another-profile")
        message = "active profile does not match"
    elif mismatch == "profile-content":
        profile = replace(profile, name="Same ID, different authored content")
        message = "profile content does not match"
    else:
        a4_source = (_RIO / "A4_Test2_T1_OSC1_FIN_P1_Kit.syx").read_bytes()
        message = "source bytes do not match"
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match=message):
        forge_candidate_pair(
            entry=entry,
            rytm_source_snapshot=source,
            analog_four_source_frame=a4_source,
            profile=profile,
            recipe=candidate.recipe,
            now=bank.updated_at,
        )
    assert journey.workspace.bank(journey.bank_id) == bank
    assert _disk(journey.workspace.store.root) == before


@pytest.mark.parametrize(
    "field", ["amp_decay", "osc1_fine", "env2_depth_a_fraction", "lfo1_phase", "osc1_tracking"]
)
def test_explicit_protected_native_scope_is_refused_without_a_revision_or_files(
    tmp_path: Path, field: str
) -> None:
    journey = _journey(tmp_path)
    bank = journey.workspace.bank(journey.bank_id)
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match="immutable or unestablished"):
        _generate(journey, fields=(field,), count=1)
    assert journey.workspace.bank(journey.bank_id) == bank
    assert _disk(journey.workspace.store.root) == before


@pytest.mark.parametrize("claim", ["encoding", "offset", "screen"])
def test_preparation_refuses_native_claims_that_disagree_with_real_readback(
    tmp_path: Path, claim: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    entry = journey.workspace.bank(journey.bank_id).entry(journey.entry_id)
    value = candidate.analog_four_candidate.values[0]
    changes = {
        "encoding": {"native_encoding": "unsigned-big-endian-q8.8"},
        "offset": {"unpacked_offsets": (value.unpacked_offsets[0] + 1,)},
        "screen": {"screen_value": "not-the-canonical-readback"},
    }
    altered = replace(
        candidate,
        analog_four_candidate=replace(
            candidate.analog_four_candidate, values=(replace(value, **changes[claim]),)
        ),
    )
    report = _review(
        replace(entry, candidates=(altered,)),
        journey.originals[ANALOG_FOUR_DEVICE_ID],
        _frame(journey, candidate),
    )
    assert not report.candidate_bytes_verified
    assert "candidate_bytes_invalid" in report.blocked_reasons
    assert report.changes == () and not report.ready
    assert report.output_authority == "offline-review-only"


@pytest.mark.parametrize("tamper", ["hidden-pitch-bit", "excluded-amp", "native-no-op"])
def test_self_consistently_rehashed_native_frames_cannot_escape_recipe_replay(
    tmp_path: Path, tamper: str
) -> None:
    journey = _journey(tmp_path, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    (candidate,) = _generate(
        journey, fields=("osc1_tune",), depth=0.0 if tamper == "native-no-op" else 0.25, count=1
    )
    bank = _favorite(journey, candidate)
    frame = _frame(journey, candidate)
    capability = get_analog_four_native_field_capability()
    before = capability.read_native_fields(frame)
    field = "amp_decay" if tamper == "excluded-amp" else "osc1_tune"
    cell = before.value(field, 1)
    offset = cell.unpacked_offsets[-1]
    changed = _patch_source(frame, (offset,), bytes((cell.native_bytes[-1] ^ 1,)))
    after = capability.read_native_fields(changed)
    if field == "osc1_tune":
        assert after.value(field, 1).screen_value == cell.screen_value
        assert after.value("osc1_fine", 1).screen_value == before.value("osc1_fine", 1).screen_value
    digest = hashlib.sha256(changed).hexdigest()
    a4 = candidate.analog_four_candidate
    values = a4.values
    if tamper == "hidden-pitch-bit":
        assert len(values) == 1
        values = (replace(values[0], encoded_native=after.value(field, 1).encoded_native),)
    a4 = replace(
        a4,
        artifact_fingerprint=digest[:16],
        sysex=replace(a4.sysex, frame_sha256=digest, retained=None),
        values=values,
    )
    if values:
        a4 = replace(
            a4,
            semantic_fingerprint=analog_four_capture_semantic_fingerprint(
                decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, changed), a4
            ),
        )
    altered = replace(candidate, analog_four_candidate=a4)
    forged_bank = _replace_candidate(bank, altered)
    frames = {
        item.artifact_id: journey.workspace.store.read_retained(item.retained)
        for item in bank.sysex_artifacts()
    }
    frames[a4.sysex.artifact_id] = changed
    disk = _disk(journey.workspace.store.root)
    with pytest.raises(DataError, match="deterministic recipe replay") as failure:
        verify_show_bank_frames(forged_bank, frames)
    assert failure.value.context["category"] == "cross-reference"
    assert _disk(journey.workspace.store.root) == disk
    if tamper == "hidden-pitch-bit":
        report = _review(
            forged_bank.entry(journey.entry_id), journey.originals[ANALOG_FOUR_DEVICE_ID], changed
        )
        assert not report.candidate_bytes_verified
        assert "candidate_bytes_invalid" in report.blocked_reasons
        assert not analog_four_recapture_semantically_matches(
            decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, changed),
            candidate.analog_four_candidate,
        )


@pytest.mark.parametrize("identity", ["hash", "size"])
def test_capture_validation_refuses_declared_identity_before_decoding(
    tmp_path: Path, identity: str
) -> None:
    journey = _journey(tmp_path)
    entry = journey.workspace.bank(journey.bank_id).entry(journey.entry_id)
    source = entry.analog_four_source
    sysex = replace(
        source.sysex,
        retained=None,
        **(
            {"frame_sha256": "0" * 64}
            if identity == "hash"
            else {"frame_bytes": source.sysex.frame_bytes + 1}
        ),
    )
    before = _disk(journey.workspace.store.root)
    with pytest.raises(DataError, match="declared identity") as failure:
        validate_show_bank_capture_frame(
            replace(source, sysex=sysex), journey.originals[ANALOG_FOUR_DEVICE_ID]
        )
    assert failure.value.context["category"] == "hash"
    assert _disk(journey.workspace.store.root) == before


def test_missing_legacy_candidate_bytes_are_blocked_and_never_reconstructed(tmp_path: Path) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    bank = journey.workspace.bank(journey.bank_id)
    without_bytes = replace(
        candidate,
        analog_four_candidate=replace(
            candidate.analog_four_candidate,
            sysex=replace(candidate.analog_four_candidate.sysex, retained=None),
        ),
    )
    legacy_bank = replace(_replace_candidate(bank, without_bytes), revision=bank.revision + 1)
    journey.workspace.store.save(legacy_bank)
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    before = _disk(journey.workspace.store.root)
    report = restarted.prepare_a4_review(
        bank.bank_id,
        journey.entry_id,
        legacy_bank.revision,
        captures={},
        target_ids=(1, 2),
        locked_ids=(2,),
        active_candidate_id=candidate.candidate_id,
        output_port_name=None,
    )
    assert "candidate_bytes_unavailable" in report.blocked_reasons
    assert not report.candidate_bytes_verified and not report.ready
    with pytest.raises(ValueError, match="not retained"):
        restarted.select_candidate(
            bank.bank_id,
            journey.entry_id,
            candidate.candidate_id,
            legacy_bank.revision,
            offline_only=True,
        )
    with pytest.raises(ValueError, match="no longer in memory"):
        restarted.retain_capture(
            bank.bank_id,
            journey.entry_id,
            legacy_bank.revision,
            capture_kind="candidate",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )
    assert restarted.bank(bank.bank_id) == legacy_bank
    assert _disk(journey.workspace.store.root) == before


def test_interrupted_publication_cache_can_retain_an_exact_legacy_candidate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    (previous,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    pending = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=workspace.source_snapshot(bank.bank_id, entry.entry_id),
        analog_four_source_frame=journey.originals[ANALOG_FOUR_DEVICE_ID],
        profile=journey.profile,
        recipe=replace(previous.recipe, seed=100),
        now=bank.updated_at,
    )
    before = _disk(workspace.store.root)
    publish = writer_module._publish_no_overwrite

    def interrupted(source, destination, *, on_published=None):
        if destination.name.endswith(".show-bank.json"):
            raise PermissionError("test manifest publication interruption")
        return publish(source, destination, on_published=on_published)

    with monkeypatch.context() as fault:
        fault.setattr(writer_module, "_publish_no_overwrite", interrupted)
        with pytest.raises(writer_module.WriteSetError) as failure:
            _generate(journey, count=1, seed=100)
    assert failure.value.failure_context.phase == "publication"
    assert failure.value.failure_context.artifact_name.endswith(".show-bank.json")
    assert workspace.bank(bank.bank_id) == bank
    assert _disk(workspace.store.root) == before
    legacy_entry = replace(
        entry, candidates=(pending.candidate,), selected_candidate_id=pending.candidate.candidate_id
    )
    legacy_bank = replace(
        bank, bank_id="legacy-cache-recovery", revision=0, entries=(legacy_entry,)
    )
    workspace.store.save(legacy_bank)
    workspace.register_imported(legacy_bank)
    report = workspace.prepare_a4_review(
        legacy_bank.bank_id,
        entry.entry_id,
        0,
        captures={},
        target_ids=(1, 2),
        locked_ids=(2,),
        active_candidate_id=pending.candidate.candidate_id,
        output_port_name=None,
    )
    assert report.candidate_bytes_verified and not report.ready
    retained = workspace.retain_capture(
        legacy_bank.bank_id,
        entry.entry_id,
        0,
        capture_kind="candidate",
        device_id=A4_SHOW_KIT_DEVICE_ID,
        current_captures={},
    )
    artifact = retained.selected_candidate.analog_four_candidate.sysex.retained
    assert (
        artifact is not None
        and workspace.store.read_retained(artifact) == pending.analog_four_frame
    )
    restarted = ShowKitForgeWorkspace(ShowBankStore(workspace.store.root))
    assert (
        restarted.original_source_frames(legacy_bank.bank_id, entry.entry_id) == journey.originals
    )
    assert restarted.bank(legacy_bank.bank_id).entry(entry.entry_id) == retained


def test_evicted_source_projection_is_rebuilt_from_retained_bytes_with_original_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_module, "MAX_VOLATILE_FRAMES", 1)
    journey = _journey(tmp_path)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    copy = workspace.duplicate(bank.bank_id, journey.entry_id, bank.revision)
    restarted = ShowKitForgeWorkspace(workspace.store)
    first = restarted.source_snapshot(bank.bank_id, journey.entry_id)
    second = restarted.source_snapshot(bank.bank_id, copy.entry_id)
    rebuilt = restarted.source_snapshot(bank.bank_id, journey.entry_id)
    assert first == second == rebuilt
    assert rebuilt.snapshot_id == bank.entry(journey.entry_id).rytm_source.snapshot_id
    assert rebuilt.captured_at == bank.entry(journey.entry_id).rytm_source.captured_at
    assert restarted.original_source_frames(bank.bank_id, copy.entry_id) == journey.originals


def test_retained_source_reassociation_refuses_conflicting_provenance(tmp_path: Path) -> None:
    journey = _journey(tmp_path)
    library = LibraryStore(tmp_path / "library")
    records = {item.device_id: item for item in library.list_records()}
    bank = journey.workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    source = entry.rytm_source
    conflicting = replace(
        bank,
        bank_id="conflicting-provenance",
        revision=0,
        entries=(
            replace(
                entry,
                rytm_source=replace(
                    source,
                    evidence=(replace(source.evidence[0], source="Another retained association"),),
                ),
            ),
        ),
    )
    journey.workspace.store.save(conflicting)
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match="association conflicts"):
        restarted.adopt_retained_sources(
            conflicting.bank_id,
            conflicting.revision,
            library=library,
            rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
            analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
            rytm_slot=20,
            analog_four_slot=21,
        )
    assert restarted.bank(conflicting.bank_id) == conflicting
    assert _disk(journey.workspace.store.root) == before


def test_missing_source_snapshot_identity_blocks_pack_verification_and_import(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path / "source")
    bank = journey.workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    missing = replace(
        bank, entries=(replace(entry, rytm_source=replace(entry.rytm_source, snapshot_id=None)),)
    )
    frames = {
        item.artifact_id: journey.workspace.store.read_retained(item.retained)
        for item in bank.sysex_artifacts()
    }
    with pytest.raises(DataError, match="cannot reconstruct") as failure:
        verify_show_bank_frames(missing, frames)
    assert failure.value.context["category"] == "cross-reference"
    assert failure.value.context["artifact_name"] == entry.rytm_source.sysex.artifact_id
    target = ShowBankStore(tmp_path / "target")
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    verified = service.verify(service.export(bank).package_id)
    with pytest.raises(DataError, match="cannot reconstruct"):
        ShowPackService(tmp_path / "packs", store=target).store_verified_import(
            replace(verified, bank=missing)
        )
    assert not target.root.exists()


def test_legacy_recall_without_registry_profile_is_refused_and_grants_no_output(
    tmp_path: Path,
) -> None:
    workspace, entry, _ = offline_workspace(tmp_path)
    candidates = generate_offline(workspace, entry.entry_id, tmp_path)
    candidate = candidates[0]
    legacy = replace(
        candidate,
        recipe=replace(candidate.recipe, profile_id="lost-legacy-author", profile=None),
        rytm_candidate=replace(candidate.rytm_candidate, profile_id="lost-legacy-author"),
    )
    bank = workspace.bank("offline-bank")
    legacy_bank = replace(_replace_candidate(bank, legacy), revision=bank.revision + 1)
    workspace.store.save(legacy_bank)
    restarted = ShowKitForgeWorkspace(workspace.store)
    session = _session(restarted, bank.bank_id, entry.entry_id, tmp_path)
    assert session.profile_registry.get(legacy.recipe.profile_id) is None
    assert len(legacy.recipe.to_dict()) == 6
    before = _disk(workspace.store.root)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "legacy-profile-missing",
                "command": {
                    "type": "show_bank_select_candidate",
                    "bank_id": bank.bank_id,
                    "entry_id": entry.entry_id,
                    "candidate_id": legacy.candidate_id,
                    "expected_revision": legacy_bank.revision,
                },
            },
            session,
        )
    )
    assert not ack["ok"]
    assert _disk(workspace.store.root) == before
    assert restarted.bank(bank.bank_id) == legacy_bank
    assert session.current_candidate is None and session.current_send_plan is None
    assert (
        session.armed_apply is None and not session.hardware_intent and not session.device.is_armed
    )
    assert not restarted.state_dict()["banks"][0]["readiness"]["show_ready"]


def test_cue_without_a_favorite_does_not_fall_back_to_its_selected_candidate(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    _generate(journey, count=1)
    bank = journey.workspace.bank(journey.bank_id)
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match="no retained favorite"):
        journey.workspace.favorite_context(bank.bank_id, journey.entry_id)
    assert journey.workspace.bank(bank.bank_id) == bank
    assert _disk(journey.workspace.store.root) == before


def test_mixed_legacy_and_native_claims_are_rejected_at_the_public_candidate_boundary(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    legacy_workspace, legacy_entry, _ = offline_workspace(tmp_path / "legacy")
    legacy_value = generate_offline(legacy_workspace, legacy_entry.entry_id, tmp_path)[
        0
    ].analog_four_candidate.values[0]
    assert isinstance(legacy_value, AnalogFourCandidateValue)
    mixed = replace(
        candidate.analog_four_candidate,
        values=(*candidate.analog_four_candidate.values, legacy_value),
    )
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match="representation must match"):
        replace(candidate, analog_four_candidate=mixed)
    assert _disk(journey.workspace.store.root) == before


def test_native_artifact_identity_does_not_replace_canonical_field_rendering(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    first, second = _generate(journey, fields=("filter2_resonance",))
    first_frame, second_frame = _frame(journey, first), _frame(journey, second)
    assert first_frame != second_frame
    altered = replace(
        first,
        analog_four_candidate=replace(
            first.analog_four_candidate,
            artifact_fingerprint=second.analog_four_candidate.artifact_fingerprint,
            sysex=replace(second.analog_four_candidate.sysex, retained=None),
        ),
    )
    entry = journey.workspace.bank(journey.bank_id).entry(journey.entry_id)
    report = _review(
        replace(entry, candidates=(altered,)),
        journey.originals[ANALOG_FOUR_DEVICE_ID],
        second_frame,
    )
    assert not report.candidate_bytes_verified and report.changes == ()
    assert "candidate_bytes_invalid" in report.blocked_reasons
    assert not report.ready and not report.hardware_send_validated


@pytest.mark.parametrize("claim", ["encoding", "offset", "protected-field"])
def test_native_recapture_rejects_claims_outside_canonical_readback(
    tmp_path: Path, claim: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    value = candidate.analog_four_candidate.values[0]
    change = {
        "encoding": {"native_encoding": "unsigned-big-endian-q8.8"},
        "offset": {"unpacked_offsets": (value.unpacked_offsets[0] + 1,)},
        "protected-field": {"parameter": "amp_decay"},
    }[claim]
    altered = replace(candidate.analog_four_candidate, values=(replace(value, **change),))
    recapture = decode_kit_capture_frame(ANALOG_FOUR_DEVICE_ID, _frame(journey, candidate))
    before = _disk(journey.workspace.store.root)
    with pytest.raises(ValueError, match="claim disagrees with canonical readback"):
        analog_four_capture_semantic_fingerprint(recapture, altered)
    assert _disk(journey.workspace.store.root) == before


def test_native_no_op_preparation_accepts_exact_bytes_without_send_or_change_authority(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    (candidate,) = _generate(journey, fields=("osc1_tune",), depth=0.0, count=1)
    entry = journey.workspace.bank(journey.bank_id).entry(journey.entry_id)
    original = journey.originals[ANALOG_FOUR_DEVICE_ID]
    assert _frame(journey, candidate) == original
    report = _review(entry, original, original)
    assert report.candidate_bytes_verified and report.changes == ()
    assert "no_a4_changes" in report.blocked_reasons
    assert not report.ready and not report.hardware_send_validated
    assert report.output_authority == "offline-review-only"


def test_verified_import_replays_protected_scope_claims_before_any_publication(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path / "source")
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = journey.workspace.bank(journey.bank_id)
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    exported = service.export(bank)
    verified = service.verify(exported.package_id)
    altered = replace(
        candidate,
        recipe=replace(
            candidate.recipe,
            analog_four_scope=replace(
                candidate.recipe.analog_four_scope,
                parameters=ParameterSelection((ParameterCell(1, "amp_decay"),)),
            ),
        ),
    )
    target = ShowBankStore(tmp_path / "target")
    original = _disk(exported.package_dir)
    with pytest.raises(DataError, match="deterministic replay failed") as failure:
        ShowPackService(tmp_path / "packs", store=target).store_verified_import(
            replace(verified, bank=_replace_candidate(verified.bank, altered))
        )
    assert failure.value.context["category"] == "cross-reference"
    assert failure.value.context["artifact_name"] == candidate.candidate_id
    assert not target.root.exists() and _disk(exported.package_dir) == original


def test_candidate_artifact_content_collision_refuses_without_overwriting_source(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    (previous,) = _generate(journey, fields=("filter2_resonance",), count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    pending = forge_candidate_pair(
        entry=entry,
        rytm_source_snapshot=workspace.source_snapshot(bank.bank_id, entry.entry_id),
        analog_four_source_frame=journey.originals[ANALOG_FOUR_DEVICE_ID],
        profile=journey.profile,
        recipe=replace(previous.recipe, seed=100),
        now=bank.updated_at,
    )
    artifact = pending.candidate.analog_four_candidate.sysex
    assert artifact.frame_sha256 != entry.analog_four_source.sysex.frame_sha256
    collision = replace(
        bank,
        bank_id="artifact-collision",
        revision=0,
        entries=(
            replace(
                entry,
                candidates=(),
                selected_candidate_id=None,
                analog_four_source=replace(
                    entry.analog_four_source,
                    sysex=replace(
                        entry.analog_four_source.sysex,
                        artifact_id=artifact.artifact_id,
                    ),
                ),
            ),
        ),
    )
    workspace.store.save(collision)
    restarted = ShowKitForgeWorkspace(workspace.store)
    before = _disk(workspace.store.root)
    with pytest.raises(ValueError, match="artifact identity collision"):
        _generate(
            replace(journey, workspace=restarted, bank_id=collision.bank_id),
            fields=("filter2_resonance",),
            seed=100,
            count=1,
        )
    assert restarted.bank(collision.bank_id) == collision
    assert restarted.original_source_frames(collision.bank_id, entry.entry_id) == journey.originals
    assert _disk(workspace.store.root) == before


@pytest.mark.parametrize("action", ["generate", "select", "favorite"])
@pytest.mark.parametrize("flag", [0, 1, "true"])
def test_offline_only_is_a_boolean_boundary_not_truthiness(
    tmp_path: Path, action: str, flag: object
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, count=1)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    before = _disk(workspace.store.root)
    with pytest.raises(ValueError, match="offline_only must be a boolean"):
        if action == "generate":
            recipe = candidate.recipe
            workspace.generate_candidates(
                bank.bank_id,
                journey.entry_id,
                bank.revision,
                profile=journey.profile,
                depth_preset=recipe.depth_preset,
                depth=recipe.depth,
                seed=recipe.seed + 1,
                candidate_count=1,
                rytm_targets=recipe.rytm_scope.target_ids,
                rytm_locks=recipe.rytm_scope.locked_ids,
                analog_four_targets=recipe.analog_four_scope.target_ids,
                analog_four_locks=recipe.analog_four_scope.locked_ids,
                offline_only=flag,
            )
        elif action == "select":
            workspace.select_candidate(
                bank.bank_id,
                journey.entry_id,
                candidate.candidate_id,
                bank.revision,
                offline_only=flag,
            )
        else:
            workspace.mark_favorite(
                bank.bank_id,
                journey.entry_id,
                candidate.candidate_id,
                bank.revision,
                offline_only=flag,
            )
    assert workspace.bank(bank.bank_id) == bank and _disk(workspace.store.root) == before


def test_live_source_cache_eviction_preserves_each_cue_anchor_offline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(workspace_module, "MAX_VOLATILE_FRAMES", 1)
    journey = _journey(tmp_path)
    workspace = journey.workspace
    cues = []
    for index in range(2):
        bank = workspace.bank(journey.bank_id)
        captures = {
            device: replace(
                decode_kit_capture_frame(device, frame),
                captured_at=bank.updated_at + timedelta(seconds=index),
            )
            for device, frame in journey.originals.items()
        }
        cues.append(
            workspace.adopt_sources(
                bank.bank_id,
                bank.revision,
                captures=captures,
                rytm_fingerprint=captures[ANALOG_RYTM_DEVICE_ID].fingerprint,
                analog_four_fingerprint=captures[ANALOG_FOUR_DEVICE_ID].fingerprint,
                rytm_slot=20,
                analog_four_slot=21,
                entry_id=f"live-source-{index}",
            )
        )
    first = workspace.source_snapshot(journey.bank_id, cues[0].entry_id)
    assert first.snapshot_id == cues[0].rytm_source.snapshot_id
    assert first.captured_at == cues[0].rytm_source.captured_at
    restarted = ShowKitForgeWorkspace(workspace.store)
    assert restarted.source_snapshot(journey.bank_id, cues[0].entry_id) == first
    for cue in cues:
        assert restarted.original_source_frames(journey.bank_id, cue.entry_id) == journey.originals
