"""Passive OXI-style live set strategy report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer OXI live set strategy report"
SOURCE_MODULE: Final[str] = "reports.oxi_live_set_strategy"
SAFETY_LINES: Final[tuple[str, ...]] = (
    "passive/read-only",
    "strategy metadata only",
    "no MIDI sending",
    "no port opening",
    "no command execution",
    "no hardware mutation",
    "no hardware required",
    "Analog Four outbound macro send blocked",
)
_SAFETY_PAYLOAD: Final[Mapping[str, object]] = MappingProxyType(
    {
        "passive": True,
        "opens_ports": False,
        "sends_midi": False,
        "mutates_hardware": False,
        "requires_hardware": False,
        "a4_outbound": "blocked",
    }
)
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_NEXT_HARDWARE_VALIDATIONS: Final[tuple[str, ...]] = (
    "Rytm full-kit macro smoke test from a fresh current-kit capture",
    "A4 input-only soft-capture pass before any outbound macro promotion",
)


@dataclass(frozen=True)
class OxiRigRole:
    """One rig component's responsibility in the live-performance model."""

    name: str
    label: str
    responsibility: str
    status: str


@dataclass(frozen=True)
class OxiLiveSetChapter:
    """One passive live-set chapter built from known macro commands."""

    order: int
    name: str
    label: str
    rytm_command: str
    macro_sequence: tuple[str, ...]
    a4_review_action: str
    operator_intent: str
    recovery_action: str


@dataclass(frozen=True)
class OxiPadPolicy:
    """Operator-facing pad-lane policy summary."""

    name: str
    pads: tuple[int, ...]
    primary_lane: str
    filter_policy: str
    lfo_policy: str
    amp_policy: str
    product_note: str


@dataclass(frozen=True)
class OxiHardwareValidationStep:
    """One operator-present validation step for the next live rig pass."""

    name: str
    device: str
    operator_path: str
    validation_mode: str
    expected_evidence: str
    safety_boundary: str


@dataclass(frozen=True)
class OxiPromotionCriterion:
    """Evidence required before a review-only lane can become active."""

    name: str
    device: str
    current_status: str
    required_evidence: str
    promotes_to: str
    safety_note: str


@dataclass(frozen=True)
class OxiOperatorCue:
    """One passive stage/inspect/fire/recover cue for live use."""

    chapter_name: str
    label: str
    oxi_action: str
    rytm_stage_command: str
    inspect_command: str
    fire_command: str
    recovery_command: str
    a4_action: str
    expected_result: str
    blocked_action: str


@dataclass(frozen=True)
class OxiRehearsalCheckpoint:
    """One passive checkpoint for an operator-present rehearsal run."""

    name: str
    phase: str
    required_command: str
    operator_confirmation: str
    success_signal: str
    blocked_action: str


@dataclass(frozen=True)
class OxiReplayCommand:
    """One deterministic command or in-shell step for later rehearsal."""

    name: str
    execution_mode: str
    command: str
    purpose: str
    expected_observation: str
    opens_ports: bool
    sends_midi: str
    safety_note: str


@dataclass(frozen=True)
class OxiLiveSetStrategyReport:
    """Passive report tying OXI, Rytm macros, A4 runway, and pad policy together."""

    title: str
    rig_roles: tuple[OxiRigRole, ...]
    chapters: tuple[OxiLiveSetChapter, ...]
    pad_policies: tuple[OxiPadPolicy, ...]
    hardware_validation_runway: tuple[OxiHardwareValidationStep, ...]
    promotion_criteria: tuple[OxiPromotionCriterion, ...]
    operator_cues: tuple[OxiOperatorCue, ...]
    rehearsal_checkpoints: tuple[OxiRehearsalCheckpoint, ...]
    replay_commands: tuple[OxiReplayCommand, ...]
    next_hardware_validations: tuple[str, ...]
    safety: Mapping[str, object]


