"""Tests for guarded RUSH16 active-kit apply calibration."""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
import yaml

from rytm_randomizer import app, mido_provider
from rytm_randomizer.devices import strategies as device_strategies
from rytm_randomizer.devices.strategies import ANALOG_FOUR_KIT_CODEC, ANALOG_RYTM_KIT_CODEC
from rytm_randomizer.senders import rush01_midi_transport
from rytm_randomizer.snapshot import encode_elektron_u14, pack_elektron_7bit
from rytm_randomizer.style_analysis import rush16_apply_calibration as calibration
from rytm_randomizer.style_analysis.rush01_midi_compiler import (
    STATUS_READY,
    Rush01DeviceConfig,
    compile_rush01_midi_plan,
)
from rytm_randomizer.style_analysis.rush16_anchor_audition import rush16_hardware_blockers
from rytm_randomizer.style_analysis.rush16_apply_calibration import (
    RUSH16_CALIBRATION_VERSION,
    Rush16CalibrationAddress,
    Rush16CalibrationTarget,
    accept_rush16_calibration_observation,
    analyze_rush16_kit_differential,
    apply_rush16_calibration_promotions,
    build_rush16_calibration_plan,
    load_or_create_rush16_checkpoint,
    next_rush16_calibration_step,
    rush16_calibration_plan_sha256,
    rush16_calibration_plan_to_dict,
    rush16_calibration_progress,
    rush16_calibration_step_requires_saved_kit,
    rush16_steps_share_witness_location,
    validate_rush16_calibration_baseline_continuity,
    write_rush16_checkpoint,
)

pytestmark = pytest.mark.fast

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SPEC_ROOT = PROJECT_ROOT / "specs" / "rush16"
RYTM_TRACKS = ("BD", "SD", "RS", "CP", "BT", "LT", "MT", "HT", "CH", "OH", "CY", "CB")
A4_TRACKS = ("T1", "T2", "T3", "T4")


def _specs() -> dict[str, object]:
    return {
        path.name: yaml.safe_load(path.read_text(encoding="utf-8"))
        for path in sorted(SPEC_ROOT.glob("*.yaml"))
        if path.name != "RUSH16_FAMILY.yaml"
    }


def _config(device: str) -> Rush01DeviceConfig:
    tracks = RYTM_TRACKS if device == "rytm" else A4_TRACKS
    return Rush01DeviceConfig(
        device,
        "Exact Output",
        {track: index + 1 for index, track in enumerate(tracks)},
        "Exact Input",
    )


def _synthetic_frame(codec=ANALOG_RYTM_KIT_CODEC) -> bytes:
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


def _changed_frame_with_value(frame: bytes, value: int) -> bytes:
    decoded = ANALOG_RYTM_KIT_CODEC.decode_frame(frame)
    unpacked = bytearray(decoded.unpacked)
    unpacked[len(decoded.spec.required_unpacked_prefix) + 20] = value
    return ANALOG_RYTM_KIT_CODEC.encode_frame(decoded, unpacked=bytes(unpacked))


def _changed_frame(frame: bytes) -> bytes:
    return _changed_frame_with_value(frame, 37)


def _differential(*, changed: bool = True) -> dict[str, object]:
    offsets = [20] if changed else []
    return {
        "baseline_sha256": "a" * 64,
        "changed_sha256": ("b" if changed else "a") * 64,
        "baseline_round_trip_identical": True,
        "changed_round_trip_identical": True,
        "frame_offsets": offsets,
        "header_offsets": [],
        "packed_offsets": offsets,
        "packed_frame_offsets": offsets,
        "unpacked_offsets": offsets,
        "integrity_frame_offsets": [],
    }


def _narrow_family(plan: object, family_id: str):
    family = next(family for family in plan.families if family.family_id == family_id)
    steps = tuple(step for step in plan.steps if step.family_id == family_id)
    return replace(plan, families=(family,), steps=steps)


def _complete_lookup_checkpoint(
    plan: object,
    path: Path,
    *,
    displayed_by_raw: dict[int, object],
    approved_by_raw: dict[int, list[object]],
) -> dict[str, object]:
    checkpoint = load_or_create_rush16_checkpoint(
        path,
        plan,
        hardware_unit="Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    while (step := next_rush16_calibration_step(plan, checkpoint)) is not None:
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value=displayed_by_raw[step.raw_value],
            approved_requested_values=approved_by_raw.get(step.raw_value, []),
            differential=_differential(),
        )
    return checkpoint


def test_calibration_plans_group_all_blockers_and_encode_only_cc_packets() -> None:
    specs = _specs()
    rytm = build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))
    a4 = build_rush16_calibration_plan("a4", specs, config=_config("a4"))

    assert len(rytm.families) == 7
    assert len(rytm.steps) == 67
    assert sum(rytm.blocker_counts_before.values()) == 29
    assert len(a4.families) == 18
    assert len(a4.steps) == 896
    assert set(a4.blocker_counts_before.values()) == {91}
    noise = next(family for family in a4.families if family.family_id == "a4_noise_color")
    assert not noise.supported
    assert not noise.candidates
    assert "No documented Noise Color MIDI address" in noise.evidence_source
    assert "PR #214" in a4.filter2_resonance_evidence
    assert not any("resonance" in family.family_id for family in a4.families)
    assert (
        calibration.build_rush16_calibration_catalog("rytm", specs)["required_observations"] == 67
    )

    first = rytm.steps[0]
    assert first.context_messages == ((0xB0, 15, 26),)
    assert first.candidate_messages == ((0xB0, 23, 0),)
    for plan in (rytm, a4):
        for step in plan.steps:
            assert step.ordered_messages
            assert all(packet[0] & 0xF0 == 0xB0 for packet in step.ordered_messages)
            assert all(0 <= packet[1] <= 119 for packet in step.ordered_messages)
            assert all(0 <= packet[2] <= 127 for packet in step.ordered_messages)
    document = rush16_calibration_plan_to_dict(rytm)
    assert document["safety"] == {
        "app_arm_required": True,
        "one_candidate_per_invocation": True,
        "manual_sound_parameter_entry": False,
        "outbound_message_types": ["CC"],
        "program_change": False,
        "transport": False,
        "realtime": False,
        "sysex_output": False,
        "save_pattern_song_project": False,
    }
    assert rush16_calibration_plan_sha256(rytm) == rush16_calibration_plan_sha256(
        build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))
    )

    coarse = next(
        family for family in a4.families if family.family_id == "a4_oscillator_coarse_tune"
    )
    fine = next(family for family in a4.families if family.family_id == "a4_oscillator_fine_tune")
    assert coarse.promotion_mode == fine.promotion_mode == "lookup"
    assert coarse.candidates == (63, 64, 65, 75, 76, 77, 82, 83, 84)
    assert fine.candidates == (56, 57, 58, 59, 63, 64, 65)
    assert {
        (witness.address.message_type, witness.address.value_domain, witness.address.controller)
        for witness in coarse.witnesses
    } == {("CC", "7bit", 16), ("CC", "7bit", 17)}
    assert {
        (witness.address.message_type, witness.address.value_domain, witness.address.controller)
        for witness in fine.witnesses
    } == {("CC", "7bit", 48), ("CC", "7bit", 49)}
    pitch_steps = tuple(
        step for step in a4.steps if step.family_id in {coarse.family_id, fine.family_id}
    )
    assert all(len(step.candidate_messages) == 1 for step in pitch_steps)
    assert not any(step.value_domain == "14bit" for step in pitch_steps)
    packet_routes: dict[tuple[str, tuple[tuple[int, int, int], ...]], str] = {}
    for step in pitch_steps:
        route = (step.track, step.candidate_messages)
        previous = packet_routes.setdefault(route, step.family_id)
        assert previous == step.family_id


def test_a4_pitch_families_promote_separate_single_cc_addresses(tmp_path: Path) -> None:
    specs = _specs()
    full_plan = build_rush16_calibration_plan("a4", specs, config=_config("a4"))
    coarse_plan = _narrow_family(full_plan, "a4_oscillator_coarse_tune")
    checkpoint = _complete_lookup_checkpoint(
        coarse_plan,
        tmp_path / "coarse.json",
        displayed_by_raw={raw: raw - 64 for raw in coarse_plan.families[0].candidates},
        approved_by_raw={64: [0], 76: [12], 83: [19]},
    )
    promotion = checkpoint["promotions"][0]
    assert {target["value_domain"] for target in promotion["targets"]} == {"7bit"}
    assert {
        (target["address"]["message_type"], target["address"]["controller"])
        for target in promotion["targets"]
    } == {("CC", 16), ("CC", 17)}

    filename = "01_DRY_AUTHORITY_A4.yaml"
    promoted = apply_rush16_calibration_promotions(
        compile_rush01_midi_plan("a4", specs[filename], config=_config("a4")),
        spec_filename=filename,
        checkpoint=checkpoint,
    )
    osc1 = next(
        field
        for field in promoted.fields
        if field.semantic_path == "tracks.T1.oscillator_1.coarse_tune_semitones"
    )
    osc2 = next(
        field
        for field in promoted.fields
        if field.semantic_path == "tracks.T1.oscillator_2.coarse_tune_semitones"
    )
    assert osc1.status == osc2.status == STATUS_READY
    assert osc1.ordered_midi_bytes == ((0xB0, 16, 64),)
    assert osc2.ordered_midi_bytes == ((0xB0, 17, 76),)
    assert osc1.controller_lsb is None and osc2.controller_lsb is None


def test_a4_pitch_display_labels_and_duplicate_route_guard() -> None:
    plan = build_rush16_calibration_plan("a4", _specs(), config=_config("a4"))
    coarse_step = next(step for step in plan.steps if step.family_id == "a4_oscillator_coarse_tune")
    fine_step = next(step for step in plan.steps if step.family_id == "a4_oscillator_fine_tune")
    assert "first pitch value" in calibration.rush16_calibration_display_label(plan, coarse_step)
    assert "second pitch value" in calibration.rush16_calibration_display_label(plan, fine_step)

    coarse = next(family for family in plan.families if family.family_id == coarse_step.family_id)
    fine = next(family for family in plan.families if family.family_id == fine_step.family_id)
    duplicate = replace(fine, witnesses=coarse.witnesses)
    with pytest.raises(ValueError, match="share one outbound address"):
        calibration._validate_distinct_family_witness_addresses((coarse, duplicate))


