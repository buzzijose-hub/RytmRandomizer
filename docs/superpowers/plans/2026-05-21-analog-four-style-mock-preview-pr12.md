# Analog Four Style Mock Preview PR12 Plan

## Goal

Add the Analog Four counterpart to the Rytm style mutation mock-preview bridge: a passive/mock-only report that converts promoted A4 style mutation-intent rows into inert CC preview rows, while honestly blocking decoded SysEx snapshots until A4 offsets are promoted.

## Scope

- Add one A4 strategy under `rytm_randomizer/devices/strategies/`.
- Add one passive report/CLI command under `rytm_randomizer/reports/`.
- Reuse existing A4 snapshot routing, mutation intent, mutation planner, and message renderer abstractions.
- Update CLI help, README, status, architecture diagrams, and focused tests.

## Non-Goals

- No real MIDI sending.
- No port opening.
- No A4 offset promotion.
- No NRPN rendering for drive/overdrive rows.
- No armed runtime behavior.

## Design Checkpoint

Decoded A4 SysEx snapshots still have `offsets_promoted=False`, so the report must not pretend it can mutate the current kit. The preview can produce CC rows only when a promoted snapshot object is available in code, which prepares the future offset-promotion workstream. For decoded files, the report surfaces the blocker and still shows deferred rows so the GUI/live workflow can explain what is missing.

CC-safe zones are intentionally narrow:

- `oscillator` -> `OSC1 Level` / CC69
- `filter` -> `Filter 1 Frequency` / CC18
- `envelope` -> `Amp Env Decay` / CC105
- `modulation` -> `LFO1 Speed` / CC116
- `effects` -> `Amp Delay Send` / CC92

`drive` remains deferred because the current A4 MIDI table treats the direct overdrive target as NRPN-only, and this slice only renders CC mock rows.

## TDD Plan

1. Red: add tests for promoted Jose Core Techno rows, NRPN-only deferrals, candidate-offset blocking, JSON/text reports, CLI parsing, passive CLI handling, and error paths.
2. Green: add the A4 mock-preview strategy/report with the smallest deterministic CC-safe mapping.
3. Refactor: share report formatting shape with the Rytm mock preview without introducing cross-device imports.
4. Verify focused tests, fast/full tests, architecture, lint, coverage, and review gate before PR.

## Gate Notes

- Gate 1: new modules get focused coverage and whole-project coverage remains above floor.
- Gate 2: V1.34 Rytm parity remains untouched.
- Gate 5/18: README, STATUS, and architecture diagrams updated because this adds CLI/report/strategy surface.
- Gate 7: N/A for hot-path metrics; this is passive reporting only.
- Gate 13: N/A; no env vars.
- Gate 16: fresh clean-base branch from `origin/modularize-v1.34`; no stacked PR.
- Gate 17: reuses existing A4 strategies and CLI registry; no parallel A4 package.
