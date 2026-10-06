"""Retained-evidence and exact-byte tests for the optional offline capability."""

from __future__ import annotations

import builtins
import json
from dataclasses import replace
from decimal import localcontext
from pathlib import Path
from typing import cast

import pytest

from rytm_randomizer.devices import (
    AnalogFourNativeEncoding,
    AnalogFourNativeMutation,
    get_analog_four_native_field_capability,
)
from rytm_randomizer.devices.strategies.analog_four_kit_fields import (
    A4Kit,
    decode_a4_pitch_components,
)
from rytm_randomizer.devices.strategies.analog_four_native_fields import (
    AnalogFourNativeDomain,
)
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

pytestmark = pytest.mark.fast
ROOT = Path(__file__).resolve().parent
RIO = ROOT / "fixtures" / "rio145"
SAVED = ROOT / "fixtures" / "analog_four_saved_kit"


def _source(name: str = "A4_Test1_Init_Kit.syx") -> bytes:
    return (RIO / name).read_bytes()


def _unpacked(frame: bytes) -> bytes:
    return decode_analog_four_saved_kit_payload(frame[1:-1], require_trailer=True).unpacked


def _patch_source(source: bytes, offsets: tuple[int, ...], native: bytes) -> bytes:
    decoded = decode_analog_four_saved_kit_payload(source[1:-1], require_trailer=True)
    patched = bytearray(decoded.unpacked)
    for offset, value in zip(offsets, native, strict=True):
        patched[offset] = value
    encoded = encode_analog_four_saved_kit_payload(decoded.prefix, bytes(patched))
    return b"\xf0" + encoded.payload + b"\xf7"


@pytest.mark.parametrize(
    "name",
    [
        "A4_Test1_Init_Kit.syx",
        "A4_RIO145_CORE_RETURN_Kit.syx",
        "A4_Test2_T1_OSC1_FIN_P1_Kit.syx",
        "A4_Test3_T1_OSC1_FIN_M1_Kit.syx",
        "A4_Test4_T1_ENV2_DEPA_P1_Kit.syx",
        "A4_Test5_T1_ENV2_DEPA_M1_Kit.syx",
        "A4_Test6_T1_OSC1_FIN_P2_Kit.syx",
        "A4_Test7_T1_OSC1_FIN_M2_Kit.syx",
    ],
)
def test_empty_selection_is_exact_zero_depth_identity_for_retained_sources(name: str) -> None:
    capability = get_analog_four_native_field_capability()
    source = _source(name)
    result = capability.render_native_fields(source, ())
    assert result.framed_sysex == result.source_framed_sysex == source
    assert result.source_sha256 == result.sha256
    assert result.source_checksum == result.rendered_checksum
    assert result.changed_unpacked_offsets == result.changed_wire_offsets == ()
    assert result.intended_unpacked_offsets == result.applied_mutations == ()
    assert result.hardware_send_validated is False
    assert result.output_authority == "local-file-only"


def test_inventory_support_is_not_inferred_from_accessor_width_or_midi_catalog() -> None:
    fields = get_analog_four_native_field_capability().native_fields()
    assert len(fields) == 106
    assert sum(field.mutation_supported for field in fields) == 75
    by_key = {field.parameter: field for field in fields}
    for key in (
        "osc1_tracking",
        "osc1_am",
        "osc_retrigger",
        "oscillator_drift",
        "legato_mode",
        "portamento",
        "filter1_resonance_boost",
        "envf_length",
    ):
        assert by_key[key].protection_reason == "native_domain_unestablished"
    for field in fields:
        if field.parameter.startswith("amp_"):
            assert field.protection_reason == "oxi_amp_protection"
        if field.parameter.endswith("_fraction"):
            assert field.protection_reason == "hidden_fraction"
    assert by_key["osc1_fine"].protection_reason == "independently_unsafe_fine"
    assert by_key["env2_depth_a"].display_quantum == "0.0078125"
    assert by_key["env2_depth_a"].width == 2


