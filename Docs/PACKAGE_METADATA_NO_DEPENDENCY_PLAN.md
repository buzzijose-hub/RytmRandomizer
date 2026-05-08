# Package Metadata No-Dependency Plan

> **For agentic workers:** REQUIRED SUB-SKILL for any future implementation:
> use verification before completion and keep the implementation slice
> separate from this planning document. This plan is not authorization to edit
> package metadata.

**Goal:** Define how future package metadata work should be planned while
keeping the current no-dependency position intact.

**Architecture:** Package metadata, if later approved, must be introduced as a
separate, review-gated slice. It must not select a real MIDI dependency, must
not add `mido`, and must not change runtime behavior by itself.

**Tech Stack:** Current Python project with no root `pyproject.toml`,
`requirements.txt`, `setup.py`, or `setup.cfg` in the checked baseline.

---

## 1. Purpose

Document a package metadata plan after the accepted user-facing no-dependency
progress report review.

This plan defines what must be true before any future package metadata file is
created or edited.

This plan does not create package metadata.

This plan does not select a dependency.

This plan does not install dependencies.

This plan does not implement real MIDI, open ports, send MIDI, add active CLI
behavior, dispatch commands, add hardware behavior, or start hardware
validation.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- bae5746 Add no-dependency user-facing progress report review

Current phase:

- Passive/Mock Foundation Phase
- mock-first active boundary exists for test-only evaluation
- first fake-provider-only real MIDI adapter boundary exists
- user-facing no-dependency progress report is reviewed and accepted
- no real MIDI dependency is selected
- package metadata remains unchanged
- hardware validation has not started

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Current Package Metadata State

Checked root package metadata files:

- `pyproject.toml`: absent
- `requirements.txt`: absent
- `setup.py`: absent
- `setup.cfg`: absent

Current decision:

- do not create package metadata in this slice
- do not edit package metadata in this slice
- keep package metadata unchanged
- keep dependency selection deferred

## 4. Accepted No-Dependency Position

Accepted dependency position:

- Candidate A: continue with no real MIDI dependency
- dependency selection remains deferred
- package metadata remains unchanged
- fake-provider-only adapter boundary remains the current adapter baseline
- passive CLI remains isolated from MIDI backend behavior
- active CLI behavior remains absent
- hardware validation remains blocked
- hardware remains off

The following candidates remain not selected:

- Candidate B: future `mido`-style adapter backend
- Candidate C: future direct backend adapter
- Candidate D: custom or OS-specific MIDI path

## 5. Future Package Metadata Goal

If package metadata is later approved, the first package metadata slice should
be boring and minimal.

The likely future goal is to create one canonical project metadata file, such
as `pyproject.toml`, only after a separate review gate accepts that edit.

The first future metadata slice should not add runtime dependencies.

The first future metadata slice should not add `mido`.

The first future metadata slice should not make hardware behavior possible.

## 6. Future Metadata Ownership

Future package metadata ownership should be explicit.

Potential future ownership:

- Create: `pyproject.toml`
- Do not create by default: `requirements.txt`
- Do not create by default: `setup.py`
- Do not create by default: `setup.cfg`

Recommendation:

- prefer one future `pyproject.toml` if package metadata is approved
- avoid split metadata across multiple package files
- keep dependency lists empty or dependency-free until a separate dependency
  selection review accepts otherwise

## 7. Future `pyproject.toml` Constraints

If a future `pyproject.toml` is approved, it must initially stay minimal.

Allowed future concepts:

- project name
- project version placeholder or existing project version if already accepted
- Python version requirement if separately reviewed
- basic project metadata
- optional test configuration only if needed and separately reviewed

Forbidden without a separate dependency selection review:

- `mido`
- `python-rtmidi`
- real MIDI backend dependencies
- hardware discovery dependencies
- GUI dependencies
- capture/audio analysis dependencies
- SysEx-related dependencies
- Analog Four dependencies
- Pads 5-12 expansion dependencies

## 8. Future Dependency Selection Boundary

This plan does not select a dependency.

This plan keeps Candidate A as the current accepted path.

Any future dependency selection requires:

- separate dependency selection review
- separate package metadata review
- clean Git status
- closeout passing
- V1.34 reference diff empty
- package metadata diff explicitly reviewed
- no passive CLI behavior regression
- no hardware required
- hardware remains off

## 9. Future Package Metadata Preconditions

Before any future package metadata edit:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- current package metadata diff is empty
- this plan has been reviewed and accepted
- exact metadata file ownership is named
- exact future metadata content is specified
- no real MIDI dependency is selected by default
- no hardware is required
- hardware remains off

## 10. Future Verification Requirements

Any future package metadata slice must verify:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff contains only the approved metadata file changes
- passive CLI still imports without opening ports
- passive CLI commands remain read-only
- no `mido` is imported
- no real MIDI dependency is installed
- no real ports are opened
- no MIDI is sent
- Git status is clean after commit

## 11. Confirmed Absent Behavior

Confirmed absent:

- no `mido`
- no real MIDI dependency
- no package metadata change
- no real MIDI backend
- no real port discovery
- no real port listing
- no real port opening
- no real MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no profile `"3"` active-boundary support
- no hardware validation
- no hardware-on authorization

## 12. Safe Next Branches

Safe next branches:

- review and accept this package metadata no-dependency plan
- pause at this clean package metadata planning checkpoint
- continue passive/project documentation
- create an exact future package metadata implementation plan only after
  explicit approval
- create a future dependency selection review only after explicit approval

## 13. Recommendation

Review and accept this plan next.

Do not create package metadata yet.

Do not select a real MIDI dependency yet.

Do not add `mido`.

Do not change package metadata.

Do not add active CLI commands.

Do not open ports.

Do not send MIDI.

Do not turn on hardware.

## 14. Decision

The package metadata path is now planned at documentation level only.

Candidate A remains the current path.

Dependency selection remains deferred.

Package metadata remains unchanged.

Hardware remains off.

No implementation is added by this slice.

## 15. Review Gate

The plan review now lives in:

- `Docs/PACKAGE_METADATA_NO_DEPENDENCY_PLAN_REVIEW.md`

The review accepts this plan as the current package metadata planning
checkpoint. It keeps Candidate A as the accepted no-dependency path, keeps
dependency selection deferred, keeps package metadata unchanged, keeps
hardware validation blocked, and keeps hardware off.

The review does not authorize creating package metadata, selecting
dependencies, editing package metadata, implementing real MIDI, adding active
CLI behavior, starting hardware validation, or turning hardware on.
