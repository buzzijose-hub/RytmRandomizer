# Dual-Machine Both-Target Hardware Send Design

## Context

The dual-machine active send path can already classify a combined Rytm + Analog
Four bridge. When the bridge uses the Analog Four safe-starter CC plan, every
event is a mapped CC and the active plan is ready. The armed sender currently
refuses `target=both` anyway, because the first hardware slice only handled one
selected port at a time.

## Goal

Allow `--arm --dual-machine-snapshot-send --snapshot-target both` to send a
ready dual-machine active plan to two selected MIDI output ports: one Analog
Rytm port and one Analog Four port.

## Chosen Approach

Keep the existing single-target sender intact and add a dual-port execution
function in `dual_machine_hardware_sender.py`. The app will build and validate
the plan before opening any port. For `target=both`, it prompts for the Rytm
output, prompts for the Analog Four output, requires exact `SEND`, opens both
ports, then routes each event by `event.device`.

This keeps the safety rule simple:

- safe-starter A4 CC plans can be sent;
- saved-offset A4 snapshot candidates remain blocked;
- no partial send occurs when any event is ineligible.

## Scope

In scope:

- Dual-port hardware execution for `DualMachineActiveSendPlan` when
  `plan.target == "both"`.
- App wiring for `--arm --dual-machine-snapshot-send --snapshot-target both`.
- One confirmation prompt after both ports are chosen.
- Fake-port tests proving Rytm events go only to the Rytm port and A4 events go
  only to the A4 port.
- Refusal before port listing/opening when the plan contains unverified A4
  saved-offset candidates.

Out of scope:

- Snapshot essence planning for Analog Four.
- Sending A4 saved-offset candidate events.
- NRPN sending.
- Continuous live SysEx receive.
- GUI workflow.

## App Shape

```text
python -m rytm_randomizer.app --arm --dual-machine-snapshot-send --snapshot-path <rytm-path> --snapshot-slot <1-128> --snapshot-depth <micro|groove|strong> --snapshot-target both
```

Optional A4 saved snapshot inputs remain allowed for dry-run/reporting, but if
they introduce saved-offset candidate events the armed both-target path refuses
before opening any port.

## Safety Rules

- The plan must be ready before MIDI ports are listed or opened.
- Every event must be an eligible mapped CC.
- Both-target hardware send requires two output selections.
- The selected port names must be different.
- Exact `SEND` confirmation is required after port selection.
- If either port open fails, any already-opened port is closed best-effort and
  no events are sent.
- The passive CLI remains read-only.

## Acceptance

- Dual-port sender import remains silent and does not import `mido` or `rtmidi`.
- A ready both-target safe-starter plan emits Rytm CCs to the Rytm fake port and
  A4 CCs to the A4 fake port.
- A both-target plan with A4 saved-offset candidates is refused before sending.
- App armed both-target fake-port test selects two ports, confirms `SEND`, sends
  to both fake ports, and closes both ports.
- App armed both-target blocked-candidate test refuses before provider
  construction.
- Focused and full test suites pass.
