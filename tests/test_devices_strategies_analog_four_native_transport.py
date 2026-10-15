"""Exact descriptive CC7 evidence, with native and physical holds preserved."""

from __future__ import annotations

import builtins
import json
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
from types import MappingProxyType

import pytest

from rytm_randomizer import data
from rytm_randomizer.data.analog_four_display import ANALOG_FOUR_PARAMETER_DISPLAY
from rytm_randomizer.data.analog_four_kit_fields import (
    A4_BIPOLAR_FIELDS,
    A4_NATIVE_CONTINUOUS_U7_FIELDS,
)
from rytm_randomizer.data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from rytm_randomizer.data.analog_four_native_transport import (
    A4_NATIVE_CC7_BINDINGS,
    A4_NATIVE_TRANSPORT_CONFLICTS,
    A4_NATIVE_TRANSPORT_HOLDS,
    AnalogFourNativeTransportPreview,
)
from rytm_randomizer.devices import (
    AnalogFourNativeMutation,
    get_analog_four_native_field_capability,
    preview_analog_four_native_cc_transport,
)
from rytm_randomizer.devices.strategies import analog_four_native_transport as transport
from rytm_randomizer.devices.strategies.analog_four_native_fields import AnalogFourNativeEncoding
from rytm_randomizer.devices.strategies.analog_four_saved_kit_codec import (
    decode_analog_four_saved_kit_payload,
    encode_analog_four_saved_kit_payload,
)

pytestmark = pytest.mark.fast
RIO = Path(__file__).parent / "fixtures" / "rio145"


@pytest.fixture(scope="module")
def source() -> bytes:
    return (RIO / "A4_Test1_Init_Kit.syx").read_bytes()


def test_exact_binding_inventory_and_conflicts_are_immutable_canonical_facts() -> None:
    fields = {f.parameter: f for f in get_analog_four_native_field_capability().native_fields()}
    assert len(A4_NATIVE_CC7_BINDINGS) == 25
    assert sum(key in A4_NATIVE_CONTINUOUS_U7_FIELDS for key in A4_NATIVE_CC7_BINDINGS) == 17
    assert sum(key in A4_BIPOLAR_FIELDS for key in A4_NATIVE_CC7_BINDINGS) == 8
    assert {
        ANALOG_FOUR_SYNTH_TRACK_CC[name].cc_msb for name in A4_NATIVE_CC7_BINDINGS.values()
    } == {
        5,
        69,
        72,
        75,
        77,
        78,
        81,
        84,
        85,
        86,
        87,
        89,
        90,
        102,
        103,
        108,
        109,
        110,
        111,
        112,
        113,
        114,
        115,
        116,
        118,
    }
    assert data.A4_NATIVE_CC7_BINDINGS is A4_NATIVE_CC7_BINDINGS
    assert {
        key: ANALOG_FOUR_SYNTH_TRACK_CC[name].cc_msb for key, name in A4_NATIVE_CC7_BINDINGS.items()
    } == {
        "osc1_level": 69,
        "osc2_level": 78,
        "noise_sample_hold": 75,
        "noise_level": 77,
        "sync_amount": 84,
        "slide_time": 5,
        "vibrato_speed": 87,
        "filter1_resonance": 89,
        "filter2_resonance": 90,
        "envf_attack": 108,
        "envf_decay": 109,
        "envf_sustain": 110,
        "envf_release": 111,
        "env2_attack": 112,
        "env2_decay": 113,
        "env2_sustain": 114,
        "env2_release": 115,
        "osc1_pw": 72,
        "osc2_pw": 81,
        "bend_depth": 85,
        "filter1_overdrive": 86,
        "filter1_env_depth": 102,
        "filter2_env_depth": 103,
        "lfo1_speed": 116,
        "lfo2_speed": 118,
    }
    for key, name in A4_NATIVE_CC7_BINDINGS.items():
        assert fields[key].mutation_supported
        assert fields[key].evidence
        assert ANALOG_FOUR_SYNTH_TRACK_CC[name].cc_lsb is None
    assert set(A4_NATIVE_TRANSPORT_CONFLICTS) == {
        "osc1_pwm_speed",
        "osc2_pwm_speed",
        "osc1_pwm_depth",
        "osc2_pwm_depth",
        "vibrato_depth",
        "noise_fade",
    }
    assert not set(A4_NATIVE_CC7_BINDINGS).intersection(A4_NATIVE_TRANSPORT_CONFLICTS)
    for key, conflict in A4_NATIVE_TRANSPORT_CONFLICTS.items():
        assert conflict.native_scale == fields[key].native_encoding.name
        assert (
            conflict.display_scale
            == ANALOG_FOUR_PARAMETER_DISPLAY[conflict.manual_name].display_scale
        )
    with pytest.raises(TypeError):
        A4_NATIVE_CC7_BINDINGS["amp_volume"] = "Volume"


