"""State-machine pins for the WS-4 ArmedApply seam.

The seam is the ONE outbound-transmit boundary (Live-but-Passive rule).
These tests pin the frozen contract:

* arm requires the exact token (empty / mismatched never arms),
* exact-name output resolution fails closed on missing/duplicate names,
* every apply requires a prior single-use per-action confirmation,
* an unready plan is refused via the ReadyPlan duck,
* a kit/sound-MUTATING apply is refused outright (no backup, no restore),
* a provider error mid-send auto-disarms — and NEVER auto-re-arms,
* a close-less port is refused AT ARM TIME (deterministic teardown is
  unimplementable without ``close``),
* every exit path — provider error, ``KeyboardInterrupt`` / ``SystemExit``
  mid-burst, context-manager exit — disarms and closes the port exactly
  once, and never swallows the interrupt,
* partial delivery is reported (``sent_count`` / ``expected_count`` /
  ``status``), not discarded,
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
    KitMutationUnsupportedError,
    PortNotClosableError,
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
) -> tuple[ArmedApplySession, _FakeOpener]:
    opener = opener if opener is not None else _FakeOpener()
    session = ArmedApplySession(
        opener=opener,
        port_name=_PORT,
        arm_token=_TOKEN,
    )
    return session, opener


# ---------------------------------------------------------------------------
# Construction gates.
# ---------------------------------------------------------------------------


def test_construction_requires_port_name() -> None:
    with pytest.raises(ArmedApplyError, match="port_name_required"):
        ArmedApplySession(opener=_FakeOpener(), port_name="", arm_token=_TOKEN)


def test_construction_requires_arm_token() -> None:
    with pytest.raises(ArmedApplyError, match="token_required"):
        ArmedApplySession(opener=_FakeOpener(), port_name=_PORT, arm_token="")


# ---------------------------------------------------------------------------
# Arm state machine.
# ---------------------------------------------------------------------------


def test_arm_requires_exact_token_and_opens_port() -> None:
    session, opener = _make_session()
    assert session.is_armed is False
    session.arm(_TOKEN)
    assert session.is_armed is True
    assert opener.opened == [_PORT]
    assert session.port_name == _PORT


def test_arm_refuses_empty_token() -> None:
    session, opener = _make_session()
    with pytest.raises(ArmedApplyError, match="token_required"):
        session.arm("")
    assert session.is_armed is False
    assert opener.opened == []


def test_arm_refuses_mismatched_token() -> None:
    session, opener = _make_session()
    with pytest.raises(ArmedApplyError, match="token_mismatch"):
        session.arm("wrong-token")
    assert session.is_armed is False
    assert opener.opened == []


def test_arm_refuses_non_string_token() -> None:
    session, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="token_required"):
        session.arm(None)  # type: ignore[arg-type]
    assert session.is_armed is False


def test_arm_while_armed_requires_explicit_disarm_first() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="already_armed"):
        session.arm(_TOKEN)
    assert session.is_armed is True


def test_arm_stays_disarmed_when_opener_raises_backend_error() -> None:
    opener = _FakeOpener(raises=OSError("no backend"))
    session, _ = _make_session(opener=opener)
    with pytest.raises(ArmedApplyError, match="port_open_failed"):
        session.arm(_TOKEN)
    assert session.is_armed is False


def test_arm_stays_disarmed_when_opener_raises_armed_apply_error() -> None:
    opener = _FakeOpener(raises=ArmedApplyError("armed_apply_output_port_not_found: x"))
    session, _ = _make_session(opener=opener)
    with pytest.raises(ArmedApplyError, match="not_found"):
        session.arm(_TOKEN)
    assert session.is_armed is False


# ---------------------------------------------------------------------------
# Confirm gate.
# ---------------------------------------------------------------------------


def test_confirm_requires_armed_state() -> None:
    session, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm("apply-1")


def test_confirm_requires_non_empty_action_id() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="action_id_required"):
        session.confirm("")


def test_apply_requires_armed_state() -> None:
    session, _ = _make_session()
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)


def test_apply_requires_prior_confirmation() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert opener.port.sent == []


def test_confirmation_is_single_use() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert result.ok is True
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert len(opener.port.sent) == 2


def test_confirmation_is_consumed_even_when_plan_is_refused() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    refused = session.apply(
        _FakeDevice(),
        _FakePlan(ready=False, readiness_reason="nope"),
        action_id="apply-1",
        mutates_kit=False,
    )
    assert refused.ok is False
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)


# ---------------------------------------------------------------------------
# Plan readiness + the kit/sound mutation refusal.
# ---------------------------------------------------------------------------


def test_apply_refuses_unready_plan_with_duck_reason() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(
        _FakeDevice(),
        _FakePlan(ready=False, readiness_reason="missing routing"),
        action_id="apply-1",
        mutates_kit=False,
    )
    assert result == ArmedApplyResult(
        device_id="fake_device",
        ok=False,
        sent_count=0,
        reason="missing routing",
        expected_count=0,
        status="refused",
    )
    assert opener.port.sent == []


def test_apply_refuses_plan_without_ready_attribute() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), object(), action_id="apply-1", mutates_kit=False)
    assert result.ok is False
    assert result.reason == "plan is not ready"
    assert opener.port.sent == []


def test_kit_mutating_apply_is_refused_outright() -> None:
    """The headline capability removal: no persistent write reaches the wire.

    An in-memory history snapshot is not a device backup and there is no
    restore path, so the seam refuses rather than pretending the write is
    reversible. ``mutates_kit`` defaults to ``True`` precisely so a caller
    must opt in to the permitted non-mutating case.
    """

    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(KitMutationUnsupportedError, match="kit_mutation_unsupported"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert opener.port.sent == []
    # The refusal is not a fault: the session stays armed for RAM-only sends.
    assert session.is_armed is True


def test_kit_mutation_refusal_is_a_fingerprinted_taxonomy_member() -> None:
    from rytm_randomizer.observability.errors import MidiError

    assert issubclass(KitMutationUnsupportedError, ArmedApplyError)
    assert issubclass(KitMutationUnsupportedError, MidiError)
    assert KitMutationUnsupportedError.fingerprint == "midi.armed_apply.kit_mutation_unsupported"


def test_kit_mutation_refusal_carries_structured_context() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(KitMutationUnsupportedError) as excinfo:
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1")
    assert excinfo.value.context == {"device_id": "fake_device", "action_id": "apply-1"}


def test_non_mutating_apply_transmits_without_any_backup() -> None:
    """RAM-only live-dial CC sends stay enabled — the permitted armed write."""

    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert result.ok is True
    assert result.sent_count == 2
    assert opener.port.sent == [(0, 10, 20), (1, 11, 21)]


def test_after_send_observes_each_successful_delivery_inside_the_seam() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    observed: list[tuple[tuple[int, int, int], int, int]] = []

    result = session.apply(
        _FakeDevice(),
        _FakePlan(),
        action_id="apply-1",
        mutates_kit=False,
        after_send=lambda triple, sent, expected: observed.append((triple, sent, expected)),
    )

    assert result.sent_count == 2
    assert opener.port.sent == [(0, 10, 20), (1, 11, 21)]
    assert observed == [((0, 10, 20), 1, 2), ((1, 11, 21), 2, 2)]


def test_after_send_failure_reports_the_already_delivered_triple() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")

    def _fail_after_delivery(_triple: tuple[int, int, int], _sent: int, _expected: int) -> None:
        raise ValueError("observer failed")

    with pytest.raises(ArmedApplyError) as excinfo:
        session.apply(
            _FakeDevice(),
            _FakePlan(),
            action_id="apply-1",
            mutates_kit=False,
            after_send=_fail_after_delivery,
        )

    assert opener.port.sent == [(0, 10, 20)]
    assert opener.port.closed == 1
    assert excinfo.value.partial_outcome is not None
    assert excinfo.value.partial_outcome.sent_count == 1


def test_apply_uses_an_injected_renderer_instead_of_the_device() -> None:
    """A caller whose plan already carries wire packets projects them directly."""

    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    seen: list[object] = []

    def _renderer(plan: object) -> list[tuple[int, int, int]]:
        seen.append(plan)
        return [(3, 44, 55)]

    plan = _FakePlan()
    result = session.apply(
        _FakeDevice(),
        plan,
        action_id="apply-1",
        mutates_kit=False,
        renderer=_renderer,
    )
    assert result.ok is True
    assert seen == [plan]
    # The device's own triples were NOT used.
    assert opener.port.sent == [(3, 44, 55)]


def test_apply_fails_closed_when_the_port_rejects_the_message_type() -> None:
    """A ``TypeError`` from the port refuses + auto-disarms, never escapes raw.

    A real ``mido`` port raises ``TypeError`` for a non-``mido.Message``.
    The wire adapter prevents that, but the seam must still fail closed.
    """

    class _TypeStrictPort:
        def __init__(self) -> None:
            self.sent: list[object] = []
            self.closed = 0

        def send(self, message: object) -> None:
            raise TypeError(f"mido port requires a mido.Message, got {type(message).__name__}")

        def close(self) -> None:
            self.closed += 1

    @dataclass
    class _StrictOpener:
        port: _TypeStrictPort = field(default_factory=_TypeStrictPort)

        def open_exact(self, _port_name: str) -> _TypeStrictPort:
            return self.port

    opener = _StrictOpener()
    session = ArmedApplySession(opener=opener, port_name=_PORT, arm_token=_TOKEN)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(ArmedApplyError, match="auto_disarmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert session.is_armed is False
    # Auto-disarm closed the port exactly once — no leaked handle.
    assert opener.port.closed == 1


# ---------------------------------------------------------------------------
# Auto-disarm + never-auto-re-arm.
# ---------------------------------------------------------------------------


def test_provider_error_mid_send_auto_disarms() -> None:
    opener = _FakeOpener(port=_FakePort(fail_after=1))
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(ArmedApplyError, match="auto_disarmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert session.is_armed is False
    assert opener.port.sent == [(0, 10, 20)]
    # Auto-disarm is a teardown path: the port is closed, not just dropped.
    assert opener.port.closed == 1


def test_partial_delivery_is_reported_not_discarded() -> None:
    """ "Send failed" for a half-applied device is a lie the operator acts on.

    The local ``sent`` counter used to be thrown away when the port
    raised, so a burst that put 1 of 2 CCs on the wire was
    indistinguishable from one that put 0. The count now rides on the
    error.
    """

    opener = _FakeOpener(port=_FakePort(fail_after=1))
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")

    with pytest.raises(ArmedApplyError) as excinfo:
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)

    outcome = excinfo.value.partial_outcome
    assert outcome is not None
    assert outcome.status == "partial"
    assert outcome.sent_count == 1
    assert outcome.expected_count == 2
    assert outcome.ok is False
    assert excinfo.value.context["sent_count"] == 1
    assert excinfo.value.context["expected_count"] == 2


def test_a_pre_wire_refusal_carries_no_partial_outcome() -> None:
    """``partial_outcome is not None`` must mean "bytes may have landed"."""

    session, _ = _make_session()
    with pytest.raises(ArmedApplyError) as excinfo:
        session.arm("wrong-token")
    assert excinfo.value.partial_outcome is None


def test_a_complete_send_reports_matching_sent_and_expected_counts() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    result = session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    assert (result.status, result.sent_count, result.expected_count) == ("complete", 2, 2)


def test_never_auto_re_arms_after_provider_error() -> None:
    opener = _FakeOpener(port=_FakePort(fail_after=0))
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")
    with pytest.raises(ArmedApplyError, match="auto_disarmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)
    # Still disarmed: apply and confirm both refuse until an explicit arm.
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-2", mutates_kit=False)
    with pytest.raises(ArmedApplyError, match="not_armed"):
        session.confirm("apply-2")
    # An explicit re-arm is required — and works.
    opener.port.fail_after = None
    session.arm(_TOKEN)
    assert session.is_armed is True


def test_disarm_is_idempotent_and_closes_port() -> None:
    session, opener = _make_session()
    session.arm(_TOKEN)
    session.disarm()
    assert session.is_armed is False
    assert opener.port.closed == 1
    session.disarm()  # idempotent — no second close, no raise
    assert opener.port.closed == 1


def test_disarm_swallows_port_close_errors() -> None:
    opener = _FakeOpener(port=_FakePort(close_raises=True))
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.disarm()
    assert session.is_armed is False


def test_disarm_clears_pending_confirmations() -> None:
    session, _ = _make_session()
    session.arm(_TOKEN)
    session.confirm("apply-1")
    session.disarm()
    session.arm(_TOKEN)
    with pytest.raises(ArmedApplyError, match="not_confirmed"):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)


@dataclass
class _NoClosePort:
    """A send-only port — the shape the seam must now REFUSE at arm time."""

    sent: list[tuple[int, int, int]] = field(default_factory=list)

    def send(self, message: tuple[int, int, int]) -> None:
        self.sent.append(message)


@dataclass
class _NoCloseOpener:
    port: _NoClosePort = field(default_factory=_NoClosePort)

    def open_exact(self, _port_name: str) -> _NoClosePort:
        return self.port


def test_arm_refuses_a_port_that_cannot_be_closed() -> None:
    """A handle the seam cannot release is a handle it must not hold.

    The previous contract treated ``close`` as optional (``getattr`` at
    disarm time), so a close-less port armed happily and then leaked the
    OS handle forever. Deterministic teardown is only implementable if
    every armed port is closable, so the check moved to arm time.
    """

    session = ArmedApplySession(opener=_NoCloseOpener(), port_name=_PORT, arm_token=_TOKEN)
    with pytest.raises(PortNotClosableError, match="port_not_closable"):
        session.arm(_TOKEN)
    assert session.is_armed is False


def test_port_not_closable_is_a_fingerprinted_armed_apply_error() -> None:
    assert issubclass(PortNotClosableError, ArmedApplyError)
    assert PortNotClosableError.fingerprint == "midi.armed_apply.port_not_closable"


def test_arm_refusal_for_a_close_less_port_carries_the_port_name() -> None:
    session = ArmedApplySession(opener=_NoCloseOpener(), port_name=_PORT, arm_token=_TOKEN)
    with pytest.raises(PortNotClosableError) as excinfo:
        session.arm(_TOKEN)
    assert excinfo.value.context == {"port_name": _PORT}


# ---------------------------------------------------------------------------
# Deterministic teardown: every exit path disarms AND closes exactly once.
# ---------------------------------------------------------------------------


def test_keyboard_interrupt_mid_send_disarms_closes_and_re_raises() -> None:
    """Ctrl+C used to leave the session ARMED with the port OPEN.

    Only ``_PORT_ERRORS`` were caught, so a ``KeyboardInterrupt`` raised
    out of ``port.send`` propagated past the state machine untouched. The
    seam now catches ``BaseException``, disarms (closing the port), and
    re-raises the original exception unchanged.
    """

    @dataclass
    class _InterruptingPort:
        sent: list[tuple[int, int, int]] = field(default_factory=list)
        closed: int = 0

        def send(self, message: tuple[int, int, int]) -> None:
            if self.sent:
                raise KeyboardInterrupt
            self.sent.append(message)

        def close(self) -> None:
            self.closed += 1

    port = _InterruptingPort()
    opener = _FakeOpener()
    opener.port = port  # type: ignore[assignment]
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")

    with pytest.raises(KeyboardInterrupt):
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)

    assert session.is_armed is False
    assert port.closed == 1
    assert port.sent == [(0, 10, 20)]


def test_system_exit_mid_send_records_the_interrupted_outcome() -> None:
    """The partial count survives on the raised exception, not just in a log."""

    @dataclass
    class _ExitingPort:
        sent: list[tuple[int, int, int]] = field(default_factory=list)
        closed: int = 0

        def send(self, message: tuple[int, int, int]) -> None:
            raise SystemExit(2)

        def close(self) -> None:
            self.closed += 1

    port = _ExitingPort()
    opener = _FakeOpener()
    opener.port = port  # type: ignore[assignment]
    session, _ = _make_session(opener=opener)
    session.arm(_TOKEN)
    session.confirm("apply-1")

    with pytest.raises(SystemExit) as excinfo:
        session.apply(_FakeDevice(), _FakePlan(), action_id="apply-1", mutates_kit=False)

    outcome = excinfo.value.__dict__["armed_apply_outcome"]
    assert outcome.status == "interrupted"
    assert outcome.sent_count == 0
    assert outcome.expected_count == 2
    assert session.is_armed is False
    assert port.closed == 1


def test_the_session_is_a_context_manager_that_always_disarms() -> None:
    """Scope exit is a teardown path too — including on an exception."""

    session, opener = _make_session()
    with session:
        session.arm(_TOKEN)
        assert session.is_armed is True
    assert session.is_armed is False
    assert opener.port.closed == 1

    session2, opener2 = _make_session()
    with pytest.raises(ValueError, match="boom"), session2:
        session2.arm(_TOKEN)
        raise ValueError("boom")
    assert session2.is_armed is False
    assert opener2.port.closed == 1


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


def test_exact_opener_rejects_a_port_without_close() -> None:
    """Fail closed at resolution, so the seam never receives an unclosable port."""

    provider = _FakeProvider(port=_NoClosePort())
    with pytest.raises(PortNotClosableError, match="port_not_closable"):
        ExactOutputOpener(provider).open_exact(_PORT)


def test_exact_opener_closes_a_port_it_refuses_for_missing_send() -> None:
    """Refusing an opened handle must not also leak it."""

    class _SendlessButClosable:
        def __init__(self) -> None:
            self.closed = 0

        def close(self) -> None:
            self.closed += 1

    port = _SendlessButClosable()
    provider = _FakeProvider(port=port)
    with pytest.raises(ArmedApplyError, match="invalid_output_port"):
        ExactOutputOpener(provider).open_exact(_PORT)
    assert port.closed == 1


def test_exact_opener_tolerates_a_failing_close_while_refusing() -> None:
    """A dying port's close error must not mask the refusal itself."""

    class _SendlessCloseRaises:
        def close(self) -> None:
            raise OSError("backend already gone")

    provider = _FakeProvider(port=_SendlessCloseRaises())
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


