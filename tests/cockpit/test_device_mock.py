"""Tests for ``rytm_randomizer.cockpit.device.mock`` — MockDeviceAdapter.

The mock holds a single :class:`Snapshot` in memory. ``apply`` honors the
pad-lock contract (locked pads keep their current params); ``commit_kit``
is a no-op (mock has no persistence) but logs at INFO so dev mode shows
the intent. ``is_armed`` is always ``False``.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/device/mock.py``.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest

from rytm_randomizer.cockpit.data import (
    CockpitSendPlan,
    MutationCandidate,
    PadDelta,
    PadState,
    SendPlanPacket,
    Snapshot,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Logging capture helper.
#
# The package-root logger (``rytm_randomizer``) sets ``propagate = False`` at
# import time (see ``rytm_randomizer/observability/__init__.py``). That
# blocks the default ``caplog`` propagation path, so we attach caplog's
# handler directly to the device-mock logger for the duration of one test.
# ---------------------------------------------------------------------------


@pytest.fixture
def capture_mock_logs(
    caplog: pytest.LogCaptureFixture,
) -> Iterator[pytest.LogCaptureFixture]:
    """Attach ``caplog``'s handler to the device-mock logger so INFO is seen."""

    logger = logging.getLogger("rytm_randomizer.cockpit.device.mock")
    prior_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(caplog.handler)
    try:
        yield caplog
    finally:
        logger.removeHandler(caplog.handler)
        logger.setLevel(prior_level)


_FIXED_TS = datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _pad(pad_id: int, machine: str = "BD Hard", **params: int) -> PadState:
    return PadState(
        pad_id=pad_id,
        machine=machine,
        params=params or {"tun": 28, "dec": 80, "lev": 110},
    )


def _snapshot(*pads: PadState) -> Snapshot:
    return Snapshot(
        snapshot_id="01HXY5Q9PJM0123456789ABCD0",
        device="analog_rytm_mk2",
        captured_at=_FIXED_TS,
        pads=pads if pads else (_pad(1), _pad(2, "SD Acoustic", tun=40, dec=60, lev=100)),
        scene_slot="A01",
        bpm=124.5,
    )


def _delta(pad_id: int, **proposed: int) -> PadDelta:
    proposed = proposed or {"tun": 99, "dec": 33, "lev": 55}
    return PadDelta(
        pad_id=pad_id,
        proposed_params=proposed,
        changed_keys=frozenset(proposed.keys()),
    )


def _candidate(*deltas: PadDelta) -> MutationCandidate:
    return MutationCandidate(
        candidate_id="01HXY5Q9PJCANDIDATE000000A",
        source_snapshot_id="01HXY5Q9PJM0123456789ABCD0",
        profile_id="profile-buzzi",
        depth=0.5,
        seed=42,
        pad_deltas=deltas or (_delta(1), _delta(2)),
        safety_status="safe",
        estimated_midi_msgs=6,
    )


def _send_plan(*packets: SendPlanPacket, ready: bool = True) -> CockpitSendPlan:
    return CockpitSendPlan(
        plan_id="sendplan-mock",
        candidate_id="candidate-mock",
        source_snapshot_id="01HXY5Q9PJM0123456789ABCD0",
        profile_id="profile-buzzi",
        ready=ready,
        readiness_reason="ready" if ready else "candidate_high_risk",
        safety_status="safe" if ready else "high_risk",
        packets=packets or (SendPlanPacket(1, "tun", 0, 52, 99),),
        locked_pad_ids=frozenset({2}),
        blocked_reasons=() if ready else ("candidate_high_risk",),
    )


# ---------------------------------------------------------------------------
# Construction + is_armed
# ---------------------------------------------------------------------------


def test_mock_is_not_armed() -> None:
    adapter = MockDeviceAdapter(initial=_snapshot())

    assert adapter.is_armed is False


def test_constructor_rejects_non_snapshot_initial() -> None:
    with pytest.raises(TypeError, match="Snapshot"):
        MockDeviceAdapter(initial="not-a-snapshot")  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# capture_snapshot returns the held state
# ---------------------------------------------------------------------------


def test_capture_returns_initial_snapshot_verbatim() -> None:
    initial = _snapshot()
    adapter = MockDeviceAdapter(initial=initial)

    assert adapter.capture_snapshot() is initial


