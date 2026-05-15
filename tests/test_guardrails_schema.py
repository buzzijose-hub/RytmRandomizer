"""Tests for the typed Guardrail Profile contract (``guardrails/schema.py``).

The schema is a leaf module: it has no dependencies on the rest of
``rytm_randomizer`` and no validation logic. The tests here cover:

* Closed enums (every named member is reachable; invalid values are
  rejected by the ``Enum`` machinery itself).
* Frozen dataclasses (mutating any field raises ``FrozenInstanceError``).
* Read-only mapping views inside :class:`MusicalCharacter` and
  :class:`RoleMapping`.
* :func:`compute_content_hash` determinism, content-sensitivity, and
  exclusion of the profile's own ``content_hash`` field from its input.
* End-to-end construction of a complete :class:`GuardrailProfile` from
  every component type in the module.
* Every branch of the private canonicalization helper so the coverage
  ratchet stays at 100%.
"""

from __future__ import annotations

import dataclasses
from types import MappingProxyType

import pytest

from rytm_randomizer.guardrails import schema
from rytm_randomizer.guardrails.schema import (
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileState,
    Provenance,
    RiskTier,
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
)


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _build_provenance() -> Provenance:
    return Provenance(
        profile_name="rolling-hypnotic",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="feat-hash-aaaa",
        derived_at="2026-05-14T12:00:00Z",
    )


def _build_character() -> MusicalCharacter:
    return MusicalCharacter(
        style_tags=("rolling", "hypnotic", "dark"),
        bpm_range=(128, 132),
        energy_profile="steady",
        density_profile="dense",
        musical_findings={
            "tempo_groove": "rock-steady",
            "low_end_behavior": "anchored",
            "percussion_density": "moderate",
            "bass_tonal_movement": "subtle-filter-motion",
            "texture_noise": "low",
            "fx_space": "narrow",
            "arrangement_energy_arc": "flat",
        },
    )


def _build_role_mapping() -> RoleMapping:
    return RoleMapping(
        assignments={
            1: RoleAssignment(role="kick", mutation_direction="tighten"),
            2: RoleAssignment(role="snare", mutation_direction="open-mid"),
            3: RoleAssignment(role="bass", mutation_direction="filter-motion"),
            4: RoleAssignment(role="accent", mutation_direction="modulate-wide"),
        }
    )


def _build_bound() -> GuardrailBound:
    return GuardrailBound(
        pad=1,
        parameter="filter_cutoff",
        low=40,
        high=80,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )


def _build_scene() -> SceneGuardrail:
    return SceneGuardrail(
        scene_key="A1",
        pads_allowed=(1, 2, 3, 4),
        mutation_depth="moderate",
        risk_class=GuardrailClass.STUDIO_DISCOVERY,
        locked_roles=("kick",),
    )


def _build_profile(*, content_hash: str = "") -> GuardrailProfile:
    return GuardrailProfile(
        provenance=_build_provenance(),
        character=_build_character(),
        role_mapping=_build_role_mapping(),
        bounds=(_build_bound(),),
        locked_default=("track_volume",),
        forbidden=("kit_clear",),
        scenes=(_build_scene(),),
        state=ProfileState.DRAFT,
        schema_version=SCHEMA_VERSION,
        content_hash=content_hash,
    )


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------


def test_schema_version_is_one_dot_zero():
    assert SCHEMA_VERSION == "1.0"


# ---------------------------------------------------------------------------
# Enum closure
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "enum_type, expected_names",
    [
        (
            GuardrailClass,
            {
                "LIVE_SAFE",
                "STUDIO_DISCOVERY",
                "EXPERIMENTAL",
                "LOCKED_DEFAULT",
                "FORBIDDEN",
            },
        ),
        (RiskTier, {"LOW", "MEDIUM", "HIGH"}),
        (
            SourceType,
            {
                "SINGLE_TRACK",
                "FOLDER_LIBRARY",
                "REFERENCE_PLAYLIST",
                "USER_RELEASE_LIBRARY",
                "LIVE_RECORDING",
                "FACTORY_SOUND_STUDY",
                "STYLE_DESCRIPTION_ONLY",
            },
        ),
        (Confidence, {"HIGH", "MEDIUM", "LOW"}),
        (
            ProfileState,
            {
                "DRAFT",
                "VALIDATED",
                "REJECTED",
                "STUDIO_TESTED",
                "LIVE_APPROVED",
                "ARCHIVED",
            },
        ),
    ],
)
def test_enum_exposes_exactly_the_specified_members(enum_type, expected_names):
    assert {member.name for member in enum_type} == expected_names


