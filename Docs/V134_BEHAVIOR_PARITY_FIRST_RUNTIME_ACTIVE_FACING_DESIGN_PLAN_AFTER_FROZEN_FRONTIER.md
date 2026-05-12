# V1.34 Behavior Parity First Runtime/Active-Facing Design Plan After Frozen Frontier

## 1. Purpose

Define the first runtime/active-facing design plan after Packet 12 report data
alignment and the frozen runtime-adjacent frontier.

This document is planning-only.

It does not implement runtime execution.

It does not implement active behavior.

It does not implement MIDI.

It does not open ports.

It does not require hardware.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this design slice:

- `bf2a44a Add behavior parity next phase selection review after frozen frontier`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 12 behavior-parity coverage report implemented and accepted
- Packet 12 behavior-parity report CLI visibility implemented and accepted
- Packet 12 report data alignment implemented and accepted
- user-facing progress/timeline update reviewed and accepted
- next-phase selection checkpoint reviewed and accepted
- `PZ`, `B`, and `L` runtime-adjacent safe-failure trio frozen for now
- first runtime/active-facing design plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Inputs

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PHASE_SELECTION_CHECKPOINT_AFTER_PACKET_12_REPORT_DATA_ALIGNMENT_AND_FROZEN_FRONTIER_REVIEW.md`

Accepted upstream selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PHASE_SELECTION_CHECKPOINT_AFTER_PACKET_12_REPORT_DATA_ALIGNMENT_AND_FROZEN_FRONTIER.md`

Related planning gates:

- `Docs/ACTIVE_LAYER_DESIGN_SPEC.md`
- `Docs/FUTURE_ACTIVE_TEST_PLAN.md`
- `Docs/FIRST_CANDIDATE_MOCK_ONLY_ACTIVE_TEST_DESIGN.md`

Accepted current frontier:

- `PZ`
- `B`
- `L`

These remain runtime-adjacent safe-failure coverage, not execution coverage.

## 4. Design Goal

Describe the first conceptual bridge from passive behavior-parity coverage
toward future runtime/active-facing work.

The bridge must remain:

- documentation-only in this slice
- mock-only or fake-provider-only before implementation
- separated from passive CLI browsing and reporting
- unable to open ports
- unable to send MIDI
- unable to mutate hardware

This plan exists to prevent the next phase from accidentally turning passive
metadata, preview, or reports into execution.

## 5. Runtime/Active-Facing Meaning

For this plan, runtime/active-facing means a future layer that may reason
about:

- operator intent
- selected command or profile key
- passive preview output
- target pad/channel scope
- safety envelope
- mock-only or fake-provider execution result
- later, and only after separate approval, active/hardware-facing execution

Runtime/active-facing does not mean real MIDI.

Runtime/active-facing does not mean hardware validation.

Runtime/active-facing does not mean CLI execution wiring.

## 6. Proposed Conceptual Responsibilities

Future design may introduce conceptual responsibilities such as:

- RuntimeIntent
  - exact requested key
  - source kind
  - target pad/channel concept
  - preview reference
  - operator confirmation state
- RuntimeSafetyEnvelope
  - mock-only flag
  - sends_real_midi flag
  - ports_allowed flag
  - hardware_required flag
  - forbidden scope markers
- RuntimePlanPreview
  - human-readable action summary
  - expected safe-failure result
  - reason execution is not performed
- MockRuntimeProvider
  - future fake provider only
  - no real ports
  - no real MIDI
  - no hardware
- ActiveBoundaryAdapter
  - future boundary concept only
  - not implemented here
  - not connected to CLI here

These names are conceptual placeholders for planning.

They are not implementation requirements in this slice.

## 7. Relationship To Passive CLI

The passive CLI remains read-only.

These commands must remain passive:

- `report`
- `list-commands`
- `list-scenes`
- `list-group-profiles`
- `search-commands`
- `search-scenes`
- `search-group-profiles`
- `inspect-command`
- `inspect-scene`
- `inspect-group-profile`
- `preview-command`
- `preview-scene`
- `preview-group-profile`
- `mock-mapper-report`
- `behavior-parity-report`

Future runtime/active-facing design must not change these commands into
execution commands.

Future runtime/active-facing design must not make these commands construct a
real MIDI sender, open ports, or mutate state.

## 8. Relationship To Current Runtime-Adjacent Coverage

The current runtime-adjacent safe-failure trio remains:

- `PZ`
- `B`
- `L`

