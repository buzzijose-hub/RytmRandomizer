# Hardware Manual Reference Inventory

## 1. Purpose

Record the local hardware manuals that can support future planning and
validation work without copying the PDF files into this repository.

This inventory is reference-only. It does not add implementation, tests, MIDI,
ports, dispatch, active behavior, package metadata, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this documentation slice:

- `36b7f55 Add Packet 5D BD Silky lane behavior`

Current phase:

- Passive/Mock Foundation Phase
- read-only behavior parity work in progress
- Packet 5D BD Silky lane behavior implemented as read-only intent metadata
- hardware manual references now being inventoried for future planning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Storage Decision

The manuals should remain outside the repository at their current local
Dropbox paths.

Reasons:

- PDF manuals are large binary files.
- The manuals are likely copyrighted vendor documentation.
- The repository only needs stable reference pointers and usage guardrails.
- Future notes can cite specific sections or pages without committing the PDF
  files.

Do not copy the manuals into the repository unless there is a separate,
explicit approval and licensing/storage decision.

## 4. Manual Inventory

### Analog Rytm MKII Manual

Local path:

- `C:\Users\Jose Buzzi\Dropbox\Utilities\elektron-analog-rytm-mkii-manual.pdf`

Device:

- Elektron Analog Rytm MKII

Future reference value:

- Analog Rytm machine/engine concepts
- kit, sound, pattern, scene, performance concepts
- parameter names and ranges
- MIDI behavior planning
- CC and hardware validation planning
- safe operator checklist refinement

Current use:

- reference only
- no hardware required
- no MIDI behavior authorized

### Analog Four MKII Manual

Local path:

- `C:\Users\Jose Buzzi\Dropbox\Utilities\Analog-Four-MKII-User-Manual_ENG_OS1.40A_200303.pdf`

Device:

- Elektron Analog Four MKII

Future reference value:

- future Analog Four architecture planning
- MIDI behavior planning for a later Analog Four phase
- parameter and performance concepts
- cross-device roadmap context

Current use:

- reference only
- Analog Four support remains out of scope
- no hardware required
- no MIDI behavior authorized

## 5. Current Safety Boundary

This inventory confirms:

- no real MIDI
- no `mido`
- no `rtmidi`
- no MIDI port discovery
- no MIDI port opening
- no MIDI sending
- no command dispatch
- no command execution
- no scene execution
- no runtime execution
- no hardware behavior
- no hardware validation
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no package metadata changes

`rytm_hybrid_randomizer_v134.py` remains untouched.

Hardware remains off.

## 6. Future Reference Workflow

When future work needs manual details:

- inspect only the relevant manual sections
- record section/page references in a new planning document
- summarize only the facts needed for the current slice
- keep vendor manual text out of the repository except for short, necessary
  references
- use manual findings to inform docs-only plans before implementation
- keep hardware off until an explicitly approved hardware-validation phase

## 7. Good Future Uses

Good future manual-backed slices:

- Rytm MIDI CC reference notes
- Rytm machine/engine parameter reference notes
- safe hardware validation checklist refinement
- first-hardware-candidate research notes
- Analog Four future-scope inventory

Each future slice should remain separately scoped and reviewed.

## 8. Non-Goals

This inventory does not:

- copy manuals into the repository
- parse manuals
- extract MIDI tables
- implement MIDI
- implement active behavior
- implement hardware behavior
- authorize turning hardware on
- authorize Analog Four work
- add SysEx
- add package dependencies
- change runtime behavior

## 9. Next Recommended Task

Return to the current behavior-parity workflow:

- create the docs-only Packet 5D implementation checkpoint, or
- pause at this clean reference-inventory checkpoint.

Hardware remains off.