_RIG_ROLES: Final[tuple[OxiRigRole, ...]] = (
    OxiRigRole(
        name="oxi-one",
        label="OXI One",
        responsibility="notes, triggers, mutes, pattern motion",
        status="external sequencer",
    ),
    OxiRigRole(
        name="analog-rytm-mkii",
        label="Analog Rytm MKII",
        responsibility="captured-kit sound-design mutation",
        status="live-safe active target",
    ),
    OxiRigRole(
        name="analog-four-mkii",
        label="Analog Four MKII",
        responsibility="tonal companion macro planning",
        status="review-only",
    ),
)

_CHAPTERS: Final[tuple[OxiLiveSetChapter, ...]] = (
    OxiLiveSetChapter(
        order=1,
        name="capture-anchor",
        label="Capture Anchor",
        rytm_command="kit/resnapshot",
        macro_sequence=("kit-core",),
        a4_review_action="hold-current-a4-patch",
        operator_intent="Capture the current Rytm kit before any set movement.",
        recovery_action="captured anchor",
    ),
    OxiLiveSetChapter(
        order=2,
        name="establish-groove",
        label="Establish Groove",
        rytm_command="macro hard-groove",
        macro_sequence=("kit-core", "hard-groove"),
        a4_review_action="review hard-groove A4 macro",
        operator_intent="Let OXI keep the groove while Rytm tightens source-first pressure.",
        recovery_action="home",
    ),
    OxiLiveSetChapter(
        order=3,
        name="pressure-build",
        label="Pressure Build",
        rytm_command="macro industrial",
        macro_sequence=("hard-groove", "industrial"),
        a4_review_action="review industrial-transition A4 macro",
        operator_intent="Raise grit, metal, and energy without releasing the kick anchor.",
        recovery_action="home",
    ),
    OxiLiveSetChapter(
        order=4,
        name="peak-texture",
        label="Peak Texture",
        rytm_command="macro industrial",
        macro_sequence=("industrial", "transition"),
        a4_review_action="review pressure macro only",
        operator_intent="Use stronger Rytm sound design as the peak while OXI carries timing.",
        recovery_action="home",
    ),
    OxiLiveSetChapter(
        order=5,
        name="space-release",
        label="Space Release",
        rytm_command="macro dub-pressure",
        macro_sequence=("dub-pressure",),
        a4_review_action="review dub-pressure A4 macro",
        operator_intent="Pull the kit toward space, delay, reverb, and lower-end pressure.",
        recovery_action="home",
    ),
    OxiLiveSetChapter(
        order=6,
        name="transition-fill",
        label="Transition Fill",
        rytm_command="macro transition",
        macro_sequence=("transition",),
        a4_review_action="review transition-only",
        operator_intent="Create a short bridge or fill before the next OXI pattern decision.",
        recovery_action="home",
    ),
    OxiLiveSetChapter(
        order=7,
        name="home-reset",
        label="Home Reset",
        rytm_command="home",
        macro_sequence=("home",),
        a4_review_action="no A4 send",
        operator_intent="Return to the captured safe kit before the next chapter.",
        recovery_action="Z + send",
    ),
)

_PAD_POLICIES: Final[tuple[OxiPadPolicy, ...]] = (
    OxiPadPolicy(
        name="kick-anchor",
        pads=(1,),
        primary_lane="SRC micro",
        filter_policy="protected",
        lfo_policy="off",
        amp_policy="foundation only",
        product_note="Pad 1 stays protected as the kick anchor",
    ),
    OxiPadPolicy(
        name="tom-source-motion",
        pads=(6, 7, 8),
        primary_lane="SRC",
        filter_policy="light",
        lfo_policy="off",
        amp_policy="overdrive/delay/reverb only",
        product_note="tom/discovery lanes can move usefully without LFO craziness",
    ),
    OxiPadPolicy(
        name="reserved-src-fx",
        pads=(5, 9, 10, 11),
        primary_lane="SRC",
        filter_policy="off",
        lfo_policy="off",
        amp_policy="overdrive/delay/reverb only",
        product_note="common Jose live lane, not a product limitation",
    ),
    OxiPadPolicy(
        name="pad-12-optional",
        pads=(12,),
        primary_lane="SRC/AMP FX",
        filter_policy="macro-dependent",
        lfo_policy="off by default",
        amp_policy="overdrive/delay/reverb only",
        product_note="available for users who rely on Pad 12",
    ),
)

