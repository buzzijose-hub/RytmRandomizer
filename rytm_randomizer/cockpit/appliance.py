"""Revision-bound touch orchestration over the existing Cockpit core.

Simulation owns no MIDI capability. Production previews use captured promoted
Rytm fields; saved-state evidence never becomes working-memory authority.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Final, cast

from ..observability.logging import get_logger
from ..snapshot.mutation_scope import MutationScope, registered_mutation_ids
from .capture.appliance_a4 import appliance_a4_parameter_encodings
from .capture.appliance_capabilities import ApplianceParameterCapability, parameter_capabilities
from .data import (
    MutationCandidate,
    PadState,
    ProfileModel,
    Snapshot,
    classify_payload,
    new_ulid,
    require_schema_version,
)
from .data.rytm_parameter_map import cockpit_parameter_mapping
from .data.stage import STAGE_DEVICE_IDS, StageDeviceId
from .device import MockDeviceAdapter
from .engine import mutate
from .export.writer import atomic_write
from .history import HistoryStore

DEVICE_IDS: Final[tuple[StageDeviceId, ...]] = STAGE_DEVICE_IDS
TARGETS: Final[Mapping[str, tuple[StageDeviceId, ...]]] = MappingProxyType(
    {
        "rytm": (DEVICE_IDS[0],),
        "a4": (DEVICE_IDS[1],),
        "both": DEVICE_IDS,
    }
)
OPERATIONS: Final[frozenset[str]] = frozenset(
    (
        "state",
        "scope",
        "mutate",
        "anchor",
        "undo",
        "redo",
        "return_anchor",
        "apply",
        "profile_save",
        "profile_load",
        "profile_delete",
        "profile_import",
        "profile_export",
    )
)
PROFILE_LIMIT: Final[int] = 32
HISTORY_LIMIT: Final[int] = 32
STORAGE_LIMIT: Final[int] = 65536
SCHEMA_VERSION: Final[int] = require_schema_version("appliance_scopes")
_logger = get_logger(__name__)


def validated_object(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError("expected an object with string keys")
    checked = cast(Mapping[object, object], value)
    if not all(isinstance(key, str) for key in checked):
        raise ValueError("expected an object with string keys")
    return cast(Mapping[str, object], value)


def _depth(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("depth must be numeric")
    result = float(value)
    if not math.isfinite(result) or not 0 <= result <= 1:
        raise ValueError("depth must be finite and between zero and one")
    return result


def _strings(value: object, available: set[str]) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError("expected a string list")
    if not all(isinstance(item, str) for item in cast(list[object], value)):
        raise ValueError("expected a string list")
    items = cast(list[str], value)
    if len(items) != len(set(items)) or not set(items) <= available:
        raise ValueError("unknown or duplicate scope member")
    return tuple(items)


@dataclass(frozen=True)
class ApplianceScope:
    """Explicit empty targets mean none; legacy MutationScope stays unchanged."""

    target_ids: tuple[int, ...]
    locked_ids: tuple[int, ...]
    page_ids: tuple[str, ...]
    track_depths: tuple[tuple[str, float], ...] = ()
    page_depths: tuple[tuple[str, float], ...] = ()
    parameter_locks: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "target_ids": list(self.target_ids),
            "locked_ids": list(self.locked_ids),
            "page_ids": list(self.page_ids),
            "track_depths": dict(self.track_depths),
            "page_depths": dict(self.page_depths),
            "parameter_locks": list(self.parameter_locks),
        }

    def effective_ids(self, device_id: StageDeviceId) -> frozenset[int]:
        if not self.target_ids:
            return frozenset()
        return MutationScope(
            frozenset(self.target_ids), frozenset(self.locked_ids)
        ).validated_effective_ids(
            registered_mutation_ids(device_id),
            item_label="track",
        )

    @classmethod
    def parse(cls, value: object, device_id: StageDeviceId) -> ApplianceScope:
        raw = validated_object(value)
        rows = parameter_capabilities(device_id)
        pages = {row.page for row in rows}
        parameters = {row.parameter_id for row in rows}
        available = set(registered_mutation_ids(device_id))

        def ids(field: str) -> tuple[int, ...]:
            values = raw.get(field, [])
            if not isinstance(values, list):
                raise ValueError("targets and locks must be lists")
            checked: list[int] = []
            for item in cast(list[object], values):
                if isinstance(item, bool) or not isinstance(item, int) or item not in available:
                    raise ValueError("track identifier is outside device domain")
                checked.append(item)
            if len(checked) != len(set(checked)):
                raise ValueError("duplicate track identifier")
            return tuple(checked)

        def depths(field: str, domain: set[str]) -> tuple[tuple[str, float], ...]:
            values = validated_object(raw.get(field, {}))
            if not set(values) <= domain:
                raise ValueError("unknown depth scope")
            return tuple((key, _depth(item)) for key, item in sorted(values.items()))

        return cls(
            ids("target_ids"),
            ids("locked_ids"),
            _strings(raw.get("page_ids", []), pages),
            depths("track_depths", {str(item) for item in available}),
            depths("page_depths", pages),
            _strings(raw.get("parameter_locks", []), parameters),
        )


class ApplianceWorkspace:
    """Single-session scope presets and bounded local history, no output seam."""

    def __init__(self, *, simulation: bool, profile_file: Path | None = None) -> None:
        self.simulation = simulation
        self.profile_file = profile_file
        self.revision = 0
        self.target = "rytm"
        self.master_depth = 0.45
        self.scopes: dict[StageDeviceId, ApplianceScope] = {}
        for device_id in DEVICE_IDS:
            rows = parameter_capabilities(device_id)
            self.scopes[device_id] = ApplianceScope(
                tuple(sorted(registered_mutation_ids(device_id))),
                (),
                tuple(dict.fromkeys(row.page for row in rows)),
                parameter_locks=tuple(row.parameter_id for row in rows if row.default_protected),
            )
        self.sources: dict[StageDeviceId, Snapshot] = {}
        self.histories: dict[StageDeviceId, HistoryStore] = {}
        self.timeline: list[dict[StageDeviceId, Snapshot]] = []
        self.cursor = 0
        self.anchor: dict[StageDeviceId, Snapshot] | None = None
        self.candidates: dict[StageDeviceId, MutationCandidate] = {}
        self.candidate: dict[str, object] | None = None
        self.context: str | None = None
        self.last_receipt: dict[str, object] | None = None
        self.profiles: dict[str, dict[str, object]] = {}
        self.storage_error: str | None = None
        self._load_profiles()

    def _load_profiles(self) -> None:
        if self.profile_file is None or not self.profile_file.exists():
            return
        try:
            if self.profile_file.stat().st_size > STORAGE_LIMIT:
                raise ValueError("oversize profile file")
            document = json.loads(self.profile_file.read_bytes())
            decision = classify_payload("appliance_scopes", document)
            if decision.refused:
                self.storage_error = decision.code
                return
            self.profiles = self._validated_profiles(decision.payload)
        except (OSError, ValueError, TypeError):
            self.storage_error = "profile_storage_corrupt_or_unreadable"

    def _validated_profiles(self, document: object) -> dict[str, dict[str, object]]:
        raw = validated_object(document)
        if raw.get("schema_version") != SCHEMA_VERSION or isinstance(
            raw.get("schema_version"), bool
        ):
            raise ValueError("unsupported profile schema")
        profiles = validated_object(raw.get("profiles"))
        if len(profiles) > PROFILE_LIMIT:
            raise ValueError("too many profiles")
        result: dict[str, dict[str, object]] = {}
        for name, item in profiles.items():
            self._name(name)
            profile = validated_object(item)
            if profile.get("target") not in TARGETS:
                raise ValueError("unknown target")
            lanes = validated_object(profile.get("lanes"))
            if set(lanes) != set(DEVICE_IDS):
                raise ValueError("profile requires both explicit lanes")
            checked = {
                device: ApplianceScope.parse(lanes[device], device).to_dict()
                for device in DEVICE_IDS
            }
            association = validated_object(profile.get("association"))
            fingerprints = validated_object(association.get("fingerprints"))
            if set(fingerprints) != set(DEVICE_IDS) or any(
                value is not None and (not isinstance(value, str) or len(value) > 128)
                for value in fingerprints.values()
            ):
                raise ValueError("invalid profile identity")
            result[name] = {
                "target": profile["target"],
                "master_depth": _depth(profile.get("master_depth")),
                "lanes": checked,
                "association": {"device_ids": list(DEVICE_IDS), "fingerprints": dict(fingerprints)},
            }
        return result

    def _publish(self, profiles: dict[str, dict[str, object]], *, recovery: bool = False) -> None:
        data = json.dumps(
            {"schema_version": SCHEMA_VERSION, "profiles": profiles}, allow_nan=False
        ).encode()
        if len(data) > STORAGE_LIMIT:
            raise ValueError("profile storage limit exceeded")
        if self.storage_error and not recovery:
            raise ValueError("profile storage requires explicit validated import recovery")
        if self.storage_error == "persisted_state.schema_newer_than_app":
            raise ValueError("newer profile schema cannot be overwritten by this build")
        if self.profile_file is not None:
            if self.storage_error and self.profile_file.exists():
                original = self.profile_file.read_bytes()
                if len(original) > STORAGE_LIMIT:
                    raise ValueError("oversize original requires operator recovery before import")
                atomic_write(
                    self.profile_file.with_name(self.profile_file.name + ".recovery-" + new_ulid()),
                    original,
                )
            atomic_write(self.profile_file, data, overwrite=True)
        self.profiles = profiles
        self.storage_error = None

    def _name(self, name: object) -> str:
        if (
            not isinstance(name, str)
            or not name.strip()
            or len(name) > 64
            or any(ord(c) < 32 for c in name)
        ):
            raise ValueError("profile name must contain 1..64 printable characters")
        return name.strip()

    def invalidate(self) -> None:
        self.candidate = None
        self.candidates.clear()
        self.revision += 1

    def revoke_context(self) -> None:
        """Drop transient source assumptions on disconnect, leaving saved rules."""
        self.context = None
        self.invalidate()
        self.sources.clear()
        self.histories.clear()
        self.timeline.clear()
        self.anchor = None
        self.cursor = 0

    def sync(
        self, source: Snapshot | None, *, context: str, a4_source: Snapshot | None = None
    ) -> None:
        if context == self.context:
            return
        self.context = context
        self.invalidate()
        _logger.info(
            "appliance_context_invalidated",
            extra={"revision": self.revision, "simulation": self.simulation},
        )
        self.sources = {} if source is None else {DEVICE_IDS[0]: source}
        if a4_source is not None and not self.simulation:
            self.sources[DEVICE_IDS[1]] = a4_source
        if self.simulation:
            rows = parameter_capabilities(DEVICE_IDS[1])
            params = {row.parameter_id: 64 for row in rows}
            self.sources[DEVICE_IDS[1]] = Snapshot(
                new_ulid(),
                DEVICE_IDS[1],
                datetime.now(timezone.utc),
                tuple(
                    PadState(track, "SIMULATED NORMALIZED MIDI", params) for track in range(1, 5)
                ),
                None,
                None,
            )
        self.histories = {}
        for device_id, snapshot in self.sources.items():
            history = HistoryStore()
            history.initial(snapshot)
            self.histories[device_id] = history
        self.timeline = [dict(self.sources)]
        self.cursor = 0
        self.anchor = None

    def change_scope(self, payload: Mapping[str, object]) -> None:
        target = payload.get("target", self.target)
        if not isinstance(target, str) or target not in TARGETS:
            raise ValueError("unknown target")
        depth = _depth(payload.get("master_depth", self.master_depth))
        lanes = validated_object(payload.get("lanes", {}))
        if not set(lanes) <= set(DEVICE_IDS):
            raise ValueError("unknown lane")
        scopes = dict(self.scopes)
        for device_id, patch in lanes.items():
            device = cast(StageDeviceId, device_id)
            merged = {**scopes[device].to_dict(), **validated_object(patch)}
            scopes[device] = ApplianceScope.parse(merged, device)
        self.target, self.master_depth, self.scopes = target, depth, scopes
        self.invalidate()

    def roll(self, profile: ProfileModel, seed: int) -> None:
        devices = TARGETS[self.target]
        if self.master_depth == 0 or all(
            not self.scopes[device].effective_ids(device) for device in devices
        ):
            self.candidate = None
            self.candidates.clear()
            return
        if any(device not in self.sources for device in devices):
            raise ValueError(
                "all selected lanes require a trustworthy source; A4 live baseline is unavailable"
            )
        if self.target == "both" and any(
            not self.scopes[device].effective_ids(device) for device in devices
        ):
            raise ValueError("linked BOTH requires eligible targets in both lanes")
        requests: dict[
            StageDeviceId,
            tuple[
                Snapshot,
                ApplianceScope,
                dict[tuple[int, str], float],
                dict[tuple[int, str], ApplianceParameterCapability],
            ],
        ] = {}
        candidates: dict[StageDeviceId, MutationCandidate] = {}
        changes: list[dict[str, object]] = []
        native_encodings = {
            encoding.parameter_id: encoding for encoding in appliance_a4_parameter_encodings()
        }
        native_bounds: dict[StageDeviceId, dict[tuple[int, str], tuple[int, int]]] = {}
        for device_id in devices:
            snapshot = self.sources[device_id]
            scope = self.scopes[device_id]
            track_depths, page_depths = dict(scope.track_depths), dict(scope.page_depths)
            rows = parameter_capabilities(device_id)
            by_cell: dict[tuple[int, str], ApplianceParameterCapability] = {}
            depths: dict[tuple[int, str], float] = {}
            bounds: dict[tuple[int, str], tuple[int, int]] = {}
            for pad in snapshot.pads:
                for key in pad.params:
                    mapping = (
                        cockpit_parameter_mapping(pad.machine, key)
                        if device_id == DEVICE_IDS[0]
                        else None
                    )
                    row = next(
                        (
                            item
                            for item in rows
                            if (
                                item.parameter_id == key
                                if device_id != DEVICE_IDS[0]
                                else mapping is not None
                                and item.parameter == mapping.parameter
                                and item.page == ("SRC" if mapping.machine_key else mapping.section)
                                and item.machine_key == mapping.machine_key
                            )
                        ),
                        None,
                    )
                    if (
                        row is None
                        or row.page not in scope.page_ids
                        or row.parameter_id in scope.parameter_locks
                    ):
                        continue
                    # Selector/routing policies never receive interpolation, even if unlocked.
                    if row.categorical or row.legal_domain.authority == "unknown":
                        continue
                    if device_id == DEVICE_IDS[1] and not self.simulation:
                        encoding = native_encodings.get(key)
                        if encoding is None or not encoding.offline_mutable:
                            continue
                        bounds[(pad.pad_id, key)] = (encoding.raw_minimum, encoding.raw_maximum)
                    by_cell[(pad.pad_id, key)] = row
                    depths[(pad.pad_id, key)] = (
                        self.master_depth
                        * track_depths.get(str(pad.pad_id), 1)
                        * page_depths.get(row.page, 1)
                    )
            if scope.effective_ids(device_id) and any(
                value > 0 and cell[0] in scope.effective_ids(device_id)
                for cell, value in depths.items()
            ):
                requests[device_id] = (snapshot, scope, depths, by_cell)
                native_bounds[device_id] = bounds
        if self.target == "both" and len(requests) != len(devices):
            raise ValueError(
                "linked BOTH requires mutable unlocked parameters and nonzero depth in each lane"
            )
        if not requests:
            self.candidate = None
            self.candidates.clear()
            return
        for device_id, (snapshot, scope, depths, by_cell) in requests.items():
            candidate = mutate(
                snapshot,
                profile,
                min(0.9, max(0.1, self.master_depth)),
                seed,
                target_pad_ids=scope.effective_ids(device_id),
                parameter_depths=depths,
                parameter_bounds=native_bounds[device_id] or None,
            )
            candidates[device_id] = candidate
            pads = {pad.pad_id: pad for pad in snapshot.pads}
            for delta in candidate.pad_deltas:
                for key in sorted(delta.changed_keys):
                    row = by_cell[(delta.pad_id, key)]
                    changes.append(
                        {
                            "device_id": device_id,
                            "track_id": delta.pad_id,
                            "parameter_id": row.parameter_id,
                            "parameter": row.parameter,
                            "page": row.page,
                            "before": pads[delta.pad_id].params[key],
                            "after": delta.proposed_params[key],
                            "before_display": (
                                native_encodings[key].format_display(pads[delta.pad_id].params[key])
                                if device_id == DEVICE_IDS[1] and not self.simulation
                                else str(pads[delta.pad_id].params[key])
                            ),
                            "after_display": (
                                native_encodings[key].format_display(delta.proposed_params[key])
                                if device_id == DEVICE_IDS[1] and not self.simulation
                                else str(delta.proposed_params[key])
                            ),
                        }
                    )
        self.candidates = candidates
        self.revision += 1
        self.candidate = (
            None
            if not changes
            else {
                "candidate_id": new_ulid(),
                "revision": self.revision,
                "changes": changes,
                "send_plan_id": None,
                "live_ready": False,
                "blocked_reasons": (
                    []
                    if self.simulation
                    else [
                        "working_state_readback_unverified",
                        "precise_hardware_restore_unvalidated",
                    ]
                ),
            }
        )

    def apply_local(self, payload: Mapping[str, object], *, hardware_intent: bool) -> None:
        if not self.simulation or hardware_intent:
            raise ValueError(
                "appliance live apply requires validated working-state readback and precise restore; existing ArmedApply authority is not extended"
            )
        if (
            self.candidate is None
            or payload.get("candidate_id") != self.candidate["candidate_id"]
            or payload.get("confirmed") is not True
        ):
            raise ValueError("exact current candidate and confirmation are required")
        snapshots = dict(self.sources)
        for device_id, candidate in self.candidates.items():
            adapter = MockDeviceAdapter(self.sources[device_id])
            snapshot = adapter.apply(candidate, frozenset(self.scopes[device_id].locked_ids))
            self.histories[device_id].append_post_send(snapshot, via="send")
            snapshots[device_id] = snapshot
        self.sources = snapshots
        self.timeline = self.timeline[: self.cursor + 1] + [dict(snapshots)]
        self.timeline = self.timeline[-HISTORY_LIMIT:]
        self.cursor = len(self.timeline) - 1
        if any(len(history.current.entries) > HISTORY_LIMIT for history in self.histories.values()):
            for device, snapshot in snapshots.items():
                store = HistoryStore()
                store.initial(snapshot)
                self.histories[device] = store
        self.last_receipt = {
            "status": "simulated_local_apply",
            "sent_count": 0,
            "expected_count": 0,
            "hardware_verified": False,
        }
        self.invalidate()

    def navigate(self, operation: str) -> None:
        if operation == "anchor":
            self.anchor = dict(self.sources)
        elif operation == "return_anchor":
            if self.anchor is None:
                raise ValueError("no local anchor captured")
            self.sources = dict(self.anchor)
            self.timeline = [dict(self.sources)]
            self.cursor = 0
        else:
            cursor = self.cursor + (-1 if operation == "undo" else 1)
            if not 0 <= cursor < len(self.timeline):
                raise ValueError("no local history entry in that direction")
            self.cursor = cursor
            self.sources = dict(self.timeline[cursor])
        self.last_receipt = {
            "status": "local_history_only",
            "sent_count": 0,
            "expected_count": 0,
            "hardware_verified": False,
        }
        self.invalidate()

    def profile_action(
        self, operation: str, payload: Mapping[str, object], fingerprints: Mapping[str, object]
    ) -> dict[str, object] | None:
        if operation == "profile_import":
            document = payload.get("document")
            if len(json.dumps(document).encode()) > STORAGE_LIMIT:
                raise ValueError("import exceeds storage limit")
            self._publish(self._validated_profiles(document), recovery=True)
            self.invalidate()
            return None
        name = self._name(payload.get("name"))
        profiles = dict(self.profiles)
        if operation == "profile_save":
            profiles[name] = {
                "target": self.target,
                "master_depth": self.master_depth,
                "lanes": {device: scope.to_dict() for device, scope in self.scopes.items()},
                "association": {"device_ids": list(DEVICE_IDS), "fingerprints": dict(fingerprints)},
            }
            if len(profiles) > PROFILE_LIMIT:
                raise ValueError("profile limit reached")
            self._publish(profiles)
        elif name not in profiles:
            raise ValueError("profile does not exist")
        elif operation == "profile_export":
            return {"schema_version": 1, "profiles": {name: profiles[name]}}
        elif operation == "profile_delete":
            del profiles[name]
            self._publish(profiles)
        else:
            profile = profiles[name]
            association = validated_object(profile["association"])
            saved = validated_object(association["fingerprints"])
            if not self.simulation and (
                any(saved.get(device) is None for device in TARGETS[str(profile["target"])])
                or any(
                    saved.get(device) != fingerprints.get(device)
                    for device in TARGETS[str(profile["target"])]
                )
            ):
                raise ValueError(
                    "profile identity is unknown or differs from current kit; capture and associate a new profile"
                )
            self.change_scope(profile)
        self.invalidate()
        return None

    def state(
        self, *, provenance: Mapping[str, dict[str, object]], armed: bool
    ) -> dict[str, object]:
        lanes: dict[str, object] = {}
        native_encodings = {
            encoding.parameter_id: encoding for encoding in appliance_a4_parameter_encodings()
        }
        for device_id in DEVICE_IDS:
            source = self.sources.get(device_id)
            selected = self.scopes[device_id].target_ids
            reference_track = min(selected) if selected else None

            def parameter_view(
                row: ApplianceParameterCapability,
                source: Snapshot | None = source,
                device_id: StageDeviceId = device_id,
                reference_track: int | None = reference_track,
            ) -> dict[str, object]:
                values: dict[str, int] = {}
                if source is not None:
                    for pad in source.pads:
                        key = row.cockpit_key if device_id == DEVICE_IDS[0] else row.parameter_id
                        if key is None or key not in pad.params:
                            continue
                        if device_id == DEVICE_IDS[0]:
                            mapping = cockpit_parameter_mapping(pad.machine, key)
                            if (
                                mapping is None
                                or mapping.machine_key != row.machine_key
                                or mapping.parameter != row.parameter
                            ):
                                continue
                        values[str(pad.pad_id)] = pad.params[key]
                encoding = native_encodings.get(row.parameter_id)
                displayed = {
                    track: (
                        encoding.format_display(value)
                        if encoding is not None and not self.simulation
                        else str(value)
                    )
                    for track, value in values.items()
                }
                return {
                    "parameter_id": row.parameter_id,
                    "page": row.page,
                    "parameter": row.parameter,
                    "cockpit_key": row.cockpit_key,
                    "machine_key": row.machine_key,
                    "value": values.get(str(reference_track)),
                    "values_by_track": values,
                    "display_value": displayed.get(str(reference_track)),
                    "display_values_by_track": displayed,
                    "default_protected": row.default_protected,
                    "categorical": row.categorical,
                    "protection_reasons": list(row.protection_reasons),
                    "blockers": list(row.blockers),
                }

            lanes[device_id] = {
                "device_id": device_id,
                "reference_track_id": reference_track,
                "scope": self.scopes[device_id].to_dict(),
                "provenance": provenance[device_id],
                "parameters": [parameter_view(row) for row in parameter_capabilities(device_id)],
                "blocked_reasons": (
                    []
                    if self.simulation
                    else ["working_state_readback_unverified", "hardware_restore_unvalidated"]
                ),
            }
        return {
            "schema_version": 1,
            "revision": self.revision,
            "mode": "simulation" if self.simulation else "production",
            "target": self.target,
            "master_depth": self.master_depth,
            "armed": armed,
            "lanes": lanes,
            "candidate": self.candidate,
            "history": {
                "can_undo": self.cursor > 0,
                "can_redo": self.cursor + 1 < len(self.timeline),
                "count": len(self.timeline),
                "anchor_captured": self.anchor is not None,
                "hardware_restore_supported": False,
            },
            "profiles": [
                {"name": name, "association": item["association"]}
                for name, item in sorted(self.profiles.items())
            ],
            "last_receipt": self.last_receipt,
            "blocked_reasons": [self.storage_error] if self.storage_error else [],
        }


def context_digest(value: Mapping[str, object]) -> str:
    """Stable invalidation fingerprint; contains no secrets or authority grants."""
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
