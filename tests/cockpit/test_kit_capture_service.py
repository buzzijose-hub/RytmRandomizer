"""Input-only dual-device current-kit capture service tests."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import nullcontext
from dataclasses import dataclass
from threading import Event

import pytest

from conftest import (
    analog_four_saved_kit_frame,
    elektron_syx_message,
    rytm_real_layout_kit_payload,
)
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    KitCaptureService,
    KitCaptureUnavailable,
    narrow_kit_capture_device_id,
)
from rytm_randomizer.cockpit.capture import service as capture_service
from rytm_randomizer.cockpit.stage.policy import A4_LANE_POLICY
from rytm_randomizer.devices import (
    AnalogFourKitSnapshot,
    RegisteredSavedKitCaptureCapability,
    RytmKitSnapshot,
    SavedKitCaptureFrame,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.observability.metrics import get_metrics

pytestmark = pytest.mark.fast


def _a4_saved_kit_frame(name: bytes = b"A4 WAREHOUSE") -> bytes:
    return analog_four_saved_kit_frame(name=name)


@dataclass
class _CaptureProvider:
    frames: tuple[bytes, ...]
    names: tuple[str, ...] = ("Elektron Input",)

    def __post_init__(self) -> None:
        self.capture_calls: list[tuple[str, float]] = []

    def list_input_names(self) -> tuple[str, ...]:
        return self.names

    def capture_sysex_messages(
        self,
        port_name: str,
        *,
        timeout_seconds: float,
    ) -> tuple[bytes, ...]:
        self.capture_calls.append((port_name, timeout_seconds))
        return self.frames


def test_disabled_capture_service_is_passive_and_never_lists_ports() -> None:
    service = KitCaptureService.disabled()

    assert service.enabled is False
    assert service.list_input_names() == ()
    with pytest.raises(KitCaptureUnavailable, match="capture is not armed"):
        service.capture(ANALOG_RYTM_DEVICE_ID, "Elektron Input")


def test_capture_device_id_narrowing_accepts_both_families_and_rejects_unknown() -> None:
    assert narrow_kit_capture_device_id(ANALOG_RYTM_DEVICE_ID) == ANALOG_RYTM_DEVICE_ID
    assert narrow_kit_capture_device_id(ANALOG_FOUR_DEVICE_ID) == ANALOG_FOUR_DEVICE_ID
    with pytest.raises(ValueError, match="must be analog_rytm_mk2 or analog_four_mk2"):
        narrow_kit_capture_device_id("digitakt")


def test_capture_service_decodes_verified_rytm_current_kit() -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload(b"WAREHOUSE RYTM"))
    provider = _CaptureProvider((frame,))
    service = KitCaptureService(provider)

    result = service.capture(ANALOG_RYTM_DEVICE_ID, "Elektron Input", timeout_seconds=7.5)

    assert result.device_id == ANALOG_RYTM_DEVICE_ID
    assert result.kit_name == "WAREHOUSE RYTM"
    assert result.slot == 0
    assert result.frame_bytes == len(frame)
    assert result.snapshot_layout == "saved_kit"
    assert result.parameter_readiness == "rytm_anchor_ready"
    assert result.round_trip_verified is True
    assert result.sent_midi is False
    assert len(result.layout_items) == 12
    assert result.layout_items[0].label == "BD Hard"
    assert result.layout_items[0].status == "mutation_ready"
    assert isinstance(result.snapshot, RytmKitSnapshot)
    assert result.snapshot.raw == frame[1:-1]
    assert result.frame == frame
    assert "snapshot" not in result.to_dict()
    assert "frame" not in result.to_dict()
    assert len(result.fingerprint) == 16
    assert provider.capture_calls == [("Elektron Input", 7.5)]


def test_enabled_capture_service_lists_inputs_only_on_explicit_call() -> None:
    provider = _CaptureProvider(())
    service = KitCaptureService(provider)

    assert service.enabled is True
    assert service.list_input_names() == ("Elektron Input",)


def test_capture_failure_logs_category_without_input_port_name(
    monkeypatch: pytest.MonkeyPatch,
    isolated_observability: None,
) -> None:
    del isolated_observability
    secret_port_name = "Jose's exact studio input"
    operation_contexts: list[dict[str, object]] = []
    warning_records: list[tuple[str, dict[str, object]]] = []

    class _FailingProvider(_CaptureProvider):
        def capture_sysex_messages(
            self,
            port_name: str,
            *,
            timeout_seconds: float,
        ) -> tuple[bytes, ...]:
            del timeout_seconds
            raise OSError(f"cannot read {port_name}")

    def capture_operation(_name: str, **context: object):
        operation_contexts.append(context)
        return nullcontext("")

    def record_warning(message: str, *, extra: dict[str, object]) -> None:
        warning_records.append((message, extra))

    monkeypatch.setattr(capture_service, "operation", capture_operation)
    monkeypatch.setattr(capture_service._logger, "warning", record_warning)
    service = KitCaptureService(_FailingProvider(()))

    with pytest.raises(OSError, match="cannot read"):
        service.capture(ANALOG_RYTM_DEVICE_ID, secret_port_name)

    assert operation_contexts == [{"device_id": ANALOG_RYTM_DEVICE_ID}]
    assert warning_records == [
        (
            "cockpit_capture_refused",
            {
                "device_id": ANALOG_RYTM_DEVICE_ID,
                "exception_type": "OSError",
                "input_only": True,
                "reason": "receive_failed",
                "sent_midi": False,
            },
        )
    ]
    assert secret_port_name not in repr(operation_contexts)
    assert secret_port_name not in repr(warning_records)
    assert get_metrics().errors_by_kind["cockpit_capture_refused"] == 1


def test_capture_service_decodes_a4_filter1_ready_without_overclaiming_other_fields() -> None:
    frame = _a4_saved_kit_frame()
    provider = _CaptureProvider((frame,))
    service = KitCaptureService(provider)

    result = service.capture(ANALOG_FOUR_DEVICE_ID, "Elektron Input")

    assert result.device_id == ANALOG_FOUR_DEVICE_ID
    assert result.kit_name == "A4 WAREHOUSE"
    assert result.slot is None
    assert result.snapshot_layout == "saved_kit"
    assert result.parameter_readiness == "filter1_frequency_offline_ready"
    assert result.round_trip_verified is True
    assert result.sent_midi is False
    assert isinstance(result.snapshot, AnalogFourKitSnapshot)
    assert result.snapshot.raw == frame[1:-1]
    assert result.frame == frame
    assert "snapshot" not in result.to_dict()
    assert "frame" not in result.to_dict()
    assert [item.label for item in result.layout_items] == ["T1", "T2", "T3", "T4"]
    assert {item.status for item in result.layout_items} == {"mutation_ready"}
    assert all(
        "every other parameter remains mapping-blocked" in item.detail
        for item in result.layout_items
    )


@pytest.mark.parametrize(
    ("device_id", "frame"),
    [
        (ANALOG_RYTM_DEVICE_ID, _a4_saved_kit_frame()),
        (
            ANALOG_FOUR_DEVICE_ID,
            elektron_syx_message(rytm_real_layout_kit_payload(b"WRONG FAMILY")),
        ),
    ],
)
def test_capture_service_rejects_a_valid_frame_for_the_wrong_device(
    device_id: str,
    frame: bytes,
) -> None:
    service = KitCaptureService(_CaptureProvider((frame,)))

    with pytest.raises(ValueError):
        service.capture(device_id, "Elektron Input")


def test_capture_service_requires_exactly_one_complete_frame() -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload())
    service = KitCaptureService(_CaptureProvider((frame, frame)))

    with pytest.raises(ValueError, match="exactly one KIT SysEx frame"):
        service.capture(ANALOG_RYTM_DEVICE_ID, "Elektron Input")


def test_capture_service_rejects_a_checksum_corrupted_frame() -> None:
    corrupted = bytearray(_a4_saved_kit_frame())
    corrupted[-5] ^= 0x01
    service = KitCaptureService(_CaptureProvider((bytes(corrupted),)))

    with pytest.raises(ValueError, match="checksum.*packed payload"):
        service.capture(ANALOG_FOUR_DEVICE_ID, "Elektron Input")


def test_capture_decoder_rejects_a_non_stable_codec_round_trip() -> None:
    class _UnstableCapability:
        def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
            return SavedKitCaptureFrame(
                payload=frame,
                snapshot_slot=0,
                header=b"header",
                unpacked=b"unpacked",
            )

        def encode_saved_kit_capture(self, _decoded: SavedKitCaptureFrame) -> bytes:
            return b"different frame"

    registered = resolve_saved_kit_capture_capability(ANALOG_RYTM_DEVICE_ID)
    unstable = RegisteredSavedKitCaptureCapability(
        device=registered.device,
        capability=_UnstableCapability(),
    )

    with pytest.raises(ValueError, match="not decode/encode stable"):
        capture_service._decode_capture_result(
            ANALOG_RYTM_DEVICE_ID,
            unstable,
            b"captured frame",
        )


def test_capture_decoder_rejects_an_unexpected_registered_snapshot(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    frame = elektron_syx_message(rytm_real_layout_kit_payload())

    class _UnexpectedDecoder:
        def decode(self, _raw: bytes, slot: int) -> object:
            del slot
            return object()

    registered = resolve_saved_kit_capture_capability(ANALOG_RYTM_DEVICE_ID)
    monkeypatch.setattr(registered.device, "snapshot_decoder", _UnexpectedDecoder())

    with pytest.raises(TypeError, match="unsupported snapshot type"):
        capture_service._decode_capture_result(
            ANALOG_RYTM_DEVICE_ID,
            registered,
            frame,
        )


def test_a4_capture_layout_cardinality_comes_from_registered_lane_policy() -> None:
    registered = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID)
    service = KitCaptureService(_CaptureProvider((_a4_saved_kit_frame(),)))

    result = service.capture(ANALOG_FOUR_DEVICE_ID, "Elektron Input")

    assert [item.index for item in result.layout_items] == sorted(A4_LANE_POLICY.available_ids)
    assert len(result.layout_items) == registered.device.track_count


def test_capture_service_serializes_rytm_and_a4_receive_windows() -> None:
    entered = Event()
    release = Event()
    frame = elektron_syx_message(rytm_real_layout_kit_payload())

    class _BlockingProvider(_CaptureProvider):
        def capture_sysex_messages(
            self,
            port_name: str,
            *,
            timeout_seconds: float,
        ) -> tuple[bytes, ...]:
            self.capture_calls.append((port_name, timeout_seconds))
            entered.set()
            if not release.wait(timeout=2.0):
                raise RuntimeError("test capture release timed out")
            return self.frames

    service = KitCaptureService(_BlockingProvider((frame,)))
    with ThreadPoolExecutor(max_workers=1) as executor:
        first_capture = executor.submit(
            service.capture,
            ANALOG_RYTM_DEVICE_ID,
            "Elektron Input",
        )
        assert entered.wait(timeout=1.0)
        with pytest.raises(KitCaptureUnavailable, match="already active"):
            service.capture(ANALOG_FOUR_DEVICE_ID, "Elektron Input")
        release.set()
        assert first_capture.result(timeout=2.0).device_id == ANALOG_RYTM_DEVICE_ID


def test_capture_service_rejects_unknown_device_and_empty_port() -> None:
    service = KitCaptureService(_CaptureProvider((_a4_saved_kit_frame(),)))

    with pytest.raises(ValueError, match="unsupported capture device"):
        service.capture("digitakt", "Elektron Input")
    with pytest.raises(ValueError, match="input port is required"):
        service.capture(ANALOG_FOUR_DEVICE_ID, "")
    with pytest.raises(ValueError, match="timeout must be positive"):
        service.capture(ANALOG_FOUR_DEVICE_ID, "Elektron Input", timeout_seconds=0)
