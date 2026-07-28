"""Architecture invariants pinning the Phase 3 cockpit export-pipeline contract.

The cockpit ``ProfileModel`` export format (``rytm_randomizer/cockpit/export/``)
is the on-disk artifact the Phase 4 embedded hardware loader will consume.
The shape of that artifact — magic prefix, format version, public Python
surface, signing envelope, round-trip contract — is **a wire-format
commitment**. Once Phase 4 firmware exists, the only way to evolve the
format is to bump :data:`FORMAT_VERSION` and teach both sides about the new
shape; silently re-shaping any of these constants strands every device
that already has an older loader baked in.

Each test in this module exists because a real review caught (or could have
caught) a real way to silently break the Phase-3-to-Phase-4 contract:

1. **MAGIC bytes** — the firmware reader's first sanity check; rotating
   these from ``"RYMP"`` to anything else stops every existing binary
   from loading without raising a useful error.
2. **FORMAT_VERSION + SUPPORTED_FORMAT_VERSIONS** — pin the supported set
   so a future PR cannot drop a version without also breaking the
   firmware compat matrix.
3. **Public surface** — the names a downstream packer/unpacker imports.
   Renaming any of these is a silent breakage for the firmware build's
   Python-side encoder.
4. **No MIDI imports** — the export pipeline is a *passive* offline
   encoder; pulling ``mido`` or ``cockpit.ws.server`` in here would mean
   the embedded toolchain inherits a desktop-only dependency.
5. **Round-trip identity** — a smoke-level pack→unpack→equality check
   so this test file alone protects the most-common breakage class
   (a serialization-field rename that survives type-checking but
   loses data on the wire).

Every test is fast (file IO + import + a tiny in-memory ProfileModel).
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
EXPORT_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "export"


# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------


def test_export_pipeline_format_magic_is_rymp() -> None:
    """The on-disk magic prefix must remain exactly ``b"RYMP"``.

    Regression guard: the Phase 4 firmware reader's first sanity check is
    ``memcmp(blob, "RYMP", 4)``. Rotating the constant on the Python side
    silently strands every previously-exported model file — the firmware
    rejects them as "bad magic" with no migration path. A four-byte
    constant is exactly the kind of thing a refactor can "tidy up" by
    accident; pinning it here makes the change a loud test failure.
    """

    from rytm_randomizer.cockpit.export import model_format

    assert model_format.MAGIC == b"RYMP", (
        "rytm_randomizer/cockpit/export/model_format.py::MAGIC must remain "
        f'exactly b"RYMP"; got {model_format.MAGIC!r}. This is a wire-format '
        "commitment to the Phase 4 firmware loader — bump FORMAT_VERSION "
        "instead of mutating the magic prefix."
    )


def test_export_pipeline_format_version_is_documented() -> None:
    """FORMAT_VERSION must be in SUPPORTED_FORMAT_VERSIONS.

    Regression guard: it is mechanically possible to bump
    ``FORMAT_VERSION`` to ``2`` while leaving ``SUPPORTED_FORMAT_VERSIONS``
    as ``frozenset({1})`` — then every freshly-packed model is
    immediately unreadable by the same Python process that wrote it.
    The matching firmware breakage is even worse (the device can't even
    write at all). This invariant pins the emit-side version into the
    accept-side set so the unpacker can always read what the packer
    produced.
    """

    from rytm_randomizer.cockpit.export import model_format

    assert isinstance(
        model_format.FORMAT_VERSION, int
    ), f"FORMAT_VERSION must be int; got {type(model_format.FORMAT_VERSION).__name__}"
    assert model_format.FORMAT_VERSION >= 1, (
        f"FORMAT_VERSION must be >= 1; got {model_format.FORMAT_VERSION}. "
        "Version 0 is reserved for 'no version declared'."
    )
    assert model_format.FORMAT_VERSION in model_format.SUPPORTED_FORMAT_VERSIONS, (
        f"FORMAT_VERSION ({model_format.FORMAT_VERSION}) must appear in "
        f"SUPPORTED_FORMAT_VERSIONS ({sorted(model_format.SUPPORTED_FORMAT_VERSIONS)}); "
        "the format the packer emits must always be readable by the unpacker."
    )
    assert 1 in model_format.SUPPORTED_FORMAT_VERSIONS, (
        "SUPPORTED_FORMAT_VERSIONS must include version 1 (the original "
        "Phase-3 format); dropping it strands every previously-exported "
        "model file."
    )


# ---------------------------------------------------------------------------
# Public surface
# ---------------------------------------------------------------------------


def test_export_pipeline_public_surface_is_stable() -> None:
    """``rytm_randomizer.cockpit.export`` must export the documented names.

    Regression guard: the Phase 4 firmware build (and any downstream
    packer tool) imports these names by string. Renaming any of them
    without coordination breaks the firmware tooling silently — the
    Python build succeeds, the export still emits bytes, but the
    embedded build can no longer locate the encoder. This pins the
    required surface; optional names (e.g. WS-A signing) are checked
    via ``getattr(..., default)`` so this guard does not race the
    parallel WS-A merge.
    """

    from rytm_randomizer.cockpit import export

    required_exports = (
        "pack_profile_model",
        "unpack_profile_model",
        "Header",
        "FORMAT_VERSION",
        "MAGIC",
        "SUPPORTED_FORMAT_VERSIONS",
    )
    declared = set(export.__all__)
    missing = [name for name in required_exports if name not in declared]
    assert not missing, (
        "rytm_randomizer.cockpit.export.__all__ is missing required public "
        f"names: {missing}. The Phase 4 firmware build imports these by "
        "string — every rename is a silent breakage."
    )
    for name in required_exports:
        assert hasattr(export, name), (
            f"rytm_randomizer.cockpit.export must expose '{name}' as a "
            "module attribute (declared in __all__ but not actually "
            "importable is a packaging error)."
        )

    # WS-A signing surface has merged: the real names are
    # ``sign_profile_blob`` (an HMAC-SHA256 signer that returns a
    # :class:`SignedBlob`) and ``verify_signed_blob`` (the receiver-side
    # verifier that returns a :class:`VerificationResult` without ever
    # raising). The earlier probe used the wrong names
    # (``sign_profile_model`` / ``verify_profile_model``) and so was a
    # silent no-op; pinning the real pair here makes any future
    # rename or removal a loud test failure.
    sign_fn = getattr(export, "sign_profile_blob", None)
    verify_fn = getattr(export, "verify_signed_blob", None)
    assert sign_fn is not None, (
        "rytm_randomizer.cockpit.export must expose 'sign_profile_blob' "
        "(the HMAC-SHA256 signer). The Phase 4 firmware build's Python "
        "encoder pairs ``sign_profile_blob`` with ``verify_signed_blob`` "
        "— removing either silently breaks the firmware tooling."
    )
    assert verify_fn is not None, (
        "rytm_randomizer.cockpit.export must expose 'verify_signed_blob' "
        "(the receiver-side verifier). Signing without verification is a "
        "broken contract — the firmware loader has no way to validate."
    )


# ---------------------------------------------------------------------------
# Import discipline
# ---------------------------------------------------------------------------


def test_export_pipeline_has_no_midi_imports() -> None:
    """No module under ``cockpit/export/`` may import MIDI / WS / IPC layers.

    Regression guard: the export pipeline is a pure, offline encoder.
    Pulling ``mido``, ``rtmidi``, ``real_midi_adapter``, ``midi_io``,
    ``cockpit.ws.server``, ``socket``, ``subprocess``, or ``asyncio``
    into this subpackage means the embedded firmware's Python-side
    encoder transitively pulls a desktop-only dependency — and worse,
    every passive CLI command that touches the export path becomes
    capable of opening a port at import time. That's the exact bug
    class that bit PR #103 (a passive command silently importing
    ``real_midi_adapter`` via a lazy chain).
    """

    forbidden_prefixes = (
        "mido",
        "rtmidi",
        "pythonrtmidi",
        "rytm_randomizer.real_midi_adapter",
        "rytm_randomizer.midi_io",
        "rytm_randomizer.mido_provider",
        "rytm_randomizer.cockpit.ws",
        "socket",
        "subprocess",
        "asyncio",
    )
    violations: list[str] = []
    for path in sorted(EXPORT_ROOT.rglob("*.py")):
        module_name = ".".join(path.relative_to(PROJECT_ROOT).with_suffix("").parts)
        package_name = module_name.rpartition(".")[0]
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        imported_modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:
                    relative_name = ("." * node.level) + (node.module or "")
                    imported_modules.append(
                        importlib.util.resolve_name(relative_name, package_name)
                    )
                elif node.module:
                    imported_modules.append(node.module)
        for imported_module in imported_modules:
            if any(
                imported_module == prefix or imported_module.startswith(f"{prefix}.")
                for prefix in forbidden_prefixes
            ):
                violations.append(f"{path.relative_to(PROJECT_ROOT)}: {imported_module}")
    assert not violations, (
        "rytm_randomizer/cockpit/export/ must remain a pure offline "
        "encoder. Forbidden imports found:\n  " + "\n  ".join(violations)
    )


def test_importing_every_export_module_does_not_load_active_midi() -> None:
    """Every passive export module must remain isolated from active MIDI."""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import importlib, pkgutil; "
                "import rytm_randomizer.cockpit.export as export; "
                "[importlib.import_module(info.name) for info in "
                "pkgutil.walk_packages(export.__path__, export.__name__ + '.')]; "
                "forbidden=('mido','rtmidi','rytm_randomizer.midi_io',"
                "'rytm_randomizer.mido_provider',"
                "'rytm_randomizer.real_midi_adapter'); "
                "loaded=tuple(name for name in sys.modules if "
                "any(name == prefix or name.startswith(prefix + '.') "
                "for prefix in forbidden)); "
                "assert not loaded, loaded"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_importing_export_package_keeps_desktop_audio_ipc_lazy() -> None:
    """The embedded export package root must not load desktop analysis IPC."""

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import rytm_randomizer.cockpit.export; "
                "forbidden=('multiprocessing','librosa','soundfile',"
                "'rytm_randomizer.style_analysis.analog_four_patch_inference'); "
                "loaded=tuple(name for name in sys.modules if "
                "any(name == prefix or name.startswith(prefix + '.') "
                "for prefix in forbidden)); "
                "assert not loaded, loaded"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_export_pipeline_round_trip_byte_identical() -> None:
    """``pack_profile_model`` then ``unpack_profile_model`` must round-trip.

    Regression guard: this is a smoke-level integrity check that covers
    both serialization paths in one go. A common breakage class is a
    silent field rename in ``ProfileModel.to_dict()`` /
    ``from_dict`` — type checking passes (both sides agree on the
    typo) but a packed-then-unpacked instance loses or transforms a
    field. With this single test in place, every such rename triggers
    an equality failure here. Once Phase 4 firmware ships, this is
    also what proves the Python encoder produces bytes the firmware
    decoder can consume (the firmware test suite mirrors the same
    pack→unpack round-trip).
    """

    from rytm_randomizer.cockpit.data import ProfileModel, StyleTrait, TraitPadWeight
    from rytm_randomizer.cockpit.export import pack_profile_model, unpack_profile_model

    original = ProfileModel(
        profile_id="profile-export-roundtrip",
        name="Round-trip smoke profile",
        kind="user",
        model_version="1.0.0",
        traits=(
            StyleTrait(name="rolling_low_end", value=0.6),
            StyleTrait(name="dark_atmosphere", value=0.25),
        ),
        pad_mappings=(
            TraitPadWeight(trait="rolling_low_end", pad_id=1, weight=0.8),
            TraitPadWeight(trait="dark_atmosphere", pad_id=4, weight=0.5),
        ),
        transition_curve="progressive",
        source_summary="arch invariant smoke fixture",
    )

    blob = pack_profile_model(original)
    restored = unpack_profile_model(blob)

    assert restored.to_dict() == original.to_dict(), (
        "pack_profile_model -> unpack_profile_model lost or transformed "
        "a field. This is a silent wire-format breakage; check "
        "ProfileModel.to_dict()/from_dict and serialize.py."
    )
    # Defence-in-depth: the dataclass equality must also hold (catches
    # frozen-dataclass-comparison drift that the dict view would miss).
    assert restored == original, (
        "Round-tripped ProfileModel does not compare equal to the original "
        "even though to_dict() matches. Check StyleTrait/TraitPadWeight "
        "tuple ordering or dataclass eq semantics."
    )


# ---------------------------------------------------------------------------
# Signed-envelope overhead
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key_id",
    [
        "",
        "k",
        "test-key",
        "buzzi-2026-key",
        "x" * 64,
        "x" * 255,
    ],
)
def test_export_pipeline_signed_envelope_overhead_matches_real_pack_signed(
    key_id: str,
) -> None:
    """The analytic envelope-overhead formula MUST match :func:`pack_signed`.

    Regression guard: the rehearsal report
    (:mod:`rytm_randomizer.reports.cockpit_export_rehearsal`) projects
    the signed file size from
    :func:`~rytm_randomizer.cockpit.export.signed_envelope_overhead_bytes`
    without actually invoking the signer. That projection is what the
    operator sees in the pre-flight check before clicking EXPORT. If a
    future refactor changes the wire layout in :mod:`.signing` (a wider
    length prefix, an extra reserved field, a different signature size)
    without also updating the formula, the rehearsal would silently
    under- or over-predict the bytes-on-disk.

    This test pins the formula to the real ``pack_signed`` output across
    several key-id lengths (including the 255-byte uint8 maximum). Any
    drift between formula and wire layout fails here at the first
    parametrization that diverges.
    """

    from rytm_randomizer.cockpit.export import (
        SIGNATURE_ALGO_HMAC_SHA256,
        pack_signed,
        sign_profile_blob,
        signed_envelope_overhead_bytes,
    )

    payload = b"X" * 100
    blob = sign_profile_blob(payload, key=b"\x00" * 32, key_id=key_id)
    envelope = pack_signed(blob)

    expected = signed_envelope_overhead_bytes(
        algo=SIGNATURE_ALGO_HMAC_SHA256,
        key_id=key_id,
    )
    actual = len(envelope) - len(payload)
    assert actual == expected, (
        f"signed envelope overhead for key_id={key_id!r}: pack_signed "
        f"produced a {actual}-byte wrapper but the analytic formula "
        f"signed_envelope_overhead_bytes predicted {expected}. The "
        "rehearsal report's would-write size has drifted from the real "
        "wire format — bump the formula or revert the wire-format change."
    )
