"""Tests for hardware-validated Analog Four saved-kit SysEx rendering."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from hashlib import sha256

import pytest

from conftest import (
    analog_four_saved_kit_frame,
)
from conftest import analog_four_saved_kit_mutation as _mutation

pytestmark = pytest.mark.fast


def _rendered_unpacked(frame: bytes) -> bytes:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_PACKED_PAYLOAD_OFFSET,
        A4_SAVED_KIT_TRAILER_SIZE,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads, unpack_elektron_7bit

    payload = extract_sysex_payloads(frame)[0]
    return unpack_elektron_7bit(payload[A4_PACKED_PAYLOAD_OFFSET:-A4_SAVED_KIT_TRAILER_SIZE])


def test_render_saved_kit_synthesizes_novel_filter2_resonance_value() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = analog_four_saved_kit_frame()
    result = render_analog_four_saved_kit(source, (_mutation(),))
    source_unpacked = _rendered_unpacked(source)
    rendered_unpacked = _rendered_unpacked(result.framed_sysex)

    assert result.kit_name == "KIT 1"
    assert result.packed_length == 2760
    assert result.source_checksum != result.rendered_checksum
    assert result.sha256 == sha256(result.framed_sysex).hexdigest()
    assert result.applied_mutations[0].unpacked_offset == 145
    assert result.applied_mutations[0].source_unpacked_value == 0
    assert result.applied_mutations[0].rendered_unpacked_value == 64
    assert rendered_unpacked[145] == 64
    assert [
        index
        for index, (before, after) in enumerate(zip(source_unpacked, rendered_unpacked))
        if before != after
    ] == [145]


def test_render_saved_kit_matches_hardware_reference_bytes_exactly() -> None:
    from pathlib import Path

    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    fixture_dir = Path(__file__).parent / "fixtures" / "analog_four_saved_kit"
    source = (fixture_dir / "filter2_res_000_source.syx").read_bytes()
    expected = (fixture_dir / "filter2_res_127_expected.syx").read_bytes()

    assert sha256(source).hexdigest() == (
        "a8fbb0552b953815fc1f6358299116866b0d94002692933abccf83655023cc6b"
    )
    result = render_analog_four_saved_kit(
        source,
        (_mutation(screen_value="127"),),
    )

    assert result.framed_sysex == expected
    assert result.sha256 == "5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b"


def test_render_saved_kit_matches_hardware_accepted_novel_64_hash() -> None:
    from pathlib import Path

    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = (
        Path(__file__).parent / "fixtures" / "analog_four_saved_kit" / "filter2_res_000_source.syx"
    ).read_bytes()
    result = render_analog_four_saved_kit(source, (_mutation(screen_value="64"),))

    assert result.sha256 == "2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7"


def test_render_saved_kit_matches_hardware_accepted_four_track_hash() -> None:
    from pathlib import Path

    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = (
        Path(__file__).parent / "fixtures" / "analog_four_saved_kit" / "filter2_res_000_source.syx"
    ).read_bytes()
    mutations = tuple(
        _mutation(track=track, screen_value=str(value))
        for track, value in ((1, 16), (2, 48), (3, 80), (4, 112))
    )
    result = render_analog_four_saved_kit(source, mutations)

    assert result.sha256 == "0e88aa6f15fd49c36696d5b8e09bda18ce5eeb8562c1a44ce46683c6deef819b"


def test_render_saved_kit_applies_distinct_values_to_all_four_tracks() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    mutations = tuple(
        _mutation(track=track, screen_value=str(value))
        for track, value in ((1, 16), (2, 48), (3, 80), (4, 112))
    )

    result = render_analog_four_saved_kit(analog_four_saved_kit_frame(), mutations)

    assert [row.unpacked_offset for row in result.applied_mutations] == [145, 495, 845, 1195]
    assert [row.rendered_unpacked_value for row in result.applied_mutations] == [16, 48, 80, 112]
    assert [
        _rendered_unpacked(result.framed_sysex)[offset] for offset in (145, 495, 845, 1195)
    ] == [
        16,
        48,
        80,
        112,
    ]


def test_render_saved_kit_preserves_neighbor_high_bit_for_validated_field() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = analog_four_saved_kit_frame(unpacked_overrides={145: 0x80})
    result = render_analog_four_saved_kit(
        source,
        (_mutation(screen_value="20"),),
    )

    assert result.applied_mutations[0].unpacked_offset == 145
    assert result.applied_mutations[0].rendered_unpacked_value == 0x94
    assert _rendered_unpacked(result.framed_sysex)[145] == 0x94


def test_render_saved_kit_rejects_candidate_only_calibration() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    with pytest.raises(ValueError, match="not hardware-write-validated"):
        render_analog_four_saved_kit(
            analog_four_saved_kit_frame(),
            (_mutation(parameter="Filter1 Resonance", screen_value="20"),),
        )


def test_render_saved_kit_emits_valid_checksum_and_packed_length() -> None:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_CHECKSUM_PACKED_OFFSET,
        A4_PACKED_PAYLOAD_OFFSET,
        A4_SAVED_KIT_TRAILER_SIZE,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )
    from rytm_randomizer.snapshot import extract_sysex_payloads

    result = render_analog_four_saved_kit(analog_four_saved_kit_frame(), (_mutation(),))
    payload = extract_sysex_payloads(result.framed_sysex)[0]
    packed = payload[A4_PACKED_PAYLOAD_OFFSET:-A4_SAVED_KIT_TRAILER_SIZE]
    checksum = (payload[-4] << 7) | payload[-3]
    packed_length = (payload[-2] << 7) | payload[-1]

    assert checksum == sum(packed[A4_CHECKSUM_PACKED_OFFSET:]) & 0x3FFF
    assert packed_length == len(packed)


def test_saved_kit_manifest_constants_pin_observed_hardware_frame_shape() -> None:
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_CHECKSUM_PACKED_OFFSET,
        A4_SAVED_KIT_TRAILER_SIZE,
        A4_SAVED_KIT_UNPACKED_SIZE,
    )
    from rytm_randomizer.snapshot import pack_elektron_7bit

    assert A4_CHECKSUM_PACKED_OFFSET == 8
    assert A4_SAVED_KIT_TRAILER_SIZE == 4
    assert A4_SAVED_KIT_UNPACKED_SIZE == 2415
    assert len(pack_elektron_7bit(bytes(A4_SAVED_KIT_UNPACKED_SIZE))) == 2760
    assert len(analog_four_saved_kit_frame()) == 2770


@pytest.mark.parametrize(
    ("mutations", "message"),
    [
        ((), "at least one mutation"),
        ((_mutation(screen_value="63"), _mutation(screen_value="64")), "duplicate mutation"),
        ((_mutation(screen_value="128"),), "unsupported screen value"),
        ((_mutation(screen_value="loud"),), "unsupported screen value"),
        (
            (_mutation(parameter="Filter2 Frequency", screen_value="64.00"),),
            "not hardware-write-validated",
        ),
        ((_mutation(track=5),), "track must be in 1..4"),
        (
            (_mutation(parameter="Filter1 Frequency", screen_value="63.50"),),
            "not hardware-write-validated",
        ),
        ((object(),), "must contain AnalogFourSavedKitMutation"),
    ],
)
def test_render_saved_kit_rejects_unsafe_mutation_requests(
    mutations: tuple[object, ...], message: str
) -> None:
    from typing import cast

    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        AnalogFourSavedKitMutation,
        render_analog_four_saved_kit,
    )

    with pytest.raises((ValueError, TypeError), match=message):
        render_analog_four_saved_kit(
            analog_four_saved_kit_frame(),
            cast(tuple[AnalogFourSavedKitMutation, ...], mutations),
        )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda frame: frame + frame, "exactly one"),
        (lambda frame: frame + b"\x01\xf7", "isolated"),
        (lambda frame: frame[1:-1], "framed"),
        (
            lambda frame: bytes([0xF0, 0x00, 0x20, 0x3C, 0x06, 0xF7]),
            "too short",
        ),
        (lambda frame: frame[:1] + b"\x01" + frame[2:], "manufacturer"),
        (lambda frame: frame[:4] + b"\x07" + frame[5:], "family"),
        (lambda frame: frame[:-5] + b"\x00\x00" + frame[-3:], "checksum"),
        (lambda frame: frame[:-3] + b"\x00\x01" + frame[-1:], "packed length"),
    ],
)
def test_render_saved_kit_rejects_malformed_or_unsupported_frames(mutator, message: str) -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    with pytest.raises(ValueError, match=message):
        render_analog_four_saved_kit(mutator(analog_four_saved_kit_frame()), (_mutation(),))


@pytest.mark.parametrize("unpacked_size", [2414, 2416])
def test_render_saved_kit_rejects_self_consistent_wrong_body_size(
    unpacked_size: int,
) -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = analog_four_saved_kit_frame(unpacked_size=unpacked_size)

    with pytest.raises(ValueError, match="unexpected length"):
        render_analog_four_saved_kit(source, (_mutation(),))


def test_render_saved_kit_rejects_wrong_saved_kit_object_byte() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = analog_four_saved_kit_frame(unpacked_overrides={0: 0x51})

    with pytest.raises(ValueError, match="not a saved kit"):
        render_analog_four_saved_kit(source, (_mutation(),))


def test_render_saved_kit_rejects_non_seven_bit_packed_byte() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    source = bytearray(analog_four_saved_kit_frame())
    packed_start = 5
    source[packed_start + 10] = 0x80
    packed = source[packed_start:-5]
    checksum = sum(packed[8:]) & 0x3FFF
    source[-5] = (checksum >> 7) & 0x7F
    source[-4] = checksum & 0x7F

    with pytest.raises(ValueError, match="outside the 7-bit MIDI data range"):
        render_analog_four_saved_kit(bytes(source), (_mutation(),))


def test_render_saved_kit_rejects_unpromoted_calibration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from dataclasses import replace

    import rytm_randomizer.devices.strategies.analog_four_saved_kit_writer as writer_module
    from rytm_randomizer.data.analog_four_sysex_calibration import (
        A4_SYSEX_CALIBRATION_STATUS_PENDING,
        analog_four_sysex_calibration_for,
    )

    pending = replace(
        analog_four_sysex_calibration_for("Filter2 Resonance"),
        status=A4_SYSEX_CALIBRATION_STATUS_PENDING,
    )
    monkeypatch.setattr(writer_module, "analog_four_sysex_calibration_for", lambda _: pending)

    with pytest.raises(ValueError, match="not hardware-write-validated"):
        writer_module.render_analog_four_saved_kit(analog_four_saved_kit_frame(), (_mutation(),))


def test_saved_kit_writer_rejects_primary_offset_at_packed_group_header() -> None:
    from dataclasses import replace

    from rytm_randomizer.data.analog_four_sysex_calibration import (
        analog_four_sysex_calibration_for,
    )
    from rytm_randomizer.devices.strategies.analog_four_offset_manifest import (
        A4_PACKED_PAYLOAD_OFFSET,
    )
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        _unpacked_offset_for_calibration,
    )

    calibration = replace(
        analog_four_sysex_calibration_for("Filter2 Resonance"),
        track_1_primary_raw_offset=A4_PACKED_PAYLOAD_OFFSET,
    )

    with pytest.raises(ValueError, match="points to a packed group header"):
        _unpacked_offset_for_calibration(calibration, 1)


def test_render_saved_kit_rejects_repacked_length_change(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.devices.strategies.analog_four_saved_kit_writer as writer_module
    import rytm_randomizer.snapshot.elektron_packed_payload as packed_payload_module

    pack = packed_payload_module.pack_elektron_7bit
    monkeypatch.setattr(
        packed_payload_module,
        "pack_elektron_7bit",
        lambda unpacked: pack(unpacked) + b"\x00",
    )

    with pytest.raises(ValueError, match="repacking changed"):
        writer_module.render_analog_four_saved_kit(analog_four_saved_kit_frame(), (_mutation(),))


def test_saved_kit_writer_result_records_are_frozen() -> None:
    from rytm_randomizer.devices.strategies.analog_four_saved_kit_writer import (
        render_analog_four_saved_kit,
    )

    result = render_analog_four_saved_kit(analog_four_saved_kit_frame(), (_mutation(),))

    with pytest.raises(FrozenInstanceError):
        result.packed_length = 1  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.applied_mutations[0].unpacked_offset = 1  # type: ignore[misc]
