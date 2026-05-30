"""Tests for ``rytm_randomizer.cockpit.export.serialize``.

These tests pin the end-to-end pack/unpack round-trip of
:class:`ProfileModel` instances and the four explicit failure modes the API
contract names: bad magic, unsupported ``format_version``, CRC mismatch,
and truncated input. The header-internal mechanics live in
``test_export_format.py``.
"""

from __future__ import annotations

import struct

import msgpack
import pytest

from rytm_randomizer.cockpit.data import (
    TRANSITION_CURVE_VALUES,
    ProfileModel,
    StyleTrait,
    TraitPadWeight,
)
from rytm_randomizer.cockpit.export import (
    FORMAT_VERSION,
    MAGIC,
    pack_profile_model,
    unpack_profile_model,
)
from rytm_randomizer.cockpit.export.model_format import (
    build_header,
    compute_crc,
    pack_crc,
)
from rytm_randomizer.cockpit.export.serialize import _pack_with_version_override

pytestmark = pytest.mark.fast


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    *,
    name: str = "buzzi",
    kind: str = "user",
    model_version: str = "1.2.0",
    traits: tuple[StyleTrait, ...] = (StyleTrait("rolling_low_end", 0.85),),
    pad_mappings: tuple[TraitPadWeight, ...] = (TraitPadWeight("rolling_low_end", 1, 0.6),),
    transition_curve: str = "linear",
    source_summary: str = "5 sources · 1,243 analyzed signals",
) -> ProfileModel:
    return ProfileModel(
        profile_id="01HXY5Q9PJM0123456789ABCD0",
        name=name,
        kind=kind,  # type: ignore[arg-type]
        model_version=model_version,
        traits=traits,
        pad_mappings=pad_mappings,
        transition_curve=transition_curve,  # type: ignore[arg-type]
        source_summary=source_summary,
    )


# ---------------------------------------------------------------------------
# Round-trip parity
# ---------------------------------------------------------------------------


def test_round_trip_default_profile() -> None:
    profile = _make_profile()
    blob = pack_profile_model(profile)
    assert unpack_profile_model(blob) == profile


def test_round_trip_profile_with_no_traits_or_mappings() -> None:
    profile = _make_profile(traits=(), pad_mappings=())
    blob = pack_profile_model(profile)
    decoded = unpack_profile_model(blob)
    assert decoded == profile
    assert decoded.traits == ()
    assert decoded.pad_mappings == ()


def test_round_trip_profile_with_many_traits_and_mappings() -> None:
    traits = tuple(StyleTrait(f"trait_{i}", round(i / 10.0, 2)) for i in range(11))
    pad_mappings = tuple(
        TraitPadWeight(trait=f"trait_{i % len(traits)}", pad_id=(i % 12) + 1, weight=0.5)
        for i in range(36)
    )
    profile = _make_profile(traits=traits, pad_mappings=pad_mappings)
    blob = pack_profile_model(profile)
    assert unpack_profile_model(blob) == profile


@pytest.mark.parametrize("curve", TRANSITION_CURVE_VALUES)
def test_round_trip_for_every_transition_curve(curve: str) -> None:
    profile = _make_profile(transition_curve=curve)
    assert unpack_profile_model(pack_profile_model(profile)) == profile


@pytest.mark.parametrize("kind", ["scene", "user"])
def test_round_trip_for_every_kind(kind: str) -> None:
    profile = _make_profile(kind=kind)
    assert unpack_profile_model(pack_profile_model(profile)) == profile


# ---------------------------------------------------------------------------
# Header parsing surface (re-asserted at the public API)
# ---------------------------------------------------------------------------


def test_packed_blob_starts_with_rymp_magic() -> None:
    blob = pack_profile_model(_make_profile())
    assert blob[:4] == MAGIC


def test_packed_blob_encodes_default_format_version() -> None:
    blob = pack_profile_model(_make_profile())
    fmt_ver = struct.unpack(">H", blob[4:6])[0]
    assert fmt_ver == FORMAT_VERSION


def test_packed_blob_encodes_profile_model_version() -> None:
    profile = _make_profile(model_version="9.9.9")
    blob = pack_profile_model(profile)
    ver_len = blob[6]
    assert ver_len == len("9.9.9")
    assert blob[7 : 7 + ver_len] == b"9.9.9"


def test_packed_blob_payload_length_matches_msgpack_body() -> None:
    profile = _make_profile()
    blob = pack_profile_model(profile)
    ver_len = blob[6]
    payload_len_offset = 7 + ver_len
    payload_len = struct.unpack(">I", blob[payload_len_offset : payload_len_offset + 4])[0]
    payload_start = payload_len_offset + 4
    expected = msgpack.packb(profile.to_dict(), use_bin_type=True)
    assert payload_len == len(expected)
    assert blob[payload_start : payload_start + payload_len] == expected


# ---------------------------------------------------------------------------
# Failure modes
# ---------------------------------------------------------------------------


def test_unpack_rejects_bad_magic() -> None:
    blob = pack_profile_model(_make_profile())
    corrupted = b"NOPE" + blob[4:]
    with pytest.raises(ValueError, match="bad magic"):
        unpack_profile_model(corrupted)


