"""Shared ``Literal`` types + ``Final`` tuples for the cockpit data model.

Per Gate 10 (string-literal dispatch hygiene), the allowed values for each
enum-like field live in exactly one place. Each ``XYZ_VALUES`` tuple is the
authoritative runtime enumeration; the matching ``Xyz`` alias is the
static-type form used in dataclass annotations and signatures.

Validation helpers and runtime guards in sibling modules (e.g.
``snapshot.py``, ``profile_model.py``) consume these tuples rather than
re-inlining the string set.
"""

from __future__ import annotations

from typing import Final, Literal

# ---------------------------------------------------------------------------
# ProfileModel.kind
# ---------------------------------------------------------------------------

Kind = Literal["scene", "user"]
"""``"scene"`` for developer-curated built-ins, ``"user"`` for operator-authored."""

KIND_VALUES: Final[tuple[Kind, ...]] = ("scene", "user")
"""Runtime tuple of every ``Kind`` literal (in spec-declaration order)."""


# ---------------------------------------------------------------------------
# HistoryEntry.kind
# ---------------------------------------------------------------------------

HistoryKind = Literal["auto", "saved"]
""""``"auto"`` for post-SEND snapshots; ``"saved"`` for ones promoted to device kit."""

HISTORY_KIND_VALUES: Final[tuple[HistoryKind, ...]] = ("auto", "saved")
"""Runtime tuple of every ``HistoryKind`` literal."""


# ---------------------------------------------------------------------------
# HistoryEntry.via
# ---------------------------------------------------------------------------

Via = Literal["send", "regen", "load", "import"]
"""How the snapshot at a history entry came into being."""

VIA_VALUES: Final[tuple[Via, ...]] = ("send", "regen", "load", "import")
"""Runtime tuple of every ``Via`` literal."""


# ---------------------------------------------------------------------------
# MutationCandidate.safety_status
# ---------------------------------------------------------------------------

Status = Literal["safe", "armed", "high_risk"]
"""Depth- and bounds-derived safety classification for a mutation candidate."""

STATUS_VALUES: Final[tuple[Status, ...]] = ("safe", "armed", "high_risk")
"""Runtime tuple of every ``Status`` literal."""


# ---------------------------------------------------------------------------
# ProfileModel.transition_curve
# ---------------------------------------------------------------------------

TransitionCurve = Literal["linear", "progressive", "progressive_w_release"]
"""Per-profile mutation transition shape (see engine spec)."""

TRANSITION_CURVE_VALUES: Final[tuple[TransitionCurve, ...]] = (
    "linear",
    "progressive",
    "progressive_w_release",
)
"""Runtime tuple of every ``TransitionCurve`` literal."""


__all__ = [
    "HISTORY_KIND_VALUES",
    "HistoryKind",
    "KIND_VALUES",
    "Kind",
    "STATUS_VALUES",
    "Status",
    "TRANSITION_CURVE_VALUES",
    "TransitionCurve",
    "VIA_VALUES",
    "Via",
]