@pytest.mark.parametrize(
    "enum_type",
    [GuardrailClass, RiskTier, SourceType, Confidence, ProfileState],
)
def test_enum_rejects_unknown_value(enum_type):
    with pytest.raises(ValueError):
        enum_type("NOT_A_REAL_MEMBER")


# ---------------------------------------------------------------------------
# Frozen-dataclass guarantees
# ---------------------------------------------------------------------------


def test_provenance_is_frozen():
    prov = _build_provenance()
    with pytest.raises(dataclasses.FrozenInstanceError):
        prov.profile_name = "other"  # type: ignore[misc]


def test_musical_character_is_frozen():
    character = _build_character()
    with pytest.raises(dataclasses.FrozenInstanceError):
        character.energy_profile = "different"  # type: ignore[misc]


def test_role_assignment_is_frozen():
    assignment = RoleAssignment(role="kick", mutation_direction="tighten")
    with pytest.raises(dataclasses.FrozenInstanceError):
        assignment.role = "snare"  # type: ignore[misc]


def test_role_mapping_is_frozen():
    role_mapping = _build_role_mapping()
    with pytest.raises(dataclasses.FrozenInstanceError):
        role_mapping.assignments = {}  # type: ignore[misc]


def test_guardrail_bound_is_frozen():
    bound = _build_bound()
    with pytest.raises(dataclasses.FrozenInstanceError):
        bound.high = 90  # type: ignore[misc]


def test_scene_guardrail_is_frozen():
    scene = _build_scene()
    with pytest.raises(dataclasses.FrozenInstanceError):
        scene.scene_key = "B2"  # type: ignore[misc]


def test_guardrail_profile_is_frozen():
    profile = _build_profile()
    with pytest.raises(dataclasses.FrozenInstanceError):
        profile.state = ProfileState.VALIDATED  # type: ignore[misc]


# ---------------------------------------------------------------------------
# Read-only mapping views
# ---------------------------------------------------------------------------


def test_musical_character_findings_are_read_only():
    character = _build_character()

    # MappingProxyType is the marker for read-only views.
    assert isinstance(character.musical_findings, MappingProxyType)
    with pytest.raises(TypeError):
        character.musical_findings["tempo_groove"] = "mutated"  # type: ignore[index]


def test_musical_character_findings_default_to_empty_read_only_view():
    character = MusicalCharacter(
        style_tags=("a", "b", "c"),
        bpm_range=(120, 124),
        energy_profile="steady",
        density_profile="sparse",
    )

    assert isinstance(character.musical_findings, MappingProxyType)
    assert dict(character.musical_findings) == {}


def test_musical_character_findings_decouple_from_caller_dict():
    findings = {"tempo_groove": "stable"}
    character = MusicalCharacter(
        style_tags=("a", "b", "c"),
        bpm_range=(120, 124),
        energy_profile="steady",
        density_profile="sparse",
        musical_findings=findings,
    )

    # Mutating the source dict must not reach into the frozen view.
    findings["tempo_groove"] = "mutated"
    assert character.musical_findings["tempo_groove"] == "stable"


def test_role_mapping_assignments_are_read_only():
    role_mapping = _build_role_mapping()

    assert isinstance(role_mapping.assignments, MappingProxyType)
    with pytest.raises(TypeError):
        role_mapping.assignments[5] = RoleAssignment(  # type: ignore[index]
            role="hat", mutation_direction="open"
        )


def test_role_mapping_decouples_from_caller_dict():
    assignments = {1: RoleAssignment(role="kick", mutation_direction="tighten")}
    role_mapping = RoleMapping(assignments=assignments)

    assignments[1] = RoleAssignment(role="snare", mutation_direction="open")

    assert role_mapping.assignments[1].role == "kick"


# ---------------------------------------------------------------------------
# Content hash
# ---------------------------------------------------------------------------


def test_compute_content_hash_is_deterministic_across_builds():
    profile_a = _build_profile()
    profile_b = _build_profile()

    assert compute_content_hash(profile_a) == compute_content_hash(profile_b)


def test_compute_content_hash_is_independent_of_content_hash_field():
    # Computing the hash, inlining it, and recomputing must yield the same
    # digest -- otherwise the field could never settle.
    profile_empty = _build_profile(content_hash="")
    digest = compute_content_hash(profile_empty)
    profile_with_hash = _build_profile(content_hash=digest)

    assert compute_content_hash(profile_with_hash) == digest


def test_compute_content_hash_returns_lowercase_sha256_hex():
    digest = compute_content_hash(_build_profile())

    assert len(digest) == 64
    assert digest == digest.lower()
    assert all(c in "0123456789abcdef" for c in digest)


