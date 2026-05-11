# V1.34 Behavior Parity PZ Read-Only Runtime Readiness Behavior Checkpoint

## 1. Purpose

Record the completed tiny `PZ` implementation slice after the accepted
runtime-state readiness and implementation plan reviews.

This checkpoint documents the new read-only/inert `PZ` runtime-readiness
behavior.

It does not authorize active behavior, anchor return execution, selected pad
switching, dispatch, MIDI, ports, package metadata changes, or hardware
behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this implementation slice:

- `5cd0850 Add PZ implementation plan review after runtime-state readiness`

Implementation milestone:

- `b04aa8d Add PZ read-only runtime readiness behavior`

Current phase:

- passive/mock foundation
- V1.34 behavior-parity implementation packets
- selected target state implemented and reviewed
- anchor state implemented and reviewed
- selected isolated pad runtime state implemented and reviewed
- `PZ` implementation plan reviewed and accepted
- `PZ` read-only runtime-readiness behavior now implemented

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Files Changed By The Milestone

Implementation files:

- `rytm_randomizer/behavior_selected_isolated_pad.py`

Test files:

- `tests/test_behavior_selected_isolated_pad.py`
- `tests/test_behavior_anchor_profile_report.py`

No closeout script update was needed because `tests/test_behavior_selected_isolated_pad.py`
is already covered by:

- `Behavior Selected Isolated Pad`

Package metadata remained untouched.

## 4. Implemented Behavior

`PZ` now reports read-only selected isolated pad anchor-return readiness.

The helper remains:

- passive
- deterministic
- metadata-rich
- copy/immutability-safe
- non-executing
- non-hardware-facing

The public helper now supports:

- `evaluate_selected_isolated_pad_behavior(command_key, runtime_state=None)`

For `PZ`, if `runtime_state` is omitted, the helper uses the conservative
passive default selected isolated pad runtime-state builder.

Default `PZ` behavior:

- selected target context defaults to Pad 3
- anchor context remains unavailable
- `accepted` is `False`
- `reason` is `anchor_unavailable_for_selected_target`
- `anchor_return_intent` is `True`
- `anchor_return_executed` is `False`
- `selected_pad_switch_executed` is `False`
- `state_changed` is `False`
- `pz_ready` is `False`
- `pz_executed` is `False`

Injected runtime-state behavior:

- runtime-state data can be consumed by `PZ`
- runtime-state data is not mutated
- missing, unsupported, stale, invalid, or unavailable contexts still fail
  safely
- no messages, ports, dispatch, execution, or hardware behavior are involved

## 5. Public Scope Update

Selected isolated pad behavior constants now reflect the accepted `PZ` scope:

- `PACKET_11A_SELECTED_ISOLATED_PAD_KEYS`
  - `("L",)`
- `PACKET_11B_SELECTED_ISOLATED_PAD_KEYS`
  - `("PZ",)`
- `SUPPORTED_SELECTED_ISOLATED_PAD_KEYS`
  - `("L", "PZ")`
- `DEFERRED_PACKET_11_SELECTED_ISOLATED_PAD_KEYS`
  - `()`

This means `PZ` is implemented as an inert readiness helper, not active anchor
return.

## 6. Confirmed Boundaries

This milestone adds no:

- selected pad switching execution
- anchor return execution
- runtime state mutation
- command dispatch
- command execution
- scene execution
- mutation execution
- CLI execution wiring
- active CLI command
- `execute-command`
- `send-command`
- `hardware-test`
- real MIDI dependency
- `mido`
- `rtmidi`
- port discovery
- port opening
- MIDI sending
- package metadata changes
- hardware behavior
- hardware validation
- SysEx
- GUI/capture
- Analog Four support
- Pads 5-12 support
- machine/profile universe expansion

`rytm_hybrid_randomizer_v134.py` remains untouched.

Package metadata remains untouched.

## 7. Preserved Behavior

Existing `L` behavior remains read-only selected isolated pad target intent.

Packet 1 selected pad status behavior remains unchanged.

Packet 3 selected isolated pad mutation intent behavior remains unchanged.

Passive CLI behavior remains unchanged.

Profile `4` mock mapper support remains unsupported/safe.

## 8. Verification

Focused pytest passed:

- `python -m pytest tests/test_behavior_selected_isolated_pad.py tests/test_behavior_anchor_profile_report.py -v`
- `30 passed`

Direct script checks passed:

- `python .\tests\test_behavior_selected_isolated_pad.py`
- `python .\tests\test_behavior_anchor_profile_report.py`

Full closeout passed:

- `powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1`

Protected diffs:

- `git diff -- rytm_hybrid_randomizer_v134.py`
  - empty
- `git diff -- pyproject.toml requirements.txt setup.py setup.cfg`
  - empty

Final git status after implementation commit:

- clean

## 9. Safety Decision

`PZ` is accepted as implemented behavior only at read-only runtime-readiness
altitude.

It is not active behavior.

It is not anchor return execution.

It is not selected pad switching.

It is not runtime mutation.

It is not hardware-facing.

## 10. Safe Next Options

Safe next options:

- docs-only review/acceptance gate for this `PZ` checkpoint
- broader behavior-parity progress report after `PZ`
- continue with another separately planned read-only behavior-parity slice
- pause at this clean implementation checkpoint

Review status:

- review document created:
  - `Docs/V134_BEHAVIOR_PARITY_PZ_READ_ONLY_RUNTIME_READINESS_BEHAVIOR_CHECKPOINT_REVIEW.md`

## 11. Recommendation

Proceed next with a docs-only review/acceptance gate for this `PZ`
implementation checkpoint.

Do not add MIDI, ports, active behavior, runtime execution, package metadata
changes, or hardware behavior.

## 12. Decision Summary

`PZ` read-only runtime-readiness behavior is implemented and checkpointed.

Hardware remains off.

No implementation beyond inert readiness behavior is authorized by this
checkpoint.
