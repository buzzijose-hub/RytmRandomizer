"""Tests for ``rytm_randomizer.cockpit.wizard.builder`` — ProfileBuilder (WS-C).

:func:`build_profile` aggregates per-source :class:`AnalysisJob` traits into
one :class:`ProfileModel`. Per spec:

* Only jobs whose ``status == "ok"`` contribute traits; pending / analyzing
  / failed jobs are silently skipped.
* Each unique :class:`StyleTrait.name` across contributing jobs is collapsed
  into one trait whose ``value`` is the arithmetic mean of per-job values.
* ``pad_mappings`` are derived from :data:`TRAIT_TO_PAD`; trait names not in
  the mapping are dropped from ``pad_mappings`` but still appear in
  ``traits``.
* No OK jobs → :class:`EmptyAnalysisError` (subclass of :class:`ValueError`).
* Every call returns a fresh :class:`ProfileModel` with a new ULID
  ``profile_id``, ``kind="user"``, ``model_version="1.0.0"``,
  ``transition_curve="progressive"``, and a ``source_summary`` of the form
  ``"<N> sources · <M> analyzed signals"``.

This module is the canonical proving ground for 100% branch coverage on
``cockpit/wizard/builder.py``.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data.profile_model import (
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.wizard.builder import EmptyAnalysisError, build_profile
from rytm_randomizer.cockpit.wizard.pad_mapping import TRAIT_TO_PAD
from rytm_randomizer.cockpit.wizard.state import AnalysisJob

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_job(
    *,
    source_id: str = "01HXY5Q9PJM0000000000SOURCE1",
    status: str = "ok",
    progress: float = 1.0,
    error: str | None = None,
    extracted_traits: tuple[StyleTrait, ...] = (),
) -> AnalysisJob:
    return AnalysisJob(
        source_id=source_id,
        status=status,  # type: ignore[arg-type]
        progress=progress,
        error=error,
        extracted_traits=extracted_traits,
    )


# ---------------------------------------------------------------------------
# Error class identity — EmptyAnalysisError MUST subclass ValueError
# ---------------------------------------------------------------------------


def test_empty_analysis_error_subclasses_value_error() -> None:
    assert issubclass(EmptyAnalysisError, ValueError)


# ---------------------------------------------------------------------------
# Empty / no-OK input → EmptyAnalysisError
# ---------------------------------------------------------------------------


def test_build_profile_raises_on_empty_jobs_tuple() -> None:
    with pytest.raises(EmptyAnalysisError, match="at least one job"):
        build_profile(name="buzzi", description=None, jobs=())


def test_build_profile_raises_when_all_jobs_failed() -> None:
    jobs = (
        _make_job(source_id="01HXY5Q9PJM0000000000SRCAAA", status="failed", error="bad header"),
        _make_job(source_id="01HXY5Q9PJM0000000000SRCBBB", status="failed", error="timeout"),
    )
    with pytest.raises(EmptyAnalysisError, match="none ok"):
        build_profile(name="buzzi", description=None, jobs=jobs)


def test_build_profile_raises_when_all_jobs_pending_or_analyzing() -> None:
    jobs = (
        _make_job(source_id="01HXY5Q9PJM0000000000SRCAAA", status="pending", progress=0.0),
        _make_job(source_id="01HXY5Q9PJM0000000000SRCBBB", status="analyzing", progress=0.5),
    )
    with pytest.raises(EmptyAnalysisError):
        build_profile(name="buzzi", description=None, jobs=jobs)


def test_build_profile_skips_non_ok_jobs_when_at_least_one_ok_job_present() -> None:
    """Mixed: 1 ok + 1 failed + 1 pending → source_summary counts only the OK job."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            status="ok",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),),
        ),
        _make_job(source_id="01HXY5Q9PJM0000000000SRCBBB", status="failed", error="boom"),
        _make_job(source_id="01HXY5Q9PJM0000000000SRCCCC", status="pending", progress=0.0),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert profile.source_summary == "1 sources · 1 analyzed signals"
    assert profile.traits == (StyleTrait(name="rolling_low_end", value=0.5),)


# ---------------------------------------------------------------------------
# Single OK job — fixed-version contract + source_summary shape
# ---------------------------------------------------------------------------


