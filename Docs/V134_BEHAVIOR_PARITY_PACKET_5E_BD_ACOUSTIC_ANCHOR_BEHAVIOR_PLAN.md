# V1.34 Behavior Parity Packet 5E BD Acoustic Anchor Behavior Plan

## 1. Purpose

Define the next tiny Packet 5 Pad 1 lane behavior implementation plan after
the accepted broader behavior-parity progress report review after Packet 5D.

Packet 5E focuses on read-only Pad 1 BD Acoustic anchor/load intent for `BA`.
This is a documentation-only plan. It adds no implementation, tests, CLI
wiring, dispatch, MIDI, port opening, package metadata, active behavior, or
hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `d3b226c Add behavior parity progress report review after Packet 5D`

Current phase:

- Passive/Mock Foundation Phase
- Packet 1 complete and accepted
- Packet 2 accepted as meaningful anchor/profile progress
- Packet 3 complete and accepted
- Packet 4 complete and accepted
- Packet 5A complete and accepted
- Packet 5B complete and accepted
- Packet 5C complete and accepted
- Packet 5D complete and accepted
- broader behavior-parity progress report after Packet 5D accepted
- Packet 5E BD Acoustic anchor behavior plan now being documented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Packet Identity

Packet name:

- Packet 5E: Pad 1 BD Acoustic Anchor Behavior Parity

Goal:

- model `BA` as deterministic read-only Pad 1 BD Acoustic anchor/load intent
- keep `BA` separate from group profile `"4"` / My BD Acoustic mock mapping
- keep Pad 1 BD Acoustic behavior separate from execution
- keep all behavior passive, import-safe, non-dispatching, and hardware-free

## 4. Accepted Context

Packet 5E builds on:

- Packet 5A read-only Pad 1 current BD engine lane intent for `BR` and `BM`
- Packet 5B read-only Pad 1 BD FM lane intent for `FT`, `FK`, `FG`, and `FZ`
- Packet 5C read-only Pad 1 BD Plastic lane intent for `BP`, `PT`, `PK`,
  `PX`, and `PBH`
- Packet 5D read-only Pad 1 BD Silky lane intent for `BI`, `ST`, `SK`, `SC`,
  and `SBH`
- Packet 2 accepted anchor/profile progress for `BH`, `BC`, `BS`, and `BF`

Existing source metadata:

- `BA` exists in `PAD1_COMMANDS`
- `BA` label is `load Pad 1 BD Acoustic anchor`
- `BA` scope is `pad_1`
- `BA` target pad is `1`
- `BA` is scaffold-only passive metadata

Important separation:

- `BA` is a Pad 1 command.
- group profile `"4"` / My BD Acoustic remains parked in mock mapper work.
- group profile `"4"` is associated with Pad 4 / BD Acoustic in the passive
  mock mapper report.
- Packet 5E must not implement group profile `"4"` support.
- Packet 5E must not implement Pad 4 BD Acoustic behavior.

## 5. Planned Packet 5E Scope

Planned implementation scope:

- `BA`: load Pad 1 BD Acoustic anchor

Packet 5E should model:

- `BA` as read-only Pad 1 BD Acoustic anchor/load intent

Reason:

- `BA` is the only remaining explicit deferred Pad 1 BD Acoustic anchor key in
  the current Packet 5 lane sequence.
- Packet 5A through Packet 5D already prove the Pad 1 lane behavior helper can
  model current-engine, BD FM, BD Plastic, and BD Silky intent safely.
- Modeling `BA` would complete the narrow explicit Pad 1 BD Acoustic anchor
  portion of Packet 5 without adding deeper lane state modeling.
- `BA` can be handled as metadata-only intent from `PAD1_COMMANDS` without
  expanding mock mapper profile support.

## 6. Deferred Scope

Deferred within Packet 5:

- deeper Pad 1 lane state modeling
- runtime selected Pad 1 machine/profile state
- runtime anchor loading
- runtime mutation execution
- runtime discovery execution

Deferred outside Packet 5E:

