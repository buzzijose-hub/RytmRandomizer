# V1.34 Behavior Parity Packet 4 Scene And Group Intent Plan

## 1. Purpose

Define the next behavior-parity implementation packet plan after the accepted
behavior-parity progress report after Packet 3.

Packet 4 targets scene and group intent behavior from the accepted V1.34
behavior parity matrix. This is a plan only. It does not implement runtime
behavior, tests, CLI wiring, dispatch, scene execution, group mutation
execution, MIDI, port opening, package metadata, active CLI behavior, or
hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `c115912 Add behavior parity progress report review after Packet 3`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- behavior-parity progress report after Packet 3 accepted
- Packet 4 scene and group intent planning now beginning

Hardware status:

- Analog Rytm MKII off.
- Analog Four MKII off.
- Hardware not required.

## 3. Packet Identity

Packet name:

- Packet 4: Scene And Group Intent Behavior Parity

Packet intent:

- model scene and group intent as deterministic read-only behavior metadata
- keep scene and group behavior separate from execution
- preserve `forbidden-early-scope` semantics for scene and group mutation
- avoid real MIDI, ports, active CLI behavior, package metadata, and hardware
- keep future implementation narrow enough for TDD and closeout

## 4. Accepted Sources

This packet plan is based on:

- `Docs/V134_BEHAVIOR_PARITY_MATRIX_SCENE_GROUP_INTENT_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_SCENE_GROUP_INTENT_SLICE_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_3.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_3_REVIEW.md`
- scene metadata in `rytm_randomizer/scenes.py`
- group command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference as the future behavior source, not edited

## 5. Planned Full Packet 4 Scope

The full Packet 4 planning scope comes from the accepted scene and group
intent matrix slice.

Scene intent commands:

- `S0`
- `S1`
- `S1A`
- `S1B`
- `S2`
- `S2A`
- `S2B`
- `S3`
- `S3A`
- `S3B`
- `S4`
- `S4A`
- `S4B`
- `S5`

Four-pad group mutation intent commands:

- `X`
- `D`
- `I`
- `4`

Lane-aware group mutation intent commands:

- `Y`
- `V`
- `N`

## 6. Packet 4A Recommended Implementation Scope

The first future implementation packet should be smaller than the full Packet
4 matrix slice.

Recommended initial implementation scope:

- read-only scene intent behavior for `S0`, `S1`, `S1A`, `S1B`, `S2`, `S2A`,
  `S2B`, `S3`, `S3A`, `S3B`, `S4`, `S4A`, `S4B`, and `S5`
- deterministic result objects or plain structured dictionaries
- copied metadata from `SCENE_COMMANDS`
- no scene execution
- no group mutation execution
- no command dispatch
- no state mutation
- no prompt loop
- no CLI wiring
- no real MIDI
- no ports
- no hardware requirement

Reason:

- Scene metadata already exists as a read-only passive registry.
- Scene intent is easier to model safely than group mutation execution.
- The future result can record scene action and scope without executing it.
- Four-pad group mutation and lane-aware group mutation are higher-risk and
  should remain deferred until scene intent behavior is stable.

## 7. Deferred Packet 4 Scope

Deferred within Packet 4:

- `X`: balanced four-lane mutate full 4-pad group
- `D`: deeper four-lane mutation, Pads 2-4 pushed harder
- `I`: intense / controlled chaos four-lane mutation
- `4`: harder / wild four-lane mutation
- `Y`: lane-aware SRC/morph mutation on all 4 group pads
- `V`: lane-aware filter mutation on all 4 group pads
- `N`: lane-aware grit mutation on all 4 group pads

Deferred concepts:

- group mutation execution
- lane-aware group mutation execution
- scene selection runtime state
- four-pad group runtime state
- four-pad anchor/profile runtime state
- lane model
- command dispatch
- scene execution
- MIDI or hardware behavior

These remain future behavior gaps and require a separate plan and review
before implementation.

## 8. Proposed Future File Ownership

The first future implementation packet should have a narrow write set.

Allowed future implementation files:

- `rytm_randomizer/behavior_scene_group.py`
- `tests/test_behavior_scene_group.py`
- `Scripts/closeout_check.ps1`, only to add the new test file to closeout

Allowed future fixture files only if deterministic text output is introduced:

- `tests/fixtures/behavior_scene_group_*_expected.txt`

Files that should remain untouched in the first implementation packet:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command files or paths
- runtime execution/dispatch/MIDI logic outside the proposed packet files

## 9. Proposed Future Behavior Shape

Future implementation may define a small read-only behavior result shape with
fields such as:

- command key
- scene name
- scene description
- scene action
- scene scope
- behavior family, such as `scene-group/scene-intent`
- reason, such as `supported_scene_intent`
- four-pad group state required: metadata only
- scene execution available: false
- state changed: false
- prompt required: false
- dispatches command: false
- executes scene: false
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

Names are planning vocabulary only.

Do not implement this shape in this slice.

## 10. Safe Failure Expectations

The future packet should fail safely for:

- unknown command keys
- group mutation keys until separately approved
- lane-aware group mutation keys until separately approved
- unsupported metadata shape
- missing scene metadata
- missing optional group state

Safe failure means:

- deterministic result or deterministic exception type if tests choose one
- no state mutation
- no prompt loop
- no dispatch
- no scene execution
- no MIDI
- no port opening
- no CLI active behavior
- no hardware requirement

## 11. Required Future Tests

Future Packet 4A tests should verify:

- importing the new module prints nothing
- supported scene keys return deterministic read-only behavior results
- `S0` returns home/clean scene intent without anchor loading
- `S1A` returns Rolling Light scene intent without scene execution
- `S4B` returns Wild Maximum scene intent while remaining forbidden for early
  hardware scope
- `S5` returns Back to Clean scene intent without anchor loading
- all scene results include copied scene metadata
- repeated scene evaluations are deterministic
- unknown keys fail safely
- `X`, `D`, `I`, `4`, `Y`, `V`, and `N` remain deferred or fail safely until
  separately approved
- Packet 1 behavior remains unchanged
- Packet 2 behavior remains unchanged
- Packet 3 behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- V1.34 reference remains untouched
- package metadata files remain absent unless separately approved
- no Analog Four or Pads 5-12 support is exposed

## 12. Closeout Expectations For Future Packet 4A

The future implementation packet must run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected closeout state:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent unless separately approved
- git status is clean after commit

## 13. Parallelization Decision

Do not parallelize the first Packet 4A implementation.

Reason:

- file ownership is concentrated in one new helper module and one test file
- scene intent result vocabulary should stabilize before group mutation
  behavior is planned
- group mutation and lane-aware group mutation remain deferred
- parallel workers would add coordination overhead before the scene/group
  behavior shape exists

Parallel implementation can be reconsidered after Packet 4A lands cleanly and
Packet 4B or later scope is separately planned.

## 14. Explicit Non-Goals

- no implementation in this slice
- no tests in this slice
- no scene execution
- no group mutation execution
- no command dispatch
- no command execution
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

## 15. Stop Conditions

Stop before future implementation if:

- Packet 4A scope grows beyond read-only scene intent behavior
- group mutation behavior is required in Packet 4A
- lane-aware group mutation behavior is required in Packet 4A
- scene execution is required
- CLI wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## 16. Next Safe Options

Safe next options:

- docs-only review/acceptance of this Packet 4 scene and group intent plan
- pause at this planning checkpoint
- if accepted, implement only Packet 4A as a tiny read-only scene intent
  behavior shape

## 17. Recommendation

Review and accept this Packet 4 plan next.

After acceptance, implement only Packet 4A as a tiny read-only scene intent
behavior shape.

Keep group mutation and lane-aware group mutation deferred unless separately
approved.

Keep hardware off.

Keep package metadata absent.

## 18. Decision

Packet 4 planning is documented.

The first future implementation target should be Packet 4A: read-only scene
intent behavior for `S0`, `S1`, `S1A`, `S1B`, `S2`, `S2A`, `S2B`, `S3`,
`S3A`, `S3B`, `S4`, `S4A`, `S4B`, and `S5`.

No implementation is added.
