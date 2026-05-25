"""Wizard command handlers — one async function per spec wizard command.

This module is the wizard-specific counterpart to :mod:`handlers`. Each of
the eight handlers:

1. Validates the command body against the wizard's state machine (e.g.
   :data:`COMMAND_WIZARD_SAVE` requires a candidate profile to exist).
2. Calls the relevant pure helper from :mod:`cockpit.wizard.state`,
   :mod:`cockpit.wizard.analyze`, or :mod:`cockpit.wizard.builder`.
3. Returns a :class:`HandlerResult` carrying the ack body **plus** the
   list of events the dispatcher should broadcast after the ack.

The contract matches :mod:`handlers` (ack first, events second) so the
single :func:`handle_command` dispatcher in :mod:`handlers` can delegate
to :data:`WIZARD_HANDLERS` without bespoke wiring.

Why the dispatcher delegates rather than merging
------------------------------------------------

The cockpit's command surface is decomposable: a reader reviewing the
"live editing" handlers (snapshots, mutations, history) should not have
to scroll past wizard-specific code, and the wizard handlers should not
need to import live-editing helpers. The single ``if cmd_type.startswith
("wizard_")`` branch in :func:`handlers.handle_command` keeps both
surfaces minimally coupled.

The :func:`_handle_wizard_analyze` handler runs the analyzer on a worker
thread via :func:`asyncio.to_thread` — the analyzer is synchronous and
blocking (it reads files, runs FFT, etc.), and the WebSocket event loop
must stay responsive to inbound commands AND outbound events. The thread
boundary is the cheapest "don't freeze the UI" affordance available.

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"Wizard commands" for the authoritative per-command semantics.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from typing import Any, Final

from ...observability.logging import get_logger
from ..data.ulid import new_ulid
from ..wizard.analyze import analyze_source
from ..wizard.builder import build_profile
from ..wizard.errors import WizardSourcePathError
from ..wizard.path_policy import WizardPathPolicy, WizardSourcePathRejected
from ..wizard.state import (
    AnalysisJob,
    InspirationSource,
    WizardState,
    narrow_kind,
    narrow_mode,
)
from .handlers import HandlerResult
from .protocol import EVENT_PROFILE_CHANGED
from .session import CockpitSession
from .wizard_protocol import (
    COMMAND_WIZARD_ADD_SOURCE,
    COMMAND_WIZARD_ANALYZE,
    COMMAND_WIZARD_CANCEL,
    COMMAND_WIZARD_REMOVE_SOURCE,
    COMMAND_WIZARD_REVIEW,
    COMMAND_WIZARD_SAVE,
    COMMAND_WIZARD_SET_METADATA,
    COMMAND_WIZARD_START,
    EVENT_ANALYSIS_PROGRESS,
    EVENT_PROFILE_CREATED,
    EVENT_WIZARD_STATE_CHANGED,
)
from .wizard_session import WizardSession, _utcnow

_logger = get_logger(__name__)
"""Module logger for wizard handler diagnostics.

