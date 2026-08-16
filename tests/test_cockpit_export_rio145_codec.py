from __future__ import annotations

import hashlib
import io
import json
import sys
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path
from typing import Callable, cast

import pytest

from rytm_randomizer.cockpit.export import rio145_codec as codec
from rytm_randomizer.cockpit.export.rio145_codec import (
    Rio145OfflineError,
    build_a4_kit,
    build_rytm_kit,
    diff_sysex,
    export_oxi_manifest,
    inspect_sysex,
    split_elektron_sysex,
    validate_a4_return,
    validate_roundtrip,
    validate_rytm_return,
)
from rytm_randomizer.devices.rio145_recipes import KitRecipeBuildResult, compile_a4_kit_recipe
from rytm_randomizer.observability.logging import configure_logging
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.snapshot import ElektronNativeObjectMessage

pytestmark = pytest.mark.fast

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "rio145"
SPECS = ROOT / "specs" / "rio145"


def _fixture(name: str) -> Path:
    return FIXTURES / name


def _single_native_message(path: Path) -> ElektronNativeObjectMessage:
    frames = split_elektron_sysex(path.read_bytes())
    assert len(frames) == 1
    return ElektronNativeObjectMessage.from_bytes(frames[0])


def _recipe(path: Path) -> Mapping[str, object]:
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(decoded, Mapping)
    return cast(Mapping[str, object], decoded)


def _a4_compilation() -> tuple[ElektronNativeObjectMessage, KitRecipeBuildResult]:
    baseline = _single_native_message(_fixture("A4_Test1_Init_Kit.syx"))
    recipe = _recipe(SPECS / "come_to_rio_a4_core.json")
    result = compile_a4_kit_recipe(baseline, recipe)
    return baseline, result


def test_multi_frame_inspection_and_roundtrip_are_strict(tmp_path: Path) -> None:
    source = _fixture("A4_Test1_Init_A01_PatternKit.syx")
    frames = split_elektron_sysex(source.read_bytes())

    assert len(frames) == 2
    assert b"".join(frames) == source.read_bytes()
    inspection = inspect_sysex(source)
    assert inspection["frame_count"] == 2
    assert inspection["hardware_access"] is False
    assert validate_roundtrip(source)["byte_identical"] is True

    with pytest.raises(Rio145OfflineError, match="framing"):
        split_elektron_sysex(b"not sysex")

    with pytest.raises(Rio145OfflineError, match="empty"):
        split_elektron_sysex(b"")
    with pytest.raises(Rio145OfflineError, match="without a closing F7"):
        split_elektron_sysex(frames[0][:-1])
    with pytest.raises(Rio145OfflineError, match="exactly one"):
        build_a4_kit(
            reference_path=source,
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            destination_slot=0,
            output_path=tmp_path / "refused.syx",
        )


