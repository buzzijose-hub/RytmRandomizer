# V1.34 Behavior Parity Packet 1B Utility/Session Plan

## Purpose

Define the next tiny behavior-parity planning slice after Packet 1A.

Packet 1B is a plan for utility/session intent behavior for the deferred
commands:

- `T`
- `C`
- `Q`

This is a plan only. It does not implement runtime behavior, tests, dispatch,
prompt loops, MIDI, port opening, active CLI behavior, package metadata, or
hardware behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- a79f92b Add Packet 1A menu utility checkpoint review

Current phase:

- Passive/Mock Foundation Phase
- V1.34 behavior parity Packet 1A implemented
- Packet 1A checkpoint and review accepted
- Packet 1B utility/session behavior now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Accepted Packet 1A Baseline

Packet 1A added:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`
- closeout label `=== Test: Behavior Menu Utility ===`
- `MenuUtilityBehaviorResult`
- `evaluate_menu_utility_behavior(command_key)`

Packet 1A supports read-only menu/status behavior for:

- `BD`
- `FM`
- `PD`
- `SM`
- `P2M`
- `J`
- `GM`
- `SCN`
- `PR`
- `SR`
- `P3M`
- `P4M`
- `H`
- `R`

Packet 1A deliberately keeps these utility/session commands deferred:

- `T`
- `C`
- `Q`

## Packet 1B Goal

Packet 1B should model the intent of deferred utility/session commands without
actually changing session state or running a prompt loop.

The first Packet 1B implementation, if later approved, should make `T`, `C`,
and `Q` inspectable as deterministic behavior results only.

It should not:

- prompt the user
- block for input
- change target pad
- change MIDI channel
- exit the Python process
- call `sys.exit`
- mutate runtime state
- open ports
- send MIDI
- dispatch commands
- wire into CLI execution

## Planned Command Meanings

`T` means:

- select target pad/channel in the future V1.34 operator flow
- Packet 1B should represent this as target-selection intent only
- no target should actually change
- no prompt should actually run

`C` means:

- change MIDI channel in the future V1.34 operator flow
- Packet 1B should represent this as channel-selection intent only
- no MIDI channel should actually change
- no prompt should actually run
- no MIDI port should open

`Q` means:

- quit the command loop in the future V1.34 operator flow
- Packet 1B should represent this as session-exit intent only
- the process must not exit
- no CLI command should be terminated from this behavior helper

## Proposed Future File Ownership

If Packet 1B is implemented later, the write set should remain narrow:

- modify `rytm_randomizer/behavior_menu_utility.py`
- modify `tests/test_behavior_menu_utility.py`

No closeout script update should be needed because `tests/test_behavior_menu_utility.py`
is already included under:

- `=== Test: Behavior Menu Utility ===`

Files that should remain untouched for Packet 1B:

- `rytm_hybrid_randomizer_v134.py`
- `rytm_randomizer/cli.py`
- `rytm_randomizer/mock_midi.py`
- `rytm_randomizer/mock_message_mapper.py`
- `rytm_randomizer/mock_mapper_report.py`
- `rytm_randomizer/real_midi_adapter.py`
- package metadata files
- active CLI command paths
- runtime execution/dispatch/MIDI logic outside the Packet 1B files

## Proposed Future Behavior Shape

Packet 1B may reuse `MenuUtilityBehaviorResult` if the existing shape remains
clear enough.

Possible future result values:

- `behavior_family`: `utility/session`
- `accepted`: true for `T`, `C`, and `Q`
- `reason`: `supported_utility_session_intent`
- `state_changed`: false
- `prompt_required`: false
- `sends_real_midi`: false
- `opens_ports`: false
- `hardware_required`: false
- `active_behavior`: false

Possible metadata for `T`:

- `source`: `UTILITY_COMMANDS`
- `scope`: `target_selection_intent`
- `future_prompt`: `target_pad_channel_selection`
- `mutates_runtime_state`: false
- `mock_only`: true

Possible metadata for `C`:

- `source`: `UTILITY_COMMANDS`
- `scope`: `midi_channel_selection_intent`
- `future_prompt`: `midi_channel_selection`
- `mutates_runtime_state`: false
- `opens_ports`: false
- `mock_only`: true

Possible metadata for `Q`:

- `source`: `UTILITY_COMMANDS`
- `scope`: `session_exit_intent`
- `would_exit_loop`: true
- `exits_process`: false
- `mutates_runtime_state`: false
- `mock_only`: true

The exact field names may be adjusted during implementation if the tests keep
the same safety meaning.

## Required Future Tests

Future Packet 1B tests should verify:

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

## Safe Failure Expectations

Packet 1B should continue to fail safely for:

- unknown command keys
- unsupported metadata shape
- non-string keys, if current behavior cannot represent them deterministically
- any future request to execute prompt/session behavior directly

Safe failure means:

- no state mutation
- no real MIDI
- no port opening
- no CLI active behavior
- no hardware requirement
- no process exit

## Closeout Expectations For Future Packet 1B

Future implementation must run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
@('pyproject.toml','requirements.txt','setup.py','setup.cfg') | ForEach-Object { "$($_): $(Test-Path $_)" }
git status --short
```

Expected closeout state:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- package metadata files remain absent unless separately approved
- git status is clean after commit

## Parallelization Decision

Do not parallelize Packet 1B implementation.

Reasons:

- the write set is concentrated in one module and one test file
- `T`, `C`, and `Q` share the same utility/session result vocabulary
- the safety semantics should be reviewed as one small unit
- parallel work would add coordination overhead without enough independence

Parallel implementation can be reconsidered for later independent behavior
domains after Packet 1B lands cleanly and is reviewed.

## Explicit Non-Goals

- no implementation in this slice
- no tests in this slice
- no command dispatch
- no command execution
- no scene execution
- no real prompt/input loop
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

## Stop Conditions

Stop before future implementation if:

- Packet 1B requires a real prompt/input loop
- Packet 1B requires CLI wiring
- `T` or `C` would actually mutate target/channel state
- `Q` would actually exit the process
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## Next Safe Options

- review and accept this Packet 1B plan
- pause at this planning checkpoint
- if accepted, implement Packet 1B exactly as a tiny scoped behavior-intent packet

## Recommendation

Review and accept this Packet 1B plan next.

After acceptance, implement only the deterministic utility/session intent
surface for `T`, `C`, and `Q`.

Keep hardware off. Keep package metadata absent.

## Decision

Packet 1B planning is documented. No implementation is added.
