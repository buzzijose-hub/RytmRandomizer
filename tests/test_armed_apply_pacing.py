"""Bounded inter-message pacing through fake output and sleeper collaborators."""

from __future__ import annotations

import time
from asyncio import CancelledError
from collections.abc import Iterator
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from inspect import signature
from typing import Final

import pytest

from rytm_randomizer.devices import Device, get_device
from rytm_randomizer.senders.armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    KitMutationUnsupportedError,
)

pytestmark = pytest.mark.fast

_PORT: Final[str] = "fake paced output"
_TOKEN: Final[str] = "paced-arm-token"
_ACTION: Final[str] = "paced-action"
_PACKETS: Final[tuple[tuple[int, int, int], ...]] = (
    (0, 74, 1),
    (2, 71, 127),
    (15, 7, 0),
)


@dataclass(frozen=True)
class _PacingPlan:
    packets: tuple[tuple[int, int, int], ...] = _PACKETS
    ready: bool = True
    readiness_reason: str = "not ready for pacing"


@dataclass
class _PacingIO:
    """One event ledger for the injected opener, output, renderer and sleeper."""

    events: list[tuple[str, object]] = field(default_factory=list)
    sent: list[object] = field(default_factory=list)
    sleeps: list[float] = field(default_factory=list)
    opened: list[str] = field(default_factory=list)
    rendered: list[object] = field(default_factory=list)
    send_error: BaseException | None = None
    sleep_error: BaseException | None = None
    close_error: BaseException | None = None
    send_fail_after: int = 0
    sleep_fail_after: int = 0
    send_attempts: int = 0
    closed: int = 0

    def open_exact(self, port_name: str) -> _PacingIO:
        assert port_name == _PORT
        self.opened.append(port_name)
        return self

    def render(self, plan: object) -> Iterator[tuple[int, int, int]]:
        assert isinstance(plan, _PacingPlan)
        self.rendered.append(plan)
        return iter(plan.packets)

    def send(self, message: object) -> None:
        self.send_attempts += 1
        if self.send_error is not None and len(self.sent) >= self.send_fail_after:
            raise self.send_error
        self.sent.append(message)
        self.events.append(("send", message))

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.events.append(("sleep", seconds))
        if self.sleep_error is not None and len(self.sleeps) > self.sleep_fail_after:
            raise self.sleep_error

    def close(self) -> None:
        self.closed += 1
        self.events.append(("close", None))
        if self.close_error is not None:
            raise self.close_error


@pytest.fixture
def pacing_rig() -> Iterator[tuple[ArmedApplySession, _PacingIO, Device]]:
    io = _PacingIO()
    session = ArmedApplySession(opener=io, port_name=_PORT, arm_token=_TOKEN, sleep=io.sleep)
    session.arm(_TOKEN)
    session.confirm(_ACTION)
    try:
        yield session, io, get_device("analog_four_mk2")
    finally:
        session.disarm()


def test_pacing_api_defaults_preserve_unpaced_delivery() -> None:
    assert signature(ArmedApplySession).parameters["sleep"].default is time.sleep
    delay = signature(ArmedApplySession.apply).parameters["inter_message_delay_seconds"]
    assert delay.default == 0.0
    assert delay.kind is delay.KEYWORD_ONLY


@pytest.mark.parametrize("delay", [None, 0, 0.0, -0.0])
@pytest.mark.parametrize("packet_count", [0, 1, 3])
def test_apply_never_sleeps_when_delay_is_omitted_or_zero(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    delay: float | None,
    packet_count: int,
) -> None:
    session, io, device = pacing_rig
    packets = _PACKETS[:packet_count]
    kwargs = {} if delay is None else {"inter_message_delay_seconds": delay}
    result = session.apply(
        device,
        _PacingPlan(packets),
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        **kwargs,
    )
    assert result == ArmedApplyResult(
        device.device_id, True, packet_count, expected_count=packet_count
    )
    assert io.events == [("send", packet) for packet in packets]
    assert io.sent == list(packets)
    assert io.sleeps == []
    assert io.opened == [_PORT]
    assert session.is_armed
    assert io.closed == 0


@pytest.mark.parametrize("delay", [5e-324, 0.125, 1, 1.0])
@pytest.mark.parametrize("packet_count", [0, 1, 2, 3])
def test_apply_sleeps_only_between_packets_when_pacing_is_positive(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    delay: float,
    packet_count: int,
) -> None:
    session, io, device = pacing_rig
    packets = _PACKETS[:packet_count]
    result = session.apply(
        device,
        _PacingPlan(packets),
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        inter_message_delay_seconds=delay,
    )
    expected_events: list[tuple[str, object]] = []
    for index, packet in enumerate(packets):
        if index:
            expected_events.append(("sleep", delay))
        expected_events.append(("send", packet))
    assert io.events == expected_events
    assert io.sleeps == [delay] * max(0, packet_count - 1)
    assert io.sent == list(packets)
    assert result == ArmedApplyResult(
        device.device_id, True, packet_count, expected_count=packet_count
    )
    assert session.is_armed
    assert io.closed == 0


