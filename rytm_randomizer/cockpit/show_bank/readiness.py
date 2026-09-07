"""Pure Show Kit Forge lifecycle transitions and readiness evaluation."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Final, cast

from ...guardrails.input_validation import require_boolean
from ..data.show_bank import (
    A4_SHOW_KIT_DEVICE_ID,
    RYTM_SHOW_KIT_DEVICE_ID,
    SHOW_BANK_REVISION_MAX,
    FavoriteRecapture,
    HardwareSaveAttestation,
    OxiShowMetadata,
    RetainedSysexArtifact,
    ShowBank,
    ShowBankEntry,
    ShowKitBlockedReason,
    ShowKitCandidate,
    ShowKitCapture,
    ShowKitDeviceId,
    ShowKitEvidence,
    ShowKitFavorite,
    ShowKitSysex,
    ShowTimePreflight,
)

Clock = Callable[[], datetime]

CATALOG_ONLY_EVIDENCE_ID: Final[str] = "imported-catalog-only"


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp; callers may inject a clock."""

    return datetime.now(tz=timezone.utc)


def _now(clock: Clock) -> datetime:
    value = clock()
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("show-bank clock must return a timezone-aware datetime")
    return value


def create_show_bank(  # noqa: PLR0913 - typed creation fields and injectable evidence clock
    *,
    bank_id: str,
    name: str,
    description: str = "",
    notes: Sequence[str] = (),
    evidence: Sequence[ShowKitEvidence] = (),
    clock: Clock = utc_now,
) -> ShowBank:
    """Create revision zero of an empty show bank."""

    timestamp = _now(clock)
    return ShowBank(
        bank_id=bank_id,
        name=name,
        description=description,
        revision=0,
        entries=(),
        notes=tuple(notes),
        evidence=tuple(evidence),
        created_at=timestamp,
        updated_at=timestamp,
    )


def _advance(bank: ShowBank, entries: tuple[ShowBankEntry, ...], timestamp: datetime) -> ShowBank:
    if bank.revision >= SHOW_BANK_REVISION_MAX:
        raise ValueError("show-bank revision limit reached")
    return replace(
        bank,
        entries=entries,
        revision=bank.revision + 1,
        updated_at=timestamp,
    )


def _entry_position(bank: ShowBank, entry_id: str) -> int:
    for index, entry in enumerate(bank.entries):
        if entry.entry_id == entry_id:
            return index
    raise ValueError(f"unknown show-bank entry id: {entry_id!r}")


def _replace_entry(
    bank: ShowBank,
    entry_id: str,
    transform: Callable[[ShowBankEntry, datetime], ShowBankEntry],
    *,
    clock: Clock,
) -> ShowBank:
    timestamp = _now(clock)
    index = _entry_position(bank, entry_id)
    entries = list(bank.entries)
    entries[index] = transform(entries[index], timestamp)
    return _advance(bank, tuple(entries), timestamp)


def add_entry(bank: ShowBank, entry: ShowBankEntry, *, clock: Clock = utc_now) -> ShowBank:
    """Append an entry and assign the next contiguous cue index."""

    if any(existing.entry_id == entry.entry_id for existing in bank.entries):
        raise ValueError(f"duplicate show-bank entry id: {entry.entry_id!r}")
    timestamp = _now(clock)
    normalized = replace(
        entry,
        cue_index=len(bank.entries) + 1,
        updated_at=timestamp,
    )
    return _advance(bank, (*bank.entries, normalized), timestamp)


def remove_entry(bank: ShowBank, entry_id: str, *, clock: Clock = utc_now) -> ShowBank:
    """Remove one cue and compact all later cue indexes."""

    timestamp = _now(clock)
    position = _entry_position(bank, entry_id)
    kept = bank.entries[:position] + bank.entries[position + 1 :]
    entries = tuple(
        replace(entry, cue_index=index, updated_at=timestamp)
        for index, entry in enumerate(kept, start=1)
    )
    return _advance(bank, entries, timestamp)


