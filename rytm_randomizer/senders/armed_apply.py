"""ArmedApply seam — the single outbound-transmit state machine (WS-4).

The Live-but-Passive safety model (``.claude/rules/live-but-passive-midi.md``)
routes **every** outbound transmit through one explicit, test-pinned state
machine. This module is that seam. It composes the pieces PR #213 / #214
proved out:

* **Explicit arm.** :meth:`ArmedApplySession.arm` takes the operator's arm
  token; a mismatched or empty token never arms. Arming opens the target
  output port through an injected :class:`ExactPortOpener` — a fail-closed,
  exact-name resolution boundary (the concrete opener lives in
  :mod:`rytm_randomizer.senders.hardware`, the whitelisted transmit module).
* **Per-action confirmation.** Every apply requires a prior, single-use
  :meth:`ArmedApplySession.confirm` for its ``action_id``. "Armed" alone is
  never enough to transmit.
* **Plan readiness.** Plans are validated through the same ``ready`` /
  ``readiness_reason`` duck the generic guarded sender uses
  (:func:`plan_readiness`); an unready plan is refused without device
  introspection.
* **Kit/sound mutation is refused, not "backed up".** The safety model
  asks for reversibility before any persistent write. Real
  capture-before-write (a SysEx dump read back from the device) and a
  restore path are **not implemented**, so the seam refuses every
  mutating apply with :class:`KitMutationUnsupportedError` rather than
  taking a nominal backup it cannot restore from. Non-mutating live-dial
  CC sends (``mutates_kit=False``) land in the device's working RAM only
  and remain permitted.
* **Never auto-re-arm.** A provider error during a send auto-disarms the
  session; re-arming requires a fresh explicit :meth:`arm` call. Nothing
  in this module re-arms as a side effect.
* **Deterministic teardown.** The armed port is a real, exclusive
  hardware handle, so :meth:`ArmedApplySession.disarm` — the one place
  it is closed — runs on *every* exit path: explicit disarm, provider
  error, ``KeyboardInterrupt`` / ``SystemExit`` / cancellation mid-burst
  (caught, disarmed, re-raised — never swallowed), context-manager exit,
  WS disconnect, and app shutdown. A port that cannot be closed is
  refused at arm time (:class:`PortNotClosableError`) rather than held
  with no way to release it.
* **Partial delivery is visible.** Every outcome carries
  ``sent_count`` / ``expected_count`` and a terminal
  :data:`ArmedApplyStatus`, including the failure paths (via
  :attr:`ArmedApplyError.partial_outcome`), so "the burst stopped
  half-way and the device is half-applied" is never reported as a plain
  failure.

This module deliberately contains **no transmit-boundary markers** — it
never constructs an output port itself. Port construction stays inside
the whitelisted :mod:`senders.hardware` module and reaches this seam only
through the :class:`ExactPortOpener` Protocol
(``tests/architecture/test_armed_entry_points.py`` enforces the split).
"""

from __future__ import annotations

import hmac
from asyncio import CancelledError
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from typing import ClassVar, Final, Literal, Protocol, runtime_checkable

from ..devices import Device
from ..observability.errors import MidiError

__all__ = [
    "ArmedApplyError",
    "ArmedApplyResult",
    "ArmedApplySession",
    "ArmedApplyStatus",
    "DeliveryObserver",
    "ExactPortOpener",
    "KitMutationUnsupportedError",
    "OutputPortLike",
    "PlanRenderer",
    "PortNotClosableError",
    "plan_readiness",
]


class ArmedApplyError(MidiError, RuntimeError):
    """The ArmedApply state machine refused an operation (fail-closed).

    Member of the unified :class:`~rytm_randomizer.observability.errors.MidiError`
    taxonomy (OBS O4 fingerprint discipline). ``RuntimeError`` is kept as
    an additional base so ``except RuntimeError`` callers keep working —
    the same dual-inheritance pattern as
    :class:`~rytm_randomizer.real_midi_adapter.RealMidiPortError`.

    When the failure happened **mid-burst**, :attr:`partial_outcome`
    carries the :class:`ArmedApplyResult` describing how far the wire
    actually got. It is ``None`` for every refusal raised before the first
    byte (token mismatch, missing confirmation, kit-mutation refusal), so
    ``exc.partial_outcome is not None`` is the precise test for "the
    device may be in a half-applied state".
    """

    fingerprint: ClassVar[str] = "midi.armed_apply.refused"

    def __init__(
        self,
        message: str = "",
        *,
        context: Mapping[str, object] | None = None,
        partial_outcome: ArmedApplyResult | None = None,
    ) -> None:
        """Capture the message/context plus an optional mid-burst outcome."""

        super().__init__(message, context=context)
        self.partial_outcome: ArmedApplyResult | None = partial_outcome