_HARDWARE_VALIDATION_RUNWAY: Final[tuple[OxiHardwareValidationStep, ...]] = (
    OxiHardwareValidationStep(
        name="rytm-kit-core-smoke",
        device="Analog Rytm MKII",
        operator_path="kit-core -> changes -> send -> go -> Z + send",
        validation_mode="operator-present armed Rytm shell",
        expected_evidence="full-kit macro sounds musical and returns to no parameter changes staged",
        safety_boundary="requires --arm and explicit shell send/go commands",
    ),
    OxiHardwareValidationStep(
        name="rytm-dual-vco-center-band",
        device="Analog Rytm MKII",
        operator_path="validate current Pad 2/3 Dual VCO CC20 center-band movement",
        validation_mode="operator-present one-CC or shell smoke test",
        expected_evidence="no visible ERR and detune movement remains useful at the chosen amount",
        safety_boundary="stay in proven center band before widening any low-anchor lane",
    ),
    OxiHardwareValidationStep(
        name="a4-soft-capture",
        device="Analog Four MKII",
        operator_path="--arm --a4-soft-capture",
        validation_mode="input-only",
        expected_evidence="tracks 1-4 emit known Appendix D labels for moved controls",
        safety_boundary="opens A4 input only; no output and no MIDI send",
    ),
    OxiHardwareValidationStep(
        name="a4-macro-dry-run",
        device="Analog Four MKII",
        operator_path="analog-four-oxi-macro-report hard-groove --events --limit 0",
        validation_mode="passive CLI",
        expected_evidence="A4 macro rows match the intended OXI companion role before hardware promotion",
        safety_boundary="report-only; no A4 output path",
    ),
)

_PROMOTION_CRITERIA: Final[tuple[OxiPromotionCriterion, ...]] = (
    OxiPromotionCriterion(
        name="a4-input-label-coverage",
        device="Analog Four MKII",
        current_status="blocked",
        required_evidence="known labels for moved controls on tracks 1-4",
        promotes_to="A4 macro readiness review",
        safety_note="input-only evidence comes before any outbound A4 macro path",
    ),
    OxiPromotionCriterion(
        name="a4-macro-review",
        device="Analog Four MKII",
        current_status="blocked",
        required_evidence="operator-approved passive macro rows for home and one pressure macro",
        promotes_to="single-macro outbound rehearsal",
        safety_note="macro rows stay report-only until the review is explicit",
    ),
    OxiPromotionCriterion(
        name="a4-explicit-arm-gate",
        device="Analog Four MKII",
        current_status="blocked",
        required_evidence="operator-confirmed --arm path with no unattended behavior",
        promotes_to="armed one-shot A4 macro validation",
        safety_note="no A4 outbound macro send until this gate is satisfied",
    ),
    OxiPromotionCriterion(
        name="a4-recovery-path",
        device="Analog Four MKII",
        current_status="blocked",
        required_evidence="documented return-to-anchor or neutral macro after a sent A4 change",
        promotes_to="candidate live companion macro",
        safety_note="no live A4 macro without a tested recovery move",
    ),
)

