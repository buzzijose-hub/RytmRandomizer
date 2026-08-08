"""AL16 bank identity and positively mapped Rytm writer facts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias, TypedDict

RytmValueConverter: TypeAlias = Literal[
    "verified_7bit",
    "centered_7bit",
    "filter_type_enum",
]
Al16TrackMode: TypeAlias = Literal["preserve", "patch"]
Al16RytmEvidenceClass: TypeAlias = Literal[
    "destination_slot",
    "machine_selection",
    "machine_source",
    "amp_volume",
    "machine_tuning",
]

RYTM_CONVERTER_VERIFIED_7BIT: Final[RytmValueConverter] = "verified_7bit"
RYTM_CONVERTER_CENTERED_7BIT: Final[RytmValueConverter] = "centered_7bit"
RYTM_CONVERTER_FILTER_TYPE_ENUM: Final[RytmValueConverter] = "filter_type_enum"
AL16_TRACK_MODE_PRESERVE: Final[Al16TrackMode] = "preserve"
AL16_TRACK_MODE_PATCH: Final[Al16TrackMode] = "patch"
AL16_BANK_SCHEMA_VERSION: Final[int] = 1
AL16_PROJECT_ID: Final[str] = "AL16"
AL16_PERFORMANCE_CONTEXT_BPM: Final[int] = 138
AL16_BANK_CONCEPT: Final[str] = (
    "One machine moving through sixteen operating states; original Reference to "
    "Discovery material, not a forensic recreation."
)
AL16_ADJACENT_SONIC_DNA_TARGET_PERCENT: Final[tuple[int, int]] = (70, 85)


@dataclass(frozen=True)
class Al16BankState:
    """One reserved operating state in the AL16 performance bank."""

    number: int
    name: str
    tonal_zone: str


class Al16BankStatePayload(TypedDict):
    """Serializable form of one reserved AL16 operating state."""

    number: int
    name: str
    tonal_zone: str


class Al16BankSpecPayload(TypedDict):
    """Typed serializable form of the canonical AL16 bank reservation."""

    schema_version: int
    project_id: str
    performance_context_bpm: int
    concept: str
    adjacent_sonic_dna_target_percent: list[int]
    states: list[Al16BankStatePayload]
    permanent_pad_roles: dict[str, str]


@dataclass(frozen=True)
class RytmWritableField:
    """One saved-kit field supported by positive layout evidence."""

    nrpn_lsb: int
    converter: RytmValueConverter


@dataclass(frozen=True)
class Al16RytmEvidenceGroup:
    """Canonical operator-session metadata for one R2 evidence class."""

    evidence_class: Al16RytmEvidenceClass
    session_number: int
    session_label: str
    expected_evidence: str


AL16_BANK_STATES: Final[tuple[Al16BankState, ...]] = (
    Al16BankState(1, "AIRLOCK", "F Phrygian"),
    Al16BankState(2, "LOCK", "F Phrygian"),
    Al16BankState(3, "ROTATION", "F Phrygian"),
    Al16BankState(4, "PRESSURE", "F Phrygian"),
    Al16BankState(5, "ORBIT", "F# Dorian"),
    Al16BankState(6, "OFFSET", "F# Dorian"),
    Al16BankState(7, "SURGE", "F# Dorian"),
    Al16BankState(8, "CROSSING", "F# Dorian into harmonic-minor tension"),
    Al16BankState(9, "COMPRESSION", "F# harmonic minor"),
    Al16BankState(10, "RITUAL", "F# harmonic minor"),
    Al16BankState(11, "APEX", "F# harmonic minor"),
    Al16BankState(12, "VACUUM", "reduced-pitch F# corridor"),
    Al16BankState(13, "REENTRY", "A minor"),
    Al16BankState(14, "TERMINAL", "A minor"),
    Al16BankState(15, "FRACTURE", "A minor with borrowed Bb/Eb friction"),
    Al16BankState(16, "SHUTDOWN", "ambiguous A-centered ending"),
)

AL16_PAD_ROLES: Final[Mapping[int, str]] = MappingProxyType(
    {
        1: "Main kick",
        2: "Secondary impact / restrained snare",
        3: "Rim / synth percussion / dry punctuation",
        4: "Clap / impulse / noise / transition utility",
        5: "Bass tom / primary tuned low body",
        6: "Low tom / secondary tuned body",
        7: "Mid tom / rotating tonal percussion",
        8: "High tom / transition accent",
        9: "Closed-hat clock",
        10: "Open hat / air",
        11: "Cymbal / ride / upper pressure",
        12: "Cowbell / metallic punctuation / alarm tone",
    }
)

AL16_RYTM_MAPPING_GAP_PATHS: Final[tuple[str, ...]] = (
    "destination_slot",
    "tracks.1.machine",
    "tracks.1.source.dec",
    "tracks.1.source.hld",
    "tracks.1.source.swd",
    "tracks.1.source.swt",
    "tracks.1.source.trn",
    "tracks.1.source.tun",
    "tracks.1.source.wav",
    "tracks.1.amp.vol",
    "tracks.3.machine",
    "tracks.3.amp.vol",
    "tracks.6.source.decay",
    "tracks.6.source.target_note",
    "tracks.6.amp.vol",
    "tracks.9.machine",
    "tracks.9.source.decay",
    "tracks.9.amp.vol",
)

AL16_RYTM_EVIDENCE_GROUPS: Final[tuple[Al16RytmEvidenceGroup, ...]] = (
    Al16RytmEvidenceGroup(
        "machine_selection",
        1,
        "configured AL02 saved-kit capture",
        "One initialized/configured saved-kit comparison showing machine bytes.",
    ),
    Al16RytmEvidenceGroup(
        "machine_source",
        1,
        "configured AL02 saved-kit capture",
        "One initialized/configured saved-kit comparison showing source-field bytes.",
    ),
    Al16RytmEvidenceGroup(
        "amp_volume",
        1,
        "configured AL02 saved-kit capture",
        "One initialized/configured saved-kit comparison showing amp-volume bytes.",
    ),
    Al16RytmEvidenceGroup(
        "machine_tuning",
        1,
        "configured AL02 saved-kit capture",
        "One XT Classic F2 display/raw observation in the configured saved kit.",
    ),
    Al16RytmEvidenceGroup(
        "destination_slot",
        2,
        "destination-slot scratch proof",
        "One user-selected scratch-slot import and dump-back header comparison.",
    ),
)

AL16_RYTM_WRITABLE_FIELDS: Final[Mapping[str, RytmWritableField]] = MappingProxyType(
    {
        "filter.atk": RytmWritableField(16, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.dec": RytmWritableField(17, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.sus": RytmWritableField(18, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.rel": RytmWritableField(19, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.frq": RytmWritableField(20, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.res": RytmWritableField(21, RYTM_CONVERTER_VERIFIED_7BIT),
        "filter.type": RytmWritableField(22, RYTM_CONVERTER_FILTER_TYPE_ENUM),
        "filter.env": RytmWritableField(23, RYTM_CONVERTER_CENTERED_7BIT),
        "amp.atk": RytmWritableField(24, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.hld": RytmWritableField(25, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.dec": RytmWritableField(26, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.ovr": RytmWritableField(27, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.del": RytmWritableField(28, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.rev": RytmWritableField(29, RYTM_CONVERTER_VERIFIED_7BIT),
        "amp.pan": RytmWritableField(30, RYTM_CONVERTER_CENTERED_7BIT),
    }
)

AL16_RYTM_FILTER_TYPES: Final[Mapping[str, int]] = MappingProxyType(
    {"LP2": 0, "LP1": 1, "BP": 2, "PK": 3, "HP2": 4, "HP1": 5, "BS": 6}
)

# Intentionally empty until a machine-specific hardware calibration is approved.
AL16_RYTM_APPROVED_TUNING: Final[Mapping[tuple[str, str], int]] = MappingProxyType({})

AL16_PRESERVED_GLOBAL_SECTIONS: Final[tuple[str, ...]] = (
    "scenes",
    "performance_macros",
    "master_delay",
    "master_reverb",
    "master_distortion",
    "master_compressor",
    "routing",
    "retrig_configuration",
    "choke_configuration",
    "unknown_and_reserved_bytes",
)


def al16_bank_spec_payload() -> Al16BankSpecPayload:
    """Return the canonical serializable AL16 bank reservation."""

    return {
        "schema_version": AL16_BANK_SCHEMA_VERSION,
        "project_id": AL16_PROJECT_ID,
        "performance_context_bpm": AL16_PERFORMANCE_CONTEXT_BPM,
        "concept": AL16_BANK_CONCEPT,
        "adjacent_sonic_dna_target_percent": list(AL16_ADJACENT_SONIC_DNA_TARGET_PERCENT),
        "states": [
            {"number": state.number, "name": state.name, "tonal_zone": state.tonal_zone}
            for state in AL16_BANK_STATES
        ],
        "permanent_pad_roles": {str(pad): role for pad, role in AL16_PAD_ROLES.items()},
    }


def render_al16_bank_spec() -> str:
    """Render the checked-in JSON-compatible YAML from canonical data."""

    return json.dumps(al16_bank_spec_payload(), indent=2, ensure_ascii=True) + "\n"


__all__ = [
    "AL16_ADJACENT_SONIC_DNA_TARGET_PERCENT",
    "AL16_BANK_CONCEPT",
    "AL16_BANK_SCHEMA_VERSION",
    "AL16_BANK_STATES",
    "AL16_PAD_ROLES",
    "AL16_PERFORMANCE_CONTEXT_BPM",
    "AL16_PRESERVED_GLOBAL_SECTIONS",
    "AL16_RYTM_APPROVED_TUNING",
    "AL16_RYTM_EVIDENCE_GROUPS",
    "AL16_RYTM_FILTER_TYPES",
    "AL16_RYTM_MAPPING_GAP_PATHS",
    "AL16_RYTM_WRITABLE_FIELDS",
    "AL16_TRACK_MODE_PATCH",
    "AL16_TRACK_MODE_PRESERVE",
    "AL16_PROJECT_ID",
    "Al16BankSpecPayload",
    "Al16BankState",
    "Al16BankStatePayload",
    "Al16TrackMode",
    "Al16RytmEvidenceClass",
    "Al16RytmEvidenceGroup",
    "RYTM_CONVERTER_CENTERED_7BIT",
    "RYTM_CONVERTER_FILTER_TYPE_ENUM",
    "RYTM_CONVERTER_VERIFIED_7BIT",
    "RytmValueConverter",
    "RytmWritableField",
    "al16_bank_spec_payload",
    "render_al16_bank_spec",
]
