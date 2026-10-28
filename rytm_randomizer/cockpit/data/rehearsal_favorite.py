"""Strict, inert local rehearsal retention; never persistent hardware authority.

The library verifies deterministic engine output above this data boundary.
Parsing here deliberately does not use the scalar DTOs' coercing loaders.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from hashlib import sha256
from types import MappingProxyType
from typing import Final

from ...guardrails.input_validation import (
    canonical_json_bytes,
    require_exact_keys,
    require_float,
    require_int,
    require_integer_tuple,
    require_object,
    require_sequence,
    require_text,
    require_text_tuple,
)
from ...snapshot.mutation_scope import MutationScope, registered_mutation_ids
from .mutation_candidate import MutationCandidate, PadDelta
from .parameter_scope import ParameterSelection
from .profile_model import ProfileModel
from .snapshot import PadState, Snapshot
from .stage import ANALOG_FOUR_DEVICE_ID, ANALOG_RYTM_DEVICE_ID, STAGE_DEVICE_IDS
from .types import narrow_status

_FAVORITE_FIELDS: Final[frozenset[str]] = frozenset(
    (
        "source_snapshot",
        "profile",
        "candidate",
        "rytm_pad_targets",
        "a4_track_targets",
        "locked_pad_ids",
        "locked_a4_track_ids",
        "rytm_parameter_selection",
        "a4_parameter_selection",
    )
)
_HASH_FIELDS: Final[frozenset[str]] = frozenset(("source_hash", "recipe_hash", "favorite_id"))


def _object(value: object, keys: frozenset[str], label: str) -> Mapping[str, object]:
    raw = require_object(value, label, ValueError)
    require_exact_keys(raw, keys, label)
    return raw


def _rehearsal_number(value: object, label: str) -> float:
    result = require_float(value, label, ValueError)
    if not math.isfinite(result):
        raise ValueError(f"{label} must be finite")
    return result


def _params(value: object) -> Mapping[str, int]:
    raw = require_object(value, "native parameters", ValueError)
    return MappingProxyType(
        {
            require_text(key, "parameter key"): require_int(item, "native value", ValueError)
            for key, item in raw.items()
        }
    )


def _snapshot_payload(snapshot: Snapshot) -> dict[str, object]:
    # Presentation facts are catalog-derived and are not source provenance.
    raw: dict[str, object] = dict(snapshot.to_dict())
    raw["pads"] = [
        {"pad_id": pad.pad_id, "machine": pad.machine, "params": dict(pad.params)}
        for pad in snapshot.pads
    ]
    return raw


def _snapshot(value: object) -> Snapshot:
    raw = _object(
        value,
        frozenset(("snapshot_id", "device", "captured_at", "pads", "scene_slot", "bpm")),
        "source snapshot",
    )
    pads: list[PadState] = []
    for item in require_sequence(raw["pads"], "source pads", ValueError):
        pad = _object(item, frozenset(("pad_id", "machine", "params")), "source pad")
        pads.append(
            PadState(
                require_int(pad["pad_id"], "pad_id", ValueError),
                require_text(pad["machine"], "machine", ValueError),
                _params(pad["params"]),
            )
        )
    scene = raw["scene_slot"]
    return Snapshot(
        require_text(raw["snapshot_id"], "snapshot_id", ValueError),
        require_text(raw["device"], "device", ValueError),
        datetime.fromisoformat(require_text(raw["captured_at"], "captured_at", ValueError)),
        tuple(pads),
        None if scene is None else require_text(scene, "scene_slot", ValueError),
        None if raw["bpm"] is None else _rehearsal_number(raw["bpm"], "bpm"),
    )


def _rehearsal_candidate(value: object) -> MutationCandidate:
    raw = _object(
        value,
        frozenset(
            (
                "candidate_id",
                "source_snapshot_id",
                "profile_id",
                "depth",
                "seed",
                "pad_deltas",
                "safety_status",
                "estimated_midi_msgs",
            )
        ),
        "candidate",
    )
    deltas: list[PadDelta] = []
    for item in require_sequence(raw["pad_deltas"], "pad_deltas", ValueError):
        delta = _object(item, frozenset(("pad_id", "proposed_params", "changed_keys")), "pad delta")
        keys = require_text_tuple(delta["changed_keys"], "changed_keys", ValueError)
        if len(set(keys)) != len(keys):
            raise ValueError("changed_keys must be unique")
        deltas.append(
            PadDelta(
                require_int(delta["pad_id"], "pad_id", ValueError),
                _params(delta["proposed_params"]),
                frozenset(keys),
            )
        )
    return MutationCandidate(
        require_text(raw["candidate_id"], "candidate_id", ValueError),
        require_text(raw["source_snapshot_id"], "source_snapshot_id", ValueError),
        require_text(raw["profile_id"], "profile_id", ValueError),
        _rehearsal_number(raw["depth"], "depth"),
        require_int(raw["seed"], "seed", ValueError),
        tuple(deltas),
        narrow_status(require_text(raw["safety_status"], "safety_status", ValueError)),
        require_int(raw["estimated_midi_msgs"], "estimated_midi_msgs", ValueError),
    )


def _ids(value: object, device_id: str) -> frozenset[int]:
    values = require_integer_tuple(value, "target/lock ids", ValueError)
    domain = registered_mutation_ids(device_id)
    if len(set(values)) != len(values) or not set(values) <= domain:
        raise ValueError("target/lock ids must be unique registered device ids")
    return frozenset(values)


def _digest(value: Mapping[str, object]) -> str:
    return sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class LocalRehearsalFavorite:
    """Exact source, recipe and candidate retained locally, without a send plan."""

    source_snapshot: Snapshot
    profile: ProfileModel
    candidate: MutationCandidate
    rytm_pad_targets: frozenset[int] = frozenset()
    a4_track_targets: frozenset[int] = frozenset()
    locked_pad_ids: frozenset[int] = frozenset()
    locked_a4_track_ids: frozenset[int] = frozenset()
    rytm_parameter_selection: ParameterSelection = field(default_factory=ParameterSelection)
    a4_parameter_selection: ParameterSelection = field(default_factory=ParameterSelection)

    def __post_init__(self) -> None:
        # Defensive typed copies validate direct construction as strictly as disk.
        object.__setattr__(
            self, "source_snapshot", _snapshot(_snapshot_payload(self.source_snapshot))
        )
        object.__setattr__(self, "profile", ProfileModel.from_strict_dict(self.profile.to_dict()))
        object.__setattr__(self, "candidate", _rehearsal_candidate(self.candidate.to_dict()))
        if self.source_snapshot.device not in STAGE_DEVICE_IDS:
            raise ValueError("favorite requires a supported device identity")
        for key, device_id in (
            ("rytm_pad_targets", ANALOG_RYTM_DEVICE_ID),
            ("locked_pad_ids", ANALOG_RYTM_DEVICE_ID),
            ("a4_track_targets", ANALOG_FOUR_DEVICE_ID),
            ("locked_a4_track_ids", ANALOG_FOUR_DEVICE_ID),
        ):
            object.__setattr__(self, key, _ids(tuple(getattr(self, key)), device_id))
        for key, device_id in (
            ("rytm_parameter_selection", ANALOG_RYTM_DEVICE_ID),
            ("a4_parameter_selection", ANALOG_FOUR_DEVICE_ID),
        ):
            selection = ParameterSelection.parse(getattr(self, key).to_list())
            if selection.cells is not None and any(
                cell.item_id not in registered_mutation_ids(device_id) for cell in selection.cells
            ):
                raise ValueError("favorite parameter selection is outside the device domain")
            object.__setattr__(self, key, selection)
        if self.candidate.source_snapshot_id != self.source_snapshot.snapshot_id:
            raise ValueError("favorite candidate source identity does not match")
        if self.candidate.profile_id != self.profile.profile_id:
            raise ValueError("favorite candidate profile identity does not match")
        self._validate_delta_scope()

    def _validate_delta_scope(self) -> None:
        source = {pad.pad_id: pad for pad in self.source_snapshot.pads}
        domain = registered_mutation_ids(self.source_snapshot.device)
        if not set(source) <= domain:
            raise ValueError("source pads are outside the registered device domain")
        if self.parameter_selection.cells is not None:
            for cell in self.parameter_selection.cells:
                if (
                    cell.item_id not in source
                    or cell.parameter_key not in source[cell.item_id].params
                ):
                    raise ValueError("favorite selection addresses an absent source parameter")
        effective = self.mutation_scope().effective_ids(source)
        ids = tuple(delta.pad_id for delta in self.candidate.pad_deltas)
        if ids != tuple(sorted(effective)):
            raise ValueError("favorite candidate does not match target/lock scope")
        for delta in self.candidate.pad_deltas:
            original = source[delta.pad_id].params
            if set(original) != set(delta.proposed_params):
                raise ValueError("favorite candidate parameter identities do not match source")
            changed = frozenset(
                key for key in original if original[key] != delta.proposed_params[key]
            )
            if changed != delta.changed_keys:
                raise ValueError("favorite candidate changed_keys do not match exact values")
            if any(not self.parameter_selection.includes(delta.pad_id, key) for key in changed):
                raise ValueError("favorite candidate changes an excluded parameter")

    def mutation_scope(self) -> MutationScope:
        """Canonical target-minus-lock interpretation for the source device."""
        if self.source_snapshot.device == ANALOG_RYTM_DEVICE_ID:
            return MutationScope(self.rytm_pad_targets, self.locked_pad_ids)
        return MutationScope(self.a4_track_targets, self.locked_a4_track_ids)

    @property
    def parameter_selection(self) -> ParameterSelection:
        """The source device's selection, not the partner's offline selection."""
        if self.source_snapshot.device == ANALOG_RYTM_DEVICE_ID:
            return self.rytm_parameter_selection
        return self.a4_parameter_selection

    @property
    def source_hash(self) -> str:
        """Full source provenance, including identity, timestamp and exact values."""
        return _digest(_snapshot_payload(self.source_snapshot))

    def _payload(self) -> dict[str, object]:
        return {
            "source_snapshot": _snapshot_payload(self.source_snapshot),
            "profile": self.profile.to_dict(),
            "candidate": self.candidate.to_dict(),
            "rytm_pad_targets": sorted(self.rytm_pad_targets),
            "a4_track_targets": sorted(self.a4_track_targets),
            "locked_pad_ids": sorted(self.locked_pad_ids),
            "locked_a4_track_ids": sorted(self.locked_a4_track_ids),
            "rytm_parameter_selection": self.rytm_parameter_selection.to_list(),
            "a4_parameter_selection": self.a4_parameter_selection.to_list(),
        }

    @property
    def recipe_hash(self) -> str:
        """Deterministic source/profile/scope/seed/depth identity, without ULIDs."""
        raw = self._payload()
        raw["candidate"] = {"depth": self.candidate.depth, "seed": self.candidate.seed}
        return _digest(raw)

    @property
    def favorite_id(self) -> str:
        """Content-derived library id, including exact retained candidate identity."""
        return "rehearsal_" + _digest(self._payload())

    def to_dict(self) -> dict[str, object]:
        """Canonical JSON model plus checked deterministic identities."""
        return {
            **self._payload(),
            "source_hash": self.source_hash,
            "recipe_hash": self.recipe_hash,
            "favorite_id": self.favorite_id,
        }

    @classmethod
    def from_dict(cls, value: object) -> LocalRehearsalFavorite:
        """Strictly parse and validate integrity; never round native values."""
        raw = _object(value, _FAVORITE_FIELDS | _HASH_FIELDS, "local rehearsal favorite")
        favorite = cls(
            source_snapshot=_snapshot(raw["source_snapshot"]),
            profile=ProfileModel.from_strict_dict(raw["profile"]),
            candidate=_rehearsal_candidate(raw["candidate"]),
            rytm_parameter_selection=ParameterSelection.parse(raw["rytm_parameter_selection"]),
            a4_parameter_selection=ParameterSelection.parse(raw["a4_parameter_selection"]),
            rytm_pad_targets=_ids(raw["rytm_pad_targets"], ANALOG_RYTM_DEVICE_ID),
            a4_track_targets=_ids(raw["a4_track_targets"], ANALOG_FOUR_DEVICE_ID),
            locked_pad_ids=_ids(raw["locked_pad_ids"], ANALOG_RYTM_DEVICE_ID),
            locked_a4_track_ids=_ids(raw["locked_a4_track_ids"], ANALOG_FOUR_DEVICE_ID),
        )
        for key in _HASH_FIELDS:
            if raw[key] != getattr(favorite, key):
                raise ValueError("favorite integrity identity does not match retained values")
        return favorite


__all__ = ["LocalRehearsalFavorite"]
