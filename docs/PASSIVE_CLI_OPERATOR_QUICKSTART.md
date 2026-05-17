# Passive CLI Operator Quickstart

## Purpose

This quickstart is for using the RytmRandomizer **passive CLI** safely. The
passive CLI is the read-only inspection / preview surface exposed by
`rytm_randomizer.cli`; it never opens a MIDI port or sends MIDI.

For the active interactive runtime (real MIDI or mock sender) use the
`rytm-randomizer` entry point with `--arm` or `--dry-run`. See `README.md`.
The active entry point also supports guarded Rytm and Analog Four smoke
modifiers described below; they are not part of the passive CLI.

The CLI is passive/read-only. It is for inspection, previewing, reporting,
listing, searching existing package metadata, and read-only analysis of saved
SysEx files only.

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

Analog Rytm and Analog Four should remain off during passive CLI inspection.

## Active 12-Pad Smoke Test

The active app can run a narrow Pads 5-12 channel smoke test:

```powershell
rytm-randomizer --dry-run --twelve-pad-smoke
rytm-randomizer --arm --twelve-pad-smoke
```

`--dry-run --twelve-pad-smoke` records the stream through `MockMidiSender`.
`--arm --twelve-pad-smoke` asks for a MIDI output port, sends the same stream
to the selected Rytm port, prints a summary, and exits.

The smoke stream sends only:

- Pan CC10 left/right/center
- Filter Frequency CC74 close/open/center
- Pads 5-12 only, mapped to MIDI channels 5-12 / wire channels 4-11

This is channel validation, not full Pads 5-12 runtime mutation. It does not
cycle machines, request SysEx, write SysEx, touch Analog Four, or run scenes.

## Active Analog Four Smoke Test

The active app can run a narrow Analog Four Track 1-4 channel smoke test:

```powershell
rytm-randomizer --dry-run --analog-four-smoke
rytm-randomizer --arm --analog-four-smoke
rytm-randomizer --dry-run --analog-four-track-smoke 1
rytm-randomizer --arm --analog-four-track-smoke 1
rytm-randomizer --dry-run --analog-four-track-filter-smoke 1
rytm-randomizer --arm --analog-four-track-filter-smoke 1
```

`--dry-run --analog-four-smoke` records the stream through `MockMidiSender`.
`--arm --analog-four-smoke` asks for a MIDI output port, sends the same stream
to the selected Analog Four port, prints a summary, and exits.
`--analog-four-track-smoke <1-4>` runs the same pan-only test for one selected
track, which is useful during headphone validation.
`--analog-four-track-filter-smoke <1-4>` runs the next cautious parameter
group: Filter 1 Frequency CC18 on one selected track only.

The pan smoke stream sends only:

- Amp Pan CC10 left/right/center
- Analog Four Tracks 1-4 only, mapped to MIDI channels 1-4 / wire channels 0-3
- Pan returns to 64 on each track

The filter smoke stream sends only:

- Filter 1 Frequency CC18 low/open/open-return
- one Analog Four track only, mapped to its matching MIDI channel / wire channel
- Filter 1 Frequency returns to 127/open so the test does not leave the track
  muffled

This is channel validation, not Analog Four runtime mutation. It does not
touch Rytm, resonance, levels, pitch, engines, NRPN, CV, SysEx, snapshots,
style kits, or cross-device scenes.

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

## SysEx Kit Bank Report

Analyze an already-saved Analog Rytm kit-bank `.syx` file:

```powershell
python -m rytm_randomizer.cli sysex-kit-bank-report "G:\ANALOG RYTM\KITS\AM9KITS.syx"
```

This command reads the file from disk and reports passive record metadata:
record count, record length, visible kit names, slot offsets, and blank/default
candidate slots. It does not request a dump from hardware, decode editable
parameters, send MIDI, open ports, or write SysEx.

## SysEx Project Report

Analyze an already-saved whole-project `.syx` dump:

```powershell
python -m rytm_randomizer.cli sysex-project-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx"
python -m rytm_randomizer.cli sysex-project-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx"
```

