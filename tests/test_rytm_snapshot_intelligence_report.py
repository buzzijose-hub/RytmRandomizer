"""Tests for the passive Rytm snapshot intelligence report."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast


def _snapshot_with_machine_facts():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    raw_values = {
        1: 0,
        2: 2,
        3: 4,
        4: 6,
        5: 7,
        6: 30,
        7: 0,
        8: 0,
        9: 9,
        10: 10,
        11: 11,
        12: 12,
    }
    facts = {
        pad: RytmSnapshotMachineFact(
            pad=pad,
            raw_machine_value=value,
            decoded_machine_value=value if pad not in (6, 7, 8) else None,
            promoted=pad not in (6, 7, 8),
            reason=(
                "promoted machine fact"
                if pad not in (6, 7, 8)
                else "candidate-only tom-pad machine fact"
            ),
        )
        for pad, value in raw_values.items()
    }
    return RytmKitSnapshot(
        slot=3,
        kit_name="LIVE KIT",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=RytmSnapshotMachineFacts(facts_by_pad=facts, promoted=False),
    )


def _promoted_snapshot_with_values(raw_values: dict[int, int]):
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = {
        pad: RytmSnapshotMachineFact(
            pad=pad,
            raw_machine_value=value,
            decoded_machine_value=value,
            promoted=True,
            reason="promoted machine fact",
        )
        for pad, value in raw_values.items()
    }
    return RytmKitSnapshot(
        slot=4,
        kit_name="PROMOTED KIT",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=RytmSnapshotMachineFacts(facts_by_pad=facts, promoted=True),
    )


def test_build_report_summarizes_snapshot_machine_fact_readiness() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    report = build_rytm_snapshot_intelligence_report(_snapshot_with_machine_facts())

    assert report.kit_name == "LIVE KIT"
    assert report.slot == 3
    assert report.pad_count == 12
    assert report.promoted_fact_count == 9
    assert report.candidate_fact_count == 3
    assert report.route_ready_count == 2
    assert report.route_blocked_count == 7
    assert report.full_snapshot_mutation_ready is False
    assert report.partial_snapshot_mutation_ready is True
    assert "candidate-only machine facts" in report.readiness_reason


def test_build_report_marks_missing_snapshot_machine_facts() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    snapshot = _promoted_snapshot_with_values({1: 0})

    report = build_rytm_snapshot_intelligence_report(snapshot)

    assert report.promoted_fact_count == 1
    assert report.candidate_fact_count == 11
    assert report.full_snapshot_mutation_ready is False
    assert report.pads_by_pad[2].raw_machine_value == -1
    assert report.pads_by_pad[2].decoded_machine_value is None
    assert report.pads_by_pad[2].route_reason == "missing snapshot machine fact"


def test_build_report_marks_candidate_only_tom_pads() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    report = build_rytm_snapshot_intelligence_report(_snapshot_with_machine_facts())

    for pad in (6, 7, 8):
        pad_report = report.pads_by_pad[pad]
        assert pad_report.fact_promoted is False
        assert pad_report.decoded_machine_value is None
        assert pad_report.route_ready is False
        assert pad_report.route_reason == "candidate-only tom-pad machine fact"


def test_build_report_routes_promoted_snapshot_machine_values() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    report = build_rytm_snapshot_intelligence_report(_snapshot_with_machine_facts())

    pad_1 = report.pads_by_pad[1]
    assert pad_1.raw_machine_value == 0
    assert pad_1.decoded_machine_value == 0
    assert pad_1.machine_key == "bd_hard"
    assert pad_1.profile_key == "2"
    assert pad_1.route_ready is True
    assert "snapshot-mutable" in pad_1.route_reason

    pad_10 = report.pads_by_pad[10]
    assert pad_10.machine_key == "oh_classic"
    assert pad_10.profile_key is None
    assert pad_10.route_ready is False
    assert "selectable-only" in pad_10.route_reason


def test_build_report_uses_routing_reason_when_all_facts_are_promoted_but_blocked() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    snapshot = _promoted_snapshot_with_values(
        {
            1: 0,
            2: 3,
            3: 32,
            4: 30,
            5: 7,
            6: 8,
            7: 8,
            8: 8,
            9: 9,
            10: 10,
            11: 11,
            12: 12,
        }
    )

    report = build_rytm_snapshot_intelligence_report(snapshot)

    assert report.candidate_fact_count == 0
    assert report.full_snapshot_mutation_ready is False
    assert "selectable-only" in report.readiness_reason


def test_readiness_reason_marks_ready_and_empty_edge_cases() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import _readiness_reason

    assert (
        _readiness_reason(
            candidate_fact_count=0,
            route_ready_count=1,
            route_readiness_reason="",
        )
        == "snapshot machine facts route to mutable V1.34 profiles"
    )
    assert (
        _readiness_reason(
            candidate_fact_count=0,
            route_ready_count=0,
            route_readiness_reason="",
        )
        == "snapshot has no promoted machine facts"
    )


def test_format_report_is_operator_facing_and_passive() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        format_rytm_snapshot_intelligence_report,
    )

    lines = format_rytm_snapshot_intelligence_report(
        _snapshot_with_machine_facts(),
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm snapshot intelligence"
    assert "Kit: LIVE KIT" in lines
    assert "Slot: 3" in lines
    assert "- Pads: 12" in lines
    assert "- Promoted machine facts: 9" in lines
    assert "- Candidate-only machine facts: 3" in lines
    assert "- Full snapshot mutation ready: False" in lines
    assert "- Partial snapshot mutation ready: True" in lines
    assert "Pad 10: raw=10 decoded=10 route_ready=False" in text
    assert "OH Classic is selectable-only" in text
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_snapshot_intelligence" in lines
    assert "In-memory only: True" in lines


def test_build_report_rejects_non_rytm_snapshot() -> None:
    from rytm_randomizer.reports.rytm_snapshot_intelligence import (
        build_rytm_snapshot_intelligence_report,
    )

    with pytest.raises(ValueError, match="RytmKitSnapshot"):
        build_rytm_snapshot_intelligence_report(object())
