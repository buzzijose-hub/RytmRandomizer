"""Tests for offline-only Analog Four Filter 1 Frequency KIT candidates."""

from __future__ import annotations

import json
from dataclasses import FrozenInstanceError
from hashlib import sha256
from pathlib import Path

import pytest

pytestmark = pytest.mark.fast

_FIXTURE_DIR = Path(__file__).parent / "fixtures" / "analog_four_saved_kit"
_SOURCE_NAME = "filter1_freq_127_source.syx"
_PENDING_NAME = "filter1_freq_tracks_16_25_48_50_80_75_112_25_pending.syx"


def _fixture_bytes(name: str) -> bytes:
    return (_FIXTURE_DIR / name).read_bytes()


def _decoded_unpacked(frame: bytes) -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    payload = extract_sysex_payloads(frame)[0]
    return decode_analog_four_saved_kit_payload(payload, require_trailer=True).unpacked


def _mutation(
    *,
    track: int = 1,
    screen_value: str = "63.50",
):
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        AnalogFourFilter1FrequencyCandidateMutation,
    )

    return AnalogFourFilter1FrequencyCandidateMutation(
        track=track,
        screen_value=screen_value,
    )


@pytest.mark.parametrize(
    ("fixture_name", "expected_sha256", "expected_raw"),
    [
        (
            _SOURCE_NAME,
            "3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95",
            b"\x7f\x00",
        ),
        (
            "filter1_freq_000_expected.syx",
            "5c8406010e86d11caeb628935820967d698b739b2d588ae949a807d358c9bde7",
            b"\x00\x00",
        ),
        (
            "filter1_freq_063_50_expected.syx",
            "d6710ca7368e59b8ac136081e61282dd538d49cddeaa5f81571dcff972819429",
            b"\x3f\x80",
        ),
    ],
)
def test_filter1_frequency_evidence_fixtures_are_hash_pinned_and_round_trip_exactly(
    fixture_name: str,
    expected_sha256: str,
    expected_raw: bytes,
) -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
        encode_analog_four_saved_kit_payload,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    frame = _fixture_bytes(fixture_name)
    payload = extract_sysex_payloads(frame)[0]
    decoded = decode_analog_four_saved_kit_payload(payload, require_trailer=True)
    reencoded = encode_analog_four_saved_kit_payload(decoded.prefix, decoded.unpacked)

    assert len(frame) == 2770
    assert sha256(frame).hexdigest() == expected_sha256
    assert decoded.unpacked[128:130] == expected_raw
    assert b"\xf0" + reencoded.payload + b"\xf7" == frame


@pytest.mark.parametrize(
    ("screen_value", "expected_name", "changed_offsets", "expected_bytes"),
    [
        ("0.00", "filter1_freq_000_expected.syx", (128,), b"\x00\x00"),
        ("63.50", "filter1_freq_063_50_expected.syx", (128, 129), b"\x3f\x80"),
    ],
)
def test_candidate_matches_isolated_hardware_capture_exactly(
    screen_value: str,
    expected_name: str,
    changed_offsets: tuple[int, ...],
    expected_bytes: bytes,
) -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    result = render_analog_four_filter1_frequency_candidate(
        _fixture_bytes(_SOURCE_NAME),
        (_mutation(screen_value=screen_value),),
    )
    applied = result.applied_mutations[0]

    assert result.framed_sysex == _fixture_bytes(expected_name)
    assert result.changed_unpacked_offsets == changed_offsets
    assert result.intended_unpacked_offsets == (128, 129)
    assert result.roundtrip_redecoded is True
    assert result.native_byte_isolation_validated is True
    assert result.validation_status == "offline-captured-kit-mutation-validated"
    assert result.output_authority == "local-file-only"
    assert result.hardware_send_validated is False
    assert applied.native_encoding == "unsigned-big-endian-q8.8"
    assert applied.intended_unpacked_offsets == (128, 129)
    assert applied.source_unpacked_bytes == b"\x7f\x00"
    assert applied.rendered_unpacked_bytes == expected_bytes
    assert applied.redecoded_raw_q8_8 == applied.raw_q8_8


