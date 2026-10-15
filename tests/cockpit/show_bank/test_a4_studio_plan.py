"""Studio packets come only from fresh canonical reconstruction, never reports."""

from __future__ import annotations

import copy
import hashlib
from collections.abc import Sequence
from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import timedelta
from pathlib import Path
from typing import TypeVar

import pytest
from cockpit.show_bank.conftest import (
    SHOW_BANK_BOUNDARY_NOW,
    build_show_bank_harness,
    generate_show_bank_candidates,
)

from rytm_randomizer.cockpit.data.a4_preparation import A4_PREPARATION_PERMANENT_BLOCKERS
from rytm_randomizer.cockpit.data.a4_studio_audition import A4StudioAuditionPlan, A4StudioRouting
from rytm_randomizer.cockpit.data.parameter_scope import ParameterCell, ParameterSelection
from rytm_randomizer.cockpit.data.show_bank import (
    A4_NATIVE_MUTATION_ALGORITHM,
    AnalogFourCandidateValue,
    AnalogFourNativeCandidateValue,
    ShowBankEntry,
    ShowKitCandidate,
    ShowKitScope,
)
from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID
from rytm_randomizer.cockpit.show_bank.a4_preparation import (
    A4PreparationContext,
    prepare_a4_audition,
)
from rytm_randomizer.cockpit.show_bank.a4_studio_audition import prepare_a4_studio_audition
from rytm_randomizer.data.analog_four_midi import ANALOG_FOUR_SYNTH_TRACK_CC
from rytm_randomizer.data.analog_four_native_transport import (
    A4_NATIVE_CC7_BINDINGS,
    A4_NATIVE_TRANSPORT_ENUM_REASON,
    A4_NATIVE_TRANSPORT_PAIRED_REASON,
    A4_NATIVE_TRANSPORT_UNMAPPED_REASON,
    AnalogFourNativeTransportPreview,
)
from rytm_randomizer.devices import (
    AnalogFourNativeMutation,
    get_analog_four_native_field_capability,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.devices.strategies.analog_four_native_fields import (
    AnalogFourNativeCandidateResult,
)
from rytm_randomizer.observability.metrics import get_metrics
from rytm_randomizer.snapshot.mutation_scope import MutationScope

pytestmark = [pytest.mark.fast, pytest.mark.usefixtures("offline_hardware_denied")]
_Record = TypeVar("_Record")


def _corrupt(record: _Record, **fields: object) -> _Record:
    malformed = copy.copy(record)
    for name, value in fields.items():
        object.__setattr__(malformed, name, value)
    return malformed


@dataclass(frozen=True)
class StudioCase:
    bank_id: str
    bank_revision: int
    entry: ShowBankEntry
    source_frame: bytes | None
    candidate_frame: bytes | None
    context: A4PreparationContext
    routing: A4StudioRouting
    session_generation: int = 3
    acknowledge_unvalidated_hardware: bool = True

    @property
    def candidate(self) -> ShowKitCandidate:
        return self.entry.candidates[0]

    def prepare(self) -> A4StudioAuditionPlan:
        return prepare_a4_studio_audition(
            bank_id=self.bank_id,
            bank_revision=self.bank_revision,
            entry=self.entry,
            source_frame=self.source_frame,
            candidate_frame=self.candidate_frame,
            context=self.context,
            routing=self.routing,
            session_generation=self.session_generation,
            acknowledge_unvalidated_hardware=self.acknowledge_unvalidated_hardware,
        )

    def with_candidate(self, candidate: ShowKitCandidate) -> StudioCase:
        return replace(self, entry=_corrupt(self.entry, candidates=(candidate,)))

    def with_mutations(self, mutations: tuple[AnalogFourNativeMutation, ...]) -> StudioCase:
        assert self.source_frame is not None
        rendered = get_analog_four_native_field_capability().render_native_fields(
            self.source_frame, mutations
        )
        values = tuple(
            AnalogFourNativeCandidateValue(
                after.track,
                after.parameter,
                after.screen_value,
                after.encoded_native,
                after.metadata.native_encoding.value,
                after.unpacked_offsets,
            )
            for applied in rendered.applied_mutations
            for after in (applied.rendered,)
        )
        a4 = replace(
            self.candidate.analog_four_candidate,
            artifact_fingerprint=rendered.sha256[:16],
            semantic_fingerprint=rendered.sha256[:16],
            sysex=replace(
                self.candidate.analog_four_candidate.sysex,
                frame_sha256=rendered.sha256,
                frame_bytes=len(rendered.framed_sysex),
                retained=None,
            ),
            values=values,
        )
        candidate = _corrupt(self.candidate, analog_four_candidate=a4)
        return replace(self.with_candidate(candidate), candidate_frame=rendered.framed_sysex)


@pytest.fixture
def studio_case(tmp_path: Path) -> StudioCase:
    harness = build_show_bank_harness(tmp_path)
    candidate = generate_show_bank_candidates(harness, count=1, seed=8)[0]
    recipe = replace(
        candidate.recipe,
        analog_four_scope=ShowKitScope(ANALOG_FOUR_DEVICE_ID),
        profile=harness.profile,
        a4_algorithm=A4_NATIVE_MUTATION_ALGORITHM,
    )
    # Retain the shared canonical paired entry; replace only the A4 recipe/value facts.
    candidate = _corrupt(candidate, recipe=recipe)
    entry = _corrupt(
        harness.workspace.bank(harness.bank_id).entry(harness.entry_id),
        candidates=(candidate,),
        selected_candidate_id=candidate.candidate_id,
    )
    case = StudioCase(
        harness.bank_id,
        harness.workspace.bank(harness.bank_id).revision,
        entry,
        harness.analog_four.frame,
        None,
        A4PreparationContext(
            scope=MutationScope(),
            capture_after=SHOW_BANK_BOUNDARY_NOW,
            checked_at=SHOW_BANK_BOUNDARY_NOW + timedelta(minutes=2),
            current_capture=replace(
                harness.analog_four,
                captured_at=SHOW_BANK_BOUNDARY_NOW + timedelta(minutes=1),
            ),
            active_candidate_id=candidate.candidate_id,
            session_connected=True,
            candidate_is_local=True,
            source_reloaded=True,
            output_port_name="  Exact A4 Output  ",
        ),
        A4StudioRouting("  Exact A4 Output  ", (16, 7, 2, 12)),
    )
    return case.with_mutations(
        tuple(
            AnalogFourNativeMutation(parameter, index % 4 + 1, 65)
            for index, parameter in enumerate(A4_NATIVE_CC7_BINDINGS)
        )
    )


def _assert_blocked(case: StudioCase, reason: str) -> A4StudioAuditionPlan:
    plan = case.prepare()
    assert not plan.ready
    assert reason in plan.blocked_reasons
    assert not plan.send_plan.ready
    assert plan.send_plan.packets == ()
    assert plan.to_dict()["send_plan"]["estimated_midi_msgs"] == 0
    return plan


def test_studio_plan_projects_all_25_exact_bindings_through_explicit_track_routing(
    studio_case: StudioCase,
) -> None:
    plan = studio_case.prepare()
    assert plan.ready and plan.blocked_reasons == ()
    assert len(plan.send_plan.packets) == len(A4_NATIVE_CC7_BINDINGS) == 25
    assert {packet.pad_id for packet in plan.send_plan.packets} == {1, 2, 3, 4}
    for packet, value in zip(
        plan.send_plan.packets, studio_case.candidate.analog_four_candidate.values, strict=True
    ):
        assert packet.parameter == value.parameter
        assert packet.pad_id == value.track_id
        assert packet.channel == studio_case.routing.track_channels[value.track_id - 1] - 1
        assert packet.value == 65
        assert (
            packet.control
            == ANALOG_FOUR_SYNTH_TRACK_CC[A4_NATIVE_CC7_BINDINGS[value.parameter]].cc_msb
        )
    assert plan.bank_id == studio_case.bank_id
    assert plan.bank_revision == studio_case.bank_revision
    assert plan.entry_id == studio_case.entry.entry_id
    assert plan.candidate_id == studio_case.candidate.candidate_id
    assert plan.session_generation == studio_case.session_generation
    assert plan.plan_id == plan.send_plan.plan_id
    assert plan.send_plan.safety_status == "armed"
    assert plan.send_plan.source_snapshot_id == studio_case.entry.analog_four_source.capture_id
    assert plan.hardware_send_validated is plan.persistent_write is False
    assert plan.output_authority == "studio-ram-only-unqualified"
    wire = plan.to_dict()
    assert wire["routing"] == {
        "output_port_name": "  Exact A4 Output  ",
        "track_channels": [16, 7, 2, 12],
    }
    assert "checked_at" not in wire
    assert plan == studio_case.prepare()
    assert wire == studio_case.prepare().to_dict()
    wire["blocked_reasons"].append("forged")
    wire["routing"]["track_channels"].clear()
    assert plan.blocked_reasons == ()
    assert plan.routing.track_channels == (16, 7, 2, 12)
    with pytest.raises(FrozenInstanceError):
        plan.bank_revision = 9
    with pytest.raises(FrozenInstanceError):
        plan.routing.output_port_name = "other"
    for field in ("hardware_send_validated", "persistent_write", "output_authority"):
        with pytest.raises(ValueError, match="init=False"):
            replace(plan, **{field: True})


def test_send_time_rebuild_ignores_checked_at_but_preserves_all_identity_inputs(
    studio_case: StudioCase,
) -> None:
    original = studio_case.prepare()
    later = replace(
        studio_case,
        context=replace(
            studio_case.context, checked_at=studio_case.context.checked_at + timedelta(seconds=5)
        ),
    )
    assert later.prepare() == original
    assert later.prepare().to_dict() == original.to_dict()
    for case in (
        replace(studio_case, bank_id="another-bank"),
        replace(studio_case, bank_revision=studio_case.bank_revision + 1),
        replace(studio_case, session_generation=4),
        replace(studio_case, entry=_corrupt(studio_case.entry, entry_id="another-cue")),
        replace(
            studio_case, routing=A4StudioRouting(studio_case.routing.output_port_name, (1, 2, 3, 4))
        ),
        replace(
            studio_case,
            context=replace(
                studio_case.context, capture_after=SHOW_BANK_BOUNDARY_NOW + timedelta(seconds=1)
            ),
        ),
    ):
        assert case.prepare().ready
        assert case.prepare().plan_id != original.plan_id


@pytest.mark.parametrize(
    "field,value",
    (
        ("captured_at", SHOW_BANK_BOUNDARY_NOW + timedelta(seconds=70)),
        ("kit_name", "Different decoded label"),
        ("slot", 8),
        ("snapshot_layout", "different-layout"),
        ("parameter_readiness", "native_fields_pending"),
        ("layout_items", ()),
    ),
)
def test_capture_identity_binds_every_existing_public_field(
    studio_case: StudioCase, field: str, value: object
) -> None:
    original = studio_case.prepare()
    capture = _corrupt(studio_case.context.current_capture, **{field: value})
    assert capture != studio_case.context.current_capture
    case = replace(studio_case, context=replace(studio_case.context, current_capture=capture))
    assert case.prepare().ready
    assert case.prepare().plan_id != original.plan_id


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("session_connected", False, "session_unavailable"),
        ("candidate_is_local", False, "candidate_not_local"),
        ("source_reloaded", False, "source_reload_required"),
        ("active_candidate_id", None, "candidate_not_selected"),
        ("active_candidate_id", "another-candidate", "candidate_not_selected"),
        ("current_capture", None, "current_capture_required"),
        ("output_port_name", None, "output_port_intent_required"),
        ("output_port_name", "other output", "output_port_mismatch"),
        ("scope", MutationScope(locked_ids=frozenset({1})), "scope_changed"),
        ("scope", MutationScope(target_ids=frozenset({2})), "scope_changed"),
    ),
)
def test_studio_plan_refuses_whole_candidate_when_current_context_is_unusable(
    studio_case: StudioCase, field: str, value: object, reason: str
) -> None:
    _assert_blocked(
        replace(studio_case, context=replace(studio_case.context, **{field: value})), reason
    )


