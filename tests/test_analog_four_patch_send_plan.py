"""Tests for passive Analog Four patch send-plan compilation."""

from __future__ import annotations

import json
import types
from pathlib import Path

import pytest

from conftest import analog_four_reference_feature_report
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report() -> FeatureReport:
    return analog_four_reference_feature_report(
        derived_at="2026-07-03T12:00:00Z",
    )


def test_patch_send_plan_compiles_selected_candidate_into_ordered_midi_events() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan,
    )

    plan = build_analog_four_patch_send_plan(
        _reference_report(),
        track=2,
        selected_candidate=1,
    )

    assert plan.version == "analog-four-patch-send-plan-v1"
    assert plan.device_id == "analog_four_mk2"
    assert plan.mode == "single-sound-live-dial"
    assert plan.selected_track == 2
    assert plan.selected_candidate == 1
    assert plan.selected_label == "Closest reference"
    assert plan.summary.total_rows == 39
    assert plan.summary.sendable_count == 33
    assert plan.summary.manual_count == 6
    assert plan.summary.cc_event_count == 23
    assert plan.summary.nrpn_event_count == 10
    assert plan.summary.transport_message_count == 53
    assert plan.summary.ready_percentage == 85
    assert plan.summary.live_dial_path == "partial-live-dial-ready"
    assert (
        plan.summary.blocking_reason
        == "paired CC LSB conversion requires hardware verification before full live dial-in"
    )

    first_event = plan.send_events[0]
    assert first_event.sequence == 1
    assert first_event.track == 2
    assert first_event.channel == 1
    assert first_event.message_kind == "cc"
    assert first_event.parameter == "OSC1 Level"
    assert first_event.cc_msb == 69
    assert first_event.midi_value == 96

    first_nrpn = next(event for event in plan.send_events if event.message_kind == "nrpn")
    assert first_nrpn.sequence == 10
    assert first_nrpn.parameter == "EnvA Env Shape"
    assert first_nrpn.nrpn_address == (1, 54)
    assert first_nrpn.midi_value == 0

    enum_values = {
        event.parameter: event.midi_value
        for event in plan.send_events
        if event.parameter
        in {
            "EnvF Gate Length",
            "EnvF Destination A",
            "EnvF Destination B",
            "LFO1 Destination A",
            "LFO1 Destination B",
        }
    }
    assert enum_values == {
        "EnvF Gate Length": 0,
        "EnvF Destination A": 96,
        "EnvF Destination B": 96,
        "LFO1 Destination A": 34,
        "LFO1 Destination B": 96,
    }
    assert {event.parameter for event in plan.manual_events} == {
        "EnvF Depth A",
        "EnvF Depth B",
        "LFO1 Depth A",
        "LFO1 Depth B",
        "Filter1 Frequency",
        "Filter2 Frequency",
    }
    assert {event.skip_code for event in plan.manual_events} == {"paired-cc-unverified"}
    assert all(event.cc_lsb is None for event in plan.send_events)
    assert "preview before armed send" in plan.safety


def test_patch_send_plan_payload_is_stable_and_embeds_learning_context() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        analog_four_patch_send_plan_to_dict,
        build_analog_four_patch_send_plan,
    )

    plan = build_analog_four_patch_send_plan(
        _reference_report(),
        track=3,
        selected_candidate=3,
    )
    payload = analog_four_patch_send_plan_to_dict(plan)

    assert payload["version"] == "analog-four-patch-send-plan-v1"
    assert payload["selected_track"] == 3
    assert payload["selected_candidate"] == 3
    assert payload["selected_label"] == "Noisy texture"
    assert payload["summary"]["sendable_count"] == plan.summary.sendable_count
    assert payload["send_events"][0]["track"] == 3
    assert payload["manual_events"]
    assert {event["skip_code"] for event in payload["manual_events"]} == {"paired-cc-unverified"}
    assert payload["learning_packet"]["selected_patch"]["label"] == "Noisy texture"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_send_plan_to_dict(plan),
        sort_keys=True,
    )
    assert payload["ready"] is True
    assert payload["readiness_reason"] == ""


