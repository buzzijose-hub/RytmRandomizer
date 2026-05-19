"""Passive operator guide for dual-machine lane-scoped validation.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..essence.machine_catalog import get_rytm_pad_capability

DEFAULT_RYTM_SLOT = 1
DEFAULT_RYTM_PAD = 1
DEFAULT_ANALOG_FOUR_SLOT = 1
DEFAULT_ANALOG_FOUR_TRACK = 4
DEFAULT_ANALOG_FOUR_MAPPING_MANIFEST_PATH = "<analog-four-mapping-manifest-path>"
DEFAULT_DEPTH = "micro"
EXPECTED_LANE_SCOPED_MESSAGES = 11
EXPECTED_RYTM_LANE_MESSAGES = 6
EXPECTED_ANALOG_FOUR_LANE_MESSAGES = 5
VALID_TARGETS = ("rytm", "analog-four", "both")
ALL_LANE_PILOT_PAIRS = ((1, 1), (5, 2), (10, 3), (12, 4))
SAVED_BANK_PREFLIGHT_COMMAND = (
    "python -m rytm_randomizer.cli dual-machine-kit-bank-readiness-report "
    "--rytm <rytm-sysex-path> --analog-four <analog-four-sysex-path>"
)
RYTM_BANK_PREFLIGHT_COMMAND = (
    "python -m rytm_randomizer.cli sysex-kit-bank-report <rytm-sysex-path>"
)
ANALOG_FOUR_BANK_PREFLIGHT_COMMAND = (
    "python -m rytm_randomizer.cli analog-four-kit-bank-report <analog-four-sysex-path>"
)


@dataclass(frozen=True)
class DualMachineLaneValidationGuideRequest:
    """Normalized operator request for the passive validation guide."""

    target: str
    rytm_pad: int | None
    analog_four_track: int | None
    analog_four_mapping_manifest: str | None


def build_dual_machine_lane_validation_guide_request(
    *,
    target: str = "both",
    rytm_pad: int | None = None,
    analog_four_track: int | None = None,
    analog_four_mapping_manifest: str | None = None,
) -> DualMachineLaneValidationGuideRequest:
    """Validate and normalize lane guide options."""

    if target not in VALID_TARGETS:
        raise ValueError("Target must be rytm, analog-four, or both")

    if rytm_pad is not None and not 1 <= rytm_pad <= 12:
        raise ValueError("Rytm pad must be between 1 and 12")
    if analog_four_track is not None and not 1 <= analog_four_track <= 4:
        raise ValueError("Analog Four track must be between 1 and 4")

    if target == "rytm":
        if analog_four_track is not None:
            raise ValueError("Analog Four track cannot be used with target rytm")
        if analog_four_mapping_manifest is not None:
            raise ValueError("Analog Four mapping manifest cannot be used with target rytm")
        return DualMachineLaneValidationGuideRequest(
            target=target,
            rytm_pad=rytm_pad or DEFAULT_RYTM_PAD,
            analog_four_track=None,
            analog_four_mapping_manifest=None,
        )
    if target == "analog-four":
        if rytm_pad is not None:
            raise ValueError("Rytm pad cannot be used with target analog-four")
        return DualMachineLaneValidationGuideRequest(
            target=target,
            rytm_pad=None,
            analog_four_track=analog_four_track or DEFAULT_ANALOG_FOUR_TRACK,
            analog_four_mapping_manifest=analog_four_mapping_manifest,
        )
    return DualMachineLaneValidationGuideRequest(
        target=target,
        rytm_pad=rytm_pad or DEFAULT_RYTM_PAD,
        analog_four_track=analog_four_track or DEFAULT_ANALOG_FOUR_TRACK,
        analog_four_mapping_manifest=analog_four_mapping_manifest,
    )


def format_dual_machine_lane_validation_guide(
    *,
    target: str = "both",
    rytm_pad: int | None = None,
    analog_four_track: int | None = None,
    analog_four_mapping_manifest: str | None = None,
) -> list[str]:
    """Return the deterministic dual-machine lane validation guide."""

    request = build_dual_machine_lane_validation_guide_request(
        target=target,
        rytm_pad=rytm_pad,
        analog_four_track=analog_four_track,
        analog_four_mapping_manifest=analog_four_mapping_manifest,
    )
    snapshot_args = _snapshot_report_args(request)
    app_args = _app_args(request)

    return [
        "RytmRandomizer passive Dual-Machine Lane Validation Guide",
        "Purpose:",
        _purpose_line(request),
        "- Validate the scoped send before widening to full dual-machine scope.",
        f"Target scope: {request.target}",
        _rytm_pad_line(request),
        _analog_four_track_line(request),
        f"Recommended depth: {DEFAULT_DEPTH}",
        f"Expected lane-scoped messages: {_expected_message_count(request)}",
        "Implementation boundaries:",
        *_implementation_boundary_lines(),
        *_saved_bank_preflight_lines(request.target),
        *_snapshot_source_note_lines(request),
        "Passive preview stack:",
        f"python -m rytm_randomizer.cli dual-machine-mock-bridge-report {snapshot_args}",
        (
            "python -m rytm_randomizer.cli "
            f"dual-machine-live-snapshot-readiness-report {snapshot_args}"
        ),
        ("python -m rytm_randomizer.cli " f"dual-machine-active-send-plan-report {snapshot_args}"),
        (
            "python -m rytm_randomizer.cli "
            f"dual-machine-guarded-send-dry-run-report {snapshot_args}"
        ),
        "App dry-run:",
        f"rytm-randomizer --dry-run {app_args}",
        "Armed validation:",
        f"rytm-randomizer --arm {app_args}",
        "Recommended live order:",
        "- Passive preview stack",
        "- App dry-run",
        _armed_order_line(request),
        "- Then widen to other pads/tracks or full target scope",
        "Operator notes template:",
        *_path_note_lines(request),
        *_port_note_lines(request),
        *_heard_note_lines(request),
        "- Expected message count seen:",
        "- Unexpected behavior:",
        "Safety:",
        "- passive/read-only",
        "- guide text only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def format_dual_machine_all_lane_validation_guide() -> list[str]:
    """Return the deterministic all-lane validation matrix."""

    lines = [
        "RytmRandomizer passive Dual-Machine All-Lane Validation Guide",
        "Purpose:",
        "- Validate every Rytm pad and every Analog Four track one lane at a time.",
        "- Use each focused guide before running any armed lane send.",
        "Recommended order:",
        "- Rytm-only Pads 1-12",
        "- Analog-Four-only Tracks 1-4",
        "- Both-machine pilot pairs",
        "Implementation boundaries:",
        *_implementation_boundary_lines(),
        *_all_lane_saved_bank_preflight_lines(),
        "Rytm-only lanes:",
    ]
    for pad in range(1, 13):
        lines.append(
            f"- Pad {_rytm_pad_label(pad)} / expected {EXPECTED_RYTM_LANE_MESSAGES} messages: "
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide "
            f"--target rytm --rytm-pad {pad}"
        )

    lines.append("Analog-Four-only lanes:")
    for track in range(1, 5):
        lines.append(
            f"- Track {track} / expected {EXPECTED_ANALOG_FOUR_LANE_MESSAGES} messages: "
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide "
            f"--target analog-four --analog-four-track {track}"
        )

    lines.append("Both-machine pilot pairs:")
    for pad, track in ALL_LANE_PILOT_PAIRS:
        lines.append(
            f"- Pad {_rytm_pad_label(pad)} + A4 Track {track} / expected "
            f"{EXPECTED_LANE_SCOPED_MESSAGES} messages: "
            "python -m rytm_randomizer.cli dual-machine-lane-validation-guide "
            f"--target both --rytm-pad {pad} --analog-four-track {track}"
        )

    lines.extend(
        [
            "Safety:",
            "- passive/read-only",
            "- guide text only",
            "- no MIDI sending",
            "- no MIDI receive",
            "- no port opening",
            "- no command execution",
            "- no hardware mutation",
            "- no live SysEx receive",
            "- no SysEx writes",
            "- no hardware required",
        ]
    )
    return lines


def format_dual_machine_lane_validation_guide_error(message: str) -> list[str]:
    """Return deterministic lane-guide CLI validation errors."""

    return [
        f"{message}. No MIDI was sent. No command executed.",
        "Safety:",
        "- passive/read-only",
        "- guide text only",
        "- no MIDI sending",
        "- no MIDI receive",
        "- no port opening",
        "- no command execution",
        "- no hardware mutation",
        "- no live SysEx receive",
        "- no SysEx writes",
        "- no hardware required",
    ]


def _snapshot_report_args(request: DualMachineLaneValidationGuideRequest) -> str:
    parts = []
    if request.target != "analog-four":
        parts.append("<rytm-sysex-path> " f"--slot {DEFAULT_RYTM_SLOT}")
    parts.append(f"--depth {DEFAULT_DEPTH}")
    if _targets_analog_four(request):
        parts.append(
            "--analog-four-path <analog-four-sysex-path> "
            f"--analog-four-slot {DEFAULT_ANALOG_FOUR_SLOT}"
        )
        parts.append(_analog_four_mapping_manifest_arg(request))
    parts.append(f"--target {request.target}")
    if request.rytm_pad is not None:
        parts.append(f"--rytm-pad {request.rytm_pad}")
    if request.analog_four_track is not None:
        parts.append(f"--analog-four-track {request.analog_four_track}")
    return " ".join(parts)


def _saved_bank_preflight_lines(target: str) -> list[str]:
    if target == "rytm":
        return [
            "Saved-bank preflight:",
            "- Export or choose the saved Rytm kit-bank/whole-project SysEx file.",
            RYTM_BANK_PREFLIGHT_COMMAND,
            "- Continue only if Rytm blocked mutation pads are 0.",
        ]
    if target == "analog-four":
        return [
            "Saved-bank preflight:",
            "- Export or choose the saved Analog Four kit-bank/whole-project SysEx file.",
            ANALOG_FOUR_BANK_PREFLIGHT_COMMAND,
            "- Continue only if Analog Four blocked tracks are 0.",
            "- Use a ready Analog Four mapping manifest before any saved A4 " "snapshot send.",
        ]
    return [
        "Saved-bank preflight:",
        "- Export or choose the saved Rytm and Analog Four kit-bank/whole-project SysEx files.",
        SAVED_BANK_PREFLIGHT_COMMAND,
        "- Continue only if combined blocked lanes are 0 and Problem slots is none.",
        "- Use a ready Analog Four mapping manifest before any saved A4 " "snapshot send.",
    ]


def _snapshot_source_note_lines(request: DualMachineLaneValidationGuideRequest) -> list[str]:
    if request.target == "rytm":
        return [
            "Snapshot source notes:",
            f"- Rytm source: <rytm-sysex-path> slot {DEFAULT_RYTM_SLOT} supplies the "
            "Rytm snapshot.",
        ]
    if request.target == "analog-four":
        return [
            "Snapshot source notes:",
            "- Analog Four source: <analog-four-sysex-path> slot "
            f"{DEFAULT_ANALOG_FOUR_SLOT} supplies saved A4 snapshot candidates.",
            "- Analog Four mapping manifest: verified saved offsets become "
            "mapped CC sends; unverified offsets stay blocked.",
        ]
    return [
        "Snapshot source notes:",
        (
            f"- Rytm source: <rytm-sysex-path> slot {DEFAULT_RYTM_SLOT} supplies the "
            "Rytm snapshot."
        ),
        "- Analog Four source: <analog-four-sysex-path> slot "
        f"{DEFAULT_ANALOG_FOUR_SLOT} supplies saved A4 snapshot candidates.",
        "- Analog Four mapping manifest: verified saved offsets become "
        "mapped CC sends; unverified offsets stay blocked.",
    ]


def _all_lane_saved_bank_preflight_lines() -> list[str]:
    return [
        "Saved-bank preflight:",
        "- Before Rytm-only lanes: " + RYTM_BANK_PREFLIGHT_COMMAND,
        "- Before Analog-Four-only lanes: " + ANALOG_FOUR_BANK_PREFLIGHT_COMMAND,
        "- Before both-machine pilot pairs: " + SAVED_BANK_PREFLIGHT_COMMAND,
        "- Prepare a ready Analog Four mapping manifest before A4 saved-snapshot " "lane sends.",
        "- Continue only if the selected scope reports zero blocked lanes.",
    ]


def _implementation_boundary_lines() -> list[str]:
    return [
        "- Rytm implementation: 12 pad/machine lanes with pad-machine compatibility gates.",
        "- Analog Four implementation: 4 synth tracks with saved-offset mapping manifest gates.",
        "- Shared layer: target scoping, reporting, orchestration, and guarded validation only.",
    ]


def _app_args(request: DualMachineLaneValidationGuideRequest) -> str:
    parts = [
        "--dual-machine-snapshot-send",
    ]
    if request.target != "analog-four":
        parts.extend(
            [
                "--snapshot-path <rytm-sysex-path>",
                f"--snapshot-slot {DEFAULT_RYTM_SLOT}",
            ]
        )
    parts.extend(
        [
            f"--snapshot-depth {DEFAULT_DEPTH}",
            f"--snapshot-target {request.target}",
        ]
    )
    if request.rytm_pad is not None:
        parts.append(f"--snapshot-rytm-pad {request.rytm_pad}")
    if request.analog_four_track is not None:
        parts.append(f"--snapshot-analog-four-track {request.analog_four_track}")
    if _targets_analog_four(request):
        parts.extend(
            [
                "--analog-four-path <analog-four-sysex-path>",
                f"--analog-four-slot {DEFAULT_ANALOG_FOUR_SLOT}",
                _analog_four_mapping_manifest_arg(request),
            ]
        )
    return " ".join(parts)


def _analog_four_mapping_manifest_arg(request: DualMachineLaneValidationGuideRequest) -> str:
    manifest_path = (
        request.analog_four_mapping_manifest or DEFAULT_ANALOG_FOUR_MAPPING_MANIFEST_PATH
    )
    return f"--analog-four-mapping-manifest {manifest_path}"


def _purpose_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.target == "rytm":
        return "- Prepare a Rytm-only lane test while leaving Analog Four untouched."
    if request.target == "analog-four":
        return "- Prepare an Analog-Four-only lane test while leaving Rytm untouched."
    return "- Prepare a lane-scoped Rytm + Analog Four test without touching hardware."


def _rytm_pad_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.rytm_pad is None:
        return "Rytm pad: not targeted"
    return f"Recommended Rytm pad: {_rytm_pad_label(request.rytm_pad)}"


def _rytm_pad_label(pad: int) -> str:
    capability = get_rytm_pad_capability(pad)
    return f"{pad} / {capability.track_code} / {capability.label}"


def _analog_four_track_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.analog_four_track is None:
        return "Analog Four track: not targeted"
    return f"Recommended Analog Four track: {request.analog_four_track}"


def _expected_message_count(request: DualMachineLaneValidationGuideRequest) -> int:
    if request.target == "rytm":
        return EXPECTED_RYTM_LANE_MESSAGES
    if request.target == "analog-four":
        return EXPECTED_ANALOG_FOUR_LANE_MESSAGES
    return EXPECTED_LANE_SCOPED_MESSAGES


def _targets_analog_four(request: DualMachineLaneValidationGuideRequest) -> bool:
    return request.target in ("analog-four", "both")


def _armed_order_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.target == "both":
        return "- Armed lane-scoped both-machine send"
    if request.target == "rytm":
        return "- Armed Rytm-only lane-scoped send"
    return "- Armed Analog-Four-only lane-scoped send"


def _path_note_lines(request: DualMachineLaneValidationGuideRequest) -> list[str]:
    if request.target == "both":
        return [
            "- Rytm project/kit path:",
            "- Analog Four project/kit path:",
            "- Analog Four mapping manifest path:",
        ]
    if request.target == "rytm":
        return ["- Rytm project/kit path:"]
    return ["- Analog Four project/kit path:", "- Analog Four mapping manifest path:"]


def _port_note_lines(request: DualMachineLaneValidationGuideRequest) -> list[str]:
    if request.target == "both":
        return ["- Rytm port selected:", "- Analog Four port selected:"]
    if request.target == "rytm":
        return ["- Rytm port selected:"]
    return ["- Analog Four port selected:"]


def _heard_note_lines(request: DualMachineLaneValidationGuideRequest) -> list[str]:
    lines = []
    if request.rytm_pad is not None:
        lines.append(f"- Pad {request.rytm_pad} heard change / safe:")
    if request.analog_four_track is not None:
        lines.append(f"- A4 Track {request.analog_four_track} heard change / safe:")
    return lines


__all__ = [
    "ALL_LANE_PILOT_PAIRS",
    "DualMachineLaneValidationGuideRequest",
    "DEFAULT_ANALOG_FOUR_MAPPING_MANIFEST_PATH",
    "DEFAULT_ANALOG_FOUR_SLOT",
    "DEFAULT_ANALOG_FOUR_TRACK",
    "DEFAULT_DEPTH",
    "DEFAULT_RYTM_PAD",
    "DEFAULT_RYTM_SLOT",
    "EXPECTED_ANALOG_FOUR_LANE_MESSAGES",
    "EXPECTED_LANE_SCOPED_MESSAGES",
    "EXPECTED_RYTM_LANE_MESSAGES",
    "VALID_TARGETS",
    "build_dual_machine_lane_validation_guide_request",
    "format_dual_machine_all_lane_validation_guide",
    "format_dual_machine_lane_validation_guide",
    "format_dual_machine_lane_validation_guide_error",
]
