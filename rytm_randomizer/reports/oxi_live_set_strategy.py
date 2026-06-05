"""Passive OXI-style live set strategy report."""

from __future__ import annotations

import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, register
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer OXI live set strategy report"
SOURCE_MODULE: Final[str] = "reports.oxi_live_set_strategy"
USAGE: Final[str] = "oxi-live-set-strategy-report usage: [--json]"
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
class OxiLiveSetStrategyReport:
    """Passive report tying OXI, Rytm macros, A4 runway, and pad policy together."""

    title: str
    rig_roles: tuple[OxiRigRole, ...]
    chapters: tuple[OxiLiveSetChapter, ...]
    pad_policies: tuple[OxiPadPolicy, ...]
    hardware_validation_runway: tuple[OxiHardwareValidationStep, ...]
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


def build_oxi_live_set_strategy_report() -> OxiLiveSetStrategyReport:
    """Return the deterministic passive OXI live set strategy report."""

    return OxiLiveSetStrategyReport(
        title=REPORT_TITLE,
        rig_roles=_RIG_ROLES,
        chapters=_CHAPTERS,
        pad_policies=_PAD_POLICIES,
        hardware_validation_runway=_HARDWARE_VALIDATION_RUNWAY,
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
        "next_hardware_validations": list(report.next_hardware_validations),
        "safety": dict(report.safety),
    }


def _parse_oxi_live_set_strategy_args(argv: Sequence[str]) -> dict[str, object]:
    if not argv:
        return {"json_output": False}
    if list(argv) == ["--json"]:
        return {"json_output": True}
    raise ValueError(USAGE)


def _handle_oxi_live_set_strategy_report(*, json_output: bool) -> int:
    if json_output:
        sys.stdout.write(
            json.dumps(
                build_oxi_live_set_strategy_payload(),
                indent=2,
                sort_keys=True,
            )
        )
        sys.stdout.write("\n")
        return 0
    report = build_oxi_live_set_strategy_report()
    sys.stdout.write("\n".join(format_oxi_live_set_strategy_report(report)))
    sys.stdout.write("\n")
    return 0


def _format_oxi_live_set_strategy_error(exc: Exception) -> str:
    return f"Error: {exc}"


OXI_LIVE_SET_STRATEGY_CLI_COMMAND: Final[CliCommand] = CliCommand(
    name="oxi-live-set-strategy-report",
    summary="Print passive OXI live set strategy chapters and pad policy.",
    args_parser=_parse_oxi_live_set_strategy_args,
    handler=_handle_oxi_live_set_strategy_report,
    error_formatter=_format_oxi_live_set_strategy_error,
)

register(OXI_LIVE_SET_STRATEGY_CLI_COMMAND)

__all__ = (
    "OXI_LIVE_SET_STRATEGY_CLI_COMMAND",
    "OxiHardwareValidationStep",
    "OxiLiveSetChapter",
    "OxiLiveSetStrategyReport",
    "OxiPadPolicy",
    "OxiRigRole",
    "REPORT_TITLE",
    "SAFETY_LINES",
    "SOURCE_MODULE",
    "USAGE",
    "build_oxi_live_set_strategy_payload",
    "build_oxi_live_set_strategy_report",
    "format_oxi_live_set_strategy_report",
)