class KitMutationUnsupportedError(ArmedApplyError):
    """A kit/sound-**mutating** armed write was refused: no restore path.

    The Live-but-Passive model promises that every armed write is
    reversible. Delivering that requires two things this codebase does
    **not** have yet:

    1. a real capture-before-write (a SysEx kit/sound dump read back
       from the device — no such readback exists; the cockpit's former
       real adapter only ever returned a placeholder snapshot, and was
       deleted with this change), and
    2. a restore path that can push a captured dump back to the device
       (no such path exists anywhere in the package).

    An in-memory history snapshot is **not** a device backup: it is
    mock-originated state that cannot be written back to hardware.
    Rather than ship a nominal backup that claims a reversibility it
    cannot deliver, the seam refuses persistent kit/sound mutation
    outright and says so in the error.

    Non-mutating live-dial CC/NRPN sends stay enabled — see
    :meth:`ArmedApplySession.apply`.
    """

    fingerprint: ClassVar[str] = "midi.armed_apply.kit_mutation_unsupported"


class PortNotClosableError(ArmedApplyError):
    """Arming was refused: the resolved port cannot be deterministically closed.

    An armed session owns a real, exclusive hardware handle. The safety
    model requires that handle to be released on *every* exit path —
    explicit disarm, provider error, WS disconnect, app shutdown, task
    cancellation, ``KeyboardInterrupt``. A port object without a callable
    ``close`` makes that guarantee unimplementable: the seam would drop
    its reference and leave the OS handle open until interpreter exit,
    holding the device's MIDI output hostage against the next arm.

    So a close-less port is refused **at arm time** rather than tolerated
    at disarm time. The canonical armed-port shape is ``send`` + ``close``
    — the same contract
    :class:`~rytm_randomizer.real_midi_adapter.RealMidiOutputPort`
    declares.
    """

    fingerprint: ClassVar[str] = "midi.armed_apply.port_not_closable"


@runtime_checkable
class OutputPortLike(Protocol):
    """Canonical armed-output surface: ``send`` **and** ``close``.

    ``close`` is not optional. It mirrors
    :class:`~rytm_randomizer.real_midi_adapter.RealMidiOutputPort` — the
    one production port shape — because an armed session must be able to
    release its exclusive hardware handle deterministically on every exit
    path. A port that cannot be closed is refused at arm time with
    :class:`PortNotClosableError`.
    """

    def send(self, message: object) -> None:
        """Transmit one rendered message toward the hardware."""

    def close(self) -> None:
        """Release the underlying hardware handle (idempotent in practice)."""


@runtime_checkable
class ExactPortOpener(Protocol):
    """Fail-closed exact-name port resolution seam.

    The concrete implementation
    (:class:`rytm_randomizer.senders.hardware.ExactOutputOpener`) lives in
    the whitelisted transmit module; this Protocol keeps the seam itself
    free of any port-construction call.
    """

    def open_exact(self, port_name: str) -> OutputPortLike:
        """Open the single output port named exactly ``port_name``.

        Must fail closed: raise :class:`ArmedApplyError` when the name is
        missing from the enumerated outputs OR matches more than one port.
        """
        ...


PlanRenderer = Callable[[object], Iterable[tuple[int, int, int]]]
"""Project one plan into the ``(channel, control, value)`` triples to send.

The default projection is ``Device.to_cc_messages``. A caller supplies its
own only when the plan already carries resolved wire packets (the cockpit's
:class:`~rytm_randomizer.cockpit.data.CockpitSendPlan`), so the hardware
boundary transmits exactly what preflight approved.
"""

DeliveryObserver = Callable[[tuple[int, int, int], int, int], object]
"""Observe one successful write as ``(triple, sent, expected)``.

The callback runs after the port accepts a triple. It supports legacy CC
metrics and inter-message pacing without creating a second transmit path.
"""

_PORT_ERRORS: Final[tuple[type[BaseException], ...]] = (
    OSError,
    RuntimeError,
    ValueError,
    TypeError,
)
"""Exception families a MIDI backend / injected hook can realistically raise.

``TypeError`` is in the set deliberately: a real ``mido`` output port
rejects any object that is not a :class:`mido.Message` with a ``TypeError``.
The wire conversion at :class:`rytm_randomizer.mido_provider.WireOutputPort`
is what prevents that from happening, but the seam must still fail **closed**
(refuse + auto-disarm) rather than propagate a bare ``TypeError`` if any
future port is handed something it cannot render.
"""


