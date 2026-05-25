"""Tests for ``rytm_randomizer.cockpit.export.cli`` — the end-to-end export CLI.

These tests exercise the full pack → (optional sign) → atomic write → verify
pipeline that drives ``cockpit-export-profile-model``. Every branch in
``cli.py`` is covered: signed vs unsigned happy paths, every validation
rule, both ``--json`` and text output modes, overwrite semantics, and the
post-write verification failure path.

Tests use a real :class:`ProfileRegistry` rooted under ``tmp_path`` — no
mocking of the registry or the wire format — so the round-trip assertion
"the bytes we wrote unpack back to a byte-identical ``ProfileModel``" is
load-bearing.

Mark: ``pytest.mark.fast`` (matches every other cockpit test module).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final
from unittest.mock import patch

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.export.cli import handle_export_profile_model
from rytm_randomizer.cockpit.export.serialize import unpack_profile_model
from rytm_randomizer.cockpit.export.signing import unpack_signed
from rytm_randomizer.cockpit.export.verifier import VerificationResult
from rytm_randomizer.cockpit.profiles import ProfileRegistry

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_KEY_HEX: Final[str] = "00112233445566778899aabbccddeeff" * 2  # 32-byte key, 64 hex chars
_KEY_ID: Final[str] = "buzzi-2026"


def _make_profile(profile_id: str = "user-rolling-low-end") -> ProfileModel:
    """Build a small, fully-valid ``ProfileModel`` for round-trip testing."""

    return ProfileModel(
        profile_id=profile_id,
        name="Rolling low end",
        kind="user",
        model_version="1.0.0",
        traits=(
            StyleTrait(name="rolling_low_end", value=0.85),
            StyleTrait(name="sparse_top", value=0.30),
        ),
        pad_mappings=(
            TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.9),
            TraitPadWeight(trait="rolling_low_end", pad_id=2, weight=0.7),
            TraitPadWeight(trait="sparse_top", pad_id=8, weight=0.6),
        ),
        transition_curve="progressive",
        source_summary="hand-tuned for buzzi-2026 set",
    )


def _save_profile(profiles_dir: Path, profile: ProfileModel) -> None:
    """Persist ``profile`` via a fresh ``ProfileRegistry``."""

    ProfileRegistry(profiles_dir).save(profile)


def _read_json(captured: str) -> dict[str, object]:
    """Parse a JSON document from captured stdout."""

    return json.loads(captured)


# ---------------------------------------------------------------------------
# Happy paths — signed
# ---------------------------------------------------------------------------


def test_signed_export_writes_round_trippable_blob(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Signed JSON path: writes envelope, verifies, JSON ack is ok."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out" / "profile.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--key-hex",
            _KEY_HEX,
            "--key-id",
            _KEY_ID,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured
    payload = _read_json(captured.out)
    assert payload["ok"] is True
    assert payload["profile_id"] == profile.profile_id
    assert payload["profile_name"] == profile.name
    assert payload["model_version"] == profile.model_version
    assert payload["output_path"] == str(output.resolve())
    assert payload["bytes_written"] > 0
    assert payload["overwrote_existing"] is False
    assert payload["signed"] is True
    assert payload["key_id"] == _KEY_ID
    assert payload["verification"]["ok"] is True
    assert payload["verification"]["reason"] == "ok"
    assert payload["verification"]["expected_key_id"] == _KEY_ID
    assert payload["verification"]["expected_algorithm"] == "hmac-sha256"
    assert isinstance(payload["verification"]["payload_size"], int)
    # Round-trip: read the envelope, unwrap, decode → equal to original.
    envelope = output.read_bytes()
    signed = unpack_signed(envelope)
    assert signed.key_id == _KEY_ID
    decoded = unpack_profile_model(signed.payload)
    assert decoded.to_dict() == profile.to_dict()


def test_signed_export_text_output_contains_all_fields(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Without ``--json``: text output carries every key field on its own line."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "profile.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--key-hex",
            _KEY_HEX,
            "--key-id",
            _KEY_ID,
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured
    assert "ok: true" in captured.out
    assert f"profile_id: {profile.profile_id}" in captured.out
    assert f"profile_name: {profile.name}" in captured.out
    assert "model_version: 1.0.0" in captured.out
    assert f"output_path: {output.resolve()}" in captured.out
    assert "bytes_written: " in captured.out
    assert "overwrote_existing: false" in captured.out
    assert "signed: true" in captured.out
    assert f"key_id: {_KEY_ID}" in captured.out
    assert "verification.ok: true" in captured.out
    assert "verification.reason: ok" in captured.out


# ---------------------------------------------------------------------------
# Happy paths — unsigned
# ---------------------------------------------------------------------------


def test_unsigned_export_writes_raw_payload(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Unsigned JSON path: writes ``RYMP`` bytes directly, verification reports unsigned_payload."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "profile.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured
    payload = _read_json(captured.out)
    assert payload["ok"] is True
    assert payload["signed"] is False
    assert "key_id" not in payload or payload["key_id"] is None
    assert payload["verification"]["ok"] is True
    assert payload["verification"]["reason"] == "ok"
    # Raw payload starts with RYMP — no signing envelope.
    assert output.read_bytes()[:4] == b"RYMP"
    decoded = unpack_profile_model(output.read_bytes())
    assert decoded.to_dict() == profile.to_dict()


def test_unsigned_export_text_output_omits_key_id(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Text output: unsigned exports do not print a ``key_id:`` line."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "profile.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured
    assert "signed: false" in captured.out
    # Top-level ``key_id:`` is omitted; the verification block's
    # ``verification.expected_key_id`` is the unsigned-mode None marker.
    assert "\nkey_id:" not in captured.out
    assert "verification.reason: ok" in captured.out
    assert "verification.expected_key_id: null" in captured.out


# ---------------------------------------------------------------------------
# Validation — mutually exclusive / required argument combos
# ---------------------------------------------------------------------------


def test_key_hex_without_key_id_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--key-hex`` without ``--key-id``: ok=False, non-zero exit, specific error."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.rymp"),
            "--key-hex",
            _KEY_HEX,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "--key-id" in payload["error"]


def test_key_id_without_key_hex_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--key-id`` without ``--key-hex``: signed mode incomplete, error."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.rymp"),
            "--key-id",
            _KEY_ID,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "--key-hex" in payload["error"]


def test_signed_and_unsigned_mutually_exclusive(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """``--key-hex`` + ``--unsigned`` is rejected before any file work."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--key-hex",
            _KEY_HEX,
            "--key-id",
            _KEY_ID,
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "mutually exclusive" in payload["error"]
    assert not output.exists()