@pytest.mark.parametrize("native", range(128))
def test_every_cc7_value_on_all_25_canonical_native_domains(source: bytes, native: int) -> None:
    capability = get_analog_four_native_field_capability()
    before = capability.read_native_fields(source)
    mutations = tuple(AnalogFourNativeMutation(key, 1, native) for key in A4_NATIVE_CC7_BINDINGS)
    preview = preview_analog_four_native_cc_transport(source, mutations)
    expected = {
        key for key in A4_NATIVE_CC7_BINDINGS if before.value(key, 1).encoded_native != native
    }
    assert {row.parameter for row in preview.changes} == expected
    assert preview.mapping_complete
    for key in A4_NATIVE_CC7_BINDINGS:
        cell = before.value(key, 1)
        assert cell.source_value_known and cell.mutable and cell.domain is not None
        assert cell.domain.index_of(native) == native
    for row in preview.changes:
        assert row.before_native == row.before_cc7 == before.value(row.parameter, 1).encoded_native
        assert row.after_native == row.after_cc7 == native
        assert (
            row.cc_number
            == ANALOG_FOUR_SYNTH_TRACK_CC[A4_NATIVE_CC7_BINDINGS[row.parameter]].cc_msb
        )
        assert row.roundtrip_exact and row.blockers == ()


@pytest.mark.parametrize("filename", ["A4_Test1_Init_Kit.syx", "A4_RIO145_CORE_RETURN_Kit.syx"])
def test_real_retained_before_after_cells_on_every_track(filename: str) -> None:
    source = (RIO / filename).read_bytes()
    capability = get_analog_four_native_field_capability()
    before = capability.read_native_fields(source)
    mutations = tuple(
        AnalogFourNativeMutation(key, track, (before.value(key, track).encoded_native + 1) % 128)
        for track in range(1, 5)
        for key in A4_NATIVE_CC7_BINDINGS
    )
    rendered = capability.render_native_fields(source, mutations)
    preview = preview_analog_four_native_cc_transport(source, mutations)
    assert len(preview.changes) == 100
    for row in preview.changes:
        assert row.before_native == before.value(row.parameter, row.track_id).encoded_native
        assert (
            row.after_native == rendered.readback.value(row.parameter, row.track_id).encoded_native
        )
        assert row.roundtrip_exact


@pytest.mark.parametrize(
    "parameter,raw,reason",
    [
        *((key, 17, "native_transport_scale_conflict") for key in A4_NATIVE_TRANSPORT_CONFLICTS),
        ("filter1_frequency", 16257, "paired_precision_requires_separate_transport"),
        ("filter2_frequency", 16257, "paired_precision_requires_separate_transport"),
        ("env2_depth_a", 16385, "paired_precision_requires_separate_transport"),
        ("osc1_tune", 16384 + 256, "paired_precision_requires_separate_transport"),
        ("osc1_waveform", 3, "native_enum_transport_unverified"),
        ("osc1_detune", 20, "native_cc7_mapping_unverified"),
    ],
)
def test_mixed_unsupported_changes_are_retained_without_partial_executable_plan(
    source: bytes,
    parameter: str,
    raw: int,
    reason: str,
) -> None:
    preview = preview_analog_four_native_cc_transport(
        source,
        (
            AnalogFourNativeMutation("noise_level", 1, 23),
            AnalogFourNativeMutation(parameter, 2, raw),
        ),
    )
    assert not preview.mapping_complete
    assert len(preview.changes) == 2
    good, blocked = preview.changes
    assert good.after_cc7 == 23 and good.roundtrip_exact
    assert blocked.after_native == raw
    assert blocked.cc_number is blocked.before_cc7 is blocked.after_cc7 is None
    assert blocked.blockers == (reason,) and not blocked.roundtrip_exact
    assert reason in preview.blocked_reasons
    payload = preview.to_dict()
    assert payload["changes"][1]["blockers"] == [reason]
    assert payload["schema_version"] == "a4-native-transport-preview-v1"
    assert not {"events", "packets", "channel", "port"}.intersection(payload)
    assert all(not {"channel", "events", "packets"}.intersection(row) for row in payload["changes"])


