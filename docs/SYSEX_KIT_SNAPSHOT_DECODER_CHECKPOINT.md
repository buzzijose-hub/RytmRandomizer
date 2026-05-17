# SysEx Kit Snapshot Decoder Checkpoint

Date: 2026-05-17

## Purpose

`sysex-kit-snapshot-report <path> --slot <1-128>` is the first passive decoder
that turns a saved Analog Rytm kit record into a 12-pad snapshot inventory. It
is the next bridge toward Live Snapshot mode: the software can now carry a
saved kit's twelve pad sound blocks as a baseline before editable parameter
maps are applied to runtime mutation.

## What It Proves

- Rytm kit records are Elektron 7-bit packed after the 10-byte SysEx header.
- Unpacking the payload exposes the kit name and twelve fixed pad sound blocks.
- Each pad block is 162 decoded bytes.
- The first pad block starts at decoded payload offset 58.
- The underlying saved track/sound struct starts at decoded payload offset 46.
- Machine IDs decode for all twelve pads, including high-bit saved values such
  as raw 128 -> BD Hard and raw 154 -> BD Sharp.
- Existing V1.34 machine maps now decode saved CC baselines for BD Hard,
  BD Classic, BD Sharp, BD Acoustic, BD FM, BD Plastic, BD Silky, SD Hard,
  SD Classic, SD FM, and SY Raw.
- Remaining identified Rytm machines decode through a generic saved CC-slot
  baseline: `SRC Slot 1-8`, filter, amp, and LFO values. This gives all twelve
  pads a snapshot baseline without claiming engine-specific musical names for
  machines that still need manual mapping.
- All twelve pad blocks are present in Jose's saved Rytm kit dumps.
- Jose's current `PROJECTRYTM01.syx` slot 1 and `ANALOGRYTMKITS2.syx` slot 16
  both report `Mapped parameter pads: 12 / 12`.
- Per-pad block hashes differ across kit slots, so the snapshot sees real saved
  kit differences rather than only generic slot names.

## Current Commands

Whole-project dump:

```powershell
python -m rytm_randomizer.cli sysex-kit-snapshot-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1
```

Performance kit bank:

```powershell
python -m rytm_randomizer.cli sysex-kit-snapshot-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16
```

Both report:

- device: Analog Rytm MKII
- record length: 2998 bytes
- decoded payload: 2613 bytes
- pad snapshots: 12 / 12
- decode status: `raw_sound_blocks_with_partial_parameter_map` when at least
  one captured machine is currently mapped
- parameter map: `partial_known_and_generic_machine_maps` when captured pads
  include both specific engine maps and generic saved-slot baselines
- mapped parameter preview lines such as `SRC Tune`, `FLT Frequency`,
  `AMP Decay`, `AMP Pan`, `SRC Slot 1`, and SY Raw LFO values

## Boundary

This is passive/read-only. It does not request dumps, receive live SysEx, open
ports, send MIDI, mutate hardware, restore a kit, or write SysEx.

The next completed slice turns this decoded 12-pad baseline into a passive
mutation plan that starts from the captured values. See
`Docs/SNAPSHOT_MUTATION_PLAN_CHECKPOINT.md`. Engine-specific naming can
continue incrementally for SY Dual VCO, CP/BT/XT/CH/OH, CY/CB, HH Basic,
HH Lab, and UT Noise, but all identified pads already have usable saved CC-slot
baselines.
