"""Passive controller-brain rehearsal scenarios.

These scenarios model virtual controller gestures against the passive
controller mapping catalog. They deliberately do not describe raw controller
messages, MIDI input ports, MIDI learn, feedback LEDs, WebSocket dispatch, or
hardware sends.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final


@dataclass(frozen=True)
class ControllerRehearsalGestureSpec:
    """One virtual controller gesture used for passive rehearsal."""

    step: int
    page_key: str
    slot: int
    gesture: str
    value_delta: int
    operator_goal: str
    expected_intent_key: str
    notes: str


@dataclass(frozen=True)
class ControllerRehearsalScenarioSpec:
    """One deterministic passive controller-brain rehearsal scenario."""

    key: str
    label: str
    profile_key: str
    summary: str
    gestures: tuple[ControllerRehearsalGestureSpec, ...]
    operator_notes: tuple[str, ...]
    blocked_active_actions: tuple[str, ...]


DEFAULT_CONTROLLER_REHEARSAL_SCENARIO: Final[str] = "warehouse-controller-brain-rehearsal"

_WAREHOUSE_REHEARSAL_GESTURES: Final[tuple[ControllerRehearsalGestureSpec, ...]] = (
    ControllerRehearsalGestureSpec(
        step=1,
        page_key="global-brain",
        slot=1,
        gesture="turn clockwise",
        value_delta=12,
        operator_goal="raise passive preview depth before choosing a direction",
        expected_intent_key="global.preview_depth",
        notes="Depth is staged only; no preview or send is executed.",
    ),
    ControllerRehearsalGestureSpec(
        step=2,
        page_key="global-brain",
        slot=7,
        gesture="press",
        value_delta=0,
        operator_goal="choose the industrial macro direction",
        expected_intent_key="macro.industrial",
        notes="Macro selection resolves to intent without mutating a snapshot.",
    ),
    ControllerRehearsalGestureSpec(
        step=3,
        page_key="rytm-pads-5-8",
        slot=1,
        gesture="turn clockwise",
        value_delta=9,
        operator_goal="bring Pad 5 into SRC-first movement",
        expected_intent_key="rytm.pad5.source_amount",
        notes="Pad 5 keeps filter and LFO de-emphasized while SRC stays primary.",
    ),
    ControllerRehearsalGestureSpec(
        step=4,
        page_key="rytm-pads-5-8",
        slot=5,
        gesture="turn clockwise",
        value_delta=14,
        operator_goal="push Pad 6 tom/source movement",
        expected_intent_key="rytm.pad6.source_amount",
        notes="Pad 6 is eligible for useful tom source movement and light filter only.",
    ),
    ControllerRehearsalGestureSpec(
        step=5,
        page_key="rytm-pads-9-12",
        slot=13,
        gesture="turn counterclockwise",
        value_delta=-7,
        operator_goal="prove Pad 12 remains optional but mapped",
        expected_intent_key="rytm.pad12.source_amount",
        notes="Pad 12 stays in the product even when an operator leaves it quiet.",
    ),
    ControllerRehearsalGestureSpec(
        step=6,
        page_key="analog-four-tracks",
        slot=1,
        gesture="turn clockwise",
        value_delta=10,
        operator_goal="stage future Analog Four Track 1 macro movement",
        expected_intent_key="a4.track1.macro_depth",
        notes="Analog Four is still a passive runway in this rehearsal packet.",
    ),
    ControllerRehearsalGestureSpec(
        step=7,
        page_key="style-crates-queue",
        slot=2,
        gesture="press",
        value_delta=0,
        operator_goal="browse the Dark Hypnotic crate",
        expected_intent_key="crate.dark_hypnotic",
        notes="Crate browse remains a local intent selection.",
    ),
    ControllerRehearsalGestureSpec(
        step=8,
        page_key="style-crates-queue",
        slot=10,
        gesture="press",
        value_delta=0,
        operator_goal="stage the first upcoming queue move",
        expected_intent_key="queue.next_1",
        notes="Queue staging does not dispatch Cockpit commands.",
    ),
    ControllerRehearsalGestureSpec(
        step=9,
        page_key="snapshot-recovery-journal",
        slot=16,
        gesture="press and hold",
        value_delta=0,
        operator_goal="verify panic home always resolves to captured anchor intent",
        expected_intent_key="snapshot.panic_home",
        notes="Recovery target is passive until an approved armed bridge exists.",
    ),
)

_WAREHOUSE_OPERATOR_NOTES: Final[tuple[str, ...]] = (
    "Treat the controller as an intent browser, not as a live MIDI input device.",
    "Use SRC-first Rytm pad controls for Pads 5-12 before broad filter or LFO moves.",
    "Keep Pad 12 available for users who want it, while allowing local lock/exclusion.",
    "Analog Four controls are staged as runway intent until a validated A4 hardware path exists.",
)

_BLOCKED_ACTIVE_ACTIONS: Final[tuple[str, ...]] = (
    "open MIDI controller input",
    "MIDI learn or raw CC capture",
    "send controller feedback",
    "dispatch Cockpit WebSocket commands",
    "open MIDI output",
    "arm hardware",
    "send hardware MIDI",
)

_WAREHOUSE_CONTROLLER_REHEARSAL: Final[ControllerRehearsalScenarioSpec] = (
    ControllerRehearsalScenarioSpec(
        key=DEFAULT_CONTROLLER_REHEARSAL_SCENARIO,
        label="Warehouse Controller Brain Rehearsal",
        profile_key="generic-16-encoder-performance",
        summary=(
            "Virtual 16-encoder rehearsal that resolves controller pages into "
            "Rytm, Analog Four, Style Crates, queue, and recovery intent."
        ),
        gestures=_WAREHOUSE_REHEARSAL_GESTURES,
        operator_notes=_WAREHOUSE_OPERATOR_NOTES,
        blocked_active_actions=_BLOCKED_ACTIVE_ACTIONS,
    )
)

CONTROLLER_REHEARSAL_SCENARIOS: Final[Mapping[str, ControllerRehearsalScenarioSpec]] = (
    MappingProxyType({DEFAULT_CONTROLLER_REHEARSAL_SCENARIO: _WAREHOUSE_CONTROLLER_REHEARSAL})
)

__all__ = (
    "CONTROLLER_REHEARSAL_SCENARIOS",
    "DEFAULT_CONTROLLER_REHEARSAL_SCENARIO",
    "ControllerRehearsalGestureSpec",
    "ControllerRehearsalScenarioSpec",
)
