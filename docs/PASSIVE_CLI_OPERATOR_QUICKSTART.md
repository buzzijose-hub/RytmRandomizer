# Passive CLI Operator Quickstart

## Purpose

This quickstart is for using the current RytmRandomizer passive CLI safely
during the V1.34 modularization phase.

The CLI is passive/read-only. It is for inspection, previewing, reporting,
listing, and searching existing scaffold metadata only.

## Current Safe Baseline

Current safe baseline:

- branch: modularize-v1.34
- protected reference: `rytm_hybrid_randomizer_v134.py`
- passive CLI only
- no MIDI sending
- no MIDI port opening
- no command execution
- no hardware mutation
- no hardware required

Analog Rytm and Analog Four should remain off during this phase.

## How To Run The Passive CLI

Run commands from the repository root:

```powershell
python -m rytm_randomizer.cli --help
```

The help output describes the passive CLI commands and repeats the key safety
boundary: no MIDI sending, no port opening, no command execution, no hardware
mutation, and no hardware required.

## Report Command

Show the passive registry report:

```powershell
python -m rytm_randomizer.cli report
```

The report is generated from the existing passive registry report layer. It is
formatted for inspection and documentation only.

## List Commands

List current passive registry sections:

```powershell
python -m rytm_randomizer.cli list-commands
python -m rytm_randomizer.cli list-scenes
python -m rytm_randomizer.cli list-group-profiles
```

These commands list existing passive metadata keys and labels/names only. They
do not execute any listed command or scene.

## Inspect Commands

Inspect representative passive metadata entries:

```powershell
python -m rytm_randomizer.cli inspect-command J
python -m rytm_randomizer.cli inspect-scene S1A
python -m rytm_randomizer.cli inspect-group-profile 2
```

Inspection reads copied metadata from the passive registry surfaces. It does
not call handlers, dispatch commands, execute scenes, change machines, or send
MIDI.

## Preview Commands

Preview passive dry-run command metadata:

```powershell
python -m rytm_randomizer.cli preview-command J
python -m rytm_randomizer.cli preview-scene S1A
python -m rytm_randomizer.cli preview-group-profile 2
```

Preview-command uses the existing passive preview helper. Preview-scene uses
existing copied scene registry metadata. Preview-group-profile uses existing
copied group profile registry metadata. They clearly state that no MIDI would
be sent, no command or scene would execute, and no hardware would be mutated.

Unknown preview keys fail safely. For example:

```powershell
python -m rytm_randomizer.cli preview-command DOES_NOT_EXIST
python -m rytm_randomizer.cli preview-scene DOES_NOT_EXIST
python -m rytm_randomizer.cli preview-group-profile DOES_NOT_EXIST
```

Expected behavior is a passive not-found message such as:

```text
Command preview not found. No MIDI was sent. No command executed. No hardware was mutated.
Scene preview not found. No MIDI was sent. No scene executed. No command executed. No hardware was mutated.
Group profile preview not found. No MIDI was sent. No command executed. No hardware was mutated.
```

## Search Commands

Search existing passive metadata:

```powershell
python -m rytm_randomizer.cli search-commands BD
python -m rytm_randomizer.cli search-scenes Wild
python -m rytm_randomizer.cli search-group-profiles Hard
```

Search is case-insensitive and read-only. Search results are metadata matches,
not executable actions.

## Safe No-Match Behavior

No-match searches exit safely and do not touch hardware. For example:

```powershell
python -m rytm_randomizer.cli search-commands DOES_NOT_EXIST
```

Expected behavior is a passive no-match message such as:

```text
no matches found. No MIDI was sent. No command executed.
```

## What This CLI Does Not Do

The passive CLI does not:

- send MIDI
- open MIDI ports
- dispatch commands
- execute commands
- call handlers
- add handlers
- mutate runtime state
- mutate hardware state
- write SysEx
- write report files at runtime
- require hardware to be connected
- add GUI behavior
- add capture behavior
- add Analog Four support
- add Pads 5-12 support
- expand the machine/profile universe

## Hardware Status

No hardware is required for the passive CLI.

During this phase:

- Analog Rytm should remain off.
- Analog Four should remain off.
- No MIDI interface needs to be connected.

## Passive-To-Active Boundary

The modular package is currently passive/read-only. Hardware-facing execution
is not yet implemented; the validated `rytm_hybrid_randomizer_v134.py` monolith
remains the only tool that sends MIDI to hardware.

The current CLI remains passive/read-only. Do not turn on Analog Rytm or Analog
Four until the project explicitly enters a hardware-facing validation phase.

## Closeout Checklist

After documentation or passive CLI-related changes, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

The V1.34 reference diff must remain empty.
