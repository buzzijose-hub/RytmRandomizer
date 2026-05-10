# V1.34 Behavior Parity Packet 5B BD FM Lane Behavior Plan

## 1. Purpose

Define the next tiny Packet 5 Pad 1 lane behavior implementation plan after
accepted Packet 5A progress.

Packet 5B focuses on read-only Pad 1 BD FM discovery and anchor-return intent.
This is a documentation-only plan. It adds no implementation, tests, CLI
wiring, dispatch, MIDI, port opening, package metadata, active behavior, or
hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `22c3e2c Add behavior parity progress report review after Packet 5A`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A complete and accepted
- Packet 5B BD FM lane behavior plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Packet Identity

Packet name:

- Packet 5B: Pad 1 BD FM Lane Behavior Parity

Goal:

- model BD FM discovery and anchor-return commands as deterministic read-only
  intent metadata
- keep BD FM lane behavior separate from execution
- keep all behavior passive, import-safe, non-dispatching, and hardware-free

## 4. Accepted Context

Packet 5B builds on:

- Packet 5A read-only Pad 1 current BD engine lane intent for `BR` and `BM`
- Packet 1 menu/status behavior for `FM`
- Packet 2 anchor/profile behavior for `BF`

Already-covered context:

- `FM`: show BD FM menu/status
- `BF`: load Pad 1 BD FM profiled anchor

Packet 5B may reference those commands as context, but must not reimplement or
change their existing behavior.

## 5. Planned Packet 5B Scope

Planned implementation scope:

- `FT`: BD FM tone/FM discovery
- `FK`: BD FM kick/body discovery
- `FG`: BD FM grit discovery
- `FZ`: return Pad 1 BD FM to anchor

Packet 5B should model:

- `FT` as read-only BD FM tone/FM discovery intent
- `FK` as read-only BD FM kick/body discovery intent
- `FG` as read-only BD FM grit discovery intent
- `FZ` as read-only BD FM anchor-return intent

Reason:

- `FT`, `FK`, `FG`, and `FZ` are the smallest coherent BD FM lane cluster.
- `FM` menu/status and `BF` anchor/profile context are already covered.
- BD FM is the first deeper Pad 1 lane family after the generic `BR`/`BM`
  current-engine vocabulary.
- This expands Packet 5 without touching BD Plastic, BD Silky, or BD Acoustic.

## 6. Deferred Packet 5 Scope

Deferred within Packet 5:

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
- Pad 1 BD Acoustic anchor/profile behavior:
  - `BA`

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

These remain future behavior gaps and require separate plans and reviews before
implementation.

## 7. Future File Ownership

Packet 5B should keep the same narrow implementation surface as Packet 5A.

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

Packet 5B should extend the existing `Pad1LaneBehaviorResult` shape instead of
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

Packet 5B may add fields only if tests prove the existing shape cannot express
BD FM discovery and return intent safely. Prefer metadata additions over new
top-level fields.

## 9. Planned Packet 5B Semantics

Future `FT` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-fm-discovery`
- `reason`: `supported_pad1_bd_fm_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD FM`
- `lane_action`: `bd_fm_tone_fm_discovery`
- BD FM engine/profile dependency recorded only
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

Future `FK` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-fm-discovery`
- `reason`: `supported_pad1_bd_fm_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD FM`
- `lane_action`: `bd_fm_kick_body_discovery`
- BD FM engine/profile dependency recorded only
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

Future `FG` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-fm-discovery`
- `reason`: `supported_pad1_bd_fm_discovery_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD FM`
- `lane_action`: `bd_fm_grit_discovery`
- BD FM engine/profile dependency recorded only
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

Future `FZ` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-fm-anchor-return`
- `reason`: `supported_pad1_bd_fm_anchor_return_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD FM`
- `lane_action`: `return_bd_fm_to_anchor`
- BD FM anchor dependency recorded only
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

Future Packet 5B metadata should be copied from `PAD1_COMMANDS` and may
include:

- `source`: `PAD1_COMMANDS`
- `source_command_type`
- `source_command_scope`
- `source_v134_reference_command`
- `source_scaffold_only`
- `target_pad`: `1`
- `lane`: `pad_1_bd_fm`
- `lane_family`: `bd_fm`
- `lane_action`
- `requires_bd_fm_engine_state`
- `requires_bd_fm_anchor_state`
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

- `FT`: `bd_fm_tone_fm_discovery`
- `FK`: `bd_fm_kick_body_discovery`
- `FG`: `bd_fm_grit_discovery`
- `FZ`: `return_bd_fm_to_anchor`

## 11. Planned Display Contract

Future display lines should remain passive and unambiguous, such as:

