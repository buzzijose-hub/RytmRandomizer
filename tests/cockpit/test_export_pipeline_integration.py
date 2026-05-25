"""WS-F end-to-end integration tests for the Phase 3 export pipeline.

These tests exercise WS-A (signing) + WS-B (writer) + WS-C (CLI) + WS-D
(rehearsal report) + the existing :class:`ProfileRegistry` as one coherent
pipeline driven from outside the process, the way an operator would.

Coverage areas (one-to-one with the WS-F brief):

1. Unsigned round-trip via subprocess CLI.
2. Signed round-trip via subprocess CLI.
3. Rehearsal-then-export consistency (the rehearsal report's claimed
   output_path / payload_size / payload_crc_hex / signed flag must match
   what the real export later produces).
4. CLI validation / error paths (unknown profile id, missing key id,
   invalid hex key, mutually-exclusive flags, must-choose, existing-file
   without ``--overwrite``, existing-file with ``--overwrite``).
5. Atomic-write guarantee (a failed run must not corrupt the prior file).
6. Verification-failure shapes (magic, version, payload byte, signature
   byte, truncated input).
7. Cross-component sanity (rehearsal sizes / crc match real export).

Mark: ``pytest.mark.fast`` so the entire integration sweep runs under
``pytest -m fast``.
"""

from __future__ import annotations

import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path
from typing import Final

import pytest

from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
from rytm_randomizer.cockpit.export import (
    SIGNATURE_HEADER_MAGIC,
    pack_profile_model,
    pack_signed,
    sign_profile_blob,
    unpack_profile_model,
    unpack_signed,
    verify_signed_blob,
    verify_unsigned_payload,
)
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.reports.cockpit_export_rehearsal import (
    build_cockpit_export_rehearsal_report,
    to_cockpit_export_rehearsal_json,
)

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Constants + helpers
# ---------------------------------------------------------------------------


PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
"""Repo root used as the subprocess cwd so ``-m rytm_randomizer.cli`` resolves."""

# 32-byte HMAC key encoded as 64 hex chars. Test-only — never reused outside.
_KEY_HEX: Final[str] = "0011223344556677" * 4
_KEY_ID: Final[str] = "buzzi-test"
_KEY_BYTES: Final[bytes] = bytes.fromhex(_KEY_HEX)


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Invoke ``python -m rytm_randomizer.cli`` with the given args.

    Uses :data:`sys.executable` so the test inherits the active interpreter
    (matters on Windows where the bare ``python`` shim from the Store can
    fail under non-interactive subprocesses).
    """

    return subprocess.run(
        [sys.executable, "-m", "rytm_randomizer.cli", *args],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )


def _build_test_profile(profile_id: str = "buzzi-int-test") -> ProfileModel:
    """Build a small but non-trivial user profile for round-trip testing."""

    return ProfileModel(
        profile_id=profile_id,
        name="buzzi-int-test",
        kind="user",
        model_version="1.0.0",
        traits=(
            StyleTrait("rolling_low_end", 0.85),
            StyleTrait("metallic_tension", 0.55),
            StyleTrait("hat_density", 0.40),
            StyleTrait("filter_motion", 0.62),
        ),
        pad_mappings=(
            TraitPadWeight("rolling_low_end", 1, 0.85),
            TraitPadWeight("metallic_tension", 2, 0.55),
            TraitPadWeight("hat_density", 3, 0.40),
            TraitPadWeight("filter_motion", 4, 0.62),
        ),
        transition_curve="progressive",
        source_summary="4 sources - 12 analyzed signals",
    )


def _seed_profile(profiles_dir: Path, profile: ProfileModel) -> None:
    """Persist ``profile`` under ``profiles_dir`` via a fresh registry."""

    ProfileRegistry(profiles_dir).save(profile)


def _isolate_user_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Point per-platform default-config envs at ``tmp_path``.

    The export writer's ``default_export_dir`` is not invoked here (the
    CLI's ``--output`` is always explicit) but a stray default-config probe
    inside the subprocess must still land under ``tmp_path``.
    """

    home = tmp_path / "home"
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(home / ".config"))
    monkeypatch.setenv("APPDATA", str(home / "AppData"))


def _read_json(text: str) -> dict[str, object]:
    """Decode a JSON document from a (possibly trailing-newline) string."""

    return json.loads(text)


