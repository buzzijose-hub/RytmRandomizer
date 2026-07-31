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

This module deliberately contains **no transmit-boundary markers** — it
never constructs an output port itself. Port construction stays inside
the whitelisted :mod:`senders.hardware` module and reaches this seam only
through the :class:`ExactPortOpener` Protocol
(``tests/architecture/test_armed_entry_points.py`` enforces the split).
"""

from __future__ import annotations

import hmac
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import ClassVar, Final, Protocol, runtime_checkable

from ..devices import Device
from ..observability.errors import MidiError

__all__ = [
    "ArmedApplyError",
    "ArmedApplyResult",
    "ArmedApplySession",
    "ExactPortOpener",
    "KitMutationUnsupportedError",
    "OutputPortLike",
    "PlanRenderer",
    "plan_readiness",
]


class ArmedApplyError(MidiError, RuntimeError):
    """The ArmedApply state machine refused an operation (fail-closed).

    Member of the unified :class:`~rytm_randomizer.observability.errors.MidiError`
    taxonomy (OBS O4 fingerprint discipline). ``RuntimeError`` is kept as
    an additional base so ``except RuntimeError`` callers keep working —
    the same dual-inheritance pattern as
    :class:`~rytm_randomizer.real_midi_adapter.RealMidiPortError`.
    """

    fingerprint: ClassVar[str] = "midi.armed_apply.refused"


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


@runtime_checkable
class OutputPortLike(Protocol):
    """Minimal armed-output surface: one ``send`` method."""

    def send(self, message: object) -> None:
        """Transmit one rendered message toward the hardware."""


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


@dataclass(frozen=True)
class ArmedApplyResult:
    """Outcome of one :meth:`ArmedApplySession.apply` attempt.

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

        Gate order (each refusal is deliberate and test-pinned):

        1. armed state (raises when disarmed),
        2. single-use per-action confirmation (raises when unconfirmed;
           the confirmation is consumed even if a later gate refuses),
        3. plan readiness (returns a refused result),
        4. **kit/sound mutation refusal** — raises
           :class:`KitMutationUnsupportedError` whenever ``mutates_kit``
           is true (the default). See below.
        5. the send itself — a provider error auto-disarms and re-raises
           as :class:`ArmedApplyError`.

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
        sent = 0
        for triple in emit(plan):
            try:
                port.send(triple)
            except _PORT_ERRORS as exc:
                # Auto-disarm on provider error. Never auto-re-arm: the
                # operator must run the explicit arm sequence again.
                self.disarm()
                raise ArmedApplyError("armed_apply_send_failed_auto_disarmed") from exc
            sent += 1
        return ArmedApplyResult(
            device_id=device.device_id,
            ok=True,
            sent_count=sent,
            reason="",
        )

    def disarm(self) -> None:
        """Drop to the passive state (idempotent); best-effort port close."""

        port = self._port
        self._reset()
        if port is None:
            return
        close = getattr(port, "close", None)
        if not callable(close):
            return
        try:
            close()
        except _PORT_ERRORS:
            # Closing an already-dead backend port must never mask the
            # disarm itself — the state machine is already passive.
            return

    def _reset(self) -> None:
        """Clear armed state + confirmations (the passive baseline)."""

        self._port = None
        self._armed = False
        self._confirmed_action_ids.clear()
