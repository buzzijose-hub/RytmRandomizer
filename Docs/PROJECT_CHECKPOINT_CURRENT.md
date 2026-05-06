# RytmRandomizer Current Project Checkpoint

Date: May 4, 2026
Status: Active branch is modularize-v1.34

## Current Stable Reference

The protected stable reference is V1.34 expanded scene layer.

Git tag:

v1.34-stable-expanded-scene-layer

V1.34 remains the behavior reference until the modular version is fully validated.

## Current Git State

Current branch:

modularize-v1.34

Recent checkpoint history:

- 97ecf09 Add registry report golden text contract
- e387f66 Add passive registry report generator
- f6b10ca Add passive architecture summary
- e7b0755 Add passive command lookup helpers
- 748c320 Add passive scene lookup helpers
- 02bd056 Add passive group profile lookup helpers
- 54aca99 Add closeout check workflow
- 55342e7 Add behavior-preserving extraction plan
- dc1ecfc Add passive registry audit reports
- eab5898 Add passive command preview reports
- be92ab4 Add passive command inspection helpers
- 68b16e1 Harden passive metadata validation tests
- 1b4aee3 Add passive metadata validation helpers
- c926719 Add constants scaffold coverage
- d56ff2f Update checkpoint after PAD_PROFILES coverage
- 03b6a8e Add PAD_PROFILES scaffold coverage
- a4a0170 Update checkpoint after command metadata refinement
- c7d5489 Refine command metadata consistency
- a87f7bb Add Codex modularization protocol
- e3a37e3 Add individual pad command metadata scaffold
- 90f1677 Refine scene command metadata scaffold
- 556a7ba Add group command metadata scaffold
- 1130205 Clean up scaffold metadata tests
- 35e598f Add menu command metadata scaffold
- a0f5005 Add forbidden action guardrail metadata
- defbf43 Add out-of-scope pad guardrail metadata
- 8be1dfa Add validated constants metadata scaffold
- 57d3502 Add group profile metadata scaffold
- ae112cf Add main prompt depth guardrail metadata
- 0b94806 Add group layout metadata scaffold
- 3222200 Expand scene metadata scaffold
- b1d04e6 Add initial modular scaffold and tests
- 7de1691 Add Codex modularization task brief
- 50b83f9 Add modularization rules
- a762bd0 Add capture tools and project docs
- cc5ce71 Baseline V1.34 expanded scene layer checkpoint

## Current Priority

Finish behavior-preserving modularization of V1.34.

No new features should be added until the modular version behaves exactly like V1.34.

## Current Modular Scaffold

The modular scaffold is still metadata-only. Current scaffold coverage includes:

- constants / pad scope guardrails
- out-of-scope Pads 5-12 guardrails
- scene command metadata
- group layout / profile metadata
- menu / status command metadata
- forbidden / no-touch action metadata
- four-lane group command metadata
- individual Pad 1-4 command metadata
- command metadata consistency checks
- passive command registry validation
- passive command inspection
- passive command preview reports
- passive registry audit reports
- passive group profile lookup helpers
- passive scene lookup helpers
- passive command lookup helpers
- unified passive registry view
- passive registry report generator
- registry report golden text contract
- passive architecture summary
- behavior-preserving extraction plan
- closeout check workflow
- scaffold metadata tests
- Codex modularization protocol

The closeout check workflow includes:

- Scripts/closeout_check.ps1
- Docs/Session_Logs/

The closeout script runs the standard passive test suite and safety checks:

- python .\tests\test_scaffold.py
- python .\tests\test_validation.py
- python .\tests\test_inspection.py
- python .\tests\test_preview.py
- python .\tests\test_audit.py
- python .\tests\test_profile_lookup.py
- python .\tests\test_scene_lookup.py
- python .\tests\test_command_lookup.py
- python .\tests\test_registry.py
- python .\tests\test_registry_report.py
- git diff -- rytm_hybrid_randomizer_v134.py
- git status --short

The closeout script now includes "Test: Profile Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Scene Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Command Lookup" as part of the standard
passive test suite.

The closeout script now includes "Test: Registry" as part of the standard
passive test suite.

The closeout script now includes "Test: Registry Report" as part of the
standard passive test suite.

The latest clean closeout confirmed that scaffold, validation, inspection,
preview, audit, profile lookup, scene lookup, command lookup, and registry tests
and registry report tests passed silently; the V1.34 reference diff was empty;
and git status was clean.

The passive registry report generator includes:

- rytm_randomizer/registry_report.py
- tests/test_registry_report.py

The registry report golden text contract includes:

- tests/test_registry_report.py
- tests/fixtures/registry_report_expected.txt

The golden text contract locks down the formatted passive registry report
output, adds snapshot-style golden text coverage, and ensures future CLI, UI,
and reporting work has a stable deterministic report structure. The test
normalizes line endings so Windows CRLF/LF differences do not cause false
failures. Closeout already includes registry report testing, so no duplicate
closeout entry was needed.

The report generator sits on top of the unified passive registry view. It
generates in-memory, read-only report data for registry sections, per-section
item counts, known sections commands/scenes/group_profiles, passive safety
boundary summary, unsupported scope summary, and active behavior status. The
formatted report is intended for inspection, documentation, future UI, and
future CLI preview work only. It does not write report files, create a CLI
command, or print during import.

The unified passive registry view includes:

- rytm_randomizer/registry.py
- tests/test_registry.py

The registry currently exposes copied read-only views for these sections:

- commands
- scenes
- group_profiles

The registry is passive/read-only from the caller perspective. It returns copied
data, does not allow caller mutation of source metadata, and uses passive
not-found behavior for unknown sections or items. It is intended for inspection,
reporting, preview, documentation, and future UI work only.

The passive architecture summary includes:

- Docs/PASSIVE_ARCHITECTURE_SUMMARY.md

The summary documents the current passive scaffold, lookup helpers, closeout
suite, safety boundaries, and conditions required before any hardware-facing
layer.

The passive command lookup helper includes:

- rytm_randomizer/command_lookup.py
- tests/test_command_lookup.py

The helper is passive/read-only. It only reads existing COMMANDS metadata.
Returned metadata is copied to prevent source mutation, and unknown command
keys return passive not-found behavior. No execution/handler/callable fields are
exposed. Pads 5-12 remain absent.

The passive scene lookup helper includes:

- rytm_randomizer/scene_lookup.py
- tests/test_scene_lookup.py

The helper is passive/read-only. It only reads existing SCENE_COMMANDS
metadata. Returned metadata is copied to prevent source mutation, and unknown
scene keys return passive not-found behavior. Pads 5-12 remain absent.

The passive group profile lookup helper includes:

- rytm_randomizer/profile_lookup.py
- tests/test_profile_lookup.py

The helper is passive/read-only. It only looks up existing
GROUP_PROFILE_METADATA keys "2", "3", "4", and "5". Returned metadata is copied
to prevent source mutation, and unknown keys return passive not-found behavior.
Pads 5-12 remain absent.

The behavior-preserving extraction plan includes:

- Docs/BEHAVIOR_PRESERVING_EXTRACTION_PLAN.md

The plan defines the transition from passive scaffold/reporting work toward
future pure extraction slices while keeping runtime wiring and MIDI/hardware
behavior out of scope until separately approved.

The passive registry audit/report layer includes:

- rytm_randomizer/audit.py
- tests/test_audit.py

The audit layer is passive/read-only and returns registry reports only. Audit
reports include validation status, command count, category/type counts, scope
counts, pad counts, all_non_executable, all_scaffold_only, and the fixed safety
summary: "No MIDI would be sent. No command would execute."

tests/test_audit.py covers:

- real COMMANDS registry audit
- validation ok
- all_non_executable
- all_scaffold_only
- scene/group/pad scope counts
- Pads limited to 1-4 where present
- synthetic invalid registry validation errors
- source metadata is not mutated

The passive command preview/report layer includes:

- rytm_randomizer/preview.py
- tests/test_preview.py

The preview layer sits on top of passive inspection and returns dry-run command
reports only. It includes the fixed safety summary: "No MIDI would be sent. No
command would execute."

tests/test_preview.py covers:

- known scene command
- group command
- pad command
- unknown command
- synthetic invalid registry validation errors
- metadata/report safety behavior

The passive command inspection layer includes:

- rytm_randomizer/inspection.py
- tests/test_inspection.py

inspect_command() returns a dry-run report only. It deep-copies metadata so
reports cannot mutate COMMANDS, calls the passive validator, and does not
dispatch, execute, send MIDI, read input, mutate state, or touch hardware.

tests/test_inspection.py covers:

- known scene command S1A
- unknown command
- group command O
- pad command P3A
- synthetic invalid registry errors
- metadata copy isolation

The passive validation layer includes:

- rytm_randomizer/validation.py
- tests/test_validation.py

