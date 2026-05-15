"""JSON-file profile store for the Guardrails system (WS-W Layer 3).

A :class:`ProfileStore` owns a directory of profile files (default
``~/.rytm-randomizer/profiles/``) and exposes :py:meth:`save`,
:py:meth:`load`, :py:meth:`list_profiles`, and :py:meth:`promote`.

**One profile = one JSON file.** The on-disk filename is
``<profile_name>-<content_hash[:8]>.json`` so multiple revisions of the same
profile name coexist by content hash. The file body is the canonical JSON
representation of the profile (sorted keys, no whitespace, enums collapsed to
``.value``) -- the same canonicalization :func:`compute_content_hash` uses, so
a round trip preserves the content hash.

**Lifecycle state machine.** :py:meth:`promote` only allows transitions the
spec section 4.3 state machine permits:

* ``DRAFT -> VALIDATED`` (the validator is the authority, but the store accepts
  it as a manual promotion)
* ``DRAFT -> REJECTED`` (audit trail)
* ``REJECTED -> DRAFT`` (corrected and resubmitted)
* ``VALIDATED -> STUDIO_TESTED`` (auditioned)
* ``STUDIO_TESTED -> VALIDATED`` (needs rework)
* ``STUDIO_TESTED -> LIVE_APPROVED`` (passed hardware validation)
* ``VALIDATED -> ARCHIVED`` (superseded)
* ``LIVE_APPROVED -> ARCHIVED`` (superseded)

Every other transition is rejected with
:class:`IllegalStateTransitionError`.
"""

from __future__ import annotations

import dataclasses
import json
import re
from collections.abc import Mapping
from dataclasses import is_dataclass
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from ..observability.errors import StateError
from ..observability.logging import get_logger
from .schema import (
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileState,
    Provenance,
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
)

__all__ = [
    "DEFAULT_PROFILES_DIR",
    "IllegalStateTransitionError",
    "LEGAL_STATE_TRANSITIONS",
    "ProfileStore",
]


_logger = get_logger(__name__)


DEFAULT_PROFILES_DIR: Path = Path.home() / ".rytm-randomizer" / "profiles"
"""Default on-disk profiles directory.

Created on demand by :class:`ProfileStore` (the constructor accepts an explicit
``profiles_dir`` so tests use a temp directory).
"""


LEGAL_STATE_TRANSITIONS: Mapping[ProfileState, frozenset[ProfileState]] = MappingProxyType(
    {
        ProfileState.DRAFT: frozenset({ProfileState.VALIDATED, ProfileState.REJECTED}),
        ProfileState.REJECTED: frozenset({ProfileState.DRAFT}),
        ProfileState.VALIDATED: frozenset({ProfileState.STUDIO_TESTED, ProfileState.ARCHIVED}),
        ProfileState.STUDIO_TESTED: frozenset({ProfileState.VALIDATED, ProfileState.LIVE_APPROVED}),
        ProfileState.LIVE_APPROVED: frozenset({ProfileState.ARCHIVED}),
        ProfileState.ARCHIVED: frozenset(),
    }
)
"""Spec section 4.3: which target states are reachable from each source state."""


_FILENAME_RE = re.compile(r"^[A-Za-z0-9_\-]+-[0-9a-f]{8}\.json$")
"""Allow-list pattern for profile filenames. Anything else is ignored."""


class IllegalStateTransitionError(StateError):
    """Raised when :py:meth:`ProfileStore.promote` is asked for a forbidden hop.

    A member of the
    :class:`~rytm_randomizer.observability.errors.StateError` family so
    callers can ``except StateError`` to catch every state-machine
    violation in the package uniformly.
    """


# ---------------------------------------------------------------------------
# Canonical JSON serialization
# ---------------------------------------------------------------------------


