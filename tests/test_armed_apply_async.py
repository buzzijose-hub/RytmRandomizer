"""Cooperative delivery through the shared ArmedApply state machine."""

from __future__ import annotations

import asyncio
from collections.abc import Iterable
from inspect import signature

import pytest
from test_armed_apply_pacing import (
    _ACTION,
    _PACKETS,
    _PORT,
    _TOKEN,
    _PacingIO,
    _PacingPlan,
)
from test_armed_apply_pacing import pacing_rig as pacing_rig

from rytm_randomizer.devices import Device, get_device
from rytm_randomizer.senders.armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    KitMutationUnsupportedError,
)

pytestmark = pytest.mark.fast


def test_apply_async_defaults_to_cooperative_asyncio_sleep() -> None:
    parameters = signature(ArmedApplySession.apply_async).parameters
    assert parameters["async_sleep"].default is asyncio.sleep
    assert parameters["async_sleep"].kind is parameters["async_sleep"].KEYWORD_ONLY
    assert parameters["inter_message_delay_seconds"].default == 0.0


@pytest.mark.parametrize("delay", [0.0, 0.125, 1.0])
@pytest.mark.parametrize("packet_count", [0, 1, 3])
def test_apply_async_preserves_sync_packet_and_pacing_order(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], delay: float, packet_count: int
) -> None:
    session, io, device = pacing_rig
    plan = _PacingPlan(_PACKETS[:packet_count])
    sync_result = session.apply(
        device,
        plan,
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        inter_message_delay_seconds=delay,
    )
    sync_events = list(io.events)
    io.events.clear()
    io.sent.clear()
    io.sleeps.clear()
    session.confirm(_ACTION)

    async def sleep(seconds: float) -> None:
        io.sleep(seconds)
        await asyncio.sleep(0)

    async_result = asyncio.run(
        session.apply_async(
            device,
            plan,
            action_id=_ACTION,
            mutates_kit=False,
            renderer=io.render,
            inter_message_delay_seconds=delay,
            async_sleep=sleep,
        )
    )
    assert async_result == sync_result
    assert io.sent == list(plan.packets)
    assert io.sleeps == [delay] * max(0, packet_count - 1)
    assert io.events == [
        event
        for index, packet in enumerate(plan.packets)
        for event in ([("sleep", delay)] if index else []) + [("send", packet)]
    ]
    assert [event for event in io.events if event[0] != "sleep"] == [
        event for event in sync_events if event[0] != "sleep"
    ]
    if delay:
        assert io.events == sync_events
    assert session.is_armed
    assert io.closed == 0


@pytest.mark.parametrize("delay", [0.0, 0.25])
@pytest.mark.parametrize("sent_count", [1, 2])
def test_apply_async_stops_at_disarm_during_an_await_without_writing_the_closed_port(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], delay: float, sent_count: int
) -> None:
    session, io, device = pacing_rig

    async def scenario() -> None:
        entered, release = asyncio.Event(), asyncio.Event()

        async def sleep(seconds: float) -> None:
            io.sleep(seconds)
            if len(io.sleeps) == sent_count:
                entered.set()
                await release.wait()

        task = asyncio.create_task(
            session.apply_async(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=io.render,
                inter_message_delay_seconds=delay,
                async_sleep=sleep,
            )
        )
        await asyncio.wait_for(entered.wait(), timeout=5)
        session.disarm()
        assert io.closed == 1
        release.set()
        with pytest.raises(ArmedApplyError, match="disarmed_during_send") as caught:
            await task
        assert caught.value.partial_outcome == ArmedApplyResult(
            device.device_id,
            False,
            sent_count,
            "armed_apply_disarmed_during_send",
            3,
            "interrupted",
        )
        assert caught.value.context["sent_count"] == sent_count
        assert caught.value.context["expected_count"] == 3
        assert io.sent == list(_PACKETS[:sent_count])
        assert io.send_attempts == sent_count
        assert not session.is_armed
        assert io.closed == 1

    asyncio.run(scenario())


