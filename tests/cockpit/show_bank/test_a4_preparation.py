"""A4 preparation revalidates exact bytes but can never authorize hardware."""

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

from rytm_randomizer.cockpit.data.a4_preparation import (
    A4_PREPARATION_PERMANENT_BLOCKERS,
    A4PreparationReport,
)
from rytm_randomizer.cockpit.data.show_bank import ShowBankEntry, ShowKitCandidate, ShowKitScope
from rytm_randomizer.cockpit.data.stage import ANALOG_FOUR_DEVICE_ID
from rytm_randomizer.cockpit.show_bank.a4_preparation import (
    A4PreparationContext,
    prepare_a4_audition,
)
from rytm_randomizer.devices import (
    AnalogFourFilter1FrequencyCandidateMutation,
    get_analog_four_filter1_frequency_candidate_capability,
    resolve_saved_kit_capture_capability,
)
from rytm_randomizer.devices.strategies.analog_four_filter1_frequency_candidate import (
    AnalogFourFilter1FrequencyCandidateResult,
)
from rytm_randomizer.snapshot.mutation_scope import MutationScope

pytestmark = pytest.mark.fast
_Record = TypeVar("_Record")


def _corrupt(record: _Record, **fields: object) -> _Record:
    """Model malformed in-memory collaborators without weakening production DTOs."""

    malformed = copy.copy(record)
    for name, value in fields.items():
        object.__setattr__(malformed, name, value)
    return malformed


@dataclass(frozen=True)
class PreparationCase:
    entry: ShowBankEntry
    source_frame: bytes | None
    candidate_frame: bytes | None
    context: A4PreparationContext

    @property
    def candidate(self) -> ShowKitCandidate:
        return self.entry.candidates[0]

    def review(self) -> A4PreparationReport:
        return prepare_a4_audition(
            entry=self.entry,
            source_frame=self.source_frame,
            candidate_frame=self.candidate_frame,
            context=self.context,
        )

    def with_candidate(self, candidate: ShowKitCandidate) -> PreparationCase:
        return replace(self, entry=_corrupt(self.entry, candidates=(candidate,)))