def test_noops_including_unsupported_transport_are_omitted(source: bytes) -> None:
    before = get_analog_four_native_field_capability().read_native_fields(source)
    preview = preview_analog_four_native_cc_transport(
        source,
        tuple(
            AnalogFourNativeMutation(key, 1, before.value(key, 1).encoded_native)
            for key in ("noise_level", "filter1_frequency", "osc1_waveform", "osc1_pwm_speed")
        ),
    )
    assert preview.changes == () and preview.mapping_complete
    assert preview.blocked_reasons == A4_NATIVE_TRANSPORT_HOLDS
    assert preview == preview_analog_four_native_cc_transport(source, ())


@pytest.mark.parametrize(
    "parameter",
    ["amp_volume", "osc1_fine", "envf_depth_a_fraction", "osc1_sub", "lfo1_phase", "osc1_tracking"],
)
def test_native_protections_cannot_be_bypassed_by_transport_preview(
    source: bytes, parameter: str
) -> None:
    before = get_analog_four_native_field_capability().read_native_fields(source)
    with pytest.raises(ValueError, match="immutable"):
        preview_analog_four_native_cc_transport(
            source,
            (AnalogFourNativeMutation(parameter, 1, before.value(parameter, 1).encoded_native),),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        AnalogFourNativeMutation("noise_level", True, 1),
        AnalogFourNativeMutation("noise_level", 1, True),
        AnalogFourNativeMutation("noise_level", 0, 1),
        AnalogFourNativeMutation("noise_level", 5, 1),
        AnalogFourNativeMutation("noise_level", 1, 128),
        AnalogFourNativeMutation("noise_level", 1, -1),
        AnalogFourNativeMutation("missing", 1, 1),
        AnalogFourNativeMutation(False, 1, 1),
        object(),
    ],
)
def test_invalid_mutations_fail_before_permissive_conversion(
    source: bytes, mutation: object
) -> None:
    with pytest.raises((TypeError, ValueError)):
        preview_analog_four_native_cc_transport(source, (mutation,))


def test_wrong_container_duplicate_unknown_source_and_working_frame_refused(source: bytes) -> None:
    mutation = AnalogFourNativeMutation("noise_level", 1, 1)
    with pytest.raises(TypeError, match="source_frame"):
        preview_analog_four_native_cc_transport(bytearray(source), ())
    with pytest.raises(TypeError, match="tuple"):
        preview_analog_four_native_cc_transport(source, [mutation])
    with pytest.raises(ValueError, match="duplicate"):
        preview_analog_four_native_cc_transport(source, (mutation, mutation))
    decoded = decode_analog_four_saved_kit_payload(source[1:-1], require_trailer=True)
    prefix = bytearray(decoded.prefix)
    prefix[5] = 0x58
    working = (
        b"\xf0"
        + encode_analog_four_saved_kit_payload(bytes(prefix), decoded.unpacked).payload
        + b"\xf7"
    )
    with pytest.raises(ValueError, match="working|indexed"):
        preview_analog_four_native_cc_transport(working, ())
    payload = bytearray(decoded.unpacked)
    cell = (
        get_analog_four_native_field_capability().read_native_fields(source).value("noise_level", 1)
    )
    payload[cell.unpacked_offsets[0]] = 255
    unknown = (
        b"\xf0"
        + encode_analog_four_saved_kit_payload(decoded.prefix, bytes(payload)).payload
        + b"\xf7"
    )
    with pytest.raises(ValueError, match="immutable"):
        preview_analog_four_native_cc_transport(unknown, (mutation,))


@pytest.mark.parametrize(
    "field,value",
    [
        ("ready", True),
        ("output_authority", "live"),
        ("hardware_send_validated", True),
        ("channel_routing_verified", True),
        ("mapping_complete", True),
        ("blocked_reasons", ()),
    ],
)
def test_direct_construction_and_replacement_cannot_lift_authority(
    field: str, value: object
) -> None:
    preview = AnalogFourNativeTransportPreview(())
    with pytest.raises(TypeError):
        AnalogFourNativeTransportPreview(changes=(), **{field: value})
    with pytest.raises(ValueError, match="init=False"):
        replace(preview, **{field: value})
    with pytest.raises(FrozenInstanceError):
        preview.ready = True
    assert (
        preview.ready
        is preview.hardware_send_validated
        is preview.channel_routing_verified
        is False
    )
    assert preview.output_authority == "offline-review-only"
    assert json.loads(json.dumps(preview.to_dict()))["blocked_reasons"] == list(
        A4_NATIVE_TRANSPORT_HOLDS
    )