def test_compute_content_hash_is_sensitive_to_provenance_change():
    baseline = _build_profile()
    altered = dataclasses.replace(
        baseline,
        provenance=Provenance(
            profile_name="OTHER",
            source_type=baseline.provenance.source_type,
            confidence=baseline.provenance.confidence,
            feature_report_hash=baseline.provenance.feature_report_hash,
            derived_at=baseline.provenance.derived_at,
        ),
    )

    assert compute_content_hash(baseline) != compute_content_hash(altered)


def test_compute_content_hash_is_sensitive_to_bound_change():
    baseline = _build_profile()
    altered_bound = GuardrailBound(
        pad=1,
        parameter="filter_cutoff",
        low=40,
        high=90,  # was 80
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    altered = dataclasses.replace(baseline, bounds=(altered_bound,))

    assert compute_content_hash(baseline) != compute_content_hash(altered)


def test_compute_content_hash_is_sensitive_to_state_change():
    baseline = _build_profile()
    altered = dataclasses.replace(baseline, state=ProfileState.VALIDATED)

    assert compute_content_hash(baseline) != compute_content_hash(altered)


def test_compute_content_hash_handles_list_branch():
    # The canonicalizer accepts ``list`` as well as ``tuple``; exercising
    # that branch via a synthetic dataclass keeps coverage at 100% even
    # though the production types use tuples.
    @dataclasses.dataclass(frozen=True)
    class _Holder:
        values: list

    holder = _Holder(values=[1, 2, 3])
    canonical = schema._to_canonical(holder)

    assert canonical == {"values": [1, 2, 3]}


def test_compute_content_hash_rejects_unsupported_value_type():
    @dataclasses.dataclass(frozen=True)
    class _Holder:
        blob: object

    holder = _Holder(blob=object())

    with pytest.raises(TypeError):
        schema._to_canonical(holder)


def test_to_canonical_handles_primitive_passthrough():
    # Cover the primitive arm of ``_to_canonical`` directly for explicit
    # branch coverage.
    assert schema._to_canonical("hello") == "hello"
    assert schema._to_canonical(7) == 7
    assert schema._to_canonical(1.5) == 1.5
    assert schema._to_canonical(True) is True
    assert schema._to_canonical(None) is None


def test_to_canonical_rejects_dataclass_type_object():
    # ``is_dataclass`` returns True for the class itself; the
    # ``not isinstance(value, type)`` guard must steer that through the
    # error path rather than recursing into ``fields()``.
    with pytest.raises(TypeError):
        schema._to_canonical(Provenance)


# ---------------------------------------------------------------------------
# End-to-end construction
# ---------------------------------------------------------------------------


def test_guardrail_profile_round_trips_every_field():
    profile = _build_profile(content_hash="placeholder")
    profile = dataclasses.replace(
        profile, content_hash=compute_content_hash(profile)
    )

    # Provenance
    assert profile.provenance.profile_name == "rolling-hypnotic"
    assert profile.provenance.source_type is SourceType.SINGLE_TRACK
    assert profile.provenance.confidence is Confidence.HIGH

    # Musical character
    assert profile.character.style_tags == ("rolling", "hypnotic", "dark")
    assert profile.character.bpm_range == (128, 132)
    assert profile.character.musical_findings["fx_space"] == "narrow"

    # Role mapping
    assert profile.role_mapping.assignments[1].role == "kick"
    assert profile.role_mapping.assignments[4].mutation_direction == "modulate-wide"

    # Bounds
    assert profile.bounds[0].pad == 1
    assert profile.bounds[0].guardrail_class is GuardrailClass.LIVE_SAFE

    # Locked / forbidden
    assert profile.locked_default == ("track_volume",)
    assert profile.forbidden == ("kit_clear",)

    # Scenes
    assert profile.scenes[0].scene_key == "A1"
    assert profile.scenes[0].risk_class is GuardrailClass.STUDIO_DISCOVERY

    # State + version
    assert profile.state is ProfileState.DRAFT
    assert profile.schema_version == SCHEMA_VERSION

    # Hash is settled.
    assert profile.content_hash == compute_content_hash(profile)


def test_guardrails_package_reexports_public_surface():
    from rytm_randomizer import guardrails

    expected = {
        "SCHEMA_VERSION",
        "Confidence",
        "GuardrailBound",
        "GuardrailClass",
        "GuardrailProfile",
        "MusicalCharacter",
        "ProfileState",
        "Provenance",
        "RiskTier",
        "RoleMapping",
        "SceneGuardrail",
        "SourceType",
        "compute_content_hash",
    }
    assert expected.issubset(set(dir(guardrails)))
    assert expected == set(guardrails.__all__)
