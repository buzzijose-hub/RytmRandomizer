"""WS-V style analysis package - Layer 1 of the four-layer guardrails system.

This package owns the **deterministic measurement** half of the
intelligence pipeline (see ``GUARDRAILS_DESIGN_SPEC.md`` section 6). Audio,
descriptions, or a mix are turned into a typed, content-hashed
:class:`FeatureReport` that the WS-V interpretation skill (Layer 2)
consumes to produce a draft :class:`~rytm_randomizer.guardrails.schema.
GuardrailProfile` (Layer 3+).

Public surface re-exported here:

* :class:`FeatureReport` - the typed measurement artifact.
* :func:`compute_feature_report_hash` - canonical SHA-256 over a report;
  the digest the profile's ``Provenance.feature_report_hash`` references.
* :func:`extract_from_audio` - librosa-backed extraction (HIGH confidence).
* :func:`extract_from_description` - description-only path (LOW confidence;
  no librosa required).
* :func:`extract_from_partial` - mixed audio + notes (MEDIUM confidence).
* :func:`analyze_library` - walk a directory; aggregate per-file features
  into a library-level :class:`FeatureReport`.

The heavy dependency (``librosa``) is **lazy-imported inside function
bodies** so the architecture conformance tests
(``tests/architecture/test_no_side_effects.py``) stay green and the core
install remains lean. The optional ``style`` extra in ``pyproject.toml``
pulls librosa in for users who need real audio measurement.
"""

from __future__ import annotations

from .extractor import (
    StyleAnalysisDependencyError,
    extract_from_audio,
    extract_from_description,
    extract_from_partial,
)
from .feature_report import FeatureReport, compute_feature_report_hash
from .library import analyze_library

__all__ = [
    "FeatureReport",
    "StyleAnalysisDependencyError",
    "analyze_library",
    "compute_feature_report_hash",
    "extract_from_audio",
    "extract_from_description",
    "extract_from_partial",
]
