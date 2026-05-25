"""ProfileBuilder — aggregate per-source analysis traits into one ProfileModel.

The :class:`ProfileBuilder` is the third leg of the Profile Wizard
(Phase 2, WS-C): WS-A produced the dataclasses that carry analyzer
output, WS-B turned an :class:`InspirationSource` into a tuple of
:class:`StyleTrait` s, and this module folds N such tuples into the
single deployable :class:`ProfileModel` the operator sees on the wizard's
"review" step.

The aggregation strategy is intentionally tiny for Phase 2:

* Only jobs whose ``status == "ok"`` contribute (pending / analyzing /
  failed jobs are silently ignored — they're either incomplete or
  surfaced as errors in the wizard UI separately).
* For each unique ``StyleTrait.name`` produced by any contributing job,
  the candidate profile's trait value is the **arithmetic mean** of every
  per-job value for that name. So three jobs producing
  ``rolling_low_end=0.5`` / ``0.7`` / ``0.9`` collapse to a single trait
  with ``value=0.7``. (A trait that only one job produced ends up with
  that one job's value verbatim.)
* ``pad_mappings`` are derived from :data:`TRAIT_TO_PAD` — each averaged
  trait whose name lives in the mapping gets one
  :class:`TraitPadWeight` whose ``weight`` is the averaged ``value``.
  Trait names not in :data:`TRAIT_TO_PAD` are silently dropped from
  ``pad_mappings`` (the trait itself still appears on the profile so the
  wizard's review step can show it).
* ``source_summary`` is the human-readable count line the review-step UI
  renders: ``"<N> sources · <M> analyzed signals"`` where ``N`` is the
  number of contributing OK jobs and ``M`` is the total count of
  per-job :class:`StyleTrait` instances summed across those jobs.

Edge cases:

* No OK jobs (empty tuple, all failed, all pending, …) → raises
  :class:`EmptyAnalysisError`. The wizard UI should refuse to advance to
  the review step when this is the case, but :func:`build_profile`
  validates the precondition defensively so misordered calls fail loudly.
* A contributing job with an empty ``extracted_traits`` tuple is counted
  toward ``N`` in ``source_summary`` but contributes nothing to the
  trait average. This matches the analyzer contract — a job can finish
  ``"ok"`` with zero traits when the source genuinely yielded no
  signal (e.g. a one-second silent clip).

The output :class:`ProfileModel` always has:

* ``kind == "user"`` (vs. the built-in ``"scene"`` profiles),
* ``model_version == "1.0.0"`` (re-analysis bumps the patch level
  outside this function — Phase 2 only writes initial versions),
* ``transition_curve == "progressive"`` (the default mutation shape),
* ``profile_id`` set via :func:`new_ulid` — every call produces a fresh
  id so two builds from identical input still get distinct ids.

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"ProfileBuilder" for the authoritative shape.
"""

from __future__ import annotations

from typing import Final

from ...observability.errors import DataError
from ...observability.logging import get_logger
from ..data.profile_model import ProfileModel, StyleTrait, TraitPadWeight
from ..data.types import Kind, TransitionCurve
from ..data.ulid import new_ulid
from .pad_mapping import TRAIT_TO_PAD
from .state import AnalysisJob

_logger = get_logger(__name__)
"""Module logger for the wizard ProfileBuilder. Bound here so future
structured log calls (per-build trait-aggregation breadcrumbs,
EmptyAnalysisError context) can land in the package's structured stream
without touching this file's imports. See ``OBSERVABILITY_REVIEW.md``
Phase 5."""

# ---------------------------------------------------------------------------
# Constants — the Phase 2 fixed-version contract
# ---------------------------------------------------------------------------

_MODEL_VERSION: Final[str] = "1.0.0"
"""Initial-build model version. Re-analysis bumps the patch level upstream."""

_PROFILE_KIND: Final[Kind] = "user"
"""Every wizard-built profile is a user profile (vs. developer-curated scenes).

Typed as :data:`Kind` (not bare ``str``) so the type checker accepts the
:class:`ProfileModel.kind` field assignment below without a
``# type: ignore`` — the literal-string ``"user"`` is statically a member
of the :data:`Kind` alias.
"""

_TRANSITION_CURVE: Final[TransitionCurve] = "progressive"
"""Default mutation transition shape for user-authored profiles.

Typed as :data:`TransitionCurve` (not bare ``str``) for the same reason
as :data:`_PROFILE_KIND` — the literal value is statically a member of
the alias, so no cast / type-ignore is needed at the call site.
"""

