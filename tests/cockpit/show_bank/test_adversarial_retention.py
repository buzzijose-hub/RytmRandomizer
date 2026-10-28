"""Adversarial retained-state transitions through public workspace contracts."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data.parameter_scope import ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import A4_SHOW_KIT_DEVICE_ID
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.observability.errors import DataError

from .test_native_offline_journey import _RIO, _disk, _favorite, _generate, _journey

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


def test_workspace_refuses_legacy_candidate_retention_when_selected_bytes_have_no_provenance(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    kept, selected = _generate(journey, fields=("filter2_resonance",))
    bank = _favorite(journey, kept)
    unretained = replace(
        selected,
        analog_four_candidate=replace(
            selected.analog_four_candidate,
            sysex=replace(selected.analog_four_candidate.sysex, retained=None),
        ),
    )
    legacy = replace(
        bank,
        revision=bank.revision + 1,
        entries=(
            replace(
                bank.entry(journey.entry_id),
                candidates=(kept, unretained),
                selected_candidate_id=selected.candidate_id,
            ),
        ),
    )
    journey.workspace.store.save(legacy)
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    before = _disk(restarted.store.root)
    with pytest.raises(ValueError, match="no longer in memory"):
        restarted.retain_capture(
            journey.bank_id,
            journey.entry_id,
            legacy.revision,
            capture_kind="candidate",
            device_id=A4_SHOW_KIT_DEVICE_ID,
            current_captures={},
        )
    assert restarted.bank(journey.bank_id) == legacy
    assert restarted.bank(journey.bank_id).entry(journey.entry_id).favorite_candidate == kept
    assert restarted.original_source_frames(journey.bank_id, journey.entry_id) == journey.originals
    assert _disk(restarted.store.root) == before


@pytest.mark.parametrize("origin", ("file", "input"))
@pytest.mark.parametrize("unnamed", ("rytm", "a4", "both"))
def test_workspace_adopts_exact_unnamed_originals_when_cue_name_needs_a_label(
    tmp_path: Path, origin: str, unnamed: str
) -> None:
    filenames = {
        ANALOG_RYTM_DEVICE_ID: (
            "RYTM_Test1_Init_Kit.syx"
            if unnamed in ("rytm", "both")
            else "RYTM_RIO145_AR_CORE_RETURN_Kit.syx"
        ),
        ANALOG_FOUR_DEVICE_ID: (
            "A4_Test1_Init_Kit.syx"
            if unnamed in ("a4", "both")
            else "A4_RIO145_CORE_RETURN_Kit.syx"
        ),
    }
    captures = {
        device: decode_kit_capture_frame(device, (_RIO / filename).read_bytes())
        for device, filename in filenames.items()
    }
    workspace = ShowKitForgeWorkspace(ShowBankStore(tmp_path / "banks"))
    bank = workspace.create_bank(name="Unnamed sources", description="", notes=())
    if origin == "file":
        library = LibraryStore(tmp_path / "library")
        records = {
            device: library.retain_source(capture, origin="file_import")
            for device, capture in captures.items()
        }
        entry = workspace.adopt_retained_sources(
            bank.bank_id,
            bank.revision,
            library=library,
            rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
            analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
            rytm_slot=20,
            analog_four_slot=21,
        )
    else:
        entry = workspace.adopt_sources(
            bank.bank_id,
            bank.revision,
            captures=captures,
            rytm_fingerprint=captures[ANALOG_RYTM_DEVICE_ID].fingerprint,
            analog_four_fingerprint=captures[ANALOG_FOUR_DEVICE_ID].fingerprint,
            rytm_slot=20,
            analog_four_slot=21,
        )
    assert entry.name.strip() == entry.name and entry.name != "+"
    assert entry.rytm_source.kit_name == captures[ANALOG_RYTM_DEVICE_ID].kit_name
    assert entry.analog_four_source.kit_name == captures[ANALOG_FOUR_DEVICE_ID].kit_name
    restarted = ShowKitForgeWorkspace(workspace.store)
    assert restarted.original_source_frames(bank.bank_id, entry.entry_id) == {
        device: capture.frame for device, capture in captures.items()
    }
    assert restarted.bank(bank.bank_id).entry(entry.entry_id) == entry


@pytest.mark.parametrize("action", ("select", "favorite"))
def test_workspace_refuses_candidate_transition_when_retained_parameter_scope_contradicts_bytes(
    tmp_path: Path, action: str
) -> None:
    journey = _journey(tmp_path)
    kept, other = _generate(journey, fields=("filter2_resonance",))
    original = _favorite(journey, kept)
    entry = original.entry(journey.entry_id)
    altered = replace(
        other,
        recipe=replace(
            other.recipe,
            analog_four_scope=replace(
                other.recipe.analog_four_scope, parameters=ParameterSelection(())
            ),
        ),
    )
    damaged = replace(
        original,
        revision=original.revision + 1,
        entries=(replace(entry, candidates=(kept, altered)),),
    )
    # This is valid canonical JSON with valid content-addressed files. Only
    # canonical recipe replay can discover the excluded native-field change.
    journey.workspace.store.save(damaged)
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    before = _disk(restarted.store.root)
    with pytest.raises(DataError, match="deterministic recipe replay"):
        restarted.candidate_context(journey.bank_id, journey.entry_id, altered.candidate_id)
    with pytest.raises(DataError, match="deterministic recipe replay"):
        if action == "select":
            restarted.select_candidate(
                journey.bank_id,
                journey.entry_id,
                altered.candidate_id,
                damaged.revision,
                offline_only=True,
            )
        else:
            restarted.mark_favorite(
                journey.bank_id,
                journey.entry_id,
                altered.candidate_id,
                damaged.revision,
                replace_existing=True,
                offline_only=True,
            )
    assert restarted.bank(journey.bank_id) == damaged
    assert restarted.bank(journey.bank_id).entry(journey.entry_id).favorite_candidate == kept
    assert restarted.original_source_frames(journey.bank_id, journey.entry_id) == journey.originals
    assert restarted.store.load(journey.bank_id, revision=original.revision) == original
    assert _disk(restarted.store.root) == before
    assert not restarted.state_dict()["banks"][0]["readiness"]["show_ready"]
