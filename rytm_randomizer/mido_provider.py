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
from time import monotonic, sleep
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


def _import_rtmidi():
    """Lazily import ``rtmidi`` for raw SysEx input capture."""

    try:
        import rtmidi  # noqa: PLC0415 - intentional lazy import for import-safety
    except ImportError as exc:  # pragma: no cover - depends on environment
        _logger.warning(
            "rtmidi_import_failed",
            extra={"reason": "ImportError"},
        )
        raise RealMidiDependencyError(
            "rtmidi_not_installed: install 'python-rtmidi' to capture SysEx"
        ) from exc
    _logger.debug("rtmidi_imported_ok")
    return rtmidi


def _coerce_midi_data(candidate: object) -> bytes | None:
    """Return raw MIDI bytes from one backend message."""

    if not isinstance(candidate, tuple) or not candidate:
        return None
    message = candidate[0]
    if not isinstance(message, (bytes, bytearray, list, tuple)):
        return None
    try:
        data = bytes(int(value) & 0xFF for value in message)
    except (TypeError, ValueError):
        return None
    return data


def _coerce_sysex_frame(candidate: object) -> bytes | None:
    """Return a complete framed SysEx byte string from one backend message."""

    data = _coerce_midi_data(candidate)
    if data is None or len(data) < 2 or data[0] != 0xF0 or data[-1] != 0xF7:
        return None
    return data


def _append_sysex_chunk(buffer: bytearray, data: bytes) -> bytes | None:
    """Append raw MIDI bytes and return a complete SysEx frame when available."""

    try:
        start = data.index(0xF0)
    except ValueError:
        if not buffer:
            return None
        start = 0

    chunk = data[start:]
    if not buffer and (not chunk or chunk[0] != 0xF0):
        return None
    buffer.extend(chunk)
    try:
        end = buffer.index(0xF7)
    except ValueError:
        return None
    frame = bytes(buffer[: end + 1])
    del buffer[: end + 1]
    return frame


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

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        """Capture the first complete SysEx frame from a hardware input.

        This uses raw ``python-rtmidi`` instead of ``mido`` so SysEx receiving
        can explicitly disable the backend's default SysEx ignore filter.
        """

        if not isinstance(port_name, str) or not port_name:
            raise RealMidiPortError("midi_input_port_required")
        if timeout_seconds <= 0:
            raise RealMidiPortError("midi_sysex_capture_timeout_seconds_required")

        with operation("capture_sysex_messages", port_name=port_name):
            rtmidi = _import_rtmidi()
            try:
                midi_in = rtmidi.MidiIn()
                available = tuple(midi_in.get_ports())
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

            if port_name not in available:
                close_port = getattr(midi_in, "close_port", None)
                if callable(close_port):
                    close_port()
                raise RealMidiPortError(f"unknown_midi_input_port: {port_name}")

            try:
                midi_in.ignore_types(sysex=False, timing=True, active_sense=True)
                midi_in.open_port(available.index(port_name))
                deadline = monotonic() + timeout_seconds
                sysex_buffer = bytearray()
                while monotonic() < deadline:
                    message = midi_in.get_message()
                    frame = _coerce_sysex_frame(message)
                    if frame is None:
                        data = _coerce_midi_data(message)
                        if data is not None:
                            frame = _append_sysex_chunk(sysex_buffer, data)
                    if frame is not None:
                        return (frame,)
                    sleep(0.01)
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
            finally:
                close_port = getattr(midi_in, "close_port", None)
                if callable(close_port):
                    try:
                        close_port()
                    except (OSError, RuntimeError, AttributeError):  # pragma: no cover
                        _logger.debug("rtmidi_sysex_capture_close_failed_best_effort")

        raise RealMidiPortError("midi_sysex_capture_timeout")


def build_mido_midi_port_provider() -> MidoMidiPortProvider:
    """Build the concrete ``mido``-backed provider (no hardware touched yet)."""

    return MidoMidiPortProvider()