- group profile `"4"` / My BD Acoustic mock mapper support
- Pad 4 BD Acoustic lane behavior
- profile `"4"` implementation
- selected profile workflow
- remaining Packet 2 anchor/profile widening
- Pad 2 lane behavior
- Pad 3 lane behavior
- Pad 4 lane behavior
- undo/commit/state behavior
- runtime prompt behavior
- dispatch and command execution behavior
- real MIDI or hardware behavior

These remain future behavior gaps and require separate plans and reviews before
implementation.

## 7. Future File Ownership

Packet 5E should keep the same narrow implementation surface as Packet 5A,
Packet 5B, Packet 5C, and Packet 5D.

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

Packet 5E should extend the existing `Pad1LaneBehaviorResult` shape instead of
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

Packet 5E should not add top-level fields unless tests prove the existing shape
cannot express `BA` safely. Prefer metadata additions over new fields.

## 9. Planned Packet 5E Semantics

Future `BA` semantics:

- `accepted`: `True`
- `behavior_family`: `pad1-lane/bd-acoustic-anchor-load`
- `reason`: `supported_pad1_bd_acoustic_anchor_load_intent`
- `target_pad`: `1`
- `lane`: `Pad 1 BD Acoustic`
- `lane_action`: `load_bd_acoustic_anchor`
- BD Acoustic anchor dependency recorded only
- group profile `"4"` dependency not recorded
- Pad 4 dependency not recorded
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

Future Packet 5E metadata should be copied from `PAD1_COMMANDS` and may include:

- `source`: `PAD1_COMMANDS`
- `source_command_type`
- `source_command_scope`
- `source_v134_reference_command`
- `source_scaffold_only`
- `target_pad`: `1`
- `lane`: `pad_1_bd_acoustic`
- `lane_family`: `bd_acoustic`
- `lane_action`: `load_bd_acoustic_anchor`
- `requires_bd_acoustic_anchor`: `True`
- `requires_group_profile_4`: `False`
- `requires_pad_4`: `False`
- `requires_depth_selection`: `False`
- `mock_only`: `True`
- `sends_real_midi`: `False`
- `opens_ports`: `False`
- `hardware_required`: `False`
- `active_behavior`: `False`
- `mutates_runtime_state`: `False`
- `dispatches_command`: `False`
- `executes_command`: `False`

The future implementation should not invent new profile metadata. If the
existing `PAD1_COMMANDS` metadata is not enough for a future implementation,
stop and create a separate decision note instead of changing metadata sources
inside Packet 5E.

## 11. Planned Display Contract

Future display lines should remain passive and unambiguous, such as:

- `BA: load Pad 1 BD Acoustic anchor`
- `Read-only Pad 1 BD Acoustic anchor intent.`
- `Target pad: 1`
- `Lane: Pad 1 BD Acoustic`
- `Lane action: load_bd_acoustic_anchor`
- `BD Acoustic anchor dependency is recorded only.`
- `Group profile 4 is not used by this Pad 1 command.`
- `No prompt would run.`
- `No state would change.`
- `No command would dispatch.`
- `No command would execute.`
- `No lane state would mutate.`
- `No MIDI would be sent.`
- `No ports would be opened.`
- `No hardware would be required.`

## 12. Safe Failure Expectations

The future Packet 5E implementation should fail safely for:

- unknown command keys
- group profile `"4"` requests in the wrong layer
- already-covered Packet 1 menu/status keys
- already-accepted Packet 5A keys if their behavior changes unexpectedly
- already-accepted Packet 5B keys if their behavior changes unexpectedly
- already-accepted Packet 5C keys if their behavior changes unexpectedly
- already-accepted Packet 5D keys if their behavior changes unexpectedly
- unsupported command metadata
- missing Pad 1 metadata
- any key outside the accepted Packet 5E scope

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

### Step 1: Extend Failing Packet 5E Tests

Modify `tests/test_behavior_pad1_lane.py`.

Add tests for:

- existing `BR` and `BM` behavior remains unchanged
- existing `FT`, `FK`, `FG`, and `FZ` behavior remains unchanged
- existing `BP`, `PT`, `PK`, `PX`, and `PBH` behavior remains unchanged
- existing `BI`, `ST`, `SK`, `SC`, and `SBH` behavior remains unchanged
- `BA` returns accepted read-only BD Acoustic anchor/load intent
- `BA` copies metadata from `PAD1_COMMANDS`
- `BA` records Pad 1 target metadata
- `BA` does not record group profile `"4"` as a dependency
- `BA` does not record Pad 4 as a dependency
- repeated `BA` evaluations are deterministic
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

