"""Adversarial appliance scopes, persistence, and shared-dispatch integration.

The only device adapter here is the existing MockDeviceAdapter. Capture tests
use committed frames through the production decoder, never simulated receipts.
"""

from __future__ import annotations

import asyncio
import copy
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import pytest

from rytm_randomizer.cockpit import appliance as appliance_module
from rytm_randomizer.cockpit.appliance import (
    DEVICE_IDS,
    PROFILE_LIMIT,
    STORAGE_LIMIT,
    ApplianceScope,
    ApplianceWorkspace,
    validated_object,
)
from rytm_randomizer.cockpit.capture.appliance_a4 import (
    appliance_a4_parameter_encodings,
    appliance_snapshot_from_a4_capture,
)
from rytm_randomizer.cockpit.capture.appliance_capabilities import parameter_capabilities
from rytm_randomizer.cockpit.capture.service import decode_kit_capture_frame
from rytm_randomizer.cockpit.data import PadState, ProfileModel, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import appliance_handlers
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices import AnalogFourKitSnapshot
from rytm_randomizer.devices.analog_four_fields import A4Kit
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from rytm_randomizer.observability.metrics import MidiMetrics

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("contents", "reason", "from_version", "to_version"),
    [
        (b"private corrupt content", "unreadable", None, None),
        (b'{"schema_version":999}', "schema_newer_than_app", 999, 1),
    ],
)
def test_profile_refusal_is_observable_without_disclosing_saved_content(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    contents: bytes,
    reason: str,
    from_version: int | None,
    to_version: int | None,
) -> None:
    profile_file = tmp_path / "private-profile.json"
    profile_file.write_bytes(contents)
    metrics = MidiMetrics()
    monkeypatch.setattr(appliance_module, "get_metrics", lambda: metrics)
    monkeypatch.setattr(appliance_module._logger, "handlers", [caplog.handler])
    with caplog.at_level(logging.WARNING, logger=appliance_module._logger.name):
        workspace = ApplianceWorkspace(simulation=False, profile_file=profile_file)
    assert workspace.storage_error is not None and not workspace.profiles
    assert profile_file.read_bytes() == contents
    assert metrics.persisted_state_refusals_by_code == {f"appliance_scopes:{reason}": 1}
    record = next(item for item in caplog.records if item.msg == "appliance_profile_load_refused")
    assert record.reason == reason and record.outcome == "preserved_refused"
    assert record.getMessage() == "appliance_profile_load_refused"
    assert record.args == () and record.exc_info is None and record.stack_info is None
    standard_fields = logging.makeLogRecord({}).__dict__.keys()
    application_fields = {
        key: value
        for key, value in record.__dict__.items()
        if key not in standard_fields and key not in {"message", "asctime", "op_id"}
    }
    assert application_fields == {
        "store_id": "appliance_scopes",
        "reason": reason,
        "from_version": from_version,
        "to_version": to_version,
        "outcome": "preserved_refused",
    }


def _source() -> Snapshot:
    return Snapshot(
        "safety-source",
        DEVICE_IDS[0],
        datetime(2026, 9, 30, tzinfo=timezone.utc),
        (
            PadState(1, "SY Raw", {"detune": 64, "dec": 70, "filter_type": 3, "unmapped": 250}),
            PadState(2, "BD Hard", {"dec": 22, "tun": 12, "flt": 80}),
        ),
        None,
        None,
    )


@pytest.fixture
def safe_workspace() -> ApplianceWorkspace:
    workspace = ApplianceWorkspace(simulation=True)
    workspace.sync(_source(), context="initial")
    return workspace


@pytest.fixture
def safe_profile(tmp_path: Path) -> ProfileModel:
    return ProfileRegistry(tmp_path / "registry").list_profiles()[0]


def _identities(value: str | None = None) -> dict[str, object]:
    return dict.fromkeys(DEVICE_IDS, value)


def _document(workspace: ApplianceWorkspace) -> dict[str, object]:
    workspace.profile_action("profile_save", {"name": "SAFE"}, _identities("source-fingerprint"))
    document = workspace.profile_action("profile_export", {"name": "SAFE"}, _identities())
    assert document is not None
    return document