def test_studio_acknowledgment_is_required_and_does_not_promote_offline_reports(
    studio_case: StudioCase,
) -> None:
    _assert_blocked(
        replace(studio_case, acknowledge_unvalidated_hardware=False),
        "unvalidated_hardware_acknowledgment_required",
    )
    report = prepare_a4_audition(
        entry=studio_case.entry,
        source_frame=studio_case.source_frame,
        candidate_frame=studio_case.candidate_frame,
        context=studio_case.context,
    )
    assert report.blocked_reasons == A4_PREPARATION_PERMANENT_BLOCKERS
    assert not report.ready
    assert not report.transport_preview.ready
    assert report.transport_preview.mapping_complete
    assert set(A4_PREPARATION_PERMANENT_BLOCKERS) <= set(report.transport_preview.blocked_reasons)


@pytest.mark.parametrize(
    "field,value,reason",
    (
        ("device_id", "analog_rytm_mk2", "current_capture_invalid"),
        ("round_trip_verified", 1, "current_capture_invalid"),
        ("input_only", 1, "current_capture_invalid"),
        ("sent_midi", 0, "current_capture_invalid"),
        ("frame_bytes", 1, "current_capture_invalid"),
        ("fingerprint", "f" * 16, "current_capture_invalid"),
        ("frame", b"broken", "current_capture_invalid"),
        ("captured_at", SHOW_BANK_BOUNDARY_NOW.replace(tzinfo=None), "current_capture_invalid"),
        ("captured_at", SHOW_BANK_BOUNDARY_NOW, "current_capture_stale"),
        ("captured_at", SHOW_BANK_BOUNDARY_NOW + timedelta(minutes=3), "current_capture_stale"),
    ),
)
def test_current_capture_must_be_exact_input_only_fresh_source_evidence(
    studio_case: StudioCase, field: str, value: object, reason: str
) -> None:
    capture = _corrupt(studio_case.context.current_capture, **{field: value})
    _assert_blocked(
        replace(studio_case, context=replace(studio_case.context, current_capture=capture)), reason
    )


