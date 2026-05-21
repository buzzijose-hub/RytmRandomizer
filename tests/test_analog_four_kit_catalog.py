import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


def _pack_elektron_7bit(unpacked: bytes) -> bytes:
    packed = bytearray()
    for cursor in range(0, len(unpacked), 7):
        group = unpacked[cursor : cursor + 7]
        header = 0
        data = bytearray()
        for bit_index, byte in enumerate(group):
            header |= ((byte >> 7) & 0x01) << bit_index
            data.append(byte & 0x7F)
        packed.append(header)
        packed.extend(data)
    return bytes(packed)


def _framed_candidate_payload(name: bytes) -> bytes:
    payload = bytes([0x00, 0x20, 0x3C, 0x07]) + name[:16].ljust(16, b"\x00")
    return bytes([0xF0]) + payload + bytes([0xF7])


def _framed_saved_kit_payload(name: bytes) -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_FAMILY_BYTE,
        A4_KIT_NAME_LENGTH,
        A4_KIT_NAME_OFFSET,
        A4_KIT_OBJECT_BYTE,
    )
    from rytm_randomizer.snapshot.envelope import ELEKTRON_MFR_ID

    unpacked = bytearray(A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH + 8)
    unpacked[0] = A4_KIT_OBJECT_BYTE
    unpacked[1] = 0x01
    unpacked[2] = 0x01
    unpacked[A4_KIT_NAME_OFFSET : A4_KIT_NAME_OFFSET + A4_KIT_NAME_LENGTH] = name[
        :A4_KIT_NAME_LENGTH
    ].ljust(A4_KIT_NAME_LENGTH, b"\x00")
    payload = ELEKTRON_MFR_ID + bytes([A4_FAMILY_BYTE]) + _pack_elektron_7bit(bytes(unpacked))
    return bytes([0xF0]) + payload + bytes([0xF7])


def _catalog_file(tmp_path: Path) -> Path:
    path = tmp_path / "a4-kits.syx"
    path.write_bytes(
        _framed_saved_kit_payload(b"KIT ONE")
        + _framed_candidate_payload(b"CANDIDATE")
        + _framed_saved_kit_payload(b"KIT TWO")
    )
    return path


def test_analog_four_kit_catalog_builds_saved_and_candidate_summary(tmp_path: Path):
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_SNAPSHOT_LAYOUT_CANDIDATE,
        A4_SNAPSHOT_LAYOUT_SAVED_KIT,
    )
    from rytm_randomizer.reports.analog_four_kit_catalog import (
        build_analog_four_kit_catalog_report,
    )

    report = build_analog_four_kit_catalog_report(_catalog_file(tmp_path))

    assert report.supported_kit_count == 3
    assert report.saved_kit_count == 2
    assert report.candidate_count == 1
    assert report.promoted_offset_count == 0
    assert report.mutation_ready_count == 0
    assert [entry.slot for entry in report.entries] == [0, 1, 2]
    assert [entry.kit_name for entry in report.entries] == [
        "KIT ONE",
        "CANDIDATE",
        "KIT TWO",
    ]
    assert report.entries[0].snapshot_layout == A4_SNAPSHOT_LAYOUT_SAVED_KIT
    assert report.entries[1].snapshot_layout == A4_SNAPSHOT_LAYOUT_CANDIDATE
    assert report.entries[0].raw_byte_count > 0
    assert report.entries[0].unpacked_byte_count > 0
    assert report.entries[0].offset_status == "candidate-only"
    assert report.entries[0].mutation_ready is False
    assert report.entries[0].readiness_reason == (
        "saved-kit decoded; offset promotion required before mutation preview"
    )


def test_analog_four_kit_catalog_text_is_operator_facing_and_limited(tmp_path: Path):
    from rytm_randomizer.reports.analog_four_kit_catalog import (
        build_analog_four_kit_catalog_report,
        format_analog_four_kit_catalog_report,
    )

    report = build_analog_four_kit_catalog_report(_catalog_file(tmp_path))
    lines = format_analog_four_kit_catalog_report(report, display_limit=2)
    text = "\n".join(lines)

    assert lines[0] == "RytmRandomizer passive Analog Four kit catalog"
    assert "Supported kits: 3" in lines
    assert "Saved-kit snapshots: 2" in lines
    assert "Candidate snapshots: 1" in lines
    assert "Mutation-ready kits: 0" in lines
    assert "Shown kits: 2" in lines
    assert "Truncated kits: 1" in lines
    assert "- Slot 0 | KIT ONE | layout saved_kit | offsets candidate-only" in text
    assert "- Slot 1 | CANDIDATE | layout candidate | offsets candidate-only" in text
    assert "KIT TWO" not in text
    assert "- SysEx decode only" in lines
    assert "- no MIDI sending" in lines
    assert "- no port opening" in lines


