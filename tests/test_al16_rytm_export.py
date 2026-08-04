from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from pathlib import Path
from types import MappingProxyType
from typing import Never, cast

import pytest
from pytest import MonkeyPatch

from conftest import ANALOG_RYTM_SAVED_KIT_TEST_HEADER
from rytm_randomizer.cockpit.export import al16_rytm_kit as exporter
from rytm_randomizer.cockpit.export.al16_rytm_kit import (
    Al16BuildError,
    Al16BuildResult,
    Al16BuildStatus,
    build_al16_rytm_kit,
    deterministic_recipe_identifier,
)
from rytm_randomizer.cockpit.export.file_export_contracts import (
    LocalFileExportErrorCode,
    LocalFileExportPhase,
    attach_local_file_export_error_context,
    classify_local_file_export_error,
    local_file_export_error_context,
)
from rytm_randomizer.cockpit.export.writer import (
    WriteSetError,
    WriteSetFailureContext,
)
from rytm_randomizer.data.al16_rytm import (
    AL16_BANK_STATES,
    AL16_PAD_ROLES,
    AL16_TRACK_MODE_PRESERVE,
    RYTM_CONVERTER_CENTERED_7BIT,
    RYTM_CONVERTER_FILTER_TYPE_ENUM,
    RYTM_CONVERTER_VERIFIED_7BIT,
    RytmValueConverter,
    al16_bank_spec_payload,
    render_al16_bank_spec,
)
from rytm_randomizer.data.analog_rytm_kit_layout import (
    RYTM_KIT_RAW_SIZE,
    RYTM_SOUND_MACHINE_TYPE_OFFSET,
)
from rytm_randomizer.data.rytm_machine_catalog import (
    RYTM_MACHINE_PROFILES,
    get_rytm_machine_profile,
    is_machine_allowed_on_pad,
)
from rytm_randomizer.devices.strategies.analog_rytm_saved_kit_codec import (
    AnalogRytmSavedKitCodecError,
    encode_analog_rytm_saved_kit_frame,
)

pytestmark = pytest.mark.fast


@pytest.fixture(autouse=True)
def _isolate_observability(isolated_observability: None) -> None:
    """Keep exporter metrics and tracing isolated for every test."""


_HEADER = ANALOG_RYTM_SAVED_KIT_TEST_HEADER
_REPO_ROOT = Path(__file__).resolve().parents[1]
_BANK_SPEC = _REPO_ROOT / "specs" / "al16" / "AL16_BANK.yaml"
_AL02_RECIPE = _REPO_ROOT / "specs" / "al16" / "AL02_LOCK_RYTM.yaml"
_COMMITTED_EVIDENCE_HASHES = {
    "output/al16/AL02_LOCK_RYTM_manifest.json": (
        "173f67f921c266cfa2fa54bd450864ee6fa708fd2c298df9014e3e9fb6e00f9f"
    ),
    "output/al16/AL02_LOCK_RYTM_validation.md": (
        "bcf04d1a77c412d93efa1ec558a817df6656ea000d0fb8b337efc992eabbe6e5"
    ),
    "output/al16/AL02_LOCK_RYTM_byte_diff.txt": (
        "5263e9042b091fb89a1a6da005e5056909a3a9a37f12490900c4b2422703701f"
    ),
}


def _recipe() -> dict[str, object]:
    parsed = cast(object, json.loads(_AL02_RECIPE.read_text(encoding="utf-8")))
    assert isinstance(parsed, dict)
    return cast(dict[str, object], parsed)


def _requested_audit_paths(recipe: Mapping[str, object]) -> set[str]:
    expected = {"kit.name", "destination_slot"}
    tracks = cast(Mapping[str, object], recipe["tracks"])
    for pad, value in tracks.items():
        track = cast(Mapping[str, object], value)
        if track["mode"] == AL16_TRACK_MODE_PRESERVE:
            continue
        expected.add(f"tracks.{pad}.machine")
        for section_name in ("source", "filter", "amp"):
            section = cast(Mapping[str, object], track[section_name])
            expected.update(f"tracks.{pad}.{section_name}.{field}" for field in section)
    return expected


def _synthetic_reference(path: Path) -> bytes:
    raw = bytearray(RYTM_KIT_RAW_SIZE)
    pad6_machine_offset = exporter._track_offset(6, RYTM_SOUND_MACHINE_TYPE_OFFSET)
    raw[pad6_machine_offset] = get_rytm_machine_profile("xt_classic").machine_value
    reference = encode_analog_rytm_saved_kit_frame(_HEADER, bytes(raw))
    path.write_bytes(reference)
    return reference


def test_al16_bank_reserves_exact_operating_states_and_roles() -> None:
    assert [state.name for state in AL16_BANK_STATES] == [
        "AIRLOCK",
        "LOCK",
        "ROTATION",
        "PRESSURE",
        "ORBIT",
        "OFFSET",
        "SURGE",
        "CROSSING",
        "COMPRESSION",
        "RITUAL",
        "APEX",
        "VACUUM",
        "REENTRY",
        "TERMINAL",
        "FRACTURE",
        "SHUTDOWN",
    ]
    assert AL16_PAD_ROLES[1] == "Main kick"
    assert AL16_PAD_ROLES[9] == "Closed-hat clock"
    assert AL16_PAD_ROLES[12] == "Cowbell / metallic punctuation / alarm tone"


def test_al16_bank_spec_matches_canonical_data_layer() -> None:
    rendered = render_al16_bank_spec()

    assert _BANK_SPEC.read_text(encoding="utf-8") == rendered
    assert json.loads(rendered) == al16_bank_spec_payload()


