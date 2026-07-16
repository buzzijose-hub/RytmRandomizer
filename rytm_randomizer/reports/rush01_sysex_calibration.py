"""Operator-facing reports for passive RUSH01 saved-kit calibration."""

from __future__ import annotations

from collections import Counter
from typing import Final

from ..style_analysis.rush01_sysex_calibration import (
    FIELD_STATUS_CANDIDATE_ONLY,
    FIELD_STATUS_CAPTURE_REQUIRED,
    Rush01SysexByteChange,
    Rush01SysexCalibrationField,
    Rush01SysexCalibrationStatus,
    Rush01SysexCaptureDiff,
)

_NO_COMMAND: Final[str] = "front panel only; no raw MIDI command emitted"
_CALIBRATION_CAPTURE_CALL: Final[str] = (
    "MidoMidiPortProvider.capture_sysex_messages(exact_input_port, "
    "timeout_seconds=<OPERATOR_TIMEOUT_SECONDS>)"
)


def format_rush01_capture_matrix(status: Rush01SysexCalibrationStatus) -> str:
    """Render one device's minimal saved-kit operator capture matrix."""

    counts = Counter(field.status for field in status.fields if field.critical)
    unresolved = tuple(
        field
        for field in status.fields
        if field.critical
        and field.status in {FIELD_STATUS_CAPTURE_REQUIRED, FIELD_STATUS_CANDIDATE_ONLY}
    )
    capture_count = sum(len(field.capture_targets) for field in unresolved)
    lines = [
        f"# {status.device_model} RUSH01 Saved-Kit Capture Matrix",
        "",
        "This is a calibration workbench, not the final delivery path. Do not run the",
        "operator commands during the coding phase. Each future capture changes exactly",
        "one semantic parameter and exports one saved/current KIT dump.",
        "",
        "## Status",
        "",
        f"- Reference: `{status.reference.filename}`",
        f"- Reference round trip byte-identical: `{str(status.reference.byte_identical).lower()}`",
        f"- Critical fields: `{sum(field.critical for field in status.fields)}`",
        f"- Mapped: `{counts['mapped']}`",
        f"- Preserve reference: `{counts['preserve_reference']}`",
        f"- Capture required: `{counts['capture_required']}`",
        f"- Candidate only: `{counts['candidate_only']}`",
        f"- Unresolved critical fields: `{len(unresolved)}`",
        f"- Minimal changed-dump captures: `{capture_count}`",
        f"- Supplied differential dumps decoded in this run: `{len(status.capture_diffs)}`",
        f"- Writer ready: `{str(status.writer_ready).lower()}`",
        "",
        "## Reused Components",
        "",
        "- Rytm one-control mutation: `python -m rytm_randomizer.app --arm --validate-one-cc`; this calls `rytm_randomizer.midi_io.send_cc`.",
        "- A4 one-parameter mutation: `--a4-send-param` or `--a4-send-nrpn-param`; these call `rytm_randomizer.midi_io.send_cc` / `send_nrpn`.",
        "- Existing generic plan sender: `rytm_randomizer.senders.midi_event_plan.send_cc_nrpn_event_plan`.",
        f"- Current-kit receive API: `{_CALIBRATION_CAPTURE_CALL}`.",
        "- Existing live receiver wrapper: `rytm_randomizer.app._capture_rytm_snapshot_shell_anchor_from_live_input`.",
        "- File framing/decoding: `snapshot.sysex_file.extract_sysex_payloads` plus the reference-bound Elektron kit codec.",
        "",
        "The receiver currently decodes live Rytm frames in memory; it does not persist a",
        "capture filename. For calibration, call the existing receiver API directly and write",
        "the returned complete frame to the exact matrix filename. No second transport is needed.",
        "",
        "## Operator Protocol",
        "",
        "1. Restore the approved initialized kit represented by the reference dump.",
        "2. Change only the listed semantic parameter, using the existing command when one is supplied; otherwise use the front panel.",
        "3. Export only the current/saved KIT to the exact changed-dump filename.",
        "4. Restore the baseline before the next observation.",
        "5. Do not promote a location from one track. A second-track witness is mandatory.",
        "6. Do not derive signed, bipolar, enum, boolean, or high-resolution conversion from a single observation.",
        *(
            [
                "7. For Rytm LT, MT, and HT source captures, manually select XT Classic before changing any source parameter."
            ]
            if status.device == "rytm"
            else []
        ),
        "",
        "## Capture Groups",
        "",
    ]
    groups: dict[str, list[Rush01SysexCalibrationField]] = {}
    for field in unresolved:
        groups.setdefault(field.capture_group, []).append(field)
    for group_name, group_fields in groups.items():
        lines.extend(_capture_group_lines(group_name, tuple(group_fields)))

    lines.extend(
        [
            "## Supplied Differential Results",
            "",
        ]
    )
    if status.capture_diffs:
        for capture_diff in status.capture_diffs:
            lines.extend(_capture_diff_lines(capture_diff))
    else:
        lines.extend(
            [
                "No differential KIT dump is present under the planned calibration paths.",
                "No offset, stride, converter, or mapping was promoted by this run.",
                "",
            ]
        )
    lines.extend(
        [
            "## Safety",
            "",
            *[f"- {line}" for line in status.safety],
            "",
        ]
    )
    return "\n".join(lines)


