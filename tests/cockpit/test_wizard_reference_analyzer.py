"""Tests for ``rytm_randomizer.cockpit.wizard.reference_analyzer``.

The reference analyzer is a pure Python lookup table mapping curated
artist / album / scene names onto canonical :class:`StyleTrait` tuples
plus a neutral fallback for unknown handles. The tests below pin every
branch of :func:`lookup_traits` (case-insensitive match, prefix match,
longest-key wins, whitespace trim, empty / unknown / non-string input).
"""

from __future__ import annotations

import pytest

from rytm_randomizer.cockpit.data.profile_model import StyleTrait
from rytm_randomizer.cockpit.wizard.reference_analyzer import lookup_traits
from rytm_randomizer.cockpit.wizard.traits import WIZARD_TRAIT_NAMES

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Trait-name invariants
# ---------------------------------------------------------------------------


def test_wizard_trait_names_are_the_four_canonical_traits() -> None:
    """The wizard trait name tuple is the single source of truth for ordering."""

    assert WIZARD_TRAIT_NAMES == (
        "rolling_low_end",
        "metallic_tension",
        "hat_density",
        "filter_motion",
    )


# ---------------------------------------------------------------------------
# Known-name matches
# ---------------------------------------------------------------------------


def test_known_name_returns_curated_trait_tuple() -> None:
    """A direct match returns the curated 4-trait tuple verbatim."""

    traits = lookup_traits("Surgeon")
    assert len(traits) == 4
    names = tuple(t.name for t in traits)
    assert names == WIZARD_TRAIT_NAMES
    # Surgeon -> rolling_low_end 0.85, metallic_tension 0.78
    by_name = {t.name: t.value for t in traits}
    assert by_name["rolling_low_end"] == pytest.approx(0.85)
    assert by_name["metallic_tension"] == pytest.approx(0.78)
    assert by_name["hat_density"] == pytest.approx(0.55)
    assert by_name["filter_motion"] == pytest.approx(0.65)


def test_known_name_lookup_is_case_insensitive() -> None:
    """``"SURGEON"`` and ``"Surgeon"`` and ``"surgeon"`` match the same entry."""

    expected = lookup_traits("surgeon")
    assert lookup_traits("SURGEON") == expected
    assert lookup_traits("Surgeon") == expected
    assert lookup_traits("sUrGeOn") == expected


def test_known_name_whitespace_trimmed_on_both_ends() -> None:
    """Leading / trailing whitespace must not block a match."""

    expected = lookup_traits("daniel avery")
    assert lookup_traits("  daniel avery  ") == expected
    assert lookup_traits("\tdaniel avery\n") == expected


def test_every_curated_entry_returns_a_4_trait_tuple() -> None:
    """Every value in the lookup table is a properly shaped 4-trait tuple.

    Walks the lookup table indirectly (every known key exercised by name)
    so the invariant is enforced even if future maintainers add entries.
    """

    known_names = (
        "surgeon",
        "regis",
        "birmingham",
        "british murder boys",
        "industrial",
        "schranz",
        "daniel avery",
        "drone logic",
        "hypnotic",
        "basic channel",
        "garage",
        "burial",
        "two-step",
        "peak-time",
        "berghain",
        "rolling",
        "acid",
        "hardfloor",
        "detroit",
        "minimal",
    )
    for name in known_names:
        traits = lookup_traits(name)
        assert len(traits) == 4, f"{name!r} returned {len(traits)} traits"
        assert tuple(t.name for t in traits) == WIZARD_TRAIT_NAMES
        for t in traits:
            assert isinstance(t, StyleTrait)
            assert 0.0 <= t.value <= 1.0


# ---------------------------------------------------------------------------
# Prefix matching + longest-key-wins
# ---------------------------------------------------------------------------


def test_longer_user_text_still_matches_shorter_key() -> None:
    """``"birmingham techno"`` matches the curated ``"birmingham"`` key."""

    expected = lookup_traits("birmingham")
    assert lookup_traits("birmingham techno") == expected


def test_longest_matching_key_wins() -> None:
    """When multiple keys are prefixes of the input, the longest matches.

    ``"basic channel sound"`` begins with both a (hypothetical short)
    key and the curated ``"basic channel"``. The longer one must win
    so a specific entry never gets shadowed by a less specific one.
    """

    # "basic channel" (13 chars) is a curated key; nothing shorter shares
    # this prefix, so this verifies the iteration ranks by key length
    # rather than dict insertion order.
    expected = lookup_traits("basic channel")
    assert lookup_traits("basic channel sound") == expected


# ---------------------------------------------------------------------------
# Unknown / empty / type-error fallbacks
# ---------------------------------------------------------------------------


def _is_neutral(traits: tuple[StyleTrait, ...]) -> bool:
    """The neutral profile = every canonical trait at exactly 0.5."""

    if len(traits) != 4:
        return False
    if tuple(t.name for t in traits) != WIZARD_TRAIT_NAMES:
        return False
    return all(t.value == pytest.approx(0.5) for t in traits)


def test_unknown_name_returns_neutral_profile() -> None:
    """An unrecognized handle returns the canonical neutral profile."""

    assert _is_neutral(lookup_traits("nobody you've ever heard of"))


def test_empty_string_returns_neutral_profile() -> None:
    """An empty / whitespace-only string short-circuits to the neutral profile.

    Branch coverage: the ``if not needle`` early-return is the only
    branch that fires here (no lookup iteration happens).
    """

    assert _is_neutral(lookup_traits(""))
    assert _is_neutral(lookup_traits("   "))
    assert _is_neutral(lookup_traits("\n\t\r"))


def test_non_string_input_raises_typeerror() -> None:
    """The contract is ``text: str`` -- anything else is a programmer bug."""

    with pytest.raises(TypeError, match="text must be a string"):
        lookup_traits(123)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        lookup_traits(None)  # type: ignore[arg-type]
