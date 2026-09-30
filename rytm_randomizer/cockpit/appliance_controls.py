"""Optional physical inputs translated into the same appliance command intents.

No GPIO package is imported here. An explicitly selected board configuration
and an injected input adapter are both required before any pin is configured.
Intents are requests to the touch command handler; they cannot arm or apply.
"""

from __future__ import annotations

import math
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Final, Literal, Protocol, TypeVar, cast, runtime_checkable

from ..guardrails.input_validation import require_int, require_text
from ..observability.logging import get_logger
from ..observability.metrics import get_metrics

ControlSource = Literal["encoder", "encoder_push", "mutate", "undo", "anchor"]
ControlAction = Literal["focus_step", "activate_focus", "mutate", "undo", "capture_anchor"]
ControlPinRole = Literal["encoder_a", "encoder_b", "encoder_push", "mutate", "undo", "anchor"]
APPLIANCE_CONTROL_EVENT: Final[str] = "appliance_control_intent"
_FOCUS_DELTA_LIMIT: Final[int] = 32
_DEBOUNCE_MS_LIMIT: Final[int] = 2000
_GPIO_LINE_LIMIT: Final[int] = 1023
_IDENTIFIER_LENGTH_LIMIT: Final[int] = 128
_EVENT_HISTORY_LIMIT: Final[int] = 128
_POLL_EVENT_LIMIT: Final[int] = 128
_DEFAULT_POLL_EVENTS: Final[int] = 32
_logger = get_logger(__name__)
_InputOutcome = Literal[
    "accepted", "duplicate", "stale", "released", "repeated_press", "debounced", "unconfigured"
]
_ControlError = Literal[
    "configure_failed", "configure_cleanup_failed", "poll_failed", "close_failed"
]


def _record_control_error(reason: _ControlError) -> None:
    """Record only bounded actual failures; input filtering is not an error."""

    get_metrics().record_error(f"appliance.controls.{reason}")
    _logger.warning("appliance_controls_failed", extra={"reason": reason, "sent_midi": False})


def _record_input(outcome: _InputOutcome, source: ControlSource) -> None:
    _logger.debug("appliance_control_input", extra={"outcome": outcome, "input_source": source})


_BUTTON_SOURCES: Final[frozenset[ControlSource]] = frozenset(
    {"encoder_push", "mutate", "undo", "anchor"}
)
_ACTIONS: Final[frozenset[ControlAction]] = frozenset(
    {"focus_step", "activate_focus", "mutate", "undo", "capture_anchor"}
)
_PIN_ROLES: Final[frozenset[ControlPinRole]] = frozenset(
    {"encoder_a", "encoder_b", "encoder_push", "mutate", "undo", "anchor"}
)

_Item = TypeVar("_Item")


def _typed_tuple(value: object, item_type: type[_Item], label: str) -> tuple[_Item, ...]:
    if not isinstance(value, tuple):
        raise TypeError(f"{label} must be an immutable tuple")
    items = cast(tuple[object, ...], value)
    if any(not isinstance(item, item_type) for item in items):
        raise TypeError(f"{label} has an invalid item")
    return cast(tuple[_Item, ...], items)


@dataclass(frozen=True)
class ApplianceControlIntent:
    """A local UI command request; normal safety gates remain downstream."""

    action: ControlAction
    delta: int = 0

    def __post_init__(self) -> None:
        if self.action not in _ACTIONS:
            raise ValueError("physical controls cannot request arm or apply")
        require_int(self.delta, "control intent delta")
        if (
            self.action == "focus_step"
            and not -_FOCUS_DELTA_LIMIT <= self.delta <= _FOCUS_DELTA_LIMIT
        ) or (self.action != "focus_step" and self.delta != 0):
            raise ValueError("only focus_step may carry a bounded delta")

    def to_dict(self) -> dict[str, object]:
        return {"action": self.action, "delta": self.delta, "source": "physical_input"}


