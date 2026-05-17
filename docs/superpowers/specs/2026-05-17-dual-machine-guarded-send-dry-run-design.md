# Dual-Machine Guarded Send Dry-Run Design

## Context

The dual-machine active send plan now classifies bridge events as eligible
mapped CC messages or blocked saved-offset candidates. The next step is a
guarded sender boundary that proves how a future hardware sender will behave
before any real port is opened.

## Goal

Add a mock-only guarded sender execution path that accepts a
`DualMachineActiveSendPlan`, refuses unsafe plans, and emits only eligible CC
events into an injected `MockMidiSender`. Expose this through a passive dry-run
CLI report so the user and Eddie can see whether the sender would emit messages
for a target scope.

## Design Options

Recommended: strict all-or-nothing by target scope.

- If the active send plan is ready, emit every eligible mapped CC event.
- If the plan has any blocked event, emit nothing.
- To send one machine while leaving the other alone, run the bridge with
  `--target rytm` or `--target analog-four`.

Alternative: partial eligible-only sending.

- This would send Rytm mapped CCs even when Analog Four candidates are blocked.
- It is riskier because a combined target could silently ignore one machine.

Alternative: jump directly to a real `--arm` command.

- This is too large for this slice because it combines guard semantics, port
  selection, operator confirmation, and hardware mutation.

## Chosen Approach

Use strict all-or-nothing by target scope. It is predictable on stage: if the
user asks for both machines and one side is unsafe, nothing is emitted. If the
user wants one machine, the existing target scope makes that explicit.

## Scope

In scope:

- New import-safe module for guarded dry-run execution.
- `DualMachineGuardedSendResult` dataclass.
- API requiring both `armed=True` and `dry_run_confirmed=True`.
- Refusal for not armed, not confirmed, and not-ready plans.
- Conversion of eligible plan events into inert `MidiMessage` CC records.
- CLI report command using `MockMidiSender` only.

Out of scope:

- Real MIDI sender integration.
- Real port listing or opening.
- Real hardware mutation.
- SysEx receive or write.
- Analog Four saved-offset to CC mapping.

## API

`execute_dual_machine_guarded_send(plan, sender, *, armed, dry_run_confirmed)`

- Requires a `DualMachineActiveSendPlan`.
- Requires a `MockMidiSender`.
- Returns accepted false without emitting if missing arming.
- Returns accepted false without emitting if missing dry-run confirmation.
- Returns accepted false without emitting if `plan.ready` is false.
- Emits only `cc` messages for eligible events when accepted.

`build_dual_machine_guarded_send_dry_run(bridge)`

- Builds the active send plan from the bridge.
- Executes the guarded send into a fresh `MockMidiSender`.
- Uses `armed=True` and `dry_run_confirmed=True` because the command is a
  passive dry-run report only.

## CLI

Command:

```text
python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong>
python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --analog-four-path <path> --analog-four-slot <1-128>
python -m rytm_randomizer.cli dual-machine-guarded-send-dry-run-report <path> --slot <1-128> --depth <micro|groove|strong> --target <rytm|analog-four|both>
```

The command is passive. It does not open ports or send MIDI. It uses an inert
mock sender to prove what a later active sender would be allowed to emit.

## Acceptance

- Safe-starter bridge emits 14 mock CC messages.
- Target `rytm` on the real project dump emits 60 mock CC messages.
- Combined real Rytm+A4 project dump is refused because the A4 side contains 24
  blocked candidate events.
- Full test suite remains green.
