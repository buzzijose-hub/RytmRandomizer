"""Concrete ``mido``-backed real MIDI port provider.

This module is import-safe: it does NOT import ``mido`` at module load time.
The ``mido`` import is lazy and happens only inside provider methods, the first
time hardware port discovery or opening is actually requested. Importing this
module therefore opens no ports, touches no hardware, and pulls in no real MIDI
library -- consistent with the passive package import contract.

The provider implements
:class:`rytm_randomizer.real_midi_adapter.RealMidiOutputProvider` plus the
input methods used by app-owned capture operations. It is constructed only
after ``python -m rytm_randomizer.app --arm`` validates the selected feature's
guards; passive commands never construct it.
"""

from __future__ import annotations

from abc import abstractmethod
from collections.abc import Callable, Iterable
from time import monotonic, sleep
from typing import TYPE_CHECKING, Protocol, cast

from .observability.logging import get_logger
from .observability.tracing import operation
from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError, RealMidiSendError

if TYPE_CHECKING:
    from .real_midi_adapter import RealMidiOutputPort

__all__ = [
    "MidoMidiPortProvider",
    "WireOutputPort",
    "build_mido_midi_port_provider",
    "neutral_cc_fields",
]

_logger = get_logger(__name__)


class RealMidiInputPort(Protocol):
    """Minimal input-port protocol for passive pending-message capture.

    Method-style members (not ``Callable`` attributes) so this protocol
    satisfies method-style consumer seams like
    :class:`rytm_randomizer.cockpit.device.midi_monitor.MidiInputPortLike`.
    """

    def iter_pending(self) -> Iterable[object]:
        """Return an iterable of backend-specific pending input messages."""
        ...

    def close(self) -> None:
        """Release the backend input port."""
        ...


class _MidoModule(Protocol):
    """Typed surface used from the lazily imported ``mido`` module."""

    Message: Callable[..., object]
    get_output_names: Callable[[], Iterable[str]]
    get_input_names: Callable[[], Iterable[str]]
    open_output: Callable[[str], RealMidiOutputPort]
    open_input: Callable[[str], RealMidiInputPort]


class _RtMidiInput(Protocol):
    """Typed raw-input surface used for guarded SysEx capture."""

    get_ports: Callable[[], Iterable[str]]
    ignore_types: Callable[..., None]
    open_port: Callable[[int], None]
    get_message: Callable[[], object]
    close_port: Callable[[], None]


class _RtMidiModule(Protocol):
    """Typed surface used from the lazily imported ``rtmidi`` module."""

    MidiIn: Callable[[], _RtMidiInput]


class _IntConvertible(Protocol):
    """Value accepted by ``int`` at the raw backend coercion boundary."""

    @abstractmethod
    def __int__(self) -> int: ...


def _close_rejected_port(port: object, *, direction: str) -> None:
    """Best-effort close a backend object that failed the port contract."""

    close = getattr(port, "close", None)
    if not callable(close):
        return
    try:
        close()
    except (KeyboardInterrupt, SystemExit, OSError, RuntimeError, AttributeError) as exc:
        _logger.warning(
            "invalid_midi_port_close_failed_best_effort",
            extra={
                "direction": direction,
                "error_type": type(exc).__name__,
                "fingerprint": f"midi.{direction}.invalid_port_close_failed",
            },
        )


def _import_mido() -> _MidoModule:
    """Lazily import ``mido``; raise a guarded error if it is unavailable."""

    try:
        import mido  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
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
    return cast(_MidoModule, mido)


def _import_rtmidi() -> _RtMidiModule:
    """Lazily import ``rtmidi`` for raw SysEx input capture."""

    try:
        import rtmidi  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - depends on environment
        _logger.warning(
            "rtmidi_import_failed",
            extra={"reason": "ImportError"},
        )
        raise RealMidiDependencyError(
            "rtmidi_not_installed: install 'python-rtmidi' to capture SysEx"
        ) from exc
    _logger.debug("rtmidi_imported_ok")
    return cast(_RtMidiModule, rtmidi)