def test_documented_field_inventory_matches_canonical_definitions_exactly() -> None:
    text = (ROOT.parent / "docs" / "A4_OFFLINE_NATIVE_FIELD_EVIDENCE.md").read_text()
    for metadata in get_analog_four_native_field_capability().native_fields():
        offsets = ",".join(str(offset) for offset in metadata.relative_offsets)
        if metadata.domain is None:
            domain = (
                "source-bound; step 256"
                if metadata.native_encoding is AnalogFourNativeEncoding.TUNE
                else "none"
            )
        elif metadata.enum_values:
            domain = "known enum codes"
        else:
            domain = f"{metadata.domain.minimum}..{metadata.domain.maximum} step {metadata.domain.quantum}"
        row = (
            f"| {metadata.parameter} | {offsets} | {metadata.native_encoding.name} | {domain} | "
            f"{metadata.protection_reason or 'mutable if source known'} |"
        )
        assert text.splitlines().count(row) == 1


def test_novel_values_for_every_supported_field_on_every_track_use_only_approved_bytes() -> None:
    capability = get_analog_four_native_field_capability()
    source = _source()
    readback = capability.read_native_fields(source)
    mutations: list[AnalogFourNativeMutation] = []
    for value in readback.values:
        if value.mutable:
            assert value.domain is not None
            index = (
                value.domain.index_of(value.encoded_native) + value.track * 3 + 1
            ) % value.domain.value_count
            mutations.append(
                AnalogFourNativeMutation(value.parameter, value.track, value.domain.value_at(index))
            )
    assert len(mutations) == 300
    first = capability.render_native_fields(source, mutations)
    assert capability.render_native_fields(source, mutations) == first
    assert first.changed_unpacked_offsets
    assert set(first.changed_unpacked_offsets) <= set(first.intended_unpacked_offsets)
    before, after = _unpacked(source), _unpacked(first.framed_sysex)
    for offset, (left, right) in enumerate(zip(before, after, strict=True)):
        if offset not in first.intended_unpacked_offsets:
            assert left == right
    for mutation in mutations:
        value = first.readback.value(mutation.parameter, mutation.track)
        assert value.encoded_native == mutation.encoded_native
        assert value.mutable
    for value in readback.values:
        if not value.mutable and not set(value.unpacked_offsets).intersection(
            first.intended_unpacked_offsets
        ):
            assert (
                first.readback.value(value.parameter, value.track).native_bytes
                == value.native_bytes
            )
    assert set(first.changed_wire_offsets) <= set(first.intended_wire_offsets)
    for track in range(4):
        old, new = A4Kit.from_bytes(before).sound(track), A4Kit.from_bytes(after).sound(track)
        for oscillator in (1, 2):
            assert (
                old.get_oscillator_pitch_components(oscillator)[1:]
                == new.get_oscillator_pitch_components(oscillator)[1:]
            )


def test_retained_four_track_return_readback_agrees_with_native_recipe() -> None:
    capability = get_analog_four_native_field_capability()
    result = capability.read_native_fields(_source("A4_RIO145_CORE_RETURN_Kit.syx"))
    recipe = json.loads((ROOT.parent / "specs" / "rio145" / "come_to_rio_a4_core.json").read_text())
    for value in result.values:
        if not value.mutable:
            continue
        track = recipe["tracks"][value.track - 1]
        if value.metadata.native_encoding is AnalogFourNativeEncoding.TUNE:
            assert value.screen_value == str(track["pitch"][value.parameter[:4]]["tune"])
        else:
            expected = next(
                section[value.parameter]
                for section in (
                    track.get(key, {})
                    for key in ("u7", "bipolar", "fixed_8_8", "enum", "destinations", "mod_depths")
                )
                if value.parameter in section
            )
            assert value.screen_value == str(expected)


@pytest.mark.parametrize(
    "field",
    [
        "osc1_waveform",
        "filter2_type",
        "envf_shape",
        "lfo1_multiplier",
        "lfo1_mode",
        "lfo2_waveform",
        "env2_destination_a",
    ],
)
def test_every_known_native_enum_code_renders_and_unknown_source_cannot_be_normalized(
    field: str,
) -> None:
    capability = get_analog_four_native_field_capability()
    source = _source()
    cell = capability.read_native_fields(source).value(field, 2)
    assert cell.domain is not None
    for raw, label in cell.metadata.enum_values:
        result = capability.render_native_fields(source, (AnalogFourNativeMutation(field, 2, raw),))
        assert result.readback.value(field, 2).screen_value == label
    unknown = _patch_source(source, cell.unpacked_offsets, b"\x7f")
    blocked = capability.read_native_fields(unknown).value(field, 2)
    assert blocked.encoded_native == 127 and blocked.screen_value is None
    assert not blocked.source_value_known and not blocked.mutable and blocked.domain is None
    with pytest.raises(ValueError, match="immutable"):
        capability.render_native_fields(
            unknown, (AnalogFourNativeMutation(field, 2, cell.encoded_native),)
        )
    assert capability.render_native_fields(unknown, ()).framed_sysex == unknown
    with pytest.raises(ValueError, match="unknown native selector"):
        capability.render_native_fields(source, (AnalogFourNativeMutation(field, 2, 127),))