def duplicate_entry(
    bank: ShowBank,
    entry_id: str,
    new_entry_id: str,
    *,
    name: str | None = None,
    clock: Clock = utc_now,
) -> ShowBank:
    """Duplicate durable cue evidence while clearing every transient readiness fact."""

    if any(entry.entry_id == new_entry_id for entry in bank.entries):
        raise ValueError(f"duplicate show-bank entry id: {new_entry_id!r}")
    timestamp = _now(clock)
    source = bank.entries[_entry_position(bank, entry_id)]
    duplicate = replace(
        source,
        entry_id=new_entry_id,
        cue_index=len(bank.entries) + 1,
        name=source.name if name is None else name,
        selected_candidate_id=None,
        rytm_live_auditioned_candidate_id=None,
        rytm_live_auditioned_at=None,
        show_time_preflight=None,
        show_ready_at=None,
        created_at=timestamp,
        updated_at=timestamp,
    )
    return _advance(bank, (*bank.entries, duplicate), timestamp)


def reorder_entries(
    bank: ShowBank,
    ordered_entry_ids: Sequence[str],
    *,
    clock: Clock = utc_now,
) -> ShowBank:
    """Reorder every entry exactly once and rewrite contiguous cue indexes."""

    ids = tuple(ordered_entry_ids)
    if len(ids) != len(set(ids)):
        raise ValueError("ordered entry ids must be unique")
    by_id = {entry.entry_id: entry for entry in bank.entries}
    if frozenset(ids) != frozenset(by_id):
        raise ValueError("ordered entry ids must contain every bank entry exactly once")
    timestamp = _now(clock)
    entries = tuple(
        replace(by_id[entry_id], cue_index=index, updated_at=timestamp)
        for index, entry_id in enumerate(ids, start=1)
    )
    return _advance(bank, entries, timestamp)


def update_bank_metadata(
    bank: ShowBank,
    *,
    name: str,
    description: str,
    notes: Sequence[str],
    clock: Clock = utc_now,
) -> ShowBank:
    """Update operator-facing bank text without changing evidence state."""

    timestamp = _now(clock)
    if bank.revision >= SHOW_BANK_REVISION_MAX:
        raise ValueError("show-bank revision limit reached")
    return replace(
        bank,
        name=name,
        description=description,
        notes=tuple(notes),
        revision=bank.revision + 1,
        updated_at=timestamp,
    )


