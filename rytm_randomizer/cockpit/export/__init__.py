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
"""

from __future__ import annotations

from .model_format import (
    FORMAT_VERSION,
    MAGIC,
    SUPPORTED_FORMAT_VERSIONS,
    Header,
)
from .serialize import pack_profile_model, unpack_profile_model

__all__ = [
    "FORMAT_VERSION",
    "Header",
    "MAGIC",
    "SUPPORTED_FORMAT_VERSIONS",
    "pack_profile_model",
    "unpack_profile_model",
]