def _session(tmp_path: Path, *, simulation: bool = True) -> CockpitSession:
    source = _source()
    history = HistoryStore()
    history.initial(source)
    return CockpitSession(
        ProfileRegistry(tmp_path / "registry"),
        history,
        MockDeviceAdapter(source),
        appliance=ApplianceWorkspace(simulation=simulation, profile_file=tmp_path / "rules.json"),
    )


def _dispatch(session: CockpitSession, operation: object, **payload: object) -> dict[str, object]:
    workspace = session.appliance
    revision = workspace.revision if workspace is not None else 0
    return asyncio.run(
        handle_command(
            {
                "request_id": "safety-request",
                "command": {
                    "type": "appliance",
                    "operation": operation,
                    "expected_revision": revision,
                    "payload": payload,
                },
            },
            session,
        )
    )


def test_continuous_bounds_come_from_actual_engine_and_unknown_fields_stay_exact(
    safe_workspace: ApplianceWorkspace, safe_profile: ProfileModel
) -> None:
    safe_workspace.change_scope(
        {"master_depth": 1, "lanes": {DEVICE_IDS[0]: {"target_ids": [1], "parameter_locks": []}}}
    )
    for seed in range(12):
        safe_workspace.roll(safe_profile, seed)
        candidate = safe_workspace.candidates[DEVICE_IDS[0]]
        source_delta = next(row for row in candidate.pad_deltas if row.pad_id == 1)
        assert 40 <= source_delta.proposed_params["detune"] <= 88
        assert source_delta.proposed_params["filter_type"] == 3
        assert source_delta.proposed_params["unmapped"] == 250
        assert all(row.pad_id != 2 for row in candidate.pad_deltas)
        assert safe_workspace.sources[DEVICE_IDS[0]].pads[1] == _source().pads[1]


