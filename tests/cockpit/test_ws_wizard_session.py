"""Tests for ``rytm_randomizer.cockpit.ws.wizard_session`` — container shape.

The wizard session module is a single ``@dataclass`` with two fields. The
tests cover construction, mutability of the ``state`` reassignment
pattern the handlers use, and the optional-attachment shape on
:class:`CockpitSession`.

These tests aim for 100% branch coverage on
``rytm_randomizer/cockpit/ws/wizard_session.py`` AND verify the
``active_wizard`` field's default on :class:`CockpitSession`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from rytm_randomizer.cockpit.data import PadState, Snapshot
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.wizard.state import WizardState
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.wizard_session import WizardSession

pytestmark = pytest.mark.fast


_WID = "01HXY5Q9PJM0000000000WIZARD"


def _snapshot() -> Snapshot:
    from datetime import datetime, timezone

    return Snapshot(
        snapshot_id="01HXY5Q9PJM0000000000000A",
        device="analog_rytm_mk2",
        captured_at=datetime(2026, 5, 23, 12, 0, 0, tzinfo=timezone.utc),
        pads=(PadState(pad_id=1, machine="BD Hard", params={"tun": 30}),),
        scene_slot="A01",
        bpm=124.0,
    )


def test_wizard_session_holds_wizard_id_and_state() -> None:
    state = WizardState.empty(_WID)
    session = WizardSession(wizard_id=_WID, state=state)

    assert session.wizard_id == _WID
    assert session.state == state


def test_wizard_session_state_is_reassignable() -> None:
    """Handlers replace ``state`` wholesale on each transition."""

    state = WizardState.empty(_WID)
    session = WizardSession(wizard_id=_WID, state=state)
    new_state = state.with_metadata(name="updated")

    session.state = new_state

    assert session.state.name == "updated"
    assert session.state is not state


def test_cockpit_session_active_wizard_defaults_to_none(tmp_path: Path) -> None:
    """The additive ``active_wizard`` field defaults to ``None`` (no wizard in flight)."""

    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)

    assert session.active_wizard is None


def test_cockpit_session_active_wizard_can_be_attached(tmp_path: Path) -> None:
    """A handler can set ``active_wizard`` to a populated :class:`WizardSession`."""

    device = MockDeviceAdapter(initial=_snapshot())
    history = HistoryStore()
    history.initial(device.capture_snapshot())
    registry = ProfileRegistry(profiles_dir=tmp_path)
    session = CockpitSession(profile_registry=registry, history_store=history, device=device)
    wizard = WizardSession(wizard_id=_WID, state=WizardState.empty(_WID))

    session.active_wizard = wizard

    assert session.active_wizard is wizard
    assert session.active_wizard.wizard_id == _WID
