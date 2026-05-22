from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.fast


ROOT = Path(__file__).resolve().parents[1]


def test_manual_hardware_validation_documents_dual_machine_strategy_redo() -> None:
    text = (ROOT / "docs" / "MANUAL_HARDWARE_VALIDATION.md").read_text()

    assert "## Dual-Machine Strategy Redo Manual Validation" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report rytm" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report a4" in text
    assert "python -m rytm_randomizer.cli dual-machine-target-report both" in text
    assert "manual only" in text.lower()


def test_manual_hardware_validation_documents_live_show_preflight() -> None:
    text = (ROOT / "docs" / "MANUAL_HARDWARE_VALIDATION.md").read_text()

    assert "## Live-Show Passive Preflight" in text
    assert "style-performance-arc-stage-routing-report" in text
    assert "SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> Z -> Q" in text
    assert "no MIDI is sent" in text
    assert "manual only" in text.lower()