def test_selector_promotion_requires_both_witnesses_and_neighbor_evidence(
    tmp_path: Path,
) -> None:
    specs = _specs()
    full_plan = build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))
    plan = _narrow_family(full_plan, "rytm_ch_osc_reset")
    checkpoint_path = tmp_path / "checkpoint.json"
    checkpoint = load_or_create_rush16_checkpoint(
        checkpoint_path,
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    observed_steps = []
    while (step := next_rush16_calibration_step(plan, checkpoint)) is not None:
        observed_steps.append(step)
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value="OFF" if step.raw_value == 0 else "ON",
            approved_requested_values=(
                [0, 0] if step.raw_value == 0 and step.witness_role == "repeat" else []
            ),
            differential=_differential(),
        )
        if next_rush16_calibration_step(plan, checkpoint) is not None:
            assert checkpoint["promotions"] == []

    assert [(step.raw_value, step.witness_role) for step in observed_steps] == [
        (0, "primary"),
        (0, "repeat"),
        (127, "primary"),
        (127, "repeat"),
    ]

    promotions = checkpoint["promotions"]
    assert isinstance(promotions, list) and len(promotions) == 1
    approved = [
        row["approved_requested_values"]
        for row in checkpoint["observations"]
        if row["approved_requested_values"]
    ]
    assert approved == [[0]]
    assert len(promotions[0]["targets"]) == 4
    assert {target["raw_value"] for target in promotions[0]["targets"]} == {0}
    progress = rush16_calibration_progress(plan, checkpoint)
    assert progress.families_complete == 1
    assert progress.observations_remaining == 0

    spec_name = "01_DRY_AUTHORITY_RYTM.yaml"
    source_plan = compile_rush01_midi_plan("rytm", specs[spec_name], config=_config("rytm"))
    before = rush16_hardware_blockers(specs[spec_name], source_plan)
    promoted = apply_rush16_calibration_promotions(
        source_plan,
        spec_filename=spec_name,
        checkpoint=checkpoint,
    )
    field = next(
        field for field in promoted.fields if field.semantic_path == "tracks.CH.synth.Osc Reset"
    )
    assert field.status == STATUS_READY
    assert field.ordered_midi_bytes == ((0xB8, 21, 0),)
    assert len(rush16_hardware_blockers(specs[spec_name], promoted)) == len(before) - 1

    write_rush16_checkpoint(checkpoint_path, checkpoint)
    loaded = load_or_create_rush16_checkpoint(
        checkpoint_path,
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    assert loaded == checkpoint
    with pytest.raises(ValueError, match="hardware_unit"):
        load_or_create_rush16_checkpoint(
            checkpoint_path,
            plan,
            hardware_unit="Different Unit",
            disposable_target="DISPOSABLE_INIT",
        )


def test_same_address_repeat_uses_primary_saved_kit_evidence(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "checkpoint.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    differentials = iter(
        (
            _differential(changed=False),
            _differential(changed=False),
            _differential(),
            _differential(changed=False),
        )
    )
    while (step := next_rush16_calibration_step(plan, checkpoint)) is not None:
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value="OFF" if step.raw_value == 0 else "ON",
            approved_requested_values=[0] if step.raw_value == 0 else [],
            differential=next(differentials),
        )

    assert len(checkpoint["promotions"]) == 1
    assert {target["raw_value"] for target in checkpoint["promotions"][0]["targets"]} == {0}


def test_display_repeat_promotes_with_one_saved_dump_per_candidate(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "checkpoint.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)

    primary_zero = next_rush16_calibration_step(plan, checkpoint)
    assert primary_zero is not None
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=primary_zero,
        display_value="OFF",
        approved_requested_values=[0],
        differential=analyze_rush16_kit_differential("rytm", baseline, baseline),
    )
    repeat_zero = next_rush16_calibration_step(plan, checkpoint)
    assert repeat_zero is not None
    assert rush16_steps_share_witness_location(plan, primary_zero, repeat_zero)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=repeat_zero,
        display_value="OFF",
        approved_requested_values=[],
        differential=None,
        evidence_reference_step_id=primary_zero.step_id,
    )
    validate_rush16_calibration_baseline_continuity(checkpoint, baseline)

    primary_on = next_rush16_calibration_step(plan, checkpoint)
    assert primary_on is not None
    assert not rush16_steps_share_witness_location(plan, primary_zero, primary_on)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=primary_on,
        display_value="ON",
        approved_requested_values=[],
        differential=analyze_rush16_kit_differential("rytm", baseline, changed),
    )
    repeat_on = next_rush16_calibration_step(plan, checkpoint)
    assert repeat_on is not None
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=repeat_on,
        display_value="ON",
        approved_requested_values=[],
        differential=None,
        evidence_reference_step_id=primary_on.step_id,
    )

    assert len(checkpoint["promotions"]) == 1
    assert checkpoint["observations"][-1]["evidence_kind"] == "display_repeat"
    assert checkpoint["observations"][-1]["differential"] is None
    validate_rush16_calibration_baseline_continuity(checkpoint, changed)


def test_display_repeat_rejects_unlinked_or_cross_track_evidence(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "rytm.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    primary = next_rush16_calibration_step(plan, checkpoint)
    assert primary is not None
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=primary,
        display_value="OFF",
        approved_requested_values=[0],
        differential=_differential(changed=False),
    )
    repeat = next_rush16_calibration_step(plan, checkpoint)
    assert repeat is not None

    for reference, display, approvals, message in (
        (None, "OFF", [], "requires an evidence reference"),
        ("wrong", "OFF", [], "immediately preceding"),
        (primary.step_id, "ON", [], "does not match"),
        (primary.step_id, "OFF", [0], "cannot add semantic approvals"),
    ):
        with pytest.raises(ValueError, match=message):
            accept_rush16_calibration_observation(
                plan,
                checkpoint,
                step=repeat,
                display_value=display,
                approved_requested_values=approvals,
                differential=None,
                evidence_reference_step_id=reference,
            )

    missing_differential = deepcopy(checkpoint)
    missing_differential["observations"][-1]["differential"] = None
    with pytest.raises(ValueError, match="no saved KIT differential"):
        accept_rush16_calibration_observation(
            plan,
            missing_differential,
            step=repeat,
            display_value="OFF",
            approved_requested_values=[],
            differential=None,
            evidence_reference_step_id=primary.step_id,
        )

    a4_plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_filter_1_frequency",
    )
    a4_checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        a4_plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    a4_primary = next_rush16_calibration_step(a4_plan, a4_checkpoint)
    assert a4_primary is not None
    a4_checkpoint = accept_rush16_calibration_observation(
        a4_plan,
        a4_checkpoint,
        step=a4_primary,
        display_value=0,
        approved_requested_values=[],
        differential=_differential(),
    )
    a4_confirmation = next(
        step
        for step in a4_plan.steps
        if step.raw_value == a4_primary.raw_value and step.witness_role != a4_primary.witness_role
    )
    assert not rush16_steps_share_witness_location(a4_plan, a4_primary, a4_confirmation)
    with pytest.raises(ValueError, match="cross-track"):
        calibration._validate_display_repeat_evidence(
            a4_plan.families[0],
            a4_checkpoint["observations"],
            step=a4_confirmation,
            display_value=0,
            approvals=[],
            evidence_reference_step_id=a4_primary.step_id,
        )


def test_cross_track_witnesses_each_require_saved_kit_evidence() -> None:
    plan = build_rush16_calibration_plan("a4", _specs(), config=_config("a4"))
    family = next(family for family in plan.families if family.family_id == "a4_filter_1_frequency")
    rows = [
        {
            "witness_role": family.witnesses[0].role,
            "differential": _differential(),
        },
        {
            "witness_role": family.witnesses[1].role,
            "differential": _differential(changed=False),
        },
    ]

    assert not calibration._family_has_saved_kit_evidence(family, rows)
    rows[1]["differential"] = _differential()
    assert calibration._family_has_saved_kit_evidence(family, rows)


def test_baseline_continuity_uses_last_accepted_changed_kit_hash(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_bd_sharp_waveform",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "checkpoint.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)
    validate_rush16_calibration_baseline_continuity(checkpoint, baseline)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=plan.steps[0],
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[],
        differential=analyze_rush16_kit_differential("rytm", baseline, changed),
    )

    validate_rush16_calibration_baseline_continuity(checkpoint, changed)
    with pytest.raises(ValueError, match="does not match the last accepted saved"):
        validate_rush16_calibration_baseline_continuity(checkpoint, baseline)

    invalid = deepcopy(checkpoint)
    invalid["observations"][-1]["differential"]["changed_sha256"] = None
    with pytest.raises(ValueError, match="missing its changed KIT SHA-256"):
        validate_rush16_calibration_baseline_continuity(invalid, changed)


def test_saved_kit_and_display_repeat_evidence_validation_edges(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    family = plan.families[0]
    primary = plan.steps[0]
    repeat = next(
        step
        for step in plan.steps
        if step.raw_value == primary.raw_value and step.witness_role == "repeat"
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "checkpoint.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )

    with pytest.raises(ValueError, match="cannot reference another step"):
        accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=primary,
            display_value="OFF",
            approved_requested_values=[0],
            differential=_differential(changed=False),
            evidence_reference_step_id="other",
        )
    with pytest.raises(ValueError, match="no saved KIT differential"):
        validate_rush16_calibration_baseline_continuity(
            {"observations": [{"differential": None}]},
            _synthetic_frame(),
        )

    with pytest.raises(ValueError, match="preceding saved KIT observation"):
        calibration._validate_display_repeat_evidence(
            family,
            [],
            step=repeat,
            display_value="OFF",
            approvals=[],
            evidence_reference_step_id=primary.step_id,
        )
    reference = {
        "step_id": primary.step_id,
        "family_id": family.family_id,
        "raw_value": primary.raw_value,
        "witness_role": primary.witness_role,
        "display_value": "OFF",
        "differential": _differential(changed=False),
    }
    wrong_family = dict(reference, family_id="other")
    with pytest.raises(ValueError, match="same family and raw candidate"):
        calibration._validate_display_repeat_evidence(
            family,
            [wrong_family],
            step=repeat,
            display_value="OFF",
            approvals=[],
            evidence_reference_step_id=primary.step_id,
        )
    missing_role = dict(reference, witness_role=None)
    with pytest.raises(ValueError, match="no witness role"):
        calibration._validate_display_repeat_evidence(
            family,
            [missing_role],
            step=repeat,
            display_value="OFF",
            approvals=[],
            evidence_reference_step_id=primary.step_id,
        )

    invalid_differentials: list[tuple[dict[str, object], str]] = []
    unstable = _differential()
    unstable["baseline_round_trip_identical"] = False
    invalid_differentials.append((unstable, "stable KIT round trips"))
    missing_hash = _differential()
    missing_hash["changed_sha256"] = None
    invalid_differentials.append((missing_hash, "requires KIT SHA-256 values"))
    changed_header = _differential()
    changed_header["header_offsets"] = [1]
    invalid_differentials.append((changed_header, "changed KIT header bytes"))
    hash_payload_mismatch = _differential()
    hash_payload_mismatch["unpacked_offsets"] = []
    invalid_differentials.append((hash_payload_mismatch, "hash/payload evidence is inconsistent"))
    missing_packed = _differential()
    missing_packed["frame_offsets"] = []
    invalid_differentials.append((missing_packed, "missing packed payload evidence"))
    no_op_offsets = _differential(changed=False)
    no_op_offsets["frame_offsets"] = [1]
    invalid_differentials.append(
        (no_op_offsets, "no-op differential contains changed byte offsets")
    )
    invalid_sequence = _differential()
    invalid_sequence["frame_offsets"] = "bad"
    invalid_differentials.append((invalid_sequence, "frame_offsets must be a sequence"))
    invalid_offset = _differential()
    invalid_offset["frame_offsets"] = [True]
    invalid_differentials.append((invalid_offset, "frame_offsets contains an invalid offset"))
    for differential, message in invalid_differentials:
        with pytest.raises(ValueError, match=message):
            calibration._validate_observation_differential(differential)

    rows = [
        {
            "approved_requested_values": [0] if step.raw_value == 0 else [],
            "raw_value": step.raw_value,
            "witness_role": step.witness_role,
            "display_value": "OFF" if step.raw_value == 0 else "ON",
        }
        for step in plan.steps
    ]
    rows.append(
        {
            "approved_requested_values": [],
            "raw_value": "bad",
            "witness_role": None,
            "display_value": "ignored",
        }
    )
    assert calibration._lookup_target_raw(family, rows)
    assert calibration.rush16_effective_requested_value({"requested": "value"}) == "value"


def test_distinct_display_candidate_requires_saved_kit_payload_change(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_bd_sharp_waveform",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "rytm.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=plan.steps[0],
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[],
        differential=_differential(changed=False),
    )
    repeat_zero = next(
        step for step in plan.steps if step.raw_value == 0 and step.witness_role == "repeat"
    )
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=repeat_zero,
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[],
        differential=_differential(changed=False),
    )

    with pytest.raises(ValueError, match="save the disposable active KIT"):
        accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=plan.steps[1],
            display_value="PLAIN_SINE_GLYPH",
            approved_requested_values=[],
            differential=_differential(changed=False),
        )

    assert next_rush16_calibration_step(plan, checkpoint) == plan.steps[1]
    assert checkpoint["promotions"] == []


