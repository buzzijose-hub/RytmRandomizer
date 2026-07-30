"""The typed :class:`FeatureReport` measurement artifact.

A :class:`FeatureReport` is the structured, immutable output of Layer 1
(deterministic measurement). It carries the audio-derived (or
description-derived) numeric summary of a reference track or library, the
:class:`~rytm_randomizer.guardrails.schema.SourceType` it came from, and a
:class:`~rytm_randomizer.guardrails.schema.Confidence` tag so downstream
layers know how much to trust it.

The full traceability chain is::

    audio -> FeatureReport (Layer 1) -> draft GuardrailProfile (Layer 2)
          -> VALIDATED GuardrailProfile (Layer 3) -> mutation bounds (Layer 4)

The profile's ``Provenance.feature_report_hash`` points back to the exact
digest :func:`compute_feature_report_hash` produces for the report it was
derived from -- so the chain is reconstructible from any link.

House style (matches ``rytm_randomizer/mock_midi.py``,
``rytm_randomizer/state/anchor.py``,
``rytm_randomizer/guardrails/schema.py``):

* ``@dataclass(frozen=True)`` -- a measurement cannot drift after the fact.
* ``tuple`` in place of ``list`` for the energy arc.
* Full type annotations under ``from __future__ import annotations``.
* No I/O at module import time -- this module is a leaf and depends only on
  the stdlib and :mod:`rytm_randomizer.guardrails.schema` (which is itself
  stdlib-only).
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import TypedDict, cast

from rytm_randomizer.guardrails.schema import Confidence, SourceType


@dataclass(frozen=True)
class FeatureReport:
    """The structured output of a Layer 1 measurement.

    All numeric fields are normalised so a profile interpreter can compare
    them across sources:

    * ``bpm`` -- beats per minute as a float. ``0.0`` on the
      description-only path (the agent supplies tempo from notes instead).
    * ``tempo_stability`` -- in ``[0.0, 1.0]``. ``1.0`` is rock-steady;
      ``0.0`` is unstable / unknown.
    * ``kick_density`` / ``percussion_density`` -- onset rate, normalised
      to roughly ``[0.0, 1.0]`` where ``1.0`` is "dense".
    * ``low_end_weight`` -- sub-frequency energy share, in ``[0.0, 1.0]``.
    * ``spectral_brightness`` -- normalised spectral centroid in
      ``[0.0, 1.0]``; ``0.0`` is dark, ``1.0`` is bright.
    * ``texture_noise`` -- broadband-noise share in ``[0.0, 1.0]``.
    * ``energy_arc`` -- a (small) tuple of normalised RMS samples taken at
      even intervals across the track / library, so the interpreter can
      see flat vs. building vs. peaked-and-dropped shape.

    The ``content_hash`` and ``derived_at`` fields tie the report to the
    profile that consumed it, exactly the way
    :class:`~rytm_randomizer.guardrails.schema.GuardrailProfile.content_hash`
    ties a validated profile to its own contents.
    """

    source_type: SourceType
    confidence: Confidence
    bpm: float
    tempo_stability: float
    kick_density: float
    percussion_density: float
    low_end_weight: float
    spectral_brightness: float
    texture_noise: float
    energy_arc: tuple[float, ...]
    content_hash: str
    derived_at: str
    """ISO 8601 timestamp string (e.g. ``"2026-05-15T12:34:56Z"``)."""


class FeatureReportPayload(TypedDict):
    """Stable JSON-ready representation of :class:`FeatureReport`."""

    source_type: str
    confidence: str
    bpm: float
    tempo_stability: float
    kick_density: float
    percussion_density: float
    low_end_weight: float
    spectral_brightness: float
    texture_noise: float
    energy_arc: list[float]
    content_hash: str
    derived_at: str


def _require_serializable_feature_report(value: object) -> FeatureReport:
    if not isinstance(value, FeatureReport):
        raise TypeError("report must be a FeatureReport")
    return value


def feature_report_to_dict(report: FeatureReport) -> FeatureReportPayload:
    """Return the canonical public payload for a measured feature report."""

    report = _require_serializable_feature_report(report)
    return {
        "source_type": report.source_type.value,
        "confidence": report.confidence.value,
        "bpm": report.bpm,
        "tempo_stability": report.tempo_stability,
        "kick_density": report.kick_density,
        "percussion_density": report.percussion_density,
        "low_end_weight": report.low_end_weight,
        "spectral_brightness": report.spectral_brightness,
        "texture_noise": report.texture_noise,
        "energy_arc": list(report.energy_arc),
        "content_hash": report.content_hash,
        "derived_at": report.derived_at,
    }


# ---------------------------------------------------------------------------
# Canonical serialization + content hashing
# ---------------------------------------------------------------------------


def _to_canonical(value: object) -> object:
    """Convert a :class:`FeatureReport` value into a JSON-canonical primitive.

    The transformation matches
    :func:`rytm_randomizer.guardrails.schema.compute_content_hash` rules so
    a profile's ``Provenance.feature_report_hash`` and the report's
    ``content_hash`` use the same canonical-JSON SHA-256 pattern:

    * :class:`Enum` -> ``.value``.
    * Dataclass -> ``dict`` of its public fields, with ``content_hash``
      excluded for :class:`FeatureReport` so the hash describes content
      and is stable across recompute-after-construction.
    * :class:`~collections.abc.Mapping` -> plain ``dict`` with stringified
      keys.
    * Tuple / list -> ``list``.
    * Primitives pass through.
    """

    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value) and not isinstance(value, type):
        result: dict[str, object] = {}
        for f in fields(value):
            if isinstance(value, FeatureReport) and f.name == "content_hash":
                # Exclude the hash field from its own hash input.
                continue
            result[f.name] = _to_canonical(getattr(value, f.name))
        return result
    if isinstance(value, Mapping):
        items = cast(Mapping[object, object], value)
        return {str(key): _to_canonical(item) for key, item in items.items()}
    if isinstance(value, (tuple, list)):
        return [_to_canonical(item) for item in cast(Sequence[object], value)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    raise TypeError(f"_to_canonical: unsupported value type {type(value).__name__!r}")


def compute_feature_report_hash(report: FeatureReport) -> str:
    """Return the deterministic SHA-256 of ``report``.

    Same canonical-JSON SHA-256 pattern as
    :func:`rytm_randomizer.guardrails.schema.compute_content_hash` so the
    WS-W ``Provenance.feature_report_hash`` field can reference a
    :class:`FeatureReport` produced here verbatim. The ``content_hash``
    field of the report is excluded from the hash input (the hash cannot
    describe itself).

    Returns a lowercase 64-character hex digest.
    """

    canonical = _to_canonical(report)
    payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


__all__ = [
    "FeatureReport",
    "FeatureReportPayload",
    "compute_feature_report_hash",
    "feature_report_to_dict",
]
