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

## Current Behavior

The Rytm side reads an existing saved `.syx` kit bank or whole-project dump,
decodes the selected kit slot, and plans bounded changes from captured values.
It does not load anchors.

The Analog Four side does not decode A4 SysEx yet. It uses the first safe
starter plan:

- Track 1: bass / low tonal anchor
- Track 2: stab / sequence pressure
- Track 3: pad / drone / atmosphere
- Track 4: FX / noise / transition

Each A4 track contributes:

- Filter 1 Frequency CC18
- Amp Pan CC10

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

The best next technical slice is to build the Analog Four saved snapshot
decoder. That would let the A4 side graduate from safe-starter planning to the
same captured-value mutation approach now working for the Rytm.
