# Cockpit Send-Plan Rehearsal Surface

## Goal

Add a passive GUI-facing rehearsal surface above cockpit send-plan readiness so
future desktop/operator views can render SEND review state from a prepared
`CockpitSendPlan` without launching a GUI or touching hardware.

## Scope

- Add `rytm_randomizer.reports.cockpit_send_plan_rehearsal_surface`.
- Register `cockpit-send-plan-rehearsal-surface-report` through the passive CLI.
- Accept exactly one read-only source: `--plan-json`, `--plan-file`,
  `--readiness-json`, or `--readiness-file`.
- Emit deterministic text and JSON with review panels, state bindings, disabled
  SEND/apply controls, acceptance checks, blocked active actions, nested
  upstream readiness metadata, safety notes, and replayable passive commands.
- Keep the command passive: no GUI launch, no sidecar launch, no hardware
  connection, no MIDI port opening, and no MIDI sending.
- Update CLI help, README, architecture/status docs, and focused coverage.

## Test Plan

- Focused report tests for ready plans, blocked plans, parser behavior, text
  output, JSON output, wrapped readiness input, file input, and passive import
  safety.
- CLI help coverage for the new user-facing command.
- Architecture tests to enforce package and passive boundary rules.
- Fast/full pytest, lint, review, and coverage gates before push.

## Rollback

Remove the report module, CLI lazy entry, help text, focused tests, and docs
entry. No V1.34 parity fixtures, cockpit SEND runtime code, GUI runtime code, or
hardware-facing code should need rollback.
