# Manual Hardware Validation Checklist

This is the exact, repeatable checklist for validating the RytmRandomizer
against a real Elektron Analog Rytm MK2. The automated WS-R end-to-end suite
(`tests/e2e/`) drives the same canonical operator-command flow against the
`MockMidiSender` on every CI run, so the suite already proves the *logic* is
correct. This checklist is the final confirmation that the **hardware path**
(`--arm`) behaves identically to what the mock recorded.

Run this whenever the project explicitly enters a hardware-validation session
or before a release candidate. It is **not** a gate on the automated suite; the
suite proves the mock-recorded logic, while this checklist confirms that the
real `--arm` path produces the expected behavior on the device.

## Prerequisites

- An Elektron Analog Rytm MK2 (firmware OS 1.61+ recommended).
- A USB-MIDI connection from the host to the Rytm.
- The Rytm powered on, set to a clean kit you do not mind being mutated, and
  no external MIDI program-change traffic running.
- A working install of this repository:
  ```
  pip install -e ".[dev]"
  ```
- Confirm the entry point resolves:
  ```
  rytm-randomizer --help
  ```
- Keep monitor volume moderate, especially for `S3B` and `S4B`.
- Start from a kit/pattern you can safely overwrite or restore.
- If possible, keep a phone or text editor nearby for notes; do not diagnose
  while the sequence is running.

## Pre-flight dry run

Before powering the hardware path, run the same command surface against the
mock sender:

```
rytm-randomizer --dry-run
```

Enter the canonical flow below and confirm the shell exits cleanly. This does
not open a MIDI port or send MIDI; it only confirms that the local entry point,
prompt flow, and command handling are ready for the hardware session.

For the guarded Pads 5-12 channel smoke path, run:

```
rytm-randomizer --dry-run --twelve-pad-smoke
```

Confirm the report says `Pads tested: 5-12` and `Messages sent: 48`.

For the guarded Analog Four Track 1-4 channel smoke path, run:

```
rytm-randomizer --dry-run --analog-four-smoke
rytm-randomizer --dry-run --analog-four-track-smoke 1
rytm-randomizer --dry-run --analog-four-track-filter-smoke 1
```

Confirm the report says `Tracks tested: 1-4` and `Messages sent: 12`.
For the one-track command, confirm the report says `Track tested: 1` and
`Messages sent: 3`.

## Canonical operator-command flow

These ten commands mirror the V1.34 baseline operator flow and the
centerpiece `tests/e2e/test_canonical_validation_flow.py` test:

```
SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> 1 -> Z -> Q
```

## Checklist

### 1. Identify the MIDI port

- [ ] Run `rytm-randomizer --arm`.
- [ ] The tool prints the available MIDI output ports.
- [ ] Note the index of the Analog Rytm output port. If multiple Rytm-related
      entries appear, choose the one labeled as the device output (not the
      input / control port).
- [ ] Enter the chosen index at the prompt. Confirm the next line reads
      `Opening MIDI output: <your port>`.

### 2. Entry flow

- [ ] At the target-pad prompt, enter `1` (Pad 1 / BD slot).
- [ ] Confirm the printout reads `Targeting Pad 1 / MIDI Channel 1`.
- [ ] At the profile prompt, enter `1` (My BD Hard / machine CC15 value 0,
      the primary default).
- [ ] Confirm the Rytm switches the active machine to My BD Hard. The
      tool prints `Switching Rytm machine to My BD Hard:` and the Rytm's
      Pad 1 machine LED reflects the change.

### 3. Drive the canonical flow

Enter each command in order; after each, sanity-check the device:

- [ ] `SCN` -- the scene/preset menu prints. No MIDI is sent to the Rytm.
- [ ] `GM` -- the global four-pad mutation menu prints. No MIDI is sent.
- [ ] `S1A` -- "Rolling Light" scene runs. The Rytm's four pads first jump
      to anchor values (auto-load), then mutate softly. Audible change on
      Pads 2-4; Pad 1 stays grounded.
- [ ] `S3A` -- "Intense Motion" scene runs. Pads 2-4 push further; Pad 3
      carries the most motion.
- [ ] `S3B` -- "Intense Grit" scene runs. Grit-forward push, kick still
      controlled.
