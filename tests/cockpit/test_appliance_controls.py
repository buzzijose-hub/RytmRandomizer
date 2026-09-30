"""Optional controls remain input-only, configured explicitly, and bounded."""

from __future__ import annotations

import logging
from collections import deque

import pytest

from rytm_randomizer.cockpit import appliance_controls as controls_module
from rytm_randomizer.cockpit.appliance_controls import (
    ApplianceBoardConfiguration,
    ApplianceControlIntent,
    ApplianceControlMapper,
    ApplianceControlMapping,
    ApplianceInputAdapter,
    ApplianceInputEvent,
    BoardPinAssignment,
    ConfiguredApplianceControls,
    ControlButtonBinding,
    make_appliance_control_sink,
)
from rytm_randomizer.observability.metrics import MidiMetrics

pytestmark = pytest.mark.fast
_EXPECTED_HISTORY_LIMIT = 128


@pytest.fixture
def control_logs(
    caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> pytest.LogCaptureFixture:
    # The shared harness intentionally stops package logs at its null handler.
    caplog.set_level(logging.DEBUG, logger=controls_module.__name__)
    monkeypatch.setattr(controls_module._logger, "handlers", [caplog.handler])
    monkeypatch.setattr(controls_module._logger, "propagate", False)
    return caplog


def test_configured_input_sink_uses_existing_kiosk_event_contract() -> None:
    events: list[dict[str, object]] = []
    adapter = _Input((ApplianceInputEvent("press", "mutate", 1, 1000),))
    controls = ConfiguredApplianceControls(
        adapter, make_appliance_control_sink(events.append), _board()
    )
    assert controls.poll() == 0 and events == []
    controls.start()
    assert controls.poll() == 1
    assert events == [
        {
            "type": "appliance_control_intent",
            "action": "mutate",
            "delta": 0,
            "source": "physical_input",
        }
    ]
    assert controls.poll() == 0  # a physical edge is never replayed
    controls.stop()


class _Input:
    def __init__(self, events: tuple[ApplianceInputEvent, ...] = ()) -> None:
        self.events = deque(events)
        self.configured: list[ApplianceBoardConfiguration] = []
        self.closed = 0
        self.fail_close = False

    def configure(self, board: ApplianceBoardConfiguration) -> None:
        self.configured.append(board)

    def read_event(self) -> ApplianceInputEvent | None:
        return self.events.popleft() if self.events else None

    def close(self) -> None:
        self.closed += 1
        if self.fail_close:
            raise OSError("reader failed")


def _board() -> ApplianceBoardConfiguration:
    # Test-only lines are explicit; these are not a product wiring assignment.
    return ApplianceBoardConfiguration(
        "mock-board",
        "/dev/gpiochip0",
        (
            BoardPinAssignment("encoder_a", 1),
            BoardPinAssignment("encoder_b", 2),
            BoardPinAssignment("mutate", 3),
            BoardPinAssignment("undo", 4),
        ),
    )


def _event(
    event_id: str, source: str = "mutate", value: int = 1, timestamp: float = 1000
) -> ApplianceInputEvent:
    return ApplianceInputEvent(event_id, source, value, timestamp)  # type: ignore[arg-type]


def test_buttons_share_safe_touch_intents_and_no_arm_or_apply_actions() -> None:
    mapper = ApplianceControlMapper()
    for source, action in [
        ("mutate", "mutate"),
        ("undo", "undo"),
        ("anchor", "capture_anchor"),
        ("encoder_push", "activate_focus"),
    ]:
        intent = mapper.handle(_event(source, source))
        assert intent == ApplianceControlIntent(action)  # type: ignore[arg-type]
        assert intent is not None
        assert intent.to_dict() == {"action": action, "delta": 0, "source": "physical_input"}
    with pytest.raises(ValueError, match="cannot request arm or apply"):
        ApplianceControlIntent("apply")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-delta intent"):
        ControlButtonBinding("mutate", "arm")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="non-delta intent"):
        ControlButtonBinding("mutate", "focus_step")
    with pytest.raises(ValueError, match="bounded delta"):
        ApplianceControlIntent("undo", 1)
    with pytest.raises(ValueError, match="bounded delta"):
        ApplianceControlIntent("focus_step", 33)


