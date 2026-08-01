"""Passive filesystem tests for the RUSH16 batch generator."""

from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from rytm_randomizer.devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC
from rytm_randomizer.snapshot import encode_elektron_u14, pack_elektron_7bit

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
_TOOL_PATH = PROJECT_ROOT / "scripts" / "rush16_anchor_audition.py"
_TOOL_SPEC = importlib.util.spec_from_file_location("rush16_anchor_audition_script", _TOOL_PATH)
if _TOOL_SPEC is None or _TOOL_SPEC.loader is None:  # pragma: no cover - import bootstrap
    raise RuntimeError(f"could not load RUSH16 generator: {_TOOL_PATH}")
tool = importlib.util.module_from_spec(_TOOL_SPEC)
_TOOL_SPEC.loader.exec_module(tool)


def _synthetic_frame(codec: object) -> bytes:
    spec = codec.spec
    unpacked = bytearray(spec.unpacked_size)
    unpacked[: len(spec.required_unpacked_prefix)] = spec.required_unpacked_prefix
    packed = pack_elektron_7bit(bytes(unpacked))
    header = spec.required_header_prefix.ljust(spec.header_size_without_f0, b"\x00")
    checksum = sum(packed[spec.checksum_packed_start :]) & 0x3FFF
    encoded_length = len(packed) + spec.length_adjustment
    return (
        b"\xf0"
        + header
        + packed
        + encode_elektron_u14(checksum)
        + encode_elektron_u14(encoded_length)
        + b"\xf7"
    )


def _copy_inputs(destination: Path) -> None:
    for relative in (
        "specs/RUSH01_RYTM.yaml",
        "specs/RUSH01_A4.yaml",
        "output/RUSH01_mapping_gaps.md",
        "output/RUSH01_RYTM_mapping_status.json",
        "output/RUSH01_A4_mapping_status.json",
    ):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PROJECT_ROOT / relative, target)
    reference = destination / "reference"
    reference.mkdir(parents=True)
    (reference / "RYTM_Test1_Init_Kit.syx").write_bytes(_synthetic_frame(ANALOG_RYTM_KIT_CODEC))
    (reference / "A4_Test1_Init_Kit.syx").write_bytes(_synthetic_frame(ANALOG_FOUR_KIT_CODEC))


def test_tool_generates_and_checks_without_importing_or_using_midi(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path)
    imported_before = set(sys.modules)
    arguments = ("--project-root", str(tmp_path), "--sync-specs")
    assert tool.run(arguments, stdout=sys.stdout, stderr=sys.stderr) == 0
    first = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes()
        for path in sorted((tmp_path / "specs" / "rush16").glob("*.yaml"))
    }
    first.update(
        {
            path.relative_to(tmp_path).as_posix(): path.read_bytes()
            for path in sorted(
                (tmp_path / "output" / "local" / "RUSH16_ANCHOR_AUDITION_001").rglob("*")
            )
            if path.is_file()
        }
    )
    assert len(list((tmp_path / "specs" / "rush16").glob("*.yaml"))) == 9
    assert (
        tool.run(("--project-root", str(tmp_path), "--check"), stdout=sys.stdout, stderr=sys.stderr)
        == 0
    )
    second = {name: (tmp_path / name).read_bytes() for name in first}
    assert first == second
    assert not list((tmp_path / "output" / "local").rglob("*.syx"))
    local_root = tmp_path / "output" / "local" / "RUSH16_ANCHOR_AUDITION_001"
    for directory in (
        "calibration",
        "captured_dumps",
        "final_sysex",
        "hardware_receipts",
        "recording_runbook",
        "session_checkpoints",
    ):
        assert (local_root / directory).is_dir()
    rytm_catalog = json.loads(
        (local_root / "calibration" / "RUSH16_RYTM_CALIBRATION_CATALOG.json").read_text(
            encoding="utf-8"
        )
    )
    a4_catalog = json.loads(
        (local_root / "calibration" / "RUSH16_A4_CALIBRATION_CATALOG.json").read_text(
            encoding="utf-8"
        )
    )
    assert rytm_catalog["required_observations"] == 67
    assert a4_catalog["required_observations"] == 896
    for catalog in (rytm_catalog, a4_catalog):
        assert catalog["output_port"] is None
        assert catalog["input_port"] is None
        assert catalog["channels"] is None
        assert catalog["configuration_ready"] is False
    calibration_runbook = (local_root / "calibration" / "RUSH16_CALIBRATION_RUNBOOK.md").read_text(
        encoding="utf-8"
    )
    assert "--arm --rush16-calibrate" in calibration_runbook
    assert "--rush16-checkpoint" in calibration_runbook
    assert not (local_root / "recording_runbook" / "RUSH16_RECORDING_RUNBOOK.md").exists()
    recording_runbook = tool._format_recording_runbook()
    assert "145 BPM" in recording_runbook
    assert recording_runbook.count(" dry") == 12
    assert "mido" not in set(sys.modules) - imported_before
    assert "rtmidi" not in set(sys.modules) - imported_before
    output = capsys.readouterr().out
    assert "8 device artifacts; 8 blocked; 0 final SysEx files" in output
    assert "MIDI backend opened: false" in output
    assert "MIDI port opened: false" in output
    assert "MIDI or SysEx transmitted: false" in output


