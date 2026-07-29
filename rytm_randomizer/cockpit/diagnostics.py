"""Error journal + operator health surface for the cockpit (WS-4).

Two small, injected pieces:

* :class:`ErrorJournal` — a bounded, **in-instance** ring of the last 50
  categorized errors ``{fingerprint, message, context, ts}``. There is no
  module-level journal: the process's one journal lives on the
  :class:`~rytm_randomizer.cockpit.ws.session.CockpitSession` and is
  injected wherever it is written (WS dispatcher, arm/disarm handlers,
  the passive :class:`~rytm_randomizer.cockpit.device.connection.ConnectionManager`).
  Entries carry taxonomy fingerprints (OBS O4) — never raw exception
  text — so the journal is wire-safe by construction.
* :func:`build_diagnostics_payload` — the read-only packet the
  ``diagnostics`` WS command returns: journal entries, the metrics
  ``errors_by_kind`` counter, the latest passive connection state,
  the enumerated ports, and a per-OS MIDI driver hint string.
"""

from __future__ import annotations

import sys
import time
from collections import deque
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final

from ..observability.metrics import get_metrics

__all__ = [
    "DEFAULT_JOURNAL_CAPACITY",
    "ErrorJournal",
    "ErrorJournalEntry",
    "build_diagnostics_payload",
    "driver_hint",
]

DEFAULT_JOURNAL_CAPACITY: Final[int] = 50
"""The journal keeps the last 50 categorized errors (spec-pinned bound)."""

_DRIVER_HINTS: Final[Mapping[str, str]] = MappingProxyType(
    {
        "darwin": (
            "macOS CoreMIDI: check Audio MIDI Setup > MIDI Studio; replug the USB "
            "cable and confirm the Rytm shows as an online device."
        ),
        "win32": (
            "Windows MME: close other apps holding the MIDI port (Overbridge, DAWs) "
            "— Windows allows only one client per port; then replug the USB cable."
        ),
        "linux": (
            "Linux ALSA: run `amidi -l` to confirm the kernel sees the device; check "
            "snd-usb-audio is loaded and your user is in the `audio` group."
        ),
    }
)
"""Per-OS operator hints, keyed by ``sys.platform`` prefix."""

_DEFAULT_DRIVER_HINT: Final[str] = (
    "Unknown platform: confirm the OS MIDI stack sees the device, then replug "
    "the USB cable and restart the cockpit sidecar."
)
"""Fallback hint for platforms outside the known ``sys.platform`` set."""


def driver_hint(platform: str | None = None) -> str:
    """Return the operator-facing MIDI driver hint for ``platform``.

    ``platform`` defaults to :data:`sys.platform`. Matching is by prefix
    (``linux2`` and friends resolve to the ``linux`` hint).
    """

    key = sys.platform if platform is None else platform
    for prefix, hint in _DRIVER_HINTS.items():
        if key.startswith(prefix):
            return hint
    return _DEFAULT_DRIVER_HINT


@dataclass(frozen=True)
class ErrorJournalEntry:
    """One categorized, wire-safe error observation."""

    fingerprint: str
    message: str
    context: Mapping[str, str] = field(default_factory=dict)
    ts: float = 0.0

    def __post_init__(self) -> None:
        """Freeze the context mapping so entries are safely shareable."""

        object.__setattr__(self, "context", MappingProxyType(dict(self.context)))

    def to_dict(self) -> dict:
        """JSON-safe dict form for the ``diagnostics`` ack payload."""

        return {
            "fingerprint": self.fingerprint,
            "message": self.message,
            "context": dict(self.context),
            "ts": self.ts,
        }


class ErrorJournal:
    """Bounded in-instance journal of the last N categorized errors.

    Args:
        capacity: Ring bound — the oldest entry is dropped once full.
        clock: Timestamp source (injectable for deterministic tests).
    """

    def __init__(
        self,
        *,
        capacity: int = DEFAULT_JOURNAL_CAPACITY,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._entries: deque[ErrorJournalEntry] = deque(maxlen=capacity)
        self._clock = clock

    @property
    def capacity(self) -> int:
        """The ring bound this journal was constructed with."""

        maxlen = self._entries.maxlen
        return maxlen if maxlen is not None else 0

    @property
    def entries(self) -> tuple[ErrorJournalEntry, ...]:
        """The journal contents, oldest first (frozen view)."""

        return tuple(self._entries)

    def record(
        self,
        fingerprint: str,
        message: str,
        context: Mapping[str, str] | None = None,
    ) -> ErrorJournalEntry:
        """Append one categorized error; returns the stored entry."""

        entry = ErrorJournalEntry(
            fingerprint=str(fingerprint),
            message=str(message),
            context={} if context is None else {str(k): str(v) for k, v in context.items()},
            ts=self._clock(),
        )
        self._entries.append(entry)
        return entry

    def to_dicts(self) -> list[dict]:
        """The journal contents as JSON-safe dicts, oldest first."""

        return [entry.to_dict() for entry in self._entries]


def build_diagnostics_payload(
    *,
    journal: ErrorJournal | None,
    connection_state: Mapping[str, object] | None,
    platform: str | None = None,
) -> dict:
    """Assemble the read-only ``diagnostics`` WS command payload.

    Args:
        journal: The session's :class:`ErrorJournal` (or ``None`` for a
            journal-less embedded harness — the payload then carries an
            empty list, never crashes).
        connection_state: The latest passive
            :meth:`~rytm_randomizer.cockpit.device.connection.ConnectionState.to_dict`
            payload, or ``None`` when no ConnectionManager is registered.
        platform: ``sys.platform`` override for deterministic tests.
    """

    metrics = get_metrics()
    available_inputs: list[str] = []
    available_outputs: list[str] = []
    if connection_state is not None:
        raw_inputs = connection_state.get("available_inputs", [])
        raw_outputs = connection_state.get("available_outputs", [])
        if isinstance(raw_inputs, (list, tuple)):
            available_inputs = [str(name) for name in raw_inputs]
        if isinstance(raw_outputs, (list, tuple)):
            available_outputs = [str(name) for name in raw_outputs]
    return {
        "journal": [] if journal is None else journal.to_dicts(),
        "errors_by_kind": dict(metrics.errors_by_kind),
        "connection": None if connection_state is None else dict(connection_state),
        "available_inputs": available_inputs,
        "available_outputs": available_outputs,
        "platform": sys.platform if platform is None else platform,
        "driver_hint": driver_hint(platform),
    }