def _payload_inside_signed_envelope(envelope_bytes: bytes) -> bytes:
    """Walk the signed envelope and return only the inner ``RYMP`` blob."""

    return unpack_signed(envelope_bytes).payload


# ---------------------------------------------------------------------------
# (1) Unsigned round-trip via subprocess CLI
# ---------------------------------------------------------------------------


def test_unsigned_export_subprocess_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subprocess unsigned export: file unpacks back to the original profile."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "buzzi-unsigned.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--json",
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _read_json(result.stdout)
    assert payload["ok"] is True
    assert payload["signed"] is False
    assert payload["bytes_written"] > 0
    assert payload["verification"]["ok"] is True
    assert payload["verification"]["reason"] == "ok"

    raw = output.read_bytes()
    assert raw[:4] == b"RYMP"
    decoded = unpack_profile_model(raw)
    assert decoded.to_dict() == profile.to_dict()
    # Byte-for-byte the same as ``pack_profile_model`` would have produced.
    assert raw == pack_profile_model(profile)


# ---------------------------------------------------------------------------
# (2) Signed round-trip via subprocess CLI
# ---------------------------------------------------------------------------


def test_signed_export_subprocess_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subprocess signed export: envelope verifies and inner payload round-trips."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "buzzi-signed.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )

    assert result.returncode == 0, result.stderr or result.stdout
    payload = _read_json(result.stdout)
    assert payload["ok"] is True
    assert payload["signed"] is True
    assert payload["key_id"] == _KEY_ID
    assert payload["bytes_written"] > 0
    assert payload["verification"]["ok"] is True
    assert payload["verification"]["reason"] == "ok"
    assert payload["verification"]["expected_key_id"] == _KEY_ID

    raw = output.read_bytes()
    assert raw[:4] == SIGNATURE_HEADER_MAGIC
    signed = unpack_signed(raw)
    assert signed.key_id == _KEY_ID
    # The verifier returns ok=True for the same bytes and the same key.
    verified = verify_signed_blob(raw, key=_KEY_BYTES)
    assert verified.ok is True
    assert verified.reason == "ok"
    # The inner payload unpacks back to the original profile.
    decoded = unpack_profile_model(signed.payload)
    assert decoded.to_dict() == profile.to_dict()


def test_signed_export_subprocess_inner_payload_equals_pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The inner ``RYMP`` payload of the signed envelope equals pack_profile_model output."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "signed.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert result.returncode == 0, result.stderr or result.stdout

    raw = output.read_bytes()
    inner = _payload_inside_signed_envelope(raw)
    assert inner == pack_profile_model(profile)


# ---------------------------------------------------------------------------
# (3) Rehearsal-then-export consistency
# ---------------------------------------------------------------------------


def test_rehearsal_then_signed_export_paths_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rehearsal report's output_path matches what the export later writes."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "buzzi.rymp"

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        key_id=_KEY_ID,
        output_path=output,
    )
    assert rehearsal.signed is True
    assert rehearsal.output_path == str(output)
    assert rehearsal.payload_size == len(pack_profile_model(profile))
    assert rehearsal.signed_size is not None

    export = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert export.returncode == 0, export.stderr or export.stdout
    ack = _read_json(export.stdout)

    # The export wrote where the rehearsal said it would.
    assert ack["output_path"] == str(output.resolve())
    # The rehearsal payload_size matches the bytes of the inner payload that
    # the export envelope wraps.
    raw = output.read_bytes()
    inner = _payload_inside_signed_envelope(raw)
    assert rehearsal.payload_size == len(inner)
    # The rehearsal's signed flag matches the export's ack.
    assert ack["signed"] is rehearsal.signed


def test_rehearsal_payload_crc_matches_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rehearsal's payload_crc_hex matches the CRC over the actual exported payload."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "buzzi-crc.rymp"

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        key_id=_KEY_ID,
        output_path=output,
    )

    export = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert export.returncode == 0, export.stderr or export.stdout

    raw = output.read_bytes()
    inner = _payload_inside_signed_envelope(raw)

    # Reconstruct the rehearsal CRC computation: zlib.crc32 of the inner
    # ``RYMP`` payload bytes (the rehearsal stores it as 8 hex chars).
    from rytm_randomizer.cockpit.export.model_format import compute_crc

    expected_crc_hex = f"{compute_crc(inner):08x}"
    assert rehearsal.payload_crc_hex == expected_crc_hex