def test_requested_value_cannot_approve_two_raw_candidates(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_bd_sharp_waveform",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "rytm.json",
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=plan.steps[0],
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[1],
        differential=_differential(),
    )
    repeat_zero = next_rush16_calibration_step(plan, checkpoint)
    assert repeat_zero is not None and repeat_zero.raw_value == 0
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=repeat_zero,
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[],
        differential=_differential(),
    )
    raw_one = next_rush16_calibration_step(plan, checkpoint)
    assert raw_one is not None and raw_one.raw_value == 1

    with pytest.raises(ValueError, match="already approved for a different raw"):
        accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=raw_one,
            display_value="PLAIN_SINE_GLYPH",
            approved_requested_values=[1],
            differential=_differential(),
        )


def test_affine_family_promotes_only_after_all_cross_track_probe_points(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_filter_1_frequency",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    while (step := next_rush16_calibration_step(plan, checkpoint)) is not None:
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value=step.raw_value,
            approved_requested_values=[],
            differential=_differential(),
        )
    promotions = checkpoint["promotions"]
    assert isinstance(promotions, list) and len(promotions) == 1
    assert promotions[0]["promotion_mode"] == "affine"
    assert {target["value_domain"] for target in promotions[0]["targets"]} == {"14bit"}


def test_a4_coarse_checkpoint_promotes_from_exact_saved_affine_evidence(
    tmp_path: Path,
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_oscillator_coarse_tune",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4_MKII_UNIT",
        disposable_target="RUSH16_A4_CALIBRATION_INIT",
    )
    displays = {63: -1, 64: 0, 65: 1, 75: 11, 76: 12, 77: 13}
    observations: list[dict[str, object]] = []
    for raw, display in displays.items():
        for witness in plan.families[0].witnesses:
            step = next(
                candidate
                for candidate in plan.steps
                if candidate.raw_value == raw and candidate.witness_role == witness.role
            )
            observations.append(
                {
                    "step_id": step.step_id,
                    "family_id": step.family_id,
                    "witness_role": step.witness_role,
                    "spec_filename": step.spec_filename,
                    "semantic_path": step.semantic_path,
                    "track": step.track,
                    "raw_value": raw,
                    "value_domain": step.value_domain,
                    "display_value": display,
                    "approved_requested_values": ([display] if display in {0, 12} else []),
                    "ordered_midi_bytes": [list(packet) for packet in step.ordered_messages],
                    "evidence_kind": "saved_kit_differential",
                    "evidence_reference_step_id": None,
                    "differential": _differential(),
                    "accepted_at_utc": "2026-08-01T00:00:00+00:00",
                }
            )
    checkpoint["observations"] = observations

    assert next_rush16_calibration_step(plan, checkpoint) is None
    progress = rush16_calibration_progress(plan, checkpoint)
    assert progress.families_complete == 1
    assert progress.observations_remaining == 0
    promotions = calibration._derive_promotions(plan, observations)
    assert len(promotions) == 1
    assert promotions[0]["promotion_mode"] == "affine"
    assert {target["raw_value"] for target in promotions[0]["targets"]} == {64, 76, 83}
    checkpoint_path = tmp_path / "a4.json"
    write_rush16_checkpoint(checkpoint_path, checkpoint)
    reloaded = load_or_create_rush16_checkpoint(
        checkpoint_path,
        plan,
        hardware_unit="A4_MKII_UNIT",
        disposable_target="RUSH16_A4_CALIBRATION_INIT",
    )
    assert reloaded["promotions"] == promotions


def test_a4_numeric_discovery_requires_three_points_then_one_saved_cross_track_raw(
    tmp_path: Path,
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_oscillator_coarse_tune",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    raw_63 = next_rush16_calibration_step(plan, checkpoint)
    assert raw_63 is not None and raw_63.raw_value == 63
    assert not rush16_calibration_step_requires_saved_kit(plan, checkpoint, raw_63)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=raw_63,
        display_value=-1,
        approved_requested_values=[],
        differential=None,
        observation_evidence_kind="display_discovery",
    )

    raw_64 = next_rush16_calibration_step(plan, checkpoint)
    assert raw_64 is not None and raw_64.raw_value == 64
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=raw_64,
        display_value=0,
        approved_requested_values=[0],
        differential=None,
        observation_evidence_kind="display_discovery",
    )
    raw_65 = next_rush16_calibration_step(plan, checkpoint)
    assert raw_65 is not None and raw_65.raw_value == 65
    assert not rush16_calibration_step_requires_saved_kit(plan, checkpoint, raw_65)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=raw_65,
        display_value=1,
        approved_requested_values=[],
        differential=None,
        observation_evidence_kind="display_discovery",
    )

    for role in ("representative_t1", "confirmation_t2"):
        certification = next_rush16_calibration_step(plan, checkpoint)
        assert certification is not None
        assert (certification.raw_value, certification.witness_role) == (63, role)
        assert rush16_calibration_step_requires_saved_kit(plan, checkpoint, certification)
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=certification,
            display_value=-1,
            approved_requested_values=[],
            differential=_differential(),
        )

    assert next_rush16_calibration_step(plan, checkpoint) is None
    assert len(checkpoint["promotions"]) == 1
    assert checkpoint["promotions"][0]["promotion_mode"] == "affine"


def test_a4_completed_pitch_family_routes_to_short_keytracking_work(
    tmp_path: Path,
) -> None:
    plan = build_rush16_calibration_plan("a4", _specs(), config=_config("a4"))
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    for raw, display, approvals in ((63, -1, []), (64, 0, [0]), (65, 1, [])):
        step = next_rush16_calibration_step(plan, checkpoint)
        assert step is not None and step.raw_value == raw
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value=display,
            approved_requested_values=approvals,
            differential=None,
            observation_evidence_kind="display_discovery",
        )
    for role in ("representative_t1", "confirmation_t2"):
        step = next_rush16_calibration_step(plan, checkpoint)
        assert step is not None
        assert (step.raw_value, step.witness_role) == (63, role)
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=step,
            display_value=-1,
            approved_requested_values=[],
            differential=_differential(),
        )

    next_step = next_rush16_calibration_step(plan, checkpoint)
    progress = rush16_calibration_progress(plan, checkpoint)
    assert next_step is not None and next_step.family_id == "a4_keytracking"
    assert progress.next_family_id == "a4_keytracking"
    assert 0 < progress.next_family_observations_remaining <= 4
    assert progress.deferred_large_selector_families > 0


def test_a4_large_selector_discovery_spreads_candidates_before_linear_fill(
    tmp_path: Path,
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_oscillator_waveform",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    first = next_rush16_calibration_step(plan, checkpoint)
    assert first is not None and first.raw_value == 0
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=first,
        display_value="UNKNOWN_0",
        approved_requested_values=[],
        differential=None,
        observation_evidence_kind="display_discovery",
    )

    second = next_rush16_calibration_step(plan, checkpoint)
    progress = rush16_calibration_progress(plan, checkpoint)
    assert second is not None and second.raw_value == 127
    assert progress.next_family_id == "a4_oscillator_waveform"
    assert progress.next_family_observations_remaining == 127
    assert progress.deferred_large_selector_families == 1


def test_a4_selector_stops_after_target_certification_and_neighbor_discovery(
    tmp_path: Path,
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_sub_oscillator",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "a4.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )

    discovery = next_rush16_calibration_step(plan, checkpoint)
    assert discovery is not None
    assert (discovery.raw_value, discovery.witness_role) == (0, "representative_t1")
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=discovery,
        display_value="off",
        approved_requested_values=["off"],
        differential=None,
        observation_evidence_kind="display_discovery",
    )

    for role in ("representative_t1", "confirmation_t2"):
        certification = next_rush16_calibration_step(plan, checkpoint)
        assert certification is not None
        assert (certification.raw_value, certification.witness_role) == (0, role)
        assert rush16_calibration_step_requires_saved_kit(plan, checkpoint, certification)
        checkpoint = accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=certification,
            display_value="off",
            approved_requested_values=["off"],
            differential=_differential(),
        )

    neighbor = next_rush16_calibration_step(plan, checkpoint)
    assert neighbor is not None
    assert (neighbor.raw_value, neighbor.witness_role) == (1, "representative_t1")
    assert not rush16_calibration_step_requires_saved_kit(plan, checkpoint, neighbor)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=neighbor,
        display_value="minus_one_octave",
        approved_requested_values=[],
        differential=None,
        observation_evidence_kind="display_discovery",
    )

    assert next_rush16_calibration_step(plan, checkpoint) is None
    assert len(checkpoint["observations"]) == 4
    assert len(checkpoint["promotions"]) == 1
    assert rush16_calibration_progress(plan, checkpoint).observations_remaining == 0


