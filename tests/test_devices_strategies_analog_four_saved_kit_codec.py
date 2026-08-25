"""Boundary tests for the Analog Four MKII saved-kit codec."""

from __future__ import annotations

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    AnalogFourSavedKitCodecError,
    AnalogFourSavedKitPayload,
)

pytestmark = pytest.mark.fast


def _native_saved_kit_prefix(*, command: int = 0x52) -> bytes:
    from rytm_randomizer.data.analog_four_saved_kit_layout import A4_FAMILY_BYTE
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

    return ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE, 0x00, command, 0x01, 0x01, 0x00])


def _decoded_hardware_payload() -> AnalogFourSavedKitPayload:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    payload = extract_sysex_payloads(analog_four_saved_kit_frame())[0]
    return decode_analog_four_saved_kit_payload(payload, require_trailer=True)


def test_decode_rejects_required_trailer_without_body() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )

    payload = _native_saved_kit_prefix() + bytes(4)

    with pytest.raises(AnalogFourSavedKitCodecError, match="payload is too short"):
        decode_analog_four_saved_kit_payload(payload, require_trailer=True)


def test_decode_rejects_unpacked_body_too_short_for_name() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import Elektron7BitMaskOrder, pack_elektron_7bit

    payload = _native_saved_kit_prefix() + pack_elektron_7bit(
        b"\x00",
        mask_order=Elektron7BitMaskOrder.MSB_FIRST,
    )

    with pytest.raises(AnalogFourSavedKitCodecError, match="too short for kit name"):
        decode_analog_four_saved_kit_payload(payload, require_trailer=False)


def test_decode_rejects_required_trailer_with_wrong_unpacked_size(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.devices.strategies.analog_four_saved_kit_codec as codec
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    payload = extract_sysex_payloads(analog_four_saved_kit_frame())[0]
    monkeypatch.setattr(
        codec,
        "unpack_elektron_7bit",
        lambda _packed, *, mask_order: b"\x00",
    )

    with pytest.raises(AnalogFourSavedKitCodecError, match="unexpected length"):
        decode_analog_four_saved_kit_payload(payload, require_trailer=True)


@pytest.mark.parametrize(
    ("prefix", "message"),
    [
        (b"\x01" + _native_saved_kit_prefix()[1:], "manufacturer"),
        (_native_saved_kit_prefix()[:-1], "unexpected length"),
        (_native_saved_kit_prefix() + b"\x00", "unexpected length"),
        (
            _native_saved_kit_prefix()[:3] + b"\x07" + _native_saved_kit_prefix()[4:],
            "family",
        ),
        (_native_saved_kit_prefix(command=0x51), "not a saved kit"),
    ],
)
def test_encode_rejects_invalid_prefix(prefix: bytes, message: str) -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    with pytest.raises(AnalogFourSavedKitCodecError, match=message):
        encode_analog_four_saved_kit_payload(prefix, _decoded_hardware_payload().unpacked)


def test_encode_rejects_wrong_unpacked_length() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    decoded = _decoded_hardware_payload()

    with pytest.raises(AnalogFourSavedKitCodecError, match="unexpected unpacked length"):
        encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked[:-1])


def test_encode_rejects_wrong_saved_kit_command() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    decoded = _decoded_hardware_payload()
    prefix = decoded.prefix[:5] + b"\x51" + decoded.prefix[6:]

    with pytest.raises(AnalogFourSavedKitCodecError, match="not a saved kit"):
        encode_analog_four_saved_kit_payload(prefix, decoded.unpacked)
