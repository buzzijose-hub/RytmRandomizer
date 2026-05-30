# Live Set Cockpit Packet Plan

Date: 2026-05-22

## Goal

Add one complete passive command, `style-performance-arc-live-set-cockpit-report`, that sits above the existing live cue sheet, runbook, stage routing, and stage rehearsal-state layers. The command gives a performer a single show-facing dashboard: launch controls, machine panels, cue cockpit cards, recovery controls, next-best-action text, optional capped mock event previews, and deterministic JSON.

## Scope

- New report module under `rytm_randomizer/reports/`.
- Passive CLI registration and help text.
- Focused report, parser, handler, CLI dispatch, help, and passive MIDI-safety tests.
- README/manual/style/architecture/status documentation updates.

## Non-Goals

- No MIDI rendering.
- No real MIDI send path.
- No MIDI port opening.
- No hardware mutation.
- No new top-level package module.
- No V1.34 parity fixture changes.

## Design

The cockpit report composes `build_style_performance_arc_stage_rehearsal_state_report` and does not bypass any lower layer. The output adds only operator-facing summaries:

- cockpit status and operator mode,
- next best action,
- launch controls from the live runbook and live set card,
- machine panels from aggregate rehearsal machine states,
- cue cockpit cards from cue-level rehearsal states,
- recovery controls built around `S5 -> Z -> Q`,
- replayable passive commands,
- nested JSON that preserves the rehearsal-state/routing/runbook/cue-sheet/reference-match payloads.

## Verification Plan

- Focused RED/GREEN tests for builder, formatter, JSON, parser, handler, CLI dispatch, help, and passive MIDI safety.
- CLI fixture refresh for top-level help.
- Architecture/lint/full/coverage/review gates before commit/push.

## Plan Requirements

- [x] Gate 1 - coverage target planned for new touched report behavior.
- [x] Gate 2 - V1.34 parity must remain byte-identical.
- [x] Gate 3 - lint trio required before push.
- [x] Gate 4 - vulture/dead-code gate required before push.
- [x] Gate 5 - docs updated with command and operator flow.
- [x] Gate 6 - typed dataclasses and no bare `Any`.
- [x] Gate 7 - passive report only; no hot active path.
- [x] Gate 8 - tests stay in existing report/CLI safety suites.
- [x] Gate 9 - new code lives in `reports/`.
- [x] Gate 10 - CLI dispatch follows existing lazy command pattern.
- [x] Gate 11 - shared fixtures reused.
- [x] Gate 12 - module constants use `Final`.
- [x] Gate 13 - no new env vars.
- [x] Gate 14 - bounded composition layer, no lower-layer reimplementation.
- [x] Gate 15 - plan captures reusable learning.
- [x] Gate 16 - one clean-base PR, no stacked PR.
- [x] Gate 17 - reuses stage rehearsal-state abstraction and existing report formatter/CLI registry.
- [x] Gate 18 - architecture docs and module count refreshed.

## Strict Rules

- [x] No hardware in tests.
- [x] Lazy MIDI imports preserved.
- [x] Hardware-pinned packages untouched.
- [x] Passive default preserved.
- [x] No stacked PR.
- [x] No hook bypass.