def plan_readiness(plan: object) -> tuple[bool, str]:
    """Return ``(ready, readiness_reason)`` via the ReadyPlan duck.

    The single readiness check shared by :func:`senders.guarded.guarded_send`,
    :func:`senders.hardware.hardware_send`, and
    :meth:`ArmedApplySession.apply` — ``getattr``-based so any device
    family's plan participates without a common base class.
    """

    ready = bool(getattr(plan, "ready", False))
    reason = str(getattr(plan, "readiness_reason", "plan is not ready"))
    return ready, reason


ArmedApplyStatus = Literal["complete", "refused", "partial", "interrupted"]
"""Terminal outcome of one apply attempt — how far the wire actually got.

* ``complete`` — every rendered triple reached the port.
* ``refused`` — a gate refused **before** the first byte
  (``sent_count == 0``, ``expected_count == 0``): an unready plan.
* ``partial`` — the port raised mid-burst. ``sent_count`` triples are on
  the wire and the device is in a half-applied state; the session
  auto-disarmed.
* ``interrupted`` — the send was aborted by something that is not a port
  error (``KeyboardInterrupt``, ``SystemExit``, task cancellation). Same
  half-applied hazard as ``partial``; the session auto-disarmed and the
  original exception was re-raised, never swallowed.

``partial`` and ``interrupted`` are surfaced through
:class:`ArmedApplyError.partial_outcome` on the raised error, because the
caller gets an exception rather than a returned result on those paths.
"""


@dataclass(frozen=True)
class ArmedApplyResult:
    """Outcome of one :meth:`ArmedApplySession.apply` attempt.

    ``sent_count`` / ``expected_count`` are always both populated so a
    caller can tell "nothing was attempted" (``0 / 0``, a refusal) from
    "everything landed" (``n / n``) from "the burst was cut short"
    (``k / n`` with ``k < n``). Partial delivery used to be invisible: the
    local counter was discarded when the port raised, so the operator was
    told "send failed" for a device that had already received half a kit's
    worth of CCs.

    There is deliberately no ``backup_taken`` field. An earlier revision
    carried one, which advertised a reversibility guarantee the seam could
    not deliver; mutating writes are now refused outright instead (see
    :class:`KitMutationUnsupportedError`), so every successful apply is by
    construction a non-mutating RAM-only send that needs no backup.
    """

    device_id: str
    ok: bool
    sent_count: int
    reason: str = ""
    expected_count: int = 0
    status: ArmedApplyStatus = "complete"