def test_apply_async_zero_delay_default_yields_to_disarm_on_the_real_event_loop(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
) -> None:
    session, io, device = pacing_rig

    async def scenario() -> None:
        task = asyncio.create_task(
            session.apply_async(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=io.render,
            )
        )
        await asyncio.sleep(0)
        assert io.sent == [_PACKETS[0]]
        session.disarm()
        with pytest.raises(ArmedApplyError) as caught:
            await task
        outcome = caught.value.partial_outcome
        assert outcome is not None
        assert (outcome.sent_count, outcome.expected_count, outcome.status) == (1, 3, "interrupted")
        assert io.sent == [_PACKETS[0]]
        assert io.sleeps == []

    asyncio.run(scenario())


@pytest.mark.parametrize("sent_count", [1, 2])
def test_apply_async_task_cancellation_disarms_and_tags_the_true_partial_outcome(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], sent_count: int
) -> None:
    session, io, device = pacing_rig
    session.confirm("queued-action")

    async def scenario() -> None:
        entered, release = asyncio.Event(), asyncio.Event()

        async def sleep(seconds: float) -> None:
            io.sleep(seconds)
            if len(io.sleeps) == sent_count:
                entered.set()
                await release.wait()

        task = asyncio.create_task(
            session.apply_async(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=io.render,
                inter_message_delay_seconds=0.25,
                async_sleep=sleep,
            )
        )
        await asyncio.wait_for(entered.wait(), timeout=5)
        task.cancel("operator cancelled delivery")
        with pytest.raises(asyncio.CancelledError) as caught:
            await task
        assert caught.value.__dict__["armed_apply_outcome"] == ArmedApplyResult(
            device.device_id,
            False,
            sent_count,
            "armed_apply_send_interrupted_auto_disarmed",
            3,
            "interrupted",
        )
        assert task.cancelled()
        assert not session.is_armed
        assert io.sent == list(_PACKETS[:sent_count])
        assert io.send_attempts == sent_count
        assert io.closed == 1

    asyncio.run(scenario())
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm(_ACTION)
    assert io.opened == [_PORT]
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
        asyncio.run(
            session.apply_async(device, _PacingPlan(), action_id="queued-action", mutates_kit=False)
        )


@pytest.mark.parametrize("error_type", [OSError, RuntimeError, ValueError, TypeError])
@pytest.mark.parametrize("stage", ["send", "sleep"])
@pytest.mark.parametrize("packet_count", [0, 1, 3])
@pytest.mark.parametrize("fail_after", [0, 1, 2])
def test_apply_async_reports_send_and_sleep_failures_without_retry_for_any_burst_size(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    error_type: type[Exception],
    stage: str,
    packet_count: int,
    fail_after: int,
) -> None:
    session, io, device = pacing_rig
    error = error_type("injected async delivery failure")
    if stage == "send":
        io.send_error, io.send_fail_after = error, fail_after
    else:
        io.sleep_error, io.sleep_fail_after = error, fail_after

    async def sleep(seconds: float) -> None:
        io.sleep(seconds)

    coroutine = session.apply_async(
        device,
        _PacingPlan(_PACKETS[:packet_count]),
        action_id=_ACTION,
        mutates_kit=False,
        renderer=io.render,
        inter_message_delay_seconds=0.25,
        async_sleep=sleep,
    )
    failure_expected = fail_after < (packet_count if stage == "send" else packet_count - 1)
    if not failure_expected:
        assert asyncio.run(coroutine) == ArmedApplyResult(
            device.device_id, True, packet_count, expected_count=packet_count
        )
        assert io.sent == list(_PACKETS[:packet_count])
        assert session.is_armed
        return
    with pytest.raises(ArmedApplyError) as caught:
        asyncio.run(coroutine)
    sent_count = fail_after + (stage == "sleep")
    assert caught.value.__cause__ is error
    assert caught.value.partial_outcome == ArmedApplyResult(
        device.device_id,
        False,
        sent_count,
        "armed_apply_send_failed_auto_disarmed",
        packet_count,
        "partial",
    )
    assert caught.value.context["sent_count"] == sent_count
    assert caught.value.context["expected_count"] == packet_count
    assert io.sent == list(_PACKETS[:sent_count])
    assert io.send_attempts == sent_count + (stage == "send")
    assert not session.is_armed
    assert io.closed == 1


