# Style Crate Rehearsal Deck Design

## Goal

Move the merged Style Crates, Style Queue, and Mutation Journal passive MVP one
step closer to the desktop cockpit without touching the desktop UI or hardware
runtime. The system should render the crate catalog, staged queue, and journal
entries as GUI-ready rehearsal cards that can be consumed later by a crate
browser or live queue panel.

## Scope

The first slice is a passive report and CLI command:

- `style-crate-rehearsal-deck-report`
- optional `--crate <key>` filter
- optional `--json` output

The report consumes only existing immutable metadata from
`rytm_randomizer/data/style_crates.py`. It does not persist a journal, execute a
queue, run the analyzer, launch the GUI, open MIDI ports, or send MIDI.

## Model

The deck has three GUI-facing card groups:

- Crate cards: crate identity, summary, tags, primary move, energy, risk, target
  pads, and an operator action.
- Queue rehearsal cards: staged move identity, chapter, status, mutation amount,
  target pads, dry-run-only marker, recovery action, and risk status.
- Journal replay cards: journal key, name, replay seed, pads, value summary,
  depth, guardrail mode, risk status, and an operator action.

Risk labels are deterministic and conservative:

- move risk 1-3: `safe`
- move risk 4-6: `review-ready`
- move risk 7-10: `high-risk`
- journal `live_safe`: `safe`
- journal `studio_wild`: `studio-only`
- other future guardrails: `explicit-opt-in`

## Architecture

Implementation lives in `rytm_randomizer/reports/style_crate_rehearsal_deck.py`
as a passive report module with frozen dataclasses and JSON-ready TypedDicts.
The command is registered through the existing `CliCommand` pattern and is added
to `cli.py`'s lazy-command manifest. Help text stays in `help_text.py`.

Docs are updated in `docs/CLI_REFERENCE.md`, `README.md`, and `docs/STATUS.md`.
No new top-level package module is added.

## Testing

Tests cover:

- default deck counts and risk classification
- single-crate filtering and validation errors
- deterministic text/JSON output
- forbidden real-MIDI import safety
- CLI parser and handler behavior
- help text safety lines

Full verification should include focused tests, CLI tests around help/usage,
architecture gates, and the repo's mechanical review gate.