def test_unpack_rejects_unsupported_format_version() -> None:
    profile = _make_profile()
    # The public ``pack_profile_model`` no longer accepts a
    # ``format_version`` kwarg (it would silently produce blobs the
    # unpacker rejects). Use the test-only ``_pack_with_version_override``
    # to drive the parser's rejection path explicitly.
    blob = _pack_with_version_override(profile, format_version=99)
    with pytest.raises(ValueError, match="unsupported format_version"):
        unpack_profile_model(blob)


def test_unpack_rejects_crc_mismatch_when_payload_byte_corrupted() -> None:
    profile = _make_profile()
    blob = bytearray(pack_profile_model(profile))
    # Flip a bit deep inside the payload region — beyond the header so we
    # don't trip the format-version check or magic check first.
    ver_len = blob[6]
    payload_start = 7 + ver_len + 4
    # The blob is at least header + 1 byte msgpack + 4 byte crc, so this
    # index is always inside the payload.
    blob[payload_start] ^= 0xFF
    with pytest.raises(ValueError, match="crc mismatch"):
        unpack_profile_model(bytes(blob))


def test_unpack_rejects_crc_mismatch_when_trailer_corrupted() -> None:
    profile = _make_profile()
    blob = bytearray(pack_profile_model(profile))
    # Flip a bit in the trailing CRC; the recomputed CRC will not match.
    blob[-1] ^= 0xFF
    with pytest.raises(ValueError, match="crc mismatch"):
        unpack_profile_model(bytes(blob))


def test_unpack_rejects_truncated_input_inside_header() -> None:
    blob = pack_profile_model(_make_profile())
    # Drop everything past the magic — the fixed header itself is incomplete.
    with pytest.raises(ValueError, match="truncated"):
        unpack_profile_model(blob[:5])


def test_unpack_rejects_truncated_input_inside_payload_or_crc() -> None:
    blob = pack_profile_model(_make_profile())
    # Trim the last 5 bytes; the payload region cannot fit alongside the
    # CRC trailer the parser will look for.
    with pytest.raises(ValueError, match="truncated"):
        unpack_profile_model(blob[:-5])


def test_unpack_rejects_completely_empty_blob() -> None:
    with pytest.raises(ValueError, match="truncated"):
        unpack_profile_model(b"")


# ---------------------------------------------------------------------------
# Payload-level malformedness (after CRC + format-version pass)
# ---------------------------------------------------------------------------


def _wrap_payload_with_valid_envelope(payload: bytes, *, model_version: str = "1.0") -> bytes:
    """Build a fully-valid header + CRC trailer around ``payload``.

    Lets the payload-level malformedness tests focus on what the parser
    does after the format envelope has passed all its other checks.
    """

    header = build_header(
        format_version=FORMAT_VERSION,
        model_version=model_version,
        payload_len=len(payload),
    )
    body = header + payload
    return body + pack_crc(compute_crc(body))


def test_unpack_rejects_payload_that_is_not_a_msgpack_map() -> None:
    # A MessagePack-encoded list is valid msgpack but the ProfileModel
    # decoder expects a map at the top level.
    payload = msgpack.packb([1, 2, 3], use_bin_type=True)
    blob = _wrap_payload_with_valid_envelope(payload)
    with pytest.raises(ValueError, match="malformed payload"):
        unpack_profile_model(blob)


def test_unpack_rejects_payload_that_is_not_valid_msgpack() -> None:
    # 0xc1 is an explicitly-reserved MessagePack opcode — decoders MUST
    # reject it. Wrap a single such byte as a "payload" of length 1.
    blob = _wrap_payload_with_valid_envelope(b"\xc1")
    with pytest.raises(ValueError, match="malformed payload"):
        unpack_profile_model(blob)


def test_unpack_rejects_msgpack_map_missing_required_profile_fields() -> None:
    payload = msgpack.packb({"profile_id": "x"}, use_bin_type=True)
    blob = _wrap_payload_with_valid_envelope(payload)
    with pytest.raises(ValueError, match="malformed payload"):
        unpack_profile_model(blob)


def test_unpack_rejects_msgpack_map_with_wrong_field_types() -> None:
    # "traits" must be a list/tuple; passing an int trips ProfileModel.from_dict's
    # explicit TypeError, which the serializer wraps in a ValueError.
    payload = msgpack.packb(
        {
            "profile_id": "01HXY5Q9PJM0123456789ABCD0",
            "name": "buzzi",
            "kind": "user",
            "model_version": "1.2.0",
            "traits": 99,
            "pad_mappings": [],
            "transition_curve": "linear",
            "source_summary": "x",
        },
        use_bin_type=True,
    )
    blob = _wrap_payload_with_valid_envelope(payload)
    with pytest.raises(ValueError, match="malformed payload"):
        unpack_profile_model(blob)


# ---------------------------------------------------------------------------
# Size sanity (spec target: < 100 KB typical)
# ---------------------------------------------------------------------------


def test_typical_profile_blob_is_under_one_kilobyte() -> None:
    blob = pack_profile_model(_make_profile())
    # The spec says < 100 KB for a fully-elaborated profile; a minimal one
    # should be far smaller. This is a smoke check that the format isn't
    # accidentally bloated by some structural mistake.
    assert len(blob) < 1024