def test_patch_send_plan_rejects_wrong_types_and_candidate_range() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        analog_four_patch_send_plan_to_dict,
        build_analog_four_patch_send_plan,
        build_analog_four_patch_send_plan_from_genome,
    )

    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_send_plan(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="plan must be"):
        analog_four_patch_send_plan_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_send_plan(_reference_report(), selected_candidate=0)
    genome = build_analog_four_patch_genome(_reference_report())
    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_send_plan_from_genome(
            object(),  # type: ignore[arg-type]
            genome,
            selected_candidate=1,
        )
    with pytest.raises(TypeError, match="genome must be"):
        build_analog_four_patch_send_plan_from_genome(
            _reference_report(),
            object(),  # type: ignore[arg-type]
            selected_candidate=1,
        )


def test_patch_send_plan_from_genome_uses_dynamic_candidate_values() -> None:
    from dataclasses import replace

    from rytm_randomizer.data.analog_four_display import make_a4_patch_value
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        build_analog_four_patch_genome,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_from_genome,
    )

    report = _reference_report()
    genome = build_analog_four_patch_genome(report)
    candidate = genome.candidates[0]
    genes = tuple(
        (
            replace(
                gene,
                value=make_a4_patch_value("Filter2 Resonance", screen_target=101),
            )
            if gene.value.parameter == "Filter2 Resonance"
            else gene
        )
        for gene in candidate.genes
    )
    dynamic_genome = replace(
        genome,
        candidates=(replace(candidate, genes=genes), *genome.candidates[1:]),
    )

    plan = build_analog_four_patch_send_plan_from_genome(
        report,
        dynamic_genome,
        selected_candidate=1,
    )

    resonance = next(event for event in plan.send_events if event.parameter == "Filter2 Resonance")
    assert plan.learning_packet.genome is dynamic_genome
    assert resonance.midi_value == 101


def test_audio_source_profiles_change_send_event_dna(monkeypatch: pytest.MonkeyPatch) -> None:
    from rytm_randomizer.style_analysis import analog_four_patch_inference as inference
    from rytm_randomizer.style_analysis.analog_four_patch_inference import (
        AnalogFourPatchAudioFeatures,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan_from_source,
    )
    from rytm_randomizer.style_analysis.extractor import AudioFeatureAnalysis

    profiles = iter(
        (
            AnalogFourPatchAudioFeatures(
                audio_sha256="1" * 64,
                duration=0.2,
                attack=0.02,
                decay=0.18,
                sustain=0.08,
                tail=0.1,
                brightness=0.12,
                spectral_flatness=0.04,
                noise=0.05,
                low_end=0.88,
                harmonicity=0.92,
                transient=0.22,
                modulation=0.06,
            ),
            AnalogFourPatchAudioFeatures(
                audio_sha256="2" * 64,
                duration=0.72,
                attack=0.32,
                decay=0.75,
                sustain=0.62,
                tail=0.78,
                brightness=0.91,
                spectral_flatness=0.84,
                noise=0.86,
                low_end=0.14,
                harmonicity=0.23,
                transient=0.91,
                modulation=0.82,
            ),
        )
    )

    def next_analysis(_path: Path) -> AudioFeatureAnalysis:
        features = next(profiles)
        return AudioFeatureAnalysis(
            feature_report=_reference_report(),
            synthesis_features=features,
        )

    from rytm_randomizer.style_analysis import analog_four_patch_send_plan as send_plan_module

    def next_audio_genome(path: Path, *, track: int):
        return inference._build_analog_four_audio_patch_genome_from_analysis(
            next_analysis(path),
            track=track,
            candidate_count=4,
        )

    monkeypatch.setattr(
        send_plan_module,
        "build_analog_four_audio_patch_genome_isolated",
        next_audio_genome,
    )

    first = build_analog_four_patch_send_plan_from_source("--audio", "first.wav").plan
    second = build_analog_four_patch_send_plan_from_source("--audio", "second.wav").plan
    first_values = {
        gene.value.parameter: gene.value.screen_value
        for gene in first.learning_packet.selected_patch.genes
    }
    second_values = {
        gene.value.parameter: gene.value.screen_value
        for gene in second.learning_packet.selected_patch.genes
    }

    assert first.source_hash == "1" * 64
    assert second.source_hash == "2" * 64
    assert first_values != second_values
    assert first_values["OSC2 Level"] < second_values["OSC2 Level"]
    assert first_values["EnvA Release Time"] < second_values["EnvA Release Time"]


