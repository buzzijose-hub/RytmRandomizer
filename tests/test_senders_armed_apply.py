"""State-machine pins for the WS-4 ArmedApply seam.

The seam is the ONE outbound-transmit boundary (Live-but-Passive rule).
These tests pin the frozen contract:

* arm requires the exact token (empty / mismatched never arms),
* exact-name output resolution fails closed on missing/duplicate names,
* every apply requires a prior single-use per-action confirmation,
* an unready plan is refused via the ReadyPlan duck,
* a failed pre-write backup refuses the send,
* a provider error mid-send auto-disarms — and NEVER auto-re-arms,
* guarded_send / hardware_send route readiness through the same helper.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from rytm_randomizer.devices import get_device
from rytm_randomizer.senders.armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    plan_readiness,
)
from rytm_randomizer.senders.guarded import guarded_send
from rytm_randomizer.senders.hardware import (
    ExactOutputOpener,
    hardware_send,
)

pytestmark = pytest.mark.fast

_TOKEN = "operator-arm-token"
_PORT = "Elektron Analog Rytm MK2"


@dataclass
class _FakePlan:
    """Duck-typed ReadyPlan for the readiness gate."""

    ready: bool = True
    readiness_reason: str = ""


@dataclass
class _FakeDevice:
    """Duck-typed Device: identity + triple renderer only."""

    device_id: str = "fake_device"
    triples: tuple[tuple[int, int, int], ...] = ((0, 10, 20), (1, 11, 21))

    def to_cc_messages(self, _plan: object) -> tuple[tuple[int, int, int], ...]:
        return self.triples


@dataclass
class _FakePort:
    """Recording output port with optional failure injection."""

    sent: list[tuple[int, int, int]] = field(default_factory=list)
    fail_after: int | None = None
    closed: int = 0
    close_raises: bool = False

    def send(self, message: tuple[int, int, int]) -> None:
        if self.fail_after is not None and len(self.sent) >= self.fail_after:
            raise OSError("backend port died")
        self.sent.append(message)

    def close(self) -> None:
        self.closed += 1
        if self.close_raises:
            raise RuntimeError("close failed")


@dataclass
class _FakeOpener:
    """ExactPortOpener double with failure injection."""

    port: _FakePort = field(default_factory=_FakePort)
    raises: BaseException | None = None
    opened: list[str] = field(default_factory=list)

    def open_exact(self, port_name: str) -> _FakePort:
        self.opened.append(port_name)
        if self.raises is not None:
            raise self.raises
        return self.port


def _make_session(
    *,
    opener: _FakeOpener | None = None,
    backup_ok: bool = True,
    backup_raises: bool = False,
) -> tuple[ArmedApplySession, _FakeOpener, list[object]]:
    opener = opener if opener is not None else _FakeOpener()
    backups: list[object] = []

    def _backup(plan: object) -> bool:
        if backup_raises:
            raise RuntimeError("backup blew up")
        backups.append(plan)
        return backup_ok

    session = ArmedApplySession(
        opener=opener,
        port_name=_PORT,
        backup=_backup,
        arm_token=_TOKEN,
    )
    return session, opener, backups


# ---------------------------------------------------------------------------
# Construction gates.
# ---------------------------------------------------------------------------


def test_construction_requires_port_name() -> None:
    with pytest.raises(ArmedApplyError, match="port_name_required"):
        ArmedApplySession(
            opener=_FakeOpener(), port_name="", backup=lambda _p: True, arm_token=_TOKEN
        )


def test_construction_requires_arm_token() -> None:
    with pytest.raises(ArmedApplyError, match="token_required"):
        ArmedApplySession(
            opener=_FakeOpener(), port_name=_PORT, backup=lambda _p: True, arm_token=""
        )


def test_construction_requires_callable_backup_hook() -> None:
    with pytest.raises(ArmedApplyError, match="backup_hook_required"):
        ArmedApplySession(
            opener=_FakeOpener(),
            port_name=_PORT,
            backup=None,  # type: ignore[arg-type]
            arm_token=_TOKEN,
        )


# ---------------------------------------------------------------------------
# Arm state machine.
# ---------------------------------------------------------------------------


def test_arm_requires_exact_token_and_opens_port() -> None:
    session, opener, _ = _make_session()
    assert session.is_armed is False
    session.arm(_TOKEN)
    assert session.is_armed is True
    assert opener.opened == [_PORT]
    assert session.port_name == _PORT


def test_arm_refuses_empty_token() -> None:
    session, opener, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="token_required"):
        session.arm("")
    assert session.is_armed is False
    assert opener.opened == []


def test_arm_refuses_mismatched_token() -> None:
    session, opener, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="token_mismatch"):
        session.arm("wrong-token")
    assert session.is_armed is False
    assert opener.opened == []


def test_arm_refuses_non_string_token() -> None:
    session, _, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="token_required"):
        session.arm(None)  # type: ignore[arg-type]
    assert session.is_armed is False


def test_arm_while_armed_requires_explicit_disarm_first() -> None:
    session, _, _ = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="already_armed"):
        session.arm(_TOKEN)
    assert session.is_armed is True


def test_arm_stays_disarmed_when_opener_raises_backend_error() -> None:
    opener = _FakeOpener(raises=OSError("no backend"))
    session, _, _ = _make_session(opener=opener)
    with pytest.raises(ArmedApplyError, match="port_open_failed"):
        session.arm(_TOKEN)
    assert session.is_armed is False


def test_arm_stays_disarmed_when_opener_raises_armed_apply_error() -> None:
    opener = _FakeOpener(raises=ArmedApplyError("armed_apply_output_port_not_found: x"))
    session, _, _ = _make_session(opener=opener)
    with pytest.raises(ArmedApplyError, match="not_found"):
        session.arm(_TOKEN)
    assert session.is_armed is False


# ---------------------------------------------------------------------------
# Confirm gate.
# ---------------------------------------------------------------------------


def test_confirm_requires_armed_state() -> None:
    session, _, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm("apply-1")


def test_confirm_requires_non_empty_action_id() -> None:
    session, _, _ = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_id_required"):
        session.confirm("")


def test_apply_requires_armed_state() -> None:
    session, _, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")


def test_apply_requires_prior_confirmation() -> None:
    session, opener, _ = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert opener.port.sent == []


def test_confirmation_is_single_use() -> None:
    session, opener, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert result.ok is True
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert len(opener.port.sent) == 2


def test_confirmation_is_consumed_even_when_plan_is_refused() -> None:
    session, _, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    refused = session.apply(
        _FakeDevice(), _FakePlan(ready=False, readiness_reason="nope"), action_id="apply-1"
    )
    assert refused.ok is False
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")


# ---------------------------------------------------------------------------
# Plan readiness + backup gates.
# ---------------------------------------------------------------------------


def test_apply_refuses_unready_plan_with_duck_reason() -> None:
    session, opener, backups = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(
        _FakeDevice(),
        _FakePlan(ready=False, readiness_reason="missing routing"),
        action_id="apply-1",
    )
    assert result == ArmedApplyResult(
        device_id="fake_device",
        ok=False,
        sent_count=0,
        reason="missing routing",
        backup_taken=False,
    )
    assert opener.port.sent == []
    assert backups == []


def test_apply_refuses_plan_without_ready_attribute() -> None:
    session, opener, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), object(), action_id="apply-1")
    assert result.ok is False
    assert result.reason == "plan is not ready"
    assert opener.port.sent == []


def test_backup_runs_before_send_and_is_recorded() -> None:
    session, opener, backups = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    plan = _FakePlan()
    result = session.apply(_FakeDevice(), plan, action_id="apply-1")
    assert result.ok is True
    assert result.backup_taken is True
    assert backups == [plan]
    assert opener.port.sent == [(0, 10, 20), (1, 11, 21)]
    assert result.sent_count == 2


def test_backup_failure_refuses_send() -> None:
    session, opener, _ = _make_session(backup_ok=False)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert result.ok is False
    assert result.backup_taken is False
    assert "backup failed" in result.reason
    assert opener.port.sent == []
    assert session.is_armed is True  # backup refusal does not disarm


def test_backup_exception_refuses_send() -> None:
    session, opener, _ = _make_session(backup_raises=True)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert result.ok is False
    assert opener.port.sent == []


def test_non_mutating_apply_skips_backup() -> None:
    session, opener, backups = _make_session(backup_ok=False)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert result.ok is True
    assert result.backup_taken is False
    assert backups == []
    assert len(opener.port.sent) == 2


# ---------------------------------------------------------------------------
# Auto-disarm + never-auto-re-arm.
# ---------------------------------------------------------------------------


def test_provider_error_mid_send_auto_disarms() -> None:
    opener = _FakeOpener(port=_FakePort(fail_after=1))
    session, _, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(ArmedApplyError, match="auto_disarmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert session.is_armed is False
    assert opener.port.sent == [(0, 10, 20)]


def test_never_auto_re_arms_after_provider_error() -> None:
    opener = _FakeOpener(port=_FakePort(fail_after=0))
    session, _, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(ArmedApplyError, match="auto_disarmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    # Still disarmed: apply and confirm both refuse until an explicit arm.
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-2")
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm("apply-2")
    # An explicit re-arm is required — and works.
    opener.port.fail_after = None
    session.arm(_TOKEN)
    assert session.is_armed is True


def test_disarm_is_idempotent_and_closes_port() -> None:
    session, opener, _ = _make_session()
    session.arm(_TOKEN)
    session.disarm()
    assert session.is_armed is False
    assert opener.port.closed == 1
    session.disarm()  # idempotent — no second close, no raise
    assert opener.port.closed == 1


def test_disarm_swallows_port_close_errors() -> None:
    opener = _FakeOpener(port=_FakePort(close_raises=True))
    session, _, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.disarm()
    assert session.is_armed is False


def test_disarm_clears_pending_confirmations() -> None:
    session, _, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    session.disarm()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")


def test_disarm_handles_port_without_close_method() -> None:
    @dataclass
    class _NoClosePort:
        sent: list[tuple[int, int, int]] = field(default_factory=list)

        def send(self, message: tuple[int, int, int]) -> None:
            self.sent.append(message)

    @dataclass
    class _NoCloseOpener:
        port: _NoClosePort = field(default_factory=_NoClosePort)

        def open_exact(self, _port_name: str) -> _NoClosePort:
            return self.port

    session = ArmedApplySession(
        opener=_NoCloseOpener(), port_name=_PORT, backup=lambda _p: True, arm_token=_TOKEN
    )
    session.arm(_TOKEN)
    session.disarm()
    assert session.is_armed is False


# ---------------------------------------------------------------------------
# ExactOutputOpener — fail-closed exact-name resolution.
# ---------------------------------------------------------------------------


@dataclass
class _FakeProvider:
    names: tuple[str, ...] = (_PORT, "Other Port")
    port: object = field(default_factory=_FakePort)
    opened: list[str] = field(default_factory=list)

    def list_output_names(self) -> tuple[str, ...]:
        return self.names

    def open_output(self, port_name: str) -> object:
        self.opened.append(port_name)
        return self.port


def test_exact_opener_opens_single_unambiguous_match() -> None:
    provider = _FakeProvider()
    opener = ExactOutputOpener(provider)
    port = opener.open_exact(_PORT)
    assert port is provider.port
    assert provider.opened == [_PORT]


def test_exact_opener_fails_closed_on_missing_name() -> None:
    provider = _FakeProvider(names=("Other Port",))
    with pytest.raises(ArmedApplyError, match="not_found"):
        ExactOutputOpener(provider).open_exact(_PORT)
    assert provider.opened == []


def test_exact_opener_fails_closed_on_duplicate_names() -> None:
    provider = _FakeProvider(names=(_PORT, _PORT))
    with pytest.raises(ArmedApplyError, match="ambiguous"):
        ExactOutputOpener(provider).open_exact(_PORT)
    assert provider.opened == []


def test_exact_opener_rejects_empty_port_name() -> None:
    with pytest.raises(ArmedApplyError, match="port_name_required"):
        ExactOutputOpener(_FakeProvider()).open_exact("")


def test_exact_opener_rejects_port_without_send() -> None:
    provider = _FakeProvider(port=object())
    with pytest.raises(ArmedApplyError, match="invalid_output_port"):
        ExactOutputOpener(provider).open_exact(_PORT)


# ---------------------------------------------------------------------------
# plan_readiness routing — guarded/hardware share the same duck.
# ---------------------------------------------------------------------------


def test_plan_readiness_duck() -> None:
    assert plan_readiness(_FakePlan()) == (True, "")
    assert plan_readiness(_FakePlan(ready=False, readiness_reason="why")) == (False, "why")
    assert plan_readiness(object()) == (False, "plan is not ready")


def test_guarded_send_routes_readiness_through_the_seam() -> None:
    device = get_device("analog_rytm_mk2")
    refused = guarded_send(device, _FakePlan(ready=False, readiness_reason="blocked"))
    assert refused.ready is False
    assert refused.reason == "blocked"
    assert refused.sent_count == 0


def test_hardware_send_routes_readiness_through_the_seam() -> None:
    device = get_device("analog_rytm_mk2")
    sent: list[tuple[int, int, int]] = []

    class _Sender:
        def send(self, message: tuple[int, int, int]) -> None:
            sent.append(message)

    refused = hardware_send(
        device, _FakePlan(ready=False, readiness_reason="blocked"), sender=_Sender(), armed=True
    )
    assert refused.ready is False
    assert refused.reason == "blocked"
    assert sent == []


def test_armed_apply_error_is_taxonomy_member_with_fingerprint() -> None:
    from rytm_randomizer.observability.errors import MidiError

    assert issubclass(ArmedApplyError, MidiError)
    assert issubclass(ArmedApplyError, RuntimeError)
    assert ArmedApplyError.fingerprint == "midi.armed_apply.refused"