# ---------------------------------------------------------------------------
# Renderer failure — the port is already open when rendering runs.
# ---------------------------------------------------------------------------


def test_apply_disarms_and_closes_when_the_renderer_raises() -> None:
    """A renderer that raises must not strand an armed, open port.

    Rendering happens AFTER the port is opened but BEFORE the first byte
    reaches the wire, so an exception there used to leave the session
    armed holding an exclusive hardware handle — the same failure class
    as an interrupted send burst, but on a path no test covered. Nothing
    was transmitted, so this is a clean zero-byte refusal: disarm, close,
    and re-raise the original exception unchanged.
    """

    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("act-1")

    def _explode(_plan: object) -> list[tuple[int, int, int]]:
        raise ValueError("device strategy produced a malformed plan")

    with pytest.raises(ValueError, match="malformed plan"):
        session.apply(
            device=_FakeDevice(),
            plan=_FakePlan(),
            action_id="act-1",
            mutates_kit=False,
            renderer=_explode,
        )

    assert session.is_armed is False
    assert opener.port.closed == 1
    assert opener.port.sent == []


def test_apply_disarms_and_closes_when_the_renderer_is_interrupted() -> None:
    """KeyboardInterrupt during rendering releases the handle and propagates."""

    session, opener = _make_session()
    session.arm(_TOKEN)
    session.confirm("act-1")

    def _interrupt(_plan: object) -> list[tuple[int, int, int]]:
        raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        session.apply(
            device=_FakeDevice(),
            plan=_FakePlan(),
            action_id="act-1",
            mutates_kit=False,
            renderer=_interrupt,
        )

    assert session.is_armed is False
    assert opener.port.closed == 1
