"""Tests for ``rytm_randomizer.cockpit.wizard.pad_mapping`` — pinned TRAIT_TO_PAD table.

The ``TRAIT_TO_PAD`` mapping is the Phase 2 single source of truth for which
:class:`~rytm_randomizer.cockpit.data.StyleTrait` names get a
:class:`~rytm_randomizer.cockpit.data.TraitPadWeight` derived by the
:class:`ProfileBuilder`. The mapping is:

* pinned to the four spec-canonical trait names + pad ids,
* exposed as a :class:`types.MappingProxyType` so it cannot be mutated at
  runtime (the "no mutable module-level state" gate),
* re-exported via ``__all__`` so star-imports stay tidy.

This module is the canonical proving ground for 100% branch coverage on
``cockpit/wizard/pad_mapping.py``.
"""

from __future__ import annotations

from types import MappingProxyType

import pytest

from rytm_randomizer.cockpit.wizard import pad_mapping
from rytm_randomizer.cockpit.wizard.pad_mapping import TRAIT_TO_PAD

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Content — the four spec-canonical trait → pad assignments
# ---------------------------------------------------------------------------


def test_trait_to_pad_contains_exactly_the_four_spec_keys() -> None:
    assert set(TRAIT_TO_PAD.keys()) == {
        "rolling_low_end",
        "metallic_tension",
        "hat_density",
        "filter_motion",
    }


def test_trait_to_pad_assigns_rolling_low_end_to_pad_1() -> None:
    assert TRAIT_TO_PAD["rolling_low_end"] == 1


def test_trait_to_pad_assigns_metallic_tension_to_pad_2() -> None:
    assert TRAIT_TO_PAD["metallic_tension"] == 2


def test_trait_to_pad_assigns_hat_density_to_pad_3() -> None:
    assert TRAIT_TO_PAD["hat_density"] == 3


def test_trait_to_pad_assigns_filter_motion_to_pad_4() -> None:
    assert TRAIT_TO_PAD["filter_motion"] == 4


def test_trait_to_pad_has_exactly_four_entries() -> None:
    assert len(TRAIT_TO_PAD) == 4


# ---------------------------------------------------------------------------
# Immutability — MappingProxyType refuses mutation at runtime
# ---------------------------------------------------------------------------


def test_trait_to_pad_is_mapping_proxy_type() -> None:
    assert isinstance(TRAIT_TO_PAD, MappingProxyType)


def test_trait_to_pad_rejects_setitem() -> None:
    with pytest.raises(TypeError):
        TRAIT_TO_PAD["new_trait"] = 5  # type: ignore[index]


def test_trait_to_pad_rejects_delitem() -> None:
    with pytest.raises(TypeError):
        del TRAIT_TO_PAD["rolling_low_end"]  # type: ignore[attr-defined]


def test_trait_to_pad_rejects_overwrite_of_existing_key() -> None:
    with pytest.raises(TypeError):
        TRAIT_TO_PAD["rolling_low_end"] = 99  # type: ignore[index]


# ---------------------------------------------------------------------------
# Module-level exports
# ---------------------------------------------------------------------------


def test_module_exports_only_trait_to_pad() -> None:
    assert pad_mapping.__all__ == ["TRAIT_TO_PAD"]