_OPERATOR_CUES: Final[tuple[OxiOperatorCue, ...]] = (
    OxiOperatorCue(
        chapter_name="capture-anchor",
        label="Capture Anchor",
        oxi_action="hold or prepare the first pattern",
        rytm_stage_command="kit/resnapshot",
        inspect_command="status",
        fire_command="no send",
        recovery_command="captured anchor",
        a4_action="hold-current-a4-patch",
        expected_result="current Rytm kit becomes the safe anchor before the set moves",
        blocked_action="no mutation before anchor capture",
    ),
    OxiOperatorCue(
        chapter_name="establish-groove",
        label="Establish Groove",
        oxi_action="keep groove, triggers, mutes, and pattern motion running",
        rytm_stage_command="macro hard-groove",
        inspect_command="changes",
        fire_command="send or go",
        recovery_command="home + send or Z + send",
        a4_action="review hard-groove A4 macro",
        expected_result="tight source-first Rytm pressure over the OXI pattern",
        blocked_action="no unattended sends",
    ),
    OxiOperatorCue(
        chapter_name="pressure-build",
        label="Pressure Build",
        oxi_action="increase pattern density or mute tension externally",
        rytm_stage_command="macro industrial",
        inspect_command="changes",
        fire_command="send or go",
        recovery_command="home + send or Z + send",
        a4_action="review industrial-transition A4 macro",
        expected_result="metallic grit rises while Pad 1 remains protected",
        blocked_action="no A4 outbound macro",
    ),
    OxiOperatorCue(
        chapter_name="peak-texture",
        label="Peak Texture",
        oxi_action="hold the peak pattern while sound design carries the lift",
        rytm_stage_command="macro industrial",
        inspect_command="changes",
        fire_command="send or go",
        recovery_command="home + send or Z + send",
        a4_action="review pressure macro only",
        expected_result="stronger Rytm pressure without releasing recovery",
        blocked_action="no chaos mode without explicit future opt-in",
    ),
    OxiOperatorCue(
        chapter_name="space-release",
        label="Space Release",
        oxi_action="thin triggers or open mutes for the release",
        rytm_stage_command="macro dub-pressure",
        inspect_command="changes",
        fire_command="send or go",
        recovery_command="home + send or Z + send",
        a4_action="review dub-pressure A4 macro",
        expected_result="delay/reverb pressure without losing the captured-kit anchor",
        blocked_action="no unattended sends",
    ),
    OxiOperatorCue(
        chapter_name="transition-fill",
        label="Transition Fill",
        oxi_action="prepare or launch the next pattern change",
        rytm_stage_command="macro transition",
        inspect_command="changes",
        fire_command="send or go",
        recovery_command="home + send or Z + send",
        a4_action="review transition-only",
        expected_result="short section movement before the next OXI decision",
        blocked_action="no transport or pattern writes",
    ),
    OxiOperatorCue(
        chapter_name="home-reset",
        label="Home Reset",
        oxi_action="settle the groove or prepare the next chapter",
        rytm_stage_command="home",
        inspect_command="changes",
        fire_command="send",
        recovery_command="Z + send",
        a4_action="no A4 send",
        expected_result="captured Rytm anchor restored",
        blocked_action="no persistent kit/project write",
    ),
)

