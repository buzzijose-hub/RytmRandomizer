"""Tests for ``rytm_randomizer.guardrails.resolver`` (WS-W Layer 4).

The resolver must:

* Refuse to start a session (hard-raise :class:`GuardrailResolutionError`)
  when the profile's lifecycle state does not satisfy the requested mode.
* Drop a bound to ``LOCKED_DEFAULT`` when its range, intersected with the
  hardware envelope, is empty -- the rest of the profile still resolves.
* Drop a bound to ``LOCKED_DEFAULT`` when the parameter doesn't exist on
  the hardware (the param is "not on the pad").
* Preserve a ``FORBIDDEN`` bound as ``FORBIDDEN``.
* Narrow -- never widen -- the bound's range to the hardware intersection.
* Produce a :class:`ResolvedBounds` where :py:meth:`ResolvedBounds.clamp_value`
  passes-through unknown ``(pad, parameter)`` pairs, clamps mutating
  classes, and returns ``None`` for locked/forbidden classes.
"""

from __future__ import annotations

import dataclasses

import pytest

from rytm_randomizer.guardrails import (
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    GuardrailResolutionError,
    MODE_EXPERIMENTAL,
    MODE_LIVE_SAFE,
    MODE_STUDIO_DISCOVERY,
    MusicalCharacter,
    ProfileState,
    Provenance,
    ResolvedBound,
    ResolvedBounds,
    RoleAssignment,
    RoleMapping,
    SCHEMA_VERSION,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
    default_hardware_ranges_for_pad,
    resolve,
)
from rytm_randomizer.observability.errors import BoundaryError


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _provenance() -> Provenance:
    return Provenance(
        profile_name="rolling-hypnotic",
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        feature_report_hash="hash",
        derived_at="2026-05-14T12:00:00Z",
    )


def _character() -> MusicalCharacter:
    return MusicalCharacter(
        style_tags=("rolling", "hypnotic", "dark"),
        bpm_range=(128, 132),
        energy_profile="steady",
        density_profile="dense",
    )


def _role_mapping() -> RoleMapping:
    return RoleMapping(
        assignments={
            1: RoleAssignment(role="kick", mutation_direction="tighten"),
        }
    )


def _profile(
    *,
    bounds: tuple[GuardrailBound, ...] = (),
    state: ProfileState = ProfileState.LIVE_APPROVED,
) -> GuardrailProfile:
    intermediate = GuardrailProfile(
        provenance=_provenance(),
        character=_character(),
        role_mapping=_role_mapping(),
        bounds=bounds,
        locked_default=(),
        forbidden=(),
        scenes=(),
        state=state,
        schema_version=SCHEMA_VERSION,
        content_hash="",
    )
    digest = compute_content_hash(intermediate)
    return dataclasses.replace(intermediate, content_hash=digest)


def _hardware_pad1(_pad: int):
    # A small synthetic hardware envelope for Pad 1.
    return {
        "FLT Frequency": (23, 36),
        "FLT Resonance": (40, 68),
        "AMP Overdrive": (16, 35),
    }


# ---------------------------------------------------------------------------
# Lifecycle: hard-refuse on state mismatch
# ---------------------------------------------------------------------------


def test_resolver_hard_refuses_validated_for_live_safe():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,), state=ProfileState.VALIDATED)

    with pytest.raises(GuardrailResolutionError) as exc:
        resolve(profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1)
    ctx = exc.value.context
    assert ctx["mode"] == MODE_LIVE_SAFE
    assert ctx["profile_state"] == "VALIDATED"


def test_resolver_hard_refuses_draft_for_studio_discovery():
    profile = _profile(state=ProfileState.DRAFT)
    with pytest.raises(GuardrailResolutionError):
        resolve(
            profile,
            MODE_STUDIO_DISCOVERY,
            hardware_ranges_for_pad=_hardware_pad1,
        )


def test_resolver_hard_refuses_unknown_mode():
    profile = _profile(state=ProfileState.LIVE_APPROVED)
    with pytest.raises(GuardrailResolutionError) as exc:
        resolve(profile, "BANANA", hardware_ranges_for_pad=_hardware_pad1)
    assert exc.value.context["mode"] == "BANANA"