def test_candidate_same_value_is_exact_noop_with_intended_offsets() -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    source = _fixture_bytes(_SOURCE_NAME)
    result = render_analog_four_filter1_frequency_candidate(
        source,
        (_mutation(screen_value="127.00"),),
    )

    assert result.framed_sysex == source
    assert result.source_sha256 == result.sha256
    assert result.intended_unpacked_offsets == (128, 129)
    assert result.changed_unpacked_offsets == ()
    assert result.changed_wire_offsets == ()


def test_candidate_renders_arbitrary_exact_q8_8_value() -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    result = render_analog_four_filter1_frequency_candidate(
        _fixture_bytes(_SOURCE_NAME),
        (_mutation(screen_value="64.25"),),
    )

    assert _decoded_unpacked(result.framed_sysex)[128:130] == b"\x40\x40"
    assert result.changed_unpacked_offsets == (128, 129)
    assert result.applied_mutations[0].redecoded_screen_value == "64.25"


def test_pending_scratch_fixture_pins_four_track_stride_and_metadata() -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    source = _fixture_bytes(_SOURCE_NAME)
    values = ((1, "16.25"), (2, "48.50"), (3, "80.75"), (4, "112.25"))
    result = render_analog_four_filter1_frequency_candidate(
        source,
        tuple(_mutation(track=track, screen_value=value) for track, value in values),
    )

    assert result.framed_sysex == _fixture_bytes(_PENDING_NAME)
    assert result.source_sha256 == (
        "3d38dd4369cbd6ea496adcfb7698025cd57e21332ffae1dd5a98e18ae767ea95"
    )
    assert result.sha256 == "829eee0209a248012a968e96df33acd007619a0078255c4fd034b5afda3520dd"
    assert result.source_checksum == 9577
    assert result.rendered_checksum == 9533
    assert result.packed_length == 2755
    assert result.encoded_length == 2760
    assert result.intended_unpacked_offsets == (
        128,
        129,
        478,
        479,
        828,
        829,
        1178,
        1179,
    )
    assert result.changed_unpacked_offsets == result.intended_unpacked_offsets
    assert result.changed_wire_offsets == (157, 158, 554, 557, 954, 957, 958, 1357, 1358, 2766)
    assert [row.raw_q8_8 for row in result.applied_mutations] == [
        0x1040,
        0x3080,
        0x50C0,
        0x7040,
    ]
    assert [row.rendered_unpacked_bytes for row in result.applied_mutations] == [
        b"\x10\x40",
        b"\x30\x80",
        b"\x50\xc0",
        b"\x70\x40",
    ]
    assert [row.redecoded_screen_value for row in result.applied_mutations] == [
        "16.25",
        "48.5",
        "80.75",
        "112.25",
    ]
    assert result.roundtrip_redecoded is True
    assert result.native_byte_isolation_validated is True
    assert result.hardware_send_validated is False


def test_pending_scratch_manifest_matches_rendered_artifact_and_has_no_observations() -> None:
    manifest = json.loads(
        (_FIXTURE_DIR / "filter1_frequency_pending_scratch_validation.json").read_text(
            encoding="utf-8"
        )
    )

    assert manifest["status"] == "pending_physical_outbound_validation"
    assert manifest["calibration_status"] == "offline-captured-kit-mutation-validated"
    assert manifest["output_authority"] == "local-file-only"
    assert manifest["hardware_send_validated"] is False
    assert manifest["source"]["sha256"] == sha256(_fixture_bytes(_SOURCE_NAME)).hexdigest()
    assert manifest["generated"]["sha256"] == sha256(_fixture_bytes(_PENDING_NAME)).hexdigest()
    assert manifest["generated"]["changed_native_offsets"] == [
        128,
        129,
        478,
        479,
        828,
        829,
        1178,
        1179,
    ]
    assert manifest["observations"] == []


