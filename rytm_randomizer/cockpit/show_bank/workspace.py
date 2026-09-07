"""Stateful orchestration for the local Show Kit Forge workspace.

The workspace composes the immutable show-bank records, pure transitions,
captured-kit codecs, and revision store.  It has no MIDI provider and no
sender.  The only live-audition transition is called by the existing guarded
Rytm ``ArmedApply`` handler *after* a successful send.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from typing import Final, Literal, cast

from ...observability.logging import get_logger
from ...observability.tracing import trace
from ..capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureDeviceId,
    KitCaptureResult,
    cockpit_snapshot_from_rytm_capture,
    decode_kit_capture_frame,
)
from ..data import MutationCandidate, ProfileModel, Snapshot, new_ulid
from ..data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    SHOW_KIT_DEPTH_PRESETS,
    HardwareSaveAttestation,
    OxiShowMetadata,
    ShowBank,
    ShowBankEntry,
    ShowBankEntryProjectionDict,
    ShowBankProjectionDict,
    ShowBankReadinessProjectionDict,
    ShowBankWorkspaceStateDict,
    ShowKitCandidate,
    ShowKitCapture,
    ShowKitDepthPreset,
    ShowKitDepthPresetsDict,
    ShowKitDeviceId,
    ShowKitLifecycleStatus,
    ShowKitReadinessProjectionDict,
    ShowKitRecipe,
    ShowKitRytmAuditionStatus,
    ShowKitScope,
)
from .forge import (
    analog_four_capture_semantic_fingerprint,
    build_source_entry,
)
from .forge import capture_reference as build_capture_reference
from .forge import (
    forge_candidate_pair,
    rytm_capture_semantic_fingerprint,
)
from .readiness import (
    Clock,
    add_candidate,
    add_entry,
    attest_hardware_save,
    create_show_bank,
    duplicate_entry,
    is_catalog_only_show_bank,
    mark_favorite,
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
from .store import ShowBankStore

SHOW_BANK_WORKSPACE_SCHEMA_VERSION: Final[Literal["show-bank-workspace-v1"]] = (
    "show-bank-workspace-v1"
)
MAX_CANDIDATES_PER_REQUEST: Final[int] = 8
MAX_VOLATILE_FRAMES: Final[int] = 128
MAX_VOLATILE_FRAME_BYTES: Final[int] = 64 * 1024 * 1024
CaptureKind = Literal["source", "favorite", "candidate"]
IdFactory = Callable[[str], str]
_logger = get_logger(__name__)


def _new_id(prefix: str) -> str:
    return f"{prefix}-{new_ulid().lower()}"


def _device_capture(
    captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
    device_id: KitCaptureDeviceId,
) -> KitCaptureResult:
    result = captures.get(device_id)
    if result is None:
        raise ValueError(f"a current {device_id} KIT capture is required")
    if not result.round_trip_verified or result.sent_midi or not result.input_only:
        raise ValueError("show-bank capture must be verified and input-only")
    return result


def _require_fresh_capture(
    result: KitCaptureResult,
    *,
    after: datetime,
    purpose: str,
) -> None:
    if result.captured_at <= after:
        raise ValueError(
            f"{purpose} requires a new current-KIT dump captured after " f"{after.isoformat()}"
        )


def _is_catalog_only(bank: ShowBank) -> bool:
    return is_catalog_only_show_bank(bank)


def _entry_recovery_actions(
    entry: ShowBankEntry,
    *,
    current_show_ready: bool,
) -> list[str]:
    actions = [
        (f"Recovery: manually load Rytm source slot " f"{entry.rytm_source.hardware_slot}."),
        (
            f"Recovery: manually load Analog Four source slot "
            f"{entry.analog_four_source.hardware_slot}."
        ),
    ]
    if entry.favorite is not None and (
        entry.rytm_hardware_save is None
        or entry.analog_four_hardware_save is None
        or entry.rytm_recapture is None
        or entry.analog_four_recapture is None
    ):
        actions.insert(0, "Save on instrument, then recapture")
    if entry.status == "verified" or (entry.status == "show-ready" and not current_show_ready):
        actions.insert(
            0,
            "Load both favorite slots, manually dump each current KIT, then run preflight.",
        )
    return actions


def _favorite_blocked_reasons(entry: ShowBankEntry) -> list[str]:
    reasons: list[str] = []
    if entry.favorite is not None:
        if entry.rytm_hardware_save is None:
            reasons.append("Rytm favorite has no manual hardware-save attestation.")
        if entry.analog_four_hardware_save is None:
            reasons.append("Analog Four favorite has no manual hardware-save attestation.")
        for label, recapture in (
            ("Rytm", entry.rytm_recapture),
            ("Analog Four", entry.analog_four_recapture),
        ):
            if recapture is None:
                reasons.append(f"{label} favorite has not been recaptured.")
            elif not recapture.matches_candidate:
                reasons.append(f"{label} recapture does not match the candidate semantics.")
    return reasons


def _entry_blocked_reasons(
    entry: ShowBankEntry,
    *,
    current_show_ready: bool,
) -> list[str]:
    reasons: list[str] = []
    if not entry.candidates:
        reasons.append("No paired candidate has been generated from the immutable sources.")
    elif entry.favorite is None:
        reasons.append("No candidate has been marked as a favorite.")
    reasons.extend(_favorite_blocked_reasons(entry))
    if entry.status == "verified":
        reasons.append("A fresh exact-fingerprint show-time preflight is required.")
    elif entry.status == "show-ready" and not current_show_ready:
        reasons.append(
            "The saved preflight is historical; fresh paired current-KIT dumps are "
            "required in this Cockpit session."
        )
    if entry.show_time_preflight is not None and not entry.show_time_preflight.ready:
        if not entry.show_time_preflight.rytm_matches:
            reasons.append("Current Rytm KIT differs from the verified favorite capture.")
        if not entry.show_time_preflight.a4_matches:
            reasons.append("Current Analog Four KIT differs from the verified favorite capture.")
    return reasons


def _project_entry(
    entry: ShowBankEntry,
    *,
    current_live_candidate_id: str | None,
    current_show_ready: bool,
) -> ShowBankEntryProjectionDict:
    if (
        current_live_candidate_id is not None
        and current_live_candidate_id == entry.rytm_live_auditioned_candidate_id
    ):
        audition_status: ShowKitRytmAuditionStatus = "live_unsaved_hardware"
    elif entry.rytm_live_auditioned_candidate_id is not None:
        audition_status = "historical_audition_hardware_unknown"
    else:
        audition_status = "not_auditioned"
    projected_status: ShowKitLifecycleStatus = (
        "verified" if entry.status == "show-ready" and not current_show_ready else entry.status
    )
    blocked = _entry_blocked_reasons(
        entry,
        current_show_ready=current_show_ready,
    )
    oxi = entry.oxi
    readiness: ShowKitReadinessProjectionDict = {
        "status": projected_status,
        "show_ready": current_show_ready,
        "blocked_reasons": blocked,
        "recovery_actions": _entry_recovery_actions(
            entry,
            current_show_ready=current_show_ready,
        ),
    }
    return {
        "entry_id": entry.entry_id,
        "cue_index": entry.cue_index,
        "name": entry.name,
        "description": entry.description,
        "rytm_source": entry.rytm_source.to_dict(),
        "analog_four_source": entry.analog_four_source.to_dict(),
        "candidates": [candidate.to_dict() for candidate in entry.candidates],
        "selected_candidate_id": entry.selected_candidate_id,
        "rytm_live_auditioned_candidate_id": entry.rytm_live_auditioned_candidate_id,
        "rytm_live_auditioned_at": (
            None
            if entry.rytm_live_auditioned_at is None
            else entry.rytm_live_auditioned_at.isoformat()
        ),
        "favorite": None if entry.favorite is None else entry.favorite.to_dict(),
        "rytm_hardware_save": (
            None if entry.rytm_hardware_save is None else entry.rytm_hardware_save.to_dict()
        ),
        "analog_four_hardware_save": (
            None
            if entry.analog_four_hardware_save is None
            else entry.analog_four_hardware_save.to_dict()
        ),
        "rytm_recapture": (
            None if entry.rytm_recapture is None else entry.rytm_recapture.to_dict()
        ),
        "analog_four_recapture": (
            None if entry.analog_four_recapture is None else entry.analog_four_recapture.to_dict()
        ),
        "show_time_preflight": (
            None if entry.show_time_preflight is None else entry.show_time_preflight.to_dict()
        ),
        "show_ready_at": (None if entry.show_ready_at is None else entry.show_ready_at.isoformat()),
        "oxi": {
            "project": oxi.project,
            "pattern": oxi.pattern,
            "chapter": oxi.chapter,
            "direct_oxi_control": False,
        },
        "audition_notes": list(entry.audition_notes),
        "energy_level": entry.energy_level,
        "energy_notes": list(entry.energy_notes),
        "transition_notes": list(entry.transition_notes),
        "recovery_notes": list(entry.recovery_notes),
        "created_at": entry.created_at.isoformat(),
        "updated_at": entry.updated_at.isoformat(),
        "status": projected_status,
        "rytm_audition_status": audition_status,
        "readiness": readiness,
    }


class ShowKitForgeWorkspace:
    """Loaded local banks plus the bounded volatile candidate-byte cache."""

    def __init__(
        self,
        store: ShowBankStore,
        *,
        clock: Clock = utc_now,
        id_factory: IdFactory = _new_id,
    ) -> None:
        self._store = store
        self._clock = clock
        self._id_factory = id_factory
        loaded = store.list_banks()
        self._banks: dict[str, ShowBank] = {bank.bank_id: bank for bank in loaded}
        self._active_bank_id: str | None = loaded[0].bank_id if loaded else None
        self._active_entry_ids: dict[str, str] = {
            bank.bank_id: bank.entries[0].entry_id for bank in loaded if bank.entries
        }
        self._workspace_revision = 0
        self._volatile_frames: dict[str, bytes] = {}
        self._source_snapshots: dict[tuple[str, str], Snapshot] = {}
        # Persisted audition/preflight records are useful history, but neither
        # proves what is currently loaded after Cockpit restarts.  These
        # process-local grants are populated only by successful work in this
        # session and deliberately start empty for loaded/imported banks.
        self._current_rytm_auditions: dict[tuple[str, str], str] = {}
        self._current_preflight_grants: dict[tuple[str, str], datetime] = {}
        self._rytm_source_capture_cutoff: datetime | None = None

    @property
    def store(self) -> ShowBankStore:
        return self._store

    @property
    def active_bank_id(self) -> str | None:
        return self._active_bank_id

    @property
    def banks(self) -> tuple[ShowBank, ...]:
        return tuple(self._banks[key] for key in sorted(self._banks))

    def bank(self, bank_id: str) -> ShowBank:
        try:
            return self._banks[bank_id]
        except KeyError as exc:
            raise ValueError("unknown show bank") from exc

    def checked_bank(self, bank_id: str, expected_revision: int) -> ShowBank:
        """Return a bank only when the client still holds its exact revision."""

        return self._checked_bank(bank_id, expected_revision)

    def register_imported(self, bank: ShowBank) -> ShowBank:
        """Hydrate a package bank after ``ShowPackService`` stored it atomically."""

        if bank.bank_id in self._banks:
            raise ValueError("a show bank with that id is already loaded")
        stored = self._store.load(bank.bank_id, revision=bank.revision)
        if stored != bank:
            raise ValueError("imported show bank differs from the stored revision")
        self._banks[bank.bank_id] = bank
        self._active_bank_id = bank.bank_id
        if bank.entries:
            self._active_entry_ids[bank.bank_id] = bank.entries[0].entry_id
        self._workspace_revision += 1
        return bank

    @staticmethod
    def _require_editable_candidate_authority(bank: ShowBank) -> None:
        if _is_catalog_only(bank):
            _logger.warning(
                "show_bank_candidate_authority_rejected",
                extra={"bank_id": bank.bank_id, "reason": "catalog_only"},
            )
            raise ValueError(
                "imported show packs are catalog-only; capture fresh source KITs "
                "before generating or auditioning candidates"
            )

    def _checked_bank(self, bank_id: str, expected_revision: int) -> ShowBank:
        bank = self.bank(bank_id)
        if isinstance(expected_revision, bool) or expected_revision != bank.revision:
            _logger.warning(
                "show_bank_revision_rejected",
                extra={"bank_id": bank.bank_id, "actual_revision": bank.revision},
            )
            raise ValueError("show bank changed; refresh before retrying")
        return bank

    def _publish(self, bank: ShowBank, *, already_saved: bool = False) -> ShowBank:
        if not already_saved:
            self._store.save(bank)
        self._banks[bank.bank_id] = bank
        self._active_bank_id = bank.bank_id
        self._workspace_revision += 1
        _logger.info(
            "show_bank_published",
            extra={
                "bank_id": bank.bank_id,
                "revision": bank.revision,
                "entry_count": len(bank.entries),
                "outcome": "published",
            },
        )
        return bank

    def state_dict(self) -> ShowBankWorkspaceStateDict:
        banks: list[ShowBankProjectionDict] = []
        for bank in self.banks:
            projected_entries: list[ShowBankEntryProjectionDict] = []
            ready_entry_ids: list[str] = []
            for entry in bank.entries:
                key = (bank.bank_id, entry.entry_id)
                current_ready = (
                    entry.show_ready_at is not None
                    and self._current_preflight_grants.get(key) == entry.show_ready_at
                )
                if current_ready:
                    ready_entry_ids.append(entry.entry_id)
                projected_entries.append(
                    _project_entry(
                        entry,
                        current_live_candidate_id=self._current_rytm_auditions.get(key),
                        current_show_ready=current_ready,
                    )
                )
            readiness = show_bank_readiness(bank)
            currently_ready = bool(bank.entries) and len(ready_entry_ids) == len(bank.entries)
            projected_status: ShowKitLifecycleStatus = bank.status
            if bank.status == "show-ready" and not currently_ready:
                projected_status = "verified"
            blocked_reasons = (
                []
                if currently_ready
                else (
                    [
                        "Fresh paired current-KIT preflight is required for every cue "
                        "in this Cockpit session."
                    ]
                    if readiness.ready
                    else list(readiness.blocked_reasons)
                )
            )
            readiness_projection: ShowBankReadinessProjectionDict = {
                "status": projected_status,
                "show_ready": currently_ready,
                "show_ready_entry_ids": ready_entry_ids,
                "blocked_reasons": blocked_reasons,
                "recovery_actions": [
                    "Resolve every cue in order, then run fresh paired current-KIT preflights."
                ],
            }
            payload: ShowBankProjectionDict = {
                "schema_version": bank.schema_version,
                "bank_id": bank.bank_id,
                "name": bank.name,
                "description": bank.description,
                "revision": bank.revision,
                "entries": projected_entries,
                "notes": list(bank.notes),
                "evidence": [item.to_dict() for item in bank.evidence],
                "created_at": bank.created_at.isoformat(),
                "updated_at": bank.updated_at.isoformat(),
                "status": projected_status,
                "active_entry_id": self._active_entry_ids.get(bank.bank_id),
                "readiness": readiness_projection,
            }
            banks.append(payload)
        depth_presets: ShowKitDepthPresetsDict = {
            "small": SHOW_KIT_DEPTH_PRESETS["small"],
            "medium": SHOW_KIT_DEPTH_PRESETS["medium"],
            "large": SHOW_KIT_DEPTH_PRESETS["large"],
        }
        return {
            "schema_version": SHOW_BANK_WORKSPACE_SCHEMA_VERSION,
            "revision": self._workspace_revision,
            "active_bank_id": self._active_bank_id,
            "banks": banks,
            "depth_presets": depth_presets,
        }

    def select_bank(self, bank_id: str) -> ShowBank:
        bank = self.bank(bank_id)
        self._active_bank_id = bank_id
        self._workspace_revision += 1
        return bank

    def revoke_hardware_evidence(self) -> bool:
        """Revoke current hardware claims after output or connection loss.

        Durable audition/preflight evidence remains historical. A subsequent
        Show Kit audition requires a new source capture and the operator's
        explicit manual source-reload attestation.
        """

        changed = bool(self._current_rytm_auditions or self._current_preflight_grants)
        self._current_rytm_auditions.clear()
        self._current_preflight_grants.clear()
        self._rytm_source_capture_cutoff = self._clock()
        if changed:
            self._workspace_revision += 1
            _logger.info(
                "show_bank_hardware_evidence_revoked",
                extra={"outcome": "revoked", "source_reload_required": True},
            )
        return changed

    def observe_capture(self, result: KitCaptureResult) -> bool:
        """Revoke current labels contradicted by a newly observed KIT.

        Preflights of other cues remain an ordered rehearsal record. Only
        the active cue claims to describe the KIT currently being inspected.
        """

        changed = False
        if result.device_id == ANALOG_RYTM_DEVICE_ID and self._current_rytm_auditions:
            self._current_rytm_auditions.clear()
            changed = True
        if self._active_bank_id is not None:
            entry_id = self._active_entry_ids.get(self._active_bank_id)
            if entry_id is not None:
                key = (self._active_bank_id, entry_id)
                entry = self.bank(self._active_bank_id).entry(entry_id)
                recapture = (
                    entry.rytm_recapture
                    if result.device_id == ANALOG_RYTM_DEVICE_ID
                    else entry.analog_four_recapture
                )
                if (
                    key in self._current_preflight_grants
                    and recapture is not None
                    and result.fingerprint != recapture.capture.fingerprint
                ):
                    self._current_preflight_grants.pop(key)
                    changed = True
        if changed:
            self._workspace_revision += 1
            _logger.info(
                "show_bank_capture_revoked_current_evidence",
                extra={"device_id": result.device_id, "outcome": "revoked"},
            )
        return changed

    def require_rytm_audition_source(
        self,
        candidate_id: str,
        captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
        *,
        manually_reloaded: bool,
        source_snapshot_id: str | None = None,
    ) -> None:
        """Require an exact source and explicit reload for a live Show SEND.

        A saved-KIT dump alone does not prove live RAM was restored. The
        operator attests the manual reload; the fresh matching input capture
        binds that statement to this cue's immutable source. No restore is
        sent here, including to pads excluded by a later candidate's scope.
        """

        matches = [
            (bank, entry)
            for bank in self.banks
            for entry in bank.entries
            if (
                source_snapshot_id is not None
                and entry.rytm_source.snapshot_id == source_snapshot_id
            )
            or any(candidate.candidate_id == candidate_id for candidate in entry.candidates)
        ]
        if not matches:
            return
        active = [
            (bank, entry)
            for bank, entry in matches
            if bank.bank_id == self._active_bank_id
            and entry.entry_id == self._active_entry_ids.get(bank.bank_id)
            and entry.selected_candidate_id == candidate_id
        ]
        if not active:
            raise ValueError("select this Show Kit candidate again before a live SEND")
        bank, entry = active[0]
        self._require_editable_candidate_authority(bank)
        if manually_reloaded is not True:
            raise ValueError(
                "Show Kit SEND requires confirmation: manually reload the Rytm source slot, "
                "capture its current KIT, then reselect the candidate"
            )
        result = _device_capture(captures, ANALOG_RYTM_DEVICE_ID)
        if result.fingerprint != entry.rytm_source.fingerprint:
            raise ValueError("Rytm current capture differs from the immutable Show Kit source")
        if self._rytm_source_capture_cutoff is not None:
            _require_fresh_capture(
                result,
                after=self._rytm_source_capture_cutoff,
                purpose="Rytm source reload after output or connection loss",
            )

    def _cache_frame(self, artifact_id: str, frame: bytes) -> None:
        """Keep a bounded volatile regeneration cache; retained files are authoritative."""

        if artifact_id in self._volatile_frames:
            self._volatile_frames.pop(artifact_id)
        self._volatile_frames[artifact_id] = frame
        while (
            len(self._volatile_frames) > MAX_VOLATILE_FRAMES
            or sum(len(item) for item in self._volatile_frames.values()) > MAX_VOLATILE_FRAME_BYTES
        ):
            oldest = next(iter(self._volatile_frames))
            self._volatile_frames.pop(oldest)

    def create_bank(
        self,
        *,
        name: str,
        description: str,
        notes: Sequence[str],
    ) -> ShowBank:
        bank = create_show_bank(
            bank_id=self._id_factory("bank"),
            name=name,
            description=description,
            notes=notes,
            clock=self._clock,
        )
        return self._publish(bank)

    def update_bank(
        self,
        bank_id: str,
        expected_revision: int,
        *,
        name: str,
        description: str,
        notes: Sequence[str],
    ) -> ShowBank:
        bank = self._checked_bank(bank_id, expected_revision)
        return self._publish(
            update_bank_metadata(
                bank,
                name=name,
                description=description,
                notes=notes,
                clock=self._clock,
            )
        )

    # Explicit action fields mirror the existing WS command contract.
    def adopt_sources(  # noqa: PLR0913
        self,
        bank_id: str,
        expected_revision: int,
        *,
        captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
        rytm_fingerprint: str,
        analog_four_fingerprint: str,
        rytm_slot: int,
        analog_four_slot: int,
        entry_id: str | None = None,
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        rytm = _device_capture(captures, ANALOG_RYTM_DEVICE_ID)
        analog_four = _device_capture(captures, ANALOG_FOUR_DEVICE_ID)
        if (
            rytm.fingerprint != rytm_fingerprint
            or analog_four.fingerprint != analog_four_fingerprint
        ):
            raise ValueError("capture fingerprint changed; review the latest captures")
        snapshot = cockpit_snapshot_from_rytm_capture(rytm)
        resolved_entry_id = entry_id or self._id_factory("cue")
        if any(item.entry_id == resolved_entry_id for item in bank.entries):
            raise ValueError("source anchors are immutable; create a new cue instead")
        entry = build_source_entry(
            entry_id=resolved_entry_id,
            cue_index=len(bank.entries) + 1,
            name=f"{rytm.kit_name} + {analog_four.kit_name}",
            description="Paired immutable source anchors",
            rytm_capture=rytm,
            analog_four_capture=analog_four,
            rytm_slot=rytm_slot,
            analog_four_slot=analog_four_slot,
            rytm_snapshot_id=snapshot.snapshot_id,
            now=self._clock(),
        )
        entry = replace(
            entry,
            rytm_source=self._share_declared_sysex(bank, entry.rytm_source),
            analog_four_source=self._share_declared_sysex(bank, entry.analog_four_source),
        )
        updated = add_entry(bank, entry, clock=self._clock)
        updated = self._retain_frames(
            updated,
            (
                (entry.rytm_source.sysex.artifact_id, rytm.frame),
                (entry.analog_four_source.sysex.artifact_id, analog_four.frame),
            ),
        )
        self._source_snapshots[(bank_id, resolved_entry_id)] = snapshot
        self._active_entry_ids[bank_id] = resolved_entry_id
        self._publish(updated, already_saved=True)
        return updated.entry(resolved_entry_id)

    def _retained_frame(self, bank: ShowBank, artifact_id: str) -> bytes:
        volatile = self._volatile_frames.get(artifact_id)
        if volatile is not None:
            return volatile
        artifact = bank.sysex_artifact(artifact_id)
        if artifact.retained is None:
            raise ValueError("exact SysEx bytes are not retained; regenerate or recapture")
        return self._store.read_retained(artifact.retained)

    def _source_snapshot(self, bank: ShowBank, entry: ShowBankEntry) -> Snapshot:
        key = (bank.bank_id, entry.entry_id)
        cached = self._source_snapshots.get(key)
        if cached is not None:
            return cached
        frame = self._retained_frame(bank, entry.rytm_source.sysex.artifact_id)
        decoded = decode_kit_capture_frame(ANALOG_RYTM_DEVICE_ID, frame)
        if decoded.fingerprint != entry.rytm_source.fingerprint:
            raise ValueError("retained Rytm source fingerprint does not match the cue")
        snapshot = cockpit_snapshot_from_rytm_capture(decoded)
        source_id = entry.rytm_source.snapshot_id
        if source_id is None:
            raise ValueError("Rytm source is missing its mutation snapshot identity")
        snapshot = replace(
            snapshot,
            snapshot_id=source_id,
            captured_at=entry.rytm_source.captured_at,
        )
        self._source_snapshots[key] = snapshot
        return snapshot

    @trace("show_kit_forge.generate_candidates")
    # Explicit action fields mirror the existing WS command contract.
    def generate_candidates(  # noqa: PLR0913
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        profile: ProfileModel,
        depth_preset: ShowKitDepthPreset,
        depth: float,
        seed: int,
        candidate_count: int,
        rytm_targets: Sequence[int],
        rytm_locks: Sequence[int],
        analog_four_targets: Sequence[int],
        analog_four_locks: Sequence[int],
    ) -> tuple[ShowKitCandidate, ...]:
        if (
            isinstance(candidate_count, bool)
            or not 1 <= candidate_count <= MAX_CANDIDATES_PER_REQUEST
        ):
            raise ValueError(f"candidate_count must be in 1..{MAX_CANDIDATES_PER_REQUEST}")
        bank = self._checked_bank(bank_id, expected_revision)
        self._require_editable_candidate_authority(bank)
        entry = bank.entry(entry_id)
        source_snapshot = self._source_snapshot(bank, entry)
        analog_four_frame = self._retained_frame(bank, entry.analog_four_source.sysex.artifact_id)
        updated = bank
        created: list[ShowKitCandidate] = []
        existing_ids = {candidate.candidate_id for candidate in entry.candidates}
        for index in range(candidate_count):
            recipe = ShowKitRecipe(
                profile_id=profile.profile_id,
                depth_preset=depth_preset,
                depth=depth,
                seed=(seed + index) & 0xFFFFFFFF,
                rytm_scope=ShowKitScope(
                    device_id=RYTM_SHOW_KIT_DEVICE_ID,
                    target_ids=tuple(rytm_targets),
                    locked_ids=tuple(rytm_locks),
                ),
                analog_four_scope=ShowKitScope(
                    device_id=A4_SHOW_KIT_DEVICE_ID,
                    target_ids=tuple(analog_four_targets),
                    locked_ids=tuple(analog_four_locks),
                ),
            )
            forged = forge_candidate_pair(
                entry=entry,
                rytm_source_snapshot=source_snapshot,
                analog_four_source_frame=analog_four_frame,
                profile=profile,
                recipe=recipe,
                now=self._clock(),
            )
            self._cache_frame(
                forged.candidate.analog_four_candidate.sysex.artifact_id,
                forged.analog_four_frame,
            )
            if forged.candidate.candidate_id in existing_ids:
                continue
            updated = add_candidate(
                updated,
                entry_id,
                forged.candidate,
                select=not created and entry.selected_candidate_id is None,
                clock=self._clock,
            )
            existing_ids.add(forged.candidate.candidate_id)
            created.append(forged.candidate)
        if not created:
            raise ValueError("that deterministic candidate set already exists")
        self._active_entry_ids[bank_id] = entry_id
        self._current_rytm_auditions.pop((bank_id, entry_id), None)
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        self._publish(updated)
        _logger.info(
            "show_kit_candidates_generated",
            extra={
                "bank_id": bank_id,
                "entry_id": entry_id,
                "seed": seed,
                "depth": depth,
                "profile_id": profile.profile_id,
                "requested_count": candidate_count,
                "created_count": len(created),
                "outcome": "published",
            },
        )
        return tuple(created)

    def select_candidate(
        self,
        bank_id: str,
        entry_id: str,
        candidate_id: str,
        expected_revision: int,
    ) -> tuple[ShowBankEntry, Snapshot, MutationCandidate]:
        bank = self._checked_bank(bank_id, expected_revision)
        self._require_editable_candidate_authority(bank)
        updated = select_candidate(bank, entry_id, candidate_id, clock=self._clock)
        selected = updated.entry(entry_id)
        candidate = selected.selected_candidate
        if candidate is None:
            raise AssertionError("candidate selection transition lost its selection")
        source = self._source_snapshot(updated, selected)
        self._active_entry_ids[bank_id] = entry_id
        self._current_rytm_auditions.pop((bank_id, entry_id), None)
        self._publish(updated)
        return selected, source, candidate.rytm_candidate

    def audition_context(
        self, bank_id: str, entry_id: str
    ) -> tuple[ShowBankEntry, Snapshot, ShowKitCandidate]:
        """Return the selected inert pair and immutable Rytm source."""

        bank = self.bank(bank_id)
        self._require_editable_candidate_authority(bank)
        entry = bank.entry(entry_id)
        selected = entry.selected_candidate
        if selected is None:
            raise ValueError("select a candidate before preparing an audition")
        return entry, self._source_snapshot(bank, entry), selected

    def source_snapshot(self, bank_id: str, entry_id: str) -> Snapshot:
        """Return a cue's immutable Rytm source projection."""

        bank = self.bank(bank_id)
        return self._source_snapshot(bank, bank.entry(entry_id))

    def mark_favorite(
        self,
        bank_id: str,
        entry_id: str,
        candidate_id: str,
        expected_revision: int,
        *,
        replace_existing: bool = False,
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        self._require_editable_candidate_authority(bank)
        entry = bank.entry(entry_id)
        updated = bank
        if entry.selected_candidate_id != candidate_id:
            updated = select_candidate(updated, entry_id, candidate_id, clock=self._clock)
        updated = mark_favorite(
            updated,
            entry_id,
            replace_existing=replace_existing,
            clock=self._clock,
        )
        favorite = updated.entry(entry_id).favorite_candidate
        if favorite is None:
            raise AssertionError("favorite transition lost its selected candidate")
        artifact = favorite.analog_four_candidate.sysex
        frame = self._retained_frame(updated, artifact.artifact_id)
        updated = self._retain_frames(updated, ((artifact.artifact_id, frame),))
        self._active_entry_ids[bank_id] = entry_id
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        self._publish(updated, already_saved=True)
        return updated.entry(entry_id)

    def attest_saved(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        device_id: ShowKitDeviceId,
        hardware_slot: int,
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        self._require_editable_candidate_authority(bank)
        if any(
            source.device_id == device_id and source.hardware_slot == hardware_slot
            for loaded_bank in self.banks
            for entry in loaded_bank.entries
            for source in (entry.rytm_source, entry.analog_four_source)
        ):
            raise ValueError("favorite hardware slot must not overwrite an immutable source slot")
        updated = attest_hardware_save(
            bank,
            entry_id,
            device_id=device_id,
            hardware_slot=hardware_slot,
            note="Operator attested a manual instrument save; not byte-verified yet.",
            clock=self._clock,
        )
        self._active_entry_ids[bank_id] = entry_id
        if device_id == RYTM_SHOW_KIT_DEVICE_ID:
            self._current_rytm_auditions.pop((bank_id, entry_id), None)
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        self._publish(updated)
        return updated.entry(entry_id)

    @staticmethod
    def _share_declared_sysex(bank: ShowBank, capture: ShowKitCapture) -> ShowKitCapture:
        for declared in bank.sysex_artifacts():
            if declared.artifact_id != capture.sysex.artifact_id:
                continue
            if (
                declared.frame_sha256 != capture.sysex.frame_sha256
                or declared.frame_bytes != capture.sysex.frame_bytes
            ):
                raise ValueError("one artifact id refers to conflicting exact bytes")
            return replace(capture, sysex=declared)
        return capture

    def verify_recaptures(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        self._require_editable_candidate_authority(bank)
        entry = bank.entry(entry_id)
        favorite = entry.favorite_candidate
        if favorite is None:
            raise ValueError("recapture verification requires a favorite")
        if entry.rytm_hardware_save is None or entry.analog_four_hardware_save is None:
            raise ValueError("Save on instrument, then recapture")
        rytm = _device_capture(captures, ANALOG_RYTM_DEVICE_ID)
        analog_four = _device_capture(captures, ANALOG_FOUR_DEVICE_ID)
        _require_fresh_capture(
            rytm,
            after=entry.rytm_hardware_save.attested_at,
            purpose="Rytm favorite verification",
        )
        _require_fresh_capture(
            analog_four,
            after=entry.analog_four_hardware_save.attested_at,
            purpose="Analog Four favorite verification",
        )
        rytm_snapshot = cockpit_snapshot_from_rytm_capture(rytm)
        rytm_reference = self._share_declared_sysex(
            bank,
            build_capture_reference(
                rytm,
                hardware_slot=entry.rytm_hardware_save.hardware_slot,
                snapshot_id=rytm_snapshot.snapshot_id,
            ),
        )
        analog_four_reference = self._share_declared_sysex(
            bank,
            build_capture_reference(
                analog_four,
                hardware_slot=entry.analog_four_hardware_save.hardware_slot,
                snapshot_id=None,
            ),
        )
        source_rytm = decode_kit_capture_frame(
            ANALOG_RYTM_DEVICE_ID,
            self._retained_frame(bank, entry.rytm_source.sysex.artifact_id),
        )
        source_analog_four = decode_kit_capture_frame(
            ANALOG_FOUR_DEVICE_ID,
            self._retained_frame(bank, entry.analog_four_source.sysex.artifact_id),
        )
        source_a4_semantic = analog_four_capture_semantic_fingerprint(
            source_analog_four,
            favorite.analog_four_candidate,
        )
        if source_a4_semantic is None:
            raise AssertionError("verified A4 source lost its promoted semantic projection")
        updated = record_recapture(
            bank,
            entry_id,
            rytm_reference,
            source_semantic_fingerprint=rytm_capture_semantic_fingerprint(source_rytm),
            observed_semantic_fingerprint=rytm_capture_semantic_fingerprint(rytm),
            comparison_reason=(
                "Compared the promoted mapped Rytm state; unknown captured bytes were "
                "retained but were not treated as mapped parameters."
            ),
            clock=self._clock,
        )
        updated = record_recapture(
            updated,
            entry_id,
            analog_four_reference,
            source_semantic_fingerprint=source_a4_semantic,
            observed_semantic_fingerprint=analog_four_capture_semantic_fingerprint(
                analog_four, favorite.analog_four_candidate
            ),
            comparison_reason=(
                "Compared only verified Filter 1 Frequency offsets on selected A4 tracks; "
                "all unverified fields remained outside the semantic claim."
            ),
            clock=self._clock,
        )
        updated = self._retain_frames(
            updated,
            (
                (rytm_reference.sysex.artifact_id, rytm.frame),
                (analog_four_reference.sysex.artifact_id, analog_four.frame),
            ),
        )
        self._active_entry_ids[bank_id] = entry_id
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        self._publish(updated, already_saved=True)
        return updated.entry(entry_id)

    def run_preflight(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        entry = bank.entry(entry_id)
        # Re-read and hash every retained artifact immediately before granting
        # show-time readiness.  In-memory metadata alone is never sufficient.
        persisted = self._store.load(
            bank_id,
            revision=bank.revision,
            verify_retained=True,
        )
        if persisted != bank:
            raise ValueError("persisted show-bank evidence changed; reload before preflight")
        if entry.rytm_recapture is None or entry.analog_four_recapture is None:
            raise ValueError("show-time preflight requires verified paired recaptures")
        rytm = _device_capture(captures, ANALOG_RYTM_DEVICE_ID)
        analog_four = _device_capture(captures, ANALOG_FOUR_DEVICE_ID)
        _require_fresh_capture(
            rytm,
            after=entry.rytm_recapture.recorded_at,
            purpose="Rytm show-time preflight",
        )
        _require_fresh_capture(
            analog_four,
            after=entry.analog_four_recapture.recorded_at,
            purpose="Analog Four show-time preflight",
        )
        if entry.show_time_preflight is not None:
            _require_fresh_capture(
                rytm,
                after=entry.show_time_preflight.checked_at,
                purpose="Rytm repeated show-time preflight",
            )
            _require_fresh_capture(
                analog_four,
                after=entry.show_time_preflight.checked_at,
                purpose="Analog Four repeated show-time preflight",
            )
        # The immutable entry requires a same-device save attestation for
        # every recapture, so paired recaptures above prove both are present.
        rytm_slot = cast(HardwareSaveAttestation, entry.rytm_hardware_save).hardware_slot
        a4_slot = cast(HardwareSaveAttestation, entry.analog_four_hardware_save).hardware_slot
        updated = record_show_time_preflight(
            bank,
            entry_id,
            current_rytm_capture=build_capture_reference(
                rytm,
                hardware_slot=rytm_slot,
                snapshot_id=cockpit_snapshot_from_rytm_capture(rytm).snapshot_id,
            ),
            current_analog_four_capture=build_capture_reference(
                analog_four,
                hardware_slot=a4_slot,
                snapshot_id=None,
            ),
            reason=(
                "Fresh input-only current-KIT captures compared byte-fingerprint identities "
                "with the retained favorite recaptures."
            ),
            clock=self._clock,
        )
        self._active_entry_ids[bank_id] = entry_id
        self._publish(updated)
        self._current_rytm_auditions.clear()
        projected_entry = updated.entry(entry_id)
        key = (bank_id, entry_id)
        if projected_entry.show_ready_at is None:
            self._current_preflight_grants.pop(key, None)
        else:
            self._current_preflight_grants[key] = projected_entry.show_ready_at
        return projected_entry

    def record_live_rytm_audition(self, candidate_id: str) -> ShowBankEntry | None:
        if self._active_bank_id is None:
            self._current_rytm_auditions.clear()
            return None
        bank = self.bank(self._active_bank_id)
        if _is_catalog_only(bank):
            self._current_rytm_auditions.clear()
            return None
        active_entry_id = self._active_entry_ids.get(bank.bank_id)
        if active_entry_id is None:
            self._current_rytm_auditions.clear()
            return None
        entry = bank.entry(active_entry_id)
        if entry.selected_candidate_id != candidate_id:
            self._current_rytm_auditions.clear()
            return None
        updated = record_rytm_live_audition(bank, entry.entry_id, clock=self._clock)
        self._publish(updated)
        self._current_rytm_auditions.clear()
        self._current_rytm_auditions[(bank.bank_id, entry.entry_id)] = candidate_id
        self._current_preflight_grants.pop((bank.bank_id, entry.entry_id), None)
        return updated.entry(entry.entry_id)

    def return_entry_to_source(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
    ) -> Snapshot:
        bank = self._checked_bank(bank_id, expected_revision)
        source = self._source_snapshot(bank, bank.entry(entry_id))
        updated = return_to_source(bank, entry_id, clock=self._clock)
        self._active_entry_ids[bank_id] = entry_id
        self._current_rytm_auditions.pop((bank_id, entry_id), None)
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        self._publish(updated)
        return source

    # Explicit action fields mirror the existing WS command contract.
    def update_entry(  # noqa: PLR0913
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        name: str,
        description: str,
        oxi: OxiShowMetadata,
        audition_notes: Sequence[str],
        energy_level: int | None,
        energy_notes: Sequence[str],
        transition_notes: Sequence[str],
        recovery_notes: Sequence[str],
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        updated = update_entry_metadata(
            bank,
            entry_id,
            name=name,
            description=description,
            oxi=oxi,
            audition_notes=audition_notes,
            energy_level=energy_level,
            energy_notes=energy_notes,
            transition_notes=transition_notes,
            recovery_notes=recovery_notes,
            clock=self._clock,
        )
        self._active_entry_ids[bank_id] = entry_id
        self._publish(updated)
        return updated.entry(entry_id)

    def reorder(
        self,
        bank_id: str,
        expected_revision: int,
        entry_ids: Sequence[str],
    ) -> ShowBank:
        bank = self._checked_bank(bank_id, expected_revision)
        return self._publish(reorder_entries(bank, entry_ids, clock=self._clock))

    def duplicate(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        duplicated_id = self._id_factory("cue")
        updated = duplicate_entry(
            bank,
            entry_id,
            duplicated_id,
            name=f"{bank.entry(entry_id).name} copy",
            clock=self._clock,
        )
        self._active_entry_ids[bank_id] = duplicated_id
        self._publish(updated)
        return updated.entry(duplicated_id)

    def remove(
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
    ) -> ShowBank:
        bank = self._checked_bank(bank_id, expected_revision)
        removed = bank.entry(entry_id)
        updated = remove_entry(bank, entry_id, clock=self._clock)
        self._active_entry_ids.pop(bank_id, None)
        self._current_rytm_auditions.pop((bank_id, entry_id), None)
        self._current_preflight_grants.pop((bank_id, entry_id), None)
        for candidate in removed.candidates:
            self._volatile_frames.pop(
                candidate.analog_four_candidate.sysex.artifact_id,
                None,
            )
        self._source_snapshots.pop((bank_id, entry_id), None)
        if updated.entries:
            self._active_entry_ids[bank_id] = updated.entries[0].entry_id
        return self._publish(updated)

    # Explicit action fields mirror the existing WS command contract.
    def retain_capture(  # noqa: PLR0913
        self,
        bank_id: str,
        entry_id: str,
        expected_revision: int,
        *,
        capture_kind: CaptureKind,
        device_id: ShowKitDeviceId,
        current_captures: Mapping[KitCaptureDeviceId, KitCaptureResult],
    ) -> ShowBankEntry:
        bank = self._checked_bank(bank_id, expected_revision)
        entry = bank.entry(entry_id)
        if capture_kind == "source":
            capture = (
                entry.rytm_source
                if device_id == RYTM_SHOW_KIT_DEVICE_ID
                else entry.analog_four_source
            )
        elif capture_kind == "favorite":
            recapture = (
                entry.rytm_recapture
                if device_id == RYTM_SHOW_KIT_DEVICE_ID
                else entry.analog_four_recapture
            )
            if recapture is None:
                raise ValueError("favorite retention requires a verified recapture")
            capture = recapture.capture
        elif capture_kind == "candidate":
            return self._retain_selected_a4_candidate(bank, entry, device_id)
        else:
            raise ValueError("capture_kind must be source, favorite, or candidate")
        runtime_frame = self._volatile_frames.get(capture.sysex.artifact_id)
        if runtime_frame is None:
            service_id = (
                ANALOG_RYTM_DEVICE_ID
                if device_id == RYTM_SHOW_KIT_DEVICE_ID
                else ANALOG_FOUR_DEVICE_ID
            )
            current = current_captures.get(service_id)
            if current is not None and current.fingerprint == capture.fingerprint:
                runtime_frame = current.frame
        if runtime_frame is None and capture.sysex.retained is not None:
            runtime_frame = self._store.read_retained(capture.sysex.retained)
        if runtime_frame is None:
            raise ValueError("exact requested capture bytes are no longer in memory; recapture it")
        updated = self._retain_frames(bank, ((capture.sysex.artifact_id, runtime_frame),))
        self._publish(updated, already_saved=True)
        return updated.entry(entry_id)

    def _retain_selected_a4_candidate(
        self, bank: ShowBank, entry: ShowBankEntry, device_id: ShowKitDeviceId
    ) -> ShowBankEntry:
        if device_id != A4_SHOW_KIT_DEVICE_ID:
            raise ValueError("candidate retention is available only for Analog Four")
        selected = entry.selected_candidate
        if selected is None:
            raise ValueError("candidate retention requires a selected candidate")
        candidate_sysex = selected.analog_four_candidate.sysex
        runtime_frame = self._volatile_frames.get(candidate_sysex.artifact_id)
        if runtime_frame is None and candidate_sysex.retained is not None:
            runtime_frame = self._store.read_retained(candidate_sysex.retained)
        if runtime_frame is None:
            raise ValueError(
                "exact A4 candidate bytes are no longer in memory; regenerate the "
                "same seed, then retain the candidate"
            )
        updated = self._retain_frames(
            bank,
            ((candidate_sysex.artifact_id, runtime_frame),),
        )
        self._publish(updated, already_saved=True)
        return updated.entry(entry.entry_id)

    def _retain_frames(
        self,
        bank: ShowBank,
        frames: Sequence[tuple[str, bytes]],
    ) -> ShowBank:
        frame_set: dict[str, bytes] = {}
        for artifact_id, frame in frames:
            previous = frame_set.setdefault(artifact_id, frame)
            if previous != frame:
                raise ValueError("one artifact id cannot retain conflicting exact bytes")
            self._cache_frame(artifact_id, frame)
        updated = self._store.retain_sysex_set(bank, frame_set)
        for artifact_id in frame_set:
            # retain_sysex_set either retains the complete set atomically or
            # raises; only its successful return allows cache eviction.
            self._volatile_frames.pop(artifact_id, None)
        return updated


__all__ = [
    "CaptureKind",
    "MAX_CANDIDATES_PER_REQUEST",
    "SHOW_BANK_WORKSPACE_SCHEMA_VERSION",
    "ShowKitForgeWorkspace",
]
