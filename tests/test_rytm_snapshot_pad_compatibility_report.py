"""Tests for the passive Rytm snapshot-pad compatibility report."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import (
    build_rytm_snapshot_pad_compatibility_report,
    format_rytm_snapshot_pad_compatibility_report,
)


def test_build_report_summarizes_snapshot_readiness() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()

    assert report.pad_count == 12
    assert report.snapshot_ready_pad_count == 4
    assert report.blocked_pad_count == 8
    assert report.allowed_slot_count == 116


def test_build_report_marks_v134_backed_pads_ready() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()

    for pad in (1, 2, 3, 4):
        pad_report = report.pads_by_pad[pad]
        assert pad_report.snapshot_ready is True
        assert pad_report.mutable_machine_count > 0
        assert "V1.34-backed" in pad_report.readiness_reason


def test_build_report_blocks_pad_10_without_tom_engine_leakage() -> None:
    report = build_rytm_snapshot_pad_compatibility_report()
    pad_10 = report.pads_by_pad[10]

    assert pad_10.track_code == "OH"
    assert pad_10.label == "Open Hihat"
    assert pad_10.snapshot_ready is False
    assert pad_10.mutable_machine_count == 0
    assert pad_10.machine_selectable_count == 8
    assert "XT Classic" not in pad_10.machine_labels
    assert "not snapshot-mutable yet" in pad_10.readiness_reason


def test_format_report_is_passive_and_operator_facing() -> None:
    lines = format_rytm_snapshot_pad_compatibility_report()
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm snapshot pad compatibility"
    assert "- Pads: 12" in lines
    assert "- Snapshot-ready pads: 4" in lines
    assert "- Blocked pads: 8" in lines
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "Snapshot ready: False" in text
    pad_10_block = text.split("Pad 10 / OH / Open Hihat:", 1)[1].split(
        "Pad 11 / CY / Cymbal:", 1
    )[0]
    assert "XT Classic" not in pad_10_block
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_snapshot_pad_compatibility" in lines
    assert "In-memory only: True" in lines
