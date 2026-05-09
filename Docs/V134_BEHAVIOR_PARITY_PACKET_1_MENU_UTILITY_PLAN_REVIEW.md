# V1.34 Behavior Parity Packet 1 Menu/Utility Plan Review

## Purpose

This document reviews and accepts the V1.34 behavior parity Packet 1
menu/utility plan.

It confirms Packet 1 is ready for a tiny first implementation slice after this
review, while keeping the review itself documentation-only.

This review does not implement runtime behavior, tests, dispatch, MIDI, port
opening, active CLI behavior, package metadata, or hardware behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 2a41615 Add V1.34 behavior parity Packet 1 plan

Current phase:

- Passive/Mock Foundation Phase
- V1.34 behavior parity readiness accepted
- Packet 1 menu/utility implementation plan documented
- Packet 1 plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

`Docs/V134_BEHAVIOR_PARITY_PACKET_1_MENU_UTILITY_PLAN.md` is accepted as the
current Packet 1 implementation plan.

The plan is accepted for a small first implementation slice.

The plan does not authorize broad behavior parity work.

The plan does not authorize real MIDI, port opening, active CLI behavior,
package metadata changes, or hardware validation.

## Accepted Packet Identity

Packet name:

- Packet 1: Menu/Utility Behavior Parity

Accepted packet intent:

- establish the first small, mock/passive-safe runtime behavior shape
- keep behavior deterministic and inspectable
- avoid real MIDI, ports, active CLI behavior, and hardware
- stabilize routing vocabulary before deeper behavior domains

## Accepted Packet 1A Scope

The review accepts Packet 1A as the first implementation subset.

Accepted Packet 1A scope:

- read-only menu/status behavior for `BD`, `FM`, `PD`, `SM`, `P2M`, `J`,
  `GM`, `SCN`, `PR`, `SR`, `P3M`, `P4M`, `H`, and `R`
- deterministic result objects or plain structured dictionaries
- no command execution
- no state mutation
- no prompt loop
- no CLI wiring
- no real MIDI
- no ports
- no hardware requirement

## Accepted Deferred Scope

The review accepts that the following remain deferred:

- `T` target pad/channel selection prompt behavior
- `C` MIDI channel selection prompt behavior
- `Q` command-loop exit behavior

Reasons:

- `T` and `C` may affect future hardware output targets.
- `Q` depends on future command-loop/session lifecycle behavior.
- Deferring them keeps Packet 1A focused on low-risk display and
  state-reporting behavior.

## Accepted Future File Ownership

The review accepts the proposed narrow future write set:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`
- `Scripts/closeout_check.ps1`, only to add the new test file to closeout

Optional future fixture files are accepted only if deterministic text output is
introduced:

- `tests/fixtures/behavior_menu_utility_*_expected.txt`

The first implementation packet should not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command paths
- runtime execution/dispatch/MIDI logic outside the proposed Packet 1A files

## Accepted Future Behavior Shape

The review accepts a small read-only behavior result shape as planning
vocabulary.

Future implementation may include fields such as:

- command key
- label
- behavior family
- display/status lines
- state dependency notes
- state changed: false
- prompt required: false
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

Exact names may be adjusted during implementation if tests keep the same
safety meaning.

## Accepted Future Test Expectations

The future Packet 1A implementation must include tests for:

- importing the new module prints nothing
- supported menu/status keys return deterministic read-only behavior results
- `BD` returns a menu/status behavior result
- `J` returns group layout display intent without group mutation
- `SCN` returns scene menu display intent without scene execution
- `H` and `R` return state-reporting intent without runtime state mutation
- unsupported keys fail safely
- `T`, `C`, and `Q` are deferred or safe-fail unless separately approved
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- V1.34 reference remains untouched
- package metadata files remain absent unless separately approved

## Parallelization Decision

Parallel implementation remains not recommended for Packet 1A.

Reasons:

- Packet 1A is intentionally small.
- The first behavior result shape needs to stabilize.
- File ownership is concentrated.
- Parallel work would add coordination overhead before the first behavior
  shape exists.

Parallel implementation can be reconsidered after Packet 1A lands cleanly.

## Confirmed Absent Behavior

- no implementation in this review
- no tests in this review
- no runtime code change
- no command dispatch
- no command execution
- no scene execution
- no prompt/input loop
- no active CLI command
- no `execute-command`
- no `send-command`
- no `hardware-test`
- no real MIDI dependency
- no `mido`
- no `rtmidi`
- no MIDI port discovery/opening/sending
- no package metadata change
- no hardware behavior
- no hardware validation
- no profile `"3"` active-boundary support
- no profile `"4"` implementation
- no Analog Four
- no Pads 5-12
- no machine/profile expansion
- no SysEx
- no GUI/capture

## Safe Next Options

- implement Packet 1A exactly as a tiny scoped packet
- pause at this accepted Packet 1 plan checkpoint
- write a user-facing progress update before implementation

## Recommendation

Proceed next with Packet 1A implementation.

Implementation should be limited to:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`
- `Scripts/closeout_check.ps1`, only to add the new test file to closeout

Keep `T`, `C`, and `Q` deferred unless separately approved.

Do not add CLI wiring.

Do not add real MIDI.

Keep hardware off.

Keep package metadata absent.

## Decision

The V1.34 behavior parity Packet 1 menu/utility plan is accepted.

The next recommended task is the tiny Packet 1A implementation for read-only
menu/status behavior.

Hardware remains off.

No implementation is added by this review.
