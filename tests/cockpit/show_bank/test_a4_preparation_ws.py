"""Current-session A4 review wiring stays read-only and refuses stale requests."""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    cockpit_snapshot_from_rytm_capture,
)
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import handlers
from rytm_randomizer.cockpit.ws.handlers import handle_command
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.cockpit.ws.show_bank_handlers import SHOW_BANK_HANDLERS

from .conftest import ShowBankHarness, build_show_bank_harness, generate_show_bank_candidates

pytestmark = pytest.mark.fast


@pytest.fixture
def review_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[ShowBankHarness, CockpitSession]:
    harness = build_show_bank_harness(tmp_path)
    candidate = generate_show_bank_candidates(harness, count=1)[0]
    snapshot = cockpit_snapshot_from_rytm_capture(harness.rytm)
    history = HistoryStore()
    history.initial(snapshot)
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial=snapshot),
        kit_captures={ANALOG_FOUR_DEVICE_ID: harness.analog_four},
        show_kit_forge=harness.workspace,
        current_candidate=candidate.rytm_candidate,
        a4_track_targets={1},
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("A4 preparation attempted a hardware operation")

    for name in ("list_input_names", "list_output_names", "open_input", "open_output"):
        monkeypatch.setattr(f"rytm_randomizer.mido_provider.MidoMidiPortProvider.{name}", forbidden)
    for name in ("arm", "confirm", "apply"):
        monkeypatch.setattr(
            f"rytm_randomizer.senders.armed_apply.ArmedApplySession.{name}", forbidden
        )
    return harness, session


def _request(
    harness: ShowBankHarness, session: CockpitSession, **overrides: object
) -> dict[str, object]:
    review: dict[str, object] = {
        "bank_id": harness.bank_id,
        "entry_id": harness.entry_id,
        "expected_revision": harness.workspace.bank(harness.bank_id).revision,
        "output_port_name": "Exact A4 intent",
        **overrides,
    }
    return asyncio.run(
        handle_command(
            {
                "request_id": "a4-review",
                "command": {"type": "show_bank_list", "a4_preparation": review},
            },
            session,
        )
    )


def test_ws_review_revalidates_candidate_but_never_grants_send(
    review_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, session = review_session
    before = harness.workspace.bank(harness.bank_id)
    ack = _request(harness, session)
    assert ack["ok"] is True
    report = ack["a4_preparation"]
    assert isinstance(report, dict)
    assert report["candidate_bytes_verified"] is True
    assert report["ready"] is report["hardware_send_validated"] is False
    assert report["source_reloaded"] is False
    assert "current_capture_stale" in report["blocked_reasons"]
    assert report["output_port_name"] == "Exact A4 intent"
    assert harness.workspace.bank(harness.bank_id) == before
    assert session.armed_apply is None
    assert session.current_send_plan is None
    assert session.unsaved_sends == 0


def test_fresh_capture_and_disconnect_cutoff_are_rechecked_each_time(
    review_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, session = review_session
    harness.clock.current += timedelta(minutes=2)
    session.kit_captures[ANALOG_FOUR_DEVICE_ID] = replace(
        harness.analog_four, captured_at=harness.clock.current - timedelta(seconds=1)
    )
    first = _request(harness, session)["a4_preparation"]
    assert isinstance(first, dict)
    assert first["current_source_verified"] is True
    harness.workspace.revoke_hardware_evidence()
    second = _request(harness, session, output_port_name=None)["a4_preparation"]
    assert isinstance(second, dict)
    assert second["current_source_verified"] is False
    assert "current_capture_stale" in second["blocked_reasons"]
    assert "output_port_intent_required" in second["blocked_reasons"]
    assert first["preparation_id"] != second["preparation_id"]


def test_changed_selection_and_scope_cannot_reuse_a_previous_review(
    review_session: tuple[ShowBankHarness, CockpitSession],
) -> None:
    harness, session = review_session
    session.current_candidate = None
    session.a4_track_locks = {1}
    report = _request(harness, session)["a4_preparation"]
    assert isinstance(report, dict)
    assert "candidate_not_selected" in report["blocked_reasons"]
    assert "scope_changed" in report["blocked_reasons"]


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"expected_revision": -1}, "show bank changed"),
        ({"expected_revision": True}, "must be an integer"),
        ({"source_reloaded": True}, "unknown"),
        ({"output_port_name": 42}, "must be a string"),
        ({"output_port_name": "bad\nport"}, "bounded plain text"),
        ({"entry_id": "missing"}, "unknown"),
    ],
)
def test_invalid_or_stale_review_request_is_refused(
    review_session: tuple[ShowBankHarness, CockpitSession],
    overrides: dict[str, object],
    message: str,
) -> None:
    harness, session = review_session
    ack = _request(harness, session, **overrides)
    assert ack["ok"] is False
    assert ack["code"] == "validation_error"
    assert ack["message"] == "command rejected by handler validation"
    assert "a4_preparation" not in ack
    with pytest.raises(ValueError, match=message):
        asyncio.run(
            SHOW_BANK_HANDLERS["show_bank_list"](
                {
                    "type": "show_bank_list",
                    "a4_preparation": {
                        "bank_id": harness.bank_id,
                        "entry_id": harness.entry_id,
                        "expected_revision": harness.workspace.bank(harness.bank_id).revision,
                        "output_port_name": "Exact A4 intent",
                        **overrides,
                    },
                },
                session,
            )
        )


