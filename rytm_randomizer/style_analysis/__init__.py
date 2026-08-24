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

from ..guardrails.schema import Confidence, SourceType
from .audio_patch_dna import (
    AUDIO_PATCH_DNA_CANDIDATE_COUNT,
    AudioPatchDnaCandidate,
    AudioPatchDnaWorkspace,
    audio_patch_dna_workspace_to_dict,
    build_audio_patch_dna_workspace,
    render_audio_patch_dna_markdown,
    select_audio_patch_dna_candidate,
)
from .audio_reference_suitability import (
    AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION,
    AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION,
    ReferenceAudioSuitability,
    ReferenceWorkflow,
    SuitabilityRecommendation,
    SuitabilityStatus,
    WorkflowSuitability,
    assess_reference_audio,
    reference_audio_suitability_to_dict,
)
from .blueprint import (
    AnalogFourTrackBlueprint,
    ReferenceStyleBlueprint,
    ReferenceTrait,
    RytmPadBlueprint,
    build_reference_style_blueprint,
    reference_style_blueprint_to_dict,
)
from .extractor import (
    AudioDnaEvidence,
    AudioFeatureAnalysis,
    AudioSynthesisFeatures,
    StyleAnalysisDependencyError,
    analyze_audio,
    audio_dna_evidence_to_dict,
    audio_synthesis_features_to_dict,
    extract_from_audio,
    extract_from_description,
    extract_from_partial,
)
from .feature_report import (
    FeatureReport,
    FeatureReportPayload,
    compute_feature_report_hash,
    feature_report_to_dict,
)
from .library import analyze_library

__all__ = [
    "AUDIO_PATCH_DNA_CANDIDATE_COUNT",
    "AUDIO_REFERENCE_SUITABILITY_POLICY_VERSION",
    "AUDIO_REFERENCE_SUITABILITY_SCHEMA_VERSION",
    "AudioDnaEvidence",
    "AudioFeatureAnalysis",
    "AudioPatchDnaCandidate",
    "AudioPatchDnaWorkspace",
    "AudioSynthesisFeatures",
    "AnalogFourTrackBlueprint",
    "Confidence",
    "FeatureReport",
    "FeatureReportPayload",
    "ReferenceStyleBlueprint",
    "ReferenceAudioSuitability",
    "ReferenceWorkflow",
    "ReferenceTrait",
    "RytmPadBlueprint",
    "SourceType",
    "StyleAnalysisDependencyError",
    "SuitabilityRecommendation",
    "SuitabilityStatus",
    "WorkflowSuitability",
    "analyze_audio",
    "assess_reference_audio",
    "audio_dna_evidence_to_dict",
    "audio_patch_dna_workspace_to_dict",
    "audio_synthesis_features_to_dict",
    "analyze_library",
    "compute_feature_report_hash",
    "feature_report_to_dict",
    "build_reference_style_blueprint",
    "build_audio_patch_dna_workspace",
    "extract_from_audio",
    "extract_from_description",
    "extract_from_partial",
    "reference_style_blueprint_to_dict",
    "reference_audio_suitability_to_dict",
    "render_audio_patch_dna_markdown",
    "select_audio_patch_dna_candidate",
]