def test_al16_generator_dependencies_match_the_complete_behavior_contract() -> None:
    assert exporter.AL16_GENERATOR_DEPENDENCIES == (
        exporter.AL16_GENERATOR_MODULE,
        "rytm_randomizer/cockpit/export/file_export_contracts.py",
        "rytm_randomizer/cockpit/export/writer.py",
        "rytm_randomizer/data/al16_rytm.py",
        "rytm_randomizer/data/analog_rytm_kit_layout.py",
        "rytm_randomizer/data/rytm_machine_catalog.py",
        "rytm_randomizer/devices/__init__.py",
        "rytm_randomizer/devices/analog_rytm.py",
        "rytm_randomizer/devices/registry.py",
        "rytm_randomizer/devices/strategies/__init__.py",
        "rytm_randomizer/devices/strategies/analog_rytm_saved_kit_codec.py",
        "rytm_randomizer/observability/errors.py",
        "rytm_randomizer/snapshot/__init__.py",
        "rytm_randomizer/snapshot/elektron_packed_payload.py",
        "rytm_randomizer/snapshot/elektron_u14.py",
        "rytm_randomizer/snapshot/envelope.py",
    )


def test_committed_al02_blocked_evidence_hashes_are_frozen() -> None:
    assert {
        relative_path: hashlib.sha256((_REPO_ROOT / relative_path).read_bytes()).hexdigest()
        for relative_path in _COMMITTED_EVIDENCE_HASHES
    } == _COMMITTED_EVIDENCE_HASHES


def test_committed_al02_evidence_is_bound_to_current_inputs_and_generator() -> None:
    manifest_path = _REPO_ROOT / "output" / "al16" / "AL02_LOCK_RYTM_manifest.json"
    parsed = cast(object, json.loads(manifest_path.read_text(encoding="utf-8")))
    manifest = exporter._as_mapping(parsed, "committed AL02 manifest")

    assert manifest["generator_contract"] == exporter.AL16_GENERATOR_CONTRACT
    assert manifest["generator_module"] == exporter.AL16_GENERATOR_MODULE
    assert manifest["generator_module_sha256"] == exporter._normalized_text_sha256(
        _REPO_ROOT / exporter.AL16_GENERATOR_MODULE
    )
    assert manifest["generator_dependency_sha256"] == exporter._generator_dependency_hashes()
    assert manifest["recipe_file"] == "specs/al16/AL02_LOCK_RYTM.yaml"
    assert manifest["recipe_sha256"] == hashlib.sha256(_AL02_RECIPE.read_bytes()).hexdigest()
    assert manifest["reference_file"] == ("output/local/reference/RYTM_Test1_Init_Kit.syx")
    assert manifest["reference_sha256"] == exporter._REFERENCE_EXPECTED_SHA256


def test_al16_build_result_rejects_output_hash_for_blocked_contract(tmp_path: Path) -> None:
    common = {
        "output_path": tmp_path / "AL02_LOCK_RYTM.syx",
        "manifest_path": tmp_path / "AL02_LOCK_RYTM_manifest.json",
        "validation_path": tmp_path / "AL02_LOCK_RYTM_validation.md",
        "byte_diff_path": tmp_path / "AL02_LOCK_RYTM_byte_diff.txt",
        "reference_sha256": "reference-sha",
        "gaps": (),
    }

    with pytest.raises(ValueError, match="blocked AL16 result cannot"):
        Al16BuildResult(
            status="blocked",
            output_sha256=cast(None, "output-sha"),
            **common,
        )


def test_al16_build_result_rejects_unknown_runtime_status(tmp_path: Path) -> None:
    common = {
        "output_path": tmp_path / "AL02_LOCK_RYTM.syx",
        "manifest_path": tmp_path / "AL02_LOCK_RYTM_manifest.json",
        "validation_path": tmp_path / "AL02_LOCK_RYTM_validation.md",
        "byte_diff_path": tmp_path / "AL02_LOCK_RYTM_byte_diff.txt",
        "reference_sha256": "reference-sha",
        "output_sha256": None,
        "gaps": (),
    }

    with pytest.raises(ValueError, match="unsupported AL16 build status"):
        Al16BuildResult(status=cast(Al16BuildStatus, "unknown"), **common)


def test_al02_recipe_identifier_is_deterministic() -> None:
    recipe = _recipe()
    reordered = {key: recipe[key] for key in reversed(recipe)}

    assert deterministic_recipe_identifier(recipe) == deterministic_recipe_identifier(reordered)


def test_al02_recipe_identifier_canonicalizes_recursive_mapping_interfaces() -> None:
    first = MappingProxyType(
        {
            "kit": MappingProxyType({"name": "AL02 LOCK", "slot": 127}),
            "values": (MappingProxyType({"value": 12}),),
        }
    )
    second = MappingProxyType(
        {
            "values": (MappingProxyType({"value": 12}),),
            "kit": MappingProxyType({"slot": 127, "name": "AL02 LOCK"}),
        }
    )

    assert deterministic_recipe_identifier(first) == deterministic_recipe_identifier(second)

    with pytest.raises(ValueError, match="string keys"):
        exporter._canonical_recipe_value(MappingProxyType({1: "invalid"}))


def test_al02_audits_are_independent_of_nested_field_order() -> None:
    recipe = _recipe()
    reordered = _recipe()
    tracks = cast(dict[str, object], reordered["tracks"])
    for track_value in tracks.values():
        track = cast(dict[str, object], track_value)
        if track["mode"] == AL16_TRACK_MODE_PRESERVE:
            continue
        for section_name in ("source", "filter", "amp"):
            section = cast(dict[str, object], track[section_name])
            track[section_name] = {key: section[key] for key in reversed(section)}

    assert exporter._inspect_recipe(
        recipe, bytes(RYTM_KIT_RAW_SIZE), 127
    ) == exporter._inspect_recipe(reordered, bytes(RYTM_KIT_RAW_SIZE), 127)