@pytest.mark.parametrize("changes", [[], (object(),)])
def test_preview_rejects_noncanonical_row_containers(changes: object) -> None:
    with pytest.raises(TypeError, match="tuple"):
        AnalogFourNativeTransportPreview(changes)


def test_roundtrip_defense_and_canonical_contract_drift_fail_closed(
    source: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    read = get_analog_four_native_field_capability().read_native_fields(source)
    cell = read.value("noise_level", 1)
    for encoding in (AnalogFourNativeEncoding.FINE, AnalogFourNativeEncoding.Q8_8):
        assert (
            transport._unsupported_reason(
                replace(cell, metadata=replace(cell.metadata, native_encoding=encoding))
            )
            == "paired_precision_requires_separate_transport"
        )
    mapping = ANALOG_FOUR_SYNTH_TRACK_CC["Noise Level"]
    display = ANALOG_FOUR_PARAMETER_DISPLAY["Noise Level"]
    with monkeypatch.context() as patch:
        patch.setattr(
            transport,
            "ANALOG_FOUR_SYNTH_TRACK_CC",
            MappingProxyType(
                {**ANALOG_FOUR_SYNTH_TRACK_CC, "Noise Level": replace(mapping, cc_lsb=45)}
            ),
        )
        assert transport._unsupported_reason(cell) == "native_cc7_contract_mismatch"
    with monkeypatch.context() as patch:
        patch.setattr(
            transport,
            "ANALOG_FOUR_PARAMETER_DISPLAY",
            MappingProxyType(
                {
                    **ANALOG_FOUR_PARAMETER_DISPLAY,
                    "Noise Level": replace(display, transport_ready=False),
                }
            ),
        )
        assert transport._unsupported_reason(cell) == "native_cc7_contract_mismatch"
    monkeypatch.setattr(transport, "_project_cc7", lambda value: (1, False))
    preview = preview_analog_four_native_cc_transport(
        source, (AnalogFourNativeMutation("noise_level", 1, 23),)
    )
    assert preview.changes[0].blockers == ("native_cc7_contract_mismatch",)
    assert not preview.mapping_complete


def test_review_does_not_import_backend_or_grant_output_and_rows_are_frozen(
    source: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = builtins.__import__

    def refuse(name, *args, **kwargs):
        assert name.split(".")[0] not in {"mido", "rtmidi"}
        assert "mido_provider" not in name and "real_midi_adapter" not in name
        return original(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", refuse)
    preview = preview_analog_four_native_cc_transport(
        source, (AnalogFourNativeMutation("noise_level", 4, 23),)
    )
    assert preview.mapping_complete and not preview.ready
    assert not hasattr(preview, "send")
    with pytest.raises(FrozenInstanceError):
        preview.changes[0].after_native = 9
    payload = preview.to_dict()
    payload["changes"][0]["blockers"].append("tampered_copy")
    assert preview.changes[0].blockers == ()


def test_decision_boundary_records_only_passive_evidence_metrics(source: bytes) -> None:
    from rytm_randomizer.observability.metrics import get_metrics

    metrics = get_metrics()
    before = metrics.errors_by_kind.copy()
    cc_counts = metrics.cc_sent_by_channel.copy()
    preview_analog_four_native_cc_transport(
        source, (AnalogFourNativeMutation("noise_level", 1, 23),)
    )
    preview_analog_four_native_cc_transport(
        source, (AnalogFourNativeMutation("filter1_frequency", 1, 16257),)
    )
    with pytest.raises(TypeError):
        preview_analog_four_native_cc_transport(
            source, (AnalogFourNativeMutation("noise_level", 1, True),)
        )
    assert (
        metrics.errors_by_kind["a4_native_transport_mapping_incomplete"]
        == before["a4_native_transport_mapping_incomplete"] + 1
    )
    assert (
        metrics.errors_by_kind["a4_native_transport_invalid_request"]
        == before["a4_native_transport_invalid_request"] + 1
    )
    assert metrics.cc_sent_by_channel == cc_counts