This command reads the file from disk and reports passive record groups for
kits, sounds, patterns, song/project slots, global-like records, and project
settings. Jose's current Rytm and Analog Four whole-project dumps each report
405 complete SysEx records with 128 kits, 128 sounds, 128 patterns, 16
song/project slots, 4 global slots, and 1 project/settings record. It does not
request a dump from hardware, receive live SysEx, decode editable parameters,
send MIDI, open ports, mutate hardware, or write SysEx.

## SysEx Kit Snapshot Report

Decode one saved Rytm kit slot into a passive 12-pad snapshot:

```powershell
python -m rytm_randomizer.cli sysex-kit-snapshot-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1
python -m rytm_randomizer.cli sysex-kit-snapshot-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16
```

This command reads either a saved Rytm kit bank or whole-project dump, selects
one kit slot, unpacks the saved Elektron 7-bit payload, and reports the 12 pad
sound blocks as a snapshot baseline. It reports kit name, slot, decoded payload
length, pad sound names, machine IDs, raw block byte count, per-pad hashes, and
saved parameter baselines for currently mapped Rytm machines such as BD Hard,
BD Sharp, BD Plastic, and SY Raw. Other identified machines report generic
saved CC-slot baselines so every non-disabled captured pad can be carried into
future snapshot-derived mutation planning. This is still not mutation logic and
not a restore path.

The command does not request a dump from hardware, receive live SysEx, send
MIDI, open ports, mutate hardware, or write SysEx.

## Snapshot Mutation Plan Report

Plan passive mutation moves from a captured saved-kit baseline:

