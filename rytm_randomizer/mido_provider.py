"""Concrete ``mido``-backed real MIDI port provider.

This module is import-safe: it does NOT import ``mido`` at module load time.
The ``mido`` import is lazy and happens only inside provider methods, the first
time hardware port discovery or opening is actually requested. Importing this
module therefore opens no ports, touches no hardware, and pulls in no real MIDI
library -- consistent with the passive package import contract.

The provider implements the same surface as
:class:`rytm_randomizer.real_midi_adapter.RealMidiPortProvider` so it can be
injected through the existing ``real_midi_adapter`` boundary
(``RealMidiSender`` / ``build_real_midi_sender``).
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING, Protocol

from .observability.logging import get_logger
from .observability.tracing import operation
from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from .real_midi_adapter import RealMidiOutputPort

__all__ = ["MidoMidiPortProvider", "build_mido_midi_port_provider"]

_logger = get_logger(__name__)


class RealMidiInputPort(Protocol):
    """Minimal input-port protocol for passive pending-message capture."""

    def iter_pending(self) -> Iterable[object]:
        """Return an iterable of backend-specific pending input messages."""


def _import_mido():
    """Lazily import ``mido``; raise a guarded error if it is unavailable."""

    try:
        import mido  # noqa: PLC0415 - intentional lazy import for import-safety
    except ImportError as exc:  # pragma: no cover - depends on environment
        _logger.warning(
            "mido_import_failed",
            extra={"reason": "ImportError"},
        )
        raise RealMidiDependencyError(
            "mido_not_installed: install 'mido' and a backend "
            "(e.g. python-rtmidi) to open real MIDI ports"
        ) from exc
    _logger.debug("mido_imported_ok")
    return mido


class MidoMidiPortProvider:
    """Real MIDI port provider backed by ``mido``.

    Duck-types :class:`rytm_randomizer.real_midi_adapter.RealMidiPortProvider`:
    it exposes output methods for ``RealMidiSender`` and input methods for
    explicit passive capture paths. ``mido`` is imported lazily inside these
    methods only.
    """

    def list_output_names(self) -> tuple[str, ...]:
        """Return available hardware MIDI output port names (lazy ``mido``)."""

        mido = _import_mido()
        # ``mido.get_output_names()`` delegates to the active backend
        # (python-rtmidi / portmidi / alsa / coremidi); each backend raises
        # its own family of errors -- ``OSError`` for system-level failures,
        # ``RuntimeError`` for backend assertions, ``ImportError`` if the
        # backend is half-installed. We catch that family and re-raise as a
        # single, taxonomy-aware ``RealMidiPortError`` so callers see one
        # canonical type at the boundary.
        try:
            names = mido.get_output_names()
        except (
            OSError,
            RuntimeError,
            ImportError,
            AttributeError,
        ) as exc:  # pragma: no cover - backend specific
            raise RealMidiPortError(
                "midi_output_discovery_failed",
                context={"underlying": repr(exc)},
            ) from exc
        return tuple(names)

    def list_input_names(self) -> tuple[str, ...]:
        """Return available hardware MIDI input port names (lazy ``mido``)."""

        mido = _import_mido()
        try:
            names = mido.get_input_names()
        except (
            OSError,
            RuntimeError,
            ImportError,
            AttributeError,
        ) as exc:  # pragma: no cover - backend specific
            raise RealMidiPortError(
                "midi_input_discovery_failed",
                context={"underlying": repr(exc)},
            ) from exc
        return tuple(names)

    def open_output(self, port_name: str) -> RealMidiOutputPort:
        """Open a hardware MIDI output port by name (lazy ``mido``).

        Wrapped in an :func:`~rytm_randomizer.observability.tracing.operation`
        span so a ``--debug`` log records exactly which port the operator
        selected, when the backend opened it, and how long it took. The
        ``RealMidiPortError`` paths bubble out through the span and are
        captured by tracing as an ``operation_error`` log line.
        """

        if not isinstance(port_name, str) or not port_name:
            raise RealMidiPortError("midi_output_port_required")

        with operation("open_output", port_name=port_name):
            mido = _import_mido()
            available = self.list_output_names()
            if port_name not in available:
                raise RealMidiPortError(f"unknown_midi_output_port: {port_name}")
            # Same backend-family catch as ``list_output_names``: every realistic
            # mido backend can fail to open a port with one of these errors. We
            # convert to a single ``RealMidiPortError`` at the boundary.
            try:
                port = mido.open_output(port_name)
            except (
                OSError,
                RuntimeError,
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - backend specific
                raise RealMidiPortError(
                    f"unavailable_midi_output_port: {port_name}",
                    context={"underlying": repr(exc)},
                ) from exc
            if not callable(getattr(port, "send", None)):
                raise RealMidiPortError(f"invalid_midi_output_port: {port_name}")
            return port

    def open_input(self, port_name: str) -> RealMidiInputPort:
        """Open a hardware MIDI input port by name (lazy ``mido``)."""

        if not isinstance(port_name, str) or not port_name:
            raise RealMidiPortError("midi_input_port_required")

        with operation("open_input", port_name=port_name):
            mido = _import_mido()
            available = self.list_input_names()
            if port_name not in available:
                raise RealMidiPortError(f"unknown_midi_input_port: {port_name}")
            try:
                port = mido.open_input(port_name)
            except (
                OSError,
                RuntimeError,
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - backend specific
                raise RealMidiPortError(
                    f"unavailable_midi_input_port: {port_name}",
                    context={"underlying": repr(exc)},
                ) from exc
            if not callable(getattr(port, "iter_pending", None)):
                raise RealMidiPortError(f"invalid_midi_input_port: {port_name}")
            return port


def build_mido_midi_port_provider() -> MidoMidiPortProvider:
    """Build the concrete ``mido``-backed provider (no hardware touched yet)."""

    return MidoMidiPortProvider()
