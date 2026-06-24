# Controller Brain Operator Package Ledger Plan

Status: in-flight
Date: 2026-06-24
Branch: `codex/controller-brain-operator-package-ledger`
Base: `origin/modularize-v1.34`

## Goal

Add a passive report and CLI surface that proves the future controller brain can
translate virtual controller gestures into Live Kit Operator Package staging
intent. This is the next clean-base OXI/E16-counterpunch slice: the controller
does not merely move knobs, it selects package actions, package slots, queue
stages, recovery paths, and readiness evidence for the live kit currently under
review.

## Scope

- Compose the existing passive `controller-brain-rehearsal-report` with the
  existing passive `live-gui-performance-console-report` operator package.
- Emit deterministic binding rows from controller assignments to operator
  package targets.
- Preserve side-effect proof: no controller input, no raw CC learn, no WebSocket
  dispatch, no MIDI output, no MIDI port, no file write, no snapshot mutation,
  and no hardware arm.
- Add CLI/help/docs coverage so operators can run the report directly.

## Out of Scope

- No real controller input.
- No MIDI learn.
- No WebSocket dispatch.
- No package apply/send.
- No cockpit UI mutation.
- No hardware testing.

## Implementation Steps

1. Add tests that pin the report model, JSON payload, formatted text, CLI
   behavior, help text, and no-real-MIDI import contract.
2. Add `rytm_randomizer.reports.controller_brain_operator_package`.
3. Wire `controller-brain-operator-package-report [--json]` into the passive CLI.
4. Update README, CLI reference, and project status.
5. Run focused tests, architecture tests, lint, and broader verification.

## Safety Contract

The report is passive/read-only. It only composes in-memory metadata from
existing passive reports and writes to stdout when invoked through the CLI. It
must not open a hardware port, import the real MIDI adapter, send MIDI, write
files, mutate snapshots, launch a GUI, or dispatch WebSocket commands.