def test_capture_must_follow_source_time_even_when_session_cutoff_is_older(
    studio_case: StudioCase,
) -> None:
    capture = replace(
        studio_case.context.current_capture,
        captured_at=studio_case.entry.analog_four_source.captured_at,
    )
    context = replace(
        studio_case.context,
        capture_after=SHOW_BANK_BOUNDARY_NOW - timedelta(minutes=10),
        current_capture=capture,
    )
    _assert_blocked(replace(studio_case, context=context), "current_capture_stale")


@pytest.mark.parametrize("slot", (None, True, 0, 129))
def test_recovery_slot_has_no_default_or_boolean_coercion(
    studio_case: StudioCase, slot: object
) -> None:
    source = _corrupt(studio_case.entry.analog_four_source, hardware_slot=slot)
    _assert_blocked(
        replace(studio_case, entry=_corrupt(studio_case.entry, analog_four_source=source)),
        "recovery_slot_required",
    )


@pytest.mark.parametrize("field", ("source_frame", "candidate_frame"))
@pytest.mark.parametrize("value", (None, b"invalid KIT"))
def test_retained_frames_are_required_and_never_replaced_by_claimed_hashes(
    studio_case: StudioCase, field: str, value: bytes | None
) -> None:
    suffix = "unavailable" if value is None else "invalid"
    _assert_blocked(
        replace(studio_case, **{field: value}), field.replace("frame", f"bytes_{suffix}")
    )


