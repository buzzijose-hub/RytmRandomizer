# Live GUI Playback Transcript Slice

## Goal

Add a passive/mock-safe report that consumes the live GUI controller-state packet and emits a deterministic playback transcript for future GUI and audio-analyzer test harnesses.

## Scope

- Add `rytm_randomizer/reports/live_gui_playback_transcript.py`.
- Add CLI command `style-performance-arc-live-gui-playback-transcript-report`.
- Add tests for report construction, JSON, formatting, CLI parsing, lazy passive CLI safety, and malformed replay-command handling.
- Update the passive command docs, help text, architecture/status notes, and CLI help fixture.

## Design

The playback transcript is the next layer after controller-state:

1. Consume a `StylePerformanceArcLiveGuiControllerStateReport`.
2. Emit ordered playback events for bootstrapping screen/render/analyzer context, hydrating controller state, queueing allowed GUI actions, asserting blocked controls/actions, and recording a final passive-safety checkpoint.
3. Emit GUI test assertions that a future GUI runner can use without needing to know the internal report chain.
4. Derive replay commands only when the upstream controller-state replay command is already complete enough to transform safely.
5. Keep all output JSON/stdout only.

## Non-goals

- No GUI launch.
- No GUI controller dispatch.
- No state-store mutation.
- No command execution.
- No audio capture or streaming.
- No MIDI sending, port opening, real MIDI rendering, SysEx writes, or hardware mutation.

## Verification

- Red/green focused TDD for the new report.
- Focused CLI/passive tests.
- Focused 100% branch coverage for the new module.
- Architecture, fast, full, package coverage, and mechanical review gates before local commit.

## Status

- [x] Tests written red first.
- [x] Report implementation complete.
- [x] CLI/help/docs wired.
- [x] Focused verification passed.
- [x] Broad verification passed.
- [x] Bundled into PR #95 after PR #94 landed; the branch is non-stacked against `origin/modularize-v1.34`, pushed for review, and no sibling PR dependency remains.

## Bundle Closeout Addendum

- Plan requirements: PR #95 links this plan and carries the full 18-gate checklist; this slice remains passive/mock-safe, uses existing `reports/`, `data/`, `CliCommand`, and formatter boundaries, and does not touch V1.34 parity.
- Rollback plan: revert the PR #95 bundle commit(s) for this report chain; because the commands are passive and lazily registered, rollback removes only report metadata/CLI/docs/tests.
- Done criteria: focused report tests pass, handler-level passive MIDI import safety passes, architecture/fast/full/coverage/review gates pass, docs counts stay current, and the PR stays non-stacked against `modularize-v1.34`.
- Bundle status: PR #94 merged; this work was recreated from `origin/modularize-v1.34`, bundled into PR #95, pushed with exact-path staging, and review was requested.