```powershell
python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report "G:\ANALOG RYTM\WHOLE PROJECT DUMP\PROJECTRYTM01.syx" --slot 1 --depth micro
python -m rytm_randomizer.cli sysex-snapshot-mutation-plan-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

This command decodes one saved Rytm kit snapshot, then proposes bounded,
deterministic CC changes from the captured parameter values. It is the passive
proof for Live Snapshot behavior: mutate from the kit that is loaded, not from
prebaked anchors. It does not send MIDI, open ports, load anchors, switch
machines, mutate hardware, or write SysEx.

## Rytm Controlled Diff Report

Compare a baseline Rytm kit export against a second export made after one controlled pad parameter change:

```powershell
python -m rytm_randomizer.cli rytm-controlled-diff-report "G:\ANALOG RYTM\MAPPING\RYTM_BASELINE.syx" "G:\ANALOG RYTM\MAPPING\RYTM_PAD1_FILTER_UP.syx" --slot 1 --pad 1 --limit 16
```

Scan all 12 pads in one passive comparison:

```powershell
python -m rytm_randomizer.cli rytm-controlled-diff-report "G:\ANALOG RYTM\MAPPING\RYTM_BASELINE.syx" "G:\ANALOG RYTM\MAPPING\RYTM_AFTER_ONE_CHANGE.syx" --slot 1 --all-pads --limit 8
```

Use this during 12-pad mapping sessions:

1. Export the baseline kit.
2. Change one known Rytm pad parameter by hand.
3. Export the same kit again.
4. Run this report to see which decoded saved parameter moved.

The single-pad form is best when you know the exact pad. The all-pad form is
best when you want the report to identify which pad changed. The output reports
mapped saved parameters only, using the current saved-kit decoder's known or
generic machine maps. It does not open MIDI ports, send MIDI, receive live
SysEx, write SysEx, switch machines, or mutate hardware.

## Dual-Machine Mock Bridge Report

Preview a coordinated passive Rytm + Analog Four mock stream:

```powershell
python -m rytm_randomizer.cli dual-machine-mock-bridge-report "G:\ANALOG RYTM\KITS\ANALOGRYTMKITS2.syx" --slot 16 --depth micro
```

This command combines the Rytm saved-kit snapshot mutation plan with the first
Analog Four Track 1-4 safe-starter plan. The Rytm side mutates from captured
saved-kit values. The Analog Four side uses only the currently validated safe
starter CCs: Track 1-4 Filter 1 Frequency CC18 and Amp Pan CC10.

It is the first passive checkpoint for the cross-device project. It does not
open either machine's MIDI port, send MIDI, request or receive SysEx, write
SysEx, switch Rytm machines, decode Analog Four snapshots, or mutate hardware.

## Essence Plan Report

Preview a 12-pad engine plan from manually supplied essence tags:

```powershell
python -m rytm_randomizer.cli essence-plan-report --tags metallic,bell,driving,repetition --discovery 0.35
```

Or derive those broad tags from a written reference description:

```powershell
python -m rytm_randomizer.cli essence-plan-report --description "metallic bell pressure driving repetition Detroit techno" --discovery 1.0
```

This command calls the passive Machine Catalog / Essence Matcher. It prints
pad roles and candidate engines, but it does not analyze audio files, copy
track identity, send MIDI, mutate hardware, or enable Pads 5-12 runtime
support. Higher discovery values may show future inventory engines that still
need manual mapping and hardware validation before mutation is allowed.

## Style Intent Report

Preview a 12-pad kit direction from broad genre or style language:

```powershell
python -m rytm_randomizer.cli style-intent-report --style "Birmingham dark techno"
python -m rytm_randomizer.cli style-intent-report --style "schranz" --discovery 0.82
```

This command is the prompt-based companion to the future audio analyzer. It
maps broad style intent into non-copying essence tags, suggests a Discovery
value, and prints the same passive 12-pad candidate plan used by
`essence-plan-report`. It does not analyze audio files, clone tracks, send
MIDI, open ports, mutate hardware, add Analog Four runtime support, or enable
Pads 5-12 runtime mutation.

## Twelve-Pad Mock Runtime Report

Build the first mock-only 12-pad runtime contract from style intent:

```powershell
python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style "Birmingham dark techno"
python -m rytm_randomizer.cli twelve-pad-mock-runtime-report --style "schranz" --discovery 0.82
```

This command turns a style prompt into 12 pad roles, mapped machine choices,
MIDI channel assignments, and inert mock CC messages. Pads are displayed as
MIDI channels 1-12 while the captured mock stream records wire channels 0-11,
matching the runtime's mido convention. Preferred future-only engines fall
back to currently mapped V1.34-safe candidates so the first 12-pad contract can
be inspected without pretending unmapped engines are hardware-ready.

This command does not open a MIDI port, send MIDI, require hardware, capture
SysEx, write SysEx, or mutate runtime/hardware state.

## Analog Four Reference Report

Inspect the first passive Analog Four MKII reference intake:

```powershell
python -m rytm_randomizer.cli analog-four-reference-report
```

This command prints the external reference source, license, update date,
parameter count, four planning track roles, starter CC/NRPN parameter groups,
and blocked next slices. It is for planning the future cross-device system:
Track 1 as bass/low tonal anchor, Track 2 as stab/sequence pressure, Track 3
as drone/pad atmosphere, and Track 4 as noise/FX transition.

This command does not add Analog Four runtime support, open an A4 port, send
MIDI, receive live SysEx, write SysEx, coordinate Rytm/A4 scenes, or mutate
hardware.

## Analog Four Kit Snapshot Report

Decode one saved Analog Four kit slot into a passive Track 1-4 inventory:

```powershell
python -m rytm_randomizer.cli analog-four-kit-snapshot-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --slot 1
```

This command reads an existing Analog Four kit bank or whole-project dump,
unpacks the saved kit payload, and reports the kit name plus four track blocks.
It intentionally marks saved parameter offsets as `saved_parameter_offsets_unmapped`
until a later mapper proves the saved kit layout.

It does not open MIDI ports, send MIDI, receive live SysEx, write SysEx, or
mutate hardware.

## Analog Four Offset Candidate Report

Scan saved Analog Four kit variations for unverified numeric offset candidates:

```powershell
python -m rytm_randomizer.cli analog-four-offset-candidate-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --track 1 --limit 12
```

Scan all four Analog Four tracks in one passive run:

```powershell
python -m rytm_randomizer.cli analog-four-offset-candidate-report "G:\ANALOG FOUR\WHOLE PROJECT DUMP\PROJECTANALOGFOUR01.syx" --all-tracks --limit 8
```

This command scans existing saved A4 kit records, extracts one Track 1-4 block
across all kits, and reports even-aligned CC-like words that vary across saved
kit variations. These are evidence points for future mapping only. The report
uses `candidate_unverified` and does not claim parameter names.

It does not open MIDI ports, send MIDI, receive live SysEx, write SysEx, name
parameters, or mutate hardware.

## Analog Four Controlled Diff Report

Compare a baseline Analog Four kit export against a second export made after one controlled parameter change:

```powershell
python -m rytm_randomizer.cli analog-four-controlled-diff-report "G:\ANALOG FOUR\MAPPING\A4_BASELINE.syx" "G:\ANALOG FOUR\MAPPING\A4_FILTER_FREQ_UP.syx" --slot 1 --track 1 --limit 16
```

Use this during mapping sessions:

1. Export the baseline kit.
2. Change one known A4 parameter by hand.
3. Export the same kit again.
4. Run this report to find the changed saved-value offset.

The output stays conservative: every changed offset is `candidate_unverified`,
and no parameter names are claimed until the same controlled change has been
confirmed.

It does not open MIDI ports, send MIDI, receive live SysEx, write SysEx, name
parameters, or mutate hardware.

## Essence Application Readiness Report

Check whether an essence plan is apply-ready under Safe Anchors or Live
Snapshot:

```powershell
python -m rytm_randomizer.cli essence-application-readiness-report --mode safe-anchors --tags metallic,bell,driving,repetition --discovery 0.35
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 1.0 --snapshot captured
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --description "metallic bell driving repetition Detroit techno" --discovery 0.35 --fixture am9-slot-01
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --style "schranz" --fixture am9-slot-01
python -m rytm_randomizer.cli essence-application-readiness-report --mode live-snapshot --style "Birmingham dark techno" --discovery 0.35 --snapshot captured
```

This command prints a per-pad gate: ready, blocked, or future-only. It makes
the current boundary visible. Safe Anchors is only four-pad runtime-ready
today, Live Snapshot requires a complete 12-pad snapshot, and future engines
remain blocked until manually mapped and validated. With `--style`, broad
style prompts use their Style Intent discovery hints unless `--discovery`
overrides them. The command does not capture kits, receive live SysEx, send
MIDI, mutate hardware, or enable Pads 5-12 runtime support. The
`--fixture am9-slot-01` option uses the passive AM9-inspired mock snapshot
inventory to show how unmapped captured machines would be blocked.

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
- analyze audio files
- request SysEx dumps
- apply decoded SysEx parameter maps to runtime mutation
- write SysEx
- write report files at runtime
- require hardware to be connected
- add GUI behavior
- add capture behavior
- add Analog Four runtime support
- add Pads 5-12 runtime mutation support
- expand the machine/profile universe

## Hardware Status

No hardware is required for the passive CLI.

During this phase:

- Analog Rytm should remain off unless you are explicitly running
  `rytm-randomizer --arm` or `rytm-randomizer --arm --twelve-pad-smoke`.
- Analog Four should remain off unless you are explicitly running
  `rytm-randomizer --arm --analog-four-smoke` or
  `rytm-randomizer --arm --analog-four-track-smoke <1-4>` or
  `rytm-randomizer --arm --analog-four-track-filter-smoke <1-4>`.
- No MIDI interface needs to be connected.

## Passive-To-Active Boundary

The `python -m rytm_randomizer.cli ...` surface remains passive/read-only. The
hardware-facing entry point is `rytm-randomizer --arm`, and the guarded 12-pad
smoke test is `rytm-randomizer --arm --twelve-pad-smoke`. The guarded Analog
Four channel smoke tests are `rytm-randomizer --arm --analog-four-smoke` and
`rytm-randomizer --arm --analog-four-track-smoke <1-4>`. The first A4
parameter smoke beyond pan is
`rytm-randomizer --arm --analog-four-track-filter-smoke <1-4>`.

Do not select the Analog Four port from Rytm commands. Do not select the Rytm
port from the Analog Four smoke command. Analog Four remains
reference-intake/mock-planning plus pan-only channel validation until it has a
separate approved runtime mutation plan.

## Closeout Checklist

After documentation or passive CLI-related changes, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git status --short
```

The V1.34 reference diff must remain empty.