@pytest.mark.parametrize(
    "parameter,reason",
    (
        ("filter1_frequency", A4_NATIVE_TRANSPORT_PAIRED_REASON),
        ("osc1_tune", A4_NATIVE_TRANSPORT_PAIRED_REASON),
        ("noise_fade", "native_transport_scale_conflict"),
        ("osc1_waveform", A4_NATIVE_TRANSPORT_ENUM_REASON),
        ("osc1_detune", A4_NATIVE_TRANSPORT_UNMAPPED_REASON),
    ),
)
def test_mixed_supported_and_unsupported_native_rows_refuse_every_packet(
    studio_case: StudioCase, parameter: str, reason: str
) -> None:
    readback = get_analog_four_native_field_capability().read_native_fields(
        studio_case.source_frame
    )
    source = readback.value(parameter, 1)
    assert source.domain is not None
    target = source.domain.value_at(1)
    if target == source.encoded_native:
        target = source.domain.value_at(0)
    case = studio_case.with_mutations(
        (
            AnalogFourNativeMutation("osc1_level", 1, 65),
            AnalogFourNativeMutation(parameter, 1, target),
        )
    )
    _assert_blocked(case, reason)


@pytest.mark.parametrize(
    "field,value",
    (("native_encoding", "guessed"), ("unpacked_offsets", (1,)), ("screen_value", "wrong")),
)
def test_native_claims_are_checked_against_exact_canonical_readback(
    studio_case: StudioCase, field: str, value: object
) -> None:
    a4 = studio_case.candidate.analog_four_candidate
    a4 = _corrupt(a4, values=(_corrupt(a4.values[0], **{field: value}), *a4.values[1:]))
    _assert_blocked(
        studio_case.with_candidate(_corrupt(studio_case.candidate, analog_four_candidate=a4)),
        "candidate_bytes_invalid",
    )


