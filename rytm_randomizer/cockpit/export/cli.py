"""End-to-end export CLI for cockpit ``ProfileModel`` artifacts.

Drives the full pack → (optional sign) → atomic write → verify pipeline
behind a single passive subcommand::

    python -m rytm_randomizer.cli cockpit-export-profile-model \\
        --profile-id <id> --profiles-dir <path> \\
        --output <file.rymp> \\
        [--key-env <ENV_VAR_NAME> --key-id <label>] \\
        [--key-hex <hexkey> --key-id <label>] \\
        [--unsigned] [--overwrite] [--json]

The flow on success:

1. Load the ``ProfileModel`` from ``ProfileRegistry(profiles_dir).get(profile_id)``.
2. Pack it via :func:`pack_profile_model`.
3. If signing is requested, :func:`sign_profile_blob` + :func:`pack_signed`
   the payload; otherwise emit the raw ``RYMP`` blob.
4. :func:`atomic_write` the envelope to ``output``.
5. Read the bytes back and :func:`verify_signed_blob` them — this is the
   post-write integrity check operators rely on.
6. Emit a structured ack (JSON if ``--json``, otherwise text).

Key-material delivery (CODE_REVIEW.md SX2)
------------------------------------------

The signing key is hex-encoded bytes. Two channels are accepted:

* **``--key-env <ENV_VAR_NAME>``** — the RECOMMENDED path. The CLI reads
  the named env var and uses its value as the key hex. The env var
  contents NEVER appear in ``/proc/<pid>/cmdline``, so a second local
  user cannot capture the key by listing processes. CI/Tauri/shell
  invocations should always use this path.
* **``--key-hex <hex>``** — DEPRECATED (kept for backward compat). The
  key hex appears verbatim in ``/proc/<pid>/cmdline`` on Linux/macOS
  and in ``Get-Process`` output on Windows for the brief window the
  subcommand runs; any local user with read access to the process
  table can capture it. A structured warning is logged whenever this
  path is used so operators can spot it in CI logs.

The two are mutually exclusive — passing both raises a validation
error rather than silently picking one.

Validation rules (every failure produces ``ok=False`` and a non-zero exit
code — no exceptions ever escape the handler):

* Any key flag AND ``--unsigned``: mutually exclusive.
* Any key flag without ``--key-id``: ``key-id`` required when key is given.
* ``--key-id`` without any key flag: a key channel is required.
* Both ``--key-env`` and ``--key-hex``: mutually exclusive — pick one.
* ``--key-env`` names an unset / empty env var: reported with the name.
* Key value not valid hex: rejected before file work.
* Neither key channel nor ``--unsigned``: explicit choice required.
* ``--profile-id`` not in registry: reported with the offending id.
* Missing required value for any option: usage hint.

The signing surface comes from sibling modules (``signing``, ``verifier``);
the atomic-write surface comes from sibling :mod:`.writer` (a hard import:
if the writer module is missing the import fails loudly at module load
rather than silently swapping in a behavioural near-duplicate).
"""

from __future__ import annotations

import json
import os
import sys
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import msgpack

from ...cli_registry import CliCommand
from ...cli_registry import register as _registry_register
from ...observability.logging import get_logger
from ...observability.metrics import get_metrics
from .serialize import pack_profile_model
from .signing import pack_signed, sign_profile_blob
from .verifier import verify_signed_blob, verify_unsigned_payload

# Hard import (no try/except fallback): if the writer module is missing
# this raises ``ImportError`` at module load. Silently substituting a
# behavioural near-duplicate (different overwrite-refusal exception,
# different default-export dir, raw ``OSError`` instead of the
# project-typed ``WriteError``) is exactly the divergence Gate 17 was
# lifted to prevent.
from .writer import WriteError, WriteResult, atomic_write, default_export_dir

_logger = get_logger(__name__)
"""Module logger for the cockpit export CLI. Bound here so PR O2 (RED
metrics for the export pipeline) and PR O6 (arch tests on hot-path
loggers) can wire their structured events without touching this file's
imports. See ``OBSERVABILITY_REVIEW.md`` Phase 5."""

