"""Tests for the passive Rytm snapshot mutation preview report."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _framed_sysex(payload: bytes) -> bytes:
    return bytes([0xF0]) + payload + bytes([0xF7])


def _promoted_snapshot_for_mutable_pads():
    from rytm_randomizer.devices.strategies import (
        RytmKitSnapshot,
        RytmSnapshotMachineFact,
        RytmSnapshotMachineFacts,
    )

    facts = RytmSnapshotMachineFacts(
        facts_by_pad={
            1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
            2: RytmSnapshotMachineFact(2, 3, 3, True, "promoted"),
            3: RytmSnapshotMachineFact(3, 32, 32, True, "promoted"),
        },
        promoted=True,
    )
    return RytmKitSnapshot(
        slot=6,
        kit_name="MUTABLE",
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
        facts_by_pad={
            1: RytmSnapshotMachineFact(1, 0, 0, True, "promoted"),
            6: RytmSnapshotMachineFact(
                6,
                8,
                None,
                False,
                "candidate-only tom-pad machine fact",
            ),
        },
        promoted=False,
    )
    return RytmKitSnapshot(
        slot=7,
        kit_name="CANDIDATE",
        raw=b"raw",
        unpacked=b"unpacked",
        machine_facts=facts,
    )


def test_build_preview_report_renders_ready_snapshot_to_mock_messages() -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import (
        build_rytm_snapshot_mutation_preview_report,
    )

    report = build_rytm_snapshot_mutation_preview_report(
        _promoted_snapshot_for_mutable_pads(),
        depth=1,
    )

    assert report.kit_name == "MUTABLE"
    assert report.slot == 6
    assert report.depth == 1
    assert report.plan_ready is True
    assert report.readiness_reason == "ready"
    assert report.mutation_event_count > 0
    assert report.mock_message_count == report.mutation_event_count
    assert report.planned_pads == (1, 2, 3)


def test_build_preview_report_reports_candidate_only_snapshot_block() -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import (
        build_rytm_snapshot_mutation_preview_report,
    )

    report = build_rytm_snapshot_mutation_preview_report(
        _candidate_only_snapshot(),
        depth=2,
    )

    assert report.plan_ready is False
    assert report.mutation_event_count == 0
    assert report.mock_message_count == 0
    assert report.planned_pads == ()
    assert "candidate-only" in report.readiness_reason


def test_format_preview_report_is_operator_facing_and_passive() -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import (
        format_rytm_snapshot_mutation_preview_report,
    )

    lines = format_rytm_snapshot_mutation_preview_report(
        _promoted_snapshot_for_mutable_pads(),
        depth=1,
    )

    assert lines[0] == "RytmRandomizer passive Rytm snapshot mutation preview"
    assert "Kit: MUTABLE" in lines
    assert "Slot: 6" in lines
    assert "Depth: 1" in lines
    assert "- Plan ready: True" in lines
    assert "- Readiness reason: ready" in lines
    assert "- Planned pads: 1, 2, 3" in lines
    assert "- passive/read-only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines
    assert "Source: rytm_randomizer.reports.rytm_snapshot_mutation_preview" in lines
    assert "In-memory only: True" in lines


def test_preview_cli_arg_parser_accepts_slot_and_depth_in_either_order() -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import _parse_cli_args

    defaulted = _parse_cli_args(["kit.syx"])
    selected = _parse_cli_args(["kit.syx", "--slot", "3", "--depth", "5"])
    reversed_order = _parse_cli_args(["kit.syx", "--depth", "2", "--slot", "4"])

    assert defaulted == {"sysex_path": Path("kit.syx"), "slot": 0, "depth": 1}
    assert selected == {"sysex_path": Path("kit.syx"), "slot": 3, "depth": 5}
    assert reversed_order == {"sysex_path": Path("kit.syx"), "slot": 4, "depth": 2}


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "requires <syx-path>"),
        (["kit.syx", "--slot"], "usage"),
        (["kit.syx", "--depth"], "usage"),
        (["kit.syx", "--list"], "usage"),
        (["kit.syx", "--bank", "1"], "usage"),
        (["kit.syx", "--slot", "not-int"], "--slot must be an integer"),
        (["kit.syx", "--depth", "not-int"], "--depth must be an integer"),
        (["kit.syx", "--slot", "-1"], "--slot must be >= 0"),
        (["kit.syx", "--depth", "-1"], "--depth must be in \\[0, 7\\]"),
        (["kit.syx", "--depth", "8"], "--depth must be in \\[0, 7\\]"),
    ],
)
def test_preview_cli_arg_parser_rejects_invalid_args(
    argv: list[str],
    message: str,
) -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_preview_cli_error_formatter_is_operator_facing() -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import _format_cli_error

    assert _format_cli_error(ValueError("bad depth")) == "Error: bad depth"


def test_preview_cli_handler_reads_requested_slot_and_reports_plan(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from conftest import rytm_real_layout_kit_payload

    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import _handle_cli_report

    first_payload = rytm_real_layout_kit_payload(name=b"FIRST")
    second_payload = rytm_real_layout_kit_payload(name=b"SECOND")
    path = tmp_path / "bank.syx"
    path.write_bytes(_framed_sysex(first_payload) + _framed_sysex(second_payload))

    rc = _handle_cli_report(sysex_path=path, slot=1, depth=2)

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Rytm snapshot mutation preview" in captured.out
    assert "Kit: SECOND" in captured.out
    assert "Slot: 1" in captured.out
    assert "Depth: 2" in captured.out
    assert "- Plan ready: False" in captured.out
    assert "- Mock messages: 0" in captured.out
    assert "candidate-only" in captured.out
    assert captured.err == ""


def test_preview_cli_handler_reports_expected_decode_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.reports.rytm_snapshot_mutation_preview import _handle_cli_report

    rc = _handle_cli_report(sysex_path=tmp_path / "missing.syx", slot=0, depth=1)

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err
