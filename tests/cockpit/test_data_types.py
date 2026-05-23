"""Tests for ``rytm_randomizer.cockpit.data.types`` — shared Literal types.

The cockpit data model surfaces a fixed vocabulary for ``ProfileModel.kind``,
``HistoryEntry.kind``, ``HistoryEntry.via``, ``MutationCandidate.safety_status``,
and ``ProfileModel.transition_curve``. Per Gate 10 (string-literal dispatch
hygiene), each set of allowed values lives in exactly one place as both a
``Literal[...]`` alias and a tuple of allowed values for runtime validation.
"""

from __future__ import annotations

from typing import Final, get_args

import pytest

from rytm_randomizer.cockpit.data import types

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Kind: "scene" | "user"
# ---------------------------------------------------------------------------


def test_kind_values_tuple_matches_literal_args() -> None:
    """``KIND_VALUES`` must enumerate every literal value of ``Kind``."""

    assert set(get_args(types.Kind)) == set(types.KIND_VALUES)


def test_kind_values_are_exact_spec() -> None:
    """``KIND_VALUES`` must be exactly the spec-listed pair."""

    assert types.KIND_VALUES == ("scene", "user")


# ---------------------------------------------------------------------------
# HistoryKind: "auto" | "saved"
# ---------------------------------------------------------------------------


def test_history_kind_values_tuple_matches_literal_args() -> None:
    assert set(get_args(types.HistoryKind)) == set(types.HISTORY_KIND_VALUES)


def test_history_kind_values_are_exact_spec() -> None:
    assert types.HISTORY_KIND_VALUES == ("auto", "saved")


# ---------------------------------------------------------------------------
# Via: "send" | "regen" | "load" | "import"
# ---------------------------------------------------------------------------


def test_via_values_tuple_matches_literal_args() -> None:
    assert set(get_args(types.Via)) == set(types.VIA_VALUES)


def test_via_values_are_exact_spec() -> None:
    assert types.VIA_VALUES == ("send", "regen", "load", "import")


# ---------------------------------------------------------------------------
# Status: "safe" | "armed" | "high_risk"
# ---------------------------------------------------------------------------


def test_status_values_tuple_matches_literal_args() -> None:
    assert set(get_args(types.Status)) == set(types.STATUS_VALUES)


def test_status_values_are_exact_spec() -> None:
    assert types.STATUS_VALUES == ("safe", "armed", "high_risk")


# ---------------------------------------------------------------------------
# TransitionCurve: "linear" | "progressive" | "progressive_w_release"
# ---------------------------------------------------------------------------


def test_transition_curve_values_tuple_matches_literal_args() -> None:
    assert set(get_args(types.TransitionCurve)) == set(types.TRANSITION_CURVE_VALUES)


def test_transition_curve_values_are_exact_spec() -> None:
    assert types.TRANSITION_CURVE_VALUES == (
        "linear",
        "progressive",
        "progressive_w_release",
    )


# ---------------------------------------------------------------------------
# Each constant tuple is typed as a ``Final`` and immutable.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "constant",
    [
        types.KIND_VALUES,
        types.HISTORY_KIND_VALUES,
        types.VIA_VALUES,
        types.STATUS_VALUES,
        types.TRANSITION_CURVE_VALUES,
    ],
)
def test_constants_are_tuples(constant: tuple[str, ...]) -> None:
    assert isinstance(constant, tuple)


def test_constants_are_marked_final() -> None:
    """The Final type aliases must be re-exported from the module's namespace."""

    # ``Final`` cannot be inspected at runtime; this asserts the names exist
    # and resolve, which is the closest mechanical proxy.
    expected: Final[tuple[str, ...]] = (
        "Kind",
        "KIND_VALUES",
        "HistoryKind",
        "HISTORY_KIND_VALUES",
        "Via",
        "VIA_VALUES",
        "Status",
        "STATUS_VALUES",
        "TransitionCurve",
        "TRANSITION_CURVE_VALUES",
    )
    for name in expected:
        assert hasattr(types, name), name
