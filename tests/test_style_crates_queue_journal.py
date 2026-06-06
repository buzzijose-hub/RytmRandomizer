from __future__ import annotations

import json
import sys
from types import MappingProxyType

import pytest

pytestmark = pytest.mark.fast

FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES = (
    "mido",
    "rtmidi",
    "pythonrtmidi",
    "rytm_randomizer.real_midi_adapter",
)


def test_style_crates_catalog_contains_required_crates_and_bounded_moves() -> None:
    from rytm_randomizer.data.style_crates import STYLE_CRATES

    assert tuple(STYLE_CRATES) == (
        "dark_hypnotic",
        "peak_time",
        "hard_groove",
        "dub_pressure",
        "industrial_broken",
        "deep_minimal",
        "chaos_fills",
        "transitions",
        "saved_accidents",
    )
    assert isinstance(STYLE_CRATES, MappingProxyType)

    for crate in STYLE_CRATES.values():
        assert crate.moves
        for move in crate.moves:
            assert 1 <= move.energy <= 10
            assert 1 <= move.risk <= 10
            assert move.tags
            assert move.target_pads
            assert all(1 <= pad <= 12 for pad in move.target_pads)
            assert move.mode
            assert move.recovery_action
            assert move.notes

    dark_move = STYLE_CRATES["dark_hypnotic"].moves[0]
    assert dark_move.key == "shadow_filter_pressure"
    assert dark_move.energy == 5
    assert dark_move.risk == 3
    assert dark_move.target_pads == (1, 3, 11)


def test_style_queue_references_catalog_and_supports_story_plus_scratchpad() -> None:
    from rytm_randomizer.data.style_crates import DEFAULT_STYLE_QUEUE, STYLE_CRATES

    use_cases = {move.use_case for move in DEFAULT_STYLE_QUEUE}
    assert use_cases == {"set_story", "live_scratchpad"}
    assert {move.status for move in DEFAULT_STYLE_QUEUE} == {"staged", "scratchpad"}

    for queued in DEFAULT_STYLE_QUEUE:
        crate = STYLE_CRATES[queued.crate_key]
        assert any(move.key == queued.move_key for move in crate.moves)
        assert queued.chapter
        assert queued.operator_note
        assert queued.mutation_amount_percent >= 0
        assert all(1 <= pad <= 12 for pad in queued.target_pads)


def test_mutation_journal_entries_are_replayable_metadata_and_immutable() -> None:
    from rytm_randomizer.data.style_crates import DEFAULT_MUTATION_JOURNAL

    entry = DEFAULT_MUTATION_JOURNAL[0]

    assert entry.name == "Warehouse Accident 01"
    assert entry.seed
    assert entry.pads == (1, 3, 11)
    assert entry.depth == "groove"
    assert entry.guardrail_mode == "live_safe"
    assert isinstance(entry.values, MappingProxyType)
    assert entry.values["pad_3_lfo_depth"] == 92
    with pytest.raises(TypeError):
        entry.values["pad_3_lfo_depth"] = 1


def test_future_danger_modes_document_12_pad_direction_without_enabling_hardware() -> None:
    from rytm_randomizer.data.style_crates import DANGER_MODES, FUTURE_DANGER_MODE_LABELS

    assert DANGER_MODES == (
        "live_safe",
        "studio_wild",
        "chaos",
        "one_shot_blast",
        "evolve_mode",
    )
    assert FUTURE_DANGER_MODE_LABELS["studio_wild"] == "Studio Wild"
    assert FUTURE_DANGER_MODE_LABELS["chaos"] == "Chaos"


