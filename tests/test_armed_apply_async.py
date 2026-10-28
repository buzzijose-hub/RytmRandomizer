"""Cooperative delivery through the shared ArmedApply state machine."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Iterable
from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

from conftest import (
    _ACTION,
    _PACKETS,
    _PORT,
    _TOKEN,
    _PacingIO,
    _PacingPlan,
)
from rytm_randomizer.devices import Device, get_device
from rytm_randomizer.senders.armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    KitMutationUnsupportedError,
)

pytestmark = pytest.mark.fast


@pytest.mark.parametrize("driver", ["sync", "async"])
@pytest.mark.parametrize("stage", ["render", "send", "sleep"])
@pytest.mark.parametrize("close_fails", [False, True])
def test_unexpected_programmer_faults_still_release_the_owned_port(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    driver: str,
    stage: str,
    close_fails: bool,
) -> None:
    session, io, device = pacing_rig

    class UnexpectedFault(Exception):
        pass

    failure = UnexpectedFault("unmodeled collaborator fault")
    if close_fails:
        io.close_error = KeyError("close failed")
    if stage == "send":
        io.send_error, io.send_fail_after = failure, 1

    def render(plan: object) -> Iterable[tuple[int, int, int]]:
        if stage == "render":
            raise failure
        return io.render(plan)

    def sleep(delay: float) -> None:
        if stage == "sleep":
            raise failure
        io.sleep(delay)

    async def async_sleep(delay: float) -> None:
        sleep(delay)

    with pytest.raises(KeyError if close_fails else UnexpectedFault) as caught:
        if driver == "async":
            asyncio.run(
                session.apply_async(
                    device,
                    _PacingPlan(),
                    action_id=_ACTION,
                    mutates_kit=False,
                    renderer=render,
                    inter_message_delay_seconds=0.02,
                    async_sleep=async_sleep,
                )
            )
        else:
            session._sleep = sleep
            session.apply(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=render,
                inter_message_delay_seconds=0.02,
            )
    assert caught.value is (io.close_error if close_fails else failure)
    assert not session.is_armed and io.closed == 1
    assert len(io.sent) == (0 if stage == "render" else 1)


def test_apply_async_defaults_to_cooperative_asyncio_sleep() -> None:
    parameters = signature(ArmedApplySession.apply_async).parameters
    assert parameters["async_sleep"].default is asyncio.sleep
    assert parameters["async_sleep"].kind is parameters["async_sleep"].KEYWORD_ONLY
    assert parameters["inter_message_delay_seconds"].default == 0.0


@pytest.mark.parametrize("driver", ["sync", "async"])
def test_successful_apply_does_not_reraise_a_callers_handled_exception(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], driver: str
) -> None:
    session, io, device = pacing_rig

    async def async_apply() -> ArmedApplyResult:
        try:
            raise LookupError("already handled by the caller")
        except LookupError:
            return await session.apply_async(
                device, _PacingPlan(), action_id=_ACTION, mutates_kit=False, renderer=io.render
            )

    if driver == "async":
        result = asyncio.run(async_apply())
    else:
        try:
            raise LookupError("already handled by the caller")
        except LookupError:
            result = session.apply(
                device, _PacingPlan(), action_id=_ACTION, mutates_kit=False, renderer=io.render
            )
    assert result == ArmedApplyResult(
        device.device_id, True, len(_PACKETS), expected_count=len(_PACKETS)
    )
    assert io.sent == list(_PACKETS)
    assert session.is_armed and io.closed == 0


@pytest.mark.parametrize("driver", ["sync", "async"])
@pytest.mark.parametrize("accepted", [0, 1, 2])
def test_delivery_progress_survives_cleanup_masking_the_original_fault(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], driver: str, accepted: int
) -> None:
    session, io, device = pacing_rig
    assert session.delivery_progress is None
    io.send_error, io.send_fail_after = OSError("send failed"), accepted
    io.close_error = KeyError("close failed")
    with pytest.raises(KeyError):
        if driver == "async":
            asyncio.run(
                session.apply_async(
                    device, _PacingPlan(), action_id=_ACTION, mutates_kit=False, renderer=io.render
                )
            )
        else:
            session.apply(
                device, _PacingPlan(), action_id=_ACTION, mutates_kit=False, renderer=io.render
            )
    progress = session.delivery_progress
    assert progress is not None
    assert (
        progress.action_id,
        progress.device_id,
        progress.sent_count,
        progress.expected_count,
    ) == (_ACTION, device.device_id, accepted, len(_PACKETS))
    with pytest.raises(FrozenInstanceError):
        progress.sent_count = 999
    assert not session.is_armed and io.closed == 1
    session.disarm()
    assert session.delivery_progress is progress


@pytest.mark.parametrize("driver", ["sync", "async"])
@pytest.mark.parametrize("ancestor_capture", [False, True])
@pytest.mark.parametrize(
    "error_type", [asyncio.CancelledError, KeyboardInterrupt, SystemExit, GeneratorExit]
)
@pytest.mark.parametrize(
    ("stage", "sent_count"),
    [
        ("render", 0),
        ("lazy-render", 0),
        ("send", 0),
        ("send", 1),
        ("send", 2),
        ("sleep", 1),
        ("sleep", 2),
    ],
)
def test_apply_preserves_control_flow_and_cleanup_diagnostics_when_close_fails(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    driver: str,
    ancestor_capture: bool,
    error_type: type[BaseException],
    stage: str,
    sent_count: int,
) -> None:
    session, io, device = pacing_rig
    if ancestor_capture:
        monkeypatch.setattr(logging.getLogger("rytm_randomizer"), "handlers", [caplog.handler])
    monkeypatch.setattr(logging.getLogger("rytm_randomizer"), "propagate", True)
    # Capture at the emission site, independently of prior package/root setup.
    logger = logging.getLogger("rytm_randomizer.senders.armed_apply")
    monkeypatch.setattr(logger, "handlers", [caplog.handler])
    monkeypatch.setattr(logger, "propagate", False)
    caplog.set_level(logging.WARNING, logger="rytm_randomizer.senders.armed_apply")
    interruption = error_type("delivery interrupted")
    sensitive_detail = "C:/private/operator-token/close failed"
    cleanup_error = KeyError(sensitive_detail)
    io.close_error = cleanup_error
    session.confirm("queued-action")
    if stage == "send":
        io.send_error, io.send_fail_after = interruption, sent_count
    elif stage == "sleep":
        io.sleep_error, io.sleep_fail_after = interruption, sent_count - 1

    def fail_iterable() -> Iterable[tuple[int, int, int]]:
        yield _PACKETS[0]
        raise interruption

    def render(plan: object) -> Iterable[tuple[int, int, int]]:
        if stage == "render":
            raise interruption
        if stage == "lazy-render":
            return fail_iterable()
        return io.render(plan)

    async def sleep(seconds: float) -> None:
        io.sleep(seconds)

    with pytest.raises(error_type) as caught:
        if driver == "async":
            asyncio.run(
                session.apply_async(
                    device,
                    _PacingPlan(),
                    action_id=_ACTION,
                    mutates_kit=False,
                    renderer=render,
                    inter_message_delay_seconds=0.25,
                    async_sleep=sleep,
                )
            )
        else:
            session.apply(
                device,
                _PacingPlan(),
                action_id=_ACTION,
                mutates_kit=False,
                renderer=render,
                inter_message_delay_seconds=0.25,
            )
    assert caught.value is interruption
    assert interruption.__cause__ is cleanup_error
    expected = 0 if stage in ("render", "lazy-render") else len(_PACKETS)
    outcome = interruption.__dict__["armed_apply_outcome"]
    assert outcome == ArmedApplyResult(
        device.device_id,
        False,
        sent_count,
        "armed_apply_send_interrupted_auto_disarmed",
        expected,
        "interrupted",
    )
    notes = " ".join(interruption.__notes__)
    assert "armed_apply_cleanup_failed" in notes
    for field in (
        f"action_id={_ACTION}",
        f"device_id={device.device_id}",
        "error_type=KeyError",
        f"sent_count={sent_count}",
        f"expected_count={expected}",
    ):
        assert field in notes
    assert sensitive_detail not in notes
    records = [record for record in caplog.records if record.msg == "armed_apply_cleanup_failed"]
    assert len(records) == 1
    record = records[0]
    assert record.name == "rytm_randomizer.senders.armed_apply"
    assert record.levelname == "WARNING"
    assert {
        key: record.__dict__[key]
        for key in ("action_id", "device_id", "error_type", "sent_count", "expected_count")
    } == {
        "action_id": _ACTION,
        "device_id": device.device_id,
        "error_type": "KeyError",
        "sent_count": sent_count,
        "expected_count": expected,
    }
    assert record.exc_info is None and record.exc_text is None
    assert sensitive_detail not in str(record.__dict__)
    with pytest.raises(FrozenInstanceError):
        outcome.sent_count = 999
    with pytest.raises(FrozenInstanceError):
        outcome.expected_count = 999
    progress = session.delivery_progress
    if expected:
        assert progress is not None
        assert (progress.sent_count, progress.expected_count) == (sent_count, expected)
        with pytest.raises(FrozenInstanceError):
            progress.sent_count = 999
        with pytest.raises(FrozenInstanceError):
            progress.expected_count = 999
    else:
        assert progress is None
    assert io.sent == list(_PACKETS[:sent_count])
    assert io.send_attempts == sent_count + (stage == "send")
    assert io.opened == [_PORT]
    assert not session.is_armed and io.closed == 1
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm("queued-action")
    session.disarm()
    assert io.closed == 1


@pytest.mark.parametrize("delay", [0.0, 0.25])
@pytest.mark.parametrize("sent_count", [1, 2])
def test_apply_async_task_stays_cancelled_when_close_fails(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], delay: float, sent_count: int
) -> None:
    session, io, device = pacing_rig
    cleanup_error = KeyError("close failed during task cancellation")
    io.close_error = cleanup_error

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
        task.cancel("operator cancelled delivery")
        with pytest.raises(asyncio.CancelledError) as caught:
            await task
        assert caught.value.args == ("operator cancelled delivery",)
        assert caught.value.__cause__ is cleanup_error
        outcome = caught.value.__dict__["armed_apply_outcome"]
        assert (outcome.sent_count, outcome.expected_count, outcome.status) == (
            sent_count,
            len(_PACKETS),
            "interrupted",
        )
        assert task.cancelled()

    asyncio.run(scenario())
    progress = session.delivery_progress
    assert progress is not None
    assert (progress.sent_count, progress.expected_count) == (sent_count, len(_PACKETS))
    assert io.sent == list(_PACKETS[:sent_count])
    assert io.send_attempts == sent_count
    assert io.opened == [_PORT]
    assert not session.is_armed and io.closed == 1


@pytest.mark.parametrize("driver", ["sync", "async"])
def test_new_attempt_and_explicit_rearm_clear_previous_progress(
    pacing_rig: tuple[ArmedApplySession, _PacingIO, Device], driver: str
) -> None:
    session, io, device = pacing_rig

    def apply(action: str) -> ArmedApplyResult:
        if driver == "async":
            return asyncio.run(
                session.apply_async(
                    device, _PacingPlan(), action_id=action, mutates_kit=False, renderer=io.render
                )
            )
        return session.apply(
            device, _PacingPlan(), action_id=action, mutates_kit=False, renderer=io.render
        )

    assert apply(_ACTION).ok
    assert session.delivery_progress.sent_count == len(_PACKETS)
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        apply("unconfirmed-next-action")
    assert session.delivery_progress is None
    session.confirm(_ACTION)
    assert apply(_ACTION).ok
    session.disarm()
    assert session.delivery_progress is not None
    session.arm(_TOKEN)
    assert session.delivery_progress is None


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