def test_description_source_stays_static_and_invalid_source_is_rejected() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        build_analog_four_patch_send_plan,
        build_analog_four_patch_send_plan_from_source,
    )
    from rytm_randomizer.style_analysis.extractor import extract_from_description

    description = "dark compact metallic stab"
    sourced = build_analog_four_patch_send_plan_from_source(
        "--description",
        description,
        track=2,
        selected_candidate=2,
    )
    direct = build_analog_four_patch_send_plan(
        extract_from_description(description),
        track=2,
        selected_candidate=2,
    )

    assert sourced.source_label == "description"
    assert sourced.source_value == description
    assert sourced.plan.send_events == direct.send_events
    with pytest.raises(ValueError, match="source_flag must be"):
        build_analog_four_patch_send_plan_from_source("--unknown", "value")


def test_patch_send_plan_defensive_helpers_cover_malformed_rows() -> None:
    from rytm_randomizer.data.analog_four_display import (
        TRANSPORT_CC_READY,
        TRANSPORT_NRPN_READY,
        TRANSPORT_SCREEN_ONLY,
        TRANSPORT_SCREEN_ONLY_NRPN,
        AnalogFourPatchValue,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        AnalogFourPatchGene,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        _build_send_summary,
        _message_kind_for,
        _send_event_from_gene,
        _skip_reason,
    )

    missing_midi_value = AnalogFourPatchValue(
        parameter="Malformed CC",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=1,
        cc_lsb=None,
        nrpn_address=None,
        transport_status=TRANSPORT_CC_READY,
        dial_direction="set manually",
    )
    missing_address_value = AnalogFourPatchValue(
        parameter="Malformed address",
        section="TEST",
        encoder="-",
        screen_value="1",
        midi_value=1,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status=TRANSPORT_NRPN_READY,
        dial_direction="set to 1",
    )
    screen_only_value = AnalogFourPatchValue(
        parameter="Screen only",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status=TRANSPORT_SCREEN_ONLY,
        dial_direction="set manually",
    )
    screen_only_nrpn_value = AnalogFourPatchValue(
        parameter="Screen-only NRPN",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=(1, 99),
        transport_status=TRANSPORT_SCREEN_ONLY_NRPN,
        dial_direction="set manually",
    )
    missing_transport_value = AnalogFourPatchValue(
        parameter="Missing transport",
        section="TEST",
        encoder="-",
        screen_value="manual",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status="unknown-ready",
        dial_direction="set manually",
    )

    malformed_gene = AnalogFourPatchGene(
        track=1,
        family="Test",
        value=missing_midi_value,
        rationale="defensive row",
        confidence="test",
    )

    with pytest.raises(ValueError, match="missing a MIDI value"):
        _send_event_from_gene(1, malformed_gene)
    with pytest.raises(ValueError, match="no CC or NRPN address"):
        _message_kind_for(missing_address_value)
    assert _skip_reason(screen_only_nrpn_value) == "NRPN destination ordinal capture pending"
    assert _skip_reason(screen_only_value) == "front-panel-only value pending capture"
    assert _skip_reason(missing_transport_value) == "transport value pending capture"
    assert _skip_reason(missing_address_value) == "transport address pending capture"

    packet = types.SimpleNamespace(
        live_dial_readiness=types.SimpleNamespace(
            blocking_reason="front-panel-only values require manual capture before automation"
        )
    )
    complete = _build_send_summary(
        packet,
        send_events=(
            types.SimpleNamespace(
                message_kind="cc",
                cc_msb=75,
                cc_lsb=None,
                nrpn_address=None,
                midi_value=64,
                channel=0,
            ),
        ),
        manual_events=(),
    )
    assert complete.live_dial_path == "transport-ready"
    assert complete.blocking_reason == "none"

    manual_only = _build_send_summary(
        packet,
        send_events=(),
        manual_events=(types.SimpleNamespace(skip_reason="manual"),),
    )
    assert manual_only.live_dial_path == "manual-only"
    assert (
        manual_only.blocking_reason
        == "front-panel-only values require manual capture before automation"
    )