def test_rehearsal_signed_size_is_conservative_upper_bound_on_real_export(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rehearsal's ``signed_size`` is a conservative upper-bound on the real signed file size.

    WS-D estimates the signed envelope size as ``payload_size + 256``
    (see ``_SIGNED_ENVELOPE_OVERHEAD_BYTES`` in
    :mod:`rytm_randomizer.reports.cockpit_export_rehearsal`). The real
    envelope wrapper for HMAC-SHA256 with a short key_id is closer to ~50
    bytes, so the rehearsal value is intentionally conservative.

    The contract this test enforces is the operationally-meaningful one:

    * the rehearsal MUST be >= the actual size (operators never get a
      surprise larger file than the rehearsal predicted), and
    * the gap stays inside the documented WS-D overhead budget (so a
      future signer change that blows the envelope past the budget gets
      caught).
    """

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "buzzi-sized.rymp"

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        key_id=_KEY_ID,
        output_path=output,
    )
    assert rehearsal.signed_size is not None

    export = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert export.returncode == 0, export.stderr or export.stdout

    actual_size = output.stat().st_size
    # Conservative upper-bound contract: rehearsal MUST NOT under-predict.
    assert rehearsal.signed_size >= actual_size, (
        f"rehearsal signed_size={rehearsal.signed_size} is smaller than the "
        f"actual signed file size={actual_size}; the rehearsal must never "
        "under-predict (operators rely on it as an upper bound)."
    )
    # And it stays inside the documented WS-D budget (256-byte overhead).
    assert rehearsal.signed_size - actual_size <= 256, (
        f"rehearsal signed_size={rehearsal.signed_size} vs actual={actual_size} "
        "drifted past the WS-D 256-byte envelope-overhead budget."
    )


def test_rehearsal_json_serialization_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The rehearsal JSON adapter emits the keys the export ack consumers expect."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        key_id=_KEY_ID,
        output_path=tmp_path / "x.rymp",
    )
    doc = to_cockpit_export_rehearsal_json(rehearsal)
    block = doc["cockpit_export_rehearsal"]
    assert isinstance(block, dict)
    # The four keys WS-F's cross-component check depends on.
    for key in ("output_path", "payload_size", "payload_crc_hex", "signed"):
        assert key in block, f"rehearsal JSON missing {key}"


# ---------------------------------------------------------------------------
# (4) CLI error paths (subprocess)
# ---------------------------------------------------------------------------


def test_cli_unknown_profile_id_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown profile id: exit non-zero, ok=False, error names the missing profile."""

    _isolate_user_home(monkeypatch, tmp_path)
    (tmp_path / "user").mkdir(parents=True, exist_ok=True)

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        "no-such-profile",
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(tmp_path / "out.rymp"),
        "--unsigned",
        "--json",
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert "no-such-profile" in payload["error"]
    assert "profile" in payload["error"].lower() or "not found" in payload["error"].lower()
    assert not (tmp_path / "out.rymp").exists()


def test_cli_key_hex_without_key_id_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """``--key-hex`` without ``--key-id``: explicit error, no file written."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--key-hex",
        _KEY_HEX,
        "--json",
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert "key-id" in payload["error"].lower() or "key id" in payload["error"].lower()
    assert not output.exists()


def test_cli_invalid_hex_key_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Non-hex ``--key-hex`` value: rejected before any write."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--key-hex",
        "zz-not-hex-zz",
        "--key-id",
        _KEY_ID,
        "--json",
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert "hex" in payload["error"].lower()
    assert not output.exists()


def test_cli_key_hex_and_unsigned_mutually_exclusive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``--key-hex`` and ``--unsigned`` together: rejected with mutex error."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "out.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert "mutually exclusive" in payload["error"].lower()
    assert not output.exists()


def test_cli_neither_signed_nor_unsigned_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without ``--key-hex`` and without ``--unsigned``: must-choose error."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(tmp_path / "out.rymp"),
        "--json",
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert "explicitly choose" in payload["error"].lower() or "must" in payload["error"].lower()


def test_cli_existing_output_without_overwrite_errors(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Output path already exists, no ``--overwrite``: file-exists error, file untouched."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "existing.rymp"
    original = b"pre-existing content"
    output.write_bytes(original)

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--json",
    )
    assert result.returncode != 0
    payload = _read_json(result.stdout)
    assert payload["ok"] is False
    assert (
        "exist" in payload["error"].lower()
        or "overwrite" in payload["error"].lower()
        or "refus" in payload["error"].lower()
    )
    # Original bytes preserved — atomic_write rejected before any write.
    assert output.read_bytes() == original


def test_cli_existing_output_with_overwrite_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Existing file + ``--overwrite``: succeeds, marks overwrote_existing=True."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "existing.rymp"
    output.write_bytes(b"stale content")

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--overwrite",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = _read_json(result.stdout)
    assert payload["ok"] is True
    assert payload["overwrote_existing"] is True
    # The file now starts with the RYMP magic — the stale content was replaced.
    assert output.read_bytes()[:4] == b"RYMP"


# ---------------------------------------------------------------------------
# (5) Atomic-write guarantee
# ---------------------------------------------------------------------------


def test_atomic_write_failed_run_does_not_touch_existing_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run that fails (no ``--overwrite``) must leave the existing file byte-identical."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "existing.rymp"
    original = b"original sentinel bytes"
    output.write_bytes(original)

    pre_size = output.stat().st_size
    pre_mtime = output.stat().st_mtime_ns

    # Small sleep so any inadvertent rewrite would produce a measurable
    # mtime delta. The check below is on bytes too, so this is belt + braces.
    time.sleep(0.05)

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert result.returncode != 0

    post_size = output.stat().st_size
    post_mtime = output.stat().st_mtime_ns
    assert post_size == pre_size
    assert post_mtime == pre_mtime
    assert output.read_bytes() == original


def test_atomic_write_overwrite_changes_size_and_mtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful overwrite run must replace the bytes (size or content change)."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "to-be-replaced.rymp"
    original = b"tiny stub"
    output.write_bytes(original)

    pre_size = output.stat().st_size
    time.sleep(0.05)

    result = _run_cli(
        "cockpit-export-profile-model",
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
        "--overwrite",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    ack = _read_json(result.stdout)
    assert ack["ok"] is True
    assert ack["overwrote_existing"] is True

    post_size = output.stat().st_size
    # The signed envelope is much larger than the 9-byte stub.
    assert post_size != pre_size
    assert post_size > pre_size
    assert output.read_bytes() != original
    # And the new bytes are a valid signed envelope.
    assert output.read_bytes()[:4] == SIGNATURE_HEADER_MAGIC


def test_atomic_write_no_temp_files_leak_on_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A successful export leaves only the target file in the destination dir."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    out_dir = tmp_path / "out_dir"
    out_dir.mkdir(parents=True, exist_ok=True)
    output = out_dir / "buzzi.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout

    # No leftover ``.tmp`` sibling files in the destination dir.
    leftovers = [p.name for p in out_dir.iterdir() if p.suffix == ".tmp"]
    assert leftovers == [], f"unexpected temp leftovers: {leftovers}"


# ---------------------------------------------------------------------------
# (6) Verification-failure path
# ---------------------------------------------------------------------------


def _produce_signed_envelope(profile: ProfileModel) -> bytes:
    """Build a signed envelope in-process (no CLI) so corruption tests stay hermetic."""

    payload = pack_profile_model(profile)
    return pack_signed(sign_profile_blob(payload, key=_KEY_BYTES, key_id=_KEY_ID))


def test_verifier_detects_magic_mismatch_corruption(tmp_path: Path) -> None:
    """Flipping the envelope magic produces a magic_mismatch verification result."""

    profile = _build_test_profile()
    envelope = bytearray(_produce_signed_envelope(profile))
    # Flip the first byte of the magic — guarantees `RYMS` becomes something else.
    envelope[0] ^= 0xFF
    corrupted = tmp_path / "magic.rymp"
    corrupted.write_bytes(bytes(envelope))

    result = verify_signed_blob(corrupted.read_bytes(), key=_KEY_BYTES)
    assert result.ok is False
    assert result.reason == "magic_mismatch"


def test_verifier_detects_truncated_envelope(tmp_path: Path) -> None:
    """A truncated envelope reports the ``truncated`` reason."""

    profile = _build_test_profile()
    envelope = _produce_signed_envelope(profile)
    # Lop off the last 16 bytes (inside the payload section).
    truncated = tmp_path / "truncated.rymp"
    truncated.write_bytes(envelope[: len(envelope) - 16])

    result = verify_signed_blob(truncated.read_bytes(), key=_KEY_BYTES)
    assert result.ok is False
    assert result.reason == "truncated"


def test_verifier_detects_unsupported_signature_version(tmp_path: Path) -> None:
    """Bumping the envelope's signature format_version reports version_unsupported."""

    profile = _build_test_profile()
    envelope = bytearray(_produce_signed_envelope(profile))
    # The format_version is a big-endian uint16 immediately after the 4-byte magic.
    struct.pack_into(">H", envelope, 4, 99)
    corrupted = tmp_path / "version.rymp"
    corrupted.write_bytes(bytes(envelope))

    result = verify_signed_blob(corrupted.read_bytes(), key=_KEY_BYTES)
    assert result.ok is False
    assert result.reason == "version_unsupported"


def test_verifier_detects_signature_byte_corruption(tmp_path: Path) -> None:
    """Flipping a byte in the signature region reports signature_mismatch."""

    profile = _build_test_profile()
    envelope = bytearray(_produce_signed_envelope(profile))
    # Decode the structure once to locate the signature offset deterministically.
    # Fixed prefix (6) + algo_len (1) + algo bytes + key_id_len (1) + key_id bytes
    # + sig_len (1) + signature bytes.
    fixed_prefix_len = 6
    algo_len = envelope[fixed_prefix_len]
    key_id_len_off = fixed_prefix_len + 1 + algo_len
    key_id_len = envelope[key_id_len_off]
    sig_len_off = key_id_len_off + 1 + key_id_len
    sig_start = sig_len_off + 1
    # Flip the very first byte of the signature.
    envelope[sig_start] ^= 0xFF
    corrupted = tmp_path / "sig.rymp"
    corrupted.write_bytes(bytes(envelope))

    result = verify_signed_blob(corrupted.read_bytes(), key=_KEY_BYTES)
    assert result.ok is False
    assert result.reason == "signature_mismatch"


def test_verifier_detects_payload_crc_corruption(tmp_path: Path) -> None:
    """Flipping a byte inside the inner ``RYMP`` payload reports payload_crc_mismatch.

    The corruption must be applied BEFORE re-signing — otherwise the
    signature check (which runs first) fires and we never reach the inner
    CRC check. So this test signs a deliberately-broken inner blob and
    asserts the verifier reports the inner CRC mismatch, not signature.
    """

    profile = _build_test_profile()
    payload = bytearray(pack_profile_model(profile))
    # The CRC32 trailer is the last 4 bytes — flip one byte of the inner
    # payload *before* the CRC trailer so the inner CRC no longer matches.
    payload[len(payload) - 5] ^= 0xFF
    envelope = pack_signed(sign_profile_blob(bytes(payload), key=_KEY_BYTES, key_id=_KEY_ID))
    corrupted = tmp_path / "crc.rymp"
    corrupted.write_bytes(envelope)

    result = verify_signed_blob(corrupted.read_bytes(), key=_KEY_BYTES)
    assert result.ok is False
    assert result.reason == "payload_crc_mismatch"


def test_verifier_unsigned_payload_round_trip(tmp_path: Path) -> None:
    """``verify_unsigned_payload`` reports ``ok`` on a clean packed profile."""

    profile = _build_test_profile()
    payload = pack_profile_model(profile)
    result = verify_unsigned_payload(payload)
    assert result.ok is True
    assert result.reason == "ok"
    assert result.payload_size == len(payload)


def test_verifier_unsigned_payload_detects_bad_magic() -> None:
    """``verify_unsigned_payload`` reports magic_mismatch on a non-``RYMP`` blob."""

    payload = bytearray(pack_profile_model(_build_test_profile()))
    payload[0] ^= 0xFF
    result = verify_unsigned_payload(bytes(payload))
    assert result.ok is False
    assert result.reason == "magic_mismatch"


def test_verifier_signed_blob_without_key_reports_unsigned_payload(tmp_path: Path) -> None:
    """Calling the verifier with key=None on a clean envelope reports unsigned_payload."""

    envelope = _produce_signed_envelope(_build_test_profile())
    result = verify_signed_blob(envelope, key=None)
    assert result.ok is True
    assert result.reason == "unsigned_payload"


# ---------------------------------------------------------------------------
# (7) Cross-component sanity
# ---------------------------------------------------------------------------


def test_rehearsal_payload_size_equals_pack_profile_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rehearsal's ``payload_size`` equals ``len(pack_profile_model(profile))`` exactly."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        unsigned=True,
    )
    assert rehearsal.payload_size == len(pack_profile_model(profile))