def test_capture_after_apply_returns_updated_snapshot() -> None:
    """``apply`` updates internal state; ``capture_snapshot`` sees the new one."""

    adapter = MockDeviceAdapter(initial=_snapshot())
    applied = adapter.apply(_candidate(), pad_locks=frozenset())

    assert adapter.capture_snapshot() is applied
    assert adapter.capture_snapshot() != _snapshot()


def test_adopt_snapshot_replaces_state_without_io_and_rejects_wrong_type() -> None:
    adapter = MockDeviceAdapter(initial=_snapshot())
    adopted = _snapshot(_pad(3, machine="SY Raw", tun=72))

    adapter.adopt_snapshot(adopted)

    assert adapter.capture_snapshot() is adopted
    with pytest.raises(TypeError, match="Snapshot"):
        adapter.adopt_snapshot(object())  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# apply: with no locks, every non-locked pad's params are replaced.
# ---------------------------------------------------------------------------


def test_apply_with_no_locks_replaces_all_addressed_pad_params() -> None:
    initial = _snapshot()
    adapter = MockDeviceAdapter(initial=initial)
    candidate = _candidate(
        _delta(1, tun=99, dec=33, lev=55),
        _delta(2, tun=11, dec=22, lev=44),
    )

    result = adapter.apply(candidate, pad_locks=frozenset())

    by_id = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert by_id[1] == {"tun": 99, "dec": 33, "lev": 55}
    assert by_id[2] == {"tun": 11, "dec": 22, "lev": 44}


def test_apply_preserves_machine_name_on_non_locked_pads() -> None:
    """Mutating a pad's params must not rename its machine."""

    initial = _snapshot(
        _pad(1, machine="BD Plastic", tun=1, dec=2, lev=3),
        _pad(2, machine="SD Acoustic", tun=10, dec=20, lev=30),
    )
    adapter = MockDeviceAdapter(initial=initial)

    result = adapter.apply(
        _candidate(_delta(1, tun=99), _delta(2, dec=33)),
        pad_locks=frozenset(),
    )

    machines = {pad.pad_id: pad.machine for pad in result.pads}
    assert machines == {1: "BD Plastic", 2: "SD Acoustic"}


# ---------------------------------------------------------------------------
# apply: with locks, locked pads keep their current params.
# ---------------------------------------------------------------------------


def test_apply_with_single_lock_skips_locked_pad() -> None:
    initial = _snapshot(
        _pad(1, machine="BD Hard", tun=10, dec=20, lev=30),
        _pad(2, machine="SD Acoustic", tun=40, dec=50, lev=60),
    )
    adapter = MockDeviceAdapter(initial=initial)
    candidate = _candidate(
        _delta(1, tun=99, dec=99, lev=99),
        _delta(2, tun=11, dec=22, lev=33),
    )

    result = adapter.apply(candidate, pad_locks=frozenset({1}))

    by_id = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert by_id[1] == {"tun": 10, "dec": 20, "lev": 30}  # unchanged
    assert by_id[2] == {"tun": 11, "dec": 22, "lev": 33}


def test_apply_with_all_pads_locked_returns_identical_param_state() -> None:
    initial = _snapshot()
    adapter = MockDeviceAdapter(initial=initial)

    result = adapter.apply(_candidate(), pad_locks=frozenset({1, 2}))

    # Same pad params (a new Snapshot object, but equal params content).
    initial_params = {pad.pad_id: dict(pad.params) for pad in initial.pads}
    result_params = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert initial_params == result_params


def test_apply_with_lock_on_pad_not_in_candidate_is_harmless() -> None:
    """Locking a pad the candidate doesn't address is a no-op for that lock."""

    initial = _snapshot(
        _pad(1, machine="BD Hard", tun=10, dec=20, lev=30),
        _pad(2, machine="SD Acoustic", tun=40, dec=50, lev=60),
    )
    adapter = MockDeviceAdapter(initial=initial)
    candidate = _candidate(_delta(1, tun=99))  # only pad 1 mentioned

    result = adapter.apply(candidate, pad_locks=frozenset({2}))

    by_id = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert by_id[1] == {"tun": 99}
    assert by_id[2] == {"tun": 40, "dec": 50, "lev": 60}  # untouched


