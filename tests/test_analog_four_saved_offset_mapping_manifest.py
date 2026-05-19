import json
import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def write_manifest(path: Path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_importing_saved_offset_mapping_manifest_is_passive_and_silent():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.analog_four.saved_offset_mapping_manifest; "
                "assert 'mido' not in sys.modules; "
                "assert 'rtmidi' not in sys.modules"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert result.stderr == ""


def test_saved_offset_mapping_manifest_report_accepts_verified_mappings(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        format_analog_four_saved_offset_mapping_manifest_report,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-verified-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                },
                {
                    "track": 2,
                    "relative_offset": 334,
                    "parameter_name": "Amp Pan",
                    "cc": 10,
                },
            ]
        },
    )

    manifest = load_analog_four_saved_offset_mapping_manifest(manifest_path)
    report = "\n".join(format_analog_four_saved_offset_mapping_manifest_report(manifest))

    assert manifest.ready is True
    assert "RytmRandomizer passive Analog Four Saved-Offset Mapping Manifest Report" in report
    assert "Ready: True" in report
    assert "Mapping count: 2" in report
    assert "Duplicate count: 0" in report
    assert "Track 1 / offset +120 / Filter 1 Frequency / CC18 / verified_cc_mapping" in report
    assert "Track 2 / offset +334 / Amp Pan / CC10 / verified_cc_mapping" in report
    assert "Runtime use:" in report
    assert (
        "analog-four-snapshot-mutation-plan-report "
        '"<a4-bank-or-project.syx>" --slot <1-128> --depth micro '
        f'--mapping-manifest "{manifest_path}"'
    ) in report
    assert (
        "dual-machine-live-snapshot-readiness-report "
        '"<rytm-bank-or-project.syx>" --slot <1-128> --depth micro '
        '--analog-four-path "<a4-bank-or-project.syx>" --analog-four-slot <1-128> '
        f'--analog-four-mapping-manifest "{manifest_path}"'
    ) in report
    assert (
        "dual-machine-guarded-send-dry-run-report "
        '"<rytm-bank-or-project.syx>" --slot <1-128> --depth micro '
        '--analog-four-path "<a4-bank-or-project.syx>" --analog-four-slot <1-128> '
        f'--analog-four-mapping-manifest "{manifest_path}"'
    ) in report
    assert "- no MIDI sending" in report


def test_ready_saved_offset_mapping_manifest_returns_ready_manifest(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        load_ready_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-ready-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                }
            ]
        },
    )

    manifest = load_ready_analog_four_saved_offset_mapping_manifest(manifest_path)

    assert manifest.ready is True
    assert manifest.reason == "verified_manifest_ready"
    assert manifest.mappings[0].parameter_name == "Filter 1 Frequency"


def test_saved_offset_mapping_manifest_blocks_duplicate_track_offsets(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        format_analog_four_saved_offset_mapping_manifest_report,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-duplicate-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                },
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 2 Frequency",
                    "cc": 19,
                },
            ]
        },
    )

    manifest = load_analog_four_saved_offset_mapping_manifest(manifest_path)
    report = "\n".join(format_analog_four_saved_offset_mapping_manifest_report(manifest))

    assert manifest.ready is False
    assert "Ready: False" in report
    assert "Reason: blocked_duplicate_track_offsets" in report
    assert "Duplicate count: 1" in report
    assert "- Track 1 / offset +120 appears 2 times" in report


def test_ready_saved_offset_mapping_manifest_rejects_duplicate_manifest(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        load_ready_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-duplicate-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                },
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 2 Frequency",
                    "cc": 19,
                },
            ]
        },
    )

    with pytest.raises(ValueError, match="mapping manifest not ready"):
        load_ready_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_reports_empty_manifest(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        format_analog_four_saved_offset_mapping_manifest_report,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-empty-mappings.json"
    write_manifest(manifest_path, {"mappings": []})

    manifest = load_analog_four_saved_offset_mapping_manifest(manifest_path)
    report = "\n".join(format_analog_four_saved_offset_mapping_manifest_report(manifest))

    assert manifest.ready is False
    assert "Reason: blocked_empty_manifest" in report
    assert "Mappings:\n- none" in report
    assert "Runtime use:" in report
    assert (
        "- blocked until manifest is ready; fix Reason before using it in send previews" in report
    )
    assert "dual-machine-guarded-send-dry-run-report" not in report


def test_saved_offset_mapping_manifest_rejects_non_object_payload(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        AnalogFourSavedOffsetMappingManifestError,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-non-object-mappings.json"
    write_manifest(manifest_path, [])

    with pytest.raises(AnalogFourSavedOffsetMappingManifestError, match="JSON object"):
        load_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_rejects_missing_mappings_list(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        AnalogFourSavedOffsetMappingManifestError,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-missing-list-mappings.json"
    write_manifest(manifest_path, {"mappings": {}})

    with pytest.raises(AnalogFourSavedOffsetMappingManifestError, match="mappings must be a list"):
        load_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_rejects_invalid_entries(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        AnalogFourSavedOffsetMappingManifestError,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-invalid-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 5,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                }
            ]
        },
    )

    with pytest.raises(AnalogFourSavedOffsetMappingManifestError, match="entry 1"):
        load_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_rejects_non_object_entries(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        AnalogFourSavedOffsetMappingManifestError,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-non-object-entry-mappings.json"
    write_manifest(manifest_path, {"mappings": ["bad"]})

    with pytest.raises(
        AnalogFourSavedOffsetMappingManifestError, match="entry 1 must be an object"
    ):
        load_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_rejects_missing_entry_keys(tmp_path):
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        AnalogFourSavedOffsetMappingManifestError,
        load_analog_four_saved_offset_mapping_manifest,
    )

    manifest_path = tmp_path / "a4-missing-key-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                }
            ]
        },
    )

    with pytest.raises(AnalogFourSavedOffsetMappingManifestError, match="entry 1 is missing cc"):
        load_analog_four_saved_offset_mapping_manifest(manifest_path)


def test_saved_offset_mapping_manifest_error_report_is_passive():
    from rytm_randomizer.analog_four.saved_offset_mapping_manifest import (
        format_analog_four_saved_offset_mapping_manifest_error,
    )

    report = "\n".join(format_analog_four_saved_offset_mapping_manifest_error("bad manifest"))

    assert "Found: False" in report
    assert "bad manifest" in report
    assert "- no MIDI sending" in report
    assert "- no command execution" in report


def test_saved_offset_mapping_manifest_cli_prints_report(tmp_path):
    manifest_path = tmp_path / "a4-verified-mappings.json"
    write_manifest(
        manifest_path,
        {
            "mappings": [
                {
                    "track": 1,
                    "relative_offset": 120,
                    "parameter_name": "Filter 1 Frequency",
                    "cc": 18,
                }
            ]
        },
    )

    result = run_cli("analog-four-saved-offset-mapping-manifest-report", str(manifest_path))

    assert result.returncode == 0
    assert (
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Manifest Report" in result.stdout
    )
    assert "Ready: True" in result.stdout
    assert "Mapping count: 1" in result.stdout
    assert "- no MIDI sending" in result.stdout
    assert result.stderr == ""


def test_saved_offset_mapping_manifest_cli_reports_missing_file():
    result = run_cli(
        "analog-four-saved-offset-mapping-manifest-report",
        "missing-a4-mappings.json",
    )

    assert result.returncode == 1
    assert (
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Manifest Report" in result.stderr
    )
    assert "File not found" in result.stderr
    assert "No MIDI was sent" in result.stderr
    assert result.stdout == ""
