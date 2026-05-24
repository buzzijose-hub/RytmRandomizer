"""``RealMidiDeviceAdapter`` — real-MIDI cockpit adapter.

Wraps the existing :class:`~rytm_randomizer.mido_provider.MidoMidiPortProvider`
+ :mod:`rytm_randomizer.real_midi_adapter` boundary so the cockpit can drive
a live Analog Rytm MK2 over MIDI. Only constructed when the operator passes
``--arm`` (Gate 9 invariant — see ``.claude/rules/architecture.md`` rule 8).

Phase 1 limitations (documented in the constructor docstring and method
docstrings; Phase 1.x will fill these in):

* :meth:`capture_snapshot` returns a placeholder snapshot rather than
  round-tripping a SysEx dump from the device.
* :meth:`commit_kit` raises :exc:`NotImplementedError` — kit-dump SysEx
  writing lands in Phase 1.x.
* :meth:`apply` emits one CC message per changed parameter, but the
  wire-format CC-number lookup is the simple identity-by-position used for
  the cockpit preview; Phase 1.x will route through ``data.profiles`` to
  get the canonical CC numbers per Rytm machine.

``mido`` is imported lazily inside the provider's methods (see
:mod:`rytm_randomizer.mido_provider`); this module never imports it
directly. The architecture test that forbids top-level ``import mido`` in
package code keeps holding.
"""

from __future__ import annotations

import hashlib
import logging
import warnings
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from ...mock_midi import MidiMessage, build_cc_message
from ...real_midi_adapter import RealMidiPortError
from ..data import MutationCandidate, PadState, Snapshot, new_ulid

if TYPE_CHECKING:  # pragma: no cover - typing only
    from ...mido_provider import MidoMidiPortProvider

_logger = logging.getLogger(__name__)

# Minimal Phase-1 CC channel; the real renderer uses
# ``AnalogRytmMessageRenderer.RYTM_DEFAULT_CHANNEL`` (also 0), but the
# cockpit adapter intentionally does not import that strategy yet — Phase
# 1.x will fold that lookup in once snapshots carry profile_keys.
_DEFAULT_MIDI_CHANNEL = 0


