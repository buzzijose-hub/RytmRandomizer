# Isolated Pad Mutation Passive Metadata Expansion Plan Review

## 1. Purpose

Review and accept
`Docs/V134_ISOLATED_PAD_MUTATION_PASSIVE_METADATA_EXPANSION_PLAN.md` as the
current planning checkpoint for a future passive metadata-only expansion of:

- `PM` / mutate selected isolated pad only using its group default zone/depth
- `PS` / mutate selected isolated pad SRC only, choose depth
- `PF` / mutate selected isolated pad Filter only, choose depth
- `PA` / mutate selected isolated pad Amp only, choose depth
- `PL` / mutate selected isolated pad LFO only, choose depth
- `PO` / mutate selected isolated pad Morph only, choose depth
- `PB` / mutate selected isolated pad Body only, choose depth
- `PG` / mutate selected isolated pad Grit only, choose depth

This is a documentation-only review gate.

This document does not add metadata.

This document does not implement commands.

This document does not add tests.

This document does not update fixtures.

This document does not wire commands into CLI, mock mapping, active execution,
dispatch, MIDI, ports, selected-pad runtime state, isolated-pad mutation
execution, depth prompt execution, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- modularize-v1.34

Current HEAD before this slice:

- 6e3a19c Add isolated pad mutation metadata expansion plan

Current phase:

- Passive/Mock Foundation Phase
- V1.34 operator command surface captured
- passive registry gap review accepted
- `T`, `C`, and `Q` implemented as passive scaffold-only metadata
- `B`, `E`, `W`, and `U` implemented as passive scaffold-only metadata
- `L` and `PZ` implemented as passive scaffold-only metadata
- isolated-pad mutation passive metadata expansion plan created
- isolated-pad mutation passive metadata expansion plan now being reviewed

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Review Decision

`Docs/V134_ISOLATED_PAD_MUTATION_PASSIVE_METADATA_EXPANSION_PLAN.md` is
accepted as the current planning checkpoint for a future metadata-only
expansion.

Accepted future target commands:

- `PM` / mutate selected isolated pad only using its group default zone/depth
- `PS` / mutate selected isolated pad SRC only, choose depth
- `PF` / mutate selected isolated pad Filter only, choose depth
- `PA` / mutate selected isolated pad Amp only, choose depth
- `PL` / mutate selected isolated pad LFO only, choose depth
- `PO` / mutate selected isolated pad Morph only, choose depth
- `PB` / mutate selected isolated pad Body only, choose depth
- `PG` / mutate selected isolated pad Grit only, choose depth

Accepted future implementation concept:

- add a passive `ISOLATED_PAD_MUTATION_COMMANDS` dictionary
- add all eight commands as scaffold-only metadata
- merge `ISOLATED_PAD_MUTATION_COMMANDS` into `COMMANDS`
- expose the commands only through existing passive registry, lookup, preview,
  list, search, inspect, and report surfaces
- update existing tests and fixtures only as needed for passive metadata
  visibility

This review does not authorize broad active behavior.

Implementation is authorized only by the current approved work packet and must
remain exactly within the accepted passive metadata-only scope.

## 4. Accepted Future Metadata Shape

Accepted future metadata shape:

```python
ISOLATED_PAD_MUTATION_COMMANDS = {
    "PM": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "full",
        "uses_group_default_zone_depth": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad only using its group default zone/depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PS": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "src",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad SRC only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PF": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "filter",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Filter only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PA": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "amp",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Amp only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PL": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "lfo",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad LFO only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PO": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "morph",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Morph only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PB": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "body",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Body only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
    "PG": {
        "type": "mutation",
        "scope": "selected_isolated_pad",
        "command_family": "isolated_pad_mutation",
        "mutation_area": "grit",
        "requires_depth_selection": True,
        "sends_midi": False,
        "label": "mutate selected isolated pad Grit only, choose depth",
        "executable": False,
        "v134_reference_command": True,
        "scaffold_only": True,
    },
}
```

Accepted future merge point:

```python
    **ISOLATED_PAD_MUTATION_COMMANDS,
```

The planned commands remain metadata-only and non-executable.

## 5. Accepted Future Files

Accepted future implementation files:

- `rytm_randomizer/commands.py`
- `tests/test_scaffold.py`
- `tests/test_command_lookup.py`
- `tests/fixtures/cli_list_commands_expected.txt`
- `tests/fixtures/registry_report_expected.txt`

No `tests/test_cli.py` change is expected unless implementation adds a new
explicit assertion around the existing passive list output.

No search fixture update is expected because the current deterministic
`search-commands` fixture uses the `guarded` query, which is not affected by
these labels.

Closeout script update is not expected because the relevant tests are already
included in closeout.

## 6. Accepted Future Expected Output Changes

Accepted future passive command count:

- current: 91
- after future implementation: 99

Accepted future captured V1.34 operator entries modeled as passive command
metadata:

- current: 88
- after future implementation: 96

Accepted future captured V1.34 operator entries still not modeled as passive
command metadata:

- current: 18
- after future implementation: 10

Accepted future passive registry report command count:

- current: `commands: 91`
- after future implementation: `commands: 99`

Accepted future passive CLI list additions:

- `- PM: mutate selected isolated pad only using its group default zone/depth`
- `- PS: mutate selected isolated pad SRC only, choose depth`
- `- PF: mutate selected isolated pad Filter only, choose depth`
- `- PA: mutate selected isolated pad Amp only, choose depth`
- `- PL: mutate selected isolated pad LFO only, choose depth`
- `- PO: mutate selected isolated pad Morph only, choose depth`
- `- PB: mutate selected isolated pad Body only, choose depth`
- `- PG: mutate selected isolated pad Grit only, choose depth`

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
- no depth prompt execution
- no anchor return execution
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
- implementation remains inside the approved work packet
- only `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG` are added
- metadata remains scaffold-only
- tests remain passive
- fixtures are updated only for deterministic passive output
- no selected-pad runtime state mutation is added
- no isolated-pad mutation execution is added
- no depth prompt execution is added
- no real MIDI dependency is added
- no ports are opened
- hardware remains off

## 9. Safe Next Branches

Safe next branches:

- pause at this accepted plan review checkpoint
- implement the tiny passive metadata-only isolated-pad mutation slice inside
  the current approved work packet
- create another docs-only progress checkpoint
- keep metadata expansion frozen and continue project documentation

Unsafe next moves without separate approval:

- adding more than `PM`, `PS`, `PF`, `PA`, `PL`, `PO`, `PB`, and `PG`
- adding profile-switch metadata
- adding legacy mutation metadata
- adding generic current-profile page mutation metadata
- adding active CLI behavior
- opening ports
- sending MIDI
- turning on hardware

## 10. Decision

`Docs/V134_ISOLATED_PAD_MUTATION_PASSIVE_METADATA_EXPANSION_PLAN.md` is
accepted for planning.

The accepted future metadata target is exactly:

- `PM`
- `PS`
- `PF`
- `PA`
- `PL`
- `PO`
- `PB`
- `PG`

No implementation is added by this slice.

Hardware remains off.

## 11. Next Recommended Task

If continuing, implement the tiny passive metadata-only isolated-pad mutation
slice exactly as described in the accepted plan.

That implementation must remain passive/scaffold-only and must not add
selected-pad runtime state mutation, isolated-pad mutation execution, depth
prompt execution, active behavior, real MIDI, ports, package metadata, or
hardware requirements.
