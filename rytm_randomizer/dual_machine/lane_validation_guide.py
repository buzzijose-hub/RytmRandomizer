"""Passive operator guide for dual-machine lane-scoped validation.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

from dataclasses import dataclass

DEFAULT_RYTM_SLOT = 1
DEFAULT_RYTM_PAD = 1
DEFAULT_ANALOG_FOUR_TRACK = 4
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


@dataclass(frozen=True)
class DualMachineLaneValidationGuideRequest:
    """Normalized operator request for the passive validation guide."""

    target: str
    rytm_pad: int | None
    analog_four_track: int | None


def build_dual_machine_lane_validation_guide_request(
    *,
    target: str = "both",
    rytm_pad: int | None = None,
    analog_four_track: int | None = None,
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
        return DualMachineLaneValidationGuideRequest(
            target=target,
            rytm_pad=rytm_pad or DEFAULT_RYTM_PAD,
            analog_four_track=None,
        )
    if target == "analog-four":
        if rytm_pad is not None:
            raise ValueError("Rytm pad cannot be used with target analog-four")
        return DualMachineLaneValidationGuideRequest(
            target=target,
            rytm_pad=None,
            analog_four_track=analog_four_track or DEFAULT_ANALOG_FOUR_TRACK,
        )
    return DualMachineLaneValidationGuideRequest(
        target=target,
        rytm_pad=rytm_pad or DEFAULT_RYTM_PAD,
        analog_four_track=analog_four_track or DEFAULT_ANALOG_FOUR_TRACK,
    )


def format_dual_machine_lane_validation_guide(
    *,
    target: str = "both",
    rytm_pad: int | None = None,
    analog_four_track: int | None = None,
) -> list[str]:
    """Return the deterministic dual-machine lane validation guide."""

    request = build_dual_machine_lane_validation_guide_request(
        target=target,
        rytm_pad=rytm_pad,
        analog_four_track=analog_four_track,
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
        *_saved_bank_preflight_lines(),
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
        "- Rytm project/kit path:",
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
        *_saved_bank_preflight_lines(),
        "Rytm-only lanes:",
    ]
    for pad in range(1, 13):
        lines.append(
            f"- Pad {pad} / expected {EXPECTED_RYTM_LANE_MESSAGES} messages: "
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
            f"- Pad {pad} + A4 Track {track} / expected "
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
    parts = [
        "<rytm-sysex-path> " f"--slot {DEFAULT_RYTM_SLOT} --depth {DEFAULT_DEPTH}",
    ]
    parts.append(f"--target {request.target}")
    if request.rytm_pad is not None:
        parts.append(f"--rytm-pad {request.rytm_pad}")
    if request.analog_four_track is not None:
        parts.append(f"--analog-four-track {request.analog_four_track}")
    return " ".join(parts)


def _saved_bank_preflight_lines() -> list[str]:
    return [
        "Saved-bank preflight:",
        "- Export or choose the saved Rytm and Analog Four kit-bank/whole-project SysEx files.",
        SAVED_BANK_PREFLIGHT_COMMAND,
        "- Continue only if combined blocked lanes are 0 and Problem slots is none.",
        "- Treat Analog Four as candidate-ready until the live lane tests confirm each track.",
    ]


def _app_args(request: DualMachineLaneValidationGuideRequest) -> str:
    parts = [
        "--dual-machine-snapshot-send",
        "--snapshot-path <rytm-sysex-path>",
        f"--snapshot-slot {DEFAULT_RYTM_SLOT}",
        f"--snapshot-depth {DEFAULT_DEPTH}",
        f"--snapshot-target {request.target}",
    ]
    if request.rytm_pad is not None:
        parts.append(f"--snapshot-rytm-pad {request.rytm_pad}")
    if request.analog_four_track is not None:
        parts.append(f"--snapshot-analog-four-track {request.analog_four_track}")
    return " ".join(parts)


def _purpose_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.target == "rytm":
        return "- Prepare a Rytm-only lane test while leaving Analog Four untouched."
    if request.target == "analog-four":
        return "- Prepare an Analog-Four-only lane test while leaving Rytm untouched."
    return "- Prepare a lane-scoped Rytm + Analog Four test without touching hardware."


def _rytm_pad_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.rytm_pad is None:
        return "Rytm pad: not targeted"
    return f"Recommended Rytm pad: {request.rytm_pad}"


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


def _armed_order_line(request: DualMachineLaneValidationGuideRequest) -> str:
    if request.target == "both":
        return "- Armed lane-scoped both-machine send"
    if request.target == "rytm":
        return "- Armed Rytm-only lane-scoped send"
    return "- Armed Analog-Four-only lane-scoped send"


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
