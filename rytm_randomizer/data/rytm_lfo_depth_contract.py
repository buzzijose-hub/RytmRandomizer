"""Rytm OS 1.72 static LFO Depth facts, not transport or hardware authority.

This contract covers logical ID 71 on ordinary Sound tracks only. The current
Sound offset and selected coupled-RAM word are different coordinates. Neither
the coupled projection nor its byte decoder establishes whole-frame ownership.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

from .analog_rytm_kit_layout import RYTM_KIT_TRACK_COUNT, RYTM_SOUND_FIELD_BY_NRPN_LSB
from .analog_rytm_midi import ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER, AnalogRytmCcMapping


@dataclass(frozen=True)
class RytmLfoDepthContract:
    """Fixed facts for this parameter; catalog addresses retain their owner."""

    logical_id: int = 0x47
    physical_slot: int = 8
    track_indices: tuple[int, ...] = tuple(range(RYTM_KIT_TRACK_COUNT))
    native_min: int = 0
    native_max: int = 0x7FFF
    native_center: int = 0x4000
    units_per_whole: int = 128
    decimal_scale: int = 100
    current_sound_offset: int = 0x24
    coupled_word_offset: int = RYTM_SOUND_FIELD_BY_NRPN_LSB[39].sound_offset
    word_size: int = 2
    coarse_shift: int = 8
    fine_shift: int = 1
    high_byte_mask: int = 0xFF00
    cc_value_max: int = 0x7F
    nrpn_value_max: int = 0x3FFF
    channel_max: int = 15
    cc_status: int = 0xB0
    midi_mapping: AnalogRytmCcMapping = ANALOG_RYTM_CC_BY_SECTION_AND_PARAMETER[
        ("LFO", "LFO Depth")
    ]
    scope: str = "LFO Depth only; ordinary Sound tracks 0..11; not FX or a full frame codec"


@dataclass(frozen=True)
class RytmLfoDepthProvenance:
    """Source-firmware identity and bounded evidence, not installed firmware."""

    os_version: str = "1.72"
    main_sha256: str = "5d0b41eed77bb08b08be13ac63c6e8f0bb6a7334195436eb0ec6b5a5f26d6772"
    evidence_kind: Literal["static-only"] = "static-only"
    contract_path: str = "rytm_lfo/contract.json"
    converter_path: str = "rytm_lfo/reference_converter.py"
    vectors_path: str = "rytm_lfo/boundary_vectors.json"
    review_path: str = "working_state/REVIEW_RYTM_LFO.md"
    formatter_invoker_address: int = 0x400F7FEE
    numeric_helper_address: int = 0x40029F2E
    nrpn_value_core_address: int = 0x400A5A9A
    cc_value_core_address: int = 0x400A5CD6
    notifier_address: int = 0x400A60AC
    coupled_copy_address: int = 0x400B9C22
    serialized_index_address: int = 0x400074BA
    limitations: tuple[str, ...] = (
        "Other notification producers were not exhaustively searched.",
        "Descriptor initialization target remains conditional.",
        "No physical validation or installed-firmware identity.",
        "No queue lifetime, coherence, commit, routing or current-source availability proof.",
        "No raw NRPN row parser, full-frame packing, persistence or output authority.",
        "Getter fallback zero does not establish an available current baseline.",
    )
    isa_caveat: str = (
        "ColdFire REMU at 0x40029f78 supplies the remainder; the generic DIVUL label is not authoritative."
    )


RYTM_LFO_DEPTH_CONTRACT: Final[RytmLfoDepthContract] = RytmLfoDepthContract()
RYTM_LFO_DEPTH_PROVENANCE: Final[RytmLfoDepthProvenance] = RytmLfoDepthProvenance()

__all__ = (
    "RYTM_LFO_DEPTH_CONTRACT",
    "RYTM_LFO_DEPTH_PROVENANCE",
    "RytmLfoDepthContract",
    "RytmLfoDepthProvenance",
)
