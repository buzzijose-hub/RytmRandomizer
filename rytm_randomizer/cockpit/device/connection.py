"""``ConnectionManager`` — the Live-but-Passive launch brain (Wave 3).

The cockpit's safety model (``.claude/rules/live-but-passive-midi.md``)
splits MIDI into two halves:

* **Inputs are free.** Enumerating ports and listening on inputs is
  passive — it never interrupts the device's sound output and gives the
  operator immediate connection-health feedback.
* **Outputs are armed.** Every outbound transmit routes through the
  ``senders`` ArmedApply seam behind an explicit in-UI arm action.

This module implements ONLY the passive half. The
:class:`ConnectionManager` polls an injected :class:`PortEnumerator`
(a pure ``list_input_names`` / ``list_output_names`` surface — the real
implementation wraps :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider`
**enumeration only**), diffs the observed port landscape into a frozen
:class:`ConnectionState`, and fires an ``on_change`` callback exactly
once per observable change. Nothing in this module can construct,
open, or write to a MIDI **output** port: the enumerator Protocol has
no ``open_*`` method, and the enumeration-only facade
(:class:`ProviderPortEnumerator`) deliberately re-exports just the two
list methods so an injected provider's open/send surface is
unreachable through this seam.

Phases (see :data:`CONNECTION_PHASES`):

* ``disconnected`` — initial state; no poll has completed yet.
* ``searching`` — polling succeeds but no Elektron-looking port is
  visible (the operator sees "cable unplugged / device off").
* ``listening`` — an Elektron-looking **input** port is visible; the
  app is passively listening. No output is opened.
* ``armed`` — reserved for the ArmedApply seam. The manager itself
  NEVER produces this phase: arming is an explicit in-UI operator
  decision and never a side effect of enumeration (and therefore can
  never auto-re-arm after a reconnect — a disconnect simply drops the
  state back to ``searching`` / ``disconnected`` on the next poll).
* ``fault`` — the enumerator raised; ``last_error_fingerprint``
  carries a stable taxonomy string an operator can grep for.

The manager is deliberately transport-agnostic: the ``on_change``
callback is where ``__main__`` wires
:meth:`~rytm_randomizer.cockpit.ws.server.ConnectionRegistry.broadcast_event`
so every live WebSocket client receives a ``connection_changed`` event
(see :mod:`rytm_randomizer.cockpit.ws.protocol`).
"""

from __future__ import annotations

import asyncio
import contextlib
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Final, Literal, Protocol, get_args, runtime_checkable

from ...observability.errors import RytmRandomizerError
from ...observability.logging import get_logger
from ...real_midi_adapter import RealMidiPortError

_logger = get_logger(__name__)
"""Module logger for the passive connection brain (poll faults, phase
flips). Structured entries carry the taxonomy ``fingerprint`` field so
operators can correlate a ``fault`` phase on the UI with the underlying
enumeration failure without any exception text reaching the wire."""


ConnectionPhase = Literal["disconnected", "searching", "listening", "armed", "fault"]
"""The connection lifecycle vocabulary.

Mirrored (as an inline ``Literal``) by
:class:`rytm_randomizer.cockpit.ws.protocol.ConnectionStateDict` — the
wire-format authority. ``tests/cockpit/test_connection_manager.py``
pins the two in sync via :func:`typing.get_args` so a rename on either
side fails loudly.
"""

CONNECTION_PHASES: Final[tuple[str, ...]] = get_args(ConnectionPhase)
"""Runtime tuple of every :data:`ConnectionPhase` value (test + doc surface)."""

DEFAULT_POLL_INTERVAL_SECONDS: Final[float] = 2.0
"""Default port-poll cadence. Injectable so tests never sleep 2 real seconds."""

ELEKTRON_PORT_NAME_PATTERNS: Final[tuple[str, ...]] = (
    "analog rytm",
    "analog four",
    "elektron",
)
"""Case-insensitive substrings that mark a port name as an Elektron device.

Heuristic by design: CoreMIDI / ALSA / WinMM all decorate port names
differently ("Analog Rytm MK2", "Elektron Analog Four MKII MIDI 1", …),
but every observed spelling contains one of these three stems.
"""