def test_sysex_split_rejects_non_adjacent_extractor_results(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(codec, "extract_sysex_payloads", lambda *_args, **_kwargs: (b"frame",))

    with pytest.raises(Rio145OfflineError, match="complete adjacent frames"):
        split_elektron_sysex(b"different input")


def test_roundtrip_detects_a_changed_reserialization(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _ChangedMessage:
        def to_bytes(self) -> bytes:
            return b"changed"

    class _ChangedParser:
        @classmethod
        def from_bytes(cls, frame: bytes) -> _ChangedMessage:
            return _ChangedMessage()

    monkeypatch.setattr(codec, "ElektronNativeObjectMessage", _ChangedParser)

    with pytest.raises(Rio145OfflineError, match="roundtrip changed"):
        validate_roundtrip(_fixture("A4_Test1_Init_Kit.syx"))


def test_json_mapping_loader_rejects_non_objects_and_non_string_keys(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "recipe.json"
    source.write_text("[]", encoding="utf-8")
    with pytest.raises(Rio145OfflineError, match="JSON object"):
        build_a4_kit(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=source,
            destination_slot=0,
            output_path=tmp_path / "non-object.syx",
        )

    monkeypatch.setattr(codec.json, "loads", lambda _text: {1: "value"})
    with pytest.raises(Rio145OfflineError, match="string keys"):
        build_a4_kit(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=source,
            destination_slot=0,
            output_path=tmp_path / "non-string-key.syx",
        )


@pytest.mark.parametrize(
    ("builder", "reference", "recipe", "expected_sha", "changed_count"),
    [
        (
            build_a4_kit,
            "A4_Test1_Init_Kit.syx",
            "come_to_rio_a4_core.json",
            "3a29f4ff39a58a188ca16745312b419f1a7d23c30ecb3541deb3e82f0a9237e0",
            354,
        ),
        (
            build_rytm_kit,
            "RYTM_Test1_Init_Kit.syx",
            "come_to_rio_rytm_core.json",
            "b024ef17f317e26ffafb4e52120527435c9e942d136e56eb95b8f27af9846057",
            495,
        ),
    ],
)
def test_builds_are_deterministic_allowlisted_and_overwrite_guarded(
    tmp_path: Path,
    builder: object,
    reference: str,
    recipe: str,
    expected_sha: str,
    changed_count: int,
) -> None:
    if builder is build_a4_kit:
        result = build_a4_kit(
            reference_path=_fixture(reference),
            recipe_path=SPECS / recipe,
            destination_slot=0,
            output_path=tmp_path / "first.syx",
        )
        second = build_a4_kit(
            reference_path=_fixture(reference),
            recipe_path=SPECS / recipe,
            destination_slot=0,
            output_path=tmp_path / "second.syx",
        )
    else:
        result = build_rytm_kit(
            reference_path=_fixture(reference),
            recipe_path=SPECS / recipe,
            destination_slot=0,
            output_path=tmp_path / "first.syx",
        )
        second = build_rytm_kit(
            reference_path=_fixture(reference),
            recipe_path=SPECS / recipe,
            destination_slot=0,
            output_path=tmp_path / "second.syx",
        )

    first_bytes = (tmp_path / "first.syx").read_bytes()
    assert first_bytes == (tmp_path / "second.syx").read_bytes()
    assert hashlib.sha256(first_bytes).hexdigest() == expected_sha
    assert result["output_sha256"] == second["output_sha256"] == expected_sha
    assert result["changed_native_payload_byte_count"] == changed_count
    assert result["changed_outside_declared_edit_regions"] == []
    assert result["hardware_access"] is False

    with pytest.raises(FileExistsError, match="already exists"):
        if builder is build_a4_kit:
            build_a4_kit(
                reference_path=_fixture(reference),
                recipe_path=SPECS / recipe,
                destination_slot=0,
                output_path=tmp_path / "first.syx",
            )
        else:
            build_rytm_kit(
                reference_path=_fixture(reference),
                recipe_path=SPECS / recipe,
                destination_slot=0,
                output_path=tmp_path / "first.syx",
            )


def test_build_guardrails_reject_invalid_slot_outside_edits_and_nondeterminism(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    reference = _fixture("A4_Test1_Init_Kit.syx")
    recipe = SPECS / "come_to_rio_a4_core.json"
    with pytest.raises(Rio145OfflineError, match="0..127"):
        build_a4_kit(
            reference_path=reference,
            recipe_path=recipe,
            destination_slot=-1,
            output_path=tmp_path / "invalid.syx",
        )

    _, compiled = _a4_compilation()

    def outside_compiler(
        _baseline: ElektronNativeObjectMessage, _recipe: Mapping[str, object]
    ) -> KitRecipeBuildResult:
        return replace(compiled, changed_outside_declared_edit_regions=(7,))

    monkeypatch.setattr(codec, "compile_a4_kit_recipe", outside_compiler)
    with pytest.raises(Rio145OfflineError, match="outside declared edit regions"):
        build_a4_kit(
            reference_path=reference,
            recipe_path=recipe,
            destination_slot=0,
            output_path=tmp_path / "outside.syx",
            overwrite=False,
        )

    altered_payload = bytearray(compiled.message.payload)
    altered_payload[0] ^= 1
    altered = replace(compiled, message=compiled.message.with_payload(altered_payload))
    results = iter((compiled, altered))

    def nondeterministic_compiler(
        _baseline: ElektronNativeObjectMessage, _recipe: Mapping[str, object]
    ) -> KitRecipeBuildResult:
        return next(results)

    monkeypatch.setattr(codec, "compile_a4_kit_recipe", nondeterministic_compiler)
    with pytest.raises(Rio145OfflineError, match="different output bytes"):
        build_a4_kit(
            reference_path=reference,
            recipe_path=recipe,
            destination_slot=0,
            output_path=tmp_path / "nondeterministic.syx",
            overwrite=False,
        )


@pytest.mark.parametrize("failure", ["reserialization", "semantic"])
def test_build_guardrails_verify_reparsed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    _baseline, compiled = _a4_compilation()
    output = compiled.message.with_slot(0).to_bytes()
    original_parser = ElektronNativeObjectMessage

    class _Reparsed:
        payload = compiled.message.payload if failure == "reserialization" else b"different payload"
        slot = 0

        def to_bytes(self) -> bytes:
            return b"different wire" if failure == "reserialization" else output

    class _Parser:
        calls = 0

        @classmethod
        def from_bytes(cls, frame: bytes) -> ElektronNativeObjectMessage | _Reparsed:
            cls.calls += 1
            if cls.calls <= 2:
                return original_parser.from_bytes(frame)
            return _Reparsed()

    monkeypatch.setattr(codec, "compile_a4_kit_recipe", lambda _baseline, _recipe: compiled)
    monkeypatch.setattr(codec, "ElektronNativeObjectMessage", _Parser)

    expected = "reserialization" if failure == "reserialization" else "semantic payload"
    with pytest.raises(Rio145OfflineError, match=expected):
        build_a4_kit(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            destination_slot=0,
            output_path=tmp_path / "output.syx",
            overwrite=False,
        )


def test_target_returns_match_compiled_native_payloads() -> None:
    a4 = validate_a4_return(
        reference_path=_fixture("A4_Test1_Init_Kit.syx"),
        recipe_path=SPECS / "come_to_rio_a4_core.json",
        returned_path=_fixture("A4_RIO145_CORE_RETURN_Kit.syx"),
    )
    rytm = validate_rytm_return(
        reference_path=_fixture("RYTM_Test1_Init_Kit.syx"),
        recipe_path=SPECS / "come_to_rio_rytm_core.json",
        returned_path=_fixture("RYTM_RIO145_AR_CORE_RETURN_Kit.syx"),
    )

    assert a4["status"] == rytm["status"] == "TARGET_UNIT_BINARY_RETURN_VALIDATED"
    assert a4["returned_slot"] == 11
    assert rytm["returned_slot"] == 3
    assert a4["native_payload_diff_count"] == rytm["native_payload_diff_count"] == 0
    assert a4["sonic_equivalence_claim"] is False
    assert rytm["sonic_equivalence_claim"] is False


def test_target_return_validation_rejects_outside_edits_and_payload_mismatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline, compiled = _a4_compilation()

    def outside_compiler(
        _baseline: ElektronNativeObjectMessage, _recipe: Mapping[str, object]
    ) -> KitRecipeBuildResult:
        return replace(compiled, changed_outside_declared_edit_regions=(1,))

    monkeypatch.setattr(codec, "compile_a4_kit_recipe", outside_compiler)
    with pytest.raises(Rio145OfflineError, match="outside declared edit regions"):
        validate_a4_return(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=_fixture("A4_RIO145_CORE_RETURN_Kit.syx"),
        )
    monkeypatch.setattr(codec, "compile_a4_kit_recipe", compile_a4_kit_recipe)

    assert baseline.product_id == compiled.message.product_id
    with pytest.raises(Rio145OfflineError, match="differs from compiled payload"):
        validate_a4_return(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=_fixture("A4_Test1_Init_Kit.syx"),
        )


def test_target_return_validation_rejects_roundtrip_and_header_mismatch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _baseline, compiled = _a4_compilation()
    original_parser = ElektronNativeObjectMessage

    class _Returned:
        payload = compiled.message.payload
        slot = 11

        def to_bytes(self) -> bytes:
            return b"changed"

    class _Parser:
        calls = 0

        @classmethod
        def from_bytes(cls, frame: bytes) -> ElektronNativeObjectMessage | _Returned:
            cls.calls += 1
            if cls.calls <= 2:
                return original_parser.from_bytes(frame)
            return _Returned()

    monkeypatch.setattr(codec, "compile_a4_kit_recipe", lambda _baseline, _recipe: compiled)
    monkeypatch.setattr(codec, "ElektronNativeObjectMessage", _Parser)
    with pytest.raises(Rio145OfflineError, match="roundtrip"):
        validate_a4_return(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=_fixture("A4_RIO145_CORE_RETURN_Kit.syx"),
        )

    monkeypatch.undo()
    returned = replace(compiled.message, device_id=(compiled.message.device_id + 1) % 128)
    returned_path = tmp_path / "header-mismatch.syx"
    returned_path.write_bytes(returned.with_slot(11).to_bytes())
    monkeypatch.setattr(codec, "compile_a4_kit_recipe", lambda _baseline, _recipe: compiled)
    with pytest.raises(Rio145OfflineError, match="normalizing the destination slot"):
        validate_a4_return(
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=returned_path,
        )


def test_diff_distinguishes_slot_only_from_native_payload_changes() -> None:
    slot_only = diff_sysex(
        _fixture("A4_Test1_Init_Kit.syx"),
        _fixture("A4_Test1_Init_Kit.syx"),
    )
    payload_change = diff_sysex(
        _fixture("A4_Test1_Init_Kit.syx"),
        _fixture("A4_Test2_T1_OSC1_FIN_P1_Kit.syx"),
    )

    assert slot_only["wire_diff_count"] == 0
    assert slot_only["native_payload_diff_count"] == 0
    assert payload_change["native_payload_diff_count"] > 0


def test_oxi_export_is_hash_pinned_and_deterministic(tmp_path: Path) -> None:
    source_manifest = json.loads((SPECS / "oxi_program_manifest.json").read_text(encoding="utf-8"))
    for section in ("ownership", "midi_sync", "optional_modulation_lanes"):
        assert "analog_rytm_mk2" in source_manifest[section]
        assert "analog_four_mk2" in source_manifest[section]
        assert "analog_rytm_mkii" not in source_manifest[section]
        assert "analog_four_mkii" not in source_manifest[section]

    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"
    kwargs = {
        "manifest_path": SPECS / "oxi_program_manifest.json",
        "events_path": SPECS / "oxi_event_list.csv",
    }
    first = export_oxi_manifest(output_path=first_path, **kwargs)
    second = export_oxi_manifest(output_path=second_path, **kwargs)

    assert first_path.read_bytes() == second_path.read_bytes()
    assert first["output_sha256"] == second["output_sha256"]
    assert first["event_count"] == 360
    assert first["arrangement_last_bar"] == 191
    assert first["native_elektron_patterns_authored"] is False
    assert first["hardware_access"] is False
    assert json.loads(first_path.read_text(encoding="utf-8"))["programs"] == [
        "RIO-A CORE",
        "RIO-B PEAK",
        "RIO-C BREAK",
        "RIO-D RISE",
    ]

    altered_manifest = tmp_path / "altered.json"
    altered_manifest.write_bytes((SPECS / "oxi_program_manifest.json").read_bytes() + b"\n")
    with pytest.raises(Rio145OfflineError, match="SHA-256"):
        export_oxi_manifest(
            manifest_path=altered_manifest,
            events_path=SPECS / "oxi_event_list.csv",
            output_path=tmp_path / "refused.json",
        )

    altered_events = tmp_path / "altered.csv"
    altered_events.write_bytes((SPECS / "oxi_event_list.csv").read_bytes() + b"\n")
    with pytest.raises(Rio145OfflineError, match="event-list SHA-256"):
        export_oxi_manifest(
            manifest_path=SPECS / "oxi_program_manifest.json",
            events_path=altered_events,
            output_path=tmp_path / "events-refused.json",
        )


def _write_oxi_case(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, object]], None],
    *,
    truncate_events: bool = False,
) -> tuple[Path, Path]:
    manifest = json.loads((SPECS / "oxi_program_manifest.json").read_text(encoding="utf-8"))
    mutate(manifest)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True), encoding="utf-8"
    )
    event_lines = (SPECS / "oxi_event_list.csv").read_bytes().splitlines(keepends=True)
    events_path = tmp_path / "events.csv"
    events_path.write_bytes(b"".join(event_lines[:-1] if truncate_events else event_lines))
    monkeypatch.setattr(
        codec, "_OXI_MANIFEST_SHA256", hashlib.sha256(manifest_path.read_bytes()).hexdigest()
    )
    monkeypatch.setattr(
        codec, "_OXI_EVENTS_SHA256", hashlib.sha256(events_path.read_bytes()).hexdigest()
    )
    return manifest_path, events_path


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda value: value.__setitem__("schema", "wrong"), "identity"),
        (lambda value: value.__setitem__("tempo_bpm", True), "145 BPM"),
        (lambda value: value.__setitem__("ownership", []), "ownership must be an object"),
        (
            lambda value: value.__setitem__("ownership", {"oxi_one": "notes"}),
            "ownership.oxi_one must be an array",
        ),
        (
            lambda value: value.__setitem__("ownership", {"oxi_one": ["notes"]}),
            "ownership does not match",
        ),
        (lambda value: value.__setitem__("programs", []), "programs must be an object"),
        (lambda value: value.__setitem__("programs", {"WRONG": {}}), "program order"),
        (lambda value: value.__setitem__("arrangement", "1-191"), "must be an array"),
        (lambda value: value.__setitem__("arrangement", [1]), "must be an object"),
        (lambda value: value.__setitem__("arrangement", [{"bars": 1}]), "must be text"),
        (lambda value: value.__setitem__("arrangement", [{"bars": "bad"}]), "bar range"),
        (lambda value: value.__setitem__("arrangement", [{"bars": "1-190"}]), "bar 191"),
        (lambda value: value.__setitem__("event_count", 359), "event_count"),
    ],
)
def test_oxi_export_rejects_tampered_semantics(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, object]], None],
    message: str,
) -> None:
    manifest_path, events_path = _write_oxi_case(tmp_path, monkeypatch, mutate)

    with pytest.raises(Rio145OfflineError, match=message):
        export_oxi_manifest(
            manifest_path=manifest_path,
            events_path=events_path,
            output_path=tmp_path / "refused.json",
        )


