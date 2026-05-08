# Behavior Parity Roadmap

## 1. Purpose

Define the documentation-only roadmap for future runtime behavior parity with
the protected V1.34 reference.

This roadmap clarifies the gap between the current passive/mock foundation and
any future modular behavior that would reproduce V1.34 operator behavior.

This document does not implement runtime behavior, tests, command dispatch,
scene execution, MIDI, port opening, package metadata changes, active CLI
commands, or hardware validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 03afb56 Add next strengthening sequence planning gate review

Current phase:

- Passive/Mock Foundation Phase
- Packets 1 through 4 active-boundary strengthening complete and reviewed
- next strengthening sequence planning gate accepted
- behavior-parity roadmap now being documented
- no real MIDI or hardware validation started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Foundation

The accepted current foundation includes:

- protected V1.34 reference
- complete captured V1.34 passive command metadata map
- passive registry and lookup/report layers
- passive CLI report/list/search/inspect/preview paths
- passive `mock-mapper-report`
- passive `active-boundary-report`
- test-only mock MIDI scaffold
- test-only mock message mapper
- mock mapper report
- mock-first active boundary for group profile `"2"` / My BD Hard only
- read-only active-boundary report
- fake-provider-only real MIDI adapter boundary
- real MIDI import safety tests
- real MIDI passive CLI safety tests
- real MIDI adapter boundary tests
- Packets 1 through 4 active-boundary strengthening sequence complete and
  reviewed

## 4. What Behavior Parity Means

Behavior parity means a future modular system should intentionally reproduce
the validated V1.34 operator behavior before replacing or competing with the
protected V1.34 reference.

Behavior parity is broader than passive command metadata coverage. It includes:

- command semantics
- state transitions
- target pad and channel selection behavior
- anchor assumptions
- current-profile behavior
- selected isolated pad behavior
- mutation-depth semantics
- page-specific mutation meaning
- scene and group intent
- undo and commit expectations
- safe failure and no-op behavior
- hardware-facing preconditions

Behavior parity does not mean immediate hardware execution.

## 5. Current Non-Parity

The project currently has complete passive visibility for the captured V1.34
operator command surface, but modular runtime behavior parity is not
implemented.

The current modular system still has no:

- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- current-profile mutation execution
- selected-profile runtime mutation
- anchor loading execution
- profile rotation execution
- undo/commit runtime behavior
- MIDI sending
- MIDI port opening
- hardware mutation
- SysEx writes
- hardware validation

The passive CLI can report, list, search, inspect, preview, and show read-only
mock/active-boundary reports. It cannot perform V1.34 commands.

## 6. Behavior Domains To Map

Future behavior-parity planning should map these domains before any modular
runtime implementation:

- operator command routing
- menu and status commands
- target pad and MIDI channel selection
- anchor and profile load behavior
- group profile and full group layout actions
- scene command behavior
- mutation-depth semantics
- guarded main-prompt depth entries
- Pad 1 BD engine lanes and BD FM/Plastic/Silky submenus
- Pad 2 secondary percussion lane
- Pad 3 SY Raw lane
- Pad 4 BD Acoustic lane
- selected isolated pad mutations
- current anchor reporting
- script state reporting
- undo and commit behavior
- quit, back, and safe no-op behavior
- hardware-facing preconditions

## 7. Needed Parity Artifacts Before Implementation

Before behavior-preserving implementation work begins, the project should have:

- a behavior parity matrix
- command-by-command behavior notes for execution-facing commands
- a state model sketch
- an anchor lifecycle model
- a mutation depth model
- a scene and group intent model
- undo and commit semantics
- safe failure and no-op semantics
- a test strategy for behavior parity
- mappings from passive metadata keys to intended behavior domains

These artifacts should remain documentation-only until separately reviewed and
accepted.

## 8. Recommended Roadmap Phases

Recommended behavior-parity phases:

- Phase A: docs-only V1.34 behavior parity matrix plan
- Phase B: docs-only state, anchor, and selection model
- Phase C: docs-only mutation and scene semantics roadmap
- Phase D: mock-only behavior-parity test plan
- Phase E: mock/fake-provider behavior tests, later and separately approved
- Phase F: runtime implementation planning, much later
- Phase G: real MIDI and hardware planning, much later and behind separate
  gates

## 9. First Recommended Next Slice

The next recommended task is a documentation-only review and acceptance gate
for this roadmap.

After review, the next planning slice should likely be:

- `Docs/V134_BEHAVIOR_PARITY_MATRIX_PLAN.md`

That plan should define the future matrix columns, command grouping, behavior
domains, and parity status values before any implementation or test changes.

## 10. Work Not Authorized By This Roadmap

This roadmap does not authorize:

- implementation
- tests
- runtime code changes
- command dispatch
- command execution
- scene execution
- prompt/input loop execution
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata changes
- MIDI port discovery
- MIDI port opening
- MIDI sending
- active CLI commands
- `execute-command`
- `send-command`
- `hardware-test`
- hardware behavior
- hardware mutation
- hardware validation
- profile `"3"` active-boundary support
- profile `"4"` implementation
- Analog Four support
- Pads 5-12 support
- machine/profile expansion
- SysEx
- GUI/capture

## 11. Parallelization Position

No parallel implementation is recommended for the immediate next slice.

Behavior-parity work can later be split into independent documentation lanes,
such as scenes, mutation depths, anchor state, and menu/status behavior.

Parallel implementation should wait until:

- each lane has a reviewed plan
- file ownership is disjoint
- closeout remains the synchronization point
- no lane touches real MIDI, ports, active CLI behavior, or hardware-facing
  scope without explicit approval

## 12. Decision

The behavior-parity roadmap is documented as the preferred next branch after
the accepted next strengthening sequence planning gate.

Hardware remains off.

No implementation is added in this slice.