def test_al02_build_fails_closed_and_writes_precise_reports(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    output_path = tmp_path / "output" / "AL02_LOCK_RYTM.syx"

    result = build_al16_rytm_kit(
        reference_path=reference_path,
        recipe_path=_AL02_RECIPE,
        destination_slot=127,
        output_path=output_path,
    )

    assert result.status == "blocked"
    assert not output_path.exists()
    assert reference_path.read_bytes() == reference
    assert result.manifest_path.is_file()
    assert result.validation_path.is_file()
    assert result.byte_diff_path.is_file()
    assert not output_path.with_name(
        f".{output_path.name}{exporter._AL16_OUTPUT_LOCK_SUFFIX}"
    ).exists()

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["build_status"] == "blocked"
    assert manifest["generator_contract"] == exporter.AL16_GENERATOR_CONTRACT
    assert manifest["generator_module"] == exporter.AL16_GENERATOR_MODULE
    assert manifest["generator_module_sha256"] == exporter._normalized_text_sha256(
        _REPO_ROOT / exporter.AL16_GENERATOR_MODULE
    )
    assert manifest["generator_dependency_sha256"] == exporter._generator_dependency_hashes()
    assert manifest["recipe_file"] == "specs/al16/AL02_LOCK_RYTM.yaml"
    assert manifest["recipe_sha256"] == hashlib.sha256(_AL02_RECIPE.read_bytes()).hexdigest()
    assert manifest["destination_slot"] == 127
    assert manifest["kit_name"] == "AL02 LOCK"
    assert manifest["preserved_tracks"] == [2, 4, 5, 7, 8, 10, 11, 12]
    assert manifest["reference_round_trip_byte_identical"] is True
    assert manifest["changed_semantic_fields"] == []
    audit_paths = {audit["semantic_path"] for audit in manifest["semantic_field_audits"]}
    assert audit_paths == _requested_audit_paths(_recipe())
    assert manifest["intentionally_changed_raw_bytes"] == 0
    assert manifest["output_emitted"] is False
    assert manifest["unknown_and_reserved_bytes_unchanged"] is True
    assert manifest["manual_hardware_import_authorized"] is False
    assert manifest["midi_ports_enumerated"] == 0
    assert manifest["midi_ports_opened"] == 0
    assert manifest["midi_messages_sent"] == 0
    assert manifest["critical_mapping_gap_count"] == 18
    gap_paths = {gap["semantic_path"] for gap in manifest["critical_mapping_gaps"]}
    assert gap_paths == {
        "destination_slot",
        "tracks.1.machine",
        "tracks.1.source.tun",
        "tracks.1.source.dec",
        "tracks.1.source.swd",
        "tracks.1.source.swt",
        "tracks.1.source.hld",
        "tracks.1.source.wav",
        "tracks.1.source.trn",
        "tracks.1.amp.vol",
        "tracks.3.machine",
        "tracks.3.amp.vol",
        "tracks.6.source.target_note",
        "tracks.6.source.decay",
        "tracks.6.amp.vol",
        "tracks.9.machine",
        "tracks.9.source.decay",
        "tracks.9.amp.vol",
    }
    validation = result.validation_path.read_text(encoding="utf-8")
    assert "BLOCKED: no SysEx was emitted" in validation
    assert "MIDI ports opened: 0" in validation
    assert "Manual hardware import authorized: no" in validation
    assert "CH BASIC" in validation
    assert "CH Classic or HH Basic" in validation
    assert "intentionally changed raw bytes: 0" in result.byte_diff_path.read_text(encoding="utf-8")


def test_al02_blocked_evidence_is_byte_identical_across_repeated_builds(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1785628800")
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )

    first = build_al16_rytm_kit(
        reference_path=reference_path,
        recipe_path=_AL02_RECIPE,
        destination_slot=127,
        output_path=tmp_path / "first" / "AL02_LOCK_RYTM.syx",
    )
    second = build_al16_rytm_kit(
        reference_path=reference_path,
        recipe_path=_AL02_RECIPE,
        destination_slot=127,
        output_path=tmp_path / "second" / "AL02_LOCK_RYTM.syx",
    )

    assert first.manifest_path.read_bytes() == second.manifest_path.read_bytes()
    assert first.validation_path.read_bytes() == second.validation_path.read_bytes()
    assert first.byte_diff_path.read_bytes() == second.byte_diff_path.read_bytes()


def test_al02_build_records_one_operation_and_one_blocked_metric(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    from rytm_randomizer.observability.metrics import get_metrics

    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    traced: list[tuple[str, str]] = []
    logged: list[dict[str, object]] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[None]:
        traced.append(("start", name))
        yield
        traced.append(("end", name))

    monkeypatch.setattr(exporter, "operation", observe_operation)
    monkeypatch.setattr(
        exporter._logger,
        "info",
        lambda _message, *, extra: logged.append(extra),
    )

    build_al16_rytm_kit(
        reference_path=reference_path,
        recipe_path=_AL02_RECIPE,
        destination_slot=127,
        output_path=tmp_path / "AL02_LOCK_RYTM.syx",
    )

    metrics = get_metrics()
    assert metrics.export_count == 1
    assert metrics.export_errors_by_code["mapping_blocked"] == 1
    assert traced == [
        ("start", "al16_rytm_kit_export"),
        ("end", "al16_rytm_kit_export"),
    ]
    assert logged[0]["outcome"] == "blocked"
    assert logged[0]["mapping_gap_count"] == 18
    assert "mapping_blocked:1" in str(logged[0]["metrics_summary"])


@pytest.mark.parametrize(
    ("exc", "phase", "expected"),
    [
        (KeyboardInterrupt(), "validation", "interrupted"),
        (FileNotFoundError(), "source_read", "input_not_found"),
        (FileNotFoundError(), "output_write", "write_failed"),
        (PermissionError(), "source_read", "permission_denied"),
        (FileExistsError(), "output_write", "overwrite_refused"),
        (OSError(), "source_read", "source_read_failed"),
        (OSError(), "output_write", "write_failed"),
        (OSError(), "validation", "validation"),
        (ValueError(), "output_write", "validation"),
    ],
)
def test_local_file_export_error_codes_are_stable(
    exc: BaseException,
    phase: LocalFileExportPhase,
    expected: str,
) -> None:
    assert (
        classify_local_file_export_error(
            exc,
            phase=phase,
        )
        == expected
    )


@pytest.mark.parametrize(
    ("exc", "phase", "expected"),
    [
        (KeyboardInterrupt(), "validation", "build_interrupted"),
        (FileNotFoundError(), "source_read", "source_input_unavailable"),
        (
            Al16BuildError("destination_slot_invalid", "invalid"),
            "validation",
            "destination_slot_invalid",
        ),
        (
            Al16BuildError("reference_sysex_invalid", "invalid"),
            "validation",
            "reference_sysex_invalid",
        ),
        (ValueError("destination slot is invalid"), "validation", "build_validation_failed"),
    ],
)
def test_al16_failure_reasons_cover_bounded_operator_categories(
    exc: BaseException,
    phase: LocalFileExportPhase,
    expected: str,
) -> None:
    assert exporter.classify_al16_failure_reason(exc, phase=phase) == expected


def test_local_file_export_error_context_is_bounded_and_fail_closed() -> None:
    exc = OSError(r"private path C:\\Users\\Example User\\secret.txt")
    attach_local_file_export_error_context(
        exc,
        error_code="write_failed",
        phase="output_write",
        artifact_name="AL02_LOCK_RYTM_manifest.json",
    )

    context = local_file_export_error_context(exc)
    assert context is not None
    assert context.error_code == "write_failed"
    assert context.phase == "output_write"
    assert context.artifact_name == "AL02_LOCK_RYTM_manifest.json"

    with pytest.raises(ValueError, match="error code"):
        attach_local_file_export_error_context(
            OSError(),
            error_code=cast(LocalFileExportErrorCode, "unknown"),
            phase="validation",
            artifact_name="artifact.json",
        )
    with pytest.raises(ValueError, match="phase"):
        attach_local_file_export_error_context(
            OSError(),
            error_code="validation",
            phase=cast(LocalFileExportPhase, "unknown"),
            artifact_name="artifact.json",
        )
    for artifact_name in (
        "",
        ".",
        "..",
        "nested/artifact.json",
        r"nested\artifact.json",
        r"C:\artifact.json",
        "bad\x01name.json",
        "x" * 256,
    ):
        with pytest.raises(ValueError, match="filename"):
            attach_local_file_export_error_context(
                OSError(),
                error_code="validation",
                phase="validation",
                artifact_name=artifact_name,
            )


@pytest.mark.parametrize(
    ("error_code", "phase", "artifact_name"),
    [
        (None, None, None),
        ("unknown", "validation", "artifact.json"),
        ("validation", None, "artifact.json"),
        ("validation", "unknown", "artifact.json"),
        ("validation", "validation", None),
        ("validation", "validation", ""),
        ("validation", "validation", "."),
        ("validation", "validation", ".."),
        ("validation", "validation", "nested/artifact.json"),
        ("validation", "validation", r"nested\artifact.json"),
        ("validation", "validation", r"C:\artifact.json"),
        ("validation", "validation", "bad\x01name.json"),
        ("validation", "validation", "x" * 256),
    ],
)
def test_local_file_export_error_context_rejects_malformed_metadata(
    error_code: object,
    phase: object,
    artifact_name: object,
) -> None:
    exc = OSError()
    exc.__dict__["local_file_export_error_code"] = error_code
    exc.__dict__["local_file_export_phase"] = phase
    exc.__dict__["local_file_export_artifact_name"] = artifact_name

    assert local_file_export_error_context(exc) is None


def test_local_file_export_rejects_unsafe_fallback_artifact_name() -> None:
    with pytest.raises(ValueError, match="fallback artifact name is not safe"):
        exporter.safe_local_file_export_artifact_name(Path("."), fallback="..")


def test_local_file_export_artifact_name_uses_shared_middle_truncation() -> None:
    bounded = exporter.safe_local_file_export_artifact_name(
        Path("abcdefghijklmnopqrstuvwxyz.json"),
        fallback="output.json",
        max_length=20,
    )

    assert bounded == "abcdefgh...wxyz.json"
    assert len(bounded) == 20


@pytest.mark.parametrize("max_length", [True, 6, 256])
def test_local_file_export_rejects_invalid_artifact_name_bounds(
    max_length: object,
) -> None:
    with pytest.raises(ValueError, match="length bound"):
        exporter.safe_local_file_export_artifact_name(
            Path("artifact.json"),
            fallback="output.json",
            max_length=cast(int, max_length),
        )


def test_local_file_export_rejects_fallback_longer_than_requested_bound() -> None:
    with pytest.raises(ValueError, match="fallback artifact name is not safe"):
        exporter.safe_local_file_export_artifact_name(
            Path("."),
            fallback="fallback.json",
            max_length=10,
        )


def test_al16_artifact_set_delegates_utf8_payloads_to_shared_writer(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def capture_write_set(
        artifacts: Mapping[Path, bytes],
        *,
        overwrite: bool,
    ) -> tuple[object, ...]:
        captured["artifacts"] = artifacts
        captured["overwrite"] = overwrite
        return ()

    monkeypatch.setattr(exporter, "atomic_write_set", capture_write_set)
    manifest_path = tmp_path / "manifest.json"
    validation_path = tmp_path / "validation.md"

    exporter._publish_artifact_set(
        {
            manifest_path: '{"name":"AL02 LOCK"}\n',
            validation_path: "verified: no\n",
        }
    )

    assert captured == {
        "artifacts": {
            manifest_path: b'{"name":"AL02 LOCK"}\n',
            validation_path: b"verified: no\n",
        },
        "overwrite": True,
    }


def test_al16_write_set_failure_reports_the_actual_failed_artifact(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    logged: list[dict[str, object]] = []
    monkeypatch.setattr(
        exporter._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    def fail_publication(**_kwargs: object) -> None:
        raise WriteSetError(
            WriteSetFailureContext(
                phase="publication",
                artifact_name="AL02_LOCK_RYTM_validation.md",
            )
        )

    monkeypatch.setattr(exporter, "_write_blocked_artifacts", fail_publication)

    with pytest.raises(WriteSetError) as raised:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        )

    context = local_file_export_error_context(raised.value)
    assert context is not None
    assert context.error_code == "write_failed"
    assert context.phase == "output_write"
    assert context.artifact_name == "AL02_LOCK_RYTM_validation.md"
    assert logged[0]["artifact_name"] == "AL02_LOCK_RYTM_validation.md"
    assert logged[0]["failure_reason"] == "artifact_publication_failed"
    assert logged[0]["transaction_phase"] == "publication"
    assert logged[0]["fingerprint"] == WriteSetError.fingerprint


@pytest.mark.parametrize(
    ("failure_target", "expected_error_code"),
    [
        ("_validate_artifact_paths", "validation"),
        ("_write_blocked_artifacts", "write_failed"),
    ],
)
def test_al16_service_classifies_failures_by_actual_caller_phase(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    failure_target: str,
    expected_error_code: str,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    logged_codes: list[object] = []
    monkeypatch.setattr(
        exporter._logger,
        "warning",
        lambda _message, *, extra: logged_codes.append(extra["error_code"]),
    )

    def fail_current_phase(**_kwargs: object) -> None:
        raise OSError("injected local-file failure")

    monkeypatch.setattr(exporter, failure_target, fail_current_phase)

    with pytest.raises(OSError, match="injected local-file failure") as raised:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        )

    assert logged_codes == [expected_error_code]
    context = local_file_export_error_context(raised.value)
    assert context is not None
    assert context.error_code == expected_error_code
    assert context.phase == (
        "validation" if failure_target == "_validate_artifact_paths" else "output_write"
    )
    expected_artifact_name = (
        "AL02_LOCK_RYTM.syx"
        if failure_target == "_validate_artifact_paths"
        else "AL02_LOCK_RYTM_manifest.json"
    )
    assert context.artifact_name == expected_artifact_name


def test_al16_service_preserves_existing_bounded_failure_context(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    logged_codes: list[object] = []
    monkeypatch.setattr(
        exporter._logger,
        "warning",
        lambda _message, *, extra: logged_codes.append(extra["error_code"]),
    )

    def fail_with_bounded_context(**_kwargs: object) -> None:
        exc = OSError("injected local-file failure")
        attach_local_file_export_error_context(
            exc,
            error_code="permission_denied",
            phase="source_read",
            artifact_name="safe-input.syx",
        )
        raise exc

    monkeypatch.setattr(exporter, "_validate_artifact_paths", fail_with_bounded_context)

    with pytest.raises(OSError, match="injected local-file failure") as raised:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        )

    assert logged_codes == ["permission_denied"]
    context = local_file_export_error_context(raised.value)
    assert context is not None
    assert context.error_code == "permission_denied"
    assert context.phase == "source_read"
    assert context.artifact_name == "safe-input.syx"


def test_al16_service_fails_closed_when_error_context_cannot_be_attached(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(exporter, "local_file_export_error_context", lambda _exc: None)
    monkeypatch.setattr(
        exporter,
        "_validate_artifact_paths",
        lambda **_kwargs: (_ for _ in ()).throw(OSError("injected failure")),
    )

    with pytest.raises(AssertionError, match="bounded AL16 export error context"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        )


def test_offline_exporter_has_no_midi_backend_dependency() -> None:
    source = (_REPO_ROOT / "rytm_randomizer" / "cockpit" / "export" / "al16_rytm_kit.py").read_text(
        encoding="utf-8"
    )

    assert "import mido" not in source
    assert "import rtmidi" not in source
    assert "MidoMidiPortProvider" not in source


def test_al16_value_readers_and_converters_fail_closed() -> None:
    for value in ([], {1: "value"}):
        with pytest.raises(ValueError, match="string keys"):
            exporter._as_mapping(value, "test")
    for value in ("", 1):
        with pytest.raises(ValueError, match="non-empty string"):
            exporter._as_string(value, "test")
    for value in (True, "1"):
        with pytest.raises(ValueError, match="must be an integer"):
            exporter._as_int(value, "test")
    assert exporter._as_string_list(["a", "b"], "test") == ("a", "b")
    for value in ("a", ["a", 1]):
        with pytest.raises(ValueError, match="array of strings"):
            exporter._as_string_list(value, "test")

    exporter._require_exact_keys({"a": 1}, "test", {"a"})
    with pytest.raises(ValueError, match=r"missing=\['b'\]"):
        exporter._require_exact_keys({"a": 1}, "test", {"a", "b"})
    with pytest.raises(ValueError, match=r"unknown=\['b'\]"):
        exporter._require_exact_keys({"a": 1, "b": 2}, "test", {"a"})
    with pytest.raises(ValueError, match=r"missing=\['b'\].*unknown=\['c'\]"):
        exporter._require_exact_keys({"a": 1, "c": 3}, "test", {"a", "b"})

    assert exporter._convert_supported_value(RYTM_CONVERTER_VERIFIED_7BIT, 127) == (127, 127)
    with pytest.raises(ValueError, match="0..127"):
        exporter._convert_supported_value(RYTM_CONVERTER_VERIFIED_7BIT, 128)
    assert exporter._convert_supported_value(RYTM_CONVERTER_CENTERED_7BIT, "neutral") == (
        0,
        64,
    )
    assert exporter._convert_supported_value(RYTM_CONVERTER_CENTERED_7BIT, "center") == (
        0,
        64,
    )
    assert exporter._convert_supported_value(RYTM_CONVERTER_CENTERED_7BIT, -64) == (-64, 0)
    with pytest.raises(ValueError, match="-64..63"):
        exporter._convert_supported_value(RYTM_CONVERTER_CENTERED_7BIT, 64)
    assert exporter._convert_supported_value(RYTM_CONVERTER_FILTER_TYPE_ENUM, "hp2") == (
        "HP2",
        4,
    )
    with pytest.raises(ValueError, match="unsupported filter type"):
        exporter._convert_supported_value(RYTM_CONVERTER_FILTER_TYPE_ENUM, "unknown")
    with pytest.raises(ValueError, match="unknown AL16 converter"):
        exporter._convert_supported_value(cast(RytmValueConverter, "missing"), 0)


def test_al16_audit_values_are_deeply_immutable() -> None:
    assert exporter._freeze_audit_value(None) is None
    assert exporter._freeze_audit_value("HP2") == "HP2"
    assert exporter._freeze_audit_value(True) is True
    assert exporter._freeze_audit_value(64) == 64
    assert exporter._freeze_audit_value((0, 64, 127)) == (0, 64, 127)

    for value in ([0, 64], (0, True), (-1,), (256,)):
        with pytest.raises(TypeError, match="immutable scalars or byte tuples"):
            exporter._freeze_audit_value(value)


def test_al16_original_semantic_and_machine_labels_are_explicit() -> None:
    assert exporter._original_semantic(RYTM_CONVERTER_CENTERED_7BIT, 0) == -64
    assert exporter._original_semantic(RYTM_CONVERTER_FILTER_TYPE_ENUM, 4) == "HP2"
    assert (
        exporter._original_semantic(RYTM_CONVERTER_FILTER_TYPE_ENUM, 127)
        == "unknown filter type 127"
    )
    assert exporter._original_semantic(RYTM_CONVERTER_VERIFIED_7BIT, 129) == 1
    assert exporter._machine_label_for_raw(RYTM_MACHINE_PROFILES[0].machine_value) == (
        RYTM_MACHINE_PROFILES[0].label
    )
    assert exporter._machine_label_for_raw(0x7F).startswith("unknown machine value")


def test_al16_machine_validation_covers_preserve_and_wrong_pad() -> None:
    raw = bytearray(RYTM_KIT_RAW_SIZE)
    allowed = next(
        profile for profile in RYTM_MACHINE_PROFILES if is_machine_allowed_on_pad(1, profile.key)
    )
    machine_offset = exporter._track_offset(1, RYTM_SOUND_MACHINE_TYPE_OFFSET)
    raw[machine_offset] = allowed.machine_value
    audits: list[exporter.FieldAudit] = []
    gaps: list[exporter.MappingGap] = []

    assert exporter._record_machine(raw, 1, {"machine": allowed.key}, audits, gaps) == allowed.key
    assert audits[-1].verification_status == "verified_preserved_machine"
    assert not gaps

    disallowed_pad, disallowed = next(
        (pad, profile)
        for pad in AL16_PAD_ROLES
        for profile in RYTM_MACHINE_PROFILES
        if not is_machine_allowed_on_pad(pad, profile.key)
    )
    assert (
        exporter._record_machine(
            raw,
            disallowed_pad,
            {"machine": disallowed.key},
            audits,
            gaps,
        )
        == disallowed.key
    )
    assert audits[-1].verification_status == "invalid_machine_for_pad"


def test_al16_tuning_resolution_requires_an_approved_machine_table(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setattr(exporter, "AL16_RYTM_APPROVED_TUNING", {("xt_classic", "F2"): 42})
    audits: list[exporter.FieldAudit] = []
    gaps: list[exporter.MappingGap] = []

    exporter._record_source_fields(6, "xt_classic", {"target_note": "f2"}, audits, gaps)

    assert audits == [
        exporter.FieldAudit(
            semantic_path="tracks.6.source.target_note",
            original_semantic_value=None,
            requested_semantic_value="F2",
            normalized_semantic_value="F2",
            encoded_raw_value_or_bytes=(42,),
            raw_location=None,
            converter_or_enumeration="approved_tuning_table:xt_classic",
            verification_status="resolved_tuning_pending_source_writer",
        )
    ]
    assert not gaps


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda recipe: recipe.update(unexpected=True), "recipe keys are invalid"),
        (lambda recipe: recipe.update(schema_version=2), "schema_version must be 1"),
        (lambda recipe: recipe.update(project_id="OTHER"), "project_id must be AL16"),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(unexpected=True),
            "kit keys are invalid",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(state=17),
            "kit.state must be in 1..16",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(state=1),
            "Phase R1 supports only the AL02 LOCK proof recipe",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(name="AL02 OTHER"),
            "kit.name must match",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(tonal_zone="Other"),
            "kit.tonal_zone must match",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(
                performance_context_bpm=140
            ),
            "performance_context_bpm must be 138",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(name="X" * 17),
            "16-byte ASCII",
        ),
        (
            lambda recipe: cast(dict[str, object], recipe["kit"]).update(name="AL02 L\u00d6CK"),
            "16-byte ASCII",
        ),
        (lambda recipe: recipe.update(preserve=[]), "complete ordered AL16"),
        (lambda recipe: cast(dict[str, object], recipe["tracks"]).pop("12"), "pads 1..12"),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["1"]
            ).update(role="Wrong role"),
            "permanent AL16 pad role",
        ),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["1"]
            ).update(mode="other"),
            "must be patch or preserve",
        ),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["1"]
            ).update(unexpected=True),
            "tracks.1 keys are invalid",
        ),
        (
            lambda recipe: cast(
                dict[str, object], cast(dict[str, object], recipe["tracks"])["2"]
            ).update(unexpected=True),
            "tracks.2 keys are invalid",
        ),
    ],
)
def test_al16_recipe_validation_rejects_invalid_contracts(
    mutate: object,
    message: str,
) -> None:
    recipe = _recipe()
    apply_mutation = mutate
    assert callable(apply_mutation)
    apply_mutation(recipe)

    with pytest.raises(Al16BuildError, match=message) as exc_info:
        exporter._inspect_recipe(recipe, bytes(RYTM_KIT_RAW_SIZE), 127)

    assert exc_info.value.reason == "recipe_schema_invalid"