class RealMidiDeviceAdapter:
    """Real-MIDI cockpit adapter wrapping an injected ``MidoMidiPortProvider``.

    Satisfies the
    :class:`~rytm_randomizer.cockpit.device.adapter.DeviceAdapter` Protocol
    via duck typing — not by inheritance.

    The provider is injected so tests can pass a fake (per the existing
    ``tests/test_mido_provider.py`` pattern). Hardware port discovery and
    opening happen lazily inside the provider's methods, so constructing
    this adapter does not touch the OS MIDI driver.

    Phase 1 caveats:

    * ``capture_snapshot`` returns a placeholder snapshot — real
      SysEx-driven readback lands in Phase 1.x.
    * ``commit_kit`` raises ``NotImplementedError``.
    * ``apply`` sends CC messages but uses a synthetic CC-number
      assignment (parameter-name hash) rather than the canonical
      ``data.profiles`` map. Phase 1.x folds that in once snapshots
      carry a profile_key per pad.
    """

    def __init__(
        self,
        midi_provider: MidoMidiPortProvider,
        *,
        port_name: str | None = None,
    ) -> None:
        """Build the adapter with an injected provider.

        ``port_name`` is optional in Phase 1; when set, ``apply`` opens
        that port lazily on first call. When ``None``, ``apply`` falls
        back to the first port the provider reports (consistent with the
        ``--arm`` default-pick behaviour in ``app.py``).
        """

        self._provider = midi_provider
        self._port_name = port_name
        # Cached port handle — opened lazily on first apply().
        self._port: object | None = None

    @property
    def is_armed(self) -> bool:
        """Always ``True`` — this adapter is the live-MIDI path."""

        return True

    def capture_snapshot(self) -> Snapshot:
        """Return a placeholder snapshot — real SysEx readback is Phase 1.x.

        .. deprecated:: Phase 1
            Real device capture-via-SysEx is not implemented yet. This
            method returns a minimal placeholder snapshot so the cockpit
            UI can boot in armed mode without crashing; downstream
            ``apply`` calls drive the real wire format from the
            candidate's ``proposed_params`` regardless of capture state.
        """

        warnings.warn(
            "RealMidiDeviceAdapter.capture_snapshot returns a placeholder "
            "in Phase 1; real SysEx-driven readback lands in Phase 1.x.",
            DeprecationWarning,
            stacklevel=2,
        )
        _logger.info("real_midi_capture_snapshot_placeholder")
        return Snapshot(
            snapshot_id=new_ulid(),
            device="analog_rytm_mk2",
            captured_at=datetime.now(tz=timezone.utc),
            pads=(),
            scene_slot=None,
            bpm=None,
        )

    def apply(
        self,
        candidate: MutationCandidate,
        pad_locks: frozenset[int],
    ) -> Snapshot:
        """Send each non-locked pad's proposed params over MIDI as CCs.

        For each :class:`~rytm_randomizer.cockpit.data.PadDelta` whose
        ``pad_id`` is not in ``pad_locks``, this method:

        1. Builds one inert :class:`~rytm_randomizer.mock_midi.MidiMessage`
           per ``(parameter, value)`` pair via :func:`build_cc_message`.
        2. Sends each message through the provider's currently-open port
           (opened lazily on the first call).

        Returns a synthesized post-state snapshot reflecting the applied
        candidate. The synthesized snapshot uses placeholder machine
        names because real-MIDI capture does not yet round-trip the
        existing machine assignments (Phase 1.x).
        """

        port = self._ensure_port_open()

        sent_pad_states: list[PadState] = []
        for delta in candidate.pad_deltas:
            if delta.pad_id in pad_locks:
                continue
            for param_name, value in delta.proposed_params.items():
                control = self._param_to_cc(param_name)
                message = build_cc_message(
                    channel=_DEFAULT_MIDI_CHANNEL,
                    control=control,
                    value=value,
                    metadata={
                        "pad": delta.pad_id,
                        "parameter": param_name,
                        "cockpit_apply": True,
                    },
                )
                self._send(port, message)
            sent_pad_states.append(
                PadState(
                    pad_id=delta.pad_id,
                    machine="unknown",  # Phase 1.x: round-trip from capture.
                    params=dict(delta.proposed_params),
                )
            )

        return Snapshot(
            snapshot_id=new_ulid(),
            device="analog_rytm_mk2",
            captured_at=datetime.now(tz=timezone.utc),
            pads=tuple(sent_pad_states),
            scene_slot=None,
            bpm=None,
        )

    def commit_kit(self, snapshot: Snapshot, label: str | None) -> None:
        """Phase 1: not implemented; kit-dump SysEx writing lands in Phase 1.x.

        Raises:
            NotImplementedError: always, until Phase 1.x.
        """

        _logger.warning(
            "real_midi_commit_kit_not_implemented",
            extra={
                "snapshot_id": snapshot.snapshot_id,
                "label": label,
            },
        )
        raise NotImplementedError("Kit-dump SysEx writing lands in Phase 1.x")

    # ------------------------------------------------------------------
    # Internal helpers — kept private so the adapter surface stays small.
    # ------------------------------------------------------------------

    def _ensure_port_open(self) -> object:
        """Lazily open the configured MIDI output port via the provider.

        ``mido`` is imported only inside the provider's methods, never
        here — this method's only side effect is delegating to the
        provider's ``list_output_names`` / ``open_output``.
        """

        if self._port is not None:
            return self._port

        port_name = self._port_name
        if port_name is None:
            # Fall back to the first available port — same default-pick
            # behavior as ``app.py`` when ``--arm`` is set without an
            # explicit ``--port``.
            names = self._provider.list_output_names()
            if not names:
                raise RealMidiPortError("no_midi_output_ports_available: cannot apply candidate")
            port_name = names[0]

        self._port = self._provider.open_output(port_name)
        return self._port

    def _send(self, port: object, message: MidiMessage) -> None:
        """Forward one ``MidiMessage`` to the provider-opened port.

        Wrapped so tests can introspect the dispatch path. The port is
        expected to expose a ``send`` method (the provider already guards
        this at ``open_output`` time).
        """

        send_callable = getattr(port, "send", None)
        if not callable(send_callable):
            raise RealMidiPortError("midi_port_missing_send_method")
        send_callable(message)

    @staticmethod
    def _param_to_cc(parameter: str) -> int:
        """Phase 1: deterministic synthetic CC slot for a parameter name.

        Phase 1.x will replace this with a lookup into
        ``rytm_randomizer.data.profiles.PROFILES`` once the cockpit's
        snapshots carry a per-pad ``profile_key``. For Phase 1 we hash
        the parameter name (via ``hashlib.sha1`` — explicitly NOT the
        builtin ``hash()`` which is salted per interpreter run) into the
        7-bit CC range so the wire format is deterministic per parameter,
        exactly what the preview path needs.
        """

        # 7-bit CC numbers live in [0, 127]; 0 and 32 are reserved for
        # bank-select pairs in MIDI, so we map into [33, 127] (a 95-wide
        # window). SHA-1 of the name is used for stability across runs.
        digest = hashlib.sha1(parameter.encode("utf-8"), usedforsecurity=False).digest()
        return 33 + (digest[0] % 95)


__all__ = ["RealMidiDeviceAdapter"]