def test_apply_keeps_pad_not_mentioned_in_candidate() -> None:
    """Pads the candidate doesn't touch are kept verbatim."""

    initial = _snapshot(
        _pad(1, machine="BD Hard", tun=10, dec=20, lev=30),
        _pad(2, machine="SD Acoustic", tun=40, dec=50, lev=60),
    )
    adapter = MockDeviceAdapter(initial=initial)

    result = adapter.apply(
        _candidate(_delta(1, tun=99)),
        pad_locks=frozenset(),
    )

    by_id = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert by_id[1] == {"tun": 99}
    assert by_id[2] == {"tun": 40, "dec": 50, "lev": 60}


def test_apply_returns_a_new_snapshot_object() -> None:
    """The post-apply snapshot is a new instance with a fresh id."""

    initial = _snapshot()
    adapter = MockDeviceAdapter(initial=initial)

    result = adapter.apply(_candidate(), pad_locks=frozenset())

    assert result is not initial
    assert result.snapshot_id != initial.snapshot_id


def test_apply_persists_state_between_calls() -> None:
    """Two successive applies compose: the second sees the first's output."""

    initial = _snapshot(
        _pad(1, machine="BD Hard", tun=10, dec=20, lev=30),
    )
    adapter = MockDeviceAdapter(initial=initial)
    first = adapter.apply(
        _candidate(_delta(1, tun=99, dec=88, lev=77)),
        pad_locks=frozenset(),
    )
    second = adapter.apply(
        _candidate(_delta(1, tun=11, dec=22, lev=33)),
        pad_locks=frozenset({1}),  # second apply locks pad 1
    )

    # First apply set {99, 88, 77}; second apply locked pad 1 so values held.
    by_id_first = {pad.pad_id: dict(pad.params) for pad in first.pads}
    by_id_second = {pad.pad_id: dict(pad.params) for pad in second.pads}
    assert by_id_first[1] == {"tun": 99, "dec": 88, "lev": 77}
    assert by_id_second[1] == {"tun": 99, "dec": 88, "lev": 77}


# ---------------------------------------------------------------------------
# apply_send_plan: prepared plan path used by cockpit SEND.
# ---------------------------------------------------------------------------


def test_apply_send_plan_updates_only_planned_packet_params() -> None:
    initial = _snapshot(
        _pad(1, machine="BD Hard", tun=10, dec=20, lev=30),
        _pad(2, machine="SD Acoustic", tun=40, dec=50, lev=60),
    )
    adapter = MockDeviceAdapter(initial=initial)
    plan = _send_plan(
        SendPlanPacket(1, "tun", 0, 52, 99),
        SendPlanPacket(1, "dec", 0, 44, 88),
    )

    result = adapter.apply_send_plan(plan)

    by_id = {pad.pad_id: dict(pad.params) for pad in result.pads}
    assert by_id[1] == {"tun": 99, "dec": 88, "lev": 30}
    assert by_id[2] == {"tun": 40, "dec": 50, "lev": 60}


def test_apply_send_plan_rejects_blocked_plan() -> None:
    adapter = MockDeviceAdapter(initial=_snapshot())

    with pytest.raises(ValueError, match="send_plan_not_ready"):
        adapter.apply_send_plan(_send_plan(ready=False))


# ---------------------------------------------------------------------------
# No persistent-write surface — the adapter is a passive state projection.
# ---------------------------------------------------------------------------


def test_the_mock_has_no_commit_kit_method() -> None:
    """``commit_kit`` is gone, and its absence is the point.

    The mock's implementation was a ``logger.info`` line, but the WS
    ``save`` handler called it and then acked durable success — so the
    cockpit told operators a kit was written to the device's persistent
    memory when nothing had been written anywhere. The method is removed
    from the Protocol and from this adapter; ``save`` refuses instead.
    """

    adapter = MockDeviceAdapter(initial=_snapshot())

    assert not hasattr(adapter, "commit_kit")


def test_the_mock_exposes_no_persistent_write_surface_at_all() -> None:
    """Nothing on the adapter claims to write through to a device."""

    surface = {name for name in dir(MockDeviceAdapter) if not name.startswith("_")}

    assert surface == {
        "adopt_snapshot",
        "apply",
        "apply_send_plan",
        "capture_snapshot",
        "is_armed",
    }
