# V1.34 Behavior Parity Packet 5 Pad 1 Lane Behavior Plan

## 1. Purpose

Define the next behavior-parity implementation packet plan after the accepted
next packet planning gate review.

Packet 5 targets Pad 1 lane behavior from the accepted V1.34 behavior parity
matrix and next-packet planning gate. This is a plan only. It does not
implement runtime behavior, tests, CLI wiring, dispatch, command execution,
lane mutation execution, MIDI, port opening, package metadata, active CLI
behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `cccde44 Add behavior parity next packet planning gate review`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity matrix documented and reviewed
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful read-only anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- behavior-parity progress report after Packet 4 accepted
- next packet planning gate created and accepted
- Packet 5 Pad 1 lane behavior planning now beginning

Hardware status:

- Analog Rytm MKII off.
- Analog Four MKII off.
- Hardware not required.

## 3. Packet Identity

Packet name:

- Packet 5: Pad 1 Lane Behavior Parity

Packet intent:

- model Pad 1 lane behavior as deterministic read-only intent metadata
- keep Pad 1 lane behavior separate from execution
- preserve existing Packet 1 through Packet 4 behavior
- preserve passive CLI behavior
- avoid real MIDI, ports, active CLI behavior, package metadata, and hardware
- keep future implementation narrow enough for TDD and closeout

## 4. Accepted Sources

This packet plan is based on:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE.md`
- `Docs/V134_BEHAVIOR_PARITY_NEXT_PACKET_PLANNING_GATE_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_PAD1_LANE_BEHAVIOR_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_PAD1_LANE_BEHAVIOR_SLICE_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_4.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_PROGRESS_REPORT_AFTER_PACKET_4_REVIEW.md`
- Pad 1 command metadata in `rytm_randomizer/commands.py`
- protected V1.34 reference as the future behavior source, not edited

## 5. Planned Full Packet 5 Scope

The full Packet 5 planning surface covers existing Pad 1 lane behavior
vocabulary from the accepted planning gate.

Pad 1 current BD engine status and mutation:

- `BR`: rotate Pad 1 to the next profiled BD engine
- `BM`: safely mutate the currently loaded Pad 1 BD engine

Pad 1 BD FM lane:

- `FM`: show BD FM menu/status
- `FT`: BD FM tone/FM discovery
- `FK`: BD FM kick/body discovery
- `FG`: BD FM grit discovery
- `FZ`: return Pad 1 BD FM to anchor

Pad 1 BD Plastic lane:

- `BP`: load Pad 1 BD Plastic profiled anchor
- `PD`: show BD Plastic menu/status
- `PT`: BD Plastic tone/modulation discovery
- `PK`: BD Plastic kick/body discovery
- `PX`: BD Plastic rubber/experimental discovery
- `PBH`: return Pad 1 BD Plastic to anchor

Pad 1 BD Silky lane:

- `BI`: load Pad 1 BD Silky profiled anchor
- `SM`: show BD Silky menu/status
- `ST`: BD Silky smooth tone discovery
- `SK`: BD Silky kick/body discovery
- `SC`: BD Silky click/dust discovery
- `SBH`: return Pad 1 BD Silky to anchor

## 6. Already Covered Context

Some Pad 1-adjacent commands already have read-only behavior elsewhere and
must not be reimplemented by Packet 5:

- `FM`, `PD`, and `SM` are already covered as menu/status behavior in Packet 1.
- `BH`, `BC`, `BS`, and `BF` are already covered as anchor/profile behavior in
  Packet 2.
- generic mutation-depth commands are already covered in Packet 3.

Packet 5 may reference those commands as context, but future Packet 5
implementation should not duplicate or change their existing behavior.

## 7. Packet 5A Recommended Implementation Scope

The first future implementation packet should be smaller than the full Packet
5 planning surface.

Recommended initial implementation scope:

- Packet 5A: read-only Pad 1 current BD engine lane intent for `BR` and `BM`

Packet 5A should model:

- `BR`: rotation intent for the current Pad 1 BD engine lane
- `BM`: safe current-engine mutation intent for the current Pad 1 BD engine
  lane

Reason:

- `BR` and `BM` are the smallest Pad 1-specific lane behavior pair.
- They are closer to the fun sound-design loop without requiring actual
  mutation execution.
- They avoid broad BD FM, BD Plastic, and BD Silky discovery semantics for the
  first Packet 5 slice.
- They can establish the Pad 1 lane result vocabulary before deeper lane
  sub-slices are planned.

## 8. Deferred Packet 5 Scope

Deferred within Packet 5:

- BD FM discovery and anchor-return intent:
  - `FT`
  - `FK`
  - `FG`
  - `FZ`
- BD Plastic load/discovery/anchor-return intent:
  - `BP`
  - `PT`
  - `PK`
  - `PX`
  - `PBH`
- BD Silky load/discovery/anchor-return intent:
  - `BI`
  - `ST`
  - `SK`
  - `SC`
  - `SBH`

Deferred concepts:

- runtime engine rotation
- runtime current-engine mutation
- runtime discovery mutation
- runtime anchor return
- Pad 1 selected-engine state
- Pad 1 lane mode state
- mutation depth prompts
- command dispatch
- MIDI or hardware behavior

These remain future behavior gaps and require separate plans and reviews
before implementation.

## 9. Proposed Future File Ownership

The first future implementation packet should keep a narrow write set.

Allowed future implementation files:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`
- `Scripts/closeout_check.ps1`, only to add the new test file to closeout