@pytest.mark.parametrize(
    "error_type", [KeyboardInterrupt, SystemExit, asyncio.CancelledError, LookupError]
)
@pytest.mark.parametrize(
    ("stage", "sent_count"), [("send", 0), ("send", 1), ("sleep", 1), ("sleep", 2)]
)
def test_apply_async_preserves_interruption_identity_and_counts(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    error_type: type[BaseException],
    stage: str,
    sent_count: int,
) -> None:
    session, io, device = pacing_rig
    error = error_type("injected async interruption")
    if stage == "send":
        io.send_error, io.send_fail_after = error, sent_count
    else:
        io.sleep_error, io.sleep_fail_after = error, sent_count - 1

    async def sleep(seconds: float) -> None:
        io.sleep(seconds)

    with pytest.raises(error_type) as caught:
        asyncio.run(
            session.apply_async(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=io.render,
                inter_message_delay_seconds=0.25,
                async_sleep=sleep,
            )
        )
    assert caught.value is error
    assert error.__dict__["armed_apply_outcome"] == ArmedApplyResult(
        device.device_id,
        False,
        sent_count,
        "armed_apply_send_interrupted_auto_disarmed",
        3,
        "interrupted",
    )
    assert io.sent == list(_PACKETS[:sent_count])
    assert not session.is_armed
    assert io.closed == 1


@pytest.mark.parametrize(
    "delay", [True, False, None, "0.25", -0.01, 1.01, float("nan"), float("inf"), 10**1000]
)
@pytest.mark.parametrize("packet_count", [0, 1, 3])
def test_apply_async_disarms_before_rendering_or_sending_when_pacing_is_invalid(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], delay: object, packet_count: int
) -> None:
    session, io, device = pacing_rig
    with pytest.raises(ArmedApplyError, match="inter_message_delay_invalid") as caught:
        asyncio.run(
            session.apply_async(
                device,
                _PacingPlan(_PACKETS[:packet_count]),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=io.render,
                inter_message_delay_seconds=delay,  # type: ignore[arg-type]
            )
        )
    assert caught.value.partial_outcome is None
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    assert not session.is_armed
    assert io.closed == 1


@pytest.mark.parametrize(
    "gate", ["disarmed", "unconfirmed", "unready", "persistent-default", "persistent-explicit"]
)
def test_apply_async_preserves_arm_confirmation_readiness_and_persistent_write_gates(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], gate: str
) -> None:
    session, io, device = pacing_rig
    if gate == "disarmed":
        session.disarm()
    action = "different-action" if gate == "unconfirmed" else _ACTION
    kwargs = {} if gate == "persistent-default" else {"mutates_kit": gate == "persistent-explicit"}
    coroutine = session.apply_async(
        device,
        _PacingPlan(ready=gate != "unready"),
        action_id=action,
        renderer=io.render,
        inter_message_delay_seconds=0.25,
        **kwargs,
    )
    if gate == "unready":
        assert asyncio.run(coroutine).status == "refused"
    else:
        error_type = (
            KitMutationUnsupportedError if gate.startswith("persistent") else ArmedApplyError
        )
        with pytest.raises(error_type):
            asyncio.run(coroutine)
    assert io.rendered == []
    assert io.sent == []
    assert io.sleeps == []
    if gate in ("unready", "persistent-default", "persistent-explicit"):
        with pytest.raises(ArmedApplyError, match="action_not_confirmed"):
            asyncio.run(
                session.apply_async(device, _PacingPlan(), action_id=_ACTION, mutates_kit=False)
            )