def test_oxi_export_rejects_non_string_mapping_keys_and_wrong_event_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(codec.json, "loads", lambda _text: {1: "value"})
    with pytest.raises(Rio145OfflineError, match="string keys"):
        export_oxi_manifest(
            manifest_path=SPECS / "oxi_program_manifest.json",
            events_path=SPECS / "oxi_event_list.csv",
            output_path=tmp_path / "non-string-key.json",
        )
    monkeypatch.undo()

    manifest = json.loads((SPECS / "oxi_program_manifest.json").read_text(encoding="utf-8"))
    manifest["ownership"] = {1: ["notes"]}
    monkeypatch.setattr(codec, "_load_json_mapping", lambda _path: manifest)
    with pytest.raises(Rio145OfflineError, match="ownership must contain only string keys"):
        export_oxi_manifest(
            manifest_path=SPECS / "oxi_program_manifest.json",
            events_path=SPECS / "oxi_event_list.csv",
            output_path=tmp_path / "nested-non-string-key.json",
        )
    monkeypatch.undo()

    manifest_path, events_path = _write_oxi_case(
        tmp_path, monkeypatch, lambda _value: None, truncate_events=True
    )
    with pytest.raises(Rio145OfflineError, match="found 359"):
        export_oxi_manifest(
            manifest_path=manifest_path,
            events_path=events_path,
            output_path=tmp_path / "refused.json",
        )


