"""The armed cockpit SEND must route through the ArmedApply seam.

Regression suite for the "the seam is dead code" defect: the seam was
whitelisted, documented, and fully tested in isolation — but no production
caller ever reached it. The cockpit SEND handler called
``session.device.apply_send_plan(...)`` directly, and the arm handler
installed a *separate* real-MIDI adapter holding its own output port. Two
handles existed and none of the promised guards (per-action confirm, plan
readiness, auto-disarm, no-second-port) protected a real send.

These tests drive the whole path with fake providers — no hardware, no real
``mido`` — and pin the four properties the fix must deliver:

a. an armed SEND reaches :meth:`ArmedApplySession.apply`,
b. it is refused without a per-action confirm,
c. a provider error auto-disarms the session,
d. arming never opens a second port.

Plus the invariant that makes the fix safe to ship: the **unarmed** path is
byte-identical to before (its acks and events are pinned elsewhere and must
not move).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from cockpit.conftest import _make_default_snapshot

from rytm_randomizer.cockpit.data import CockpitSendPlan, SendPlanPacket
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.device.connection import set_active_connection_manager
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.protocol import EVENT_SESSION_STATUS
from rytm_randomizer.cockpit.ws.session import CockpitSession

pytestmark = pytest.mark.fast

_ARM_TOKEN = "operator-arm-token"
_OUT_PORT = "Elektron Analog Rytm MK2 Out"


@dataclass
class _FakeOutPort:
    """Records every message the armed seam transmits."""

    name: str = _OUT_PORT
    sent: list[object] = field(default_factory=list)
    closed: int = 0
    fail_after: int | None = None

    def send(self, message: object) -> None:
        if self.fail_after is not None and len(self.sent) >= self.fail_after:
            raise OSError("backend port died mid-send")
        self.sent.append(message)

    def close(self) -> None:
        self.closed += 1


@dataclass
class _FakeProvider:
    """Counts every ``open_output`` so a second port cannot go unnoticed."""

    names: tuple[str, ...] = (_OUT_PORT,)
    port: _FakeOutPort = field(default_factory=_FakeOutPort)
    open_calls: list[str] = field(default_factory=list)

    def list_output_names(self) -> tuple[str, ...]:
        return self.names

    def open_output(self, port_name: str) -> _FakeOutPort:
        self.open_calls.append(port_name)
        return self.port


def _make_session(tmp_path: Path) -> CockpitSession:
    initial = _make_default_snapshot()
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=HistoryStore(),
        device=MockDeviceAdapter(initial=initial),
    )
    session.history_store.initial(initial)
    return session


def _dispatch(session: CockpitSession, cmd: dict, request_id: str = "req-1") -> dict:
    return asyncio.run(handlers.handle_command({"request_id": request_id, "command": cmd}, session))


def _arm(session: CockpitSession) -> dict:
    return _dispatch(
        session,
        {
            "type": "arm",
            "arm_token": _ARM_TOKEN,
            "confirm": True,
            "port_name": _OUT_PORT,
        },
    )


def _plan(*, ready: bool = True, plan_id: str = "plan-1") -> CockpitSendPlan:
    """A prepared plan whose packets already carry resolved wire triples."""

    return CockpitSendPlan(
        plan_id=plan_id,
        candidate_id="cand-1",
        source_snapshot_id="snap-1",
        profile_id="scene-industrial",
        ready=ready,
        readiness_reason="ready" if ready else "candidate_high_risk",
        safety_status="armed" if ready else "high_risk",
        packets=(
            SendPlanPacket(pad_id=1, parameter="tun", channel=0, control=16, value=42),
            SendPlanPacket(pad_id=2, parameter="dec", channel=0, control=17, value=90),
        ),
        locked_pad_ids=frozenset(),
        blocked_reasons=() if ready else ("candidate_high_risk",),
    )


def _stage_send(session: CockpitSession, *, ready: bool = True) -> CockpitSendPlan:
    """Put a candidate + prepared plan on the session so SEND is reachable."""

    _dispatch(session, {"type": "select_profile", "profile_id": "scene-industrial"})
    _dispatch(session, {"type": "set_depth", "depth": 0.45})
    assert session.current_candidate is not None
    plan = _plan(ready=ready)
    session.current_send_plan = plan
    return plan


@pytest.fixture(autouse=True)
def _no_active_manager() -> object:
    set_active_connection_manager(None)
    yield
    set_active_connection_manager(None)


# ---------------------------------------------------------------------------
# (a) An armed SEND reaches ArmedApplySession.apply — and only it transmits.
# ---------------------------------------------------------------------------


def test_armed_send_transmits_through_the_seam(tmp_path: Path) -> None:
    """The bytes leave via the seam's port, carrying the plan's own packets."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    plan = _stage_send(session)

    applied: list[tuple[object, str, bool]] = []
    real_apply = session.armed_apply.apply  # type: ignore[union-attr]

    def _spy(device, plan_arg, *, action_id, mutates_kit=True, renderer=None):  # type: ignore[no-untyped-def]
        applied.append((plan_arg, action_id, mutates_kit))
        return real_apply(
            device,
            plan_arg,
            action_id=action_id,
            mutates_kit=mutates_kit,
            renderer=renderer,
        )

    session.armed_apply.apply = _spy  # type: ignore[union-attr, assignment, method-assign]

    ack = _dispatch(session, {"type": "send", "confirm": True})

    assert ack["ok"] is True
    # (a) the seam's apply ran, with the prepared plan and a RAM-only intent.
    assert applied == [(plan, plan.plan_id, False)]
    # The wire triples are exactly the plan's preflight-resolved packets —
    # nothing is recomputed at the hardware boundary.
    assert provider.port.sent == [(0, 16, 42), (0, 17, 90)]