_ENUMERATION_ERRORS: Final[tuple[type[BaseException], ...]] = (
    RealMidiPortError,
    OSError,
    RuntimeError,
    ValueError,
)
"""Exception families a hostile/absent MIDI backend can raise during
enumeration. ``MidoMidiPortProvider.list_*_names`` already funnels its
backend errors into :class:`RealMidiPortError` (a ``RuntimeError``
subclass); the extra arms cover injected test doubles and future
non-mido enumerators."""

_FALLBACK_FINGERPRINT_PREFIX: Final[str] = "cockpit.connection.enumeration_failed"
"""Fingerprint stem for non-taxonomy exceptions caught during a poll."""


@runtime_checkable
class DiagnosticsJournal(Protocol):
    """Duck-typed sink for wire-safe categorized error observations.

    Structurally satisfied by
    :class:`~rytm_randomizer.cockpit.diagnostics.ErrorJournal`; declared
    here as a Protocol so the passive connection brain stays import-light
    (no dependency edge onto the diagnostics module).
    """

    def record(
        self,
        fingerprint: str,
        message: str,
        context: Mapping[str, str] | None = None,
    ) -> object:
        """Append one categorized error observation."""


@runtime_checkable
class PortEnumerator(Protocol):
    """The passive enumeration seam the manager polls.

    Deliberately the *smallest possible* MIDI surface: two list methods,
    no ``open_*``, no ``send``. Any object with these two methods works —
    :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider` satisfies
    it structurally, and :class:`ProviderPortEnumerator` narrows a
    provider down to exactly this surface.
    """

    def list_input_names(self) -> tuple[str, ...]:
        """Return the currently visible MIDI input port names."""

    def list_output_names(self) -> tuple[str, ...]:
        """Return the currently visible MIDI output port names."""


class NullPortEnumerator:
    """Enumerator for hosts without a MIDI stack — always sees zero ports.

    Used by ``cockpit.__main__`` when ``mido`` is not importable so the
    cockpit still boots (phase stays ``searching``) instead of crashing
    on a missing optional dependency.
    """

    def list_input_names(self) -> tuple[str, ...]:
        """No MIDI stack — no inputs."""

        return ()

    def list_output_names(self) -> tuple[str, ...]:
        """No MIDI stack — no outputs."""

        return ()


class ProviderPortEnumerator:
    """Enumeration-only facade over a ``MidoMidiPortProvider``-shaped provider.

    The provider object also exposes ``open_output`` / ``open_input``;
    wrapping it behind this facade means nothing reachable from the
    :class:`ConnectionManager` can open a port — the Live-but-Passive
    guarantee is structural, not conventional.
    """

    def __init__(self, provider: PortEnumerator) -> None:
        """Capture the provider; only its two list methods are ever called."""

        self._provider = provider

    def list_input_names(self) -> tuple[str, ...]:
        """Delegate to the provider's input enumeration (lazy ``mido``)."""

        return tuple(self._provider.list_input_names())

    def list_output_names(self) -> tuple[str, ...]:
        """Delegate to the provider's output enumeration (lazy ``mido``)."""

        return tuple(self._provider.list_output_names())


def is_elektron_port_name(name: str) -> bool:
    """True when ``name`` looks like an Elektron device port (case-insensitive)."""

    lowered = name.lower()
    return any(pattern in lowered for pattern in ELEKTRON_PORT_NAME_PATTERNS)


