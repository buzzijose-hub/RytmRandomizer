# Live Render Bundle Design

## Goal

Add a passive live render bundle that turns the selected reference performance arc into a rehearsal-ready mock-render packet. The bundle should let Jose inspect, in one place, which segment is coming, which Rytm pads and Analog Four tracks are planned, how many mock rows would render, which A4 rows remain deferred, and which replayable passive commands can reproduce the same preview.

## Scope

Add one passive CLI report:

```text
style-performance-arc-live-render-bundle-report
```

The command builds on the existing reference arc readiness, audition packet, rehearsal manifest, live-session packet, and dual-machine style performance set-plan reports. It does not render to a real MIDI port, does not open ports, does not execute shell commands, and does not mutate connected hardware.

## Behavior

The report accepts the same saved-kit-bank and arc-planning options as the live-session packet:

```text
style-performance-arc-live-render-bundle-report [<arc-key> ...] --rytm <syx-path> [--analog-four <syx-path>] [--scope dual|rytm-only|analog-four-only|a4-only] [--rank N] [--total-minutes N] [--segment-minutes N] [--discovery-start N] [--discovery-end N] [--events] [--limit N] [--json]
```

With no arc keys, it evaluates the curated reference arcs and selects the best ranked ready or partial arc. With arc keys, it limits selection to those arcs.

The text report emits:

- Bundle summary: scope, selected arc, duration, selected rank, readiness totals, event rows, mock messages, and deferred rows.
- Replayable passive commands: live render bundle, live session packet, rehearsal manifest, audition packet, readiness matrix, and set plan.
- Segment render bundles: one segment card per timed arc segment with time window, style key, discovery amount, discovery band, mutation depth, readiness, listen-for cue, go/no-go cue, reset cue, Rytm preview summary, Analog Four preview summary, and counts.
- Optional event previews: capped mock event rows for each segment using the already validated set-plan preview rows.
- Deferred rows: the A4 rows that are not mock-renderable yet, formatted segment by segment.
- Safety block: explicit passive/mock-only language.

The JSON report emits deterministic data for the GUI, future audio-analyzer planner, and future active rehearsal mode:

- selected arc/readiness metadata
- embedded live session packet JSON
- `render_bundle` totals
- segment render bundles with event preview rows, deferred rows, and full per-segment mock preview JSON
- safety lines

## Data Model

Add frozen dataclasses in `rytm_randomizer/reports/style_performance_arcs.py`:

- `StylePerformanceArcLiveRenderSegment`: a segment-level packet that joins a live-session segment to the underlying set-plan preview. It stores event preview rows and deferred rows as tuple strings so text and JSON stay aligned.
- `StylePerformanceArcLiveRenderBundleReport`: the selected live-session packet plus render-bundle segments and suggested commands.

The bundle intentionally keeps the underlying `DualMachineStyleSelectionMockPreviewPlan` on each render segment so the report can serialize the exact mock preview already produced by the set-plan pipeline.

## Architecture

This is a projection over existing passive report data. It belongs in `rytm_randomizer/reports/style_performance_arcs.py` with the rest of the reference arc stack rather than a new device package or runtime module.

The data path is:

```text
style performance arc
-> readiness matrix
-> audition packet
-> rehearsal manifest
-> live session packet
-> live render bundle
-> text/JSON passive report
```

Segment mock rows come from `DualMachineStylePerformanceSetSegment.preview_plan` and `format_dual_machine_style_selection_mock_preview_event_rows`. The full machine preview JSON comes from `to_dual_machine_style_selection_mock_preview_json`.

## Safety

The new safety block must include:

- passive/read-only
- live render bundle
- mock render preview only
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

1. Add failing report builder/formatter/JSON tests.
2. Add failing parser/handler and CLI/help tests.
3. Add passive real-MIDI safety coverage for the new command.
4. Implement the additive report.
5. Update help, README, style docs, status, architecture references, and CLI help fixture.
6. Run focused tests, architecture tests, fast/full suite, coverage, lint, vulture, and review gate before push.