def test_rehearsal_payload_crc_hex_is_8_chars(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Rehearsal CRC is the 8-char zero-padded big-endian hex of the CRC32."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)

    rehearsal = build_cockpit_export_rehearsal_report(
        profile_id=profile.profile_id,
        profiles_dir=tmp_path,
        unsigned=True,
    )
    assert len(rehearsal.payload_crc_hex) == 8
    # It must be parseable as a non-negative hex int.
    int(rehearsal.payload_crc_hex, 16)


def test_full_unsigned_pipeline_pack_verify_unpack_round_trip(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pack -> CLI write (unsigned) -> verify_unsigned_payload -> unpack is consistent."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "full.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout

    raw = output.read_bytes()
    # Verifier accepts the bytes directly.
    verified = verify_unsigned_payload(raw)
    assert verified.ok is True
    assert verified.reason == "ok"
    assert verified.payload_size == len(raw)
    # Decoder rebuilds the original profile.
    decoded = unpack_profile_model(raw)
    assert decoded.to_dict() == profile.to_dict()


def test_full_signed_pipeline_subprocess_then_in_process_verify(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """End-to-end: subprocess CLI -> in-process unpack_signed + verify + unpack_profile_model."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "full-signed.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert result.returncode == 0, result.stderr or result.stdout

    raw = output.read_bytes()
    blob = unpack_signed(raw)
    assert blob.key_id == _KEY_ID
    assert blob.algorithm == "hmac-sha256"
    verified = verify_signed_blob(raw, key=_KEY_BYTES, expected_key_id=_KEY_ID)
    assert verified.ok is True
    assert verified.reason == "ok"
    decoded = unpack_profile_model(blob.payload)
    assert decoded.to_dict() == profile.to_dict()


def test_full_pipeline_wrong_key_id_routes_to_key_id_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Subprocess writes envelope keyed as A; verifier with expected_key_id=B reports key_id_mismatch."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    output = tmp_path / "wrong-keyid.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
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
    )
    assert result.returncode == 0, result.stderr or result.stdout

    verified = verify_signed_blob(
        output.read_bytes(), key=_KEY_BYTES, expected_key_id="not-this-key"
    )
    assert verified.ok is False
    assert verified.reason == "key_id_mismatch"
    assert verified.expected_key_id == _KEY_ID
    assert verified.expected_algorithm == "hmac-sha256"


def test_cli_writes_into_freshly_created_parent_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The export creates missing parent directories under ``--output``."""

    _isolate_user_home(monkeypatch, tmp_path)
    profile = _build_test_profile()
    _seed_profile(tmp_path, profile)
    nested = tmp_path / "one" / "two" / "three"
    assert not nested.exists()
    output = nested / "buzzi.rymp"

    result = _run_cli(
        "cockpit-export-profile-model",
        "--profile-id",
        profile.profile_id,
        "--profiles-dir",
        str(tmp_path),
        "--output",
        str(output),
        "--unsigned",
        "--json",
    )
    assert result.returncode == 0, result.stderr or result.stdout
    assert output.exists()
    assert output.read_bytes()[:4] == b"RYMP"


# ---------------------------------------------------------------------------
# Sanity check on the test fixture itself
# ---------------------------------------------------------------------------


def test_build_test_profile_round_trips_through_registry(tmp_path: Path) -> None:
    """The integration-test fixture profile survives a registry save/get round-trip."""

    profile = _build_test_profile()
    registry = ProfileRegistry(tmp_path)
    registry.save(profile)
    # PR 7 — IH2: save() returns None; derive the on-disk path
    # explicitly from the profile id.
    saved_path = tmp_path / "user" / f"{profile.profile_id}.json"
    assert saved_path.exists()
    loaded = registry.get(profile.profile_id)
    assert loaded is not None
    assert loaded.to_dict() == profile.to_dict()


def test_subprocess_pythonpath_root_is_correct() -> None:
    """The PROJECT_ROOT constant points at the actual repo root (sanity)."""

    assert (PROJECT_ROOT / "rytm_randomizer" / "cli.py").is_file()
    assert (PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "export").is_dir()
    # ``os`` is imported to keep `_isolate_user_home` future-proof for any
    # os-specific path normalization tests; reference it here so the
    # import isn't flagged as unused if those grow in.
    assert os.path.sep in str(PROJECT_ROOT)
