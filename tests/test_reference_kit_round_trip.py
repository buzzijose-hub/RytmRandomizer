"""Reference-anchored Elektron kit codec tests for the RUSH01 build."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
import yaml

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = PROJECT_ROOT / "reference"
SPEC_DIR = PROJECT_ROOT / "specs"


def _read_optional_reference(filename: str) -> bytes:
    path = REFERENCE_DIR / filename
    if not path.is_file():
        pytest.skip(
            "optional local-reference integration requires private dump: " f"reference/{filename}"
        )
    return path.read_bytes()


@pytest.mark.parametrize(
    ("filename", "model", "reference_filename", "expected_length"),
    (
        ("RUSH01_RYTM.yaml", "Analog Rytm MKII", "RYTM_Test1_Init_Kit.syx", 2998),
        ("RUSH01_A4.yaml", "Analog Four MKII", "A4_Test1_Init_Kit.syx", 2770),
    ),
)
def test_rush01_spec_parses_with_unverified_firmware_and_approved_reference(
    filename: str,
    model: str,
    reference_filename: str,
    expected_length: int,
) -> None:
    spec = yaml.safe_load((SPEC_DIR / filename).read_text(encoding="utf-8"))

    assert isinstance(spec, dict)
    assert spec["device"]["model"] == model
    assert spec["device"]["firmware"] == {
        "installed": "UNVERIFIED_FROM_DEVICE",
        "do_not_infer": True,
    }
    assert spec["reference"]["filename"] == reference_filename
    assert spec["reference"]["approved_as_trusted_anchor"] is True
    assert spec["reference"]["expected_length_bytes"] == expected_length


def test_rytm_spec_uses_catalog_machines_manual_toms_and_typed_selectors() -> None:
    from rytm_randomizer.data.plans import FILTER_TYPE_NAMES
    from rytm_randomizer.data.rytm_machine_catalog import (
        RYTM_MACHINE_PROFILES,
        is_machine_allowed_on_pad,
    )

    spec = yaml.safe_load((SPEC_DIR / "RUSH01_RYTM.yaml").read_text(encoding="utf-8"))
    track_codes = ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB")
    profile_by_label = {profile.label: profile for profile in RYTM_MACHINE_PROFILES}

    for pad, track_code in enumerate(track_codes, start=1):
        track = spec["tracks"][track_code]
        machine = track["machine"]
        profile = profile_by_label[machine["name"]]
        assert "id" not in machine
        expected_selection = (
            "manual_setup_required" if track_code in {"LT", "MT", "HT"} else "catalog_verified"
        )
        assert machine["selection"] == expected_selection
        assert is_machine_allowed_on_pad(pad, profile.key)

        filter_type = track["filter"]["TYPE"]
        assert FILTER_TYPE_NAMES[filter_type["id"]] == filter_type["name"]

    snap_type = spec["tracks"]["BT"]["synth"]["Snap Type"]
    assert snap_type == {
        "type": "enum",
        "requested": "preserve_reference",
        "raw_midi": "learn_required",
    }
    assert "SNP" not in spec["tracks"]["BT"]["synth"]
    assert set(spec["tracks"]["CB"]["synth"]) == {
        "Level",
        "Tune",
        "Decay Time",
        "Detune",
    }


@pytest.mark.parametrize(
    ("filename", "expected_bytes", "expected_sha256", "codec_name"),
    (
        (
            "RYTM_Test1_Init_Kit.syx",
            2998,
            "8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd",
            "ANALOG_RYTM_KIT_CODEC",
        ),
        (
            "A4_Test1_Init_Kit.syx",
            2770,
            "50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e",
            "ANALOG_FOUR_KIT_CODEC",
        ),
    ),
)
def test_approved_reference_round_trip_is_byte_identical(
    filename: str,
    expected_bytes: int,
    expected_sha256: str,
    codec_name: str,
) -> None:
    from rytm_randomizer.devices import strategies

    frame = _read_optional_reference(filename)
    codec = getattr(strategies, codec_name)
    decoded = codec.decode_frame(frame)
    encoded = codec.encode_frame(decoded)

    assert len(frame) == expected_bytes
    assert sha256(frame).hexdigest() == expected_sha256
    assert encoded == frame
    assert sha256(encoded).hexdigest() == expected_sha256
    assert frame[:1] == b"\xf0"
    assert frame[-1:] == b"\xf7"
    assert all(byte <= 0x7F for byte in frame[1:-1])


def test_reference_codecs_decode_verified_container_metadata() -> None:
    from rytm_randomizer.devices.strategies import (
        ANALOG_FOUR_KIT_CODEC,
        ANALOG_RYTM_KIT_CODEC,
    )

    rytm = ANALOG_RYTM_KIT_CODEC.decode_frame(_read_optional_reference("RYTM_Test1_Init_Kit.syx"))
    a4 = ANALOG_FOUR_KIT_CODEC.decode_frame(_read_optional_reference("A4_Test1_Init_Kit.syx"))

    assert len(rytm.header) == 9
    assert len(rytm.packed) == 2983
    assert len(rytm.unpacked) == 2610
    assert rytm.checksum == 10997
    assert rytm.encoded_length == 2988

    assert len(a4.header) == 4
    assert len(a4.packed) == 2760
    assert len(a4.unpacked) == 2415
    assert a4.checksum == 9215
    assert a4.encoded_length == 2760


def test_reference_bound_codec_preserves_unknown_bytes_during_known_kit_name_patch() -> None:
    from rytm_randomizer.data import RYTM_KIT_NAME_LENGTH, RYTM_KIT_NAME_OFFSET
    from rytm_randomizer.devices.strategies import ANALOG_RYTM_KIT_CODEC
    from rytm_randomizer.snapshot import encode_elektron_u14, read_ascii_name

    frame = _read_optional_reference("RYTM_Test1_Init_Kit.syx")
    decoded = ANALOG_RYTM_KIT_CODEC.decode_frame(frame)
    patched = bytearray(decoded.unpacked)
    requested_name = "RUSH01"
    encoded_name = requested_name.encode("ascii").ljust(RYTM_KIT_NAME_LENGTH, b"\x00")
    patched[RYTM_KIT_NAME_OFFSET : RYTM_KIT_NAME_OFFSET + RYTM_KIT_NAME_LENGTH] = encoded_name

    generated = ANALOG_RYTM_KIT_CODEC.encode_frame(decoded, unpacked=bytes(patched))
    regenerated = ANALOG_RYTM_KIT_CODEC.decode_frame(generated)

    expected_unpacked_changes = [
        index
        for index, (before, after) in enumerate(zip(decoded.unpacked, patched))
        if before != after
    ]
    changed_unpacked = [
        index
        for index, (before, after) in enumerate(zip(decoded.unpacked, regenerated.unpacked))
        if before != after
    ]
    assert changed_unpacked == expected_unpacked_changes
    assert regenerated.header == decoded.header
    assert regenerated.unpacked[:RYTM_KIT_NAME_OFFSET] == decoded.unpacked[:RYTM_KIT_NAME_OFFSET]
    assert (
        regenerated.unpacked[RYTM_KIT_NAME_OFFSET + RYTM_KIT_NAME_LENGTH :]
        == decoded.unpacked[RYTM_KIT_NAME_OFFSET + RYTM_KIT_NAME_LENGTH :]
    )
    assert (
        read_ascii_name(
            regenerated.unpacked,
            offset=RYTM_KIT_NAME_OFFSET,
            length=RYTM_KIT_NAME_LENGTH,
        )
        == requested_name
    )

    packed_start = 1 + len(decoded.header)
    expected_payload_offsets = {
        packed_start + index
        for index, (before, after) in enumerate(zip(decoded.packed, regenerated.packed))
        if before != after
    }
    expected_checksum = (
        sum(regenerated.packed[ANALOG_RYTM_KIT_CODEC.spec.checksum_packed_start :]) & 0x3FFF
    )
    assert generated[-5:-3] == encode_elektron_u14(expected_checksum)
    assert generated[-3:-1] == frame[-3:-1]
    expected_integrity_offsets = {
        index for index in range(len(frame) - 5, len(frame) - 3) if frame[index] != generated[index]
    }
    changed_frame_offsets = {
        index for index, (before, after) in enumerate(zip(frame, generated)) if before != after
    }
    assert changed_frame_offsets == expected_payload_offsets | expected_integrity_offsets

    assert generated.startswith(b"\xf0")
    assert generated.endswith(b"\xf7")
    assert all(byte <= 0x7F for byte in generated[1:-1])
    assert ANALOG_RYTM_KIT_CODEC.encode_frame(regenerated) == generated