def test_live_safe_accepts_only_live_approved():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,), state=ProfileState.LIVE_APPROVED)
    resolved = resolve(profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1)
    assert resolved.mode == MODE_LIVE_SAFE


def test_studio_discovery_accepts_validated_and_up():
    profile = _profile(state=ProfileState.STUDIO_TESTED)
    resolved = resolve(
        profile,
        MODE_STUDIO_DISCOVERY,
        hardware_ranges_for_pad=_hardware_pad1,
    )
    assert resolved.mode == MODE_STUDIO_DISCOVERY


def test_experimental_accepts_validated_and_up():
    profile = _profile(state=ProfileState.VALIDATED)
    resolved = resolve(
        profile,
        MODE_EXPERIMENTAL,
        hardware_ranges_for_pad=_hardware_pad1,
    )
    assert resolved.mode == MODE_EXPERIMENTAL


# ---------------------------------------------------------------------------
# Per-bound intersection / fail-loud-but-soft
# ---------------------------------------------------------------------------


def test_bound_within_hardware_keeps_its_class_and_narrows_to_intersection():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,))
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "FLT Frequency")
    assert rb is not None
    assert rb.low == 25
    assert rb.high == 33
    assert rb.guardrail_class is GuardrailClass.LIVE_SAFE


def test_bound_wider_than_hardware_clamps_to_hardware():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=10,    # below hardware low (23)
        high=100,  # above hardware high (36)
        guardrail_class=GuardrailClass.STUDIO_DISCOVERY,
        direction="open",
    )
    profile = _profile(bounds=(bound,), state=ProfileState.LIVE_APPROVED)
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "FLT Frequency")
    # The intersection is exactly the hardware envelope.
    assert rb is not None
    assert rb.low == 23
    assert rb.high == 36


def test_empty_intersection_drops_to_locked_default():
    # Bound range [60, 70] vs hardware [23, 36] -- no overlap.
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=60,
        high=70,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,))
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "FLT Frequency")
    assert rb is not None
    assert rb.guardrail_class is GuardrailClass.LOCKED_DEFAULT


def test_unknown_param_drops_to_locked_default():
    bound = GuardrailBound(
        pad=1,
        parameter="THIS PARAM DOES NOT EXIST",
        low=0,
        high=10,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,))
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "THIS PARAM DOES NOT EXIST")
    assert rb is not None
    assert rb.guardrail_class is GuardrailClass.LOCKED_DEFAULT


def test_forbidden_bound_stays_forbidden_even_in_hardware_range():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.FORBIDDEN,
        direction="static",
    )
    profile = _profile(bounds=(bound,))
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "FLT Frequency")
    assert rb is not None
    assert rb.guardrail_class is GuardrailClass.FORBIDDEN


def test_locked_default_bound_remains_locked_default():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LOCKED_DEFAULT,
        direction="static",
    )
    profile = _profile(bounds=(bound,))
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    rb = resolved.get(1, "FLT Frequency")
    assert rb is not None
    assert rb.guardrail_class is GuardrailClass.LOCKED_DEFAULT


def test_resolved_bounds_are_subset_of_hardware_ranges():
    bounds = (
        GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=10,
            high=100,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="open",
        ),
        GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=20,
            high=80,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="modulate",
        ),
    )
    profile = _profile(bounds=bounds)
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )

    for (pad, param), rb in resolved.by_pad_param.items():
        hw_low, hw_high = _hardware_pad1(pad)[param]
        assert rb.low >= hw_low
        assert rb.high <= hw_high


# ---------------------------------------------------------------------------
# ResolvedBounds value-object behavior
# ---------------------------------------------------------------------------


def test_resolved_bounds_get_returns_none_for_missing_entry():
    rb = ResolvedBounds(by_pad_param={}, mode=MODE_LIVE_SAFE)
    assert rb.get(1, "anything") is None


