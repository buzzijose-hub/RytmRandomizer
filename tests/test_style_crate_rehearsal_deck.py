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


def test_style_crate_rehearsal_deck_builds_gui_ready_cards() -> None:
    from rytm_randomizer.reports.style_crate_rehearsal_deck import (
        build_style_crate_rehearsal_deck,
        format_style_crate_rehearsal_deck,
        to_style_crate_rehearsal_deck_json,
    )

    deck = build_style_crate_rehearsal_deck()

    assert deck.deck_version == "style-crate-rehearsal-deck-v1"
    assert deck.crate_filter == "all"
    assert deck.deck_status == "passive-ready"
    assert len(deck.deck_id) == 16
    assert len(deck.crate_cards) == 9
    assert len(deck.queue_cards) == 4
    assert len(deck.journal_cards) == 2
    assert isinstance(deck.crates_by_key, MappingProxyType)
    assert deck.crate_cards[0].crate_key == "dark_hypnotic"
    assert deck.crate_cards[0].primary_move_key == "shadow_filter_pressure"
    assert deck.crate_cards[0].risk_status == "safe"
    assert deck.queue_cards[2].queue_key == "queue-peak-metal"
    assert deck.queue_cards[2].risk_status == "high-risk"
    assert deck.queue_cards[2].operator_action == (
        "Stage recovery first; keep this move in dry-run review."
    )
    assert deck.journal_cards[0].replay_seed == "style-journal-warehouse-0001"
    assert deck.journal_cards[1].risk_status == "studio-only"
    assert "fire queued style move" in deck.blocked_actions
    assert "no MIDI sending" in deck.safety_lines
    assert deck.replay_commands == (
        "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report",
        "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report --json",
    )

    lines = format_style_crate_rehearsal_deck(deck)
    text = "\n".join(lines)
    assert lines[0] == "RytmRandomizer passive style crate rehearsal deck"
    assert "Deck summary:" in lines
    assert "Crate cards:" in lines
    assert "Queue rehearsal cards:" in lines
    assert "Journal replay cards:" in lines
    assert "industrial_broken: Industrial/Broken | risk=high-risk | energy=8/10" in text
    assert "queue-peak-metal -> Broken Metal Stress | high-risk" in text
    assert "broken_fill_seed_02: Broken Fill Seed 02 | studio-only" in text
    assert "- no port opening" in lines

    payload = to_style_crate_rehearsal_deck_json(deck)
    model = payload["style_crate_rehearsal_deck"]
    assert model["crate_filter"] == "all"
    assert model["queue_cards"][2]["risk_status"] == "high-risk"
    assert model["journal_cards"][0]["replay_seed"] == "style-journal-warehouse-0001"
    json.dumps(payload, sort_keys=True)


def test_style_crate_rehearsal_deck_filters_one_crate_and_keeps_replay_command() -> None:
    from rytm_randomizer.reports.style_crate_rehearsal_deck import (
        build_style_crate_rehearsal_deck,
    )

    deck = build_style_crate_rehearsal_deck(crate_key="industrial_broken")

    assert deck.crate_filter == "industrial_broken"
    assert [card.crate_key for card in deck.crate_cards] == ["industrial_broken"]
    assert [card.queue_key for card in deck.queue_cards] == ["queue-peak-metal"]
    assert deck.journal_cards == ()
    assert deck.replay_commands == (
        "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report "
        "--crate industrial_broken",
        "python -m rytm_randomizer.cli style-crate-rehearsal-deck-report "
        "--crate industrial_broken --json",
    )

    with pytest.raises(ValueError, match="unknown style crate"):
        build_style_crate_rehearsal_deck(crate_key="missing")

    with pytest.raises(ValueError, match="crate_key"):
        build_style_crate_rehearsal_deck(crate_key=" ")


