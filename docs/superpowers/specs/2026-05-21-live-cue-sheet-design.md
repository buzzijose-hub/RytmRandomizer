# Live Cue Sheet Design

## Goal

Add a passive live cue sheet that turns the selected reference performance arc live render bundle into an operator-ready run sheet for rehearsal and future live-show workflows. The sheet should answer, segment by segment: which machines are involved, what to listen for, how risky the cue is, what hand move to make, and how to recover.

## Scope

Add one passive CLI report:

```text
style-performance-arc-live-cue-sheet-report
```

The command builds on the existing style-performance arc readiness, audition packet, rehearsal manifest, live-session packet, and live render bundle reports. It does not render to a real MIDI port, open ports, execute shell commands, write SysEx, or mutate connected hardware.

## Behavior

The report accepts the same saved-kit-bank and arc-planning options as the live render bundle:

```text
style-performance-arc-live-cue-sheet-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
```

With no arc keys, it evaluates the curated reference arcs and selects the best ranked ready or partial arc. With arc keys, it limits selection to those arcs.

The text report emits:

- Cue sheet summary: scope, duration, cue count, readiness totals, event rows, and deferred rows.
- Selected arc metadata and replayable passive commands.
- Preflight cues derived from the live-session packet launch checklist.
- Performance cues: time window, style key, machine focus, readiness, risk label, hands-on move, listen-for cue, go/no-go cue, recovery action, machine summaries, and render row counts.
- Stage packet: compact show-day cue cards with selected arc, scope, readiness, planned pads/tracks, risk labels, hands-on moves, listening targets, recovery actions, and mock/deferred row totals.
- Optional capped mock render row previews per segment.
- Recovery cues deduplicated across the selected segments.
- Safety block with explicit passive/read-only language.

The JSON report emits deterministic data for future GUI/audio-analyzer/live-workflow surfaces:

- selected readiness metadata
- embedded live render bundle JSON
- cue sheet scope, timing, suggested commands, preflight cues, recovery cues, totals, and cues
- safety lines

## Data Model

Add frozen dataclasses in `rytm_randomizer/reports/style_performance_arcs.py`:

- `StylePerformanceArcLiveCue`: wraps a live render segment with operator-facing machine focus, risk level, hands-on move, and recovery action.
- `StylePerformanceArcStageCard`: a compact per-cue handoff row for show-day operation.
- `StylePerformanceArcStagePacket`: the selected-arc handoff packet for the live cue sheet and reference-match report.
- `StylePerformanceArcLiveCueSheetReport`: wraps the selected live render bundle with suggested commands, preflight cues, recovery cues, and generated cues.

## Safety

The new safety block must include:

- passive/read-only
- live cue sheet
- operator cue sheet only
- uses live render bundle mock rows
- existing saved-kit snapshots only
- metadata and plan expansion only
- no real MIDI rendering
- no MIDI sending
- no port opening
- no command execution
- no hardware mutation
- no hardware required

## Non-Goals

- No real MIDI send path.
- No active `--arm` command.
- No continuous live snapshot tracking.
- No SysEx writes back to the machines.
- No audio analysis or stem analysis in this PR.
- No changes to V1.34 engine/group/scene parity.

## Testing

Use TDD:

1. Add failing builder/formatter/JSON cue-sheet tests.
2. Add failing parser/handler and CLI/help tests.
3. Add passive real-MIDI safety coverage for the new command.
4. Implement the additive report.
5. Update help, README, style docs, status, architecture references, CLI help fixture, and PR plan.
6. Run focused tests, architecture tests, fast/full suite, coverage, lint, vulture, and review gate before push.
