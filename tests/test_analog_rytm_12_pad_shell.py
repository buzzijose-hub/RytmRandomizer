"""Tests for the all-12-pad Analog Rytm interactive mutation shell."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.fast

from rytm_randomizer.data.analog_rytm_style_recipes import (
    ANALOG_RYTM_STYLE_RECIPES,
    AnalogRytmRenderedStyleEvent,
    render_analog_rytm_style_recipe,
)
from rytm_randomizer.engines.analog_rytm_12_pad_shell import (
    ANALOG_RYTM_12_PAD_MUTATIONS,
    AnalogRytm12PadShell,
    format_12_pad_preview,
    mutate_12_pad_events,
)
from rytm_randomizer.mock_midi import MockMidiSender


def _events_by_pad(
    events: tuple[AnalogRytmRenderedStyleEvent, ...],
) -> dict[int, tuple[AnalogRytmRenderedStyleEvent, ...]]:
    return {pad: tuple(event for event in events if event.pad == pad) for pad in range(1, 13)}


def _changed_pads(
    before: tuple[AnalogRytmRenderedStyleEvent, ...],
    after: tuple[AnalogRytmRenderedStyleEvent, ...],
) -> set[int]:
    return {
        old.pad
        for old, new in zip(before, after, strict=True)
        if old.parameter != "Track Machine Type" and old.value != new.value
    }


def _event(
    *,
    pad: int = 1,
    machine_key: str = "bd_hard",
    section: str = "AMP",
    parameter: str = "Amp Pan",
    value: int = 64,
) -> AnalogRytmRenderedStyleEvent:
    return AnalogRytmRenderedStyleEvent(
        pad=pad,
        channel=pad - 1,
        machine_key=machine_key,
        section=section,
        parameter=parameter,
        cc_msb=10,
        value=value,
        risk="safe",
        mutation_status="validated_runtime",
        source="manual",
        intent="coverage probe",
    )


def test_12_pad_shell_loads_style_without_sending_midi() -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)

    assert shell.dispatch("load detroit-deep") is True

    assert shell.state.style_name == "detroit-deep"
    assert shell.state.style_label == "Detroit Deep"
    assert shell.state.mutation_name == "anchor"
    assert {event.pad for event in shell.state.current_events} == set(range(1, 13))
    assert len(sender.sent_messages) == 0


def test_12_pad_shell_preview_reports_full_current_plan(capsys) -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)
    shell.dispatch("load detroit-deep")
    shell.dispatch("roll")

    shell.dispatch("preview")
    captured = capsys.readouterr()

    assert "RytmRandomizer 12-pad shell preview" in captured.out
    assert "style: Detroit Deep" in captured.out
    assert "mutation: rolling" in captured.out
    assert "pads: 12" in captured.out
    assert "event count:" in captured.out
    assert "Pad 01 bd_hard" in captured.out
    assert "Pad 12 cb_classic" in captured.out
    assert captured.err == ""


def test_format_12_pad_preview_is_pure_and_deterministic() -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)
    shell.dispatch("load detroit-deep")

    first = format_12_pad_preview(shell.state)
    second = format_12_pad_preview(shell.state)

    assert first == second
    assert "mutation: anchor" in first
    assert "sent messages: 0" in first


@pytest.mark.parametrize("mutation_name", tuple(sorted(ANALOG_RYTM_12_PAD_MUTATIONS)))
def test_12_pad_mutations_change_every_pad_and_keep_kick_filters_safe(
    mutation_name: str,
) -> None:
    before = render_analog_rytm_style_recipe(ANALOG_RYTM_STYLE_RECIPES["detroit-deep"])

    after = mutate_12_pad_events(before, mutation_name)

    assert len(after) == len(before)
    assert _changed_pads(before, after) == set(range(1, 13))
    for pad_events in _events_by_pad(after).values():
        for event in pad_events:
            assert 0 <= event.value <= 127
            if (
                event.machine_key.startswith("bd_")
                and event.section == "FILTER"
                and event.parameter == "Filter Frequency"
            ):
                assert event.value <= 32


def test_12_pad_shell_send_writes_current_plan_to_sender() -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)
    shell.dispatch("load detroit-deep")
    shell.dispatch("deep")

    assert shell.dispatch("send") is True

    assert len(sender.sent_messages) == len(shell.state.current_events)
    assert {message.channel for message in sender.sent_messages} == set(range(12))
    assert sender.sent_messages[0].control == 15


def test_12_pad_shell_undo_restores_previous_plan() -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)
    shell.dispatch("load detroit-deep")
    anchor = shell.state.current_events
    shell.dispatch("grit")

    assert shell.state.current_events != anchor
    assert shell.dispatch("undo") is True

    assert shell.state.current_events == anchor
    assert shell.state.mutation_name == "undo"


def test_12_pad_shell_reset_restores_loaded_anchor() -> None:
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender)
    shell.dispatch("load detroit-deep")
    anchor = shell.state.current_events
    shell.dispatch("warehouse")

    assert shell.state.current_events != anchor
    assert shell.dispatch("reset") is True

    assert shell.state.current_events == anchor
    assert shell.state.mutation_name == "anchor"


def test_12_pad_shell_run_accepts_scripted_commands(capsys) -> None:
    commands = iter(["load detroit-deep", "roll", "send", "q"])
    sender = MockMidiSender()
    shell = AnalogRytm12PadShell(sender, input_func=lambda _prompt="": next(commands))

    exit_code = shell.run()
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "RytmRandomizer 12-pad shell" in captured.out
    assert "loaded: Detroit Deep" in captured.out
    assert "mutation applied: rolling" in captured.out
    assert "sent current 12-pad plan" in captured.out
    assert len(sender.sent_messages) == len(shell.state.current_events)


def test_12_pad_role_and_parameter_family_edges() -> None:
    from rytm_randomizer.engines import analog_rytm_12_pad_shell as shellmod

    assert shellmod.classify_rytm_pad_role("sy_raw") == "synth"
    assert shellmod.classify_rytm_pad_role("dual_vco") == "synth"
    assert shellmod.classify_rytm_pad_role("ut_noise") == "utility"
    assert shellmod.classify_rytm_pad_role("fx_track") == "percussion"

    assert shellmod._twelve_pad_parameter_family("FM Amount") == "drive"
    assert shellmod._twelve_pad_parameter_family("Snap Amount") == "transient"


def test_12_pad_mutation_preserves_and_falls_back_for_edge_values() -> None:
    events = (
        _event(parameter="Track Machine Type", value=0),
        _event(parameter="Amp Pan", value=127),
    )

    mutated = mutate_12_pad_events(events, "rolling")

    assert mutated[0] == events[0]
    assert mutated[1].value == 126
    assert mutated[1].intent == "rolling: role fallback"


def test_12_pad_kick_filter_fallback_preserves_sub_weight() -> None:
    events = (
        _event(
            section="FILTER",
            parameter="Filter Frequency",
            value=100,
        ),
    )

    mutated = mutate_12_pad_events(events, "warehouse")

    assert mutated[0].value <= 32
    assert "preserve kick sub weight" in mutated[0].intent


def test_12_pad_shell_unloaded_and_misc_dispatch_edges(capsys) -> None:
    shell = AnalogRytm12PadShell(MockMidiSender())

    assert shell.dispatch("") is True
    assert shell.dispatch("send") is True
    assert shell.dispatch("undo") is True
    assert shell.dispatch("reset") is True
    assert shell.dispatch("help") is True
    assert shell.dispatch("styles") is True
    assert shell.dispatch("load") is True
    assert shell.dispatch("unknown") is True

    captured = capsys.readouterr()
    assert "load a 12-pad style first" in captured.out
    assert "available 12-pad styles:" in captured.out
    assert "load requires a style name" in captured.out
    assert "unknown 12-pad command: unknown" in captured.out
