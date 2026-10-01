"""Independent manual transcriptions, not expectations generated from the tables.

Sources: Elektron Digitakt OS1.52A Appendix B pp. 88-89 and Digitakt II
OS1.10 Appendix B pp. 105-106. The pinned official links and distinctions
are recorded in docs/superpowers/plans/2026-09-08-digitakt-review-repairs.md.
These assignments establish no saved-project offsets or physical send authority.
"""

from __future__ import annotations

import pytest

from rytm_randomizer.data.digitakt_midi import (
    DIGITAKT_II_TRACK_CC,
    DIGITAKT_II_TRACK_CC_BY_MSB,
    DIGITAKT_MK1_TRACK_CC,
    DIGITAKT_MK1_TRACK_CC_BY_MSB,
)

pytestmark = pytest.mark.fast


@pytest.mark.parametrize(
    ("parameter", "cc", "nrpn_msb", "nrpn_lsb"),
    [
        ("Track Mute", 94, 1, 101),
        ("Track Level", 95, 1, 100),
        ("Filter Frequency", 74, 1, 20),
        ("Filter Resonance", 75, 1, 21),
        ("Filter Envelope Depth", 77, 1, 23),
        ("Amp Overdrive", 81, 1, 27),
        ("Sample Tune", 16, 1, 0),
        ("Sample Select", 19, 1, 3),
        ("Delay Send", 82, 1, 28),
        ("Reverb Send", 83, 1, 29),
    ],
)
def test_mk1_assignments_match_os152a_appendix_b(
    parameter: str, cc: int, nrpn_msb: int, nrpn_lsb: int
) -> None:
    row = DIGITAKT_MK1_TRACK_CC[parameter]
    assert (row.cc_msb, row.cc_lsb, row.nrpn_msb, row.nrpn_lsb) == (
        cc,
        None,
        nrpn_msb,
        nrpn_lsb,
    )
    assert DIGITAKT_MK1_TRACK_CC_BY_MSB[cc] is row


@pytest.mark.parametrize(
    ("parameter", "cc", "nrpn_msb", "nrpn_lsb"),
    [
        ("Track Mute", 94, 1, 101),
        ("Track Level", 95, 1, 100),
        ("Filter Frequency", 74, 1, 20),
        ("Filter Data Entry F", 75, 1, 21),
        ("Filter Envelope Depth", 77, 1, 23),
        ("FX Overdrive", 57, None, None),
        ("Sample Tune", 16, 1, 0),
        ("Sample Select", None, 1, 3),
        ("Delay Send", 84, 1, 36),
        ("Reverb Send", 85, 1, 37),
    ],
)
def test_ii_assignments_match_os110_appendix_b(
    parameter: str, cc: int | None, nrpn_msb: int | None, nrpn_lsb: int | None
) -> None:
    row = DIGITAKT_II_TRACK_CC[parameter]
    assert (row.cc_msb, row.cc_lsb, row.nrpn_msb, row.nrpn_lsb) == (
        cc,
        None,
        nrpn_msb,
        nrpn_lsb,
    )
    if cc is not None:
        assert DIGITAKT_II_TRACK_CC_BY_MSB[cc] is row


def test_ii_sample_selection_does_not_claim_the_distinct_sample_slot_cc() -> None:
    """II p.109 CC19 selects a slot within a bank; p.105 NRPN1/3 selects a sample."""

    assert DIGITAKT_II_TRACK_CC["Sample Select"].cc_msb is None
    assert 19 not in DIGITAKT_II_TRACK_CC_BY_MSB
    assert "Sample Slot" not in DIGITAKT_II_TRACK_CC


def test_ii_filter_f_and_effects_do_not_inherit_mk1_semantics() -> None:
    assert "Filter Resonance" not in DIGITAKT_II_TRACK_CC
    assert DIGITAKT_II_TRACK_CC["Filter Data Entry F"].encoder == "F"
    for name in ("FX Overdrive", "Delay Send", "Reverb Send"):
        assert DIGITAKT_II_TRACK_CC[name].section == "FX"
    assert DIGITAKT_MK1_TRACK_CC["Amp Overdrive"].section == "AMP"
