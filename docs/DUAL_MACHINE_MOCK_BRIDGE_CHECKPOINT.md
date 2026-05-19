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

## Current Behavior

The Rytm side reads an existing saved `.syx` kit bank or whole-project dump,
decodes the selected kit slot, and plans bounded changes from captured values.
It does not load anchors.

The Analog Four side can either use a safe starter profile or decode an
existing saved A4 kit bank / whole-project dump into saved-offset candidate
events. These saved-offset events are still marked `candidate_unverified`
until the exact A4 parameter mapping is promoted from candidate offsets to
validated named CC mappings.

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

The best next technical slice is to promote selected Analog Four saved-offset
candidates into validated named parameter mappings through controlled hardware
tests, then let the guarded sender emit those mapped A4 snapshot changes.
