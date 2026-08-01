"""Data-layer drift guard — every public ``rytm_randomizer.data`` export is frozen.

``tests/fixtures/data_layer/<name>.json`` holds a deterministic JSON dump of
each public data-layer export, captured by
``scripts/capture_data_layer_dumps.py`` (which refuses to run without
``RYTM_DATA_DUMP_CAPTURE=1`` — capture is a deliberate, reviewed act).

These tests re-serialize the live exports with the SAME serializer (imported
from the capture script, so the two can never drift apart) and deep-compare
against the fixtures. Any change to a fact table — a CC number, an anchor,
a profile field — shows up as a reviewable JSON diff instead of sliding
through unnoticed.

This is complementary to ``tests/test_data_layer.py`` (spot-check
expectations) and is NOT V1.34 parity — the fixtures here cover the passive
``data/`` tables only.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Final

import pytest

import rytm_randomizer.data as data

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
FIXTURE_DIR: Final[Path] = PROJECT_ROOT / "tests" / "fixtures" / "data_layer"
CAPTURE_SCRIPT: Final[Path] = PROJECT_ROOT / "scripts" / "capture_data_layer_dumps.py"


def _load_capture_module() -> ModuleType:
    """Import the capture script by path (scripts/ is not a package)."""

    spec = importlib.util.spec_from_file_location("capture_data_layer_dumps", CAPTURE_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_CAPTURE: Final[ModuleType] = _load_capture_module()
EXPORT_NAMES: Final[tuple[str, ...]] = _CAPTURE.public_export_names()


@pytest.mark.parametrize("name", EXPORT_NAMES)
def test_data_export_matches_fixture(name: str) -> None:
    """The live export serializes byte-identically to its frozen fixture.

    On failure: either revert the accidental data change, or — if the change
    is intentional and reviewed — regenerate the fixtures with
    ``RYTM_DATA_DUMP_CAPTURE=1 python scripts/capture_data_layer_dumps.py``
    and commit the JSON diff for review.
    """

    fixture_path = FIXTURE_DIR / f"{name}.json"
    assert fixture_path.is_file(), (
        f"Missing fixture for data export {name!r}. Capture it with "
        "RYTM_DATA_DUMP_CAPTURE=1 python scripts/capture_data_layer_dumps.py"
    )

    expected = json.loads(fixture_path.read_text(encoding="utf-8"))
    live = _CAPTURE.serialize(getattr(data, name))
    assert live == expected, (
        f"Data-layer drift detected in {name!r}: the live value no longer "
        f"matches tests/fixtures/data_layer/{name}.json. Revert the change, "
        "or regenerate the fixtures deliberately (RYTM_DATA_DUMP_CAPTURE=1) "
        "and commit the diff."
    )


def test_fixture_dir_matches_export_surface_exactly() -> None:
    """No orphan fixture files and no missing exports.

    Renaming/removing a data export must remove its fixture in the same PR;
    adding an export must capture a fixture for it. This keeps the fixture
    directory a precise mirror of the public data surface.
    """

    expected_files = {f"{name}.json" for name in EXPORT_NAMES}
    present_files = {path.name for path in FIXTURE_DIR.glob("*.json")}

    orphans = sorted(present_files - expected_files)
    assert not orphans, (
        "Orphan fixture file(s) in tests/fixtures/data_layer/ with no "
        "matching public data export. Remove them (or restore the export):\n"
        "    " + "\n    ".join(orphans)
    )

    missing = sorted(expected_files - present_files)
    assert not missing, (
        "Public data export(s) without a fixture. Capture them with "
        "RYTM_DATA_DUMP_CAPTURE=1 python scripts/capture_data_layer_dumps.py:\n"
        "    " + "\n    ".join(missing)
    )
