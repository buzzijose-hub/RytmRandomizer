"""Release warnings must cover every permitted real transmit boundary."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast
ROOT: Final[Path] = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from release_paths import is_hardware_path  # noqa: E402


def test_release_paths_cover_transmit_allowlist_and_frozen_parity() -> None:
    boundary = runpy.run_path(str(Path(__file__).with_name("test_armed_entry_points.py")))
    assert all(is_hardware_path(path) for path in boundary["_ALLOWED_TRANSMIT_MODULES"])
    assert is_hardware_path("tests/fixtures/v134_parity/future-case.json")
    assert is_hardware_path("rytm_randomizer/engines/future_engine.py")
    assert is_hardware_path("rytm_randomizer/senders/future_sender.py")
    assert not is_hardware_path("docs/midi_io.py")
    assert not is_hardware_path("rytm_randomizer/midi_io.py.backup")
