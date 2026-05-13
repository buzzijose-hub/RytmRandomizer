# V1.34 Behavior Parity Roadmap/Timeline Update After Runtime Plan Report CLI Preview

## 1. Purpose

Provide a broader behavior-parity roadmap and timeline update after the
accepted passive runtime plan report CLI preview.

This report summarizes:

- what exists now
- what the runtime plan report CLI preview means
- what has been proven
- what remains parked or intentionally absent
- where the project is in the behavior-parity phase
- what the safe next branches are
- rough time expectations before the next more active-facing phase

This report is documentation-only.

It adds no implementation, tests, fixtures, closeout script changes, CLI
changes, CLI execution wiring, runtime execution, dispatch, command execution,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `3f2a624 Add next branch selection after runtime plan CLI progress review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime plan report CLI preview implemented and accepted
- next branch selected as a broader roadmap/timeline update
- roadmap/timeline update now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Phase Name

Current phase:

- Behavior-Parity Passive/Mock Visibility Phase

This phase is still:

- passive by default
- mock-only for runtime and active-boundary planning
- read-only from CLI
- hardware-off
- not a real MIDI phase
- not a hardware validation phase

## 4. Latest Meaningful Milestone

Latest meaningful implementation milestone:

- `01a8735 Add runtime plan report CLI preview`

Latest accepted checkpoint/review arc:

- `f309f77 Add runtime plan report CLI preview checkpoint`
- `3b30b03 Add runtime plan report CLI preview checkpoint review`
- `49406e8 Add progress report after runtime plan CLI preview`
- `3a7a70a Add progress report review after runtime plan CLI preview`
- `3f2a624 Add next branch selection after runtime plan CLI progress review`

What it means:

- the runtime plan report can now be viewed from the passive CLI
- runtime planning visibility is operator-facing
- profiles `2` and `3` are visible as supported runtime planning inputs
- profile `4` remains parked
- unsupported planning inputs remain visible as unsupported
- active CLI wiring remains absent
- runtime execution remains absent
- hardware remains off

This is another step toward a usable operator-facing control-room view without
crossing into execution.

## 5. Current Passive CLI Visibility

Current passive CLI visibility includes:

- `python -m rytm_randomizer.cli report`
- `python -m rytm_randomizer.cli mock-mapper-report`
- `python -m rytm_randomizer.cli runtime-plan-report`
- `python -m rytm_randomizer.cli active-boundary-report`
- `python -m rytm_randomizer.cli anchor-profile-report`
- `python -m rytm_randomizer.cli behavior-parity-report`
- `python -m rytm_randomizer.cli list-commands`
- `python -m rytm_randomizer.cli list-scenes`
- `python -m rytm_randomizer.cli list-group-profiles`
- `python -m rytm_randomizer.cli search-commands <query>`
- `python -m rytm_randomizer.cli search-scenes <query>`
- `python -m rytm_randomizer.cli search-group-profiles <query>`
- `python -m rytm_randomizer.cli inspect-command <key>`
- `python -m rytm_randomizer.cli inspect-scene <key>`
- `python -m rytm_randomizer.cli inspect-group-profile <key>`
- `python -m rytm_randomizer.cli preview-command <key>`
- `python -m rytm_randomizer.cli preview-scene <key>`
- `python -m rytm_randomizer.cli preview-group-profile <key>`

These commands remain passive/read-only.

They do not execute commands, open ports, send MIDI, dispatch runtime actions,
mutate hardware, or require hardware.

## 6. Current Runtime Planning Visibility

The runtime plan report CLI preview shows:

- supported planning inputs:
  - group profile `2` / My BD Hard
  - group profile `3` / My BD Classic
- parked planning inputs:
  - group profile `4` / My BD Acoustic
- unsupported planning inputs:
  - unknown group profile key
  - unsupported scene source kind
- runtime safety:
  - would execute: false
  - mock-only: true
  - sends real MIDI: false
  - ports allowed: false
  - hardware required: false
  - runtime execution: absent
  - CLI execution wiring: absent
  - dispatch: absent

In plain language:

- the CLI can now show a future-execution-shaped plan
- the plan is still blocked
- the plan is still read-only
- the plan still cannot touch hardware

## 7. Accepted Profile Semantics

Profile `2` / My BD Hard:

- runtime-plan supported planning input
- active-boundary accepted first mock-only active candidate
- blocked by default
- visible in runtime plan report CLI output
- mock-only
- no real MIDI
- no hardware

Profile `3` / My BD Classic:

- runtime-plan supported planning input
- active-boundary intentionally unsupported
- visible in runtime plan report CLI output
- preserved as an intentional runtime-plan/active-boundary difference
- no active-boundary support added

Profile `4` / My BD Acoustic:

- parked
- unsupported
- visible as parked in runtime plan report CLI output
- no mapper expansion added
- no active-boundary support added

## 8. Current Behavior-Parity Foundation

The current modular behavior-parity foundation includes:

- passive metadata scaffold
- passive validation, inspection, preview, and audit helpers
- passive registry and registry report
- passive CLI report/list/search/inspect/preview paths
- mock MIDI scaffold
- mock message mapper and report
- mock mapper report CLI preview
- behavior helper surfaces for the current read-only intent layer
- behavior reports and passive CLI visibility
- runtime-adjacent mock-only safe-failure coverage for `PZ`, `B`, and `L`
- runtime plan scaffold
- runtime plan report
- runtime plan report CLI preview
- active-boundary report
- active/runtime report alignment tests
- real MIDI import and passive CLI safety checks

The project can now describe and preview a large slice of V1.34-like behavior
without executing anything.

## 9. Current Closeout Coverage

Current closeout coverage includes:

- scaffold
- validation
- inspection
- preview
- audit
- profile lookup
- scene lookup
- command lookup
- registry
- registry report
- registry report CLI
- passive CLI
- behavior menu utility
- behavior anchor profile
- behavior anchor profile report
- behavior mutation depth
- behavior scene group
- behavior Pad 1 lane
- behavior Pad 2 lane
- behavior Pad 3 lane
- behavior Pad 4 lane
- behavior undo/commit/state
- behavior selected profile
- behavior selected isolated pad
- selected target state
- anchor state
- selected isolated pad runtime state
- runtime-adjacent mock-only `PZ`
- runtime-adjacent mock-only `B`
- runtime-adjacent mock-only `L`
- behavior parity coverage report
- mock MIDI
- mock message mapper
- mock mapper report
- mock-only active candidate
- active boundary
- active boundary report
- real MIDI import safety
- real MIDI passive CLI safety
- real MIDI adapter boundary
- runtime plan
- runtime plan report
- active/runtime report alignment

This matters because the passive/mock and runtime-adjacent safety surface is
now part of the regular closeout loop.

## 10. What Has Been Proven

The current foundation proves:

- V1.34 reference protection is still working
- package metadata protection is still working
- passive CLI commands can expose reports without becoming active commands
- runtime planning can be represented without execution
- runtime planning can be shown from CLI without execution
- profile `4` can remain parked without blocking progress
- unsupported inputs can remain visible and safe
- runtime-adjacent safe-failure concepts can be tested without hardware
- active-boundary alignment can be tested without hardware
- the project can improve visibility without moving closer to real MIDI

## 11. What Remains Parked

Parked/safe scope:

- active CLI commands
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- profile `4` mock mapper support
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- real MIDI
- hardware validation

The parked scope is not forgotten.

It is deliberately held behind future design/review gates.

## 12. What Remains Intentionally Absent

Still absent:

- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- CLI execution wiring
- runtime execution
- dispatch
- command execution
- scene execution
- mutation execution
- runtime state mutation
- selected pad switching execution
- selected pad anchor return execution
- profile `4` active-boundary support
- fourth runtime-adjacent candidate
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- package metadata changes
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 13. Progress Estimate

Approximate current progress:

- full dream project:
  - 35-40%
- core modular software foundation:
  - 90%+
- passive CLI / dry-run / visibility foundation:
  - 95%+
- captured V1.34 passive metadata map:
  - 100% for the currently captured command surface
- read-only behavior-parity foundation:
  - 90%+
- mock MIDI / mock active-boundary foundation:
  - 80-90%
- runtime planning visibility:
  - 70-80%
- real MIDI / hardware validation:
  - 0% real hardware validation
- GUI/reference-analysis/performance ecosystem:
  - not started

These are planning estimates, not release promises.

## 14. Rough Timeline Expectations

If work continues in larger safe packets:

- next documentation/review checkpoint:
  - roughly 30-60 minutes
- roadmap/timeline review and next-branch selection:
  - roughly 1-2 focused hours
- another tiny mock-only safety gap, if selected:
  - roughly 2-5 focused hours
- passive/runtime visibility phase review:
  - roughly 1-2 focused hours
- first narrow runtime/active-facing implementation beyond reporting:
  - likely 4-10 focused hours after a separate plan/review
- real MIDI boundary preparation:
  - likely 6-12 focused hours after mock-only confidence
- real hardware validation preparation:
  - likely 4-8 focused hours after real MIDI boundary design and tests

Real hardware validation remains later and separately approved.

The next phase is closer, but it is not hardware execution yet.

The next phase is likely:

- passive/runtime visibility phase review, or
- one more tiny mock-only safety gap, or
- roadmap-guided selection of the first narrow runtime/active-facing
  implementation plan

## 15. Meaning For The Dream Project

The project now has a visible passive control-room layer and a blocked
runtime-planning layer.

That means the future active layer is no longer a vague idea. It now has:

- passive CLI visibility
- mock MIDI foundations
- mock-only active candidate vocabulary
- runtime plan vocabulary
- read-only runtime plan reporting
- active-boundary reporting
- closeout coverage
- protected reference and dependency boundaries

The fun stuff is closer because the project can now show what future action
would mean before anything is allowed to act.

But the hardware line remains uncrossed, which is still the correct safety
posture.

## 16. Safe Next Branches

Safe next branches:

- Option A: docs-only review/acceptance gate for this roadmap/timeline update
- Option B: docs-only passive/runtime visibility phase review
- Option C: docs-only next-branch selection for another tiny mock-only safety
  gap
- Option D: pause at this clean checkpoint
- Option E: user-facing progress/timeline summary for session handoff

## 17. Recommendation

Review and accept this roadmap/timeline update next.

Then choose between:

- passive/runtime visibility phase review, or
- another tiny mock-only safety gap.

Do not jump to real MIDI.

Do not turn on hardware.

Do not add active CLI commands yet.

Do not add runtime execution yet.

Do not add profile `4` active-boundary support without a separate plan.

## 18. Decision

The behavior-parity roadmap/timeline after the runtime plan report CLI preview
is now updated.

The project is closer to active-facing work, but remains passive/mock-only.

Hardware remains off.

No implementation in this slice.

## 19. Review Status

This roadmap/timeline update has been reviewed and accepted as the current
behavior-parity roadmap/timeline reference after the passive runtime plan
report CLI preview.

Review document:

- `Docs/V134_BEHAVIOR_PARITY_ROADMAP_TIMELINE_UPDATE_AFTER_RUNTIME_PLAN_REPORT_CLI_PREVIEW_REVIEW.md`
