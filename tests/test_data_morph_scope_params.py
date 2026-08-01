"""Tests for the discrete-vs-continuous parameter classification fact table."""

from __future__ import annotations

import pytest

from rytm_randomizer import data
from rytm_randomizer.data import morph_scope_params

pytestmark = pytest.mark.fast


def test_discrete_names_reexported_from_data_package() -> None:
    # The fact table is re-exported through the data package namespace; the
    # helper predicate stays on the submodule (the package __all__ is
    # UPPER_SNAKE constants only, per tests/architecture/test_data_not_code.py).
    assert data.DISCRETE_PARAM_NAMES is morph_scope_params.DISCRETE_PARAM_NAMES
    assert not hasattr(data, "is_discrete_param")


def test_is_discrete_param_true_for_selectors() -> None:
    assert morph_scope_params.is_discrete_param("SRC Waveform") is True
    assert morph_scope_params.is_discrete_param("LFO Destination") is True
    assert morph_scope_params.is_discrete_param("FLT Type") is True


def test_is_discrete_param_false_for_continuous() -> None:
    assert morph_scope_params.is_discrete_param("SRC Tune") is False
    assert morph_scope_params.is_discrete_param("FLT Frequency") is False
    assert morph_scope_params.is_discrete_param("unknown param") is False


def test_discrete_set_is_frozen() -> None:
    assert isinstance(morph_scope_params.DISCRETE_PARAM_NAMES, frozenset)