def test_one_intent_per_press_no_repeat_and_bounce_or_duplicate_or_stale() -> None:
    mapper = ApplianceControlMapper()
    assert mapper.handle(_event("first")) == ApplianceControlIntent("mutate")
    assert mapper.handle(_event("first")) is None
    assert mapper.handle(_event("repeat", timestamp=1001)) is None
    assert mapper.handle(_event("release", value=0, timestamp=1020)) is None
    assert mapper.handle(_event("bounce", timestamp=1030)) is None
    assert mapper.handle(_event("release2", value=0, timestamp=1200)) is None
    assert mapper.handle(_event("second", timestamp=1201)) == ApplianceControlIntent("mutate")
    assert mapper.handle(_event("late", "undo", timestamp=1100)) is None
    assert mapper.handle(_event("never_pressed_release", "undo", 0, 1300)) is None
    mapper.reset()
    assert mapper.handle(_event("first")) == ApplianceControlIntent("mutate")
    with pytest.raises(TypeError, match="ApplianceInputEvent"):
        mapper.handle({})  # type: ignore[arg-type]


def test_mapping_is_configurable_and_encoder_moves_focus_only() -> None:
    mapper = ApplianceControlMapper(
        ApplianceControlMapping(encoder_step=3, buttons=(ControlButtonBinding("mutate", "undo"),))
    )
    assert mapper.handle(_event("cw", "encoder")) == ApplianceControlIntent("focus_step", 3)
    assert mapper.handle(_event("ccw", "encoder", -1)) == ApplianceControlIntent("focus_step", -3)
    assert mapper.handle(_event("remapped")) == ApplianceControlIntent("undo")
    assert mapper.handle(_event("unbound", "anchor")) is None
    for index in range(256):
        mapper.handle(_event(str(index), "encoder", timestamp=1100 + index))
    assert len(mapper._seen) == _EXPECTED_HISTORY_LIMIT


@pytest.mark.parametrize(
    "kwargs",
    [
        {"schema_version": 2},
        {"schema_version": True},
        {"encoder_step": 0},
        {"encoder_step": True},
        {"encoder_step": 33},
        {"debounce_ms": -1},
        {"debounce_ms": 2001},
        {"buttons": []},
        {"buttons": ("bad",)},
        {"buttons": (ControlButtonBinding("undo", "undo"), ControlButtonBinding("undo", "mutate"))},
    ],
)
def test_invalid_mapping_refused(kwargs: dict[str, object]) -> None:
    with pytest.raises((ValueError, TypeError)):
        ApplianceControlMapping(**kwargs)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="supported physical button"):
        ControlButtonBinding("encoder", "undo")


@pytest.mark.parametrize(
    "args",
    [
        ("", "encoder", 1, 0),
        ("x" * 129, "encoder", 1, 0),
        ("x", "bad", 1, 0),
        ("x", "encoder", 0, 0),
        ("x", "encoder", True, 0),
        ("x", "undo", 2, 0),
        ("x", "undo", 1, -1),
        ("x", "undo", 1, float("nan")),
        ("x", "undo", 1, float("inf")),
        ("x", "undo", 1, True),
        ("x", "undo", 1, "0"),
    ],
)
def test_malformed_events_refused(args: tuple[object, ...]) -> None:
    with pytest.raises((ValueError, TypeError)):
        ApplianceInputEvent(*args)  # type: ignore[arg-type]


@pytest.mark.parametrize("args", [("bad", 1), ("mutate", -1), ("mutate", 1024), ("mutate", True)])
def test_invalid_pin_assignment_refused(args: tuple[object, ...]) -> None:
    with pytest.raises((ValueError, TypeError)):
        BoardPinAssignment(*args)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "args",
    [
        ("", "/dev/gpiochip0", (BoardPinAssignment("mutate", 1),)),
        ("b" * 129, "/dev/gpiochip0", (BoardPinAssignment("mutate", 1),)),
        ("b", "gpiochip0", (BoardPinAssignment("mutate", 1),)),
        ("b", "/dev/gpiochip0/../1", (BoardPinAssignment("mutate", 1),)),
        ("b", "/dev/gpiochip0", ()),
        ("b", "/dev/gpiochip0", [BoardPinAssignment("mutate", 1)]),
        ("b", "/dev/gpiochip0", ("bad",)),
        ("b", "/dev/gpiochip0", (BoardPinAssignment("mutate", 1), BoardPinAssignment("undo", 1))),
        ("b", "/dev/gpiochip0", (BoardPinAssignment("mutate", 1), BoardPinAssignment("mutate", 2))),
        ("b", "/dev/gpiochip0", (BoardPinAssignment("encoder_a", 1),)),
        ("b", "/dev/gpiochip0", (BoardPinAssignment("encoder_b", 1),)),
    ],
)
def test_invalid_or_ambiguous_board_refused(args: tuple[object, ...]) -> None:
    with pytest.raises((ValueError, TypeError)):
        ApplianceBoardConfiguration(*args)  # type: ignore[arg-type]