_COMMAND_NAME: Final[str] = "cockpit-export-profile-model"
"""Subcommand token registered with the cli dispatcher."""

_USAGE: Final[str] = (
    f"{_COMMAND_NAME} usage: "
    "--profile-id <id> --profiles-dir <path> --output <file.rymp> "
    "[--key-env <ENV_VAR_NAME> | --key-hex <hex>] --key-id <label> "
    "[--unsigned] [--overwrite] [--json]"
)
"""Single-line usage string echoed on parse errors."""

_KEY_HEX_DEPRECATION_LOG_EVENT: Final[str] = "deprecated_key_hex_argv_used"
"""Structured log event name for SX2 --key-hex deprecation warnings.

Operators grep this event in CI / Tauri logs to spot environments still
delivering keys via argv. The event is emitted exactly once per CLI
invocation that uses ``--key-hex``."""


@dataclass(frozen=True)
class _CliOptions:
    """Parsed command-line options (validated structurally, not semantically).

    The validator (``_validate``) performs the cross-field semantic checks
    — mutually-exclusive flags, signing-mode completeness — separately so
    parse errors and validation errors are reported with distinct wording.
    """

    profile_id: str
    profiles_dir: Path
    output: Path
    key_hex: str | None
    key_env: str | None
    key_id: str | None
    unsigned: bool
    overwrite: bool
    json_output: bool


def _pop_value(remaining: list[str], option: str) -> str:
    """Pop the next CLI option value or raise ``ValueError`` with usage."""

    if not remaining:
        raise ValueError(f"{option} requires a value. {_USAGE}")
    return remaining.pop(0)


def _parse_args(args: Sequence[str]) -> _CliOptions:
    """Walk ``args`` left-to-right collecting recognized options.

    Required positional inputs (``--profile-id``, ``--profiles-dir``,
    ``--output``) raise :class:`ValueError` if absent — those errors get
    converted into ``ok=False`` acks one layer up.
    """

    profile_id: str | None = None
    profiles_dir: Path | None = None
    output: Path | None = None
    key_hex: str | None = None
    key_env: str | None = None
    key_id: str | None = None
    unsigned = False
    overwrite = False
    json_output = False

    remaining = list(args)
    while remaining:
        option = remaining.pop(0)
        if option == "--profile-id":
            profile_id = _pop_value(remaining, option)
        elif option == "--profiles-dir":
            profiles_dir = Path(_pop_value(remaining, option))
        elif option == "--output":
            output = Path(_pop_value(remaining, option))
        elif option == "--key-hex":
            key_hex = _pop_value(remaining, option)
        elif option == "--key-env":
            key_env = _pop_value(remaining, option)
        elif option == "--key-id":
            key_id = _pop_value(remaining, option)
        elif option == "--unsigned":
            unsigned = True
        elif option == "--overwrite":
            overwrite = True
        elif option == "--json":
            json_output = True
        else:
            raise ValueError(f"unknown option {option!r}. {_USAGE}")

    if profile_id is None:
        raise ValueError(f"--profile-id is required. {_USAGE}")
    if profiles_dir is None:
        raise ValueError(f"--profiles-dir is required. {_USAGE}")
    if output is None:
        raise ValueError(f"--output is required. {_USAGE}")

    return _CliOptions(
        profile_id=profile_id,
        profiles_dir=profiles_dir,
        output=output,
        key_hex=key_hex,
        key_env=key_env,
        key_id=key_id,
        unsigned=unsigned,
        overwrite=overwrite,
        json_output=json_output,
    )


def _validate(options: _CliOptions) -> None:
    """Cross-field semantic validation. Raises :class:`ValueError` on failure."""

    has_hex = options.key_hex is not None
    has_env = options.key_env is not None
    has_key = has_hex or has_env
    has_key_id = options.key_id is not None

    if has_hex and has_env:
        raise ValueError(
            "--key-hex and --key-env are mutually exclusive. Pick one channel "
            "for the signing key (prefer --key-env for security — SX2)."
        )
    if has_key and options.unsigned:
        raise ValueError(
            "--key-hex/--key-env and --unsigned are mutually exclusive — "
            "a key flag implies a signed export"
        )
    if has_key and not has_key_id:
        raise ValueError("--key-id is required when --key-hex/--key-env is provided")
    if has_key_id and not has_key:
        raise ValueError("--key-hex or --key-env is required when --key-id is provided")
    if not has_key and not options.unsigned:
        raise ValueError(
            "must explicitly choose --key-env/--key-id (preferred), "
            "--key-hex/--key-id (deprecated — SX2), or --unsigned "
            "— no silent default"
        )