@pytest.mark.parametrize("lazy", [False, True])
@pytest.mark.parametrize(
    "error_type", [ValueError, KeyboardInterrupt, SystemExit, asyncio.CancelledError]
)
def test_apply_async_disarms_without_any_bytes_when_renderer_or_iterable_fails(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    lazy: bool,
    error_type: type[BaseException],
) -> None:
    session, io, device = pacing_rig
    error = error_type("render failed")

    def fail_iterable() -> Iterable[tuple[int, int, int]]:
        yield _PACKETS[0]
        raise error

    def render(_plan: object) -> Iterable[tuple[int, int, int]]:
        if lazy:
            return fail_iterable()
        raise error

    with pytest.raises(error_type) as caught:
        asyncio.run(
            session.apply_async(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=render,
                inter_message_delay_seconds=0.25,
            )
        )
    assert caught.value is error
    assert io.sent == []
    assert io.sleeps == []
    assert not session.is_armed
    assert io.closed == 1
    if not isinstance(error, Exception):
        assert error.__dict__["armed_apply_outcome"] == ArmedApplyResult(
            device.device_id,
            False,
            0,
            "armed_apply_send_interrupted_auto_disarmed",
            0,
            "interrupted",
        )
    else:
        assert "armed_apply_outcome" not in error.__dict__


def test_apply_async_refuses_a_replaced_port_after_disarm_and_explicit_rearm() -> None:
    old_port, new_port = _PacingIO(), _PacingIO()
    ports = iter((old_port, new_port))

    class Opener:
        def open_exact(self, _name: str) -> _PacingIO:
            return next(ports)

    session = ArmedApplySession(opener=Opener(), port_name=_PORT, arm_token=_TOKEN)
    session.arm(_TOKEN)
    session.confirm(_ACTION)

    async def sleep(_seconds: float) -> None:
        session.disarm()
        session.arm(_TOKEN)

    with pytest.raises(ArmedApplyError) as caught:
        asyncio.run(
            session.apply_async(
                get_device("analog_four_mk2"),
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=old_port.render,
                inter_message_delay_seconds=0.25,
                async_sleep=sleep,
            )
        )
    outcome = caught.value.partial_outcome
    assert outcome is not None
    assert (outcome.sent_count, outcome.expected_count, outcome.status) == (1, 3, "interrupted")
    assert old_port.sent == [_PACKETS[0]]
    assert new_port.sent == []
    assert old_port.closed == new_port.closed == 1
    assert not session.is_armed


@pytest.mark.parametrize("during_render", [False, True])
def test_sync_apply_also_rechecks_authority_immediately_before_each_send(
    during_render: bool,
) -> None:
    io = _PacingIO()

    def sleep(seconds: float) -> None:
        io.sleep(seconds)
        session.disarm()

    def render(plan: object) -> Iterable[tuple[int, int, int]]:
        if during_render:
            session.disarm()
        return io.render(plan)

    session = ArmedApplySession(opener=io, port_name=_PORT, arm_token=_TOKEN, sleep=sleep)
    session.arm(_TOKEN)
    session.confirm(_ACTION)
    with pytest.raises(ArmedApplyError) as caught:
        session.apply(
            get_device("analog_four_mk2"),
            _PacingPlan(),
            action_id=_ACTION,
            mutates_kit=False,
            renderer=render,
            inter_message_delay_seconds=0.25,
        )
    outcome = caught.value.partial_outcome
    assert outcome is not None
    assert (outcome.sent_count, outcome.expected_count, outcome.status) == (
        0 if during_render else 1,
        3,
        "interrupted",
    )
    assert io.sent == ([] if during_render else [_PACKETS[0]])
    assert io.closed == 1
    assert not session.is_armed