@pytest.mark.parametrize(
    "name,expected",
    [("A4_Test2_T1_OSC1_FIN_P1_Kit.syx", 0x4003), ("A4_Test3_T1_OSC1_FIN_M1_Kit.syx", 0x3FFE)],
)
def test_tune_sampling_preserves_exact_hidden_fine_residual(name: str, expected: int) -> None:
    capability = get_analog_four_native_field_capability()
    source = _source(name)
    value = capability.read_native_fields(source).value("osc1_tune", 1)
    assert value.encoded_native == expected and value.domain is not None
    raw = expected + 7 * 256
    result = capability.render_native_fields(
        source, (AnalogFourNativeMutation("osc1_tune", 1, raw),)
    )
    assert result.readback.value("osc1_tune", 1).encoded_native == raw
    assert decode_a4_pitch_components(raw)[1:] == decode_a4_pitch_components(expected)[1:]
    assert (
        result.intended_unpacked_offsets
        == result.changed_unpacked_offsets
        == (value.unpacked_offsets[0],)
    )
    with pytest.raises(ValueError, match="exact native domain"):
        capability.render_native_fields(
            source, (AnalogFourNativeMutation("osc1_tune", 1, raw + 1),)
        )
    # A non-pitch change must not normalize either pitch word.
    other = capability.render_native_fields(
        source, (AnalogFourNativeMutation("filter1_resonance", 4, 91),)
    )
    assert other.readback.value("osc1_tune", 1).native_bytes == value.native_bytes


@pytest.mark.parametrize(
    "field,raw,text",
    [
        ("filter1_frequency", 0x4001, "64.00390625"),
        ("filter2_frequency", 0x3F7F, "63.49609375"),
        ("env2_depth_a", 0x4001, "0.0078125"),
        ("lfo2_depth_b", 0x3FFF, "-0.0078125"),
        ("envf_depth_b", 0, "-128"),
    ],
)
def test_fractional_native_precision_survives_render_readback_and_decimal_context(
    field: str, raw: int, text: str
) -> None:
    capability = get_analog_four_native_field_capability()
    with localcontext() as context:
        context.prec = 1
        result = capability.render_native_fields(
            _source(), (AnalogFourNativeMutation(field, 3, raw),)
        )
    value = result.readback.value(field, 3)
    assert value.encoded_native == raw and value.screen_value == text
    assert int.from_bytes(value.native_bytes, "big") == raw
    assert len(value.native_bytes) == 2


@pytest.mark.parametrize(
    "field",
    [
        "osc1_fine",
        "osc2_fine",
        "amp_volume",
        "amp_shape",
        "amp_pan",
        "amp_attack",
        "envf_depth_a_fraction",
        "osc1_tracking",
        "env2_length",
    ],
)
def test_protected_or_unestablished_fields_are_rejected_even_for_same_source_value(
    field: str,
) -> None:
    capability = get_analog_four_native_field_capability()
    cell = capability.read_native_fields(_source()).value(field, 1)
    with pytest.raises(ValueError, match="immutable"):
        capability.render_native_fields(
            _source(), (AnalogFourNativeMutation(field, 1, cell.encoded_native),)
        )


@pytest.mark.parametrize(
    "mutation",
    [
        AnalogFourNativeMutation("filter1_resonance", True, 20),
        AnalogFourNativeMutation("filter1_resonance", 5, 20),
        AnalogFourNativeMutation("filter1_resonance", 1, True),
        AnalogFourNativeMutation("filter1_resonance", 1, -1),
        AnalogFourNativeMutation("filter1_resonance", 1, 128),
        AnalogFourNativeMutation("filter1_frequency", 1, 0x7F01),
        AnalogFourNativeMutation("Filter1 Frequency", 1, 30),
        AnalogFourNativeMutation("rytm_src_1", 1, 30),
    ],
)
def test_foreign_keys_bool_ids_and_wrong_native_domains_fail_closed(
    mutation: AnalogFourNativeMutation,
) -> None:
    with pytest.raises(ValueError):
        get_analog_four_native_field_capability().render_native_fields(_source(), (mutation,))


