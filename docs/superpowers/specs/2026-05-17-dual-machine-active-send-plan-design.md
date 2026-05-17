# Dual-Machine Active Send Plan Design

## Context

The project now has a passive dual-machine bridge that combines Analog Rytm
saved-kit snapshot mutations with either Analog Four safe-starter CC messages
or Analog Four saved-offset snapshot candidates. The live snapshot readiness
gate correctly marks mapped CC streams as ready and saved-offset candidates as
blocked. The next milestone is not real sending yet; it is a final passive send
plan that proves which events would be eligible for a future guarded active
sender.

## Goal

Add a passive `dual-machine-active-send-plan-report` command that reads the
existing dual-machine bridge and prints a deterministic event-level send plan.
It must separate mapped CC messages that a later active sender may use from
unverified candidate events that must remain blocked.

## Chosen Approach

Use the existing bridge and readiness gate as the source of truth, then add a
thin send-plan layer on top.

The other viable paths were to merge this into the readiness report or jump
straight to a real `--arm` command. Keeping it separate is safer: readiness
answers "is the whole bridge allowed?" while the send plan answers "which exact
events would be allowed or blocked?" Real sending should wait until this report
is green on the user's actual dumps.

## Scope

In scope:

- Passive report-only module and CLI command.
- Event-level eligibility for mapped CC messages.
- Event-level blocking for `saved_offset_candidate` messages.
- Target scoping inherited from the bridge: Rytm only, Analog Four only, or
  both.
- Deterministic counts for eligible, blocked, and total planned events.
- Real-dump verification against the user's Rytm and Analog Four project dumps.

Out of scope:

- No MIDI port opening.
- No MIDI sending.
- No SysEx receive or write.
- No live hardware mutation.
- No Analog Four saved-offset to CC mapping claim.
- No new active command.

## Data Model

`DualMachineSendPlanEvent` represents one planned event:

- `device`
- `source`
- `message_type`
- `channel`
- `control`
- `value`
- `eligible`
- `reason`
- `label`

`DualMachineActiveSendPlan` represents the whole passive plan:

- `target`
- `ready`
- `readiness_reason`
- `events`
- derived `eligible_message_count`
- derived `blocked_event_count`
- derived `combined_event_count`

## Eligibility Rules

- A captured bridge message with type `cc` is eligible.
- A captured bridge message with type `saved_offset_candidate` is blocked with
  reason `candidate_unverified_no_cc_mapping`.
- Any future unknown message type is blocked as `unsupported_message_type`.
- If any event is blocked, the plan is not ready.
- If the readiness gate is not ready, the plan is not ready even if some mapped
  CC events are individually eligible.

## Reporting

The formatter prints:

- report title
- target
- send plan readiness and reason
- eligible mapped CC count
- blocked candidate event count
- combined planned event count
- event preview lines
- mapping policy
- passive safety lines

Event lines must be explicit enough for the user and Eddie to see what a future
sender would do without needing to inspect code.

## CLI

Command:

```text
python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong>
python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
python -m rytm_randomizer.cli dual-machine-active-send-plan-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
```

The parser follows the existing dual-machine bridge/readiness optional argument
shape. Error handling should use deterministic passive report text and return
nonzero for invalid input.

## Testing

Tests must prove:

- importing the module is silent and does not import MIDI libraries
- safe-starter bridge produces 14 eligible mapped CC events and no blocked
  events
- Analog Four saved snapshot candidates produce eligible Rytm CC events plus
  blocked A4 candidate events
- formatter prints the blocking policy and passive safety lines
- CLI help exposes the new command and safety language
- CLI command reads saved dumps and reports the blocked candidate path

## Acceptance

The real-dump command using the user's Rytm and Analog Four project dumps should
report:

- send plan ready: false
- Rytm mapped CC messages eligible
- Analog Four saved-offset candidate events blocked
- no MIDI sending

This gives us the last passive checklist before designing a guarded active
sender.
