"""Passive operator guide for dual-machine lane-scoped validation.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

DEFAULT_RYTM_SLOT = 1
DEFAULT_RYTM_PAD = 1
DEFAULT_ANALOG_FOUR_TRACK = 4
DEFAULT_DEPTH = "micro"
EXPECTED_LANE_SCOPED_MESSAGES = 11


def format_dual_machine_lane_validation_guide() -> list[str]:
    """Return the deterministic dual-machine lane validation guide."""

    lane_args = (
        f"--snapshot-rytm-pad {DEFAULT_RYTM_PAD} "
        f"--snapshot-analog-four-track {DEFAULT_ANALOG_FOUR_TRACK}"
    )
    snapshot_args = (
        "<rytm-sysex-path> "
        f"--slot {DEFAULT_RYTM_SLOT} --depth {DEFAULT_DEPTH} "
        f"--rytm-pad {DEFAULT_RYTM_PAD} "
        f"--analog-four-track {DEFAULT_ANALOG_FOUR_TRACK}"
    )
    app_args = (
        "--dual-machine-snapshot-send "
        "--snapshot-path <rytm-sysex-path> "
        f"--snapshot-slot {DEFAULT_RYTM_SLOT} "
        f"--snapshot-depth {DEFAULT_DEPTH} "
        "--snapshot-target both "
        f"{lane_args}"
    )

    return [
        "RytmRandomizer passive Dual-Machine Lane Validation Guide",
        "Purpose:",
        "- Prepare a lane-scoped Rytm + Analog Four test without touching hardware.",
        "- Validate one Rytm pad plus one A4 track before full dual-machine sends.",
        f"Recommended Rytm pad: {DEFAULT_RYTM_PAD}",
        f"Recommended Analog Four track: {DEFAULT_ANALOG_FOUR_TRACK}",
        f"Recommended depth: {DEFAULT_DEPTH}",
        f"Expected lane-scoped messages: {EXPECTED_LANE_SCOPED_MESSAGES}",
        "Passive preview stack:",
        f"python -m rytm_randomizer.cli dual-machine-mock-bridge-report {snapshot_args}",
        (
            "python -m rytm_randomizer.cli "
            f"dual-machine-live-snapshot-readiness-report {snapshot_args}"
        ),
        (
            "python -m rytm_randomizer.cli "
            f"dual-machine-active-send-plan-report {snapshot_args}"
        ),
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
        "- Armed lane-scoped both-machine send",
        "- Then widen to other pads/tracks or full target scope",
        "Operator notes template:",
        "- Rytm project/kit path:",
        "- Rytm port selected:",
        "- Analog Four port selected:",
        f"- Pad {DEFAULT_RYTM_PAD} heard change / safe:",
        f"- A4 Track {DEFAULT_ANALOG_FOUR_TRACK} heard change / safe:",
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


__all__ = [
    "DEFAULT_ANALOG_FOUR_TRACK",
    "DEFAULT_DEPTH",
    "DEFAULT_RYTM_PAD",
    "DEFAULT_RYTM_SLOT",
    "EXPECTED_LANE_SCOPED_MESSAGES",
    "format_dual_machine_lane_validation_guide",
]
