# Mock MIDI Boundary Test Plan

## Purpose

This document defines a test-only mock MIDI boundary before any real MIDI
implementation.

It is design/planning only. No MIDI code is added by this document. No active
execution exists yet.

## Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 78d527a Add active-layer design review

Current phase:

- passive CLI / dry-run foundation complete
- active-layer design/spec accepted for planning

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## Current Passive Capabilities

- report
- list commands/scenes/group profiles
- search commands/scenes/group profiles
- inspect commands/scenes/group profiles
- preview commands/scenes/group profiles

## Mock MIDI Boundary Concept

- Future MIDI behavior must be isolated behind a mockable interface.
- High-level active command logic must not directly open ports.
- High-level active command logic must not directly call real MIDI libraries.
- Tests must be able to capture intended MIDI messages without touching hardware.
- Real MIDI output must be impossible in ordinary unit tests.

## Proposed Conceptual Interfaces

These are future design names only, not implementation.

### MidiMessage

- command type
- channel
- control/change value
- metadata

### MidiSender

- `send(message)`
- `send_many(messages)`

### MockMidiSender

- records messages in memory
- never opens ports
- never talks to hardware

### MidiPortProvider

- future real implementation only
- forbidden in unit tests

### HardwareExecutionContext

- target device
- target port
- armed status
- dry-run preview reference

### ActiveCommandExecutor

- receives validated command metadata
- receives execution context
- emits messages through injected sender

## Test-Only Design Rules

- Unit tests must use MockMidiSender only.
- Unit tests must assert no real ports are opened.
- Unit tests must assert no real MIDI is sent.
- Tests should inspect intended message objects.
- Tests should fail if active code tries to import or call real port-opening behavior.
- Passive CLI tests must remain unchanged and must prove passive commands stay passive.

## Future Message Verification

Tests should verify:

- expected channel
- expected CC number
- expected value
- expected command key
- expected pad/track scope
- expected safety metadata

Tests should not require hardware. Tests should not depend on connected
devices.

## Arming And Mock Execution

Future active command tests must include:

- missing `--armed` fails safely
- unknown command fails safely
- unsupported command fails safely
- known test candidate with `--armed` emits expected mock messages only
- no messages emitted when validation fails
- no messages emitted for passive commands

## Passive-To-Active Separation

- Passive commands must never receive a real MidiSender.
- report/list/search/inspect/preview must not construct HardwareExecutionContext.
- report/list/search/inspect/preview must not open ports.
- report/list/search/inspect/preview must not emit messages.
- The passive CLI remains read-only by default.

## First Mock Test Candidate Constraints

Do not select final real hardware test yet.

Mock candidate may describe one validated Pad 1 anchor or simple CC action only
as a future test candidate.

It must be tiny, isolated, and reversible.

It must not:

- be a scene
- be a global mutation
- be wild/random discovery
- use SysEx
- touch Pads 5-12
- touch Analog Four
- change project
- save or clear a kit
- change pattern
- start/stop transport
- change clock

## Forbidden In This Phase

- real MIDI library integration
- port opening
- hardware detection
- hardware send
- active CLI command
- execute-command
- send-command
- hardware-test implementation
- scenes/global mutation execution
- Pads 5-12
- Analog Four
- SysEx
- GUI
- capture

## Future Closeout Expectations Before Implementation

- Closeout must still pass.
- V1.34 reference diff must remain empty.
- Git status must be clean.
- Passive CLI tests must still pass.
- Mock MIDI tests must prove no real ports are touched.
- Any future active test file must be explicit about mock-only behavior.

## Operator/Hardware Reminder

- Do not turn on Analog Rytm.
- Do not turn on Analog Four.
- Hardware is not needed for mock design or mock tests.
- Hardware validation requires a later explicit phase.

## Next Recommended Task After This Plan

Review status:

- `Docs/MOCK_MIDI_BOUNDARY_TEST_PLAN_REVIEW.md`

The mock MIDI boundary test plan is accepted for planning. The next recommended
task is a test-only mock MIDI scaffold with no real MIDI backend, or a more
detailed implementation spec if further review is needed.

Implemented milestone:

- 58f4a44 Add test-only mock MIDI scaffold
- `rytm_randomizer/mock_midi.py`
- `tests/test_mock_midi.py`
- `Scripts/closeout_check.ps1`

The scaffold records intended messages in memory only and keeps all MIDI
behavior mock-only/test-only. It adds no real MIDI backend, no port provider,
no hardware detection, no hardware send, no active CLI command, and no
execution.

Mock MIDI scaffold review:

- `Docs/MOCK_MIDI_SCAFFOLD_REVIEW.md`

The review accepts the test-only mock MIDI scaffold, records that no real MIDI
behavior exists, sets the next recommended task as mock message mapping
design/spec or a test-only mapper scaffold, and keeps hardware off.

Mock message mapping design/spec:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC.md`

The spec defines future mock-only mapping from passive metadata to mock
MidiMessage objects, keeps hardware off, keeps real MIDI absent, and sets the
next recommended task as review/acceptance before any mapper scaffold.

Mock message mapping design/spec review:

- `Docs/MOCK_MESSAGE_MAPPING_DESIGN_SPEC_REVIEW.md`

The review accepts the mock message mapping design/spec for planning, records
that no mapper implementation exists yet, sets the next recommended task as a
test-only mock mapper scaffold for group profile 2, and keeps hardware off.

Test-only mock message mapper:

- 4a590c8 Add test-only mock message mapper
- `rytm_randomizer/mock_message_mapper.py`
- `tests/test_mock_message_mapper.py`
- `Scripts/closeout_check.ps1`

The mapper uses existing passive group profile metadata and the mock_midi.py
scaffold to create deterministic inert mock MidiMessage objects for group
profile key `"2"` / My BD Hard only. It records cleanly through
MockMidiSender, fails safely for unknown or unsupported keys, and is not wired
to CLI or runtime execution. The closeout suite now includes "Test: Mock
Message Mapper".

Still no real MIDI and no hardware.