- `<key>: <label>`
- `Read-only Pad 1 BD FM lane intent.`
- `Target pad: 1`
- `Lane: Pad 1 BD FM`
- `Lane action: <lane action>`
- `BD FM dependency is recorded only.`
- `Future discovery depth is recorded only.` for `FT`, `FK`, and `FG`
- `Anchor-return dependency is recorded only.` for `FZ`
- `No prompt would run.`
- `No state would change.`
- `No command would dispatch.`
- `No command would execute.`
- `No lane state would mutate.`
- `No MIDI would be sent.`
- `No ports would be opened.`
- `No hardware would be required.`

## 12. Safe Failure Expectations

The future Packet 5B implementation should fail safely for:

- unknown command keys
- deferred BD Plastic lane keys
- deferred BD Silky lane keys
- deferred `BA`
- already-covered Packet 1 menu/status keys
- already-covered Packet 2 anchor/profile keys
- unsupported command metadata
- missing Pad 1 metadata
- any key outside the accepted Packet 5B scope

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

### Step 1: Extend Failing Packet 5B Tests

Modify `tests/test_behavior_pad1_lane.py`.

Add tests for:

- existing `BR` and `BM` behavior remains unchanged
- `FT` returns accepted read-only BD FM tone/FM discovery intent
- `FK` returns accepted read-only BD FM kick/body discovery intent
- `FG` returns accepted read-only BD FM grit discovery intent
- `FZ` returns accepted read-only BD FM anchor-return intent
- `FT`, `FK`, `FG`, and `FZ` copy metadata from `PAD1_COMMANDS`
- repeated `FT`, `FK`, `FG`, and `FZ` evaluations are deterministic
- BD Plastic keys remain deferred/safe
- BD Silky keys remain deferred/safe
- `BA` remains deferred/safe
- `FM` and `BF` are not reimplemented by Packet 5B
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

- fails because `FT`, `FK`, `FG`, and `FZ` still return deferred results.

### Step 2: Implement Minimal Packet 5B Behavior

Modify only:

- `rytm_randomizer/behavior_pad1_lane.py`

Implementation should:

- preserve existing Packet 5A `BR` and `BM` behavior exactly
- add Packet 5B accepted key constants for `FT`, `FK`, `FG`, and `FZ`
- narrow the deferred Packet 5 key set by removing `FT`, `FK`, `FG`, and `FZ`
- add deterministic lane actions for the BD FM keys
- add accepted result construction for BD FM discovery and return intent
- preserve safe failure behavior for BD Plastic, BD Silky, `BA`, unknown keys,
  and already-covered context keys
- import no real MIDI libraries
- open no ports
- send no MIDI
- add no active behavior

### Step 3: Run Packet 5B Target Test

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

Packet 5B must not add:

- implementation in this slice
- tests in this slice
- Pad 1 BD FM discovery execution
- Pad 1 BD FM anchor-return execution
- Pad 1 runtime engine rotation
- Pad 1 current-engine mutation execution
- BD Plastic behavior
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

- Packet 5B scope grows beyond `FT`, `FK`, `FG`, and `FZ`
- actual BD FM discovery execution is required
- actual BD FM anchor return execution is required
- BD Plastic or BD Silky behavior is required in Packet 5B
- `BA` behavior is required in Packet 5B
- CLI execution wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## 16. Parallelization Decision

Do not parallelize the first Packet 5B implementation.

Reason:

- file ownership remains concentrated in the same helper module and test file
- Packet 5B should preserve Packet 5A behavior exactly
- BD FM discovery/return vocabulary should stabilize before BD Plastic or BD
  Silky sub-slices are split out

Parallel implementation can be reconsidered later after Packet 5B lands and
future Packet 5C/5D scopes are separately planned with disjoint ownership.

## 17. Safe Next Options

Safe next options:

- docs-only review/acceptance of this Packet 5B BD FM lane behavior plan
- pause at this planning checkpoint
- if accepted, implement only Packet 5B as a tiny read-only `FT`/`FK`/`FG`/`FZ`
  intent behavior shape

## 18. Recommendation

Review and accept this Packet 5B plan next.

After acceptance, implement only Packet 5B as a tiny read-only Pad 1 BD FM
lane intent behavior shape for `FT`, `FK`, `FG`, and `FZ`.

Keep BD Plastic, BD Silky, Pad 1 BD Acoustic, runtime mutation, MIDI, ports,
active behavior, package metadata, and hardware behavior deferred.

## 19. Decision

Packet 5B planning is documented.

The next implementation target should be Packet 5B: read-only Pad 1 BD FM
lane intent behavior for `FT`, `FK`, `FG`, and `FZ`.

No implementation is added.

## 20. Review Follow-Up

This plan was reviewed and accepted in:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_5B_BD_FM_LANE_BEHAVIOR_PLAN_REVIEW.md`

The accepted next implementation target remains Packet 5B: read-only Pad 1 BD
FM lane intent behavior for `FT`, `FK`, `FG`, and `FZ`.

The review keeps BD Plastic, BD Silky, Pad 1 BD Acoustic, runtime mutation,
dispatch, MIDI, ports, package metadata, active behavior, and hardware behavior
deferred.