def test_offline_operations_do_not_load_midi_backends(tmp_path: Path) -> None:
    before = set(sys.modules)
    validate_roundtrip(_fixture("A4_Test1_Init_Kit.syx"))
    export_oxi_manifest(
        manifest_path=SPECS / "oxi_program_manifest.json",
        events_path=SPECS / "oxi_event_list.csv",
        output_path=tmp_path / "evidence.json",
    )
    loaded = set(sys.modules) - before

    assert not {"mido", "rtmidi", "pythonrtmidi"}.intersection(loaded)
    assert "rytm_randomizer.real_midi_adapter" not in loaded
    assert "rytm_randomizer.mido_provider" not in loaded


def test_rio145_public_boundary_records_bounded_success_and_failure_telemetry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    isolated_observability: None,
) -> None:
    assert isolated_observability is None
    traced: list[tuple[str, str]] = []

    @contextmanager
    def observe_operation(name: str, **_kwargs: object) -> Iterator[str]:
        traced.append(("start", name))
        try:
            yield "rio145-test-op"
        finally:
            traced.append(("end", name))

    monkeypatch.setattr(codec, "operation", observe_operation)
    log_stream = io.StringIO()
    configure_logging(json=True, stream=log_stream)

    result = inspect_sysex(_fixture("A4_Test1_Init_Kit.syx"))
    with pytest.raises(FileNotFoundError):
        inspect_sysex(tmp_path / "missing.syx")

    metrics = get_metrics()
    assert result["hardware_access"] is False
    assert metrics.export_count == 2
    assert metrics.export_errors_by_code == {"offline_validation": 1}
    assert traced == [
        ("start", "rio145_inspect_sysex"),
        ("end", "rio145_inspect_sysex"),
        ("start", "rio145_inspect_sysex"),
        ("end", "rio145_inspect_sysex"),
    ]
    records = [json.loads(line) for line in log_stream.getvalue().splitlines()]
    completed = next(
        record for record in records if record["message"] == "RIO145 offline operation completed"
    )
    failed = next(
        record for record in records if record["message"] == "RIO145 offline operation failed"
    )
    assert completed["outcome"] == "completed"
    assert failed["outcome"] == "failed"
    assert failed["error_code"] == "offline_validation"
    assert failed["fingerprint"] == "boundary.rio145.offline_operation"
    assert "path" not in failed
