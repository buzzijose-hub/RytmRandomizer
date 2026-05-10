# V1.34 Behavior Parity Packet 5C BD Plastic Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 5 Pad 1 lane behavior implementation plan after
the accepted broader behavior-parity progress report review after Packet 5B.

Packet 5C focuses on read-only Pad 1 BD Plastic anchor/load, discovery, and
anchor-return intent. This is a documentation-only plan. It adds no
implementation, tests, CLI wiring, dispatch, MIDI, port opening, package
metadata, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `7900a90 Add behavior parity progress report review after Packet 5B`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A complete and accepted
- Packet 5B complete and accepted
- broader behavior-parity progress report after Packet 5B accepted
- Packet 5C BD Plastic lane behavior plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Packet Identity

Packet name:

- Packet 5C: Pad 1 BD Plastic Lane Behavior Parity

Goal:

- model BD Plastic profiled anchor/load, discovery, and anchor-return commands
  as deterministic read-only intent metadata
- keep BD Plastic lane behavior separate from execution
- keep all behavior passive, import-safe, non-dispatching, and hardware-free

## 4. Accepted Context

Packet 5C builds on:

- Packet 5A read-only Pad 1 current BD engine lane intent for `BR` and `BM`
- Packet 5B read-only Pad 1 BD FM lane intent for `FT`, `FK`, `FG`, and `FZ`
- Packet 1 menu/status behavior for `PD`

Already-covered context:

- `PD`: show BD Plastic menu/status

Packet 5C may reference `PD` as context, but must not reimplement or change
its existing Packet 1 behavior.

Unlike Packet 5B, the BD Plastic profiled anchor/load command is not already
accepted in Packet 2. Therefore Packet 5C may include `BP` as read-only
metadata-only BD Plastic profiled anchor/load intent while still adding no
execution behavior.

## 5. Planned Packet 5C Scope

Planned implementation scope:

- `BP`: load Pad 1 BD Plastic profiled anchor
- `PT`: BD Plastic tone/modulation discovery
- `PK`: BD Plastic kick/body discovery
- `PX`: BD Plastic rubber/experimental discovery
- `PBH`: return Pad 1 BD Plastic to anchor

Packet 5C should model:

- `BP` as read-only BD Plastic profiled anchor/load intent
- `PT` as read-only BD Plastic tone/modulation discovery intent
- `PK` as read-only BD Plastic kick/body discovery intent
- `PX` as read-only BD Plastic rubber/experimental discovery intent
- `PBH` as read-only BD Plastic anchor-return intent

Reason:

- `BP`, `PT`, `PK`, `PX`, and `PBH` are the smallest coherent BD Plastic lane
  cluster.
- `PD` menu/status context is already covered.
- BD Plastic is the next deferred Pad 1 lane family after accepted BD FM
  progress.
- This expands Packet 5 without touching BD Silky or BD Acoustic.

## 6. Deferred Packet 5 Scope

Deferred within Packet 5:

- BD Silky load/discovery/anchor-return intent:
  - `BI`
  - `ST`
  - `SK`
  - `SC`
  - `SBH`
- Pad 1 BD Acoustic anchor/profile behavior:
  - `BA`

Deferred concepts:

- runtime engine rotation
- runtime current-engine mutation
- runtime discovery mutation
- runtime anchor load
- runtime anchor return
- Pad 1 selected-engine state
- Pad 1 lane mode state
- mutation depth prompts
- command dispatch
- MIDI or hardware behavior

These remain future behavior gaps and require separate plans and reviews before
implementation.

## 7. Future File Ownership

Packet 5C should keep the same narrow implementation surface as Packet 5A and
Packet 5B.

Allowed future implementation files:

- `rytm_randomizer/behavior_pad1_lane.py`
- `tests/test_behavior_pad1_lane.py`

Closeout script:

- no closeout script update should be needed
- `tests/test_behavior_pad1_lane.py` is already covered by
  `=== Test: Behavior Pad 1 Lane ===`

Files that should remain untouched:

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
- docs, except for a later checkpoint/review after implementation

## 8. Proposed Future Behavior Shape

Packet 5C should extend the existing `Pad1LaneBehaviorResult` shape instead of
creating a new behavior result type.

Existing result fields should remain valid:

- command key
- label
- behavior family
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

Packet 5C may add fields only if tests prove the existing shape cannot express
BD Plastic intent safely. Prefer metadata additions over new top-level fields.

## 9. Planned Packet 5C Semantics

