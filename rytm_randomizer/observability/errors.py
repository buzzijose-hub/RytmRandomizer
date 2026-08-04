# pyright: reportUnsupportedDunderAll=false
"""Unified error taxonomy for the RytmRandomizer package.

WHAT
====

Defines :class:`RytmRandomizerError` as the single root of the package's
error hierarchy and five taxonomy bases beneath it:

* :class:`MidiError` -- MIDI-boundary failures. ``RealMidiDependencyError``
  / ``RealMidiPortError`` / ``RealMidiSendError`` in
  :mod:`rytm_randomizer.real_midi_adapter` are re-homed under this via
  multi-inheritance so existing ``except`` clauses keep working AND new
  callers can ``except MidiError`` to catch the whole MIDI boundary.
* :class:`StateError` -- invalid state transitions, missing required
  runtime state, contract violations on the state holders.
* :class:`DataError` -- missing or malformed entry in the data layer
  (``rytm_randomizer/data/``). ``MockMessageMappingError`` is re-homed here.
* :class:`BoundaryError` -- generic boundary / contract violation that
  does not fit MIDI or data buckets. ``ActiveBoundaryError`` is re-homed
  here.
* :class:`ConfigError` -- config / mode misuse (e.g. running ``--arm``
  with ``--dry-run`` together, or a typo in a level name passed to
  :func:`~rytm_randomizer.observability.logging.configure_logging`).

Every member carries an optional ``context: Mapping`` for structured
diagnostic data, frozen after construction. Stringifying the error
appends a deterministic ``[context: ...]`` tail when non-empty.

WHY
===

Two consumers depend on this shape:

1. **Operator log triage.** Every concrete subclass declares a stable
   ``fingerprint`` class attribute -- a lowercase dot-separated path
   ``<subsystem>.<verb>.<noun>`` (e.g. ``"midi.port.open_failed"``,
   ``"export.write.failed"``). Operators ``grep`` on fingerprints in
   logs; a future Sentry / alerting tier groups on them. The
   fingerprint is the one vocabulary shared across logs, metrics, and
   breadcrumbs. The root base + five taxonomy bases carry placeholder
   ``<family>.error.unspecified`` fingerprints so an inadvertent raw
   raise still has *some* aggregator; concrete subclasses override.

2. **Caller backwards-compatibility.** Class identity is preserved for
   re-homed errors: the original module (``real_midi_adapter`` /
   ``mock_message_mapper`` / ``active_boundary``) still owns the class
   object so ``isinstance(...)`` checks and ``import`` paths in
   existing tests are unchanged. This module re-exports them solely as
   a convenience -- it does NOT shadow the canonical owners.

The dual structure (taxonomy bases + per-call ``context``) prevents two
specific bug classes: stringly-typed error-type sniffing (callers branch
on ``isinstance`` against the taxonomy, not on ``str(exc)`` substrings)
and lost diagnostic context (the ``context`` mapping carries the
structured payload an operator needs without inflating the message text
sent to the wire / log formatter).

REFERENCES
==========

* ``rytm_randomizer/real_midi_adapter.py`` -- the re-homed MIDI errors.
* ``rytm_randomizer/mock_message_mapper.py`` -- the re-homed data error.
* ``rytm_randomizer/active_boundary.py`` -- the re-homed boundary error.
* OBSERVABILITY_REVIEW.md OBS O4 -- fingerprint discipline.
* ``tests/architecture/test_observability.py`` -- enforces every package
  ``raise`` either uses the taxonomy or an allowlisted stdlib class.
* CODE_REVIEW.md P7 -- the docstring-reorder finding behind this header
  structure.
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
    "MidiEventPlanSendError",
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


class MidiEventPlanSendError(MidiError, RuntimeError):
    """A validated MIDI event plan failed after partial or zero delivery."""

    fingerprint: ClassVar[str] = "midi.event_plan.send_failed"

    def __init__(
        self,
        message: str,
        *,
        sent_message_count: int,
        expected_message_count: int,
        interrupted: bool = False,
    ) -> None:
        super().__init__(
            message,
            context={
                "sent_message_count": sent_message_count,
                "expected_message_count": expected_message_count,
                "interrupted": interrupted,
            },
        )
        self.sent_message_count = sent_message_count
        self.expected_message_count = expected_message_count
        self.interrupted = interrupted


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

    .. note::

        **CODE_REVIEW.md finding H8 — documented punt (target: post-Phase 3).**

        (a) *Why this helper exists today*: it lets us preserve the original
        class identity (so ``isinstance(exc, real_midi_adapter.RealMidiPortError)``
        keeps working for callers that already imported the legacy name) while
        also re-exporting the same class under :mod:`observability.errors` so a
        new caller can write ``except MidiError:``. The lazy
        :func:`importlib.import_module` call keeps this module a leaf of the
        package import graph (the architecture test in
        ``tests/architecture/test_no_side_effects.py`` enforces that
        :mod:`observability` does not eagerly drag the real-MIDI adapter into
        ``sys.modules`` on import).

        (b) *What would replace it*: **declarative bases.** Move the bare
        ``MidiError`` / ``DataError`` / ``BoundaryError`` class definitions
        here (already done), and have ``real_midi_adapter.py`` /
        ``mock_message_mapper.py`` / ``active_boundary.py`` import those bases
        directly and subclass them at class-definition time. The
        ``__getattr__`` PEP 562 re-export below would shrink to a static
        ``from .real_midi_adapter import RealMidiPortError`` tuple. The
        :func:`importlib.import_module` indirection vanishes.

        (c) *Why it is a punt, not a fix today*: declaring the bases here and
        having the leaf modules subclass them inverts the current import
        direction (today the leaves don't import :mod:`observability.errors`).
        That inversion needs an architecture-test refresh, a sweep of the
        circular-import landscape (``real_midi_adapter`` is imported by the
        active stack at startup; ``observability.errors`` is on the boot
        path), and migration of every existing ``except RuntimeError`` /
        ``except ValueError`` call site that relies on the legacy
        multi-inheritance shape. CODE_REVIEW.md classifies H8 as HIGH
        rather than CRITICAL specifically because the architecture test
        *catches* the import-direction violation today, so the runtime
        mechanism here is the operative safety net.

        **TODO (H8)**: refactor to declarative inheritance after the Phase 3
        cockpit-export pipeline ships and the real-MIDI adapter's import
        graph is decoupled from the ``--arm`` boot path. Track in a
        follow-up PR; do NOT bundle with unrelated work because the import
        graph shift will touch every architecture test in
        ``tests/architecture/test_import_direction.py``.
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