def test_analog_four_kit_catalog_formats_empty_report_and_rejects_negative_limit():
    from rytm_randomizer.reports.analog_four_kit_catalog import (
        AnalogFourKitCatalogReport,
        format_analog_four_kit_catalog_report,
    )

    report = AnalogFourKitCatalogReport(
        sysex_path=Path("empty.syx"),
        supported_kit_count=0,
        saved_kit_count=0,
        candidate_count=0,
        promoted_offset_count=0,
        mutation_ready_count=0,
        entries=(),
    )

    lines = format_analog_four_kit_catalog_report(report)

    assert "Shown kits: 0" in lines
    assert "Truncated kits: 0" in lines
    assert "- none" in lines
    with pytest.raises(ValueError, match="display_limit must be >= 0"):
        format_analog_four_kit_catalog_report(report, display_limit=-1)


def test_analog_four_kit_catalog_entry_marks_promoted_offsets_ready():
    from rytm_randomizer.devices.strategies import AnalogFourKitSnapshot
    from rytm_randomizer.reports.analog_four_kit_catalog import _entry_from_snapshot

    entry = _entry_from_snapshot(
        AnalogFourKitSnapshot(
            slot=9,
            kit_name="PROMOTED",
            raw=b"\x00\x20\x3c\x07PROMOTED",
            offsets_promoted=True,
            unpacked=b"\x52\x01\x01",
        )
    )

    assert entry.offset_status == "promoted"
    assert entry.mutation_ready is True
    assert entry.readiness_reason == "ready for promoted-offset planning"


def test_analog_four_kit_catalog_json_is_deterministic(tmp_path: Path):
    from rytm_randomizer.reports.analog_four_kit_catalog import (
        build_analog_four_kit_catalog_report,
        to_analog_four_kit_catalog_json,
    )

    report = build_analog_four_kit_catalog_report(_catalog_file(tmp_path))
    payload = to_analog_four_kit_catalog_json(report, display_limit=1)

    assert payload["supported_kit_count"] == 3
    assert payload["shown_count"] == 1
    assert payload["truncated_count"] == 2
    assert payload["entries"] == [
        {
            "slot": 0,
            "kit_name": "KIT ONE",
            "snapshot_layout": "saved_kit",
            "offset_status": "candidate-only",
            "offsets_promoted": False,
            "mutation_ready": False,
            "readiness_reason": (
                "saved-kit decoded; offset promotion required before mutation preview"
            ),
            "raw_byte_count": report.entries[0].raw_byte_count,
            "unpacked_byte_count": report.entries[0].unpacked_byte_count,
        }
    ]
    assert payload["safety"][0] == "passive/read-only"


def test_analog_four_kit_catalog_cli_parser_accepts_limit_and_json():
    from rytm_randomizer.reports.analog_four_kit_catalog import _parse_cli_args

    assert _parse_cli_args(["a4.syx"]) == {
        "sysex_path": Path("a4.syx"),
        "display_limit": None,
        "json_output": False,
    }
    assert _parse_cli_args(["a4.syx", "--limit", "0", "--json"]) == {
        "sysex_path": Path("a4.syx"),
        "display_limit": 0,
        "json_output": True,
    }


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        ([], "usage"),
        (["a4.syx", "--limit"], "usage"),
        (["a4.syx", "--unknown", "1"], "usage"),
        (["a4.syx", "--limit", "nope"], "--limit must be an integer"),
        (["a4.syx", "--limit", "-1"], "--limit must be >= 0"),
    ],
)
def test_analog_four_kit_catalog_cli_parser_rejects_bad_args(argv, message):
    from rytm_randomizer.reports.analog_four_kit_catalog import _parse_cli_args

    with pytest.raises(ValueError, match=message):
        _parse_cli_args(argv)


def test_analog_four_kit_catalog_cli_handler_reports_json(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_kit_catalog import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=_catalog_file(tmp_path),
        display_limit=1,
        json_output=True,
    )

    captured = capsys.readouterr()
    parsed = json.loads(captured.out)
    assert rc == 0
    assert parsed["entries"][0]["kit_name"] == "KIT ONE"
    assert parsed["shown_count"] == 1
    assert parsed["truncated_count"] == 2
    assert captured.err == ""


def test_analog_four_kit_catalog_cli_handler_reports_text(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_kit_catalog import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=_catalog_file(tmp_path),
        display_limit=1,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 0
    assert "RytmRandomizer passive Analog Four kit catalog" in captured.out
    assert "Shown kits: 1" in captured.out
    assert "KIT ONE" in captured.out
    assert "KIT TWO" not in captured.out
    assert captured.err == ""


def test_analog_four_kit_catalog_cli_handler_reports_errors(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
):
    from rytm_randomizer.reports.analog_four_kit_catalog import _handle_cli_report

    rc = _handle_cli_report(
        sysex_path=tmp_path / "missing.syx",
        display_limit=None,
        json_output=False,
    )

    captured = capsys.readouterr()
    assert rc == 2
    assert captured.out == ""
    assert "SysEx file does not exist" in captured.err
    assert "Traceback" not in captured.err


def test_analog_four_kit_catalog_cli_error_formatter_is_plain_error():
    from rytm_randomizer.reports.analog_four_kit_catalog import _format_cli_error

    assert _format_cli_error(ValueError("bad catalog")) == "Error: bad catalog"
