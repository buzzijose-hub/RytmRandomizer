# RUSH01 Saved-Kit SysEx Calibration Report

## Objective

The final products remain offline Elektron KIT SysEx files:

- `output/RUSH01_RYTM.syx`
- `output/RUSH01_A4.syx`

Neither file is generated in this phase because both devices still have unresolved
critical saved-kit mappings. The device-assisted MIDI compiler is retained only as
semantic enumeration and calibration support.

## Readiness

| Device | Critical | Mapped | Preserve | Capture required | Candidate only | Unresolved | Writer ready |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| Analog Rytm MKII | 312 | 185 | 1 | 123 | 3 | 126 | False |
| Analog Four MKII | 244 | 0 | 4 | 228 | 12 | 240 | False |

## Reference Round Trips

| Device | Reference | Bytes | SHA-256 | Header | Packed | Unpacked | Result |
| --- | --- | ---: | --- | ---: | ---: | ---: | --- |
| Analog Rytm MKII | `reference/RYTM_Test1_Init_Kit.syx` | 2998 | `8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd` | 9 | 2983 | 2610 | **PASS, byte-identical** |
| Analog Four MKII | `reference/A4_Test1_Init_Kit.syx` | 2770 | `50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e` | 4 | 2760 | 2415 | **PASS, byte-identical** |

Both codecs start from the approved reference frame, preserve the complete header and
unknown object bytes, and recalculate packing, checksum, and encoded length. No blank
or invented kit object is used.

## Current Evidence

- Rytm supplied differential dumps: `0`.
- A4 supplied differential dumps: `0`.
- New mappings promoted by this run: `0`.
- Existing A4 candidate calibration fixtures are serialized for Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency; they remain writer-blocking.
- The Rytm `+162` sound-record layout and A4 `+350` unpacked / `+400` packed track strides are candidate inputs for unresolved fields, not automatic promotions.

## Gap Report Reconciliation

The workbench reads `output/RUSH01_mapping_gaps.md` and compiles current semantic paths
from the corrected YAML specifications. Stale gap aliases are retained as audit data but
are not reintroduced into the capture plan.

- Rytm superseded paths: `tracks.BD.synth.WAV`, `tracks.BT.synth.SNP`, `tracks.CB.synth.PW1`, `tracks.CB.synth.PW2`, `tracks.CH.synth.RST`, `tracks.CY.synth.TYP`
- A4 superseded paths: none

This excludes the obsolete `SNP`, `PW1`, and `PW2` rows from current Rytm work while
keeping the corrected typed `Snap Type: preserve_reference` request visible.

## Existing Components To Call Directly

- `rytm_randomizer.midi_io.send_cc` and `send_nrpn`: canonical V1.34 mutation primitives.
- `rytm_randomizer.senders.midi_event_plan.send_cc_nrpn_event_plan`: canonical ordered CC/NRPN plan sender.
- `rytm_randomizer.app --arm --validate-one-cc`: existing one-CC Rytm operator command.
- `rytm_randomizer.app --arm --a4-send-param` and `--a4-send-nrpn-param`: existing one-parameter A4 commands.
- `rytm_randomizer.mido_provider.MidoMidiPortProvider.capture_sysex_messages`: current raw SysEx receiver.
- `rytm_randomizer.app._capture_rytm_snapshot_shell_anchor_from_live_input`: current-kit receive/decode wrapper used by the snapshot shell.
- `rytm_randomizer.snapshot.sysex_file.extract_sysex_payloads`: complete-frame extraction.
- `ANALOG_RYTM_KIT_CODEC` and `ANALOG_FOUR_KIT_CODEC`: saved-kit validation, unpacking, packing, checksum, and length.

## Duplicate Device-Assisted Code Classification

Retain the following as calibration support; do not extend it into the final delivery path:

- `rytm_randomizer/senders/rush01_midi_transport.py`: `open_exact_output` and byte-plan replay overlap the established provider/app port boundary and `midi_io.send_cc` sender path.
- `tools/rush01_midi_apply.py`: duplicates a general apply/list-port command surface already represented by the V1.34 app handlers.
- `rytm_randomizer/style_analysis/rush01_midi_compiler.py`: useful for semantic ordering, catalog validation, typed transport values, and one-parameter capture planning only.
- `tools/rush01_midi_learn.py` and `state/midi_observation.py`: useful for input-side calibration observations only.

No module above is called by the offline saved-kit writer planned for final delivery.

## Promotion Rules

- One changed parameter per dump; unexplained changed bytes block promotion.
- Multiple observations are mandatory for signed, bipolar, enum, boolean, and high-resolution fields.
- A track stride is never promoted from one track; a second distinct track is mandatory.
- Existing candidate offsets remain candidate-only until source dumps and writer round-trip fixtures are present.
- Every promoted mapping must have a committed unit-test fixture.
- Final `.syx` generation remains disabled until unresolved critical count is zero for that device.

## Hardware Safety

- No MIDI backend was imported or opened while generating this report.
- No MIDI port was opened.
- No MIDI data or SysEx was transmitted.
- No Elektron device was accessed.
- No `--apply` command was run.
