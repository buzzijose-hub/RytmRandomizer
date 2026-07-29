"""Generic arm-gated hardware sender for Device mutation plans.

This module is on the armed transmit whitelist
(``tests/architecture/test_armed_entry_points.py``): it is one of the
two ``senders`` files allowed to define the hardware send / construct a
real output port. The WS-4 :class:`ExactOutputOpener` therefore lives
here — it is the only concrete implementation of the ArmedApply seam's
:class:`~rytm_randomizer.senders.armed_apply.ExactPortOpener` Protocol,
keeping ``armed_apply.py`` itself free of port construction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

from ..devices import Device
from .armed_apply import ArmedApplyError, OutputPortLike, plan_readiness


class TripleSender(Protocol):
    """Boundary for sending rendered CC triples in tests and production."""

    def send(self, message: tuple[int, int, int]) -> None:
        """Transmit one rendered ``(channel, control, value)`` triple."""


class OutputOpeningProvider(Protocol):
    """The provider surface :class:`ExactOutputOpener` narrows down.

    Structurally satisfied by
    :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider` and by
    test fakes: two methods, nothing else reachable.
    """

    def list_output_names(self) -> tuple[str, ...]:
        """Return the currently visible MIDI output port names."""

    def open_output(self, port_name: str) -> object:
        """Open a hardware MIDI output port by name."""


class ExactOutputOpener:
    """Fail-closed exact-name output resolution over an injected provider.

    Mirrors the exact-open semantics the ArmedApply seam requires: the
    requested name must match **exactly one** enumerated output port —
    zero matches and duplicate matches both refuse (fail closed), so an
    armed session can never grab "some other" port than the one the
    operator confirmed.
    """

    def __init__(self, provider: OutputOpeningProvider) -> None:
        """Capture the provider; no hardware is touched at construction."""

        self._provider = provider

    def open_exact(self, port_name: str) -> OutputPortLike:
        """Open the single output named exactly ``port_name`` (fail-closed)."""

        if not isinstance(port_name, str) or not port_name:
            raise ArmedApplyError("armed_apply_port_name_required")
        names = tuple(self._provider.list_output_names())
        matches = [name for name in names if name == port_name]
        if not matches:
            raise ArmedApplyError(f"armed_apply_output_port_not_found: {port_name}")
        if len(matches) > 1:
            raise ArmedApplyError(f"armed_apply_output_port_ambiguous: {port_name}")
        port = self._provider.open_output(port_name)
        if not callable(getattr(port, "send", None)):
            raise ArmedApplyError(f"armed_apply_invalid_output_port: {port_name}")
        return cast(OutputPortLike, port)


@dataclass(frozen=True)
class HardwareSendResult:
    """Result of an arm-gated hardware send attempt."""

    device_id: str
    ready: bool
    sent_count: int
    reason: str = ""


def hardware_send(
    device: Device,
    plan: object,
    *,
    sender: TripleSender,
    armed: bool,
) -> HardwareSendResult:
    """Send a plan to hardware only when armed and ready."""

    if not armed:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason="hardware send requires --arm",
        )

    ready, reason = plan_readiness(plan)
    if not ready:
        return HardwareSendResult(
            device_id=device.device_id,
            ready=False,
            sent_count=0,
            reason=reason,
        )

    triples = tuple(device.to_cc_messages(plan))
    for triple in triples:
        sender.send(triple)
    return HardwareSendResult(
        device_id=device.device_id,
        ready=True,
        sent_count=len(triples),
        reason="",
    )