def test_tool_check_rejects_stale_specs_and_local_artifacts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path)
    assert (
        tool.run(
            ("--project-root", str(tmp_path), "--sync-specs"),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        == 0
    )
    spec = tmp_path / "specs" / "rush16" / "01_DRY_AUTHORITY_RYTM.yaml"
    spec.write_text("stale\n", encoding="utf-8")
    assert (
        tool.run(("--project-root", str(tmp_path), "--check"), stdout=sys.stdout, stderr=sys.stderr)
        == 1
    )
    assert "semantic specs are stale" in capsys.readouterr().err

    shutil.copyfile(PROJECT_ROOT / "specs" / "rush16" / spec.name, spec)
    report = tmp_path / "output" / "local" / "RUSH16_ANCHOR_AUDITION_001" / "BUILD_REPORT.md"
    report.write_text("stale\n", encoding="utf-8")
    assert (
        tool.run(("--project-root", str(tmp_path), "--check"), stdout=sys.stdout, stderr=sys.stderr)
        == 1
    )
    assert "local build artifacts are stale" in capsys.readouterr().err


def test_tool_requires_sync_and_reports_missing_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _copy_inputs(tmp_path)
    assert tool.run(("--project-root", str(tmp_path)), stdout=sys.stdout, stderr=sys.stderr) == 2
    assert "rerun with --sync-specs" in capsys.readouterr().err
    assert (
        tool.run(
            ("--project-root", str(tmp_path / "missing"), "--sync-specs"),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        == 2
    )
    assert "required file does not exist" in capsys.readouterr().err


def test_tool_helpers_preserve_placeholder_configuration_as_unconfigured() -> None:
    config = {
        "rytm": {
            "output_port": "<REPLACE_WITH_EXACT_PORT>",
            "tracks": {"BD": "<CONFIGURE>"},
        }
    }
    assert tool._device_config_or_none(config, "rytm") is None
    assert not tool._capture_input_configured(config, "rytm")
    assert tool._device_config_or_none(None, "rytm") is None
    assert tool._display_path(PROJECT_ROOT / "specs", PROJECT_ROOT) == "specs"
    assert tool._display_path(Path("Z:/outside"), PROJECT_ROOT) == "Z:\\outside"


def test_tool_helpers_cover_config_and_input_validation(tmp_path: Path) -> None:
    tracks = {
        track: index + 1
        for index, track in enumerate(
            ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB")
        )
    }
    config = {
        "rytm": {
            "output_port": "Exact Output",
            "input_port": "Exact Input",
            "tracks": tracks,
        }
    }
    parsed = tool._device_config_or_none(config, "rytm")
    assert parsed is not None
    assert parsed.output_port == "Exact Output"
    assert tool._capture_input_configured(config, "rytm")
    assert not tool._capture_input_configured({"rytm": []}, "rytm")
    assert not tool._device_config_has_placeholders([], "rytm")
    assert not tool._device_config_has_placeholders({"rytm": []}, "rytm")
    assert not tool._device_config_has_placeholders(
        {"rytm": {"output_port": "Exact Output", "tracks": []}}, "rytm"
    )
    assert tool._device_config_has_placeholders(
        {"rytm": {"output_port": "Exact Output", "tracks": {"BD": "<CONFIGURE>"}}},
        "rytm",
    )
    assert not tool._device_config_has_placeholders(config, "rytm")
    with pytest.raises(ValueError, match="required file does not exist"):
        tool._read_bytes(tmp_path / "missing.syx")
    with pytest.raises(ValueError, match="families must be a sequence"):
        tool._format_calibration_runbook(
            config_path="config.yaml",
            catalogs={"rytm": {"families": None}, "a4": {"families": []}},
        )


def test_tool_reuses_checkpoints_and_defers_recording_runbook_until_final(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _copy_inputs(tmp_path)
    assert (
        tool.run(
            ("--project-root", str(tmp_path), "--sync-specs"),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        == 0
    )
    checkpoint_root = (
        tmp_path / "output" / "local" / "RUSH16_ANCHOR_AUDITION_001" / "session_checkpoints"
    )
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    (checkpoint_root / "rytm.checkpoint.json").write_text("{}\n", encoding="utf-8")
    promoted: list[str] = []

    def passthrough_promotion(plan: object, *, spec_filename: str, checkpoint: object) -> object:
        assert checkpoint == {}
        promoted.append(spec_filename)
        return plan

    original_build_entry = tool.build_rush16_build_entry

    def final_build_entry(**kwargs: object):
        return replace(original_build_entry(**kwargs), final_sysex_generated=True)

    monkeypatch.setattr(tool, "apply_rush16_calibration_promotions", passthrough_promotion)
    monkeypatch.setattr(tool, "build_rush16_build_entry", final_build_entry)
    absolute_config = tmp_path / "missing-config.yaml"
    assert (
        tool.run(
            (
                "--project-root",
                str(tmp_path),
                "--config",
                str(absolute_config),
            ),
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        == 0
    )
    assert len(promoted) == 4
    assert (
        tmp_path
        / "output"
        / "local"
        / "RUSH16_ANCHOR_AUDITION_001"
        / "recording_runbook"
        / "RUSH16_RECORDING_RUNBOOK.md"
    ).is_file()


def test_tool_main_and_parser_are_passive(monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[tuple[str, ...]] = []

    def fake_run(argv: tuple[str, ...], *, stdout: object, stderr: object) -> int:
        observed.append(argv)
        return 9

    monkeypatch.setattr(tool, "run", fake_run)
    assert tool.main(["--check"]) == 9
    assert observed == [("--check",)]
    assert "--apply" not in tool.build_parser().format_help()