def _resolve_key_hex(options: _CliOptions) -> str:
    """Return the hex-encoded key for ``options``.

    Reads from ``--key-env`` (preferred) or ``--key-hex`` (deprecated).
    The two are mutually exclusive at the validation layer, so exactly
    one channel is set when this function runs.

    The ``--key-hex`` path emits a structured deprecation log event
    so operators can spot environments still leaking keys via
    ``/proc/<pid>/cmdline``. The fix: switch the caller to
    ``--key-env RYTM_RAND_KEY_HEX`` and set the env var instead.

    Raises ``ValueError`` if ``--key-env`` names an env var that is
    unset or empty — without that check the operator gets a confusing
    "key is empty hex" error one layer down.
    """

    if options.key_env is not None:
        # ``--key-env`` is the secure path — value lives in the
        # process environ, not argv, so /proc/<pid>/cmdline doesn't
        # leak it.
        raw = os.environ.get(options.key_env)
        if raw is None or raw == "":
            raise ValueError(
                f"--key-env {options.key_env!r} names an env var that is "
                "unset or empty. Set the env var to the hex-encoded key "
                "before invoking the export command."
            )
        return raw
    # ``--key-hex`` path — log a deprecation warning so operators can
    # find argv-leak invocations in shipped log streams. The key bytes
    # themselves are NEVER logged (only the deprecation marker).
    _logger.warning(
        _KEY_HEX_DEPRECATION_LOG_EVENT,
        extra={
            "channel": "argv",
            "recommendation": "use --key-env <ENV_VAR_NAME> instead",
            "vulnerability": "SX2",
        },
    )
    # ``--key-hex`` must be set here per the _validate XOR contract.
    # Belt-and-braces: if a future refactor breaks the invariant, fail
    # loud with a recognisable message rather than returning ``None``.
    if options.key_hex is None:  # pragma: no cover - validator contract
        raise ValueError(
            "_resolve_key_hex called with neither --key-env nor --key-hex set "
            "(validator contract broken — fix _validate)"
        )
    return options.key_hex


def _decode_key(key_hex: str, *, source: str) -> bytes:
    """Decode a hex-encoded signing key or raise ``ValueError`` on bad input.

    ``source`` is a short label such as ``"--key-env <NAME>"`` or
    ``"--key-hex"`` used in the error message so the operator knows
    which channel produced the bad hex.
    """

    try:
        return bytes.fromhex(key_hex)
    except ValueError as exc:
        raise ValueError(f"{source} is invalid hex: {exc}") from exc


def _verification_to_dict(*, blob: bytes, signed: bool, key: bytes | None) -> dict[str, object]:
    """Build the verification sub-dict for the ack payload.

    Re-runs the verifier against the bytes that were just written so the
    ack reflects what an operator would see on a fresh load. ``signed``
    determines which entry point we use.
    """

    if signed:
        result = verify_signed_blob(blob, key=key)
    else:
        result = verify_unsigned_payload(blob)
    return {
        "ok": result.ok,
        "reason": result.reason,
        "expected_key_id": result.expected_key_id,
        "expected_algorithm": result.expected_algorithm,
        "payload_size": result.payload_size,
    }


def _build_result(
    *,
    options: _CliOptions,
    profile_id: str,
    profile_name: str,
    model_version: str,
    write_result: WriteResult,
    written_bytes: bytes,
    signed: bool,
    key: bytes | None,
) -> dict[str, object]:
    """Assemble the operator-facing ack dict for a successful export."""

    verification = _verification_to_dict(blob=written_bytes, signed=signed, key=key)
    payload: dict[str, object] = {
        "ok": verification["ok"] is True,
        "profile_id": profile_id,
        "profile_name": profile_name,
        "model_version": model_version,
        "output_path": str(write_result.path),
        "bytes_written": write_result.bytes_written,
        "overwrote_existing": write_result.overwrote_existing,
        "signed": signed,
        "verification": verification,
    }
    if signed:
        payload["key_id"] = options.key_id
    return payload


