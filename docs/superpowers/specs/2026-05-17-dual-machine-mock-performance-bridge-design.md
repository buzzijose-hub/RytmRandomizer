# Dual-Machine Mock Performance Bridge Design

Date: 2026-05-17

## Goal

Build the first combined Rytm + Analog Four passive performance bridge. The
bridge should show one coordinated mock plan for both machines without opening
ports or sending MIDI:

- Analog Rytm MKII: use the decoded saved-kit snapshot and the existing
  captured-value mutation planner.
- Analog Four MKII: use a conservative four-track starter plan built only from
  parameters already proven through hardware smoke tests.
- Combined output: show exact mock CC messages for both devices, with separate
  device labels, MIDI channels, wire channels, controls, and safety notes.

This milestone is not Rytm-only. It acknowledges that both machines have
responded to hardware tests, while keeping their software maturity levels clear.

## Current State

The Rytm path is deeper:

- saved Rytm kits decode into 12-pad snapshots
- all identified Rytm pads have either specific parameter names or generic
  saved CC-slot baselines
- `sysex-snapshot-mutation-plan-report` can propose bounded captured-value
  changes from Jose's saved kits

The Analog Four path is earlier but real:

- Track 1-4 pan CC smoke tests have been implemented
- one-track Filter 1 Frequency CC18 smoke tests have been implemented
- Jose confirmed all four A4 tracks responded
- A4 saved SysEx snapshot decoding is not implemented yet

## Recommended Approach

Add a new passive module, tentatively `dual_machine_mock_bridge.py`, that
combines two subplans:

1. Rytm subplan
   - Input: saved Rytm `.syx` path, slot, and depth.
   - Source: `snapshot_mutation_planner.build_snapshot_mutation_plan_from_file`.
   - Output: one mock CC message per planned Rytm change.
   - Metadata: device `Analog Rytm MKII`, pad number, MIDI channel, wire channel,
     machine label, parameter name, captured value, planned value, delta.

2. Analog Four subplan
   - Input: no SysEx snapshot yet; use safe starter roles for Tracks 1-4.
   - Source: validated CCs only at first.
   - Track roles:
     - Track 1: bass / low tonal anchor
     - Track 2: stab / sequence pressure
     - Track 3: pad / drone / atmosphere
     - Track 4: FX / noise / transition
   - First safe controls:
     - Amp Pan CC10, centered around 64
     - Filter 1 Frequency CC18, conservative movement ending in a safe open-ish
       range
   - Metadata: device `Analog Four MKII`, track number, MIDI channel, wire
     channel, role label, parameter name, baseline type `safe_starter`, planned
     value.

3. Combined mock stream
   - Use `MockMidiSender` and `build_cc_message`.
   - Capture messages in deterministic order:
     1. all Rytm snapshot-derived planned changes
     2. all Analog Four safe-starter planned changes
   - Do not import `mido` or `rtmidi`.
   - Do not call the active app or hardware smoke runners.

## CLI Contract

Add a passive report command:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

The report should include:

- Rytm source file, slot, kit name, depth
- Rytm planned pads and planned changes
- A4 track count and starter message count
- combined mock message count
- per-device message preview
- clear maturity labels:
  - `Rytm source: saved-kit snapshot`
  - `A4 source: safe starter CC plan`
- safety:
  - passive/read-only
  - mock sender only
  - no MIDI sending
  - no port opening
  - no live SysEx receive
  - no SysEx writes
  - no hardware mutation

## Testing

Add tests before implementation:

- importing the new module is silent and does not import real MIDI libraries
- building a bridge from a synthetic Rytm kit produces Rytm mock messages from
  captured values, not anchors
- A4 contributes four tracks and only the safe-starter CCs
- combined `MockMidiSender` message count equals Rytm messages plus A4 messages
- CLI report reads a saved kit file and exits zero without hardware
- CLI help exposes the command as passive
- invalid depth and missing slot fail safely

## Boundaries

Do not add:

- real MIDI sending
- port selection
- A4 SysEx snapshot decoding
- A4 engine cycling
- A4 NRPN or CV mutation
- Rytm machine switching
- anchor loading
- cross-device armed mode
- GUI behavior

## Next Slice After This

After this bridge is green, the next useful slice is either:

1. turn the combined mock stream into a dry-run operator flow, or
2. start the Analog Four saved snapshot decoder so the A4 side can graduate
   from safe-starter planning to captured-value planning.
