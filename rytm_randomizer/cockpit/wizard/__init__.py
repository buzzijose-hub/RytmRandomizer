"""Profile Wizard data model + state transitions (Phase 2 · WS-A).

The wizard authoring surface walks the operator through four steps —
``"name"`` → ``"add"`` → ``"analyze"`` → ``"review"`` — to produce a
deployable :class:`~rytm_randomizer.cockpit.data.ProfileModel` from one or
more :class:`InspirationSource` s. Each source kicks off an
:class:`AnalysisJob`; once every job reaches ``"ok"`` the review step shows
the derived :class:`~rytm_randomizer.cockpit.data.StyleTrait` bars and
candidate profile.

This subpackage holds **only the pure data + state-transition layer**.
The analyzer pipeline (WS-B), the :class:`ProfileBuilder` (WS-C), and the
WebSocket Protocol extensions (WS-D) consume these dataclasses without
re-defining them.

See ``docs/superpowers/specs/2026-05-24-profile-wizard-design.md``
§"Core data abstractions" for the authoritative shape.
"""

from __future__ import annotations

from .state import (
    KIND_VALUES,
    MODE_VALUES,
    STATUS_VALUES,
    STEP_VALUES,
    AnalysisJob,
    InspirationSource,
    Kind,
    Mode,
    Status,
    Step,
    WizardState,
)

__all__ = [
    "AnalysisJob",
    "InspirationSource",
    "KIND_VALUES",
    "Kind",
    "MODE_VALUES",
    "Mode",
    "STATUS_VALUES",
    "STEP_VALUES",
    "Status",
    "Step",
    "WizardState",
]