def test_style_crates_queue_journal_report_formats_text_and_json() -> None:
    from rytm_randomizer.reports.style_crates_queue_journal import (
        build_style_crates_queue_journal_report,
        format_style_crates_queue_journal_report,
        to_style_crates_queue_journal_json,
    )

    report = build_style_crates_queue_journal_report()

    assert report.crate_count == 9
    assert report.move_count >= 9
    assert report.queue_move_count == 4
    assert report.journal_entry_count == 2
    assert isinstance(report.crates_by_key, MappingProxyType)
    assert "no MIDI sending" in report.safety_lines
    assert "dispatch queued move" in report.blocked_actions
    assert report.reference_analyzer_status == "future: not implemented in passive MVP"

    lines = format_style_crates_queue_journal_report(report)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style crates queue journal report"
    assert "Summary:" in lines
    assert "Style Crates:" in lines
    assert "Staged Queue:" in lines
    assert "Mutation Journal:" in lines
    assert "Future Danger Modes:" in lines
    assert "dark_hypnotic: Dark Hypnotic" in text
    assert "industrial_broken: Industrial/Broken" in text
    assert "Warehouse Accident 01" in text
    assert "- no port opening" in lines

    payload = to_style_crates_queue_journal_json(report)
    json.dumps(payload, sort_keys=True)
    model = payload["style_crates_queue_journal"]
    assert model["crate_count"] == 9
    assert model["queue"][0]["use_case"] == "set_story"
    assert model["journal"][0]["guardrail_mode"] == "live_safe"
    assert payload["safety"][0] == "passive/read-only"


def test_style_crates_queue_journal_report_is_deterministic_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.style_crates_queue_journal import (
        build_style_crates_queue_journal_report,
        format_style_crates_queue_journal_report,
    )

    first = format_style_crates_queue_journal_report(build_style_crates_queue_journal_report())
    second = format_style_crates_queue_journal_report(build_style_crates_queue_journal_report())

    assert first == second
    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_style_crates_queue_journal_cli_command_parser_and_handler(capsys) -> None:
    from rytm_randomizer.reports.style_crates_queue_journal import (
        STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND,
    )

    assert STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.args_parser([]) == {"json_output": False}
    assert STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.args_parser(["--json"]) == {"json_output": True}
    with pytest.raises(ValueError, match="style-crates-queue-journal-report"):
        STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.args_parser(["--mutate"])

    assert STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.handler(json_output=False) == 0
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style crates queue journal report" in captured.out
    assert "Style Crates:" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""

    assert STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.handler(json_output=True) == 0
    captured_json = capsys.readouterr()
    assert json.loads(captured_json.out)["style_crates_queue_journal"]["crate_count"] == 9
    assert captured_json.err == ""


def test_style_crates_queue_journal_help_resolves_with_safety_lines() -> None:
    from rytm_randomizer.help_text import resolve_help_text
    from rytm_randomizer.reports.style_crates_queue_journal import SAFETY_LINES

    output = resolve_help_text("style-crates-queue-journal-report")

    assert "RytmRandomizer passive CLI: style-crates-queue-journal-report" in output
    assert "Lists passive Style Crates, staged queue moves, and Mutation Journal entries." in output
    assert output.split("Safety:\n", 1)[1].splitlines() == [f"  {line}" for line in SAFETY_LINES]


