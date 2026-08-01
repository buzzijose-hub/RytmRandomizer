"""Boundary tests for the Analog Four MKII saved-kit codec."""

from __future__ import annotations

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    AnalogFourSavedKitPayload,
)

pytestmark = pytest.mark.fast


def _decoded_hardware_payload() -> AnalogFourSavedKitPayload:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    payload = extract_sysex_payloads(analog_four_saved_kit_frame())[0]
    return decode_analog_four_saved_kit_payload(payload, require_trailer=True)


def test_decode_rejects_required_trailer_without_body() -> None:
    from rytm_randomizer.data.analog_four_saved_kit_layout import A4_FAMILY_BYTE
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID

    payload = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + bytes(4)

    with pytest.raises(ValueError, match="payload is too short"):
        decode_analog_four_saved_kit_payload(payload, require_trailer=True)


def test_decode_rejects_unpacked_body_too_short_for_name() -> None:
    from rytm_randomizer.data.analog_four_saved_kit_layout import (
        A4_FAMILY_BYTE,
        A4_KIT_OBJECT_BYTE,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import ELEKTRON_MFR_ID, pack_elektron_7bit

    payload = (
        ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + pack_elektron_7bit(bytes([A4_KIT_OBJECT_BYTE]))
    )

    with pytest.raises(ValueError, match="too short for kit name"):
        decode_analog_four_saved_kit_payload(payload, require_trailer=False)


@pytest.mark.parametrize(
    ("prefix", "message"),
    [
        (b"\x01\x20\x3c\x06", "prefix is invalid"),
        (b"\x00\x20\x3c\x06\x00", "prefix is invalid"),
        (b"\x00\x20\x3c\x07", "wrong family"),
    ],
)
def test_encode_rejects_invalid_prefix(prefix: bytes, message: str) -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    with pytest.raises(ValueError, match=message):
        encode_analog_four_saved_kit_payload(prefix, _decoded_hardware_payload().unpacked)


def test_encode_rejects_wrong_unpacked_length() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    decoded = _decoded_hardware_payload()

    with pytest.raises(ValueError, match="unexpected unpacked length"):
        encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked[:-1])


def test_encode_rejects_wrong_saved_kit_object() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        encode_analog_four_saved_kit_payload,
    )

    decoded = _decoded_hardware_payload()
    unpacked = bytes([0x51]) + decoded.unpacked[1:]

    with pytest.raises(ValueError, match="not a saved kit"):
        encode_analog_four_saved_kit_payload(decoded.prefix, unpacked)