def test_armed_send_refuses_an_unready_plan_without_transmitting(tmp_path: Path) -> None:
    """The handler's own readiness gate fires before the seam is even reached."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session, ready=False)

    ack = _dispatch(session, {"type": "send", "confirm": True})

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert provider.port.sent == []


def test_armed_send_refuses_when_the_seam_reports_an_unready_plan(
    tmp_path: Path,
) -> None:
    """A plan the seam refuses on readiness never reaches the wire either."""

    from rytm_randomizer.senders.armed_apply import ArmedApplyResult

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session)

    def _refuse(*_args: object, **_kwargs: object) -> ArmedApplyResult:
        return ArmedApplyResult(
            device_id="analog_rytm_mk2", ok=False, sent_count=0, reason="not ready"
        )

    session.armed_apply.apply = _refuse  # type: ignore[union-attr, assignment, method-assign]

    ack = _dispatch(session, {"type": "send", "confirm": True})

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert provider.port.sent == []
    # State is untouched: the plan is still staged for a retry.
    assert session.current_send_plan is not None


# ---------------------------------------------------------------------------
# (b) No per-action confirm -> refused.
# ---------------------------------------------------------------------------


def test_armed_send_is_refused_without_a_per_action_confirm(tmp_path: Path) -> None:
    """ "Armed" is a session state; each individual write needs its own yes."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session)

    ack = _dispatch(session, {"type": "send"})

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert "confirm" in ack["message"]
    assert provider.port.sent == []
    # Nothing was consumed: the plan and candidate survive for a retry.
    assert session.current_send_plan is not None
    assert session.current_candidate is not None
    # And the session is still armed — a missing confirm is not a fault.
    assert handlers.session_is_armed(session) is True


