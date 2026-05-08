# L PZ Passive Metadata Expansion Plan Review

## 1. Purpose

Review and accept `Docs/V134_L_PZ_PASSIVE_METADATA_EXPANSION_PLAN.md` as the
current planning checkpoint for a future passive metadata-only expansion of:

- `L` / select isolated single-pad mutation target, default Pad 3
- `PZ` / return selected isolated pad to anchor only

This is a documentation-only review gate.

This document does not add metadata.

This document does not implement commands.

This document does not add tests.

This document does not update fixtures.

This document does not wire commands into CLI, mock mapping, active execution,
dispatch, MIDI, ports, selected-pad runtime state, anchor return execution, or
hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- ac71857 Add L PZ passive metadata expansion plan

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- `L` and `PZ` passive metadata expansion plan created
- `L` and `PZ` passive metadata expansion plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/V134_L_PZ_PASSIVE_METADATA_EXPANSION_PLAN.md` is accepted as the current
planning checkpoint for a future metadata-only expansion.

Accepted future target commands:

- `L` / select isolated single-pad mutation target, default Pad 3
- `PZ` / return selected isolated pad to anchor only

Accepted future implementation concept:

- add a passive `ISOLATED_PAD_UTILITY_COMMANDS` dictionary
- add `L` and `PZ` as scaffold-only metadata
- merge `ISOLATED_PAD_UTILITY_COMMANDS` into `COMMANDS`
- expose the commands only through existing passive registry, lookup, preview,
  list, search, inspect, and report surfaces
- update existing tests and fixtures only as needed for passive metadata
  visibility

This review does not authorize direct implementation by itself.

Implementation still requires a separate explicit request.

## 4. Accepted Future Metadata Shape

Accepted future metadata shape:

```python
ISOLATED_PAD_UTILITY_COMMANDS = {
    "L": {
        "type": "selection",
        "scope": "isolated_pad_target",
        "sends_midi": False,
        "label": "select isolated single-pad mutation target, default Pad 3",
        "default_pad": 3,
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PZ": {
        "type": "anchor_return",
        "scope": "selected_isolated_pad",
        "sends_midi": False,
        "label": "return selected isolated pad to anchor only",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Accepted future merge point:

```python
    **ISOLATED_PAD_UTILITY_COMMANDS,
```

The planned commands remain metadata-only and non-executable.

## 5. Accepted Future Files

Accepted future implementation files:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

Possible future fixture update if explicitly needed:

- `tests/fixtures/cli_search_commands_known_expected.txt`

Closeout script update is not expected because the relevant tests are already
included in closeout.

## 6. Accepted Future Expected Output Changes

Accepted future passive command count:

- current: 89
- after future implementation: 91

Accepted future captured V1.34 operator entries modeled as passive command
metadata:

- current: 86
- after future implementation: 88

Accepted future captured V1.34 operator entries still not modeled as passive
command metadata:

- current: 20
- after future implementation: 18

Accepted future passive registry report command count:

- current: `commands: 89`
- after future implementation: `commands: 91`

Accepted future passive CLI list additions:

- `- L: select isolated single-pad mutation target, default Pad 3`
- `- PZ: return selected isolated pad to anchor only`

No new top-level CLI command should be added.

## 7. Safety Boundaries

This review confirms:

- no command metadata changes
- no tests changed
- no fixtures changed
- no runtime code changes
- no CLI wiring changes
- no package metadata changes
- no dependency selection
- no `mido`
- no real MIDI dependency
- no real port discovery
- no real port listing
- no real port opening
- no MIDI sending
- no active CLI command
- no execute-command
- no send-command
- no hardware-test
- no dispatch
- no command execution
- no scene execution
- no selected-pad runtime state mutation
- no isolated-pad mutation execution
- no active anchor return execution
- no hardware behavior
- no hardware detection
- no SysEx
- no GUI/capture
- no Analog Four support
- no Pads 5-12 support
- no machine/profile expansion
- no profile `"4"` implementation
- no hardware validation
- no hardware-on authorization

`rytm_hybrid_randomizer_v134.py` remains untouched.

Analog Rytm MKII remains off.

Analog Four MKII remains off.

## 8. Preconditions Before Future Implementation

Before implementing this plan:

- clean Git status
- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- this review gate is committed
- implementation is explicitly requested
- only `L` and `PZ` are added
- metadata remains scaffold-only
- tests remain passive
- fixtures are updated only for deterministic passive output
- no selected-pad runtime state mutation is added
- no active anchor return execution is added
- no real MIDI dependency is added
- no ports are opened
- hardware remains off

## 9. Safe Next Branches

Safe next branches:

- pause at this accepted plan review checkpoint
- implement the tiny passive metadata-only `L` and `PZ` slice after explicit
  approval
- create another docs-only progress checkpoint
- keep metadata expansion frozen and continue project documentation

Unsafe next moves without separate approval:

- adding more than `L` and `PZ`
- adding isolated-pad mutation metadata
- adding profile-switch metadata
- adding legacy mutation metadata
- adding active CLI behavior
- opening ports
- sending MIDI
- turning on hardware

## 10. Decision

`Docs/V134_L_PZ_PASSIVE_METADATA_EXPANSION_PLAN.md` is accepted for planning.

The accepted future metadata target is exactly:

- `L`
- `PZ`

No implementation is added by this slice.

Hardware remains off.

## 11. Next Recommended Task

If continuing, implement the tiny passive metadata-only `L` and `PZ` slice
exactly as described in the accepted plan.

That implementation must remain passive/scaffold-only and must not add
selected-pad runtime state mutation, active anchor return execution, active
behavior, real MIDI, ports, package metadata, or hardware requirements.
