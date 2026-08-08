"""Operator tests for passive AL16 Rytm mapping evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import (
    ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
    Al16RytmMappingTestInputs,
    write_al16_rytm_mapping_test_inputs,
)
from rytm_randomizer.data.al16_rytm import AL16_RYTM_MAPPING_GAP_PATHS
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_RAW_SIZE,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
    analog_rytm_track_sound_offset,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    encode_analog_rytm_saved_kit_frame,
)

pytestmark = pytest.mark.fast

_RECIPE = {
    "tracks": {
        "1": {"machine": "bd_classic"},
        "3": {"machine": "rs_classic"},
        "6": {"machine": "xt_classic"},
        "9": {"machine": "ch_basic"},
    }
}


def _write_inputs(tmp_path: Path) -> Al16RytmMappingTestInputs:
    baseline = bytes(RYTM_KIT_RAW_SIZE)
    configured = bytearray(baseline)
    configured[analog_rytm_track_sound_offset(1, RYTM_SOUND_MACHINE_TYPE_OFFSET)] = 1
    reference_frame = encode_analog_rytm_saved_kit_frame(
        header=ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
        unpacked=baseline,
    )
    configured_frame = encode_analog_rytm_saved_kit_frame(
        header=ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
        unpacked=bytes(configured),
    )
    recipe_payload = json.dumps(_RECIPE, sort_keys=True).encode("utf-8")
    return write_al16_rytm_mapping_test_inputs(
        tmp_path,
        reference_frame=reference_frame,
        configured_frame=configured_frame,
        recipe=_RECIPE,
        recipe_payload=recipe_payload,
        semantic_paths=AL16_RYTM_MAPPING_GAP_PATHS,
        requested_values={"tracks.1.machine": "BD Classic"},
    )


def test_registered_help_states_passive_boundary(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    assert main(["al16-rytm-mapping-evidence", "--help"]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    assert "review_required" in captured.out
    assert "no MIDI port enumeration or opening" in captured.out


def test_registered_command_writes_review_only_report(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    inputs = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    args = [
        "al16-rytm-mapping-evidence",
        "--reference",
        str(inputs.reference_path),
        "--configured",
        str(inputs.configured_path),
        "--recipe",
        str(inputs.recipe_path),
        "--gap-manifest",
        str(inputs.manifest_path),
        "--expected-gap-manifest-sha256",
        inputs.manifest_sha256,
        "--report",
        str(report_path),
    ]

    assert main(args) == 0
    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert captured.err == ""
    assert "mapping_gaps: 18" in captured.out
    assert "candidate_locations_changed: 1" in captured.out
    assert "changed_header_indices: 0" in captured.out
    assert "promotion_status: review_required" in captured.out
    assert "midi_ports_opened: 0" in captured.out
    assert report["promotion_status"] == "review_required"
    assert report["schema_version"] == 1
    assert report["provenance"]["recipe_artifact"] == "recipe.yaml"
    observations = {
        observation["semantic_path"]: observation
        for observation in report["candidate_observations"]
    }
    assert observations["tracks.1.machine"]["requested_semantic_value"] == "BD Classic"
    assert str(tmp_path) not in captured.out

    assert main(args) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [overwrite_refused]" in captured.err


def test_command_rejects_colliding_path_roles_before_source_read(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure_cli as cli

    inputs = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    analyzer_called = False

    def forbidden_analyzer(**_kwargs: object) -> object:
        nonlocal analyzer_called
        analyzer_called = True
        raise AssertionError("source analyzer must not run for colliding path roles")

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", forbidden_analyzer)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.reference_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=report_path,
        )
        == 2
    )
    captured = capsys.readouterr()
    assert analyzer_called is False
    assert captured.out == ""
    assert "Error [validation]" in captured.err
    assert str(tmp_path) not in captured.err
    assert not report_path.exists()


@pytest.mark.parametrize(
    ("args", "message"),
    [
        ([], "--reference is required"),
        (["--reference"], "--reference requires a value"),
        (
            [
                "--reference",
                "reference.syx",
                "--configured",
                "configured.syx",
                "--recipe",
                "recipe.yaml",
                "--gap-manifest",
                "manifest.json",
                "--report",
                "report.json",
            ],
            "--expected-gap-manifest-sha256 is required",
        ),
        (["--unknown"], "unknown option"),
        (
            ["--reference", "one.syx", "--reference", "two.syx"],
            "--reference may be supplied only once",
        ),
        (
            [
                "--expected-gap-manifest-sha256",
                "a" * 64,
                "--expected-gap-manifest-sha256",
                "b" * 64,
            ],
            "--expected-gap-manifest-sha256 may be supplied only once",
        ),
    ],
)
def test_parser_rejects_invalid_arguments(args: list[str], message: str) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure_cli import (
        parse_al16_rytm_mapping_evidence_args,
    )

    with pytest.raises(ValueError, match=message):
        parse_al16_rytm_mapping_evidence_args(args)


def test_registered_command_formats_invalid_input(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cli import main

    secret = "--secret=C:\\private\\evidence.syx"
    assert main(["al16-rytm-mapping-evidence", secret]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [invalid_input]: unknown option" in captured.err
    assert secret not in captured.err


def test_command_rejects_malformed_gap_manifest(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure_cli import (
        handle_al16_rytm_mapping_evidence,
    )

    inputs = _write_inputs(tmp_path)
    manifest_payload = json.loads(inputs.manifest_path.read_text(encoding="utf-8"))
    manifest_payload["critical_mapping_gaps"] = []
    manifest_bytes = json.dumps(manifest_payload).encode("utf-8")
    inputs.manifest_path.write_bytes(manifest_bytes)
    manifest_sha256 = hashlib.sha256(manifest_bytes).hexdigest()
    report_path = tmp_path / "mapping-evidence.json"

    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=manifest_sha256,
            report_path=report_path,
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [validation]" in captured.err
    assert not report_path.exists()


def test_command_rejects_non_object_recipe(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure_cli import (
        handle_al16_rytm_mapping_evidence,
    )

    inputs = _write_inputs(tmp_path)
    inputs.recipe_path.write_text("[]", encoding="utf-8")
    report_path = tmp_path / "mapping-evidence.json"

    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=report_path,
        )
        == 2
    )
    captured = capsys.readouterr()
    assert "Error [validation]" in captured.err
    assert not report_path.exists()


def test_command_rejects_unsafe_path_before_reading_inputs(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure_cli as cli

    inputs = _write_inputs(tmp_path)

    def unexpected_analysis(**_kwargs: object) -> None:
        pytest.fail("input analysis must not begin before path validation")

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", unexpected_analysis)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=tmp_path / "unsafe\nreference.syx",
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=tmp_path / "mapping-evidence.json",
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [validation]" in captured.err
    assert str(tmp_path) not in captured.err
    assert inputs.reference_path.exists()


def test_command_handles_operator_interrupt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure_cli as cli

    inputs = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"

    def interrupt(**_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", interrupt)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=report_path,
        )
        == 130
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [interrupted]" in captured.err
    assert not report_path.exists()


def test_command_records_success_and_validation_metrics(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from rytm_randomizer.cockpit.export.al16_rytm_mapping_closure_cli import (
        handle_al16_rytm_mapping_evidence,
    )
    from rytm_randomizer.observability.metrics import get_metrics

    inputs = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    metrics = get_metrics()
    initial_count = metrics.export_count
    initial_overwrite_errors = metrics.export_errors_by_code["overwrite_refused"]
    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=report_path,
        )
        == 0
    )
    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=inputs.reference_path,
            configured_path=inputs.configured_path,
            recipe_path=inputs.recipe_path,
            gap_manifest_path=inputs.manifest_path,
            expected_gap_manifest_sha256=inputs.manifest_sha256,
            report_path=report_path,
        )
        == 2
    )
    capsys.readouterr()

    assert metrics.export_count == initial_count + 2
    assert metrics.export_errors_by_code["overwrite_refused"] == initial_overwrite_errors + 1
