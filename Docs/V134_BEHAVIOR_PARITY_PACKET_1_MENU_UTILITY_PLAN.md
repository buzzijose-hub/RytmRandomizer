# V1.34 Behavior Parity Packet 1 Menu/Utility Plan

## Purpose

This document defines the first behavior-parity implementation packet plan.

The packet target is menu/status and utility behavior from the accepted
V1.34 behavior parity matrix.

This is a plan only. It does not implement runtime behavior, tests, dispatch,
MIDI, port opening, active CLI behavior, package metadata, or hardware
behavior.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 3a85c52 Add behavior parity readiness session handoff

Current phase:

- Passive/Mock Foundation Phase
- V1.34 behavior parity matrix complete
- implementation readiness checkpoint accepted
- first behavior-parity packet planning now beginning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Packet Identity

Packet name:

- Packet 1: Menu/Utility Behavior Parity

Packet intent:

- establish the first small, mock/passive-safe runtime behavior shape
- keep behavior deterministic and inspectable
- avoid real MIDI, ports, active CLI behavior, and hardware
- stabilize routing vocabulary before deeper behavior domains

## Accepted Sources

This packet plan is based on:

- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MENU_UTILITY_SLICE.md`
- `Docs/V134_BEHAVIOR_PARITY_MATRIX_MENU_UTILITY_SLICE_REVIEW.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_READINESS_CHECKPOINT.md`
- `Docs/V134_BEHAVIOR_PARITY_IMPLEMENTATION_READINESS_CHECKPOINT_REVIEW.md`
- passive command metadata in `rytm_randomizer/commands.py`
- passive CLI and lookup behavior already covered by closeout
- protected V1.34 reference as the future behavior source, not edited

## Planned Command Scope

The planning scope comes from the accepted menu/utility matrix slice.

Menu/status display commands:

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

Utility/session commands:

- `T`
- `C`
- `Q`

## Packet 1A Recommended Implementation Scope

The first implementation packet should be even smaller than the full matrix
slice.

Recommended initial implementation scope:

- read-only menu/status display behavior for `BD`, `FM`, `PD`, `SM`, `P2M`,
  `J`, `GM`, `SCN`, `PR`, `SR`, `P3M`, `P4M`, `H`, and `R`
- deterministic result objects or plain structured dictionaries
- no command execution
- no state mutation
- no prompt loop
- no CLI wiring
- no real MIDI
- no ports
- no hardware requirement

Recommended deferred scope within the same behavior family:

- `T` target pad/channel selection prompt behavior
- `C` MIDI channel selection prompt behavior
- `Q` command-loop exit behavior

Reason:

- `T` and `C` may affect future hardware output targets.
- `Q` depends on a future command-loop/session lifecycle.
- Keeping these deferred preserves the first packet as a low-risk display and
  state-reporting shape.

## Proposed Future File Ownership

The first future implementation packet should have a narrow write set.

Allowed future implementation files:

- `rytm_randomizer/behavior_menu_utility.py`
- `tests/test_behavior_menu_utility.py`
- `Scripts/closeout_check.ps1`, only to add the new test file to closeout

Allowed future fixture files only if deterministic text output is introduced:

- `tests/fixtures/behavior_menu_utility_*_expected.txt`

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

## Proposed Future Behavior Shape

Future implementation may define a small read-only behavior result shape with
fields such as:

- command key
- label
- behavior family
- display/status lines
- state dependency notes
- state changed: false
- prompt required: false for Packet 1A
- sends real MIDI: false
- opens ports: false
- hardware required: false
- active behavior: false

Names are planning vocabulary only.

Do not implement this shape in this slice.

## Safe Failure Expectations

The future packet should fail safely for:

- unknown command keys
- command keys outside Packet 1A
- `T`, `C`, and `Q` until separately approved
- unsupported metadata shape
- missing optional state

Safe failure means:

- no exception unless tests intentionally assert a deterministic exception type
- no state mutation
- no MIDI
- no port opening
- no CLI active behavior
- no hardware requirement

## Required Future Tests

Future Packet 1A tests should verify:

- importing the new module prints nothing
- supported menu/status keys return deterministic read-only behavior results
- `BD` returns a menu/status behavior result
- `J` returns a group layout display intent without group mutation
- `SCN` returns scene menu display intent without scene execution
- `H` and `R` return state-reporting intent without runtime state mutation
- unsupported keys fail safely
- `T`, `C`, and `Q` are deferred or safe-fail unless separately approved
- passive CLI behavior remains unchanged
- no real MIDI library is imported
- no ports are opened
- no MIDI is sent
- no active CLI command is added
- V1.34 reference remains untouched
- package metadata files remain absent unless separately approved

## Closeout Expectations For Future Packet 1A

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

## Parallelization Decision

Do not parallelize the first implementation packet.

Reason:

- the packet is intentionally small
- routing shape and result shape need to stabilize
- file ownership is concentrated
- parallel workers would add coordination overhead before the first behavior
  shape exists

Parallel implementation can be reconsidered after Packet 1A lands cleanly.

## Explicit Non-Goals

- no implementation in this slice
- no tests in this slice
- no command dispatch in this slice
- no command execution
- no scene execution
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

## Stop Conditions

Stop before future implementation if:

- Packet 1A scope grows beyond read-only menu/status behavior
- `T`, `C`, or `Q` require prompt/session behavior in the first packet
- CLI wiring is required
- active behavior is required
- real MIDI is required
- port opening is required
- hardware is required
- package metadata changes are required without separate approval
- file ownership expands beyond the allowed future implementation files
- tests are not clear before code changes

## Next Safe Options

- docs-only review/acceptance of this Packet 1 plan
- pause at this planning checkpoint
- if accepted, implement Packet 1A exactly as a tiny scoped packet

## Recommendation

Review and accept this Packet 1 plan next.

After acceptance, implement only Packet 1A as a tiny read-only menu/status
behavior shape.

Keep `T`, `C`, and `Q` deferred unless separately approved.

Keep hardware off.

Keep package metadata absent.

## Decision

Packet 1 planning is documented.

The first future implementation target should be Packet 1A: read-only
menu/status behavior for the lowest-risk display and state-reporting commands.

No implementation is added.