def test_adaptive_scheduler_skips_observed_neighbors_and_exhausted_families(
    tmp_path: Path,
) -> None:
    full_plan = build_rush16_calibration_plan("a4", _specs(), config=_config("a4"))
    selector_plan = _narrow_family(full_plan, "a4_sub_oscillator")
    family = selector_plan.families[0]
    by_location = {(step.raw_value, step.witness_role): step for step in selector_plan.steps}
    saved_rows = []
    for role in ("representative_t1", "confirmation_t2"):
        step = by_location[(1, role)]
        saved_rows.append(
            {
                "step_id": step.step_id,
                "family_id": family.family_id,
                "witness_role": role,
                "raw_value": 1,
                "display_value": "off",
                "approved_requested_values": ["off"],
                "differential": _differential(),
            }
        )
    observed_neighbor = by_location[(0, "representative_t1")]
    saved_rows.append(
        {
            "step_id": observed_neighbor.step_id,
            "family_id": family.family_id,
            "witness_role": observed_neighbor.witness_role,
            "raw_value": 0,
            "display_value": "neighbor-zero",
            "approved_requested_values": [],
            "differential": None,
        }
    )
    selector_checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "selector.json",
        selector_plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    selector_checkpoint["observations"] = saved_rows

    second_neighbor = next_rush16_calibration_step(selector_plan, selector_checkpoint)
    assert second_neighbor is not None
    assert (second_neighbor.raw_value, second_neighbor.witness_role) == (
        2,
        "representative_t1",
    )
    assert (
        rush16_calibration_progress(selector_plan, selector_checkpoint).observations_remaining > 0
    )

    first_family = full_plan.families[0]
    primary_role = first_family.witnesses[0].role
    exhausted_rows = [
        {
            "step_id": step.step_id,
            "family_id": first_family.family_id,
            "witness_role": step.witness_role,
            "raw_value": step.raw_value,
            "display_value": "unmapped",
            "approved_requested_values": [],
            "differential": None,
        }
        for step in full_plan.steps
        if step.family_id == first_family.family_id and step.witness_role == primary_role
    ]
    full_checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "full.json",
        full_plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    full_checkpoint["observations"] = exhausted_rows

    next_family_step = next_rush16_calibration_step(full_plan, full_checkpoint)
    assert next_family_step is not None
    assert next_family_step.family_id != first_family.family_id


def test_adaptive_affine_and_candidate_defensive_edges(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_filter_1_frequency",
    )
    family = plan.families[0]
    primary_role = family.witnesses[0].role
    confirmation_role = family.witnesses[1].role
    primary_rows = [
        {
            "step_id": step.step_id,
            "family_id": family.family_id,
            "witness_role": step.witness_role,
            "raw_value": step.raw_value,
            "display_value": step.raw_value,
            "approved_requested_values": [],
            "differential": None,
        }
        for step in plan.steps
        if step.witness_role == primary_role and step.raw_value in family.candidates[:3]
    ]
    first_raw = family.candidates[0]
    first_confirmation = next(
        step
        for step in plan.steps
        if step.witness_role == confirmation_role and step.raw_value == first_raw
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "affine.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    checkpoint["observations"] = primary_rows

    assert calibration._affine_confirmation_raw(family, primary_rows) == first_raw
    assert rush16_calibration_step_requires_saved_kit(plan, checkpoint, first_confirmation)
    assert rush16_calibration_progress(plan, checkpoint).observations_remaining > 0

    first_confirmation_row = {
        "step_id": first_confirmation.step_id,
        "family_id": family.family_id,
        "witness_role": confirmation_role,
        "raw_value": first_raw,
        "display_value": first_raw,
        "approved_requested_values": [],
        "differential": _differential(),
    }
    assert (
        calibration._affine_confirmation_raw(family, [*primary_rows, first_confirmation_row])
        == first_raw
    )
    first_primary_saved = dict(primary_rows[0], differential=_differential())
    assert (
        calibration._affine_confirmation_raw(
            family,
            [*primary_rows[1:], first_primary_saved, first_confirmation_row],
        )
        is None
    )
    all_confirmed = [
        *primary_rows,
        *(
            {
                "family_id": family.family_id,
                "witness_role": confirmation_role,
                "raw_value": row["raw_value"],
                "display_value": row["display_value"],
                "approved_requested_values": [],
                "differential": _differential(),
            }
            for row in primary_rows
        ),
    ]
    assert calibration._affine_confirmation_raw(family, all_confirmed) == first_raw

    conflicting = [*primary_rows, dict(primary_rows[0], display_value=999)]
    assert calibration._affine_fit(family, conflicting) is None
    assert (
        calibration._adaptive_target_raws(
            family,
            [{"raw_value": "bad", "approved_requested_values": []}],
        )
        == {}
    )
    assert calibration._neighboring_candidates(family, -1) == ()
    monkeypatch.setattr(calibration, "_affine_fit", lambda *_args: (1.0, 0.0))
    assert calibration._affine_confirmation_raw(family, []) is None


def test_observation_evidence_kind_must_match_payload(tmp_path: Path) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("a4", _specs(), config=_config("a4")),
        "a4_oscillator_coarse_tune",
    )
    checkpoint = load_or_create_rush16_checkpoint(
        tmp_path / "evidence.json",
        plan,
        hardware_unit="A4 Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    step = next_rush16_calibration_step(plan, checkpoint)
    assert step is not None

    for differential, kind, message in (
        (_differential(), "display_discovery", "cannot include saved-KIT evidence"),
        (None, "saved_kit_differential", "does not match its payload"),
        (_differential(), "display_repeat", "does not match its payload"),
    ):
        with pytest.raises(ValueError, match=message):
            accept_rush16_calibration_observation(
                plan,
                checkpoint,
                step=step,
                display_value=-1,
                approved_requested_values=[],
                differential=differential,
                observation_evidence_kind=kind,
            )


def test_kit_differential_reports_packed_unpacked_and_integrity_locations() -> None:
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)
    differential = analyze_rush16_kit_differential("rytm", baseline, changed)
    assert differential["baseline_round_trip_identical"] is True
    assert differential["changed_round_trip_identical"] is True
    assert differential["unpacked_offsets"]
    assert differential["packed_offsets"]
    assert differential["packed_frame_offsets"]
    assert differential["integrity_frame_offsets"]
    assert differential["header_offsets"] == []
    with pytest.raises(ValueError, match="equal lengths"):
        analyze_rush16_kit_differential("rytm", baseline, changed + b"\x00")


class _FakeOutput:
    def __init__(self) -> None:
        self.closed = False

    def send(self, _message: object) -> None:
        raise AssertionError("send_cc is replaced by a recorder")

    def close(self) -> None:
        self.closed = True


class _FakeCalibrationProvider:
    def __init__(self, frames: tuple[bytes, ...]) -> None:
        self.frames = list(frames)
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
        return (self.frames.pop(0),)


def _write_rytm_calibration_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "rytm": {
                    "output_port": "Exact Output",
                    "input_port": "Exact Input",
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )


def _write_a4_calibration_config(path: Path) -> None:
    path.write_text(
        yaml.safe_dump(
            {
                "a4": {
                    "output_port": "Exact Output",
                    "input_port": "Exact Input",
                    "tracks": dict(_config("a4").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )


def _continuous_calibration_arguments(config_path: Path, root: Path) -> list[str]:
    return [
        "--arm",
        "--rush16-calibrate",
        "--rush16-continuous",
        "--rush01-device",
        "rytm",
        "--rush01-config",
        str(config_path),
        "--rush01-disposable-target",
        "DISPOSABLE_INIT",
        "--rush16-hardware-unit",
        "Rytm Unit A",
        "--rush16-session-root",
        str(root),
        "--rush01-capture-timeout",
        "12",
        "--rush01-delay-ms",
        "0",
        "--confirm-rush16-calibration-send",
    ]


class _CaptureProvider:
    def __init__(self, frames: tuple[bytes, ...]) -> None:
        self.frames = frames

    def capture_sysex_messages(
        self, _port_name: str, *, timeout_seconds: float
    ) -> tuple[bytes, ...]:
        assert timeout_seconds == 12.0
        return self.frames


def test_armed_calibration_runs_one_fake_probe_and_checkpoints_after_acceptance(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    baseline = _synthetic_frame()
    provider = _FakeCalibrationProvider((baseline, _changed_frame(baseline)))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, control, value, *, channel, sleep: sent.append((channel, control, value)),
    )
    responses = iter(("", '"BD SHARP 0"', "1", ""))
    prompts: list[str] = []

    def read_operator_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(app, "_read_rush16_operator_input", read_operator_input)
    root = tmp_path / "local"
    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "Rytm Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-capture-timeout",
            "12",
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )
    output = capsys.readouterr().out
    assert result == 0
    assert sent == [(0, 15, 26), (0, 23, 0)]
    assert provider.opened_outputs == ["Exact Output"]
    assert provider.output.closed
    assert provider.captured_inputs == ["Exact Input", "Exact Input"]
    assert "provider not constructed" in output
    assert "operator sound-parameter entry: forbidden" in output
    assert "Baseline MIDI input is opening now" in output
    assert "Unique requested semantic values in this family: [1]" in output
    assert any("Approve only values" in prompt for prompt in prompts)
    assert any("Save the disposable active KIT" in prompt for prompt in prompts)
    assert "Changed MIDI input is opening now" in output
    assert "families complete=0" in output
    checkpoint = json.loads(
        (root / "session_checkpoints" / "rytm.checkpoint.json").read_text(encoding="utf-8")
    )
    assert len(checkpoint["observations"]) == 1
    assert checkpoint["observations"][0]["approved_requested_values"] == [1]
    assert not checkpoint["promotions"]
    assert len(list((root / "captured_dumps").glob("*.syx"))) == 2
    assert len(list((root / "hardware_receipts").glob("*.json"))) == 1
    assert (root / "calibration" / "RYTM_CALIBRATION_PLAN.json").is_file()
    matrix = json.loads(
        (root / "calibration" / "RYTM_BUILD_MATRIX.json").read_text(encoding="utf-8")
    )
    assert len(matrix["entries"]) == 4
    assert all(entry["hardware_apply_blocker_count"] > 0 for entry in matrix["entries"])
    assert not (root / "final_sysex").exists()


def test_a4_display_discovery_opens_output_only_and_skips_kit_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_a4_calibration_config(config_path)
    provider = _FakeCalibrationProvider(())
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, control, value, *, channel, sleep: sent.append((channel, control, value)),
    )
    prompts: list[str] = []
    responses = iter(("", "-1", "[]"))

    def read_operator_input(prompt: str) -> str:
        prompts.append(prompt)
        return next(responses)

    monkeypatch.setattr(app, "_read_rush16_operator_input", read_operator_input)
    root = tmp_path / "local"
    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush01-device",
            "a4",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "A4 Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    output = capsys.readouterr().out
    assert result == 0
    assert sent == [(0, 16, 63)]
    assert provider.opened_outputs == ["Exact Output"]
    assert provider.output.closed
    assert provider.captured_inputs == []
    assert "display discovery; no KIT save or SysEx capture" in output
    assert "no KIT was saved and no SysEx input was captured" in output
    assert not any("Save the disposable active KIT" in prompt for prompt in prompts)
    checkpoint = json.loads(
        (root / "session_checkpoints" / "a4.checkpoint.json").read_text(encoding="utf-8")
    )
    assert checkpoint["observations"][0]["evidence_kind"] == "display_discovery"
    assert checkpoint["observations"][0]["differential"] is None
    assert not (root / "captured_dumps").exists()


def test_a4_continuous_discovery_batches_quick_probes_then_pauses_before_save(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_a4_calibration_config(config_path)
    provider = _FakeCalibrationProvider(())
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, control, value, *, channel, sleep: sent.append((channel, control, value)),
    )
    responses = iter(("", "-1", "[]", "", "0", "0", "", "1", "[]"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))
    root = tmp_path / "continuous-discovery"

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush16-continuous",
            "--rush01-device",
            "a4",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "A4 Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    assert result == 0
    assert sent == [(0, 16, 63), (0, 16, 64), (0, 16, 65)]
    assert provider.captured_inputs == []
    assert provider.opened_outputs == ["Exact Output"] * 3
    checkpoint = json.loads(
        (root / "session_checkpoints" / "a4.checkpoint.json").read_text(encoding="utf-8")
    )
    assert len(checkpoint["observations"]) == 3
    assert {row["evidence_kind"] for row in checkpoint["observations"]} == {"display_discovery"}
    output = capsys.readouterr().out
    assert "continuous discovery paused before saved-KIT certification" in output
    assert "Baseline MIDI input is opening now" not in output


@pytest.mark.parametrize(
    ("response", "expected_result", "message"),
    (
        ("q", 0, "continuous discovery paused safely"),
        ("continue", 1, "discovery prompt accepts only Enter or Q"),
    ),
)
def test_a4_continuous_discovery_validates_ready_response_before_output(
    response: str,
    expected_result: int,
    message: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_a4_calibration_config(config_path)
    provider = _FakeCalibrationProvider(())
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("MIDI sent")),
    )
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: response)

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush16-continuous",
            "--rush01-device",
            "a4",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "A4 Unit A",
            "--rush16-session-root",
            str(tmp_path / "local"),
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    captured = capsys.readouterr()
    assert result == expected_result
    assert message in captured.out + captured.err
    assert provider.opened_outputs == []


