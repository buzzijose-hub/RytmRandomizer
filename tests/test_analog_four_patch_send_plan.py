"""Tests for passive Analog Four patch send-plan compilation."""

from __future__ import annotations

import json
import types

import pytest

from rytm_randomizer.guardrails.schema import Confidence, SourceType
from rytm_randomizer.style_analysis import FeatureReport

pytestmark = pytest.mark.fast


def _reference_report() -> FeatureReport:
    return FeatureReport(
        source_type=SourceType.SINGLE_TRACK,
        confidence=Confidence.HIGH,
        bpm=134.0,
        tempo_stability=0.91,
        kick_density=0.48,
        percussion_density=0.78,
        low_end_weight=0.42,
        spectral_brightness=0.63,
        texture_noise=0.34,
        energy_arc=(0.18, 0.34, 0.48, 0.72, 0.84, 0.78, 0.61, 0.4),
        content_hash="",
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
    assert plan.summary.sendable_count == 34
    assert plan.summary.manual_count == 5
    assert plan.summary.cc_event_count == 29
    assert plan.summary.nrpn_event_count == 5
    assert plan.summary.transport_message_count == 44
    assert plan.summary.live_dial_path == "partial-live-dial-ready"

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

    manual_parameters = {event.parameter for event in plan.manual_events}
    assert manual_parameters == {
        "EnvF Gate Length",
        "EnvF Destination A",
        "EnvF Destination B",
        "LFO1 Destination A",
        "LFO1 Destination B",
    }
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
    assert payload["learning_packet"]["selected_patch"]["label"] == "Noisy texture"
    assert json.dumps(payload, sort_keys=True) == json.dumps(
        analog_four_patch_send_plan_to_dict(plan),
        sort_keys=True,
    )
    assert payload["ready"] is True
    assert payload["readiness_reason"] == ""


def test_patch_send_plan_rejects_wrong_types_and_candidate_range() -> None:
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
        analog_four_patch_send_plan_to_dict,
        build_analog_four_patch_send_plan,
    )

    with pytest.raises(TypeError, match="report must be"):
        build_analog_four_patch_send_plan(object())  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="plan must be"):
        analog_four_patch_send_plan_to_dict(object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="candidate must be in"):
        build_analog_four_patch_send_plan(_reference_report(), selected_candidate=0)


def test_patch_send_plan_defensive_helpers_cover_malformed_rows() -> None:
    from rytm_randomizer.data.analog_four_display import (
        TRANSPORT_CC_READY,
        TRANSPORT_NRPN_READY,
        TRANSPORT_SCREEN_ONLY,
        AnalogFourPatchValue,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_genome import (
        AnalogFourPatchGene,
    )
    from rytm_randomizer.style_analysis.analog_four_patch_send_plan import (
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
    assert _skip_reason(screen_only_value) == "front-panel-only value pending capture"
    assert _skip_reason(missing_transport_value) == "transport value pending capture"
    assert _skip_reason(missing_address_value) == "transport address pending capture"


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
