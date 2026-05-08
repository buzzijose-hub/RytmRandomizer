# V1.34 Legacy Single-Profile Mutation Next Passive Metadata Gap Decision Note

## Purpose

Select the next passive metadata planning target after the completed profile
selection / anchor loading metadata checkpoint.

This is a documentation-only decision note. It does not add metadata, tests,
fixtures, runtime behavior, CLI wiring, dispatch, MIDI, ports, package
metadata, active behavior, hardware behavior, or hardware validation.

## Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this slice:

- `249bc67 Update checkpoint after profile selection anchor passive metadata`

Current passive command count:

- `101`

Captured V1.34 operator command entries modeled as passive command metadata:

- `98`

Remaining captured command-surface gaps:

- `8`

## Current Remaining Gap Candidates

The remaining captured V1.34 command-surface gaps are:

- `M1` / Legacy single-profile full micro mutation
- `M2` / Legacy single-profile full groove mutation
- `M3` / Legacy single-profile full strong mutation
- `S` / SRC-only mutation, choose depth
- `F` / Filter-only mutation, choose depth
- `A` / Amp-only mutation, choose depth
- `G` / Grit-only mutation, choose depth
- `K` / Kick body mutation, choose depth

## Selected Next Planning Target

The selected next planning target is legacy single-profile mutation metadata:

- `M1` / Legacy single-profile full micro mutation
- `M2` / Legacy single-profile full groove mutation
- `M3` / Legacy single-profile full strong mutation

## Rationale

- `M1`, `M2`, and `M3` form a contained legacy mutation group.
- They come naturally after `P` and `M`, which model selected-profile
  workflow metadata.
- They can be represented as passive scaffold metadata without runtime
  selected-profile mutation.
- The three-command group is smaller than the remaining five generic
  current-profile page mutation commands.
- Keeping `S`, `F`, `A`, `G`, and `K` parked preserves a final contained
  metadata slice for later planning.

## Future Count Movement If Implemented

If later implemented as passive metadata only:

- passive command count would move from `101` to `104`
- captured modeled count would move from `98` to `101`
- remaining captured gaps would move from `8` to `5`

This note does not implement that movement.

## Required Future Plan Scope

A future expansion plan should define:

- a passive metadata dictionary for legacy single-profile mutation commands
- metadata for `M1`
- metadata for `M2`
- metadata for `M3`
- expected command count movement from `101` to `104`
- expected registry report count movement from `commands: 101` to
  `commands: 104`
- expected captured modeled count movement from `98` to `101`
- expected remaining gap movement from `8` to `5`
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
- No selected-profile runtime mutation
- No legacy mutation execution
- No depth execution
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

- Do not implement `M1`, `M2`, or `M3` metadata in this slice.
- Do not implement `S`, `F`, `A`, `G`, or `K` metadata yet.
- Do not add selected-profile mutation execution.
- Do not add depth execution.
- Do not add runtime selected-profile state mutation.
- Do not add active CLI behavior.
- Do not add real MIDI or ports.
- Do not turn on hardware.

## Decision

Proceed next with a documentation-only passive metadata expansion plan for:

- `M1`
- `M2`
- `M3`

Implementation remains parked until a separate plan, review, and explicit
approval.
