"""Selected reconciled MIDI Guide descriptions, never executable domains.

CSV numeric choices are reference claims, not verified native or wire codes.
The tables intentionally do not replace catalog addresses, mutation policy,
saved-KIT fields, converters, or readiness. Missing values stay missing.
Derived MIDI Guide data and its adaptations are CC-BY-SA-4.0; the packaged
attribution notice below applies to these tables, not to the application's code.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

ReferenceOrientation: TypeAlias = Literal["zero_based", "centered"]
ReferenceProtocol: TypeAlias = Literal["cc", "nrpn"]

MIDI_GUIDE_DATA_NOTICE: Final[str] = (
    "Selected MIDI reference data adapted from MIDI Guide, maintained by Pencil Research "
    "and its contributors (https://midi.guide/d/elektron/; "
    "https://github.com/pencilresearch/midi). "
    "The derived data tables and adaptations in elektron_midi_descriptions.py are licensed "
    "under Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0): "
    "https://creativecommons.org/licenses/by-sa/4.0/ . "
    "Upstream license: https://github.com/pencilresearch/midi/blob/main/LICENSE . "
    "Changes: selected rows reconciled to canonical catalog names; reference-only labels, "
    "ranges, orientations and omissions separated from executable domains; conflicts retained. "
    "Device-specific material may be owned by the respective manufacturers, as upstream notes. "
    "No endorsement, target-unit verification, native authoring or MIDI authority is implied."
)


@dataclass(frozen=True)
class MidiReferenceSource:
    """Provenance of the supplied file, not a hardware validation receipt.

    The hash identifies the user's CSV, not a verified upstream commit or byte
    identity. The CSV does not establish the installed target-unit firmware.
    """

    device_page: str
    supplied_filename: str
    supplied_sha256: str
    attribution: str = "MIDI Guide / Pencil Research and contributors"
    repository_url: str = "https://github.com/pencilresearch/midi"
    license_id: str = "CC-BY-SA-4.0"
    license_url: str = "https://creativecommons.org/licenses/by-sa/4.0/"
    upstream_license_url: str = "https://github.com/pencilresearch/midi/blob/main/LICENSE"


MIDI_GUIDE_SOURCES: Final[Mapping[str, MidiReferenceSource]] = MappingProxyType(
    {
        "rytm": MidiReferenceSource(
            "https://midi.guide/d/elektron/analog-rytm-mkii/",
            "Analog Rytm MKII.csv",
            "c370aa520117322ef559147b94b9cee9c392f6482a5147f0ea2485a07ace0cc5",
        ),
        "a4": MidiReferenceSource(
            "https://midi.guide/d/elektron/analog-four-mkii/",
            "Analog Four MKII.csv",
            "da38d8ec8df47d4a6c39034b2f1c829475ac301c712d26c0a4b4787ae259ea69",
        ),
    }
)

_RYTM_MANUAL: Final[str] = (
    "https://www.elektron.se/wp-content/uploads/2025/01/"
    "Analog-Rytm-MKII-User-Manual_ENG_OS1.72_250130.pdf"
)
_A4_MANUAL: Final[str] = (
    "https://www.elektron.se/wp-content/uploads/2024/09/"
    "Analog-Four-MKII-User-Manual_ENG_OS1.51C_220204-1.pdf"
)


@dataclass(frozen=True)
class MidiParameterDescription:
    """A reference projection; no field is an executable legal-value domain.

    ``source_row`` counts the CSV header as row 1. ``None`` records an omission.
    All numeric labels remain reference-only, even when the manual confirms the
    named options. Qualitative units do not define code-to-unit conversions.
    """

    source: MidiReferenceSource
    source_row: int | None
    cc_range: tuple[int, int] | None
    nrpn_range: tuple[int, int] | None
    orientation: ReferenceOrientation | None = None
    reference_labels: tuple[tuple[int, str], ...] = ()
    units: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()
    supporting_urls: tuple[str, ...] = ()
    missing_source_fields: tuple[str, ...] = ()

    @property
    def code_authority(self) -> Literal["reference_only"]:
        return "reference_only"

    def label_for_value(self, value: int, *, protocol: ReferenceProtocol = "cc") -> str | None:
        """Look up a reference label strictly, without converting or clamping."""

        if type(value) is not int:
            raise ValueError("reference_value_requires_integer")
        if protocol not in ("cc", "nrpn"):
            raise ValueError("reference_protocol_unknown")
        bounds = self.cc_range if protocol == "cc" else self.nrpn_range
        if bounds is None:
            raise ValueError("reference_range_unavailable")
        if not bounds[0] <= value <= bounds[1]:
            raise ValueError("reference_value_outside_reported_range")
        for code, label in self.reference_labels:
            if code == value:
                return label
        return None


@dataclass(frozen=True)
class MidiReferenceNote:
    source: MidiReferenceSource
    source_row: int
    message: str


# Exact CSV labels; the regular pulse-width suffix is data, not a conversion.
_CHIP_WAVEFORM_NAMES: Final[tuple[str, ...]] = (
    "Analog Sine",
    "Asymmetric Sine",
    "Triangle",
    "Sinesaw",
    "Saw",
    "Square",
    "Noise",
    "Anim 1",
    "Anim 2",
    "Anim 3",
    "Anim 4",
    "Anim 5",
    "PWM+",
    "PWM-",
    ".TRI",
    "+TRI",
    "TRI+",
    "TRI*",
    ".SAW",
    "+SAW",
    "SAW+",
    "SAW*",
    ".SQR",
    "+SQR",
    "SQR+",
    "SQR*",
    "TBL1",
    "TBL2",
    "TBL3",
) + tuple(f"P{width}%" for width in range(1, 100))

_RYTM_SOURCE: Final[MidiReferenceSource] = MIDI_GUIDE_SOURCES["rytm"]
_A4_SOURCE: Final[MidiReferenceSource] = MIDI_GUIDE_SOURCES["a4"]
_CHIP_MISSING_NRPN: Final[tuple[str, ...]] = ("nrpn_address", "nrpn_range")

RYTM_MIDI_DESCRIPTIONS: Final[Mapping[tuple[str, str], MidiParameterDescription]] = (
    MappingProxyType(
        {
            ("ut_impulse", "Polarity"): MidiParameterDescription(
                _RYTM_SOURCE,
                322,
                (0, 1),
                (0, 1),
                "zero_based",
                ((0, "Positive"), (1, "Negative")),
                notes=("Manual names POS/NEG but does not establish these numeric wire codes.",),
                supporting_urls=(_RYTM_MANUAL + "#page=97",),
            ),
            ("sy_chip", "Waveform"): MidiParameterDescription(
                _RYTM_SOURCE,
                230,
                (0, 127),
                None,
                "zero_based",
                tuple(enumerate(_CHIP_WAVEFORM_NAMES)),
                notes=("128 CSV labels do not establish native selector encoding.",),
                supporting_urls=(_RYTM_MANUAL,),
                missing_source_fields=_CHIP_MISSING_NRPN,
            ),
            ("sy_chip", "Speed"): MidiParameterDescription(
                _RYTM_SOURCE,
                231,
                (0, 127),
                None,
                "zero_based",
                units=("BPM note divisions", "Hz", "single-shot"),
                notes=(
                    "Manual describes tempo-synced, fixed-Hz and single-shot regions; "
                    "numeric boundaries, mode codes and conversions are not established.",
                ),
                supporting_urls=(_RYTM_MANUAL,),
                missing_source_fields=_CHIP_MISSING_NRPN + ("usage",),
            ),
            ("cy_ride", "Cymbal Type"): MidiParameterDescription(
                _RYTM_SOURCE,
                297,
                (0, 3),
                (0, 3),
                "zero_based",
                ((0, "A"), (1, "B"), (2, "C"), (3, "D")),
                notes=("A-D names do not resolve the held CY Ride native SRC slot semantics.",),
                supporting_urls=(_RYTM_MANUAL,),
            ),
            ("bt_classic", "Sweep Depth"): MidiParameterDescription(
                _RYTM_SOURCE,
                None,
                None,
                None,
                notes=(
                    "CSV omits this parameter; retain the independent Appendix C/D catalog row.",
                ),
                supporting_urls=(_RYTM_MANUAL + "#page=93", _RYTM_MANUAL + "#page=105"),
                missing_source_fields=("parameter_row",),
            ),
            ("SAMPLE", "Sample Tune"): MidiParameterDescription(
                _RYTM_SOURCE, 33, (40, 88), (40, 88), "centered"
            ),
            ("SAMPLE", "Sample Fine tune"): MidiParameterDescription(
                _RYTM_SOURCE, 34, (0, 127), (0, 127), "centered"
            ),
            ("FILTER", "Filter Env Depth"): MidiParameterDescription(
                _RYTM_SOURCE, 48, (0, 127), (0, 127), "centered"
            ),
            ("AMP", "Amp Pan"): MidiParameterDescription(
                _RYTM_SOURCE, 55, (0, 127), (0, 127), "centered"
            ),
            ("cy_ride", "Tune"): MidiParameterDescription(
                _RYTM_SOURCE, 296, (0, 127), (0, 127), "centered"
            ),
            ("ut_noise", "Sweep Depth"): MidiParameterDescription(
                _RYTM_SOURCE, 317, (0, 127), (0, 127), "centered"
            ),
            ("sy_chip", "Tune"): MidiParameterDescription(
                _RYTM_SOURCE,
                229,
                (0, 127),
                None,
                "centered",
                missing_source_fields=_CHIP_MISSING_NRPN,
            ),
            **{
                ("sy_chip", f"Offset {index}"): MidiParameterDescription(
                    _RYTM_SOURCE,
                    231 + index,
                    (40, 88),
                    None,
                    "centered",
                    notes=("Reported MIDI range is not a legal native offset domain.",),
                    missing_source_fields=_CHIP_MISSING_NRPN,
                )
                for index in (2, 3, 4)
            },
        }
    )
)

# Kept separate from A4 display/native domains, including calibrated F1 Q8.8.
A4_MIDI_DESCRIPTIONS: Final[Mapping[str, MidiParameterDescription]] = MappingProxyType(
    {
        "Filter1 Frequency": MidiParameterDescription(
            _A4_SOURCE,
            48,
            (0, 127),
            (0, 127),
            "zero_based",
            notes=("CSV MIDI ranges do not replace calibrated native F1 Q8.8 or its converter.",),
            supporting_urls=(_A4_MANUAL + "#page=88", _A4_MANUAL + "#page=106"),
        ),
        "Filter2 Type": MidiParameterDescription(
            _A4_SOURCE,
            55,
            None,
            (0, 6),
            "zero_based",
            (
                (0, "2-pole Lowpass"),
                (1, "1-pole Lowpass"),
                (2, "Bandpass"),
                (3, "1-pole Highpass"),
                (4, "2-pole Highpass"),
                (5, "Bandstop"),
                (6, "Peak"),
            ),
            notes=("Reference ordinals do not replace native codes or lift enum transport holds.",),
            supporting_urls=(_A4_MANUAL + "#page=88",),
            missing_source_fields=("cc_address", "cc_range"),
        ),
        "Volume": MidiParameterDescription(
            _A4_SOURCE,
            62,
            (0, 127),
            (0, 127),
            "zero_based",
            notes=("MIDI reference knowledge does not lift OXI AMP ownership/protection.",),
        ),
    }
)

RYTM_MACHINE_REFERENCE_NOTES: Final[Mapping[str, tuple[MidiReferenceNote, ...]]] = MappingProxyType(
    {
        "bd_hard": (
            MidiReferenceNote(
                _RYTM_SOURCE,
                12,
                "CSV omits BD Hard / identity 0 and reports MIDI range 1..33; "
                "retain native identity 0 without inferring a MIDI encoding.",
            ),
        ),
        "rs_classic": (
            MidiReferenceNote(
                _RYTM_SOURCE,
                12,
                "CSV labels both codes 4 and 5 RS Hard; retain canonical RS Classic identity 5 "
                "and treat the duplicate label as a conflict, not a wire-encoding correction.",
            ),
        ),
    }
)

__all__ = [
    "A4_MIDI_DESCRIPTIONS",
    "MIDI_GUIDE_DATA_NOTICE",
    "MIDI_GUIDE_SOURCES",
    "MidiParameterDescription",
    "MidiReferenceNote",
    "MidiReferenceSource",
    "RYTM_MACHINE_REFERENCE_NOTES",
    "RYTM_MIDI_DESCRIPTIONS",
    "ReferenceOrientation",
    "ReferenceProtocol",
]