def update_entry_metadata(  # noqa: PLR0913 - explicit typed cue fields preserve omission semantics
    bank: ShowBank,
    entry_id: str,
    *,
    name: str,
    description: str,
    oxi: OxiShowMetadata,
    audition_notes: Sequence[str],
    energy_level: int | None,
    energy_notes: Sequence[str],
    transition_notes: Sequence[str],
    recovery_notes: Sequence[str],
    clock: Clock = utc_now,
) -> ShowBank:
    """Update one cue's descriptive/OXI fields without changing its favorite."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        return replace(
            entry,
            name=name,
            description=description,
            oxi=oxi,
            audition_notes=tuple(audition_notes),
            energy_level=energy_level,
            energy_notes=tuple(energy_notes),
            transition_notes=tuple(transition_notes),
            recovery_notes=tuple(recovery_notes),
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def add_candidate(
    bank: ShowBank,
    entry_id: str,
    candidate: ShowKitCandidate,
    *,
    select: bool = False,
    clock: Clock = utc_now,
) -> ShowBank:
    """Add an inert paired candidate; selection remains an explicit choice."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if any(item.candidate_id == candidate.candidate_id for item in entry.candidates):
            raise ValueError(f"duplicate candidate id: {candidate.candidate_id!r}")
        return replace(
            entry,
            candidates=(*entry.candidates, candidate),
            selected_candidate_id=(
                candidate.candidate_id if select else entry.selected_candidate_id
            ),
            rytm_live_auditioned_candidate_id=(
                None if select else entry.rytm_live_auditioned_candidate_id
            ),
            rytm_live_auditioned_at=(None if select else entry.rytm_live_auditioned_at),
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def select_candidate(
    bank: ShowBank,
    entry_id: str,
    candidate_id: str,
    *,
    clock: Clock = utc_now,
) -> ShowBank:
    """Select an exact candidate for preview/prepare without favoriting it."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if all(item.candidate_id != candidate_id for item in entry.candidates):
            raise ValueError(f"unknown candidate id: {candidate_id!r}")
        return replace(
            entry,
            selected_candidate_id=candidate_id,
            rytm_live_auditioned_candidate_id=None,
            rytm_live_auditioned_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def record_rytm_live_audition(
    bank: ShowBank,
    entry_id: str,
    *,
    clock: Clock = utc_now,
) -> ShowBank:
    """Record a successful Rytm RAM-only ArmedApply for the selected candidate."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if entry.selected_candidate_id is None:
            raise ValueError("Rytm live audition requires a selected candidate")
        return replace(
            entry,
            rytm_live_auditioned_candidate_id=entry.selected_candidate_id,
            rytm_live_auditioned_at=timestamp,
            show_ready_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def mark_favorite(
    bank: ShowBank,
    entry_id: str,
    *,
    notes: Sequence[str] = (),
    replace_existing: bool = False,
    clock: Clock = utc_now,
) -> ShowBank:
    """Promote the selected candidate; changing an existing favorite is explicit."""

    require_boolean(replace_existing, "replace_existing")

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if entry.selected_candidate_id is None:
            raise ValueError("marking a favorite requires a selected candidate")
        if entry.favorite is not None:
            if entry.favorite.candidate_id == entry.selected_candidate_id:
                return replace(
                    entry,
                    favorite=replace(entry.favorite, notes=tuple(notes)),
                    updated_at=timestamp,
                )
            if not replace_existing:
                raise ValueError("replacing a different favorite requires replace_existing=True")
        return replace(
            entry,
            favorite=ShowKitFavorite(
                candidate_id=entry.selected_candidate_id,
                selected_at=timestamp,
                notes=tuple(notes),
            ),
            rytm_hardware_save=None,
            analog_four_hardware_save=None,
            rytm_recapture=None,
            analog_four_recapture=None,
            show_time_preflight=None,
            show_ready_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def attest_hardware_save(  # noqa: PLR0913 - paired slots, operator evidence, and injectable clock
    bank: ShowBank,
    entry_id: str,
    *,
    device_id: ShowKitDeviceId,
    hardware_slot: int,
    note: str,
    clock: Clock = utc_now,
) -> ShowBank:
    """Record a manual save statement; it does not verify bytes."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if entry.favorite is None:
            raise ValueError("hardware-save attestation requires a favorite")
        save = HardwareSaveAttestation(
            device_id=device_id,
            hardware_slot=hardware_slot,
            attested_at=timestamp,
            note=note,
        )
        if device_id == RYTM_SHOW_KIT_DEVICE_ID:
            return replace(
                entry,
                rytm_hardware_save=save,
                rytm_recapture=None,
                show_time_preflight=None,
                show_ready_at=None,
                updated_at=timestamp,
            )
        return replace(
            entry,
            analog_four_hardware_save=save,
            analog_four_recapture=None,
            show_time_preflight=None,
            show_ready_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def record_recapture(  # noqa: PLR0913 - paired capture/equivalence evidence stays explicit
    bank: ShowBank,
    entry_id: str,
    capture: ShowKitCapture,
    *,
    source_semantic_fingerprint: str,
    observed_semantic_fingerprint: str | None,
    comparison_reason: str,
    clock: Clock = utc_now,
) -> ShowBank:
    """Compare a fresh capture with the favorite and preserve mismatches."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        favorite = entry.favorite_candidate
        if favorite is None:
            raise ValueError("favorite recapture requires a favorite")
        if capture.device_id == RYTM_SHOW_KIT_DEVICE_ID:
            if entry.rytm_hardware_save is None:
                raise ValueError("Rytm recapture requires a Rytm hardware-save attestation")
            expected = favorite.rytm_semantic_fingerprint
            recapture = FavoriteRecapture(
                device_id=capture.device_id,
                expected_semantic_fingerprint=expected,
                source_semantic_fingerprint=source_semantic_fingerprint,
                observed_semantic_fingerprint=observed_semantic_fingerprint,
                capture=capture,
                recorded_at=timestamp,
                matches_candidate=observed_semantic_fingerprint == expected,
                matches_source=(observed_semantic_fingerprint == source_semantic_fingerprint),
                comparison_reason=comparison_reason,
            )
            return replace(
                entry,
                rytm_recapture=recapture,
                show_time_preflight=None,
                show_ready_at=None,
                updated_at=timestamp,
            )
        if entry.analog_four_hardware_save is None:
            raise ValueError("A4 recapture requires an A4 hardware-save attestation")
        expected = favorite.analog_four_candidate.semantic_fingerprint
        recapture = FavoriteRecapture(
            device_id=capture.device_id,
            expected_semantic_fingerprint=expected,
            source_semantic_fingerprint=source_semantic_fingerprint,
            observed_semantic_fingerprint=observed_semantic_fingerprint,
            capture=capture,
            recorded_at=timestamp,
            matches_candidate=observed_semantic_fingerprint == expected,
            matches_source=observed_semantic_fingerprint == source_semantic_fingerprint,
            comparison_reason=comparison_reason,
        )
        return replace(
            entry,
            analog_four_recapture=recapture,
            show_time_preflight=None,
            show_ready_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def record_show_time_preflight(  # noqa: PLR0913 - paired fresh evidence and expected cue identity
    bank: ShowBank,
    entry_id: str,
    *,
    current_rytm_capture: ShowKitCapture,
    current_analog_four_capture: ShowKitCapture,
    reason: str,
    clock: Clock = utc_now,
) -> ShowBank:
    """Compare current full captures and grant or revoke transient readiness."""

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        if entry.status not in ("verified", "show-ready"):
            raise ValueError("show-time preflight requires a verified paired favorite")
        rytm_slot = (
            entry.rytm_hardware_save.hardware_slot
            if entry.rytm_hardware_save is not None
            else entry.rytm_source.hardware_slot
        )
        analog_four_slot = (
            entry.analog_four_hardware_save.hardware_slot
            if entry.analog_four_hardware_save is not None
            else entry.analog_four_source.hardware_slot
        )
        if rytm_slot is None or analog_four_slot is None:
            raise ValueError("show-time preflight requires paired hardware slots")
        if current_rytm_capture.device_id != RYTM_SHOW_KIT_DEVICE_ID:
            raise ValueError("show-time Rytm capture is attached to the wrong device")
        if current_analog_four_capture.device_id != A4_SHOW_KIT_DEVICE_ID:
            raise ValueError("show-time A4 capture is attached to the wrong device")
        # The entry status invariant already proves these optionals are present.
        rytm_recapture = cast(FavoriteRecapture, entry.rytm_recapture)
        analog_four_recapture = cast(FavoriteRecapture, entry.analog_four_recapture)
        prior_checked_at = (
            None if entry.show_time_preflight is None else entry.show_time_preflight.checked_at
        )
        rytm_cutoff = rytm_recapture.recorded_at
        a4_cutoff = analog_four_recapture.recorded_at
        if prior_checked_at is not None:
            rytm_cutoff = max(rytm_cutoff, prior_checked_at)
            a4_cutoff = max(a4_cutoff, prior_checked_at)
        if current_rytm_capture.captured_at <= rytm_cutoff:
            raise ValueError("show-time Rytm capture must be newer than prior evidence")
        if current_analog_four_capture.captured_at <= a4_cutoff:
            raise ValueError("show-time A4 capture must be newer than prior evidence")
        expected_rytm = rytm_recapture.capture.fingerprint
        expected_a4 = analog_four_recapture.capture.fingerprint
        preflight = ShowTimePreflight(
            expected_rytm_fingerprint=expected_rytm,
            observed_rytm_fingerprint=current_rytm_capture.fingerprint,
            observed_rytm_capture_id=current_rytm_capture.capture_id,
            observed_rytm_captured_at=current_rytm_capture.captured_at,
            rytm_matches=current_rytm_capture.fingerprint == expected_rytm,
            expected_a4_fingerprint=expected_a4,
            observed_a4_fingerprint=current_analog_four_capture.fingerprint,
            observed_a4_capture_id=current_analog_four_capture.capture_id,
            observed_a4_captured_at=current_analog_four_capture.captured_at,
            a4_matches=current_analog_four_capture.fingerprint == expected_a4,
            checked_at=timestamp,
            reason=reason,
        )
        return replace(
            entry,
            show_time_preflight=preflight,
            show_ready_at=timestamp if preflight.ready else None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def return_to_source(
    bank: ShowBank,
    entry_id: str,
    *,
    clock: Clock = utc_now,
) -> ShowBank:
    """Clear active audition selection while preserving the full evidence catalog.

    The actual instrument return remains a manual source-slot load.  This
    transition records only that Cockpit is no longer auditioning a generated
    candidate; it must never erase favorites, save attestations, or recaptures.
    """

    def transform(entry: ShowBankEntry, timestamp: datetime) -> ShowBankEntry:
        return replace(
            entry,
            selected_candidate_id=None,
            rytm_live_auditioned_candidate_id=None,
            rytm_live_auditioned_at=None,
            show_ready_at=None,
            updated_at=timestamp,
        )

    return _replace_entry(bank, entry_id, transform, clock=clock)


def is_catalog_only_show_bank(bank: ShowBank) -> bool:
    """Return whether imported state is explicitly non-audition-authoritative."""

    return any(item.evidence_id == CATALOG_ONLY_EVIDENCE_ID for item in bank.evidence)


def normalize_catalog_import(bank: ShowBank, *, clock: Clock = utc_now) -> ShowBank:
    """Project a verified package into inert catalog-only local state.

    Historical favorites, save attestations, recaptures, and preflight evidence
    remain available for inspection and re-export.  Process-current selection,
    live-audition, and show-ready authority are revoked explicitly.
    """

    timestamp = _now(clock)
    marker = ShowKitEvidence(
        evidence_id=CATALOG_ONLY_EVIDENCE_ID,
        status="blocked",
        source="Show-pack catalog import",
        observed_at=timestamp,
        notes=(
            "Imported candidate history grants no ArmedApply authority.",
            "Capture fresh source KITs before generating or auditioning candidates.",
        ),
    )
    found = False
    evidence: list[ShowKitEvidence] = []
    for item in bank.evidence:
        if item.evidence_id == CATALOG_ONLY_EVIDENCE_ID:
            if not found:
                evidence.append(marker)
                found = True
            continue
        evidence.append(item)
    if not found:
        evidence.append(marker)
    entries = tuple(
        replace(
            entry,
            selected_candidate_id=None,
            rytm_live_auditioned_candidate_id=None,
            rytm_live_auditioned_at=None,
            show_ready_at=None,
            updated_at=timestamp,
        )
        for entry in bank.entries
    )
    # Import publishes a new create-only local namespace. Revision numbers are
    # local history, so even a package at the source ceiling starts at zero.
    # The verified source revision remains immutable in the package manifest.
    return replace(
        bank, revision=0, evidence=tuple(evidence), entries=entries, updated_at=timestamp
    )


def _replace_sysex(sysex: ShowKitSysex, artifact: RetainedSysexArtifact) -> ShowKitSysex:
    if sysex.frame_sha256 != artifact.sha256 or sysex.frame_bytes != artifact.byte_count:
        raise ValueError("retained bytes do not match the declared SysEx identity")
    return replace(sysex, retained=artifact)


def _replace_capture_artifact(
    capture: ShowKitCapture,
    artifact_id: str,
    artifact: RetainedSysexArtifact,
) -> ShowKitCapture:
    if capture.sysex.artifact_id != artifact_id:
        return capture
    return replace(capture, sysex=_replace_sysex(capture.sysex, artifact))


def attach_retained_sysex(
    bank: ShowBank,
    artifact_id: str,
    artifact: RetainedSysexArtifact,
    *,
    clock: Clock = utc_now,
) -> ShowBank:
    """Attach explicit local-retention metadata to every matching reference."""

    declared = bank.sysex_artifact(artifact_id)
    if declared.retained == artifact:
        return bank
    if declared.retained is not None:
        raise ValueError("SysEx artifact is already retained with different metadata")
    timestamp = _now(clock)
    entries: list[ShowBankEntry] = []
    for entry in bank.entries:
        candidates = tuple(
            replace(
                candidate,
                analog_four_candidate=replace(
                    candidate.analog_four_candidate,
                    sysex=(
                        _replace_sysex(candidate.analog_four_candidate.sysex, artifact)
                        if candidate.analog_four_candidate.sysex.artifact_id == artifact_id
                        else candidate.analog_four_candidate.sysex
                    ),
                ),
            )
            for candidate in entry.candidates
        )
        rytm_recapture = entry.rytm_recapture
        if rytm_recapture is not None:
            rytm_recapture = replace(
                rytm_recapture,
                capture=_replace_capture_artifact(rytm_recapture.capture, artifact_id, artifact),
            )
        a4_recapture = entry.analog_four_recapture
        if a4_recapture is not None:
            a4_recapture = replace(
                a4_recapture,
                capture=_replace_capture_artifact(a4_recapture.capture, artifact_id, artifact),
            )
        entries.append(
            replace(
                entry,
                rytm_source=_replace_capture_artifact(entry.rytm_source, artifact_id, artifact),
                analog_four_source=_replace_capture_artifact(
                    entry.analog_four_source, artifact_id, artifact
                ),
                candidates=candidates,
                rytm_recapture=rytm_recapture,
                analog_four_recapture=a4_recapture,
                updated_at=timestamp,
            )
        )
    return _advance(bank, tuple(entries), timestamp)


@dataclass(frozen=True)
class ShowBankReadiness:
    """Pure bank-level preflight result with bounded actionable reasons."""

    ready: bool
    entry_count: int
    show_ready_entry_ids: tuple[str, ...]
    blocked_reasons: tuple[ShowKitBlockedReason, ...]


def show_bank_readiness(bank: ShowBank) -> ShowBankReadiness:
    """Summarize whether every ordered cue has an explicit show-ready grant."""

    ready_ids = tuple(entry.entry_id for entry in bank.entries if entry.status == "show-ready")
    reasons: list[ShowKitBlockedReason] = []
    if not bank.entries:
        reasons.append("show_bank_empty")
    for entry in bank.entries:
        if entry.status != "show-ready":
            reasons.append("cue_not_show_ready")
        if entry.rytm_recapture is not None and not entry.rytm_recapture.matches_candidate:
            reasons.append("rytm_recapture_mismatch")
        if (
            entry.analog_four_recapture is not None
            and not entry.analog_four_recapture.matches_candidate
        ):
            reasons.append("a4_recapture_mismatch")
    return ShowBankReadiness(
        ready=bool(bank.entries) and len(ready_ids) == len(bank.entries),
        entry_count=len(bank.entries),
        show_ready_entry_ids=ready_ids,
        blocked_reasons=tuple(dict.fromkeys(reasons)),
    )


__all__ = [
    "CATALOG_ONLY_EVIDENCE_ID",
    "Clock",
    "ShowBankReadiness",
    "add_candidate",
    "add_entry",
    "attach_retained_sysex",
    "attest_hardware_save",
    "create_show_bank",
    "duplicate_entry",
    "mark_favorite",
    "is_catalog_only_show_bank",
    "normalize_catalog_import",
    "record_recapture",
    "record_rytm_live_audition",
    "record_show_time_preflight",
    "remove_entry",
    "reorder_entries",
    "return_to_source",
    "select_candidate",
    "show_bank_readiness",
    "update_bank_metadata",
    "update_entry_metadata",
    "utc_now",
]
