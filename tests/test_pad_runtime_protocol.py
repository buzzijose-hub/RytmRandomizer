"""WS-S2 tests: PadRuntimeState Protocol + PadRuntime dataclass.

The Protocol replaces the duck-typed mixin contract documented in
``engines/_runtime.py``'s module docstring. PadRuntime is the concrete
composable dataclass that satisfies both PadRuntimeState and
IsolatedPadState. Existing engines continue to inherit PadRuntimeMixin /
IsolatedPadMixin; future engines (e.g. PR #21's pad-12 engines) compose
PadRuntime instead.

Test naming: test_<unit>_<behavior>_when_<condition> per Gate 8.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# WS-M4: mark this module as fast-suite; pytest -m fast skips the 505
# warm-worker V1.34 parity fixtures and runs in <60s.
pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------------------------
# 1. Protocol export + runtime_checkable
# ---------------------------------------------------------------------------


def test_pad_runtime_state_protocol_is_exported() -> None:
    from rytm_randomizer.engines._runtime import PadRuntimeState

    assert PadRuntimeState is not None


def test_isolated_pad_state_protocol_is_exported() -> None:
    from rytm_randomizer.engines._runtime import IsolatedPadState

    assert IsolatedPadState is not None


def test_pad_runtime_dataclass_is_exported() -> None:
    from rytm_randomizer.engines._runtime import PadRuntime

    assert PadRuntime is not None


def test_pad_runtime_state_is_runtime_checkable() -> None:
    """isinstance(obj, PadRuntimeState) must work, not raise TypeError."""

    from rytm_randomizer.engines._runtime import PadRuntime, PadRuntimeState

    rt = PadRuntime(out=object())
    # Should not raise TypeError ("Instance and class checks can only be used
    # with @runtime_checkable protocols").
    assert isinstance(rt, PadRuntimeState)


def test_isolated_pad_state_is_runtime_checkable() -> None:
    from rytm_randomizer.engines._runtime import IsolatedPadState, PadRuntime

    rt = PadRuntime(out=object())
    assert isinstance(rt, IsolatedPadState)


# ---------------------------------------------------------------------------
# 2. PadRuntime dataclass shape
# ---------------------------------------------------------------------------


def test_pad_runtime_dataclass_has_all_required_attributes() -> None:
    from rytm_randomizer.engines._runtime import PadRuntime

    rt = PadRuntime(out=object())
    # Per the Protocol, every attribute must exist.
    for attr in (
        "out",
        "channel",
        "sleep",
        "rng",
        "active_profile",
        "anchor_state",
        "current_state",
        "previous_state",
        "target_pad",
        "resolved_bounds",
        "isolated_pad",
        "group_anchor_states",
        "group_current_states",
        "group_previous_states",
    ):
        assert hasattr(rt, attr), f"PadRuntime missing required attribute {attr!r}"


def test_pad_runtime_defaults_to_stdlib_sleep_and_random() -> None:
    """The dataclass __post_init__ wires sane defaults so PadRuntime(out=X) works."""

    import random as _random
    import time as _time

    from rytm_randomizer.engines._runtime import PadRuntime

    rt = PadRuntime(out=object())
    assert rt.sleep is _time.sleep
    assert rt.rng is _random


def test_pad_runtime_channel_and_target_pad_admit_pad_12_range() -> None:
    """PR #21 forward-compat: a pad-12 engine satisfies the Protocol without change."""

    from rytm_randomizer.engines._runtime import PadRuntime, PadRuntimeState

    rt = PadRuntime(out=object(), channel=11, target_pad=12)
    assert rt.channel == 11
    assert rt.target_pad == 12
    assert isinstance(rt, PadRuntimeState)


def test_pad_runtime_is_mutable() -> None:
    """anchor_state / current_state / previous_state get reassigned by the helpers;
    a frozen dataclass would force a replace() on every transition. This test
    pins the mutability contract -- if a future refactor makes it frozen, this
    must change deliberately."""

    from rytm_randomizer.engines._runtime import PadRuntime

    rt = PadRuntime(out=object())
    rt.current_state = {"FLT Frequency": 64}
    assert rt.current_state == {"FLT Frequency": 64}


# ---------------------------------------------------------------------------
# 3. Negative case: non-conforming object does not satisfy the Protocol
# ---------------------------------------------------------------------------


def test_object_missing_pad_runtime_attributes_is_not_a_pad_runtime_state() -> None:
    """A plain object lacks every Protocol attribute -- not a PadRuntimeState."""

    from rytm_randomizer.engines._runtime import PadRuntimeState

    assert not isinstance(object(), PadRuntimeState)


# ---------------------------------------------------------------------------
# 4. Mixin path still works (existing engines unchanged)
# ---------------------------------------------------------------------------


def test_existing_mixins_remain_exported_alongside_protocols() -> None:
    """WS-S2 is additive: the legacy PadRuntimeMixin / IsolatedPadMixin
    continue to exist and continue to be used by engines/pad{1-4}.py and
    group_runner.py. The Protocols and dataclass are the composition
    alternative for new engines."""

    from rytm_randomizer.engines._runtime import (
        IsolatedPadMixin,
        IsolatedPadState,
        PadRuntime,
        PadRuntimeMixin,
        PadRuntimeState,
    )

    assert PadRuntimeMixin is not None
    assert IsolatedPadMixin is not None
    assert PadRuntime is not None
    assert PadRuntimeState is not None
    assert IsolatedPadState is not None
