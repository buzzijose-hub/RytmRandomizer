"""Canonical A4 studio trials compose the real workspace with fake hardware only."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
from datetime import timedelta
from pathlib import Path
from threading import Event, Timer
from typing import Final

import pytest
from cockpit.conftest import TEST_WS_TOKEN, complete_handshake, send_cmd
from fastapi.testclient import TestClient

from conftest import RecordingOut
from rytm_randomizer.cockpit.capture import (
    ANALOG_FOUR_DEVICE_ID,
    ANALOG_RYTM_DEVICE_ID,
    cockpit_snapshot_from_rytm_capture,
)
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import A4_NATIVE_MUTATION_ALGORITHM
from rytm_randomizer.cockpit.device import MockDeviceAdapter
from rytm_randomizer.cockpit.history import HistoryStore
from rytm_randomizer.cockpit.profiles import ProfileRegistry
from rytm_randomizer.cockpit.ws import a4_studio_handlers, handlers
from rytm_randomizer.cockpit.ws import server as ws_server
from rytm_randomizer.cockpit.ws.protocol import INITIAL_EVENT_COUNT, WS_SUBPROTOCOL
from rytm_randomizer.cockpit.ws.server import create_app
from rytm_randomizer.cockpit.ws.session import CockpitSession
from rytm_randomizer.devices import Device, get_device
from rytm_randomizer.observability.errors import MidiError
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.senders.armed_apply import (
    ArmedApplyError,
    ArmedApplyResult,
    ArmedApplySession,
    PlanRenderer,
)

from .conftest import ShowBankHarness, build_show_bank_harness

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_TEST_ARM_SECRET: Final[str] = "studio-test-capability"


class UnexpectedStudioFault(Exception):
    pass


class StudioPort(RecordingOut):
    def __init__(self) -> None:
        super().__init__()
        self.closed = 0
        self.fail_after: int | None = None
        self.send_error: BaseException | None = None
        self.close_error: BaseException | None = None

    def send(self, message: object) -> None:
        if self.fail_after is not None and len(self.sent) >= self.fail_after:
            raise self.send_error or OSError("fake studio output failed")
        super().send(message)

    def close(self) -> None:
        self.closed += 1
        if self.close_error is not None:
            raise self.close_error


@dataclass
class StudioProvider:
    port: StudioPort = field(default_factory=StudioPort)
    opened: list[str] = field(default_factory=list)
    names: tuple[str, ...] = ("Elektron Analog Four MKII Out",)

    def list_output_names(self) -> tuple[str, ...]:
        return self.names

    def open_output(self, port_name: str) -> StudioPort:
        self.opened.append(port_name)
        return self.port


@dataclass
class StudioCase:
    harness: ShowBankHarness
    session: CockpitSession
    provider: StudioProvider

    def command(self, kind: str, **values: object) -> dict[str, object]:
        return asyncio.run(
            handlers.handle_command(
                {
                    "request_id": "studio",
                    "command": {"type": kind, **values},
                },
                self.session,
            )
        )

    def arm(self, **values: object) -> dict[str, object]:
        fields: dict[str, object] = {
            "arm_token": _TEST_ARM_SECRET,
            "confirm": True,
            "port_name": "Elektron Analog Four MKII Out",
            "device_id": ANALOG_FOUR_DEVICE_ID,
            "acknowledge_unvalidated_hardware": True,
        }
        return self.command("arm", **{**fields, **values})

    def prepare(self, **overrides: object) -> dict[str, object]:
        h = self.harness
        fields: dict[str, object] = {
            "bank_id": h.bank_id,
            "entry_id": h.entry_id,
            "expected_revision": h.workspace.bank(h.bank_id).revision,
            "output_port_name": "Elektron Analog Four MKII Out",
            "track_channels": [6, 7, 8, 9],
            "source_reloaded": True,
            "acknowledge_unvalidated_hardware": True,
        }
        return self.command("show_bank_prepare_a4_studio_audition", **{**fields, **overrides})

    def send(self, **overrides: object) -> dict[str, object]:
        plan = self.session.a4_studio_plan
        fields: dict[str, object] = {
            "send_plan_id": "missing" if plan is None else plan.plan_id,
            "confirm": True,
            "source_reloaded": True,
            "acknowledge_unvalidated_hardware": True,
        }
        return self.command("show_bank_send_a4_studio_audition", **{**fields, **overrides})


@pytest.fixture
def studio_case(tmp_path: Path) -> StudioCase:
    h = build_show_bank_harness(tmp_path)
    selection = ParameterSelection(
        tuple(
            ParameterCell(1, name)
            for name in (
                "env2_attack",
                "env2_decay",
                "env2_sustain",
                "env2_release",
                "envf_attack",
                "envf_decay",
                "envf_sustain",
                "envf_release",
            )
        )
    )
    candidates = h.workspace.generate_candidates(
        h.bank_id,
        h.entry_id,
        h.workspace.bank(h.bank_id).revision,
        profile=h.profile,
        depth_preset="small",
        depth=0.25,
        seed=91,
        candidate_count=1,
        rytm_targets=(),
        rytm_locks=tuple(range(1, 13)),
        analog_four_targets=(1,),
        analog_four_locks=(),
        rytm_parameters=ParameterSelection(()),
        analog_four_parameters=selection,
        a4_algorithm=A4_NATIVE_MUTATION_ALGORITHM,
    )
    snapshot = cockpit_snapshot_from_rytm_capture(h.rytm)
    history = HistoryStore()
    history.initial(snapshot)
    provider = StudioProvider()
    session = CockpitSession(
        profile_registry=ProfileRegistry(tmp_path / "profiles"),
        history_store=history,
        device=MockDeviceAdapter(initial=snapshot),
        show_kit_forge=h.workspace,
        arm_secret=_TEST_ARM_SECRET,
        arm_port_provider=provider,
    )
    case = StudioCase(h, session, provider)
    selected = case.command(
        "show_bank_select_candidate",
        bank_id=h.bank_id,
        entry_id=h.entry_id,
        candidate_id=candidates[0].candidate_id,
        expected_revision=h.workspace.bank(h.bank_id).revision,
    )
    assert selected["ok"] is True
    h.clock.current += timedelta(seconds=3)
    session.kit_captures[ANALOG_FOUR_DEVICE_ID] = replace(
        h.analog_four,
        captured_at=h.clock.current - timedelta(seconds=1),
    )
    return case


def test_a4_studio_trial_sends_exact_configured_packets_and_consumes_plan(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"] is True
    assert handlers.build_session_status(case.session)["armed_device_id"] == ANALOG_FOUR_DEVICE_ID
    assert case.prepare()["ok"] is True
    plan = case.session.a4_studio_plan
    assert plan is not None and plan.ready
    assert len(plan.send_plan.packets) >= 2
    expected = [(p.channel, p.control, p.value) for p in plan.send_plan.packets]
    assert {channel for channel, _, _ in expected} == {5}
    before = case.harness.workspace.bank(case.harness.bank_id)
    result = case.send()
    assert result["ok"] is True
    assert result["a4_studio_outcome"]["sent_count"] == len(expected)
    assert case.provider.port.sent == expected
    assert case.provider.opened == ["Elektron Analog Four MKII Out"]
    assert case.session.a4_studio_plan is None
    assert case.session.unsaved_sends == 1
    assert case.harness.workspace.bank(case.harness.bank_id) == before
    assert case.send()["ok"] is False
    assert case.prepare()["ok"] is True
    assert case.session.a4_studio_plan is not None and not case.session.a4_studio_plan.ready
    assert "current_capture_stale" in case.session.a4_studio_plan.blocked_reasons
    assert case.session.stage_coordinator.state.analog_four.authority_state == "blocked"


def test_actual_websocket_prepares_and_delivers_canonical_a4_plan(studio_case: StudioCase) -> None:
    case = studio_case
    assert case.arm()["ok"]
    with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            prepared = send_cmd(
                ws,
                "show_bank_prepare_a4_studio_audition",
                request_id="studio-prepare",
                bank_id=case.harness.bank_id,
                entry_id=case.harness.entry_id,
                expected_revision=case.harness.workspace.bank(case.harness.bank_id).revision,
                output_port_name="Elektron Analog Four MKII Out",
                track_channels=[6, 7, 8, 9],
                source_reloaded=True,
                acknowledge_unvalidated_hardware=True,
            )
            assert prepared["ok"] and prepared["a4_studio_plan"]["ready"]
            plan = case.session.a4_studio_plan
            assert plan is not None and plan.ready
            expected = [
                (packet.channel, packet.control, packet.value) for packet in plan.send_plan.packets
            ]
            delivered = send_cmd(
                ws,
                "show_bank_send_a4_studio_audition",
                request_id="studio-deliver",
                send_plan_id=plan.plan_id,
                confirm=True,
                source_reloaded=True,
                acknowledge_unvalidated_hardware=True,
            )
            assert delivered["ok"] and delivered["a4_studio_outcome"]["status"] == "complete"
            assert delivered["a4_studio_outcome"]["sent_count"] == len(expected)
            assert case.provider.port.sent == expected
            assert case.session.a4_studio_plan is None
    assert case.provider.port.closed == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("confirm", False),
        ("source_reloaded", False),
        ("acknowledge_unvalidated_hardware", False),
        ("confirm", 1),
        ("send_plan_id", "another-plan"),
    ],
)
def test_a4_studio_send_requires_all_exact_operator_confirmations(
    studio_case: StudioCase, field: str, value: object
) -> None:
    assert studio_case.arm()["ok"]
    assert studio_case.prepare()["ok"]
    assert studio_case.send(**{field: value})["ok"] is False
    assert studio_case.provider.port.sent == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"track_channels": [1, 1, 3, 4]},
        {"track_channels": [True, 2, 3, 4]},
        {"track_channels": [1, 2, 3]},
        {"track_channels": [0, 2, 3, 4]},
        {"output_port_name": "bad\nport"},
        {"source_reloaded": 1},
        {"expected_revision": True},
        {"packets": []},
    ],
)
def test_a4_studio_preparation_rejects_malformed_or_injected_data(
    studio_case: StudioCase, overrides: dict[str, object]
) -> None:
    assert studio_case.prepare(**overrides)["ok"] is False
    assert studio_case.session.a4_studio_plan is None
    assert studio_case.provider.opened == []


def test_a4_studio_prepare_without_arm_never_sends_or_opens_port(studio_case: StudioCase) -> None:
    assert studio_case.prepare()["ok"] is True
    assert studio_case.send()["ok"] is False
    assert studio_case.provider.opened == []
    assert studio_case.provider.port.sent == []


def test_rytm_send_cannot_use_an_a4_armed_output(studio_case: StudioCase) -> None:
    assert studio_case.arm()["ok"] is True
    assert studio_case.command("send")["ok"] is False
    assert studio_case.provider.port.sent == []


def test_a4_send_cannot_use_rytm_identity_even_with_exact_port_and_ready_plan(
    studio_case: StudioCase,
) -> None:
    assert studio_case.arm()["ok"]
    assert studio_case.prepare()["ok"]
    plan = studio_case.session.a4_studio_plan
    assert plan is not None and plan.ready
    assert studio_case.session.armed_apply.port_name == plan.routing.output_port_name
    studio_case.session.armed_device_id = ANALOG_RYTM_DEVICE_ID
    assert studio_case.send()["ok"] is False
    assert studio_case.provider.port.sent == []


@pytest.mark.parametrize(
    "kind", ["show_bank_prepare_a4_studio_audition", "show_bank_send_a4_studio_audition"]
)
def test_a4_studio_validation_redacts_request_fields_from_logs(
    studio_case: StudioCase, ws_handler_caplog, kind: str
) -> None:
    sensitive = "C:/private/operator-session.wav"
    result = studio_case.command(kind, **{sensitive: True})
    assert result["ok"] is False
    record = next(item for item in ws_handler_caplog.records if item.msg == "handler_exception")
    assert record.exception_repr == "ValueError('<redacted-local-artifact>')"
    assert sensitive not in repr(record.__dict__)


def test_a4_partial_provider_failure_reports_counts_disarms_and_requires_reload(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"] is True
    assert case.prepare()["ok"] is True
    case.provider.port.fail_after = 1
    result = case.send()
    assert result["ok"] is False
    assert result["a4_studio_outcome"]["status"] == "partial"
    assert result["a4_studio_outcome"]["sent_count"] == 1
    assert result["source_reload_required"] is True
    assert case.session.armed_apply is None
    assert case.session.hardware_intent is True
    assert case.provider.port.closed == 1
    assert case.session.a4_studio_plan is None
    assert case.send()["ok"] is False
    assert len(case.provider.port.sent) == 1


@pytest.mark.parametrize(
    "error_type", [MidiError, ArithmeticError, AssertionError, KeyError, UnexpectedStudioFault]
)
def test_a4_recognized_faults_keep_counts_and_publish_revoked_authority(
    studio_case: StudioCase, error_type: type[Exception]
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan = case.session.a4_studio_plan
    assert plan is not None
    before = sum(get_metrics().cc_sent_by_channel.values())
    case.provider.port.fail_after = 1
    case.provider.port.send_error = error_type("injected delivery fault")
    result = case.send()
    assert result["ok"] is False
    assert result["a4_studio_outcome"]["sent_count"] == 1
    assert result["a4_studio_outcome"]["expected_count"] == len(plan.send_plan.packets)
    assert sum(get_metrics().cc_sent_by_channel.values()) == before + 1
    assert case.session.error_journal.entries[-1].context["sent_count"] == "1"
    events = case.session.pending_events
    status = next(event for event in events if event["type"] == "session_status")
    assert status["armed"] is False
    assert any(event["type"] == "dual_machine_stage_changed" for event in events)
    assert any(
        event["type"] == "mutation_previewed" and event["candidate"] is None for event in events
    )


def test_a4_close_fault_cannot_erase_already_accepted_packets(studio_case: StudioCase) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan = case.session.a4_studio_plan
    assert plan is not None
    case.provider.port.fail_after = 1
    case.provider.port.close_error = KeyError("injected close fault")
    result = case.send()
    assert result["ok"] is False
    assert result["a4_studio_outcome"]["sent_count"] == 1
    assert result["a4_studio_outcome"]["expected_count"] == len(plan.send_plan.packets)
    assert case.session.error_journal.entries[-1].context["sent_count"] == "1"
    assert case.session.armed_apply is None and case.provider.port.closed == 1


@pytest.mark.parametrize("drift", ["action", "device"])
def test_failure_receipt_ignores_progress_from_another_action_or_device(
    studio_case: StudioCase, drift: str
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan, armed = case.session.a4_studio_plan, case.session.armed_apply
    assert plan is not None and armed is not None
    action = "another-action" if drift == "action" else plan.plan_id
    device_id = ANALOG_RYTM_DEVICE_ID if drift == "device" else ANALOG_FOUR_DEVICE_ID
    armed.confirm(action)
    assert armed.apply(
        get_device(device_id),
        plan.send_plan,
        action_id=action,
        mutates_kit=False,
        renderer=handlers.cockpit_send_plan_triples,
    ).ok
    receipt = a4_studio_handlers._failure_result(armed, plan)
    assert receipt.sent_count == 0 and receipt.expected_count == len(plan.send_plan.packets)


def test_failure_receipt_never_labels_delivered_packets_as_zero_byte_refusal(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan, armed = case.session.a4_studio_plan, case.session.armed_apply
    assert plan is not None and armed is not None
    armed.confirm(plan.plan_id)
    assert armed.apply(
        get_device(ANALOG_FOUR_DEVICE_ID),
        plan.send_plan,
        action_id=plan.plan_id,
        mutates_kit=False,
        renderer=handlers.cockpit_send_plan_triples,
    ).ok
    receipt = a4_studio_handlers._failure_result(armed, plan, status="refused")
    assert receipt.sent_count == len(plan.send_plan.packets) and receipt.status == "interrupted"


def test_exception_receipt_cannot_promote_a_tagged_success(studio_case: StudioCase) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan, armed = case.session.a4_studio_plan, case.session.armed_apply
    assert plan is not None and armed is not None
    error = RuntimeError("injected tagged fault")
    error.__dict__["armed_apply_outcome"] = ArmedApplyResult(
        ANALOG_FOUR_DEVICE_ID, True, 0, expected_count=len(plan.send_plan.packets)
    )
    receipt = a4_studio_handlers._failure_result(armed, plan, error=error)
    assert receipt.ok is False and receipt.status == "interrupted" and receipt.sent_count == 0


def test_final_cleanup_fault_still_journals_and_queues_revoked_state(
    studio_case: StudioCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]

    def fail_confirmation(self: ArmedApplySession, action_id: object) -> None:
        raise ValueError("injected pre-delivery fault")

    monkeypatch.setattr(ArmedApplySession, "confirm", fail_confirmation)
    case.provider.port.close_error = KeyError("injected final cleanup fault")
    result = case.send()
    assert result["ok"] is False
    assert case.session.error_journal.entries[-1].context["sent_count"] == "0"
    assert any(
        event["type"] == "session_status" and event["armed"] is False
        for event in case.session.pending_events
    )
    assert case.provider.port.sent == [] and case.provider.port.closed == 1


@pytest.mark.parametrize("close_fault", [False, True])
def test_internal_delivery_cancellation_is_not_swallowed_by_result_collection(
    studio_case: StudioCase, close_fault: bool
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    case.provider.port.fail_after = 1
    case.provider.port.send_error = asyncio.CancelledError("injected delivery cancellation")
    if close_fault:
        case.provider.port.close_error = KeyError("injected close failure")
    with pytest.raises(asyncio.CancelledError):
        case.send()
    assert case.session.error_journal.entries[-1].context["sent_count"] == "1"
    assert case.session.armed_apply is None and case.provider.port.closed == 1
    assert any(
        event["type"] == "session_status" and event["armed"] is False
        for event in case.session.pending_events
    )


@pytest.mark.parametrize("close_fault", [False, True])
def test_websocket_internal_cancellation_publishes_revocations_without_another_command(
    studio_case: StudioCase, close_fault: bool
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan = case.session.a4_studio_plan
    assert plan is not None
    case.provider.port.fail_after = 1
    case.provider.port.send_error = asyncio.CancelledError("private injected cancellation")
    if close_fault:
        case.provider.port.close_error = KeyError("private injected close failure")
    metrics = get_metrics()
    commands_before = metrics.ws_command_count["show_bank_send_a4_studio_audition"]
    sent_before = sum(metrics.cc_sent_by_channel.values())
    with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            for _ in range(INITIAL_EVENT_COUNT):
                ws.receive_json()
            # A deadline sentinel bounds the broken case; it is never needed to
            # trigger the revocations and must not precede them on the wire.
            deadline = Timer(
                2,
                ws.send_json,
                args=({"request_id": "deadline", "command": {"type": "diagnostics"}},),
            )
            deadline.start()
            try:
                ws.send_json(_send_envelope(case))
                frames = []
                for _ in range(32):
                    frame = ws.receive_json()
                    frames.append(frame)
                    assert (
                        frame.get("request_id") != "deadline"
                    ), "revocations required another command"
                    if frame.get("type") == "mutation_previewed" and frame["candidate"] is None:
                        break
                else:
                    pytest.fail("cancellation revocations missing")
            finally:
                deadline.cancel()
                deadline.join(timeout=2)
            assert frames[0]["request_id"] == "studio-send"
            assert frames[0]["ok"] is False
            assert frames[0]["code"] == "validation_error"
            assert "cancelled" in frames[0]["message"]
            assert "private" not in str(frames)
            assert any(f.get("type") == "session_status" and f["armed"] is False for f in frames)
            assert any(
                f.get("type") == "send_plan_changed" and f["send_plan"] is None for f in frames
            )
            assert any(f.get("type") == "dual_machine_stage_changed" for f in frames)
            assert case.session.pending_events == []
            assert (
                metrics.ws_command_count["show_bank_send_a4_studio_audition"] == commands_before + 1
            )
            assert send_cmd(ws, "diagnostics", request_id="after-cancel")["ok"] is True
            stale = send_cmd(
                ws,
                "show_bank_send_a4_studio_audition",
                request_id="stale-repeat",
                send_plan_id=plan.plan_id,
                confirm=True,
                source_reloaded=True,
                acknowledge_unvalidated_hardware=True,
            )
            assert stale["ok"] is False and "Prepare a ready A4 studio plan" in stale["message"]
            disarmed = send_cmd(ws, "disarm", request_id="disarm-again")
            assert disarmed["ok"] is False and disarmed["message"] == "session is not armed"
    outcomes = [
        e
        for e in case.session.error_journal.entries
        if e.fingerprint == "cockpit.a4_studio_outcome"
    ]
    assert len(outcomes) == 1
    assert outcomes[0].context["status"] == "interrupted"
    assert outcomes[0].context["sent_count"] == "1"
    assert outcomes[0].context["expected_count"] == str(len(plan.send_plan.packets))
    assert metrics.ws_command_count["show_bank_send_a4_studio_audition"] == commands_before + 2
    assert sum(metrics.cc_sent_by_channel.values()) == sent_before + 1
    assert case.provider.port.closed == 1 and len(case.provider.port.sent) == 1
    assert case.session.armed_apply is None and not case.session.a4_studio_sending


def test_confirmation_race_returns_zero_byte_receipt_and_revoked_state(
    studio_case: StudioCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]

    def refuse_confirmation(self: ArmedApplySession, action_id: object) -> None:
        raise ArmedApplyError("injected confirmation race")

    monkeypatch.setattr(ArmedApplySession, "confirm", refuse_confirmation)
    result = case.send()
    assert result["ok"] is False and result["a4_studio_outcome"]["sent_count"] == 0
    assert result["a4_studio_outcome"]["status"] == "refused"
    assert case.session.armed_apply is None and case.provider.port.closed == 1


def test_actual_websocket_fault_receipt_is_followed_by_revoked_state(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    plan = case.session.a4_studio_plan
    assert plan is not None
    case.provider.port.fail_after = 1
    case.provider.port.send_error = KeyError("injected send fault")
    with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            result = send_cmd(
                ws,
                "show_bank_send_a4_studio_audition",
                request_id="fault-send",
                send_plan_id=plan.plan_id,
                confirm=True,
                source_reloaded=True,
                acknowledge_unvalidated_hardware=True,
            )
            assert result["ok"] is False and result["a4_studio_outcome"]["sent_count"] == 1
            ws.send_json({"request_id": "after-fault", "command": {"type": "diagnostics"}})
            updates = []
            for _ in range(64):
                frame = ws.receive_json()
                if frame.get("request_id") == "after-fault":
                    break
                updates.append(frame)
            else:
                pytest.fail("diagnostics ACK missing after failed studio SEND")
            assert any(
                frame.get("type") == "session_status" and frame["armed"] is False
                for frame in updates
            )
            assert any(
                frame.get("type") == "send_plan_changed" and frame["send_plan"] is None
                for frame in updates
            )
            assert any(frame.get("type") == "dual_machine_stage_changed" for frame in updates)


@pytest.mark.parametrize(
    "change", ["capture", "parameters", "targets", "candidate", "port", "generation"]
)
def test_a4_send_revalidates_current_context_not_just_plan_id(
    studio_case: StudioCase, change: str
) -> None:
    case = studio_case
    assert case.arm()["ok"] is True
    assert case.prepare()["ok"] is True
    session = case.session
    if change == "capture":
        capture = session.kit_captures[ANALOG_FOUR_DEVICE_ID]
        session.kit_captures[ANALOG_FOUR_DEVICE_ID] = replace(
            capture, captured_at=capture.captured_at + timedelta(microseconds=1)
        )
    elif change == "parameters":
        session.a4_parameters = ParameterSelection(())
    elif change == "targets":
        session.a4_track_targets = {2}
    elif change == "candidate":
        session.current_candidate = None
    elif change == "generation":
        session.a4_studio_generation += 1
    else:
        assert session.armed_apply is not None
        session.armed_apply._port_name = "Another output"
    assert case.send()["ok"] is False
    assert case.provider.port.sent == []


def test_new_source_capture_after_a_successful_attempt_allows_repreparation(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    assert case.send()["ok"]
    case.harness.clock.current += timedelta(seconds=3)
    case.session.kit_captures[ANALOG_FOUR_DEVICE_ID] = replace(
        case.harness.analog_four,
        captured_at=case.harness.clock.current - timedelta(seconds=1),
    )
    assert case.prepare()["ok"]
    assert case.session.a4_studio_plan is not None and case.session.a4_studio_plan.ready
    assert case.send()["ok"]


def test_scope_command_and_disconnect_clear_pending_a4_preparation(studio_case: StudioCase) -> None:
    case = studio_case
    assert case.prepare()["ok"]
    assert case.command("set_a4_track_lock", track=1, locked=True)["ok"]
    assert case.session.a4_studio_plan is None
    assert case.arm()["ok"]
    handlers.disarm_session_on_teardown(case.session)
    assert case.session.armed_apply is None
    assert case.provider.port.closed == 1


@pytest.mark.parametrize(
    "name", ["Elektron Analog Rytm MKII Out", "Generic MIDI OUT", "Analog Four Rytm bridge"]
)
def test_a4_studio_arm_rejects_wrong_or_generic_output_labels_before_open(
    studio_case: StudioCase, name: str
) -> None:
    studio_case.provider.names = (name,)
    assert studio_case.arm(port_name=name)["ok"] is False
    assert studio_case.provider.opened == []


def test_default_rytm_arm_cannot_target_a_known_a4_output(studio_case: StudioCase) -> None:
    result = studio_case.command(
        "arm",
        arm_token=_TEST_ARM_SECRET,
        confirm=True,
        port_name="Elektron Analog Four MKII Out",
    )
    assert result["ok"] is False
    assert studio_case.provider.opened == []


@pytest.mark.parametrize("value", [False, 1, None])
def test_a4_arm_requires_explicit_unqualified_hardware_acknowledgment(
    studio_case: StudioCase, value: object
) -> None:
    assert studio_case.arm(acknowledge_unvalidated_hardware=value)["ok"] is False
    assert studio_case.provider.opened == []


def test_unwired_a4_workspace_cannot_prepare_or_reuse_a_ready_plan(studio_case: StudioCase) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    case.session.show_kit_forge = None
    assert case.send()["ok"] is False
    assert case.session.a4_studio_plan is None
    assert case.prepare()["ok"] is False
    assert case.provider.port.sent == []


@dataclass
class DeliveryPause:
    entered: Event = field(default_factory=Event)
    release: Event = field(default_factory=Event)

    async def wait_entered(self) -> None:
        async def wait() -> None:
            while not self.entered.is_set():
                await asyncio.sleep(0.001)

        await asyncio.wait_for(wait(), timeout=2)


@pytest.fixture
def paused_delivery(monkeypatch: pytest.MonkeyPatch) -> DeliveryPause:
    pause = DeliveryPause()
    original = ArmedApplySession.apply_async

    async def pause_between_messages(_delay: float) -> None:
        pause.entered.set()
        while not pause.release.is_set():
            await asyncio.sleep(0.001)

    async def apply_with_pause(
        self: ArmedApplySession,
        device: Device,
        plan: object,
        *,
        action_id: str,
        mutates_kit: bool = True,
        renderer: PlanRenderer | None = None,
        inter_message_delay_seconds: float = 0.0,
    ) -> ArmedApplyResult:
        return await original(
            self,
            device,
            plan,
            action_id=action_id,
            mutates_kit=mutates_kit,
            renderer=renderer,
            inter_message_delay_seconds=inter_message_delay_seconds,
            async_sleep=pause_between_messages,
        )

    monkeypatch.setattr(ArmedApplySession, "apply_async", apply_with_pause)
    return pause


def _send_envelope(case: StudioCase) -> dict[str, object]:
    plan = case.session.a4_studio_plan
    assert plan is not None
    return {
        "request_id": "studio-send",
        "command": {
            "type": "show_bank_send_a4_studio_audition",
            "send_plan_id": plan.plan_id,
            "confirm": True,
            "source_reloaded": True,
            "acknowledge_unvalidated_hardware": True,
        },
    }


def test_cooperative_a4_send_allows_disarm_and_refuses_concurrent_mutation(
    studio_case: StudioCase, paused_delivery: DeliveryPause
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)

    async def scenario() -> None:
        task = asyncio.create_task(handlers.handle_command(envelope, case.session))
        await paused_delivery.wait_entered()
        before = case.session.depth
        metrics = get_metrics()
        requests_before = metrics.ws_command_count["set_depth"]
        errors_before = metrics.ws_command_errors_by_code["validation_error"]
        refused = await handlers.handle_command(
            {"request_id": "other", "command": {"type": "set_depth", "depth": 0.7}}, case.session
        )
        assert refused["ok"] is False and case.session.depth == before
        assert metrics.ws_command_count["set_depth"] == requests_before + 1
        assert metrics.ws_command_errors_by_code["validation_error"] == errors_before + 1
        disarm = await handlers.handle_command(
            {"request_id": "stop", "command": {"type": "disarm"}}, case.session
        )
        assert disarm["ok"] is True
        assert len(case.provider.port.sent) == 1
        paused_delivery.release.set()
        result = await asyncio.wait_for(task, timeout=2)
        assert result["ok"] is False
        assert result["a4_studio_outcome"]["status"] == "interrupted"
        assert result["a4_studio_outcome"]["sent_count"] == 1

    asyncio.run(scenario())
    assert len(case.provider.port.sent) == 1
    assert case.provider.port.closed == 1
    assert case.session.a4_studio_sending is False


def test_cancelled_a4_delivery_retains_interrupted_counts_and_revokes_authority(
    studio_case: StudioCase, paused_delivery: DeliveryPause
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)

    async def scenario() -> None:
        task = asyncio.create_task(handlers.handle_command(envelope, case.session))
        await paused_delivery.wait_entered()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    outcomes = [
        entry
        for entry in case.session.error_journal.entries
        if entry.fingerprint == "cockpit.a4_studio_outcome"
    ]
    assert outcomes[-1].context["status"] == "interrupted"
    assert outcomes[-1].context["sent_count"] == "1"
    assert case.session.armed_apply is None
    assert case.session.a4_studio_sending is False
    assert case.provider.port.closed == 1
    assert len(case.provider.port.sent) == 1


def test_actual_websocket_reader_processes_disarm_before_remaining_a4_packets(
    studio_case: StudioCase, paused_delivery: DeliveryPause
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)
    timer = Timer(2, paused_delivery.release.set)
    try:
        with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
            with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
                complete_handshake(ws)
                for _ in range(5):
                    ws.receive_json()
                timer.start()
                ws.send_json(envelope)
                assert paused_delivery.entered.wait(timeout=2)
                ws.send_json({"request_id": "stop", "command": {"type": "disarm"}})
                for _ in range(30):
                    message = ws.receive_json()
                    if message.get("request_id") == "stop":
                        assert message["ok"] is True
                        break
                else:
                    pytest.fail("DISARM acknowledgment missing")
                assert len(case.provider.port.sent) == 1
                paused_delivery.release.set()
                for _ in range(30):
                    message = ws.receive_json()
                    if message.get("request_id") == "studio-send":
                        assert message["a4_studio_outcome"]["status"] == "interrupted"
                        assert message["a4_studio_outcome"]["sent_count"] == 1
                        break
                else:
                    pytest.fail("interrupted SEND acknowledgment missing")
    finally:
        paused_delivery.release.set()
        timer.cancel()
        if timer.ident is not None:
            timer.join(timeout=2)
    assert case.provider.port.closed == 1
    assert len(case.provider.port.sent) == 1


def test_actual_websocket_disconnect_cancels_owned_a4_delivery(
    studio_case: StudioCase, paused_delivery: DeliveryPause
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)
    timer = Timer(2, paused_delivery.release.set)
    try:
        with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
            with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
                complete_handshake(ws)
                for _ in range(5):
                    ws.receive_json()
                timer.start()
                ws.send_json(envelope)
                assert paused_delivery.entered.wait(timeout=2)
    finally:
        paused_delivery.release.set()
        timer.cancel()
        if timer.ident is not None:
            timer.join(timeout=2)
    assert case.session.armed_apply is None
    assert case.session.a4_studio_sending is False
    assert case.provider.port.closed == 1
    assert len(case.provider.port.sent) == 1
    outcome = [
        entry
        for entry in case.session.error_journal.entries
        if entry.fingerprint == "cockpit.a4_studio_outcome"
    ][-1]
    assert outcome.context["status"] == "interrupted"
    assert outcome.context["sent_count"] == "1"


def test_internal_a4_cancellation_racing_disconnect_records_one_terminal_outcome(
    studio_case: StudioCase, paused_delivery: DeliveryPause
) -> None:
    case = studio_case
    assert case.arm()["ok"] and case.prepare()["ok"]
    envelope = _send_envelope(case)
    case.provider.port.fail_after = 1
    case.provider.port.send_error = asyncio.CancelledError("cancel during disconnect")
    with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            for _ in range(INITIAL_EVENT_COUNT):
                ws.receive_json()
            ws.send_json(envelope)
            assert paused_delivery.entered.wait(timeout=2)
            paused_delivery.release.set()
        with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
            complete_handshake(ws)
            bootstrap = [ws.receive_json() for _ in range(INITIAL_EVENT_COUNT)]
            assert next(f for f in bootstrap if f["type"] == "session_status")["armed"] is False
            assert send_cmd(ws, "diagnostics")["ok"] is True
    outcomes = [
        e
        for e in case.session.error_journal.entries
        if e.fingerprint == "cockpit.a4_studio_outcome"
    ]
    assert len(outcomes) == 1 and outcomes[0].context["sent_count"] == "1"
    assert outcomes[0].context["status"] == "interrupted"
    assert case.provider.port.closed == 1 and len(case.provider.port.sent) == 1
    assert case.session.armed_apply is None and not case.session.a4_studio_sending


def test_websocket_refuses_a4_send_behind_an_existing_owned_operation(
    studio_case: StudioCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)
    pause = DeliveryPause()
    original = ws_server.handle_command

    async def held_reference(envelope: dict[str, object], session: CockpitSession):
        if envelope.get("command") == {"type": "reference_sound"}:
            pause.entered.set()
            while not pause.release.is_set():
                await asyncio.sleep(0.001)
            return {"request_id": envelope["request_id"], "ok": True}
        return await original(envelope, session)

    monkeypatch.setattr(ws_server, "handle_command", held_reference)
    timer = Timer(2, pause.release.set)
    try:
        with TestClient(create_app(case.session, token=TEST_WS_TOKEN)) as client:
            with client.websocket_connect("/ws", subprotocols=[WS_SUBPROTOCOL]) as ws:
                complete_handshake(ws)
                for _ in range(5):
                    ws.receive_json()
                timer.start()
                ws.send_json({"request_id": "reference", "command": {"type": "reference_sound"}})
                assert pause.entered.wait(timeout=2)
                ws.send_json(envelope)
                for _ in range(30):
                    refused = ws.receive_json()
                    if refused.get("request_id") == "studio-send":
                        break
                else:
                    pytest.fail("busy A4 SEND refusal missing")
                assert refused["ok"] is False and refused["code"] == "validation_error"
                assert not pause.release.is_set()
                assert case.provider.port.sent == []
                ws.send_json({"request_id": "stop", "command": {"type": "disarm"}})
                for _ in range(30):
                    if ws.receive_json().get("request_id") == "stop":
                        break
                else:
                    pytest.fail("DISARM acknowledgment missing during reference analysis")
                assert case.session.armed_apply is None
                pause.release.set()
    finally:
        pause.release.set()
        timer.cancel()
        if timer.ident is not None:
            timer.join(timeout=2)
    assert case.provider.port.sent == []


def test_cancellation_before_first_a4_message_records_zero_delivery(
    studio_case: StudioCase,
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    envelope = _send_envelope(case)

    async def scenario() -> None:
        task = asyncio.create_task(handlers.handle_command(envelope, case.session))
        await asyncio.sleep(0)
        assert case.session.a4_studio_sending is True
        assert case.provider.port.sent == []
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    assert case.session.armed_apply is None
    outcome = case.session.error_journal.entries[-1]
    assert outcome.context["status"] == "interrupted"
    assert outcome.context["sent_count"] == "0"


@pytest.mark.parametrize("fail", [False, True])
def test_a4_attempt_publishes_revoked_current_grants_on_success_and_failure(
    studio_case: StudioCase, fail: bool
) -> None:
    case = studio_case
    assert case.arm()["ok"]
    assert case.prepare()["ok"]
    workspace = case.harness.workspace
    # Synthetic process-local grant exercises revocation, not physical evidence.
    workspace._current_preflight_grants[(case.harness.bank_id, case.harness.entry_id)] = (
        case.harness.clock.current
    )
    if fail:
        case.provider.port.fail_after = 1
    result = case.send()
    assert result["ok"] is not fail
    assert workspace._current_preflight_grants == {}
    events = [
        event for event in case.session.pending_events if event["type"] == "show_bank_changed"
    ]
    assert events
    assert events[-1]["show_bank"] == workspace.state_dict()


def test_a4_preflight_rejects_removed_selection_and_persisted_manifest_drift(
    studio_case: StudioCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = studio_case
    workspace = case.harness.workspace
    bank = workspace.bank(case.harness.bank_id)
    original_load = workspace.store.load

    def changed_manifest(*args: object, **kwargs: object):
        return replace(bank, name="Changed outside this session")

    monkeypatch.setattr(workspace.store, "load", changed_manifest)
    assert case.prepare()["ok"] is False
    monkeypatch.setattr(workspace.store, "load", original_load)
    workspace.return_entry_to_source(case.harness.bank_id, case.harness.entry_id, bank.revision)
    assert case.prepare()["ok"] is False


def test_inactive_show_bank_cannot_lend_a_candidate_to_a4_output(studio_case: StudioCase) -> None:
    case = studio_case
    case.harness.workspace.create_bank(name="Another active bank", description="", notes=())
    assert case.prepare()["ok"] is True
    plan = case.session.a4_studio_plan
    assert plan is not None and not plan.ready
    assert "candidate_not_selected" in plan.blocked_reasons
