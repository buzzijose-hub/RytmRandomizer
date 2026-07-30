"""Keep the Analog Four audio-patch run state aligned with its JSON schema."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = (
    PROJECT_ROOT
    / "docs"
    / "superpowers"
    / "plans"
    / "2026-07-03-analog-four-audio-patch-genome_STATE.json"
)
SCHEMA_PATH = STATE_PATH.with_suffix(".schema.json")


def _matches_declared_type(value: object, declared_type: str) -> bool:
    if declared_type == "object":
        return isinstance(value, dict)
    if declared_type == "string":
        return isinstance(value, str)
    if declared_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared_type == "null":
        return value is None
    raise AssertionError(f"Unsupported schema type in state contract: {declared_type}")


def _validate(value: object, schema: dict[str, object], path: str = "$") -> None:
    declared = schema.get("type")
    if isinstance(declared, str):
        assert _matches_declared_type(
            value, declared
        ), f"{path} must have schema type {declared}; got {type(value).__name__}"
    elif isinstance(declared, list):
        assert any(
            isinstance(item, str) and _matches_declared_type(value, item) for item in declared
        ), f"{path} must have one of schema types {declared}"

    if "const" in schema:
        assert value == schema["const"], f"{path} must equal {schema['const']!r}"

    allowed = schema.get("enum")
    if isinstance(allowed, list):
        assert value in allowed, f"{path} must be one of {allowed}; got {value!r}"

    if isinstance(value, str):
        minimum_length = schema.get("minLength")
        if isinstance(minimum_length, int):
            assert (
                len(value) >= minimum_length
            ), f"{path} must contain at least {minimum_length} characters"
        pattern = schema.get("pattern")
        if isinstance(pattern, str):
            assert re.fullmatch(pattern, value), f"{path} must match schema pattern {pattern!r}"

    if isinstance(value, int) and not isinstance(value, bool):
        minimum = schema.get("minimum")
        if isinstance(minimum, int):
            assert value >= minimum, f"{path} must be at least {minimum}"

    if not isinstance(value, dict):
        return

    required = schema.get("required", [])
    assert isinstance(required, list)
    missing = [key for key in required if isinstance(key, str) and key not in value]
    assert not missing, f"{path} is missing required properties: {missing}"

    properties = schema.get("properties", {})
    assert isinstance(properties, dict)
    for key, child_schema in properties.items():
        if key not in value:
            continue
        assert isinstance(key, str)
        assert isinstance(child_schema, dict)
        _validate(value[key], child_schema, f"{path}.{key}")

    extras = set(value) - set(properties)
    additional = schema.get("additionalProperties", True)
    if additional is False:
        assert not extras, f"{path} has undeclared properties: {sorted(extras)}"
    elif isinstance(additional, dict):
        for key in sorted(extras):
            _validate(value[key], additional, f"{path}.{key}")


def test_analog_four_audio_patch_state_matches_declared_schema() -> None:
    state = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    assert isinstance(state, dict)
    assert isinstance(schema, dict)
    _validate(state, schema)
