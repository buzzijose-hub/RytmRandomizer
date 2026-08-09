from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable

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
from rytm_randomizer.devices.rio145_recipes import compile_a4_kit_recipe
from rytm_randomizer.snapshot import ElektronNativeObjectMessage

pytestmark = pytest.mark.fast

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures" / "rio145"
SPECS = ROOT / "specs" / "rio145"


def _fixture(name: str) -> Path:
    return FIXTURES / name


@dataclass(frozen=True)
class _FakeBuildResult:
    message: ElektronNativeObjectMessage
    changed_payload_offsets: tuple[int, ...] = ()
    changed_outside_declared_edit_regions: tuple[int, ...] = ()
    changed_payload_byte_count: int = 0


def _a4_compilation() -> tuple[ElektronNativeObjectMessage, _FakeBuildResult]:
    _, baseline = codec._single_message(_fixture("A4_Test1_Init_Kit.syx"))
    recipe = codec._load_json_mapping(SPECS / "come_to_rio_a4_core.json")
    result = compile_a4_kit_recipe(baseline, recipe)
    return baseline, _FakeBuildResult(
        message=result.message,
        changed_payload_offsets=result.changed_payload_offsets,
        changed_outside_declared_edit_regions=result.changed_outside_declared_edit_regions,
        changed_payload_byte_count=result.changed_payload_byte_count,
    )


def test_multi_frame_inspection_and_roundtrip_are_strict() -> None:
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
    with pytest.raises(Rio145OfflineError, match="unterminated"):
        split_elektron_sysex(frames[0][:-1])
    with pytest.raises(Rio145OfflineError, match="exactly one"):
        codec._single_message(source)


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
        codec._load_json_mapping(source)

    monkeypatch.setattr(codec.json, "loads", lambda _text: {1: "value"})
    with pytest.raises(Rio145OfflineError, match="string keys"):
        codec._load_json_mapping(source)


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
    ) -> _FakeBuildResult:
        return replace(compiled, changed_outside_declared_edit_regions=(7,))

    with pytest.raises(Rio145OfflineError, match="outside declared edit regions"):
        codec._build_kit(
            device="analog_four_mkii",
            reference_path=reference,
            recipe_path=recipe,
            destination_slot=0,
            output_path=tmp_path / "outside.syx",
            overwrite=False,
            compiler=outside_compiler,
        )

    altered_payload = bytearray(compiled.message.payload)
    altered_payload[0] ^= 1
    altered = replace(compiled, message=compiled.message.with_payload(altered_payload))
    results = iter((compiled, altered))

    def nondeterministic_compiler(
        _baseline: ElektronNativeObjectMessage, _recipe: Mapping[str, object]
    ) -> _FakeBuildResult:
        return next(results)

    with pytest.raises(Rio145OfflineError, match="different output bytes"):
        codec._build_kit(
            device="analog_four_mkii",
            reference_path=reference,
            recipe_path=recipe,
            destination_slot=0,
            output_path=tmp_path / "nondeterministic.syx",
            overwrite=False,
            compiler=nondeterministic_compiler,
        )


@pytest.mark.parametrize("failure", ["reserialization", "semantic"])
def test_build_guardrails_verify_reparsed_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    baseline, compiled = _a4_compilation()
    output = compiled.message.with_slot(0).to_bytes()

    class _Reparsed:
        payload = compiled.message.payload if failure == "reserialization" else b"different payload"
        slot = 0

        def to_bytes(self) -> bytes:
            return b"different wire" if failure == "reserialization" else output

    class _Parser:
        @classmethod
        def from_bytes(cls, _frame: bytes) -> _Reparsed:
            return _Reparsed()

    monkeypatch.setattr(codec, "_single_message", lambda _path: (b"reference", baseline))
    monkeypatch.setattr(codec, "ElektronNativeObjectMessage", _Parser)

    expected = "reserialization" if failure == "reserialization" else "semantic payload"
    with pytest.raises(Rio145OfflineError, match=expected):
        codec._build_kit(
            device="analog_four_mkii",
            reference_path=tmp_path / "reference.syx",
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            destination_slot=0,
            output_path=tmp_path / "output.syx",
            overwrite=False,
            compiler=lambda _baseline, _recipe: compiled,
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


def test_target_return_validation_rejects_outside_edits_and_payload_mismatch() -> None:
    baseline, compiled = _a4_compilation()

    def outside_compiler(
        _baseline: ElektronNativeObjectMessage, _recipe: Mapping[str, object]
    ) -> _FakeBuildResult:
        return replace(compiled, changed_outside_declared_edit_regions=(1,))

    with pytest.raises(Rio145OfflineError, match="outside declared edit regions"):
        codec._validate_target_return(
            device="analog_four_mkii",
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=_fixture("A4_RIO145_CORE_RETURN_Kit.syx"),
            compiler=outside_compiler,
        )

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
    baseline, compiled = _a4_compilation()

    class _Returned:
        payload = compiled.message.payload
        slot = 11

        def to_bytes(self) -> bytes:
            return b"changed"

    calls = iter(((b"reference", baseline), (b"returned", _Returned())))
    monkeypatch.setattr(codec, "_single_message", lambda _path: next(calls))
    with pytest.raises(Rio145OfflineError, match="roundtrip"):
        codec._validate_target_return(
            device="analog_four_mkii",
            reference_path=tmp_path / "reference.syx",
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=tmp_path / "returned.syx",
            compiler=lambda _baseline, _recipe: compiled,
        )

    monkeypatch.undo()
    returned = replace(compiled.message, device_id=(compiled.message.device_id + 1) % 128)
    returned_path = tmp_path / "header-mismatch.syx"
    returned_path.write_bytes(returned.with_slot(11).to_bytes())
    with pytest.raises(Rio145OfflineError, match="normalizing the destination slot"):
        codec._validate_target_return(
            device="analog_four_mkii",
            reference_path=_fixture("A4_Test1_Init_Kit.syx"),
            recipe_path=SPECS / "come_to_rio_a4_core.json",
            returned_path=returned_path,
            compiler=lambda _baseline, _recipe: compiled,
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
        codec, "_OXI_MANIFEST_SHA256", codec._rio145_sha256(manifest_path.read_bytes())
    )
    monkeypatch.setattr(codec, "_OXI_EVENTS_SHA256", codec._rio145_sha256(events_path.read_bytes()))
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
    with pytest.raises(Rio145OfflineError, match="string keys"):
        codec._rio145_require_mapping({1: "value"}, "mapping")
    with pytest.raises(Rio145OfflineError, match="must be an array"):
        codec._rio145_require_sequence(b"bytes", "sequence")

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