def test_style_crate_rehearsal_deck_marks_explicit_opt_in_journal_entries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.data.style_crates import MutationJournalEntry
    from rytm_randomizer.reports import style_crate_rehearsal_deck as report

    entry = MutationJournalEntry(
        key="chaos-memory",
        name="Chaos Memory",
        tags=("chaos", "review"),
        seed="style-journal-chaos-0001",
        pads=(1, 7, 12),
        values={"drive": 118, "motion": 121},
        depth="strong",
        guardrail_mode="chaos",
        notes="Explicit opt-in replay seed for future studio review.",
    )
    monkeypatch.setattr(report, "DEFAULT_MUTATION_JOURNAL", (entry,))

    deck = report.build_style_crate_rehearsal_deck()

    assert deck.journal_cards[0].risk_status == "explicit-opt-in"
    assert deck.journal_cards[0].operator_action == (
        "Requires explicit future opt-in before replay."
    )


def test_style_crate_rehearsal_deck_rejects_stale_queue_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from rytm_randomizer.data.style_crates import StyleQueueMove
    from rytm_randomizer.reports import style_crate_rehearsal_deck as report

    queued = StyleQueueMove(
        key="queue-stale-move",
        use_case="set_story",
        chapter="chapter-stale",
        order=1,
        crate_key="dark_hypnotic",
        move_key="missing-move",
        status="staged",
        mutation_amount_percent=25,
        target_pads=(1, 3),
        operator_note="Should fail before a stale move can become a card.",
    )
    monkeypatch.setattr(report, "DEFAULT_STYLE_QUEUE", (queued,))

    with pytest.raises(KeyError, match="unknown move"):
        report.build_style_crate_rehearsal_deck(crate_key="dark_hypnotic")


def test_style_crate_rehearsal_deck_is_deterministic_and_passive() -> None:
    before_modules = set(sys.modules)

    from rytm_randomizer.reports.style_crate_rehearsal_deck import (
        build_style_crate_rehearsal_deck,
        format_style_crate_rehearsal_deck,
    )

    first = format_style_crate_rehearsal_deck(build_style_crate_rehearsal_deck())
    second = format_style_crate_rehearsal_deck(build_style_crate_rehearsal_deck())

    assert first == second
    imported_modules = set(sys.modules) - before_modules
    assert not (set(FORBIDDEN_REAL_MIDI_AND_ADAPTER_MODULES) & imported_modules)


def test_style_crate_rehearsal_deck_cli_parser_and_handler(capsys) -> None:
    from rytm_randomizer.reports.style_crate_rehearsal_deck import (
        STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND,
    )

    assert STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.args_parser([]) == {
        "crate_key": None,
        "json_output": False,
    }
    assert STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.args_parser(["--json"]) == {
        "crate_key": None,
        "json_output": True,
    }
    assert STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.args_parser(
        ["--crate", "industrial_broken", "--json"]
    ) == {"crate_key": "industrial_broken", "json_output": True}
    with pytest.raises(ValueError, match="--crate requires"):
        STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.args_parser(["--crate"])
    with pytest.raises(ValueError, match="style-crate-rehearsal-deck-report"):
        STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.args_parser(["--mutate"])

    assert (
        STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.handler(
            crate_key="industrial_broken",
            json_output=False,
        )
        == 0
    )
    captured = capsys.readouterr()
    assert "RytmRandomizer passive style crate rehearsal deck" in captured.out
    assert "industrial_broken: Industrial/Broken" in captured.out
    assert "- no MIDI sending" in captured.out
    assert captured.err == ""

    assert (
        STYLE_CRATE_REHEARSAL_DECK_CLI_COMMAND.handler(
            crate_key=None,
            json_output=True,
        )
        == 0
    )
    captured_json = capsys.readouterr()
    assert (
        json.loads(captured_json.out)["style_crate_rehearsal_deck"]["deck_status"]
        == "passive-ready"
    )
    assert captured_json.err == ""


def test_style_crate_rehearsal_deck_help_resolves_with_safety_lines() -> None:
    from rytm_randomizer.help_text import resolve_help_text
    from rytm_randomizer.reports.style_crate_rehearsal_deck import SAFETY_LINES

    output = resolve_help_text("style-crate-rehearsal-deck-report")

    assert "RytmRandomizer passive CLI: style-crate-rehearsal-deck-report" in output
    assert "Builds passive GUI-ready crate, queue, and journal rehearsal cards." in output
    assert output.split("Safety:\n", 1)[1].splitlines() == [f"  {line}" for line in SAFETY_LINES]
