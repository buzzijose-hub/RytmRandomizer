# V1.34 Profile Selection Anchor Next Passive Metadata Gap Decision Note

## Purpose

Select the next passive metadata planning target after the completed
isolated-pad mutation metadata checkpoint.

This is a documentation-only decision note. It does not add metadata, tests,
fixtures, runtime behavior, CLI wiring, dispatch, MIDI, ports, package
metadata, active behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `3d45ff9 Update checkpoint after isolated pad mutation passive metadata`

Current passive command count:

- `99`

Captured V1.34 operator command entries modeled as passive command metadata:

- `96`

Remaining captured command-surface gaps:

- `10`

## Current Remaining Gap Candidates

The remaining captured V1.34 command-surface gaps are:

- `P` / select/switch profile and change Rytm machine
- `M` / load selected profile anchor
- `M1` / Legacy single-profile full micro mutation
- `M2` / Legacy single-profile full groove mutation
- `M3` / Legacy single-profile full strong mutation
- `S` / SRC-only mutation, choose depth
- `F` / Filter-only mutation, choose depth
- `A` / Amp-only mutation, choose depth
- `G` / Grit-only mutation, choose depth
- `K` / Kick body mutation, choose depth

## Selected Next Planning Target

The selected next planning target is profile selection / anchor loading
metadata:

- `P` / select/switch profile and change Rytm machine
- `M` / load selected profile anchor

## Rationale

- `P` and `M` are foundational profile workflow commands.
- They are narrower than generic mutation commands.
- They can be represented as passive scaffold metadata without runtime state
  mutation.
- They bridge the already-modeled profile metadata and the remaining
  single-profile command surface.
- Modeling them first keeps `M1`, `M2`, `M3`, `S`, `F`, `A`, `G`, and `K`
  parked until separately planned.

## Future Count Movement If Implemented

If later implemented as passive metadata only:

- passive command count would move from `99` to `101`
- captured modeled count would move from `96` to `98`
- remaining captured gaps would move from `10` to `8`

This note does not implement that movement.

## Required Future Plan Scope

A future expansion plan should define:

- a passive metadata dictionary for profile selection / anchor loading
- metadata for `P`
- metadata for `M`
- expected command count movement from `99` to `101`
- expected registry report count movement from `commands: 99` to
  `commands: 101`
- expected captured modeled count movement from `96` to `98`
- expected remaining gap movement from `10` to `8`
- existing scaffold and command lookup test updates
- passive list/report fixture updates

## Safety Boundaries

- No real MIDI
- No `mido`
- No MIDI port opening
- No MIDI sending
- No active execution
- No CLI active command
- No runtime dispatch
- No command execution
- No scene execution
- No profile runtime state mutation
- No machine change execution
- No anchor loading execution
- No selected profile persistence
- No hardware behavior
- No SysEx
- No GUI/capture
- No Analog Four support
- No Pads 5-12 support
- No machine/profile universe expansion
- No package metadata changes
- `rytm_hybrid_randomizer_v134.py` remains untouched

## Rejected Next Moves For This Slice

- Do not implement `P` or `M` metadata in this slice.
- Do not implement `M1`, `M2`, or `M3` metadata yet.
- Do not implement `S`, `F`, `A`, `G`, or `K` metadata yet.
- Do not add runtime profile switching.
- Do not add machine change execution.
- Do not add anchor loading execution.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not turn on hardware.

## Decision

Proceed next with a documentation-only passive metadata expansion plan for:

- `P`
- `M`

Implementation remains parked until a separate plan, review, and explicit
approval.