@pytest.fixture
def preparation_case(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> PreparationCase:
    harness = build_show_bank_harness(tmp_path)
    candidate = generate_show_bank_candidates(harness, count=1, seed=8)[0]
    entry = replace(
        harness.workspace.bank(harness.bank_id).entry(harness.entry_id),
        selected_candidate_id=candidate.candidate_id,
    )
    rendered = (
        get_analog_four_filter1_frequency_candidate_capability().render_filter1_frequency_candidate(
            harness.analog_four.frame,
            tuple(
                AnalogFourFilter1FrequencyCandidateMutation(value.track_id, value.screen_value)
                for value in candidate.analog_four_candidate.values
            ),
        )
    )

    def forbidden_hardware(*_args: object, **_kwargs: object) -> None:
        pytest.fail("offline A4 preparation attempted a hardware operation")

    for member in ("list_input_names", "list_output_names", "open_input", "open_output"):
        monkeypatch.setattr(
            f"rytm_randomizer.mido_provider.MidoMidiPortProvider.{member}", forbidden_hardware
        )
    for member in ("arm", "confirm", "apply"):
        monkeypatch.setattr(
            f"rytm_randomizer.senders.armed_apply.ArmedApplySession.{member}", forbidden_hardware
        )
    return PreparationCase(
        entry=entry,
        source_frame=harness.analog_four.frame,
        candidate_frame=rendered.framed_sysex,
        context=A4PreparationContext(
            scope=MutationScope(target_ids=frozenset({1})),
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
            output_port_name="Exact A4 output intent",
        ),
    )


def test_complete_local_evidence_is_deterministic_and_still_permanently_blocked(
    preparation_case: PreparationCase,
) -> None:
    report = preparation_case.review()
    assert report == preparation_case.review()
    assert report.blocked_reasons == A4_PREPARATION_PERMANENT_BLOCKERS
    assert report.ready is False
    assert report.hardware_send_validated is False
    assert report.output_authority == "offline-review-only"
    assert report.candidate_bytes_verified is True
    assert report.current_source_verified is True
    assert report.recovery_slot == preparation_case.entry.analog_four_source.hardware_slot
    assert report.target_ids == report.effective_ids == (1,)
    assert report.locked_ids == ()
    assert report.changes[0].track_id == 1
    assert report.changes[0].unpacked_offsets == (128, 129)
    assert report.changes[0].before_raw_q8_8 != report.changes[0].after_raw_q8_8
    assert report.changes[0].parameter == "Filter1 Frequency"
    wire = report.to_dict()
    assert wire["device_id"] == ANALOG_FOUR_DEVICE_ID
    assert wire["schema_version"] == "a4-preparation-v1"
    assert (
        wire["current_capture_at"]
        == preparation_case.context.current_capture.captured_at.isoformat()
    )
    assert wire["changes"][0]["unpacked_offsets"] == [128, 129]
    assert "packets" not in wire
    assert "framed_sysex" not in wire
    wire["blocked_reasons"].clear()
    wire["changes"].clear()
    assert report.blocked_reasons == A4_PREPARATION_PERMANENT_BLOCKERS
    assert report.changes
    with pytest.raises(FrozenInstanceError):
        report.ready = True
    with pytest.raises(ValueError, match="init=False"):
        replace(report, hardware_send_validated=True)
    assert replace(report, blocked_reasons=()).blocked_reasons == A4_PREPARATION_PERMANENT_BLOCKERS


@pytest.mark.parametrize(
    ("field", "value", "reason"),
    (
        ("session_connected", False, "session_unavailable"),
        ("candidate_is_local", False, "candidate_not_local"),
        ("source_reloaded", False, "source_reload_required"),
        ("active_candidate_id", None, "candidate_not_selected"),
        ("active_candidate_id", "other-candidate", "candidate_not_selected"),
        ("output_port_name", None, "output_port_intent_required"),
        ("output_port_name", "   ", "output_port_intent_required"),
        ("scope", MutationScope(), "scope_changed"),
        (
            "scope",
            MutationScope(target_ids=frozenset({1}), locked_ids=frozenset({1})),
            "scope_changed",
        ),
    ),
)
def test_current_context_changes_revoke_preparation_and_change_identity(
    preparation_case: PreparationCase, field: str, value: object, reason: str
) -> None:
    original = preparation_case.review()
    context = replace(preparation_case.context, **{field: value})
    report = replace(preparation_case, context=context).review()
    assert reason in report.blocked_reasons
    assert report.preparation_id != original.preparation_id
    assert report.ready is False


def test_capture_alone_and_imported_records_cannot_authorize_or_assert_a_reload(
    preparation_case: PreparationCase,
) -> None:
    context = A4PreparationContext(
        scope=preparation_case.context.scope,
        capture_after=preparation_case.context.capture_after,
        checked_at=preparation_case.context.checked_at,
        current_capture=preparation_case.context.current_capture,
    )
    report = replace(preparation_case, context=context).review()
    assert report.current_source_verified
    assert not report.source_reloaded
    assert not report.candidate_is_local
    assert {"candidate_not_local", "source_reload_required", "session_unavailable"}.issubset(
        report.blocked_reasons
    )


@pytest.mark.parametrize("member", ("source_frame", "candidate_frame"))
def test_missing_retained_bytes_are_explicit_blockers(
    preparation_case: PreparationCase, member: str
) -> None:
    report = replace(preparation_case, **{member: None}).review()
    assert member.replace("frame", "bytes_unavailable") in report.blocked_reasons
    assert not report.candidate_bytes_verified
    assert report.changes == ()


def test_missing_selection_and_recovery_slot_have_no_implicit_fallback(
    preparation_case: PreparationCase,
) -> None:
    source = replace(preparation_case.entry.analog_four_source, hardware_slot=None)
    entry = _corrupt(preparation_case.entry, selected_candidate_id=None, analog_four_source=source)
    report = replace(preparation_case, entry=entry).review()
    assert report.candidate_id is report.candidate_frame_sha256 is None
    assert report.recovery_slot is None
    assert {"candidate_not_selected", "recovery_slot_required"}.issubset(report.blocked_reasons)


@pytest.mark.parametrize(
    "field,value",
    (("device_id", "analog_rytm_mk2"), ("round_trip_verified", 1), ("fingerprint", "f" * 16)),
)
def test_source_metadata_is_checked_against_canonical_bytes(
    preparation_case: PreparationCase, field: str, value: object
) -> None:
    source = _corrupt(preparation_case.entry.analog_four_source, **{field: value})
    report = replace(
        preparation_case, entry=_corrupt(preparation_case.entry, analog_four_source=source)
    ).review()
    assert "source_bytes_invalid" in report.blocked_reasons
    assert not report.candidate_bytes_verified


@pytest.mark.parametrize("field,value", (("frame_bytes", 1), ("frame_sha256", "f" * 64)))
def test_source_artifact_identity_is_revalidated(
    preparation_case: PreparationCase, field: str, value: object
) -> None:
    source = preparation_case.entry.analog_four_source
    source = replace(source, sysex=_corrupt(source.sysex, **{field: value}))
    report = replace(
        preparation_case, entry=_corrupt(preparation_case.entry, analog_four_source=source)
    ).review()
    assert "source_bytes_invalid" in report.blocked_reasons


def test_malformed_source_frame_cannot_borrow_a_declared_hash(
    preparation_case: PreparationCase,
) -> None:
    malformed = b"not a KIT"
    source = preparation_case.entry.analog_four_source
    source = replace(
        source,
        sysex=replace(
            source.sysex,
            frame_sha256=hashlib.sha256(malformed).hexdigest(),
            frame_bytes=len(malformed),
            retained=None,
        ),
    )
    report = replace(
        preparation_case,
        source_frame=malformed,
        entry=_corrupt(preparation_case.entry, analog_four_source=source),
    ).review()
    assert "source_bytes_invalid" in report.blocked_reasons


def test_registered_codec_roundtrip_is_required(
    preparation_case: PreparationCase, monkeypatch: pytest.MonkeyPatch
) -> None:
    device = resolve_saved_kit_capture_capability(ANALOG_FOUR_DEVICE_ID).device
    monkeypatch.setattr(device, "encode_saved_kit_capture", lambda _decoded: b"changed")
    report = preparation_case.review()
    assert "source_bytes_invalid" in report.blocked_reasons
    assert "current_capture_invalid" in report.blocked_reasons


@pytest.mark.parametrize(
    "field,value",
    (("source_fingerprint", "f" * 16), ("frame_sha256", "f" * 64), ("frame_bytes", 1)),
)
def test_candidate_identity_cannot_be_forged(
    preparation_case: PreparationCase, field: str, value: object
) -> None:
    candidate = preparation_case.candidate
    a4 = candidate.analog_four_candidate
    if field == "source_fingerprint":
        a4 = _corrupt(a4, source_fingerprint=value)
    else:
        a4 = _corrupt(a4, sysex=_corrupt(a4.sysex, **{field: value}))
    report = preparation_case.with_candidate(_corrupt(candidate, analog_four_candidate=a4)).review()
    assert "candidate_bytes_invalid" in report.blocked_reasons
    assert not report.candidate_bytes_verified


def test_outer_candidate_source_identity_is_checked(preparation_case: PreparationCase) -> None:
    candidate = _corrupt(preparation_case.candidate, source_a4_fingerprint="f" * 16)
    assert (
        "candidate_bytes_invalid"
        in preparation_case.with_candidate(candidate).review().blocked_reasons
    )


@pytest.mark.parametrize(
    "field,value",
    (("parameter", "Amp Attack"), ("unpacked_offset", 0), ("encoded_unsigned_8_8", 1234)),
)
def test_claimed_field_locations_and_values_never_override_the_renderer(
    preparation_case: PreparationCase, field: str, value: object
) -> None:
    candidate = preparation_case.candidate
    a4 = candidate.analog_four_candidate
    a4 = _corrupt(a4, values=(_corrupt(a4.values[0], **{field: value}),))
    report = preparation_case.with_candidate(_corrupt(candidate, analog_four_candidate=a4)).review()
    assert "candidate_bytes_invalid" in report.blocked_reasons
    assert report.changes == ()


def test_valid_bytes_outside_the_declared_scope_are_rejected(
    preparation_case: PreparationCase,
) -> None:
    candidate = preparation_case.candidate
    recipe = replace(
        candidate.recipe, analog_four_scope=ShowKitScope(ANALOG_FOUR_DEVICE_ID, (2,), ())
    )
    report = preparation_case.with_candidate(_corrupt(candidate, recipe=recipe)).review()
    assert {"scope_changed", "candidate_bytes_invalid"}.issubset(report.blocked_reasons)


def test_candidate_frame_must_equal_canonical_rerender(preparation_case: PreparationCase) -> None:
    candidate = preparation_case.candidate
    a4 = candidate.analog_four_candidate
    source = preparation_case.entry.analog_four_source
    a4 = _corrupt(a4, sysex=source.sysex)
    case = preparation_case.with_candidate(_corrupt(candidate, analog_four_candidate=a4))
    report = replace(case, candidate_frame=case.source_frame).review()
    assert "candidate_bytes_invalid" in report.blocked_reasons


@pytest.mark.parametrize(
    "field,value",
    (
        ("roundtrip_redecoded", False),
        ("native_byte_isolation_validated", False),
        ("hardware_send_validated", True),
    ),
)
def test_renderer_verdict_cannot_widen_authority(
    preparation_case: PreparationCase, monkeypatch: pytest.MonkeyPatch, field: str, value: object
) -> None:
    capability = get_analog_four_filter1_frequency_candidate_capability()
    original = capability.render_filter1_frequency_candidate

    def corrupted_render(
        source: bytes, mutations: Sequence[AnalogFourFilter1FrequencyCandidateMutation]
    ) -> AnalogFourFilter1FrequencyCandidateResult:
        return _corrupt(original(source, mutations), **{field: value})

    monkeypatch.setattr(capability, "render_filter1_frequency_candidate", corrupted_render)
    report = preparation_case.review()
    assert "candidate_bytes_invalid" in report.blocked_reasons
    assert report.hardware_send_validated is False


def test_fully_locked_partner_stays_an_exact_unchanged_source(
    preparation_case: PreparationCase,
) -> None:
    candidate = preparation_case.candidate
    scope = ShowKitScope(ANALOG_FOUR_DEVICE_ID, (), (1, 2, 3, 4))
    a4 = _corrupt(
        candidate.analog_four_candidate,
        values=(),
        sysex=preparation_case.entry.analog_four_source.sysex,
    )
    candidate = _corrupt(
        candidate,
        analog_four_candidate=a4,
        recipe=replace(candidate.recipe, analog_four_scope=scope),
    )
    case = preparation_case.with_candidate(candidate)
    context = replace(case.context, scope=MutationScope(locked_ids=frozenset({1, 2, 3, 4})))
    report = replace(case, context=context, candidate_frame=case.source_frame).review()
    assert report.candidate_bytes_verified
    assert report.changes == ()
    assert report.effective_ids == ()
    assert "no_a4_changes" in report.blocked_reasons


def test_current_capture_is_required_even_if_a_retained_source_exists(
    preparation_case: PreparationCase,
) -> None:
    report = replace(
        preparation_case, context=replace(preparation_case.context, current_capture=None)
    ).review()
    assert "current_capture_required" in report.blocked_reasons
    assert report.current_capture_at is report.current_capture_fingerprint is None
    assert report.to_dict()["current_capture_at"] is None


@pytest.mark.parametrize(
    "field,value",
    (
        ("device_id", "analog_rytm_mk2"),
        ("round_trip_verified", False),
        ("input_only", False),
        ("sent_midi", True),
        ("frame_bytes", 1),
        ("fingerprint", "f" * 16),
        ("frame", b"broken"),
        ("captured_at", SHOW_BANK_BOUNDARY_NOW.replace(tzinfo=None)),
    ),
)
def test_invalid_current_capture_cannot_supply_source_evidence(
    preparation_case: PreparationCase, field: str, value: object
) -> None:
    capture = _corrupt(preparation_case.context.current_capture, **{field: value})
    report = replace(
        preparation_case, context=replace(preparation_case.context, current_capture=capture)
    ).review()
    assert "current_capture_invalid" in report.blocked_reasons
    assert not report.current_source_verified


@pytest.mark.parametrize("minutes", (-3, 0, 3))
def test_capture_must_follow_cutoff_and_not_come_from_the_future(
    preparation_case: PreparationCase, minutes: int
) -> None:
    capture = replace(
        preparation_case.context.current_capture,
        captured_at=SHOW_BANK_BOUNDARY_NOW + timedelta(minutes=minutes),
    )
    report = replace(
        preparation_case, context=replace(preparation_case.context, current_capture=capture)
    ).review()
    assert "current_capture_stale" in report.blocked_reasons
    assert not report.current_source_verified


def test_saved_source_capture_cannot_be_reused_with_an_older_session_cutoff(
    preparation_case: PreparationCase,
) -> None:
    capture = replace(
        preparation_case.context.current_capture,
        captured_at=preparation_case.entry.analog_four_source.captured_at,
    )
    context = replace(
        preparation_case.context,
        capture_after=SHOW_BANK_BOUNDARY_NOW - timedelta(minutes=10),
        current_capture=capture,
    )
    assert (
        "current_capture_stale"
        in replace(preparation_case, context=context).review().blocked_reasons
    )


def test_current_source_must_match_both_payload_and_frame_identity(
    preparation_case: PreparationCase,
) -> None:
    source = replace(preparation_case.entry.analog_four_source, fingerprint="f" * 16)
    report = replace(
        preparation_case, entry=_corrupt(preparation_case.entry, analog_four_source=source)
    ).review()
    assert "current_source_mismatch" in report.blocked_reasons
    source = preparation_case.entry.analog_four_source
    source = replace(source, sysex=_corrupt(source.sysex, frame_sha256="f" * 64))
    report = replace(
        preparation_case, entry=_corrupt(preparation_case.entry, analog_four_source=source)
    ).review()
    assert "current_source_mismatch" in report.blocked_reasons


@pytest.mark.parametrize("field", ("session_connected", "candidate_is_local", "source_reloaded"))
def test_context_flags_refuse_integer_boolean_coercion(
    preparation_case: PreparationCase, field: str
) -> None:
    with pytest.raises(ValueError, match=f"{field} must be a boolean"):
        replace(preparation_case.context, **{field: 1})


@pytest.mark.parametrize("field", ("capture_after", "checked_at"))
def test_context_requires_aware_timestamps(preparation_case: PreparationCase, field: str) -> None:
    with pytest.raises(ValueError, match="timezone"):
        replace(preparation_case.context, **{field: SHOW_BANK_BOUNDARY_NOW.replace(tzinfo=None)})


def test_context_refuses_an_inverted_time_window(preparation_case: PreparationCase) -> None:
    with pytest.raises(ValueError, match="must not follow checked_at"):
        replace(preparation_case.context, capture_after=SHOW_BANK_BOUNDARY_NOW + timedelta(days=1))


@pytest.mark.parametrize("name", (False, "x" * 257, "port\nname", "port\x7fname"))
def test_output_intent_is_bounded_exact_text(
    preparation_case: PreparationCase, name: object
) -> None:
    with pytest.raises(ValueError, match="output_port_name"):
        replace(preparation_case.context, output_port_name=name)


def test_valid_output_intent_is_preserved_without_name_normalization(
    preparation_case: PreparationCase,
) -> None:
    report = replace(
        preparation_case,
        context=replace(preparation_case.context, output_port_name="  Exact output  "),
    ).review()
    assert report.output_port_name == "  Exact output  "
    assert "output_port_intent_required" not in report.blocked_reasons
    assert report.preparation_id != preparation_case.review().preparation_id


def test_scope_ids_are_checked_against_the_registered_device(
    preparation_case: PreparationCase,
) -> None:
    context = replace(preparation_case.context, scope=MutationScope(target_ids=frozenset({5})))
    with pytest.raises(ValueError, match="target A4 track ids are unavailable"):
        replace(preparation_case, context=context).review()
