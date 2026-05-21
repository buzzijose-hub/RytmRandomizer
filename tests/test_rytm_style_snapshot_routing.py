from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast


def _style_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
                2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
                3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
                10: RytmSnapshotMachineFact(10, 10, 10, True, "promoted"),
            }
        ),
        promoted=True,
    )
    return RytmKitSnapshot(
        slot=4,
        kit_name="STYLEKIT",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def _candidate_only_snapshot():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad=MappingProxyType(
            {
                6: RytmSnapshotMachineFact(
                    6,
                    8,
                    None,
                    False,
                    "candidate-only tom-pad machine fact",
                ),
            }
        ),
        promoted=False,
    )
    return RytmKitSnapshot(
        slot=5,
        kit_name="CANDIDATE",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def test_style_snapshot_routing_requires_known_style_key():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        plan_rytm_style_snapshot_routes(_style_snapshot(), "ghost_style")


def test_style_snapshot_routing_reports_ready_and_blocked_pads():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")

    assert plan.kit_name == "STYLEKIT"
    assert plan.slot == 4
    assert plan.style_key == "birmingham_pressure"
    assert plan.ready_pad_count == 3
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is True
    assert plan.pads_by_pad[1].route_ready is True
    assert plan.pads_by_pad[1].profile_key == "2"
    assert plan.pads_by_pad[10].track_code == "OH"
    assert plan.pads_by_pad[10].current_machine_key == "oh_classic"
    assert plan.pads_by_pad[10].route_ready is False
    assert "selectable-only" in plan.pads_by_pad[10].readiness_reason


def test_style_snapshot_routing_uses_style_vector_for_favored_zones():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    birmingham = plan_rytm_style_snapshot_routes(_style_snapshot(), "birmingham_pressure")
    deep = plan_rytm_style_snapshot_routes(_style_snapshot(), "deep_dark_hypnosis")

    assert birmingham.favored_zones[:3] == ("grit", "body", "amp")
    assert "filter" in deep.favored_zones
    assert "lfo" in deep.favored_zones


def test_style_snapshot_routing_ranks_legal_machine_candidates_per_pad():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_style_snapshot(), "mills_hypnotic")

    assert plan.pads_by_pad[1].compatible_machine_candidates[0].machine_key == "bd_fm"
    pad_10_candidates = {
        candidate.machine_key for candidate in plan.pads_by_pad[10].compatible_machine_candidates
    }
    assert "oh_classic" in pad_10_candidates
    assert "oh_metallic" in pad_10_candidates
    assert "xt_classic" not in pad_10_candidates
    assert plan.pads_by_pad[10].mutable_machine_candidates == ()


def test_style_snapshot_routing_blocks_candidate_only_machine_facts():
    from rytm_randomizer.devices.strategies.analog_rytm_style_snapshot_routing import (
        plan_rytm_style_snapshot_routes,
    )

    plan = plan_rytm_style_snapshot_routes(_candidate_only_snapshot(), "warehouse_peak")

    assert plan.ready_pad_count == 0
    assert plan.blocked_pad_count == 1
    assert plan.partial_snapshot_mutation_ready is False
    assert plan.pads_by_pad[6].track_code == "LT"
    assert plan.pads_by_pad[6].route_ready is False
    assert "candidate-only" in plan.pads_by_pad[6].readiness_reason


def test_style_snapshot_routing_report_is_operator_facing_and_passive():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    lines = format_rytm_style_snapshot_routing_report(
        _style_snapshot(),
        style_key="birmingham_pressure",
    )
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Rytm style snapshot routing"
    assert "Kit: STYLEKIT" in lines
    assert "Slot: 4" in lines
    assert "Style target: birmingham_pressure" in lines
    assert "- Ready pads: 3" in lines
    assert "- Blocked pads: 1" in lines
    assert "Favored zones: grit, body, amp" in text
    assert "Pad 10 / OH / Open Hihat:" in text
    assert "  Current machine: oh_classic / CC15 10" in text
    assert "  Route ready: False" in text
    assert "  Mutable candidates: none" in text
    assert "  Compatible candidates:" in text
    assert "oh_metallic" in text
    assert "xt_classic" not in text
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_style_snapshot_routing" in lines
    assert "In-memory only: True" in lines


def test_style_snapshot_routing_report_rejects_unknown_style_safely():
    from rytm_randomizer.reports.rytm_style_snapshot_routing import (
        format_rytm_style_snapshot_routing_report,
    )

    with pytest.raises(ValueError, match="Unknown style target key: ghost_style"):
        format_rytm_style_snapshot_routing_report(_style_snapshot(), style_key="ghost_style")