@pytest.mark.parametrize(
    "screen_value",
    [
        "-0.00390625",
        "127.00390625",
        "16.10",
        "63.50000000000000000000000000000000000000001",
        "1e1000000",
        "-1e1000000",
        "1e-1000000",
        "NaN",
        "loud",
    ],
)
def test_candidate_rejects_out_of_range_nonrepresentable_and_invalid_values(
    screen_value: str,
) -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    with pytest.raises(ValueError, match="unsupported screen value"):
        render_analog_four_filter1_frequency_candidate(
            _fixture_bytes(_SOURCE_NAME),
            (_mutation(screen_value=screen_value),),
        )


@pytest.mark.parametrize("precision", [2, 28, 50])
def test_candidate_exact_q8_8_validation_does_not_depend_on_decimal_precision(
    precision: int,
) -> None:
    from decimal import localcontext

    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    with localcontext() as context:
        context.prec = precision
        result = render_analog_four_filter1_frequency_candidate(
            _fixture_bytes(_SOURCE_NAME),
            (_mutation(screen_value="64.00390625"),),
        )
        with pytest.raises(ValueError, match="unsupported screen value"):
            render_analog_four_filter1_frequency_candidate(
                _fixture_bytes(_SOURCE_NAME),
                (_mutation(screen_value="64.00390625000000000000000000000000000001"),),
            )

    assert result.applied_mutations[0].raw_q8_8 == 0x4001
    assert result.applied_mutations[0].redecoded_screen_value == "64.00390625"
    assert _decoded_unpacked(result.framed_sysex)[128:130] == b"\x40\x01"


def test_candidate_rejects_checksum_valid_source_that_cannot_round_trip_exactly() -> None:
    from rytm_randomizer.data.analog_four_saved_kit_layout import (
        A4_PACKED_PAYLOAD_OFFSET,
        A4_SAVED_KIT_TRAILER_SIZE,
    )
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        analog_four_saved_kit_checksum,
    )

    source = _fixture_bytes(_SOURCE_NAME)
    noncanonical = bytearray(source)
    # The last packed group has two data bytes. Its low five mask bits do
    # not decode into native bytes, but source validation must preserve them.
    trailer_start = len(noncanonical) - A4_SAVED_KIT_TRAILER_SIZE - 1
    noncanonical[trailer_start - 3] |= 1
    packed = bytes(noncanonical[1 + A4_PACKED_PAYLOAD_OFFSET : trailer_start])
    checksum = analog_four_saved_kit_checksum(packed)
    noncanonical[trailer_start : trailer_start + 2] = bytes((checksum >> 7, checksum & 0x7F))
    altered_source = bytes(noncanonical)

    assert _decoded_unpacked(altered_source) == _decoded_unpacked(source)
    with pytest.raises(ValueError, match="source must round-trip byte-identically"):
        render_analog_four_filter1_frequency_candidate(
            altered_source,
            (_mutation(screen_value="127.00"),),
        )


def test_candidate_preserves_unknown_native_bytes_and_untargeted_tracks() -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
        decode_analog_four_saved_kit_payload,
        encode_analog_four_saved_kit_payload,
    )

    decoded = decode_analog_four_saved_kit_payload(
        _fixture_bytes(_SOURCE_NAME)[1:-1],
        require_trailer=True,
    )
    source_native = bytearray(decoded.unpacked)
    source_native[2000] = 0xDF
    encoded = encode_analog_four_saved_kit_payload(decoded.prefix, bytes(source_native))
    source = b"\xf0" + encoded.payload + b"\xf7"

    result = render_analog_four_filter1_frequency_candidate(
        source,
        (_mutation(track=3, screen_value="80.75"),),
    )
    expected_native = source_native.copy()
    expected_native[828:830] = b"\x50\xc0"

    assert _decoded_unpacked(result.framed_sysex) == bytes(expected_native)
    assert result.changed_unpacked_offsets == (828, 829)
    assert result.framed_sysex[: 1 + len(decoded.prefix)] == source[: 1 + len(decoded.prefix)]