def test_neither_signed_nor_unsigned_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Neither ``--key-hex`` nor ``--unsigned`` provided: explicit choice required."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.rymp"),
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "must explicitly choose" in payload["error"]


# ---------------------------------------------------------------------------
# Validation — bad inputs
# ---------------------------------------------------------------------------


def test_invalid_hex_key_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """``--key-hex`` value not valid hex: clean ok=False, no file written."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--key-hex",
            "not-hex-zz",
            "--key-id",
            _KEY_ID,
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "invalid" in payload["error"].lower()
    assert not output.exists()


def test_unknown_profile_id_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Unknown ``--profile-id``: ok=False, no file written, error mentions id."""

    output = tmp_path / "out.rymp"

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            "does-not-exist",
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "does-not-exist" in payload["error"]
    assert not output.exists()


def test_missing_required_argument_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Missing ``--profile-id`` (a required arg): ok=False with usage hint."""

    exit_code = handle_export_profile_model(
        [
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.rymp"),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "--profile-id" in payload["error"]


def test_missing_profiles_dir_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Missing ``--profiles-dir``: ok=False with the right field name."""

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            "anything",
            "--output",
            str(tmp_path / "out.rymp"),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "--profiles-dir" in payload["error"]


def test_missing_output_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Missing ``--output``: ok=False with the right field name."""

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            "anything",
            "--profiles-dir",
            str(tmp_path),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "--output" in payload["error"]


def test_missing_value_for_option_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """An option without its value: ok=False with usage."""

    exit_code = handle_export_profile_model(
        [
            "--json",
            "--profile-id",  # no value follows
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert "requires a value" in payload["error"]


def test_unknown_option_errors(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """An unrecognized flag is rejected before any file work."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(tmp_path / "out.rymp"),
            "--unsigned",
            "--bogus-flag",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False