def format_rush01_sysex_calibration_report(
    rytm: Rush01SysexCalibrationStatus,
    a4: Rush01SysexCalibrationStatus,
) -> str:
    """Render the combined saved-kit calibration phase report."""

    lines = [
        "# RUSH01 Saved-Kit SysEx Calibration Report",
        "",
        "## Objective",
        "",
        "The final products remain offline Elektron KIT SysEx files:",
        "",
        "- `output/RUSH01_RYTM.syx`",
        "- `output/RUSH01_A4.syx`",
        "",
        "Neither file is generated in this phase because both devices still have unresolved",
        "critical saved-kit mappings. The device-assisted MIDI compiler is retained only as",
        "semantic enumeration and calibration support.",
        "",
        "## Readiness",
        "",
        "| Device | Critical | Mapped | Preserve | Capture required | Candidate only | Unresolved | Writer ready |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
        _readiness_row(rytm),
        _readiness_row(a4),
        "",
        "## Reference Round Trips",
        "",
        "| Device | Reference | Bytes | SHA-256 | Header | Packed | Unpacked | Result |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | --- |",
        _round_trip_row(rytm),
        _round_trip_row(a4),
        "",
        "Both codecs start from the approved reference frame, preserve the complete header and",
        "unknown object bytes, and recalculate packing, checksum, and encoded length. No blank",
        "or invented kit object is used.",
        "",
        "## Current Evidence",
        "",
        f"- Rytm supplied differential dumps: `{len(rytm.capture_diffs)}`.",
        f"- A4 supplied differential dumps: `{len(a4.capture_diffs)}`.",
        "- New mappings promoted by this run: `0`.",
        "- Existing A4 candidate calibration fixtures are serialized for Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency; they remain writer-blocking.",
        "- The Rytm `+162` sound-record layout and A4 `+350` unpacked / `+400` packed track strides are candidate inputs for unresolved fields, not automatic promotions.",
        "",
        "## Gap Report Reconciliation",
        "",
        "The workbench reads `output/RUSH01_mapping_gaps.md` and compiles current semantic paths",
        "from the corrected YAML specifications. Stale gap aliases are retained as audit data but",
        "are not reintroduced into the capture plan.",
        "",
        f"- Rytm superseded paths: {_inline_paths(rytm.superseded_mapping_gap_paths)}",
        f"- A4 superseded paths: {_inline_paths(a4.superseded_mapping_gap_paths)}",
        "",
        "This excludes the obsolete `SNP`, `PW1`, and `PW2` rows from current Rytm work while",
        "keeping the corrected typed `Snap Type: preserve_reference` request visible.",
        "",
        "## Existing Components To Call Directly",
        "",
        "- `rytm_randomizer.midi_io.send_cc` and `send_nrpn`: canonical V1.34 mutation primitives.",
        "- `rytm_randomizer.senders.midi_event_plan.send_cc_nrpn_event_plan`: canonical ordered CC/NRPN plan sender.",
        "- `rytm_randomizer.app --arm --validate-one-cc`: existing one-CC Rytm operator command.",
        "- `rytm_randomizer.app --arm --a4-send-param` and `--a4-send-nrpn-param`: existing one-parameter A4 commands.",
        "- `rytm_randomizer.mido_provider.MidoMidiPortProvider.capture_sysex_messages`: current raw SysEx receiver.",
        "- `rytm_randomizer.app._capture_rytm_snapshot_shell_anchor_from_live_input`: current-kit receive/decode wrapper used by the snapshot shell.",
        "- `rytm_randomizer.snapshot.sysex_file.extract_sysex_payloads`: complete-frame extraction.",
        "- `ANALOG_RYTM_KIT_CODEC` and `ANALOG_FOUR_KIT_CODEC`: saved-kit validation, unpacking, packing, checksum, and length.",
        "",
        "## Duplicate Device-Assisted Code Classification",
        "",
        "Retain the following as calibration support; do not extend it into the final delivery path:",
        "",
        "- `rytm_randomizer/senders/rush01_midi_transport.py`: `open_exact_output` and byte-plan replay overlap the established provider/app port boundary and `midi_io.send_cc` sender path.",
        "- `tools/rush01_midi_apply.py`: duplicates a general apply/list-port command surface already represented by the V1.34 app handlers.",
        "- `rytm_randomizer/style_analysis/rush01_midi_compiler.py`: useful for semantic ordering, catalog validation, typed transport values, and one-parameter capture planning only.",
        "- `tools/rush01_midi_learn.py` and `state/midi_observation.py`: useful for input-side calibration observations only.",
        "",
        "No module above is called by the offline saved-kit writer planned for final delivery.",
        "",
        "## Promotion Rules",
        "",
        "- One changed parameter per dump; unexplained changed bytes block promotion.",
        "- Multiple observations are mandatory for signed, bipolar, enum, boolean, and high-resolution fields.",
        "- A track stride is never promoted from one track; a second distinct track is mandatory.",
        "- Existing candidate offsets remain candidate-only until source dumps and writer round-trip fixtures are present.",
        "- Every promoted mapping must have a committed unit-test fixture.",
        "- Final `.syx` generation remains disabled until unresolved critical count is zero for that device.",
        "",
        "## Hardware Safety",
        "",
        "- No MIDI backend was imported or opened while generating this report.",
        "- No MIDI port was opened.",
        "- No MIDI data or SysEx was transmitted.",
        "- No Elektron device was accessed.",
        "- No `--apply` command was run.",
        "",
    ]
    return "\n".join(lines)


