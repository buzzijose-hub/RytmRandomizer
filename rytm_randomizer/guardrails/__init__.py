"""WS-W guardrails engine package.

This package owns the typed Guardrail Profile contract, the validator, the
profile store, and the resolver. The four modules form the WS-W spec sections
13-16: ``schema`` (Layer 3 contract), ``validation`` (Layer 3 enforcement),
``store`` (Layer 3 persistence + lifecycle), ``resolver`` (Layer 4 -- the
intersection with hardware ranges).

The public surface re-exported here is the contract WS-V (style analysis),
the engines, and external callers are written against.
"""

from __future__ import annotations

from .resolver import (
    MODE_EXPERIMENTAL,
    MODE_LIVE_SAFE,
    MODE_STATE_REQUIREMENTS,
    MODE_STUDIO_DISCOVERY,
    GuardrailResolutionError,
    ResolvedBound,
    ResolvedBounds,
    default_hardware_ranges_for_pad,
    resolve,
)
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
    RoleAssignment,
    RoleMapping,
    SceneGuardrail,
    SourceType,
    compute_content_hash,
)
from .store import (
    DEFAULT_PROFILES_DIR,
    LEGAL_STATE_TRANSITIONS,
    IllegalStateTransitionError,
    ProfileStore,
)
from .validation import (
    DESTRUCTIVE_HIGH_RISK_PARAMETERS,
    HIGH_RISK_PARAMETERS,
    KNOWN_SCHEMA_VERSIONS,
    MUTATING_CLASSES,
    PAD_PROFILE_KEY,
    ProfileRejectedError,
    validate,
)

__all__ = [
    # schema
    "SCHEMA_VERSION",
    "Confidence",
    "GuardrailBound",
    "GuardrailClass",
    "GuardrailProfile",
    "MusicalCharacter",
    "ProfileState",
    "Provenance",
    "RiskTier",
    "RoleAssignment",
    "RoleMapping",
    "SceneGuardrail",
    "SourceType",
    "compute_content_hash",
    # validation
    "DESTRUCTIVE_HIGH_RISK_PARAMETERS",
    "HIGH_RISK_PARAMETERS",
    "KNOWN_SCHEMA_VERSIONS",
    "MUTATING_CLASSES",
    "PAD_PROFILE_KEY",
    "ProfileRejectedError",
    "validate",
    # store
    "DEFAULT_PROFILES_DIR",
    "IllegalStateTransitionError",
    "LEGAL_STATE_TRANSITIONS",
    "ProfileStore",
    # resolver
    "GuardrailResolutionError",
    "MODE_EXPERIMENTAL",
    "MODE_LIVE_SAFE",
    "MODE_STATE_REQUIREMENTS",
    "MODE_STUDIO_DISCOVERY",
    "ResolvedBound",
    "ResolvedBounds",
    "default_hardware_ranges_for_pad",
    "resolve",
]
