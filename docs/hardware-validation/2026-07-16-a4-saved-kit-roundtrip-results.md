# Analog Four Saved-Kit Round-Trip Hardware Validation Results

Date: 2026-07-16

## Purpose

Validate the narrowest generated Analog Four MKII saved-kit path: decode one
valid kit, mutate calibrated Filter2 Resonance bytes, rebuild Elektron 7-bit
packing plus checksum/length trailer, transfer the generated `.syx` file, and
confirm the front-panel values with the operator present.

This evidence validates Filter2 Resonance only. It does not validate other A4
parameters, direct MIDI sending, unattended transfers, patterns, projects, or
a complete patch-genome-to-kit compiler.

## Setup

- Target hardware: Elektron Analog Four MKII
- Disposable project: `Test 1`
- Received kit name: `KIT 1`
- Clean baseline file: `A4_Test1_Init_Kit.syx`
- Clean baseline SHA256:
  `50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e`
- Executable writer regression source: Filter2 Resonance `0`, SHA256
  `a8fbb0552b953815fc1f6358299116866b0d94002692933abccf83655023cc6b`
- Sanitized source/expected captures are committed under
  `tests/fixtures/analog_four_saved_kit/` for exact byte-level regression.
- Frame size: 2,770 bytes
- Packed payload size: 2,760 bytes
- Unpacked saved-kit body size: 2,415 bytes
- Transfer utility and A4 firmware version: not recorded during this studio pass
- Operator confirmation: Jose Buzzi, present for every receive and value check

## Results

| Generated file | SHA256 | Expected values | Hardware observation |
|---|---|---|---|
| `A4_CODEX_TEST_T1_Filter2Res_127_GENERATED.syx` | `5ebb386677aff324ef96d631e7888a9681caefbd976bdc2eac69b52a0fb0e26b` | T1 `127` | Received as `KIT 1`; T1 displayed `127`. Byte-identical to `A4_Test1_T1_Filter2Res_127_Kit.syx`. |
| `A4_CODEX_TEST_T1_Filter2Res_064_GENERATED.syx` | `2fee1aa93c98e0221dbe7bac296c51268360c5c61e11c8eea77fd091cbbd94f7` | T1 `64` | Received as `KIT 1`; T1 displayed novel value `64`. |
| `A4_CODEX_TEST_T1-4_Filter2Res_016_048_080_112_GENERATED.syx` | `0e88aa6f15fd49c36696d5b8e09bda18ce5eeb8562c1a44ce46683c6deef819b` | T1 `16`, T2 `48`, T3 `80`, T4 `112` | Received as `KIT 1`; all four tracks displayed the expected independent values. |

## Validated Layout

- Filter2 Resonance unpacked offsets: `145`, `495`, `845`, `1195`
- Unpacked track stride: `+350`
- Corresponding packed offsets: `170`, `570`, `970`, `1370`
- Packed track stride: `+400`
- Checksum: `sum(packed[8:]) & 0x3FFF`
- Trailer: 14-bit checksum followed by 14-bit packed length

## Outcome

Passed.

The reference-value file proved byte-for-byte reconstruction, the value-64
file proved synthesis beyond captured anchors, and the four-track file proved
that independent mutations survive one shared repack/checksum operation.

The same renderer is reachable through the registered local-file command:

```text
python -m rytm_randomizer.cli analog-four-saved-kit-export --source <kit.syx> --output <generated.syx> --filter2-resonance 1:16 --filter2-resonance 2:48 --filter2-resonance 3:80 --filter2-resonance 4:112 --json
```

This command writes a file only. Transfer to the A4 remains an explicit
operator action.

## Safety Boundary

- Generated files are written locally and never sent automatically.
- Existing output files are refused unless overwrite is explicitly enabled.
- The operator-facing exporter accepts only `hardware-write-validated` fields.
- Filter1 Frequency, Filter1 Resonance, and Filter2 Frequency remain
  candidate-only and blocked from normal export.
- Recovery is the operator's saved project/kit backup plus reloading the clean
  `Test 1` baseline; stop immediately on a wrong kit name, track, or value.

## Next Safe Step

Use this renderer as the exact transport target for one DNA parameter family
at a time. Promote another field only after the same reference, novel-value,
and cross-track evidence exists for that field.