The validator is read-only/passive and validates command registry safety. It
checks for executable: True, forbidden execution fields, missing scaffold_only /
v134_reference_command flags, and forbidden Pads 5-12 references.

Passive metadata validation hardening:

- nested forbidden pad tests exposed and fixed a TypeError
- validation now handles nested containers before direct forbidden-pad membership checks
- tests/test_validation.py covers nested pad lists containing forbidden Pads 5-12
- tests/test_validation.py covers forbidden pad text such as Pad 5
- tests/test_validation.py covers forbidden pad scope metadata such as pad_5

Scaffold metadata tests now include PAD_PROFILES coverage:

- exact key set {1, 3}
- no Pads 5-12
- Pad 1 links to existing PAD_1_DEFAULT_PROFILE
- Pad 3 remains SY Raw
- Pad 3 uses existing PAD_3_SY_RAW_CC_MAP

Scaffold metadata tests now also cover constants:

- MACHINE_CC == 15
- PAD1_DEFAULT_HOME == "BD Hard"
- Pad 1 default profile remains aligned with PAD1_DEFAULT_HOME

Command metadata consistency now covers:

- MENU_COMMANDS protocol fields
- full passive SCENE_COMMANDS metadata preserved inside COMMANDS
- guarded main-prompt 1/2/3 protocol fields
- all applicable command metadata remains executable: False
- no forbidden execution fields or runtime hooks

All metadata registries are passive. They do not dispatch commands, send MIDI,
read input, open ports, mutate state, or call runtime functions.

V1.34 remains protected. No runtime execution, MIDI sending, input handling,
command dispatch, Pads 5-12 expansion, GUI, capture, SysEx, or Analog Four
work has been added.

The passive validation layer added no MIDI sending, command dispatch, input
handling, SysEx, capture/state, GUI, Analog Four, or hardware behavior.

The passive validation hardening added no MIDI, runtime dispatch, input
handling, hardware state changes, SysEx, capture, GUI, Analog Four, or Pads
5-12 support.

The passive inspection layer added no MIDI, runtime execution, dispatch, input
handling, SysEx, capture, GUI, Analog Four, or Pads 5-12 support.

The passive preview layer added no MIDI, port opening, live randomizer, command
execution, dispatch, input handling, state mutation, SysEx, capture, GUI,
Analog Four, Pads 5-12 support, mutation behavior, handlers/callables, or
runtime hooks.

The passive audit layer added no MIDI, port opening, live randomizer, command
execution, dispatch, input handling, state mutation, SysEx, capture, GUI,
Analog Four, Pads 5-12 support, mutation behavior, handlers/callables, or
runtime hooks.

The passive group profile lookup helper added no MIDI, ports, dispatch,
hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12 support.

The passive scene lookup helper added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The passive command lookup helper added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The passive architecture summary added no MIDI, ports, dispatch, command
execution, hardware mutation, SysEx, GUI, capture, Analog Four, or Pads 5-12
support.

The unified passive registry view added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, or Pads 5-12 support. The protected V1.34 reference remains untouched.

The passive registry report generator added no MIDI sending, port opening,
dispatch, command execution, hardware mutation, SysEx, GUI, capture, Analog Four
support, Pads 5-12 support, or machine/profile universe expansion. The
protected V1.34 reference remains untouched.

The registry report golden text contract was test-only/passive hardening. It
added no CLI behavior, report file writing at runtime, import-time printing,
MIDI sending, port opening, dispatch, command execution, hardware mutation,
SysEx, GUI, capture, Analog Four support, Pads 5-12 support, or machine/profile
universe expansion. The protected V1.34 reference remains untouched.

## Validated Rytm Scope

Current validated system focuses on Analog Rytm MKII Pads 1-4.

- Pad 1 = main kick / BD engine lane
- Pad 2 = secondary percussion / snare lane
- Pad 3 = SY Raw bass / synth-percussion lane
- Pad 4 = BD Acoustic body / accent lane

## Validated Scene Layer

V1.34 includes the expanded scene system:

- S1A = Rolling Light
- S1B = Rolling Push
- S2A = Deeper Groove
- S2B = Deeper Pressure
- S3A = Intense Motion
- S3B = Intense Grit
- S4A = Wild Controlled
- S4B = Wild Maximum
- S5 = return to clean anchors

## Permanent Safety Principle

Load anchors remain permanent.

Capture features may be added later, but capture does not replace validated anchors.

Validated anchors remain the safety net.