def _capture_group_lines(
    group_name: str,
    fields: tuple[Rush01SysexCalibrationField, ...],
) -> list[str]:
    lines = [
        f"### `{group_name}`",
        "",
        "| Semantic path | Track | Converter | Required front-panel / raw MIDI values | Baseline | Changed dump filenames | Captures | Candidate location | Evidence for promotion |",
        "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
    ]
    for field in fields:
        values = _capture_values(field)
        filenames = "<br>".join(f"`{target.filename}`" for target in field.capture_targets)
        if not filenames and field.shared_capture_group_owner is not None:
            filenames = f"shared with `{field.shared_capture_group_owner}`"
        evidence = "<br>".join(field.evidence_needed)
        lines.append(
            "| "
            f"`{field.semantic_path}` | {field.track or '-'} | `{field.converter_family}` | "
            f"{values} | `{_baseline(field)}` | {filenames or '-'} | "
            f"{len(field.capture_targets)} | {_candidate_location(field)} | {evidence} |"
        )
    lines.extend(["", "Commands:", ""])
    commands_added = False
    for field in fields:
        for target in field.capture_targets:
            command = target.mutation_command or _NO_COMMAND
            lines.append(f"- `{field.semantic_path}` / `{target.observation_label}`: {command}")
            commands_added = True
    if not commands_added:
        lines.append("- No additional command; this group reuses its listed owner captures.")
    lines.extend(
        ["", "Capture API after each mutation:", "", f"- `{_CALIBRATION_CAPTURE_CALL}`", ""]
    )
    return lines


