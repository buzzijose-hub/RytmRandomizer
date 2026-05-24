"""Tests for ``rytm_randomizer.cockpit.wizard.state`` — Profile Wizard data model.

Three frozen dataclasses (:class:`InspirationSource`, :class:`AnalysisJob`,
:class:`WizardState`) plus six pure state-transition helpers on
:class:`WizardState`. Every helper MUST:

* be **pure** (return a new state, never mutate ``self``),
* raise ``ValueError`` on contract violations (unknown source id, advance
  past last step, duplicate add, etc.),
* round-trip losslessly through ``to_dict`` / ``from_dict``.

This module is the canonical proving ground for 100% branch coverage on
``cockpit/wizard/state.py``.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data.profile_model import (
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.wizard import (
    KIND_VALUES,
    MODE_VALUES,
    STATUS_VALUES,
    STEP_VALUES,
    AnalysisJob,
    InspirationSource,
    WizardState,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_FIXED_TS = datetime(2026, 5, 24, 12, 0, 0, tzinfo=timezone.utc)


def _make_source(
    *,
    source_id: str = "01HXY5Q9PJM0000000000SOURCE1",
    kind: str = "artist",
    mode: str = "reference",
    location: str = "Surgeon",
    display_name: str = "Surgeon",
    added_at: datetime | None = None,
) -> InspirationSource:
    return InspirationSource(
        source_id=source_id,
        kind=kind,  # type: ignore[arg-type]
        mode=mode,  # type: ignore[arg-type]
        location=location,
        display_name=display_name,
        added_at=added_at or _FIXED_TS,
    )


def _make_job(
    *,
    source_id: str = "01HXY5Q9PJM0000000000SOURCE1",
    status: str = "pending",
    progress: float = 0.0,
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


def _make_state(
    *,
    wizard_id: str = "01HXY5Q9PJM00000000000WIZARD",
    step: str = "name",
    name: str | None = None,
    description: str | None = None,
    sources: tuple[InspirationSource, ...] = (),
    jobs: tuple[AnalysisJob, ...] = (),
    candidate_profile: ProfileModel | None = None,
) -> WizardState:
    return WizardState(
        wizard_id=wizard_id,
        step=step,  # type: ignore[arg-type]
        name=name,
        description=description,
        sources=sources,
        jobs=jobs,
        candidate_profile=candidate_profile,
    )


def _make_profile() -> ProfileModel:
    return ProfileModel(
        profile_id="01HXY5Q9PJM00000000000PROFILE",
        name="buzzi",
        kind="user",
        model_version="1.0.0",
        traits=(StyleTrait(name="rolling_low_end", value=0.85),),
        pad_mappings=(TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.7),),
        transition_curve="progressive",
        source_summary="1 source",
    )


# ---------------------------------------------------------------------------
# Module-level Literal exports
# ---------------------------------------------------------------------------


def test_kind_values_match_spec() -> None:
    assert KIND_VALUES == ("kit", "sound", "song", "album", "artist")


def test_mode_values_match_spec() -> None:
    assert MODE_VALUES == ("file", "folder", "reference")


def test_status_values_match_spec() -> None:
    assert STATUS_VALUES == ("pending", "analyzing", "ok", "failed")


def test_step_values_match_spec_order() -> None:
    """The four steps MUST be declared in advance order — :meth:`advance_step` relies on it."""

    assert STEP_VALUES == ("name", "add", "analyze", "review")


# ---------------------------------------------------------------------------
# InspirationSource — immutability + field validation
# ---------------------------------------------------------------------------


def test_inspiration_source_is_frozen() -> None:
    src = _make_source()
    with pytest.raises(FrozenInstanceError):
        src.kind = "kit"  # type: ignore[misc]


def test_inspiration_source_rejects_empty_source_id() -> None:
    with pytest.raises(ValueError, match="source_id"):
        _make_source(source_id="")


@pytest.mark.parametrize("kind", list(KIND_VALUES))
def test_inspiration_source_accepts_canonical_kind(kind: str) -> None:
    src = _make_source(kind=kind)
    assert src.kind == kind


def test_inspiration_source_rejects_unknown_kind() -> None:
    with pytest.raises(ValueError, match="kind"):
        _make_source(kind="not-a-kind")


@pytest.mark.parametrize("mode", list(MODE_VALUES))
def test_inspiration_source_accepts_canonical_mode(mode: str) -> None:
    src = _make_source(mode=mode)
    assert src.mode == mode


def test_inspiration_source_rejects_unknown_mode() -> None:
    with pytest.raises(ValueError, match="mode"):
        _make_source(mode="streaming")


def test_inspiration_source_rejects_empty_location() -> None:
    with pytest.raises(ValueError, match="location"):
        _make_source(location="")


def test_inspiration_source_rejects_empty_display_name() -> None:
    with pytest.raises(ValueError, match="display_name"):
        _make_source(display_name="")


def test_inspiration_source_to_dict_round_trip() -> None:
    src = _make_source()
    restored = InspirationSource.from_dict(src.to_dict())
    assert restored == src


def test_inspiration_source_to_dict_keys_are_stable() -> None:
    src = _make_source()
    data = src.to_dict()
    assert set(data.keys()) == {
        "source_id",
        "kind",
        "mode",
        "location",
        "display_name",
        "added_at",
    }
    # ``added_at`` is ISO 8601 so JSON layers don't need a custom encoder.
    assert data["added_at"] == _FIXED_TS.isoformat()


# ---------------------------------------------------------------------------
# AnalysisJob — immutability + field validation
# ---------------------------------------------------------------------------


def test_analysis_job_is_frozen() -> None:
    job = _make_job()
    with pytest.raises(FrozenInstanceError):
        job.status = "ok"  # type: ignore[misc]


def test_analysis_job_rejects_empty_source_id() -> None:
    with pytest.raises(ValueError, match="source_id"):
        _make_job(source_id="")


@pytest.mark.parametrize("status", list(STATUS_VALUES))
def test_analysis_job_accepts_canonical_status(status: str) -> None:
    job = _make_job(status=status)
    assert job.status == status


def test_analysis_job_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="status"):
        _make_job(status="cancelled")


@pytest.mark.parametrize("progress", [0.0, 0.5, 1.0])
def test_analysis_job_accepts_progress_inside_unit_range(progress: float) -> None:
    job = _make_job(progress=progress)
    assert job.progress == progress


@pytest.mark.parametrize("progress", [-0.01, 1.01, -1.0, 2.0])
def test_analysis_job_rejects_progress_outside_unit_range(progress: float) -> None:
    with pytest.raises(ValueError, match="progress"):
        _make_job(progress=progress)


def test_analysis_job_to_dict_round_trip_empty_traits() -> None:
    job = _make_job()
    restored = AnalysisJob.from_dict(job.to_dict())
    assert restored == job


def test_analysis_job_to_dict_round_trip_with_traits_and_error() -> None:
    job = _make_job(
        status="failed",
        progress=0.42,
        error="analyzer crashed on bad header",
        extracted_traits=(StyleTrait(name="hat_density", value=0.3),),
    )
    restored = AnalysisJob.from_dict(job.to_dict())
    assert restored == job
    assert restored.error == "analyzer crashed on bad header"


def test_analysis_job_to_dict_round_trip_ok_with_traits() -> None:
    job = _make_job(
        status="ok",
        progress=1.0,
        error=None,
        extracted_traits=(
            StyleTrait(name="rolling_low_end", value=0.9),
            StyleTrait(name="hat_density", value=0.2),
        ),
    )
    restored = AnalysisJob.from_dict(job.to_dict())
    assert restored == job


def test_analysis_job_from_dict_rejects_non_iterable_traits() -> None:
    bad = {
        "source_id": "01H",
        "status": "pending",
        "progress": 0.0,
        "error": None,
        "extracted_traits": {"not": "a list"},
    }
    with pytest.raises(TypeError, match="extracted_traits"):
        AnalysisJob.from_dict(bad)


def test_analysis_job_to_dict_keys_are_stable() -> None:
    job = _make_job()
    assert set(job.to_dict().keys()) == {
        "source_id",
        "status",
        "progress",
        "error",
        "extracted_traits",
    }


# ---------------------------------------------------------------------------
# WizardState — immutability + field validation
# ---------------------------------------------------------------------------


def test_wizard_state_is_frozen() -> None:
    state = _make_state()
    with pytest.raises(FrozenInstanceError):
        state.step = "add"  # type: ignore[misc]


def test_wizard_state_rejects_empty_wizard_id() -> None:
    with pytest.raises(ValueError, match="wizard_id"):
        _make_state(wizard_id="")


@pytest.mark.parametrize("step", list(STEP_VALUES))
def test_wizard_state_accepts_canonical_step(step: str) -> None:
    state = _make_state(step=step)
    assert state.step == step


def test_wizard_state_rejects_unknown_step() -> None:
    with pytest.raises(ValueError, match="step"):
        _make_state(step="cleanup")


# ---------------------------------------------------------------------------
# WizardState.empty — factory
# ---------------------------------------------------------------------------


def test_wizard_state_empty_starts_at_name_step_with_no_content() -> None:
    state = WizardState.empty("01HXY5Q9PJM00000000000WIZARD")
    assert state.wizard_id == "01HXY5Q9PJM00000000000WIZARD"
    assert state.step == "name"
    assert state.name is None
    assert state.description is None
    assert state.sources == ()
    assert state.jobs == ()
    assert state.candidate_profile is None


# ---------------------------------------------------------------------------
# WizardState.with_metadata — name + description partial / full updates
# ---------------------------------------------------------------------------


def test_with_metadata_returns_new_instance_and_does_not_mutate() -> None:
    state = _make_state()
    new_state = state.with_metadata(name="buzzi")
    assert new_state is not state
    assert state.name is None  # original unchanged
    assert new_state.name == "buzzi"


def test_with_metadata_leaves_unspecified_field_unchanged() -> None:
    state = _make_state(name="buzzi", description="hard techno")
    # Pass only name; description must be preserved.
    new_state = state.with_metadata(name="surgeon")
    assert new_state.name == "surgeon"
    assert new_state.description == "hard techno"


def test_with_metadata_can_set_only_description() -> None:
    state = _make_state(name="buzzi")
    new_state = state.with_metadata(description="metallic")
    assert new_state.name == "buzzi"
    assert new_state.description == "metallic"


def test_with_metadata_can_set_both_at_once() -> None:
    state = _make_state()
    new_state = state.with_metadata(name="buzzi", description="techno")
    assert new_state.name == "buzzi"
    assert new_state.description == "techno"


def test_with_metadata_with_no_arguments_is_noop_returning_equal_state() -> None:
    state = _make_state(name="buzzi", description="techno")
    new_state = state.with_metadata()
    assert new_state == state
    assert new_state is not state  # still a fresh instance


def test_with_metadata_empty_string_clears_the_field() -> None:
    """Spec: ``""`` means "explicitly cleared" (distinct from ``None`` = unchanged)."""

    state = _make_state(name="buzzi", description="techno")
    new_state = state.with_metadata(name="", description="")
    assert new_state.name == ""
    assert new_state.description == ""


# ---------------------------------------------------------------------------
# WizardState.advance_step — name → add → analyze → review → raise
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "from_step,to_step",
    [("name", "add"), ("add", "analyze"), ("analyze", "review")],
)
def test_advance_step_moves_forward_through_valid_transitions(from_step: str, to_step: str) -> None:
    state = _make_state(step=from_step)
    new_state = state.advance_step()
    assert new_state.step == to_step
    assert state.step == from_step  # original unchanged


def test_advance_step_returns_new_instance() -> None:
    state = _make_state(step="name")
    new_state = state.advance_step()
    assert new_state is not state


def test_advance_step_at_review_raises() -> None:
    state = _make_state(step="review")
    with pytest.raises(ValueError, match="final step"):
        state.advance_step()


# ---------------------------------------------------------------------------
# WizardState.with_source — append source + create pending job
# ---------------------------------------------------------------------------


def test_with_source_appends_and_creates_pending_job() -> None:
    state = _make_state()
    src = _make_source()
    new_state = state.with_source(src)

    assert new_state.sources == (src,)
    assert len(new_state.jobs) == 1
    job = new_state.jobs[0]
    assert job.source_id == src.source_id
    assert job.status == "pending"
    assert job.progress == 0.0
    assert job.error is None
    assert job.extracted_traits == ()
    # original unchanged
    assert state.sources == ()
    assert state.jobs == ()


def test_with_source_appends_to_existing_sources_in_order() -> None:
    src_a = _make_source(source_id="01HXY5Q9PJM0000000000SRCAAA", display_name="A")
    src_b = _make_source(source_id="01HXY5Q9PJM0000000000SRCBBB", display_name="B")
    state = _make_state().with_source(src_a).with_source(src_b)

    assert state.sources == (src_a, src_b)
    assert tuple(j.source_id for j in state.jobs) == (src_a.source_id, src_b.source_id)


def test_with_source_rejects_duplicate_source_id() -> None:
    src = _make_source()
    state = _make_state().with_source(src)
    with pytest.raises(ValueError, match="already present"):
        state.with_source(src)


# ---------------------------------------------------------------------------
# WizardState.without_source — remove source + its job
# ---------------------------------------------------------------------------


def test_without_source_removes_matching_source_and_job() -> None:
    src_a = _make_source(source_id="01HXY5Q9PJM0000000000SRCAAA", display_name="A")
    src_b = _make_source(source_id="01HXY5Q9PJM0000000000SRCBBB", display_name="B")
    state = _make_state().with_source(src_a).with_source(src_b)

    new_state = state.without_source(src_a.source_id)

    assert new_state.sources == (src_b,)
    assert tuple(j.source_id for j in new_state.jobs) == (src_b.source_id,)
    # original unchanged
    assert state.sources == (src_a, src_b)


def test_without_source_raises_for_unknown_source_id() -> None:
    state = _make_state()
    with pytest.raises(ValueError, match="not present"):
        state.without_source("01HXY5Q9PJM0000000000UNKNOWN")


def test_without_source_only_removes_target_when_others_share_no_id() -> None:
    src = _make_source()
    state = _make_state().with_source(src)
    new_state = state.without_source(src.source_id)
    assert new_state.sources == ()
    assert new_state.jobs == ()


# ---------------------------------------------------------------------------
# WizardState.with_job_update — replace job by source_id
# ---------------------------------------------------------------------------


def test_with_job_update_replaces_only_matching_job() -> None:
    src_a = _make_source(source_id="01HXY5Q9PJM0000000000SRCAAA", display_name="A")
    src_b = _make_source(source_id="01HXY5Q9PJM0000000000SRCBBB", display_name="B")
    state = _make_state().with_source(src_a).with_source(src_b)

    updated_a = AnalysisJob(
        source_id=src_a.source_id,
        status="analyzing",
        progress=0.5,
        error=None,
        extracted_traits=(),
    )
    new_state = state.with_job_update(updated_a)

    # A is replaced; B is untouched (still pending).
    jobs_by_source = {j.source_id: j for j in new_state.jobs}
    assert jobs_by_source[src_a.source_id] == updated_a
    assert jobs_by_source[src_b.source_id].status == "pending"
    # original unchanged
    orig_by_source = {j.source_id: j for j in state.jobs}
    assert orig_by_source[src_a.source_id].status == "pending"


def test_with_job_update_preserves_job_order() -> None:
    src_a = _make_source(source_id="01HXY5Q9PJM0000000000SRCAAA", display_name="A")
    src_b = _make_source(source_id="01HXY5Q9PJM0000000000SRCBBB", display_name="B")
    src_c = _make_source(source_id="01HXY5Q9PJM0000000000SRCCCC", display_name="C")
    state = _make_state().with_source(src_a).with_source(src_b).with_source(src_c)
    updated_b = AnalysisJob(
        source_id=src_b.source_id,
        status="ok",
        progress=1.0,
        error=None,
        extracted_traits=(StyleTrait(name="hat_density", value=0.5),),
    )
    new_state = state.with_job_update(updated_b)
    assert tuple(j.source_id for j in new_state.jobs) == (
        src_a.source_id,
        src_b.source_id,
        src_c.source_id,
    )
    assert new_state.jobs[1] == updated_b


def test_with_job_update_raises_for_unknown_source_id() -> None:
    state = _make_state()
    orphan_job = AnalysisJob(
        source_id="01HXY5Q9PJM0000000000ORPHAN",
        status="analyzing",
        progress=0.5,
        error=None,
        extracted_traits=(),
    )
    with pytest.raises(ValueError, match="no job present"):
        state.with_job_update(orphan_job)


# ---------------------------------------------------------------------------
# WizardState.with_candidate — set candidate_profile
# ---------------------------------------------------------------------------


def test_with_candidate_sets_candidate_profile() -> None:
    state = _make_state()
    profile = _make_profile()
    new_state = state.with_candidate(profile)
    assert new_state.candidate_profile == profile
    assert state.candidate_profile is None  # original unchanged


def test_with_candidate_overwrites_existing_candidate() -> None:
    first = _make_profile()
    second = ProfileModel(
        profile_id="01HXY5Q9PJM0000000000PROFIL2",
        name="other",
        kind="user",
        model_version="1.0.1",
        traits=(),
        pad_mappings=(),
        transition_curve="linear",
        source_summary="",
    )
    state = _make_state().with_candidate(first)
    new_state = state.with_candidate(second)
    assert new_state.candidate_profile == second


# ---------------------------------------------------------------------------
# WizardState — round-trip serialization
# ---------------------------------------------------------------------------


def test_wizard_state_to_dict_round_trip_empty() -> None:
    state = WizardState.empty("01HXY5Q9PJM00000000000WIZARD")
    restored = WizardState.from_dict(state.to_dict())
    assert restored == state


def test_wizard_state_to_dict_round_trip_full() -> None:
    src = _make_source()
    profile = _make_profile()
    state = (
        WizardState.empty("01HXY5Q9PJM00000000000WIZARD")
        .with_metadata(name="buzzi", description="hard techno")
        .with_source(src)
        .advance_step()  # → "add"
        .advance_step()  # → "analyze"
        .with_job_update(
            AnalysisJob(
                source_id=src.source_id,
                status="ok",
                progress=1.0,
                error=None,
                extracted_traits=(StyleTrait(name="rolling_low_end", value=0.85),),
            )
        )
        .advance_step()  # → "review"
        .with_candidate(profile)
    )
    restored = WizardState.from_dict(state.to_dict())
    assert restored == state
    assert restored.step == "review"
    assert restored.candidate_profile == profile


def test_wizard_state_to_dict_round_trip_with_failed_job() -> None:
    src = _make_source()
    state = (
        _make_state()
        .with_source(src)
        .with_job_update(
            AnalysisJob(
                source_id=src.source_id,
                status="failed",
                progress=0.3,
                error="file not found",
                extracted_traits=(),
            )
        )
    )
    restored = WizardState.from_dict(state.to_dict())
    assert restored == state


def test_wizard_state_to_dict_keys_are_stable() -> None:
    state = WizardState.empty("01H")
    assert set(state.to_dict().keys()) == {
        "wizard_id",
        "step",
        "name",
        "description",
        "sources",
        "jobs",
        "candidate_profile",
    }


def test_wizard_state_to_dict_serializes_none_candidate_as_none() -> None:
    state = WizardState.empty("01H")
    data = state.to_dict()
    assert data["candidate_profile"] is None


def test_wizard_state_to_dict_serializes_present_candidate_as_dict() -> None:
    profile = _make_profile()
    state = WizardState.empty("01H").with_candidate(profile)
    data = state.to_dict()
    assert data["candidate_profile"] == profile.to_dict()


def test_wizard_state_from_dict_rejects_non_iterable_sources() -> None:
    bad = WizardState.empty("01H").to_dict()
    bad["sources"] = {"not": "a list"}
    with pytest.raises(TypeError, match="sources"):
        WizardState.from_dict(bad)


def test_wizard_state_from_dict_rejects_non_iterable_jobs() -> None:
    bad = WizardState.empty("01H").to_dict()
    bad["jobs"] = {"not": "a list"}
    with pytest.raises(TypeError, match="jobs"):
        WizardState.from_dict(bad)


def test_wizard_state_from_dict_rejects_invalid_candidate_profile_type() -> None:
    bad = WizardState.empty("01H").to_dict()
    bad["candidate_profile"] = ["not", "a", "mapping"]
    with pytest.raises(TypeError, match="candidate_profile"):
        WizardState.from_dict(bad)


def test_wizard_state_from_dict_preserves_none_string_fields() -> None:
    """Round-trip: ``name=None`` and ``description=None`` come back as ``None`` (not ``"None"``)."""

    state = WizardState.empty("01H")
    restored = WizardState.from_dict(state.to_dict())
    assert restored.name is None
    assert restored.description is None


def test_wizard_state_from_dict_decodes_string_metadata() -> None:
    state = _make_state(name="buzzi", description="techno")
    restored = WizardState.from_dict(state.to_dict())
    assert restored.name == "buzzi"
    assert restored.description == "techno"


# ---------------------------------------------------------------------------
# Composition: WizardState transitions chain correctly
# ---------------------------------------------------------------------------


def test_full_wizard_lifecycle_produces_expected_state() -> None:
    """Smoke test: name → add → analyze → review covers every transition once."""

    src = _make_source()
    state = (
        WizardState.empty("01HXY5Q9PJM00000000000WIZARD")
        .with_metadata(name="buzzi")
        .advance_step()  # name → add
        .with_source(src)
        .advance_step()  # add → analyze
        .with_job_update(
            AnalysisJob(
                source_id=src.source_id,
                status="analyzing",
                progress=0.5,
                error=None,
                extracted_traits=(),
            )
        )
        .with_job_update(
            AnalysisJob(
                source_id=src.source_id,
                status="ok",
                progress=1.0,
                error=None,
                extracted_traits=(StyleTrait(name="rolling_low_end", value=0.8),),
            )
        )
        .advance_step()  # analyze → review
        .with_candidate(_make_profile())
    )
    assert state.step == "review"
    assert state.name == "buzzi"
    assert len(state.sources) == 1
    assert state.jobs[0].status == "ok"
    assert state.candidate_profile is not None


def test_remove_then_re_add_same_source_id_succeeds() -> None:
    """After :meth:`without_source`, the ``source_id`` is free to be re-added."""

    src = _make_source()
    state = _make_state().with_source(src).without_source(src.source_id).with_source(src)
    assert state.sources == (src,)
    assert state.jobs[0].source_id == src.source_id
    assert state.jobs[0].status == "pending"
