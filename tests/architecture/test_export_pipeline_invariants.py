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

from pathlib import Path
from typing import Final

import pytest

pytestmark = pytest.mark.fast

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[2]
EXPORT_ROOT: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "cockpit" / "export"


# ---------------------------------------------------------------------------
# Format constants
# ---------------------------------------------------------------------------


def test_export_pipeline_format_magic_is_RYMP() -> None:
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

    # Optional signing/verifier names — WS-A may not have merged yet.
    # Probe via getattr-with-default so this test does NOT block until
    # WS-A is in. When they do land, this assertion turns into a noop
    # because the names will simply be present.
    sign_fn = getattr(export, "sign_profile_model", None)
    verify_fn = getattr(export, "verify_profile_model", None)
    if sign_fn is not None or verify_fn is not None:
        # If either side has merged, BOTH should be present — a signer
        # without a verifier is a broken contract.
        assert sign_fn is not None, (
            "verify_profile_model is exposed but sign_profile_model is not; "
            "the signing envelope is a pair — expose both or neither."
        )
        assert verify_fn is not None, (
            "sign_profile_model is exposed but verify_profile_model is not; "
            "the signing envelope is a pair — expose both or neither."
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

    forbidden_substrings = (
        "import mido",
        "from mido",
        "import rtmidi",
        "from rtmidi",
        "import pythonrtmidi",
        "from pythonrtmidi",
        "rytm_randomizer.real_midi_adapter",
        "rytm_randomizer.midi_io",
        "rytm_randomizer.cockpit.ws",
        "import socket",
        "from socket",
        "import subprocess",
        "from subprocess",
        "import asyncio",
        "from asyncio",
    )
    violations: list[str] = []
    for path in sorted(EXPORT_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for needle in forbidden_substrings:
            if needle in source:
                violations.append(f"{path.relative_to(PROJECT_ROOT)}: {needle}")
    assert not violations, (
        "rytm_randomizer/cockpit/export/ must remain a pure offline "
        "encoder. Forbidden imports found:\n  " + "\n  ".join(violations)
    )


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
