"""Passive saved-kit calibration coverage for the RUSH01 workbench."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
from typing import cast

import pytest
import yaml

from rytm_randomizer.data.analog_four_sysex_calibration import (
    ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS,
)
from rytm_randomizer.devices.strategies import (
    ANALOG_FOUR_KIT_CODEC,
    ANALOG_RYTM_KIT_CODEC,
)
from rytm_randomizer.reports import rush01_sysex_calibration as calibration_report
from rytm_randomizer.snapshot.envelope import (
    DecodedElektronKitFrame,
    ElektronKitCodec,
    encode_elektron_u14,
    pack_elektron_7bit,
)
from rytm_randomizer.style_analysis import rush01_sysex_calibration as calibration
from rytm_randomizer.style_analysis.rush01_midi_compiler import compile_rush01_midi_plan

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_yaml(filename: str) -> object:
    return yaml.safe_load((PROJECT_ROOT / "specs" / filename).read_text(encoding="utf-8"))


def _mapping_gaps() -> str:
    return (PROJECT_ROOT / "output" / "RUSH01_mapping_gaps.md").read_text(encoding="utf-8")


def _reference(filename: str) -> bytes:
    codec = (
        ANALOG_RYTM_KIT_CODEC if filename == "RYTM_Test1_Init_Kit.syx" else ANALOG_FOUR_KIT_CODEC
    )
    spec = codec.spec
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


def _build(
    device: str,
    *,
    capture_frames: dict[str, bytes] | None = None,
) -> calibration.Rush01SysexCalibrationStatus:
    if device == "rytm":
        return calibration.build_rush01_sysex_calibration(
            device,
            _load_yaml("RUSH01_RYTM.yaml"),
            mapping_gaps_text=_mapping_gaps(),
            reference_frame=_reference("RYTM_Test1_Init_Kit.syx"),
            codec=ANALOG_RYTM_KIT_CODEC,
            capture_frames=capture_frames,
        )
    return calibration.build_rush01_sysex_calibration(
        device,
        _load_yaml("RUSH01_A4.yaml"),
        mapping_gaps_text=_mapping_gaps(),
        reference_frame=_reference("A4_Test1_Init_Kit.syx"),
        codec=ANALOG_FOUR_KIT_CODEC,
        capture_frames=capture_frames,
    )


@pytest.fixture(scope="module")
def statuses() -> tuple[
    calibration.Rush01SysexCalibrationStatus,
    calibration.Rush01SysexCalibrationStatus,
]:
    return _build("rytm"), _build("a4")


def _field(
    status: calibration.Rush01SysexCalibrationStatus,
    path: str,
) -> calibration.Rush01SysexCalibrationField:
    matches = tuple(field for field in status.fields if field.semantic_path == path)
    assert len(matches) == 1
    return matches[0]


def _target(
    field: calibration.Rush01SysexCalibrationField,
    label: str,
) -> calibration.Rush01SysexCaptureTarget:
    matches = tuple(target for target in field.capture_targets if target.observation_label == label)
    assert len(matches) == 1
    return matches[0]


def _patch_unpacked_byte(
    codec: ElektronKitCodec,
    frame: bytes,
    offset: int,
) -> bytes:
    decoded = codec.decode_frame(frame)
    unpacked = bytearray(decoded.unpacked)
    unpacked[offset] = 1 if unpacked[offset] != 1 else 2
    return codec.encode_frame(decoded, unpacked=bytes(unpacked))


def test_statuses_preserve_reference_round_trips_and_exact_readiness_counts(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, a4 = statuses
    rytm_payload = calibration.rush01_sysex_calibration_to_dict(rytm)
    a4_payload = calibration.rush01_sysex_calibration_to_dict(a4)

    assert rytm.reference.byte_identical is True
    assert rytm.reference.byte_count == 2998
    assert rytm.reference.sha256 == sha256(_reference("RYTM_Test1_Init_Kit.syx")).hexdigest()
    assert rytm_payload["summary"] == {
        "critical_fields": 312,
        "mapped_fields": 180,
        "preserve_reference_fields": 1,
        "capture_required_fields": 128,
        "candidate_only_fields": 3,
        "unresolved_critical_fields": 131,
        "expected_changed_captures": 140,
        "supplied_differential_dumps": 0,
        "valid_differential_dumps": 0,
        "invalid_differential_dumps": 0,
        "promoted_mappings_from_this_run": 0,
    }

    assert a4.reference.byte_identical is True
    assert a4.reference.byte_count == 2770
    assert a4.reference.sha256 == sha256(_reference("A4_Test1_Init_Kit.syx")).hexdigest()
    assert a4_payload["summary"] == {
        "critical_fields": 244,
        "mapped_fields": 0,
        "preserve_reference_fields": 4,
        "capture_required_fields": 224,
        "candidate_only_fields": 16,
        "unresolved_critical_fields": 240,
        "expected_changed_captures": 254,
        "supplied_differential_dumps": 0,
        "valid_differential_dumps": 0,
        "invalid_differential_dumps": 0,
        "promoted_mappings_from_this_run": 0,
    }
    assert rytm.writer_ready is False
    assert a4.writer_ready is False
    assert rytm.final_sysex_generated is False
    assert a4.final_sysex_generated is False


def test_current_specs_scope_gap_reconciliation_and_have_unique_critical_paths(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, a4 = statuses

    assert rytm.superseded_mapping_gap_paths == (
        "tracks.BD.synth.WAV",
        "tracks.BT.synth.SNP",
        "tracks.CB.synth.PW1",
        "tracks.CB.synth.PW2",
        "tracks.CH.synth.RST",
        "tracks.CY.synth.TYP",
    )
    assert a4.superseded_mapping_gap_paths == ()
    assert all("tracks.T" not in path for path in rytm.mapping_gap_paths)
    assert all(
        path.startswith("tracks.T") for path in a4.mapping_gap_paths if path.startswith("tracks.")
    )

    for status in statuses:
        critical = tuple(field for field in status.fields if field.critical)
        assert len({field.semantic_path for field in critical}) == len(critical)
        for field in critical:
            if field.status in {
                calibration.FIELD_STATUS_CAPTURE_REQUIRED,
                calibration.FIELD_STATUS_CANDIDATE_ONLY,
            }:
                assert field.evidence_needed
                assert field.capture_targets or field.shared_capture_group_owner is not None


def test_rytm_mapped_and_blocked_fields_are_distinguished_without_guessing(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, _ = statuses
    frequency = _field(rytm, "tracks.BD.filter.FRQ")
    snap_type = _field(rytm, "tracks.BT.synth.Snap Type")
    lt_source = _field(rytm, "tracks.LT.synth.Level")
    samples = tuple(field for field in rytm.fields if ".sample.level" in field.semantic_path)

    assert frequency.status == calibration.FIELD_STATUS_MAPPED
    assert frequency.candidate_unpacked_offset == 114
    assert frequency.candidate_packed_data_offset == 131
    assert frequency.candidate_frame_offset == 141
    assert frequency.capture_targets == ()

    assert snap_type.status == calibration.FIELD_STATUS_PRESERVE
    assert snap_type.requested_value == {
        "type": "enum",
        "requested": "preserve_reference",
        "raw_midi": "learn_required",
    }
    assert lt_source.status == calibration.FIELD_STATUS_CAPTURE_REQUIRED
    assert "--validate-one-cc" in _target(lt_source, "requested").mutation_command

    assert len(samples) == 12
    assert {field.requested_value for field in samples} == {0}
    assert {field.status for field in samples} == {calibration.FIELD_STATUS_CAPTURE_REQUIRED}
    assert all("zero playback" in field.reason for field in samples)


def test_a4_existing_calibrations_remain_candidate_only_and_fixture_backed(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    _, a4 = statuses
    frequency = _field(a4, "tracks.T1.filter_1.frequency")
    fixtures = calibration.analog_four_candidate_fixture_payloads()

    assert frequency.status == calibration.FIELD_STATUS_CANDIDATE_ONLY
    assert frequency.candidate_unpacked_offset is None
    assert frequency.candidate_packed_data_offset == 156
    assert frequency.candidate_unpacked_stride == 350
    assert frequency.candidate_packed_stride == 400
    assert len(fixtures) == len(ANALOG_FOUR_SYSEX_FIELD_CALIBRATIONS) == 4
    assert set(fixtures) == {
        "analog_four_filter1_frequency",
        "analog_four_filter1_resonance",
        "analog_four_filter2_frequency",
        "analog_four_filter2_resonance",
    }
    assert all(payload["writer_ready"] is False for payload in fixtures.values())
    assert all(payload["evidence"] for payload in fixtures.values())


def test_differential_dump_reports_every_byte_view_and_never_promotes() -> None:
    initial = _build("rytm")
    reference = _reference("RYTM_Test1_Init_Kit.syx")
    owner = _field(initial, "track_levels.BD")
    witness = _field(initial, "track_levels.SD")
    owner_target = _target(owner, "mid")
    witness_target = _target(witness, "mid")
    captures = {
        owner_target.filename: _patch_unpacked_byte(ANALOG_RYTM_KIT_CODEC, reference, 300),
        witness_target.filename: _patch_unpacked_byte(ANALOG_RYTM_KIT_CODEC, reference, 300 + 162),
        "calibration/sysex/rytm/unplanned.syx": reference,
    }

    status = _build("rytm", capture_frames=captures)
    payload = calibration.rush01_sysex_calibration_to_dict(status)
    assigned = tuple(diff for diff in status.capture_diffs if diff.semantic_path is not None)
    unplanned = next(diff for diff in status.capture_diffs if diff.semantic_path is None)
    detected = tuple(
        stride
        for stride in status.stride_candidates
        if stride.source.startswith("supplied differential dumps")
    )

    assert len(assigned) == 2
    assert all(diff.valid for diff in assigned)
    assert all(len(diff.unpacked_changes) == 1 for diff in assigned)
    assert all(diff.packed_changes for diff in assigned)
    assert all(diff.integrity_changes for diff in assigned)
    assert all(diff.header_changes == () for diff in assigned)
    assert unplanned.valid is True
    assert unplanned.unpacked_changes == ()
    assert detected
    assert detected[0].capture_group == "rytm.track_level"
    assert detected[0].unpacked_stride == 162
    assert detected[0].confirmed_on_second_track is True
    assert detected[0].promoted is False
    assert payload["summary"]["promoted_mappings_from_this_run"] == 0


def test_invalid_differential_is_reported_with_expected_semantic_metadata() -> None:
    initial = _build("rytm")
    field = _field(initial, "track_levels.BD")
    target = _target(field, "min")
    status = _build("rytm", capture_frames={target.filename: b"\xf0\xf7"})
    diff = status.capture_diffs[0]

    assert diff.valid is False
    assert diff.semantic_path == "track_levels.BD"
    assert diff.track == "BD"
    assert diff.observation_label == "min"
    assert diff.observation_value == "0"
    assert diff.error
    assert diff.header_changes == ()
    assert diff.packed_changes == ()
    assert diff.unpacked_changes == ()
    assert diff.integrity_changes == ()


def test_reports_state_capture_protocol_reuse_and_hardware_safety(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, a4 = statuses
    rytm_matrix = calibration_report.format_rush01_capture_matrix(rytm)
    a4_matrix = calibration_report.format_rush01_capture_matrix(a4)
    report = calibration_report.format_rush01_sysex_calibration_report(rytm, a4)

    assert "manually select XT Classic" in rytm_matrix
    assert "manually select XT Classic" not in a4_matrix
    assert "MidoMidiPortProvider.capture_sysex_messages" in rytm_matrix
    assert "<OPERATOR_TIMEOUT_SECONDS>" in a4_matrix
    assert "rytm_randomizer.midi_io.send_cc" in report
    assert "rytm_randomizer/senders/rush01_midi_transport.py" in report
    assert "calibration support" in report
    assert "No MIDI backend was imported or opened" in report
    assert "No MIDI data or SysEx was transmitted" in report
    assert "Neither file is generated" in report


def test_matrix_renders_valid_and_invalid_supplied_differentials() -> None:
    initial = _build("rytm")
    field = _field(initial, "track_levels.BD")
    valid_target = _target(field, "mid")
    invalid_target = _target(field, "max")
    reference = _reference("RYTM_Test1_Init_Kit.syx")
    status = _build(
        "rytm",
        capture_frames={
            valid_target.filename: _patch_unpacked_byte(ANALOG_RYTM_KIT_CODEC, reference, 300),
            invalid_target.filename: b"not sysex",
        },
    )
    matrix = calibration_report.format_rush01_capture_matrix(status)

    assert "Valid saved-kit frame: `true`" in matrix
    assert "Unpacked object changes: offset 0x012C" in matrix
    assert "Valid saved-kit frame: `false`" in matrix
    assert "Error:" in matrix


def test_defensive_validation_rejects_unsupported_inputs() -> None:
    with pytest.raises(ValueError, match="device must"):
        _build("not-an-elektron")
    with pytest.raises(ValueError, match="equal lengths"):
        calibration._byte_changes(b"a", b"ab")
    with pytest.raises(ValueError, match="must be a mapping"):
        calibration._require_mapping([], path="test.value")
    with pytest.raises(ValueError, match="machine name"):
        calibration._rytm_machine_profile(123)
    with pytest.raises(KeyError, match="unknown Rytm machine"):
        calibration._rytm_machine_profile("not a machine")
    with pytest.raises(KeyError, match="unsupported A4 semantic path"):
        calibration._a4_binding_for_path("effects.delay.time")
    with pytest.raises(KeyError, match="unknown A4 candidate"):
        calibration._a4_candidate_capture_group("not a candidate")


def test_matching_promoted_rytm_machine_is_already_mapped() -> None:
    spec = cast(dict[str, object], _load_yaml("RUSH01_RYTM.yaml"))
    plan = compile_rush01_midi_plan("rytm", spec)
    field = next(item for item in plan.fields if item.semantic_path == "tracks.BD.machine")
    tracks = cast(dict[str, object], spec["tracks"])
    track_spec = cast(dict[str, object], tracks["BD"])
    machine = cast(dict[str, object], track_spec["machine"])
    profile = calibration._rytm_machine_profile(machine["name"])
    reference = _reference("RYTM_Test1_Init_Kit.syx")
    snapshot = calibration.AnalogRytmSnapshotDecoder().decode(reference[1:-1], slot=0)
    facts = dict(snapshot.machine_facts.facts_by_pad)
    facts[1] = replace(
        facts[1],
        decoded_machine_value=profile.machine_value,
        promoted=True,
    )
    promoted_snapshot = replace(
        snapshot,
        machine_facts=replace(snapshot.machine_facts, facts_by_pad=facts, promoted=True),
    )

    result = calibration._classify_rytm_machine_field(
        field,
        track_spec=track_spec,
        track_index=0,
        snapshot=promoted_snapshot,
    )

    assert result.status == calibration.FIELD_STATUS_MAPPED
    assert result.evidence_needed == ()


def test_reference_round_trip_failure_stops_before_field_generation() -> None:
    class NonRoundTripCodec:
        def decode_frame(self, frame: bytes) -> DecodedElektronKitFrame:
            return ANALOG_RYTM_KIT_CODEC.decode_frame(frame)

        def encode_frame(
            self,
            decoded: DecodedElektronKitFrame,
            *,
            unpacked: bytes | None = None,
        ) -> bytes:
            del unpacked
            return decoded.original_frame + b"\x00"

    with pytest.raises(ValueError, match="round trip is not identical"):
        calibration.build_rush01_sysex_calibration(
            "rytm",
            _load_yaml("RUSH01_RYTM.yaml"),
            mapping_gaps_text=_mapping_gaps(),
            reference_frame=_reference("RYTM_Test1_Init_Kit.syx"),
            codec=cast(ElektronKitCodec, NonRoundTripCodec()),
        )


def test_small_pure_helpers_cover_no_candidate_and_no_command_cases(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, a4 = statuses
    preserve = _field(a4, "tracks.T1.filter_envelope.gate_length")
    orphan = replace(
        preserve,
        status=calibration.FIELD_STATUS_CAPTURE_REQUIRED,
        capture_targets=(),
        shared_capture_group_owner=None,
    )

    assert calibration._constant_offset_delta((), ()) is None
    assert (
        calibration._constant_offset_delta(
            (calibration.Rush01SysexByteChange(2, 0, 1),),
            (
                calibration.Rush01SysexByteChange(3, 0, 1),
                calibration.Rush01SysexByteChange(4, 0, 1),
            ),
        )
        is None
    )
    assert (
        calibration._constant_offset_delta(
            (
                calibration.Rush01SysexByteChange(1, 0, 1),
                calibration.Rush01SysexByteChange(2, 0, 1),
            ),
            (
                calibration.Rush01SysexByteChange(4, 0, 1),
                calibration.Rush01SysexByteChange(6, 0, 1),
            ),
        )
        is None
    )
    assert (
        calibration._constant_offset_delta(
            (calibration.Rush01SysexByteChange(3, 0, 1),),
            (calibration.Rush01SysexByteChange(2, 0, 1),),
        )
        is None
    )
    assert calibration._capture_slug("***") == "value"
    assert calibration._requested_text({"requested": "keep"}) == "keep"
    assert calibration._requested_text({"name": "named"}) == "named"
    assert calibration._requested_text({}) == "{}"
    assert calibration._requested_text(True) == "true"
    assert calibration._requested_text(False) == "false"
    assert calibration._json_value((1, [2], object()))[:2] == [1, [2]]
    assert calibration_report._candidate_location(preserve) == "unknown"
    assert calibration_report._changes(()) == "none"
    assert "No additional command" in "\n".join(
        calibration_report._capture_group_lines("test.group", (orphan,))
    )
    assert calibration_report._inline_paths(()) == "none"


def test_internal_classifiers_reject_plan_fields_without_tracks() -> None:
    rytm_spec = _load_yaml("RUSH01_RYTM.yaml")
    rytm_plan = compile_rush01_midi_plan("rytm", rytm_spec)
    rytm_field = next(field for field in rytm_plan.fields if field.track is not None)
    with pytest.raises(ValueError, match="Rytm critical field has no track"):
        calibration._classify_rytm_fields(
            (replace(rytm_field, track=None),),
            rytm_spec,
            _reference("RYTM_Test1_Init_Kit.syx"),
            ANALOG_RYTM_KIT_CODEC,
        )

    a4_spec = _load_yaml("RUSH01_A4.yaml")
    a4_plan = compile_rush01_midi_plan("a4", a4_spec)
    a4_field = next(field for field in a4_plan.fields if field.track is not None)
    with pytest.raises(ValueError, match="A4 critical field has no track"):
        calibration._classify_a4_fields((replace(a4_field, track=None),))


def test_rytm_unknown_layout_and_source_mapping_remain_unsupported(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    spec = _load_yaml("RUSH01_RYTM.yaml")
    assert isinstance(spec, dict)
    tracks = spec["tracks"]
    assert isinstance(tracks, dict)
    plan = compile_rush01_midi_plan("rytm", spec)
    filter_field = next(
        field for field in plan.fields if field.semantic_path == "tracks.BD.filter.FRQ"
    )
    source_field = next(
        field for field in plan.fields if field.semantic_path == "tracks.BD.synth.Level"
    )
    decoded = ANALOG_RYTM_KIT_CODEC.decode_frame(_reference("RYTM_Test1_Init_Kit.syx"))

    monkeypatch.setattr(calibration, "RYTM_SOUND_FIELD_BY_NRPN_LSB", {})
    classified = calibration._classify_rytm_parameter_field(
        filter_field,
        track_spec=cast(dict[str, object], tracks["BD"]),
        track_index=0,
        reference=decoded,
    )
    assert classified.status == calibration.FIELD_STATUS_CAPTURE_REQUIRED
    assert classified.candidate_unpacked_offset is None
    assert "no saved-kit location" in classified.reason

    with pytest.raises(KeyError, match="no Rytm source mapping"):
        calibration._rytm_mapping_for_field(
            replace(source_field, semantic_path="tracks.BD.synth.Not A Parameter"),
            cast(dict[str, object], tracks["BD"]),
        )


def test_capture_assignment_and_enum_helpers_cover_defensive_shapes(
    statuses: tuple[
        calibration.Rush01SysexCalibrationStatus,
        calibration.Rush01SysexCalibrationStatus,
    ],
) -> None:
    rytm, a4 = statuses
    first = _field(rytm, "tracks.BD.synth.Level")
    second = next(
        field
        for field in rytm.fields
        if field.track == "BD" and ".synth." in field.semantic_path and field != first
    )
    assigned = calibration._assign_capture_targets(
        (
            replace(first, sequence=1, capture_group="test.same-track"),
            replace(second, sequence=2, capture_group="test.same-track"),
        )
    )
    assert all(field.capture_targets for field in assigned)

    with pytest.raises(ValueError, match="owner has no targets"):
        calibration._stride_witness_target(first, ())

    enum_field = replace(first, converter_family="enum")
    assert calibration._rytm_enum_option_count(replace(enum_field, track=None)) == 2
    assert (
        calibration._rytm_enum_option_count(replace(enum_field, semantic_path="tracks.BD.machine"))
        == 2
    )
    assert (
        calibration._rytm_enum_option_count(
            replace(enum_field, catalog_parameter="No matching selector")
        )
        == 2
    )

    a4_field = _field(a4, "tracks.T1.oscillator_1.waveform")
    assert (
        calibration._mutation_command(
            replace(a4_field, catalog_parameter=None, nrpn_address=None), 64
        )
        is None
    )
    assert calibration._a4_candidate_calibration(first) is None
    assert (
        calibration._a4_candidate_calibration(
            replace(a4_field, semantic_path="build_policy.kit_name")
        )
        is None
    )


def test_stride_detector_ignores_same_track_and_nonconstant_differentials() -> None:
    def capture_diff(
        source: str,
        track: str,
        unpacked: tuple[calibration.Rush01SysexByteChange, ...],
        packed: tuple[calibration.Rush01SysexByteChange, ...],
    ) -> calibration.Rush01SysexCaptureDiff:
        return calibration.Rush01SysexCaptureDiff(
            source_file=source,
            semantic_path=f"track_levels.{track}",
            track=track,
            capture_group="test.stride",
            observation_label="mid",
            observation_value="64",
            valid=True,
            error=None,
            byte_count=10,
            sha256="0" * 64,
            header_changes=(),
            packed_changes=packed,
            unpacked_changes=unpacked,
            integrity_changes=(),
        )

    one = (calibration.Rush01SysexByteChange(10, 0, 1),)
    same_track = (
        capture_diff("one", "BD", one, one),
        capture_diff("two", "BD", one, one),
    )
    assert calibration._detected_stride_candidates("rytm", same_track) == ()

    two_changes = (
        calibration.Rush01SysexByteChange(20, 0, 1),
        calibration.Rush01SysexByteChange(22, 0, 1),
    )
    nonconstant = (
        capture_diff("one", "BD", one, one),
        capture_diff("two", "SD", two_changes, two_changes),
    )
    assert calibration._detected_stride_candidates("rytm", nonconstant) == ()


def test_a4_binding_requires_a_known_section_and_field() -> None:
    with pytest.raises(KeyError, match="no A4 binding"):
        calibration._a4_binding_for_path("tracks.T1.unknown.field")