- fails because `BA` still returns a deferred result.

### Step 2: Implement Minimal Packet 5E Behavior

Modify only:

- `rytm_randomizer/behavior_pad1_lane.py`

Implementation should:

- preserve existing Packet 5A `BR` and `BM` behavior exactly
- preserve existing Packet 5B `FT`, `FK`, `FG`, and `FZ` behavior exactly
- preserve existing Packet 5C `BP`, `PT`, `PK`, `PX`, and `PBH` behavior
  exactly
- preserve existing Packet 5D `BI`, `ST`, `SK`, `SC`, and `SBH` behavior
  exactly
- add a Packet 5E accepted key constant for `BA`
- remove `BA` from `DEFERRED_PACKET_5_PAD1_LANE_KEYS`
- add deterministic lane action `load_bd_acoustic_anchor`
- add accepted result construction for BD Acoustic anchor/load intent
- preserve safe failure behavior for unknown keys and already-covered context
  keys
- import no real MIDI libraries
- open no ports
- send no MIDI
- add no active behavior

### Step 3: Run Packet 5E Target Test

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

Packet 5E must not add:

- implementation in this slice
- tests in this slice
- Pad 1 BD Acoustic anchor/load execution
- group profile `"4"` mock mapper support
- group profile `"4"` active-boundary support
- Pad 4 BD Acoustic behavior
- profile `"4"` implementation
- Pad 1 runtime engine rotation
- Pad 1 current-engine mutation execution
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
- Analog Four
- Pads 5-12
- machine/profile expansion
- SysEx
- GUI/capture

## 15. Stop Conditions

Stop before future implementation if:

- Packet 5E scope grows beyond `BA`
- actual BD Acoustic anchor/load execution is required
- group profile `"4"` support is required
- Pad 4 BD Acoustic behavior is required
- deeper Pad 1 lane state modeling is required
- CLI execution wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## 16. Parallelization Decision

Do not parallelize the first Packet 5E implementation.

Reason:

- file ownership remains concentrated in the same helper module and test file
- `BA` must preserve Packet 5A, Packet 5B, Packet 5C, and Packet 5D behavior
  exactly
- `BA` must be separated carefully from group profile `"4"` and Pad 4 BD
  Acoustic concepts before any wider branch is split out

Parallel implementation can be reconsidered later for independent packets such
as Pad 2, Pad 3, Pad 4, undo/state, or separate docs-only roadmap work.

## 17. Safe Next Options

Safe next options:

- docs-only review/acceptance of this Packet 5E BD Acoustic anchor behavior
  plan
- pause at this planning checkpoint
- if accepted, implement only Packet 5E as a tiny read-only `BA` intent
  behavior shape

## 18. Recommendation

Review and accept this Packet 5E plan next.

After acceptance, implement only Packet 5E as a tiny read-only Pad 1 BD
Acoustic anchor intent behavior shape for `BA`.

Keep group profile `"4"`, Pad 4 BD Acoustic behavior, deeper lane state
modeling, runtime mutation, MIDI, ports, active behavior, package metadata, and
hardware behavior deferred.

## 19. Decision

Packet 5E planning is documented.

The next implementation target should be Packet 5E: read-only Pad 1 BD
Acoustic anchor intent behavior for `BA`.

No implementation is added.

## 20. Review Follow-Up

This plan was reviewed and accepted in:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_5E_BD_ACOUSTIC_ANCHOR_BEHAVIOR_PLAN_REVIEW.md`

The accepted next implementation target remains Packet 5E: read-only Pad 1 BD
Acoustic anchor intent behavior for `BA`.

The review keeps group profile `"4"` / My BD Acoustic, Pad 4 BD Acoustic
behavior, deeper Pad 1 lane state modeling, runtime mutation, dispatch, MIDI,
ports, package metadata, active behavior, and hardware behavior deferred.
