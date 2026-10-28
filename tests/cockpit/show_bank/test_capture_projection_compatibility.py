"""Old committed-source favorites retain exact replay under an expanded capture domain."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from cockpit.conftest import MutableClock

from conftest import analog_four_saved_kit_frame, elektron_syx_message, rytm_real_layout_kit_payload
from rytm_randomizer.cockpit.capture import (
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.capture.projection import project_rytm_capture_snapshot
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import ShowBank
from rytm_randomizer.cockpit.show_bank.export import ShowPackService, verify_show_bank_frames
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.data.analog_rytm_kit_layout import analog_rytm_track_sound_offset
from rytm_randomizer.data.analog_rytm_midi import (
    RYTM_CAPTURE_PROJECTION_V1,
    RYTM_CAPTURE_PROJECTION_V2,
)
from rytm_randomizer.devices import (
    AnalogFourFilter1FrequencyCandidateMutation,
    get_analog_four_filter1_frequency_candidate_capability,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from rytm_randomizer.observability.errors import DataError

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
ROOT = Path(__file__).resolve().parents[3]


def _legacy(name: str, root: Path) -> tuple[ShowKitForgeWorkspace, ShowBank, dict[str, bytes]]:
    payload = json.loads(
        (ROOT / "tests/fixtures/legacy_rytm_projection" / name).read_text(encoding="utf-8")
    )
    bank = ShowBank.from_dict(payload)
    assert bank.to_dict() == payload
    entry = bank.entries[0]
    favorite = entry.favorite_candidate
    assert favorite is not None
    a4_source = analog_four_saved_kit_frame(name=b"BOUNDARY A4")
    rendered = (
        get_analog_four_filter1_frequency_candidate_capability().render_filter1_frequency_candidate(
            a4_source,
            tuple(
                AnalogFourFilter1FrequencyCandidateMutation(value.track_id, value.screen_value)
                for value in favorite.analog_four_candidate.values
            ),
        )
    )
    frames = {
        entry.rytm_source.sysex.artifact_id: elektron_syx_message(
            rytm_real_layout_kit_payload(b"BOUNDARY RYTM")
        ),
        entry.analog_four_source.sysex.artifact_id: a4_source,
        favorite.analog_four_candidate.sysex.artifact_id: rendered.framed_sysex,
    }
    verify_show_bank_frames(bank, frames)
    store = ShowBankStore(root)
    store.import_verified(bank, frames)
    return ShowKitForgeWorkspace(store), bank, frames


@pytest.mark.parametrize("name", ("a4_only_v1.json", "scoped_rytm_v1.json"))
def test_previous_source_favorites_replay_recall_and_reexport_without_new_parameters(
    tmp_path: Path, name: str
) -> None:
    workspace, bank, frames = _legacy(name, tmp_path / "banks")
    entry = bank.entries[0]
    original = (ROOT / "tests/fixtures/legacy_rytm_projection" / name).read_bytes()
    source, favorite, frame = workspace.favorite_context(bank.bank_id, entry.entry_id)
    assert favorite.recipe.rytm_projection == RYTM_CAPTURE_PROJECTION_V1
    assert all("sample_bit" not in pad.params for pad in source.pads)
    assert frame == frames[favorite.analog_four_candidate.sysex.artifact_id]
    recalled = workspace.recall_candidate(
        bank.bank_id, entry.entry_id, favorite.candidate_id, bank.revision, offline_only=True
    )
    assert recalled.source == source
    _, audition_source, selected = workspace.audition_context(bank.bank_id, entry.entry_id)
    assert audition_source == source and selected == favorite
    service = ShowPackService(tmp_path / "packs", store=workspace.store)
    exported = service.export(workspace.bank(bank.bank_id))
    destination = ShowBankStore(tmp_path / "clean")
    copied = ShowPackService(tmp_path / "packs", store=destination).import_into_store(
        exported.package_id, destination_bank_id="legacy-copy"
    )
    restarted = ShowKitForgeWorkspace(destination)
    copy_source, copy_favorite, copy_frame = restarted.favorite_context(
        copied.bank.bank_id, entry.entry_id
    )
    assert copy_source == source and copy_favorite == favorite and copy_frame == frame
    assert (ROOT / "tests/fixtures/legacy_rytm_projection" / name).read_bytes() == original
    assert (
        workspace.original_source_frames(bank.bank_id, entry.entry_id)["analog_rytm_mk2"]
        == frames[entry.rytm_source.sysex.artifact_id]
    )


def test_new_generation_after_old_favorite_uses_current_domain_without_rewriting_old_candidate(
    tmp_path: Path,
) -> None:
    workspace, bank, frames = _legacy("scoped_rytm_v1.json", tmp_path / "banks")
    entry = bank.entries[0]
    old = entry.favorite_candidate
    assert old is not None and old.recipe.profile is not None
    first_recall = workspace.recall_candidate(
        bank.bank_id, entry.entry_id, old.candidate_id, bank.revision, offline_only=True
    )
    assert all("sample_bit" not in pad.params for pad in first_recall.source.pads)
    bank = workspace.bank(bank.bank_id)
    (new,) = workspace.generate_candidates(
        bank.bank_id,
        entry.entry_id,
        bank.revision,
        profile=old.recipe.profile,
        depth_preset="small",
        depth=0.25,
        seed=8,
        candidate_count=1,
        rytm_targets=(2,),
        rytm_locks=(),
        analog_four_targets=(1,),
        analog_four_locks=(),
        rytm_parameters=ParameterSelection((ParameterCell(2, "sample_bit"),)),
        offline_only=True,
    )
    assert new.recipe.rytm_projection == RYTM_CAPTURE_PROJECTION_V2
    assert "sample_bit" in new.rytm_candidate.pad_deltas[0].proposed_params
    assert workspace.bank(bank.bank_id).entry(entry.entry_id).favorite_candidate == old
    source, recalled, _ = workspace.favorite_context(bank.bank_id, entry.entry_id)
    assert recalled == old and all("sample_bit" not in pad.params for pad in source.pads)
    second_recall = workspace.recall_candidate(
        bank.bank_id,
        entry.entry_id,
        old.candidate_id,
        workspace.bank(bank.bank_id).revision,
        offline_only=True,
    )
    assert second_recall.candidate == old and second_recall.source == source
    all_frames = dict(frames)
    artifact = new.analog_four_candidate.sysex
    assert artifact.retained is not None
    all_frames[artifact.artifact_id] = workspace.store.read_retained(artifact.retained)
    verify_show_bank_frames(workspace.bank(bank.bank_id), all_frames)


def test_old_candidate_cannot_be_promoted_to_new_projection_by_changing_metadata(
    tmp_path: Path,
) -> None:
    _, bank, frames = _legacy("scoped_rytm_v1.json", tmp_path / "banks")
    entry = bank.entries[0]
    old = entry.favorite_candidate
    assert old is not None
    claimed = replace(old, recipe=replace(old.recipe, rytm_projection=RYTM_CAPTURE_PROJECTION_V2))
    forged = replace(bank, entries=(replace(entry, candidates=(claimed,)),))
    with pytest.raises(DataError, match="deterministic recipe replay"):
        verify_show_bank_frames(forged, frames)


@pytest.mark.parametrize("version", (RYTM_CAPTURE_PROJECTION_V1, RYTM_CAPTURE_PROJECTION_V2))
def test_recorded_projection_survives_recapture_restart_and_package_verification(
    tmp_path: Path, version: str
) -> None:
    prior, bank, frames = _legacy("a4_only_v1.json", tmp_path / "banks")
    clock = MutableClock(datetime(2026, 10, 15, 12, tzinfo=timezone.utc))
    workspace = ShowKitForgeWorkspace(prior.store, clock=clock)
    entry = bank.entries[0]
    favorite = entry.favorite_candidate
    assert favorite is not None and favorite.recipe.profile is not None
    if version == RYTM_CAPTURE_PROJECTION_V2:
        (new,) = workspace.generate_candidates(
            bank.bank_id,
            entry.entry_id,
            bank.revision,
            profile=favorite.recipe.profile,
            depth_preset="small",
            depth=0.25,
            seed=8,
            candidate_count=1,
            rytm_targets=(),
            rytm_locks=tuple(range(1, 13)),
            analog_four_targets=(1,),
            analog_four_locks=(),
            offline_only=True,
        )
        workspace.mark_favorite(
            bank.bank_id,
            entry.entry_id,
            new.candidate_id,
            workspace.bank(bank.bank_id).revision,
            replace_existing=True,
            offline_only=True,
        )
        favorite = new
    assert favorite.recipe.rytm_projection == version
    assert favorite.rytm_candidate.pad_deltas == ()
    for device, slot in (("analog_rytm_mk2", 40), ("analog_four_mk2", 41)):
        workspace.attest_saved(
            bank.bank_id,
            entry.entry_id,
            workspace.bank(bank.bank_id).revision,
            device_id=device,
            hardware_slot=slot,
        )
        clock.current += timedelta(seconds=1)
    rytm_frame = frames[entry.rytm_source.sysex.artifact_id]
    if version == RYTM_CAPTURE_PROJECTION_V2:
        decoded = decode_analog_rytm_saved_kit_frame(rytm_frame)
        payload = bytearray(decoded.unpacked)
        payload[analog_rytm_track_sound_offset(2, 0x32)] = 1
        rytm_frame = encode_analog_rytm_saved_kit_frame(decoded.header, bytes(payload))
    artifact = favorite.analog_four_candidate.sysex
    assert artifact.retained is not None
    captures = {
        "analog_rytm_mk2": replace(
            decode_kit_capture_frame("analog_rytm_mk2", rytm_frame), captured_at=clock.current
        ),
        "analog_four_mk2": replace(
            decode_kit_capture_frame(
                "analog_four_mk2", workspace.store.read_retained(artifact.retained)
            ),
            captured_at=clock.current,
        ),
    }
    clock.current += timedelta(seconds=1)
    observed = workspace.verify_recaptures(
        bank.bank_id, entry.entry_id, workspace.bank(bank.bank_id).revision, captures=captures
    )
    assert observed.rytm_recapture is not None
    assert (
        observed.analog_four_recapture is not None
        and observed.analog_four_recapture.matches_candidate
    )
    assert observed.rytm_recapture.matches_candidate is (version == RYTM_CAPTURE_PROJECTION_V1)
    restarted = ShowKitForgeWorkspace(workspace.store, clock=clock)
    service = ShowPackService(tmp_path / "packages", store=restarted.store)
    exported = service.export(restarted.bank(bank.bank_id))
    service.verify(exported.package_id)
    copied_store = ShowBankStore(tmp_path / "copied")
    copied = ShowPackService(tmp_path / "packages", store=copied_store).import_into_store(
        exported.package_id, destination_bank_id="copy"
    )
    _, copied_favorite, _ = ShowKitForgeWorkspace(copied_store).favorite_context(
        copied.bank.bank_id, entry.entry_id
    )
    assert copied_favorite.recipe.rytm_projection == version


def test_projection_views_preserve_current_source_and_all_unrelated_values() -> None:
    current = cockpit_snapshot_from_rytm_capture(
        decode_kit_capture_frame(
            "analog_rytm_mk2", elektron_syx_message(rytm_real_layout_kit_payload())
        )
    )
    assert project_rytm_capture_snapshot(current, RYTM_CAPTURE_PROJECTION_V2) is current
    old = project_rytm_capture_snapshot(current, RYTM_CAPTURE_PROJECTION_V1)
    assert old.snapshot_id == current.snapshot_id and old.captured_at == current.captured_at
    for before, after in zip(current.pads, old.pads, strict=True):
        assert "sample_bit" in before.params and "sample_bit" not in after.params
        assert after.params == {
            key: value for key, value in before.params.items() if key != "sample_bit"
        }


@pytest.mark.parametrize("version", (True, None, 1, "unknown", []))
def test_projection_view_refuses_unknown_versions_before_replay(version: object) -> None:
    current = cockpit_snapshot_from_rytm_capture(
        decode_kit_capture_frame(
            "analog_rytm_mk2", elektron_syx_message(rytm_real_layout_kit_payload())
        )
    )
    with pytest.raises(ValueError, match="unsupported Rytm capture projection"):
        project_rytm_capture_snapshot(current, version)


def test_frontend_recipe_wire_names_preserve_both_recorded_projection_versions() -> None:
    protocol = (ROOT / "desktop/web/src/ws/protocol.ts").read_text(encoding="utf-8")
    recipe = protocol.split("export interface ShowKitRecipe {", 1)[1].split("\n}", 1)[0]
    assert "rytm_projection?:" in recipe
    assert f"'{RYTM_CAPTURE_PROJECTION_V1}'" in recipe
    assert f"'{RYTM_CAPTURE_PROJECTION_V2}'" in recipe