def test_self_consistently_rehashed_protected_bytes_and_hidden_changes_are_refused(
    studio_case: StudioCase,
) -> None:
    case = studio_case.with_mutations((AnalogFourNativeMutation("osc1_level", 1, 65),))
    a4 = case.candidate.analog_four_candidate
    capability = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID).capability
    decoded = capability.decode_saved_kit_capture(case.candidate_frame)
    body = bytearray(decoded.unpacked)
    body[-20] ^= 1
    frame = capability.encode_saved_kit_capture(replace(decoded, unpacked=bytes(body)))
    a4 = replace(a4, sysex=replace(a4.sysex, frame_sha256=hashlib.sha256(frame).hexdigest()))
    case = replace(
        case.with_candidate(_corrupt(case.candidate, analog_four_candidate=a4)),
        candidate_frame=frame,
    )
    _assert_blocked(case, "candidate_bytes_invalid")
    # Removing a claim cannot hide its actual valid native change in the frame.
    a4 = studio_case.candidate.analog_four_candidate
    a4 = _corrupt(a4, values=a4.values[1:])
    _assert_blocked(
        studio_case.with_candidate(_corrupt(studio_case.candidate, analog_four_candidate=a4)),
        "candidate_bytes_invalid",
    )


@pytest.mark.parametrize("selection", ((), (ParameterCell(1, "noise_level"),)))
def test_explicit_empty_or_excluding_parameter_selection_never_sends_a_subset(
    studio_case: StudioCase, selection: tuple[ParameterCell, ...]
) -> None:
    candidate = studio_case.candidate
    scope = replace(candidate.recipe.analog_four_scope, parameters=ParameterSelection(selection))
    candidate = _corrupt(candidate, recipe=replace(candidate.recipe, analog_four_scope=scope))
    _assert_blocked(studio_case.with_candidate(candidate), "candidate_bytes_invalid")


def test_valid_target_minus_lock_scope_is_retained_and_outside_rows_refuse(
    studio_case: StudioCase,
) -> None:
    case = studio_case.with_mutations((AnalogFourNativeMutation("osc1_level", 4, 65),))
    scope = ShowKitScope(ANALOG_FOUR_DEVICE_ID, (1, 4), (1,))
    candidate = _corrupt(
        case.candidate, recipe=replace(case.candidate.recipe, analog_four_scope=scope)
    )
    context = replace(
        case.context, scope=MutationScope(target_ids=frozenset({1, 4}), locked_ids=frozenset({1}))
    )
    case = replace(case.with_candidate(candidate), context=context)
    assert case.prepare().ready
    assert [packet.pad_id for packet in case.prepare().send_plan.packets] == [4]
    assert case.prepare().send_plan.locked_pad_ids == frozenset({1})
    assert case.prepare().send_plan.target_pad_ids == frozenset({1, 4})
    locked = case.with_mutations((AnalogFourNativeMutation("osc1_level", 1, 65),))
    _assert_blocked(locked, "candidate_bytes_invalid")


