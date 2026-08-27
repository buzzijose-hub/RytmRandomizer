# Targeted live-kit mutation architecture: before and after

| Surface | Before | After |
|---|---|---|
| Scope | Implicit all-pad behavior plus Rytm locks | Generic `MutationScope`; Cockpit `MutationTargets`; empty targets mean all |
| Device seam | `plan(snapshot, depth)` | `plan(snapshot, depth, scope)` across Protocol and registered devices |
| Session/wire | No target state | Rytm/A4 target fields, typed set/clear commands, whole-state event |
| Send safety | Candidate and locks only | Target/lock evidence plus packet-level contradiction rejection |
| Rytm capture | Verified capture retained | Promoted mapped rows become an in-memory Cockpit anchor; unknowns omitted |
| A4 capture | Verified capture retained | Exact capture retained; semantic mutation explicitly zero-event and blocked |
| UI | Individual lock/depth controls | Multi-select targets with targeted, locked, and inactive visual states |
| Cockpit hardware authority | Passive/mock output; packaged Tauri grants input capture only | Packaged Tauri grants verified input capture and retains the repo's single in-UI `ArmedApplySession` output boundary |
| Live SEND authorization | Ready plan selected implicitly from session | UI confirms exact details and armed WS requires the matching current `send_plan_id` through the existing ArmedApply lifecycle |
| Dual-machine coordination | Independent UI fragments without a whole-stage truth | One coordinator publishes independent Rytm/A4 capture, scope, candidate, plan, authority, blocker, and recovery state |

No module was renamed or deleted. New modules are
`snapshot/mutation_scope.py`, `cockpit/mutation_targets.py`,
`cockpit/data/stage.py`, and the existing capture subpackage's `bridge.py`.
No top-level package, device family package, sender, or SysEx envelope
implementation was added.

The composition deliberately does not restore the deleted
`RealMidiDeviceAdapter`. `MockDeviceAdapter` remains the Cockpit state/history
model, while all real output authority stays exclusively in the existing
`senders.armed_apply.ArmedApplySession`. The packaged shell's added authority
is input-only current-KIT capture; ordinary passive entry points stay passive,
and A4 mutation output remains structurally blocked.