def _coerce_midi_data(candidate: object) -> bytes | None:
    """Return raw MIDI bytes from one backend message."""

    if not isinstance(candidate, tuple) or not candidate:
        return None
    message = cast(tuple[object, ...], candidate)[0]
    if not isinstance(message, (bytes, bytearray, list, tuple)):
        return None
    values = cast(Iterable[object], message)
    try:
        data = bytes(int(cast(_IntConvertible, value)) & 0xFF for value in values)
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
    buffer.extend(chunk)
    try:
        end = buffer.index(0xF7)
    except ValueError:
        return None
    frame = bytes(buffer[: end + 1])
    del buffer[: end + 1]
    return frame


def _require_mido_port_name(value: object, *, direction: str) -> str:
    if not isinstance(value, str) or not value:
        raise RealMidiPortError(f"midi_{direction}_port_required")
    return value


def _require_7bit(value: object, *, field: str) -> int:
    """Coerce one wire field to a 7-bit int, or refuse (fail closed)."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise RealMidiSendError(f"midi_wire_field_not_int: {field}")
    if not 0 <= value <= 127:
        raise RealMidiSendError(f"midi_wire_field_out_of_range: {field}")
    return value


def _require_channel(value: object) -> int:
    """Coerce a MIDI channel to ``0..15``, or refuse (fail closed)."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise RealMidiSendError("midi_wire_field_not_int: channel")
    if not 0 <= value <= 15:
        raise RealMidiSendError("midi_wire_field_out_of_range: channel")
    return value


def neutral_cc_fields(message: object) -> tuple[int, int, int]:
    """Normalise one neutral CC message to ``(channel, control, value)``.

    The armed path carries device-neutral messages in exactly two shapes,
    and **neither is acceptable to a real ``mido`` output port**:

    * a ``(channel, control, value)`` triple — what
      :meth:`rytm_randomizer.devices.Device.to_cc_messages` renders, and
      what the ArmedApply seam iterates;
    * a :class:`~rytm_randomizer.mock_midi.MidiMessage` — the inert
      dataclass the cockpit adapters build via ``build_cc_message``.

    Both are normalised here, at the lazy real-MIDI boundary, so the
    conversion to :class:`mido.Message` happens in exactly one place
    (:class:`WireOutputPort`). Anything else fails closed with
    :exc:`~rytm_randomizer.real_midi_adapter.RealMidiSendError`.
    """

    if isinstance(message, tuple):
        fields = cast(tuple[object, ...], message)
        if len(fields) != 3:
            raise RealMidiSendError("midi_wire_triple_arity")
        return (
            _require_channel(fields[0]),
            _require_7bit(fields[1], field="control"),
            _require_7bit(fields[2], field="value"),
        )

    message_type = getattr(message, "message_type", None)
    if message_type is None:
        raise RealMidiSendError(f"midi_wire_unsupported_message: {type(message).__name__}")
    if message_type not in ("cc", "control_change"):
        raise RealMidiSendError(f"midi_wire_unsupported_message_type: {message_type!s}")
    return (
        _require_channel(getattr(message, "channel", None)),
        _require_7bit(getattr(message, "control", None), field="control"),
        _require_7bit(getattr(message, "value", None), field="value"),
    )


class WireOutputPort:
    """The one place a neutral message becomes a real ``mido.Message``.

    A real ``mido`` output port rejects anything that is not a
    :class:`mido.Message`; the armed path upstream deliberately speaks in
    device-neutral triples / inert :class:`~rytm_randomizer.mock_midi.MidiMessage`
    dataclasses so no engine, runner, or cockpit adapter has to know about
    ``mido``. This wrapper closes that gap at the lazy real-MIDI boundary —
    the same shape :func:`rytm_randomizer.midi_io.send_cc` already uses for
    its real branch (build ``mido.Message`` immediately before ``send``).

    Wrapping (rather than converting at each call site) means the armed
    seam holds a port that *is* the conversion, so a future message kind
    cannot silently bypass it.
    """

    def __init__(self, port: RealMidiOutputPort, mido_module: _MidoModule) -> None:
        """Capture the opened backend port plus the already-imported ``mido``."""

        self._port = port
        self._mido = mido_module

    @property
    def name(self) -> str | None:
        """The backend port's own name, when it exposes one."""

        name = getattr(self._port, "name", None)
        return None if name is None else str(name)

    def send(self, message: object) -> None:
        """Convert ``message`` to a ``mido.Message`` and transmit it."""

        channel, control, value = neutral_cc_fields(message)
        wire_message = self._mido.Message(
            "control_change",
            channel=channel,
            control=control,
            value=value,
        )
        self._port.send(wire_message)

    def close(self) -> None:
        """Close the wrapped backend port."""

        self._port.close()