def test_build_profile_single_ok_job_produces_user_kind_profile() -> None:
    jobs = (
        _make_job(
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.85),
                StyleTrait(name="hat_density", value=0.4),
            ),
        ),
    )
    profile = build_profile(name="buzzi", description="hard techno", jobs=jobs)

    assert isinstance(profile, ProfileModel)
    assert profile.name == "buzzi"
    assert profile.kind == "user"
    assert profile.model_version == "1.0.0"
    assert profile.transition_curve == "progressive"
    assert profile.source_summary == "1 sources · 2 analyzed signals"


def test_build_profile_passes_name_through_verbatim() -> None:
    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    profile = build_profile(name="surgeon-001", description=None, jobs=jobs)
    assert profile.name == "surgeon-001"


def test_build_profile_assigns_fresh_ulid_to_profile_id() -> None:
    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    # ULIDs are 26-char Crockford base32; a non-empty string passes the
    # ProfileModel validator and matches the ulid module's contract.
    assert isinstance(profile.profile_id, str)
    assert len(profile.profile_id) == 26


def test_build_profile_two_calls_with_identical_input_produce_distinct_profile_ids() -> None:
    """Per spec: every build_profile call gets a fresh ULID, even on identical input."""

    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    a = build_profile(name="buzzi", description=None, jobs=jobs)
    b = build_profile(name="buzzi", description=None, jobs=jobs)
    assert a.profile_id != b.profile_id


# ---------------------------------------------------------------------------
# Multiple OK jobs — arithmetic mean aggregation
# ---------------------------------------------------------------------------


def test_build_profile_averages_same_trait_across_three_jobs() -> None:
    """Three jobs with rolling_low_end 0.5 / 0.7 / 0.9 → averaged trait 0.7."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.7),),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCCCC",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.9),),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert len(profile.traits) == 1
    assert profile.traits[0].name == "rolling_low_end"
    assert profile.traits[0].value == pytest.approx(0.7)
    assert profile.source_summary == "3 sources · 3 analyzed signals"


def test_build_profile_averages_overlapping_trait_names_independently() -> None:
    """Two jobs share rolling_low_end and hat_density; both are averaged separately."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.4),
                StyleTrait(name="hat_density", value=0.2),
            ),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.6),
                StyleTrait(name="hat_density", value=0.8),
            ),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    by_name = {t.name: t.value for t in profile.traits}
    assert by_name["rolling_low_end"] == pytest.approx(0.5)
    assert by_name["hat_density"] == pytest.approx(0.5)


def test_build_profile_preserves_first_seen_trait_order_across_jobs() -> None:
    """The order in `traits` follows first-seen ordering across the input jobs."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.5),
                StyleTrait(name="metallic_tension", value=0.3),
            ),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(
                # hat_density appears AFTER the SRCAAA traits in input order
                StyleTrait(name="hat_density", value=0.7),
                # metallic_tension already seen — must not reorder
                StyleTrait(name="metallic_tension", value=0.5),
            ),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert tuple(t.name for t in profile.traits) == (
        "rolling_low_end",
        "metallic_tension",
        "hat_density",
    )


def test_build_profile_single_occurrence_trait_keeps_verbatim_value() -> None:
    """A trait produced by exactly one job ends up with that job's value verbatim."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.42),),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(StyleTrait(name="hat_density", value=0.91),),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    by_name = {t.name: t.value for t in profile.traits}
    assert by_name["rolling_low_end"] == 0.42
    assert by_name["hat_density"] == 0.91


# ---------------------------------------------------------------------------
# Empty extracted_traits — counts toward N but contributes nothing to average
# ---------------------------------------------------------------------------


