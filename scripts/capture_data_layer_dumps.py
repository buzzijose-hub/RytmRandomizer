"""Capture deterministic JSON dumps of every public ``rytm_randomizer.data`` export.

Writes one ``tests/fixtures/data_layer/<name>.json`` file per public export
of the data layer, using the deterministic serializer below. The companion
guard ``tests/test_data_layer_drift.py`` re-serializes the live exports on
every test run and deep-compares them against these fixtures, so any drift
in the fact tables is a loud, reviewable diff.

This is NOT V1.34 parity capture — it never touches
``tests/fixtures/v134_parity/`` and it reads only the passive ``data/``
fact tables (no engines, no MIDI, no randomization).

Usage (deliberate capture only)::

    RYTM_DATA_DUMP_CAPTURE=1 .venv/bin/python scripts/capture_data_layer_dumps.py

Without ``RYTM_DATA_DUMP_CAPTURE=1`` the script refuses to run, so it cannot
be triggered accidentally from an editor task or a stray shell history entry.

Serializer contract (shared with the drift test, which imports this module):

* frozen dataclasses  -> ``{field: serialized value}`` in field order
* Mapping / MappingProxyType -> dict with deterministically-encoded,
  sorted string keys
* tuple               -> list (order preserved)
* frozenset / set     -> sorted list (sorted by canonical JSON of elements)
* bytes               -> hex string
* Enum                -> its ``value`` (serialized)
* int / float / str / bool / None -> as-is
* callables / types / modules -> skipped at export level; an error anywhere
  nested (they have no deterministic value identity)
"""

from __future__ import annotations

import dataclasses
import enum
import inspect
import json
import os
import sys
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
FIXTURE_DIR: Final[Path] = PROJECT_ROOT / "tests" / "fixtures" / "data_layer"
CAPTURE_ENV_VAR: Final[str] = "RYTM_DATA_DUMP_CAPTURE"

JsonValue = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def _is_skippable_export(value: object) -> bool:
    """Return True for exports with no data identity (callables, types, modules)."""

    return isinstance(value, (type, ModuleType)) or inspect.isroutine(value) or callable(value)


def _encode_key(key: object) -> str:
    """Encode a mapping key as a deterministic string (JSON keys must be str)."""

    if isinstance(key, str):
        return key
    if isinstance(key, (bool, int, tuple)):
        return repr(key)
    raise TypeError(f"Unsupported mapping key type for data-layer dump: {type(key)!r}")


def serialize(value: object) -> JsonValue:
    """Deterministically serialize a data-layer value to JSON-compatible types."""

    if isinstance(value, enum.Enum):
        return serialize(value.value)
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, bytes):
        return value.hex()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            field.name: serialize(getattr(value, field.name)) for field in dataclasses.fields(value)
        }
    if isinstance(value, Mapping):
        encoded = {_encode_key(key): serialize(item) for key, item in value.items()}
        if len(encoded) != len(value):
            raise ValueError("Mapping key encoding collision in data-layer dump")
        return {key: encoded[key] for key in sorted(encoded)}
    if isinstance(value, (set, frozenset)):
        serialized = [serialize(item) for item in value]
        return sorted(serialized, key=lambda item: json.dumps(item, sort_keys=True))
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    raise TypeError(f"Unsupported type in data-layer dump: {type(value)!r}")


def _import_data() -> ModuleType:
    """Import ``rytm_randomizer.data``, tolerating a non-repo-root cwd."""

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    import rytm_randomizer.data as data

    return data


def public_export_names() -> tuple[str, ...]:
    """Return the sorted public data exports (skipping callables/types/modules)."""

    data = _import_data()

    declared = getattr(data, "__all__", None)
    names = (
        list(declared)
        if declared is not None
        else [name for name in dir(data) if not name.startswith("_")]
    )
    return tuple(sorted(name for name in names if not _is_skippable_export(getattr(data, name))))


def capture(fixture_dir: Path = FIXTURE_DIR) -> tuple[str, ...]:
    """Write one ``<name>.json`` fixture per public export; return the names."""

    data = _import_data()

    fixture_dir.mkdir(parents=True, exist_ok=True)
    names = public_export_names()
    expected_files = {f"{name}.json" for name in names}

    for name in names:
        payload = serialize(getattr(data, name))
        target = fixture_dir / f"{name}.json"
        target.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    for orphan in sorted(fixture_dir.glob("*.json")):
        if orphan.name not in expected_files:
            orphan.unlink()

    return names


def main() -> int:
    if os.environ.get(CAPTURE_ENV_VAR) != "1":
        sys.stderr.write(
            "Refusing to capture: data-layer dump capture is a deliberate act.\n"
            f"Set {CAPTURE_ENV_VAR}=1 to rewrite tests/fixtures/data_layer/.\n"
        )
        return 2
    names = capture()
    sys.stdout.write(f"Captured {len(names)} data-layer dumps into {FIXTURE_DIR}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
