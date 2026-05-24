"""``WizardSession`` — per-connection wizard authoring state.

The wizard surface is a *modal* extension of the cockpit's command loop:
between :data:`COMMAND_WIZARD_START` and :data:`COMMAND_WIZARD_SAVE` /
:data:`COMMAND_WIZARD_CANCEL`, every wizard command operates on the same
in-flight :class:`WizardState`. This module gives that state a lightweight
container so the WS handlers can mutate it without leaking wizard concerns
into :class:`CockpitSession`.

The Phase 1 cockpit binds one :class:`CockpitSession` per process; the
wizard piggy-backs on that lifetime by sitting on the session as an
``active_wizard: WizardSession | None`` field. ``None`` means "no wizard
in flight"; a populated value means "the operator is mid-authoring".

Why a separate dataclass (and not a few fields on :class:`CockpitSession`)
-------------------------------------------------------------------------

Bundling ``wizard_id`` + ``state`` keeps the cockpit session's surface
narrow — adding two wizard fields would force every cockpit handler to
reason about wizard nulling on cancel. With one container, the cockpit
session sees a single optional pointer and the wizard handlers own the
container's internals.

The dataclass is intentionally mutable (matching :class:`CockpitSession`):
the wizard's *state* is itself a frozen :class:`WizardState`, so each
mutation here is a single ``self.state = ...`` reassignment, not an
in-place edit of the frozen state.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..wizard.state import WizardState


@dataclass
class WizardSession:
    """Container for one in-flight wizard authoring session.

    ``wizard_id`` matches :attr:`WizardState.wizard_id` and is duplicated
    here so the WS dispatcher can correlate inbound commands to the
    session without unpacking the frozen state. ``state`` is the current
    :class:`WizardState`; each transition handler replaces it wholesale
    (the state itself is immutable).
    """

    wizard_id: str
    state: WizardState


__all__ = ["WizardSession"]
