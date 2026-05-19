from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANUAL_HARDWARE_VALIDATION = PROJECT_ROOT / "docs" / "MANUAL_HARDWARE_VALIDATION.md"


def test_manual_hardware_validation_names_runtime_preflights_and_lane_labels():
    text = MANUAL_HARDWARE_VALIDATION.read_text(encoding="utf-8")

    assert "python -m rytm_randomizer.cli rytm-12-pad-engine-matrix-report" in text
    assert "Pad 10 is `OH / Open hihat`, not an XT tom lane" in text
    assert "Track 3 / large motion layer" in text


def test_manual_hardware_validation_documents_a4_only_snapshot_without_rytm_path():
    text = MANUAL_HARDWARE_VALIDATION.read_text(encoding="utf-8")

    assert "--snapshot-target analog-four" in text
    assert "--analog-four-path <analog-four-sysex-path> --analog-four-slot 1" in text
    assert "does not require `--snapshot-path` or `--snapshot-slot`" in text
