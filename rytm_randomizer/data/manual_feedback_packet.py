"""Canonical manual-feedback packet data.

The data in this module is intentionally passive: it describes what an
operator should observe, capture, and route to review after installer,
profile-wizard, cockpit, and hardware-smoke testing. It does not launch a GUI,
open MIDI ports, or send MIDI.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Literal, TypeAlias

ManualFeedbackCategory: TypeAlias = Literal[
    "installer",
    "cockpit",
    "profile",
    "analyzer",
    "export",
    "mock",
    "hardware",
]
ManualFeedbackPriority: TypeAlias = Literal["blocker", "high", "medium", "low", "info"]


@dataclass(frozen=True)
class ManualFeedbackStep:
    """One operator-observation prompt in a manual feedback packet."""

    key: str
    category: ManualFeedbackCategory
    title: str
    prompt: str
    capture: str
    expected: str
    priority: ManualFeedbackPriority
    reviewer_note: str


@dataclass(frozen=True)
class ManualFeedbackScenario:
    """A named subset of feedback prompts for a manual testing pass."""

    key: str
    title: str
    summary: str
    step_keys: tuple[str, ...]
    review_focus_keys: tuple[str, ...]


DEFAULT_MANUAL_FEEDBACK_SCENARIO: Final[str] = "full"

MANUAL_FEEDBACK_STEPS: Final[tuple[ManualFeedbackStep, ...]] = (
    ManualFeedbackStep(
        key="installer-artifact",
        category="installer",
        title="Installer artifact and launch",
        prompt="Confirm which downloaded installer/artifact was used and whether the unsigned warning appeared.",
        capture="installer filename, GitHub Actions run/artifact, warning screenshot if present",
        expected="installer launches the cockpit without requiring repository source commands",
        priority="high",
        reviewer_note="Confirms Eddie's installer path is usable before deeper product feedback.",
    ),
    ManualFeedbackStep(
        key="cockpit-connection-state",
        category="cockpit",
        title="Cockpit connection state",
        prompt="Record whether the cockpit reaches Mock/Safe or remains reconnecting.",
        capture="cockpit status bar plus sidecar terminal lines",
        expected="GUI shows Mock Safe, a backend port, and no unsaved hardware sends",
        priority="high",
        reviewer_note="Separates installer launch defects from sidecar/WebSocket startup defects.",
    ),
    ManualFeedbackStep(
        key="profile-create-flow",
        category="profile",
        title="Profile wizard create flow",
        prompt="Walk Name -> Add -> Analyze -> Review with one reference track or text source.",
        capture="source type, source label, wizard step, and any disabled Review/Create state",
        expected="analysis completes or emits a specific actionable setup error",
        priority="high",
        reviewer_note="Captures whether Phase 3 is functionally testable before UI polish.",
    ),
    ManualFeedbackStep(
        key="analyzer-style-extra",
        category="analyzer",
        title="Analyzer dependency gate",
        prompt="If analysis reports a missing optional extra, record the exact extra and recovery path.",
        capture="exact missing-extra/error text and whether retry succeeds",
        expected="installer bundle includes analyzer dependency or the UI gives a one-click-clear next action",
        priority="blocker",
        reviewer_note="Current manual test saw the style optional-extra message while analyzing The Bells.",
    ),
    ManualFeedbackStep(
        key="reference-analysis-result",
        category="analyzer",
        title="Reference analysis result",
        prompt="After a track such as The Bells or Doggystyle analyzes, capture the generated traits and confidence.",
        capture="trait list, percentages, source label, and whether the result feels like inspiration rather than a copy",
        expected="traits summarize musical behavior without claiming to recreate copyrighted material",
        priority="medium",
        reviewer_note="Feeds the future reference-track analyzer design with concrete operator feedback.",
    ),
    ManualFeedbackStep(
        key="export-model-no-op",
        category="export",
        title="Export model action",
        prompt="Press Export Model after analysis and record whether a file, save dialog, toast, or error appears.",
        capture="screenshot plus backend/console output after pressing Export Model",
        expected="export either writes/prompts for a .rymp artifact or shows a classified error",
        priority="blocker",
        reviewer_note="Manual test reported Export Model appeared to do nothing.",
    ),
    ManualFeedbackStep(
        key="pad-scope-gap",
        category="cockpit",
        title="Pad/device scope expectation",
        prompt="Record visible pad/device coverage versus expected 12 Rytm pads plus Analog Four device visibility.",
        capture="screenshot of pad grid/device rail and notes on missing pads or devices",
        expected="Rytm 12-pad path is tracked separately from current 4-pad mock surface",
        priority="high",
        reviewer_note="Keeps 4-pad legacy cockpit behavior separate from the 12-pad/A4 product goal.",
    ),
    ManualFeedbackStep(
        key="mock-send-controls",
        category="mock",
        title="Mock SEND and undo controls",
        prompt="Exercise Preview/Prepare/SEND/Undo/Save in Mock mode and record button state transitions.",
        capture="button enabled/disabled states, history entries, and any no-op clicks",
        expected="mock actions never open ports or send MIDI and give deterministic operator feedback",
        priority="medium",
        reviewer_note="Surfaces GUI control contract gaps without touching hardware.",
    ),
    ManualFeedbackStep(
        key="hardware-arm-boundary",
        category="hardware",
        title="Hardware arm boundary",
        prompt="Before any hardware smoke test, confirm the path requires explicit --arm or a locked GUI hardware toggle.",
        capture="command or GUI state showing the explicit armed boundary",
        expected="no unattended hardware behavior; operator chooses the port and action explicitly",
        priority="blocker",
        reviewer_note="Preserves the project-wide passive default while manual testing proceeds.",
    ),
    ManualFeedbackStep(
        key="hardware-stop-conditions",
        category="hardware",
        title="Hardware stop conditions",
        prompt="If an approved smoke test is run, stop at the first unexpected pad/device/port behavior.",
        capture="track, command, selected port, expected result, actual result, and stop reason",
        expected="one observation row per action; no loops continue after unexpected behavior",
        priority="blocker",
        reviewer_note="Turns manual hardware feedback into reproducible review evidence.",
    ),
)

MANUAL_FEEDBACK_SCENARIOS: Final[tuple[ManualFeedbackScenario, ...]] = (
    ManualFeedbackScenario(
        key="full",
        title="Full manual validation feedback",
        summary="Installer, cockpit, profile wizard, analyzer, export, mock controls, and hardware boundary.",
        step_keys=tuple(step.key for step in MANUAL_FEEDBACK_STEPS),
        review_focus_keys=("analyzer-style-extra", "export-model-no-op", "pad-scope-gap"),
    ),
    ManualFeedbackScenario(
        key="installer",
        title="Installer and sidecar feedback",
        summary="Installer artifact, unsigned warning, cockpit launch, and WebSocket/sidecar state.",
        step_keys=("installer-artifact", "cockpit-connection-state"),
        review_focus_keys=("installer-artifact", "cockpit-connection-state"),
    ),
    ManualFeedbackScenario(
        key="profile",
        title="Profile wizard and analyzer feedback",
        summary="Profile creation, reference analysis, export action, and pad-scope product gaps.",
        step_keys=(
            "profile-create-flow",
            "analyzer-style-extra",
            "reference-analysis-result",
            "export-model-no-op",
            "pad-scope-gap",
        ),
        review_focus_keys=("analyzer-style-extra", "export-model-no-op", "pad-scope-gap"),
    ),
    ManualFeedbackScenario(
        key="mock",
        title="Mock cockpit control feedback",
        summary="Mock-safe button, history, snapshot, and no-send control behavior.",
        step_keys=("cockpit-connection-state", "mock-send-controls", "pad-scope-gap"),
        review_focus_keys=("mock-send-controls", "pad-scope-gap"),
    ),
    ManualFeedbackScenario(
        key="hardware",
        title="Hardware-boundary smoke feedback",
        summary="Explicit arm boundary and stop-condition capture for approved manual hardware passes.",
        step_keys=("hardware-arm-boundary", "hardware-stop-conditions", "pad-scope-gap"),
        review_focus_keys=("hardware-arm-boundary", "hardware-stop-conditions"),
    ),
    ManualFeedbackScenario(
        key="review",
        title="Reviewer triage feedback",
        summary="The current highest-priority defects to hand back to review.",
        step_keys=("analyzer-style-extra", "export-model-no-op", "pad-scope-gap"),
        review_focus_keys=("analyzer-style-extra", "export-model-no-op", "pad-scope-gap"),
    ),
)

MANUAL_FEEDBACK_STEPS_BY_KEY: Final[MappingProxyType[str, ManualFeedbackStep]] = MappingProxyType(
    {step.key: step for step in MANUAL_FEEDBACK_STEPS}
)
MANUAL_FEEDBACK_SCENARIOS_BY_KEY: Final[MappingProxyType[str, ManualFeedbackScenario]] = (
    MappingProxyType({scenario.key: scenario for scenario in MANUAL_FEEDBACK_SCENARIOS})
)
MANUAL_FEEDBACK_SCENARIO_KEYS: Final[tuple[str, ...]] = tuple(
    scenario.key for scenario in MANUAL_FEEDBACK_SCENARIOS
)


__all__ = [
    "DEFAULT_MANUAL_FEEDBACK_SCENARIO",
    "MANUAL_FEEDBACK_SCENARIOS",
    "MANUAL_FEEDBACK_SCENARIOS_BY_KEY",
    "MANUAL_FEEDBACK_SCENARIO_KEYS",
    "MANUAL_FEEDBACK_STEPS",
    "MANUAL_FEEDBACK_STEPS_BY_KEY",
    "ManualFeedbackCategory",
    "ManualFeedbackPriority",
    "ManualFeedbackScenario",
    "ManualFeedbackStep",
]
