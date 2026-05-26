"""Tests for the passive live GUI snapshot compatibility model."""

from __future__ import annotations

import json
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def test_snapshot_compatibility_model_summarizes_current_12_pad_state() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_compatibility_model import (
        build_live_gui_snapshot_compatibility_model,
        format_live_gui_snapshot_compatibility_model,
        to_live_gui_snapshot_compatibility_model_json,
    )

    report = build_live_gui_snapshot_compatibility_model(
        panel_label="Snapshot Compatibility",
        session_label="Warehouse live session",
    )

    assert report.model_version == "live-gui-snapshot-compatibility-v1"
    assert len(report.compatibility_id) == 16
    assert report.panel_label == "Snapshot Compatibility"
    assert report.session_label == "Warehouse live session"
    assert report.pad_count == 12
    assert report.snapshot_mutable_pad_count == 4
    assert report.planned_pad_count == 8
    assert report.compatibility_status == "limited"
    assert report.status_badge == "Limited"
    assert report.summary == "4 of 12 pads are snapshot-mutable; 8 are planned/locked."
    assert report.view_details_enabled is True
    assert report.required_actions == (
        "review-planned-pad-locks",
        "implement-remaining-pad-engines",
    )
    assert report.blocked_actions == (
        "no snapshot file parsing",
        "no MIDI port opened",
        "no MIDI sending",
        "no hardware mutation",
    )
    assert report.replay_commands == (
        "python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report",
    )

    pads_by_number = {pad.pad: pad for pad in report.pads}
    assert pads_by_number[1].status == "compatible"
    assert pads_by_number[1].severity == "ready"
    assert pads_by_number[1].snapshot_mutation_enabled is True
    assert pads_by_number[1].map_safe is True
    assert pads_by_number[10].track_code == "OH"
    assert pads_by_number[10].label == "Open Hihat"
    assert pads_by_number[10].status == "planned"
    assert pads_by_number[10].severity == "limited"
    assert pads_by_number[10].snapshot_mutation_enabled is False
    assert pads_by_number[10].map_safe is True
    assert pads_by_number[10].lock_reason.endswith("none are snapshot-mutable yet.")

    payload = to_live_gui_snapshot_compatibility_model_json(report)
    assert payload["live_gui_snapshot_compatibility"]["compatibility_status"] == "limited"
    assert payload["live_gui_snapshot_compatibility"]["pads"][9]["track_code"] == "OH"
    assert payload["safety"][0] == "passive/read-only"
    json.dumps(payload, sort_keys=True)

    lines = format_live_gui_snapshot_compatibility_model(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive live GUI snapshot compatibility model"
    assert "Snapshot compatibility summary:" in lines
    assert "- compatibility status: limited" in lines
    assert "Pad compatibility rows:" in lines
    assert "Pad 10 / OH / Open Hihat: planned" in text
    assert "- no MIDI sending" in lines


def test_snapshot_compatibility_model_marks_all_mutable_source_compatible() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_compatibility_model import (
        build_live_gui_snapshot_compatibility_model,
    )
    from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import (
        RytmSnapshotPadCompatibilityPadReport,
        RytmSnapshotPadCompatibilityReport,
    )

    pad_reports = {
        pad: RytmSnapshotPadCompatibilityPadReport(
            pad=pad,
            track_code=f"P{pad:02d}",
            label=f"Pad {pad}",
            allowed_machine_count=1,
            mutable_machine_count=1,
            machine_selectable_count=0,
            snapshot_ready=True,
            readiness_reason="Snapshot-ready: custom all-pad fixture.",
            machine_labels=(f"Machine {pad}",),
        )
        for pad in range(1, 13)
    }
    source_report = RytmSnapshotPadCompatibilityReport(
        pad_count=12,
        snapshot_ready_pad_count=12,
        blocked_pad_count=0,
        allowed_slot_count=12,
        pads_by_pad=MappingProxyType(pad_reports),
    )

    report = build_live_gui_snapshot_compatibility_model(source_report=source_report)

    assert report.compatibility_status == "compatible"
    assert report.status_badge == "Compatible"
    assert report.snapshot_mutable_pad_count == 12
    assert report.planned_pad_count == 0
    assert report.summary == "All 12 pads map safely to the current snapshot."
    assert report.required_actions == ("view-details",)
    assert all(pad.status == "compatible" for pad in report.pads)


def test_snapshot_compatibility_model_validation_edges() -> None:
    from rytm_randomizer.reports.live_gui_snapshot_compatibility_model import (
        build_live_gui_snapshot_compatibility_model,
    )
    from rytm_randomizer.reports.rytm_snapshot_pad_compatibility import (
        RytmSnapshotPadCompatibilityReport,
    )

    with pytest.raises(ValueError, match="panel_label"):
        build_live_gui_snapshot_compatibility_model(panel_label=" ")

    with pytest.raises(ValueError, match="session_label"):
        build_live_gui_snapshot_compatibility_model(session_label=" ")

    invalid_source = RytmSnapshotPadCompatibilityReport(
        pad_count=0,
        snapshot_ready_pad_count=0,
        blocked_pad_count=0,
        allowed_slot_count=0,
        pads_by_pad=MappingProxyType({}),
    )
    with pytest.raises(ValueError, match="source_report"):
        build_live_gui_snapshot_compatibility_model(source_report=invalid_source)
