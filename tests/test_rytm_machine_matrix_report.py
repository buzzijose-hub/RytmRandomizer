"""Tests for the passive Rytm 12-pad machine matrix report."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.reports.rytm_machine_matrix import (
    build_rytm_machine_matrix_report,
    format_rytm_machine_matrix_report,
)


def _block_between(lines: list[str], start: str, next_start: str) -> list[str]:
    return lines[lines.index(start) : lines.index(next_start)]


def test_build_report_has_expected_totals() -> None:
    report = build_rytm_machine_matrix_report()

    assert report.pad_count == 12
    assert report.machine_profile_count == 33
    assert report.allowed_slot_count == 116
    assert not hasattr(report, "cc15_selectable_slot_count")
    assert not hasattr(report, "pending_machine_value_count")


def test_build_report_marks_pad_10_as_open_hihat() -> None:
    report = build_rytm_machine_matrix_report()
    pad_10 = report.pads_by_pad[10]

    assert pad_10.track_code == "OH"
    assert pad_10.label == "Open Hihat"
    assert "OH Classic (CC15 10)" in pad_10.machines
    assert "XT Classic (CC15 8)" not in pad_10.machines


def test_format_report_includes_totals_and_pad_10_safety_boundaries() -> None:
    lines = format_rytm_machine_matrix_report()
    text = "\n".join(lines)
    pad_10_lines = _block_between(
        lines,
        "Pad 10 / OH / Open Hihat:",
        "Pad 11 / CY / Cymbal:",
    )

    assert lines[0] == "RytmRandomizer passive Rytm 12-pad machine matrix"
    assert "- Pads: 12" in lines
    assert "- Machine profiles: 33" in lines
    assert "- Allowed pad-machine slots: 116" in lines
    assert not any("CC15-selectable slots" in line for line in lines)
    assert not any("Pending machine values" in line for line in lines)
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "OH Classic (CC15 10)" in text
    assert "  - XT Classic (CC15 8)" not in pad_10_lines
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_machine_matrix" in lines
    assert "In-memory only: True" in lines
