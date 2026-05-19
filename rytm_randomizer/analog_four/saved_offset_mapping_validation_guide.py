"""Passive guide for proving Analog Four saved-offset mappings.

This module is pure text. It imports no MIDI libraries, opens no ports, sends
no MIDI, receives no SysEx, writes no SysEx, and mutates no hardware.
"""

from __future__ import annotations

SUPPORTED_MAPPING_PARAMETERS = {
    "filter-1-frequency": ("Filter 1 Frequency", 18),
    "filter-2-frequency": ("Filter 2 Frequency", 19),
    "osc1-level": ("OSC1 Level", 69),
    "osc2-level": ("OSC2 Level", 78),
    "osc1-waveform": ("OSC1 Waveform", 70),
    "noise-fade": ("Noise Fade", 76),
    "noise-level": ("Noise Level", 77),
    "amp-pan": ("Amp Pan", 10),
    "amp-env-decay": ("Amp Env Decay", 105),
    "reverb-send": ("Reverb Send", 93),
    "track-level": ("Track Level", 95),
}
DEFAULT_MAPPING_PARAMETER = "filter-1-frequency"
DEFAULT_MAPPING_TRACK = 1
DEFAULT_DIFF_LIMIT = 8


def format_analog_four_saved_offset_mapping_validation_guide(
    *,
    track: int = DEFAULT_MAPPING_TRACK,
    parameter: str = DEFAULT_MAPPING_PARAMETER,
) -> list[str]:
    """Return the deterministic A4 saved-offset mapping validation guide."""

    if track not in range(1, 5):
        raise ValueError("track must be 1-4")
    parameter_key = _normalize_parameter(parameter)
    parameter_name, cc = SUPPORTED_MAPPING_PARAMETERS[parameter_key]

    return [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Validation Guide",
        "Purpose:",
        "- Prepare a controlled before/after export workflow for proving one A4 saved offset.",
        "- Cover the mapped-CC starter-profile parameters already used by A4 runtime plans.",
        "- Promote only offsets proven by controlled diffs into named CC mappings.",
        "- Keep unverified saved offsets blocked from guarded hardware sends.",
        "Selected target:",
        f"- Track: {track}",
        f"- Parameter: {parameter_name}",
        f"- Parameter key: {parameter_key}",
        f"- Known runtime CC: CC{cc}",
        f"- Supported mapping targets: {', '.join(sorted(SUPPORTED_MAPPING_PARAMETERS))}",
        "Operator setup:",
        "- Use a copied or otherwise restorable A4 kit slot, not the only live copy.",
        "- Start from a saved baseline export before changing the parameter.",
        "- Change exactly one parameter on exactly one track.",
        "- Save/export the variant immediately after that one change.",
        "Controlled export workflow:",
        "1. Export the baseline kit or whole project to <before.syx>.",
        (
            f"2. On A4 Track {track}, change only {parameter_name} "
            "by a clearly audible but reversible amount."
        ),
        "3. Export the variant kit or whole project to <after.syx>.",
        "4. Run the passive controlled-diff command below.",
        "Passive diff command:",
        (
            "python -m rytm_randomizer.cli analog-four-controlled-diff-report "
            f'"<before.syx>" "<after.syx>" --slot <1-128> '
            f"--track {track} --limit {DEFAULT_DIFF_LIMIT}"
        ),
        "Promotion rule:",
        "- Accept the result only when the changed offset set is small and explainable.",
        "- Prefer one changed candidate offset for the selected parameter.",
        "- If several offsets move, repeat the export with a cleaner single-parameter change.",
        "- Do not add a mapping from a broad performance tweak or a multi-knob edit.",
        "Mapping entry shape after proof:",
        "AnalogFourVerifiedSavedOffsetMapping(",
        f"    track={track},",
        "    relative_offset=<proved-offset>,",
        f'    parameter_name="{parameter_name}",',
        f"    cc={cc},",
        ")",
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


def format_analog_four_saved_offset_mapping_validation_error(message: str) -> list[str]:
    """Format deterministic A4 saved-offset mapping guide errors."""

    return [
        "RytmRandomizer passive Analog Four Saved-Offset Mapping Validation Guide",
        "Found: False",
        f"Message: {message}. No MIDI was sent. No command executed.",
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


def _normalize_parameter(parameter: str) -> str:
    key = str(parameter).strip().lower().replace("_", "-")
    if key not in SUPPORTED_MAPPING_PARAMETERS:
        supported = ", ".join(sorted(SUPPORTED_MAPPING_PARAMETERS))
        raise ValueError(f"parameter must be one of: {supported}")
    return key


__all__ = [
    "DEFAULT_MAPPING_PARAMETER",
    "DEFAULT_MAPPING_TRACK",
    "SUPPORTED_MAPPING_PARAMETERS",
    "format_analog_four_saved_offset_mapping_validation_error",
    "format_analog_four_saved_offset_mapping_validation_guide",
]