_REHEARSAL_CHECKPOINTS: Final[tuple[OxiRehearsalCheckpoint, ...]] = (
    OxiRehearsalCheckpoint(
        name="capture-current-kit",
        phase="pre-set",
        required_command="kit/resnapshot",
        operator_confirmation="Rytm sent the intended KIT SysEx",
        success_signal="new kit name and fingerprint are visible",
        blocked_action="do not mutate before a captured anchor exists",
    ),
    OxiRehearsalCheckpoint(
        name="stage-first-macro",
        phase="pre-set",
        required_command="kit-core or macro hard-groove",
        operator_confirmation="macro matches the first planned chapter",
        success_signal="changes shows staged sound-design movement",
        blocked_action="do not type send before reviewing changes",
    ),
    OxiRehearsalCheckpoint(
        name="inspect-before-send",
        phase="before-send",
        required_command="changes",
        operator_confirmation="staged rows match the intended chapter",
        success_signal="operator can name the pads and lanes that will move",
        blocked_action="no blind sends",
    ),
    OxiRehearsalCheckpoint(
        name="fire-manually",
        phase="send",
        required_command="send or go",
        operator_confirmation="Jose is listening with the machines on",
        success_signal="variation sounds useful without visible hardware errors",
        blocked_action="no unattended hardware behavior",
    ),
    OxiRehearsalCheckpoint(
        name="recover-anchor",
        phase="recovery",
        required_command="home + send or Z + send",
        operator_confirmation="recovery command sent after the audition",
        success_signal="no parameter changes staged after recovery",
        blocked_action="do not continue if recovery is unclear",
    ),
    OxiRehearsalCheckpoint(
        name="promote-a4-only-after-evidence",
        phase="a4-gate",
        required_command="--arm --a4-soft-capture",
        operator_confirmation="A4 labels and recovery path are documented",
        success_signal="A4 remains review-only until promotion criteria pass",
        blocked_action="no A4 outbound macro during Rytm-only rehearsal",
    ),
    OxiRehearsalCheckpoint(
        name="document-after-set",
        phase="after-set",
        required_command="write down useful macros, bad rows, and recovery notes",
        operator_confirmation="musical notes and hardware symptoms are captured",
        success_signal="notes captured for the next bundle",
        blocked_action="do not promote untested behavior from memory alone",
    ),
)

_REPLAY_COMMANDS: Final[tuple[OxiReplayCommand, ...]] = (
    OxiReplayCommand(
        name="read-strategy",
        execution_mode="passive-cli",
        command="python -m rytm_randomizer.cli oxi-live-set-strategy-report",
        purpose="Read the operator strategy in text form before a rehearsal.",
        expected_observation="report prints OXI roles, chapters, pad policies, and safety notes",
        opens_ports=False,
        sends_midi="never",
        safety_note="metadata-only report",
    ),
    OxiReplayCommand(
        name="read-strategy-json",
        execution_mode="passive-cli",
        command="python -m rytm_randomizer.cli oxi-live-set-strategy-report --json",
        purpose="Expose deterministic JSON for the future GUI/control surface.",
        expected_observation="JSON contains chapters, cues, checkpoints, and replay commands",
        opens_ports=False,
        sends_midi="never",
        safety_note="metadata-only report",
    ),
    OxiReplayCommand(
        name="review-a4-hard-groove",
        execution_mode="passive-cli",
        command=(
            "python -m rytm_randomizer.cli analog-four-oxi-macro-report hard-groove "
            "--seed 23 --intensity 6 --events --limit 0"
        ),
        purpose="Review the A4 companion idea without promoting an outbound path.",
        expected_observation="A4 rows render as dry-run metadata only",
        opens_ports=False,
        sends_midi="never",
        safety_note="A4 remains review-only",
    ),
    OxiReplayCommand(
        name="start-rytm-live-shell",
        execution_mode="armed-operator-shell",
        command=(
            "python -m rytm_randomizer.app --arm --rytm-live-snapshot-shell "
            "--confirm-rytm-snapshot-shell-send"
        ),
        purpose="Capture the current Rytm kit and enter the operator-present shell.",
        expected_observation="loaded kit name and fingerprint are visible",
        opens_ports=True,
        sends_midi="only after explicit in-shell send/go",
        safety_note="requires Jose present with hardware on",
    ),
    OxiReplayCommand(
        name="stage-hard-groove",
        execution_mode="in-shell",
        command="macro hard-groove",
        purpose="Stage the first OXI-style sound-design move.",
        expected_observation="macro is staged but not sent",
        opens_ports=True,
        sends_midi="not by itself",
        safety_note="inspect before send",
    ),
    OxiReplayCommand(
        name="inspect-staged-plan",
        execution_mode="in-shell",
        command="changes",
        purpose="Review pads, lanes, and values before firing.",
        expected_observation="staged rows are printed for operator review",
        opens_ports=True,
        sends_midi="never",
        safety_note="must happen before fire-manually",
    ),
    OxiReplayCommand(
        name="fire-manually",
        execution_mode="in-shell",
        command="send or go",
        purpose="Fire the staged plan only after listening readiness is confirmed.",
        expected_observation="Rytm changes audibly without unattended behavior",
        opens_ports=True,
        sends_midi="operator-confirmed",
        safety_note="Jose must be present and listening",
    ),
    OxiReplayCommand(
        name="recover-anchor",
        execution_mode="in-shell",
        command="home + send or Z + send",
        purpose="Return the hardware to the captured safe kit.",
        expected_observation="changes returns to no parameter changes staged",
        opens_ports=True,
        sends_midi="operator-confirmed",
        safety_note="recovery path must stay available",
    ),
)


