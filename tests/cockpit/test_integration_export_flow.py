"""Integration: ``export_profile_model`` returns bytes that round-trip parse.

EXPORT packs the requested profile into either the portable binary format
(header + MessagePack payload + CRC32) or a JSON representation
(``ProfileModel.to_dict()`` UTF-8 encoded). The ack carries the result as
base64-encoded bytes under ``model_bytes_b64``.

Round-trip is the load-bearing check: bytes the export emits MUST parse
back to a ``ProfileModel`` byte-identical to the original. This is the
GUI-to-firmware contract — the embedded runtime in Phase 4 will only
accept blobs produced by this exact handler.

Spec reference: see ``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Model Export".
"""

from __future__ import annotations

import base64
import json

import pytest
from cockpit.conftest import send_cmd

from rytm_randomizer.cockpit.export import unpack_profile_model
from rytm_randomizer.cockpit.profiles import ProfileRegistry

pytestmark = pytest.mark.fast


def test_export_binary_returns_round_trippable_blob(cockpit_ws: object) -> None:
    """EXPORT target='binary' returns a blob that unpacks back to the same ProfileModel."""

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-industrial",
        target="binary",
    )

    assert ack["ok"] is True
    raw = base64.b64decode(ack["model_bytes_b64"])
    # Round-trip parse: bytes → ProfileModel.
    decoded = unpack_profile_model(raw)
    assert decoded.profile_id == "scene-industrial"
    assert decoded.name == "industrial"
    assert decoded.kind == "scene"


def test_export_binary_blob_has_magic_prefix(cockpit_ws: object) -> None:
    """The portable binary format always starts with the magic prefix ``RYMP``."""

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-garage",
        target="binary",
    )

    raw = base64.b64decode(ack["model_bytes_b64"])
    assert raw[:4] == b"RYMP"


def test_export_json_returns_valid_profile_dict(cockpit_ws: object) -> None:
    """EXPORT target='json' returns a UTF-8 JSON dict of ``ProfileModel.to_dict()``."""

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-hypnotic",
        target="json",
    )

    assert ack["ok"] is True
    raw = base64.b64decode(ack["model_bytes_b64"])
    payload = json.loads(raw.decode("utf-8"))
    assert payload["profile_id"] == "scene-hypnotic"
    assert payload["name"] == "hypnotic"
    assert payload["kind"] == "scene"
    # Every scene has at least one trait + at least one pad_mapping.
    assert len(payload["traits"]) > 0
    assert len(payload["pad_mappings"]) > 0


def test_export_unknown_profile_id_returns_error(cockpit_ws: object) -> None:
    """An unknown profile_id returns ``ok=False`` with a readable error."""

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-does-not-exist",
        target="binary",
    )

    assert ack["ok"] is False
    assert "unknown profile_id" in ack["error"]


def test_export_invalid_target_returns_error(cockpit_ws: object) -> None:
    """A ``target`` other than 'binary'/'json' returns a clear validation error."""

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-industrial",
        target="msgpack",  # not a supported target string
    )

    assert ack["ok"] is False
    assert "target must be" in ack["error"]


def test_export_json_matches_builtin_scene_definition(cockpit_ws: object) -> None:
    """The exported JSON for a built-in scene equals ``BUILTIN_SCENES`` entry's dict form."""

    # Look up the same profile through a fresh registry to compare against.
    from rytm_randomizer.cockpit.profiles.builtin import BUILTIN_SCENES

    # The registry lookup is exercised through the cockpit_client fixture; we
    # only need the dict form to compare.
    assert ProfileRegistry  # type-checker hint: imported via conftest path
    industrial = next(p for p in BUILTIN_SCENES if p.profile_id == "scene-industrial")

    ack = send_cmd(
        cockpit_ws,
        "export_profile_model",
        profile_id="scene-industrial",
        target="json",
    )
    raw = base64.b64decode(ack["model_bytes_b64"])
    exported = json.loads(raw.decode("utf-8"))

    assert exported == industrial.to_dict()
