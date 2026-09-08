"""Manual-backed Digitakt MIDI CC facts.

Two Digitakt generations are in scope and they do **not** share a track
domain:

* **Digitakt (MK1)** -- 8 audio tracks + 8 MIDI tracks. Source: Digitakt
  User Manual ENG OS1.30, Appendix A: MIDI.
* **Digitakt II** -- 16 audio tracks. Source: Digitakt II User Manual ENG
  OS1.01, Appendix A: MIDI.

Per the data-not-code rule these tables live here exactly once and are
re-exported through :mod:`rytm_randomizer.data`. Strategy modules look CC
numbers up through this module; they never re-type the facts.

Every row below is transcribed from the published manual appendix. The
values are control-change assignments -- the same bytes any MIDI monitor
shows on the cable -- not reverse-engineered internals.

Scope note: these CC rows describe **live-dial** (working-RAM) control
only. They are deliberately NOT evidence for saved-project byte offsets;
see :mod:`rytm_randomizer.data.digitakt_saved_kit_layout`, which keeps
those unpromoted. Inferring offsets from live CC facts is forbidden by
``.claude/rules/targeted-mutation-safety.md`` #6.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

#: Digitakt (both generations) uses the standard NRPN control triple.
DIGITAKT_NRPN_PARAMETER_MSB_CC: Final[int] = 99
DIGITAKT_NRPN_PARAMETER_LSB_CC: Final[int] = 98
DIGITAKT_NRPN_DATA_MSB_CC: Final[int] = 6

#: Audio-track counts per generation. MIDI tracks are sequencer-only and
#: are not mutation targets, so they are excluded from the track domain.
DIGITAKT_MK1_AUDIO_TRACK_COUNT: Final[int] = 8
DIGITAKT_II_AUDIO_TRACK_COUNT: Final[int] = 16


@dataclass(frozen=True)
class DigitaktNrpnControlSpec:
    """The three CCs that carry one NRPN parameter change."""

    parameter_msb_cc: int
    parameter_lsb_cc: int
    data_msb_cc: int


DIGITAKT_NRPN_CONTROLS: Final[DigitaktNrpnControlSpec] = DigitaktNrpnControlSpec(
    parameter_msb_cc=DIGITAKT_NRPN_PARAMETER_MSB_CC,
    parameter_lsb_cc=DIGITAKT_NRPN_PARAMETER_LSB_CC,
    data_msb_cc=DIGITAKT_NRPN_DATA_MSB_CC,
)


@dataclass(frozen=True)
class DigitaktCcMapping:
    """One manual-documented Digitakt CC / NRPN assignment."""

    parameter: str
    section: str
    encoder: str
    cc_msb: int | None
    cc_lsb: int | None
    nrpn_msb: int | None
    nrpn_lsb: int | None


# ---------------------------------------------------------------------------
# Digitakt (MK1) -- Source: Digitakt User Manual ENG OS1.30, Appendix A: MIDI.
# ---------------------------------------------------------------------------
_DIGITAKT_MK1_TRACK_CC: Final[Mapping[str, DigitaktCcMapping]] = MappingProxyType(
    {
        "Track Mute": DigitaktCcMapping(
            parameter="Track Mute",
            section="TRACK",
            encoder="-",
            cc_msb=94,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=101,
        ),
        "Track Level": DigitaktCcMapping(
            parameter="Track Level",
            section="TRACK",
            encoder="-",
            cc_msb=95,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=100,
        ),
        "Filter Frequency": DigitaktCcMapping(
            parameter="Filter Frequency",
            section="FILTER",
            encoder="E",
            cc_msb=74,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=20,
        ),
        "Filter Resonance": DigitaktCcMapping(
            parameter="Filter Resonance",
            section="FILTER",
            encoder="F",
            cc_msb=75,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=21,
        ),
        "Filter Envelope Depth": DigitaktCcMapping(
            parameter="Filter Envelope Depth",
            section="FILTER",
            encoder="H",
            cc_msb=76,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=26,
        ),
        "Amp Overdrive": DigitaktCcMapping(
            parameter="Amp Overdrive",
            section="AMP",
            encoder="A",
            cc_msb=81,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=30,
        ),
        "Sample Tune": DigitaktCcMapping(
            parameter="Sample Tune",
            section="SRC",
            encoder="B",
            cc_msb=16,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=8,
        ),
        "Sample Slot": DigitaktCcMapping(
            parameter="Sample Slot",
            section="SRC",
            encoder="D",
            cc_msb=19,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=10,
        ),
        "Delay Send": DigitaktCcMapping(
            parameter="Delay Send",
            section="AMP",
            encoder="G",
            cc_msb=30,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=36,
        ),
        "Reverb Send": DigitaktCcMapping(
            parameter="Reverb Send",
            section="AMP",
            encoder="H",
            cc_msb=31,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=37,
        ),
    }
)

# ---------------------------------------------------------------------------
# Digitakt II -- Source: Digitakt II User Manual ENG OS1.01, Appendix A: MIDI.
# The DT II keeps the MK1 assignments for the rows below and extends the
# track domain to 16.
# ---------------------------------------------------------------------------
_DIGITAKT_II_TRACK_CC: Final[Mapping[str, DigitaktCcMapping]] = MappingProxyType(
    {
        "Track Mute": DigitaktCcMapping(
            parameter="Track Mute",
            section="TRACK",
            encoder="-",
            cc_msb=94,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=101,
        ),
        "Track Level": DigitaktCcMapping(
            parameter="Track Level",
            section="TRACK",
            encoder="-",
            cc_msb=95,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=100,
        ),
        "Filter Frequency": DigitaktCcMapping(
            parameter="Filter Frequency",
            section="FILTER",
            encoder="E",
            cc_msb=74,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=20,
        ),
        "Filter Resonance": DigitaktCcMapping(
            parameter="Filter Resonance",
            section="FILTER",
            encoder="F",
            cc_msb=75,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=21,
        ),
        "Filter Envelope Depth": DigitaktCcMapping(
            parameter="Filter Envelope Depth",
            section="FILTER",
            encoder="H",
            cc_msb=76,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=26,
        ),
        "Amp Overdrive": DigitaktCcMapping(
            parameter="Amp Overdrive",
            section="AMP",
            encoder="A",
            cc_msb=81,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=30,
        ),
        "Sample Tune": DigitaktCcMapping(
            parameter="Sample Tune",
            section="SRC",
            encoder="B",
            cc_msb=16,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=8,
        ),
        "Sample Slot": DigitaktCcMapping(
            parameter="Sample Slot",
            section="SRC",
            encoder="D",
            cc_msb=19,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=10,
        ),
        "Delay Send": DigitaktCcMapping(
            parameter="Delay Send",
            section="AMP",
            encoder="G",
            cc_msb=30,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=36,
        ),
        "Reverb Send": DigitaktCcMapping(
            parameter="Reverb Send",
            section="AMP",
            encoder="H",
            cc_msb=31,
            cc_lsb=None,
            nrpn_msb=1,
            nrpn_lsb=37,
        ),
    }
)

DIGITAKT_MK1_TRACK_CC: Final[Mapping[str, DigitaktCcMapping]] = _DIGITAKT_MK1_TRACK_CC
DIGITAKT_II_TRACK_CC: Final[Mapping[str, DigitaktCcMapping]] = _DIGITAKT_II_TRACK_CC


def _by_msb(table: Mapping[str, DigitaktCcMapping]) -> Mapping[int, DigitaktCcMapping]:
    """Index a CC table by its MSB CC number for reverse lookup."""

    return MappingProxyType({row.cc_msb: row for row in table.values() if row.cc_msb is not None})


DIGITAKT_MK1_TRACK_CC_BY_MSB: Final[Mapping[int, DigitaktCcMapping]] = _by_msb(
    _DIGITAKT_MK1_TRACK_CC
)
DIGITAKT_II_TRACK_CC_BY_MSB: Final[Mapping[int, DigitaktCcMapping]] = _by_msb(_DIGITAKT_II_TRACK_CC)


__all__ = [
    "DIGITAKT_II_AUDIO_TRACK_COUNT",
    "DIGITAKT_II_TRACK_CC",
    "DIGITAKT_II_TRACK_CC_BY_MSB",
    "DIGITAKT_MK1_AUDIO_TRACK_COUNT",
    "DIGITAKT_MK1_TRACK_CC",
    "DIGITAKT_MK1_TRACK_CC_BY_MSB",
    "DIGITAKT_NRPN_CONTROLS",
    "DIGITAKT_NRPN_DATA_MSB_CC",
    "DIGITAKT_NRPN_PARAMETER_LSB_CC",
    "DIGITAKT_NRPN_PARAMETER_MSB_CC",
    "DigitaktCcMapping",
    "DigitaktNrpnControlSpec",
]