class ArmedApplySession:
    """The one armed transmit state machine (frozen contract, test-pinned).

    Lifecycle::

        disarmed --arm(token)--> armed --disarm() / provider error--> disarmed

    * Construction never touches hardware.
    * :meth:`arm` requires the exact construction-time token and opens the
      port through the injected opener (fail-closed on missing/duplicate
      names).
    * :meth:`apply` requires armed state, a prior single-use
      :meth:`confirm` for its ``action_id``, and a ready plan. A
      kit/sound-mutating apply is always refused
      (:class:`KitMutationUnsupportedError`); only non-mutating
      ``mutates_kit=False`` RAM-only sends reach the wire.
    * A provider error mid-send **auto-disarms**; the session never
      re-arms on its own.
    """

    def __init__(
        self,
        *,
        opener: ExactPortOpener,
        port_name: object,
        arm_token: object,
    ) -> None:
        """Capture the collaborators; refuse unusable configuration eagerly.

        ``port_name`` and ``arm_token`` are typed ``object`` on purpose:
        both originate from wire-supplied operator input, so the
        ``isinstance`` checks below are genuine runtime validation (the
        fail-closed refusals), not redundant defensive narrowing.

        There is deliberately **no backup hook**. An earlier revision took
        one, which implied the seam could make an armed kit write
        reversible; it could not (the only available "backup" was an
        in-memory, mock-originated history snapshot with no restore path).
        Kit/sound mutation is now refused outright instead — see
        :class:`KitMutationUnsupportedError`.
        """

        if not isinstance(port_name, str) or not port_name:
            raise ArmedApplyError("armed_apply_port_name_required")
        if not isinstance(arm_token, str) or not arm_token:
            raise ArmedApplyError("armed_apply_token_required")
        self._opener = opener
        self._port_name = port_name
        self._arm_token = arm_token
        self._port: OutputPortLike | None = None
        self._armed = False
        self._confirmed_action_ids: set[str] = set()

    @property
    def is_armed(self) -> bool:
        """True while the session holds an open, explicitly-armed port."""

        return self._armed

    @property
    def port_name(self) -> str:
        """The exact output-port name this session targets."""

        return self._port_name

    def arm(self, token: object) -> None:
        """Arm the session: validate the token, then open the exact port.

        Raises :class:`ArmedApplyError` when already armed (re-arming is
        an explicit disarm-then-arm sequence, never implicit), when the
        token is empty or mismatched, or when the opener fails — in which
        case the session stays disarmed (fail closed).

        A resolved port that is not **closable** (no callable ``close``)
        is refused with :class:`PortNotClosableError` and closed-over
        immediately: the seam cannot promise deterministic teardown of a
        handle it has no way to release, so it declines to hold one.
        """

        if self._armed:
            raise ArmedApplyError("armed_apply_already_armed: disarm first")
        if not isinstance(token, str) or not token:
            raise ArmedApplyError("armed_apply_token_required")
        if not hmac.compare_digest(token, self._arm_token):
            raise ArmedApplyError("armed_apply_token_mismatch")
        try:
            port = self._opener.open_exact(self._port_name)
        except ArmedApplyError:
            self._reset()
            raise
        except _PORT_ERRORS as exc:
            self._reset()
            raise ArmedApplyError("armed_apply_port_open_failed") from exc
        if not callable(getattr(port, "close", None)):
            self._reset()
            raise PortNotClosableError(
                "armed_apply_port_not_closable: an armed output port must expose "
                "close() so the handle is released on every teardown path",
                context={"port_name": self._port_name},
            )
        self._port = port
        self._armed = True

    def confirm(self, action_id: object) -> None:
        """Record a single-use confirmation for one upcoming apply.

        Requires armed state — confirming while disarmed is a state-machine
        violation, not a queued intent.
        """

        if not self._armed:
            raise ArmedApplyError("armed_apply_not_armed")
        if not isinstance(action_id, str) or not action_id:
            raise ArmedApplyError("armed_apply_action_id_required")
        self._confirmed_action_ids.add(action_id)

    def apply(
        self,
        device: Device,
        plan: object,
        *,
        action_id: str,
        mutates_kit: bool = True,
        renderer: PlanRenderer | None = None,
        after_send: DeliveryObserver | None = None,
    ) -> ArmedApplyResult:
        """Transmit ``plan`` through ``device``'s renderer — fully gated.

        ``renderer`` overrides how ``plan`` becomes wire triples. It
        defaults to ``device.to_cc_messages`` (the Device-Protocol path
        used by the CLI/shell senders). The cockpit passes its own
        projection because a
        :class:`~rytm_randomizer.cockpit.data.CockpitSendPlan` already
        carries fully-resolved ``(channel, control, value)`` packets from
        preflight — re-deriving them through a device strategy would
        recompute the wire format at the hardware boundary, which the
        SEND contract forbids. Every gate below applies identically
        either way; only the projection differs.

        ``after_send`` observes each successful write with the transmitted
        triple, the one-based sent count, and the total expected count. A
        callback failure is a mid-burst failure because the current triple is
        already on the wire: the session auto-disarms and reports that triple
        in the partial outcome.

        Gate order (each refusal is deliberate and test-pinned):

        1. armed state (raises when disarmed),
        2. single-use per-action confirmation (raises when unconfirmed;
           the confirmation is consumed even if a later gate refuses),
        3. plan readiness (returns a ``status="refused"`` result),
        4. **kit/sound mutation refusal** — raises
           :class:`KitMutationUnsupportedError` whenever ``mutates_kit``
           is true (the default). See below.
        5. the send itself — a provider error auto-disarms (closing the
           port) and re-raises as :class:`ArmedApplyError` carrying a
           ``status="partial"``
           :attr:`~ArmedApplyError.partial_outcome`; a
           ``KeyboardInterrupt`` / ``SystemExit`` / cancellation likewise
           auto-disarms, tags the exception with an
           ``armed_apply_outcome`` of ``status="interrupted"``, and
           re-raises the original exception unchanged.

        **What is and is not permitted on hardware.** ``mutates_kit``
        defaults to ``True`` so a caller must *opt in* to the permitted
        narrow case:

        * ``mutates_kit=True`` — a write that changes persistent
          kit/sound memory. **Always refused.** Reversibility requires a
          real capture-before-write plus a restore path, neither of which
          exists (see :class:`KitMutationUnsupportedError`). This is a
          deliberate capability removal, not a temporary bug.
        * ``mutates_kit=False`` — a non-mutating live-dial CC/NRPN send.
          These land in the device's working RAM only and are undone by
          reloading the kit from the device's own memory, so they need no
          backup of ours. Permitted, and the only armed writes that are.
        """

        if not self._armed or self._port is None:
            raise ArmedApplyError("armed_apply_not_armed")
        if action_id not in self._confirmed_action_ids:
            raise ArmedApplyError("armed_apply_action_not_confirmed")
        self._confirmed_action_ids.discard(action_id)

        ready, reason = plan_readiness(plan)
        if not ready:
            return ArmedApplyResult(
                device_id=device.device_id,
                ok=False,
                sent_count=0,
                reason=reason,
                expected_count=0,
                status="refused",
            )

        if mutates_kit:
            raise KitMutationUnsupportedError(
                "armed_apply_kit_mutation_unsupported: persistent kit/sound "
                "writes are disabled because real capture-before-write and a "
                "restore path are not implemented; only non-mutating "
                "(RAM-only) live-dial CC sends are permitted",
                context={"device_id": device.device_id, "action_id": action_id},
            )

        port = self._port
        emit = device.to_cc_messages if renderer is None else renderer
        render_complete = False
        try:
            triples = tuple(emit(plan))
            render_complete = True
        finally:
            # Rendering runs while the port is already open. ``finally``
            # closes it for every exception class without a broad catch.
            if not render_complete:
                self.disarm()
        expected = len(triples)
        sent = 0
        for triple in triples:
            try:
                port.send(triple)
                sent += 1
                if after_send is not None:
                    after_send(triple, sent, expected)
            except _PORT_ERRORS as exc:
                # Auto-disarm on provider error (which closes the port).
                # Never auto-re-arm: the operator must run the explicit
                # arm sequence again. The count is carried on the error so
                # a half-applied device is visible, not silently discarded.
                self.disarm()
                raise ArmedApplyError(
                    "armed_apply_send_failed_auto_disarmed",
                    context={
                        "device_id": device.device_id,
                        "action_id": action_id,
                        "sent_count": sent,
                        "expected_count": expected,
                    },
                    partial_outcome=ArmedApplyResult(
                        device_id=device.device_id,
                        ok=False,
                        sent_count=sent,
                        reason="armed_apply_send_failed_auto_disarmed",
                        expected_count=expected,
                        status="partial",
                    ),
                ) from exc
            except (KeyboardInterrupt, SystemExit, CancelledError) as exc:
                # KeyboardInterrupt / SystemExit / CancelledError land here.
                # Without this arm the session stayed ARMED with the port
                # OPEN — Ctrl+C during a burst left the operator holding an
                # exclusive hardware handle with no way to release it. We
                # disarm (which closes the port), attach the partial
                # outcome for the caller's teardown log, and RE-RAISE:
                # control-flow exceptions are never swallowed.
                self.disarm()
                exc.__dict__["armed_apply_outcome"] = ArmedApplyResult(
                    device_id=device.device_id,
                    ok=False,
                    sent_count=sent,
                    reason="armed_apply_send_interrupted_auto_disarmed",
                    expected_count=expected,
                    status="interrupted",
                )
                raise
        return ArmedApplyResult(
            device_id=device.device_id,
            ok=True,
            sent_count=sent,
            reason="",
            expected_count=expected,
            status="complete",
        )

    def disarm(self) -> None:
        """Drop to the passive state (idempotent) and close the port.

        Deterministic teardown: this is the single place the armed
        hardware handle is released, and every exit path routes through
        it — explicit ``disarm``, a provider error mid-send, an
        interrupt/cancellation mid-send, WS disconnect, app shutdown.
        Calling it twice closes once (:meth:`_reset` drops the reference
        before the close, so the second call has nothing to close).

        A ``close()`` that itself raises a backend error is swallowed: the
        state machine is already passive at that point, and masking the
        disarm behind a dying port's exception would leave callers unsure
        whether they are armed.
        """

        port = self._port
        self._reset()
        if port is None:
            return
        try:
            port.close()
        except _PORT_ERRORS:
            # Closing an already-dead backend port must never mask the
            # disarm itself — the state machine is already passive.
            return

    def __enter__(self) -> ArmedApplySession:
        """Enter a scope whose exit is guaranteed to disarm.

        Lets callers that own an armed session for a bounded region (app
        shutdown paths, tests, future CLI arm blocks) express the teardown
        guarantee structurally instead of remembering a ``finally``.
        """

        return self

    def __exit__(self, *_exc_info: object) -> Literal[False]:
        """Always disarm on scope exit; never suppress the exception."""

        self.disarm()
        return False

    def _reset(self) -> None:
        """Clear armed state + confirmations (the passive baseline)."""

        self._port = None
        self._armed = False
        self._confirmed_action_ids.clear()
