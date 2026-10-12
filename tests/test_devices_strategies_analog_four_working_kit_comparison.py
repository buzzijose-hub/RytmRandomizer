"""Literal, synthetic checks of the bounded offline A4 experiment comparison."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
from typing import cast

import pytest

from conftest import analog_four_saved_kit_frame
from rytm_randomizer.devices.saved_kit_capture import (
    RegisteredSavedKitCaptureCapability,
    SavedKitCaptureFrame,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.devices.strategies import analog_four_working_kit_comparison as comparison
from rytm_randomizer.devices.strategies.analog_four_working_kit_comparison import (
    AnalogFourWorkingKitFrames,
    compare_analog_four_working_kit,
)

pytestmark = pytest.mark.fast


def _frame(*, kind: int = 82, slot: int = 3, overrides: dict[int, int] | None = None) -> bytes:
    raw = bytearray(analog_four_saved_kit_frame(unpacked_overrides=overrides))
    raw[6] = kind
    raw[9] = slot
    return bytes(raw)


def _experiment(track: int = 1, *, unknown: bool = False) -> AnalogFourWorkingKitFrames:
    offset = (128, 478, 828, 1178)[track - 1]
    baseline = _frame(overrides={offset: 0, offset + 1: 1})
    changes = {offset: 0, offset + 1: 2}
    if unknown:
        changes[2000] = 128
    working = _frame(kind=88, overrides=changes)
    saved = _frame(overrides=changes)
    return AnalogFourWorkingKitFrames(baseline, baseline, working, working, saved, baseline)


def _compare(
    frames: AnalogFourWorkingKitFrames, track: int = 1
) -> comparison.AnalogFourWorkingKitComparison:
    return compare_analog_four_working_kit(
        frames,
        track=track,
        evidence_origin="synthetic",
        baseline_label="0.00",
        changed_label="0.00",
    )


@pytest.mark.parametrize("track", [1, 2, 3, 4])
def test_six_stages_keep_literal_words_labels_metadata_and_selected_track_isolation(
    track: int,
) -> None:
    inputs = _experiment(track)
    result = _compare(inputs, track)
    assert result.track == track
    assert result.evidence_origin == "synthetic"
    assert [item.header_kind for item in result.frames] == [82, 82, 88, 88, 82, 82]
    assert [item.source_kind.value for item in result.frames] == [
        "indexed_kit_bank",
        "indexed_kit_bank",
        "working_kit_ram",
        "working_kit_ram",
        "indexed_kit_bank",
        "indexed_kit_bank",
    ]
    for observation, raw in zip(result.frames, inputs.ordered(), strict=True):
        assert observation.raw_sha256 == sha256(raw).hexdigest()
        assert observation.slot == 3
        assert observation.protocol_version == (1, 1)
        assert observation.kit_storage_version == 11
        assert observation.sound_storage_versions == (6, 6, 6, 6)
        assert [word.body_offset for word in observation.f1] == [128, 478, 828, 1178]
        assert [word.track for word in observation.f1] == [1, 2, 3, 4]
        assert [word.screen_label for word in observation.f1] == ["0.00"] * 4
    assert result.frames[0].f1[track - 1].native == 1
    assert result.frames[2].f1[track - 1].native == 2
    assert result.frames[2].body_sha256 == result.frames[4].body_sha256
    assert result.frames[2].raw_sha256 != result.frames[4].raw_sha256
    assert result.checks.baselines_raw_equal is True
    assert result.checks.baselines_body_equal is True
    assert result.checks.baselines_selected_f1_equal is True
    assert result.checks.selected_b_differs_from_u is True
    assert result.checks.repeat_raw_equal is True
    assert result.checks.repeat_body_equal is True
    assert result.checks.repeat_selected_f1_equal is True
    assert result.checks.post_save_body_equals_u is True
    assert result.checks.post_save_selected_f1_equals_u is True
    assert result.checks.recovery_raw_equals_b is True
    assert result.checks.recovery_body_equals_b is True
    assert result.checks.recovery_selected_f1_equals_b is True
    assert result.checks.only_selected_f1_body_changed is True
    assert result.checks.baseline_label_matches is True
    assert result.checks.changed_label_matches is True
    assert result.hardware_validated is False
    assert result.query_authority is result.send_authority is result.restore_authority is False
    assert result.complete_kit_claimed is result.current_baseline_coherence_established is False
    assert result.installed_firmware is None
    with pytest.raises(FrozenInstanceError):
        result.__setattr__("track", 2)


def test_whole_raw_and_body_diffs_keep_unknown_high_bits_explicit() -> None:
    result = _compare(_experiment(unknown=True))
    delta = result.differences[1]
    assert [
        (item.offset, item.before, item.after, item.classification.value) for item in delta.body
    ] == [(129, 1, 2, "verified_f1"), (2000, 0, 128, "other_unresolved")]
    assert delta.raw_equal is False
    assert delta.body_equal is False
    assert {item.classification.value for item in delta.raw} == {
        "verified_f1",
        "known_header",
        "known_integrity",
        "other_unresolved",
    }
    assert len(delta.raw) == sum(
        a != b
        for a, b in zip(
            _experiment(unknown=True).queried_indexed_baseline,
            _experiment(unknown=True).working_first,
            strict=True,
        )
    )
    assert result.checks.only_selected_f1_body_changed is False
    assert result.checks.repeat_raw_equal is True
    assert result.hardware_validated is False


def test_shared_packing_mask_with_unknown_change_is_not_attributed_only_to_f1() -> None:
    baseline = _frame(overrides={129: 0})
    working = _frame(kind=88, overrides={129: 128, 130: 128})
    result = _compare(
        AnalogFourWorkingKitFrames(
            baseline, baseline, working, working, _frame(overrides={129: 128, 130: 128}), baseline
        )
    )
    delta = result.differences[1]
    assert [(item.offset, item.classification.value) for item in delta.body] == [
        (129, "verified_f1"),
        (130, "other_unresolved"),
    ]
    # Both bytes share the mask at framed offset 154; an unknown bit remains explicit.
    assert (
        next(item for item in delta.raw if item.offset == 154).classification.value
        == "other_unresolved"
    )


def test_nonselected_track_f1_difference_is_known_but_fails_isolation() -> None:
    inputs = _experiment()
    other = _frame(kind=88, overrides={129: 2, 479: 128})
    result = _compare(replace(inputs, working_first=other))
    assert result.frames[2].f1[1].native == 128
    assert result.frames[2].f1[1].screen_label == "0.50"
    assert result.checks.only_selected_f1_body_changed is False
    assert result.checks.repeat_selected_f1_equal is True
    assert result.checks.repeat_body_equal is False
    assert result.checks.repeat_raw_equal is False
    assert result.checks.post_save_body_equals_u is False


def test_valid_disagreements_return_failure_checks_without_discarding_differences() -> None:
    inputs = _experiment()
    result = _compare(
        replace(
            inputs,
            queried_indexed_baseline=_frame(overrides={129: 3}),
            working_repeat=_frame(kind=88, overrides={129: 4}),
            post_save_indexed=_frame(overrides={129: 5}),
            recovered_indexed=_frame(overrides={129: 6}),
        )
    )
    assert result.checks.baselines_raw_equal is False
    assert result.checks.baselines_body_equal is False
    assert result.checks.baselines_selected_f1_equal is False
    assert result.checks.repeat_selected_f1_equal is False
    assert result.checks.post_save_selected_f1_equals_u is False
    assert result.checks.recovery_selected_f1_equals_b is False
    assert result.checks.recovery_body_equals_b is False
    assert result.checks.recovery_raw_equals_b is False
    assert all(delta.body for delta in result.differences)


def test_labels_are_forward_checks_not_unique_inverses_and_absence_is_unknown() -> None:
    inputs = _experiment()
    result = compare_analog_four_working_kit(
        inputs, track=1, evidence_origin="operator_supplied_files"
    )
    assert result.checks.baseline_label_matches is result.checks.changed_label_matches is None
    assert _compare(inputs).checks.selected_b_differs_from_u is True
    same = _compare(replace(inputs, working_first=_frame(kind=88, overrides={129: 1})))
    assert same.checks.selected_b_differs_from_u is False
    wrong = compare_analog_four_working_kit(
        inputs, track=1, evidence_origin="synthetic", baseline_label="0", changed_label="127.00"
    )
    assert wrong.checks.baseline_label_matches is wrong.checks.changed_label_matches is False


@pytest.mark.parametrize("track", [True, 0, 5, 1.0])
def test_invalid_selected_track_fails(track: object) -> None:
    with pytest.raises((TypeError, ValueError)):
        _compare(_experiment(), cast(int, track))


@pytest.mark.parametrize("origin", ["", "physical_validated", None, True])
def test_missing_or_unknown_evidence_origin_fails(origin: object) -> None:
    with pytest.raises(ValueError, match="evidence origin"):
        compare_analog_four_working_kit(_experiment(), track=1, evidence_origin=cast(str, origin))


@pytest.mark.parametrize("label", ["", " ", True])
def test_invalid_recorded_label_fails(label: object) -> None:
    with pytest.raises((TypeError, ValueError), match="label"):
        compare_analog_four_working_kit(
            _experiment(), track=1, evidence_origin="synthetic", baseline_label=cast(str, label)
        )


@pytest.mark.parametrize("raw", [b"", b"\xf0\xf7", bytes(2771), None])
def test_missing_or_wrong_extent_frame_fails_with_stage(raw: object) -> None:
    with pytest.raises(ValueError, match="working_first"):
        _compare(replace(_experiment(), working_first=cast(bytes, raw)))


@pytest.mark.parametrize(
    "field,raw",
    [
        ("working_first", _frame()),
        ("post_save_indexed", _frame(kind=88)),
        ("working_repeat", _frame(kind=88, slot=4)),
        ("queried_indexed_baseline", _frame(slot=4)),
    ],
    ids=("working_kind", "saved_kind", "working_slot", "indexed_slot"),
)
def test_wrong_source_kind_or_slot_refuses_mismatched_stage(field: str, raw: bytes) -> None:
    with pytest.raises(ValueError, match="kind|slot"):
        _compare(replace(_experiment(), **{field: raw}))


@pytest.mark.parametrize("overrides", [{3: 12}, {32: 0}, {39: 7}, {378: 0}, {128: 128}])
def test_semantically_invalid_but_checksummed_frames_are_refused_by_canonical_codec(
    overrides: dict[int, int],
) -> None:
    with pytest.raises(ValueError, match="working_first.*invalid"):
        _compare(replace(_experiment(), working_first=_frame(kind=88, overrides=overrides)))


def test_bad_integrity_or_protocol_is_refused() -> None:
    for offset in (7, -5):
        raw = bytearray(_experiment().working_first)
        raw[offset] ^= 1
        with pytest.raises(ValueError, match="invalid"):
            _compare(replace(_experiment(), working_first=bytes(raw)))


def test_registry_capture_roundtrip_failure_is_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    registered = resolve_saved_kit_capture_capability("analog_four_mk2")

    class InexactCapability:
        def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
            return registered.capability.decode_saved_kit_capture(frame)

        def encode_saved_kit_capture(self, decoded: SavedKitCaptureFrame) -> bytes:
            return b"inexact"

    monkeypatch.setattr(
        comparison,
        "resolve_saved_kit_capture_capability",
        lambda _: RegisteredSavedKitCaptureCapability(registered.device, InexactCapability()),
    )
    with pytest.raises(ValueError, match="round-trip"):
        _compare(_experiment())


@pytest.mark.parametrize("bad_header", [True, False])
def test_incompatible_registry_decoder_extents_are_refused(
    monkeypatch: pytest.MonkeyPatch, bad_header: bool
) -> None:
    registered = resolve_saved_kit_capture_capability("analog_four_mk2")
    inputs = _experiment()

    class IncompatibleCapability:
        def decode_saved_kit_capture(self, frame: bytes) -> SavedKitCaptureFrame:
            decoded = registered.capability.decode_saved_kit_capture(frame)
            return (
                replace(decoded, header=decoded.header[:-1])
                if bad_header
                else replace(decoded, unpacked=decoded.unpacked[:-1])
            )

        def encode_saved_kit_capture(self, decoded: SavedKitCaptureFrame) -> bytes:
            return inputs.manual_indexed_baseline

    monkeypatch.setattr(
        comparison,
        "resolve_saved_kit_capture_capability",
        lambda _: RegisteredSavedKitCaptureCapability(registered.device, IncompatibleCapability()),
    )
    with pytest.raises(ValueError, match="extents"):
        _compare(inputs)