def test_build_profile_ok_job_with_no_traits_counts_toward_source_summary() -> None:
    """An OK job with no traits still bumps the ``N`` in '<N> sources …'."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    # 2 OK jobs · 1 total trait signal
    assert profile.source_summary == "2 sources · 1 analyzed signals"
    # The empty-traits job contributes nothing to the average, so the
    # rolling_low_end value matches the only contributing job.
    assert profile.traits == (StyleTrait(name="rolling_low_end", value=0.5),)


def test_build_profile_all_ok_jobs_with_empty_traits_yields_no_traits() -> None:
    """All-OK + all-empty → a valid ProfileModel with empty traits + pad_mappings."""

    jobs = (
        _make_job(source_id="01HXY5Q9PJM0000000000SRCAAA", extracted_traits=()),
        _make_job(source_id="01HXY5Q9PJM0000000000SRCBBB", extracted_traits=()),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert profile.traits == ()
    assert profile.pad_mappings == ()
    assert profile.source_summary == "2 sources · 0 analyzed signals"


# ---------------------------------------------------------------------------
# pad_mappings derivation — TRAIT_TO_PAD-driven, unmapped traits dropped
# ---------------------------------------------------------------------------


def test_build_profile_emits_pad_mapping_for_each_mapped_trait() -> None:
    """Each trait whose name is in TRAIT_TO_PAD produces one TraitPadWeight."""

    jobs = (
        _make_job(
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.6),
                StyleTrait(name="metallic_tension", value=0.5),
                StyleTrait(name="hat_density", value=0.4),
                StyleTrait(name="filter_motion", value=0.3),
            ),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    pads_by_trait = {m.trait: (m.pad_id, m.weight) for m in profile.pad_mappings}
    assert pads_by_trait == {
        "rolling_low_end": (1, 0.6),
        "metallic_tension": (2, 0.5),
        "hat_density": (3, 0.4),
        "filter_motion": (4, 0.3),
    }


def test_build_profile_pad_weight_uses_averaged_value() -> None:
    """The TraitPadWeight.weight equals the trait's averaged value (not a per-job value)."""

    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.2),),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(StyleTrait(name="rolling_low_end", value=0.8),),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert profile.pad_mappings == (TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.5),)


def test_build_profile_drops_unmapped_traits_from_pad_mappings_but_keeps_in_traits() -> None:
    """A trait name absent from TRAIT_TO_PAD must NOT produce a pad_mapping."""

    assert "unknown_trait" not in TRAIT_TO_PAD
    jobs = (
        _make_job(
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.5),
                StyleTrait(name="unknown_trait", value=0.7),
            ),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    # The trait IS kept in traits...
    trait_names = {t.name for t in profile.traits}
    assert trait_names == {"rolling_low_end", "unknown_trait"}
    # ...but it must NOT show up in pad_mappings.
    pad_trait_names = {m.trait for m in profile.pad_mappings}
    assert pad_trait_names == {"rolling_low_end"}


def test_build_profile_no_mapped_traits_yields_empty_pad_mappings() -> None:
    jobs = (
        _make_job(
            extracted_traits=(StyleTrait(name="some_other_trait", value=0.5),),
        ),
    )
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    assert profile.pad_mappings == ()
    assert profile.traits == (StyleTrait(name="some_other_trait", value=0.5),)


# ---------------------------------------------------------------------------
# description argument — accepted (any string or None) and discarded
# ---------------------------------------------------------------------------


def test_build_profile_accepts_none_description() -> None:
    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    profile = build_profile(name="buzzi", description=None, jobs=jobs)
    # ProfileModel has no description field — argument is silently discarded.
    assert not hasattr(profile, "description")


def test_build_profile_accepts_string_description_and_discards_it() -> None:
    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    profile = build_profile(name="buzzi", description="hard techno · metallic", jobs=jobs)
    assert not hasattr(profile, "description")


def test_build_profile_description_does_not_affect_other_fields() -> None:
    """Same jobs, different descriptions → identical traits / pad_mappings / summary."""

    jobs = (_make_job(extracted_traits=(StyleTrait(name="rolling_low_end", value=0.5),)),)
    a = build_profile(name="buzzi", description=None, jobs=jobs)
    b = build_profile(name="buzzi", description="anything goes here", jobs=jobs)
    assert a.traits == b.traits
    assert a.pad_mappings == b.pad_mappings
    assert a.source_summary == b.source_summary
    assert a.name == b.name
    assert a.kind == b.kind
    assert a.transition_curve == b.transition_curve
    assert a.model_version == b.model_version


# ---------------------------------------------------------------------------
# Composite: full review-step profile is round-trip-serializable
# ---------------------------------------------------------------------------


def test_build_profile_output_round_trips_through_to_dict() -> None:
    jobs = (
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCAAA",
            extracted_traits=(
                StyleTrait(name="rolling_low_end", value=0.6),
                StyleTrait(name="hat_density", value=0.4),
            ),
        ),
        _make_job(
            source_id="01HXY5Q9PJM0000000000SRCBBB",
            extracted_traits=(StyleTrait(name="metallic_tension", value=0.7),),
        ),
    )
    profile = build_profile(name="buzzi", description="metallic", jobs=jobs)
    restored = ProfileModel.from_dict(profile.to_dict())
    assert restored == profile
