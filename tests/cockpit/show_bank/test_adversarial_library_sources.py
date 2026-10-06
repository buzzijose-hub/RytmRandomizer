"""Library import and migration compose with retained bank/favorite evidence."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from rytm_randomizer.cockpit.data.parameter_scope import ParameterSelection
from rytm_randomizer.cockpit.data.rehearsal_favorite import LocalRehearsalFavorite
from rytm_randomizer.cockpit.export import writer
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.observability.errors import PersistedStateVersionError

from .test_native_offline_journey import _disk, _favorite, _generate, _journey
from .test_offline_retention import library_sources

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]


@pytest.mark.parametrize("identity", ("missing", "wrong-family"))
def test_workspace_preserves_prior_favorite_when_library_source_association_is_invalid(
    tmp_path: Path, identity: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = _favorite(journey, candidate)
    library = LibraryStore(tmp_path / "library")
    records = {record.device_id: record for record in library.list_records()}
    source_id = (
        "absent-record" if identity == "missing" else records[ANALOG_FOUR_DEVICE_ID].record_id
    )
    bank_before = _disk(journey.workspace.store.root)
    library_before = _disk(library.library_dir)
    with pytest.raises(ValueError, match="missing or belongs to another family"):
        journey.workspace.adopt_retained_sources(
            journey.bank_id,
            bank.revision,
            library=library,
            rytm_record_id=source_id,
            analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
            rytm_slot=30,
            analog_four_slot=31,
            entry_id="must-not-adopt",
        )
    assert journey.workspace.bank(journey.bank_id) == bank
    assert journey.workspace.favorite_context(journey.bank_id, journey.entry_id)[1] == candidate
    assert _disk(journey.workspace.store.root) == bank_before
    assert _disk(library.library_dir) == library_before


@pytest.mark.parametrize("version", (1, 2))
def test_workspace_legacy_adoption_preserves_library_provenance_when_reconstruction_is_explicit(
    tmp_path: Path, version: int
) -> None:
    source, records, frames = library_sources(tmp_path / "source")
    legacy = LibraryStore(tmp_path / "legacy")
    legacy.library_dir.mkdir()
    for record in records.values():
        raw = record.to_dict()
        raw.pop("source_frame")
        raw.pop("source_origin")
        if version == 1:
            raw.pop("record_kind")
            raw.pop("rehearsal")
        raw["schema_version"] = version
        (legacy.library_dir / f"{record.record_id}.json").write_text(
            json.dumps(raw), encoding="utf-8"
        )
    legacy_before = _disk(legacy.library_dir)
    originals_before = _disk(source.library_dir)
    workspace = ShowKitForgeWorkspace(ShowBankStore(tmp_path / "banks"))
    bank = workspace.create_bank(name="Explicit reconstructed sources", description="", notes=())
    bank_before = _disk(workspace.store.root)
    args = {
        "library": legacy,
        "rytm_record_id": records[ANALOG_RYTM_DEVICE_ID].record_id,
        "analog_four_record_id": records[ANALOG_FOUR_DEVICE_ID].record_id,
        "rytm_slot": 20,
        "analog_four_slot": 21,
        "entry_id": "legacy-cue",
    }
    with pytest.raises(ValueError, match="explicit reconstruction"):
        workspace.adopt_retained_sources(bank.bank_id, bank.revision, **args)
    assert workspace.bank(bank.bank_id) == bank and _disk(workspace.store.root) == bank_before
    entry = workspace.adopt_retained_sources(
        bank.bank_id, bank.revision, **args, allow_legacy_reconstruction=True
    )
    assert workspace.original_source_frames(bank.bank_id, entry.entry_id) == frames
    assert entry.rytm_source.capture_id.startswith("file-")
    assert entry.analog_four_source.capture_id.startswith("file-")
    for record in records.values():
        migrated = legacy.get(record.record_id, strict_original_source=True)
        assert migrated is not None
        assert migrated.source_frame is None and migrated.source_origin is None
    assert _disk(legacy.library_dir) == legacy_before
    assert _disk(source.library_dir) == originals_before
    assert not workspace.state_dict()["banks"][0]["readiness"]["show_ready"]


def test_library_duplicate_imports_preserve_bank_and_favorite_when_newer_library_data_is_refused(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = _favorite(journey, candidate)
    captures = tmp_path / "captures"
    captures.mkdir()
    pair = journey.originals[ANALOG_RYTM_DEVICE_ID] + journey.originals[ANALOG_FOUR_DEVICE_ID]
    (captures / "paired.syx").write_bytes(pair)
    (captures / "same-pair.syx").write_bytes(pair)
    (captures / "invalid.syx").write_bytes(b"not a framed KIT")
    library = LibraryStore(tmp_path / "library", captures_dir=captures)
    for record in library.list_records():
        library.tag(record.record_id, ("immutable", "kept"))
    records = library.list_records()
    before = _disk(library.library_dir)
    bank_before = _disk(journey.workspace.store.root)
    for _ in range(2):
        outcome = library.import_captures()
        assert outcome.imported == () and outcome.skipped_existing == 4
        assert outcome.failed_files == ("invalid.syx",)
        assert library.list_records() == records
        assert _disk(library.library_dir) == before
    record_path = library.library_dir / f"{records[0].record_id}.json"
    raw = json.loads(record_path.read_bytes())
    raw["schema_version"] = 4
    record_path.write_text(json.dumps(raw), encoding="utf-8")
    newer_before = _disk(library.library_dir)
    with pytest.raises(PersistedStateVersionError):
        library.import_captures()
    with pytest.raises(PersistedStateVersionError):
        library.read_source_frame(records[0].record_id)
    assert _disk(library.library_dir) == newer_before
    restarted = ShowKitForgeWorkspace(journey.workspace.store)
    assert restarted.bank(journey.bank_id) == bank
    assert restarted.favorite_context(journey.bank_id, journey.entry_id)[1] == candidate
    assert restarted.original_source_frames(journey.bank_id, journey.entry_id) == journey.originals
    assert _disk(journey.workspace.store.root) == bank_before


@pytest.mark.parametrize("kind", ("source", "favorite"))
def test_library_overwrite_restores_all_evidence_when_tag_publish_interrupts_after_replace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = _favorite(journey, candidate)
    favorite = LocalRehearsalFavorite(
        source_snapshot=journey.workspace.source_snapshot(journey.bank_id, journey.entry_id),
        profile=journey.profile,
        candidate=candidate.rytm_candidate,
        rytm_pad_targets=frozenset(),
        locked_pad_ids=frozenset(range(1, 13)),
        a4_track_targets=frozenset((1, 2)),
        locked_a4_track_ids=frozenset((1, 2, 3, 4)),
        rytm_parameter_selection=ParameterSelection(()),
        a4_parameter_selection=ParameterSelection(()),
    )
    library = LibraryStore(tmp_path / "library")
    favorite_record = library.retain_rehearsal(favorite, "Scoped offline favorite")
    source_record = next(record for record in library.list_records() if record.rehearsal is None)
    record = source_record if kind == "source" else favorite_record
    path = library.library_dir / f"{record.record_id}.json"
    before = _disk(library.library_dir)
    bank_before = _disk(journey.workspace.store.root)
    replace_file = writer.os.replace
    observed: list[Path] = []

    def interrupt(source, destination):
        result = replace_file(source, destination)
        if Path(destination) == path and Path(source).suffix == ".stage":
            observed.append(path)
            raise KeyboardInterrupt("test tag interruption after actual replacement")
        return result

    with monkeypatch.context() as patch:
        patch.setattr(writer.os, "replace", interrupt)
        with pytest.raises(KeyboardInterrupt):
            library.tag(record.record_id, ("must-not-commit",))
    assert observed == [path] and _disk(library.library_dir) == before
    assert library.get(favorite_record.record_id).rehearsal == favorite
    for source in library.list_records():
        if source.rehearsal is None:
            assert (
                library.read_source_frame(source.record_id) == journey.originals[source.device_id]
            )
    assert journey.workspace.bank(journey.bank_id) == bank
    assert _disk(journey.workspace.store.root) == bank_before
    assert library.tag(record.record_id, ("retry",)).tags == ("retry",)