def test_a4_continuous_discovery_pauses_before_another_quick_step(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_a4_calibration_config(config_path)
    provider = _FakeCalibrationProvider(())
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    saved_kit_requirements = iter((True, False))
    monkeypatch.setattr(
        calibration,
        "rush16_calibration_step_requires_saved_kit",
        lambda _plan, _checkpoint, _step: next(saved_kit_requirements),
    )
    monkeypatch.setattr(
        calibration,
        "validate_rush16_calibration_baseline_continuity",
        lambda _checkpoint, _baseline: None,
    )
    monkeypatch.setattr(
        calibration,
        "analyze_rush16_kit_differential",
        lambda _device, _baseline, _changed: _differential(),
    )
    monkeypatch.setattr(
        calibration,
        "accept_rush16_calibration_observation",
        lambda _plan, checkpoint, **_kwargs: checkpoint,
    )
    captures = iter((b"baseline", b"changed"))
    monkeypatch.setattr(
        app,
        "_capture_rush16_calibration_frame",
        lambda _provider, **_kwargs: next(captures),
    )
    monkeypatch.setattr(app, "_rush16_paired_repeat_step", lambda *_args: None)
    responses = iter(("", "-1", "[]", ""))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush16-continuous",
            "--rush01-device",
            "a4",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "A4 Unit A",
            "--rush16-session-root",
            str(tmp_path / "local"),
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    assert result == 0
    assert provider.captured_inputs == []
    assert "paused before the next quick display-discovery step" in capsys.readouterr().out


def test_armed_calibration_rejects_baseline_drift_before_output(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    plan = build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm"))
    root = tmp_path / "local"
    checkpoint_path = root / "session_checkpoints" / "rytm.checkpoint.json"
    checkpoint = load_or_create_rush16_checkpoint(
        checkpoint_path,
        plan,
        hardware_unit="Rytm Unit A",
        disposable_target="DISPOSABLE_INIT",
    )
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)
    checkpoint = accept_rush16_calibration_observation(
        plan,
        checkpoint,
        step=plan.steps[0],
        display_value="SINE_GLYPH_WITH_LEADING_BOX",
        approved_requested_values=[],
        differential=analyze_rush16_kit_differential("rytm", baseline, changed),
    )
    write_rush16_checkpoint(checkpoint_path, checkpoint)
    provider = _FakeCalibrationProvider((baseline,))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("CC sent")),
    )
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: "")

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "Rytm Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-capture-timeout",
            "12",
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    assert result == 1
    assert provider.captured_inputs == ["Exact Input"]
    assert provider.opened_outputs == []
    assert "no candidate MIDI was sent" in capsys.readouterr().err


def test_continuous_calibration_pairs_repeats_and_chains_saved_dumps(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    baseline = _synthetic_frame()
    raw_zero = _changed_frame_with_value(baseline, 37)
    raw_one = _changed_frame_with_value(raw_zero, 38)
    provider = _FakeCalibrationProvider((baseline, raw_zero, raw_one))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    sent: list[tuple[int, int, int]] = []
    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda _out, control, value, *, channel, sleep: sent.append((channel, control, value)),
    )
    responses = iter(
        (
            "",
            "WAVE0",
            "",
            "WAVE0",
            "[]",
            "",
            "",
            "WAVE1",
            "",
            "WAVE1",
            "1",
            "",
            "q",
        )
    )
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))
    root = tmp_path / "continuous"

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush16-continuous",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "Rytm Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-capture-timeout",
            "12",
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    assert result == 0
    assert provider.captured_inputs == ["Exact Input"] * 3
    assert provider.opened_outputs == ["Exact Output"] * 4
    assert sent == [
        (0, 15, 26),
        (0, 23, 0),
        (0, 15, 26),
        (0, 23, 0),
        (0, 15, 26),
        (0, 23, 1),
        (0, 15, 26),
        (0, 23, 1),
    ]
    checkpoint = json.loads(
        (root / "session_checkpoints" / "rytm.checkpoint.json").read_text(encoding="utf-8")
    )
    assert [row["evidence_kind"] for row in checkpoint["observations"]] == [
        "saved_kit_differential",
        "display_repeat",
        "saved_kit_differential",
        "display_repeat",
    ]
    assert (
        checkpoint["observations"][1]["evidence_reference_step_id"]
        == checkpoint["observations"][0]["step_id"]
    )
    assert checkpoint["observations"][1]["differential"] is None
    assert len(list((root / "captured_dumps").glob("*.syx"))) == 3
    assert len(list((root / "hardware_receipts").glob("*.json"))) == 4
    repeat_receipt = json.loads(
        (root / "hardware_receipts" / "0013_rytm_bd_sharp_waveform_repeat_0.json").read_text(
            encoding="utf-8"
        )
    )
    assert repeat_receipt["evidence_kind"] == "display_repeat"
    assert repeat_receipt["baseline_path"] is None
    assert repeat_receipt["changed_path"] is None
    output = capsys.readouterr().out
    assert "provider constructed; all ports currently closed" in output
    assert "paused after an accepted cycle" in output


