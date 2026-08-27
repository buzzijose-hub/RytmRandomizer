"""Shared ``Literal`` types + ``Final`` tuples for the cockpit data model.

Per Gate 10 (string-literal dispatch hygiene), the allowed values for each
enum-like field live in exactly one place. Each ``XYZ_VALUES`` tuple is the
authoritative runtime enumeration; the matching ``Xyz`` alias is the
static-type form used in dataclass annotations and signatures.

Validation helpers and runtime guards in sibling modules (e.g.
``snapshot.py``, ``profile_model.py``) consume these tuples rather than
re-inlining the string set.

Narrowing helpers
-----------------

Each ``Xyz`` Literal also has a ``narrow_xyz(s: str) -> Xyz`` helper that
takes a raw ``str`` from the wire (or any untyped ``object`` source), checks
membership against the ``_VALUES`` tuple, and either returns the narrowed
``Literal`` or raises :class:`ValueError`. These helpers replace the
``# type: ignore[arg-type]`` "trust me, this string is one of the literals"
pattern at every wire boundary: the narrow is *earned* at runtime via the
membership check, then the static type follows from a single
:func:`typing.cast` call internal to the helper.

The error messages truncate untrusted input to :data:`_ERROR_REPR_MAX_LEN`
characters so a malicious large blob cannot bloat a log line, and use
``repr()`` to escape non-printable bytes.
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

Via = Literal["send", "regen", "load", "import", "capture"]
"""How the snapshot at a history entry came into being."""

VIA_VALUES: Final[tuple[Via, ...]] = ("send", "regen", "load", "import", "capture")
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


# ---------------------------------------------------------------------------
# Narrowing helpers — earn the Literal at runtime, then cast.
# ---------------------------------------------------------------------------

_ERROR_REPR_MAX_LEN: Final[int] = 50
"""Max length (in source characters) of any untrusted ``str`` echoed in a
narrow-helper error message. Untrusted input from the wire could be huge or
contain control characters; truncating + ``repr()``-ing keeps log lines tame
without losing the value's diagnostic shape for legitimate small inputs."""


def safe_repr(value: str) -> str:
    """Return a length-bounded, escape-quoted repr of ``value`` for error messages.

    ``repr()`` already escapes non-printable bytes and quotes the string;
    this wrapper additionally truncates the *source* string to
    :data:`_ERROR_REPR_MAX_LEN` characters before repring so a 10MB blob
    on the wire cannot blow up a log line.

    Truncation is appended with a ``"...(truncated)"`` marker INSIDE the
    repr quotes so a reader can tell the value was cut. The escape work
    (control characters, embedded quotes) is left to ``repr()``.
    """

    if len(value) > _ERROR_REPR_MAX_LEN:
        return repr(value[:_ERROR_REPR_MAX_LEN] + "...(truncated)")
    return repr(value)


def _safe_repr(value: str) -> str:
    """Backward-compatible private alias for older sibling modules."""

    return safe_repr(value)


def narrow_kind(s: str) -> Kind:
    """Narrow ``s`` to :data:`Kind` or raise :class:`ValueError`.

    Runtime-checks membership against :data:`KIND_VALUES`. On match,
    :func:`typing.cast` is sound because we just proved ``s in KIND_VALUES``.
    On miss, raise ``ValueError`` with a sanitized (truncated) repr of the
    offending value plus the full allowed set so the failure is debuggable
    without leaking large untrusted strings into logs.
    """

    if s in KIND_VALUES:
        return s
    raise ValueError(f"invalid kind: {_safe_repr(s)}; expected one of {KIND_VALUES}")


def narrow_history_kind(s: str) -> HistoryKind:
    """Narrow ``s`` to :data:`HistoryKind` or raise :class:`ValueError`."""

    if s in HISTORY_KIND_VALUES:
        return s
    raise ValueError(
        f"invalid history kind: {_safe_repr(s)}; expected one of {HISTORY_KIND_VALUES}"
    )


def narrow_via(s: str) -> Via:
    """Narrow ``s`` to :data:`Via` or raise :class:`ValueError`."""

    if s in VIA_VALUES:
        return s
    raise ValueError(f"invalid via: {_safe_repr(s)}; expected one of {VIA_VALUES}")


def narrow_status(s: str) -> Status:
    """Narrow ``s`` to :data:`Status` or raise :class:`ValueError`."""

    if s in STATUS_VALUES:
        return s
    raise ValueError(f"invalid status: {_safe_repr(s)}; expected one of {STATUS_VALUES}")


def narrow_transition_curve(s: str) -> TransitionCurve:
    """Narrow ``s`` to :data:`TransitionCurve` or raise :class:`ValueError`."""

    if s in TRANSITION_CURVE_VALUES:
        return s
    raise ValueError(
        "invalid transition_curve: " f"{_safe_repr(s)}; expected one of {TRANSITION_CURVE_VALUES}"
    )


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
    "narrow_history_kind",
    "narrow_kind",
    "narrow_status",
    "narrow_transition_curve",
    "narrow_via",
    "safe_repr",
]
