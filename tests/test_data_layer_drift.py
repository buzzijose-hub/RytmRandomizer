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


def test_appliance_bindings_preserve_native_pairs_and_shared_device_targets() -> None:
    """Catalog bindings name existing fields without introducing wire authority."""

    assert dict(data.DUAL_MACHINE_TARGET_IDS) == {
        "rytm": ("analog_rytm_mk2",),
        "rytm-only": ("analog_rytm_mk2",),
        "a4": ("analog_four_mk2",),
        "a4-only": ("analog_four_mk2",),
        "both": ("analog_rytm_mk2", "analog_four_mk2"),
    }
    assert data.A4_APPLIANCE_PARAMETER_FIELDS["OSC1 Pitch"] == ("osc1_tune", "osc1_fine")
    assert data.A4_APPLIANCE_PARAMETER_FIELDS["LFO1 Depth A"] == (
        "lfo1_depth_a",
        "lfo1_depth_a_fraction",
    )
    assert data.A4_APPLIANCE_NATIVE_ONLY_PARAMETERS["OSC1 Fine"] == ("OSC 1", "osc1_fine")
    assert data.RYTM_APPLIANCE_FX_FIELDS["Compressor Output Volume"] == "compressor_volume"


def test_a4_native_domains_preserve_integer_precision_and_paired_fine_protection() -> None:
    """Pin representative native units independently of generated JSON snapshots."""

    assert {
        "word": (data.A4_NATIVE_WORD_MIN, data.A4_NATIVE_WORD_MAX),
        "byte": (data.A4_NATIVE_BYTE_MIN, data.A4_NATIVE_BYTE_MAX),
        "bipolar": (data.A4_BIPOLAR_ZERO, data.A4_BIPOLAR_MIN, data.A4_BIPOLAR_MAX),
        "pitch": (data.A4_PITCH_ZERO, data.A4_PITCH_UNITS_PER_SEMITONE),
        "coarse_pitch": (data.A4_PITCH_COARSE_MIN, data.A4_PITCH_COARSE_MAX),
        "fine_native": (data.A4_FINE_NATIVE_MIN, data.A4_FINE_NATIVE_MAX),
        "fine_display": (data.A4_FINE_DISPLAY_MIN, data.A4_FINE_DISPLAY_MAX),
        "fine_units": data.A4_FINE_UNITS_PER_DISPLAY,
        "depth": (data.A4_MOD_DEPTH_ZERO, data.A4_MOD_DEPTH_UNITS_PER_DISPLAY),
        "depth_display": (data.A4_MOD_DEPTH_DISPLAY_MIN, data.A4_MOD_DEPTH_DISPLAY_MAX),
    } == {
        "word": (0, 32767),
        "byte": (0, 127),
        "bipolar": (64, -64, 63),
        "pitch": (16384, 256),
        "coarse_pitch": (-64, 63),
        "fine_native": (-128, 127),
        "fine_display": (-64, 63),
        "fine_units": 2,
        "depth": (16384, 128),
        "depth_display": (-128.0, 127.9921875),
    }
    assert frozenset({"osc1_tune", "osc2_tune"}) == data.A4_OSCILLATOR_PITCH_FIELDS
    assert frozenset({"osc1_fine", "osc2_fine"}) == data.A4_OSCILLATOR_FINE_FIELDS
    assert (
        data.A4_NATIVE_FIELD_DOMAINS["filter1_frequency"] is data.A4_NATIVE_FORMAT_DOMAINS["q8.8"]
    )
    assert data.A4_NATIVE_FIELD_DOMAINS["lfo1_depth_a"] is data.A4_NATIVE_FORMAT_DOMAINS["q8.7"]
    assert data.A4_NATIVE_FIELD_DOMAINS["osc1_detune"] is data.A4_NATIVE_FORMAT_DOMAINS["bipolar"]
    assert data.A4_NATIVE_FIELD_DOMAINS["osc1_fine"].offline_mutable is False
    assert "lfo1_depth_a_fraction" not in data.A4_NATIVE_FIELD_DOMAINS


def test_appliance_scope_store_adds_versioned_presets_without_redefining_existing_stores() -> None:
    """The new store owns presets only and retains the existing store schema versions."""

    store = data.PERSISTED_STATE_STORES["appliance_scopes"]
    assert store.store_id == "appliance_scopes"
    assert store.schema_version == 1
    assert store.owner_module == "rytm_randomizer.cockpit.appliance"
    assert store.description == "Bounded touch scope presets; no transient hardware authority."
    assert store.migrations == ()
    assert data.PERSISTED_STATE_STORES["library_store"].schema_version == 1
    assert data.PERSISTED_STATE_STORES["profile_registry"].schema_version == 1