def test_generic_cc_nrpn_event_sender_sends_and_fails_closed() -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import send_cc_nrpn_event_plan

    sender = MockMidiSender()
    sent_count = send_cc_nrpn_event_plan(
        (
            types.SimpleNamespace(
                message_kind="cc",
                cc_msb=74,
                midi_value=96,
                channel=2,
                nrpn_address=None,
            ),
            types.SimpleNamespace(
                message_kind="nrpn",
                cc_msb=None,
                midi_value=5,
                channel=2,
                nrpn_address=(1, 54),
            ),
        ),
        sender,
        sleep=lambda _seconds: None,
    )

    assert sent_count == 4
    assert [
        (message.channel, message.control, message.value) for message in sender.sent_messages
    ] == [
        (2, 74, 96),
        (2, 99, 1),
        (2, 98, 54),
        (2, 6, 5),
    ]

    with pytest.raises(ValueError, match="unsupported MIDI event kind"):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="sysex",
                    cc_msb=None,
                    midi_value=1,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )
    with pytest.raises(ValueError, match="missing a CC MSB"):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=None,
                    midi_value=1,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )
    with pytest.raises(ValueError, match="missing an NRPN address"):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="nrpn",
                    cc_msb=None,
                    midi_value=1,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )
    with pytest.raises(ValueError, match="exactly two MIDI bytes"):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="nrpn",
                    cc_msb=None,
                    midi_value=1,
                    channel=0,
                    nrpn_address=(1,),
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )

    unsent = MockMidiSender()
    with pytest.raises(ValueError, match="missing a CC MSB"):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=74,
                    midi_value=96,
                    channel=2,
                    nrpn_address=None,
                ),
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=None,
                    midi_value=1,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            unsent,
            sleep=lambda _seconds: None,
        )
    assert unsent.sent_messages == ()


@pytest.mark.parametrize(
    ("event", "expected"),
    (
        (
            types.SimpleNamespace(
                message_kind="cc",
                cc_msb=18,
                cc_lsb=50,
                midi_value=64,
                channel=0,
                nrpn_address=None,
            ),
            "verified CC14 transport",
        ),
        (
            types.SimpleNamespace(
                message_kind="cc",
                cc_msb=74,
                cc_lsb=None,
                midi_value=64,
                channel=0,
                nrpn_address=(1, 2),
            ),
            "must not include an NRPN address",
        ),
        (
            types.SimpleNamespace(
                message_kind="nrpn",
                cc_msb=74,
                cc_lsb=None,
                midi_value=64,
                channel=0,
                nrpn_address=(1, 2),
            ),
            "must not include a CC address",
        ),
    ),
)
def test_generic_midi_event_plan_rejects_ambiguous_or_paired_addresses(
    event: object,
    expected: str,
) -> None:
    from rytm_randomizer.behavior.midi_event_plan import validate_cc_nrpn_event_plan

    with pytest.raises(ValueError, match=expected):
        validate_cc_nrpn_event_plan((event,))  # type: ignore[arg-type]


def test_generic_midi_event_kind_rejects_cc_lsb_without_cc_msb() -> None:
    from rytm_randomizer.behavior.midi_event_plan import midi_event_kind_for_addresses

    with pytest.raises(ValueError, match="CC LSB requires a CC MSB"):
        midi_event_kind_for_addresses(
            cc_msb=None,
            cc_lsb=1,
            nrpn_address=None,
        )


def test_generic_sender_fails_closed_if_validated_nrpn_address_changes() -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import send_cc_nrpn_event_plan

    class MutableNrpnEvent:
        message_kind = "nrpn"
        cc_msb = None
        midi_value = 5
        channel = 0

        def __init__(self) -> None:
            self.read_count = 0

        @property
        def nrpn_address(self):
            self.read_count += 1
            return (1, 54) if self.read_count == 1 else None

    sender = MockMidiSender()
    with pytest.raises(AssertionError, match="lost its address"):
        send_cc_nrpn_event_plan(
            (MutableNrpnEvent(),),
            sender,
            sleep=lambda _seconds: None,
        )
    assert sender.sent_messages == ()


def test_a4_send_plan_uses_neutral_midi_event_kind_vocabulary() -> None:
    from typing import get_args

    from rytm_randomizer.senders.midi_event_plan import (
        MIDI_EVENT_KIND_CC,
        MIDI_EVENT_KIND_NRPN,
        MidiEventKind,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        ANALOG_FOUR_PATCH_SEND_KIND_CC,
        ANALOG_FOUR_PATCH_SEND_KIND_NRPN,
    )

    assert frozenset(get_args(MidiEventKind)) == frozenset({"cc", "nrpn"})
    assert ANALOG_FOUR_PATCH_SEND_KIND_CC == MIDI_EVENT_KIND_CC
    assert ANALOG_FOUR_PATCH_SEND_KIND_NRPN == MIDI_EVENT_KIND_NRPN


