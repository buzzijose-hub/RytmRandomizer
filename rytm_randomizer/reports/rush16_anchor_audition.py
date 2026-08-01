"""Deterministic reports for the passive RUSH16 anchor audition batch."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Final

from ..data.rush16 import RUSH16_BATCH_ID, RUSH16_VERSION
from ..style_analysis.rush16_anchor_audition import Rush16BuildEntry

_VALIDATION_CHECKS: Final[tuple[str, ...]] = (
    "valid_sysex_framing",
    "legal_7bit_data_bytes",
    "correct_packed_and_unpacked_lengths",
    "correct_checksum_and_trailer",
    "stable_decode_encode_round_trip",
    "requested_semantics_decode_correctly",
    "unknown_and_reserved_fields_preserved",
    "no_unintended_sample_dependency",
    "hardware_accepts_kit",
    "hardware_return_confirms_critical_values",
    "unrequested_semantic_fields_stable",
    "output_gain_within_family_policy",
    "paired_low_end_ownership_compatible",
    "four_anchors_materially_distinct",
)


def rush16_build_entry_to_dict(entry: Rush16BuildEntry) -> dict[str, object]:
    """Return one stable JSON-ready build matrix row."""

    strategy = (
        "direct_sysex"
        if entry.direct_sysex_ready
        else (
            "hardware_assisted"
            if entry.hardware_assisted_ready
            else "blocked_automated_calibration"
        )
    )
    return {
        "anchor_id": entry.anchor_id,
        "device": entry.device,
        "spec_filename": entry.spec_filename,
        "target_filename": entry.target_filename,
        "spec_sha256": entry.spec_sha256,
        "reference_sha256": entry.reference_sha256,
        "reference_round_trip_identical": entry.reference_round_trip_identical,
        "construction_strategy": strategy,
        "direct_sysex_ready": entry.direct_sysex_ready,
        "hardware_apply_ready": entry.hardware_apply_ready,
        "hardware_capture_configured": entry.hardware_capture_configured,
        "hardware_assisted_ready": entry.hardware_assisted_ready,
        "final_sysex_generated": entry.final_sysex_generated,
        "direct_blockers": list(entry.direct_blockers),
        "hardware_blockers": list(entry.hardware_blockers),
        "semantic_status_counts": dict(entry.status_counts),
        "midi_ready_fields": entry.midi_ready_fields,
        "midi_message_count": entry.midi_message_count,
        "output_port_configured": entry.output_port_configured,
    }


def build_rush16_matrix(entries: Sequence[Rush16BuildEntry]) -> dict[str, object]:
    """Build the complete eight-artifact construction matrix."""

    rows = [rush16_build_entry_to_dict(entry) for entry in entries]
    return {
        "batch_id": RUSH16_BATCH_ID,
        "batch_version": RUSH16_VERSION,
        "final_artifact_count": sum(bool(row["final_sysex_generated"]) for row in rows),
        "direct_ready_count": sum(bool(row["direct_sysex_ready"]) for row in rows),
        "hardware_assisted_ready_count": sum(bool(row["hardware_assisted_ready"]) for row in rows),
        "entries": rows,
        "safety": {
            "partial_kit_finalization": False,
            "manual_sound_parameter_entry": False,
            "midi_backend_opened_during_build": False,
            "midi_port_opened_during_build": False,
            "midi_or_sysex_transmitted_during_build": False,
        },
    }


def build_rush16_family_manifest(
    entries: Sequence[Rush16BuildEntry],
    *,
    family_spec_sha256: str,
) -> dict[str, object]:
    """Build the family-level hash and readiness ledger."""

    return {
        "batch_id": RUSH16_BATCH_ID,
        "batch_version": RUSH16_VERSION,
        "family_spec_sha256": family_spec_sha256,
        "kits": [
            {
                "anchor_id": entry.anchor_id,
                "device": entry.device,
                "target_filename": entry.target_filename,
                "semantic_spec_sha256": entry.spec_sha256,
                "trusted_reference_sha256": entry.reference_sha256,
                "hardware_return_sha256": None,
                "final_kit_sha256": None,
                "final": False,
            }
            for entry in entries
        ],
        "family_acceptance": {
            "low_end_ownership_reviewed": False,
            "output_gain_policy_reviewed": False,
            "anchors_materially_distinct_reviewed": False,
            "accepted": False,
        },
    }


def build_rush16_recording_manifest(entries: Sequence[Rush16BuildEntry]) -> dict[str, object]:
    """Build the required 12-take recording ledger with no invented metadata."""

    anchors: list[str] = []
    for entry in entries:
        if entry.anchor_id not in anchors:
            anchors.append(entry.anchor_id)
    recordings = []
    for anchor_id in anchors:
        for stem in ("RYTM", "A4", "COMBINED"):
            recordings.append(
                {
                    "filename": f"{anchor_id}_{stem}.wav",
                    "anchor_id": anchor_id,
                    "stem": stem.lower(),
                    "recording_sha256": None,
                    "accepted": None,
                    "revision_notes": None,
                }
            )
    return {
        "batch_id": RUSH16_BATCH_ID,
        "tempo_bpm": None,
        "oxi_pattern_version": None,
        "oxi_root": None,
        "oxi_velocity_profile": None,
        "oxi_note_length_profile": None,
        "rytm_firmware": None,
        "a4_firmware": None,
        "rytm_gain_settings": None,
        "a4_gain_settings": None,
        "octatrack_gain_settings": None,
        "octatrack_constraints": {
            "routing_and_recording_only": True,
            "transition_scenes": False,
            "retriggers": False,
            "reverb_freeze": False,
            "master_coloration": False,
        },
        "kit_hashes": {
            entry.target_filename: {
                "final_kit_sha256": None,
                "hardware_return_sha256": None,
            }
            for entry in entries
        },
        "recordings": recordings,
    }


def build_rush16_validation(entry: Rush16BuildEntry) -> dict[str, object]:
    """Record all 14 final-kit checks without claiming unrun validation."""

    return {
        "batch_id": RUSH16_BATCH_ID,
        "anchor_id": entry.anchor_id,
        "device": entry.device,
        "target_filename": entry.target_filename,
        "final_artifact_present": False,
        "reference_preconditions": {
            "trusted_reference_sha256": entry.reference_sha256,
            "reference_decode_encode_round_trip": (
                "pass" if entry.reference_round_trip_identical else "fail"
            ),
        },
        "checks": [
            {
                "sequence": sequence,
                "check": check,
                "status": "not_run_no_final_artifact",
                "evidence": None,
            }
            for sequence, check in enumerate(_VALIDATION_CHECKS, start=1)
        ],
        "accepted": False,
    }


def format_rush16_build_report(entries: Sequence[Rush16BuildEntry]) -> str:
    """Render the human-readable construction report."""

    lines = [
        "# RUSH16 Anchor Audition Batch v0.1",
        "",
        "No final kit is present. Every row is blocked until all sound-critical fields are automatic and a hardware-return dump passes all 14 checks.",
        "",
        "| Anchor | Device | Direct | Active-kit apply | Capture configured | Final | Direct blockers | Apply blockers |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for entry in entries:
        lines.append(
            f"| {entry.anchor_id} | {entry.device} | {str(entry.direct_sysex_ready).lower()} | "
            f"{str(entry.hardware_apply_ready).lower()} | "
            f"{str(entry.hardware_capture_configured).lower()} | false | "
            f"{len(entry.direct_blockers)} | {len(entry.hardware_blockers)} |"
        )
    lines.extend(
        [
            "",
            "## Construction Policy",
            "",
            "- Direct output is allowed only when every critical saved-kit mapping is promoted.",
            "- Hardware-assisted output is allowed only when every critical field is automatically applied and the exact return-input port is configured.",
            "- Selecting a disposable active kit, saving it, and initiating its dump are the only permitted manual device actions.",
            "- No oscillator, filter, envelope, machine, level, effect, or routing value may be entered manually.",
            "- The current partial MIDI plans are calibration/review artifacts and must not be applied.",
            "",
            "## Safety",
            "",
            "- MIDI backend opened during build: `false`",
            "- MIDI port opened during build: `false`",
            "- MIDI or SysEx transmitted during build: `false`",
            "- Final SysEx generated: `false`",
            "",
        ]
    )
    return "\n".join(lines)


def format_rush16_operator_runbook(
    entries: Sequence[Rush16BuildEntry],
    *,
    config_path: str,
) -> str:
    """Render exact guarded commands; blocked rows are clearly non-executable."""

    lines = [
        "# RUSH16 Operator Runbook",
        "",
        "## Current Gate",
        "",
        "Do not run the armed commands below while `BUILD_MATRIX.json` reports blockers. The app also fails closed before constructing a MIDI provider.",
        "",
        "Passive deterministic check:",
        "",
        "```powershell",
        ".\\.venv\\Scripts\\python.exe scripts\\rush16_anchor_audition.py --check",
        "```",
        "",
        "## Hardware Sequence After All Gates Pass",
        "",
        "1. Connect one device and verify the exact configured input/output names.",
        "2. Select an initialized disposable active-kit slot on the device.",
        "3. Run exactly one device/anchor command below and review every printed field and MIDI packet.",
        "4. Authorize output with the feature-specific confirmation flag already shown.",
        "5. Save the active kit and initiate its current-kit SysEx dump when prompted.",
        "6. Validate the captured target passively before treating it as final.",
        "",
    ]
    for entry in entries:
        spec_path = f"specs/rush16/{entry.spec_filename}"
        capture_path = (
            "output/local/RUSH16_ANCHOR_AUDITION_001/captured_kit_targets/"
            f"{entry.target_filename}"
        )
        target_label = entry.target_filename.removesuffix(".syx")
        lines.extend(
            [
                f"### {entry.anchor_id} {entry.device.upper()}",
                "",
                f"Current status: `blocked` ({len(entry.hardware_blockers)} critical apply blockers).",
                "",
                "```powershell",
                ".\\.venv\\Scripts\\python.exe -m rytm_randomizer.app --arm "
                f"--rush01-apply-plan --rush01-device {entry.device} "
                f'--rush01-config "{config_path}" --rush01-spec "{spec_path}" '
                f'--rush01-disposable-target "{target_label}" '
                f'--rush01-capture-output "{capture_path}" '
                "--confirm-rush01-midi-send",
                "```",
                "",
            ]
        )
    lines.extend(
        [
            "## Audition Recording",
            "",
            "Record Rytm dry, A4 dry, and combined dry for each anchor using one unchanged OXI pattern, tempo, root, velocity profile, note-length profile, and gain stage. The Octatrack is routing/recording only.",
            "",
        ]
    )
    return "\n".join(lines)


__all__ = [
    "build_rush16_family_manifest",
    "build_rush16_matrix",
    "build_rush16_recording_manifest",
    "build_rush16_validation",
    "format_rush16_build_report",
    "format_rush16_operator_runbook",
    "rush16_build_entry_to_dict",
]
