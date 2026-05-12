# V1.34 Behavior Parity Next Branch Selection After Runtime Plan Scaffold Review

## 1. Purpose

Select the next safe branch after accepting the mock-only runtime plan scaffold.

This is a documentation-only selection checkpoint.

It does not implement the selected branch.

It adds no code, tests, fixture changes, closeout script changes, CLI changes,
CLI execution wiring, runtime execution, dispatch, command execution, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this selection slice:

- `27cf313 Add runtime plan scaffold checkpoint review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- runtime plan scaffold implemented
- runtime plan scaffold checkpoint reviewed and accepted
- next branch now being selected

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Current Baseline

Accepted runtime plan scaffold:

- `rytm_randomizer/runtime_plan.py`
- `tests/test_runtime_plan.py`
- `Scripts/closeout_check.ps1`

Accepted review gate:

- `Docs/V134_BEHAVIOR_PARITY_RUNTIME_PLAN_SCAFFOLD_CHECKPOINT_REVIEW.md`

Accepted runtime plan baseline:

- mock-only
- inert
- closeout-covered by `=== Test: Runtime Plan ===`
- group profiles `2` and `3` return blocked previews only
- unknown keys fail safely
- unsupported source kinds fail safely
- profile `4` remains parked
- no preview executes

## 4. Candidate Next Branches

Safe candidate branches:

- Option A: pause at the accepted runtime plan scaffold baseline
- Option B: create a docs-only first runtime plan expansion design
- Option C: create a docs-only fake-provider recording expansion design
- Option D: create a broader user-facing progress/timeline update
- Option E: return to behavior-parity packet implementation planning

## 5. Selected Next Branch

Selected next branch:

- docs-only first runtime plan expansion design

Reason:

- the runtime plan scaffold is now implemented and accepted
- the next move should clarify how the runtime plan may expand before any
  additional implementation
- a design gate is safer than adding more runtime-facing code immediately
- profile `4`, a fourth runtime-adjacent candidate, CLI execution, real MIDI,
  and hardware behavior remain parked

## 6. Selected Branch Boundaries

The selected branch must remain documentation-only.

The selected branch may discuss:

- what the next runtime plan expansion should represent
- how `RuntimeIntent` should stay separate from execution
- how blocked previews should remain the default
- how fake-provider records should remain in memory only
- how future tests should continue proving no MIDI, no ports, and no CLI
  execution
- whether any later implementation should strengthen safe-failure metadata

The selected branch must not implement:

- new runtime plan code
- new tests
- fake-provider expansion
- active boundary expansion
- CLI execution wiring
- dispatch
- command execution
- MIDI
- ports
- hardware behavior

## 7. Parked Scope

Still parked:

- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- active CLI commands
- real MIDI
- hardware validation

## 8. Confirmed Absent Behavior

This selection checkpoint adds no:

- real MIDI
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- active CLI execution
- `execute-command`
- `send-command`
- `hardware-test`
- runtime mutation
- dispatch
- command execution
- scene execution
- profile `4` mock mapper support
- fourth runtime-adjacent candidate
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture
- package metadata changes
- active behavior
- hardware behavior

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 9. Recommended Next Task

Create the docs-only first runtime plan expansion design.

The design should remain planning-only and should not authorize implementation
by itself.

## 10. Decision

The next branch is selected:

- docs-only first runtime plan expansion design

Hardware remains off.

No implementation in this slice.