def test_continuous_calibration_rejects_repeat_display_mismatch_before_save(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    provider = _FakeCalibrationProvider((_synthetic_frame(),))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    responses = iter(("", "WAVE0", "", "DIFFERENT"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))
    root = tmp_path / "mismatch"

    result = app.main(
        [
            "--arm",
            "--rush16-calibrate",
            "--rush16-continuous",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(config_path),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "Rytm Unit A",
            "--rush16-session-root",
            str(root),
            "--rush01-capture-timeout",
            "12",
            "--rush01-delay-ms",
            "0",
            "--confirm-rush16-calibration-send",
        ]
    )

    assert result == 1
    assert provider.captured_inputs == ["Exact Input"]
    assert not (root / "session_checkpoints" / "rytm.checkpoint.json").exists()
    assert not (root / "hardware_receipts").exists()
    assert "repeated display does not match" in capsys.readouterr().err


def test_continuous_calibration_helper_validation_edges() -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    primary = plan.steps[0]
    repeat = next(
        step
        for step in plan.steps
        if step.raw_value == primary.raw_value and step.witness_role == "repeat"
    )

    with pytest.raises(TypeError, match="requested values require"):
        app._rush16_unique_requested_values(object(), primary)
    with pytest.raises(TypeError, match="paired repeat requires"):
        app._rush16_paired_repeat_step(object(), {}, primary)

    duplicate_repeat = replace(
        repeat,
        step_id=f"{repeat.step_id}:duplicate",
        sequence=repeat.sequence + 1000,
    )
    ambiguous = replace(plan, steps=plan.steps + (duplicate_repeat,))
    with pytest.raises(ValueError, match="multiple same-location repeat witnesses"):
        app._rush16_paired_repeat_step(ambiguous, {"observations": []}, primary)


def test_continuous_calibration_accepts_cross_track_family_without_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_rytm_calibration_config(config_path)
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_xt_classic_machine",
    )
    monkeypatch.setattr(calibration, "build_rush16_calibration_plan", lambda *_args, **_kw: plan)
    baseline = _synthetic_frame()
    provider = _FakeCalibrationProvider((baseline, _changed_frame(baseline)))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    responses = iter(("", "XT Classic", '"XT Classic"', "", "q"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(_continuous_calibration_arguments(config_path, tmp_path / "cross-track"))

    assert result == 0
    assert provider.opened_outputs == ["Exact Output"]
    assert provider.captured_inputs == ["Exact Input", "Exact Input"]
    assert "paused after an accepted cycle" in capsys.readouterr().out


def test_continuous_calibration_rejects_invalid_paired_step_type(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_rytm_calibration_config(config_path)
    provider = _FakeCalibrationProvider((_synthetic_frame(),))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(app, "_rush16_paired_repeat_step", lambda *_args: object())
    responses = iter(("", "WAVE0"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(_continuous_calibration_arguments(config_path, tmp_path / "bad-type"))

    assert result == 1
    assert "paired repeat is not a calibration step" in capsys.readouterr().err


def test_continuous_calibration_rejects_checkpoint_order_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_rytm_calibration_config(config_path)
    baseline = _synthetic_frame()
    provider = _FakeCalibrationProvider((baseline, _changed_frame(baseline)))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    real_next = calibration.next_rush16_calibration_step
    calls = 0

    def mismatched_next(plan, checkpoint):
        nonlocal calls
        calls += 1
        if calls == 3:
            return plan.steps[1]
        return real_next(plan, checkpoint)

    monkeypatch.setattr(calibration, "next_rush16_calibration_step", mismatched_next)
    responses = iter(("", "WAVE0", "", "WAVE0", "[]", ""))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(
        _continuous_calibration_arguments(config_path, tmp_path / "bad-checkpoint-order")
    )

    assert result == 1
    assert "paired repeat is not the next checkpoint step" in capsys.readouterr().err


def test_continuous_calibration_reports_completion_after_final_pair(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_rytm_calibration_config(config_path)
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    monkeypatch.setattr(calibration, "build_rush16_calibration_plan", lambda *_args, **_kw: plan)
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)
    provider = _FakeCalibrationProvider((baseline, baseline, changed))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    responses = iter(("", "OFF", "", "OFF", "0", "", "", "ON", "", "ON", "[]", ""))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(_continuous_calibration_arguments(config_path, tmp_path / "complete"))

    assert result == 0
    assert provider.opened_outputs == ["Exact Output"] * 4
    assert provider.captured_inputs == ["Exact Input"] * 3
    assert "supported calibration observations are complete" in capsys.readouterr().out


def test_continuous_calibration_rejects_nonempty_continue_response(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = tmp_path / "config.yaml"
    _write_rytm_calibration_config(config_path)
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    monkeypatch.setattr(calibration, "build_rush16_calibration_plan", lambda *_args, **_kw: plan)
    baseline = _synthetic_frame()
    provider = _FakeCalibrationProvider((baseline, baseline))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    responses = iter(("", "OFF", "", "OFF", "0", "", "continue"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))

    result = app.main(_continuous_calibration_arguments(config_path, tmp_path / "bad-continue"))

    assert result == 1
    assert "continuous prompt accepts only Enter or Q" in capsys.readouterr().err


def test_calibration_validation_fails_before_provider_construction(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    result = app.main(
        [
            "--rush16-calibrate",
            "--rush01-device",
            "rytm",
            "--rush01-config",
            str(tmp_path / "missing.yaml"),
            "--rush01-disposable-target",
            "DISPOSABLE_INIT",
            "--rush16-hardware-unit",
            "Rytm Unit A",
            "--confirm-rush16-calibration-send",
        ]
    )
    assert result == 1
    assert "require --arm" in capsys.readouterr().err


def test_message_transport_rejects_non_cc_and_closes_after_send_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = _FakeCalibrationProvider((_synthetic_frame(), _synthetic_frame()))
    with pytest.raises(ValueError, match="control-change"):
        rush01_midi_transport.apply_rush01_messages(
            ((0xC0, 1, 2),),
            provider,
            port_name="Exact Output",
            delay_ms=0,
            sleep=lambda _seconds: None,
        )
    assert not provider.opened_outputs

    monkeypatch.setattr(
        rush01_midi_transport,
        "send_cc",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("send failed")),
    )
    with pytest.raises(RuntimeError, match="send failed"):
        rush01_midi_transport.apply_rush01_messages(
            ((0xB0, 21, 0),),
            provider,
            port_name="Exact Output",
            delay_ms=0,
            sleep=lambda _seconds: None,
        )
    assert provider.output.closed


@pytest.mark.parametrize("delay", [True, "1", -1, 10_001])
def test_message_transport_rejects_invalid_delay_values(delay: object) -> None:
    with pytest.raises(ValueError, match="delay_ms"):
        rush01_midi_transport.validate_rush01_messages(((0xB0, 1, 2),), delay_ms=delay)


@pytest.mark.parametrize(
    ("messages", "message"),
    [
        ((), "must not be empty"),
        (((0xB0, 1),), "exactly three"),
        (((0xB0, -1, 2),), "channel-mode"),
        (((0xB0, 120, 2),), "channel-mode"),
        (((0xB0, 1, -1),), "data bytes"),
        (((0xB0, 1, 128),), "data bytes"),
    ],
)
def test_message_transport_rejects_malformed_cc_packets(
    messages: tuple[tuple[int, ...], ...],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        rush01_midi_transport.validate_rush01_messages(messages, delay_ms=0)


def test_plan_and_catalog_validation_rejects_incomplete_or_unmapped_inputs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specs = _specs()
    with pytest.raises(ValueError, match="device must"):
        build_rush16_calibration_plan("other", specs, config=_config("rytm"))
    with pytest.raises(ValueError, match="config device"):
        build_rush16_calibration_plan("rytm", specs, config=_config("a4"))
    no_input = replace(_config("rytm"), input_port=None)
    with pytest.raises(ValueError, match="input_port"):
        build_rush16_calibration_plan("rytm", specs, config=no_input)
    incomplete = {
        name: spec for name, spec in specs.items() if name != "01_DRY_AUTHORITY_RYTM.yaml"
    }
    with pytest.raises(ValueError, match="four rytm"):
        build_rush16_calibration_plan("rytm", incomplete, config=_config("rytm"))
    with pytest.raises(ValueError, match="device must"):
        calibration.build_rush16_calibration_catalog("other", specs)
    with pytest.raises(ValueError, match="four a4"):
        calibration.build_rush16_calibration_catalog(
            "a4", {"one.yaml": specs["01_DRY_AUTHORITY_A4.yaml"]}
        )

    original = calibration._FAMILY_TEMPLATES
    monkeypatch.setattr(
        calibration,
        "_FAMILY_TEMPLATES",
        tuple(template for template in original if template.family_id != "rytm_ch_osc_reset"),
    )
    with pytest.raises(ValueError, match="no family"):
        build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))
    with pytest.raises(ValueError, match="no family"):
        calibration.build_rush16_calibration_catalog("rytm", specs)

    missing_witness = replace(
        original[0],
        witnesses=(replace(original[0].witnesses[0], spec_filename="missing.yaml"),),
    )
    monkeypatch.setattr(calibration, "_FAMILY_TEMPLATES", (missing_witness,) + original[1:])
    with pytest.raises(ValueError, match="missing RUSH16 witness spec"):
        build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))


def test_checkpoint_and_observation_validation_edges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan = _narrow_family(
        build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    path = tmp_path / "checkpoint.json"
    with pytest.raises(ValueError, match="hardware unit"):
        load_or_create_rush16_checkpoint(
            path, plan, hardware_unit="", disposable_target="DISPOSABLE_INIT"
        )
    with pytest.raises(ValueError, match="disposable target"):
        load_or_create_rush16_checkpoint(path, plan, hardware_unit="Unit", disposable_target="")
    checkpoint = load_or_create_rush16_checkpoint(
        path,
        plan,
        hardware_unit="Unit",
        disposable_target="DISPOSABLE_INIT",
    )
    with pytest.raises(ValueError, match="not the next"):
        accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=plan.steps[1],
            display_value="ON",
            approved_requested_values=[],
            differential={},
        )
    with pytest.raises(ValueError, match="not requested"):
        accept_rush16_calibration_observation(
            plan,
            checkpoint,
            step=plan.steps[0],
            display_value="OFF",
            approved_requested_values=[99],
            differential={},
        )
    with pytest.raises(ValueError, match="unknown.*family"):
        calibration._family_by_id(plan, "missing")

    def fail_replace(_path: Path, _target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        write_rush16_checkpoint(path, checkpoint)
    assert not path.with_suffix(".json.tmp").exists()


def test_promotion_overlay_rejects_stale_invalid_and_unconfigured_targets(
    tmp_path: Path,
) -> None:
    specs = _specs()
    narrowed = _narrow_family(
        build_rush16_calibration_plan("rytm", specs, config=_config("rytm")),
        "rytm_ch_osc_reset",
    )
    checkpoint = _complete_lookup_checkpoint(
        narrowed,
        tmp_path / "ch.json",
        displayed_by_raw={0: "OFF", 127: "ON"},
        approved_by_raw={0: [0]},
    )
    filename = "01_DRY_AUTHORITY_RYTM.yaml"
    source = compile_rush01_midi_plan("rytm", specs[filename], config=_config("rytm"))

    invalid = deepcopy(checkpoint)
    invalid["version"] = "wrong"
    with pytest.raises(ValueError, match="version"):
        apply_rush16_calibration_promotions(source, spec_filename=filename, checkpoint=invalid)
    invalid = deepcopy(checkpoint)
    invalid["device"] = "a4"
    with pytest.raises(ValueError, match="device"):
        apply_rush16_calibration_promotions(source, spec_filename=filename, checkpoint=invalid)

    legacy = deepcopy(checkpoint)
    legacy["version"] = "rush16-apply-calibration-v2"
    for promotion in legacy["promotions"]:
        for legacy_target in promotion["targets"]:
            legacy_target.pop("address")
    legacy_promoted = apply_rush16_calibration_promotions(
        source,
        spec_filename=filename,
        checkpoint=legacy,
    )
    legacy_field = next(
        field
        for field in legacy_promoted.fields
        if field.semantic_path == "tracks.CH.synth.Osc Reset"
    )
    assert legacy_field.ordered_midi_bytes == ((0xB8, 21, 0),)

    legacy_with_address = deepcopy(legacy)
    legacy_with_address["promotions"][0]["targets"][0]["address"] = {}
    with pytest.raises(ValueError, match="legacy.*must not supply"):
        apply_rush16_calibration_promotions(
            source,
            spec_filename=filename,
            checkpoint=legacy_with_address,
        )

    legacy_without_route = deepcopy(legacy)
    route_path = legacy_without_route["promotions"][0]["targets"][0]["semantic_path"]
    source_without_route = replace(
        source,
        fields=tuple(
            (
                replace(field, message_type=None, controller=None, nrpn_address=None)
                if field.semantic_path == route_path
                else field
            )
            for field in source.fields
        ),
    )
    with pytest.raises(ValueError, match="no unique documented address"):
        apply_rush16_calibration_promotions(
            source_without_route,
            spec_filename=filename,
            checkpoint=legacy_without_route,
        )

    target = checkpoint["promotions"][0]["targets"][0]
    for key, value, message in (
        ("requested_fingerprint", "stale", "stale"),
        ("raw_value", True, "raw value"),
        ("value_domain", "wrong", "domain"),
    ):
        invalid = deepcopy(checkpoint)
        invalid["promotions"][0]["targets"][0][key] = value
        with pytest.raises(ValueError, match=message):
            apply_rush16_calibration_promotions(source, spec_filename=filename, checkpoint=invalid)
    assert target["raw_value"] == 0

    inconsistent_address = deepcopy(checkpoint)
    inconsistent_address["promotions"][0]["targets"][0]["address"]["value_domain"] = "14bit"
    with pytest.raises(ValueError, match="address value domain is inconsistent"):
        apply_rush16_calibration_promotions(
            source,
            spec_filename=filename,
            checkpoint=inconsistent_address,
        )

    unconfigured = compile_rush01_midi_plan("rytm", specs[filename])
    with pytest.raises(ValueError, match="no configured channel"):
        apply_rush16_calibration_promotions(
            unconfigured,
            spec_filename=filename,
            checkpoint=checkpoint,
        )


def test_machine_cc14_and_nrpn_promotions_encode_their_documented_addresses(
    tmp_path: Path,
) -> None:
    specs = _specs()
    rytm_plan = _narrow_family(
        build_rush16_calibration_plan("rytm", specs, config=_config("rytm")),
        "rytm_xt_classic_machine",
    )
    machine_checkpoint = _complete_lookup_checkpoint(
        rytm_plan,
        tmp_path / "machine.json",
        displayed_by_raw={8: "XT Classic"},
        approved_by_raw={8: ["XT Classic"]},
    )
    filename = "01_DRY_AUTHORITY_RYTM.yaml"
    promoted_rytm = apply_rush16_calibration_promotions(
        compile_rush01_midi_plan("rytm", specs[filename], config=_config("rytm")),
        spec_filename=filename,
        checkpoint=machine_checkpoint,
    )
    lt = next(field for field in promoted_rytm.fields if field.semantic_path == "tracks.LT.machine")
    assert lt.ordered_midi_bytes == ((0xB5, 15, 8),)

    a4_filename = "01_DRY_AUTHORITY_A4.yaml"
    a4_source = compile_rush01_midi_plan("a4", specs[a4_filename], config=_config("a4"))

    def checkpoint_for(path: str, raw: int, domain: str) -> dict[str, object]:
        field = next(field for field in a4_source.fields if field.semantic_path == path)
        return {
            "version": RUSH16_CALIBRATION_VERSION,
            "device": "a4",
            "plan_sha256": "evidence",
            "promotions": [
                {
                    "family_id": "test_family",
                    "evidence_sha256": "evidence",
                    "targets": [
                        {
                            "spec_filename": a4_filename,
                            "semantic_path": path,
                            "requested_fingerprint": calibration._fingerprint(
                                field.requested_value
                            ),
                            "raw_value": raw,
                            "value_domain": domain,
                            "address": {
                                "message_type": field.message_type,
                                "value_domain": domain,
                                "controller": field.controller,
                                "controller_lsb": field.controller_lsb,
                                "nrpn_address": (
                                    list(field.nrpn_address)
                                    if field.nrpn_address is not None
                                    else None
                                ),
                            },
                        }
                    ],
                }
            ],
        }

    cc14_checkpoint = checkpoint_for("tracks.T1.filter_1.frequency", 12345, "14bit")
    cc14 = apply_rush16_calibration_promotions(
        a4_source,
        spec_filename=a4_filename,
        checkpoint=cc14_checkpoint,
    )
    field = next(
        field for field in cc14.fields if field.semantic_path == "tracks.T1.filter_1.frequency"
    )
    assert field.ordered_midi_bytes == ((0xB0, 18, 96), (0xB0, 50, 57))

    legacy_cc14 = deepcopy(cc14_checkpoint)
    legacy_cc14["version"] = "rush16-apply-calibration-v2"
    legacy_cc14["promotions"][0]["targets"][0].pop("address")
    legacy_field = next(
        field
        for field in apply_rush16_calibration_promotions(
            a4_source,
            spec_filename=a4_filename,
            checkpoint=legacy_cc14,
        ).fields
        if field.semantic_path == "tracks.T1.filter_1.frequency"
    )
    assert legacy_field.ordered_midi_bytes == ((0xB0, 18, 96), (0xB0, 50, 57))

    nrpn_checkpoint = checkpoint_for("tracks.T1.oscillator_common.osc1_am", 127, "7bit")
    nrpn = apply_rush16_calibration_promotions(
        a4_source,
        spec_filename=a4_filename,
        checkpoint=nrpn_checkpoint,
    )
    field = next(
        field
        for field in nrpn.fields
        if field.semantic_path == "tracks.T1.oscillator_common.osc1_am"
    )
    assert field.ordered_midi_bytes == ((0xB0, 99, 1), (0xB0, 98, 30), (0xB0, 6, 127))

    legacy_nrpn = deepcopy(nrpn_checkpoint)
    legacy_nrpn["version"] = "rush16-apply-calibration-v2"
    legacy_nrpn["promotions"][0]["targets"][0].pop("address")
    legacy_field = next(
        field
        for field in apply_rush16_calibration_promotions(
            a4_source,
            spec_filename=a4_filename,
            checkpoint=legacy_nrpn,
        ).fields
        if field.semantic_path == "tracks.T1.oscillator_common.osc1_am"
    )
    assert legacy_field.ordered_midi_bytes == (
        (0xB0, 99, 1),
        (0xB0, 98, 30),
        (0xB0, 6, 127),
    )


def test_converter_derivation_and_address_validation_edges() -> None:
    specs = _specs()
    plan = build_rush16_calibration_plan("a4", specs, config=_config("a4"))
    family = next(family for family in plan.families if family.family_id == "a4_filter_1_frequency")

    def rows(display) -> list[dict[str, object]]:
        return [
            {
                "family_id": family.family_id,
                "witness_role": step.witness_role,
                "raw_value": step.raw_value,
                "display_value": display(step),
                "approved_requested_values": [],
            }
            for step in plan.steps
            if step.family_id == family.family_id
        ]

    assert calibration._affine_target_raw(family, []) == {}
    assert calibration._affine_target_raw(family, rows(lambda _step: "not numeric")) == {}
    inconsistent = rows(
        lambda step: step.raw_value + (1 if step.witness_role.endswith("t2") else 0)
    )
    assert calibration._affine_target_raw(family, inconsistent) == {}
    assert calibration._affine_target_raw(family, rows(lambda _step: 1)) == {}
    nonlinear = rows(lambda step: step.raw_value * step.raw_value)
    assert calibration._affine_target_raw(family, nonlinear) == {}

    two_point = replace(family, candidates=(0, 1))
    two_rows = [row for row in rows(lambda step: step.raw_value) if row["raw_value"] in {0, 1}]
    assert calibration._affine_target_raw(two_point, two_rows) == {}
    nonnumeric_target = replace(
        family,
        targets=(Rush16CalibrationTarget("x.yaml", "x", "text", "fingerprint"),),
    )
    assert (
        calibration._affine_target_raw(nonnumeric_target, rows(lambda step: step.raw_value)) == {}
    )
    out_of_range = replace(
        family,
        targets=(Rush16CalibrationTarget("x.yaml", "x", 20000, "fingerprint"),),
    )
    assert calibration._affine_target_raw(out_of_range, rows(lambda step: step.raw_value)) == {}
    mixed_targets = replace(
        family,
        targets=(
            Rush16CalibrationTarget("x.yaml", "text", "text", "text"),
            Rush16CalibrationTarget("x.yaml", "outside", 20000, "outside"),
            family.targets[0],
        ),
    )
    saved_rows = [
        dict(row, differential=_differential()) for row in rows(lambda step: step.raw_value)
    ]
    assert calibration._predict_affine_target_raws(mixed_targets, saved_rows)

    confirmation_rows = [
        row
        for row in rows(lambda step: step.raw_value)
        if row["witness_role"] == family.witnesses[1].role
    ]
    assert calibration._affine_confirmation_raw(family, confirmation_rows) is None
    assert (
        calibration._a4_family_remaining_step_count(
            plan, replace(family, witnesses=()), confirmation_rows
        )
        == 0
    )

    boolean = next(family for family in plan.families if family.family_id == "a4_keytracking")
    assert calibration._lookup_target_raw(boolean, []) == {}
    malformed_lookup = [
        {
            "approved_requested_values": [True],
            "raw_value": "127",
            "witness_role": "representative_t1",
            "display_value": "ON",
        }
    ]
    assert calibration._lookup_target_raw(boolean, malformed_lookup) == {}
    selector = next(
        family
        for family in build_rush16_calibration_plan("rytm", specs, config=_config("rytm")).families
        if family.family_id == "rytm_ch_osc_reset"
    )
    assert (
        calibration._lookup_target_raw(
            selector,
            [
                {
                    "approved_requested_values": [0],
                    "raw_value": "0",
                    "witness_role": "primary",
                    "display_value": "OFF",
                }
            ],
        )
        == {}
    )
    machine = next(
        family
        for family in build_rush16_calibration_plan("rytm", specs, config=_config("rytm")).families
        if family.family_id == "rytm_xt_classic_machine"
    )
    assert calibration._selector_neighbors_observed(machine, [], 8, set())
    assert calibration._derive_promotions(plan, []) == []

    with pytest.raises(ValueError, match="CC calibration"):
        calibration._encode_address(Rush16CalibrationAddress("CC", "7bit"), 0, 0)
    with pytest.raises(ValueError, match="CC14 calibration"):
        calibration._encode_address(Rush16CalibrationAddress("CC14", "14bit", controller=1), 0, 0)
    with pytest.raises(ValueError, match="NRPN calibration"):
        calibration._encode_address(Rush16CalibrationAddress("NRPN", "7bit"), 0, 0)


def test_target_and_promotion_address_validation_edges() -> None:
    plan = build_rush16_calibration_plan("a4", _specs(), config=_config("a4"))
    family = next(
        family for family in plan.families if family.family_id == "a4_oscillator_coarse_tune"
    )
    with pytest.raises(ValueError, match="no unique calibrated address"):
        calibration._address_for_target(family, "tracks.T1.unmapped.parameter")

    shared_address = family.witnesses[0].address
    unique_fallback = replace(
        family,
        witnesses=tuple(replace(witness, address=shared_address) for witness in family.witnesses),
    )
    assert (
        calibration._address_for_target(unique_fallback, "tracks.T9.unmapped.parameter")
        == shared_address
    )
    with pytest.raises(ValueError, match="no track prefix"):
        calibration._track_relative_semantic_path("global.parameter")

    valid = {
        "message_type": "CC",
        "value_domain": "7bit",
        "controller": 1,
        "controller_lsb": None,
        "nrpn_address": None,
    }
    invalid_payloads = (
        ({**valid, "message_type": "invalid"}, "message type"),
        ({**valid, "value_domain": "invalid"}, "value domain"),
        ({**valid, "controller": True}, "controller is invalid"),
        ({**valid, "controller_lsb": True}, "LSB controller"),
        ({**valid, "nrpn_address": [1]}, "NRPN is invalid"),
    )
    for payload, message in invalid_payloads:
        with pytest.raises(ValueError, match=message):
            calibration._address_from_dict(payload)


def test_machine_context_and_internal_shape_validation_edges() -> None:
    specs = _specs()
    plan = build_rush16_calibration_plan("rytm", specs, config=_config("rytm"))
    witness = plan.families[0].witnesses[0]
    assert (
        calibration._machine_context_messages(
            "a4", specs[witness.spec_filename], witness, 0, witness.role
        )
        == ()
    )
    assert (
        calibration._machine_context_messages(
            "rytm", specs[witness.spec_filename], witness, 0, "rytm_xt_classic_machine"
        )
        == ()
    )
    malformed = deepcopy(specs[witness.spec_filename])
    malformed["tracks"][witness.track]["machine"] = "bad"
    with pytest.raises(ValueError, match="no machine context"):
        calibration._machine_context_messages("rytm", malformed, witness, 0, "other")
    malformed = deepcopy(specs[witness.spec_filename])
    malformed["tracks"][witness.track]["machine"]["name"] = "Unknown Machine"
    with pytest.raises(ValueError, match="absent from catalog"):
        calibration._machine_context_messages("rytm", malformed, witness, 0, "other")
    with pytest.raises(ValueError, match="no channel"):
        calibration._midi_channel(replace(_config("rytm"), track_channels={}), "BD")
    with pytest.raises(ValueError, match="spec device"):
        calibration._spec_device({"rush16": {"device": "other"}})
    with pytest.raises(ValueError, match="must be a mapping"):
        calibration._mapping([], "value")
    with pytest.raises(ValueError, match="must be a sequence"):
        calibration._require_object_sequence("bad", "value")
    with pytest.raises(ValueError, match="equal lengths"):
        calibration._changed_offsets(b"a", b"ab")
    assert calibration._target_requested_value("tracks.LT.machine", {"name": 8}) == {"name": 8}


def test_differential_rejects_codec_round_trip_instability(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    baseline = _synthetic_frame()
    changed = _changed_frame(baseline)
    actual = ANALOG_RYTM_KIT_CODEC

    class UnstableCodec:
        spec = actual.spec

        @staticmethod
        def decode_frame(frame: bytes):
            return actual.decode_frame(frame)

        @staticmethod
        def encode_frame(decoded):
            return b"unstable"

    monkeypatch.setattr(calibration, "ANALOG_RYTM_KIT_CODEC", UnstableCodec())
    with pytest.raises(ValueError, match="baseline KIT"):
        analyze_rush16_kit_differential("rytm", baseline, changed)

    class ChangedUnstableCodec:
        spec = actual.spec

        @staticmethod
        def decode_frame(frame: bytes):
            return actual.decode_frame(frame)

        @staticmethod
        def encode_frame(decoded):
            if decoded.original_frame == changed:
                return b"unstable"
            return actual.encode_frame(decoded)

    monkeypatch.setattr(calibration, "ANALOG_RYTM_KIT_CODEC", ChangedUnstableCodec())
    with pytest.raises(ValueError, match="changed KIT"):
        analyze_rush16_kit_differential("rytm", baseline, changed)


@pytest.mark.parametrize(
    ("removed", "extra", "message"),
    [
        (("--rush01-config", "missing.yaml"), (), "requires --rush01-config"),
        (("--rush01-disposable-target", "DISPOSABLE"), (), "disposable-target"),
        (("--rush16-hardware-unit", "Unit"), (), "hardware-unit"),
        (("--confirm-rush16-calibration-send",), (), "confirm-rush16"),
        ((), ("--rush01-capture-timeout", "0"), "capture-timeout"),
        ((), ("--rush01-delay-ms", "10001"), "delay-ms"),
        ((), ("--rush01-spec", "other.yaml"), "cannot be combined"),
    ],
)
def test_calibration_argument_validation_fails_before_provider(
    removed: tuple[str, ...],
    extra: tuple[str, ...],
    message: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    arguments = [
        "--arm",
        "--rush16-calibrate",
        "--rush01-device",
        "rytm",
        "--rush01-config",
        "missing.yaml",
        "--rush01-disposable-target",
        "DISPOSABLE",
        "--rush16-hardware-unit",
        "Unit",
        "--rush01-capture-timeout",
        "12",
        "--rush01-delay-ms",
        "0",
        "--confirm-rush16-calibration-send",
    ]
    for value in removed:
        arguments.remove(value)
    arguments.extend(extra)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert app.main(arguments) == 1
    assert message in capsys.readouterr().err


def test_continuous_calibration_requires_calibration_operation_before_provider(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )

    assert app.main(["--rush16-continuous"]) == 1
    assert "--rush16-continuous requires --rush16-calibrate" in capsys.readouterr().err


def test_apply_checkpoint_argument_conflicts_fail_before_provider(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    checkpoint = tmp_path / "checkpoint.json"
    checkpoint.write_text("[]\n", encoding="utf-8")
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    common = [
        "--arm",
        "--rush01-apply-plan",
        "--rush01-device",
        "rytm",
        "--rush01-config",
        str(config_path),
        "--confirm-rush01-midi-send",
        "--rush16-checkpoint",
        str(checkpoint),
    ]
    assert app.main(common) == 1
    assert "requires --rush01-spec" in capsys.readouterr().err

    non_rush16 = PROJECT_ROOT / "specs" / "RUSH01_RYTM.yaml"
    assert (
        app.main(
            common
            + [
                "--rush01-spec",
                str(non_rush16),
                "--rush01-disposable-target",
                "DISPOSABLE",
            ]
        )
        == 1
    )
    assert "requires a RUSH16" in capsys.readouterr().err

    rush16_spec = SPEC_ROOT / "01_DRY_AUTHORITY_RYTM.yaml"
    assert (
        app.main(
            common
            + [
                "--rush01-spec",
                str(rush16_spec),
                "--rush01-disposable-target",
                "DISPOSABLE",
            ]
        )
        == 1
    )
    assert "JSON object" in capsys.readouterr().err

    assert (
        app.main(
            common
            + [
                "--rush01-spec",
                str(rush16_spec),
                "--rush01-disposable-target",
                "DISPOSABLE",
                "--rush16-hardware-unit",
                "Unit",
            ]
        )
        == 1
    )
    assert "calibration arguments require --rush16-calibrate" in capsys.readouterr().err

    checkpoint.write_text(
        json.dumps(
            {
                "version": RUSH16_CALIBRATION_VERSION,
                "device": "rytm",
                "promotions": [],
            }
        ),
        encoding="utf-8",
    )
    assert (
        app.main(
            common
            + [
                "--rush01-spec",
                str(rush16_spec),
                "--rush01-disposable-target",
                "DISPOSABLE",
            ]
        )
        == 1
    )
    assert "automated calibration is required" in capsys.readouterr().err


def test_rush16_app_helpers_fail_closed_and_cover_a4_capture(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert app._parse_rush16_display_value("SINE_GLYPH_WITH_LEADING_BOX") == (
        "SINE_GLYPH_WITH_LEADING_BOX"
    )
    assert app._parse_rush16_display_value('"SAW"') == "SAW"
    assert app._parse_rush16_display_value("1") == 1
    with pytest.raises(ValueError, match="displayed value is required"):
        app._parse_rush16_display_value("  ")

    plan = build_rush16_calibration_plan("rytm", _specs(), config=_config("rytm"))
    typed_step = next(step for step in plan.steps if step.family_id == "rytm_sy_raw_waveform_1")
    assert app._rush16_unique_requested_values(plan, typed_step) == ["sawtooth"]
    with monkeypatch.context() as prompt_patch:
        prompt_patch.setattr(app, "_read_rush16_operator_input", lambda _prompt: "sawtooth")
        assert app._read_rush16_semantic_approvals(["sawtooth"]) == ["sawtooth"]
        prompt_patch.setattr(app, "_read_rush16_operator_input", lambda _prompt: "triangle")
        with pytest.raises(ValueError, match="must be a requested value"):
            app._read_rush16_semantic_approvals(["sawtooth"])

    destination = tmp_path / "local.json"

    def fail_replace(_path: Path, _target: Path) -> Path:
        raise OSError("replace failed")

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="replace failed"):
        app._write_rush16_local_bytes(destination, b"data")
    assert not destination.with_suffix(".json.tmp").exists()
    monkeypatch.undo()

    with pytest.raises(ValueError, match="exactly one"):
        app._capture_rush16_calibration_frame(
            _CaptureProvider(()),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
        )
    a4_frame = _synthetic_frame(ANALOG_FOUR_KIT_CODEC)
    assert (
        app._capture_rush16_calibration_frame(
            _CaptureProvider((a4_frame,)),
            device="a4",
            input_port="Exact Input",
            timeout_seconds=12.0,
        )
        == a4_frame
    )

    class UnstableCodec:
        @staticmethod
        def decode_frame(frame: bytes) -> bytes:
            return frame

        @staticmethod
        def encode_frame(_decoded: bytes) -> bytes:
            return b"different"

    monkeypatch.setattr(device_strategies, "ANALOG_RYTM_KIT_CODEC", UnstableCodec())
    with pytest.raises(ValueError, match="decode/encode stable"):
        app._capture_rush16_calibration_frame(
            _CaptureProvider((_synthetic_frame(),)),
            device="rytm",
            input_port="Exact Input",
            timeout_seconds=12.0,
        )
    with pytest.raises(TypeError, match="requires a plan and step"):
        app._write_rush16_calibration_preview(
            object(),
            object(),
            checkpoint_path=tmp_path / "x.json",
            disposable_target="DISPOSABLE",
        )


def test_promoted_matrix_rejects_invalid_config_and_spec(tmp_path: Path) -> None:
    checkpoint = {
        "version": RUSH16_CALIBRATION_VERSION,
        "device": "rytm",
        "promotions": [],
    }
    with pytest.raises(TypeError, match="device config"):
        app._write_rush16_promoted_build_matrix(
            tmp_path,
            device="rytm",
            specs={},
            config=object(),
            checkpoint=checkpoint,
        )
    with pytest.raises(ValueError, match="must be a mapping"):
        app._write_rush16_promoted_build_matrix(
            tmp_path,
            device="rytm",
            specs={"bad.yaml": "bad"},
            config=_config("rytm"),
            checkpoint=checkpoint,
        )
    app._write_rush16_promoted_build_matrix(
        tmp_path,
        device="rytm",
        specs={"ignored.yaml": {}},
        config=_config("rytm"),
        checkpoint=checkpoint,
    )
    matrix = json.loads(
        (tmp_path / "calibration" / "RYTM_BUILD_MATRIX.json").read_text(encoding="utf-8")
    )
    assert matrix["entries"] == []


def test_completed_calibration_resume_returns_before_provider(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(calibration, "next_rush16_calibration_step", lambda *_args: None)
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert (
        app.main(
            [
                "--arm",
                "--rush16-calibrate",
                "--rush01-device",
                "rytm",
                "--rush01-config",
                str(config_path),
                "--rush01-disposable-target",
                "DISPOSABLE",
                "--rush16-hardware-unit",
                "Unit",
                "--rush16-session-root",
                str(tmp_path / "local"),
                "--confirm-rush16-calibration-send",
            ]
        )
        == 0
    )
    assert "observations are complete" in capsys.readouterr().out


def test_calibration_runner_cancellation_and_bad_approval_fail_safely(
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
                    "tracks": dict(_config("rytm").track_channels),
                }
            }
        ),
        encoding="utf-8",
    )
    base = [
        "--arm",
        "--rush16-calibrate",
        "--rush01-device",
        "rytm",
        "--rush01-config",
        str(config_path),
        "--rush01-disposable-target",
        "DISPOSABLE",
        "--rush16-hardware-unit",
        "Unit",
        "--rush01-capture-timeout",
        "12",
        "--rush01-delay-ms",
        "0",
        "--confirm-rush16-calibration-send",
    ]
    monkeypatch.setattr(
        app,
        "_read_rush16_operator_input",
        lambda _prompt: (_ for _ in ()).throw(KeyboardInterrupt()),
    )
    assert app.main(base + ["--rush16-session-root", str(tmp_path / "cancel")]) == 130
    assert "cancelled" in capsys.readouterr().err

    baseline = _synthetic_frame()
    provider = _FakeCalibrationProvider((baseline, _changed_frame(baseline)))
    monkeypatch.setattr(mido_provider, "build_mido_midi_port_provider", lambda: provider)
    monkeypatch.setattr(rush01_midi_transport, "send_cc", lambda *_args, **_kwargs: None)
    responses = iter(("", '"BD SHARP 0"', "{}"))
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: next(responses))
    assert app.main(base + ["--rush16-session-root", str(tmp_path / "bad")]) == 1
    assert provider.output.closed
    assert "must be a requested value or a JSON array" in capsys.readouterr().err

    class FailingProvider(_FakeCalibrationProvider):
        def capture_sysex_messages(
            self, port_name: str, *, timeout_seconds: float
        ) -> tuple[bytes, ...]:
            raise RuntimeError("capture failed")

    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: FailingProvider((baseline, baseline)),
    )
    monkeypatch.setattr(app, "_read_rush16_operator_input", lambda _prompt: "")
    assert app.main(base + ["--rush16-session-root", str(tmp_path / "failure")]) == 1
    assert "capture failed" in capsys.readouterr().err


def test_calibration_runner_reports_pre_provider_validation_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        mido_provider,
        "build_mido_midi_port_provider",
        lambda: (_ for _ in ()).throw(AssertionError("provider constructed")),
    )
    assert (
        app.main(
            [
                "--arm",
                "--rush16-calibrate",
                "--rush01-device",
                "rytm",
                "--rush01-config",
                str(tmp_path / "missing.yaml"),
                "--rush01-disposable-target",
                "DISPOSABLE",
                "--rush16-hardware-unit",
                "Unit",
                "--confirm-rush16-calibration-send",
            ]
        )
        == 1
    )
    assert "validation failed" in capsys.readouterr().err