@pytest.mark.parametrize("track", [0, 5, True])
def test_candidate_rejects_invalid_track(track: int) -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    with pytest.raises(ValueError, match="track must be in 1..4"):
        render_analog_four_filter1_frequency_candidate(
            _fixture_bytes(_SOURCE_NAME),
            (_mutation(track=track),),
        )


def test_candidate_rejects_duplicate_wrong_record_and_demoted_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace
    from typing import cast

    import rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate as module
    import rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate as generic_module
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_PENDING,
        analog_four_sysex_calibration_for,
    )

    source = _fixture_bytes(_SOURCE_NAME)
    unchanged = module.render_analog_four_filter1_frequency_candidate(source, ())
    assert unchanged.framed_sysex == source
    assert unchanged.applied_mutations == ()
    assert unchanged.changed_unpacked_offsets == ()
    assert unchanged.changed_wire_offsets == ()
    assert unchanged.roundtrip_redecoded is True
    assert unchanged.hardware_send_validated is False
    with pytest.raises(ValueError, match="duplicate"):
        module.render_analog_four_filter1_frequency_candidate(
            source,
            (_mutation(), _mutation(screen_value="64.00")),
        )
    with pytest.raises(TypeError, match="must contain"):
        module.render_analog_four_filter1_frequency_candidate(
            source,
            cast(tuple[module.AnalogFourFilter1FrequencyCandidateMutation, ...], (object(),)),
        )

    pending = replace(
        analog_four_sysex_calibration_for("Filter1 Frequency"),
        status=A4_SYSEX_CALIBRATION_STATUS_PENDING,
    )
    monkeypatch.setattr(generic_module, "analog_four_sysex_calibration_for", lambda _: pending)
    with pytest.raises(ValueError, match="not offline-captured-kit-mutation-validated"):
        module.render_analog_four_filter1_frequency_candidate(source, (_mutation(),))


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda frame: frame + frame, "exactly one"),
        (lambda frame: frame + b"\x01\xf7", "isolated"),
        (lambda frame: frame[1:-1], "framed"),
        (lambda frame: frame[:4] + b"\x07" + frame[5:], "family"),
    ],
)
def test_candidate_rejects_malformed_or_unsupported_source(mutator, message: str) -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    with pytest.raises(ValueError, match=message):
        render_analog_four_filter1_frequency_candidate(
            mutator(_fixture_bytes(_SOURCE_NAME)),
            (_mutation(),),
        )


def test_candidate_result_is_frozen() -> None:
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    result = render_analog_four_filter1_frequency_candidate(
        _fixture_bytes(_SOURCE_NAME),
        (_mutation(),),
    )

    with pytest.raises(FrozenInstanceError):
        result.hardware_send_validated = True  # type: ignore[misc]


@pytest.mark.parametrize(
    "drift",
    [
        {"parameter": "Filter2 Frequency"},
        {"track_1_primary_raw_offset": 157},
        {"track_1_primary_raw_offset": 153},  # Packed mask, never native data.
        {"track_raw_stride": 401},
        {"track_unpacked_stride": 351},
        {"track_raw_stride": 400.0},
        {"track_1_primary_raw_offset": True},
        {"native_field": None},
        {"native_field": "filter1_resonance"},
        {"native_encoding": "little-endian"},
        {"native_width": 1},
        {"native_scale": 128},
        {"native_raw_min": True},
        {"native_raw_min": -1},
        {"native_raw_max": 0x8000},
        {"native_raw_min": 1},
        {"native_raw_max": 0x7F01},
        {"screen_max": "126.00"},
    ],
)
def test_calibration_drift_is_rejected_before_patching_any_field(
    monkeypatch: pytest.MonkeyPatch, drift: dict[str, object]
) -> None:
    from dataclasses import replace

    import rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate as renderer
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )
    from rytm_randomizer.devices.strategies.analog_four_kit_fields import A4Sound

    canonical = analog_four_sysex_calibration_for("Filter1 Frequency")
    changed = replace(canonical, **drift)
    resolutions = iter((canonical, changed))
    monkeypatch.setattr(renderer, "analog_four_sysex_calibration_for", lambda _: next(resolutions))
    patches: list[tuple[str, int]] = []
    monkeypatch.setattr(
        A4Sound, "set_fixed_8_8_raw", lambda self, field, raw: patches.append((field, raw))
    )
    source = _fixture_bytes(_SOURCE_NAME)

    with pytest.raises(ValueError, match="calibrat|native range"):
        renderer.render_analog_four_saved_kit_candidate(
            source,
            (
                renderer.AnalogFourSavedKitCandidateMutation("Filter1 Frequency", 1, "32"),
                renderer.AnalogFourSavedKitCandidateMutation("Filter1 Frequency", 2, "64"),
            ),
        )

    assert patches == []
    assert source == _fixture_bytes(_SOURCE_NAME)


