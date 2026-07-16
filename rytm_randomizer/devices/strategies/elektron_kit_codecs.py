"""Verified reference-bound kit envelope codecs for supported Elektron devices."""

from __future__ import annotations

from typing import Final

from ...data.analog_rytm_kit_layout import (
    RYTM_KIT_CHECKSUM_PACKED_START,
    RYTM_KIT_LENGTH_ADJUSTMENT,
    RYTM_KIT_RAW_SIZE,
    RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
    RYTM_SYSEX_PRODUCT_ID,
)
from ...snapshot.envelope import (
    ELEKTRON_MFR_ID,
    ElektronKitCodec,
    ElektronKitEnvelopeSpec,
)
from .analog_four_offset_manifest import (
    A4_FAMILY_BYTE,
    A4_KIT_CHECKSUM_PACKED_START,
    A4_KIT_LENGTH_ADJUSTMENT,
    A4_KIT_OBJECT_BYTE,
    A4_KIT_RAW_SIZE,
    A4_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
)

ANALOG_RYTM_KIT_CODEC: Final[ElektronKitCodec] = ElektronKitCodec(
    ElektronKitEnvelopeSpec(
        label="Analog Rytm MKII saved kit",
        required_header_prefix=ELEKTRON_MFR_ID + bytes([RYTM_SYSEX_PRODUCT_ID]),
        header_size_without_f0=RYTM_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
        unpacked_size=RYTM_KIT_RAW_SIZE,
        checksum_packed_start=RYTM_KIT_CHECKSUM_PACKED_START,
        length_adjustment=RYTM_KIT_LENGTH_ADJUSTMENT,
    )
)

ANALOG_FOUR_KIT_CODEC: Final[ElektronKitCodec] = ElektronKitCodec(
    ElektronKitEnvelopeSpec(
        label="Analog Four MKII saved kit",
        required_header_prefix=ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]),
        header_size_without_f0=A4_KIT_SYSEX_HEADER_SIZE_WITHOUT_F0,
        unpacked_size=A4_KIT_RAW_SIZE,
        checksum_packed_start=A4_KIT_CHECKSUM_PACKED_START,
        length_adjustment=A4_KIT_LENGTH_ADJUSTMENT,
        required_unpacked_prefix=bytes([A4_KIT_OBJECT_BYTE]),
    )
)

__all__ = ["ANALOG_FOUR_KIT_CODEC", "ANALOG_RYTM_KIT_CODEC"]
