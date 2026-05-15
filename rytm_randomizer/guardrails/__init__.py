"""WS-W guardrails engine package.

This package owns the typed Guardrail Profile contract and (in later
phases) the validator, profile store, and resolver. Today only the leaf
``schema`` module exists; ``validation.py``, ``store.py``, and
``resolver.py`` land in Phase D after observability.

The public surface re-exported here is the contract WS-V (style analysis)
and the rest of WS-W are written against.
"""

from __future__ import annotations

from .schema import (
    SCHEMA_VERSION,
    Confidence,
    GuardrailBound,
    GuardrailClass,
    GuardrailProfile,
    MusicalCharacter,
    ProfileState,
    Provenance,
    RiskTier,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
)

__all__ = [
    "SCHEMA_VERSION",
    "Confidence",
    "GuardrailBound",
    "GuardrailClass",
    "GuardrailProfile",
    "MusicalCharacter",
    "ProfileState",
    "Provenance",
    "RiskTier",
    "RoleMapping",
    "SceneGuardrail",
    "SourceType",
    "compute_content_hash",
]
