# Cockpit Send-Plan Operator Readiness Report

## Goal

Add a passive operator-facing report that consumes a prepared `CockpitSendPlan`
JSON document and explains whether the cockpit SEND button may be enabled. This
is the read-only review layer after `prepare_send_plan` and before any future
armed hardware path.

## Scope

- Add `rytm_randomizer.reports.cockpit_send_plan_operator_readiness`.
- Register `cockpit-send-plan-readiness-report` through the passive CLI registry.
- Accept exactly one read-only source: `--plan-json <json>` or `--plan-file <path>`.
- Emit deterministic text and JSON with ready/blocked status, readiness reason,
  locked pads, pad packet summaries, blocked active actions, safety notes, and
  replayable passive commands.
- Keep the command passive: no GUI launch, no hardware connection, no MIDI port
  opening, and no MIDI sending.
- Update CLI help, README, architecture/status docs, and focused coverage.

## Test Plan

- Focused report tests for ready plans, blocked plans, parser behavior, text
  output, JSON output, and passive import safety.
- CLI help coverage for the new user-facing command.
- Architecture tests to enforce package and passive boundary rules.
- Fast/full pytest, lint, review, and coverage gates before push.

## Rollback

Remove the report module, CLI lazy entry, help text, focused tests, and docs
entry. No V1.34 parity fixtures or hardware-facing code should need rollback.