def test_exact_native_noop_and_all_locked_scope_produce_zero_packets(
    studio_case: StudioCase,
) -> None:
    case = studio_case.with_mutations(())
    _assert_blocked(case, "no_a4_changes")
    scope = ShowKitScope(ANALOG_FOUR_DEVICE_ID, (), (1, 2, 3, 4))
    candidate = _corrupt(
        case.candidate, recipe=replace(case.candidate.recipe, analog_four_scope=scope)
    )
    case = replace(
        case.with_candidate(candidate),
        context=replace(case.context, scope=MutationScope(locked_ids=frozenset({1, 2, 3, 4}))),
    )
    _assert_blocked(case, "no_a4_changes")


@pytest.mark.parametrize(
    "name",
    (
        True,
        None,
        "",
        "   ",
        "p" * 257,
        "port\nname",
        "port\x7f",
        "port\x85",
        "port\u202e",
        "port\u2028",
    ),
)
def test_routing_rejects_nontext_empty_unbounded_and_control_names(name: object) -> None:
    with pytest.raises(ValueError, match="output_port_name"):
        A4StudioRouting(name, (1, 2, 3, 4))


@pytest.mark.parametrize(
    "channels",
    (
        None,
        True,
        "1234",
        [1, 2, 3, 4],
        (),
        (1, 2, 3),
        (1, 2, 3, 4, 5),
        (True, 2, 3, 4),
        (1.0, 2, 3, 4),
        ("1", 2, 3, 4),
        (0, 2, 3, 4),
        (17, 2, 3, 4),
        (1, 1, 3, 4),
    ),
)
def test_routing_requires_exactly_four_distinct_strict_user_channels(channels: object) -> None:
    with pytest.raises(ValueError):
        A4StudioRouting("A4", channels)


@pytest.mark.parametrize(
    "field,value",
    (
        ("bank_id", "bad/id"),
        ("bank_revision", True),
        ("bank_revision", -1),
        ("session_generation", True),
        ("session_generation", -1),
        ("acknowledge_unvalidated_hardware", 1),
    ),
)
def test_studio_api_rejects_malformed_identifiers_generations_and_boolean_intent(
    studio_case: StudioCase, field: str, value: object
) -> None:
    with pytest.raises(ValueError):
        replace(studio_case, **{field: value}).prepare()


def test_wrapper_refuses_mutable_reasons_contradictory_readiness_and_partial_blocked_packets(
    studio_case: StudioCase,
) -> None:
    plan = studio_case.prepare()
    with pytest.raises(TypeError, match="immutable tuple"):
        replace(plan, blocked_reasons=[])
    with pytest.raises(ValueError, match="readiness"):
        replace(plan, blocked_reasons=("refused",))
    send_plan = replace(
        plan.send_plan,
        ready=False,
        readiness_reason="unsupported_control_changed",
        blocked_reasons=("unsupported_control_changed",),
    )
    with pytest.raises(ValueError, match="zero packets"):
        replace(plan, send_plan=send_plan, blocked_reasons=("refused",))


@pytest.mark.parametrize("field", ("source_frame", "candidate_frame"))
def test_canonical_review_refuses_mutable_frame_buffers(
    studio_case: StudioCase, field: str
) -> None:
    frame = getattr(studio_case, field)
    _assert_blocked(
        replace(studio_case, **{field: bytearray(frame)}),
        field.replace("frame", "bytes_invalid"),
    )


def test_canonical_review_refuses_mixed_legacy_native_claims(studio_case: StudioCase) -> None:
    a4 = studio_case.candidate.analog_four_candidate
    legacy = AnalogFourCandidateValue(1, "Filter1 Frequency", "1", 256, 128)
    a4 = _corrupt(a4, values=(*a4.values, legacy))
    _assert_blocked(
        studio_case.with_candidate(_corrupt(studio_case.candidate, analog_four_candidate=a4)),
        "candidate_bytes_invalid",
    )


@pytest.mark.parametrize("field", ("track_id", "encoded_native"))
def test_native_boolean_claims_cannot_alias_exact_integer_facts(
    studio_case: StudioCase, field: str
) -> None:
    a4 = studio_case.candidate.analog_four_candidate
    a4 = _corrupt(a4, values=(_corrupt(a4.values[0], **{field: True}), *a4.values[1:]))
    _assert_blocked(
        studio_case.with_candidate(_corrupt(studio_case.candidate, analog_four_candidate=a4)),
        "candidate_bytes_invalid",
    )