def test_renderer_consumes_packed_calibration_method_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.data.analog_four_sysex_calibration import AnalogFourSysexFieldCalibration
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    monkeypatch.setattr(
        AnalogFourSysexFieldCalibration, "primary_raw_offset_for_track", lambda self, track: 157
    )
    with pytest.raises(ValueError, match="calibration offset disagrees"):
        render_analog_four_filter1_frequency_candidate(_fixture_bytes(_SOURCE_NAME), (_mutation(),))


def test_renderer_rejects_canonical_field_map_drift(monkeypatch: pytest.MonkeyPatch) -> None:
    import rytm_randomizer.data.analog_four_sysex_calibration as calibration
    from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
        render_analog_four_filter1_frequency_candidate,
    )

    fields = dict(calibration.A4_TRACK_OFFSETS)
    fields["filter1_frequency"] += 1
    monkeypatch.setattr(calibration, "A4_TRACK_OFFSETS", fields)
    with pytest.raises(ValueError, match="calibration offset disagrees"):
        render_analog_four_filter1_frequency_candidate(_fixture_bytes(_SOURCE_NAME), (_mutation(),))


def test_shared_renderer_accepts_another_field_only_after_explicit_offline_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace
    from typing import cast

    import rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate as renderer
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
        analog_four_sysex_calibration_for,
    )

    source = _fixture_bytes(_SOURCE_NAME)
    mutation = renderer.AnalogFourSavedKitCandidateMutation("Filter2 Frequency", 4, "64.00390625")
    with pytest.raises(ValueError, match="not offline-captured-kit-mutation-validated"):
        renderer.render_analog_four_saved_kit_candidate(source, (mutation,))
    with pytest.raises(TypeError, match="must contain"):
        renderer.render_analog_four_saved_kit_candidate(
            source, cast(tuple[renderer.AnalogFourSavedKitCandidateMutation, ...], (object(),))
        )

    # A hypothetical promotion is test-local; production keeps Filter 2 unpromoted.
    calibration = replace(
        analog_four_sysex_calibration_for("Filter2 Frequency"),
        status=A4_SYSEX_CALIBRATION_STATUS_OFFLINE_CAPTURED_KIT_MUTATION_VALIDATED,
        native_field="filter2_frequency",
        native_raw_max=0x7F00,
    )
    monkeypatch.setattr(renderer, "analog_four_sysex_calibration_for", lambda _: calibration)
    result = renderer.render_analog_four_saved_kit_candidate(source, (mutation,))

    expected = bytearray(_decoded_unpacked(source))
    expected[1188:1190] = b"\x40\x01"
    assert _decoded_unpacked(result.framed_sysex) == bytes(expected)
    assert result.intended_unpacked_offsets == (1188, 1189)
    assert result.applied_mutations[0].parameter == "Filter2 Frequency"
    assert result.applied_mutations[0].redecoded_screen_value == "64.00390625"
    assert result.roundtrip_redecoded and result.native_byte_isolation_validated
    assert result.hardware_send_validated is False
    assert result.output_authority == "local-file-only"
    with pytest.raises(ValueError, match="init=False"):
        replace(result, hardware_send_validated=True)