Used for the categorical analyzer-failure log lines (H4) and the
wizard-replacement warning (M11). The structured ``extra=`` payload
captures the full detail (paths, exception types, ages) that the WS ack
intentionally hides from the operator's browser.
"""

# ---------------------------------------------------------------------------
# Module-level wizard path policy
# ---------------------------------------------------------------------------

#: Default policy used by :func:`_handle_wizard_add_source` when the session
#: does not carry its own. Read from the ``WIZARD_SOURCE_ROOTS`` env var at
#: import time so a deployment can pin the allow-list without touching code.
#: Tests override this via :func:`_set_path_policy` so per-test ``tmp_path``
#: roots are exercised without leaking into the global env.
_PATH_POLICY: WizardPathPolicy = WizardPathPolicy.from_env()


def _set_path_policy(policy: WizardPathPolicy) -> None:
    """Override the module-level :class:`WizardPathPolicy` (testing only).

    The production cockpit reads the policy at import time via
    :meth:`WizardPathPolicy.from_env`. Tests that want to pin a
    ``tmp_path`` root call this helper from their fixture; the
    ``monkeypatch`` fixture restores the original value at teardown via
    :meth:`pytest.MonkeyPatch.setattr`.
    """

    global _PATH_POLICY
    _PATH_POLICY = policy


# ---------------------------------------------------------------------------
# Analyzer failure surface
# ---------------------------------------------------------------------------

#: Union of analyzer failure modes the analyze loop catches and downgrades to a
#: ``failed`` job. ``WizardSourcePathError`` inherits ``FileNotFoundError``,
#: ``extract_from_audio`` may raise ``OSError`` on unreadable files, the
#: dispatcher raises ``ValueError`` for unsupported ``(kind, mode)`` pairs, and
#: the underlying audio extractor surfaces ``RuntimeError`` for unsupported
#: codecs. Anything outside this set is a programmer bug and is allowed to
#: bubble up.
_ANALYZER_FAILURE_EXCEPTIONS: Final[tuple[type[BaseException], ...]] = (
    FileNotFoundError,
    OSError,
    ValueError,
    RuntimeError,
)


# ---------------------------------------------------------------------------
# Categorical analyzer-failure reason set (H4 — sanitize the error path)
# ---------------------------------------------------------------------------

#: Fixed categorical reasons that :func:`_handle_wizard_analyze` reports in
#: :attr:`AnalysisJob.error`. The actual exception message (which often
#: includes the source path) is NEVER forwarded over the wire -- it is
#: logged server-side via :data:`_logger` at WARNING level for operators.
REASON_PATH_NOT_FOUND: Final[str] = "path_not_found"
REASON_UNSUPPORTED_FORMAT: Final[str] = "unsupported_format"
REASON_READ_FAILED: Final[str] = "read_failed"
REASON_ANALYSIS_FAILED: Final[str] = "analysis_failed"

ANALYZER_FAILURE_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_PATH_NOT_FOUND,
        REASON_UNSUPPORTED_FORMAT,
        REASON_READ_FAILED,
        REASON_ANALYSIS_FAILED,
    }
)


def _categorical_reason(exc: BaseException) -> str:
    """Map an analyzer failure exception to one of :data:`ANALYZER_FAILURE_REASONS`.

    Mapping is by exception type:

    * :class:`WizardSourcePathError` /
      :class:`WizardSourcePathRejected` / :class:`FileNotFoundError`
      → ``"path_not_found"`` (path missing on disk OR rejected by the
      allow-list; the WS surface intentionally collapses both so the
      caller cannot distinguish a typo from a forbidden path).
    * :class:`ValueError` → ``"unsupported_format"`` (the analyzer
      dispatcher raises ValueError for unsupported ``(kind, mode)`` pairs
      and for non-file/non-dir kit paths).
    * :class:`OSError` → ``"read_failed"`` (a permission / I/O error
      reading the file).
    * Everything else in :data:`_ANALYZER_FAILURE_EXCEPTIONS` →
      ``"analysis_failed"`` (the catch-all reason for runtime failures
      inside the analyzer).
    """

    if isinstance(exc, (WizardSourcePathError, WizardSourcePathRejected, FileNotFoundError)):
        return REASON_PATH_NOT_FOUND
    if isinstance(exc, ValueError):
        return REASON_UNSUPPORTED_FORMAT
    if isinstance(exc, OSError):
        return REASON_READ_FAILED
    return REASON_ANALYSIS_FAILED


# ---------------------------------------------------------------------------
# Event payload builders
# ---------------------------------------------------------------------------


def _build_wizard_state_changed(state: WizardState) -> dict:
    """Construct the ``wizard_state_changed`` event payload."""

    return {"type": EVENT_WIZARD_STATE_CHANGED, "state": state.to_dict()}


def _build_analysis_progress(job: AnalysisJob) -> dict:
    """Construct the ``analysis_progress`` event payload for one job."""

    return {"type": EVENT_ANALYSIS_PROGRESS, "job": job.to_dict()}


def _build_profile_created(profile: Any) -> dict:
    """Construct the ``profile_created`` event payload (the saved profile)."""

    return {"type": EVENT_PROFILE_CREATED, "profile": profile.to_dict()}


def _build_profile_changed(profile: Any) -> dict:
    """Construct the cockpit's existing ``profile_changed`` event for the new profile."""

    return {"type": EVENT_PROFILE_CHANGED, "profile": profile.to_dict()}


