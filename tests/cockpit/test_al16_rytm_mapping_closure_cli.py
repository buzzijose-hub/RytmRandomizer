"""Operator tests for passive AL16 Rytm mapping evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from conftest import ANALOG_RYTM_SAVED_KIT_TEST_HEADER
from rytm_randomizer.cockpit.export.al16_rytm_kit import (
    deterministic_recipe_identifier,
)
from rytm_randomizer.data.analog_rytm_kit_layout import RYTM_KIT_RAW_SIZE
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
_GAP_PATHS = (
    "destination_slot",
    "tracks.1.machine",
    "tracks.1.source.dec",
    "tracks.1.source.hld",
    "tracks.1.source.swd",
    "tracks.1.source.swt",
    "tracks.1.source.trn",
    "tracks.1.source.tun",
    "tracks.1.source.wav",
    "tracks.1.amp.vol",
    "tracks.3.machine",
    "tracks.3.amp.vol",
    "tracks.6.source.decay",
    "tracks.6.source.target_note",
    "tracks.6.amp.vol",
    "tracks.9.machine",
    "tracks.9.source.decay",
    "tracks.9.amp.vol",
)


def _write_inputs(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    baseline = bytes(RYTM_KIT_RAW_SIZE)
    configured = bytearray(baseline)
    configured[170] = 1
    reference_path = tmp_path / "reference.syx"
    configured_path = tmp_path / "configured.syx"
    recipe_path = tmp_path / "recipe.yaml"
    manifest_path = tmp_path / "manifest.json"
    reference_frame = encode_analog_rytm_saved_kit_frame(
        header=ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
        unpacked=baseline,
    )
    reference_path.write_bytes(reference_frame)
    configured_path.write_bytes(
        encode_analog_rytm_saved_kit_frame(
            header=ANALOG_RYTM_SAVED_KIT_TEST_HEADER,
            unpacked=bytes(configured),
        )
    )
    recipe_payload = json.dumps(_RECIPE, sort_keys=True).encode("utf-8")
    recipe_path.write_bytes(recipe_payload)
    manifest_path.write_text(
        json.dumps(
            {
                "critical_mapping_gaps": [{"semantic_path": path} for path in _GAP_PATHS],
                "deterministic_recipe_identifier": deterministic_recipe_identifier(_RECIPE),
                "recipe_sha256": hashlib.sha256(recipe_payload).hexdigest(),
                "reference_sha256": hashlib.sha256(reference_frame).hexdigest(),
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return reference_path, configured_path, recipe_path, manifest_path


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

    reference, configured, recipe, manifest = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    args = [
        "al16-rytm-mapping-evidence",
        "--reference",
        str(reference),
        "--configured",
        str(configured),
        "--recipe",
        str(recipe),
        "--gap-manifest",
        str(manifest),
        "--report",
        str(report_path),
    ]

    assert main(args) == 0
    captured = capsys.readouterr()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert captured.err == ""
    assert "mapping_gaps: 18" in captured.out
    assert "candidate_locations_changed: 1" in captured.out
    assert "promotion_status: review_required" in captured.out
    assert "midi_ports_opened: 0" in captured.out
    assert report["promotion_status"] == "review_required"
    assert report["provenance"]["recipe_artifact"] == "recipe.yaml"
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

    reference, _configured, recipe, manifest = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    analyzer_called = False

    def forbidden_analyzer(**_kwargs: object) -> object:
        nonlocal analyzer_called
        analyzer_called = True
        raise AssertionError("source analyzer must not run for colliding path roles")

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", forbidden_analyzer)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=reference,
            recipe_path=recipe,
            gap_manifest_path=manifest,
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
        (["--unknown"], "unknown option"),
        (
            ["--reference", "one.syx", "--reference", "two.syx"],
            "--reference may be supplied only once",
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

    reference, configured, recipe, manifest = _write_inputs(tmp_path)
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    manifest_payload["critical_mapping_gaps"] = []
    manifest.write_text(json.dumps(manifest_payload), encoding="utf-8")
    report_path = tmp_path / "mapping-evidence.json"

    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
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

    reference, configured, recipe, manifest = _write_inputs(tmp_path)
    recipe.write_text("[]", encoding="utf-8")
    report_path = tmp_path / "mapping-evidence.json"

    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
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

    reference, configured, recipe, manifest = _write_inputs(tmp_path)

    def unexpected_analysis(**_kwargs: object) -> None:
        pytest.fail("input analysis must not begin before path validation")

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", unexpected_analysis)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=tmp_path / "unsafe\nreference.syx",
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
            report_path=tmp_path / "mapping-evidence.json",
        )
        == 2
    )
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error [validation]" in captured.err
    assert str(tmp_path) not in captured.err
    assert reference.exists()


def test_command_handles_operator_interrupt(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.cockpit.export import al16_rytm_mapping_closure_cli as cli

    reference, configured, recipe, manifest = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"

    def interrupt(**_kwargs: object) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "analyze_mapping_capture_files", interrupt)

    assert (
        cli.handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
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

    reference, configured, recipe, manifest = _write_inputs(tmp_path)
    report_path = tmp_path / "mapping-evidence.json"
    metrics = get_metrics()
    initial_count = metrics.export_count
    initial_overwrite_errors = metrics.export_errors_by_code["overwrite_refused"]
    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
            report_path=report_path,
        )
        == 0
    )
    assert (
        handle_al16_rytm_mapping_evidence(
            reference_path=reference,
            configured_path=configured,
            recipe_path=recipe,
            gap_manifest_path=manifest,
            report_path=report_path,
        )
        == 2
    )
    capsys.readouterr()

    assert metrics.export_count == initial_count + 2
    assert metrics.export_errors_by_code["overwrite_refused"] == initial_overwrite_errors + 1
