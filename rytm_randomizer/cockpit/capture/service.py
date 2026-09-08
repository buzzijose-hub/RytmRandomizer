"""Shared, input-only current-kit capture for Analog Rytm and Analog Four.

The service owns no MIDI backend. An explicitly armed ``app.py`` composition
injects a :class:`SysexCaptureProvider`; the ordinary Cockpit sidecar uses
``KitCaptureService.disabled()`` and therefore cannot enumerate or open ports.

Every received frame is validated by the canonical device-specific
``ElektronKitCodec`` before it reaches the registered device's existing
``SnapshotDecoder`` strategy. No SysEx request is sent, no output port is
opened, and the frame is not written to disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Final, Literal, Protocol, TypedDict

from ...data import RYTM_MACHINE_PROFILES
from ...devices import (
    AnalogFourKitSnapshot,
    RegisteredSavedKitCaptureCapability,
    RytmKitSnapshot,
    analog_four_snapshot_payload_fingerprint,
    resolve_saved_kit_capture_capability,
    rytm_snapshot_payload_fingerprint,
)
from ...observability.errors import RytmRandomizerError, StateError
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from ...observability.tracing import operation
from ..data.stage import StageDeviceId
from ..stage.policy import (
    A4_LANE_POLICY,
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
)

CAPTURE_TIMEOUT_SECONDS: Final[float] = 120.0

KitCaptureDeviceId = StageDeviceId
KitParameterReadiness = Literal[
    "rytm_anchor_ready",
    "filter1_frequency_offline_ready",
    "exact_kit_anchor_offsets_candidate",
]
KitCaptureLayoutStatus = Literal["mutation_ready", "captured_mapping_pending"]
KitCaptureRefusalReason = Literal[
    "capture_busy",
    "capture_not_armed",
    "frame_count_invalid",
    "frame_validation_failed",
    "input_port_required",
    "receive_failed",
    "timeout_invalid",
    "unsupported_device",
]
KitCaptureSnapshot = RytmKitSnapshot | AnalogFourKitSnapshot
CAPTURE_DEVICE_IDS: Final[tuple[KitCaptureDeviceId, ...]] = (
    ANALOG_RYTM_DEVICE_ID,
    ANALOG_FOUR_DEVICE_ID,
)
_logger = get_logger(__name__)
_CAPTURE_REFUSED_ERROR_KIND: Final[str] = "cockpit_capture_refused"


def _record_capture_refusal(
    reason: KitCaptureRefusalReason,
    *,
    device_id: str,
    exception_type: str | None = None,
) -> None:
    """Emit one bounded refusal signal without exposing a MIDI port name."""

    context: dict[str, object] = {
        "device_id": device_id if device_id in CAPTURE_DEVICE_IDS else "unsupported",
        "exception_type": exception_type,
        "input_only": True,
        "reason": reason,
        "sent_midi": False,
    }
    _logger.warning("cockpit_capture_refused", extra=context)
    get_metrics().record_error(_CAPTURE_REFUSED_ERROR_KIND)


class SysexCaptureProvider(Protocol):
    """Injected real-MIDI input surface; implementations remain outside Cockpit."""

    def list_input_names(self) -> tuple[str, ...]:
        """Return currently available MIDI input names."""

        ...

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        """Receive complete framed SysEx messages from one input port."""

        ...


KitCaptureUnavailable = StateError
"""Compatibility name for capture-state failures in the shared taxonomy."""


class KitCaptureResultDict(TypedDict):
    """JSON-ready capture result mirrored by the TypeScript wire contract."""

    device_id: KitCaptureDeviceId
    kit_name: str
    slot: int | None
    fingerprint: str
    frame_bytes: int
    captured_at: str
    snapshot_layout: str
    parameter_readiness: KitParameterReadiness
    round_trip_verified: bool
    input_only: bool
    sent_midi: bool
    layout_items: list[KitCaptureLayoutItemDict]


class KitCaptureLayoutItemDict(TypedDict):
    """One machine-specific track/pad row shown after capture."""

    index: int
    label: str
    status: KitCaptureLayoutStatus
    detail: str


@dataclass(frozen=True)
class KitCaptureLayoutItem:
    """Decoded Rytm pad or exact-but-not-yet-mapped A4 track row."""

    index: int
    label: str
    status: KitCaptureLayoutStatus
    detail: str

    def to_dict(self) -> KitCaptureLayoutItemDict:
        return {
            "index": self.index,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class KitCaptureResult:
    """Verified in-memory anchor for one received saved-kit frame.

    ``snapshot`` retains the decoded exact payload for mutation bridges and
    ``frame`` retains the exact, already verified framed SysEx bytes for an
    explicit operator keep/export action. Both are deliberately omitted from
    :meth:`to_dict`, so raw kit bytes never cross the WebSocket or get written
    to disk implicitly.
    """

    device_id: KitCaptureDeviceId
    kit_name: str
    slot: int | None
    fingerprint: str
    frame_bytes: int
    captured_at: datetime
    snapshot_layout: str
    parameter_readiness: KitParameterReadiness
    snapshot: KitCaptureSnapshot = field(repr=False, compare=False)
    frame: bytes = field(repr=False, compare=False)
    round_trip_verified: bool = True
    input_only: bool = True
    sent_midi: bool = False
    layout_items: tuple[KitCaptureLayoutItem, ...] = ()

    def to_dict(self) -> KitCaptureResultDict:
        """Return the stable WebSocket payload shape."""

        return {
            "device_id": self.device_id,
            "kit_name": self.kit_name,
            "slot": self.slot,
            "fingerprint": self.fingerprint,
            "frame_bytes": self.frame_bytes,
            "captured_at": self.captured_at.isoformat(),
            "snapshot_layout": self.snapshot_layout,
            "parameter_readiness": self.parameter_readiness,
            "round_trip_verified": self.round_trip_verified,
            "input_only": self.input_only,
            "sent_midi": self.sent_midi,
            "layout_items": [item.to_dict() for item in self.layout_items],
        }


def narrow_kit_capture_device_id(value: object) -> KitCaptureDeviceId:
    """Validate and narrow an untrusted wire value to a supported device id."""

    if value in CAPTURE_DEVICE_IDS:
        return value
    raise ValueError("capture device_id must be analog_rytm_mk2 or analog_four_mk2")


def _decode_capture_result(
    device_id: KitCaptureDeviceId,
    registered: RegisteredSavedKitCaptureCapability,
    frame: bytes,
) -> KitCaptureResult:
    decoded_frame = registered.capability.decode_saved_kit_capture(frame)
    if registered.capability.encode_saved_kit_capture(decoded_frame) != frame:
        raise ValueError("captured KIT frame is not decode/encode stable")

    device = registered.device
    snapshot = device.snapshot_decoder.decode(
        decoded_frame.payload,
        slot=decoded_frame.snapshot_slot,
    )
    captured_at = datetime.now(timezone.utc)

    if device_id == ANALOG_RYTM_DEVICE_ID and isinstance(snapshot, RytmKitSnapshot):
        profiles_by_value = {profile.machine_value: profile for profile in RYTM_MACHINE_PROFILES}
        layout_items = tuple(
            KitCaptureLayoutItem(
                index=pad,
                label=(
                    profiles_by_value[fact.raw_machine_value & 0x7F].label
                    if (fact.raw_machine_value & 0x7F) in profiles_by_value
                    else f"Machine {fact.raw_machine_value & 0x7F}"
                ),
                status="mutation_ready" if fact.promoted else "captured_mapping_pending",
                detail=fact.reason,
            )
            for pad, fact in sorted(snapshot.machine_facts.facts_by_pad.items())
        )
        return KitCaptureResult(
            device_id=ANALOG_RYTM_DEVICE_ID,
            kit_name=snapshot.kit_name,
            slot=snapshot.slot,
            fingerprint=rytm_snapshot_payload_fingerprint(snapshot),
            frame_bytes=len(frame),
            captured_at=captured_at,
            snapshot_layout="saved_kit",
            parameter_readiness="rytm_anchor_ready",
            snapshot=snapshot,
            frame=bytes(frame),
            layout_items=layout_items,
        )
    if device_id == ANALOG_FOUR_DEVICE_ID and isinstance(snapshot, AnalogFourKitSnapshot):
        layout_items = tuple(
            KitCaptureLayoutItem(
                index=index,
                label=f"T{index}",
                status="mutation_ready",
                detail=(
                    "Filter 1 Frequency is verified for offline captured-kit "
                    "mutation; every other parameter remains mapping-blocked"
                ),
            )
            for index in sorted(A4_LANE_POLICY.available_ids)
        )
        return KitCaptureResult(
            device_id=ANALOG_FOUR_DEVICE_ID,
            kit_name=snapshot.kit_name,
            slot=None,
            fingerprint=analog_four_snapshot_payload_fingerprint(snapshot),
            frame_bytes=len(frame),
            captured_at=captured_at,
            snapshot_layout=snapshot.snapshot_layout,
            parameter_readiness="filter1_frequency_offline_ready",
            snapshot=snapshot,
            frame=bytes(frame),
            layout_items=layout_items,
        )
    raise TypeError("registered capture decoder returned an unsupported snapshot type")


def decode_kit_capture_frame(device_id: str, frame: bytes) -> KitCaptureResult:
    """Decode one already-received saved-KIT frame without any MIDI I/O.

    Show-pack import and recovery need the same strict codec round trip as a
    live input-only capture, but must not enumerate or open a port.  This
    deliberately small public bridge reuses the registered capture
    capability and returns the ordinary in-memory result; it never persists
    the frame and grants no output authority.
    """

    registered = resolve_saved_kit_capture_capability(device_id)
    narrowed_device_id = narrow_kit_capture_device_id(device_id)
    return _decode_capture_result(narrowed_device_id, registered, frame)


class KitCaptureService:
    """Receive and validate current-kit dumps through an injected input provider."""

    def __init__(self, provider: SysexCaptureProvider | None) -> None:
        self._provider = provider
        self._capture_lock = Lock()

    @classmethod
    def disabled(cls) -> KitCaptureService:
        """Return a passive service that cannot enumerate or open MIDI inputs."""

        return cls(None)

    @property
    def enabled(self) -> bool:
        """Whether an explicitly armed input provider was injected."""

        return self._provider is not None

    def list_input_names(self) -> tuple[str, ...]:
        """List inputs only when capture authority was explicitly injected."""

        if self._provider is None:
            return ()
        with operation("cockpit_list_capture_inputs"):
            names = self._provider.list_input_names()
        _logger.info(
            "cockpit_capture_inputs_listed",
            extra={
                "input_count": len(names),
                "opened_midi_port": False,
                "sent_midi": False,
            },
        )
        return names

    def capture(
        self,
        device_id: str,
        port_name: str,
        *,
        timeout_seconds: float = CAPTURE_TIMEOUT_SECONDS,
    ) -> KitCaptureResult:
        """Receive exactly one complete current-kit frame and decode its anchor."""

        try:
            registered = resolve_saved_kit_capture_capability(device_id)
            narrowed_device_id = narrow_kit_capture_device_id(device_id)
        except (TypeError, ValueError) as exc:
            _record_capture_refusal(
                "unsupported_device",
                device_id=device_id,
                exception_type=type(exc).__name__,
            )
            raise
        if not port_name:
            _record_capture_refusal("input_port_required", device_id=narrowed_device_id)
            raise ValueError("capture input port is required")
        if self._provider is None:
            _record_capture_refusal("capture_not_armed", device_id=narrowed_device_id)
            raise StateError("current-kit capture is not armed")
        if timeout_seconds <= 0:
            _record_capture_refusal("timeout_invalid", device_id=narrowed_device_id)
            raise ValueError("capture timeout must be positive")
        if not self._capture_lock.acquire(blocking=False):
            _record_capture_refusal("capture_busy", device_id=narrowed_device_id)
            raise StateError("another current-kit capture is already active")

        try:
            with operation(
                "cockpit_capture_current_kit",
                device_id=narrowed_device_id,
            ):
                try:
                    frames = self._provider.capture_sysex_messages(
                        port_name,
                        timeout_seconds=timeout_seconds,
                    )
                except (OSError, RuntimeError, TypeError, ValueError) as exc:
                    _record_capture_refusal(
                        "receive_failed",
                        device_id=narrowed_device_id,
                        exception_type=type(exc).__name__,
                    )
                    raise
                if len(frames) != 1:
                    _record_capture_refusal(
                        "frame_count_invalid",
                        device_id=narrowed_device_id,
                    )
                    raise ValueError("current-kit capture requires exactly one KIT SysEx frame")
                try:
                    result = _decode_capture_result(narrowed_device_id, registered, frames[0])
                except (RytmRandomizerError, TypeError, ValueError) as exc:
                    _record_capture_refusal(
                        "frame_validation_failed",
                        device_id=narrowed_device_id,
                        exception_type=type(exc).__name__,
                    )
                    raise
        finally:
            self._capture_lock.release()

        _logger.info(
            "cockpit_current_kit_captured",
            extra={
                "device_id": result.device_id,
                "kit_name": result.kit_name,
                "fingerprint": result.fingerprint,
                "frame_bytes": result.frame_bytes,
                "input_only": True,
                "sent_midi": False,
            },
        )
        return result


__all__ = [
    "ANALOG_FOUR_DEVICE_ID",
    "ANALOG_RYTM_DEVICE_ID",
    "CAPTURE_DEVICE_IDS",
    "CAPTURE_TIMEOUT_SECONDS",
    "KitCaptureDeviceId",
    "KitCaptureLayoutItem",
    "KitCaptureLayoutItemDict",
    "KitCaptureResult",
    "KitCaptureResultDict",
    "KitCaptureService",
    "KitCaptureSnapshot",
    "KitCaptureUnavailable",
    "SysexCaptureProvider",
    "decode_kit_capture_frame",
    "narrow_kit_capture_device_id",
]
