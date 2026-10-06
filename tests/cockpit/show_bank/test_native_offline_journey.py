"""Retained native-field journeys prove local bytes, never hardware evidence."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureDeviceId,
    decode_kit_capture_frame,
)
from rytm_randomizer.cockpit.data import ProfileModel
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import (
    A4_NATIVE_MUTATION_ALGORITHM,
    AnalogFourNativeCandidateValue,
    ShowBank,
    ShowKitCandidate,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.library import LibraryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.show_bank.a4_preparation import (
    A4PreparationContext,
    prepare_a4_audition,
)
from rytm_randomizer.cockpit.show_bank.export import ShowPackService
from rytm_randomizer.cockpit.show_bank.readiness import is_catalog_only_show_bank
from rytm_randomizer.cockpit.show_bank.store import ShowBankStore
from rytm_randomizer.cockpit.show_bank.workspace import ShowKitForgeWorkspace
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.data.analog_four_sysex_calibration import A4_FILTER1_FREQUENCY_PARAMETER
from rytm_randomizer.devices import get_analog_four_native_field_capability
from rytm_randomizer.devices.strategies.analog_four_kit_fields import decode_a4_pitch_components
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
)
from rytm_randomizer.observability.errors import DataError
from rytm_randomizer.snapshot.mutation_scope import MutationScope

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_RIO: Final[Path] = Path(__file__).resolve().parents[2] / "fixtures" / "rio145"
_CORE: Final[str] = "A4_RIO145_CORE_RETURN_Kit.syx"
_FIELDS: Final[tuple[str, ...]] = (
    "filter2_resonance",
    "osc1_pwm_speed",
    "osc1_pwm_depth",
    "filter2_frequency",
    "env2_depth_a",
)


@dataclass(frozen=True)
class _Journey:
    workspace: ShowKitForgeWorkspace
    profile: ProfileModel
    originals: dict[KitCaptureDeviceId, bytes]
    bank_id: str
    entry_id: str


def _journey(root: Path, a4_name: str = _CORE) -> _Journey:
    originals = {
        ANALOG_RYTM_DEVICE_ID: (_RIO / "RYTM_RIO145_AR_CORE_RETURN_Kit.syx").read_bytes(),
        ANALOG_FOUR_DEVICE_ID: (_RIO / a4_name).read_bytes(),
    }
    library = LibraryStore(root / "library")
    records = {
        device: library.retain_source(decode_kit_capture_frame(device, frame), origin="file_import")
        for device, frame in originals.items()
    }
    workspace = ShowKitForgeWorkspace(ShowBankStore(root / "banks"))
    bank = workspace.create_bank(name="Native offline set", description="", notes=())
    entry = workspace.adopt_retained_sources(
        bank.bank_id,
        bank.revision,
        library=LibraryStore(root / "library"),
        rytm_record_id=records[ANALOG_RYTM_DEVICE_ID].record_id,
        analog_four_record_id=records[ANALOG_FOUR_DEVICE_ID].record_id,
        rytm_slot=20,
        analog_four_slot=21,
    )
    profile = replace(
        ProfileRegistry(root / "profiles").list_profiles()[0],
        profile_id="retained-native-author",
        kind="user",
    )
    return _Journey(workspace, profile, originals, bank.bank_id, entry.entry_id)


def _cells(fields: tuple[str, ...]) -> ParameterSelection:
    return ParameterSelection(
        tuple(ParameterCell(track, key) for track in (1, 2, 4) for key in fields)
    )


def _generate(
    journey: _Journey,
    *,
    fields: tuple[str, ...] = _FIELDS,
    depth: float = 0.25,
    locks: tuple[int, ...] = (2,),
    seed: int = 99,
    count: int = 2,
) -> tuple[ShowKitCandidate, ...]:
    workspace = journey.workspace
    return workspace.generate_candidates(
        journey.bank_id,
        journey.entry_id,
        workspace.bank(journey.bank_id).revision,
        profile=journey.profile,
        depth_preset="small",
        depth=depth,
        seed=seed,
        candidate_count=count,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1, 2),
        analog_four_locks=locks,
        rytm_parameters=ParameterSelection(()),
        analog_four_parameters=_cells(fields),
        offline_only=True,
        a4_algorithm=A4_NATIVE_MUTATION_ALGORITHM,
    )


def _frame(journey: _Journey, candidate: ShowKitCandidate) -> bytes:
    retained = candidate.analog_four_candidate.sysex.retained
    assert retained is not None
    return journey.workspace.store.read_retained(retained)


def _favorite(journey: _Journey, candidate: ShowKitCandidate) -> ShowBank:
    workspace = journey.workspace
    workspace.select_candidate(
        journey.bank_id,
        journey.entry_id,
        candidate.candidate_id,
        workspace.bank(journey.bank_id).revision,
        offline_only=True,
    )
    workspace.mark_favorite(
        journey.bank_id,
        journey.entry_id,
        candidate.candidate_id,
        workspace.bank(journey.bank_id).revision,
        offline_only=True,
    )
    return workspace.bank(journey.bank_id)


def _disk(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def _session(
    workspace: ShowKitForgeWorkspace, bank_id: str, entry_id: str, root: Path
) -> CockpitSession:
    source = workspace.source_snapshot(bank_id, entry_id)
    history = HistoryStore()
    history.initial(source)
    return CockpitSession(
        profile_registry=ProfileRegistry(root / "missing-profiles"),
        history_store=history,
        device=MockDeviceAdapter(source),
        show_kit_forge=workspace,
    )


@pytest.mark.parametrize(
    "source_name,fields,source_pitch",
    [
        (_CORE, _FIELDS, None),
        ("A4_Test2_T1_OSC1_FIN_P1_Kit.syx", ("osc1_tune",), 0x4003),
        ("A4_Test3_T1_OSC1_FIN_M1_Kit.syx", ("osc1_tune",), 0x3FFE),
    ],
)
def test_native_retained_journey_exports_imports_restarts_and_recalls_exactly_disarmed(
    tmp_path: Path, source_name: str, fields: tuple[str, ...], source_pitch: int | None
) -> None:
    journey = _journey(tmp_path / "source", source_name)
    capability = get_analog_four_native_field_capability()
    original = journey.originals[ANALOG_FOUR_DEVICE_ID]
    before = capability.read_native_fields(original)
    source_bytes = decode_analog_four_saved_kit_payload(
        original[1:-1], require_trailer=True
    ).unpacked
    candidates = _generate(journey, fields=fields)
    assert {
        value.parameter for item in candidates for value in item.analog_four_candidate.values
    } == set(fields)
    for candidate in candidates:
        frame = _frame(journey, candidate)
        after = capability.read_native_fields(frame)
        rendered = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True).unpacked
        approved = set()
        for value in candidate.analog_four_candidate.values:
            assert isinstance(value, AnalogFourNativeCandidateValue)
            cell = after.value(value.parameter, value.track_id)
            assert value.track_id == 1 and value.parameter in fields
            assert (
                value.encoded_native,
                value.screen_value,
                value.native_encoding,
                value.unpacked_offsets,
            ) == (
                cell.encoded_native,
                cell.screen_value,
                cell.metadata.native_encoding.value,
                cell.unpacked_offsets,
            )
            approved.update(
                cell.unpacked_offsets[:1]
                if value.parameter.endswith("tune")
                else cell.unpacked_offsets
            )
        changed = {
            offset
            for offset, pair in enumerate(zip(source_bytes, rendered, strict=True))
            if pair[0] != pair[1]
        }
        assert changed and changed <= approved
        assert candidate.rytm_candidate.estimated_midi_msgs == 0
        assert not any(delta.changed_keys for delta in candidate.rytm_candidate.pad_deltas)
        assert after.output_authority == "local-file-only" and not after.hardware_send_validated
        for source_cell in before.values:
            if not set(source_cell.unpacked_offsets).intersection(approved):
                assert (
                    after.value(source_cell.parameter, source_cell.track).native_bytes
                    == source_cell.native_bytes
                )
        if source_pitch is not None:
            assert before.value("osc1_tune", 1).encoded_native == source_pitch
            assert (
                decode_a4_pitch_components(after.value("osc1_tune", 1).encoded_native)[1:]
                == decode_a4_pitch_components(source_pitch)[1:]
            )
    favorite = candidates[1]
    favorite_frame = _frame(journey, favorite)
    bank = _favorite(journey, favorite)
    exported = ShowPackService(tmp_path / "packs", store=journey.workspace.store).export(bank)
    target_root = tmp_path / "clean-banks"
    imported = ShowPackService(
        tmp_path / "packs", store=ShowBankStore(target_root)
    ).import_into_store(exported.package_id, destination_bank_id="native-copy")
    restarted = ShowKitForgeWorkspace(ShowBankStore(target_root))
    assert is_catalog_only_show_bank(imported.bank)
    assert restarted.original_source_frames("native-copy", journey.entry_id) == journey.originals
    source, recalled, recalled_frame = restarted.favorite_context("native-copy", journey.entry_id)
    assert recalled == favorite and recalled_frame == favorite_frame
    assert recalled.recipe.profile == journey.profile
    assert recalled.recipe.a4_algorithm == A4_NATIVE_MUTATION_ALGORITHM
    session = _session(restarted, "native-copy", journey.entry_id, tmp_path)
    assert session.profile_registry.get(journey.profile.profile_id) is None
    session.hardware_intent = True
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "native-recall",
                "command": {
                    "type": "show_bank_select_candidate",
                    "bank_id": "native-copy",
                    "entry_id": journey.entry_id,
                    "candidate_id": favorite.candidate_id,
                    "expected_revision": imported.bank.revision,
                },
            },
            session,
        )
    )
    assert ack["ok"], ack
    assert session.device.capture_snapshot() == source
    assert (
        session.active_profile == journey.profile
        and session.current_candidate == favorite.rytm_candidate
    )
    assert (session.depth, session.seed) == (favorite.recipe.depth, favorite.recipe.seed)
    assert session.a4_track_targets == {1, 2} and session.a4_track_locks == {2}
    assert session.pad_locks == set(range(1, 13)) and not session.rytm_pad_targets
    assert session.a4_parameters == favorite.recipe.analog_four_scope.parameters
    assert session.rytm_parameters == favorite.recipe.rytm_scope.parameters
    assert session.offline_a4_capture.frame == original and not session.kit_captures
    assert session.recalled_offline_favorite and session.current_send_plan is None
    assert (
        session.armed_apply is None and not session.hardware_intent and not session.device.is_armed
    )
    assert not restarted.state_dict()["banks"][0]["readiness"]["show_ready"]
    with pytest.raises(ValueError, match="catalog-only"):
        restarted.audition_context("native-copy", journey.entry_id)


@pytest.mark.parametrize("no_op", ["zero-depth", "fully-locked", "no-fields"])
def test_native_no_op_is_exact_source_and_reuses_one_retained_artifact(
    tmp_path: Path, no_op: str
) -> None:
    journey = _journey(tmp_path, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    candidates = _generate(
        journey,
        fields=() if no_op == "no-fields" else ("osc1_tune",),
        depth=0.0 if no_op == "zero-depth" else 0.25,
        locks=(1, 2, 3, 4) if no_op == "fully-locked" else (2,),
    )
    source = journey.originals[ANALOG_FOUR_DEVICE_ID]
    assert candidates[0].candidate_id != candidates[1].candidate_id
    assert candidates[0].analog_four_candidate.sysex == candidates[1].analog_four_candidate.sysex
    for candidate in candidates:
        assert _frame(journey, candidate) == source
        assert candidate.analog_four_candidate.values == ()
        assert (
            candidate.analog_four_candidate.semantic_fingerprint == candidate.source_a4_fingerprint
        )
    artifact = candidates[0].analog_four_candidate.sysex.retained
    assert artifact.sha256 == hashlib.sha256(source).hexdigest()
    bank = _favorite(journey, candidates[1])
    exported = ShowPackService(tmp_path / "packs", store=journey.workspace.store).export(bank)
    target = ShowBankStore(tmp_path / "clean")
    ShowPackService(tmp_path / "packs", store=target).import_into_store(exported.package_id)
    assert (
        ShowKitForgeWorkspace(ShowBankStore(target.root)).favorite_context(
            journey.bank_id, journey.entry_id
        )[2]
        == source
    )


def test_repeating_native_recipe_after_restart_refuses_without_new_revisions_or_artifacts(
    tmp_path: Path,
) -> None:
    journey = _journey(tmp_path)
    candidates = _generate(journey)
    before = _disk(journey.workspace.store.root)
    restarted = replace(
        journey, workspace=ShowKitForgeWorkspace(ShowBankStore(journey.workspace.store.root))
    )
    with pytest.raises(ValueError, match="already exists"):
        _generate(restarted)
    assert (
        restarted.workspace.bank(journey.bank_id).entry(journey.entry_id).candidates == candidates
    )
    assert _disk(journey.workspace.store.root) == before


@pytest.mark.parametrize(
    "corruption",
    [
        "native-value",
        "native-encoding",
        "native-offset",
        "native-screen",
        "excluded-cell",
        "locked-track",
        "legacy-without-profile",
        "native-without-profile",
        "empty-values-wrong-fingerprint",
        "empty-values-source-fingerprint",
        "recipe-seed",
    ],
)
def test_corrupt_native_package_claims_and_scopes_are_refused_before_clean_store_publication(
    tmp_path: Path, corruption: str
) -> None:
    journey = _journey(tmp_path / "source")
    (candidate,) = _generate(journey, fields=("filter2_resonance",), count=1)
    bank = _favorite(journey, candidate)
    exported = ShowPackService(tmp_path / "packs", store=journey.workspace.store).export(bank)
    path = exported.package_dir / "manifest.json"
    raw = json.loads(path.read_bytes())
    claim = raw["bank"]["entries"][0]["candidates"][0]
    value = claim["analog_four_candidate"]["values"][0]
    if corruption == "native-value":
        value["encoded_native"] = (value["encoded_native"] + 1) % 128
    elif corruption == "native-encoding":
        value["native_encoding"] = "unsigned-big-endian-q8.8"
    elif corruption == "native-offset":
        value["unpacked_offsets"][0] += 1
    elif corruption == "native-screen":
        value["screen_value"] = "126" if value["screen_value"] == "127" else "127"
    elif corruption == "excluded-cell":
        claim["recipe"]["analog_four_scope"]["parameter_cells"] = [
            {"item_id": 1, "parameter_key": "osc1_pwm_speed"}
        ]
    elif corruption == "locked-track":
        claim["recipe"]["analog_four_scope"]["locked_ids"] = [1, 2]
    elif corruption == "legacy-without-profile":
        claim["recipe"].pop("profile")
        claim["recipe"].pop("a4_algorithm")
    elif corruption == "native-without-profile":
        claim["recipe"].pop("profile")
    elif corruption.startswith("empty-values"):
        claim["analog_four_candidate"]["values"] = []
        claim["analog_four_candidate"]["semantic_fingerprint"] = (
            "0" * 16
            if corruption == "empty-values-wrong-fingerprint"
            else claim["source_a4_fingerprint"]
        )
    else:
        claim["recipe"]["seed"] += 1
        claim["rytm_candidate"]["seed"] += 1
    modified = (
        json.dumps(raw, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        + "\n"
    ).encode()
    path.write_bytes(modified)
    target = ShowBankStore(tmp_path / "clean")
    with pytest.raises(DataError):
        ShowPackService(tmp_path / "packs", store=target).import_into_store(exported.package_id)
    assert not target.root.exists()
    assert path.read_bytes() == modified


@pytest.mark.parametrize("field", ["filter2_resonance", A4_FILTER1_FREQUENCY_PARAMETER])
def test_native_preparation_verifies_parameter_cells_and_normalizes_f1_alias(
    tmp_path: Path, field: str
) -> None:
    journey = _journey(tmp_path)
    (candidate,) = _generate(journey, fields=(field,), count=1)
    entry = journey.workspace.bank(journey.bank_id).entry(journey.entry_id)
    source = journey.originals[ANALOG_FOUR_DEVICE_ID]
    frame = _frame(journey, candidate)
    now = journey.workspace.bank(journey.bank_id).updated_at
    context = A4PreparationContext(
        scope=MutationScope(frozenset((1, 2)), frozenset((2,))),
        capture_after=now,
        checked_at=now,
        current_capture=None,
        active_candidate_id=candidate.candidate_id,
        session_connected=False,
        candidate_is_local=False,
        source_reloaded=False,
        output_port_name=None,
    )
    report = prepare_a4_audition(
        entry=entry, source_frame=source, candidate_frame=frame, context=context
    )
    assert report.candidate_bytes_verified
    forged = replace(
        candidate,
        recipe=replace(
            candidate.recipe,
            analog_four_scope=replace(
                candidate.recipe.analog_four_scope, parameters=ParameterSelection(())
            ),
        ),
    )
    report = prepare_a4_audition(
        entry=replace(entry, candidates=(forged,)),
        source_frame=source,
        candidate_frame=frame,
        context=context,
    )
    assert (
        not report.candidate_bytes_verified and "candidate_bytes_invalid" in report.blocked_reasons
    )


def test_import_copy_is_create_only_and_revokes_session_output_intent(tmp_path: Path) -> None:
    journey = _journey(tmp_path / "source")
    (candidate,) = _generate(journey, count=1)
    bank = _favorite(journey, candidate)
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    exported = service.export(bank)
    session = _session(journey.workspace, bank.bank_id, journey.entry_id, tmp_path)
    session.show_pack_service = service
    session.hardware_intent = True
    ack = asyncio.run(
        handlers.handle_command(
            {
                "request_id": "native-import",
                "command": {
                    "type": "show_bank_import",
                    "pack_name": exported.package_id,
                    "destination_bank_id": "native-copy",
                },
            },
            session,
        )
    )
    assert ack["ok"], ack
    assert ack["show_pack_import"]["bank_id"] == "native-copy"
    assert session.armed_apply is None and not session.hardware_intent
    assert session.current_send_plan is None and session.recalled_offline_favorite
    assert journey.workspace.bank(bank.bank_id) == bank
    assert (
        journey.workspace.original_source_frames("native-copy", journey.entry_id)
        == journey.originals
    )
    before = _disk(journey.workspace.store.root)
    with pytest.raises(FileExistsError, match="namespace already exists"):
        service.import_into_store(exported.package_id, destination_bank_id="native-copy")
    assert _disk(journey.workspace.store.root) == before