@pytest.mark.parametrize(
    "delay",
    [
        pytest.param(True, id="true"),
        pytest.param(False, id="false"),
        pytest.param(None, id="none"),
        pytest.param("0", id="zero-string"),
        pytest.param("0.25", id="numeric-string"),
        pytest.param(b"0.25", id="bytes"),
        pytest.param([], id="list"),
        pytest.param({}, id="mapping"),
        pytest.param((), id="tuple"),
        pytest.param(object(), id="object"),
        pytest.param(0j, id="complex"),
        pytest.param(Decimal("0.25"), id="decimal"),
        pytest.param(Fraction(1, 4), id="fraction"),
        pytest.param(-1, id="negative-int"),
        pytest.param(2, id="too-large-int"),
        pytest.param(-(10**1000), id="huge-negative-int"),
        pytest.param(10**1000, id="huge-positive-int"),
        pytest.param(-5e-324, id="just-below-zero"),
        pytest.param(1.0000000000000002, id="just-above-one"),
        pytest.param(float("nan"), id="nan"),
        pytest.param(float("inf"), id="positive-infinity"),
        pytest.param(float("-inf"), id="negative-infinity"),
    ],
)
@pytest.mark.parametrize("gate", ["confirmed", "unconfirmed", "unready", "persistent", "disarmed"])
@pytest.mark.parametrize("packet_count", [0, 1, 3])
def test_apply_refuses_invalid_delay_before_any_work_and_disarms_an_open_port(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    delay: object,
    gate: str,
    packet_count: int,
) -> None:
    session, io, device = pacing_rig
    action = "unconfirmed" if gate == "unconfirmed" else _ACTION
    if gate == "disarmed":
        session.disarm()
    with pytest.raises(ArmedApplyError, match="inter_message_delay_invalid") as caught:
        session.apply(
            device,
            _PacingPlan(_PACKETS[:packet_count], ready=gate != "unready"),
            action_id=action,
            mutates_kit=gate == "persistent",
            renderer=io.render,
            inter_message_delay_seconds=delay,  # type: ignore[arg-type]
        )
    assert caught.value.partial_outcome is None
    assert not session.is_armed
    assert io.closed == 1
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    session.disarm()
    assert io.closed == 1
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)


@pytest.mark.parametrize("error_type", [OSError, RuntimeError, ValueError, TypeError])
@pytest.mark.parametrize(
    ("stage", "fail_after", "sent_count", "sleep_count"),
    [
        ("send", 0, 0, 0),
        ("send", 1, 1, 1),
        ("send", 2, 2, 2),
        ("sleep", 0, 1, 1),
        ("sleep", 1, 2, 2),
    ],
)
def test_apply_reports_truthful_partial_counts_and_never_retries_when_send_or_sleep_fails(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    error_type: type[Exception],
    stage: str,
    fail_after: int,
    sent_count: int,
    sleep_count: int,
) -> None:
    session, io, device = pacing_rig
    error = error_type("injected pacing failure")
    if stage == "send":
        io.send_error, io.send_fail_after = error, fail_after
    else:
        io.sleep_error, io.sleep_fail_after = error, fail_after
    session.confirm("queued-action")
    with pytest.raises(ArmedApplyError, match="send_failed_auto_disarmed") as caught:
        session.apply(
            device,
            _PacingPlan(),
            action_id=_ACTION,
            mutates_kit=False,
            renderer=io.render,
            inter_message_delay_seconds=0.25,
        )
    assert caught.value.__cause__ is error
    assert caught.value.partial_outcome == ArmedApplyResult(
        device.device_id,
        False,
        sent_count,
        reason="armed_apply_send_failed_auto_disarmed",
        expected_count=3,
        status="partial",
    )
    assert caught.value.context == {
        "device_id": device.device_id,
        "action_id": _ACTION,
        "sent_count": sent_count,
        "expected_count": 3,
    }
    assert io.sent == list(_PACKETS[:sent_count])
    assert io.send_attempts == sent_count + (stage == "send")
    assert io.sleeps == [0.25] * sleep_count
    assert not session.is_armed
    assert io.closed == 1
    assert io.events[-1] == ("close", None)
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.apply(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm(_ACTION)
    assert io.opened == [_PORT]
    session.disarm()
    assert io.closed == 1
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id="queued-action", mutates_kit=False)