@pytest.mark.parametrize(
    "patch",
    [
        {"target_ids": []},
        {"locked_ids": [1, 2, 3, 4]},
        {"page_ids": []},
        {"track_depths": {"1": 0, "2": 0, "3": 0, "4": 0}},
    ],
)
def test_both_preflights_every_lane_before_any_engine_call(
    safe_workspace: ApplianceWorkspace,
    safe_profile: ProfileModel,
    patch: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    safe_workspace.change_scope({"target": "both", "lanes": {DEVICE_IDS[1]: patch}})
    called: list[object] = []
    monkeypatch.setattr(appliance_module, "mutate", lambda *args, **kwargs: called.append(args))
    with pytest.raises(ValueError, match="linked BOTH"):
        safe_workspace.roll(safe_profile, 4)
    assert called == []
    assert safe_workspace.candidate is None
    assert safe_workspace.candidates == {}


def test_all_parameters_locked_or_unknown_yields_no_candidate_or_engine_work(
    safe_workspace: ApplianceWorkspace,
    safe_profile: ProfileModel,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    locks = [row.parameter_id for row in parameter_capabilities(DEVICE_IDS[0])]
    safe_workspace.change_scope({"lanes": {DEVICE_IDS[0]: {"parameter_locks": locks}}})
    monkeypatch.setattr(
        appliance_module,
        "mutate",
        lambda *args, **kwargs: pytest.fail("no eligible parameter should run the engine"),
    )
    safe_workspace.roll(safe_profile, 123)
    assert safe_workspace.candidate is None
    safe_workspace.change_scope({"lanes": {DEVICE_IDS[0]: {"parameter_locks": [], "page_ids": []}}})
    safe_workspace.roll(safe_profile, 123)
    assert not safe_workspace.candidates


@pytest.mark.parametrize(
    "payload",
    [
        None,
        {1: "wrong-key"},
        {"target_ids": "1"},
        {"page_ids": "SRC"},
        {"page_ids": [1]},
        {"page_ids": ["SRC", "SRC"]},
    ],
)
def test_untyped_or_duplicate_scope_input_is_refused(payload: object) -> None:
    with pytest.raises(ValueError):
        ApplianceScope.parse(payload, DEVICE_IDS[0])
    with pytest.raises(ValueError):
        validated_object({1: "wrong"})


@pytest.mark.parametrize("name", [None, "", "   ", "x" * 65, "line\nbreak", "control\x00"])
def test_profile_names_are_bounded_and_printable(
    safe_workspace: ApplianceWorkspace, name: object
) -> None:
    with pytest.raises(ValueError, match="printable"):
        safe_workspace.profile_action("profile_save", {"name": name}, _identities())
    assert safe_workspace.profiles == {}


@pytest.mark.parametrize(
    "patch",
    [
        {"target": "bad"},
        {"lanes": {}},
        {"association": {"fingerprints": {}}},
        {"association": {"fingerprints": dict.fromkeys(DEVICE_IDS, 1)}},
        {"association": {"fingerprints": dict.fromkeys(DEVICE_IDS, "x" * 129)}},
    ],
)
def test_profile_import_refuses_bad_association_before_replacing_existing_rules(
    safe_workspace: ApplianceWorkspace, patch: dict[str, object]
) -> None:
    document = _document(safe_workspace)
    malformed = copy.deepcopy(document)
    malformed["profiles"]["SAFE"].update(patch)
    before = copy.deepcopy(safe_workspace.profiles)
    with pytest.raises(ValueError):
        safe_workspace.profile_action("profile_import", {"document": malformed}, _identities())
    assert safe_workspace.profiles == before


def test_import_and_save_limits_refuse_without_publishing(
    safe_workspace: ApplianceWorkspace,
) -> None:
    document = _document(safe_workspace)
    profile = document["profiles"]["SAFE"]
    too_many = {
        "schema_version": 1,
        "profiles": {str(i): profile for i in range(PROFILE_LIMIT + 1)},
    }
    with pytest.raises(ValueError, match="too many profiles"):
        safe_workspace._validated_profiles(too_many)
    safe_workspace.profiles = {str(i): profile for i in range(PROFILE_LIMIT)}
    with pytest.raises(ValueError, match="profile limit"):
        safe_workspace.profile_action("profile_save", {"name": "NEW"}, _identities())
    with pytest.raises(ValueError, match="import exceeds"):
        safe_workspace.profile_action(
            "profile_import", {"document": "x" * STORAGE_LIMIT}, _identities()
        )
    with pytest.raises(ValueError, match="storage limit"):
        safe_workspace._publish({"too-large": {"data": "x" * STORAGE_LIMIT}})
    with pytest.raises(ValueError, match="profile does not exist"):
        safe_workspace.profile_action("profile_delete", {"name": "ABSENT"}, _identities())


def test_production_profile_recall_requires_known_matching_identity(
    safe_workspace: ApplianceWorkspace,
) -> None:
    safe_workspace.simulation = False
    safe_workspace.profile_action("profile_save", {"name": "UNKNOWN"}, _identities())
    with pytest.raises(ValueError, match="identity is unknown"):
        safe_workspace.profile_action("profile_load", {"name": "UNKNOWN"}, _identities())
    safe_workspace.profile_action("profile_save", {"name": "KNOWN"}, _identities("known"))
    with pytest.raises(ValueError, match="differs from current kit"):
        safe_workspace.profile_action("profile_load", {"name": "KNOWN"}, _identities("other"))
    safe_workspace.profile_action("profile_load", {"name": "KNOWN"}, _identities("known"))
    assert safe_workspace.candidate is None
    assert safe_workspace.profiles["KNOWN"]["association"]["fingerprints"] == _identities("known")


def test_corrupt_recovery_keeps_exact_original_and_only_publishes_validated_import(
    safe_workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    document = _document(safe_workspace)
    target = tmp_path / "corrupt-rules.json"
    target.write_bytes(b"{broken")
    recovering = ApplianceWorkspace(simulation=True, profile_file=target)
    with pytest.raises(ValueError, match="explicit validated import"):
        recovering.profile_action("profile_save", {"name": "NEW"}, _identities())
    recovering.profile_action("profile_import", {"document": document}, _identities())
    backups = list(tmp_path.glob("corrupt-rules.json.recovery-*"))
    assert len(backups) == 1 and backups[0].read_bytes() == b"{broken"
    assert json.loads(target.read_bytes()) == document
    assert recovering.storage_error is None
    assert recovering.candidate is None and recovering.anchor is None


def test_future_schema_and_oversized_original_are_never_overwritten(
    safe_workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    document = _document(safe_workspace)
    target = tmp_path / "rules.json"
    original = json.dumps({"schema_version": 999, "profiles": {}}).encode()
    target.write_bytes(original)
    future = ApplianceWorkspace(simulation=True, profile_file=target)
    assert future.storage_error == "persisted_state.schema_newer_than_app"
    with pytest.raises(ValueError, match="newer profile schema"):
        future.profile_action("profile_import", {"document": document}, _identities())
    assert target.read_bytes() == original
    oversized = b"x" * (STORAGE_LIMIT + 1)
    target.write_bytes(oversized)
    limited = ApplianceWorkspace(simulation=True, profile_file=target)
    assert limited.storage_error == "profile_storage_corrupt_or_unreadable"
    with pytest.raises(ValueError, match="oversize original"):
        limited.profile_action("profile_import", {"document": document}, _identities())
    assert target.read_bytes() == oversized


def test_atomic_full_disk_failure_preserves_rules_and_existing_file(
    safe_workspace: ApplianceWorkspace, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    document = _document(safe_workspace)
    target = tmp_path / "rules.json"
    original = json.dumps(document).encode()
    target.write_bytes(original)
    saved = ApplianceWorkspace(simulation=True, profile_file=target)
    before = copy.deepcopy(saved.profiles)

    def full_disk(*args: object, **kwargs: object) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(appliance_module, "atomic_write", full_disk)
    with pytest.raises(OSError, match="disk full"):
        saved.profile_action("profile_save", {"name": "NEW"}, _identities())
    assert saved.profiles == before
    assert target.read_bytes() == original


def test_missing_profile_file_and_corrupt_mapping_return_actionable_state(tmp_path: Path) -> None:
    absent = ApplianceWorkspace(simulation=False, profile_file=tmp_path / "absent.json")
    assert absent.profiles == {} and absent.storage_error is None
    state = absent.state(provenance={device: {} for device in DEVICE_IDS}, armed=False)
    assert state["mode"] == "production" and not state["armed"]
    assert not state["history"]["hardware_restore_supported"]
    assert all(lane["reference_track_id"] is not None for lane in state["lanes"].values())
    corrupt = tmp_path / "corrupt-shape.json"
    corrupt.write_text(json.dumps({"schema_version": 1, "profiles": []}))
    failed = ApplianceWorkspace(simulation=False, profile_file=corrupt)
    state = failed.state(provenance={device: {} for device in DEVICE_IDS}, armed=False)
    assert state["blocked_reasons"] == ["profile_storage_corrupt_or_unreadable"]


def test_state_values_are_track_and_engine_specific_and_empty_target_has_no_reference(
    safe_workspace: ApplianceWorkspace,
) -> None:
    safe_workspace.change_scope({"lanes": {DEVICE_IDS[0]: {"target_ids": [2]}}})
    state = safe_workspace.state(provenance={device: {} for device in DEVICE_IDS}, armed=False)
    lane = state["lanes"][DEVICE_IDS[0]]
    assert lane["reference_track_id"] == 2
    sy_decay = next(
        row
        for row in lane["parameters"]
        if row["parameter"] == "Decay" and row["machine_key"] == "sy_raw"
    )
    bd_decay = next(
        row
        for row in lane["parameters"]
        if row["parameter"] == "Decay" and row["machine_key"] == "bd_hard"
    )
    assert sy_decay["values_by_track"] == {"1": 70} and sy_decay["value"] is None
    assert bd_decay["values_by_track"] == {"2": 22} and bd_decay["value"] == 22
    safe_workspace.change_scope({"lanes": {DEVICE_IDS[0]: {"target_ids": []}}})
    state = safe_workspace.state(provenance={device: {} for device in DEVICE_IDS}, armed=False)
    assert state["lanes"][DEVICE_IDS[0]]["reference_track_id"] is None
    assert all(row["value"] is None for row in state["lanes"][DEVICE_IDS[0]]["parameters"])


def test_local_navigation_does_not_claim_restore_and_production_apply_is_always_refused(
    safe_workspace: ApplianceWorkspace,
) -> None:
    for action in ("undo", "redo", "return_anchor"):
        with pytest.raises(ValueError):
            safe_workspace.navigate(action)
    safe_workspace.simulation = False
    safe_workspace.sync(_source(), context="production")
    assert set(safe_workspace.sources) == {DEVICE_IDS[0]}
    with pytest.raises(ValueError, match="live apply requires"):
        safe_workspace.apply_local({"confirmed": True}, hardware_intent=False)
    safe_workspace.navigate("anchor")
    safe_workspace.navigate("return_anchor")
    assert safe_workspace.last_receipt["status"] == "local_history_only"
    assert safe_workspace.last_receipt["sent_count"] == 0


def test_disconnect_revokes_all_transient_assumptions_and_preserves_saved_rules(
    safe_workspace: ApplianceWorkspace, safe_profile: ProfileModel
) -> None:
    _document(safe_workspace)
    safe_workspace.navigate("anchor")
    safe_workspace.roll(safe_profile, 5)
    assert safe_workspace.candidate is not None
    before = copy.deepcopy(safe_workspace.profiles)
    revision = safe_workspace.revision
    safe_workspace.revoke_context()
    assert safe_workspace.revision == revision + 1
    assert safe_workspace.context is None
    assert safe_workspace.candidate is None and not safe_workspace.candidates
    assert safe_workspace.anchor is None and not safe_workspace.sources
    assert not safe_workspace.histories and not safe_workspace.timeline
    assert safe_workspace.cursor == 0
    assert safe_workspace.profiles == before


def test_shared_dispatch_exercises_simulated_scope_roll_apply_history_and_profiles(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path)
    state = _dispatch(session, "state")
    assert state["ok"] and state["appliance"]["mode"] == "simulation"
    assert _dispatch(session, "scope", target="both")["ok"]
    assert _dispatch(session, "anchor")["ok"]
    assert _dispatch(session, "mutate")["ok"]
    candidate = session.appliance.candidate
    assert candidate is not None
    applied = _dispatch(session, "apply", candidate_id=candidate["candidate_id"], confirmed=True)
    assert applied["ok"] and applied["appliance"]["last_receipt"]["sent_count"] == 0
    assert _dispatch(session, "undo")["ok"]
    assert _dispatch(session, "redo")["ok"]
    assert _dispatch(session, "return_anchor")["ok"]
    assert _dispatch(session, "profile_save", name="LIVE")["ok"]
    exported = _dispatch(session, "profile_export", name="LIVE")
    assert exported["ok"] and exported["document"]["schema_version"] == 1
    assert _dispatch(session, "profile_delete", name="LIVE")["ok"]
    assert _dispatch(session, "profile_import", document=exported["document"])["ok"]
    assert _dispatch(session, "profile_load", name="LIVE")["ok"]
    assert session.pending_events[-1]["type"] == "appliance_changed"


@pytest.mark.parametrize("operation", [None, "wrong", 1])
def test_unknown_shared_command_does_not_initialize_workspace(
    tmp_path: Path, operation: object
) -> None:
    session = _session(tmp_path)
    session.appliance = None
    result = _dispatch(session, operation)
    assert not result["ok"] and result["code"] == "validation_error"
    assert session.appliance is None


@pytest.mark.parametrize("revision", [True, "1", -1, None])
def test_shared_dispatch_rejects_stale_boolean_or_untyped_revisions(
    tmp_path: Path, revision: object
) -> None:
    session = _session(tmp_path)
    assert _dispatch(session, "state")["ok"]
    result = asyncio.run(
        handle_command(
            {
                "request_id": "r",
                "command": {
                    "type": "appliance",
                    "operation": "anchor",
                    "expected_revision": revision,
                },
            },
            session,
        )
    )
    assert not result["ok"] and result["code"] == "validation_error"
    assert session.appliance.anchor is None


def test_dispatch_lazy_initialization_is_explicitly_simulated_or_production(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv(appliance_handlers.PROFILE_FILE_ENV, str(tmp_path / "scope-rules.json"))
    monkeypatch.setenv(appliance_handlers.SIMULATION_ENV, "1")
    session = _session(tmp_path)
    session.appliance = None
    assert _dispatch(session, "state")["appliance"]["mode"] == "simulation"
    assert session.appliance.profile_file == tmp_path / "scope-rules.json"
    monkeypatch.delenv(appliance_handlers.SIMULATION_ENV)
    monkeypatch.delenv(appliance_handlers.PROFILE_FILE_ENV)
    monkeypatch.setattr(
        appliance_handlers, "default_profiles_dir", lambda: tmp_path / "canonical" / "profiles"
    )
    session.appliance = None
    result = _dispatch(session, "state")
    assert result["appliance"]["mode"] == "production"
    assert session.appliance.profile_file == tmp_path / "canonical" / "appliance-scopes.json"
    assert all(
        lane["provenance"]["source_type"] == "disconnected"
        for lane in result["appliance"]["lanes"].values()
    )


def test_dispatch_requires_profile_and_hardware_intent_never_downgrades_to_mock(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    session = _session(tmp_path)
    assert _dispatch(session, "state")["ok"]
    monkeypatch.setattr(session.profile_registry, "list_profiles", lambda: [])
    result = _dispatch(session, "mutate")
    assert not result["ok"] and result["code"] == "validation_error"
    session.active_profile = ProfileRegistry(tmp_path / "other").list_profiles()[0]
    assert _dispatch(session, "state")["ok"]
    assert _dispatch(session, "mutate")["ok"]
    candidate = session.appliance.candidate
    assert candidate is not None
    session.hardware_intent = True
    result = _dispatch(session, "apply", candidate_id=candidate["candidate_id"], confirmed=True)
    assert not result["ok"]
    assert session.appliance.last_receipt is None
    assert session.appliance.candidate is None
    assert session.device.capture_snapshot() == _source()


def test_production_capture_provenance_uses_real_decoder_without_unsaved_claim(
    tmp_path: Path,
) -> None:
    session = _session(tmp_path, simulation=False)
    fixtures = Path(__file__).resolve().parents[1] / "fixtures" / "rio145"
    for device, filename in [
        (DEVICE_IDS[0], "RYTM_Test1_Init_Kit.syx"),
        (DEVICE_IDS[1], "A4_Test1_Init_Kit.syx"),
    ]:
        session.kit_captures[device] = decode_kit_capture_frame(
            device, (fixtures / filename).read_bytes()
        )
    result = _dispatch(session, "state")
    assert result["ok"]
    assert set(session.appliance.sources) == set(DEVICE_IDS)
    for device in DEVICE_IDS:
        provenance = result["appliance"]["lanes"][device]["provenance"]
        assert provenance["source_type"] == "saved_kit"
        assert provenance["fingerprint"] == session.kit_captures[device].fingerprint
        assert provenance["captured_at"]
        assert provenance["working_state_verified"] is False
    assert not _dispatch(session, "apply", confirmed=True)["ok"]


def _captured_session(tmp_path: Path) -> CockpitSession:
    session = _session(tmp_path, simulation=False)
    fixtures = Path(__file__).parents[1] / "fixtures/rio145"
    for device, filename in [
        (DEVICE_IDS[0], "RYTM_Test1_Init_Kit.syx"),
        (DEVICE_IDS[1], "A4_Test1_Init_Kit.syx"),
    ]:
        session.kit_captures[device] = decode_kit_capture_frame(
            device, (fixtures / filename).read_bytes()
        )
    captured = session.kit_captures[DEVICE_IDS[1]]
    assert isinstance(captured.snapshot, AnalogFourKitSnapshot)
    kit = A4Kit.from_bytes(captured.snapshot.unpacked)
    for track, frequency in [(0, 0x4003), (1, 0x4137)]:
        sound = kit.sound(track)
        sound.set_fixed_8_8_raw("filter1_frequency", frequency)
        sound.set_oscillator_pitch_raw(1, 0x4003)
        sound.set_mod_depth("env2_depth_a", -1 / 128)
        sound.set_bipolar("osc1_detune", -17)
        kit.replace_sound(track, sound)
    source = decode_analog_four_saved_kit_payload(captured.frame[1:-1], require_trailer=True)
    encoded = encode_analog_four_saved_kit_payload(source.prefix, kit.to_bytes())
    session.kit_captures[DEVICE_IDS[1]] = decode_kit_capture_frame(
        DEVICE_IDS[1], b"\xf0" + encoded.payload + b"\xf7"
    )
    return session


def test_captured_production_a4_state_is_native_and_repeated_state_preserves_context(
    tmp_path: Path,
) -> None:
    session = _captured_session(tmp_path)
    first = _dispatch(session, "state")
    assert first["ok"]
    source_ids = {
        device: snapshot.snapshot_id for device, snapshot in session.appliance.sources.items()
    }
    state = _dispatch(session, "state")
    assert state["ok"]
    assert source_ids == {
        device: snapshot.snapshot_id for device, snapshot in session.appliance.sources.items()
    }
    rows = state["appliance"]["lanes"][DEVICE_IDS[1]]["parameters"]
    frequency = next(row for row in rows if row["parameter"] == "Filter1 Frequency")
    assert frequency["values_by_track"]["1"] == 0x4003
    assert frequency["values_by_track"]["2"] == 0x4137
    assert frequency["display_values_by_track"]["1"] == "64.01171875"
    assert frequency["display_values_by_track"]["2"] == "65.21484375"
    fine = next(row for row in rows if row["parameter"] == "OSC1 Fine")
    assert fine["value"] == 1 and fine["display_value"] == "1"
    unsupported = next(row for row in rows if row["parameter"] == "Performance Parameter A")
    assert unsupported["value"] is None and not unsupported["values_by_track"]
    assert unsupported["blockers"]
    assert not state["appliance"]["history"]["hardware_restore_supported"]


def test_a4_native_preview_is_scoped_deterministic_and_never_grants_apply(tmp_path: Path) -> None:
    session = _captured_session(tmp_path)
    assert _dispatch(session, "state")["ok"]
    workspace = session.appliance
    source = workspace.sources[DEVICE_IDS[1]]
    original_frame = session.kit_captures[DEVICE_IDS[1]].frame
    assert _dispatch(
        session, "scope", target="a4", master_depth=0.1, lanes={DEVICE_IDS[1]: {"target_ids": [1]}}
    )["ok"]
    profile = session.profile_registry.list_profiles()[0]
    workspace.roll(profile, 29)
    candidate = workspace.candidates[DEVICE_IDS[1]]
    proposal = candidate.pad_deltas[0]
    assert len(candidate.pad_deltas) == 1 and proposal.pad_id == 1
    assert proposal.changed_keys
    encodings = {row.parameter_id: row for row in appliance_a4_parameter_encodings()}
    rows = {row.parameter_id: row for row in parameter_capabilities(DEVICE_IDS[1])}
    for key, value in proposal.proposed_params.items():
        encodings[key].validate_raw(value)
        if rows[key].default_protected:
            assert value == source.pads[0].params[key]
    frequency_id = next(key for key, row in encodings.items() if row.field == "filter1_frequency")
    assert proposal.proposed_params[frequency_id] > 127
    assert proposal.proposed_params[frequency_id] % 256 != 0
    assert source.pads[0].params[frequency_id] == 0x4003
    assert not workspace.candidate["live_ready"] and workspace.candidate["send_plan_id"] is None
    change = next(
        row for row in workspace.candidate["changes"] if row["parameter_id"] == frequency_id
    )
    assert change["before"] == 0x4003 and change["before_display"] == "64.01171875"
    assert change["after_display"] == encodings[frequency_id].format_display(change["after"])
    workspace.roll(profile, 29)
    assert workspace.candidates[DEVICE_IDS[1]].pad_deltas == candidate.pad_deltas
    receipt = _dispatch(
        session, "apply", candidate_id=workspace.candidate["candidate_id"], confirmed=True
    )
    assert not receipt["ok"]
    assert workspace.sources[DEVICE_IDS[1]] == source
    assert workspace.last_receipt is None
    assert session.kit_captures[DEVICE_IDS[1]].frame == original_frame


def test_even_explicit_unprotect_keeps_fine_shared_field_and_unknown_selectors_exact(
    tmp_path: Path,
) -> None:
    session = _captured_session(tmp_path)
    assert _dispatch(session, "state")["ok"]
    workspace = session.appliance
    source = workspace.sources[DEVICE_IDS[1]]
    assert _dispatch(
        session,
        "scope",
        target="a4",
        lanes={DEVICE_IDS[1]: {"target_ids": [1], "parameter_locks": []}},
    )["ok"]
    workspace.roll(session.profile_registry.list_profiles()[0], 21)
    proposal = workspace.candidates[DEVICE_IDS[1]].pad_deltas[0]
    for encoding in appliance_a4_parameter_encodings():
        if encoding.categorical or not encoding.offline_mutable:
            assert (
                proposal.proposed_params[encoding.parameter_id]
                == source.pads[0].params[encoding.parameter_id]
            )
            assert encoding.parameter_id not in proposal.changed_keys


def test_native_production_both_preview_stages_both_and_refuses_partial_lane(
    tmp_path: Path,
) -> None:
    session = _captured_session(tmp_path)
    assert _dispatch(session, "state")["ok"]
    assert _dispatch(session, "scope", target="both")["ok"]
    assert _dispatch(session, "mutate")["ok"]
    workspace = session.appliance
    assert set(workspace.candidates) == set(DEVICE_IDS)
    assert {row["device_id"] for row in workspace.candidate["changes"]} == set(DEVICE_IDS)
    assert _dispatch(session, "scope", lanes={DEVICE_IDS[1]: {"target_ids": []}})["ok"]
    assert not _dispatch(session, "mutate")["ok"]
    assert workspace.candidate is None and not workspace.candidates


def test_simulation_ignores_native_capture_and_retains_its_explicit_encoding(
    safe_workspace: ApplianceWorkspace, tmp_path: Path
) -> None:
    source = _captured_session(tmp_path).kit_captures[DEVICE_IDS[1]]
    captured_snapshot = appliance_snapshot_from_a4_capture(source)
    safe_workspace.sync(_source(), context="simulation-with-capture", a4_source=captured_snapshot)
    assert safe_workspace.sources[DEVICE_IDS[1]].pads[0].machine == "SIMULATED NORMALIZED MIDI"
    assert set(safe_workspace.sources[DEVICE_IDS[1]].pads[0].params.values()) == {64}


def test_native_source_documented_only_values_do_not_become_mutable(tmp_path: Path) -> None:
    workspace = ApplianceWorkspace(simulation=False)
    row = next(row for row in parameter_capabilities(DEVICE_IDS[1]) if not row.native_fields)
    source = Snapshot(
        "documented-source",
        DEVICE_IDS[1],
        datetime.now(timezone.utc),
        (PadState(1, "A4 CAPTURED SAVED KIT", {row.parameter_id: 64}),),
        None,
        None,
    )
    workspace.sync(None, context="documented-only", a4_source=source)
    workspace.change_scope({"target": "a4", "lanes": {DEVICE_IDS[1]: {"parameter_locks": []}}})
    workspace.roll(ProfileRegistry(tmp_path / "registry").list_profiles()[0], 42)
    assert workspace.candidate is None and not workspace.candidates