- [ ] `S4B` -- "Wild Maximum" scene runs. The widest documented push;
      every pad should change clearly but the kick foundation stays
      recognizable.
- [ ] `S5` -- "Back to Clean" scene runs. **All four pads return to the
      validated anchor state.** This is the critical safety behavior:
      listen for every pad snapping back to its baseline.
- [ ] `1` -- bare depth digit at the main Command prompt. **The tool
      prints the guardrail message and sends NO MIDI** -- confirm the
      Rytm does not change. The console output should include
      `No MIDI was sent.`
- [ ] `Z` -- "return group to anchors". Same audible behavior as `S5`:
      every pad returns to anchor.
- [ ] `Q` -- quit. The tool prints `Exiting.` and returns to the shell
      prompt cleanly. **No exception, no stack trace.**

### 4. Confirm clean exit

- [ ] The MIDI port closes silently (no errors in the console).
- [ ] The Rytm holds the anchor state it ended on (since the last command
      was an anchor-return).
- [ ] Re-running `rytm-randomizer --arm` and immediately quitting with
      `Q` exits cleanly too.

### 5. Cross-check against the automated suite

- [ ] On the same machine that just passed the hardware run, run:
      ```
      pytest tests/e2e/ -v
      ```
- [ ] All E2E tests pass. The automated suite's canonical-flow test
      asserts the **same** ten-command sequence against the
      `MockMidiSender`-recorded golden file. A green E2E suite plus a
      green hardware run is the full validation gate.

### 6. Optional guarded Pads 5-12 smoke test

Run this only on a copied/disposable kit or pattern you can restore:

```
rytm-randomizer --arm --twelve-pad-smoke
```

- [ ] Select the Analog Rytm output port, not Analog Four.
- [ ] Confirm the report starts with
      `RytmRandomizer Twelve-Pad Hardware Smoke Report`.
- [ ] Confirm the report says `Mode: arm`, `Pads tested: 5-12`, and
      `Messages sent: 48`.
- [ ] Listen for Pads 5, 6, 7, 8, 9, 10, 11, and 12 responding as the tool
      moves Pan CC10 and Filter Frequency CC74.
- [ ] Confirm no A4 port was selected, no machine/engine cycling occurred,
      and no SysEx was requested or written.
- [ ] Do not save the kit afterward unless you intentionally want the final
      centered Pan/Filter values.

### 7. Optional guarded Analog Four smoke test

Run this only with the Analog Four connected, audible, and on a copied or
restorable pattern/kit:

```
rytm-randomizer --arm --analog-four-smoke
```

Or test one track at a time:

```
rytm-randomizer --arm --analog-four-track-smoke 1
rytm-randomizer --arm --analog-four-track-smoke 2
rytm-randomizer --arm --analog-four-track-smoke 3
rytm-randomizer --arm --analog-four-track-smoke 4
```

To test the next cautious parameter group, run Filter 1 Frequency on one
track at a time:

```
rytm-randomizer --arm --analog-four-track-filter-smoke 1
rytm-randomizer --arm --analog-four-track-filter-smoke 2
rytm-randomizer --arm --analog-four-track-filter-smoke 3
rytm-randomizer --arm --analog-four-track-filter-smoke 4
```

- [ ] Select the Analog Four output port, not Analog Rytm.
- [ ] Confirm the report starts with
      `RytmRandomizer Analog Four Hardware Smoke Report` for the all-track
      command or `RytmRandomizer Analog Four Track Smoke Report` for the
      one-track pan command or
      `RytmRandomizer Analog Four Track Filter Smoke Report` for the
      one-track filter command.
- [ ] Confirm the report says `Mode: arm` and either `Tracks tested: 1-4` /
      `Messages sent: 12` or `Track tested: <n>` / `Messages sent: 3`.
- [ ] Listen for Tracks 1, 2, 3, and 4 panning left/right, then returning to
      center.
- [ ] For the filter command, listen for the selected track moving darker /
      open, then returning to open. The final value is `CC18 -> 127`, not a
      captured original patch value.
- [ ] Confirm no Rytm port was selected, no filter/level/pitch movement
      occurred during pan smoke, no resonance/level/pitch movement occurred
      during filter smoke, no engine cycling occurred, and no SysEx was
      requested or written.