def make_appliance_control_sink(
    emit_event: Callable[[dict[str, object]], object],
) -> Callable[[ApplianceControlIntent], None]:
    """Wire configured inputs to one kiosk's existing bounded event queue.

    The frontend consumes these intents through its ordinary touch handlers.
    Select one authenticated kiosk queue rather than broadcasting physical
    presses to multiple clients. This bridge does not queue or replay commands
    across a disconnected browser and never opens a GPIO or MIDI device.
    """

    def emit(intent: ApplianceControlIntent) -> None:
        emit_event({"type": APPLIANCE_CONTROL_EVENT, **intent.to_dict()})

    return emit


@dataclass(frozen=True)
class ControlButtonBinding:
    source: ControlSource
    action: ControlAction

    def __post_init__(self) -> None:
        if self.source not in _BUTTON_SOURCES:
            raise ValueError("button binding source must be a supported physical button")
        if self.action not in _ACTIONS or self.action == "focus_step":
            raise ValueError("button binding must request a safe non-delta intent")


@dataclass(frozen=True)
class ApplianceControlMapping:
    """Versioned, configurable intent mapping, independent of board wiring."""

    schema_version: Literal[1] = 1
    encoder_step: int = 1
    debounce_ms: int = 150
    buttons: tuple[ControlButtonBinding, ...] = (
        ControlButtonBinding("encoder_push", "activate_focus"),
        ControlButtonBinding("mutate", "mutate"),
        ControlButtonBinding("undo", "undo"),
        ControlButtonBinding("anchor", "capture_anchor"),
    )

    def __post_init__(self) -> None:
        if require_int(self.schema_version, "control mapping schema_version") != 1:
            raise ValueError("unsupported control mapping schema_version")
        if not 1 <= require_int(self.encoder_step, "encoder_step") <= _FOCUS_DELTA_LIMIT:
            raise ValueError("encoder_step must be in 1..32")
        if not 0 <= require_int(self.debounce_ms, "debounce_ms") <= _DEBOUNCE_MS_LIMIT:
            raise ValueError("debounce_ms must be in 0..2000")
        _typed_tuple(self.buttons, ControlButtonBinding, "buttons")
        if len({item.source for item in self.buttons}) != len(self.buttons):
            raise ValueError("duplicate physical button source")


@dataclass(frozen=True)
class BoardPinAssignment:
    """Explicit chip-line assignment supplied by the selected board profile."""

    role: ControlPinRole
    line: int

    def __post_init__(self) -> None:
        if self.role not in _PIN_ROLES:
            raise ValueError("unknown board pin role")
        if not 0 <= require_int(self.line, "GPIO chip line") <= _GPIO_LINE_LIMIT:
            raise ValueError("GPIO chip line must be in 0..1023")


@dataclass(frozen=True)
class ApplianceBoardConfiguration:
    board_id: str
    gpio_chip: str
    pins: tuple[BoardPinAssignment, ...]

    def __post_init__(self) -> None:
        if (
            not require_text(self.board_id, "board_id").strip()
            or len(self.board_id) > _IDENTIFIER_LENGTH_LIMIT
        ):
            raise ValueError("an explicit bounded board_id is required")
        if (
            not require_text(self.gpio_chip, "gpio_chip").startswith("/dev/gpiochip")
            or not self.gpio_chip[len("/dev/gpiochip") :].isdigit()
        ):
            raise ValueError("gpio_chip must identify an explicit /dev/gpiochipN")
        _typed_tuple(self.pins, BoardPinAssignment, "pins")
        if not self.pins:
            raise ValueError("explicit immutable pin assignments are required")
        roles = {pin.role for pin in self.pins}
        if len(roles) != len(self.pins) or len({pin.line for pin in self.pins}) != len(self.pins):
            raise ValueError("pin roles and chip lines must be unique")
        if ("encoder_a" in roles) != ("encoder_b" in roles):
            raise ValueError("both encoder phase lines must be configured together")