def test_workspace_reviews_inactive_or_unselected_cues_as_blocked(tmp_path: Path) -> None:
    harness = build_show_bank_harness(tmp_path)
    workspace = harness.workspace
    report = workspace.prepare_a4_review(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures={},
        target_ids=(),
        locked_ids=(),
        active_candidate_id=None,
        output_port_name=None,
    )
    assert report.candidate_id is None
    assert "candidate_not_selected" in report.blocked_reasons
    candidate = generate_show_bank_candidates(harness, count=1)[0]
    workspace.create_bank(name="Other bank", description="", notes=())
    report = workspace.prepare_a4_review(
        harness.bank_id,
        harness.entry_id,
        workspace.bank(harness.bank_id).revision,
        captures={},
        target_ids=(1,),
        locked_ids=(),
        active_candidate_id=candidate.candidate_id,
        output_port_name=None,
    )
    assert "candidate_not_selected" in report.blocked_reasons
    assert report.ready is False


@pytest.mark.parametrize("kind", ("unknown_key", "candidate_id", "short_key"))
def test_rejected_request_logs_are_bounded_without_losing_internal_error_details(
    review_session: tuple[ShowBankHarness, CockpitSession],
    ws_handler_caplog: pytest.LogCaptureFixture,
    kind: str,
) -> None:
    harness, session = review_session
    limit = handlers._HANDLER_EXCEPTION_REPR_MAX_CHARS
    value = "extra" if kind == "short_key" else "x" * (limit * 2) + "unlogged-tail"
    command: dict[str, object]
    if kind == "candidate_id":
        command = {
            "type": "show_bank_select_candidate",
            "bank_id": harness.bank_id,
            "entry_id": harness.entry_id,
            "expected_revision": harness.workspace.bank(harness.bank_id).revision,
            "candidate_id": value,
        }
    else:
        command = {
            "type": "show_bank_list",
            "a4_preparation": {
                "bank_id": harness.bank_id,
                "entry_id": harness.entry_id,
                "expected_revision": harness.workspace.bank(harness.bank_id).revision,
                "output_port_name": None,
                value: True,
            },
        }
    command_type = str(command["type"])
    with pytest.raises(ValueError, match="unknown") as internal_error:
        asyncio.run(SHOW_BANK_HANDLERS[command_type](command, session))
    assert value in str(internal_error.value)
    ack = asyncio.run(handle_command({"request_id": "bounded-error", "command": command}, session))
    assert ack == {
        "request_id": "bounded-error",
        "ok": False,
        "code": "validation_error",
        "message": "command rejected by handler validation",
    }
    record = next(
        record for record in ws_handler_caplog.records if record.msg == "handler_exception"
    )
    detail = record.__dict__["exception_repr"]
    assert len(detail) <= limit
    assert record.__dict__["exception_type"] == "ValueError"
    assert record.__dict__["code"] == "validation_error"
    if kind == "short_key":
        assert detail == repr(internal_error.value)
    else:
        assert len(detail) == limit
        assert detail.startswith("ValueError(")
        assert detail.endswith("...")
        assert "unlogged-tail" not in repr(record.__dict__)
    assert session.armed_apply is None
    assert session.current_send_plan is None
    assert session.unsaved_sends == 0
