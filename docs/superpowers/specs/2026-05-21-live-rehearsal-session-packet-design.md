# Live Rehearsal Session Packet Design

## Goal

Build a passive operator packet that turns the selected reference-arc rehearsal manifest into a live-session checklist Jose can use before studio or show testing. The packet must answer: what arc did the software pick, what should be loaded, what segment comes next, what should Jose listen for, when should he reset or abort, and what passive command can be rerun to inspect the same material.

## Scope

Add one passive CLI report:

```text
style-performance-arc-live-session-packet-report
```

The command reuses the merged rehearsal manifest builder. It does not choose new kits, decode new SysEx offsets, render armed MIDI, open ports, or mutate hardware. It packages the existing manifest into a more live-operator-focused view.

## Behavior

With saved Rytm and optional Analog Four kit banks, the command evaluates the same reference arcs as the readiness/audition/rehearsal flow, selects the requested ranked arc, and emits:

- Session summary: scope, selected arc, duration, segment count, readiness totals, and selected rank.
- Launch checklist: saved-bank confirmation, passive-only warning, segment-by-segment rehearsal advice, reset advice, and one-machine scope reminder.
- Suggested passive commands: rerun the manifest, rerun the audition packet, rerun the readiness matrix, and rerun the selected set-plan preview.
- Segment cards: time window, style key, discovery amount, discovery band, mutation depth, readiness, listen-for guidance, go/no-go cue, reset cue, Rytm preview, Analog Four preview, and row counts.
- Optional mock event rows using the existing set-plan event preview extraction.
- Deterministic JSON for future GUI/audio-analyzer use.

## CLI Shape

The command mirrors `style-performance-arc-rehearsal-manifest-report` options:

```text
style-performance-arc-live-session-packet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
```

`--events` and `--limit` remain passive and show capped mock event rows only. `--json` returns deterministic packet data and does not print prose.

## Data Model

Add two frozen dataclasses in `rytm_randomizer/reports/style_performance_arcs.py`:

- `StylePerformanceArcLiveSessionSegment`: one operator card derived from a rehearsal segment.
- `StylePerformanceArcLiveSessionPacketReport`: the selected rehearsal manifest plus launch checklist, suggested commands, and segment cards.

Each segment card stores derived text fields instead of recomputing them in the formatter. This keeps JSON and text output aligned.

## Guidance Rules

The packet uses deterministic text derived from existing fields:

- `reference-close` or low discovery: listen for subtle variation while preserving the loaded kit identity.
- `balanced` discovery: listen for useful groove movement and tonal pressure without losing the segment role.
- `wide`, `wild`, or high discovery: listen for surprise, edge, and whether the machine still supports the live set.
- Ready segments are marked as auditionable.
- Partial segments are marked as rehearse carefully.
- Blocked segments are marked as planning-only until better saved kit material exists.

Exact labels come from the existing discovery band/depth/readiness strings so the packet remains deterministic and does not need audio analysis yet.

## Safety

The report safety block must include:

- passive/read-only
- live rehearsal session packet
- operator checklist only
- metadata and plan expansion only
- no MIDI sending
- no port opening
- no command execution
- no hardware mutation
- no hardware required

## Architecture

This remains in `reports.style_performance_arcs` because it is a projection over the already selected reference arc. It should not create a new root module, new device package, or new strategy. CLI registration follows the lazy command pattern in `rytm_randomizer/cli.py`, help text lives in `rytm_randomizer/help_text.py`, and tests extend `tests/test_style_performance_arcs_report.py`.

## Testing

Use TDD:

1. Write a failing builder/formatter/JSON test.
2. Write failing parser/handler and CLI/help tests.
3. Implement the report.
4. Run focused tests and then the full verification gate before commit/push.

Required focused tests:

```bash
python -m pytest tests/test_style_performance_arcs_report.py -n 0
python -m pytest tests/test_cli.py tests/test_cli_coverage.py tests/test_real_midi_passive_cli_safety.py -n 0
```

Required closeout:

```bash
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m pytest --cov=rytm_randomizer --cov-branch --cov-report=term-missing
python scripts\code_review_gate.py --mode cli
```

## Rollback

Revert the PR commit. The feature is additive and passive, so rollback removes the command, tests, and docs without affecting existing reports or runtime behavior.
