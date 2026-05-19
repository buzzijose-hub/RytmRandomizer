# Dual-Machine Mock Bridge Checkpoint

Date: 2026-05-17

## What This Milestone Proves

The project now has a passive combined Rytm + Analog Four planning bridge.
It lets us inspect one coordinated mock message stream for both machines
without opening MIDI ports or sending hardware data.

This is the first software checkpoint where the project is clearly no longer
Rytm-only:

- Analog Rytm MKII uses saved-kit snapshot mutation planning.
- Analog Four MKII contributes a conservative Track 1-4 starter plan from
  hardware-validated CCs.
- The combined output is captured through `MockMidiSender` only.

## Operator Command

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

Target-aware variants:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro --target rytm
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro --target analog-four
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro --target both
```

A4-only saved-snapshot variant:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report --target analog-four --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1
```

Verified A4 saved-offset manifest variant:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro --analog-four-path "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --analog-four-slot 1 --analog-four-mapping-manifest "G:\ANALOG FOUR\MAPPING\a4-verified-mappings.json"
```

## Current Behavior

The Rytm side reads an existing saved `.syx` kit bank or whole-project dump,
decodes the selected kit slot, and plans bounded changes from captured values.
It does not load anchors.

The Analog Four side can either use a safe starter profile or decode an
existing saved A4 kit bank / whole-project dump into saved-offset candidate
events. These saved-offset events are still marked `candidate_unverified`
until the exact A4 parameter mapping is promoted from candidate offsets to
validated named CC mappings.

The promotion path is now wired: when a controlled-diff-proven A4 saved offset
is supplied to the snapshot planner, the bridge turns that one offset into a
named mapped CC mock event. Any remaining unverified saved offsets stay
blocked, so guarded sending only becomes ready when the selected target plan
contains mapped CC events and no candidate events.

The same ready manifest gate now reaches the dual-machine preview, readiness,
active-send plan, and guarded-send dry-run commands through
`--analog-four-mapping-manifest <path>`. Duplicate or empty manifests fail
closed; matching A4 saved offsets become named CC mock events, and unmatched
offsets remain `candidate_unverified`.

The first safe starter plan is:

- Track 1: bass / low tonal anchor
- Track 2: stab / sequence pressure
- Track 3: pad / drone / atmosphere
- Track 4: FX / noise / transition

Each A4 track contributes:

- Filter 1 Frequency CC18
- Amp Pan CC10

The bridge now honors Live Snapshot target scope:

- `--target rytm` emits only Rytm mock messages and marks Analog Four untouched.
- `--target analog-four` emits only Analog Four mock messages and marks Rytm
  untouched. With an A4 saved snapshot path, this target no longer requires any
  Rytm file or Rytm slot.
- `--target both` is the default combined behavior.

## Safety Boundary

This report is passive/read-only:

- mock sender only
- no MIDI sending
- no MIDI receive
- no port opening
- no command execution
- no hardware mutation
- no live SysEx receive
- no SysEx writes
- no hardware required

## Next Best Slice

The best next technical slice is to run controlled hardware/export tests for
one low-risk Analog Four parameter at a time, add the proven entries to the
local manifest, and use the dual-machine readiness and guarded dry-run reports
to prove when a selected A4 snapshot is fully mapped.
