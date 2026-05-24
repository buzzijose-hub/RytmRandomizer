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
from typing import Any

from ..data.ulid import new_ulid
from ..wizard.analyze import analyze_source
from ..wizard.builder import build_profile
from ..wizard.state import (
    KIND_VALUES,
    MODE_VALUES,
    AnalysisJob,
    InspirationSource,
    WizardState,
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
from .wizard_session import WizardSession

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

    Replaces any in-flight wizard wholesale — the previous session is
    dropped. (The web UI guards against starting a new wizard while one
    is in flight, but the server tolerates the race rather than reject.)
    """

    del cmd
    wizard_id = new_ulid()
    state = WizardState.empty(wizard_id)
    session.active_wizard = WizardSession(wizard_id=wizard_id, state=state)
    return HandlerResult(
        ack={"ok": True, "wizard_id": wizard_id},
        events=[_build_wizard_state_changed(state)],
    )


async def _handle_wizard_set_metadata(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Apply ``name`` / ``description`` from the command body to the wizard state."""

    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    name_raw = cmd.get("name")
    description_raw = cmd.get("description")
    name = None if name_raw is None else str(name_raw)
    description = None if description_raw is None else str(description_raw)
    new_state = wizard.state.with_metadata(name=name, description=description)
    wizard.state = new_state
    return HandlerResult(
        ack={"ok": True, "state": new_state.to_dict()},
        events=[_build_wizard_state_changed(new_state)],
    )


async def _handle_wizard_add_source(cmd: dict, session: CockpitSession) -> HandlerResult:
    """Append an :class:`InspirationSource` to the wizard state."""

    wizard = session.active_wizard
    if wizard is None:
        return HandlerResult(ack={"ok": False, "error": "no active wizard session"})
    kind = str(cmd.get("kind", ""))
    mode = str(cmd.get("mode", ""))
    location = str(cmd.get("location", ""))
    display_name = str(cmd.get("display_name", ""))
    if kind not in KIND_VALUES:
        return HandlerResult(
            ack={"ok": False, "error": f"kind must be one of {KIND_VALUES}; got {kind!r}"}
        )
    if mode not in MODE_VALUES:
        return HandlerResult(
            ack={"ok": False, "error": f"mode must be one of {MODE_VALUES}; got {mode!r}"}
        )
    source_id = new_ulid()
    source = InspirationSource(
        source_id=source_id,
        kind=kind,  # type: ignore[arg-type]
        mode=mode,  # type: ignore[arg-type]
        location=location,
        display_name=display_name,
        added_at=datetime.now(timezone.utc),
    )
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
        except (
            FileNotFoundError,
            OSError,
            ValueError,
            RuntimeError,
        ) as exc:
            terminal_job = AnalysisJob(
                source_id=source.source_id,
                status="failed",
                progress=1.0,
                error=str(exc),
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


__all__ = ["WIZARD_HANDLERS"]