_OK_STATUS: Final[str] = "ok"
"""Only :class:`AnalysisJob` instances with this status contribute traits."""


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class EmptyAnalysisError(DataError, ValueError):
    """Raised when :func:`build_profile` receives no contributing OK jobs.

    Multi-inheritance via :class:`DataError` (the RytmRandomizerError
    taxonomy branch for missing / malformed data) AND :class:`ValueError`
    (stdlib) means:

    * ``except ValueError:`` callers continue to work without import changes
      (idiomatic Python validation-error handling);
    * The observability conformance test
      (``tests/architecture/test_observability.py``) recognises the raise as
      a taxonomy member, satisfying the per-PR check that every package
      ``raise`` either uses the taxonomy or an allowlisted stdlib class.

    Mirrors :class:`rytm_randomizer.cockpit.wizard.errors.
    WizardSourcePathError`, which uses the same dual-inheritance pattern.
    """


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_profile(
    name: str,
    description: str | None,
    jobs: tuple[AnalysisJob, ...],
) -> ProfileModel:
    """Aggregate per-source :class:`AnalysisJob` traits into one :class:`ProfileModel`.

    Only jobs with ``status == "ok"`` contribute (pending / analyzing /
    failed are ignored). For each unique
    :class:`StyleTrait.name <StyleTrait>` across all contributing jobs,
    the trait's value on the output profile is the arithmetic mean of
    every per-job value for that name. Trait names that appear in
    :data:`TRAIT_TO_PAD` additionally produce one
    :class:`TraitPadWeight` whose ``weight`` is the averaged value.

    Args:
        name: Operator-supplied profile name (passes through verbatim;
            :class:`ProfileModel`'s validator rejects empty strings).
        description: Optional operator-supplied description. Not stored
            on the :class:`ProfileModel` directly (the dataclass has no
            description field) — this argument is accepted for API
            symmetry with the wizard handler and for forward
            compatibility when a description field lands.
        jobs: Every :class:`AnalysisJob` the wizard collected, OK or
            not. Pass the wizard's full job tuple; the function filters
            to OK internally.

    Returns:
        A fresh :class:`ProfileModel` with ``kind="user"``,
        ``model_version="1.0.0"``, ``transition_curve="progressive"``,
        a unique ULID ``profile_id``, the averaged ``traits``, the
        :data:`TRAIT_TO_PAD`-derived ``pad_mappings``, and a human-readable
        ``source_summary``.

    Raises:
        EmptyAnalysisError: If no job in ``jobs`` has ``status == "ok"``.
    """

    del description  # accepted for API symmetry; no ProfileModel field today.

    ok_jobs = tuple(job for job in jobs if job.status == _OK_STATUS)
    if not ok_jobs:
        raise EmptyAnalysisError(
            "build_profile requires at least one job with status='ok'; "
            f"got {len(jobs)} job(s), none ok"
        )

    averaged = _average_traits(ok_jobs)
    traits = tuple(StyleTrait(name=trait_name, value=value) for trait_name, value in averaged)
    pad_mappings = tuple(
        TraitPadWeight(trait=trait_name, pad_id=TRAIT_TO_PAD[trait_name], weight=value)
        for trait_name, value in averaged
        if trait_name in TRAIT_TO_PAD
    )
    source_summary = _format_source_summary(ok_jobs)

    return ProfileModel(
        profile_id=new_ulid(),
        name=name,
        kind=_PROFILE_KIND,
        model_version=_MODEL_VERSION,
        traits=traits,
        pad_mappings=pad_mappings,
        transition_curve=_TRANSITION_CURVE,
        source_summary=source_summary,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _average_traits(ok_jobs: tuple[AnalysisJob, ...]) -> tuple[tuple[str, float], ...]:
    """Return ``((trait_name, mean_value), ...)`` averaged across ``ok_jobs``.

    Trait order in the output follows first-seen order across the input
    jobs (so the wizard's review-step UI renders traits in a stable
    operator-visible order rather than a hash-order shuffle).

    Pure: same inputs → same outputs; no hidden state, no I/O.
    """

    sums: dict[str, float] = {}
    counts: dict[str, int] = {}
    order: list[str] = []
    for job in ok_jobs:
        for trait in job.extracted_traits:
            if trait.name not in counts:
                order.append(trait.name)
                sums[trait.name] = 0.0
                counts[trait.name] = 0
            sums[trait.name] += trait.value
            counts[trait.name] += 1
    return tuple((trait_name, sums[trait_name] / counts[trait_name]) for trait_name in order)


def _format_source_summary(ok_jobs: tuple[AnalysisJob, ...]) -> str:
    """Format the ``"<N> sources · <M> analyzed signals"`` line.

    ``N`` is the count of contributing OK jobs (the caller has already
    filtered to OK only); ``M`` is the total per-job
    :class:`StyleTrait` count summed across those jobs.
    """

    signal_count = sum(len(job.extracted_traits) for job in ok_jobs)
    return f"{len(ok_jobs)} sources · {signal_count} analyzed signals"


__all__ = ["EmptyAnalysisError", "build_profile"]
