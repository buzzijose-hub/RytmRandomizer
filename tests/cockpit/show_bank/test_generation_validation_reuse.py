"""Generation reuses one fresh proof without authorizing retained or volatile drift."""

from __future__ import annotations

import asyncio
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureResult,
)
from rytm_randomizer.cockpit.data.show_bank import RetainedSysexArtifact, ShowBank, ShowKitSysex
from rytm_randomizer.cockpit.export.writer import WriteError
from rytm_randomizer.cockpit.show_bank import store as store_module
from rytm_randomizer.cockpit.show_bank import workspace as workspace_module
from rytm_randomizer.cockpit.show_bank.export import verify_show_bank_frames
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.observability.errors import DataError

from .test_candidate_consumer_contracts import _generate_legacy
from .test_native_offline_journey import _disk, _favorite, _generate, _journey, _session
from .test_recall_validation_reuse import _session_state

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.mark.parametrize("different_selection", [False, True])
def test_generation_proves_bank_once_and_reads_originals_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, different_selection: bool
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey)
    bank = _favorite(journey, kept)
    workspace = journey.workspace
    if different_selection:
        workspace.select_candidate(
            journey.bank_id,
            journey.entry_id,
            other.candidate_id,
            bank.revision,
            offline_only=True,
        )
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    source_names = {
        entry.rytm_source.sysex.retained.artifact_name,
        entry.analog_four_source.sysex.retained.artifact_name,
    }
    reads: list[str] = []
    proofs: list[int] = []
    read = workspace.store.read_retained

    def read_count(artifact: RetainedSysexArtifact) -> bytes:
        reads.append(artifact.artifact_name)
        return read(artifact)

    def proof_count(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        proofs.append(bank.revision)

    monkeypatch.setattr(workspace.store, "read_retained", read_count)
    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", proof_count)
    created = _generate(journey, seed=700, count=1)
    assert len(created) == 1 and proofs == [bank.revision]
    assert all(reads.count(name) == 1 for name in source_names)
    assert workspace.bank(journey.bank_id).entry(journey.entry_id).favorite_candidate == kept


def test_candidate_frame_proof_enumeration_is_constant_and_reads_retained_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    candidates = _generate(journey, count=8)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    artifacts = bank.sysex_artifacts()
    enumeration = ShowBank.sysex_artifacts
    counts: list[str] = []
    reads: list[str] = []
    lookups: list[str] = []
    proofs: list[tuple[str, ...]] = []
    read = workspace.store.read_retained
    lookup = ShowBank.sysex_artifact

    def counted_enumeration(self: ShowBank) -> tuple[ShowKitSysex, ...]:
        counts.append(self.bank_id)
        return enumeration(self)

    def counted_read(artifact: RetainedSysexArtifact) -> bytes:
        reads.append(artifact.artifact_name)
        return read(artifact)

    def counted_lookup(self: ShowBank, artifact_id: str) -> ShowKitSysex:
        lookups.append(artifact_id)
        return lookup(self, artifact_id)

    def counted_proof(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        proofs.append(
            tuple(
                candidate.candidate_id for entry in bank.entries for candidate in entry.candidates
            )
        )

    monkeypatch.setattr(ShowBank, "sysex_artifacts", counted_enumeration)
    monkeypatch.setattr(workspace.store, "read_retained", counted_read)
    monkeypatch.setattr(ShowBank, "sysex_artifact", counted_lookup)
    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", counted_proof)
    source, candidate, frame = workspace.candidate_context(
        journey.bank_id, journey.entry_id, candidates[-1].candidate_id
    )
    assert (
        candidate == candidates[-1]
        and source.snapshot_id == candidate.rytm_candidate.source_snapshot_id
    )
    assert frame and len(counts) <= 2 and all(value == bank.bank_id for value in counts)
    assert len(lookups) <= 1
    assert proofs == [tuple(item.candidate_id for item in candidates)]
    assert len(reads) == len(artifacts)


@pytest.mark.parametrize("role", ["source", "unrelated-candidate", "favorite"])
@pytest.mark.parametrize("damage", ["missing", "changed", "unsafe"])
def test_generation_fresh_proof_refuses_damaged_artifact_without_publication(
    tmp_path: Path, role: str, damage: str
) -> None:
    journey = _journey(tmp_path)
    kept, selected, unrelated = _generate(journey, count=3)
    bank = _favorite(journey, kept)
    workspace = journey.workspace
    workspace.select_candidate(
        journey.bank_id, journey.entry_id, selected.candidate_id, bank.revision, offline_only=True
    )
    _generate(journey, seed=700, count=1)
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    artifact = {
        "source": entry.analog_four_source.sysex,
        "unrelated-candidate": unrelated.analog_four_candidate.sysex,
        "favorite": kept.analog_four_candidate.sysex,
    }[role].retained
    assert artifact is not None
    path = workspace.store.root / artifact.artifact_name
    if damage == "missing":
        path.unlink()
    elif damage == "changed":
        frame = path.read_bytes()
        path.write_bytes(frame[:-1] + bytes((frame[-1] ^ 1,)))
    else:
        path.unlink()
        path.mkdir()
    before = _disk(workspace.store.root)
    state = workspace.state_dict()
    with pytest.raises(DataError):
        _generate(journey, seed=710, count=1)
    assert workspace.bank(journey.bank_id) == bank
    assert workspace.state_dict() == state
    assert _disk(workspace.store.root) == before


@pytest.mark.parametrize("command_type", ["show_bank_select_candidate", "show_bank_mark_favorite"])
@pytest.mark.parametrize("fault", [None, "bad-cache", "missing-source", "publication"])
def test_cache_only_legacy_recall_keeps_canonical_proof_and_publication_guards(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, command_type: str, fault: str | None
) -> None:
    journey = _journey(tmp_path)
    candidate = _generate_legacy(journey)
    retained = candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    frame = journey.workspace.store.read_retained(retained)
    bank = journey.workspace.bank(journey.bank_id)
    cached_candidate = replace(
        candidate,
        analog_four_candidate=replace(
            candidate.analog_four_candidate,
            sysex=replace(candidate.analog_four_candidate.sysex, retained=None),
        ),
    )
    cached_bank = replace(
        bank,
        revision=bank.revision + 1,
        entries=(replace(bank.entry(journey.entry_id), candidates=(cached_candidate,)),),
    )
    journey.workspace.store.save(cached_bank)
    workspace = ShowKitForgeWorkspace(journey.workspace.store)
    assert retained.sha256 != cached_bank.entries[0].analog_four_source.sysex.frame_sha256
    (workspace.store.root / retained.artifact_name).unlink()
    workspace._cache_frame(
        candidate.analog_four_candidate.sysex.artifact_id,
        frame[:-1] if fault == "bad-cache" else frame,
    )
    session = _session(workspace, journey.bank_id, journey.entry_id, tmp_path)
    if fault == "missing-source":
        source = cached_bank.entries[0].analog_four_source.sysex.retained
        assert source is not None
        (workspace.store.root / source.artifact_name).unlink()
    elif fault == "publication":

        def refuse_publication(*_args: object, **_kwargs: object) -> None:
            raise WriteError("injected cache-only publication failure")

        monkeypatch.setattr(workspace.store, "retain_sysex_set", refuse_publication)
    before = _session_state(session)
    disk = _disk(workspace.store.root)
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "cached-legacy-proof",
                "command": {
                    "type": command_type,
                    "bank_id": journey.bank_id,
                    "entry_id": journey.entry_id,
                    "candidate_id": candidate.candidate_id,
                    "expected_revision": cached_bank.revision,
                },
            },
            session,
        )
    )
    if fault is None:
        assert ack["ok"], ack
        published = workspace.bank(journey.bank_id).entry(journey.entry_id)
        result = published.selected_candidate.analog_four_candidate.sysex.retained
        assert result is not None and workspace.store.read_retained(result) == frame
        assert session.current_candidate == candidate.rytm_candidate
        assert (
            session.armed_apply is None
            and not session.device.is_armed
            and not session.hardware_intent
        )
    else:
        assert not ack["ok"], ack
        assert workspace.bank(journey.bank_id) == cached_bank
        assert _session_state(session) == before
        assert _disk(workspace.store.root) == disk