The trio proves selected runtime-adjacent behavior can be represented safely
as non-executing, mock-only, or safe-failure coverage.

The trio does not authorize:

- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation

The fourth runtime-adjacent candidate remains parked.

## 9. First Design Boundary

The first runtime/active-facing boundary should be a planning boundary, not an
execution boundary.

It should define how future code would answer:

- What did the operator intend?
- What passive preview already exists?
- What exact key or profile is in scope?
- What pad/channel concept is in scope?
- What safety envelope applies?
- Why is execution blocked?
- What would a mock-only provider record later?

It should not send anything.

It should not open anything.

It should not mutate anything.

## 10. Safe-Failure Requirements

Any future runtime/active-facing implementation must fail safely when:

- the key is unknown
- the key is unsupported
- the source kind is unsupported
- target pad/channel scope is unclear
- arming is missing
- the requested behavior is a scene
- the requested behavior is global mutation
- the requested behavior touches Pads 5-12
- the requested behavior touches Analog Four
- the requested behavior requires SysEx
- the requested behavior implies project, kit, pattern, transport, or clock
  mutation

Safe failure means:

- no messages emitted
- no ports opened
- no MIDI sent
- no runtime state mutated
- no hardware required
- clear reason returned or reported

## 11. Candidate Scope For Future Planning

The safest future planning candidate remains:

- group profile `"2"` / My BD Hard

Reasons:

- existing passive metadata
- existing mock mapper support
- existing first-candidate mock-only active test design
- validated Pad 1 concept
- no profile `4` requirement

This document does not implement that candidate.

It only acknowledges it as the likely first planning reference.

## 12. Parked Scope

The following remain parked:

- fourth runtime-adjacent candidate
- profile `4` mock mapper support
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- scene execution
- global mutation execution
- runtime mutation
- active CLI commands
- real MIDI adapter usage
- hardware validation

## 13. Forbidden In This Slice

This slice adds no:

- code changes
- test changes
- fixture changes
- closeout script changes
- package metadata changes
- CLI changes
- runtime module
- active boundary module
- fake provider module
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 14. Preconditions Before Any Implementation Plan

Before any implementation plan for this design:

- clean Git status
- full closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this design plan is reviewed and accepted
- implementation scope is separately selected
- implementation plan is separately written
- implementation plan is separately reviewed
- all implementation remains mock-only or fake-provider-only first
- passive CLI remains read-only
- no real MIDI libraries are imported
- no ports are opened
- no hardware is required

## 15. Verification Expectations For Future Work

Future work derived from this plan must prove:

- passive CLI commands remain passive
- passive imports remain side-effect free
- unknown keys fail safely
- unsupported keys fail safely
- missing arming fails safely if arming is introduced
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- V1.34 reference remains untouched
- package metadata remains untouched
- profile `4` remains parked unless separately approved
- hardware remains off

## 16. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this design plan
- pause at this clean design checkpoint
- create a narrower mock-only/fake-provider implementation plan after review
- write a project-level roadmap update if more orientation is needed

## 17. Recommendation

Review and accept this design plan next.

After review, decide whether to create a narrow mock-only/fake-provider
implementation plan.

Do not implement runtime execution yet.

Do not add CLI execution wiring yet.

Do not add real MIDI.

Do not open ports.

Do not turn on hardware.

## 18. Decision

The first runtime/active-facing design plan is documented.

The current runtime-adjacent safe-failure trio remains frozen:

- `PZ`
- `B`
- `L`

The fourth runtime-adjacent candidate remains parked.

Profile `4` mock mapper support remains parked.

Hardware remains off.

No implementation in this slice.

## 19. Review Status

This design plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_FIRST_RUNTIME_ACTIVE_FACING_DESIGN_PLAN_AFTER_FROZEN_FRONTIER_REVIEW.md`

The review accepts this document as the current planning bridge from read-only
behavior-parity coverage toward future runtime/active-facing work.

The next selected branch is:

- docs-only narrow mock-only/fake-provider implementation plan

The review keeps the current runtime-adjacent safe-failure trio frozen:

- `PZ`
- `B`
- `L`

The review keeps the fourth runtime-adjacent candidate parked.

The review keeps profile `4` mock mapper support parked.

No runtime/active-facing design implementation, runtime module, active boundary
module, fake provider module, tests, fixture changes, CLI changes, CLI
execution wiring, dispatch, command execution, runtime execution, MIDI, ports,
package metadata changes, active behavior, or hardware behavior is authorized
by the review.
