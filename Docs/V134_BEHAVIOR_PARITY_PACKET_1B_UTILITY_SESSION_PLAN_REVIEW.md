# V1.34 Behavior Parity Packet 1B Utility/Session Plan Review

## Purpose

Review and accept the V1.34 behavior parity Packet 1B utility/session plan.

This review confirms Packet 1B is ready for a tiny future implementation
slice after this review, while keeping the review itself documentation-only.

This review does not implement runtime behavior, tests, dispatch, prompt
loops, MIDI, port opening, active CLI behavior, package metadata, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- a79f92b Add Packet 1A menu utility checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- Packet 1A read-only menu/status behavior implemented and accepted
- Packet 1B utility/session implementation plan documented
- Packet 1B plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Review Decision

`Docs/V134_BEHAVIOR_PARITY_PACKET_1B_UTILITY_SESSION_PLAN.md` is accepted as
the current Packet 1B implementation plan.

The plan is accepted for a small future implementation slice.

The plan does not authorize broad behavior parity work.

The plan does not authorize real MIDI, port opening, active CLI behavior,
package metadata changes, or hardware validation.

## Accepted Packet Identity

Packet name:

- Packet 1B: Utility/Session Behavior Intent

Accepted command scope:

- `T`
- `C`
- `Q`

Accepted packet intent:

- model utility/session intent deterministically
- avoid prompt loops
- avoid state mutation
- avoid process exit
- avoid real MIDI, ports, active CLI behavior, and hardware

## Accepted Future Behavior Meaning

The review accepts the future meaning of `T` as:

- target pad/channel selection intent
- no actual target change
- no prompt loop
- no hardware behavior

The review accepts the future meaning of `C` as:

- MIDI channel selection intent
- no actual channel change
- no prompt loop
- no MIDI port opening

The review accepts the future meaning of `Q` as:

- command-loop exit intent
- no `sys.exit`
- no process termination from the behavior helper
- no CLI termination behavior

## Accepted Future File Ownership

The review accepts the proposed future write set:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`

No closeout script update should be needed because `tests/test_behavior_menu_utility.py`
is already included in closeout.

The future Packet 1B implementation should not edit:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command paths
- runtime execution/dispatch/MIDI logic outside the Packet 1B files

## Accepted Future Behavior Shape

The review accepts reusing `MenuUtilityBehaviorResult` if it remains clear.

Future Packet 1B results may use:

- `behavior_family`: `utility/session`
- `accepted`: true
- `reason`: `supported_utility_session_intent`
- `state_changed`: false
- `prompt_required`: false
- `sends_real_midi`: false
- `opens_ports`: false
- `hardware_required`: false
- `active_behavior`: false

The review accepts metadata describing target-selection intent, MIDI-channel
selection intent, and session-exit intent, as long as that metadata remains
mock/passive-safe and does not imply real execution.

## Accepted Future Test Expectations

The future Packet 1B implementation must include tests for:

- importing `rytm_randomizer.behavior_menu_utility` prints nothing
- Packet 1A supported menu/status keys remain unchanged
- `T` returns deterministic target-selection intent
- `T` does not mutate target pad/channel state
- `T` does not prompt or block
- `C` returns deterministic MIDI-channel-selection intent
- `C` does not change MIDI channel state
- `C` does not open ports
- `C` does not prompt or block
- `Q` returns deterministic session-exit intent
- `Q` does not call `sys.exit`
- `Q` does not terminate the Python process
- unknown keys still fail safely
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- V1.34 reference remains untouched
- package metadata files remain absent unless separately approved

## Parallelization Decision

Parallel implementation remains not recommended for Packet 1B.

Reasons:

- write ownership is concentrated
- `T`, `C`, and `Q` share one utility/session vocabulary
- the safety semantics should stabilize in one small serial slice
- coordination overhead would outweigh any speed gain

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

- implement Packet 1B exactly as a tiny scoped behavior-intent packet
- pause at this accepted Packet 1B plan checkpoint
- write a short progress update before implementation

## Recommendation

Proceed next with Packet 1B implementation.

Implementation should be limited to:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`

Do not update closeout unless the implementation unexpectedly creates a new
test file, which is not recommended.

Do not add CLI wiring. Do not add real MIDI. Keep hardware off. Keep package
metadata absent.

## Decision

The V1.34 behavior parity Packet 1B utility/session plan is accepted.

The next recommended task is the tiny Packet 1B implementation for
deterministic `T`, `C`, and `Q` utility/session intent behavior.

Hardware remains off. No implementation is added by this review.