@pytest.mark.parametrize("device_id", [ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID])
def test_generation_refuses_source_decoder_drift_after_whole_proof(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, device_id: str
) -> None:
    journey = _journey(tmp_path)
    _generate(journey)
    bank = journey.workspace.bank(journey.bank_id)
    disk = _disk(journey.workspace.store.root)
    decode = store_module.decode_kit_capture_frame

    def proof_then_drift(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)

        def contradictory(family: str, frame: bytes) -> KitCaptureResult:
            result = decode(family, frame)
            if family == device_id and frame == journey.originals[device_id]:
                return replace(result, fingerprint="changed-source")
            return result

        monkeypatch.setattr(store_module, "decode_kit_capture_frame", contradictory)

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", proof_then_drift)
    with pytest.raises(DataError):
        _generate(journey, seed=700, count=1)
    assert journey.workspace.bank(journey.bank_id) == bank
    assert _disk(journey.workspace.store.root) == disk


@pytest.mark.parametrize("device_id", [ANALOG_RYTM_DEVICE_ID, ANALOG_FOUR_DEVICE_ID])
def test_generation_refuses_unretained_source_without_cache_authority(
    tmp_path: Path, device_id: str
) -> None:
    journey = _journey(tmp_path)
    _generate(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    entry = bank.entry(journey.entry_id)
    source = entry.rytm_source if device_id == ANALOG_RYTM_DEVICE_ID else entry.analog_four_source
    unretained = replace(source, sysex=replace(source.sysex, retained=None))
    changed_entry = replace(
        entry,
        **(
            {"rytm_source": unretained}
            if device_id == ANALOG_RYTM_DEVICE_ID
            else {"analog_four_source": unretained}
        ),
    )
    unretained_bank = replace(
        bank, bank_id="unretained-generation-source", revision=0, entries=(changed_entry,)
    )
    workspace.store.save(unretained_bank)
    workspace.register_imported(unretained_bank)
    workspace._cache_frame(source.sysex.artifact_id, journey.originals[device_id])
    before = _disk(workspace.store.root)
    with pytest.raises(DataError):
        _generate(replace(journey, bank_id=unretained_bank.bank_id), seed=700, count=1)
    assert workspace.bank(unretained_bank.bank_id) == unretained_bank
    assert _disk(workspace.store.root) == before


def test_generation_cancelled_proof_does_not_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    _generate(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    before = _disk(workspace.store.root)

    def cancel(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        raise asyncio.CancelledError

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", cancel)
    with pytest.raises(asyncio.CancelledError):
        _generate(journey, seed=700, count=1)
    assert workspace.bank(journey.bank_id) == bank
    assert _disk(workspace.store.root) == before


def test_generation_refuses_bank_identity_change_after_proof_before_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    journey = _journey(tmp_path)
    _generate(journey)
    workspace = journey.workspace
    bank = workspace.bank(journey.bank_id)
    before = _disk(workspace.store.root)
    replacement = replace(bank)

    def replace_after_proof(bank: ShowBank, frames: Mapping[str, bytes]) -> None:
        verify_show_bank_frames(bank, frames)
        monkeypatch.setitem(workspace._banks, bank.bank_id, replacement)

    monkeypatch.setattr(workspace_module, "verify_show_bank_frames", replace_after_proof)
    with pytest.raises(ValueError, match="show bank changed"):
        _generate(journey, seed=700, count=1)
    assert workspace.bank(journey.bank_id) is replacement
    assert _disk(workspace.store.root) == before