def test_duplicate_and_wrong_record_requests_fail_closed() -> None:
    capability = get_analog_four_native_field_capability()
    mutation = AnalogFourNativeMutation("noise_level", 1, 81)
    with pytest.raises(ValueError, match="duplicate"):
        capability.render_native_fields(_source(), (mutation, mutation))
    with pytest.raises(TypeError, match="AnalogFourNativeMutation"):
        capability.render_native_fields(
            _source(), cast(tuple[AnalogFourNativeMutation, ...], (object(),))
        )


def test_unknown_numeric_and_coupled_sources_stay_byte_exact_and_cannot_be_overwritten() -> None:
    capability = get_analog_four_native_field_capability()
    for field, native in (
        ("osc1_tune", b"\xff\xff"),
        ("osc1_tune", b"\x7f\xff"),
        ("filter1_frequency", b"\x7f\xff"),
        ("env2_depth_a", b"\xff\x00"),
        ("noise_level", b"\xff"),
    ):
        cell = capability.read_native_fields(_source()).value(field, 1)
        source = _patch_source(_source(), cell.unpacked_offsets, native)
        read = capability.read_native_fields(source).value(field, 1)
        assert not read.mutable
        assert capability.render_native_fields(source, ()).framed_sysex == source
        with pytest.raises(ValueError, match="immutable"):
            capability.render_native_fields(
                source, (AnalogFourNativeMutation(field, 1, cell.encoded_native),)
            )


def test_source_validation_rejects_wrong_family_corruption_and_multiple_frames() -> None:
    capability = get_analog_four_native_field_capability()
    source = _source()
    for bad in (
        source + source,
        source[1:-1],
        source[:4] + b"\x07" + source[5:],
        source[:-4] + b"\x00\x00\x00\xf7",
        source + b"\x00",
    ):
        with pytest.raises(ValueError):
            capability.render_native_fields(bad, ())


def test_renderer_rejects_unapproved_converter_bytes_and_inexact_readback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.devices.strategies.analog_four_native_fields as native

    original = native._apply_native_value

    def corrupt(sound, source, raw):
        original(sound, source, raw)
        sound.set_u7("noise_level", 71)

    monkeypatch.setattr(native, "_apply_native_value", corrupt)
    with pytest.raises(ValueError, match="outside selected"):
        native.render_analog_four_native_fields(
            _source(), (AnalogFourNativeMutation("filter1_resonance", 1, 33),)
        )
    monkeypatch.setattr(native, "_apply_native_value", lambda sound, source, raw: None)
    with pytest.raises(ValueError, match="readback disagrees"):
        native.render_analog_four_native_fields(
            _source(), (AnalogFourNativeMutation("filter1_resonance", 1, 33),)
        )


def test_generic_native_f1_bytes_match_legacy_adapter_and_f2_reference_hashes() -> None:
    from rytm_randomizer.devices import (
        AnalogFourFilter1FrequencyCandidateMutation,
        get_analog_four_filter1_frequency_candidate_capability,
    )

    capability = get_analog_four_native_field_capability()
    f1source = (SAVED / "filter1_freq_127_source.syx").read_bytes()
    new = capability.render_native_fields(
        f1source, (AnalogFourNativeMutation("filter1_frequency", 1, 0x3F80),)
    )
    legacy = (
        get_analog_four_filter1_frequency_candidate_capability().render_filter1_frequency_candidate(
            f1source, (AnalogFourFilter1FrequencyCandidateMutation(1, "63.5"),)
        )
    )
    assert (
        new.framed_sysex
        == legacy.framed_sysex
        == (SAVED / "filter1_freq_063_50_expected.syx").read_bytes()
    )
    f2source = (SAVED / "filter2_res_000_source.syx").read_bytes()
    reference = capability.render_native_fields(
        f2source, (AnalogFourNativeMutation("filter2_resonance", 1, 127),)
    )
    assert reference.framed_sysex == (SAVED / "filter2_res_127_expected.syx").read_bytes()
    novel = capability.render_native_fields(
        f2source, (AnalogFourNativeMutation("filter2_resonance", 1, 64),)
    )
    assert novel.sha256 == "2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7"
    four = capability.render_native_fields(
        f2source,
        tuple(
            AnalogFourNativeMutation("filter2_resonance", track, raw)
            for track, raw in ((1, 16), (2, 48), (3, 80), (4, 112))
        ),
    )
    assert four.sha256 == "0e88aa6f15fd49c36696d5b8e09bda18ce5eeb8562c1a44ce46683c6deef819b"


