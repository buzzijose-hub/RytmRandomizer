"""Manual validation kit facts for operator-facing passive reports."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final, Literal

ManualValidationMode = Literal["passive", "mock", "armed-manual"]


@dataclass(frozen=True)
class ManualValidationPhase:
    """Ordered validation phase in the manual test itinerary."""

    slug: str
    title: str
    summary: str
    step_ids: tuple[str, ...]


@dataclass(frozen=True)
class ManualValidationStep:
    """One manual validation step rendered by the passive kit report."""

    step_id: str
    phase: str
    title: str
    mode: ManualValidationMode
    requires_installer: bool
    requires_hardware: bool
    operator_actions: tuple[str, ...]
    expected_observations: tuple[str, ...]
    evidence_prompts: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    passive_commands: tuple[str, ...] = ()
    manual_commands: tuple[str, ...] = ()


MANUAL_VALIDATION_PHASES: Final[tuple[ManualValidationPhase, ...]] = (
    ManualValidationPhase(
        slug="installer_bootstrap",
        title="Installer bootstrap",
        summary="Install or launch the desktop build and confirm the cockpit starts in mock-safe mode.",
        step_ids=(
            "install_unsigned_desktop",
            "launch_cockpit_desktop",
            "confirm_mock_safe_connection",
        ),
    ),
    ManualValidationPhase(
        slug="profile_workflow",
        title="Profile workflow",
        summary="Exercise reference-profile creation, analyzer readiness, and export affordances.",
        step_ids=(
            "create_profile_from_reference",
            "record_analyzer_dependency_state",
            "export_profile_model",
        ),
    ),
    ManualValidationPhase(
        slug="mock_rehearsal",
        title="Mock rehearsal",
        summary="Rehearse preview, regen, prepare, history, save, and disabled active controls.",
        step_ids=(
            "review_mock_dashboard_state",
            "rehearse_preview_regen_save",
            "check_prepare_send_controls",
            "check_snapshot_history_recovery",
        ),
    ),
    ManualValidationPhase(
        slug="armed_smoke",
        title="Armed smoke",
        summary="Run one deliberate operator-armed Rytm smoke test after passive checks are complete.",
        step_ids=(
            "verify_hardware_preconditions",
            "run_single_cc_smoke",
            "return_to_clean_after_smoke",
        ),
    ),
    ManualValidationPhase(
        slug="evidence_closeout",
        title="Evidence closeout",
        summary="Collect reviewer-ready evidence, observations, and stop-condition notes.",
        step_ids=(
            "collect_validation_evidence",
            "write_feedback_summary",
        ),
    ),
)


MANUAL_VALIDATION_STEPS: Final[tuple[ManualValidationStep, ...]] = (
    ManualValidationStep(
        step_id="install_unsigned_desktop",
        phase="installer_bootstrap",
        title="Install unsigned desktop build",
        mode="passive",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Download the Windows installer artifact from the green installer workflow.",
            "Run the unsigned installer and accept the Windows warning only for this known build.",
            "Do not connect hardware for this step.",
        ),
        expected_observations=(
            "The installer completes without requiring source checkout commands.",
            "A RytmRandomizer Cockpit shortcut or app entry is available.",
        ),
        evidence_prompts=(
            "Installer filename and workflow run id.",
            "Screenshot of any warning dialog accepted.",
        ),
        stop_conditions=(
            "Installer cannot start.",
            "Windows blocks the installer without an override option.",
        ),
    ),
    ManualValidationStep(
        step_id="launch_cockpit_desktop",
        phase="installer_bootstrap",
        title="Launch cockpit desktop shell",
        mode="passive",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Open RytmRandomizer Cockpit from the installed app entry.",
            "Wait for the sidecar terminal to report application startup complete.",
        ),
        expected_observations=(
            "The cockpit window renders the dashboard instead of staying on Connecting.",
            "The sidecar shows a local WebSocket connection.",
        ),
        evidence_prompts=(
            "Screenshot of the cockpit dashboard.",
            "Copy of the sidecar terminal startup lines.",
        ),
        stop_conditions=(
            "Cockpit remains reconnecting for more than 30 seconds.",
            "The sidecar exits or reports an import error.",
        ),
    ),
    ManualValidationStep(
        step_id="confirm_mock_safe_connection",
        phase="installer_bootstrap",
        title="Confirm mock-safe connection state",
        mode="mock",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Read the top status strip before touching any hardware control.",
            "Confirm the UI reports Mock or Safe state and no selected MIDI port.",
        ),
        expected_observations=(
            "Status indicates mock-safe behavior.",
            "Port status is none, closed, or not opened.",
            "No unsolicited hardware prompt appears.",
        ),
        evidence_prompts=("Screenshot of the status strip.",),
        stop_conditions=(
            "A MIDI port opens before explicit operator action.",
            "The UI reports unsaved sends before any operator send action.",
        ),
    ),
    ManualValidationStep(
        step_id="create_profile_from_reference",
        phase="profile_workflow",
        title="Create profile from reference",
        mode="passive",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Open Create Profile.",
            "Name the profile after the reference vibe, not the copyrighted track.",
            "Add reference text or an owned local audio file.",
        ),
        expected_observations=(
            "The wizard advances through name, add, analyze, and review steps.",
            "Reference material is treated as inspiration only.",
        ),
        evidence_prompts=(
            "Profile name used.",
            "Screenshot of the analyze or review step.",
        ),
        stop_conditions=(
            "The wizard accepts no source input.",
            "The UI claims it will copy or recreate the reference track.",
        ),
    ),
    ManualValidationStep(
        step_id="record_analyzer_dependency_state",
        phase="profile_workflow",
        title="Record analyzer dependency state",
        mode="passive",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Run analysis once from the profile wizard.",
            "If optional audio extraction dependencies are missing, capture the exact message.",
        ),
        expected_observations=(
            "Analysis either completes or shows a clear optional-extra requirement.",
            "The failure state remains contained to the profile wizard.",
        ),
        evidence_prompts=(
            "Analyzer success summary or exact dependency error.",
            "Whether the installed build or source checkout was used.",
        ),
        stop_conditions=(
            "Analyzer failure crashes the cockpit.",
            "Analyzer starts hardware behavior.",
        ),
    ),
    ManualValidationStep(
        step_id="export_profile_model",
        phase="profile_workflow",
        title="Export profile model",
        mode="passive",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Click Export Model after analysis or profile review is available.",
            "If the UI does not respond, capture the click target and surrounding state.",
        ),
        expected_observations=(
            "The UI either exports a profile artifact or reports why export is disabled.",
            "No MIDI or hardware state changes occur.",
        ),
        evidence_prompts=(
            "Exported file path or disabled reason.",
            "Screenshot before and after clicking Export Model.",
        ),
        stop_conditions=(
            "Export silently does nothing.",
            "Export attempts to open hardware.",
        ),
        passive_commands=(
            "python -m rytm_randomizer.cli cockpit-export-rehearsal-report "
            "--profile-id <profile-id> --profiles-dir <profiles-dir> --key-id dev-key",
        ),
    ),
    ManualValidationStep(
        step_id="review_mock_dashboard_state",
        phase="mock_rehearsal",
        title="Review mock dashboard state",
        mode="mock",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Confirm pad cards, mutation panel, reference profile, and status strip render.",
            "Note visible pad count and any locked or planned pads.",
        ),
        expected_observations=(
            "Dashboard is usable in mock mode.",
            "Any missing 12-pad coverage is visible as a product gap, not a safety failure.",
        ),
        evidence_prompts=(
            "Screenshot of the dashboard.",
            "Observed pad count and device labels.",
        ),
        stop_conditions=(
            "Dashboard controls overlap or cannot be read.",
            "SEND appears armed while no port is selected.",
        ),
    ),
    ManualValidationStep(
        step_id="rehearse_preview_regen_save",
        phase="mock_rehearsal",
        title="Rehearse preview, regen, and save",
        mode="mock",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Toggle preview if available.",
            "Move the mutation amount slider and click Regen.",
            "Save the mock result or record why Save is disabled.",
        ),
        expected_observations=(
            "Controls update deterministic mock state without hardware output.",
            "Snapshot history or last-action state changes after mock operations.",
        ),
        evidence_prompts=(
            "Before and after screenshots.",
            "Observed snapshot-history or action-log entry.",
        ),
        stop_conditions=(
            "Preview or Regen opens a port.",
            "Save writes outside an explicitly selected profile/export path.",
        ),
    ),
    ManualValidationStep(
        step_id="check_prepare_send_controls",
        phase="mock_rehearsal",
        title="Check prepare and send controls",
        mode="mock",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Inspect Prepare, Send, Apply, Arm, and port controls.",
            "Try disabled controls only far enough to capture their disabled reason.",
        ),
        expected_observations=(
            "Hardware-affecting controls remain disabled until explicit arming and port selection.",
            "Disabled reasons are visible or inferable from the UI state.",
        ),
        evidence_prompts=(
            "Screenshot of disabled SEND or Arm controls.",
            "Any tooltip, warning, or disabled reason text.",
        ),
        stop_conditions=(
            "A hardware-affecting control fires in mock mode.",
            "A disabled control has no visible blocked reason.",
        ),
    ),
    ManualValidationStep(
        step_id="check_snapshot_history_recovery",
        phase="mock_rehearsal",
        title="Check snapshot history and recovery",
        mode="mock",
        requires_installer=True,
        requires_hardware=False,
        operator_actions=(
            "Create at least two mock changes.",
            "Use undo, snapshot history, or recovery controls if present.",
        ),
        expected_observations=(
            "The UI exposes a way to understand or recover from recent mock changes.",
            "Recovery does not require hardware.",
        ),
        evidence_prompts=(
            "Screenshot of history, undo stack, or recovery state.",
            "List of controls that appeared missing or confusing.",
        ),
        stop_conditions=(
            "Undo or recovery changes hardware.",
            "The UI cannot explain what changed.",
        ),
    ),
    ManualValidationStep(
        step_id="verify_hardware_preconditions",
        phase="armed_smoke",
        title="Verify hardware preconditions",
        mode="armed-manual",
        requires_installer=False,
        requires_hardware=True,
        operator_actions=(
            "Power the Analog Rytm only when ready for a deliberate manual smoke test.",
            "Confirm audio monitoring is safe and volume is conservative.",
            "Confirm no other DAW or MIDI tool is holding the Rytm output port.",
        ),
        expected_observations=(
            "The Rytm is visible as an output port only after the operator enters the armed path.",
            "No unattended loop is running.",
        ),
        evidence_prompts=(
            "Port name shown to the operator.",
            "Current Rytm project or kit context.",
        ),
        stop_conditions=(
            "Port list is ambiguous.",
            "Another app has the port open.",
            "The Rytm is not in a state safe for a single CC smoke test.",
        ),
    ),
    ManualValidationStep(
        step_id="run_single_cc_smoke",
        phase="armed_smoke",
        title="Run one single-CC smoke test",
        mode="armed-manual",
        requires_installer=False,
        requires_hardware=True,
        operator_actions=(
            "Run the printed armed command manually from PowerShell only after confirming the port.",
            "Select the Analog Rytm output port when prompted.",
            "Observe only the target track for the expected single parameter response.",
        ),
        expected_observations=(
            "Only Track 1 responds to CC17 value 64.",
            "No non-target pad changes.",
        ),
        evidence_prompts=(
            "Selected output port number and name.",
            "Whether only the target track changed.",
            "Terminal output from the armed smoke command.",
        ),
        stop_conditions=(
            "Any non-target pad changes.",
            "The command repeats without another explicit operator action.",
            "The selected port is not the Analog Rytm.",
        ),
        passive_commands=("python -m rytm_randomizer.cli rytm-outbound-cc-repeatability-report",),
        manual_commands=(
            "python -m rytm_randomizer.app --arm --validate-one-cc "
            "--channel 0 --control 17 --value 64",
        ),
    ),
    ManualValidationStep(
        step_id="return_to_clean_after_smoke",
        phase="armed_smoke",
        title="Return to clean after smoke",
        mode="armed-manual",
        requires_installer=False,
        requires_hardware=True,
        operator_actions=(
            "Return the tested parameter or kit to its prior state on the hardware.",
            "Close the armed process after the one smoke test.",
        ),
        expected_observations=(
            "No background process continues after the smoke test.",
            "The Rytm returns to the expected local state.",
        ),
        evidence_prompts=(
            "Confirmation that the armed process exited.",
            "Any manual recovery performed on the Rytm.",
        ),
        stop_conditions=(
            "The process remains open unexpectedly.",
            "Hardware state cannot be returned to the expected local state.",
        ),
    ),
    ManualValidationStep(
        step_id="collect_validation_evidence",
        phase="evidence_closeout",
        title="Collect validation evidence",
        mode="passive",
        requires_installer=False,
        requires_hardware=False,
        operator_actions=(
            "Gather screenshots, terminal logs, exported profile files, and hardware observations.",
            "Keep pass/fail notes tied to the phase and step ids in this report.",
        ),
        expected_observations=(
            "Evidence can be reviewed without rerunning hardware.",
            "Failures include enough context for a focused follow-up PR.",
        ),
        evidence_prompts=(
            "Screenshots for each failed or surprising UI state.",
            "Terminal logs for installer, sidecar, CLI, and armed smoke steps.",
            "Exported profile filename or missing-export evidence.",
        ),
        stop_conditions=(
            "Evidence contains private audio paths that should not be posted publicly.",
        ),
        passive_commands=("python -m rytm_randomizer.cli manual-validation-kit-report --json",),
    ),
    ManualValidationStep(
        step_id="write_feedback_summary",
        phase="evidence_closeout",
        title="Write feedback summary",
        mode="passive",
        requires_installer=False,
        requires_hardware=False,
        operator_actions=(
            "Summarize the highest-impact blockers first.",
            "Separate product gaps from safety bugs.",
            "Mention whether testing used installer or source checkout.",
        ),
        expected_observations=(
            "Reviewers can prioritize the next implementation slice.",
            "Safety failures are distinguishable from UX polish requests.",
        ),
        evidence_prompts=(
            "Three-bullet pass/fail summary.",
            "Exact command or UI action that reproduced each failure.",
        ),
        stop_conditions=(
            "A safety failure occurred and needs immediate triage before more testing.",
        ),
    ),
)


__all__ = [
    "MANUAL_VALIDATION_PHASES",
    "MANUAL_VALIDATION_STEPS",
    "ManualValidationMode",
    "ManualValidationPhase",
    "ManualValidationStep",
]