def test_al16_recipe_validation_rejects_invalid_destination_slot() -> None:
    with pytest.raises(Al16BuildError, match="destination slot") as exc_info:
        exporter._inspect_recipe(_recipe(), bytes(RYTM_KIT_RAW_SIZE), 128)

    assert exc_info.value.reason == "destination_slot_invalid"


@pytest.mark.parametrize(
    "unsafe_output",
    [Path("."), Path(".."), Path("x" * 256)],
)
def test_al16_build_rejects_unsafe_output_names_with_bounded_context(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    unsafe_output: Path,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )

    with pytest.raises(ValueError, match="safe filename") as raised:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=unsafe_output,
        )

    context = local_file_export_error_context(raised.value)
    assert context is not None
    assert context.error_code == "validation"
    assert context.phase == "validation"
    assert context.artifact_name == exporter.safe_local_file_export_artifact_name(
        unsafe_output,
        fallback="output.syx",
    )


def test_al16_build_refuses_round_trip_drift_and_stale_output(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    original_codec = exporter.get_analog_rytm_saved_kit_codec_capability()

    class _DriftingCodec:
        def decode_saved_kit_frame(self, frame: bytes):
            return original_codec.decode_saved_kit_frame(frame)

        def encode_saved_kit_frame(self, header: bytes, unpacked: bytes) -> bytes:
            encoded = original_codec.encode_saved_kit_frame(header, unpacked)
            return encoded[:-1] + b"\x00"

    monkeypatch.setattr(
        exporter,
        "get_analog_rytm_saved_kit_codec_capability",
        _DriftingCodec,
    )
    with pytest.raises(ValueError, match="not byte-identical"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    monkeypatch.setattr(
        exporter,
        "get_analog_rytm_saved_kit_codec_capability",
        lambda: original_codec,
    )
    output_path.write_bytes(b"stale")
    with pytest.raises(FileExistsError, match="potentially stale output"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )


def test_al16_build_refuses_an_existing_output_lock_without_removing_it(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    lock_path = output_path.with_name(f".{output_path.name}{exporter._AL16_OUTPUT_LOCK_SUFFIX}")
    lock_path.mkdir()

    with pytest.raises(Al16BuildError) as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    assert exc_info.value.reason == "artifact_path_collision"
    assert lock_path.is_dir()
    assert not output_path.exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_manifest.json").exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_validation.md").exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_byte_diff.txt").exists()


def test_al16_build_rechecks_stale_output_inside_publication_lock(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "RYTM_Test1_Init_Kit.syx"
    reference = _synthetic_reference(reference_path)
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    inspect_recipe = exporter._inspect_recipe

    def create_racing_output(
        recipe: Mapping[str, object],
        reference_raw: bytes,
        destination_slot: int,
    ) -> tuple[
        list[exporter.FieldAudit],
        list[exporter.MappingGap],
        list[int],
    ]:
        result = inspect_recipe(recipe, reference_raw, destination_slot)
        output_path.write_bytes(b"concurrent-output")
        return result

    monkeypatch.setattr(exporter, "_inspect_recipe", create_racing_output)

    with pytest.raises(FileExistsError, match="potentially stale output"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    lock_path = output_path.with_name(f".{output_path.name}{exporter._AL16_OUTPUT_LOCK_SUFFIX}")
    assert output_path.read_bytes() == b"concurrent-output"
    assert not lock_path.exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_manifest.json").exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_validation.md").exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_byte_diff.txt").exists()


def test_al16_build_timestamp_supports_explicit_and_default_reproducible_modes(
    monkeypatch: MonkeyPatch,
) -> None:
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "0")
    assert exporter._build_timestamp() == "1970-01-01T00:00:00+00:00"
    monkeypatch.delenv("SOURCE_DATE_EPOCH")
    assert exporter._build_timestamp() == "1970-01-01T00:00:00+00:00"
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "9" * 100)
    with pytest.raises(ValueError, match="in-range integer Unix timestamp"):
        exporter._build_timestamp()


@pytest.mark.parametrize("collision_input", ["reference", "recipe"])
def test_al16_build_rejects_evidence_path_input_collisions(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
    collision_input: str,
) -> None:
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    manifest_path = tmp_path / "AL02_LOCK_RYTM_manifest.json"
    reference_path = tmp_path / "reference.syx"
    recipe_path = tmp_path / "recipe.json"
    if collision_input == "reference":
        reference_path = manifest_path
        reference = _synthetic_reference(reference_path)
        recipe_path.write_bytes(_AL02_RECIPE.read_bytes())
    else:
        reference = _synthetic_reference(reference_path)
        recipe_path = manifest_path
        recipe_path.write_bytes(_AL02_RECIPE.read_bytes())
    input_path = reference_path if collision_input == "reference" else recipe_path
    input_bytes = input_path.read_bytes()
    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )

    with pytest.raises(ValueError, match=f"collides with {collision_input} input"):
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=recipe_path,
            destination_slot=127,
            output_path=output_path,
        )

    assert input_path.read_bytes() == input_bytes
    assert not output_path.exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_validation.md").exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_byte_diff.txt").exists()