Allowed future fixture files only if deterministic text output is introduced:

- `tests/fixtures/behavior_pad1_lane_*_expected.txt`

Files that should remain untouched in the first implementation packet:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/active_boundary.py`
- `rytm_randomizer/active_boundary_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command files or paths
- runtime execution/dispatch/MIDI logic outside the proposed packet files

## 10. Proposed Future Behavior Shape

Future implementation may define a small read-only behavior result shape such
as `Pad1LaneBehaviorResult`.

Planned result fields may include:

- command key
- label
- behavior family, such as `pad1-lane/current-bd-engine`
- accepted
- reason
- target pad
- lane
- lane action
- engine dependency
- depth dependency
- display lines
- state changed
- prompt required
- dispatches command
- executes command
- mutates lane state
- sends real MIDI
- opens ports
- hardware required
- active behavior
- metadata

Names are planning vocabulary only. Do not implement this shape in this slice.

## 11. Planned Packet 5A Semantics

Future `BR` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/current-bd-engine`
- `reason`: `supported_pad1_current_engine_lane_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD engine`
- `lane_action`: `rotate_profiled_bd_engine`
- current Pad 1 engine state dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Future `BM` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/current-bd-engine`
- `reason`: `supported_pad1_current_engine_lane_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD engine`
- `lane_action`: `safe_current_engine_mutation`
- current Pad 1 engine state dependency recorded only
- future safe mutation depth dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

## 12. Planned Metadata Contract

Future Packet 5A metadata should be copied from `PAD1_COMMANDS` and may
include:

