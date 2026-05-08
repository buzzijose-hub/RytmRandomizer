# V1.34 Behavior Parity Matrix Plan

## 1. Purpose

Define the documentation-only plan for a future V1.34 behavior parity matrix.

The future matrix should make the gap between captured passive command
metadata and modular runtime behavior parity explicit, command by command and
domain by domain.

This plan defines the matrix shape, source documents, status language, command
grouping, and safe build order. It does not populate the full matrix in this
slice.

This document adds no implementation, tests, runtime behavior, command
dispatch, scene execution, MIDI, port opening, package metadata changes,
active CLI commands, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- af0deee Add behavior parity roadmap review

Current phase:

- Passive/Mock Foundation Phase
- Packets 1 through 4 active-boundary strengthening complete and reviewed
- next strengthening sequence planning gate accepted
- behavior-parity roadmap created and accepted
- V1.34 behavior parity matrix plan now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Matrix Goal

The future behavior parity matrix should answer these questions:

- What V1.34 operator command or behavior is being represented?
- What passive metadata already captures it?
- What behavior domain does it belong to?
- What state, anchor, profile, pad, channel, depth, or scene assumptions does
  it depend on?
- What future modular behavior would be required for parity?
- What is intentionally still absent?
- What tests or planning artifacts are required before implementation?

The matrix should keep future implementation honest by showing the difference
between visibility and behavior.

## 4. Source Documents And Data

The future matrix should be built from existing sources only.

Accepted sources:

- `rytm_hybrid_randomizer_v134.py` as protected behavior reference, read-only
- `Docs/V134_OPERATOR_COMMAND_SURFACE_REFERENCE.md`
- `Docs/V134_UNCAPTURED_BEHAVIOR_REVIEW.md`
- `Docs/BEHAVIOR_PARITY_ROADMAP.md`
- `Docs/BEHAVIOR_PARITY_ROADMAP_REVIEW.md`
- `rytm_randomizer/commands.py` passive command metadata
- `rytm_randomizer/scenes.py` passive scene metadata
- `rytm_randomizer/group_profiles.py` passive group profile metadata
- passive registry and lookup/report outputs
- passive CLI report/list/search/inspect/preview outputs

The matrix plan does not authorize editing the protected V1.34 reference or
metadata sources.

## 5. Proposed Matrix Columns

The future matrix should use deterministic columns:

- command key
- V1.34 label or operator-facing description
- passive metadata source
- passive metadata status
- behavior domain
- command family
- menu or page context
- target pad scope
- target channel scope
- state dependencies
- anchor/profile dependencies
- mutation-depth dependencies
- scene/group intent
- hardware/MIDI implication
- safe failure or no-op expectation
- current modular behavior status
- parity gap summary
- required future artifact
- required future test category
- implementation authorization status
- notes

The column names should stay stable once accepted so later matrix updates can
be reviewed cleanly.

## 6. Proposed Status Values

Use small, deterministic status values.

Passive metadata status:

- captured
- not-applicable
- review-needed

Current modular behavior status:

- passive-only
- mock-only
- fake-provider-only
- not-implemented
- out-of-scope

Implementation authorization status:

- blocked
- documentation-only
- test-plan-needed
- test-only-approved
- implementation-plan-needed
- separately-approved

Hardware/MIDI implication:

- none
- future-mock-only
- future-fake-provider-only
- future-real-midi-risk
- forbidden-early-scope

These status values are planning vocabulary only. They do not create runtime
behavior.

## 7. Proposed Behavior Domains

The future matrix should group commands into behavior domains before any
implementation planning.

Initial behavior domains:

- operator routing
- menu/status display
- target pad and channel selection
- profile selection
- anchor load and return
- current anchor reporting
- script state reporting
- single-profile mutation
- current-profile mutation
- selected isolated pad mutation
- group layout and group anchors
- group mutation
- scene selection and scene intent
- depth selection and guarded numeric input
- BD engine navigation
- BD FM discovery
- BD Plastic discovery
- BD Silky discovery
- Pad 2 secondary percussion lane
- Pad 3 SY Raw lane
- Pad 4 BD Acoustic lane
- waveform and discovery boundaries
- undo and commit behavior
- quit/back/no-op behavior
- hardware-facing preconditions

The matrix can add a new domain only through a later reviewed matrix update.

## 8. Proposed Command Families

The future matrix should use command families to make review easier.

Initial command families:

- main prompt navigation
- Pad 1 BD anchors and mutation
- BD FM lane
- BD Plastic lane
- BD Silky lane
- Pad 2 lane
- Pad 3 lane
- Pad 4 lane
- four-pad group layout and anchors
- four-pad group mutation
- scenes
- isolated pad mutation
- profile selection and anchors
- legacy mutation
- guarded depth inputs
- utility and state
- quit

Families are documentation labels only. They do not expand machine/profile
scope.

## 9. Matrix Build Order

Recommended build order:

1. Define and review the matrix schema.
2. Add the first docs-only matrix section for passive command families.
3. Add menu/status and utility command rows.
4. Add anchor/profile command rows.
5. Add mutation-depth and guarded numeric input rows.
6. Add scene and group intent rows.
7. Add lane-specific rows for Pads 1 through 4.
8. Add undo/commit/state rows.
9. Review the complete matrix before any mock-only behavior test planning.

Each build step should stay documentation-only until separately approved.

## 10. First Matrix Slice Recommendation

After this plan is reviewed and accepted, the first matrix slice should be:

- docs-only matrix schema and first rows for menu/status and utility commands

Reason:

- these commands are easier to reason about than mutation or scene behavior
- they clarify routing/status expectations before state-changing behavior
- they keep hardware-facing behavior out of scope

The first matrix slice should not include runtime code, tests, MIDI, ports,
active CLI behavior, dispatch, command execution, or hardware validation.

## 11. Parallelization Position

No parallel implementation is recommended for the immediate next slice.

Future documentation-only matrix population could be parallelized by domain
only after:

- the matrix schema is accepted
- domain ownership is disjoint
- closeout remains the synchronization point
- no lane edits code or tests
- no lane touches real MIDI, ports, active CLI behavior, or hardware-facing
  scope

The first actual matrix slice should be done serially to keep the schema stable.

## 12. Stop Conditions

Stop immediately if any matrix work introduces or requests:

- runtime code changes
- tests
- command dispatch
- command execution
- scene execution
- real MIDI
- `mido`
- `rtmidi`
- package metadata changes
- port discovery
- port opening
- MIDI sending
- active CLI commands
- hardware behavior
- hardware validation
- profile `"3"` active-boundary support
- profile `"4"` implementation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- SysEx
- GUI/capture

## 13. Decision

The V1.34 behavior parity matrix plan is documented.

The next recommended task is a documentation-only review and acceptance gate
for this plan.

After review, the next likely planning artifact is a docs-only matrix schema
and first-row slice.

Hardware remains off.

No implementation is added in this slice.