def test_al16_build_rejects_artifact_path_collisions(tmp_path: Path) -> None:
    duplicate_sidecar = tmp_path / "AL02_LOCK_RYTM_evidence.json"

    with pytest.raises(ValueError, match="validation artifact path collides with manifest"):
        exporter._validate_artifact_paths(
            reference_path=tmp_path / "reference.syx",
            recipe_path=tmp_path / "recipe.yaml",
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
            manifest_path=duplicate_sidecar,
            validation_path=duplicate_sidecar,
            byte_diff_path=tmp_path / "AL02_LOCK_RYTM_byte_diff.txt",
        )


def test_al16_build_rejects_canonical_artifact_path_aliases(tmp_path: Path) -> None:
    evidence_dir = tmp_path / "evidence"

    with pytest.raises(ValueError, match="validation artifact path collides with manifest"):
        exporter._validate_artifact_paths(
            reference_path=tmp_path / "reference.syx",
            recipe_path=tmp_path / "recipe.yaml",
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
            manifest_path=evidence_dir / "alias.json",
            validation_path=evidence_dir / ".." / "evidence" / "alias.json",
            byte_diff_path=evidence_dir / "AL02_LOCK_RYTM_byte_diff.txt",
        )


def test_al16_output_lock_cleanup_failure_preserves_active_exception(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    lock_path = output_path.with_name(f".{output_path.name}.al16-build.lock")
    path_type = type(lock_path)
    real_rmdir = path_type.rmdir

    def fail_lock_cleanup(_path: Path) -> None:
        raise PermissionError("lock cleanup denied")

    monkeypatch.setattr(path_type, "rmdir", fail_lock_cleanup)

    with pytest.raises(RuntimeError, match="primary build failure") as exc_info:
        with exporter._exclusive_al16_output_lock(output_path):
            raise RuntimeError("primary build failure")

    assert any("output lock cleanup also failed" in note for note in exc_info.value.__notes__)
    assert lock_path.is_dir()
    real_rmdir(lock_path)


def test_al16_output_lock_cleanup_failure_is_typed_without_active_exception(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    lock_path = output_path.with_name(f".{output_path.name}.al16-build.lock")
    path_type = type(lock_path)
    real_rmdir = path_type.rmdir

    def fail_lock_cleanup(_path: Path) -> None:
        raise PermissionError("lock cleanup denied")

    monkeypatch.setattr(path_type, "rmdir", fail_lock_cleanup)

    with pytest.raises(Al16BuildError, match="output lock cleanup failed") as exc_info:
        with exporter._exclusive_al16_output_lock(output_path):
            pass

    assert exc_info.value.reason == "artifact_publication_failed"
    assert isinstance(exc_info.value.__cause__, PermissionError)
    assert lock_path.is_dir()
    real_rmdir(lock_path)


def test_al16_build_rejects_an_unexpected_initialized_reference(tmp_path: Path) -> None:
    reference_path = tmp_path / "wrong.syx"
    _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"

    with pytest.raises(Al16BuildError, match="reference SHA-256 mismatch") as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    assert exc_info.value.reason == "reference_hash_mismatch"
    context = local_file_export_error_context(exc_info.value)
    assert context is not None
    assert context.phase == "validation"
    assert not output_path.exists()
    assert not output_path.with_name("AL02_LOCK_RYTM_manifest.json").exists()


def test_al16_build_classifies_invalid_reference_sysex_with_typed_error(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "reference.syx"
    reference = _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"

    class InvalidCodec:
        def decode_saved_kit_frame(self, _frame: bytes) -> Never:
            raise AnalogRytmSavedKitCodecError("invalid saved-KIT envelope")

    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(
        exporter,
        "get_analog_rytm_saved_kit_codec_capability",
        InvalidCodec,
    )

    with pytest.raises(Al16BuildError) as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    assert exc_info.value.reason == "reference_sysex_invalid"
    assert isinstance(exc_info.value.__cause__, AnalogRytmSavedKitCodecError)
    context = local_file_export_error_context(exc_info.value)
    assert context is not None
    assert context.phase == "validation"


def test_al16_build_does_not_reclassify_unexpected_codec_failure(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "reference.syx"
    reference = _synthetic_reference(reference_path)

    class DefectiveCodec:
        def decode_saved_kit_frame(self, _frame: bytes) -> Never:
            raise ValueError("unexpected codec defect")

    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(
        exporter,
        "get_analog_rytm_saved_kit_codec_capability",
        DefectiveCodec,
    )

    with pytest.raises(ValueError, match="unexpected codec defect") as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=tmp_path / "AL02_LOCK_RYTM.syx",
        )

    assert not isinstance(exc_info.value, Al16BuildError)
    context = local_file_export_error_context(exc_info.value)
    assert context is not None
    assert context.phase == "validation"


@pytest.mark.parametrize("payload", (b"\xff", b"{"))
def test_al16_recipe_loader_classifies_expected_decode_failures(payload: bytes) -> None:
    with pytest.raises(Al16BuildError) as exc_info:
        exporter._load_recipe_bytes(payload)

    assert exc_info.value.reason == "recipe_schema_invalid"
    assert isinstance(
        exc_info.value.__cause__,
        (UnicodeDecodeError, json.JSONDecodeError),
    )


def test_al16_build_does_not_mask_unexpected_recipe_load_failure(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "reference.syx"
    reference = _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"

    def fail_recipe_load(_recipe_bytes: bytes) -> Never:
        raise KeyError("missing recipe root")

    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(exporter, "_load_recipe_bytes", fail_recipe_load)

    with pytest.raises(KeyError, match="missing recipe root") as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    context = local_file_export_error_context(exc_info.value)
    assert context is not None
    assert context.phase == "validation"


def test_al16_build_does_not_mask_unexpected_recipe_inspection_failure(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "reference.syx"
    reference = _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"

    def fail_inspection(*_args: object) -> Never:
        raise TypeError("unexpected recipe shape")

    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(exporter, "_inspect_recipe", fail_inspection)

    with pytest.raises(TypeError, match="unexpected recipe shape") as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    context = local_file_export_error_context(exc_info.value)
    assert context is not None
    assert context.phase == "validation"


def test_al16_build_preserves_typed_recipe_inspection_error(
    tmp_path: Path,
    monkeypatch: MonkeyPatch,
) -> None:
    reference_path = tmp_path / "reference.syx"
    reference = _synthetic_reference(reference_path)
    output_path = tmp_path / "AL02_LOCK_RYTM.syx"
    expected = Al16BuildError("destination_slot_invalid", "typed validation failure")
    logged: list[dict[str, object]] = []

    def fail_inspection(*_args: object) -> Never:
        raise expected

    monkeypatch.setattr(
        exporter,
        "_REFERENCE_EXPECTED_SHA256",
        hashlib.sha256(reference).hexdigest(),
    )
    monkeypatch.setattr(exporter, "_inspect_recipe", fail_inspection)
    monkeypatch.setattr(
        exporter._logger,
        "warning",
        lambda _message, *, extra: logged.append(extra),
    )

    with pytest.raises(Al16BuildError) as exc_info:
        build_al16_rytm_kit(
            reference_path=reference_path,
            recipe_path=_AL02_RECIPE,
            destination_slot=127,
            output_path=output_path,
        )

    assert exc_info.value is expected
    assert logged[0]["fingerprint"] == expected.fingerprint
