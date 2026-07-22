"""Generate desktop/web/src/types/live_gui_protocol.ts from the Python TypedDicts.

The shared live-GUI TypeScript protocol used to be hand-maintained as a third
copy of every contract (frozen dataclass -> sibling TypedDict -> TS interface).
This script derives the TypeScript interfaces from the Python TypedDict
contracts in ``rytm_randomizer/reports/live_gui_*_model.py`` and
``rytm_randomizer/reports/performance_console/*.py`` so the TS file is a
generated artifact instead of a hand-synced mirror.

Interfaces whose Python side is still an untyped ``dict[str, object]`` payload
builder (the performance-console panel payloads) have no TypedDict to derive
from yet; their shapes are pinned in the ``_InterfaceSpec`` tables below.
Promoting those builders to TypedDicts lets the corresponding spec rows move
into the derived path.

Usage (from the repo root)::

    python scripts/generate_live_gui_protocol_ts.py            # rewrite the TS file
    python scripts/generate_live_gui_protocol_ts.py --check    # verify, write nothing
    python scripts/generate_live_gui_protocol_ts.py --fixture  # also write the JSON fixture

``tests/architecture/test_live_gui_protocol_is_generated.py`` runs the
renderers in-process and fails when the committed artifacts drift.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Final

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
REPORTS_DIR: Final[Path] = PROJECT_ROOT / "rytm_randomizer" / "reports"
PROTOCOL_TS_PATH: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "src" / "types" / "live_gui_protocol.ts"
)
FIXTURE_JSON_PATH: Final[Path] = (
    PROJECT_ROOT / "desktop" / "web" / "tests" / "cockpit" / "fixtures" / "performance_console.json"
)

_EMPTY_STR_MAP: Final[Mapping[str, str]] = MappingProxyType({})

_HEADER: Final[str] = (
    "/**\n"
    " * Shared live-GUI protocol types.\n"
    " *\n"
    " * GENERATED — edit the Python TypedDicts and re-run\n"
    " * scripts/generate_live_gui_protocol_ts.py.\n"
    " *\n"
    " * Source of truth: the sibling TypedDict contracts in\n"
    " * `rytm_randomizer/reports/live_gui_*_model.py`.\n"
    " * `tests/architecture/test_live_gui_protocol_ts_matches_python_typeddicts.py`\n"
    " * keeps these TypeScript field names aligned with the Python contracts.\n"
    " */\n"
    "\n"
    "import type { StyleCrateRehearsalDeckDict } from './style_crate_rehearsal_deck';"
)

_FOOTER: Final[str] = (
    "export interface LiveReadinessModel {\n"
    "  pad_surface: LiveGuiRytmTwelvePadSurfaceModelDict;\n"
    "  device_inventory: LiveGuiDeviceInventoryModelDict;\n"
    "  scene_queue: LiveGuiSceneQueueModelDict;\n"
    "  status_footer: LiveGuiStatusFooterModelDict;\n"
    "  snapshot_history: LiveGuiSnapshotHistoryModelDict;\n"
    "  safety_checklist: LiveGuiSafetyChecklistModelDict;\n"
    "  command_queue: LiveGuiCommandQueueModelDict;\n"
    "  analyzer_panel: LiveGuiAnalyzerPanelModelDict;\n"
    "  hardware_rail: LiveGuiHardwareRailModelDict;\n"
    "  snapshot_compatibility: LiveGuiSnapshotCompatibilityModelDict;\n"
    "}\n"
    "\n"
    "export interface LiveReadinessPanelProps {\n"
    "  model?: LiveReadinessModel;\n"
    "}\n"
    "\n"
    "export type LivePerformanceFlowStepModel = LiveGuiPerformanceFlowStepDict;\n"
    "\n"
    "export type LivePerformanceFlowModel = LiveGuiPerformanceFlowModelDict;\n"
    "\n"
    "export interface LiveReadinessPanelViewProps extends LiveReadinessPanelProps {\n"
    "  performanceFlow?: LivePerformanceFlowModel;\n"
    "}"
)

_PRIMITIVE_TS_TYPES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "str": "string",
        "int": "number",
        "float": "number",
        "bool": "boolean",
    }
)


@dataclass(frozen=True)
class _InterfaceSpec:
    """One TypeScript interface pinned directly in this generator."""

    name: str
    fields: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class _ModulePart:
    """Interfaces derived from the TypedDicts of one Python module."""

    relative_path: str
    renames: Mapping[str, str] = field(default_factory=lambda: _EMPTY_STR_MAP)
    emit_order: tuple[str, ...] = ()
    field_overrides: Mapping[tuple[str, str], str] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(frozen=True)
class _LiteralPart:
    """Interfaces with no Python TypedDict source yet, pinned as specs."""

    specs: tuple[_InterfaceSpec, ...]


@dataclass(frozen=True)
class _RawPart:
    """A verbatim TypeScript block (hand-shaped view-layer helpers)."""

    text: str


_CONSOLE_PANEL_INTERFACES: Final[tuple[_InterfaceSpec, ...]] = (
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleMacroActionCardDict",
        fields=(
            ("macro_key", "string"),
            ("order", "number"),
            ("label", "string"),
            ("shell_command", "string"),
            ("send_policy", "string"),
            ("recovery_action", "string"),
            ("risk_label", "string"),
            ("affected_pads", "ReadonlyArray<number>"),
            ("pad_count", "number"),
            ("status", "string"),
            ("hardware_action_state", "string"),
            ("hardware_send_enabled", "boolean"),
            ("dry_run_only", "boolean"),
            ("operator_hint", "string"),
            ("test_id", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleMacroActionDeckDict",
        fields=(
            ("deck_version", "string"),
            ("deck_id", "string"),
            ("deck_status", "string"),
            ("current_macro_key", "string"),
            ("cards", "ReadonlyArray<LiveGuiPerformanceConsoleMacroActionCardDict>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRytmLanePolicyPadGroupDict",
        fields=(
            ("group_key", "string"),
            ("pads", "ReadonlyArray<number>"),
            ("summary", "string"),
            ("lane_policy", "string"),
            ("operator_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRytmPadPolicyCardDict",
        fields=(
            ("amount", "string | null"),
            ("density", "string | null"),
            ("bias", "string | null"),
            ("lane_policies", "Readonly<Record<string, string>>"),
            ("section_family_allowlists", "Readonly<Record<string, ReadonlyArray<string>>>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRytmMacroPolicyRowDict",
        fields=(
            ("macro_key", "string"),
            ("order", "number"),
            ("label", "string"),
            ("style_crate", "string"),
            ("risk_label", "string"),
            ("energy", "number"),
            ("risk", "number"),
            ("affected_pads", "ReadonlyArray<number>"),
            ("locked_pads", "ReadonlyArray<number>"),
            ("lane_policy_summary", "string"),
            (
                "pad_policy_cards",
                "Readonly<Record<string, LiveGuiPerformanceConsoleRytmPadPolicyCardDict>>",
            ),
            ("recovery_action", "string"),
            ("summary", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRytmLanePolicyMatrixDict",
        fields=(
            ("matrix_version", "string"),
            ("matrix_id", "string"),
            ("matrix_status", "string"),
            ("source_report", "string"),
            ("macro_count", "number"),
            ("pad_groups", "ReadonlyArray<LiveGuiPerformanceConsoleRytmLanePolicyPadGroupDict>"),
            ("macro_rows", "ReadonlyArray<LiveGuiPerformanceConsoleRytmMacroPolicyRowDict>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRehearsalChapterDict",
        fields=(
            ("order", "number"),
            ("name", "string"),
            ("label", "string"),
            ("rytm_command", "string"),
            ("macro_sequence", "ReadonlyArray<string>"),
            ("a4_review_action", "string"),
            ("operator_intent", "string"),
            ("recovery_action", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRehearsalCueDict",
        fields=(
            ("chapter_name", "string"),
            ("label", "string"),
            ("oxi_action", "string"),
            ("rytm_stage_command", "string"),
            ("inspect_command", "string"),
            ("fire_command", "string"),
            ("recovery_command", "string"),
            ("a4_action", "string"),
            ("expected_result", "string"),
            ("blocked_action", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsolePadLaneCheckDict",
        fields=(
            ("pads", "ReadonlyArray<number>"),
            ("summary", "string"),
            ("expected_motion", "string"),
            ("warning", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleMacroCheckpointDict",
        fields=(
            ("name", "string"),
            ("label", "string"),
            ("risk_label", "string"),
            ("recovery_action", "string"),
            ("affected_pads", "ReadonlyArray<number>"),
            ("summary", "string"),
            ("checkpoints", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleHardwareValidationStepDict",
        fields=(
            ("name", "string"),
            ("device", "string"),
            ("operator_path", "string"),
            ("validation_mode", "string"),
            ("expected_evidence", "string"),
            ("safety_boundary", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsolePromotionCriterionDict",
        fields=(
            ("name", "string"),
            ("device", "string"),
            ("current_status", "string"),
            ("required_evidence", "string"),
            ("promotes_to", "string"),
            ("safety_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleReplayCommandDict",
        fields=(
            ("name", "string"),
            ("execution_mode", "string"),
            ("command", "string"),
            ("purpose", "string"),
            ("expected_observation", "string"),
            ("opens_ports", "boolean"),
            ("sends_midi", "string"),
            ("safety_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRehearsalBoardDict",
        fields=(
            ("board_version", "string"),
            ("board_id", "string"),
            ("board_status", "string"),
            ("title", "string"),
            ("launch_command", "string"),
            ("studio_workflow", "ReadonlyArray<string>"),
            ("chapters", "ReadonlyArray<LiveGuiPerformanceConsoleRehearsalChapterDict>"),
            ("operator_cues", "ReadonlyArray<LiveGuiPerformanceConsoleRehearsalCueDict>"),
            ("pad_lane_checks", "ReadonlyArray<LiveGuiPerformanceConsolePadLaneCheckDict>"),
            ("macro_checkpoints", "ReadonlyArray<LiveGuiPerformanceConsoleMacroCheckpointDict>"),
            (
                "hardware_validation_runway",
                "ReadonlyArray<LiveGuiPerformanceConsoleHardwareValidationStepDict>",
            ),
            (
                "promotion_criteria",
                "ReadonlyArray<LiveGuiPerformanceConsolePromotionCriterionDict>",
            ),
            ("recovery_checks", "ReadonlyArray<string>"),
            ("next_hardware_validations", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<LiveGuiPerformanceConsoleReplayCommandDict>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleControllerTemplateRowDict",
        fields=(
            ("assignment_key", "string"),
            ("page_key", "string"),
            ("page_label", "string"),
            ("page_index", "number"),
            ("slot", "number"),
            ("label", "string"),
            ("target_device", "string"),
            ("target_scope", "string"),
            ("intent_key", "string"),
            ("action", "string"),
            ("lane", "string"),
            ("safety_tier", "string"),
            ("recovery_action", "string"),
            ("operator_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleControllerTemplatePageCardDict",
        fields=(
            ("page_key", "string"),
            ("page_label", "string"),
            ("page_index", "number"),
            ("row_count", "number"),
            ("first_slot", "number"),
            ("last_slot", "number"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleControllerGestureOutcomeDict",
        fields=(
            ("step", "number"),
            ("assignment_key", "string"),
            ("page_key", "string"),
            ("slot", "number"),
            ("gesture", "string"),
            ("value_delta", "number"),
            ("resolved_intent_key", "string"),
            ("resolved_action", "string"),
            ("resolved_target_device", "string"),
            ("resolved_target_scope", "string"),
            ("lane", "string"),
            ("safety_tier", "string"),
            ("recovery_action", "string"),
            ("status", "string"),
            ("operator_goal", "string"),
            ("notes", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleControllerBrainPanelDict",
        fields=(
            ("panel_version", "string"),
            ("panel_id", "string"),
            ("panel_status", "string"),
            ("source_report", "string"),
            ("title", "string"),
            ("profile_key", "string"),
            ("profile_label", "string"),
            ("controller_family", "string"),
            ("controller_layout", "string"),
            ("scenario_key", "string"),
            ("scenario_label", "string"),
            ("scenario_summary", "string"),
            ("template_row_count", "number"),
            ("template_rows", "ReadonlyArray<LiveGuiPerformanceConsoleControllerTemplateRowDict>"),
            ("template_page_count", "number"),
            (
                "template_page_cards",
                "ReadonlyArray<LiveGuiPerformanceConsoleControllerTemplatePageCardDict>",
            ),
            ("gesture_count", "number"),
            (
                "gesture_outcomes",
                "ReadonlyArray<LiveGuiPerformanceConsoleControllerGestureOutcomeDict>",
            ),
            ("operator_notes", "ReadonlyArray<string>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureWorkflowStepDict",
        fields=(
            ("step_key", "string"),
            ("label", "string"),
            ("operator_command", "string"),
            ("description", "string"),
            ("cockpit_state", "string"),
            ("safety_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureDifferentiatorDict",
        fields=(
            ("name", "string"),
            ("label", "string"),
            ("summary", "string"),
            ("controller_limit", "string"),
            ("why_it_matters", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCapturePanelDict",
        fields=(
            ("panel_version", "string"),
            ("panel_id", "string"),
            ("panel_status", "string"),
            ("title", "string"),
            ("tagline", "string"),
            ("source_report", "string"),
            ("launch_command", "string"),
            (
                "workflow_steps",
                "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureWorkflowStepDict>",
            ),
            (
                "differentiators",
                "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureDifferentiatorDict>",
            ),
            ("recovery_commands", "ReadonlyArray<string>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchSlotDict",
        fields=(
            ("slot_key", "string"),
            ("label", "string"),
            ("slot_status", "string"),
            ("operator_command", "string"),
            ("stores", "string"),
            ("source", "string"),
            ("safety_note", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureAnchorCheckDict",
        fields=(
            ("check_key", "string"),
            ("label", "string"),
            ("status", "string"),
            ("evidence", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureAnchorVerificationDict",
        fields=(
            ("anchor_key", "string"),
            ("expected_kit_label", "string"),
            ("fingerprint_source", "string"),
            ("checks", "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureAnchorCheckDict>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureReadinessGateDict",
        fields=(
            ("gate_key", "string"),
            ("label", "string"),
            ("status", "string"),
            ("operator_action", "string"),
            ("cockpit_action_allowed", "boolean"),
            ("blocked_action", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureMutationReadinessDict",
        fields=(
            ("readiness_status", "string"),
            ("ready_gate_count", "number"),
            ("blocked_gate_count", "number"),
            ("gates", "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureReadinessGateDict>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureRecoveryGateDict",
        fields=(
            ("gate_key", "string"),
            ("label", "string"),
            ("operator_sequence", "string"),
            ("expected_result", "string"),
            ("required_before_fire", "boolean"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCapturePackageManifestDict",
        fields=(
            ("manifest_version", "string"),
            ("manifest_id", "string"),
            ("source_panel_id", "string"),
            ("exports_files", "boolean"),
            ("includes", "ReadonlyArray<string>"),
            ("disabled_controls", "ReadonlyArray<string>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchDict",
        fields=(
            ("workbench_version", "string"),
            ("workbench_id", "string"),
            ("workbench_status", "string"),
            ("title", "string"),
            ("summary", "string"),
            ("source_panel_id", "string"),
            ("launch_command", "string"),
            (
                "capture_slots",
                "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchSlotDict>",
            ),
            (
                "anchor_verification",
                "LiveGuiPerformanceConsoleLiveKitCaptureAnchorVerificationDict",
            ),
            ("mutation_readiness", "LiveGuiPerformanceConsoleLiveKitCaptureMutationReadinessDict"),
            (
                "recovery_gates",
                "ReadonlyArray<LiveGuiPerformanceConsoleLiveKitCaptureRecoveryGateDict>",
            ),
            ("package_manifest", "LiveGuiPerformanceConsoleLiveKitCapturePackageManifestDict"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
            ("replay_commands", "ReadonlyArray<string>"),
        ),
    ),
)

_CONSOLE_REVIEW_INTERFACES: Final[tuple[_InterfaceSpec, ...]] = (
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleAnalogFourReviewStepDict",
        fields=(
            ("order", "number"),
            ("macro_name", "string"),
            ("macro_label", "string"),
            ("summary", "string"),
            ("seed", "number"),
            ("intensity", "number"),
            ("energy", "number"),
            ("readiness", "string"),
            ("event_count", "number"),
            ("ready_count", "number"),
            ("review_count", "number"),
            ("blocked_count", "number"),
            ("validation_command", "string"),
            ("recovery_action", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleAnalogFourReviewFocusDict",
        fields=(
            ("macro_name", "string"),
            ("macro_label", "string"),
            ("seed", "number"),
            ("intensity", "number"),
            ("energy", "number"),
            ("readiness", "string"),
            ("event_count", "number"),
            ("ready_count", "number"),
            ("review_count", "number"),
            ("blocked_count", "number"),
            ("shown_count", "number"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleAnalogFourReadinessEventDict",
        fields=(
            ("track", "number"),
            ("role", "string"),
            ("lane", "string"),
            ("parameter", "string"),
            ("channel", "number"),
            ("control", "number"),
            ("value", "number"),
            ("status", "string"),
            ("validation_command", "string"),
            ("reason", "string"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleAnalogFourReviewSurfaceDict",
        fields=(
            ("surface_version", "string"),
            ("surface_id", "string"),
            ("surface_status", "string"),
            ("title", "string"),
            ("set_name", "string"),
            ("step_count", "number"),
            ("current_step", "LiveGuiPerformanceConsoleAnalogFourReviewStepDict"),
            ("up_next", "ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReviewStepDict>"),
            ("steps", "ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReviewStepDict>"),
            ("review_focus", "LiveGuiPerformanceConsoleAnalogFourReviewFocusDict"),
            (
                "readiness_events",
                "ReadonlyArray<LiveGuiPerformanceConsoleAnalogFourReadinessEventDict>",
            ),
            ("preflight_command", "string"),
            ("validation_steps", "ReadonlyArray<string>"),
            ("recovery_notes", "ReadonlyArray<string>"),
            ("promotion_gates", "ReadonlyArray<string>"),
            ("replay_command", "string"),
            ("readiness_replay_command", "string"),
            ("opens_ports", "boolean"),
            ("sends_midi", "boolean"),
            ("hardware_required", "boolean"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety_lines", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleDeviceInventoryModelDict",
        fields=(
            ("model_version", "string"),
            ("device_count", "number"),
            ("cards", "ReadonlyArray<LiveGuiDeviceInventoryCardDict>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety", "ReadonlyArray<string>"),
        ),
    ),
    _InterfaceSpec(
        name="LiveGuiPerformanceConsoleRytmTwelvePadSurfaceModelDict",
        fields=(
            ("model_version", "string"),
            ("pad_count", "number"),
            ("active_pad_count", "number"),
            ("planned_pad_count", "number"),
            ("cards", "ReadonlyArray<LiveGuiRytmPadSurfaceCardDict>"),
            ("blocked_actions", "ReadonlyArray<string>"),
            ("safety", "ReadonlyArray<string>"),
        ),
    ),
)

_MODEL_MODULE_FILENAMES: Final[tuple[str, ...]] = (
    "live_gui_12_pad_surface_model.py",
    "live_gui_device_inventory_model.py",
    "live_gui_scene_queue_model.py",
    "live_gui_status_footer_model.py",
    "live_gui_snapshot_history_model.py",
    "live_gui_safety_checklist_model.py",
    "live_gui_command_queue_model.py",
    "live_gui_analyzer_panel_model.py",
    "live_gui_hardware_rail_model.py",
    "live_gui_snapshot_compatibility_model.py",
    "live_gui_dual_device_rig_readiness_model.py",
    "live_gui_performance_flow_model.py",
)

_AUDITION_RENAMES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "LiveKitPackageAuditionSlot": ("LiveGuiPerformanceConsoleLiveKitPackageAuditionSlotDict"),
        "LiveKitPackageAuditionQueueRow": (
            "LiveGuiPerformanceConsoleLiveKitPackageAuditionQueueDict"
        ),
        "LiveKitPackageAuditionCheck": ("LiveGuiPerformanceConsoleLiveKitPackageAuditionCheckDict"),
        "LiveKitPackageAuditionJournalPreview": (
            "LiveGuiPerformanceConsoleLiveKitPackageAuditionJournalPreviewDict"
        ),
        "LiveKitPackageAuditionSummary": (
            "LiveGuiPerformanceConsoleLiveKitPackageAuditionSummaryDict"
        ),
        "LiveKitPackageAuditionPayload": ("LiveGuiPerformanceConsoleLiveKitPackageAuditionDict"),
    }
)

_OPERATOR_PACKAGE_RENAMES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "LiveKitOperatorPackageManifest": (
            "LiveGuiPerformanceConsoleLiveKitOperatorPackageManifestDict"
        ),
        "LiveKitOperatorPackageStep": ("LiveGuiPerformanceConsoleLiveKitOperatorPackageStepDict"),
        "LiveKitOperatorPackageSlotBinding": (
            "LiveGuiPerformanceConsoleLiveKitOperatorPackageSlotBindingDict"
        ),
        "LiveKitOperatorPackageRecoveryRequirement": (
            "LiveGuiPerformanceConsoleLiveKitOperatorPackageRecoveryRequirementDict"
        ),
        "LiveKitOperatorPackageJournalCommitPreview": (
            "LiveGuiPerformanceConsoleLiveKitOperatorPackageJournalCommitPreviewDict"
        ),
        "LiveKitOperatorPackageLocalExportPreview": (
            "LiveGuiPerformanceConsoleLiveKitOperatorPackageLocalExportPreviewDict"
        ),
        "LiveKitOperatorPackagePayload": ("LiveGuiPerformanceConsoleLiveKitOperatorPackageDict"),
    }
)

_REVIEW_LEDGER_RENAMES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "LiveKitOperatorReviewLedgerStage": (
            "LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStageDict"
        ),
        "LiveKitOperatorReviewLedgerStep": (
            "LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerStepDict"
        ),
        "LiveKitOperatorReviewLedgerReadinessSummary": (
            "LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerReadinessSummaryDict"
        ),
        "LiveKitOperatorReviewLedgerPayload": (
            "LiveGuiPerformanceConsoleLiveKitOperatorReviewLedgerDict"
        ),
    }
)

_CONSOLE_MODEL_FIELD_OVERRIDES: Final[Mapping[tuple[str, str], str]] = MappingProxyType(
    {
        ("LiveGuiPerformanceConsoleModelDict", "device_inventory"): (
            "LiveGuiPerformanceConsoleDeviceInventoryModelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "rytm_pad_surface"): (
            "LiveGuiPerformanceConsoleRytmTwelvePadSurfaceModelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "rytm_lane_policy_matrix"): (
            "LiveGuiPerformanceConsoleRytmLanePolicyMatrixDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "performance_flow"): (
            "LiveGuiPerformanceFlowModelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "macro_action_deck"): (
            "LiveGuiPerformanceConsoleMacroActionDeckDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "rehearsal_board"): (
            "LiveGuiPerformanceConsoleRehearsalBoardDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "controller_brain_panel"): (
            "LiveGuiPerformanceConsoleControllerBrainPanelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "live_kit_capture_panel"): (
            "LiveGuiPerformanceConsoleLiveKitCapturePanelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "live_kit_capture_workbench"): (
            "LiveGuiPerformanceConsoleLiveKitCaptureWorkbenchDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "analog_four_review_surface"): (
            "LiveGuiPerformanceConsoleAnalogFourReviewSurfaceDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "style_queue"): "StyleCrateRehearsalDeckDict",
        ("LiveGuiPerformanceConsoleModelDict", "analyzer_panel"): "LiveGuiAnalyzerPanelModelDict",
        ("LiveGuiPerformanceConsoleModelDict", "snapshot_history"): (
            "LiveGuiSnapshotHistoryModelDict"
        ),
        ("LiveGuiPerformanceConsoleModelDict", "command_queue"): "LiveGuiCommandQueueModelDict",
        ("LiveGuiPerformanceConsoleModelDict", "safety_checklist"): (
            "LiveGuiSafetyChecklistModelDict"
        ),
    }
)

_PARTS: Final[tuple[_ModulePart | _LiteralPart | _RawPart, ...]] = (
    *(_ModulePart(relative_path=filename) for filename in _MODEL_MODULE_FILENAMES),
    _LiteralPart(specs=_CONSOLE_PANEL_INTERFACES),
    _ModulePart(
        relative_path="performance_console/live_kit_package_audition.py",
        renames=_AUDITION_RENAMES,
        emit_order=(
            "LiveKitPackageAuditionSlot",
            "LiveKitPackageAuditionQueueRow",
            "LiveKitPackageAuditionCheck",
            "LiveKitPackageAuditionJournalPreview",
            "LiveKitPackageAuditionSummary",
            "LiveKitPackageAuditionPayload",
        ),
    ),
    _ModulePart(
        relative_path="performance_console/live_kit_operator_package.py",
        renames=_OPERATOR_PACKAGE_RENAMES,
    ),
    _ModulePart(
        relative_path="performance_console/live_kit_operator_review_ledger.py",
        renames=_REVIEW_LEDGER_RENAMES,
    ),
    _LiteralPart(specs=_CONSOLE_REVIEW_INTERFACES),
    _ModulePart(
        relative_path="live_gui_performance_console_model.py",
        field_overrides=_CONSOLE_MODEL_FIELD_OVERRIDES,
    ),
    _RawPart(text=_FOOTER),
)


def _base_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def _is_typed_dict(node: ast.ClassDef) -> bool:
    return any(_base_name(base) == "TypedDict" for base in node.bases)


def _is_string_literal_alias(node: ast.stmt) -> bool:
    if not isinstance(node, (ast.AnnAssign, ast.Assign)):
        return False
    value = node.value
    return isinstance(value, ast.Subscript) and _base_name(value.value) == "Literal"


def _alias_target_names(node: ast.stmt) -> tuple[str, ...]:
    if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
        return (node.target.id,)
    if isinstance(node, ast.Assign):
        return tuple(target.id for target in node.targets if isinstance(target, ast.Name))
    return ()


@dataclass(frozen=True)
class _ParsedModule:
    """TypedDict classes and string-literal aliases of one source module."""

    relative_path: str
    typed_dicts: tuple[ast.ClassDef, ...]
    literal_aliases: frozenset[str]


def _parse_module(relative_path: str) -> _ParsedModule:
    source_path = REPORTS_DIR / relative_path
    tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
    typed_dicts = tuple(
        node for node in tree.body if isinstance(node, ast.ClassDef) and _is_typed_dict(node)
    )
    aliases = frozenset(
        name
        for statement in tree.body
        if _is_string_literal_alias(statement)
        for name in _alias_target_names(statement)
    )
    return _ParsedModule(
        relative_path=relative_path,
        typed_dicts=typed_dicts,
        literal_aliases=aliases,
    )


def _global_names(parsed: Mapping[str, _ParsedModule]) -> tuple[Mapping[str, str], frozenset[str]]:
    """Map every known Python contract name to its TypeScript interface name."""

    names: dict[str, str] = {}
    aliases: set[str] = set()
    for part in _PARTS:
        if not isinstance(part, _ModulePart):
            continue
        module = parsed[part.relative_path]
        aliases.update(module.literal_aliases)
        for node in module.typed_dicts:
            names[node.name] = part.renames.get(node.name, node.name)
    return MappingProxyType(names), frozenset(aliases)


def _render_type(
    node: ast.expr,
    names: Mapping[str, str],
    aliases: frozenset[str],
    context: str,
) -> str:
    if isinstance(node, ast.Name):
        primitive = _PRIMITIVE_TS_TYPES.get(node.id)
        if primitive is not None:
            return primitive
        if node.id in names:
            return names[node.id]
        if node.id in aliases:
            return "string"
        raise ValueError(f"{context}: unmapped type name {node.id!r}")
    if (
        isinstance(node, ast.BinOp)
        and isinstance(node.op, ast.BitOr)
        and isinstance(node.right, ast.Constant)
        and node.right.value is None
    ):
        return f"{_render_type(node.left, names, aliases, context)} | null"
    if isinstance(node, ast.Subscript):
        base = _base_name(node.value)
        if base == "tuple" and isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
            element, ellipsis = node.slice.elts
            if isinstance(ellipsis, ast.Constant) and ellipsis.value is Ellipsis:
                return f"ReadonlyArray<{_render_type(element, names, aliases, context)}>"
        if base == "list":
            return f"ReadonlyArray<{_render_type(node.slice, names, aliases, context)}>"
        if base == "Mapping" and isinstance(node.slice, ast.Tuple) and len(node.slice.elts) == 2:
            key_node, value_node = node.slice.elts
            key = _render_type(key_node, names, aliases, context)
            value = _render_type(value_node, names, aliases, context)
            return f"Readonly<Record<{key}, {value}>>"
    raise ValueError(f"{context}: unsupported annotation {ast.unparse(node)!r}")


def _typed_dict_spec(
    node: ast.ClassDef,
    part: _ModulePart,
    names: Mapping[str, str],
    aliases: frozenset[str],
) -> _InterfaceSpec:
    fields: list[tuple[str, str]] = []
    for statement in node.body:
        if not isinstance(statement, ast.AnnAssign) or not isinstance(statement.target, ast.Name):
            continue
        field_name = statement.target.id
        override = part.field_overrides.get((node.name, field_name))
        if override is not None:
            fields.append((field_name, override))
            continue
        context = f"{part.relative_path}::{node.name}.{field_name}"
        fields.append((field_name, _render_type(statement.annotation, names, aliases, context)))
    return _InterfaceSpec(name=names[node.name], fields=tuple(fields))


def _module_specs(
    part: _ModulePart,
    parsed: Mapping[str, _ParsedModule],
    names: Mapping[str, str],
    aliases: frozenset[str],
) -> tuple[_InterfaceSpec, ...]:
    module = parsed[part.relative_path]
    by_name = {node.name: node for node in module.typed_dicts}
    if part.emit_order:
        if set(part.emit_order) != set(by_name):
            raise ValueError(
                f"{part.relative_path}: emit_order {sorted(part.emit_order)!r} does not match "
                f"the module's TypedDicts {sorted(by_name)!r}; update the generator."
            )
        ordered = tuple(by_name[name] for name in part.emit_order)
    else:
        ordered = module.typed_dicts
    return tuple(_typed_dict_spec(node, part, names, aliases) for node in ordered)


def _render_interface(spec: _InterfaceSpec) -> str:
    lines = [f"export interface {spec.name} {{"]
    lines.extend(f"  {field_name}: {ts_type};" for field_name, ts_type in spec.fields)
    lines.append("}")
    return "\n".join(lines)


def render_live_gui_protocol_ts() -> str:
    """Render the full live_gui_protocol.ts file content."""

    parsed = {
        part.relative_path: _parse_module(part.relative_path)
        for part in _PARTS
        if isinstance(part, _ModulePart)
    }
    names, aliases = _global_names(parsed)
    chunks: list[str] = [_HEADER]
    for part in _PARTS:
        if isinstance(part, _ModulePart):
            chunks.extend(
                _render_interface(spec) for spec in _module_specs(part, parsed, names, aliases)
            )
        elif isinstance(part, _LiteralPart):
            chunks.extend(_render_interface(spec) for spec in part.specs)
        else:
            chunks.append(part.text)
    return "\n\n".join(chunks) + "\n"


def render_performance_console_fixture_json() -> str:
    """Render the deterministic performance-console payload fixture."""

    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    from rytm_randomizer.reports.live_gui_performance_console_model import (
        live_gui_performance_console_model_payload,
    )

    return json.dumps(live_gui_performance_console_model_payload(), indent=2) + "\n"


def _check_file(path: Path, expected: str, label: str) -> bool:
    actual = path.read_text(encoding="utf-8") if path.is_file() else ""
    if actual == expected:
        print(f"OK: {label} is up to date.")
        return True
    diff = difflib.unified_diff(
        actual.splitlines(keepends=True),
        expected.splitlines(keepends=True),
        fromfile=f"committed/{label}",
        tofile=f"generated/{label}",
    )
    sys.stdout.writelines(diff)
    print(f"STALE: {label} does not match the generator output.")
    return False


def main(argv: tuple[str, ...] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the committed artifacts match the generator output; write nothing",
    )
    parser.add_argument(
        "--fixture",
        action="store_true",
        help="also generate desktop/web/tests/cockpit/fixtures/performance_console.json",
    )
    args = parser.parse_args(argv)

    protocol_ts = render_live_gui_protocol_ts()
    if args.check:
        ok = _check_file(PROTOCOL_TS_PATH, protocol_ts, PROTOCOL_TS_PATH.name)
        if args.fixture:
            fixture_ok = _check_file(
                FIXTURE_JSON_PATH, render_performance_console_fixture_json(), FIXTURE_JSON_PATH.name
            )
            ok = ok and fixture_ok
        return 0 if ok else 1

    PROTOCOL_TS_PATH.write_text(protocol_ts, encoding="utf-8")
    print(f"wrote {PROTOCOL_TS_PATH.relative_to(PROJECT_ROOT)}")
    if args.fixture:
        FIXTURE_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)
        FIXTURE_JSON_PATH.write_text(render_performance_console_fixture_json(), encoding="utf-8")
        print(f"wrote {FIXTURE_JSON_PATH.relative_to(PROJECT_ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
