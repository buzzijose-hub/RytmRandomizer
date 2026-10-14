"""Pinned community CSV provenance and reconciliation evidence, not grants."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from .elektron_midi_descriptions import MIDI_GUIDE_SOURCES


@dataclass(frozen=True)
class MidiCsvSourceSpec:
    """Immutable identity of one supplied reference file."""

    family: str
    device_id: str
    device_label: str
    filename: str
    sha256: str
    row_count: int
    source_url: str
    manual_url: str


MIDI_CSV_SOURCES: Final[tuple[MidiCsvSourceSpec, ...]] = (
    MidiCsvSourceSpec(
        "a4",
        "analog_four_mk2",
        "Analog Four MKII",
        MIDI_GUIDE_SOURCES["a4"].supplied_filename,
        MIDI_GUIDE_SOURCES["a4"].supplied_sha256,
        230,
        MIDI_GUIDE_SOURCES["a4"].device_page,
        "https://www.elektron.se/wp-content/uploads/2024/09/Analog-Four-MKII-User-Manual_ENG_OS1.51C_220204-1.pdf",
    ),
    MidiCsvSourceSpec(
        "rytm",
        "analog_rytm_mk2",
        "Analog Rytm MKII",
        MIDI_GUIDE_SOURCES["rytm"].supplied_filename,
        MIDI_GUIDE_SOURCES["rytm"].supplied_sha256,
        322,
        MIDI_GUIDE_SOURCES["rytm"].device_page,
        "https://www.elektron.se/wp-content/uploads/2025/01/Analog-Rytm-MKII-User-Manual_ENG_OS1.72_250130.pdf",
    ),
)
MIDI_CSV_COLUMNS: Final[tuple[str, ...]] = (
    "manufacturer",
    "device",
    "section",
    "parameter_name",
    "parameter_description",
    "cc_msb",
    "cc_lsb",
    "cc_min_value",
    "cc_max_value",
    "cc_default_value",
    "nrpn_msb",
    "nrpn_lsb",
    "nrpn_min_value",
    "nrpn_max_value",
    "nrpn_default_value",
    "orientation",
    "notes",
    "usage",
)
MIDI_CSV_ADDRESS_COLUMNS: Final[tuple[str, ...]] = (
    "cc_msb",
    "cc_lsb",
    "nrpn_msb",
    "nrpn_lsb",
)
MIDI_CSV_ADDRESS_MAX: Final[int] = 127
MIDI_CSV_VALUE_MAX: Final[int] = 16383
MIDI_CSV_FIRST_AUDIT_ROW: Final[int] = 2
MIDI_CSV_ATTRIBUTION: Final[str] = MIDI_GUIDE_SOURCES["a4"].attribution
MIDI_CSV_REPOSITORY: Final[str] = MIDI_GUIDE_SOURCES["a4"].repository_url
MIDI_CSV_LICENSE: Final[str] = MIDI_GUIDE_SOURCES["a4"].license_id
MIDI_CSV_LICENSE_URL: Final[str] = MIDI_GUIDE_SOURCES["a4"].upstream_license_url
MIDI_CSV_UPSTREAM_COMMIT: Final[str] = str(
    getattr(MIDI_GUIDE_SOURCES["a4"], "upstream_revision", None)
    or "a52a7c9e1a81a4e95f31ec8b6a660071d11ecd6b"
)
MIDI_CSV_UPSTREAM_BLOBS: Final = MappingProxyType(
    {
        "a4": str(
            getattr(MIDI_GUIDE_SOURCES["a4"], "upstream_blob_sha1", None)
            or "53a1a26263782ce8f044b112a33642de27f547cd"
        ),
        "rytm": str(
            getattr(MIDI_GUIDE_SOURCES["rytm"], "upstream_blob_sha1", None)
            or "46cc786dc106f35a00a9412057f8ee63192aa308"
        ),
    }
)
MIDI_CSV_UPSTREAM_LAST_CHANGE: Final = MappingProxyType(
    {
        "a4": "1bf3ced25095dff32f71f8930da7415206d47130",
        "rytm": "3a072c57adfe7cfc85327b65617324d002cafca0",
    }
)
MIDI_CSV_ORIENTATION: Final = MappingProxyType({"0-based": "zero_based", "centered": "centered"})

# Scope aliases identify a page/track, never a parameter from its label alone.
MIDI_CSV_RYTM_SECTIONS: Final = MappingProxyType(
    {
        "Trig": "TRIG PARAMETERS",
        "Synth: General": "SYNTH",
        "Sample": "SAMPLE",
        "Filter": "FILTER",
        "Amp": "AMP",
        "LFO": "LFO",
        "FX: Delay": "DELAY",
        "FX: Reverb": "REVERB",
        "FX: Distortion": "DISTORTION",
        "FX: Compressor": "COMPRESSOR",
        "Kit": "COMMON",
        "Performance": "PERFORMANCE",
        "Euclidean": "EUCLIDEAN",
    }
)
MIDI_CSV_A4_SECTIONS: Final = MappingProxyType(
    {
        "Performance": "performance",
        "Modulation": "synth",
        "Track": "synth",
        "Amp": "synth",
        "Filters": "synth",
        "Synth: Noise": "synth",
        "Synth: OSC": "synth",
        "Synth: OSC1": "synth",
        "Synth: OSC2": "synth",
        "CVs": "cv",
        "FX: Chorus": "fx",
        "FX: Delay": "fx",
        "FX: Extern In": "fx",
        "FX: LFOs": "fx",
        "FX: Reverb": "fx",
    }
)
MIDI_CSV_HARDWARE_EVIDENCE: Final[tuple[str, ...]] = (
    "docs/hardware-validation/2026-10-01-cy-ride-inbound-address-check.md",
    "docs/hardware-validation/2026-07-17-a4-live-dial-enum-evidence.md",
    "docs/hardware-validation/2026-08-28-a4-filter1-frequency-saved-kit-evidence.md",
    "docs/NATIVE_REPRESENTATION_INTEGRATION.md",
    "docs/RYTM_MAPPING_STATUS.md",
)
MIDI_CSV_EVIDENCE_NOTES: Final = MappingProxyType(
    {
        "a4": (
            "CSV selector ordinals are hypotheses, not native enum codes or physical receipts.",
            "Retained July rehearsal disproved EnvF Gate Length, EnvF destinations, LFO1 multiplier/destinations/mode.",
            "F1 saved-KIT Q8.8 evidence does not prove live CC/NRPN precision, freshness or automatic restore.",
            "A4/BOTH output remains held; reference FX/CV controls have no implied saved-field mapping.",
        ),
        "rytm": (
            "validated_runtime is a software catalog category, not a per-row physical acceptance receipt.",
            "CY Ride HIT CC19 and TYP CC20 have narrow inbound receipts, not native-slot or outbound proof.",
            "All CY Ride SRC controls remain blocked regardless of address agreement.",
            "Tune/native machine identity and MIDI scalars are distinct; no universal note or selector inverse.",
            "Paired controls and automatic restore remain held; guarded cc7 still needs current session evidence.",
        ),
    }
)
MIDI_CSV_MANUAL_CHECKS: Final = MappingProxyType(
    {
        "rytm": {
            "version": "OS1.72_250130",
            "retrieved_sha256": "6485fc5eee11cd210913fa6041cde889b74ddaff19042220cea1db4b7b5d985f",
            "retrieved_bytes": 13216102,
            "pages": 114,
            "checked_pages": (85, 86, 87, 93, 94, 105, 108),
            "method": "read-only official PDF fetch and local pypdf extraction; originals untouched",
            "findings": (
                "BT Classic Sweep Depth: CC19, NRPN1:3; absent from supplied CSV, not from manual.",
                "CY Ride Hit Decay: CC19/NRPN1:3; Cymbal Type: CC20/NRPN1:4; agrees with narrow inbound receipts.",
                "General SRC ordering differs from front-panel parameter ordering; machine context is mandatory.",
                "LFO Depth pairs CC109/118; CSV and native representation cannot certify paired output or restore.",
                "MIDI appendix establishes addresses, not narrower ranges, enum inverses or per-row physical receipts.",
            ),
            "not_checked": "No target-unit outbound, native-slot, precision, freshness or restore experiment.",
        },
        "a4": {
            "version": "OS1.51C_220204",
            "checked_pages": (37, 97, 98, 102, 103, 104, 105, 106, 107),
            "method": "official PDF text inspection; no document bytes redistributed",
            "findings": (
                "FX NRPN bank2 and CV bank3 are distinct from synth/performance context.",
                "Envelope/LFO MIDI tables document addresses, not exact ordinal-to-native conversion.",
                "CSV reference tracks can include FX/CV pages that the synth saved-field strategy does not cover.",
                "July physical enum corrections supersede plugin/list-index hypotheses; general A4/BOTH remains held.",
            ),
            "not_checked": "OS1.51C manual does not prove installed OS1.55 target behavior or physical acceptance.",
        },
    }
)