def test_no_pin_activity_without_selected_configuration_and_bounded_polling() -> None:
    reader = _Input((_event("e1"), _event("e2", "undo")))
    intents: list[ApplianceControlIntent] = []
    controls = ConfiguredApplianceControls(reader, intents.append)
    assert controls.poll() == 0
    controls.stop()
    assert reader.configured == []
    assert reader.closed == 0
    with pytest.raises(ValueError, match="selected board configuration"):
        controls.start()
    assert reader.configured == []
    controls.board = _board()
    controls.start()
    controls.start()
    assert reader.configured == [_board()]
    assert controls.poll(maximum_events=1) == 1
    assert intents == [ApplianceControlIntent("mutate")]
    assert len(reader.events) == 1
    assert controls.poll() == 1
    assert controls.poll() == 0
    reader.events.append(_event("release", value=0))
    assert controls.poll() == 0
    controls.stop()
    controls.stop()
    assert reader.closed == 1
    assert controls.poll() == 0
    assert not controls.mapper._seen
    for maximum in (0, 129, True):
        with pytest.raises((ValueError, TypeError)):
            controls.poll(maximum_events=maximum)


def test_close_error_still_drops_transient_input_state() -> None:
    reader = _Input((_event("e"),))
    reader.fail_close = True
    controls = ConfiguredApplianceControls(reader, lambda _: None, _board())
    controls.start()
    controls.poll()
    with pytest.raises(OSError, match="reader failed"):
        controls.stop()
    assert controls.poll() == 0
    assert not controls.mapper._seen


def test_input_protocol_is_structural_and_declared_methods_are_inert() -> None:
    reader = _Input()
    assert isinstance(reader, ApplianceInputAdapter)
    assert ApplianceInputAdapter.configure(reader, _board()) is None
    assert ApplianceInputAdapter.read_event(reader) is None
    assert ApplianceInputAdapter.close(reader) is None
    assert reader.configured == []
    assert reader.closed == 0


def test_only_board_configured_sources_are_forwarded() -> None:
    reader = _Input((_event("bad-source", "undo"), _event("selected-source")))
    board = ApplianceBoardConfiguration(
        "button-only", "/dev/gpiochip1", (BoardPinAssignment("mutate", 4),)
    )
    intents: list[ApplianceControlIntent] = []
    controls = ConfiguredApplianceControls(reader, intents.append, board)
    controls.start()
    assert controls.poll() == 1
    assert intents == [ApplianceControlIntent("mutate")]
    controls.stop()