@dataclass(frozen=True)
class ConnectionState:
    """One immutable observation of the MIDI connection landscape.

    ``changed_at`` is the (injectable) clock reading taken when this
    state replaced its predecessor; it is excluded from change
    detection (see :meth:`matches`) so a re-poll that observes the same
    landscape never re-fires ``on_change``.
    """

    phase: ConnectionPhase
    available_inputs: tuple[str, ...]
    available_outputs: tuple[str, ...]
    selected_input: str | None
    selected_output: str | None
    last_error_fingerprint: str | None
    changed_at: float

    def matches(self, other: ConnectionState) -> bool:
        """True when every field except ``changed_at`` equals ``other``'s."""

        return (
            self.phase == other.phase
            and self.available_inputs == other.available_inputs
            and self.available_outputs == other.available_outputs
            and self.selected_input == other.selected_input
            and self.selected_output == other.selected_output
            and self.last_error_fingerprint == other.last_error_fingerprint
        )

    def to_dict(self) -> dict:
        """JSON-safe dict matching ``protocol.ConnectionStateDict`` exactly."""

        return {
            "phase": self.phase,
            "available_inputs": list(self.available_inputs),
            "available_outputs": list(self.available_outputs),
            "selected_input": self.selected_input,
            "selected_output": self.selected_output,
            "last_error_fingerprint": self.last_error_fingerprint,
            "changed_at": self.changed_at,
        }


def _error_fingerprint(exc: BaseException) -> str:
    """Stable, wire-safe taxonomy string for an enumeration failure.

    Taxonomy exceptions carry their own ``fingerprint`` class attribute
    (OBS O4); anything else collapses to a deterministic
    ``cockpit.connection.enumeration_failed.<typename>`` stem. Never
    includes ``str(exc)`` — exception text stays in the structured log.
    """

    if isinstance(exc, RytmRandomizerError):
        return exc.fingerprint
    return f"{_FALLBACK_FINGERPRINT_PREFIX}.{type(exc).__name__.lower()}"


class ConnectionManager:
    """Poll-driven, passive connection-state tracker.

    Args:
        enumerator: The :class:`PortEnumerator` to poll. Tests inject a
            fake; production injects :class:`ProviderPortEnumerator`
            (or :class:`NullPortEnumerator` when ``mido`` is absent).
        poll_interval: Seconds between polls in :meth:`run`. Injectable
            so tests never sleep the production 2s cadence.
        on_change: Fired with the fresh :class:`ConnectionState` exactly
            once per observable diff (never for a no-change re-poll).
            ``__main__`` wires the WS broadcast here.
        clock: Timestamp source for ``changed_at``. Injectable for
            deterministic tests; defaults to :func:`time.time`.
    """

    def __init__(
        self,
        enumerator: PortEnumerator,
        *,
        poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
        on_change: Callable[[ConnectionState], None] | None = None,
        clock: Callable[[], float] = time.time,
        journal: DiagnosticsJournal | None = None,
    ) -> None:
        self._enumerator = enumerator
        self._poll_interval = float(poll_interval)
        self._on_change = on_change
        self._notify_hooks: list[Callable[[ConnectionState], None]] = []
        self._clock = clock
        self._journal = journal
        self._task: asyncio.Task[None] | None = None
        self._state = ConnectionState(
            phase="disconnected",
            available_inputs=(),
            available_outputs=(),
            selected_input=None,
            selected_output=None,
            last_error_fingerprint=None,
            changed_at=clock(),
        )

    @property
    def state(self) -> ConnectionState:
        """The latest observed :class:`ConnectionState` (frozen)."""

        return self._state

    @property
    def poll_interval(self) -> float:
        """Seconds between polls in :meth:`run` (fixed at construction)."""

        return self._poll_interval

    def add_notify_hook(self, hook: Callable[[ConnectionState], None]) -> None:
        """Register an additional per-diff observer (Wave 4).

        Hooks fire after ``on_change`` on every observable diff, in
        registration order. ``__main__`` uses this to wire the armed
        watchdog (device gone while armed → auto-disarm + fault signal)
        alongside the WS broadcast without composing closures by hand.
        Purely passive: a hook can never grant transmit authority.
        """

        self._notify_hooks.append(hook)

    def poll_once(self) -> ConnectionState:
        """Enumerate ports once; diff; fire ``on_change`` on a real change.

        Pure passive observation: the enumerator's two list methods are
        the only collaborator calls. An enumeration failure flips the
        phase to ``fault`` with a stable fingerprint; a later successful
        poll recovers to ``searching`` / ``listening`` automatically —
        but NEVER to ``armed`` (arming is not this manager's decision).

        Returns the current state (fresh on change, prior on no-change).
        """

        try:
            inputs = tuple(self._enumerator.list_input_names())
            outputs = tuple(self._enumerator.list_output_names())
        except _ENUMERATION_ERRORS as exc:
            fingerprint = _error_fingerprint(exc)
            _logger.warning(
                "connection_poll_enumeration_failed",
                extra={
                    "exception_type": type(exc).__name__,
                    "exception_repr": repr(exc),
                    "fingerprint": fingerprint,
                },
            )
            if self._journal is not None:
                # Wave 4: enumeration faults land in the injected bounded
                # error journal so the diagnostics command can replay them
                # (fingerprints only — never raw exception text).
                self._journal.record(
                    fingerprint,
                    "MIDI port enumeration failed",
                    context={"exception_type": type(exc).__name__},
                )
            candidate = ConnectionState(
                phase="fault",
                available_inputs=(),
                available_outputs=(),
                selected_input=None,
                selected_output=None,
                last_error_fingerprint=fingerprint,
                changed_at=self._clock(),
            )
        else:
            selected_input = next((n for n in inputs if is_elektron_port_name(n)), None)
            selected_output = next((n for n in outputs if is_elektron_port_name(n)), None)
            phase: ConnectionPhase = "listening" if selected_input is not None else "searching"
            candidate = ConnectionState(
                phase=phase,
                available_inputs=inputs,
                available_outputs=outputs,
                selected_input=selected_input,
                selected_output=selected_output,
                last_error_fingerprint=None,
                changed_at=self._clock(),
            )

        if candidate.matches(self._state):
            return self._state
        self._state = candidate
        if self._on_change is not None:
            self._on_change(candidate)
        for hook in self._notify_hooks:
            hook(candidate)
        return candidate

    async def run(self) -> None:
        """Poll forever at ``poll_interval`` until cancelled.

        The loop body is one synchronous :meth:`poll_once` plus one
        ``asyncio.sleep`` — cancellation (via :meth:`stop` or task
        teardown) is the only exit.
        """

        while True:
            self.poll_once()
            await asyncio.sleep(self._poll_interval)

    async def start(self) -> None:
        """Spawn the :meth:`run` loop as a background task (idempotent).

        Registered as the FastAPI ``startup`` handler by ``__main__`` so
        the loop lands on uvicorn's serving event loop — the same loop
        the per-connection outbound queues capture, which is what makes
        the broadcast fan-out loop-safe.
        """

        if self._task is not None:
            return
        self._task = asyncio.get_running_loop().create_task(self.run())

    async def stop(self) -> None:
        """Cancel + await the background poll task (idempotent)."""

        task = self._task
        self._task = None
        if task is None:
            return
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task