def _format_text(payload: dict[str, object]) -> str:
    """Format an ack dict as a human-readable, key: value block."""

    lines: list[str] = []
    # `field` rather than `key` so it doesn't read as if it shadowed
    # any of the HMAC-key-related names elsewhere in this module (L2
    # from CODE_REVIEW.md).
    for field in (
        "ok",
        "profile_id",
        "profile_name",
        "model_version",
        "output_path",
        "bytes_written",
        "overwrote_existing",
        "signed",
    ):
        if field in payload:
            lines.append(f"{field}: {_json_scalar(payload[field])}")
    if "key_id" in payload:
        lines.append(f"key_id: {_json_scalar(payload['key_id'])}")
    if "error" in payload:
        lines.append(f"error: {payload['error']}")
    verification = payload.get("verification")
    if isinstance(verification, dict):
        for field in ("ok", "reason", "expected_key_id", "expected_algorithm", "payload_size"):
            lines.append(f"verification.{field}: {_json_scalar(verification[field])}")
    return "\n".join(lines) + "\n"


def _json_scalar(value: object) -> str:
    """Render a scalar the same way JSON would (``true``/``false``/``null``)."""

    if value is True:
        return "true"
    if value is False:
        return "false"
    if value is None:
        return "null"
    return str(value)


def _emit(payload: dict[str, object], *, json_output: bool) -> None:
    """Write the ack payload to stdout in the requested format."""

    if json_output:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True))
        sys.stdout.write("\n")
        return
    sys.stdout.write(_format_text(payload))


def _error_payload(message: str) -> dict[str, object]:
    """Build a deterministic ``ok=False`` ack from an error message."""

    return {"ok": False, "error": message}


def _classify_export_error(exc: BaseException) -> str:
    """Map an export-pipeline exception to a categorical RED-metrics label.

    Kept deliberately small and stable — these strings show up in the
    ``export_errors_by_code`` counter histogram operators scan at shell
    exit. A free-form ``type(exc).__name__`` would explode the cardinality
    and defeat the purpose of a categorized counter (cf. the same rule
    enforced for ``record_error``).
    """

    if isinstance(exc, FileExistsError):
        return "overwrite_refused"
    if isinstance(exc, OSError):
        return "write_failed"
    if isinstance(exc, OverflowError):
        return "pack_overflow"
    if isinstance(exc, msgpack.exceptions.PackException):
        return "pack_failed"
    if isinstance(exc, (ValueError, TypeError)):
        return "validation"
    return "unknown"  # pragma: no cover - belt-and-braces; all known paths hit above