def test_resolved_bounds_is_frozen():
    rb = ResolvedBounds(by_pad_param={}, mode=MODE_LIVE_SAFE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        rb.mode = "other"  # type: ignore[misc]


def test_resolved_bound_is_frozen():
    rb = ResolvedBound(low=0, high=10, guardrail_class=GuardrailClass.LIVE_SAFE)
    with pytest.raises(dataclasses.FrozenInstanceError):
        rb.low = 5  # type: ignore[misc]


def test_clamp_value_passes_through_unknown_entries():
    rb = ResolvedBounds(by_pad_param={}, mode=MODE_LIVE_SAFE)
    assert rb.clamp_value(1, "anything", 42) == 42


def test_clamp_value_clamps_mutating_class_values():
    table = {
        (1, "FLT Frequency"): ResolvedBound(
            low=25,
            high=33,
            guardrail_class=GuardrailClass.LIVE_SAFE,
        ),
    }
    rb = ResolvedBounds(by_pad_param=table, mode=MODE_LIVE_SAFE)
    assert rb.clamp_value(1, "FLT Frequency", 10) == 25
    assert rb.clamp_value(1, "FLT Frequency", 100) == 33
    assert rb.clamp_value(1, "FLT Frequency", 30) == 30


def test_clamp_value_returns_none_for_locked_default():
    table = {
        (1, "FLT Frequency"): ResolvedBound(
            low=25,
            high=33,
            guardrail_class=GuardrailClass.LOCKED_DEFAULT,
        ),
    }
    rb = ResolvedBounds(by_pad_param=table, mode=MODE_LIVE_SAFE)
    assert rb.clamp_value(1, "FLT Frequency", 30) is None


def test_clamp_value_returns_none_for_forbidden():
    table = {
        (1, "FLT Frequency"): ResolvedBound(
            low=25,
            high=33,
            guardrail_class=GuardrailClass.FORBIDDEN,
        ),
    }
    rb = ResolvedBounds(by_pad_param=table, mode=MODE_LIVE_SAFE)
    assert rb.clamp_value(1, "FLT Frequency", 30) is None


# ---------------------------------------------------------------------------
# Default hardware-range adapter
# ---------------------------------------------------------------------------


def test_default_hardware_ranges_for_pad_1_includes_known_param():
    ranges = default_hardware_ranges_for_pad(1)
    # BD_HARD_SAFE has FLT Frequency in its safe table.
    assert "FLT Frequency" in ranges
    low, high = ranges["FLT Frequency"]
    assert low == 23 and high == 36


def test_default_hardware_ranges_for_unknown_pad_returns_empty():
    ranges = default_hardware_ranges_for_pad(99)
    assert ranges == {}


def test_resolver_uses_default_hardware_adapter_when_none_provided():
    bound = GuardrailBound(
        pad=1,
        parameter="FLT Frequency",
        low=25,
        high=33,
        guardrail_class=GuardrailClass.LIVE_SAFE,
        direction="tighten",
    )
    profile = _profile(bounds=(bound,))

    resolved = resolve(profile, MODE_LIVE_SAFE)
    rb = resolved.get(1, "FLT Frequency")
    assert rb is not None
    assert rb.low == 25
    assert rb.high == 33


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------


def test_resolution_error_is_a_boundary_error():
    err = GuardrailResolutionError("test", context={"mode": MODE_LIVE_SAFE})
    assert isinstance(err, BoundaryError)


# ---------------------------------------------------------------------------
# Caching: multiple bounds on the same pad call the adapter once
# ---------------------------------------------------------------------------


def test_resolver_caches_hardware_lookups_per_pad():
    calls: list[int] = []

    def counting_adapter(pad: int):
        calls.append(pad)
        return _hardware_pad1(pad)

    bounds = (
        GuardrailBound(
            pad=1,
            parameter="FLT Frequency",
            low=25,
            high=33,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="tighten",
        ),
        GuardrailBound(
            pad=1,
            parameter="FLT Resonance",
            low=45,
            high=60,
            guardrail_class=GuardrailClass.LIVE_SAFE,
            direction="modulate",
        ),
    )
    profile = _profile(bounds=bounds)
    resolve(profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=counting_adapter)

    assert calls == [1]


# ---------------------------------------------------------------------------
# Empty profile (no bounds) resolves to an empty table
# ---------------------------------------------------------------------------


def test_empty_profile_yields_empty_resolved_bounds():
    profile = _profile(bounds=())
    resolved = resolve(
        profile, MODE_LIVE_SAFE, hardware_ranges_for_pad=_hardware_pad1
    )
    assert dict(resolved.by_pad_param) == {}