@pytest.mark.parametrize("error_type", [KeyboardInterrupt, SystemExit, CancelledError, LookupError])
@pytest.mark.parametrize(
    ("stage", "sent_count"),
    [("send", 0), ("send", 1), ("send", 2), ("sleep", 1), ("sleep", 2)],
)
def test_apply_preserves_interruption_identity_and_counts_when_send_or_sleep_is_cancelled(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    error_type: type[BaseException],
    stage: str,
    sent_count: int,
) -> None:
    session, io, device = pacing_rig
    error = error_type("injected interruption")
    if stage == "send":
        io.send_error, io.send_fail_after = error, sent_count
    else:
        io.sleep_error, io.sleep_fail_after = error, sent_count - 1
    with pytest.raises(error_type) as caught:
        session.apply(
            device,
            _PacingPlan(),
            action_id=_ACTION,
            mutates_kit=False,
            renderer=io.render,
            inter_message_delay_seconds=0.25,
        )
    assert caught.value is error
    assert error.__dict__["armed_apply_outcome"] == ArmedApplyResult(
        device.device_id,
        False,
        sent_count,
        reason="armed_apply_send_interrupted_auto_disarmed",
        expected_count=3,
        status="interrupted",
    )
    assert io.sent == list(_PACKETS[:sent_count])
    assert io.send_attempts == sent_count + (stage == "send")
    assert io.sleeps == [0.25] * sent_count
    assert not session.is_armed
    assert io.closed == 1
    session.disarm()
    assert io.closed == 1


def test_apply_retains_sleep_failure_outcome_when_close_also_fails(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
) -> None:
    session, io, device = pacing_rig
    io.sleep_error = OSError("sleep failed")
    io.close_error = RuntimeError("close failed")
    with pytest.raises(ArmedApplyError) as caught:
        session.apply(
            device,
            _PacingPlan(),
            action_id=_ACTION,
            mutates_kit=False,
            renderer=io.render,
            inter_message_delay_seconds=0.25,
        )
    assert caught.value.__cause__ is io.sleep_error
    outcome = caught.value.partial_outcome
    assert outcome is not None
    assert (outcome.sent_count, outcome.expected_count, outcome.status) == (1, 3, "partial")
    assert not session.is_armed
    assert io.closed == 1


def test_apply_requires_fresh_confirmation_for_each_paced_action_and_after_disarm(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
) -> None:
    session, io, device = pacing_rig
    session.apply(
        device,
        _PacingPlan(),
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        inter_message_delay_seconds=0.25,
    )
    session.confirm("different-action")
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)
    assert io.sent == list(_PACKETS)
    assert io.sleeps == [0.25, 0.25]
    session.disarm()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id="different-action", mutates_kit=False)
    assert io.sent == list(_PACKETS)
    assert io.closed == 1


@pytest.mark.parametrize("armed", [True, False])
def test_apply_cannot_bypass_arm_and_confirmation_gates_when_pacing_is_requested(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], armed: bool
) -> None:
    session, io, device = pacing_rig
    if not armed:
        session.disarm()
    with pytest.raises(ArmedApplyError, match="not_confirmed" if armed else "not_armed"):
        session.apply(
            device,
            _PacingPlan(),
            action_id="unconfirmed-action",
            mutates_kit=False,
            renderer=io.render,
            inter_message_delay_seconds=0.25,
        )
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    assert session.is_armed is armed


@pytest.mark.parametrize("mutates_kit", [None, True])
def test_apply_still_refuses_persistent_writes_when_pacing_is_requested(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], mutates_kit: bool | None
) -> None:
    session, io, device = pacing_rig
    kwargs = {} if mutates_kit is None else {"mutates_kit": mutates_kit}
    with pytest.raises(KitMutationUnsupportedError) as caught:
        session.apply(
            device,
            _PacingPlan(),
            action_id=_ACTION,
            renderer=io.render,
            inter_message_delay_seconds=0.25,
            **kwargs,
        )
    assert caught.value.partial_outcome is None
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    assert session.is_armed
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)


def test_apply_never_renders_or_sleeps_when_paced_plan_is_unready(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
) -> None:
    session, io, device = pacing_rig
    result = session.apply(
        device,
        _PacingPlan(ready=False),
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        inter_message_delay_seconds=0.25,
    )
    assert result == ArmedApplyResult(
        device.device_id, False, 0, "not ready for pacing", 0, "refused"
    )
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    assert session.is_armed
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        session.apply(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)
