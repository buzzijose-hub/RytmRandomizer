"""Generate the passive RUSH16 anchor audition batch without hardware access."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from hashlib import sha256
from pathlib import Path
from typing import Final, TextIO

import yaml

PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:  # pragma: no cover - standalone bootstrap
    sys.path.insert(0, str(PROJECT_ROOT))

from rytm_randomizer.data.rush16 import RUSH16_ANCHORS, RUSH16_BATCH_ID  # noqa: E402
from rytm_randomizer.devices.strategies import (  # noqa: E402
    ANALOG_FOUR_KIT_CODEC,
    ANALOG_RYTM_KIT_CODEC,
)
from rytm_randomizer.reports.rush16_anchor_audition import (  # noqa: E402
    build_rush16_family_manifest,
    build_rush16_matrix,
    build_rush16_recording_manifest,
    build_rush16_validation,
    format_rush16_build_report,
    format_rush16_operator_runbook,
)
from rytm_randomizer.style_analysis.rush01_midi_compiler import (  # noqa: E402
    RUSH01_DEVICE_A4,
    RUSH01_DEVICE_RYTM,
    Rush01DeviceConfig,
    compile_rush01_midi_plan,
    parse_rush01_device_config,
    rush01_midi_plan_to_dict,
)
from rytm_randomizer.style_analysis.rush01_sysex_calibration import (  # noqa: E402
    build_rush01_sysex_calibration,
)
from rytm_randomizer.style_analysis.rush16_anchor_audition import (  # noqa: E402
    Rush16BuildEntry,
    build_rush16_build_entry,
    build_rush16_spec_documents,
    rush16_spec_filename,
)
from rytm_randomizer.style_analysis.rush16_apply_calibration import (  # noqa: E402
    apply_rush16_calibration_promotions,
    build_rush16_calibration_catalog,
)

_SOURCE_SPECS: Final[Mapping[str, str]] = {
    RUSH01_DEVICE_RYTM: "specs/RUSH01_RYTM.yaml",
    RUSH01_DEVICE_A4: "specs/RUSH01_A4.yaml",
}
_BASELINE_STATUS: Final[Mapping[str, str]] = {
    RUSH01_DEVICE_RYTM: "output/RUSH01_RYTM_mapping_status.json",
    RUSH01_DEVICE_A4: "output/RUSH01_A4_mapping_status.json",
}
_REFERENCE: Final[Mapping[str, str]] = {
    RUSH01_DEVICE_RYTM: "reference/RYTM_Test1_Init_Kit.syx",
    RUSH01_DEVICE_A4: "reference/A4_Test1_Init_Kit.syx",
}
_MAPPING_GAPS: Final[str] = "output/RUSH01_mapping_gaps.md"
_SPEC_ROOT: Final[str] = "specs/rush16"
_DEFAULT_CONFIG: Final[str] = "config/rush01_midi_channels.yaml"
_LOCAL_ROOT: Final[str] = f"output/local/{RUSH16_BATCH_ID}"
_LOCAL_DIRECTORIES: Final[tuple[str, ...]] = (
    "calibration",
    "captured_dumps",
    "final_sysex",
    "hardware_receipts",
    "recording_runbook",
    "session_checkpoints",
    "semantic_specs",
    "direct_sysex",
    "hardware_apply_plans",
    "captured_kit_targets",
    "validation",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the passive batch parser."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path(_DEFAULT_CONFIG),
        help="Optional exact local port/channel config; missing values remain unconfigured.",
    )
    parser.add_argument(
        "--sync-specs",
        action="store_true",
        help="Regenerate the nine tracked semantic specs before building local artifacts.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Compare specs and local artifacts byte-for-byte without writing.",
    )
    return parser


def run(
    argv: Sequence[str],
    *,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Generate or check the complete passive batch."""

    args = build_parser().parse_args(tuple(argv))
    project_root = args.project_root.resolve()
    config_path = args.config
    if not config_path.is_absolute():
        config_path = project_root / config_path
    try:
        spec_artifacts = _expected_spec_artifacts(project_root)
        spec_mismatches = _compare_artifacts(project_root, spec_artifacts)
        if args.check and spec_mismatches:
            _write_mismatches(stderr, "RUSH16 semantic specs are stale or missing", spec_mismatches)
            return 1
        if args.sync_specs and not args.check:
            _write_artifacts(project_root, spec_artifacts)
        elif spec_mismatches:
            stderr.write("RUSH16 semantic specs are missing or stale; rerun with --sync-specs.\n")
            return 2

        local_artifacts, directories, entries = _expected_local_artifacts(
            project_root,
            config_path=config_path,
            spec_artifacts=spec_artifacts,
        )
        if args.check:
            local_mismatches = _compare_artifacts(project_root, local_artifacts)
            if local_mismatches:
                _write_mismatches(
                    stderr, "RUSH16 local build artifacts are stale or missing", local_mismatches
                )
                return 1
        else:
            for relative_directory in directories:
                (project_root / relative_directory).mkdir(parents=True, exist_ok=True)
            _write_artifacts(project_root, local_artifacts)
    except (OSError, TypeError, ValueError, KeyError, json.JSONDecodeError, yaml.YAMLError) as exc:
        stderr.write(f"RUSH16 anchor audition build failed: {exc}\n")
        return 2

    blocked = sum(bool(entry.hardware_blockers) for entry in entries)
    mode = "checked" if args.check else "generated"
    stdout.write(
        f"RUSH16 anchor audition batch {mode}: {len(entries)} device artifacts; "
        f"{blocked} blocked; 0 final SysEx files.\n"
    )
    stdout.write("MIDI backend opened: false\n")
    stdout.write("MIDI port opened: false\n")
    stdout.write("MIDI or SysEx transmitted: false\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""

    return run(
        tuple(sys.argv[1:] if argv is None else argv),
        stdout=sys.stdout,
        stderr=sys.stderr,
    )


def _expected_spec_artifacts(project_root: Path) -> Mapping[str, bytes]:
    source_documents = {
        device: _read_yaml(project_root / relative_path)
        for device, relative_path in _SOURCE_SPECS.items()
    }
    source_hashes = {
        relative_path: sha256(_read_bytes(project_root / relative_path)).hexdigest()
        for relative_path in _SOURCE_SPECS.values()
    }
    baseline_statuses = {
        device: _read_json(project_root / relative_path)
        for device, relative_path in _BASELINE_STATUS.items()
    }
    documents = build_rush16_spec_documents(
        source_documents[RUSH01_DEVICE_RYTM],
        source_documents[RUSH01_DEVICE_A4],
        source_hashes=source_hashes,
        baseline_mapping_statuses=baseline_statuses,
    )
    return {
        f"{_SPEC_ROOT}/{filename}": _yaml_bytes(document)
        for filename, document in documents.items()
    }


def _expected_local_artifacts(
    project_root: Path,
    *,
    config_path: Path,
    spec_artifacts: Mapping[str, bytes],
) -> tuple[Mapping[str, bytes], tuple[str, ...], tuple[Rush16BuildEntry, ...]]:
    mapping_gaps = _read_text(project_root / _MAPPING_GAPS)
    config_document = _read_yaml(config_path) if config_path.is_file() else None
    references = {device: _read_bytes(project_root / path) for device, path in _REFERENCE.items()}
    entries: list[Rush16BuildEntry] = []
    plans: dict[str, dict[str, object]] = {}
    validations: dict[str, dict[str, object]] = {}
    semantic_copies: dict[str, bytes] = {}
    spec_documents: dict[str, object] = {}
    checkpoints = {
        device: _read_json(path)
        for device in (RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4)
        if (
            path := project_root / _LOCAL_ROOT / "session_checkpoints" / f"{device}.checkpoint.json"
        ).is_file()
    }
    for anchor in RUSH16_ANCHORS:
        for device in (RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4):
            filename = rush16_spec_filename(anchor.anchor_id, device)
            relative_spec_path = f"{_SPEC_ROOT}/{filename}"
            spec_bytes = spec_artifacts[relative_spec_path]
            spec = yaml.safe_load(spec_bytes.decode("utf-8"))
            config = _device_config_or_none(config_document, device)
            plan = compile_rush01_midi_plan(device, spec, config=config)
            if device in checkpoints:
                plan = apply_rush16_calibration_promotions(
                    plan,
                    spec_filename=filename,
                    checkpoint=checkpoints[device],
                )
            codec = ANALOG_RYTM_KIT_CODEC if device == RUSH01_DEVICE_RYTM else ANALOG_FOUR_KIT_CODEC
            sysex_status = build_rush01_sysex_calibration(
                device,
                spec,
                mapping_gaps_text=mapping_gaps,
                reference_frame=references[device],
                codec=codec,
            )
            capture_configured = _capture_input_configured(config_document, device)
            entry = build_rush16_build_entry(
                anchor_id=anchor.anchor_id,
                device=device,
                spec_filename=filename,
                spec_bytes=spec_bytes,
                spec=spec,
                plan=plan,
                sysex_status=sysex_status,
                hardware_capture_configured=capture_configured,
            )
            entries.append(entry)
            stem = filename.removesuffix(".yaml")
            plans[stem] = {
                "batch_id": RUSH16_BATCH_ID,
                "anchor_id": anchor.anchor_id,
                "device": device,
                "semantic_spec": relative_spec_path,
                "application_blocked": not entry.hardware_apply_ready,
                "hardware_blockers": list(entry.hardware_blockers),
                "capture_input_configured": capture_configured,
                "rush01_plan": rush01_midi_plan_to_dict(plan),
            }
            validations[stem] = build_rush16_validation(entry)
            semantic_copies[filename] = spec_bytes
            spec_documents[filename] = spec

    entry_tuple = tuple(entries)
    family_spec = spec_artifacts[f"{_SPEC_ROOT}/RUSH16_FAMILY.yaml"]
    calibration_catalogs = {
        device: build_rush16_calibration_catalog(device, spec_documents)
        for device in (RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4)
    }
    local_artifacts: dict[str, bytes] = {
        f"{_LOCAL_ROOT}/BUILD_MATRIX.json": _json_bytes(build_rush16_matrix(entry_tuple)),
        f"{_LOCAL_ROOT}/BUILD_REPORT.md": format_rush16_build_report(entry_tuple).encode("utf-8"),
        f"{_LOCAL_ROOT}/OPERATOR_RUNBOOK.md": format_rush16_operator_runbook(
            entry_tuple,
            config_path=_display_path(config_path, project_root),
        ).encode("utf-8"),
        f"{_LOCAL_ROOT}/RECORDING_MANIFEST.json": _json_bytes(
            build_rush16_recording_manifest(entry_tuple)
        ),
        f"{_LOCAL_ROOT}/RUSH16_FAMILY_MANIFEST.json": _json_bytes(
            build_rush16_family_manifest(
                entry_tuple,
                family_spec_sha256=sha256(family_spec).hexdigest(),
            )
        ),
        f"{_LOCAL_ROOT}/calibration/RUSH16_RYTM_CALIBRATION_CATALOG.json": _json_bytes(
            calibration_catalogs[RUSH01_DEVICE_RYTM]
        ),
        f"{_LOCAL_ROOT}/calibration/RUSH16_A4_CALIBRATION_CATALOG.json": _json_bytes(
            calibration_catalogs[RUSH01_DEVICE_A4]
        ),
        f"{_LOCAL_ROOT}/calibration/RUSH16_CALIBRATION_RUNBOOK.md": (
            _format_calibration_runbook(
                config_path=_display_path(config_path, project_root),
                catalogs=calibration_catalogs,
            ).encode("utf-8")
        ),
    }
    if all(entry.final_sysex_generated for entry in entry_tuple):
        local_artifacts[f"{_LOCAL_ROOT}/recording_runbook/RUSH16_RECORDING_RUNBOOK.md"] = (
            _format_recording_runbook().encode("utf-8")
        )
    for filename, content in semantic_copies.items():
        local_artifacts[f"{_LOCAL_ROOT}/semantic_specs/{filename}"] = content
    local_artifacts[f"{_LOCAL_ROOT}/semantic_specs/RUSH16_FAMILY.yaml"] = family_spec
    for stem, plan in plans.items():
        local_artifacts[f"{_LOCAL_ROOT}/hardware_apply_plans/{stem}.plan.json"] = _json_bytes(plan)
    for stem, validation in validations.items():
        local_artifacts[f"{_LOCAL_ROOT}/validation/{stem}.validation.json"] = _json_bytes(
            validation
        )
    directories = tuple(f"{_LOCAL_ROOT}/{name}" for name in _LOCAL_DIRECTORIES)
    return local_artifacts, directories, entry_tuple


def _format_calibration_runbook(
    *,
    config_path: str,
    catalogs: Mapping[str, Mapping[str, object]],
) -> str:
    root = _LOCAL_ROOT
    lines = [
        "# RUSH16 Apply-Calibration Runbook",
        "",
        "Configure exact input/output port names and track channels in "
        f"`{config_path}`. No port or channel is inferred. Load a disposable initialized active "
        "KIT; do not enter any sound parameter manually.",
        "",
        "## Guarded Commands",
        "",
        "Run the applicable command repeatedly. Each invocation previews one candidate and resumes "
        "from its checkpoint. A4 display-discovery steps open the exact output only, require no KIT "
        "save, and capture no SysEx input. Only useful target certification and affine cross-route "
        "confirmation steps capture baseline/changed KIT dumps and require a manual disposable-KIT "
        "save. Rytm keeps the exhaustive saved-KIT evidence workflow.",
        "",
        "```powershell",
        "python -m rytm_randomizer.app --arm --rush16-calibrate --rush01-device rytm "
        f"--rush01-config {config_path} --rush01-disposable-target RUSH16_RYTM_CALIBRATION_INIT "
        "--rush16-hardware-unit RYTM_MKII_UNIT --confirm-rush16-calibration-send "
        f"--rush16-session-root {root}",
        "python -m rytm_randomizer.app --arm --rush16-calibrate --rush01-device a4 "
        f"--rush01-config {config_path} --rush01-disposable-target RUSH16_A4_CALIBRATION_INIT "
        "--rush16-hardware-unit A4_MKII_UNIT --confirm-rush16-calibration-send "
        f"--rush16-session-root {root}",
        "```",
        "",
        "Allowed operator actions are connection, disposable-KIT loading, armed authorization, "
        "display reporting, active-KIT save/dump initiation, and listening approval. The changed KIT "
        "must be saved before its dump is initiated. The app sends "
        "machine context before machine-specific source candidates and closes each port after its "
        "single operation.",
        "",
        "## Anchor Apply And Hardware-Return Capture",
        "",
        "Run these only after the corresponding four build-matrix blocker counts are zero. Captures "
        "remain candidates under `captured_dumps/`; validation, not capture, controls promotion to "
        "`final_sysex/`.",
        "",
        "```powershell",
    ]
    for anchor in RUSH16_ANCHORS:
        for device, suffix in ((RUSH01_DEVICE_RYTM, "RYTM"), (RUSH01_DEVICE_A4, "A4")):
            filename = f"{anchor.anchor_id}_{suffix}"
            lines.append(
                "python -m rytm_randomizer.app --arm --rush01-apply-plan "
                f"--rush01-device {device} --rush01-config {config_path} "
                f"--rush01-spec specs/rush16/{filename}.yaml "
                f"--rush01-disposable-target {filename}_ACTIVE_INIT "
                f"--rush16-checkpoint {root}/session_checkpoints/{device}.checkpoint.json "
                f"--rush01-capture-output {root}/captured_dumps/{filename}.syx "
                "--confirm-rush01-midi-send"
            )
    lines.extend(("```", "", "## Family Counts", ""))
    for device in (RUSH01_DEVICE_RYTM, RUSH01_DEVICE_A4):
        catalog = catalogs[device]
        families = catalog.get("families")
        if not isinstance(families, Sequence):
            raise ValueError("RUSH16 calibration catalog families must be a sequence")
        supported = sum(
            isinstance(family, Mapping)
            and bool(family.get("supported"))
            and bool(family.get("targets"))
            for family in families
        )
        unsupported = [
            str(family.get("label"))
            for family in families
            if isinstance(family, Mapping) and not family.get("supported")
        ]
        lines.append(
            f"- {device}: {supported} supported families; "
            f"{catalog.get('required_observations')} deterministic candidate ceiling "
            "(adaptive A4 scheduling normally stops earlier); "
            f"initial blockers {catalog.get('blocker_counts_before')}."
        )
        for label in unsupported:
            lines.append(
                f"- {device} unsupported: {label}; authoritative MIDI-address evidence is required "
                "before any packet can be generated."
            )
    lines.extend(
        [
            "",
            "Filter 2 Resonance reuses PR #214 hardware evidence when integrated and is not "
            "recalibrated. `final_sysex/` remains empty until a hardware-return KIT passes every "
            "final validation check.",
            "",
        ]
    )
    return "\n".join(lines)


def _format_recording_runbook() -> str:
    anchors = tuple(anchor.anchor_id for anchor in RUSH16_ANCHORS)
    lines = [
        "# RUSH16 Anchor Recording Runbook",
        "",
        "Start only after all eight hardware-return KIT files pass final validation.",
        "",
        "## Locked Session",
        "",
        "- Tempo: 145 BPM.",
        "- Use one unchanged OXI sequence for every take.",
        "- Lock one root note before take 1 and keep it unchanged.",
        "- Keep velocities, note lengths, and swing unchanged.",
        "- Keep Octatrack input gains unchanged.",
        "- Octatrack is routing/recording only: no transition FX and no master coloration.",
        "",
        "## Twelve Stems",
        "",
    ]
    for anchor in anchors:
        lines.extend(
            (
                f"- {anchor} - Rytm dry",
                f"- {anchor} - A4 dry",
                f"- {anchor} - combined dry",
            )
        )
    lines.extend(
        [
            "",
            "Record the three stems for an anchor without changing the locked session, then listen "
            "and approve before advancing to the next anchor.",
            "",
        ]
    )
    return "\n".join(lines)


def _capture_input_configured(config: object, device: str) -> bool:
    if config is None:
        return False
    root = config if isinstance(config, Mapping) else {}
    section = root.get(device)
    if not isinstance(section, Mapping):
        return False
    input_port = section.get("input_port")
    return (
        isinstance(input_port, str) and bool(input_port.strip()) and not _is_placeholder(input_port)
    )


def _device_config_or_none(config: object, device: str) -> Rush01DeviceConfig | None:
    if config is None:
        return None
    if _device_config_has_placeholders(config, device):
        return None
    return parse_rush01_device_config(config, device)


def _device_config_has_placeholders(config: object, device: str) -> bool:
    if not isinstance(config, Mapping):
        return False
    section = config.get(device)
    if not isinstance(section, Mapping):
        return False
    output_port = section.get("output_port")
    if isinstance(output_port, str) and _is_placeholder(output_port):
        return True
    tracks = section.get("tracks")
    if not isinstance(tracks, Mapping):
        return False
    return any(isinstance(value, str) and _is_placeholder(value) for value in tracks.values())


def _is_placeholder(value: str) -> bool:
    normalized = value.strip().lower()
    return (
        not normalized
        or normalized.startswith("<")
        or "replace" in normalized
        or "configure" in normalized
        or normalized in {"todo", "null", "none", "unconfigured"}
    )


def _display_path(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _compare_artifacts(project_root: Path, artifacts: Mapping[str, bytes]) -> tuple[str, ...]:
    return tuple(
        relative_path
        for relative_path, expected in artifacts.items()
        if not (project_root / relative_path).is_file()
        or (project_root / relative_path).read_bytes() != expected
    )


def _write_artifacts(project_root: Path, artifacts: Mapping[str, bytes]) -> None:
    for relative_path, content in artifacts.items():
        path = project_root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _write_mismatches(stderr: TextIO, heading: str, paths: Sequence[str]) -> None:
    stderr.write(f"{heading}:\n")
    stderr.write("".join(f"- {path}\n" for path in paths))


def _read_yaml(path: Path) -> object:
    return yaml.safe_load(_read_text(path))


def _read_json(path: Path) -> object:
    return json.loads(_read_text(path))


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise ValueError(f"required file does not exist: {path}")
    return path.read_text(encoding="utf-8")


def _read_bytes(path: Path) -> bytes:
    if not path.is_file():
        raise ValueError(f"required file does not exist: {path}")
    return path.read_bytes()


def _yaml_bytes(document: object) -> bytes:
    return yaml.safe_dump(
        document,
        sort_keys=False,
        allow_unicode=False,
        width=100,
    ).encode("utf-8")


def _json_bytes(document: object) -> bytes:
    return (json.dumps(document, indent=2, sort_keys=True) + "\n").encode("utf-8")


if __name__ == "__main__":  # pragma: no cover - direct CLI boundary
    raise SystemExit(main())
