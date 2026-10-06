"""The explicit QA CLI delegates to real pack/codec verification without hardware."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.show_bank.export import ShowPackService

from .test_native_offline_journey import _favorite, _generate, _journey

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_ROOT: Final[Path] = Path(__file__).resolve().parents[3]


def _run(package: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_ROOT / "scripts" / "verify_offline_rehearsal_pack.py"), str(package)],
        cwd=_ROOT,
        env={**os.environ, "PYTHONPATH": str(_ROOT), "RYTM_RAND_MIDI_BACKEND": "off"},
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_rehearsal_pack_verifier_checks_native_precision_and_reserved_bytes(tmp_path: Path) -> None:
    journey = _journey(tmp_path, "A4_Test2_T1_OSC1_FIN_P1_Kit.syx")
    candidate = _generate(journey, fields=("osc1_tune",), count=1)[0]
    bank = _favorite(journey, candidate)
    service = ShowPackService(tmp_path / "packs", store=journey.workspace.store)
    exported = service.export(bank, package_id="rehearsal")
    result = _run(exported.package_dir)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["verified"] and report["canonical_profile_replay"]
    assert report["native_value_checks"] == 1
    assert report["approved_changed_native_bytes"] == 1
    assert len(report["original_frame_sha256"]) == 2
    assert report["hardware_access"] is False
    assert report["hardware_validation_granted"] is False


@pytest.mark.parametrize("failure", ["missing", "truncated", "bad-suffix"])
def test_rehearsal_pack_verifier_refuses_bad_packages_without_private_details(
    tmp_path: Path, failure: str
) -> None:
    package = tmp_path / "private-operator-name.show-pack"
    if failure == "bad-suffix":
        package = tmp_path / "private-operator-name"
    elif failure == "truncated":
        package.mkdir()
        (package / "manifest.json").write_bytes(b'{"format":')
    result = _run(package)
    assert result.returncode == 1
    report = json.loads(result.stdout)
    assert report["verified"] is False
    assert report["error_type"] in {"DataError", "ValueError"}
    assert str(tmp_path) not in result.stdout and "private-operator-name" not in result.stdout
    assert result.stderr == ""