- `source`: `PAD1_COMMANDS`
- `source_command_type`
- `source_command_scope`
- `source_v134_reference_command`
- `source_scaffold_only`
- `target_pad`: `1`
- `lane`: `pad_1_bd_engine`
- `lane_action`
- `requires_current_engine_state`
- `requires_depth_selection`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`

Suggested deterministic lane actions:

- `BR`: `rotate_profiled_bd_engine`
- `BM`: `safe_current_engine_mutation`

## 13. Planned Display Contract

Future display lines should remain passive and unambiguous, such as:

- `<key>: <label>`
- `Read-only Pad 1 lane intent.`
- `Target pad: 1`
- `Lane: Pad 1 BD engine`
- `Lane action: <lane action>`
- `Current-engine dependency is recorded only.`
- `No prompt would run.`
- `No state would change.`
- `No command would dispatch.`
- `No command would execute.`
- `No MIDI would be sent.`
- `No ports would be opened.`
- `No hardware would be required.`

## 14. Safe Failure Expectations

The future Packet 5A implementation should fail safely for:

- unknown command keys
- deferred BD FM discovery keys
- deferred BD Plastic lane keys
- deferred BD Silky lane keys
- already-covered Packet 1 menu/status keys
- already-covered Packet 2 anchor/profile keys
- unsupported command metadata
- missing Pad 1 metadata

Safe failure means:

- deterministic result
- `accepted`: `False`
- no prompt loop
- no dispatch
- no command execution
- no runtime state mutation
- no Pad 1 lane mutation
- no MIDI
- no port opening
- no CLI active behavior
- no hardware requirement

## 15. Required Future TDD Steps

Future implementation should use a red/green flow.

### Step 1: Write Failing Packet 5A Tests

Create `tests/test_behavior_pad1_lane.py`.

Add tests for:

- importing `rytm_randomizer.behavior_pad1_lane` prints nothing
- `BR` returns accepted read-only Pad 1 current-engine rotation intent
- `BM` returns accepted read-only Pad 1 current-engine mutation intent
- `BR` and `BM` copy metadata from `PAD1_COMMANDS`
- metadata is copied and immutable
- repeated `BR` and `BM` evaluations are deterministic
- deferred Packet 5 keys fail safely
- unknown keys fail safely
- Packet 1 behavior remains unchanged
- Packet 2 behavior remains unchanged
- Packet 3 behavior remains unchanged
- Packet 4 behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no package metadata files are introduced
- no active behavior names are exposed
- no Analog Four or Pads 5-12 support is exposed

Run:

```powershell
python .\tests\test_behavior_pad1_lane.py
```

Expected red result:

- fails because `rytm_randomizer.behavior_pad1_lane` does not exist yet

### Step 2: Implement Minimal Packet 5A Behavior

Create `rytm_randomizer/behavior_pad1_lane.py` only.

Expected implementation shape:

- add Packet 5A accepted key constants for `BR` and `BM`
- add deferred Packet 5 key constants for the rest of the Pad 1 lane surface
- add immutable read-only result dataclass or equivalent
- add `evaluate_pad1_lane_behavior(command_key)`
- build accepted results from copied `PAD1_COMMANDS` metadata
- keep all behavior read-only and intent-only
- keep deferred and unknown keys safe

### Step 3: Add Closeout Coverage

Update `Scripts/closeout_check.ps1` only to add:

- `=== Test: Behavior Pad 1 Lane ===`
- `tests/test_behavior_pad1_lane.py`

No other closeout changes should be needed.

### Step 4: Verify Targeted Tests

Run:

```powershell
python .\tests\test_behavior_pad1_lane.py
python .\tests\test_behavior_menu_utility.py
python .\tests\test_behavior_anchor_profile.py
python .\tests\test_behavior_mutation_depth.py
python .\tests\test_behavior_scene_group.py
python .\tests\test_cli.py
```

Expected green result:

- all targeted tests pass

### Step 5: Run Full Closeout

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected result:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- `git status --short` shows only intended files before commit

## 16. Required Future Tests

Future Packet 5A tests should verify:

- importing `rytm_randomizer.behavior_pad1_lane` prints nothing
- `BR` returns read-only Pad 1 current-engine rotation intent
- `BM` returns read-only Pad 1 current-engine mutation intent
- `BR` and `BM` preserve labels from `PAD1_COMMANDS`
- `BR` and `BM` record target pad `1`
- `BR` and `BM` record lane `Pad 1 BD engine`
- `BR` records lane action `rotate_profiled_bd_engine`
- `BM` records lane action `safe_current_engine_mutation`
- `BR` and `BM` dispatch no command
- `BR` and `BM` execute no command
- `BR` and `BM` mutate no runtime state
- `BR` and `BM` send no MIDI
- `BR` and `BM` open no ports
- `BR` and `BM` require no hardware
- repeated evaluations are deterministic
- metadata is copied and immutable
- deferred Packet 5 keys fail safely
- already-covered Packet 1 and Packet 2 keys are not reimplemented
- unknown keys fail safely
- Packet 1 through Packet 4 behavior remains unchanged
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- package metadata files remain absent
- V1.34 reference remains untouched
- no Analog Four or Pads 5-12 support is exposed

## 17. Closeout Expectations For Future Packet 5A

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

## 18. Parallelization Decision

Do not parallelize the first Packet 5A implementation.

Reason:

- file ownership is concentrated in one new helper module and one new test file
- Pad 1 lane result vocabulary should stabilize before BD FM, BD Plastic, or
  BD Silky sub-slices are split out
- the first implementation should be small enough for one focused TDD pass

Parallel implementation can be reconsidered later after Packet 5A lands and
future Packet 5B/5C/5D scopes are separately planned with disjoint ownership.

## 19. Explicit Non-Goals

- no implementation in this slice
- no tests in this slice
- no Pad 1 runtime engine rotation
- no Pad 1 current-engine mutation execution
- no BD FM discovery execution
- no BD Plastic discovery execution
- no BD Silky discovery execution
- no anchor return execution
- no selected Pad 1 runtime state mutation
- no prompt/input loop
- no command dispatch
- no command execution
- no CLI execution wiring
- no active CLI command
- no `execute-command`
- no `send-command`
- no `hardware-test`
- no real MIDI dependency
- no `mido`
- no `rtmidi`
- no package metadata
- no port discovery
- no port opening
- no MIDI sending
- no hardware behavior
- no hardware validation
- no profile `"3"` active-boundary support
- no profile `"4"` implementation
- no Analog Four
- no Pads 5-12
- no machine/profile expansion
- no SysEx
- no GUI/capture

## 20. Stop Conditions

Stop before future implementation if:

- Packet 5A scope grows beyond `BR` and `BM`
- actual Pad 1 engine rotation is required
- actual Pad 1 mutation execution is required
- BD FM, BD Plastic, or BD Silky discovery behavior is required in Packet 5A
- anchor return execution is required
- CLI execution wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## 21. Next Safe Options

Safe next options:

- docs-only review/acceptance of this Packet 5 Pad 1 lane behavior plan
- pause at this planning checkpoint
- if accepted, implement only Packet 5A as a tiny read-only `BR`/`BM` intent
  behavior shape

## 22. Recommendation

Review and accept this Packet 5 plan next.

After acceptance, implement only Packet 5A as a tiny read-only Pad 1 current
BD engine lane intent behavior shape for `BR` and `BM`.

Keep BD FM, BD Plastic, BD Silky, anchor return, runtime mutation, MIDI,
ports, active behavior, package metadata, and hardware behavior deferred.

## 23. Decision

Packet 5 planning is documented.

The first future implementation target should be Packet 5A: read-only Pad 1
current BD engine lane intent behavior for `BR` and `BM`.

No implementation is added.