Future `BP` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-plastic-anchor-load`
- `reason`: `supported_pad1_bd_plastic_anchor_load_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Plastic`
- `lane_action`: `load_bd_plastic_profiled_anchor`
- BD Plastic anchor/profile dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Future `PT` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-plastic-discovery`
- `reason`: `supported_pad1_bd_plastic_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Plastic`
- `lane_action`: `bd_plastic_tone_modulation_discovery`
- BD Plastic engine/profile dependency recorded only
- future discovery depth dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Future `PK` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-plastic-discovery`
- `reason`: `supported_pad1_bd_plastic_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Plastic`
- `lane_action`: `bd_plastic_kick_body_discovery`
- BD Plastic engine/profile dependency recorded only
- future discovery depth dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Future `PX` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-plastic-discovery`
- `reason`: `supported_pad1_bd_plastic_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Plastic`
- `lane_action`: `bd_plastic_rubber_experimental_discovery`
- BD Plastic engine/profile dependency recorded only
- future discovery depth dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

Future `PBH` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-plastic-anchor-return`
- `reason`: `supported_pad1_bd_plastic_anchor_return_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Plastic`
- `lane_action`: `return_bd_plastic_to_anchor`
- BD Plastic anchor dependency recorded only
- state changed: `False`
- prompt required: `False`
- dispatches command: `False`
- executes command: `False`
- mutates lane state: `False`
- sends real MIDI: `False`
- opens ports: `False`
- hardware required: `False`
- active behavior: `False`

## 10. Planned Metadata Contract

Future Packet 5C metadata should be copied from `PAD1_COMMANDS` and may
include:

- `source`: `PAD1_COMMANDS`
- `source_command_type`
- `source_command_scope`
- `source_v134_reference_command`
- `source_scaffold_only`
- `target_pad`: `1`
- `lane`: `pad_1_bd_plastic`
- `lane_family`: `bd_plastic`
- `lane_action`
- `requires_bd_plastic_engine_profile`
- `requires_bd_plastic_anchor`
- `requires_depth_selection`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`
- `dispatches_command`: `False`
- `executes_command`: `False`

Suggested deterministic lane actions:

- `BP`: `load_bd_plastic_profiled_anchor`
- `PT`: `bd_plastic_tone_modulation_discovery`
- `PK`: `bd_plastic_kick_body_discovery`
- `PX`: `bd_plastic_rubber_experimental_discovery`
- `PBH`: `return_bd_plastic_to_anchor`

## 11. Planned Display Contract

Future display lines should remain passive and unambiguous, such as:

- `<key>: <label>`
- `Read-only Pad 1 BD Plastic lane intent.`
- `Target pad: 1`
- `Lane: Pad 1 BD Plastic`
- `Lane action: <lane action>`
- `BD Plastic anchor/profile dependency is recorded only.` for `BP`
- `BD Plastic engine/profile dependency is recorded only.` for `PT`, `PK`,
  and `PX`
- `Future BD Plastic discovery depth is recorded only.` for `PT`, `PK`, and
  `PX`
- `BD Plastic anchor dependency is recorded only.` for `PBH`
- `No prompt would run.`
- `No state would change.`
- `No command would dispatch.`
- `No command would execute.`
- `No lane state would mutate.`
- `No MIDI would be sent.`
- `No ports would be opened.`
- `No hardware would be required.`

## 12. Safe Failure Expectations

The future Packet 5C implementation should fail safely for:

- unknown command keys
- deferred BD Silky lane keys
- deferred `BA`
- already-covered Packet 1 menu/status keys
- already-accepted Packet 5A keys if their behavior changes unexpectedly
- already-accepted Packet 5B keys if their behavior changes unexpectedly
- unsupported command metadata
- missing Pad 1 metadata
- any key outside the accepted Packet 5C scope

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

## 13. Required Future TDD Steps

Future implementation should use a red/green flow.

### Step 1: Extend Failing Packet 5C Tests

Modify `tests/test_behavior_pad1_lane.py`.

Add tests for:

- existing `BR` and `BM` behavior remains unchanged
- existing `FT`, `FK`, `FG`, and `FZ` behavior remains unchanged
- `BP` returns accepted read-only BD Plastic anchor/load intent
- `PT` returns accepted read-only BD Plastic tone/modulation discovery intent
- `PK` returns accepted read-only BD Plastic kick/body discovery intent
- `PX` returns accepted read-only BD Plastic rubber/experimental discovery
  intent
- `PBH` returns accepted read-only BD Plastic anchor-return intent
- `BP`, `PT`, `PK`, `PX`, and `PBH` copy metadata from `PAD1_COMMANDS`
- repeated `BP`, `PT`, `PK`, `PX`, and `PBH` evaluations are deterministic
- BD Silky keys remain deferred/safe
- `BA` remains deferred/safe
- `PD` is not reimplemented by Packet 5C
- unknown keys still fail safely
- passive CLI behavior remains unchanged
- no real MIDI libraries are imported
- package metadata remains absent
- no active behavior names are exposed
- no Analog Four support is exposed
- no Pads 5-12 support is exposed

