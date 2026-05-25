"""Frozen dataclasses + pure state transitions for the Profile Wizard.

Three dataclasses, all ``frozen=True``:

* :class:`InspirationSource` — one thing the operator wants the analyzer to
  look at (a kit file, a folder of audio, an artist name, etc.).
* :class:`AnalysisJob` — the analyzer's progress and result for one source.
* :class:`WizardState` — the whole wizard session: which step the operator
  is on, the current name/description, the tuples of sources + jobs, and
  (once analysis finishes) the candidate :class:`ProfileModel`.

Every state-transition helper on :class:`WizardState` is **pure**: it
returns a NEW :class:`WizardState` and never mutates ``self``. The wizard
is therefore safe to share across coroutines, render in React without
hidden aliasing, and snapshot for undo.

All three dataclasses round-trip losslessly through ``to_dict`` /
``from_dict`` so the WebSocket Protocol (WS-D) can serialize them without
re-implementing the shape.

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"Core data abstractions" for the authoritative shape.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Final, Literal, Self, TypedDict, cast

from ..data.profile_model import ProfileModel, ProfileModelDict, StyleTrait, StyleTraitDict
from ..data.types import _safe_repr

# ---------------------------------------------------------------------------
# Literal types + Final runtime tuples (Gate 10: single source of truth per enum)
# ---------------------------------------------------------------------------

Kind = Literal["kit", "sound", "song", "album", "artist"]
"""What musical concept an :class:`InspirationSource` represents."""

KIND_VALUES: Final[tuple[Kind, ...]] = ("kit", "sound", "song", "album", "artist")
"""Runtime tuple of every :data:`Kind` literal (spec-declaration order)."""

Mode = Literal["file", "folder", "reference"]
"""How the analyzer should reach the source: a file path, a folder path,
or a free-text reference (artist name, album name, song title)."""

MODE_VALUES: Final[tuple[Mode, ...]] = ("file", "folder", "reference")
"""Runtime tuple of every :data:`Mode` literal."""

Status = Literal["pending", "analyzing", "ok", "failed"]
""":class:`AnalysisJob` lifecycle: queued, running, finished OK, or errored."""

STATUS_VALUES: Final[tuple[Status, ...]] = ("pending", "analyzing", "ok", "failed")
"""Runtime tuple of every :data:`Status` literal."""

Step = Literal["name", "add", "analyze", "review"]
"""Which step of the wizard the operator is currently on."""

STEP_VALUES: Final[tuple[Step, ...]] = ("name", "add", "analyze", "review")
"""Runtime tuple of every :data:`Step` literal (advance order)."""


# ---------------------------------------------------------------------------
# Narrowing helpers — earn the wire-side Literal at runtime, then cast.
# ---------------------------------------------------------------------------


def narrow_kind(s: str) -> Kind:
    """Narrow ``s`` to wizard :data:`Kind` or raise :class:`ValueError`.

    Mirrors :func:`rytm_randomizer.cockpit.data.types.narrow_kind` for the
    wizard's own :data:`Kind` alias (which uses a different value set —
    ``"kit"`` / ``"sound"`` / ``"song"`` / ``"album"`` / ``"artist"`` vs.
    the data-layer ``"scene"`` / ``"user"``).
    """

    if s in KIND_VALUES:
        return cast(Kind, s)
    raise ValueError(f"invalid kind: {_safe_repr(s)}; expected one of {KIND_VALUES}")


def narrow_mode(s: str) -> Mode:
    """Narrow ``s`` to :data:`Mode` or raise :class:`ValueError`."""

    if s in MODE_VALUES:
        return cast(Mode, s)
    raise ValueError(f"invalid mode: {_safe_repr(s)}; expected one of {MODE_VALUES}")


def narrow_status(s: str) -> Status:
    """Narrow ``s`` to wizard :data:`Status` or raise :class:`ValueError`."""

    if s in STATUS_VALUES:
        return cast(Status, s)
    raise ValueError(f"invalid status: {_safe_repr(s)}; expected one of {STATUS_VALUES}")


def narrow_step(s: str) -> Step:
    """Narrow ``s`` to :data:`Step` or raise :class:`ValueError`."""

    if s in STEP_VALUES:
        return cast(Step, s)
    raise ValueError(f"invalid step: {_safe_repr(s)}; expected one of {STEP_VALUES}")


# ---------------------------------------------------------------------------
# Wire-shape TypedDicts (M1/P2 — explicit dict shapes for callers + IDEs)
#
# Literal-valued fields (``kind`` / ``mode`` / ``status`` / ``step``) are
# typed as plain ``str`` because the wire layer may receive any string —
# runtime narrowing in each ``from_dict`` is the validation boundary.
# ---------------------------------------------------------------------------


class InspirationSourceDict(TypedDict):
    """Wire shape of :class:`InspirationSource`."""

    source_id: str
    kind: str
    mode: str
    location: str
    display_name: str
    added_at: str  # ISO 8601


class AnalysisJobDict(TypedDict):
    """Wire shape of :class:`AnalysisJob`."""

    source_id: str
    status: str
    progress: float
    error: str | None
    extracted_traits: list[StyleTraitDict]


class WizardStateDict(TypedDict):
    """Wire shape of :class:`WizardState`."""

    wizard_id: str
    step: str
    name: str | None
    description: str | None
    sources: list[InspirationSourceDict]
    jobs: list[AnalysisJobDict]
    candidate_profile: ProfileModelDict | None


# ---------------------------------------------------------------------------
# InspirationSource
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class InspirationSource:
    """One thing the operator wants the analyzer to consider.

    Sources are typed (:data:`Kind`) AND addressed (:data:`Mode`):

    * a Surgeon kit dump is ``kind="kit"`` + ``mode="file"``,
    * a folder of techno WAVs is ``kind="song"`` + ``mode="folder"``,
    * just typing "Surgeon" is ``kind="artist"`` + ``mode="reference"``.

    ``source_id`` is a ULID assigned at construction (the WS handler
    generates it via :func:`~rytm_randomizer.cockpit.data.ulid.new_ulid`).
    The wizard keys :class:`AnalysisJob` instances by ``source_id``, so
    every source has at most one job at a time.
    """

    source_id: str
    kind: Kind
    mode: Mode
    location: str
    display_name: str
    added_at: datetime

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if self.kind not in KIND_VALUES:
            raise ValueError(f"kind must be one of {KIND_VALUES}; got {self.kind!r}")
        if self.mode not in MODE_VALUES:
            raise ValueError(f"mode must be one of {MODE_VALUES}; got {self.mode!r}")
        if not self.location:
            raise ValueError("location must be a non-empty string")
        if not self.display_name:
            raise ValueError("display_name must be a non-empty string")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "kind": self.kind,
            "mode": self.mode,
            "location": self.location,
            "display_name": self.display_name,
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        return cls(
            source_id=str(data["source_id"]),
            kind=narrow_kind(str(data["kind"])),
            mode=narrow_mode(str(data["mode"])),
            location=str(data["location"]),
            display_name=str(data["display_name"]),
            added_at=datetime.fromisoformat(str(data["added_at"])),
        )


# ---------------------------------------------------------------------------
# AnalysisJob
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AnalysisJob:
    """Per-source analyzer progress + result snapshot.

    Lifecycle (Status): ``"pending"`` → ``"analyzing"`` → ``"ok"`` (or
    ``"failed"``). ``progress`` is a unit-interval float so the React
    progress bar can render without re-normalizing. ``error`` is populated
    only when ``status == "failed"``; ``extracted_traits`` is populated
    only when ``status == "ok"``.

    Every job references its :class:`InspirationSource` by ``source_id``;
    :meth:`WizardState.with_job_update` looks the job up by that key.
    """

    source_id: str
    status: Status
    progress: float
    error: str | None
    extracted_traits: tuple[StyleTrait, ...]

    def __post_init__(self) -> None:
        if not self.source_id:
            raise ValueError("source_id must be a non-empty string")
        if self.status not in STATUS_VALUES:
            raise ValueError(f"status must be one of {STATUS_VALUES}; got {self.status!r}")
        if self.progress < 0.0 or self.progress > 1.0:
            raise ValueError(f"progress must lie in [0.0, 1.0]; got {self.progress}")

    def to_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "status": self.status,
            "progress": self.progress,
            "error": self.error,
            "extracted_traits": [t.to_dict() for t in self.extracted_traits],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        traits_obj = data["extracted_traits"]
        if not isinstance(traits_obj, (list, tuple)):
            raise TypeError(
                f"extracted_traits must be a list/tuple; got {type(traits_obj).__name__}"
            )
        error_obj = data["error"]
        return cls(
            source_id=str(data["source_id"]),
            status=narrow_status(str(data["status"])),
            progress=float(data["progress"]),  # type: ignore[arg-type]
            error=None if error_obj is None else str(error_obj),
            extracted_traits=tuple(StyleTrait.from_dict(t) for t in traits_obj),
        )


# ---------------------------------------------------------------------------
# WizardState — the session itself + pure state-transition helpers
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class WizardState:
    """The whole wizard session at a point in time.

    ``wizard_id`` is the ULID the WS handler assigned at :meth:`empty` time
    and which clients echo back on every subsequent command. ``step``
    tracks the operator's current position (one of :data:`STEP_VALUES`).
    ``name`` and ``description`` are populated on the ``"name"`` step.
    ``sources`` accumulates on the ``"add"`` step; ``jobs`` are created on
    add (status ``"pending"``) and updated during ``"analyze"``.
    ``candidate_profile`` is set when the wizard reaches ``"review"`` (the
    :class:`ProfileBuilder` produces it; this layer just holds the result).

    Every transition helper returns a NEW :class:`WizardState`; the input
    instance is never mutated, so callers can keep prior states for undo /
    history without defensive copies.
    """

    wizard_id: str
    step: Step
    name: str | None
    description: str | None
    sources: tuple[InspirationSource, ...]
    jobs: tuple[AnalysisJob, ...]
    candidate_profile: ProfileModel | None

    def __post_init__(self) -> None:
        if not self.wizard_id:
            raise ValueError("wizard_id must be a non-empty string")
        if self.step not in STEP_VALUES:
            raise ValueError(f"step must be one of {STEP_VALUES}; got {self.step!r}")

    # -- Factories -----------------------------------------------------------

    @classmethod
    def empty(cls, wizard_id: str) -> Self:
        """Construct a fresh wizard session at step ``"name"`` with no content."""

        return cls(
            wizard_id=wizard_id,
            step="name",
            name=None,
            description=None,
            sources=(),
            jobs=(),
            candidate_profile=None,
        )

    # -- Pure state transitions ---------------------------------------------

    def with_metadata(
        self,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Self:
        """Return a copy with ``name`` and/or ``description`` overwritten.

        Both arguments default to ``None`` meaning "leave the current value
        unchanged". To explicitly clear a field, pass an empty string —
        downstream renderers treat ``""`` as cleared (a non-empty string
        means a real value).
        """

        new_name = self.name if name is None else name
        new_description = self.description if description is None else description
        return _replace(
            self,
            name=new_name,
            description=new_description,
        )

    def advance_step(self) -> Self:
        """Return a copy advanced one step along :data:`STEP_VALUES`.

        ``"name"`` → ``"add"`` → ``"analyze"`` → ``"review"``. Raising at
        the final boundary (instead of silently returning ``self``) makes
        the WS handler's bug visible — the operator should never be able
        to advance past the review step.
        """

        idx = STEP_VALUES.index(self.step)
        if idx == len(STEP_VALUES) - 1:
            raise ValueError(f"cannot advance past the final step {self.step!r}")
        return _replace(self, step=STEP_VALUES[idx + 1])

    def with_source(self, source: InspirationSource) -> Self:
        """Append ``source`` + create its pending :class:`AnalysisJob`.

        Raises ``ValueError`` if a source with the same ``source_id`` is
        already present — the wizard treats ``source_id`` as the unique
        key. (Re-adding the same source means the WS handler generated a
        duplicate ULID, which is a bug.)
        """

        if any(existing.source_id == source.source_id for existing in self.sources):
            raise ValueError(f"source_id {source.source_id!r} is already present")
        pending_job = AnalysisJob(
            source_id=source.source_id,
            status="pending",
            progress=0.0,
            error=None,
            extracted_traits=(),
        )
        return _replace(
            self,
            sources=self.sources + (source,),
            jobs=self.jobs + (pending_job,),
        )

    def without_source(self, source_id: str) -> Self:
        """Return a copy with the source AND its job for ``source_id`` removed.

        Raises ``ValueError`` if no source matches — the WS handler should
        validate this against the current state before forwarding the
        command.
        """

        if not any(s.source_id == source_id for s in self.sources):
            raise ValueError(f"source_id {source_id!r} is not present")
        new_sources = tuple(s for s in self.sources if s.source_id != source_id)
        new_jobs = tuple(j for j in self.jobs if j.source_id != source_id)
        return _replace(self, sources=new_sources, jobs=new_jobs)

    def with_job_update(self, job: AnalysisJob) -> Self:
        """Return a copy with the matching job replaced.

        The replacement is keyed by ``job.source_id``. Raises
        ``ValueError`` if no job with that ``source_id`` exists; the
        analyzer should never report progress for a removed source.
        """

        if not any(existing.source_id == job.source_id for existing in self.jobs):
            raise ValueError(f"no job present for source_id {job.source_id!r}")
        new_jobs = tuple(
            job if existing.source_id == job.source_id else existing for existing in self.jobs
        )
        return _replace(self, jobs=new_jobs)

    def with_candidate(self, profile: ProfileModel) -> Self:
        """Return a copy with ``candidate_profile`` set.

        The :class:`ProfileBuilder` calls this on transition into the
        ``"review"`` step. The wizard caller is responsible for advancing
        the step itself (review-state validation lives at a higher layer).
        """

        return _replace(self, candidate_profile=profile)

    # -- Serialization ------------------------------------------------------

    def to_dict(self) -> dict[str, object]:
        return {
            "wizard_id": self.wizard_id,
            "step": self.step,
            "name": self.name,
            "description": self.description,
            "sources": [s.to_dict() for s in self.sources],
            "jobs": [j.to_dict() for j in self.jobs],
            "candidate_profile": (
                None if self.candidate_profile is None else self.candidate_profile.to_dict()
            ),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> Self:
        sources_obj = data["sources"]
        jobs_obj = data["jobs"]
        if not isinstance(sources_obj, (list, tuple)):
            raise TypeError(f"sources must be a list/tuple; got {type(sources_obj).__name__}")
        if not isinstance(jobs_obj, (list, tuple)):
            raise TypeError(f"jobs must be a list/tuple; got {type(jobs_obj).__name__}")
        name_obj = data["name"]
        description_obj = data["description"]
        candidate_obj = data["candidate_profile"]
        if candidate_obj is None:
            candidate_profile: ProfileModel | None = None
        elif isinstance(candidate_obj, Mapping):
            candidate_profile = ProfileModel.from_dict(candidate_obj)
        else:
            raise TypeError(
                "candidate_profile must be None or a Mapping; "
                f"got {type(candidate_obj).__name__}"
            )
        return cls(
            wizard_id=str(data["wizard_id"]),
            step=narrow_step(str(data["step"])),
            name=None if name_obj is None else str(name_obj),
            description=None if description_obj is None else str(description_obj),
            sources=tuple(InspirationSource.from_dict(s) for s in sources_obj),
            jobs=tuple(AnalysisJob.from_dict(j) for j in jobs_obj),
            candidate_profile=candidate_profile,
        )


# ---------------------------------------------------------------------------
# Internal helper: dataclasses.replace bound to the concrete WizardState type
# ---------------------------------------------------------------------------


def _replace(state: WizardState, **changes: object) -> WizardState:
    """Wrap :func:`dataclasses.replace` so the return type stays concrete.

    Using ``dataclasses.replace`` directly here means ``mypy`` resolves the
    return type to ``WizardState`` (matching the ``Self``-annotated helpers
    above without contaminating each call site with a cast).
    """

    from dataclasses import replace as _dc_replace

    return _dc_replace(state, **changes)  # type: ignore[arg-type]


__all__ = [
    "AnalysisJob",
    "AnalysisJobDict",
    "InspirationSource",
    "InspirationSourceDict",
    "KIND_VALUES",
    "Kind",
    "MODE_VALUES",
    "Mode",
    "STATUS_VALUES",
    "STEP_VALUES",
    "Status",
    "Step",
    "WizardState",
    "WizardStateDict",
    "narrow_kind",
    "narrow_mode",
    "narrow_status",
    "narrow_step",
]