def test_style_crates_validation_errors_are_explicit_for_future_catalog_edits() -> None:
    import rytm_randomizer.data.style_crates as style_crates

    base_move = style_crates.StyleCrateMove(
        key="move",
        name="Move",
        summary="Move summary",
        energy=5,
        risk=4,
        tags=("tag",),
        target_pads=(1,),
        mode="live_safe",
        recovery_action="return to anchor",
        notes="notes",
    )
    base_crate = style_crates.StyleCrate(
        key="crate",
        name="Crate",
        summary="Crate summary",
        tags=("tag",),
        moves=(base_move,),
    )

    with pytest.raises(ValueError, match="must not be blank"):
        style_crates._validate_nonblank(" ", field="crate key")
    with pytest.raises(ValueError, match="requires at least one"):
        style_crates._validate_pads("move", ())
    with pytest.raises(ValueError, match="invalid 1-12"):
        style_crates._validate_pads("move", (13,))
    with pytest.raises(ValueError, match="energy must be in 1..10"):
        style_crates._validate_score("move", field="energy", value=0)
    with pytest.raises(ValueError, match="duplicate style crate key"):
        style_crates._validated_crates((base_crate, base_crate))
    with pytest.raises(ValueError, match="duplicate move key"):
        style_crates._validated_crates(
            (
                style_crates.StyleCrate(
                    key="crate",
                    name="Crate",
                    summary="Crate summary",
                    tags=("tag",),
                    moves=(base_move, base_move),
                ),
            )
        )

    with pytest.raises(ValueError, match="order must be >= 1"):
        style_crates._validated_queue(
            (
                style_crates.StyleQueueMove(
                    key="bad_order",
                    order=0,
                    crate_key="dark_hypnotic",
                    move_key="shadow_filter_pressure",
                    chapter="chapter",
                    use_case="set_story",
                    status="staged",
                    mutation_amount_percent=40,
                    target_pads=(1,),
                    operator_note="note",
                ),
            )
        )
    with pytest.raises(ValueError, match="references unknown crate"):
        style_crates._validated_queue(
            (
                style_crates.StyleQueueMove(
                    key="bad_crate",
                    order=1,
                    crate_key="unknown",
                    move_key="shadow_filter_pressure",
                    chapter="chapter",
                    use_case="set_story",
                    status="staged",
                    mutation_amount_percent=40,
                    target_pads=(1,),
                    operator_note="note",
                ),
            )
        )
    with pytest.raises(ValueError, match="references unknown move"):
        style_crates._validated_queue(
            (
                style_crates.StyleQueueMove(
                    key="bad_move",
                    order=1,
                    crate_key="dark_hypnotic",
                    move_key="unknown",
                    chapter="chapter",
                    use_case="set_story",
                    status="staged",
                    mutation_amount_percent=40,
                    target_pads=(1,),
                    operator_note="note",
                ),
            )
        )
    with pytest.raises(ValueError, match="mutation_amount_percent"):
        style_crates._validated_queue(
            (
                style_crates.StyleQueueMove(
                    key="bad_amount",
                    order=1,
                    crate_key="dark_hypnotic",
                    move_key="shadow_filter_pressure",
                    chapter="chapter",
                    use_case="set_story",
                    status="staged",
                    mutation_amount_percent=101,
                    target_pads=(1,),
                    operator_note="note",
                ),
            )
        )
    with pytest.raises(ValueError, match="known danger mode"):
        style_crates._validated_journal(
            (
                style_crates.MutationJournalEntry(
                    key="entry",
                    name="Entry",
                    tags=("tag",),
                    seed="seed",
                    pads=(1,),
                    values={"cc_17": 64},
                    depth="micro",
                    guardrail_mode="unknown",
                    notes="notes",
                ),
            )
        )


def test_style_crates_report_lookup_errors_and_json_handler_edge(capsys) -> None:
    import rytm_randomizer.reports.style_crates_queue_journal as report_module
    from rytm_randomizer.data.style_crates import StyleCrate, StyleCrateMove

    first = StyleCrateMove(
        key="first",
        name="First",
        summary="First summary",
        energy=1,
        risk=1,
        tags=("tag",),
        target_pads=(1,),
        mode="live_safe",
        recovery_action="return",
        notes="notes",
    )
    second = StyleCrateMove(
        key="second",
        name="Second",
        summary="Second summary",
        energy=2,
        risk=2,
        tags=("tag",),
        target_pads=(2,),
        mode="live_safe",
        recovery_action="return",
        notes="notes",
    )
    crate = StyleCrate(
        key="crate",
        name="Crate",
        summary="Crate summary",
        tags=("tag",),
        moves=(first, second),
    )

    assert report_module._move_by_key(crate, "second") is second
    with pytest.raises(KeyError, match="unknown move"):
        report_module._move_by_key(crate, "missing")

    assert report_module.STYLE_CRATES_QUEUE_JOURNAL_CLI_COMMAND.handler(json_output=True) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["style_crates_queue_journal"]["journal_entry_count"] == 2
