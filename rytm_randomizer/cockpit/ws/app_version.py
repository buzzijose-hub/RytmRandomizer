"""Resolve the running sidecar's application version for the WS handshake.

WHAT
====

Exposes :func:`resolve_app_version`, which returns the strict-SemVer
string the cockpit sidecar reports as ``session_status.app_version``
(auto-update contract **I1**). The value is sourced from the version
spine's single accessor, :data:`rytm_randomizer._version.__version__`
(contract **I7**) — this module never re-derives a version from
``pyproject.toml``, ``VERSION``, or ``importlib.metadata`` itself. Doing
so would be exactly the fork the version spine exists to prevent.

WHY A RESOLVER AND NOT A BARE IMPORT
====================================

Two properties the WS bootstrap needs that a module-level
``from .._version import __version__`` cannot give:

1. **The handshake must never fail to build.** ``session_status`` is the
   first frame every cockpit client receives; if version resolution
   raised, the whole cockpit would fail to boot over a cosmetic string.
   A missing or malformed spine degrades to
   :data:`UNKNOWN_APP_VERSION` with a typed taxonomy fingerprint, a
   structured log line, and an error metric — never a raised exception
   and never a silent blank.
2. **Import-time purity.** The cockpit package must import with no
   side effects; resolution therefore happens per call, in-function, and
   the import of the spine module is deferred to call time so a source
   checkout mid-bootstrap cannot poison the module graph.

The value is read-only, server→client, and emitted only at handshake
time (plus the existing ``session_status`` refresh points). Nothing here
opens a port, transmits, or grants any authority — it is a string.

OBSERVABILITY
=============

Every non-happy path emits the same triple the rest of the cockpit
boundary uses: a structured ``_logger.warning`` naming a stable
fingerprint, and :meth:`MidiMetrics.record_error` on that same
fingerprint. Two fingerprints exist:

* ``cockpit.app_version.unavailable`` — the version spine module is not
  importable or exposes no ``__version__``.
* ``cockpit.app_version.malformed`` — the spine resolved, but the value
  is not a strict SemVer string, so contract I1 cannot be honoured.

Emitted details are bounded to the taxonomy fingerprint and the
exception *type name* — never ``str(exc)``, never a filesystem path.

REFERENCES
==========

* ``docs/superpowers/plans/2026-08-03-autoupdate-distribution.md`` §2 —
  the version spine and ``session_status.app_version``.
* ``docs/superpowers/plans/2026-09-07-autoupdate-implementation.md`` —
  contracts I1 (produced here) and I7 (consumed here).
* ``rytm_randomizer/cockpit/ws/handlers.py`` — the single caller
  (``_build_session_status``).
"""

from __future__ import annotations

import re
from typing import Final

from ...observability.logging import get_logger
from ...observability.metrics import get_metrics

__all__ = [
    "APP_VERSION_MALFORMED_FINGERPRINT",
    "APP_VERSION_UNAVAILABLE_FINGERPRINT",
    "SEMVER_PATTERN",
    "UNKNOWN_APP_VERSION",
    "is_strict_semver",
    "resolve_app_version",
]

_logger: Final = get_logger(__name__)

APP_VERSION_UNAVAILABLE_FINGERPRINT: Final[str] = "cockpit.app_version.unavailable"
"""Taxonomy fingerprint: the I7 version spine could not be imported."""

APP_VERSION_MALFORMED_FINGERPRINT: Final[str] = "cockpit.app_version.malformed"
"""Taxonomy fingerprint: the I7 spine resolved a non-SemVer value."""

UNKNOWN_APP_VERSION: Final[str] = "0.0.0"
"""Degraded sentinel emitted when the spine cannot be resolved.

Deliberately a *valid* SemVer string: contract I1 promises consumers a
strict SemVer, and a client comparing versions must never have to parse
a free-form marker like ``"unknown"``. ``0.0.0`` sorts below every real
release, so an update client in the degraded state offers an update
rather than suppressing one — fail toward informing the operator.
"""

SEMVER_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)"
    r"(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?"
    r"(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)
"""The official SemVer 2.0.0 grammar, verbatim from semver.org.

Pinned here (rather than pulled from a dependency) because the cockpit
WS layer is a wire-format authority and must not gain a runtime
dependency to validate a string it already owns the shape of.
"""


def is_strict_semver(value: str) -> bool:
    """True when ``value`` is a strict SemVer 2.0.0 version string.

    Contract I1 promises consumers a strict SemVer; this is the predicate
    that promise is checked against on both the producing (here) and
    consuming side.
    """

    return SEMVER_PATTERN.match(value) is not None


def resolve_app_version() -> str:
    """Return the sidecar's SemVer version string for contract I1.

    Reads :data:`rytm_randomizer._version.__version__` (contract I7).
    Never raises: an unimportable spine, an absent ``__version__``, or a
    non-SemVer value each degrade to :data:`UNKNOWN_APP_VERSION` after
    emitting the structured-log + error-metric pair for the matching
    taxonomy fingerprint.
    """

    try:
        from ..._version import __version__ as spine_version
    except ImportError as exc:
        _logger.warning(
            "cockpit_app_version_unavailable",
            extra={
                "exception_type": type(exc).__name__,
                "fingerprint": APP_VERSION_UNAVAILABLE_FINGERPRINT,
            },
        )
        get_metrics().record_error(APP_VERSION_UNAVAILABLE_FINGERPRINT)
        return UNKNOWN_APP_VERSION

    if not isinstance(  # pyright: ignore[reportUnnecessaryIsInstance]
        spine_version, str
    ) or not is_strict_semver(spine_version):
        _logger.warning(
            "cockpit_app_version_malformed",
            extra={
                "value_type": type(spine_version).__name__,
                "fingerprint": APP_VERSION_MALFORMED_FINGERPRINT,
            },
        )
        get_metrics().record_error(APP_VERSION_MALFORMED_FINGERPRINT)
        return UNKNOWN_APP_VERSION

    return spine_version
