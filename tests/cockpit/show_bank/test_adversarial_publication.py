"""Loaded workspaces fail closed and retry without losing prior retained favorites."""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.export import writer
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.observability.errors import DataError

from .test_native_offline_journey import _RIO, _disk, _favorite, _frame, _generate, _journey

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.mark.parametrize("action", ("select", "favorite"))
@pytest.mark.parametrize("role", ("rytm_source", "a4_source", "candidate", "favorite"))
@pytest.mark.parametrize("damage", ("missing", "truncated", "swapped"))
def test_workspace_refuses_publication_when_previously_verified_retained_artifact_changes(
    tmp_path: Path, action: str, role: str, damage: str
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey, fields=("filter2_resonance",))
    bank = _favorite(journey, kept)
    favorite_frame = _frame(journey, kept)
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    # Warm every source/verification path before damaging the on-disk artifact.
    assert restarted.favorite_context(journey.bank_id, journey.entry_id)[1] == kept
    entry = bank.entry(journey.entry_id)
    artifact = {
        "rytm_source": entry.rytm_source.sysex,
        "a4_source": entry.analog_four_source.sysex,
        "candidate": other.analog_four_candidate.sysex,
        "favorite": kept.analog_four_candidate.sysex,
    }[role].retained
    assert artifact is not None
    path = restarted.store.root / artifact.artifact_name
    exact = path.read_bytes()
    if damage == "missing":
        path.unlink()
    elif damage == "truncated":
        path.write_bytes(exact[:-1])
    else:
        replacement = (
            journey.originals[ANALOG_FOUR_DEVICE_ID]
            if role == "rytm_source"
            else journey.originals[ANALOG_RYTM_DEVICE_ID]
        )
        path.write_bytes(replacement)
    before = _disk(restarted.store.root)
    state = restarted.state_dict()
    with pytest.raises(DataError):
        if action == "select":
            restarted.select_candidate(
                journey.bank_id,
                journey.entry_id,
                other.candidate_id,
                bank.revision,
                offline_only=True,
            )
        else:
            restarted.mark_favorite(
                journey.bank_id,
                journey.entry_id,
                other.candidate_id,
                bank.revision,
                replace_existing=True,
                offline_only=True,
            )
    assert restarted.bank(journey.bank_id) == bank
    assert restarted.store.load(journey.bank_id, verify_retained=False) == bank
    assert restarted.state_dict() == state
    assert _disk(restarted.store.root) == before
    scanner = ShowBankStore(restarted.store.root)
    assert scanner.list_banks() == ()
    assert scanner.scan_failures[0].bank_id == journey.bank_id
    path.write_bytes(exact)
    assert restarted.favorite_context(journey.bank_id, journey.entry_id)[2] == favorite_frame
    assert restarted.original_source_frames(journey.bank_id, journey.entry_id) == journey.originals
    restarted.select_candidate(
        journey.bank_id, journey.entry_id, other.candidate_id, bank.revision, offline_only=True
    )
    assert restarted.bank(journey.bank_id).entry(journey.entry_id).favorite_candidate == kept


@pytest.mark.parametrize(
    "action,phase",
    (
        ("generate", "staging"),
        ("generate", "sysex"),
        ("generate", "manifest"),
        ("adopt", "sysex"),
        ("adopt", "manifest"),
        ("select", "manifest"),
        ("favorite", "staging"),
        ("favorite", "manifest"),
    ),
)
def test_workspace_restores_prior_favorite_and_sources_when_publication_is_interrupted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, action: str, phase: str
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey, fields=("filter2_resonance",))
    bank = _favorite(journey, kept)
    workspace = journey.workspace
    favorite_frame = _frame(journey, kept)
    library = LibraryStore(tmp_path / "library")
    records = {
        device: library.retain_source(
            decode_kit_capture_frame(device, (_RIO / filename).read_bytes())
        )
        for device, filename in (
            (ANALOG_RYTM_DEVICE_ID, "RYTM_Test1_Init_Kit.syx"),
            (ANALOG_FOUR_DEVICE_ID, "A4_Test3_T1_OSC1_FIN_M1_Kit.syx"),
        )
    }

    def perform() -> None:
        revision = workspace.bank(journey.bank_id).revision
        if action == "generate":
            _generate(journey, fields=("filter2_resonance",), seed=703)
        elif action == "adopt":
            workspace.adopt_retained_sources(
                journey.bank_id,
                revision,
                library=library,
                rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
                analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
                rytm_slot=30,
                analog_four_slot=31,
                entry_id="retry-cue",
            )
        elif action == "select":
            workspace.select_candidate(
                journey.bank_id, journey.entry_id, other.candidate_id, revision, offline_only=True
            )
        else:
            workspace.mark_favorite(
                journey.bank_id,
                journey.entry_id,
                other.candidate_id,
                revision,
                replace_existing=True,
                offline_only=True,
            )

    before = _disk(workspace.store.root)
    library_before = _disk(library.library_dir)
    state = workspace.state_dict()
    published: list[str] = []
    publish = writer._publish_no_overwrite
    stage = writer.atomic_write

    def interrupt_publication(source, destination, *, on_published=None):
        result = publish(source, destination, on_published=on_published)
        if destination.parent == workspace.store.root:
            published.append(destination.name)
            if (phase == "sysex" and destination.suffix == ".syx") or (
                phase == "manifest" and destination.name.endswith(".show-bank.json")
            ):
                raise KeyboardInterrupt("test interruption after actual publication")
        return result

    def interrupt_staging(path, data, *, overwrite=False):
        result = stage(path, data, overwrite=overwrite)
        if path.suffix == ".stage":
            published.append("staged")
            raise KeyboardInterrupt("test interruption after actual staging")
        return result

    with monkeypatch.context() as patch:
        if phase == "staging":
            patch.setattr(writer, "atomic_write", interrupt_staging)
        else:
            patch.setattr(writer, "_publish_no_overwrite", interrupt_publication)
        with pytest.raises(KeyboardInterrupt):
            perform()
    assert published
    assert workspace.bank(journey.bank_id) == bank
    assert workspace.state_dict() == state
    assert _disk(workspace.store.root) == before
    assert _disk(library.library_dir) == library_before
    restarted = ShowKitForgeWorkspace(ShowBankStore(workspace.store.root))
    assert restarted.bank(journey.bank_id) == bank
    assert restarted.favorite_context(journey.bank_id, journey.entry_id)[2] == favorite_frame
    assert restarted.original_source_frames(journey.bank_id, journey.entry_id) == journey.originals
    perform()
    committed = workspace.bank(journey.bank_id)
    assert committed.revision > bank.revision
    assert workspace.store.load(journey.bank_id) == committed
    if action != "favorite":
        assert committed.entry(journey.entry_id).favorite_candidate == kept
    else:
        assert committed.entry(journey.entry_id).favorite_candidate == other
    assert not workspace.state_dict()["banks"][0]["readiness"]["show_ready"]
