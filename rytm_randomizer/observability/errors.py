"""Unified error taxonomy for the RytmRandomizer package (Wave 4 / WS-U).

This module defines a single :class:`RytmRandomizerError` root with a small,
practical hierarchy:

* :class:`MidiError` -- base for MIDI-boundary failures. The existing
  ``RealMidiDependencyError`` / ``RealMidiPortError`` / ``RealMidiSendError``
  in :mod:`rytm_randomizer.real_midi_adapter` are re-homed under it via
  multi-inheritance so existing ``except`` clauses keep working AND new
  callers can ``except MidiError`` to catch the whole MIDI boundary.
* :class:`StateError` -- invalid state transitions, missing required runtime
  state, contract violations on the state holders.
* :class:`DataError` -- a missing or malformed entry in the data layer
  (``rytm_randomizer/data/``). ``MockMessageMappingError`` is re-homed here.
* :class:`BoundaryError` -- a generic boundary / contract violation that
  does not fit the MIDI or data buckets. ``ActiveBoundaryError`` is re-homed
  here.
* :class:`ConfigError` -- config / mode misuse (e.g. running ``--arm`` and
  ``--dry-run`` together, or a typo in a level name passed to
  :func:`~rytm_randomizer.observability.logging.configure_logging`).

Every member of the hierarchy carries an optional ``context: Mapping`` so a
caller can attach structured diagnostic data alongside the message:

.. code-block:: python

    raise StateError(
        "no profile selected",
        context={"command": "m", "active_profile": None},
    )

The ``context`` is read-only after construction. Stringifying the error keeps
the original message but appends a deterministic ``[context: ...]`` tail when
non-empty, so a logged exception still shows the structured data without
needing custom formatting.

Class identity is preserved for the re-homed errors: the original module
(``real_midi_adapter`` / ``mock_message_mapper`` / ``active_boundary``)
still owns the class object so ``isinstance(...)`` checks and ``import``
paths in existing tests are unchanged. This module re-exports them solely
as a convenience.

OBS O4 -- fingerprint discipline. Every concrete subclass of
:class:`RytmRandomizerError` declares a stable, short ``fingerprint``
class attribute -- a lowercase dot-separated path of the form
``<subsystem>.<verb>.<noun>`` (e.g. ``"midi.port.open_failed"``,
``"export.write.failed"``). The fingerprint is what an operator
``grep``s for in logs and what a future Sentry / alerting tier groups
on; it is the same vocabulary across logs, metrics, and breadcrumbs.
The root base and the five taxonomy bases carry placeholder
``<family>.error.unspecified`` fingerprints so an inadvertent raw
raise still has *some* aggregator; concrete subclasses override.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import MappingProxyType
from typing import ClassVar

__all__ = [
    "ActiveBoundaryError",
    "BoundaryError",
    "ConfigError",
    "DataError",
    "MidiError",
    "MockMessageMappingError",
    "RealMidiDependencyError",
    "RealMidiPortError",
    "RealMidiSendError",
    "RytmRandomizerError",
    "StateError",
]


def _freeze_context(context: Mapping[str, object] | None) -> Mapping[str, object]:
    """Return an immutable view of ``context`` (empty when ``None``)."""

    if context is None:
        return MappingProxyType({})
    return MappingProxyType(dict(context))


class RytmRandomizerError(Exception):
    """Base for every error raised by the RytmRandomizer package.

    Carries an optional ``context`` mapping that callers use to attach
    structured diagnostic data. The ``context`` is captured as an immutable
    view at construction time.

    OBS O4: every concrete subclass declares a stable, short ``fingerprint``
    class attribute (a lowercase dot-separated path). The root carries a
    fallback so a raw ``raise RytmRandomizerError(...)`` still aggregates.
    """

    fingerprint: ClassVar[str] = "rytm_randomizer.error.unspecified"

    def __init__(
        self,
        message: str = "",
        *,
        context: Mapping[str, object] | None = None,
    ) -> None:
        super().__init__(message)
        self._message = message
        self._context: Mapping[str, object] = _freeze_context(context)

    @property
    def message(self) -> str:
        """The plain message portion (without the context tail)."""

        return self._message

    @property
    def context(self) -> Mapping[str, object]:
        """The structured context attached to this error (read-only)."""

        return self._context

    def __str__(self) -> str:
        if not self._context:
            return self._message
        ctx = ", ".join(f"{k}={v!r}" for k, v in self._context.items())
        return f"{self._message} [context: {ctx}]"


class MidiError(RytmRandomizerError):
    """Base for failures at the MIDI boundary (port open, send, translate)."""

    fingerprint: ClassVar[str] = "midi.error.unspecified"


class StateError(RytmRandomizerError):
    """Invalid runtime state transition or missing required state."""

    fingerprint: ClassVar[str] = "state.error.unspecified"


class DataError(RytmRandomizerError):
    """Missing or malformed data-layer entry."""

    fingerprint: ClassVar[str] = "data.error.unspecified"


class BoundaryError(RytmRandomizerError):
    """Generic boundary / contract violation that is not MIDI- or data-shaped."""

    fingerprint: ClassVar[str] = "boundary.error.unspecified"


class ConfigError(RytmRandomizerError):
    """Configuration or mode misuse (CLI flags, log level names, etc.)."""

    fingerprint: ClassVar[str] = "config.error.unspecified"


# ---------------------------------------------------------------------------
# Re-home the existing module-local error classes under the taxonomy.
#
# Multi-inheritance preserves the original ancestors (``RuntimeError`` /
# ``ValueError``) so existing call sites of ``except RuntimeError`` /
# ``except ValueError`` keep working. The class *identity* is also preserved
# because the class object still lives in its original module; this module
# just re-exports a reference. ``isinstance(exc, MidiError)`` now succeeds
# for every legacy MIDI-adapter error, which is the win.
# ---------------------------------------------------------------------------


def _rehome(original_module: str, class_name: str, new_base: type) -> type:
    """Re-home an existing class under ``new_base`` without breaking imports.

    The original module already imports cleanly with its own definition; this
    helper does NOT *replace* the original class. It only fetches it from the
    already-loaded module (when present) so the re-export here is the *same*
    object. The actual multi-inheritance is done in the original module's
    source (see ``real_midi_adapter.py`` / ``mock_message_mapper.py`` /
    ``active_boundary.py`` updates in this WS-U change set).

    We keep this helper as documentation for future maintainers: "we wire the
    new base in the original module, then re-export here so call sites can
    pick whichever import path is convenient".
    """

    import importlib  # noqa: PLC0415 - lazy to keep this module a pure-data leaf

    module = importlib.import_module(original_module)
    cls = getattr(module, class_name)
    if not issubclass(cls, new_base):  # pragma: no cover - defensive
        raise TypeError(f"{original_module}.{class_name} must inherit from {new_base.__name__}")
    return cls


def __getattr__(name: str) -> type:
    """Lazily re-export re-homed error classes from their original modules.

    PEP 562 module-level ``__getattr__``. Resolves ``RealMidiDependencyError``
    / ``RealMidiPortError`` / ``RealMidiSendError`` /
    ``MockMessageMappingError`` / ``ActiveBoundaryError`` on first access by
    importing the original module. The lazy import keeps this module a leaf
    of the package import graph (the architecture test enforces it), so
    importing :mod:`rytm_randomizer.observability` itself does not drag in
    the MIDI adapter and friends.
    """

    if name == "RealMidiDependencyError":
        return _rehome("rytm_randomizer.real_midi_adapter", name, MidiError)
    if name == "RealMidiPortError":
        return _rehome("rytm_randomizer.real_midi_adapter", name, MidiError)
    if name == "RealMidiSendError":
        return _rehome("rytm_randomizer.real_midi_adapter", name, MidiError)
    if name == "MockMessageMappingError":
        return _rehome("rytm_randomizer.mock_message_mapper", name, DataError)
    if name == "ActiveBoundaryError":
        return _rehome("rytm_randomizer.active_boundary", name, BoundaryError)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