@pytest.mark.parametrize(
    ("channel", "midi_value", "error"),
    (
        (True, 64, "event channel must be an integer in 0..127"),
        (0, 128, "event MIDI value must be an integer in 0..127"),
        (16, 64, "event channel must be an integer in 0..15"),
    ),
)
def test_generic_event_sender_rejects_invalid_midi_bytes_before_delivery(
    channel: object,
    midi_value: object,
    error: str,
) -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import send_cc_nrpn_event_plan

    sender = MockMidiSender()
    with pytest.raises(ValueError, match=error.replace("..", r"\.\.")):
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=74,
                    midi_value=midi_value,
                    channel=channel,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )

    assert sender.sent_messages == ()


def test_generic_event_sender_reports_partial_nrpn_delivery() -> None:
    from rytm_randomizer.mock_midi import MidiMessage, MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import (
        MidiEventPlanSendError,
        send_cc_nrpn_event_plan,
    )

    class FailAfterOneMessage(MockMidiSender):
        def send(self, message: object) -> None:
            if self.sent_messages:
                raise OSError("simulated port interruption")
            super().send(message)

    sender = FailAfterOneMessage()
    with pytest.raises(MidiEventPlanSendError) as caught:
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="nrpn",
                    cc_msb=None,
                    midi_value=64,
                    channel=0,
                    nrpn_address=(1, 54),
                ),
            ),
            sender,
            sleep=lambda _seconds: None,
        )

    assert caught.value.sent_message_count == 1
    assert caught.value.expected_message_count == 3
    assert isinstance(caught.value, RuntimeError)
    assert "1 of 3 messages" in str(caught.value)
    assert sender.sent_messages == (MidiMessage("control_change", 0, 99, 1),)


def test_generic_event_sender_counts_delivery_before_pacing_failure() -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import (
        MidiEventPlanSendError,
        send_cc_nrpn_event_plan,
    )

    sender = MockMidiSender()

    def interrupt_pacing(_seconds: float) -> None:
        raise RuntimeError("pacing interrupted")

    with pytest.raises(MidiEventPlanSendError) as caught:
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=74,
                    midi_value=64,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=interrupt_pacing,
        )

    assert caught.value.sent_message_count == 1
    assert caught.value.expected_message_count == 1
    assert len(sender.sent_messages) == 1


@pytest.mark.parametrize("interruption", [KeyboardInterrupt(), SystemExit(7)])
def test_generic_event_sender_wraps_operator_interrupt_with_delivery_count(
    interruption: BaseException,
) -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders.midi_event_plan import (
        MidiEventPlanSendError,
        send_cc_nrpn_event_plan,
    )

    sender = MockMidiSender()

    def interrupt_pacing(_seconds: float) -> None:
        raise interruption

    with pytest.raises(MidiEventPlanSendError) as caught:
        send_cc_nrpn_event_plan(
            (
                types.SimpleNamespace(
                    message_kind="cc",
                    cc_msb=74,
                    midi_value=64,
                    channel=0,
                    nrpn_address=None,
                ),
            ),
            sender,
            sleep=interrupt_pacing,
        )

    assert caught.value.interrupted is True
    assert caught.value.sent_message_count == 1
    assert caught.value.expected_message_count == 1


def test_patch_send_plan_classifies_non_transport_value_with_typed_skip_code() -> None:
    from rytm_randomizer.data.analog_four_display import (
        TRANSPORT_SCREEN_ONLY,
        AnalogFourPatchValue,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        _is_sendable_value,
        _skip_code,
    )

    value = AnalogFourPatchValue(
        parameter="Manual",
        section="TEST",
        encoder="A",
        screen_value="OFF",
        midi_value=None,
        cc_msb=None,
        cc_lsb=None,
        nrpn_address=None,
        transport_status=TRANSPORT_SCREEN_ONLY,
        dial_direction="leave at OFF",
    )

    assert not _is_sendable_value(value)
    assert _skip_code(value) == "not-transport-ready"


def test_generic_event_sender_asserts_if_validated_cc_loses_address(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.mock_midi import MockMidiSender
    from rytm_randomizer.senders import midi_event_plan

    event = types.SimpleNamespace(
        message_kind="cc",
        cc_msb=None,
        midi_value=64,
        channel=0,
        nrpn_address=None,
    )
    monkeypatch.setattr(
        midi_event_plan,
        "_validate_cc_nrpn_event_plan",
        lambda _events: 1,
    )

    with pytest.raises(AssertionError, match="validated CC event lost its address"):
        midi_event_plan.send_cc_nrpn_event_plan(
            (event,),
            MockMidiSender(),
            sleep=lambda _seconds: None,
        )