def build_oxi_live_set_strategy_report() -> OxiLiveSetStrategyReport:
    """Return the deterministic passive OXI live set strategy report."""

    return OxiLiveSetStrategyReport(
        title=REPORT_TITLE,
        rig_roles=_RIG_ROLES,
        chapters=_CHAPTERS,
        pad_policies=_PAD_POLICIES,
        hardware_validation_runway=_HARDWARE_VALIDATION_RUNWAY,
        promotion_criteria=_PROMOTION_CRITERIA,
        operator_cues=_OPERATOR_CUES,
        rehearsal_checkpoints=_REHEARSAL_CHECKPOINTS,
        replay_commands=_REPLAY_COMMANDS,
        next_hardware_validations=_NEXT_HARDWARE_VALIDATIONS,
        safety=_SAFETY_PAYLOAD,
    )


def _chapter_line(chapter: OxiLiveSetChapter) -> str:
    macros = ", ".join(chapter.macro_sequence)
    return (
        f"- {chapter.order}. {chapter.name} | command={chapter.rytm_command} | "
        f"macros={macros} | recovery={chapter.recovery_action}"
    )


def _pad_policy_line(policy: OxiPadPolicy) -> str:
    pads = ", ".join(str(pad) for pad in policy.pads)
    return (
        f"- {policy.name} | pads={pads} | primary={policy.primary_lane} | "
        f"filter={policy.filter_policy} | lfo={policy.lfo_policy} | "
        f"amp={policy.amp_policy}"
    )


def _validation_step_line(step: OxiHardwareValidationStep) -> str:
    return f"- {step.name} | {step.device} | {step.validation_mode} | " f"path={step.operator_path}"


def _promotion_criterion_line(criterion: OxiPromotionCriterion) -> str:
    return f"- {criterion.name} | {criterion.device} | {criterion.current_status}"


def _operator_cue_line(cue: OxiOperatorCue) -> str:
    return (
        f"- {cue.chapter_name} | OXI={cue.oxi_action} | "
        f"Rytm={cue.rytm_stage_command} | Inspect={cue.inspect_command}"
    )


def _rehearsal_checkpoint_line(checkpoint: OxiRehearsalCheckpoint) -> str:
    return f"- {checkpoint.name} | {checkpoint.phase} | command={checkpoint.required_command}"


def _replay_command_line(command: OxiReplayCommand) -> str:
    return (
        f"- {command.name} | {command.execution_mode} | "
        f"opens_ports={command.opens_ports} | sends_midi={command.sends_midi}"
    )


