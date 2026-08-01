"""Semantic, construction, and app-boundary tests for the RUSH16 batch."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest
import yaml

from rytm_randomizer import app, mido_provider
from rytm_randomizer.data.rush16 import RUSH16_ANCHORS, RUSH16_STATUS_VALUES
from rytm_randomizer.devices import strategies as device_strategies
from rytm_randomizer.devices.strategies import ANALOG_RYTM_KIT_CODEC
from rytm_randomizer.reports.rush16_anchor_audition import rush16_build_entry_to_dict
from rytm_randomizer.senders import rush01_midi_transport
from rytm_randomizer.snapshot import encode_elektron_u14, pack_elektron_7bit
from rytm_randomizer.style_analysis import rush16_anchor_audition as rush16
from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    compile_rush01_midi_plan,
    parse_rush01_device_config,
)
from rytm_randomizer.style_analysis.rush01_sysex_calibration import (
    FIELD_STATUS_MAPPED,
    build_rush01_sysex_calibration,
)
from rytm_randomizer.style_analysis.rush16_anchor_audition import (
    Rush16FieldStatus,
    build_rush16_build_entry,
    build_rush16_family_document,
    build_rush16_spec_documents,
    rush16_anchor_id,
    rush16_field_readiness,
    rush16_hardware_blockers,
    validate_rush16_plan_for_apply,
    validate_rush16_spec,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = PROJECT_ROOT / "specs" / "rush16"


def _load_spec(filename: str) -> dict[str, object]:
    payload = yaml.safe_load((SPEC_ROOT / filename).read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _configured(device: str):
    tracks = (
        {
            track: index
            for index, track in enumerate(
                ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB"),
                start=1,
            )
        }
        if device == "rytm"
        else {"T1": 1, "T2": 2, "T3": 3, "T4": 4}
    )
    return parse_rush01_device_config(
        {
            device: {
                "output_port": "Exact Output",
                "input_port": "Exact Input",
                "tracks": tracks,
            }
        },
        device,
    )


def _synthetic_frame() -> bytes:
    spec = ANALOG_RYTM_KIT_CODEC.spec
    unpacked = bytearray(spec.unpacked_size)
    unpacked[: len(spec.required_unpacked_prefix)] = spec.required_unpacked_prefix
    packed = pack_elektron_7bit(bytes(unpacked))
    header = spec.required_header_prefix.ljust(spec.header_size_without_f0, b"\x00")
    checksum = sum(packed[spec.checksum_packed_start :]) & 0x3FFF
    encoded_length = len(packed) + spec.length_adjustment
    return (
        b"\xf0"
        + header
        + packed
        + encode_elektron_u14(checksum)
        + encode_elektron_u14(encoded_length)
        + b"\xf7"
    )


def _ready_rytm_spec() -> dict[str, object]:
    spec = _load_spec("01_DRY_AUTHORITY_RYTM.yaml")
    tracks = cast(dict[str, object], spec["tracks"])
    for track in ("LT", "MT", "HT"):
        track_spec = cast(dict[str, object], tracks[track])
        cast(dict[str, object], track_spec["machine"])["selection"] = "catalog_verified"
    cast(dict[str, object], cast(dict[str, object], tracks["BD"])["synth"])["Waveform"] = {
        "type": "enum",
        "requested": "waveform_1",
        "raw_midi": 1,
    }
    cast(dict[str, object], cast(dict[str, object], tracks["CH"])["synth"])["Osc Reset"] = {
        "type": "enum",
        "requested": "off",
        "raw_midi": 0,
    }
    cast(dict[str, object], cast(dict[str, object], tracks["CY"])["synth"])["Cymbal Type"] = {
        "type": "enum",
        "requested": "type_0",
        "raw_midi": 0,
    }
    return spec


def test_all_eight_specs_are_exact_covered_and_sample_free() -> None:
    filenames = sorted(path.name for path in SPEC_ROOT.glob("*.yaml"))
    assert filenames == sorted(
        [
            f"{anchor.anchor_id}_{device}.yaml"
            for anchor in RUSH16_ANCHORS
            for device in ("RYTM", "A4")
        ]
        + ["RUSH16_FAMILY.yaml"]
    )

    for filename in filenames:
        if filename == "RUSH16_FAMILY.yaml":
            continue
        device = "rytm" if filename.endswith("_RYTM.yaml") else "a4"
        spec = _load_spec(filename)
        validate_rush16_spec(spec, device)
        readiness = rush16_field_readiness(spec)
        assert readiness
        assert {entry.status for entry in readiness.values()} <= set(RUSH16_STATUS_VALUES)
        assert not any(
            entry.sound_critical and entry.status == "manual_menu_action_only"
            for entry in readiness.values()
        )
        if device == "rytm":
            tracks = spec["tracks"]
            assert isinstance(tracks, dict)
            assert all(
                track["sample"] == {"level": 0, "dependency": "none"} for track in tracks.values()
            )


def test_anchor_deltas_are_materially_distinct_and_preserve_fixed_roles() -> None:
    rytm_specs = [_load_spec(f"{anchor.anchor_id}_RYTM.yaml") for anchor in RUSH16_ANCHORS]
    a4_specs = [_load_spec(f"{anchor.anchor_id}_A4.yaml") for anchor in RUSH16_ANCHORS]
    assert len({yaml.safe_dump(spec["tracks"], sort_keys=True) for spec in rytm_specs}) == 4
    assert len({yaml.safe_dump(spec["tracks"], sort_keys=True) for spec in a4_specs}) == 4

    for spec in rytm_specs:
        tracks = spec["tracks"]
        assert tracks["BD"]["machine"]["name"] == "BD Sharp"
        assert tracks["RS"]["machine"]["name"] == "RS Hard"
        assert tracks["CP"]["machine"]["name"] == "CP Classic"
    for spec in a4_specs:
        assert tuple(spec["tracks"]) == ("T1", "T2", "T3", "T4")

    assert rytm_specs[1]["tracks"]["SD"]["machine"]["name"] == "SY Raw"
    assert rytm_specs[2]["tracks"]["SD"]["machine"]["name"] == "SY Chip"
    assert rytm_specs[3]["tracks"]["SD"]["synth"] == rytm_specs[1]["tracks"]["SD"]["synth"]


def test_configured_plans_encode_only_ordered_cc_packets_and_remain_blocked() -> None:
    for filename in sorted(SPEC_ROOT.glob("*_RYTM.yaml")) + sorted(SPEC_ROOT.glob("*_A4.yaml")):
        device = "rytm" if filename.name.endswith("_RYTM.yaml") else "a4"
        spec = yaml.safe_load(filename.read_text(encoding="utf-8"))
        plan = compile_rush01_midi_plan(device, spec, config=_configured(device))
        for field in plan.fields:
            if field.status != "ready":
                continue
            assert field.channel is not None
            assert field.ordered_midi_bytes
            assert all(packet[0] & 0xF0 == 0xB0 for packet in field.ordered_midi_bytes)
            assert all(0 <= byte <= 255 for packet in field.ordered_midi_bytes for byte in packet)
            assert all(
                0 <= data <= 127 for packet in field.ordered_midi_bytes for data in packet[1:]
            )
        blockers = rush16_hardware_blockers(spec, plan)
        assert blockers
        with pytest.raises(ValueError, match="automated calibration"):
            validate_rush16_plan_for_apply(spec, plan)


def test_rush16_app_preview_fails_before_provider_for_incomplete_anchor(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "rytm": {
                    "output_port": "Exact Output",
                    "input_port": "Exact Input",
                    "tracks": dict(_configured("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    result = app.main(
        [
            "--arm",
            "--rush01-apply-plan",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-spec",
            str(SPEC_ROOT / "01_DRY_AUTHORITY_RYTM.yaml"),
            "--rush01-disposable-target",
            "R16_01_DRY",
            "--confirm-rush01-midi-send",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert "provider not constructed" in captured.out
    assert "Program Change: 0" in captured.out
    assert "tracks.BD.machine" in captured.out
    assert "automated calibration is required" in captured.err


@dataclass
class _CaptureProvider:
    frames: tuple[bytes, ...]

    def capture_sysex_messages(
        self, _port_name: str, *, timeout_seconds: float
    ) -> tuple[bytes, ...]:
        assert timeout_seconds == 12.0
        return self.frames


class _FakeOutput:
    def __init__(self) -> None:
        self.closed = False

    def send(self, _message: object) -> None:
        raise AssertionError("send_cc is replaced by an inert recorder")

    def close(self) -> None:
        self.closed = True


class _ApplyCaptureProvider:
    def __init__(self, frame: bytes) -> None:
        self.frame = frame
        self.output = _FakeOutput()
        self.opened_outputs: list[str] = []
        self.captured_inputs: list[str] = []

    def list_output_names(self) -> tuple[str, ...]:
        return ("Exact Output",)

    def open_output(self, port_name: str) -> _FakeOutput:
        self.opened_outputs.append(port_name)
        return self.output

    def capture_sysex_messages(
        self, port_name: str, *, timeout_seconds: float
    ) -> tuple[bytes, ...]:
        assert timeout_seconds == 12.0
        self.captured_inputs.append(port_name)
        return (self.frame,)


def test_hardware_return_capture_validates_round_trip_and_never_overwrites(tmp_path: Path) -> None:
    frame = _synthetic_frame()
    destination = tmp_path / "candidate.syx"
    digest = app._capture_rush01_hardware_return(
        _CaptureProvider((frame,)),
        device="rytm",
        input_port="Exact Input",
        timeout_seconds=12.0,
        output_path=destination,
    )
    assert destination.read_bytes() == frame
    assert len(digest) == 64
    with pytest.raises(ValueError, match="already exists"):
        app._capture_rush01_hardware_return(
            _CaptureProvider((frame,)),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
            output_path=destination,
        )
    with pytest.raises(ValueError, match=".syx suffix"):
        app._capture_rush01_hardware_return(
            _CaptureProvider((frame,)),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
            output_path=tmp_path / "candidate.bin",
        )
    with pytest.raises(ValueError, match="exactly one"):
        app._capture_rush01_hardware_return(
            _CaptureProvider(()),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
            output_path=tmp_path / "missing.syx",
        )


def test_hardware_return_capture_rejects_unstable_codec(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _UnstableCodec:
        @staticmethod
        def decode_frame(frame: bytes) -> bytes:
            return frame

        @staticmethod
        def encode_frame(_decoded: bytes) -> bytes:
            return b"different"

    monkeypatch.setattr(device_strategies, "ANALOG_RYTM_KIT_CODEC", _UnstableCodec())
    with pytest.raises(ValueError, match="decode/encode stable"):
        app._capture_rush01_hardware_return(
            _CaptureProvider((_synthetic_frame(),)),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
            output_path=tmp_path / "unstable.syx",
        )


def test_hardware_return_capture_removes_temporary_file_after_replace_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "candidate.syx"

    def _fail_replace(_path: Path, _target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", _fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        app._capture_rush01_hardware_return(
            _CaptureProvider((_synthetic_frame(),)),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
            output_path=destination,
        )
    assert not destination.with_suffix(".syx.tmp").exists()


def test_existing_armed_operation_can_apply_complete_fake_plan_then_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec = _ready_rytm_spec()
    spec_path = tmp_path / "ready.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=False), encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "rytm": {
                    "output_port": "Exact Output",
                    "input_port": "Exact Input",
                    "tracks": dict(_configured("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    provider = _ApplyCaptureProvider(_synthetic_frame())
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, control, value, *, channel, sleep: sent.append((channel, control, value)),
    )
    capture_path = tmp_path / "captured.syx"
    result = app.main(
        [
            "--arm",
            "--rush01-apply-plan",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-spec",
            str(spec_path),
            "--rush01-disposable-target",
            "R16_01_DRY",
            "--rush01-capture-output",
            str(capture_path),
            "--rush01-capture-timeout",
            "12",
            "--rush01-delay-ms",
            "0",
            "--confirm-rush01-midi-send",
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert sent
    assert provider.opened_outputs == ["Exact Output"]
    assert provider.output.closed
    assert provider.captured_inputs == ["Exact Input"]
    assert capture_path.read_bytes() == provider.frame
    assert "output port closed" in output
    assert "This is not final" in output


def test_custom_capture_requires_configured_input_before_provider(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec_path = tmp_path / "ready.yaml"
    spec_path.write_text(yaml.safe_dump(_ready_rytm_spec(), sort_keys=False), encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "rytm": {
                    "output_port": "Exact Output",
                    "tracks": dict(_configured("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    result = app.main(
        [
            "--arm",
            "--rush01-apply-plan",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-spec",
            str(spec_path),
            "--rush01-disposable-target",
            "R16_01_DRY",
            "--rush01-capture-output",
            str(tmp_path / "captured.syx"),
            "--confirm-rush01-midi-send",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert "provider not constructed" in captured.out
    assert "input_port is required" in captured.err


def test_custom_capture_failure_is_reported_after_fake_apply(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    spec_path = tmp_path / "ready.yaml"
    spec_path.write_text(yaml.safe_dump(_ready_rytm_spec(), sort_keys=False), encoding="utf-8")
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        yaml.safe_dump(
            {
                "rytm": {
                    "output_port": "Exact Output",
                    "input_port": "Exact Input",
                    "tracks": dict(_configured("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    provider = _ApplyCaptureProvider(_synthetic_frame())
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        app,
        "_capture_rush01_hardware_return",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("capture rejected")),
    )
    result = app.main(
        [
            "--arm",
            "--rush01-apply-plan",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-spec",
            str(spec_path),
            "--rush01-disposable-target",
            "R16_01_DRY",
            "--rush01-capture-output",
            str(tmp_path / "captured.syx"),
            "--rush01-delay-ms",
            "0",
            "--confirm-rush01-midi-send",
        ]
    )
    captured = capsys.readouterr()
    assert result == 1
    assert provider.opened_outputs == ["Exact Output"]
    assert provider.output.closed
    assert "capture failed safely: capture rejected" in captured.err


@pytest.mark.parametrize(
    "extra",
    (
        ("--rush01-spec", "x.yaml"),
        ("--rush01-disposable-target", "target"),
        ("--rush01-capture-output", "capture.syx"),
        ("--rush01-capture-timeout", "301"),
        ("--rush01-capture-timeout", "12"),
        (
            "--rush01-spec",
            str(SPEC_ROOT / "01_DRY_AUTHORITY_RYTM.yaml"),
            "--rush01-disposable-target",
            "R16_01_DRY",
            "--rush01-track",
            "BD",
        ),
    ),
)
def test_custom_apply_options_fail_before_provider_without_required_context(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    extra: tuple[str, ...],
) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert (
        app.main(
            [
                "--arm",
                "--rush01-apply-plan",
                "--rush01-device",
                "rytm",
                "--rush01-config",
                str(config_path),
                "--confirm-rush01-midi-send",
                *extra,
            ]
        )
        == 1
    )


def test_rush01_capture_config_rejects_invalid_input_port_values() -> None:
    tracks = dict(_configured("rytm").track_channels)
    for invalid in (1, "REPLACE_WITH_EXACT_INPUT_PORT"):
        payload = {
            "rytm": {
                "output_port": "Exact Output",
                "input_port": invalid,
                "tracks": tracks,
            }
        }
        with pytest.raises(ValueError, match="input_port"):
            parse_rush01_device_config(payload, "rytm")


def test_rush01_preview_rejects_non_plan() -> None:
    with pytest.raises(TypeError, match="Rush01MidiPlan"):
        app._write_rush01_plan_preview(
            object(),
            spec_path=SPEC_ROOT / "01_DRY_AUTHORITY_RYTM.yaml",
            disposable_target=None,
        )


def test_rush16_defensive_spec_and_readiness_validation() -> None:
    source_hashes = {
        "specs/RUSH01_RYTM.yaml": sha256(
            (PROJECT_ROOT / "specs" / "RUSH01_RYTM.yaml").read_bytes()
        ).hexdigest(),
        "specs/RUSH01_A4.yaml": sha256(
            (PROJECT_ROOT / "specs" / "RUSH01_A4.yaml").read_bytes()
        ).hexdigest(),
    }
    baseline = {
        "rytm": json.loads(
            (PROJECT_ROOT / "output" / "RUSH01_RYTM_mapping_status.json").read_text()
        ),
        "a4": json.loads((PROJECT_ROOT / "output" / "RUSH01_A4_mapping_status.json").read_text()),
    }
    with pytest.raises(ValueError, match="required for a4"):
        build_rush16_spec_documents(
            yaml.safe_load((PROJECT_ROOT / "specs" / "RUSH01_RYTM.yaml").read_text()),
            yaml.safe_load((PROJECT_ROOT / "specs" / "RUSH01_A4.yaml").read_text()),
            source_hashes=source_hashes,
            baseline_mapping_statuses={"rytm": baseline["rytm"]},
        )
    with pytest.raises(ValueError, match="SHA-256"):
        build_rush16_family_document({})

    base = _load_spec("01_DRY_AUTHORITY_RYTM.yaml")
    bad_version = deepcopy(base)
    bad_version["rush16"]["batch_version"] = "unsupported"
    with pytest.raises(ValueError, match="batch version"):
        validate_rush16_spec(bad_version, "rytm")
    bad_device = deepcopy(base)
    bad_device["rush16"]["device"] = "a4"
    with pytest.raises(ValueError, match="device does not match"):
        validate_rush16_spec(bad_device, "rytm")
    missing_status = deepcopy(base)
    missing_status["rush16"]["semantic_field_statuses"].pop("track_levels.BD")
    with pytest.raises(ValueError, match="coverage mismatch"):
        validate_rush16_spec(missing_status, "rytm")
    critical_manual = deepcopy(base)
    critical_manual["rush16"]["semantic_field_statuses"]["track_levels.BD"][
        "status"
    ] = "manual_menu_action_only"
    with pytest.raises(ValueError, match="forbidden for sound"):
        validate_rush16_spec(critical_manual, "rytm")
    sample_dependency = deepcopy(base)
    sample_dependency["tracks"]["BD"]["sample"]["dependency"] = "external"
    with pytest.raises(ValueError, match="sample level 0"):
        validate_rush16_spec(sample_dependency, "rytm")


@pytest.mark.parametrize(
    ("mutator", "error"),
    (
        (lambda statuses: statuses.update({"": next(iter(statuses.values()))}), "paths"),
        (
            lambda statuses: statuses[next(iter(statuses))].update({"status": "unknown"}),
            "unsupported RUSH16 status",
        ),
        (
            lambda statuses: statuses[next(iter(statuses))].update({"sound_critical": 1}),
            "sound_critical",
        ),
        (
            lambda statuses: statuses[next(iter(statuses))].update({"reason": ""}),
            "reason is required",
        ),
        (
            lambda statuses: statuses[next(iter(statuses))].update({"evidence_source": ""}),
            "evidence source is required",
        ),
    ),
)
def test_rush16_field_readiness_rejects_malformed_records(mutator: object, error: str) -> None:
    spec = _load_spec("01_DRY_AUTHORITY_RYTM.yaml")
    statuses = spec["rush16"]["semantic_field_statuses"]
    cast(object, mutator)(statuses)
    with pytest.raises(ValueError, match=error):
        rush16_field_readiness(spec)


def test_rush16_internal_fail_closed_edges_and_ready_build_entry() -> None:
    spec = _ready_rytm_spec()
    configured_plan = compile_rush01_midi_plan("rytm", spec, config=_configured("rytm"))
    assert rush16_anchor_id(spec) == "01_DRY_AUTHORITY"
    invalid_anchor = deepcopy(spec)
    invalid_anchor["rush16"]["anchor_id"] = "UNKNOWN"
    with pytest.raises(ValueError, match="unknown anchor"):
        rush16_anchor_id(invalid_anchor)

    unconfigured_plan = compile_rush01_midi_plan("rytm", spec)
    with pytest.raises(ValueError, match="configured channels"):
        validate_rush16_plan_for_apply(spec, unconfigured_plan)
    missing_field = deepcopy(spec)
    missing_field["rush16"]["semantic_field_statuses"]["tracks.BD.unmapped"] = {
        "status": "blocked_unverified",
        "sound_critical": True,
        "reason": "test",
        "evidence_source": "test",
    }
    assert "tracks.BD.unmapped" in rush16_hardware_blockers(missing_field, configured_plan)

    mapping_gaps = (PROJECT_ROOT / "output" / "RUSH01_mapping_gaps.md").read_text()
    calibration = build_rush01_sysex_calibration(
        "rytm",
        spec,
        mapping_gaps_text=mapping_gaps,
        reference_frame=_synthetic_frame(),
        codec=ANALOG_RYTM_KIT_CODEC,
    )
    promoted = replace(
        calibration,
        fields=tuple(
            replace(field, status=FIELD_STATUS_MAPPED) if field.critical else field
            for field in calibration.fields
        ),
    )
    entry = build_rush16_build_entry(
        anchor_id="01_DRY_AUTHORITY",
        device="rytm",
        spec_filename="01_DRY_AUTHORITY_RYTM.yaml",
        spec_bytes=yaml.safe_dump(spec).encode(),
        spec=spec,
        plan=configured_plan,
        sysex_status=promoted,
        hardware_capture_configured=True,
    )
    assert entry.direct_sysex_ready
    assert entry.hardware_assisted_ready
    assert entry.status_counts["midi_apply_ready"]
    assert rush16_build_entry_to_dict(entry)["construction_strategy"] == "direct_sysex"
    hardware_only = replace(entry, direct_sysex_ready=False)
    assert rush16_build_entry_to_dict(hardware_only)["construction_strategy"] == (
        "hardware_assisted"
    )


def test_rush16_private_helpers_reject_unmapped_shapes() -> None:
    base = _load_spec("01_DRY_AUTHORITY_RYTM.yaml")
    plan = compile_rush01_midi_plan("rytm", base)
    preserve = next(field for field in plan.fields if field.status == "preserve_reference")
    ready = next(field for field in plan.fields if field.status == "ready")
    kit_name = next(
        field for field in plan.fields if field.semantic_path == "build_policy.kit_name"
    )
    assert (
        rush16._field_status(
            preserve.semantic_path,
            critical=False,
            sysex_entry=None,
            midi_field=preserve,
            requested=preserve.requested_value,
        )[0]
        == "writer_ready"
    )
    assert (
        rush16._field_status(
            "missing",
            critical=True,
            sysex_entry=None,
            midi_field=None,
            requested=0,
        )[0]
        == "blocked_unverified"
    )
    assert (
        rush16._field_status(
            kit_name.semantic_path,
            critical=False,
            sysex_entry=None,
            midi_field=kit_name,
            requested=kit_name.requested_value,
        )[0]
        == "manual_menu_action_only"
    )
    unknown = replace(ready, status=cast(Rush16FieldStatus, "unknown"))
    assert (
        rush16._field_status(
            ready.semantic_path,
            critical=True,
            sysex_entry=None,
            midi_field=unknown,
            requested=0,
        )[0]
        == "blocked_unverified"
    )
    assert not rush16._baseline_mapping_status_by_path({"fields": [{"semantic_path": 1}]})
    with pytest.raises(ValueError, match="must be a sequence"):
        rush16._baseline_mapping_status_by_path({"fields": "bad"})
    with pytest.raises(ValueError, match="does not exist"):
        rush16.rush16_value_at_path(base, "tracks.BD.missing")
    with pytest.raises(ValueError, match="parent path"):
        rush16._set_value_at_path(base, "spec_version.child", 1)
    with pytest.raises(ValueError, match="does not exist"):
        rush16._set_value_at_path(base, "tracks.BD.missing", 1)
