# Manual Hardware Validation Checklist

This is the exact, repeatable checklist for validating the RytmRandomizer
against a real Elektron Analog Rytm MK2. The automated WS-R end-to-end suite
(`tests/e2e/`) drives the same canonical operator-command flow against the
`MockMidiSender` on every CI run, so the suite already proves the *logic* is
correct. This checklist is the final confirmation that the **hardware path**
(`--arm`) behaves identically to what the mock recorded.

Run this whenever it is convenient after merging to `main`. It is **not** a
gate on the WS-R workstream itself; the automated suite is. The
`.github/workflows/release.yml` notes this checklist as a recommended
pre-release step.

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

## Dual-Machine Strategy Redo Manual Validation

These checks are manual only. Do not add them to CI.

1. Run `python -m rytm_randomizer.cli dual-machine-target-report rytm`.
2. Confirm the report lists only `analog_rytm_mk2`.
3. Run `python -m rytm_randomizer.cli dual-machine-target-report a4`.
4. Confirm the report lists only `analog_four_mk2`.
5. Run `python -m rytm_randomizer.cli dual-machine-target-report both`.
6. Confirm both devices are listed.
7. Do not run armed hardware sends until the A4 readiness report says the plan is ready.

## Live-Show Passive Preflight

These checks are manual only. They are safe to run before a live rehearsal because
no MIDI is sent, no port is opened, and no hardware is mutated.

1. Run a passive stage-routing report against the saved kit banks you plan to use:
   ```
   python -m rytm_randomizer.cli style-performance-arc-stage-routing-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8
   ```
2. Run the passive stage rehearsal state report for the same saved kit banks:
   ```
   python -m rytm_randomizer.cli style-performance-arc-stage-rehearsal-state-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8
   ```
3. Run the passive live set cockpit report for the same saved kit banks:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-set-cockpit-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8
   ```
4. Run the passive live show export packet for the same saved kit banks:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-show-export-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8
   ```
5. Run the passive live transition timeline for the same saved kit banks:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-transition-timeline-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --events --limit 8
   ```
6. Run the passive live command deck for the cue you want to rehearse:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-command-deck-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --events --limit 8
   ```
7. Run the passive live state packet for the cue you want a future GUI to render:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-state-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --events --limit 8
   ```
8. Run the passive live analyzer target packet before any future analyzer compare:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-analyzer-targets-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3
   ```
9. Run the passive live GUI/audio-analyzer readiness bundle before any future GUI or analyzer compare:
   ```
   python -m rytm_randomizer.cli style-performance-arc-live-gui-analyzer-readiness-report --description "Jeff Mills Oscar Mulero Birmingham pressure" --rytm "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --analog-four "G:\ANALOG FOUR\KITS\ANALOGFOURKITS1.syx" --cue 1 --lookahead 2 --matches 3
   ```
10. Confirm the reports print `Live set card:`, `Route cards:`, `Stage rehearsal summary:`, `Machine states:`, `Cue states:`, `Cockpit summary:`, `Machine panels:`, `Cue cockpit cards:`, `Show export summary:`, `Machine handoff manifest:`, `Cue launch script:`, `Transition timeline summary:`, `Transition cards:`, `Command deck summary:`, `Now cue:`, `Live state summary:`, `Current GUI state:`, `Machine state panels:`, `Live analyzer handoff summary:`, `Live analyzer target packet summary:`, and `GUI/audio-analyzer readiness bundle summary:`.
11. Confirm each cue lists saved-kit slots/fingerprints, planned pads/tracks,
   Rytm mock rows, A4 deferred/candidate rows, blockers, and recovery actions.
12. Confirm rehearsal/cockpit/export/timeline/deck/state/analyzer target/readiness packets mark each cue as `go`, `rehearse`, or `do-not-arm` where applicable.
13. Treat the current validated Rytm live flow as:
   ```
   SCN -> GM -> S1A -> S3A -> S3B -> S4B -> S5 -> Z -> Q
   ```
13. Keep volume moderate before `S3B` and `S4B`.
14. If the set gets too hot, use `S5`, then `Z`, then `Q`.
15. Remember that the passive reports are route/rehearsal/cockpit/export/state/analyzer cards only. Armed runtime
   mutation remains the validated four-pad Rytm surface until a later runtime
   slice promotes more live sends.

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