class MidoMidiPortProvider:
    """Real MIDI port provider backed by ``mido``.

    Implements the neutral ``RealMidiOutputProvider`` protocol and app-owned
    input capture methods. ``mido`` is imported lazily inside these methods
    only, after the armed app path has completed its feature-specific guards.
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

        The returned port is a :class:`WireOutputPort` wrapper, not the raw
        backend port: every armed caller upstream speaks in device-neutral
        triples / inert ``MidiMessage`` dataclasses, and a real ``mido`` port
        accepts only :class:`mido.Message`. The wrapper performs that
        conversion here, at the single lazy real-MIDI boundary, so no caller
        can hand a real port an object it rejects.

        Wrapped in an :func:`~rytm_randomizer.observability.tracing.operation`
        span so a ``--debug`` log records when the backend opened the selected
        port and how long it took, without persisting the machine-local port
        name. The ``RealMidiPortError`` paths bubble out through the span and
        are captured by tracing as an ``operation_error`` log line.
        """

        checked_port_name = _require_mido_port_name(port_name, direction="output")

        with operation("open_output"):
            mido = _import_mido()
            available = self.list_output_names()
            if checked_port_name not in available:
                raise RealMidiPortError(f"unknown_midi_output_port: {checked_port_name}")
            # Same backend-family catch as ``list_output_names``: every realistic
            # mido backend can fail to open a port with one of these errors. We
            # convert to a single ``RealMidiPortError`` at the boundary.
            try:
                port = mido.open_output(checked_port_name)
            except (
                OSError,
                RuntimeError,
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - backend specific
                raise RealMidiPortError(
                    f"unavailable_midi_output_port: {checked_port_name}",
                    context={"underlying": repr(exc)},
                ) from exc
            if not callable(getattr(port, "send", None)) or not callable(
                getattr(port, "close", None)
            ):
                _close_rejected_port(port, direction="output")
                raise RealMidiPortError(f"invalid_midi_output_port: {checked_port_name}")
            return WireOutputPort(port, mido)

    def open_input(self, port_name: str) -> RealMidiInputPort:
        """Open a hardware MIDI input port by name (lazy ``mido``)."""

        checked_port_name = _require_mido_port_name(port_name, direction="input")

        with operation("open_input"):
            mido = _import_mido()
            available = self.list_input_names()
            if checked_port_name not in available:
                raise RealMidiPortError(f"unknown_midi_input_port: {checked_port_name}")
            try:
                port = mido.open_input(checked_port_name)
            except (
                OSError,
                RuntimeError,
                ImportError,
                AttributeError,
            ) as exc:  # pragma: no cover - backend specific
                raise RealMidiPortError(
                    f"unavailable_midi_input_port: {checked_port_name}",
                    context={"underlying": repr(exc)},
                ) from exc
            if not callable(getattr(port, "iter_pending", None)) or not callable(
                getattr(port, "close", None)
            ):
                _close_rejected_port(port, direction="input")
                raise RealMidiPortError(f"invalid_midi_input_port: {checked_port_name}")
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

        checked_port_name = _require_mido_port_name(port_name, direction="input")
        if timeout_seconds <= 0:
            raise RealMidiPortError("midi_sysex_capture_timeout_seconds_required")

        with operation("capture_sysex_messages"):
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

            if checked_port_name not in available:
                close_port = getattr(midi_in, "close_port", None)
                if callable(close_port):
                    close_port()
                raise RealMidiPortError(f"unknown_midi_input_port: {checked_port_name}")

            try:
                midi_in.ignore_types(sysex=False, timing=True, active_sense=True)
                midi_in.open_port(available.index(checked_port_name))
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
                    f"unavailable_midi_input_port: {checked_port_name}",
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