@dataclass(frozen=True)
class ApplianceInputEvent:
    """Already interpreted input; an adapter owns board-specific quadrature."""

    event_id: str
    source: ControlSource
    value: int
    timestamp_ms: float

    def __post_init__(self) -> None:
        if (
            not require_text(self.event_id, "event_id")
            or len(self.event_id) > _IDENTIFIER_LENGTH_LIMIT
        ):
            raise ValueError("a bounded input event_id is required")
        if self.source not in _BUTTON_SOURCES and self.source != "encoder":
            raise ValueError("unsupported physical input source")
        require_int(self.value, "physical input value")
        if self.source == "encoder" and self.value not in {-1, 1}:
            raise ValueError("encoder event must represent one -1 or +1 detent")
        if self.source != "encoder" and self.value not in {0, 1}:
            raise ValueError("button events must use 0 release or 1 press")
        timestamp = cast(object, self.timestamp_ms)
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not math.isfinite(timestamp)
            or timestamp < 0
        ):
            raise ValueError("timestamp_ms must be finite and nonnegative")


@runtime_checkable
class ApplianceInputAdapter(Protocol):
    """Optional dependency-injected input reader; no MIDI methods exist."""

    def configure(self, board: ApplianceBoardConfiguration) -> None: ...

    def read_event(self) -> ApplianceInputEvent | None: ...

    def close(self) -> None: ...


@dataclass
class ApplianceControlMapper:
    mapping: ApplianceControlMapping = field(default_factory=ApplianceControlMapping)
    _seen: deque[str] = field(
        default_factory=lambda: deque(maxlen=_EVENT_HISTORY_LIMIT), init=False
    )
    _pressed: set[ControlSource] = field(default_factory=lambda: set[ControlSource](), init=False)
    _last_press: dict[ControlSource, float] = field(
        default_factory=lambda: dict[ControlSource, float](), init=False
    )
    _latest_timestamp_ms: float = field(default=-1, init=False)

    def handle(self, event: object) -> ApplianceControlIntent | None:
        """Emit at most one intent per fresh press/detent, never auto-repeat."""

        if not isinstance(event, ApplianceInputEvent):
            raise TypeError("physical input must be an ApplianceInputEvent")
        outcome, intent = self._interpret(event)
        _record_input(outcome, event.source)
        return intent

    def _interpret(
        self, event: ApplianceInputEvent
    ) -> tuple[_InputOutcome, ApplianceControlIntent | None]:
        if event.event_id in self._seen:
            return "duplicate", None
        if event.timestamp_ms < self._latest_timestamp_ms:
            return "stale", None
        self._seen.append(event.event_id)
        self._latest_timestamp_ms = event.timestamp_ms
        if event.source == "encoder":
            return "accepted", ApplianceControlIntent(
                "focus_step", event.value * self.mapping.encoder_step
            )
        return self._button_intent(event)

    def _button_intent(
        self, event: ApplianceInputEvent
    ) -> tuple[_InputOutcome, ApplianceControlIntent | None]:
        if event.value == 0:
            self._pressed.discard(event.source)
            return "released", None
        if event.source in self._pressed:
            return "repeated_press", None
        self._pressed.add(event.source)
        prior = self._last_press.get(event.source)
        if prior is not None and event.timestamp_ms - prior < self.mapping.debounce_ms:
            return "debounced", None
        self._last_press[event.source] = event.timestamp_ms
        binding = next((item for item in self.mapping.buttons if item.source == event.source), None)
        return (
            ("unconfigured", None)
            if binding is None
            else ("accepted", ApplianceControlIntent(binding.action))
        )

    def reset(self) -> None:
        """Drop input state after shutdown/restart; no pending work is replayed."""

        self._seen.clear()
        self._pressed.clear()
        self._last_press.clear()
        self._latest_timestamp_ms = -1


