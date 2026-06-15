"""Passive controller-brain mapping catalog report."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final

from ..cli_registry import CliCommand, make_passive_report_command, register
from ..data.controller_mapping_profiles import (
    CONTROLLER_MAPPING_PROFILES,
    DEFAULT_CONTROLLER_MAPPING_PROFILE,
    ControllerMappingControlSpec,
    ControllerMappingPageSpec,
    ControllerMappingProfileSpec,
)
from .formatter import PassiveReportHeader, passive_report_lines

REPORT_TITLE: Final[str] = "RytmRandomizer passive controller brain mapping report"
SOURCE_MODULE: Final[str] = "reports.controller_mapping_profile_catalog"
_HEADER: Final[PassiveReportHeader] = PassiveReportHeader(
    title=REPORT_TITLE,
    source_module=SOURCE_MODULE,
)
_SAFETY: Final[Mapping[str, object]] = MappingProxyType(
    {
        "passive": True,
        "controller_input": False,
        "opens_ports": False,
        "sends_midi": False,
        "mutates_hardware": False,
        "dispatches_websocket_commands": False,
    }
)


@dataclass(frozen=True)
class ControllerMappingProfileReport:
    """Passive report for one controller mapping profile."""

    title: str
    profile: ControllerMappingProfileSpec
    safety: Mapping[str, object]


def _resolve_controller_profile(profile_key: str) -> ControllerMappingProfileSpec:
    try:
        return CONTROLLER_MAPPING_PROFILES[profile_key]
    except KeyError as exc:
        available = ", ".join(CONTROLLER_MAPPING_PROFILES)
        raise ValueError(
            f"unknown controller mapping profile {profile_key!r}: {available}"
        ) from exc


def build_controller_mapping_profile_report(
    profile_key: str = DEFAULT_CONTROLLER_MAPPING_PROFILE,
) -> ControllerMappingProfileReport:
    """Build the passive controller-brain mapping report."""

    return ControllerMappingProfileReport(
        title=REPORT_TITLE,
        profile=_resolve_controller_profile(profile_key),
        safety=_SAFETY,
    )


def _control_line(control: ControllerMappingControlSpec) -> str:
    return (
        f"  {control.slot:02d}. {control.label} | "
        f"{control.target_device}/{control.target_scope} | "
        f"intent={control.intent_key} | action={control.action} | "
        f"lane={control.lane} | safety={control.safety_tier} | "
        f"recovery={control.recovery_action}"
    )


def _page_lines(index: int, page: ControllerMappingPageSpec) -> list[str]:
    lines = [
        f"Page {index}: {page.label}",
        f"  key: {page.key}",
        f"  summary: {page.summary}",
    ]
    lines.extend(_control_line(control) for control in page.controls)
    return lines


def format_controller_mapping_profile_report(
    report: ControllerMappingProfileReport | None = None,
) -> tuple[str, ...]:
    """Format ``report`` as deterministic operator-readable text lines."""

    source_report = build_controller_mapping_profile_report() if report is None else report
    body_lines: list[str] = [
        f"Controller profile: {source_report.profile.key}",
        f"Label: {source_report.profile.label}",
        f"Controller family: {source_report.profile.controller_family}",
        f"Layout: {source_report.profile.controller_layout}",
        f"Encoder slots per page: {source_report.profile.encoder_count}",
        f"Safety summary: {source_report.profile.safety_summary}",
        "",
        "Pages:",
    ]
    for index, page in enumerate(source_report.profile.pages, start=1):
        body_lines.extend(_page_lines(index, page))
    body_lines.extend(
        [
            "",
            "Safety:",
            *[f"- {name}: {source_report.safety[name]}" for name in sorted(source_report.safety)],
            "",
            "Blocked active actions:",
            *[f"- {action}" for action in source_report.profile.blocked_active_actions],
        ]
    )
    return tuple(passive_report_lines(_HEADER, body_lines))


def _control_payload(control: ControllerMappingControlSpec) -> dict[str, object]:
    return {
        "slot": control.slot,
        "label": control.label,
        "target_device": control.target_device,
        "target_scope": control.target_scope,
        "intent_key": control.intent_key,
        "action": control.action,
        "lane": control.lane,
        "safety_tier": control.safety_tier,
        "recovery_action": control.recovery_action,
        "notes": control.notes,
    }


def _page_payload(page: ControllerMappingPageSpec) -> dict[str, object]:
    return {
        "key": page.key,
        "label": page.label,
        "summary": page.summary,
        "controls": [_control_payload(control) for control in page.controls],
    }


def build_controller_mapping_profile_payload(
    profile_key: str = DEFAULT_CONTROLLER_MAPPING_PROFILE,
) -> dict[str, object]:
    """Build deterministic JSON-ready controller-brain mapping data."""

    report = build_controller_mapping_profile_report(profile_key)
    return {
        "title": report.title,
        "profile_key": report.profile.key,
        "label": report.profile.label,
        "controller_family": report.profile.controller_family,
        "controller_layout": report.profile.controller_layout,
        "encoder_count": report.profile.encoder_count,
        "safety_summary": report.profile.safety_summary,
        "safety": dict(report.safety),
        "blocked_active_actions": list(report.profile.blocked_active_actions),
        "pages": [_page_payload(page) for page in report.profile.pages],
    }


CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND: Final[CliCommand] = make_passive_report_command(
    "controller-brain-mapping-report",
    "Passive 16-encoder controller-brain intent mapping catalog.",
    format_lines=lambda: format_controller_mapping_profile_report(),
    build_payload=build_controller_mapping_profile_payload,
)

register(CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND)

__all__ = (
    "CONTROLLER_MAPPING_PROFILE_CATALOG_CLI_COMMAND",
    "ControllerMappingProfileReport",
    "build_controller_mapping_profile_payload",
    "build_controller_mapping_profile_report",
    "format_controller_mapping_profile_report",
)
