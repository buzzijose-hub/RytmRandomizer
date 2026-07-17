"""Cockpit model export pipeline — portable binary serialization for ``ProfileModel``.

This subpackage is Phase 3 of the cockpit/profile-model design (WS-G). It
produces and consumes the deployable artifact format described in
``docs/superpowers/specs/2026-05-23-cockpit-and-profile-model-design.md``
§"Model Export":

* :func:`pack_profile_model` — turn a :class:`~rytm_randomizer.cockpit.data.ProfileModel`
  into a versioned binary blob (header + MessagePack payload + CRC32).
* :func:`unpack_profile_model` — round-trip the binary back to a
  ``ProfileModel`` (used by tests today, and by the embedded hardware runtime
  in Phase 4).

The on-disk shape is intentionally tiny (typical profile < 100 KB), versioned
(header carries format and model versions), forward-compatible (new optional
fields don't break old loaders), and language-agnostic (MessagePack has
implementations in C, Rust, Python, JavaScript) so the GUI-produced model
runs identically on the embedded firmware.

The package ``__all__`` is intentionally narrow: it lists only the
consumer-facing surface (the WS handlers, the CLI dispatcher, the
rehearsal report, and the architecture / integration test suite).
Implementation-detail names (atomic-writer helpers, default-export
subdir constant, internal dataclasses) remain reachable via the
submodule path — ``cockpit.export.writer.atomic_write`` etc. — but are
deliberately omitted here so future readers see the genuine public
contract at a glance.
"""

from __future__ import annotations

from .analog_four_cli import (
    ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND,
    handle_analog_four_saved_kit_export,
)
from .analog_four_kit import (
    AnalogFourSavedKitExportResult,
    export_analog_four_saved_kit,
)
from .analog_four_patch_batch_cli import (
    ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND,
    handle_analog_four_audio_patch_batch,
)
from .cli import (
    COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND,
    handle_export_profile_model,
)
from .model_format import (
    FORMAT_VERSION,
    MAGIC,
    SUPPORTED_FORMAT_VERSIONS,
    Header,
)
from .serialize import pack_profile_model, unpack_profile_model
from .signing import (
    SIGNATURE_ALGO_HMAC_SHA256,
    SIGNATURE_HEADER_MAGIC,
    pack_signed,
    sign_profile_blob,
    signed_envelope_overhead_bytes,
    unpack_signed,
)
from .verifier import (
    verify_signed_blob,
    verify_unsigned_payload,
)

__all__ = [
    "AnalogFourSavedKitExportResult",
    "ANALOG_FOUR_AUDIO_PATCH_BATCH_CLI_COMMAND",
    "ANALOG_FOUR_SAVED_KIT_EXPORT_CLI_COMMAND",
    "COCKPIT_EXPORT_PROFILE_MODEL_CLI_COMMAND",
    "FORMAT_VERSION",
    "Header",
    "MAGIC",
    "SIGNATURE_ALGO_HMAC_SHA256",
    "SIGNATURE_HEADER_MAGIC",
    "SUPPORTED_FORMAT_VERSIONS",
    "handle_export_profile_model",
    "handle_analog_four_audio_patch_batch",
    "handle_analog_four_saved_kit_export",
    "export_analog_four_saved_kit",
    "pack_profile_model",
    "pack_signed",
    "sign_profile_blob",
    "signed_envelope_overhead_bytes",
    "unpack_profile_model",
    "unpack_signed",
    "verify_signed_blob",
    "verify_unsigned_payload",
]