def test_filter_observability_is_bounded_and_excludes_event_identity(
    control_logs: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog = control_logs
    metrics = MidiMetrics()
    monkeypatch.setattr(controls_module, "get_metrics", lambda: metrics)
    mapper = ApplianceControlMapper(
        ApplianceControlMapping(buttons=(ControlButtonBinding("mutate", "mutate"),))
    )
    event = _event("private-event-identity")
    assert mapper.handle(event) == ApplianceControlIntent("mutate")
    assert mapper.handle(event) is None
    assert mapper.handle(_event("private-stale", "undo", timestamp=900)) is None
    assert mapper.handle(_event("private-release", value=0, timestamp=1001)) is None
    assert mapper.handle(_event("private-bounce", timestamp=1020)) is None
    assert mapper.handle(_event("private-release2", value=0, timestamp=1200)) is None
    assert mapper.handle(_event("private-next", timestamp=1201)) == ApplianceControlIntent("mutate")
    assert mapper.handle(_event("private-repeat", timestamp=1202)) is None
    assert mapper.handle(_event("private-unbound", "anchor", timestamp=1250)) is None
    assert mapper.handle(
        _event("private-detent", "encoder", timestamp=1270)
    ) == ApplianceControlIntent("focus_step", 1)
    outcomes = [
        record.__dict__["outcome"]
        for record in caplog.records
        if record.message == "appliance_control_input"
    ]
    assert outcomes == [
        "accepted",
        "duplicate",
        "stale",
        "released",
        "debounced",
        "released",
        "accepted",
        "repeated_press",
        "unconfigured",
        "accepted",
    ]
    assert "private-" not in str([record.__dict__ for record in caplog.records])
    assert metrics.errors_by_kind == {}
    assert metrics.cc_sent_by_channel == {}


def test_control_lifecycle_logs_counts_without_board_wiring_or_input_payload(
    control_logs: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog = control_logs
    metrics = MidiMetrics()
    monkeypatch.setattr(controls_module, "get_metrics", lambda: metrics)
    reader = _Input(
        (
            _event("private-unconfigured", "undo"),
            _event("private-press"),
            _event("private-release", value=0, timestamp=1001),
        )
    )
    expected_processed_count = len(reader.events)
    board = ApplianceBoardConfiguration(
        "private-board-identity", "/dev/gpiochip9", (BoardPinAssignment("mutate", 79),)
    )
    intents: list[ApplianceControlIntent] = []
    controls = ConfiguredApplianceControls(reader, intents.append, board)
    controls.start()
    controls.start()
    assert controls.poll() == 1
    controls.stop()
    controls.stop()
    assert intents == [ApplianceControlIntent("mutate")]
    started = [
        record for record in caplog.records if record.message == "appliance_controls_started"
    ]
    stopped = [
        record for record in caplog.records if record.message == "appliance_controls_stopped"
    ]
    polls = [record for record in caplog.records if record.message == "appliance_controls_poll"]
    assert len(started) == 1 and started[0].__dict__["configured_sources_count"] == 1
    assert len(stopped) == 1 and stopped[0].__dict__["sent_midi"] is False
    assert len(polls) == 1
    assert polls[0].__dict__["processed_count"] == expected_processed_count
    assert polls[0].__dict__["emitted_count"] == len(intents)
    records = str([record.__dict__ for record in caplog.records])
    assert "private-" not in records and "/dev/gpiochip9" not in records
    assert "board_id" not in records and "event_id" not in records and "timestamp_ms" not in records
    assert metrics.errors_by_kind == {} and metrics.cc_sent_by_channel == {}


@pytest.mark.parametrize(
    "failure", ["configure_failed", "configure_cleanup_failed", "poll_failed", "close_failed"]
)
def test_actual_adapter_failures_record_bounded_errors_and_cleanup_state(
    failure: str, control_logs: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
    caplog = control_logs
    metrics = MidiMetrics()
    monkeypatch.setattr(controls_module, "get_metrics", lambda: metrics)
    reader = _Input()
    controls = ConfiguredApplianceControls(reader, lambda _: None, _board())
    controls.mapper.handle(_event("private-transient-state"))

    def fail_configure(_: ApplianceBoardConfiguration) -> None:
        raise RuntimeError("private-adapter-fault")

    def fail_read() -> None:
        raise RuntimeError("private-adapter-fault")

    expected = {f"appliance.controls.{failure}": 1}
    if failure.startswith("configure"):
        monkeypatch.setattr(reader, "configure", fail_configure)
        if failure == "configure_cleanup_failed":
            reader.fail_close = True
            expected["appliance.controls.configure_failed"] = 1
        with pytest.raises(RuntimeError, match="private-adapter-fault"):
            controls.start()
        assert reader.closed == 1
    else:
        controls.start()
        if failure == "poll_failed":
            monkeypatch.setattr(reader, "read_event", fail_read)
            with pytest.raises(RuntimeError, match="private-adapter-fault"):
                controls.poll()
            controls.stop()
        else:
            reader.fail_close = True
            with pytest.raises(OSError, match="reader failed"):
                controls.stop()
    assert controls.poll() == 0
    assert not controls.mapper._seen and not controls._configured_sources
    assert metrics.errors_by_kind == expected
    assert metrics.cc_sent_by_channel == {}
    reasons = [
        record.__dict__["reason"]
        for record in caplog.records
        if record.message == "appliance_controls_failed"
    ]
    assert {f"appliance.controls.{reason}" for reason in reasons} == expected.keys()
    assert "private-" not in str([record.__dict__ for record in caplog.records])


def test_failed_intent_sink_is_not_replayed_or_counted_as_a_midi_send(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metrics = MidiMetrics()
    monkeypatch.setattr(controls_module, "get_metrics", lambda: metrics)
    reader = _Input((_event("private-press"),))

    def fail_sink(_: ApplianceControlIntent) -> None:
        raise RuntimeError("kiosk unavailable")

    controls = ConfiguredApplianceControls(reader, fail_sink, _board())
    controls.start()
    with pytest.raises(RuntimeError, match="kiosk unavailable"):
        controls.poll()
    delivered: list[ApplianceControlIntent] = []
    controls.intent_sink = delivered.append
    assert controls.poll() == 0 and not delivered
    controls.stop()
    assert metrics.errors_by_kind == {"appliance.controls.poll_failed": 1}
    assert metrics.cc_sent_by_channel == {}