def _to_json_primitive(value: object) -> object:
    """Recursively convert a schema value into JSON primitives.

    Mirrors :func:`rytm_randomizer.guardrails.schema._to_canonical` but
    produces JSON-ready data (Enums to ``.value``, dataclasses to plain
    dicts, tuples to lists). The result is safe to pass to ``json.dumps``.

    This intentionally does **not** exclude the ``content_hash`` field --
    we serialize the WHOLE profile, including its already-computed hash,
    so a load can verify what it reads. The hash check itself is handled
    by recomputing on the way back in (see :py:meth:`ProfileStore.load`).
    """

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for f in dataclasses.fields(value):
            result[f.name] = _to_json_primitive(getattr(value, f.name))
        return result
    if isinstance(value, Mapping):
        return {str(k): _to_json_primitive(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_to_json_primitive(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"_to_json_primitive: unsupported value type {type(value).__name__!r}")


def _profile_to_canonical_json(profile: GuardrailProfile) -> str:
    """Return the canonical JSON string for ``profile``.

    The same canonicalization that :func:`compute_content_hash` uses
    (``sort_keys=True``, ``separators=(",", ":")``), so the on-disk file
    content for a profile with hash X is exactly the bytes that hashed
    to X (modulo the ``content_hash`` field itself, which we include in
    the file but exclude from the hash input).
    """

    canonical = _to_json_primitive(profile)
    return json.dumps(canonical, sort_keys=True, separators=(",", ":"))


# ---------------------------------------------------------------------------
# Canonical JSON deserialization
# ---------------------------------------------------------------------------


def _coerce_str(payload: Mapping[str, Any], key: str) -> str:
    raw = payload.get(key)
    if not isinstance(raw, str):
        raise StateError(
            f"profile JSON missing or wrong-typed string field {key!r}",
            context={"field": key, "got": type(raw).__name__},
        )
    return raw


def _coerce_tuple_of_str(payload: Mapping[str, Any], key: str) -> tuple[str, ...]:
    raw = payload.get(key)
    if not isinstance(raw, list):
        raise StateError(
            f"profile JSON missing or wrong-typed list field {key!r}",
            context={"field": key, "got": type(raw).__name__},
        )
    if not all(isinstance(x, str) for x in raw):
        raise StateError(
            f"profile JSON {key!r} contains a non-string entry",
            context={"field": key},
        )
    return tuple(raw)


def _coerce_tuple_of_int(payload: Mapping[str, Any], key: str) -> tuple[int, ...]:
    raw = payload.get(key)
    if not isinstance(raw, list):
        raise StateError(
            f"profile JSON missing or wrong-typed list field {key!r}",
            context={"field": key, "got": type(raw).__name__},
        )
    if not all(isinstance(x, int) for x in raw):
        raise StateError(
            f"profile JSON {key!r} contains a non-int entry",
            context={"field": key},
        )
    return tuple(raw)


def _provenance_from_json(payload: Mapping[str, Any]) -> Provenance:
    return Provenance(
        profile_name=_coerce_str(payload, "profile_name"),
        source_type=SourceType(_coerce_str(payload, "source_type")),
        confidence=Confidence(_coerce_str(payload, "confidence")),
        feature_report_hash=_coerce_str(payload, "feature_report_hash"),
        derived_at=_coerce_str(payload, "derived_at"),
    )


def _character_from_json(payload: Mapping[str, Any]) -> MusicalCharacter:
    bpm_low, bpm_high = _coerce_tuple_of_int(payload, "bpm_range")
    findings_raw = payload.get("musical_findings", {})
    if not isinstance(findings_raw, Mapping):
        raise StateError(
            "profile JSON musical_findings must be an object",
            context={"got": type(findings_raw).__name__},
        )
    findings = {str(k): str(v) for k, v in findings_raw.items()}
    return MusicalCharacter(
        style_tags=_coerce_tuple_of_str(payload, "style_tags"),
        bpm_range=(bpm_low, bpm_high),
        energy_profile=_coerce_str(payload, "energy_profile"),
        density_profile=_coerce_str(payload, "density_profile"),
        musical_findings=findings,
    )


def _role_mapping_from_json(payload: Mapping[str, Any]) -> RoleMapping:
    assignments_raw = payload.get("assignments", {})
    if not isinstance(assignments_raw, Mapping):
        raise StateError(
            "profile JSON role_mapping.assignments must be an object",
            context={"got": type(assignments_raw).__name__},
        )
    parsed: dict[int, RoleAssignment] = {}
    for k, entry in assignments_raw.items():
        if not isinstance(entry, Mapping):
            raise StateError(
                "profile JSON role_mapping entry must be an object",
                context={"key": k, "got": type(entry).__name__},
            )
        parsed[int(k)] = RoleAssignment(
            role=_coerce_str(entry, "role"),
            mutation_direction=_coerce_str(entry, "mutation_direction"),
        )
    return RoleMapping(assignments=parsed)


def _bound_from_json(payload: Mapping[str, Any]) -> GuardrailBound:
    pad = payload.get("pad")
    low = payload.get("low")
    high = payload.get("high")
    if not isinstance(pad, int) or not isinstance(low, int) or not isinstance(high, int):
        raise StateError(
            "profile JSON GuardrailBound pad/low/high must be integers",
            context={"got": payload},
        )
    return GuardrailBound(
        pad=pad,
        parameter=_coerce_str(payload, "parameter"),
        low=low,
        high=high,
        guardrail_class=GuardrailClass(_coerce_str(payload, "guardrail_class")),
        direction=_coerce_str(payload, "direction"),
    )


def _scene_from_json(payload: Mapping[str, Any]) -> SceneGuardrail:
    return SceneGuardrail(
        scene_key=_coerce_str(payload, "scene_key"),
        pads_allowed=_coerce_tuple_of_int(payload, "pads_allowed"),
        mutation_depth=_coerce_str(payload, "mutation_depth"),
        risk_class=GuardrailClass(_coerce_str(payload, "risk_class")),
        locked_roles=_coerce_tuple_of_str(payload, "locked_roles"),
    )


def _profile_from_json(payload: Mapping[str, Any]) -> GuardrailProfile:
    """Rebuild a :class:`GuardrailProfile` from its canonical JSON payload."""

    if not isinstance(payload, Mapping):
        raise StateError(
            "profile JSON top-level must be an object",
            context={"got": type(payload).__name__},
        )

    bounds_raw = payload.get("bounds")
    if not isinstance(bounds_raw, list):
        raise StateError(
            "profile JSON bounds must be a list",
            context={"got": type(bounds_raw).__name__},
        )
    scenes_raw = payload.get("scenes")
    if not isinstance(scenes_raw, list):
        raise StateError(
            "profile JSON scenes must be a list",
            context={"got": type(scenes_raw).__name__},
        )

    provenance_raw = payload.get("provenance")
    if not isinstance(provenance_raw, Mapping):
        raise StateError(
            "profile JSON provenance must be an object",
            context={"got": type(provenance_raw).__name__},
        )
    character_raw = payload.get("character")
    if not isinstance(character_raw, Mapping):
        raise StateError(
            "profile JSON character must be an object",
            context={"got": type(character_raw).__name__},
        )
    role_raw = payload.get("role_mapping")
    if not isinstance(role_raw, Mapping):
        raise StateError(
            "profile JSON role_mapping must be an object",
            context={"got": type(role_raw).__name__},
        )

    return GuardrailProfile(
        provenance=_provenance_from_json(provenance_raw),
        character=_character_from_json(character_raw),
        role_mapping=_role_mapping_from_json(role_raw),
        bounds=tuple(_bound_from_json(b) for b in bounds_raw),
        locked_default=_coerce_tuple_of_str(payload, "locked_default"),
        forbidden=_coerce_tuple_of_str(payload, "forbidden"),
        scenes=tuple(_scene_from_json(s) for s in scenes_raw),
        state=ProfileState(_coerce_str(payload, "state")),
        schema_version=_coerce_str(payload, "schema_version"),
        content_hash=_coerce_str(payload, "content_hash"),
    )


# ---------------------------------------------------------------------------
# The store
# ---------------------------------------------------------------------------


class ProfileStore:
    """A directory of JSON-on-disk Guardrail Profiles.

    The store does not enforce validation -- callers should pass profiles
    through :func:`~rytm_randomizer.guardrails.validation.validate` before
    saving. The store is responsible for: durable persistence, deterministic
    filenames, schema-version filtering, and the lifecycle state machine in
    :py:meth:`promote`.
    """

    def __init__(self, profiles_dir: Path | None = None) -> None:
        self._dir: Path = profiles_dir if profiles_dir is not None else DEFAULT_PROFILES_DIR

    @property
    def profiles_dir(self) -> Path:
        """The on-disk directory this store manages (read-only attribute)."""

        return self._dir

    @staticmethod
    def _filename_for(profile: GuardrailProfile) -> str:
        """Return ``<profile_name>-<content_hash[:8]>.json``.

        The slug uses only ``A-Za-z0-9_-`` (other characters become ``_``) so
        the filename is portable across filesystems. The 8-char prefix of the
        content hash is enough to discriminate sibling files; collisions on
        the same content hash are a no-op (idempotent save).
        """

        slug = re.sub(r"[^A-Za-z0-9_\-]", "_", profile.provenance.profile_name)
        return f"{slug}-{profile.content_hash[:8]}.json"

    def save(self, profile: GuardrailProfile) -> Path:
        """Write ``profile`` to disk and return its file path.

        The directory is created on demand. The write is atomic-enough for
        this use case (the operator owns the directory; the file is
        rewritten in one ``write_text`` call). Returns the path so callers
        can chain (e.g. a save-then-promote-then-resave loop).
        """

        if not profile.content_hash:
            raise StateError(
                "cannot save a profile without a content_hash",
                context={"profile_name": profile.provenance.profile_name},
            )

        self._dir.mkdir(parents=True, exist_ok=True)
        path = self._dir / self._filename_for(profile)
        path.write_text(
            _profile_to_canonical_json(profile),
            encoding="utf-8",
        )

        _logger.info(
            "guardrails.store.save",
            extra={
                "kind": "guardrails_store_save",
                "path": str(path),
                "profile_name": profile.provenance.profile_name,
                "state": profile.state.value,
                "content_hash": profile.content_hash,
            },
        )
        return path

    def load(self, path: Path) -> GuardrailProfile:
        """Read ``path`` and reconstruct the profile.

        Verifies that the on-disk ``content_hash`` matches what the
        canonical canonicalizer recomputes -- a mismatch surfaces as a
        :class:`StateError` because the file is either tampered with or
        was written under a different schema.
        """

        payload_str = path.read_text(encoding="utf-8")
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError as exc:
            raise StateError(
                "profile JSON is not parseable",
                context={"path": str(path), "decode_error": str(exc)},
            ) from exc

        profile = _profile_from_json(payload)

        # Recompute hash on the rebuilt profile (with content_hash zeroed)
        # to verify integrity. If the file was hand-edited so the content
        # changed but the hash field did not, this catches it.
        recomputed = compute_content_hash(dataclasses.replace(profile, content_hash=""))
        if recomputed != profile.content_hash:
            raise StateError(
                "profile content_hash does not match recomputed digest",
                context={
                    "path": str(path),
                    "stored": profile.content_hash,
                    "recomputed": recomputed,
                },
            )

        return profile

    def list_profiles(self) -> list[Path]:
        """Return every profile file in the directory, sorted and deduplicated.

        Only files matching :data:`_FILENAME_RE` and whose ``schema_version``
        equals :data:`SCHEMA_VERSION` are returned. Files for an unknown
        schema version are silently skipped so a tooling upgrade does not
        crash on legacy artifacts.
        """

        if not self._dir.is_dir():
            return []
        seen: set[Path] = set()
        result: list[Path] = []
        for path in sorted(self._dir.iterdir()):
            if not path.is_file():
                continue
            if not _FILENAME_RE.match(path.name):
                continue
            # Filter by schema_version: read only enough to extract the field.
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            if not isinstance(payload, Mapping):
                continue
            if payload.get("schema_version") != SCHEMA_VERSION:
                continue
            if path in seen:  # pragma: no cover - defensive; iterdir() is unique
                continue
            seen.add(path)
            result.append(path)
        return result

    @staticmethod
    def promote(profile: GuardrailProfile, new_state: ProfileState) -> GuardrailProfile:
        """Return a new profile with ``state`` updated to ``new_state``.

        Raises :class:`IllegalStateTransitionError` (a member of
        :class:`~rytm_randomizer.observability.errors.StateError`) when the
        transition is not in :data:`LEGAL_STATE_TRANSITIONS`. ``content_hash``
        is recomputed because state is part of the hash input.
        """

        allowed = LEGAL_STATE_TRANSITIONS.get(profile.state, frozenset())
        if new_state not in allowed:
            raise IllegalStateTransitionError(
                "illegal profile state transition",
                context={
                    "from_state": profile.state.value,
                    "to_state": new_state.value,
                    "allowed": sorted(s.value for s in allowed),
                },
            )

        promoted = dataclasses.replace(profile, state=new_state, content_hash="")
        digest = compute_content_hash(promoted)
        promoted = dataclasses.replace(promoted, content_hash=digest)

        _logger.info(
            "guardrails.store.promote",
            extra={
                "kind": "guardrails_store_promote",
                "profile_name": profile.provenance.profile_name,
                "from_state": profile.state.value,
                "to_state": new_state.value,
                "content_hash": digest,
            },
        )
        return promoted
