"""Tests for ``rytm_randomizer.guardrails.validation`` (WS-W Layer 3).

The validator must:

* Accept a well-formed draft and return a frozen ``VALIDATED`` profile with
  ``content_hash`` set.
* Reject any structural violation with :class:`ProfileRejectedError`.
* Reject any semantic violation (bound outside the hardware envelope, unknown
  param/pad, both-LIVE_SAFE-and-FORBIDDEN, missing role) with
  :class:`ProfileRejectedError`.
* Rewrite high-risk parameters in a mutating class to ``LOCKED_DEFAULT``
  (or ``FORBIDDEN`` for the destructive subset) without rejecting the
  profile.
* Leave the original draft unmodified (it is frozen, but the test pins
  this through deep comparison).

The fixtures below construct a draft against the canonical Pad 1 BD Hard
profile (``data/.PROFILES["2"]``) so the semantic check has real ranges
to validate against.
"""

from __future__ import annotations

import dataclasses

import pytest

from rytm_randomizer.guardrails import (
    HIGH_RISK_PARAMETERS,
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileRejectedError,
    ProfileState,
    Provenance,
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    validate,
)
from rytm_randomizer.observability.errors import BoundaryError

# ---------------------------------------------------------------------------
# Builders -- a happy-path draft that should validate green
# ---------------------------------------------------------------------------


def _provenance() -> Provenance:
    return Provenance(
        profile_name="rolling-hypnotic",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="feat-hash-aaaa",
        derived_at="2026-05-14T12:00:00Z",
    )


def _character() -> MusicalCharacter:
    return MusicalCharacter(
        style_tags=("rolling", "hypnotic", "dark"),
        bpm_range=(128, 132),
        energy_profile="steady",
        density_profile="dense",
        musical_findings={"tempo_groove": "steady"},
    )


def _role_mapping() -> RoleMapping:
    return RoleMapping(
        assignments={
            1: RoleAssignment(role="kick", mutation_direction="tighten"),
            2: RoleAssignment(role="snare", mutation_direction="open-mid"),
            3: RoleAssignment(role="bass", mutation_direction="filter-motion"),
            4: RoleAssignment(role="accent", mutation_direction="modulate-wide"),
        }
    )


def _bound_in_range() -> GuardrailBound:
    # BD_HARD_SAFE["FLT Frequency"] = (23, 36); pick a strict subset.
    return GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )


def _draft(
    *,
    bounds: tuple[GuardrailBound, ...] = (),
    locked_default: tuple[str, ...] = (),
    forbidden: tuple[str, ...] = (),
    state: ProfileState = ProfileState.DRAFT,
    schema_version: str = SCHEMA_VERSION,
) -> GuardrailProfile:
    if not bounds:
        bounds = (_bound_in_range(),)
    return GuardrailProfile(
        provenance=_provenance(),
        character=_character(),
        role_mapping=_role_mapping(),
        bounds=bounds,
        locked_default=locked_default,
        forbidden=forbidden,
        scenes=(
            SceneGuardrail(
                scene_key="A1",
                pads_allowed=(1, 2, 3, 4),
                mutation_depth="moderate",
                risk_class=GuardrailClass.LIVE_SAFE,
                locked_roles=("kick",),
            ),
        ),
        state=state,
        schema_version=schema_version,
        content_hash="",
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


def test_validate_returns_validated_profile_with_content_hash():
    validated = validate(_draft())

    assert validated.state is ProfileState.VALIDATED
    assert validated.content_hash != ""
    assert len(validated.content_hash) == 64  # sha256 hex


def test_validate_does_not_mutate_input_draft():
    draft = _draft()
    original = dataclasses.replace(draft)

    validate(draft)

    assert draft == original
    assert draft.state is ProfileState.DRAFT


def test_validate_returns_a_frozen_profile():
    validated = validate(_draft())
    with pytest.raises(dataclasses.FrozenInstanceError):
        validated.state = ProfileState.LIVE_APPROVED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Structural rejection paths
# ---------------------------------------------------------------------------


def test_validate_rejects_unknown_schema_version():
    draft = _draft(schema_version="9.99")
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "structural"
    assert exc.value.context["schema_version"] == "9.99"


def test_validate_rejects_non_profile_input():
    with pytest.raises(ProfileRejectedError) as exc:
        validate("not a profile")  # type: ignore[arg-type]
    assert exc.value.context["layer"] == "structural"


def test_validate_rejects_empty_profile_name(monkeypatch):
    # Bypass frozen-dataclass check by re-creating a Provenance with empty name
    bad_prov = Provenance(
        profile_name="",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="hash",
        derived_at="t",
    )
    draft = dataclasses.replace(_draft(), provenance=bad_prov)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_validate_rejects_inverted_bpm_range():
    bad_char = MusicalCharacter(
        style_tags=("a", "b", "c"),
        bpm_range=(140, 100),
        energy_profile="steady",
        density_profile="dense",
    )
    draft = dataclasses.replace(_draft(), character=bad_char)
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "structural"


def test_validate_rejects_low_greater_than_high_bound():
    bad_bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=50,
        high=30,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "structural"


def test_validate_rejects_non_tuple_bounds():
    # The schema accepts any iterable -- but the validator demands a tuple.
    draft = _draft()
    draft = dataclasses.replace(draft, bounds=[_bound_in_range()])  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


# ---------------------------------------------------------------------------
# Semantic rejection paths
# ---------------------------------------------------------------------------


def test_validate_rejects_bound_outside_hardware_range():
    # FLT Frequency hardware range on Pad 1 is (23, 36); 50 is over the top.
    bad_bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=23,
        high=50,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="open",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"
    assert exc.value.context["parameter"] == "FLT Frequency"
    assert exc.value.context["hardware_range"] == (23, 36)


def test_validate_rejects_bound_below_hardware_range():
    bad_bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=10,
        high=30,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"


def test_validate_rejects_unknown_parameter():
    bad_bound = GuardrailBound(
        pad=1,
        parameter="THIS PARAMETER DOES NOT EXIST",
        low=0,
        high=10,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"
    assert exc.value.context["parameter"] == "THIS PARAMETER DOES NOT EXIST"


def test_validate_rejects_unknown_pad():
    bad_bound = GuardrailBound(
        pad=99,
        parameter="FLT Frequency",
        low=0,
        high=10,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"
    assert exc.value.context["pad"] == 99


def test_validate_rejects_param_both_mutating_and_forbidden():
    bound = _bound_in_range()
    draft = _draft(
        bounds=(bound,),
        forbidden=(bound.parameter,),
    )
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"
    assert exc.value.context["parameter"] == bound.parameter


def test_validate_rejects_mutated_bound_without_role_mapping():
    # Pad 1 has a role; if we point a mutating bound at a pad outside
    # role_mapping, semantic check rejects.
    role_only_2 = RoleMapping(
        assignments={2: RoleAssignment(role="snare", mutation_direction="open-mid")}
    )
    bound = _bound_in_range()  # pad=1
    draft = dataclasses.replace(_draft(bounds=(bound,)), role_mapping=role_only_2)
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "semantic"


# ---------------------------------------------------------------------------
# Safety floor -- rewrite, not reject
# ---------------------------------------------------------------------------


def test_safety_floor_rewrites_high_risk_to_locked_default():
    # ``master_volume`` is in HIGH_RISK_PARAMETERS but NOT in the destructive
    # subset, so the rewrite target is LOCKED_DEFAULT.
    # Use a pad/parameter combo: pad 1 doesn't have "master_volume"; we
    # need a high-risk parameter that DOES exist on the hardware. Use
    # ``AMP Level`` -- it's in HIGH_RISK_PARAMETERS and is a known param
    # on some profiles. But Pad 1 BD Hard does not have AMP Level. We
    # need to pick a high-risk parameter that exists on a pad's profile.
    #
    # Strategy: monkeypatch -- not appropriate for production tests. Instead
    # craft the draft to put a high-risk param on a pad that doesn't have
    # that parameter, and bypass the semantic check by having the param NOT
    # be in HIGH_RISK_PARAMETERS but using a parameter that exists.
    #
    # Final approach: We use FLT Frequency (which IS in the hardware
    # range) and just don't put it in HIGH_RISK; then we test by directly
    # constructing a draft whose bound parameter is one of the high-risk
    # ones AND exists on the pad. Looking through param maps: none of the
    # high-risk parameters are in the profile params (track_volume, clock,
    # etc. are conceptual). So we monkeypatch HIGH_RISK_PARAMETERS for
    # this single test to include FLT Frequency.
    from rytm_randomizer.guardrails import validation as val_mod

    original = val_mod.HIGH_RISK_PARAMETERS
    try:
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original | {"FLT Frequency"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=25,
            high=33,
            guardrail_class=GuardrailClass.STUDIO_DISCOVERY,
            direction="open",
        )
        draft = _draft(bounds=(bound,))
        validated = validate(draft)

        # The bound's class is rewritten to LOCKED_DEFAULT.
        assert len(validated.bounds) == 1
        assert validated.bounds[0].guardrail_class is GuardrailClass.LOCKED_DEFAULT
        # And the parameter shows up in locked_default for inspection.
        assert "FLT Frequency" in validated.locked_default
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original


def test_safety_floor_rewrites_destructive_to_forbidden():
    # ``kit_clear`` is destructive -> rewrite target is FORBIDDEN.
    from rytm_randomizer.guardrails import validation as val_mod

    original_safe = val_mod.HIGH_RISK_PARAMETERS
    original_destr = val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS
    try:
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original_safe | {"FLT Resonance"})
        val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS = frozenset(original_destr | {"FLT Resonance"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=45,
            high=60,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="modulate",
        )
        draft = _draft(bounds=(bound,))
        validated = validate(draft)

        assert validated.bounds[0].guardrail_class is GuardrailClass.FORBIDDEN
        assert "FLT Resonance" in validated.forbidden
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original_safe
        val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS = original_destr


def test_safety_floor_leaves_non_high_risk_bound_alone():
    # FLT Frequency is NOT in HIGH_RISK_PARAMETERS by default -- a
    # mutating-class bound on it should survive unchanged.
    bound = _bound_in_range()
    draft = _draft(bounds=(bound,))
    validated = validate(draft)

    assert validated.bounds[0].guardrail_class is GuardrailClass.LIVE_SAFE
    assert validated.bounds[0].parameter == bound.parameter


def test_safety_floor_does_not_double_record_forbidden_param():
    """A destructive high-risk param already in forbidden -- the rewriter
    finds the bound, neutralizes it, but does NOT re-append to the
    forbidden tuple."""

    from rytm_randomizer.guardrails import validation as val_mod

    original_safe = val_mod.HIGH_RISK_PARAMETERS
    original_destr = val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS
    try:
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original_safe | {"FLT Resonance"})
        val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS = frozenset(original_destr | {"FLT Resonance"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=45,
            high=60,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="modulate",
        )
        # Already in forbidden -- the bound is mutating (semantic guard would
        # normally reject this, but the test pre-stages a *new* forbidden
        # entry that's also being mutated to force the dedup branch).
        # Build a draft where the bound is on FLT Resonance but the same
        # param appears in forbidden after the semantic check would have
        # blocked it -- so we need to bypass semantic by using a parameter
        # that is in forbidden AND has a mutating bound (the validator's
        # semantic check rejects this combination -- so we have to use a
        # different draft entirely).
        #
        # Approach: pre-seed forbidden with the parameter; then submit the
        # bound -- the semantic check will reject. That's not the path I
        # want to exercise. Instead I need TWO bounds: one already
        # destructive (so it gets re-rewritten in the same loop), and
        # the second pass adds the same param again.
        #
        # Simpler: two bounds on the same destructive param. The first
        # rewrite adds to forbidden; the second sees the param already
        # in forbidden_seen and skips the append.
        # Pad 4 (BD Acoustic profile key "4") FLT Resonance safe is
        # (22, 42) -- pick a bound inside that envelope.
        bound2 = GuardrailBound(
            pad=4,
            parameter="FLT Resonance",
            low=25,
            high=35,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="modulate",
        )
        draft = _draft(bounds=(bound, bound2))
        validated = validate(draft)

        # The param appears exactly ONCE in forbidden despite two bounds.
        assert validated.forbidden.count("FLT Resonance") == 1
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original_safe
        val_mod.DESTRUCTIVE_HIGH_RISK_PARAMETERS = original_destr


def test_safety_floor_does_not_double_record_locked_param():
    """Pre-existing locked_default entry survives untouched."""

    from rytm_randomizer.guardrails import validation as val_mod

    original = val_mod.HIGH_RISK_PARAMETERS
    try:
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original | {"FLT Frequency"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=25,
            high=33,
            guardrail_class=GuardrailClass.STUDIO_DISCOVERY,
            direction="open",
        )
        # Already locked -- rewriter must keep one entry, not two.
        draft = _draft(bounds=(bound,), locked_default=("FLT Frequency",))
        validated = validate(draft)

        assert validated.locked_default.count("FLT Frequency") == 1
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original


def test_safety_floor_skips_already_locked_class():
    """A LOCKED_DEFAULT bound is not in MUTATING_CLASSES; nothing rewrites it."""

    from rytm_randomizer.guardrails import validation as val_mod

    original = val_mod.HIGH_RISK_PARAMETERS
    try:
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original | {"FLT Frequency"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=25,
            high=33,
            guardrail_class=GuardrailClass.LOCKED_DEFAULT,
            direction="static",
        )
        draft = _draft(bounds=(bound,))
        validated = validate(draft)

        # No rewrite occurred -> bound class stays LOCKED_DEFAULT.
        assert validated.bounds[0].guardrail_class is GuardrailClass.LOCKED_DEFAULT
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original


# ---------------------------------------------------------------------------
# Error taxonomy + context surface
# ---------------------------------------------------------------------------


def test_profile_rejected_is_a_boundary_error():
    """``ProfileRejectedError`` lives under ``BoundaryError`` (so the
    package-wide ``except BoundaryError`` catches it)."""

    err = ProfileRejectedError("test", context={"layer": "structural"})
    assert isinstance(err, BoundaryError)


def test_high_risk_parameters_include_expected_floor():
    # The safety floor must, at minimum, cover these spec section 5.2
    # entries.
    expected_subset = {
        "track_volume",
        "master_volume",
        "clock",
        "transport",
        "pattern_change",
        "program_change",
        "project_change",
        "kit_save",
        "kit_clear",
        "sysex_unvalidated",
        "live_machine_switch",
    }
    assert expected_subset.issubset(HIGH_RISK_PARAMETERS)


# ---------------------------------------------------------------------------
# Per-branch structural coverage -- every ``raise ProfileRejectedError`` in
# ``_check_structural`` deserves an explicit hit so the branch coverage
# ratchet stays at 100% on validation.py.
# ---------------------------------------------------------------------------


def _draft_with_corrupted_field(field: str, value) -> GuardrailProfile:
    """Use ``dataclasses.replace`` to plant a wrong-typed value into ``draft``.

    The schema is a frozen dataclass with no runtime type check, so
    ``dataclasses.replace`` accepts anything; the validator is the one that
    must report it as structural garbage.
    """

    base = _draft()
    return dataclasses.replace(base, **{field: value})


def test_structural_rejects_wrong_typed_provenance():
    draft = _draft_with_corrupted_field("provenance", "not a Provenance")
    with pytest.raises(ProfileRejectedError) as exc:
        validate(draft)
    assert exc.value.context["layer"] == "structural"


def test_structural_rejects_wrong_typed_source_type():
    bad_prov = Provenance(
        profile_name="x",
        source_type="not an enum",  # type: ignore[arg-type]
        confidence=Confidence.HIGH,
        feature_report_hash="h",
        derived_at="t",
    )
    draft = dataclasses.replace(_draft(), provenance=bad_prov)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_confidence():
    bad_prov = Provenance(
        profile_name="x",
        source_type=SourceType.SINGLE_TRACK,
        confidence="HIGH",  # type: ignore[arg-type]
        feature_report_hash="h",
        derived_at="t",
    )
    draft = dataclasses.replace(_draft(), provenance=bad_prov)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_string_feature_report_hash():
    bad_prov = Provenance(
        profile_name="x",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash=12345,  # type: ignore[arg-type]
        derived_at="t",
    )
    draft = dataclasses.replace(_draft(), provenance=bad_prov)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_string_derived_at():
    bad_prov = Provenance(
        profile_name="x",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="h",
        derived_at=12345,  # type: ignore[arg-type]
    )
    draft = dataclasses.replace(_draft(), provenance=bad_prov)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_character():
    draft = _draft_with_corrupted_field("character", "not a Character")
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_tuple_style_tags():
    bad_char = MusicalCharacter(
        style_tags=["list", "instead", "of", "tuple"],  # type: ignore[arg-type]
        bpm_range=(120, 124),
        energy_profile="steady",
        density_profile="dense",
    )
    draft = dataclasses.replace(_draft(), character=bad_char)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_bpm_range():
    bad_char = MusicalCharacter(
        style_tags=("a", "b"),
        bpm_range=(120,),  # type: ignore[arg-type] # length 1, not 2
        energy_profile="steady",
        density_profile="dense",
    )
    draft = dataclasses.replace(_draft(), character=bad_char)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_int_bpm_range():
    bad_char = MusicalCharacter(
        style_tags=("a", "b"),
        bpm_range=("low", "high"),  # type: ignore[arg-type]
        energy_profile="steady",
        density_profile="dense",
    )
    draft = dataclasses.replace(_draft(), character=bad_char)
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_role_mapping():
    draft = _draft_with_corrupted_field("role_mapping", "not a RoleMapping")
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_guardrail_bound_in_bounds():
    draft = dataclasses.replace(_draft(), bounds=("not a bound",))  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_guardrail_class():
    bad_bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class="LIVE_SAFE",  # type: ignore[arg-type] # string, not enum
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_int_low_high():
    bad_bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low="twenty-five",  # type: ignore[arg-type]
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    draft = _draft(bounds=(bad_bound,))
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_tuple_locked_default():
    draft = dataclasses.replace(_draft(), locked_default=["not", "tuple"])  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_tuple_forbidden():
    draft = dataclasses.replace(_draft(), forbidden=["not", "tuple"])  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_tuple_scenes():
    draft = dataclasses.replace(_draft(), scenes=["not", "tuple"])  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_non_scene_in_scenes():
    draft = dataclasses.replace(_draft(), scenes=("not a scene",))  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


def test_structural_rejects_wrong_typed_state():
    draft = dataclasses.replace(_draft(), state="VALIDATED")  # type: ignore[arg-type]
    with pytest.raises(ProfileRejectedError):
        validate(draft)


# ---------------------------------------------------------------------------
# _hardware_range_for branches
# ---------------------------------------------------------------------------


def test_hardware_range_for_unknown_pad_returns_none():
    from rytm_randomizer.guardrails.validation import _hardware_range_for

    assert _hardware_range_for(99, "FLT Frequency") is None


def test_hardware_range_for_unknown_param_on_known_pad_returns_none():
    from rytm_randomizer.guardrails.validation import _hardware_range_for

    assert _hardware_range_for(1, "THIS PARAM DOES NOT EXIST") is None


# ---------------------------------------------------------------------------
# Logging emits on validate + safety-floor rewrite
# ---------------------------------------------------------------------------


def test_validate_emits_log_record():
    import logging

    from rytm_randomizer.guardrails.validation import _logger

    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    _logger.addHandler(handler)
    try:
        _logger.setLevel(logging.INFO)
        validate(_draft())
    finally:
        _logger.removeHandler(handler)

    assert any("guardrails.validate" in r.getMessage() for r in records)


def test_safety_floor_rewrite_emits_log_record():
    import logging

    from rytm_randomizer.guardrails import validation as val_mod

    original = val_mod.HIGH_RISK_PARAMETERS
    records: list[logging.LogRecord] = []
    handler = logging.Handler()
    handler.emit = records.append  # type: ignore[method-assign]
    val_mod._logger.addHandler(handler)
    try:
        val_mod._logger.setLevel(logging.INFO)
        val_mod.HIGH_RISK_PARAMETERS = frozenset(original | {"FLT Frequency"})
        bound = GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=25,
            high=33,
            guardrail_class=GuardrailClass.STUDIO_DISCOVERY,
            direction="open",
        )
        validate(_draft(bounds=(bound,)))
    finally:
        val_mod.HIGH_RISK_PARAMETERS = original
        val_mod._logger.removeHandler(handler)

    assert any("guardrails.safety_floor" in r.getMessage() for r in records)