# ---------------------------------------------------------------------------
# Per-command handlers
# ---------------------------------------------------------------------------


async def _handle_wizard_start(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Begin a fresh wizard session and attach it to ``session.active_wizard``.

    Replaces any in-flight wizard wholesale -- the previous session is
    dropped. (The web UI guards against starting a new wizard while one
    is in flight, but the server tolerates the race rather than reject.)

    M11: when a replacement happens the previous wizard's ``wizard_id``
    and accumulated age are emitted via :data:`_logger` at WARNING level
    AND surfaced on the ack as ``previous_wizard_id`` so the operator's
    UI can offer a "restore previous wizard" affordance instead of
    silently destroying minutes of work.
    """

    del cmd
    wizard_id = new_ulid()
    state = WizardState.empty(wizard_id)
    previous = session.active_wizard
    previous_wizard_id: str | None = None
    if previous is not None:
        previous_wizard_id = previous.wizard_id
        age_seconds = max(0.0, (_utcnow() - previous.started_at).total_seconds())
        _logger.warning(
            "wizard_replaced",
            extra={
                "previous_wizard_id": previous.wizard_id,
                "previous_state_age_seconds": age_seconds,
                "previous_step": previous.state.step,
                "previous_source_count": len(previous.state.sources),
                "new_wizard_id": wizard_id,
            },
        )
    session.active_wizard = WizardSession(wizard_id=wizard_id, state=state)
    ack: dict[str, Any] = {"ok": True, "wizard_id": wizard_id}
    if previous_wizard_id is not None:
        ack["previous_wizard_id"] = previous_wizard_id
    return HandlerResult(
        ack=ack,
        events=[_build_wizard_state_changed(state)],
    )


async def _handle_wizard_set_metadata(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Apply ``name`` / ``description`` from the command body to the wizard state.

    Wire semantics (three-state, per the C4 fix in CODE_REVIEW.md PR 1):

    * key missing from ``cmd`` → leave the corresponding state field
      unchanged (passes ``None`` to :meth:`WizardState.with_metadata`,
      which documents ``None`` as "leave unchanged").
    * key present with JSON ``null`` → clear the corresponding state
      field (passes ``""`` to :meth:`WizardState.with_metadata`, which
      documents ``""`` as "cleared").
    * key present with a string value → set the corresponding state field
      to that string verbatim.

    The branch on ``"name" in cmd`` (and likewise ``"description"``) is
    load-bearing: ``cmd.get("name")`` would collapse "missing" and
    "explicit ``null``" into the same ``None``, re-introducing the
    documented-contract inversion C4 was filed against.
    """

    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    name = _resolve_metadata_field(cmd, "name")
    description = _resolve_metadata_field(cmd, "description")
    new_state = wizard.state.with_metadata(name=name, description=description)
    wizard.state = new_state
    return HandlerResult(
        ack={"ok": True, "state": new_state.to_dict()},
        events=[_build_wizard_state_changed(new_state)],
    )


def _resolve_metadata_field(cmd: dict, key: str) -> str | None:
    """Translate one wire-level ``set_metadata`` field into ``with_metadata`` input.

    Three-state wire → two-sentinel pure helper:

    * key missing → return ``None`` (``with_metadata`` reads ``None`` as
      "leave unchanged").
    * key present and ``None`` → return ``""`` (``with_metadata`` reads
      ``""`` as "cleared").
    * key present and any other value → return ``str(value)``.

    Kept as a small named helper so the dispatcher stays readable and the
    three-state mapping is asserted once in unit tests rather than
    duplicated for ``name`` and ``description``.
    """

    if key not in cmd:
        return None
    raw = cmd[key]
    if raw is None:
        return ""
    return str(raw)


async def _handle_wizard_add_source(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Append an :class:`InspirationSource` to the wizard state.

    Field-level validation (kind/mode/location/display_name) is delegated
    to :meth:`InspirationSource.__post_init__`, which raises ``ValueError``
    with the same diagnostic the manual check would have produced -- caught
    here and surfaced as an ack-level ``ok=False`` so the wire shape is
    unchanged.

    C2: ``file`` / ``folder`` mode locations are validated against the
    module-level :class:`WizardPathPolicy` BEFORE the source dataclass
    is constructed. Rejected paths return a categorical ack
    (``code="wizard_source_path_rejected"``) that never echoes the
    rejected path -- the full detail is logged server-side via
    :data:`_logger` at WARNING level. Reference-mode sources (free-text
    artist / album names) skip the policy: there is no filesystem path
    to validate.
    """

    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    kind_raw = str(cmd.get("kind", ""))
    mode_raw = str(cmd.get("mode", ""))
    location = str(cmd.get("location", ""))
    display_name = str(cmd.get("display_name", ""))

    # C2: filesystem-mode sources MUST land inside an allow-listed root.
    # Reference-mode sources are free-text identifiers and skip the policy.
    if mode in ("file", "folder"):
        try:
            _PATH_POLICY.validate(location)
        except WizardSourcePathRejected as exc:
            _logger.warning(
                "wizard_source_path_rejected",
                extra={
                    "reason": str(exc),
                    "location": location,
                    "mode": mode,
                    "kind": kind,
                    "wizard_id": wizard.wizard_id,
                },
            )
            return HandlerResult(
                ack={
                    "ok": False,
                    "code": "wizard_source_path_rejected",
                    "error": str(exc),
                }
            )

    source_id = new_ulid()
    # narrow_kind / narrow_mode raise ValueError on invalid wire values; that
    # gets caught by the same except branch below as
    # ``InspirationSource.__post_init__``'s validation, so the wire shape
    # (``{"ok": false, "error": ...}``) is unchanged.
    try:
        kind = narrow_kind(kind_raw)
        mode = narrow_mode(mode_raw)
        source = InspirationSource(
            source_id=source_id,
            kind=kind,
            mode=mode,
            location=location,
            display_name=display_name,
            added_at=datetime.now(timezone.utc),
        )
    except ValueError as exc:
        return HandlerResult(ack={"ok": False, "error": str(exc)})
    new_state = wizard.state.with_source(source)
    wizard.state = new_state
    return HandlerResult(
        ack={"ok": True, "state": new_state.to_dict(), "source_id": source_id},
        events=[_build_wizard_state_changed(new_state)],
    )


async def _handle_wizard_remove_source(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Drop one source (and its job) from the wizard state."""

    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    source_id = str(cmd.get("source_id", ""))
    if not source_id:
        return HandlerResult(ack={"ok": False, "error": "source_id is required"})
    new_state = wizard.state.without_source(source_id)
    wizard.state = new_state
    return HandlerResult(
        ack={"ok": True, "state": new_state.to_dict()},
        events=[_build_wizard_state_changed(new_state)],
    )


async def _handle_wizard_analyze(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Run the analyzer across every source; emit ``analysis_progress`` per job.

    Per-job lifecycle: ``pending`` → ``analyzing`` (progress=0.0, traits=())
    → ``ok`` (progress=1.0, traits=<analyzer output>) OR ``failed``
    (error=<exception message>). The handler emits one
    ``analysis_progress`` event for the ``analyzing`` transition and one
    for the terminal transition (``ok``/``failed``).

    The analyzer itself is synchronous and blocking, so it runs via
    :func:`asyncio.to_thread` — the WebSocket event loop stays responsive
    so other commands (e.g. a concurrent ``wizard_cancel``) can land
    while a long analysis is in flight.
    """

    del cmd
    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    events: list[dict] = []
    state = wizard.state
    for source in state.sources:
        # ``analyzing`` transition — visible to the UI before the blocking
        # thread call so progress bars animate even on slow analyzers.
        analyzing_job = AnalysisJob(
            source_id=source.source_id,
            status="analyzing",
            progress=0.0,
            error=None,
            extracted_traits=(),
        )
        state = state.with_job_update(analyzing_job)
        wizard.state = state
        events.append(_build_analysis_progress(analyzing_job))
        try:
            traits = await asyncio.to_thread(analyze_source, source)
        except _ANALYZER_FAILURE_EXCEPTIONS as exc:
            # H4: never echo the analyzer message back over the wire --
            # ``extract_from_audio`` / the SysEx analyzer routinely raise
            # exceptions whose str() embeds the source path, which would
            # let a hostile WS peer probe the filesystem via the error
            # field. Map to a categorical reason and log the full detail
            # server-side instead.
            reason = _categorical_reason(exc)
            _logger.warning(
                "wizard_analyzer_failure",
                extra={
                    "reason": reason,
                    "source_id": source.source_id,
                    "source_kind": source.kind,
                    "source_mode": source.mode,
                    "source_location": source.location,
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc),
                    "wizard_id": wizard.wizard_id,
                },
            )
            terminal_job = AnalysisJob(
                source_id=source.source_id,
                status="failed",
                progress=1.0,
                error=reason,
                extracted_traits=(),
            )
        else:
            terminal_job = AnalysisJob(
                source_id=source.source_id,
                status="ok",
                progress=1.0,
                error=None,
                extracted_traits=traits,
            )
        state = state.with_job_update(terminal_job)
        wizard.state = state
        events.append(_build_analysis_progress(terminal_job))
    events.append(_build_wizard_state_changed(state))
    return HandlerResult(ack={"ok": True}, events=events)


async def _handle_wizard_review(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Build the candidate :class:`ProfileModel` from OK jobs + store it on the state."""

    del cmd
    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    state = wizard.state
    if state.name is None or not state.name:
        return HandlerResult(ack={"ok": False, "error": "wizard requires a name before review"})
    profile = build_profile(state.name, state.description, state.jobs)
    new_state = state.with_candidate(profile)
    wizard.state = new_state
    return HandlerResult(
        ack={"ok": True, "candidate_profile": profile.to_dict()},
        events=[_build_wizard_state_changed(new_state)],
    )


async def _handle_wizard_save(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Persist the candidate profile via :meth:`ProfileRegistry.save`.

    Emits both :data:`EVENT_PROFILE_CREATED` (wizard-specific) AND
    :data:`EVENT_PROFILE_CHANGED` (the cockpit's existing event) so the
    cockpit's active-profile chip reflects the new profile without an
    explicit ``select_profile`` round-trip.

    Clears :attr:`CockpitSession.active_wizard` so the next command sees
    a clean slate.
    """

    del cmd
    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    profile = wizard.state.candidate_profile
    if profile is None:
        return HandlerResult(
            ack={"ok": False, "error": "no candidate profile; call wizard_review first"}
        )
    session.profile_registry.save(profile)
    session.active_wizard = None
    return HandlerResult(
        ack={"ok": True, "profile_id": profile.profile_id},
        events=[
            _build_profile_created(profile),
            _build_profile_changed(profile),
        ],
    )


async def _handle_wizard_cancel(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Drop the in-flight wizard session.

    Idempotent: cancelling when no wizard is active still returns
    ``ok=True`` — the operator's mental model is "the wizard is closed",
    which is true either way.
    """

    del cmd
    session.active_wizard = None
    return HandlerResult(ack={"ok": True})


# ---------------------------------------------------------------------------
# Dispatcher table — consumed by :func:`handlers.handle_command`.
# ---------------------------------------------------------------------------

WIZARD_HANDLERS: dict[
    str,
    Callable[[dict, CockpitSession], Awaitable[HandlerResult]],
] = {
    COMMAND_WIZARD_START: _handle_wizard_start,
    COMMAND_WIZARD_SET_METADATA: _handle_wizard_set_metadata,
    COMMAND_WIZARD_ADD_SOURCE: _handle_wizard_add_source,
    COMMAND_WIZARD_REMOVE_SOURCE: _handle_wizard_remove_source,
    COMMAND_WIZARD_ANALYZE: _handle_wizard_analyze,
    COMMAND_WIZARD_REVIEW: _handle_wizard_review,
    COMMAND_WIZARD_SAVE: _handle_wizard_save,
    COMMAND_WIZARD_CANCEL: _handle_wizard_cancel,
}


__all__ = [
    "ANALYZER_FAILURE_REASONS",
    "REASON_ANALYSIS_FAILED",
    "REASON_PATH_NOT_FOUND",
    "REASON_READ_FAILED",
    "REASON_UNSUPPORTED_FORMAT",
    "WIZARD_HANDLERS",
]
