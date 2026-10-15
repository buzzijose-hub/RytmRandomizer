"""Bounded read-only file/report checks, with explicitly synthetic inputs."""

from __future__ import annotations

import json
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.reports.analog_four_working_kit_comparison import (
    AnalogFourWorkingKitFiles,
    build_analog_four_working_kit_comparison_report,
    to_analog_four_working_kit_comparison_json,
)

pytestmark = pytest.mark.fast


def _inputs(root: Path) -> AnalogFourWorkingKitFiles:
    indexed = analog_four_saved_kit_frame(unpacked_overrides={129: 1})
    working = bytearray(analog_four_saved_kit_frame(unpacked_overrides={129: 2}))
    working[6] = 88
    saved = analog_four_saved_kit_frame(unpacked_overrides={129: 2})
    paths = tuple(root / f"stage{number}.syx" for number in range(6))
    for path, raw in zip(
        paths, (indexed, indexed, bytes(working), bytes(working), saved, indexed), strict=True
    ):
        path.write_bytes(raw)
    return AnalogFourWorkingKitFiles(*paths)


def test_file_report_json_retains_whole_inspection_and_preserves_originals(tmp_path: Path) -> None:
    files = _inputs(tmp_path)
    before = {path: sha256(path.read_bytes()).hexdigest() for path in files.ordered()}
    report = build_analog_four_working_kit_comparison_report(
        files, track=1, evidence_origin="synthetic", baseline_label="0.00", changed_label="0.00"
    )
    data = json.loads(to_analog_four_working_kit_comparison_json(report))
    assert data["evidence_origin"] == "synthetic"
    assert data["frames"][2]["f1"][0] == {
        "track": 1,
        "body_offset": 128,
        "native": 2,
        "screen_label": "0.00",
    }
    assert data["frames"][2]["source_kind"] == "working_kit_ram"
    assert data["frames"][2]["protocol_version"] == [1, 1]
    assert data["frames"][2]["sound_storage_versions"] == [6, 6, 6, 6]
    assert data["differences"][1]["body"] == [
        {"offset": 129, "before": 1, "after": 2, "classification": "verified_f1"}
    ]
    assert data["checks"]["selected_b_differs_from_u"] is True
    for name in (
        "hardware_validated",
        "query_authority",
        "send_authority",
        "restore_authority",
        "complete_kit_claimed",
        "current_baseline_coherence_established",
    ):
        assert data[name] is False
    assert data["installed_firmware"] is None
    assert {path: sha256(path.read_bytes()).hexdigest() for path in files.ordered()} == before
    assert len(tuple(tmp_path.iterdir())) == 6


def test_missing_file_failure_names_stage_and_preserves_other_inputs(tmp_path: Path) -> None:
    files = _inputs(tmp_path)
    before = {path: path.read_bytes() for path in files.ordered()}
    broken = replace(files, working_first=tmp_path / "missing.syx")
    with pytest.raises(ValueError, match="working_first.*missing or unreadable"):
        build_analog_four_working_kit_comparison_report(
            broken, track=1, evidence_origin="synthetic"
        )
    assert {path: path.read_bytes() for path in files.ordered()} == before


@pytest.mark.parametrize("size", [0, 2769, 2771, 10000])
def test_incompatible_file_extent_is_refused_without_modification(
    tmp_path: Path, size: int
) -> None:
    files = _inputs(tmp_path)
    invalid = tmp_path / "invalid.syx"
    raw = bytes(size)
    invalid.write_bytes(raw)
    with pytest.raises(ValueError, match="working_repeat.*one complete"):
        build_analog_four_working_kit_comparison_report(
            replace(files, working_repeat=invalid), track=1, evidence_origin="synthetic"
        )
    assert invalid.read_bytes() == raw


def test_semantic_file_failure_preserves_every_supplied_file(tmp_path: Path) -> None:
    files = _inputs(tmp_path)
    files.post_save_indexed.write_bytes(analog_four_saved_kit_frame(unpacked_overrides={32: 0}))
    before = {path: path.read_bytes() for path in files.ordered()}
    with pytest.raises(ValueError, match="post_save_indexed.*invalid"):
        build_analog_four_working_kit_comparison_report(
            files, track=1, evidence_origin="operator_supplied_files"
        )
    assert {path: path.read_bytes() for path in files.ordered()} == before
