"""Passive operator guide for Twelve Pad Rytm runtime validation.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

DEFAULT_VALIDATION_STYLE = "Birmingham dark techno"
DEFAULT_VALIDATION_DISCOVERY = 0.35


def format_rytm_runtime_validation_guide() -> list[str]:
    """Return the deterministic Rytm runtime hardware validation guide."""

    style_arg = f'--runtime-style "{DEFAULT_VALIDATION_STYLE}"'
    discovery_arg = f"--runtime-discovery {DEFAULT_VALIDATION_DISCOVERY:.2f}"
    lines = [
        "RytmRandomizer passive Twelve Pad Rytm Runtime Validation Guide",
        "Purpose:",
        "- Prepare the guarded Rytm runtime hardware test without touching hardware.",
        "- Validate one Rytm pad at a time before sending the full 12-pad runtime.",
        f"Recommended style: {DEFAULT_VALIDATION_STYLE}",
        f"Recommended discovery: {DEFAULT_VALIDATION_DISCOVERY:.2f}",
        "Expected one-pad messages: 11",
        "Expected full-runtime messages: 132",
        "Passive preview before active validation:",
        (
            "python -m rytm_randomizer.cli twelve-pad-rytm-runtime-report "
            f'--style "{DEFAULT_VALIDATION_STYLE}" '
            f"--discovery {DEFAULT_VALIDATION_DISCOVERY:.2f} --runtime-pad 10"
        ),
        "One-pad validation order:",
    ]
    for pad in range(1, 13):
        lines.extend(
            [
                f"- Pad {pad} dry-run:",
                (
                    "rytm-randomizer --dry-run --twelve-pad-rytm-runtime "
                    f"{style_arg} {discovery_arg} --runtime-pad {pad}"
                ),
                f"- Pad {pad} armed send:",
                (
                    "rytm-randomizer --arm --twelve-pad-rytm-runtime "
                    f"{style_arg} {discovery_arg} --runtime-pad {pad}"
                ),
            ]
        )

    lines.extend(
        [
            "Full 12-pad runtime validation:",
            ("rytm-randomizer --dry-run --twelve-pad-rytm-runtime " f"{style_arg} {discovery_arg}"),
            ("rytm-randomizer --arm --twelve-pad-rytm-runtime " f"{style_arg} {discovery_arg}"),
            "Recommended live order:",
            "- Pad 1 through Pad 12, then full 12-pad runtime",
            "Operator notes template:",
            "- Rytm port selected:",
            "- Pad 1 heard change / safe:",
            "- Pad 2 heard change / safe:",
            "- Pad 3 heard change / safe:",
            "- Pad 4 heard change / safe:",
            "- Pad 5 heard change / safe:",
            "- Pad 6 heard change / safe:",
            "- Pad 7 heard change / safe:",
            "- Pad 8 heard change / safe:",
            "- Pad 9 heard change / safe:",
            "- Pad 10 heard change / safe:",
            "- Pad 11 heard change / safe:",
            "- Pad 12 heard change / safe:",
            "- Full 12-pad runtime tested:",
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
    "DEFAULT_VALIDATION_DISCOVERY",
    "DEFAULT_VALIDATION_STYLE",
    "format_rytm_runtime_validation_guide",
]
