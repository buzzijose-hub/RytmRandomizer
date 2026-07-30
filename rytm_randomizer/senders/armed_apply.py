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
* **Backup before mutation.** A **required** injected backup hook runs
  before any kit/sound-mutating apply; when the backup fails (returns
  falsy or raises), the send is refused.
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
from collections.abc import Callable
from dataclasses import dataclass
from typing import ClassVar, Final, Protocol, runtime_checkable

from ..devices import Device
from ..observability.errors import MidiError

__all__ = [
    "ArmedApplyError",
    "ArmedApplyResult",
    "ArmedApplySession",
    "BackupHook",
    "ExactPortOpener",
    "OutputPortLike",
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


BackupHook = Callable[[object], bool]
"""Pre-write backup callback: receives the plan, returns ``True`` on success.

A falsy return (or a raised error) refuses the send — the backup is the
reversibility guarantee for every armed kit/sound mutation.
"""

_PORT_ERRORS: Final[tuple[type[BaseException], ...]] = (OSError, RuntimeError, ValueError)
"""Exception families a MIDI backend / injected hook can realistically raise."""


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
    """Outcome of one :meth:`ArmedApplySession.apply` attempt."""

    device_id: str
    ok: bool
    sent_count: int
    reason: str = ""
    backup_taken: bool = False


class ArmedApplySession:
    """The one armed transmit state machine (frozen contract, test-pinned).

    Lifecycle::

        disarmed --arm(token)--> armed --disarm() / provider error--> disarmed

    * Construction never touches hardware.
    * :meth:`arm` requires the exact construction-time token and opens the
      port through the injected opener (fail-closed on missing/duplicate
      names).
    * :meth:`apply` requires armed state, a prior single-use
      :meth:`confirm` for its ``action_id``, a ready plan, and a
      successful pre-write backup (for kit/sound-mutating applies).
    * A provider error mid-send **auto-disarms**; the session never
      re-arms on its own.
    """

    def __init__(
        self,
        *,
        opener: ExactPortOpener,
        port_name: object,
        backup: BackupHook,
        arm_token: object,
    ) -> None:
        """Capture the collaborators; refuse unusable configuration eagerly.

        ``port_name`` and ``arm_token`` are typed ``object`` on purpose:
        both originate from wire-supplied operator input, so the
        ``isinstance`` checks below are genuine runtime validation (the
        fail-closed refusals), not redundant defensive narrowing.
        """

        if not isinstance(port_name, str) or not port_name:
            raise ArmedApplyError("armed_apply_port_name_required")
        if not isinstance(arm_token, str) or not arm_token:
            raise ArmedApplyError("armed_apply_token_required")
        if not callable(backup):
            raise ArmedApplyError("armed_apply_backup_hook_required")
        self._opener = opener
        self._port_name = port_name
        self._backup = backup
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
    ) -> ArmedApplyResult:
        """Transmit ``plan`` through ``device``'s renderer — fully gated.

        Gate order (each refusal is deliberate and test-pinned):

        1. armed state (raises when disarmed),
        2. single-use per-action confirmation (raises when unconfirmed;
           the confirmation is consumed even if a later gate refuses),
        3. plan readiness (returns a refused result),
        4. pre-write backup for kit/sound mutations (returns a refused
           result when the hook fails or raises),
        5. the send itself — a provider error auto-disarms and re-raises
           as :class:`ArmedApplyError`.
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
                backup_taken=False,
            )

        backup_taken = False
        if mutates_kit:
            try:
                backup_ok = bool(self._backup(plan))
            except _PORT_ERRORS:
                backup_ok = False
            if not backup_ok:
                return ArmedApplyResult(
                    device_id=device.device_id,
                    ok=False,
                    sent_count=0,
                    reason="pre-write backup failed; send refused",
                    backup_taken=False,
                )
            backup_taken = True

        port = self._port
        sent = 0
        for triple in device.to_cc_messages(plan):
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
            backup_taken=backup_taken,
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
