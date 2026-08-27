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
from ...devices import get_device
from ...devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)
from ...devices.strategies.analog_four_snapshot_decoder import (
    AnalogFourKitSnapshot,
    analog_four_snapshot_payload_fingerprint,
)
from ...devices.strategies.analog_rytm_saved_kit_codec import (
    decode_analog_rytm_saved_kit_frame,
    encode_analog_rytm_saved_kit_frame,
)
from ...devices.strategies.analog_rytm_snapshot_decoder import (
    RytmKitSnapshot,
    rytm_snapshot_payload_fingerprint,
)
from ...observability.errors import StateError
from ...observability.logging import get_logger
from ...observability.tracing import operation

ANALOG_RYTM_DEVICE_ID: Final[Literal["analog_rytm_mk2"]] = "analog_rytm_mk2"
ANALOG_FOUR_DEVICE_ID: Final[Literal["analog_four_mk2"]] = "analog_four_mk2"
CAPTURE_TIMEOUT_SECONDS: Final[float] = 120.0

KitCaptureDeviceId = Literal["analog_rytm_mk2", "analog_four_mk2"]
KitParameterReadiness = Literal[
    "rytm_anchor_ready",
    "exact_kit_anchor_offsets_candidate",
]
KitCaptureLayoutStatus = Literal["mutation_ready", "captured_mapping_pending"]
KitCaptureSnapshot = RytmKitSnapshot | AnalogFourKitSnapshot
CAPTURE_DEVICE_IDS: Final[tuple[KitCaptureDeviceId, ...]] = (
    ANALOG_RYTM_DEVICE_ID,
    ANALOG_FOUR_DEVICE_ID,
)
_ANALOG_FOUR_TRACK_LABELS: Final[tuple[str, ...]] = ("T1", "T2", "T3", "T4")

_logger = get_logger(__name__)


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

    ``snapshot`` retains the decoded exact payload for the upcoming
    mutation bridge. It is deliberately omitted from :meth:`to_dict`, so raw
    kit bytes never cross the WebSocket or get written to disk implicitly.
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


@dataclass(frozen=True)
class _CaptureDeviceSpec:
    device_id: KitCaptureDeviceId
    codec: _CaptureFrameCodec


@dataclass(frozen=True)
class _DecodedCaptureFrame:
    payload: bytes
    slot: int
    header: bytes
    unpacked: bytes


class _CaptureFrameCodec(Protocol):
    def decode_frame(self, frame: bytes) -> object:
        """Decode and validate one complete family-specific frame."""

        ...

    def encode_frame(self, decoded: object) -> bytes:
        """Re-encode the decoded frame for an exact stability check."""

        ...


class _AnalogRytmCaptureFrameCodec:
    def decode_frame(self, frame: bytes) -> object:
        decoded = decode_analog_rytm_saved_kit_frame(frame)
        return _DecodedCaptureFrame(
            payload=frame[1:-1],
            slot=decoded.header[-1],
            header=decoded.header,
            unpacked=decoded.unpacked,
        )

    def encode_frame(self, decoded: object) -> bytes:
        if not isinstance(decoded, _DecodedCaptureFrame):
            raise TypeError("Rytm capture codec received an unsupported decoded frame")
        return encode_analog_rytm_saved_kit_frame(decoded.header, decoded.unpacked)


class _AnalogFourCaptureFrameCodec:
    def decode_frame(self, frame: bytes) -> object:
        if len(frame) < 2 or frame[0] != 0xF0 or frame[-1] != 0xF7:
            raise ValueError("Analog Four saved-kit SysEx framing is invalid")
        decoded = decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True)
        return _DecodedCaptureFrame(
            payload=frame[1:-1],
            slot=0,
            header=decoded.prefix,
            unpacked=decoded.unpacked,
        )

    def encode_frame(self, decoded: object) -> bytes:
        if not isinstance(decoded, _DecodedCaptureFrame):
            raise TypeError("A4 capture codec received an unsupported decoded frame")
        encoded = encode_analog_four_saved_kit_payload(decoded.header, decoded.unpacked)
        return bytes((0xF0,)) + encoded.payload + bytes((0xF7,))


_CAPTURE_DEVICE_SPECS: Final[tuple[_CaptureDeviceSpec, ...]] = (
    _CaptureDeviceSpec(ANALOG_RYTM_DEVICE_ID, _AnalogRytmCaptureFrameCodec()),
    _CaptureDeviceSpec(ANALOG_FOUR_DEVICE_ID, _AnalogFourCaptureFrameCodec()),
)


def _capture_device_spec(device_id: str) -> _CaptureDeviceSpec:
    for spec in _CAPTURE_DEVICE_SPECS:
        if spec.device_id == device_id:
            return spec
    raise ValueError(f"unsupported capture device: {device_id}")


def narrow_kit_capture_device_id(value: object) -> KitCaptureDeviceId:
    """Validate and narrow an untrusted wire value to a supported device id."""

    if value in CAPTURE_DEVICE_IDS:
        return value
    raise ValueError("capture device_id must be analog_rytm_mk2 or analog_four_mk2")


def _decode_capture_result(
    spec: _CaptureDeviceSpec,
    frame: bytes,
) -> KitCaptureResult:
    decoded_frame = spec.codec.decode_frame(frame)
    if spec.codec.encode_frame(decoded_frame) != frame:
        raise ValueError("captured KIT frame is not decode/encode stable")
    if not isinstance(decoded_frame, _DecodedCaptureFrame):
        raise TypeError("capture codec returned an unsupported decoded frame")

    device = get_device(spec.device_id)
    snapshot = device.snapshot_decoder.decode(decoded_frame.payload, slot=decoded_frame.slot)
    captured_at = datetime.now(timezone.utc)

    if isinstance(snapshot, RytmKitSnapshot):
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
            layout_items=layout_items,
        )
    if isinstance(snapshot, AnalogFourKitSnapshot):
        layout_items = tuple(
            KitCaptureLayoutItem(
                index=index,
                label=track_code,
                status="captured_mapping_pending",
                detail="Exact saved-kit bytes captured; semantic parameter offsets pending mapping",
            )
            for index, track_code in enumerate(_ANALOG_FOUR_TRACK_LABELS, start=1)
        )
        return KitCaptureResult(
            device_id=ANALOG_FOUR_DEVICE_ID,
            kit_name=snapshot.kit_name,
            slot=None,
            fingerprint=analog_four_snapshot_payload_fingerprint(snapshot),
            frame_bytes=len(frame),
            captured_at=captured_at,
            snapshot_layout=snapshot.snapshot_layout,
            parameter_readiness="exact_kit_anchor_offsets_candidate",
            snapshot=snapshot,
            layout_items=layout_items,
        )
    raise TypeError("registered capture decoder returned an unsupported snapshot type")


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

        spec = _capture_device_spec(device_id)
        if not port_name:
            raise ValueError("capture input port is required")
        if self._provider is None:
            raise StateError("current-kit capture is not armed")
        if timeout_seconds <= 0:
            raise ValueError("capture timeout must be positive")
        if not self._capture_lock.acquire(blocking=False):
            raise StateError("another current-kit capture is already active")

        try:
            with operation(
                "cockpit_capture_current_kit",
                device_id=spec.device_id,
                port_name=port_name,
            ):
                frames = self._provider.capture_sysex_messages(
                    port_name,
                    timeout_seconds=timeout_seconds,
                )
                if len(frames) != 1:
                    raise ValueError("current-kit capture requires exactly one KIT SysEx frame")
                result = _decode_capture_result(spec, frames[0])
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
    "narrow_kit_capture_device_id",
]