def handle_export_profile_model(args: Sequence[str]) -> int:
    """Parse, validate, execute the export pipeline. Return the exit code.

    Every exception path converts to ``ok=False`` and a non-zero exit
    code; no exception ever escapes the handler. The CLI dispatcher
    relies on this contract — the registered ``CliCommand`` does not set
    an ``error_formatter`` because there are no parser errors to format.
    """

    args_list = list(args)
    # ``json_output`` is parsed once early so error acks before validation
    # complete still respect the operator's chosen format.
    json_output = "--json" in args_list
    # OBS O2 — RED metrics. Time the whole pipeline (parse + validate +
    # pack + sign + write + verify). The metric is recorded exactly once
    # at exit, on every code path, via the ``finally`` block below so
    # rate/error/duration stays accurate even if a future contributor
    # adds an early return.
    _metrics = get_metrics()
    _t0 = time.perf_counter()
    _error_code: str | None = None
    try:
        options = _parse_args(args_list)
        json_output = options.json_output
        _validate(options)

        key_bytes: bytes | None = None
        if (options.key_hex is not None or options.key_env is not None) and (
            options.key_id is not None
        ):
            key_hex = _resolve_key_hex(options)
            source = (
                f"--key-env {options.key_env!r}" if options.key_env is not None else "--key-hex"
            )
            key_bytes = _decode_key(key_hex, source=source)

        # Local import keeps the cockpit-data import out of the hot path
        # for ``--help`` and parse-failure invocations.
        from rytm_randomizer.cockpit.profiles import ProfileRegistry

        registry = ProfileRegistry(options.profiles_dir)
        profile = registry.get(options.profile_id)
        if profile is None:
            raise ValueError(f"unknown profile_id: {options.profile_id}")

        payload = pack_profile_model(profile)
        signed = key_bytes is not None
        if signed and options.key_id is not None and key_bytes is not None:
            envelope = pack_signed(sign_profile_blob(payload, key=key_bytes, key_id=options.key_id))
        else:
            envelope = payload

        write_result = atomic_write(options.output, envelope, overwrite=options.overwrite)
        written_bytes = write_result.path.read_bytes()

        ack = _build_result(
            options=options,
            profile_id=profile.profile_id,
            profile_name=profile.name,
            model_version=profile.model_version,
            write_result=write_result,
            written_bytes=written_bytes,
            signed=signed,
            key=key_bytes,
        )
    except (
        # Validation / arg-parse errors (``_parse_args``, ``_validate``,
        # ``_decode_key``, ``pack_signed`` width caps, ``serialize`` /
        # ``model_format`` field-shape errors, ``ProfileModel.from_dict``).
        ValueError,
        TypeError,
        # ``pack_profile_model`` -> ``msgpack.packb`` can raise
        # ``PackOverflowError`` (an ``OverflowError`` subclass) for an
        # int that does not fit msgpack's wire range. Catch the broader
        # ``OverflowError`` so future overflow paths stay swallowed too.
        OverflowError,
        # ``atomic_write`` raises ``FileExistsError`` on overwrite
        # refusal and ``WriteError`` (a ``DataError`` + ``OSError``) on
        # any underlying ``OSError`` from write / fsync / replace. The
        # ``OSError`` base catches both.
        OSError,
        # ``msgpack.packb`` can raise ``PackException`` (a bare
        # ``Exception`` subclass) on any other pack failure — type
        # not serializable, recursion-depth overflow, etc. Caught
        # explicitly so it does not escape the handler.
        msgpack.exceptions.PackException,
    ) as exc:
        _error_code = _classify_export_error(exc)
        ack = _error_payload(str(exc))
        _emit(ack, json_output=json_output)
        _metrics.record_export((time.perf_counter() - _t0) * 1000.0, error_code=_error_code)
        return 2

    _emit(ack, json_output=json_output)
    ok = ack.get("ok") is True
    if not ok and _error_code is None:
        # ack.ok is False but no exception was raised — the verifier
        # rejected the bytes just written. Record under a distinct bucket
        # so operators can spot post-write integrity regressions.
        _error_code = "verify_failed"
    _metrics.record_export((time.perf_counter() - _t0) * 1000.0, error_code=_error_code)
    return 0 if ok else 2


def _parse_for_registry(argv: Sequence[str]) -> dict[str, object]:
    """Adapter for the CLI registry's ``args_parser`` contract.

    The registry expects ``argv -> dict[str, Any]``; the handler accepts
    a single ``args`` list. Wrapping keeps the handler simple to test in
    isolation while still allowing dispatch through the registry.
    """

    return {"args": list(argv)}


def _handle_for_registry(*, args: Sequence[str]) -> int:
    """Adapter for the CLI registry's ``handler`` contract."""

    return handle_export_profile_model(args)


COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name=_COMMAND_NAME,
    summary=("Export a cockpit ProfileModel artifact " "(pack + sign + atomic write + verify)."),
    args_parser=_parse_for_registry,
    handler=_handle_for_registry,
)
"""Registered ``CliCommand`` for the lazy dispatcher to look up."""

_registry_register(COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND)


__all__ = [
    "COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND",
    # Re-exported writer surface so callers that previously imported
    # these names from this module (when the WS-B fallback lived here)
    # keep working — the canonical home is :mod:`.writer`.
    "WriteError",
    "WriteResult",
    "atomic_write",
    "default_export_dir",
    "handle_export_profile_model",
]