# ---------------------------------------------------------------------------
# Overwrite semantics
# ---------------------------------------------------------------------------


def test_existing_file_without_overwrite_errors(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pre-existing output path without ``--overwrite``: error, original kept."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"
    output.write_bytes(b"existing content")

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    # Original bytes preserved — atomic_write refused to overwrite.
    assert output.read_bytes() == b"existing content"


def test_existing_file_with_overwrite_succeeds(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Pre-existing output path with ``--overwrite``: succeeds, marks overwrote=true."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"
    output.write_bytes(b"stale content")

    exit_code = handle_export_profile_model(
        [
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--overwrite",
            "--json",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0, captured
    payload = _read_json(captured.out)
    assert payload["ok"] is True
    assert payload["overwrote_existing"] is True
    assert output.read_bytes()[:4] == b"RYMP"


# ---------------------------------------------------------------------------
# Post-write verification failure
# ---------------------------------------------------------------------------


def test_post_write_verification_failure_surfaces_in_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """If verification fails after the write, the JSON ack reports ok=False."""

    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    failing = VerificationResult(
        ok=False,
        reason="signature_mismatch",
        expected_key_id=_KEY_ID,
        expected_algorithm="hmac-sha256",
        payload_size=42,
    )
    with patch(
        "rytm_randomizer.cockpit.export.cli.verify_signed_blob",
        return_value=failing,
    ):
        exit_code = handle_export_profile_model(
            [
                "--profile-id",
                profile.profile_id,
                "--profiles-dir",
                str(tmp_path),
                "--output",
                str(output),
                "--key-hex",
                _KEY_HEX,
                "--key-id",
                _KEY_ID,
                "--json",
            ]
        )

    captured = capsys.readouterr()
    assert exit_code != 0
    payload = _read_json(captured.out)
    assert payload["ok"] is False
    assert payload["verification"]["ok"] is False
    assert payload["verification"]["reason"] == "signature_mismatch"
    # The bytes are still on disk (verification is a *check*, not a rollback).
    assert output.exists()


# ---------------------------------------------------------------------------
# Public surface / help
# ---------------------------------------------------------------------------


def test_handle_export_profile_model_is_callable_with_empty_args(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Empty arg list: ok=False, exit non-zero, no crash. Falls back to text mode."""

    exit_code = handle_export_profile_model([])

    captured = capsys.readouterr()
    assert exit_code != 0
    # No --json: text mode. Error message points at the missing required arg.
    assert "ok: false" in captured.out
    assert "--profile-id" in captured.out


def test_help_text_advertises_new_command() -> None:
    """The top-level CLI help mentions ``cockpit-export-profile-model``."""

    from rytm_randomizer.help_text import resolve_help_text

    top_level = resolve_help_text("--help")
    assert "cockpit-export-profile-model" in top_level

    detailed = resolve_help_text("cockpit-export-profile-model")
    assert detailed.startswith("RytmRandomizer passive CLI: cockpit-export-profile-model")
    assert "--key-hex" in detailed
    assert "--unsigned" in detailed


def test_cli_dispatch_registers_command(tmp_path: Path) -> None:
    """The lazy command registry resolves the new subcommand to a handler."""

    import importlib

    # Importing the cli module triggers no registration; the dispatcher does
    # the lazy import. Drive the dispatcher directly so we can stay in-process.
    cli_module = importlib.import_module("rytm_randomizer.cli")
    profile = _make_profile()
    _save_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    exit_code = cli_module._registered_command_exit_code(
        [
            "cockpit-export-profile-model",
            "--profile-id",
            profile.profile_id,
            "--profiles-dir",
            str(tmp_path),
            "--output",
            str(output),
            "--unsigned",
            "--json",
        ]
    )

    assert exit_code == 0
    assert output.exists()