@dataclass
class ConfiguredApplianceControls:
    """Bounded polling bridge into the touch intent sink, when configured."""

    adapter: ApplianceInputAdapter
    intent_sink: Callable[[ApplianceControlIntent], None]
    board: ApplianceBoardConfiguration | None = None
    mapper: ApplianceControlMapper = field(default_factory=ApplianceControlMapper)
    _started: bool = field(default=False, init=False)
    _configured_sources: frozenset[ControlSource] = field(
        default_factory=lambda: frozenset[ControlSource](), init=False
    )

    def start(self) -> None:
        if self._started:
            _logger.debug("appliance_controls_start", extra={"outcome": "already_started"})
            return
        if self.board is None:
            _logger.info(
                "appliance_controls_start_refused", extra={"reason": "board_configuration_required"}
            )
            raise ValueError("physical controls require a selected board configuration")
        try:
            self.adapter.configure(self.board)
        except (OSError, RuntimeError, TypeError, ValueError):
            _record_control_error("configure_failed")
            # An adapter may have acquired some lines before failing. Close it
            # once and preserve the configuration error even if cleanup fails.
            try:
                self.adapter.close()
            except (OSError, RuntimeError, TypeError, ValueError):
                _record_control_error("configure_cleanup_failed")
            self.mapper.reset()
            raise
        roles = {pin.role for pin in self.board.pins}
        self._configured_sources = frozenset(
            cast(ControlSource, role) for role in roles if role not in {"encoder_a", "encoder_b"}
        )
        if "encoder_a" in roles:
            self._configured_sources |= frozenset[ControlSource]({"encoder"})
        self._started = True
        _logger.info(
            "appliance_controls_started",
            extra={"configured_sources_count": len(self._configured_sources), "sent_midi": False},
        )

    def poll(self, *, maximum_events: int = _DEFAULT_POLL_EVENTS) -> int:
        """Read bounded work; the sink uses normal command validation/gating."""

        if not 1 <= require_int(maximum_events, "maximum_events") <= _POLL_EVENT_LIMIT:
            _logger.info("appliance_controls_poll_refused", extra={"reason": "event_limit_invalid"})
            raise ValueError("maximum_events must be in 1..128")
        if not self._started:
            _logger.debug(
                "appliance_controls_poll",
                extra={"outcome": "inactive", "processed_count": 0, "emitted_count": 0},
            )
            return 0
        emitted = 0
        processed = 0
        try:
            for _ in range(maximum_events):
                event = self.adapter.read_event()
                if event is None:
                    break
                processed += 1
                if event.source not in self._configured_sources:
                    _record_input("unconfigured", event.source)
                    continue
                intent = self.mapper.handle(event)
                if intent is not None:
                    self.intent_sink(intent)
                    emitted += 1
        except (OSError, RuntimeError, TypeError, ValueError):
            _record_control_error("poll_failed")
            raise
        _logger.debug(
            "appliance_controls_poll",
            extra={"outcome": "completed", "processed_count": processed, "emitted_count": emitted},
        )
        return emitted

    def stop(self) -> None:
        if self._started:
            self._started = False
            self._configured_sources = frozenset()
            try:
                self.adapter.close()
            except (OSError, RuntimeError, TypeError, ValueError):
                _record_control_error("close_failed")
                raise
            finally:
                self.mapper.reset()
                _logger.info("appliance_controls_stopped", extra={"sent_midi": False})
        else:
            _logger.debug("appliance_controls_stop", extra={"outcome": "inactive"})


__all__ = [
    "APPLIANCE_CONTROL_EVENT",
    "ApplianceBoardConfiguration",
    "ApplianceControlIntent",
    "ApplianceControlMapper",
    "ApplianceControlMapping",
    "ApplianceInputAdapter",
    "ApplianceInputEvent",
    "BoardPinAssignment",
    "ConfiguredApplianceControls",
    "ControlButtonBinding",
    "make_appliance_control_sink",
]