- [ ] Do not save the kit afterward unless you intentionally want the final
      centered Pan or open Filter 1 Frequency values.

## First-session notes template

### First validated V1.34 alpha pass

```text
Date: 2026-05-15
Branch / commit: modularize-v1.34 / local working tree
Rytm OS version: not recorded
MIDI port selected: 1 = Elektron Analog Rytm MKII 1
Kit / pattern used: operator test kit/pattern

Pre-flight --dry-run:
- pass / fail: pass
- notes: fresh wheel installed cleanly in a temp venv; canonical command flow
  exited cleanly with MockMidiSender capturing 511 messages.

Hardware canonical flow:
- port opened cleanly: yes
- target pad/profile selected cleanly: target pad yes; initial SCN typed at
  the profile prompt was safely rejected as Invalid profile with no MIDI.
- SCN no MIDI: yes, when entered at the main Command prompt
- GM no MIDI: yes
- S1A expected soft mutation: yes, audible
- S3A expected stronger motion: yes, audible
- S3B expected grit, volume safe: yes, audible
- S4B expected widest push, volume safe: yes, audible
- S5 returned all pads to anchors: yes
- bare 1 sent no MIDI: yes
- Z returned all pads to anchors: yes
- Q exited cleanly: yes

Unexpected behavior:
- No hardware fault observed. Operator-flow note: typing a command at the
  startup profile prompt is safe but mildly confusing; later UX polish should
  make the profile step clearer.

Audio notes / musical reaction:
- Scene mutations were heard on the Analog Rytm, and S5/Z audibly returned
  the kit to the validated clean anchors.

Decision:
- pass

Optional Pads 5-12 smoke:
- dry-run report pass / fail: not run in first session
- hardware smoke pass / fail: not run in first session
- pads 5-12 responded: not recorded in first session
- notes:

Optional Analog Four smoke:
- dry-run report pass / fail: not run in first session
- hardware smoke pass / fail: not run in first session
- tracks 1-4 responded: not recorded in first session
- notes:
```

Use this short template for future real-machine passes:

```text
Date:
Branch / commit:
Rytm OS version:
MIDI port selected:
Kit / pattern used:

Pre-flight --dry-run:
- pass / fail:
- notes:

Hardware canonical flow:
- port opened cleanly:
- target pad/profile selected cleanly:
- SCN no MIDI:
- GM no MIDI:
- S1A expected soft mutation:
- S3A expected stronger motion:
- S3B expected grit, volume safe:
- S4B expected widest push, volume safe:
- S5 returned all pads to anchors:
- bare 1 sent no MIDI:
- Z returned all pads to anchors:
- Q exited cleanly:

Unexpected behavior:

Audio notes / musical reaction:

Decision:
- pass / needs investigation / stop hardware testing

Optional Pads 5-12 smoke:
- dry-run report pass / fail:
- hardware smoke pass / fail:
- pads 5-12 responded:
- notes:

Optional Analog Four smoke:
- dry-run report pass / fail:
- hardware smoke pass / fail:
- tracks 1-4 responded:
- notes:
```

## What to do if a step fails

- **Scene does not audibly change the Rytm**: confirm the MIDI cable, the
  Rytm's MIDI channel routing (Pad 1 = ch 1, Pad 2 = ch 2, etc.), and
  that no external sequencer is overriding values on the same CCs.
- **Bare-depth `1` sent MIDI**: this is a regression. The automated
  `test_bare_main_prompt_depth_digit_emits_no_midi[1]` test would also
  have failed; capture the console output and open an issue.
- **`S5`/`Z` did not return to anchors**: this is a regression. The
  automated `test_s5_returns_all_four_pads_to_anchors` and
  `test_z_returns_all_four_pads_to_anchors` tests guard this; capture
  the console output and open an issue.
- **`Q` raises an exception**: capture the stack trace; the interactive
  shell catches `EOFError` / `KeyboardInterrupt` but other exceptions
  should never happen.

## Why this exists

The Analog Rytm cannot be driven from CI. The WS-R E2E suite proves the
randomizer's MIDI message stream is identical between runs and matches the
committed golden file, but only a human at the device can confirm those
messages actually translate into the audible behavior the V1.34 baseline
documents. This checklist is the bridge.