@pytest.mark.parametrize("confirm", [False, "true", 1, None])
def test_armed_send_requires_confirm_to_be_exactly_true(tmp_path: Path, confirm: object) -> None:
    """Truthy-but-not-``True`` never counts as an operator confirmation."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session)

    ack = _dispatch(session, {"type": "send", "confirm": confirm})

    assert ack["ok"] is False
    assert provider.port.sent == []


# ---------------------------------------------------------------------------
# (c) A provider error auto-disarms.
# ---------------------------------------------------------------------------


def test_armed_send_auto_disarms_on_provider_error(tmp_path: Path) -> None:
    """A dead port drops the session to passive; it never auto-re-arms."""

    session = _make_session(tmp_path)
    provider = _FakeProvider(port=_FakeOutPort(fail_after=0))
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session)

    ack = _dispatch(session, {"type": "send", "confirm": True})

    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    # (c) auto-disarmed, and the handler cleared the rest of the armed state.
    assert session.armed_apply is None
    assert handlers.session_is_armed(session) is False
    # The operator is told, via the journal and a fresh status broadcast.
    assert session.error_journal.entries[-1].fingerprint == "cockpit.arm.send_refused"
    assert session.pending_events[-1]["type"] == EVENT_SESSION_STATUS
    assert session.pending_events[-1]["armed"] is False
    # Nothing was written to history: the send did not happen.
    assert session.unsaved_sends == 0


def test_a_refused_armed_send_that_stays_armed_does_not_tear_down(
    tmp_path: Path,
) -> None:
    """Only an auto-disarming failure tears the session down.

    A seam refusal that leaves the session armed (e.g. a confirmation
    replay) must not disarm the operator as a side effect.
    """

    from rytm_randomizer.senders.armed_apply import ArmedApplyError

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    _stage_send(session)

    def _raise(*_args: object, **_kwargs: object) -> None:
        raise ArmedApplyError("armed_apply_action_not_confirmed")

    session.armed_apply.apply = _raise  # type: ignore[union-attr, assignment, method-assign]

    ack = _dispatch(session, {"type": "send", "confirm": True})

    assert ack["ok"] is False
    assert session.armed_apply is not None
    assert handlers.session_is_armed(session) is True


# ---------------------------------------------------------------------------
# (d) Exactly one port is ever opened.
# ---------------------------------------------------------------------------


def test_arming_and_sending_opens_exactly_one_port(tmp_path: Path) -> None:
    """The two-handles defect, pinned: one arm + N sends = one open_output."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider

    assert _arm(session)["ok"] is True
    assert provider.open_calls == [_OUT_PORT]

    for index in range(3):
        _stage_send(session)
        # Each SEND needs a distinct plan_id so its confirmation is single-use.
        session.current_send_plan = _plan(plan_id=f"plan-{index}")
        assert _dispatch(session, {"type": "send", "confirm": True})["ok"] is True

    # (d) still exactly one port — no second adapter, no re-open per send.
    assert provider.open_calls == [_OUT_PORT]
    assert len(provider.port.sent) == 6


def test_disarm_closes_the_single_port_and_stops_transmitting(tmp_path: Path) -> None:
    """After disarm the passive path resumes and nothing reaches the wire."""

    session = _make_session(tmp_path)
    provider = _FakeProvider()
    session.arm_port_provider = provider
    assert _arm(session)["ok"] is True
    assert _dispatch(session, {"type": "disarm"})["ok"] is True
    assert provider.port.closed == 1

    _stage_send(session)
    ack = _dispatch(session, {"type": "send"})

    # Unarmed SEND succeeds without a confirm (the historical mock contract)
    # and transmits nothing.
    assert ack["ok"] is True
    assert provider.port.sent == []
    assert provider.open_calls == [_OUT_PORT]


# ---------------------------------------------------------------------------
# The unarmed path must stay byte-identical.
# ---------------------------------------------------------------------------


def test_unarmed_send_needs_no_confirm_and_never_touches_the_seam(
    tmp_path: Path,
) -> None:
    """A mock session behaves exactly as it did before the seam was wired.

    The unarmed acks/events are pinned by the integration suites; this test
    guards the specific risk that the new armed branch leaks a confirmation
    requirement into the passive path.
    """

    session = _make_session(tmp_path)
    _stage_send(session)

    ack = _dispatch(session, {"type": "send"})

    assert ack["ok"] is True
    assert ack["send_plan_id"] == "plan-1"
    assert ack["new_snapshot_id"]
    assert session.armed_apply is None
    assert session.unsaved_sends == 1
    assert [event["type"] for event in session.pending_events] == [
        "snapshot_changed",
        "history_updated",
        "mutation_previewed",
        "send_plan_changed",
        EVENT_SESSION_STATUS,
    ]
