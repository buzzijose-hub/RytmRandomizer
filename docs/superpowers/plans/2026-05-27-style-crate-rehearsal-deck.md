# Style Crate Rehearsal Deck Plan

## Objective

Add a passive GUI-ready rehearsal deck that turns existing Style Crates, staged
queue moves, and Mutation Journal entries into deterministic crate, queue, and
journal cards.

## Constraints

- No MIDI port opening or MIDI sends.
- No GUI launch.
- No analyzer invocation.
- No journal persistence writes.
- No hardware behavior change.
- Preserve V1.34 parity fixtures.
- Keep work under `rytm_randomizer/reports/` and existing CLI/help patterns.

## Implementation Steps

1. Add failing tests in `tests/test_style_crate_rehearsal_deck.py` for the
   default deck, crate filtering, deterministic passive behavior, CLI handling,
   and help text.
2. Add `rytm_randomizer/reports/style_crate_rehearsal_deck.py` with frozen
   dataclasses, JSON conversion, text formatting, CLI parsing, and `CliCommand`
   registration.
3. Register the command in `rytm_randomizer/cli.py`.
4. Add help text in `rytm_randomizer/help_text.py`.
5. Update operator docs and status:
   - `README.md`
   - `docs/CLI_REFERENCE.md`
   - `docs/STATUS.md`
6. Refresh affected CLI help expectations if the top-level help fixture changes.
7. Verify with focused tests, CLI integration tests, architecture tests, lint,
   and the mechanical review gate.

## Verification Targets

```bash
python -m pytest tests/test_style_crate_rehearsal_deck.py -n 0 -q
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0 -q
python -m pytest tests/architecture/ -q
python scripts/code_review_gate.py --mode cli
```

## Safety Result

The command emits text/JSON only. It exposes blocked actions for queue firing,
journal replay, GUI launch, MIDI port opening, MIDI sending, and hardware
mutation.