# ---------------------------------------------------------------------------
# Active-manager registration seam.
#
# The WS handlers build ``session_status`` events from a ``CockpitSession``
# alone, but the connection phase lives on the process's one
# ConnectionManager (owned by ``__main__``). Mirroring the
# ``devices/registry.py`` pattern, the manager registers itself here and
# the handlers read it back — an explicit, documented seam rather than a
# dynamic attribute side-channel on the session (which
# ``tests/architecture/test_no_side_channel_session_attrs.py`` forbids).
# Phase-1 scope is one cockpit session per process, so a per-process
# registration is exactly the right cardinality.
# ---------------------------------------------------------------------------

_active_manager: ConnectionManager | None = None


def set_active_connection_manager(manager: ConnectionManager | None) -> None:
    """Register (or clear, with ``None``) the process's ConnectionManager."""

    global _active_manager
    _active_manager = manager


def active_connection_manager() -> ConnectionManager | None:
    """Return the registered ConnectionManager, or ``None`` when unwired."""

    return _active_manager


__all__ = [
    "CONNECTION_PHASES",
    "DEFAULT_POLL_INTERVAL_SECONDS",
    "ELEKTRON_PORT_NAME_PATTERNS",
    "ConnectionManager",
    "ConnectionPhase",
    "ConnectionState",
    "DiagnosticsJournal",
    "NullPortEnumerator",
    "PortEnumerator",
    "ProviderPortEnumerator",
    "active_connection_manager",
    "is_elektron_port_name",
    "set_active_connection_manager",
]