def format_oxi_live_set_strategy_report(
    report: OxiLiveSetStrategyReport | None = None,
) -> list[str]:
    """Return deterministic operator-facing strategy report lines."""

    resolved = report if report is not None else build_oxi_live_set_strategy_report()
    lines = [
        "OXI live set strategy:",
        "- Rytm acts as second performer for sound design while OXI drives the pattern.",
        "- Analog Four is review-only until an explicit outbound macro path is validated.",
        "Rig roles:",
    ]
    for role in resolved.rig_roles:
        lines.append(f"- {role.label} ({role.name}) | {role.status} | {role.responsibility}")
    lines.append("Live chapters:")
    for chapter in resolved.chapters:
        lines.append(_chapter_line(chapter))
        lines.append(f"  {chapter.operator_intent}")
        lines.append(f"  A4: {chapter.a4_review_action}")
    lines.append("Pad policies:")
    for policy in resolved.pad_policies:
        lines.append(_pad_policy_line(policy))
        lines.append(f"  {policy.product_note}")
    lines.append("Hardware validation runway:")
    for step in resolved.hardware_validation_runway:
        lines.append(_validation_step_line(step))
        lines.append(f"  Evidence: {step.expected_evidence}")
        lines.append(f"  Boundary: {step.safety_boundary}")
    lines.append("Promotion criteria:")
    for criterion in resolved.promotion_criteria:
        lines.append(_promotion_criterion_line(criterion))
        lines.append(f"  Required evidence: {criterion.required_evidence}")
        lines.append(f"  Promotes to: {criterion.promotes_to}")
        lines.append(f"  Safety: {criterion.safety_note}")
    lines.append("Operator cue sheet:")
    for cue in resolved.operator_cues:
        lines.append(_operator_cue_line(cue))
        lines.append(f"  Fire: {cue.fire_command}")
        lines.append(f"  Recover: {cue.recovery_command}")
        lines.append(f"  A4: {cue.a4_action}")
        lines.append(f"  Result: {cue.expected_result}")
        lines.append(f"  Blocked: {cue.blocked_action}")
    lines.append("Rehearsal checkpoints:")
    for checkpoint in resolved.rehearsal_checkpoints:
        lines.append(_rehearsal_checkpoint_line(checkpoint))
        lines.append(f"  Confirm: {checkpoint.operator_confirmation}")
        lines.append(f"  Success: {checkpoint.success_signal}")
        lines.append(f"  Blocked: {checkpoint.blocked_action}")
    lines.append("Replay / rehearsal commands:")
    for command in resolved.replay_commands:
        lines.append(_replay_command_line(command))
        lines.append(f"  Command: {command.command}")
        lines.append(f"  Purpose: {command.purpose}")
        lines.append(f"  Expect: {command.expected_observation}")
        lines.append(f"  Safety: {command.safety_note}")
    lines.append("Next hardware validations:")
    lines.extend(f"- {item}" for item in resolved.next_hardware_validations)
    lines.append("Safety:")
    lines.extend(f"- {line}" for line in SAFETY_LINES)
    return passive_report_lines(_HEADER, lines)


def _rig_role_payload(role: OxiRigRole) -> dict[str, object]:
    return {
        "name": role.name,
        "label": role.label,
        "responsibility": role.responsibility,
        "status": role.status,
    }


def _chapter_payload(chapter: OxiLiveSetChapter) -> dict[str, object]:
    return {
        "order": chapter.order,
        "name": chapter.name,
        "label": chapter.label,
        "rytm_command": chapter.rytm_command,
        "macro_sequence": list(chapter.macro_sequence),
        "a4_review_action": chapter.a4_review_action,
        "operator_intent": chapter.operator_intent,
        "recovery_action": chapter.recovery_action,
    }


def _pad_policy_payload(policy: OxiPadPolicy) -> dict[str, object]:
    return {
        "name": policy.name,
        "pads": list(policy.pads),
        "primary_lane": policy.primary_lane,
        "filter_policy": policy.filter_policy,
        "lfo_policy": policy.lfo_policy,
        "amp_policy": policy.amp_policy,
        "product_note": policy.product_note,
    }


def _validation_step_payload(step: OxiHardwareValidationStep) -> dict[str, object]:
    return {
        "name": step.name,
        "device": step.device,
        "operator_path": step.operator_path,
        "validation_mode": step.validation_mode,
        "expected_evidence": step.expected_evidence,
        "safety_boundary": step.safety_boundary,
    }


