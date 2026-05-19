"""Passive operator guide for Analog Four runtime hardware validation.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

SUPPORTED_PROFILES = ("balanced", "birmingham-dark", "detroit-classic", "peak-time")
DEFAULT_VALIDATION_PROFILE = "peak-time"


def format_analog_four_runtime_validation_guide() -> list[str]:
    """Return the deterministic A4 runtime hardware validation guide."""

    lines = [
        "RytmRandomizer passive Analog Four Runtime Validation Guide",
        "Purpose:",
        "- Prepare the guarded A4 runtime hardware test without touching hardware.",
        "- Validate one A4 track at a time before sending the full profile.",
        "Supported profiles:",
        f"- {', '.join(SUPPORTED_PROFILES)}",
        f"Recommended profile: {DEFAULT_VALIDATION_PROFILE}",
        "Expected single-track messages: 5",
        "Expected full-profile messages: 20",
        "Single-track validation order:",
    ]
    for track in range(1, 5):
        lines.extend(
            [
                f"- Track {track} dry-run:",
                (
                    "rytm-randomizer --dry-run --analog-four-runtime "
                    f"--analog-four-profile {DEFAULT_VALIDATION_PROFILE} "
                    f"--analog-four-runtime-track {track}"
                ),
                f"- Track {track} armed send:",
                (
                    "rytm-randomizer --arm --analog-four-runtime "
                    f"--analog-four-profile {DEFAULT_VALIDATION_PROFILE} "
                    f"--analog-four-runtime-track {track}"
                ),
            ]
        )

    lines.extend(
        [
            "Full-profile validation:",
            (
                "rytm-randomizer --dry-run --analog-four-runtime "
                f"--analog-four-profile {DEFAULT_VALIDATION_PROFILE}"
            ),
            (
                "rytm-randomizer --arm --analog-four-runtime "
                f"--analog-four-profile {DEFAULT_VALIDATION_PROFILE}"
            ),
            "Recommended live order:",
            "- Track 1, Track 2, Track 3, Track 4, then full profile",
            "Operator notes template:",
            "- A4 port selected:",
            "- Track 1 heard change / returned safe:",
            "- Track 2 heard change / returned safe:",
            "- Track 3 heard change / returned safe:",
            "- Track 4 heard change / returned safe:",
            "- Full profile tested:",
            "- Unexpected behavior:",
            "Safety:",
            "- passive/read-only",
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


__all__ = [
    "DEFAULT_VALIDATION_PROFILE",
    "SUPPORTED_PROFILES",
    "format_analog_four_runtime_validation_guide",
]
