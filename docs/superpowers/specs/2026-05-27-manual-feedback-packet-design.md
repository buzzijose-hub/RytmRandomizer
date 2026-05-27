# Manual Feedback Packet Design

Date: 2026-05-27

## Goal

Add a passive report that turns Jose's current manual testing observations into
structured reviewer evidence. The report gives the operator a deterministic
checklist for installer launch, cockpit sidecar state, Profile Wizard analysis,
Export Model behavior, current four-pad versus desired 12-pad scope, mock
controls, and the explicit hardware boundary.

This is deliberately not a new GUI feature. It is a bridge between the live
manual testing session and Eddie's review loop so feedback is reproducible,
prioritized, and safe to hand back to code.

## Architecture Fit

- Canonical prompt data lives in `rytm_randomizer/data/manual_feedback_packet.py`.
- The passive report surface lives in
  `rytm_randomizer/reports/manual_feedback_packet.py`.
- The CLI is a lazy `CliCommand` named `manual-feedback-packet-report`.
- The top-level passive CLI help documents the command so the passive safety
  sweep can auto-discover and exercise `--help`.

The report reuses the existing `PassiveReportHeader` formatter, `cli_registry`
dispatch, and data-layer export pattern. It adds no top-level package, no new
device family, no sender, no renderer, and no mutation path.

## Scenarios

The report supports named subsets so an operator can capture only the evidence
needed for the current handoff:

- `full` - installer, cockpit, wizard, analyzer, export, mock controls, and
  hardware boundary.
- `installer` - installer artifact, unsigned warning, cockpit launch, and
  sidecar connection state.
- `profile` - Profile Wizard create flow, analyzer setup, reference result,
  Export Model, and pad-scope feedback.
- `mock` - cockpit mock-control button and history behavior.
- `hardware` - explicit arm boundary, stop conditions, and pad-scope notes.
- `review` - the highest-priority current defects: analyzer dependency, export
  no-op, and 12-pad scope gap.

## Safety Contract

The report is evidence-only.

- No GUI launch.
- No audio analysis.
- No profile export write.
- No MIDI import or port discovery.
- No MIDI send.
- No hardware action.
- No unattended behavior.

Hardware feedback remains manual and explicitly approved. The report only tells
the operator what to record if an approved smoke test is run.

## Future Extension

Later GUI work can consume the JSON payload to render a "Send feedback to
review" panel, but that future panel should keep the same passive defaults. The
same model can also be used to link screenshots, logs, installer artifact IDs,
or `.rymp` export outcomes once those capture paths are designed.
