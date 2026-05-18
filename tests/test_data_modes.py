"""Tests for ``rytm_randomizer.data.modes`` — the WS-M3 string-literal source of truth.

These tests pin the canonical surface so the dispatch-site migration that
consumes these constants (a follow-up WS) can rely on a stable contract.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.data import modes

pytestmark = pytest.mark.fast


# --- Public surface ---------------------------------------------------------


def test_literal_aliases_are_importable() -> None:
    """Each Literal alias must be importable from the modes module."""
    for name in (
        "IntensityMode",
        "PageMode",
        "MutationKind",
        "Pad1Mode",
        "ZoneName",
    ):
        assert hasattr(modes, name), f"missing Literal alias: {name}"


def test_final_tuples_are_importable() -> None:
    """Each Final tuple constant must be importable from the modes module."""
    for name in (
        "INTENSITY_MODES",
        "PAGE_MODES",
        "MUTATION_KINDS",
        "PAD1_MODES",
        "ZONE_NAMES",
    ):
        assert hasattr(modes, name), f"missing Final tuple: {name}"


def test_all_exports_are_complete() -> None:
    """``__all__`` must enumerate every public name (5 aliases + 5 tuples)."""
    assert set(modes.__all__) == {
        "IntensityMode",
        "INTENSITY_MODES",
        "PageMode",
        "PAGE_MODES",
        "MutationKind",
        "MUTATION_KINDS",
        "Pad1Mode",
        "PAD1_MODES",
        "ZoneName",
        "ZONE_NAMES",
    }


# --- Content & order --------------------------------------------------------


def test_intensity_modes_content_and_order() -> None:
    """Intensity modes match the V1.34 canonical order: balanced → harder."""
    assert modes.INTENSITY_MODES == ("balanced", "deeper", "intense", "harder")


def test_page_modes_content_and_order() -> None:
    """Page modes match the canonical Rytm page order."""
    assert modes.PAGE_MODES == (
        "src",
        "filter",
        "amp",
        "lfo",
        "morph",
        "body",
        "grit",
    )


def test_mutation_kinds_content_and_order() -> None:
    """Mutation kinds: discovery (free) before mutation (incremental)."""
    assert modes.MUTATION_KINDS == ("discovery", "mutation")


def test_pad1_modes_content_and_order() -> None:
    """Pad-1 BD machines in the order used by ``randomization.py``."""
    assert modes.PAD1_MODES == ("sharp", "hard", "classic", "fm")


def test_zone_names_content_and_order() -> None:
    """Zone names match the WS-S3 depth-prompt zone order."""
    assert modes.ZONE_NAMES == ("src", "filter", "amp", "grit", "body")


# --- Immutability -----------------------------------------------------------


def test_every_constant_is_a_tuple_not_a_list() -> None:
    """Per Gate 12, module-level sequence constants are tuples (immutable)."""
    for name in (
        "INTENSITY_MODES",
        "PAGE_MODES",
        "MUTATION_KINDS",
        "PAD1_MODES",
        "ZONE_NAMES",
    ):
        value = getattr(modes, name)
        assert isinstance(value, tuple), f"{name} must be a tuple, got {type(value).__name__}"
        assert not isinstance(value, list), f"{name} must not be a list"


# --- Length consistency -----------------------------------------------------


def test_tuple_lengths_match_documented_cardinality() -> None:
    """Lengths pin the cardinality so accidental adds/removes are caught."""
    assert len(modes.INTENSITY_MODES) == 4
    assert len(modes.PAGE_MODES) == 7
    assert len(modes.MUTATION_KINDS) == 2
    assert len(modes.PAD1_MODES) == 4
    assert len(modes.ZONE_NAMES) == 5


def test_no_duplicates_within_any_tuple() -> None:
    """Each tuple must contain unique values (drift-guard)."""
    for name in (
        "INTENSITY_MODES",
        "PAGE_MODES",
        "MUTATION_KINDS",
        "PAD1_MODES",
        "ZONE_NAMES",
    ):
        value = getattr(modes, name)
        assert len(set(value)) == len(value), f"{name} has duplicates: {value}"