@pytest.mark.parametrize(
    "parameter",
    ("amp_volume", "osc1_fine", "portamento", "lfo1_phase", "All Notes Off", "osc1_level\n"),
)
def test_protected_unresolved_and_control_claims_refuse_whole_plan(
    studio_case: StudioCase, parameter: str
) -> None:
    a4 = studio_case.candidate.analog_four_candidate
    a4 = _corrupt(a4, values=(_corrupt(a4.values[0], parameter=parameter), *a4.values[1:]))
    _assert_blocked(
        studio_case.with_candidate(_corrupt(studio_case.candidate, analog_four_candidate=a4)),
        "candidate_bytes_invalid",
    )


@pytest.mark.parametrize(
    "field,value",
    (
        ("roundtrip_redecoded", False),
        ("native_byte_isolation_validated", False),
        ("hardware_send_validated", True),
    ),
)
def test_native_renderer_cannot_widen_studio_authority(
    studio_case: StudioCase, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    capability = get_analog_four_native_field_capability()
    original = capability.render_native_fields

    def malformed(
        source: bytes, mutations: Sequence[AnalogFourNativeMutation]
    ) -> AnalogFourNativeCandidateResult:
        return _corrupt(original(source, mutations), **{field: value})

    monkeypatch.setattr(capability, "render_native_fields", malformed)
    _assert_blocked(studio_case, "candidate_bytes_invalid")


def test_canonical_parameter_selection_can_allow_exact_changes(studio_case: StudioCase) -> None:
    candidate = studio_case.candidate
    scope = replace(
        candidate.recipe.analog_four_scope,
        parameters=ParameterSelection(
            tuple(
                ParameterCell(value.track_id, value.parameter)
                for value in candidate.analog_four_candidate.values
            )
        ),
    )
    candidate = _corrupt(candidate, recipe=replace(candidate.recipe, analog_four_scope=scope))
    plan = studio_case.with_candidate(candidate).prepare()
    assert plan.ready
    assert plan.send_plan.packets == studio_case.prepare().send_plan.packets
    assert plan.plan_id != studio_case.prepare().plan_id


@pytest.mark.parametrize("projection", (None, AnalogFourNativeTransportPreview(())))
def test_missing_or_empty_canonical_projection_refuses_whole_plan(
    studio_case: StudioCase,
    monkeypatch: pytest.MonkeyPatch,
    projection: AnalogFourNativeTransportPreview | None,
) -> None:
    monkeypatch.setattr(
        "rytm_randomizer.cockpit.show_bank.a4_preparation.preview_analog_four_native_cc_transport",
        lambda _source, _mutations: projection,
    )
    _assert_blocked(studio_case, "no_a4_changes")


def test_missing_selection_returns_a_blocked_nullable_identity(studio_case: StudioCase) -> None:
    case = replace(studio_case, entry=_corrupt(studio_case.entry, selected_candidate_id=None))
    plan = _assert_blocked(case, "candidate_not_selected")
    assert plan.candidate_id is plan.to_dict()["candidate_id"] is None


def test_explicit_high_risk_candidate_is_refused_and_builder_records_categorical_decision(
    studio_case: StudioCase, package_logs: pytest.LogCaptureFixture
) -> None:
    candidate = _corrupt(
        studio_case.candidate,
        rytm_candidate=replace(studio_case.candidate.rytm_candidate, safety_status="high_risk"),
    )
    before = get_metrics().errors_by_kind["a4_studio_audition_refused"]
    plan = _assert_blocked(studio_case.with_candidate(candidate), "candidate_high_risk")
    assert plan.send_plan.safety_status == "high_risk"
    assert plan.send_plan.readiness_reason == "candidate_high_risk"
    assert get_metrics().errors_by_kind["a4_studio_audition_refused"] == before + 1
    record = next(
        item for item in package_logs.records if item.message == "a4_studio_audition_prepared"
    )
    assert record.ready is False
    assert record.packet_count == 0
    assert record.plan_id == plan.plan_id
    assert record.session_generation == studio_case.session_generation
    assert record.blocked_reasons == ["candidate_high_risk"]