Run:

```powershell
python .\tests\test_behavior_pad1_lane.py
```

Expected red result:

- fails because `BP`, `PT`, `PK`, `PX`, and `PBH` still return deferred
  results.

### Step 2: Implement Minimal Packet 5C Behavior

Modify only:

- `rytm_randomizer/behavior_pad1_lane.py`

Implementation should:

- preserve existing Packet 5A `BR` and `BM` behavior exactly
- preserve existing Packet 5B `FT`, `FK`, `FG`, and `FZ` behavior exactly
- add Packet 5C accepted key constants for `BP`, `PT`, `PK`, `PX`, and `PBH`
- narrow the deferred Packet 5 key set by removing `BP`, `PT`, `PK`, `PX`, and
  `PBH`
- add deterministic lane actions for the BD Plastic keys
- add accepted result construction for BD Plastic anchor/load, discovery, and
  return intent
- preserve safe failure behavior for BD Silky, `BA`, unknown keys, and
  already-covered context keys
- import no real MIDI libraries
- open no ports
- send no MIDI
- add no active behavior

### Step 3: Run Packet 5C Target Test

Run:

```powershell
python .\tests\test_behavior_pad1_lane.py
```

Expected green result:

- passes silently.

### Step 4: Run Targeted Regressions

Run:

```powershell
python .\tests\test_behavior_menu_utility.py
python .\tests\test_behavior_anchor_profile.py
python .\tests\test_behavior_mutation_depth.py
python .\tests\test_behavior_scene_group.py
python .\tests\test_cli.py
```

Expected result:

- pass silently.

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
- git status is clean after commit

## 14. Explicit Non-Goals

Packet 5C must not add:

- implementation in this slice
- tests in this slice
- Pad 1 BD Plastic anchor/load execution
- Pad 1 BD Plastic discovery execution
- Pad 1 BD Plastic anchor-return execution
- Pad 1 runtime engine rotation
- Pad 1 current-engine mutation execution
- BD Silky behavior
- `BA` behavior
- selected Pad 1 runtime state mutation
- prompt/input loop
- command dispatch
- command execution
- CLI execution wiring
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependency
- `mido`
- `rtmidi`
- package metadata
- port discovery
- port opening
- MIDI sending
- hardware behavior
- hardware validation
- profile `"3"` active-boundary support
- profile `"4"` implementation
- Analog Four
- Pads 5-12
- machine/profile expansion
- SysEx
- GUI/capture

## 15. Stop Conditions

Stop before future implementation if:

- Packet 5C scope grows beyond `BP`, `PT`, `PK`, `PX`, and `PBH`
- actual BD Plastic anchor/load execution is required
- actual BD Plastic discovery execution is required
- actual BD Plastic anchor return execution is required
- BD Silky behavior is required in Packet 5C
- `BA` behavior is required in Packet 5C
- CLI execution wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## 16. Parallelization Decision

Do not parallelize the first Packet 5C implementation.

Reason:

- file ownership remains concentrated in the same helper module and test file
- Packet 5C must preserve Packet 5A and Packet 5B behavior exactly
- BD Plastic anchor/load, discovery, and return vocabulary should stabilize
  before BD Silky or Pad 1 BD Acoustic sub-slices are split out

Parallel implementation can be reconsidered later after Packet 5C lands and
future Packet 5D/5E scopes are separately planned with disjoint ownership.

## 17. Safe Next Options

Safe next options:

- docs-only review/acceptance of this Packet 5C BD Plastic lane behavior plan
- pause at this planning checkpoint
- if accepted, implement only Packet 5C as a tiny read-only `BP`/`PT`/`PK`/
  `PX`/`PBH` intent behavior shape

## 18. Recommendation

Review and accept this Packet 5C plan next.

After acceptance, implement only Packet 5C as a tiny read-only Pad 1 BD Plastic
lane intent behavior shape for `BP`, `PT`, `PK`, `PX`, and `PBH`.

Keep BD Silky, Pad 1 BD Acoustic, runtime mutation, MIDI, ports, active
behavior, package metadata, and hardware behavior deferred.

## 19. Decision

Packet 5C planning is documented.

The next implementation target should be Packet 5C: read-only Pad 1 BD Plastic
lane intent behavior for `BP`, `PT`, `PK`, `PX`, and `PBH`.

No implementation is added.
