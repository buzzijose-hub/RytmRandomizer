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

from typing import TYPE_CHECKING

from .real_midi_adapter import RealMidiDependencyError, RealMidiPortError

if TYPE_CHECKING:  # pragma: no cover - typing only, never imported at runtime
    from .real_midi_adapter import RealMidiOutputPort

__all__ = ["MidoMidiPortProvider", "build_mido_midi_port_provider"]


def _import_mido():
    """Lazily import ``mido``; raise a guarded error if it is unavailable."""

    try:
        import mido  # noqa: PLC0415 - intentional lazy import for import-safety
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise RealMidiDependencyError(
            "mido_not_installed: install 'mido' and a backend "
            "(e.g. python-rtmidi) to open real MIDI ports"
        ) from exc
    return mido


class MidoMidiPortProvider:
    """Real MIDI port provider backed by ``mido``.

    Duck-types :class:`rytm_randomizer.real_midi_adapter.RealMidiPortProvider`:
    it exposes ``list_output_names`` and ``open_output`` so it can be passed to
    ``RealMidiSender``. ``mido`` is imported lazily inside these methods only.
    """

    def list_output_names(self) -> tuple[str, ...]:
        """Return available hardware MIDI output port names (lazy ``mido``)."""

        mido = _import_mido()
        try:
            names = mido.get_output_names()
        except Exception as exc:  # pragma: no cover - backend specific
            raise RealMidiPortError(f"midi_output_discovery_failed: {exc}") from exc
        return tuple(names)

    def open_output(self, port_name: str) -> "RealMidiOutputPort":
        """Open a hardware MIDI output port by name (lazy ``mido``)."""

        if not isinstance(port_name, str) or not port_name:
            raise RealMidiPortError("midi_output_port_required")

        mido = _import_mido()
        available = self.list_output_names()
        if port_name not in available:
            raise RealMidiPortError(f"unknown_midi_output_port: {port_name}")
        try:
            port = mido.open_output(port_name)
        except Exception as exc:  # pragma: no cover - backend specific
            raise RealMidiPortError(
                f"unavailable_midi_output_port: {port_name}"
            ) from exc
        if not callable(getattr(port, "send", None)):
            raise RealMidiPortError(f"invalid_midi_output_port: {port_name}")
        return port


def build_mido_midi_port_provider() -> MidoMidiPortProvider:
    """Build the concrete ``mido``-backed provider (no hardware touched yet)."""

    return MidoMidiPortProvider()