def _capture_values(field: Rush01SysexCalibrationField) -> str:
    if not field.capture_targets:
        return f"reuse `{field.shared_capture_group_owner}` converter/stride evidence"
    return "<br>".join(
        f"{target.front_panel_value} / raw "
        f"{target.raw_midi_value if target.raw_midi_value is not None else 'unknown'}"
        for target in field.capture_targets
    )


def _candidate_location(field: Rush01SysexCalibrationField) -> str:
    parts: list[str] = []
    if field.candidate_unpacked_offset is not None:
        parts.append(f"unpacked `0x{field.candidate_unpacked_offset:04X}`")
    if field.candidate_packed_data_offset is not None:
        parts.append(f"packed `0x{field.candidate_packed_data_offset:04X}`")
    if field.candidate_unpacked_stride is not None:
        parts.append(f"unpacked stride `{field.candidate_unpacked_stride}`")
    if field.candidate_packed_stride is not None:
        parts.append(f"packed stride `{field.candidate_packed_stride}`")
    if not parts:
        return "unknown"
    return "; ".join(parts) + "; not promoted for this field"


def _capture_diff_lines(capture_diff: Rush01SysexCaptureDiff) -> list[str]:
    lines = [
        f"### `{capture_diff.source_file}`",
        "",
        f"- Valid saved-kit frame: `{str(capture_diff.valid).lower()}`",
        f"- Semantic path: `{capture_diff.semantic_path or 'unassigned'}`",
        f"- Track: `{capture_diff.track or 'unassigned'}`",
        f"- Observation: `{capture_diff.observation_value or 'unassigned'}`",
        f"- SHA-256: `{capture_diff.sha256}`",
    ]
    if not capture_diff.valid:
        lines.extend([f"- Error: `{capture_diff.error}`", ""])
        return lines
    lines.extend(
        [
            f"- Header changes: {_changes(capture_diff.header_changes)}",
            f"- Packed payload changes: {_changes(capture_diff.packed_changes)}",
            f"- Unpacked object changes: {_changes(capture_diff.unpacked_changes)}",
            f"- Integrity changes: {_changes(capture_diff.integrity_changes)}",
            "",
        ]
    )
    return lines


def _changes(changes: tuple[Rush01SysexByteChange, ...]) -> str:
    if not changes:
        return "none"
    return ", ".join(
        f"offset 0x{change.offset:04X}"
        + (f" / frame 0x{change.frame_offset:04X}" if change.frame_offset is not None else "")
        + f" 0x{change.before:02X}->0x{change.after:02X}"
        for change in changes
    )


def _readiness_row(status: Rush01SysexCalibrationStatus) -> str:
    counts = Counter(field.status for field in status.fields if field.critical)
    critical = sum(field.critical for field in status.fields)
    unresolved = counts[FIELD_STATUS_CAPTURE_REQUIRED] + counts[FIELD_STATUS_CANDIDATE_ONLY]
    return (
        f"| {status.device_model} | {critical} | {counts['mapped']} | "
        f"{counts['preserve_reference']} | {counts['capture_required']} | "
        f"{counts['candidate_only']} | {unresolved} | {status.writer_ready} |"
    )


def _round_trip_row(status: Rush01SysexCalibrationStatus) -> str:
    reference = status.reference
    result = "PASS, byte-identical" if reference.byte_identical else "FAIL"
    return (
        f"| {status.device_model} | `{reference.filename}` | {reference.byte_count} | "
        f"`{reference.sha256}` | {reference.header_bytes} | {reference.packed_bytes} | "
        f"{reference.unpacked_bytes} | **{result}** |"
    )


def _inline_paths(paths: tuple[str, ...]) -> str:
    return ", ".join(f"`{path}`" for path in paths) if paths else "none"


def _baseline(field: Rush01SysexCalibrationField) -> str:
    return (
        "reference/RYTM_Test1_Init_Kit.syx"
        if field.device == "rytm"
        else "reference/A4_Test1_Init_Kit.syx"
    )


__all__ = [
    "format_rush01_capture_matrix",
    "format_rush01_sysex_calibration_report",
]