def _promotion_criterion_payload(criterion: OxiPromotionCriterion) -> dict[str, object]:
    return {
        "name": criterion.name,
        "device": criterion.device,
        "current_status": criterion.current_status,
        "required_evidence": criterion.required_evidence,
        "promotes_to": criterion.promotes_to,
        "safety_note": criterion.safety_note,
    }


def _operator_cue_payload(cue: OxiOperatorCue) -> dict[str, object]:
    return {
        "chapter_name": cue.chapter_name,
        "label": cue.label,
        "oxi_action": cue.oxi_action,
        "rytm_stage_command": cue.rytm_stage_command,
        "inspect_command": cue.inspect_command,
        "fire_command": cue.fire_command,
        "recovery_command": cue.recovery_command,
        "a4_action": cue.a4_action,
        "expected_result": cue.expected_result,
        "blocked_action": cue.blocked_action,
    }


def _rehearsal_checkpoint_payload(checkpoint: OxiRehearsalCheckpoint) -> dict[str, object]:
    return {
        "name": checkpoint.name,
        "phase": checkpoint.phase,
        "required_command": checkpoint.required_command,
        "operator_confirmation": checkpoint.operator_confirmation,
        "success_signal": checkpoint.success_signal,
        "blocked_action": checkpoint.blocked_action,
    }


def _replay_command_payload(command: OxiReplayCommand) -> dict[str, object]:
    return {
        "name": command.name,
        "execution_mode": command.execution_mode,
        "command": command.command,
        "purpose": command.purpose,
        "expected_observation": command.expected_observation,
        "opens_ports": command.opens_ports,
        "sends_midi": command.sends_midi,
        "safety_note": command.safety_note,
    }


def build_oxi_live_set_strategy_payload() -> dict[str, object]:
    """Return JSON-ready deterministic strategy metadata."""

    report = build_oxi_live_set_strategy_report()
    return {
        "title": report.title,
        "rig_roles": [_rig_role_payload(role) for role in report.rig_roles],
        "chapters": [_chapter_payload(chapter) for chapter in report.chapters],
        "pad_policies": [_pad_policy_payload(policy) for policy in report.pad_policies],
        "hardware_validation_runway": [
            _validation_step_payload(step) for step in report.hardware_validation_runway
        ],
        "promotion_criteria": [
            _promotion_criterion_payload(criterion) for criterion in report.promotion_criteria
        ],
        "operator_cues": [_operator_cue_payload(cue) for cue in report.operator_cues],
        "rehearsal_checkpoints": [
            _rehearsal_checkpoint_payload(checkpoint) for checkpoint in report.rehearsal_checkpoints
        ],
        "replay_commands": [_replay_command_payload(command) for command in report.replay_commands],
        "next_hardware_validations": list(report.next_hardware_validations),
        "safety": dict(report.safety),
    }


OXI_LIVE_SET_STRATEGY_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    name="oxi-live-set-strategy-report",
    summary="Print passive OXI live set strategy chapters and pad policy.",
    format_lines=format_oxi_live_set_strategy_report,
    build_payload=build_oxi_live_set_strategy_payload,
)

register(OXI_LIVE_SET_STRATEGY_CLI_COMMAND)

__all__ = (
    "OXI_LIVE_SET_STRATEGY_CLI_COMMAND",
    "OxiHardwareValidationStep",
    "OxiLiveSetChapter",
    "OxiLiveSetStrategyReport",
    "OxiOperatorCue",
    "OxiPadPolicy",
    "OxiPromotionCriterion",
    "OxiRehearsalCheckpoint",
    "OxiReplayCommand",
    "OxiRigRole",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "build_oxi_live_set_strategy_payload",
    "build_oxi_live_set_strategy_report",
    "format_oxi_live_set_strategy_report",
)
