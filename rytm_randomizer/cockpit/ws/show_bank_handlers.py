"""WebSocket command adapters for the server-authoritative Show Kit Forge."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from types import MappingProxyType
from typing import Final, cast

from ...guardrails.input_validation import (
    require_boolean,
    require_exact_keys,
    require_float,
    require_int,
    require_integer_tuple,
    require_object,
    require_text,
    require_text_tuple,
)
from ..data.show_bank import (
    OxiShowMetadata,
    ShowKitDepthPreset,
    ShowKitDeviceId,
    narrow_show_kit_depth_preset,
    narrow_show_kit_device_id,
)
from ..show_bank.workspace import CaptureKind, ShowKitForgeWorkspace
from ..stage.policy import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID
from .protocol import (
    COMMAND_SHOW_BANK_ADOPT_SOURCES,
    COMMAND_SHOW_BANK_ATTEST_HARDWARE_SAVED,
    COMMAND_SHOW_BANK_CREATE,
    COMMAND_SHOW_BANK_DUPLICATE_ENTRY,
    COMMAND_SHOW_BANK_EXPORT,
    COMMAND_SHOW_BANK_GENERATE_CANDIDATES,
    COMMAND_SHOW_BANK_IMPORT,
    COMMAND_SHOW_BANK_LIST,
    COMMAND_SHOW_BANK_MARK_FAVORITE,
    COMMAND_SHOW_BANK_REMOVE_ENTRY,
    COMMAND_SHOW_BANK_REORDER_ENTRIES,
    COMMAND_SHOW_BANK_RETAIN_CAPTURE,
    COMMAND_SHOW_BANK_RETURN_SOURCE,
    COMMAND_SHOW_BANK_RUN_PREFLIGHT,
    COMMAND_SHOW_BANK_SELECT,
    COMMAND_SHOW_BANK_SELECT_CANDIDATE,
    COMMAND_SHOW_BANK_UPDATE,
    COMMAND_SHOW_BANK_UPDATE_ENTRY,
    COMMAND_SHOW_BANK_VERIFY_RECAPTURE,
    EVENT_DUAL_MACHINE_STAGE_CHANGED,
    EVENT_HISTORY_UPDATED,
    EVENT_MUTATION_LOCKS_CHANGED,
    EVENT_MUTATION_PREVIEWED,
    EVENT_MUTATION_TARGETS_CHANGED,
    EVENT_PROFILE_CHANGED,
    EVENT_SEND_PLAN_CHANGED,
    EVENT_SHOW_BANK_CHANGED,
    EVENT_SNAPSHOT_CHANGED,
    ShowBankChangedEvent,
    ShowBankSourceSlotsAck,
    ShowPackExportAck,
    ShowPackImportAck,
)
from .result import HandlerResult
from .session import CockpitSession

A4_HARDWARE_BLOCK_REASON: Final[str] = "a4_hardware_audition_validation_pending"


def _workspace(session: CockpitSession) -> ShowKitForgeWorkspace:
    workspace = session.show_kit_forge
    if workspace is None:
        raise ValueError("Show Kit Forge local persistence is not configured")
    return workspace


def build_show_bank_changed(session: CockpitSession) -> dict[str, object]:
    """Build one complete workspace replacement event."""

    workspace = _workspace(session)
    event: ShowBankChangedEvent = {
        "type": EVENT_SHOW_BANK_CHANGED,
        "show_bank": workspace.state_dict(),
    }
    return dict(event)


def _ok(session: CockpitSession, **values: object) -> HandlerResult:
    return HandlerResult(
        ack={"ok": True, **values},
        events=[build_show_bank_changed(session)],
    )


def _show_bank_text(
    values: Mapping[str, object],
    key: str,
    *,
    allow_empty: bool = False,
) -> str:
    normalized = require_text(values.get(key), key, ValueError).strip()
    if not allow_empty and not normalized:
        raise ValueError(f"{key} must not be empty")
    return normalized


def _integer(values: Mapping[str, object], key: str) -> int:
    return require_int(values.get(key), key, ValueError)


def _optional_integer(values: Mapping[str, object], key: str) -> int | None:
    value = values.get(key)
    return None if value is None else require_int(value, key, ValueError)


def _optional_boolean(values: Mapping[str, object], key: str, *, default: bool) -> bool:
    return require_boolean(values.get(key, default), key, ValueError)


def _number(values: Mapping[str, object], key: str) -> float:
    return require_float(values.get(key), key, ValueError)


def _string_list(values: Mapping[str, object], key: str) -> tuple[str, ...]:
    return require_text_tuple(values.get(key), key, ValueError, kind="list")


def _integer_list(values: Mapping[str, object], key: str) -> tuple[int, ...]:
    return require_integer_tuple(values.get(key), key, ValueError, kind="list")


def _device(values: Mapping[str, object]) -> ShowKitDeviceId:
    return narrow_show_kit_device_id(_show_bank_text(values, "device_id"))


def _capture_kind(values: Mapping[str, object]) -> CaptureKind:
    value = _show_bank_text(values, "capture_kind")
    if value in ("source", "favorite", "candidate"):
        return value
    raise ValueError("capture_kind must be source, favorite, or candidate")


def _oxi(values: Mapping[str, object]) -> OxiShowMetadata:
    mapping = require_object(values.get("oxi"), "oxi", ValueError)
    if mapping.get("direct_oxi_control") is not False:
        raise ValueError("direct OXI control is not supported")
    return OxiShowMetadata(
        project=_show_bank_text(mapping, "project", allow_empty=True),
        pattern=_show_bank_text(mapping, "pattern", allow_empty=True),
        chapter=_show_bank_text(mapping, "chapter", allow_empty=True),
    )


def _ensure_history_snapshot(session: CockpitSession, snapshot_id: str) -> None:
    history = session.history_store.current
    known_ids = {entry.snapshot.snapshot_id for entry in history.entries}
    if snapshot_id in known_ids:
        session.history_store.load(snapshot_id)
        return
    snapshot = session.device.capture_snapshot()
    if snapshot.snapshot_id != snapshot_id:
        raise ValueError("device projection did not adopt the expected source")
    if session.history_store.has_entries:
        session.history_store.append_post_send(snapshot, via="load")
    else:
        session.history_store.initial(snapshot)


def _source_events(session: CockpitSession) -> list[dict[str, object]]:
    snapshot = session.device.capture_snapshot()
    return [
        {"type": EVENT_SNAPSHOT_CHANGED, "snapshot": snapshot.to_dict()},
        {"type": EVENT_HISTORY_UPDATED, "history": session.history_store.current.to_dict()},
        {"type": EVENT_MUTATION_PREVIEWED, "candidate": None},
        {"type": EVENT_SEND_PLAN_CHANGED, "send_plan": None},
        {
            "type": EVENT_DUAL_MACHINE_STAGE_CHANGED,
            "stage": session.stage_coordinator.state.to_dict(),
        },
    ]


def _sync_source(
    session: CockpitSession,
    workspace: ShowKitForgeWorkspace,
    bank_id: str,
    entry_id: str,
) -> list[dict[str, object]]:
    source = workspace.source_snapshot(bank_id, entry_id)
    session.device.adopt_snapshot(source)
    _ensure_history_snapshot(session, source.snapshot_id)
    session.current_candidate = None
    session.current_send_plan = None
    session.stage_coordinator.record_candidate(ANALOG_RYTM_DEVICE_ID, ready=None)
    session.stage_coordinator.record_candidate(
        ANALOG_FOUR_DEVICE_ID,
        ready=None,
        blocked_reason=A4_HARDWARE_BLOCK_REASON,
    )
    return _source_events(session)


def _sync_selected_candidate(
    session: CockpitSession,
    workspace: ShowKitForgeWorkspace,
    bank_id: str,
    entry_id: str,
) -> list[dict[str, object]]:
    _, source, selected = workspace.audition_context(bank_id, entry_id)
    profile = session.profile_registry.get(selected.recipe.profile_id)
    if profile is None:
        raise ValueError("candidate profile is no longer available")
    session.device.adopt_snapshot(source)
    _ensure_history_snapshot(session, source.snapshot_id)
    session.active_profile = profile
    session.depth = selected.recipe.depth
    session.seed = selected.recipe.seed
    session.rytm_pad_targets = set(selected.recipe.rytm_scope.target_ids)
    session.pad_locks = set(selected.recipe.rytm_scope.locked_ids)
    session.a4_track_targets = set(selected.recipe.analog_four_scope.target_ids)
    session.a4_track_locks = set(selected.recipe.analog_four_scope.locked_ids)
    session.current_candidate = selected.rytm_candidate
    session.current_send_plan = None
    session.preview_on = True
    session.stage_coordinator.record_scope(
        ANALOG_RYTM_DEVICE_ID,
        target_ids=frozenset(session.rytm_pad_targets),
        locked_ids=frozenset(session.pad_locks),
        effective_ids=frozenset(selected.recipe.rytm_scope.effective_ids),
    )
    session.stage_coordinator.record_scope(
        ANALOG_FOUR_DEVICE_ID,
        target_ids=frozenset(session.a4_track_targets),
        locked_ids=frozenset(session.a4_track_locks),
        effective_ids=frozenset(selected.recipe.analog_four_scope.effective_ids),
    )
    session.stage_coordinator.record_candidate(ANALOG_RYTM_DEVICE_ID, ready=True)
    session.stage_coordinator.record_candidate(
        ANALOG_FOUR_DEVICE_ID,
        ready=True,
        blocked_reason=A4_HARDWARE_BLOCK_REASON,
    )
    return [
        {"type": EVENT_SNAPSHOT_CHANGED, "snapshot": source.to_dict()},
        {"type": EVENT_HISTORY_UPDATED, "history": session.history_store.current.to_dict()},
        {"type": EVENT_PROFILE_CHANGED, "profile": profile.to_dict()},
        {
            "type": EVENT_MUTATION_TARGETS_CHANGED,
            "rytm_pad_targets": sorted(session.rytm_pad_targets),
            "a4_track_targets": sorted(session.a4_track_targets),
        },
        {
            "type": EVENT_MUTATION_LOCKS_CHANGED,
            "rytm_pad_locks": sorted(session.pad_locks),
            "a4_track_locks": sorted(session.a4_track_locks),
        },
        {
            "type": EVENT_MUTATION_PREVIEWED,
            "candidate": selected.rytm_candidate.to_dict(),
        },
        {"type": EVENT_SEND_PLAN_CHANGED, "send_plan": None},
        {
            "type": EVENT_DUAL_MACHINE_STAGE_CHANGED,
            "stage": session.stage_coordinator.state.to_dict(),
        },
    ]


async def _handle_list(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    if "a4_preparation" in cmd:
        review = require_object(cmd["a4_preparation"], "a4_preparation", ValueError)
        require_exact_keys(
            review,
            frozenset({"bank_id", "entry_id", "expected_revision", "output_port_name"}),
            "a4_preparation",
        )
        port = review["output_port_name"]
        report = workspace.prepare_a4_review(
            require_text(review["bank_id"], "bank_id", ValueError),
            require_text(review["entry_id"], "entry_id", ValueError),
            require_int(review["expected_revision"], "expected_revision", ValueError),
            captures=session.kit_captures,
            target_ids=tuple(session.a4_track_targets),
            locked_ids=tuple(session.a4_track_locks),
            active_candidate_id=(
                None
                if session.current_candidate is None
                else session.current_candidate.candidate_id
            ),
            output_port_name=(
                None if port is None else require_text(port, "output_port_name", ValueError)
            ),
        )
        return _ok(session, show_bank=workspace.state_dict(), a4_preparation=report.to_dict())
    return _ok(session, show_bank=workspace.state_dict())


async def _handle_create(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank = workspace.create_bank(
        name=_show_bank_text(cmd, "name"),
        description=_show_bank_text(cmd, "description", allow_empty=True),
        notes=_string_list(cmd, "notes"),
    )
    return _ok(session, show_bank_id=bank.bank_id)


async def _handle_select(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank = workspace.select_bank(_show_bank_text(cmd, "bank_id"))
    return _ok(session, show_bank_id=bank.bank_id)


async def _handle_update(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank = workspace.update_bank(
        _show_bank_text(cmd, "bank_id"),
        _integer(cmd, "expected_revision"),
        name=_show_bank_text(cmd, "name"),
        description=_show_bank_text(cmd, "description", allow_empty=True),
        notes=_string_list(cmd, "notes"),
    )
    return _ok(session, show_bank_id=bank.bank_id)


async def _handle_adopt_sources(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id_value = cmd.get("entry_id")
    if entry_id_value is not None and not isinstance(entry_id_value, str):
        raise ValueError("entry_id must be a string")
    entry = workspace.adopt_sources(
        bank_id,
        _integer(cmd, "expected_revision"),
        captures=session.kit_captures,
        rytm_fingerprint=_show_bank_text(cmd, "rytm_fingerprint"),
        analog_four_fingerprint=_show_bank_text(cmd, "a4_fingerprint"),
        rytm_slot=_integer(cmd, "rytm_slot"),
        analog_four_slot=_integer(cmd, "a4_slot"),
        entry_id=entry_id_value,
    )
    events = _sync_source(session, workspace, bank_id, entry.entry_id)
    events.append(build_show_bank_changed(session))
    return HandlerResult(ack={"ok": True, "show_bank_entry_id": entry.entry_id}, events=events)


async def _handle_generate(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    profile_id = _show_bank_text(cmd, "profile_id")
    profile = session.profile_registry.get(profile_id)
    if profile is None:
        raise ValueError("unknown candidate profile")
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id = _show_bank_text(cmd, "entry_id")
    depth_preset: ShowKitDepthPreset = narrow_show_kit_depth_preset(
        _show_bank_text(cmd, "depth_preset")
    )
    created = workspace.generate_candidates(
        bank_id,
        entry_id,
        _integer(cmd, "expected_revision"),
        profile=profile,
        depth_preset=depth_preset,
        depth=_number(cmd, "depth"),
        seed=_integer(cmd, "seed"),
        candidate_count=_integer(cmd, "candidate_count"),
        rytm_targets=_integer_list(cmd, "rytm_targets"),
        rytm_locks=_integer_list(cmd, "rytm_locks"),
        analog_four_targets=_integer_list(cmd, "a4_targets"),
        analog_four_locks=_integer_list(cmd, "a4_locks"),
    )
    events = _sync_selected_candidate(session, workspace, bank_id, entry_id)
    events.append(build_show_bank_changed(session))
    return HandlerResult(
        ack={"ok": True, "candidate_ids": [item.candidate_id for item in created]},
        events=events,
    )


async def _handle_select_candidate(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    workspace = _workspace(session)
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id = _show_bank_text(cmd, "entry_id")
    candidate_id = _show_bank_text(cmd, "candidate_id")
    workspace.select_candidate(
        bank_id,
        entry_id,
        candidate_id,
        _integer(cmd, "expected_revision"),
    )
    events = _sync_selected_candidate(session, workspace, bank_id, entry_id)
    events.append(build_show_bank_changed(session))
    return HandlerResult(ack={"ok": True, "candidate_id": candidate_id}, events=events)


async def _handle_mark_favorite(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id = _show_bank_text(cmd, "entry_id")
    candidate_id = _show_bank_text(cmd, "candidate_id")
    workspace.mark_favorite(
        bank_id,
        entry_id,
        candidate_id,
        _integer(cmd, "expected_revision"),
        replace_existing=_optional_boolean(
            cmd,
            "replace_existing",
            default=False,
        ),
    )
    events = _sync_selected_candidate(session, workspace, bank_id, entry_id)
    events.append(build_show_bank_changed(session))
    return HandlerResult(ack={"ok": True, "candidate_id": candidate_id}, events=events)


async def _handle_attest_saved(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.attest_saved(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
        device_id=_device(cmd),
        hardware_slot=_integer(cmd, "slot"),
    )
    return _ok(session, show_bank_entry_id=entry.entry_id)


async def _handle_verify_recapture(
    cmd: dict[str, object], session: CockpitSession
) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.verify_recaptures(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
        captures=session.kit_captures,
    )
    return _ok(session, show_bank_entry_id=entry.entry_id)


async def _handle_run_preflight(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.run_preflight(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
        captures=session.kit_captures,
    )
    return _ok(session, show_ready=entry.status == "show-ready")


async def _handle_return_source(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id = _show_bank_text(cmd, "entry_id")
    source = workspace.return_entry_to_source(bank_id, entry_id, _integer(cmd, "expected_revision"))
    entry = workspace.bank(bank_id).entry(entry_id)
    # ShowBankEntry validates both source slots at construction/import.
    source_slots: ShowBankSourceSlotsAck = {
        "rytm": cast(int, entry.rytm_source.hardware_slot),
        "analog_four": cast(int, entry.analog_four_source.hardware_slot),
    }
    session.device.adopt_snapshot(source)
    _ensure_history_snapshot(session, source.snapshot_id)
    session.current_candidate = None
    session.current_send_plan = None
    session.preview_on = False
    session.stage_coordinator.record_candidate(ANALOG_RYTM_DEVICE_ID, ready=None)
    session.stage_coordinator.record_candidate(
        ANALOG_FOUR_DEVICE_ID,
        ready=None,
        blocked_reason=A4_HARDWARE_BLOCK_REASON,
    )
    events = _source_events(session)
    events.append(build_show_bank_changed(session))
    return HandlerResult(
        ack={
            "ok": True,
            "source_snapshot_id": source.snapshot_id,
            "hardware_changed": False,
            "source_slots": source_slots,
            "instruction": (
                "Cockpit reset its in-memory audition only; no instrument changed. "
                "Manually load the immutable Rytm and Analog Four source slots to "
                "return hardware."
            ),
        },
        events=events,
    )


async def _handle_update_entry(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.update_entry(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
        name=_show_bank_text(cmd, "name"),
        description=_show_bank_text(cmd, "description", allow_empty=True),
        oxi=_oxi(cmd),
        audition_notes=_string_list(cmd, "audition_notes"),
        energy_level=_optional_integer(cmd, "energy_level"),
        energy_notes=_string_list(cmd, "energy_notes"),
        transition_notes=_string_list(cmd, "transition_notes"),
        recovery_notes=_string_list(cmd, "recovery_notes"),
    )
    return _ok(session, show_bank_entry_id=entry.entry_id)


async def _handle_reorder(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank = workspace.reorder(
        _show_bank_text(cmd, "bank_id"),
        _integer(cmd, "expected_revision"),
        _string_list(cmd, "entry_ids"),
    )
    return _ok(session, show_bank_id=bank.bank_id)


async def _handle_duplicate(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.duplicate(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
    )
    return _ok(session, show_bank_entry_id=entry.entry_id)


async def _handle_remove(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    bank_id = _show_bank_text(cmd, "bank_id")
    entry_id = _show_bank_text(cmd, "entry_id")
    removed = workspace.bank(bank_id).entry(entry_id)
    bank = workspace.remove(
        bank_id,
        entry_id,
        _integer(cmd, "expected_revision"),
    )
    current = session.current_candidate
    events: list[dict[str, object]] = []
    if current is not None and (
        current.source_snapshot_id == removed.rytm_source.snapshot_id
        or any(candidate.candidate_id == current.candidate_id for candidate in removed.candidates)
    ):
        session.current_candidate = None
        session.current_send_plan = None
        session.preview_on = False
        session.stage_coordinator.record_candidate(ANALOG_RYTM_DEVICE_ID, ready=None)
        session.stage_coordinator.record_candidate(
            ANALOG_FOUR_DEVICE_ID, ready=None, blocked_reason=A4_HARDWARE_BLOCK_REASON
        )
        events.extend(_source_events(session))
    events.append(build_show_bank_changed(session))
    return HandlerResult(ack={"ok": True, "show_bank_id": bank.bank_id}, events=events)


async def _handle_retain(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    entry = workspace.retain_capture(
        _show_bank_text(cmd, "bank_id"),
        _show_bank_text(cmd, "entry_id"),
        _integer(cmd, "expected_revision"),
        capture_kind=_capture_kind(cmd),
        device_id=_device(cmd),
        current_captures=session.kit_captures,
    )
    return _ok(session, show_bank_entry_id=entry.entry_id)


async def _handle_export(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    pack_service = session.show_pack_service
    if pack_service is None:
        raise ValueError("show-pack export is not configured")
    bank = workspace.checked_bank(
        _show_bank_text(cmd, "bank_id"),
        _integer(cmd, "expected_revision"),
    )
    result = pack_service.export(
        bank,
        package_id=_show_bank_text(cmd, "artifact_name"),
    )
    export_ack: ShowPackExportAck = {
        "package_id": result.package_id,
        "directory_name": result.package_dir.name,
        "artifact_count": len(result.manifest.artifacts) + 2,
    }
    return HandlerResult(
        ack={
            "ok": True,
            "show_pack_export": export_ack,
        }
    )


async def _handle_import(cmd: dict[str, object], session: CockpitSession) -> HandlerResult:
    workspace = _workspace(session)
    pack_service = session.show_pack_service
    if pack_service is None:
        raise ValueError("show-pack import is not configured")
    package_id = _show_bank_text(cmd, "pack_name")
    verified = pack_service.verify(package_id)
    # Check the in-memory collision before writing. The store independently
    # refuses every existing revision, so a concurrent collision also fails
    # closed at publication.
    if any(bank.bank_id == verified.bank.bank_id for bank in workspace.banks):
        raise ValueError("a show bank with that id already exists")
    stored = pack_service.store_verified_import(verified)
    imported = workspace.register_imported(stored.bank)
    import_ack: ShowPackImportAck = {
        "package_id": package_id,
        "bank_id": imported.bank_id,
        "artifact_count": len(verified.frames_by_artifact_id),
        "write_count": len(stored.writes),
    }
    return _ok(
        session,
        show_pack_import=import_ack,
    )


ShowBankHandler = Callable[[dict[str, object], CockpitSession], Awaitable[HandlerResult]]

SHOW_BANK_HANDLERS: Final[Mapping[str, ShowBankHandler]] = MappingProxyType(
    {
        COMMAND_SHOW_BANK_LIST: _handle_list,
        COMMAND_SHOW_BANK_CREATE: _handle_create,
        COMMAND_SHOW_BANK_SELECT: _handle_select,
        COMMAND_SHOW_BANK_UPDATE: _handle_update,
        COMMAND_SHOW_BANK_ADOPT_SOURCES: _handle_adopt_sources,
        COMMAND_SHOW_BANK_GENERATE_CANDIDATES: _handle_generate,
        COMMAND_SHOW_BANK_SELECT_CANDIDATE: _handle_select_candidate,
        COMMAND_SHOW_BANK_MARK_FAVORITE: _handle_mark_favorite,
        COMMAND_SHOW_BANK_ATTEST_HARDWARE_SAVED: _handle_attest_saved,
        COMMAND_SHOW_BANK_VERIFY_RECAPTURE: _handle_verify_recapture,
        COMMAND_SHOW_BANK_RUN_PREFLIGHT: _handle_run_preflight,
        COMMAND_SHOW_BANK_RETURN_SOURCE: _handle_return_source,
        COMMAND_SHOW_BANK_UPDATE_ENTRY: _handle_update_entry,
        COMMAND_SHOW_BANK_REORDER_ENTRIES: _handle_reorder,
        COMMAND_SHOW_BANK_DUPLICATE_ENTRY: _handle_duplicate,
        COMMAND_SHOW_BANK_REMOVE_ENTRY: _handle_remove,
        COMMAND_SHOW_BANK_RETAIN_CAPTURE: _handle_retain,
        COMMAND_SHOW_BANK_IMPORT: _handle_import,
        COMMAND_SHOW_BANK_EXPORT: _handle_export,
    }
)

__all__ = ["SHOW_BANK_HANDLERS", "ShowBankHandler", "build_show_bank_changed"]