def test_native_domain_sampling_is_exact_and_rejects_bool_indices() -> None:
    domain = AnalogFourNativeDomain(3, 0x7F03, 256)
    assert domain.value_count == 128
    assert domain.value_at(3) == 0x0303
    assert domain.index_of(0x0303) == 3
    for index in (True, -1, 128):
        with pytest.raises(ValueError):
            domain.value_at(index)


def test_optional_resolver_fails_closed_without_widening_device(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.devices import analog_four, get_device

    monkeypatch.setattr(analog_four.registry, "get_device", lambda _: get_device("analog_rytm_mk2"))
    with pytest.raises(TypeError, match="native field capability"):
        get_analog_four_native_field_capability()


def test_readback_and_render_never_import_midi_or_reach_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = _source()
    original = builtins.__import__

    def refuse(name, *args, **kwargs):
        assert name.split(".")[0] not in {"mido", "rtmidi"}
        assert "mido_provider" not in name and "real_midi_adapter" not in name
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuse)
    capability = get_analog_four_native_field_capability()
    result = capability.render_native_fields(
        source, (AnalogFourNativeMutation("noise_color", 4, 7),)
    )
    assert result.output_authority == "local-file-only" and not result.hardware_send_validated
    assert not hasattr(result, "send")


def test_shared_patch_verifier_rejects_codec_readback_and_foreign_wire_changes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import rytm_randomizer.devices.strategies.analog_four_saved_kit_candidate as candidate

    source = _source()
    decoded = candidate.validate_analog_four_candidate_source(source)
    original_decode = candidate.decode_analog_four_saved_kit_payload
    monkeypatch.setattr(
        candidate,
        "decode_analog_four_saved_kit_payload",
        lambda payload, **kwargs: replace(decoded, unpacked=bytes(len(decoded.unpacked))),
    )
    with pytest.raises(ValueError, match="exact native round trip"):
        candidate.encode_analog_four_candidate_patch(source, decoded, decoded.unpacked, ())
    monkeypatch.setattr(candidate, "decode_analog_four_saved_kit_payload", original_decode)
    # A valid but different slot has the same native body; it is not an approved field edit.
    wrong_frame = bytearray(source)
    wrong_frame[9] = (wrong_frame[9] + 1) % 128
    with pytest.raises(ValueError, match="wire bytes outside"):
        candidate.encode_analog_four_candidate_patch(
            bytes(wrong_frame), decoded, decoded.unpacked, ()
        )


def test_exact_native_format_rejects_bad_types_and_ranges() -> None:
    from rytm_randomizer.data.analog_four_kit_fields import format_a4_fixed_8_8, parse_a4_fixed_8_8

    with pytest.raises(TypeError):
        format_a4_fixed_8_8(True)
    with pytest.raises(ValueError):
        format_a4_fixed_8_8(0x8000)
    with pytest.raises(ValueError):
        parse_a4_fixed_8_8(1)


def test_registered_native_and_capture_capabilities_compose_without_io() -> None:
    from rytm_randomizer.devices import get_device
    from rytm_randomizer.devices.analog_four import (
        AnalogFourDevice,
        get_analog_four_saved_kit_capability,
    )

    capability = get_analog_four_native_field_capability()
    assert capability.native_fields() == get_analog_four_native_field_capability().native_fields()
    device = cast(AnalogFourDevice, get_device("analog_four_mk2"))
    decoded = device.decode_saved_kit_capture(_source())
    assert device.encode_saved_kit_capture(decoded) == _source()
    with pytest.raises(ValueError, match="framing"):
        device.decode_saved_kit_capture(b"bad")
    with pytest.raises(TypeError, match="unsupported frame"):
        device.encode_saved_kit_capture(object())
    assert get_analog_four_saved_kit_capability() is device
    from rytm_randomizer.devices.analog_four import AnalogFourSavedKitMutation

    legacy = device.render_saved_kit(
        (SAVED / "filter2_res_000_source.syx").read_bytes(),
        (AnalogFourSavedKitMutation(parameter="Filter2 Resonance", track=1, screen_value="64"),),
    )
    assert legacy.sha256 == "2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7"
