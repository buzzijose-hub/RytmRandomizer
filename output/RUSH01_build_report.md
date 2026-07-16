# RUSH01 Build Report

Build date: 2026-07-15

## Outcome

| Device | Result | Generated SysEx | Manifest |
| --- | --- | --- | --- |
| Analog Rytm MKII | **BLOCKED** | Not created | Not created |
| Analog Four MKII | **BLOCKED** | Not created | Not created |

Both devices have unresolved critical mappings. Per the build policy, no
partial or misleading kit was generated. See
`output/RUSH01_mapping_gaps.md` for exact gaps and required evidence.

## Input Verification

All four required inputs exist and both YAML documents parse successfully.
Firmware remains `UNVERIFIED_FROM_DEVICE`; the approved exact-target-unit
reference dump is the compatibility anchor.

| Device | Reference | Bytes | SHA-256 | Framing | MIDI data bytes |
| --- | --- | ---: | --- | --- | --- |
| Analog Rytm MKII | `reference/RYTM_Test1_Init_Kit.syx` | 2998 | `8bda94d6d5031e038c8d810789301f35242ed539338a0399548869a34e1dc4dd` | One complete `F0...F7` frame | All `<= 0x7F` |
| Analog Four MKII | `reference/A4_Test1_Init_Kit.syx` | 2770 | `50c753f3a2acd73ca77e2930e9b9658ea62bbe51f7cb9f7644e6f8ff2689cc5e` | One complete `F0...F7` frame | All `<= 0x7F` |

The source references were read only and were not overwritten.

## Reference Round Trips

| Device | Header bytes | Packed bytes | Decoded object bytes | Stored checksum | Stored length | Decode/encode result |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Analog Rytm MKII | 9 | 2983 | 2610 | 10997 | 2988 | **PASS**, byte-identical |
| Analog Four MKII | 4 | 2760 | 2415 | 9215 | 2760 | **PASS**, byte-identical |

Verified integrity rules:

- Rytm checksum: `sum(packed) & 0x3fff`
- Rytm stored length: `len(packed) + 5`
- A4 checksum: `sum(packed[8:]) & 0x3fff`
- A4 stored length: `len(packed)`

The encoder accepts a validated decoded frame rather than a blank object. It
preserves the complete reference header and decoded object, repacks all object
bytes, and recalculates checksum and length.

## Semantic Audit

- All Rytm machine enum name/ID pairs agree with the repository machine
  catalog, and every requested machine is legal on its selected pad.
- All Rytm Filter Mode name/ID pairs agree with the established table:
  LP2=`0`, Bandpass=`2`, HP1=`3`, HP2=`4`.
- No supplied enum conflict was silently accepted.
- Rytm critical verification is incomplete because machine writes and level
  fields remain locked/unmapped, several source surfaces are documented-only,
  required selectors are numeric-only, and CB Metallic `PW1/PW2` are unmapped.
- A4 critical verification is incomplete because the requested saved-kit
  field locations and typed conversions are not promoted. Three filter fields
  have candidate-only calibration evidence, which is insufficient for the
  arbitrary targets in this specification.

Semantic verification against a generated kit is therefore **not applicable**:
neither device passed the pre-generation critical mapping gate.

## Unknown and Reserved Byte Preservation

- Reference decode/encode changed zero bytes for both devices: **PASS**.
- A codec test patches one known decoded Rytm kit-name byte and verifies that
  every other decoded byte and the complete reference header remain identical:
  **PASS**.
- Generated-kit unknown-byte comparison is not applicable because no device
  output was emitted.

## Changed-Byte Diff

Reference round trips:

- Analog Rytm MKII: no changed bytes.
- Analog Four MKII: no changed bytes.

Generated semantic diff: none; generation stopped before mutation because of
critical mapping gaps.

## Unsupported Noncritical Fields

- Rytm per-track `sound_name`
- A4 per-track `sound_name`
- Both devices' cosmetic `design_role` labels

Kit-name mappings are known, but no names were patched into a blocked partial
kit. Rytm sample levels were also preserved because the catalog marks Sample
Level `locked_default`; details are in the mapping-gap report.

## Output Files

Created:

- `output/RUSH01_build_report.md`
- `output/RUSH01_mapping_gaps.md`

Intentionally not created:

- `output/RUSH01_RYTM.syx`
- `output/RUSH01_A4.syx`
- `output/RUSH01_RYTM_manifest.json`
- `output/RUSH01_A4_manifest.json`

There are no generated output SHA-256 values because no `.syx` passed the
critical mapping gate.

## Test Evidence

All commands used the repository virtual environment and opened no MIDI port.

| Verification | Command | Result |
| --- | --- | --- |
| Focused codec, reference, decoder, calibration, catalog, and data tests | `.venv\\Scripts\\python.exe -m pytest tests/test_snapshot_envelope.py tests/test_reference_kit_round_trip.py tests/test_devices_strategies_analog_four_snapshot_decoder.py tests/test_devices_strategies_snapshot_decoder.py tests/test_analog_four_sysex_calibration.py tests/test_analog_rytm_midi_catalog.py tests/test_data_layer.py -n 0 -q` | **139 passed**, 0 failed |
| Touched codec branch coverage | `.venv\\Scripts\\python.exe -m pytest tests/test_snapshot_envelope.py tests/test_reference_kit_round_trip.py -n 0 --cov=rytm_randomizer.snapshot.envelope --cov=rytm_randomizer.devices.strategies.elektron_kit_codecs --cov-branch --cov-report=term-missing --cov-fail-under=100 -q` | **60 passed**, 100% branch coverage, 0 failed |
| Architecture gate | `.venv\\Scripts\\python.exe -m pytest tests/architecture/ -q` | **663 passed**, 0 failed, 1 pre-existing warn-only duplicate-`main` warning |
| Full repository suite | `.venv\\Scripts\\python.exe -m pytest` | **6141 passed**, 3 skipped, 0 failed, 34 warnings |
| Ruff | `.venv\\Scripts\\python.exe -m ruff check .` | Passed |
| Black | `.venv\\Scripts\\python.exe -m black --check --target-version=py311 .` | 685 files unchanged |
| isort | `.venv\\Scripts\\python.exe -m isort --profile black --check-only .` | Passed; 6 files skipped by repository configuration |

The focused tests assert both approved references are byte-identical after
decode/encode, validate framing and 7-bit legality, and verify stored length
and checksum formulas. A positively mapped Rytm kit-name field patch converts
the semantic name `RUSH01` to fixed-width ASCII, decodes it back identically,
is stable after a second encode, and proves that only the expected packed-name
bytes plus recalculated checksum bytes differ; every other decoded byte and
the complete header remain identical. Requested critical-field semantic round
trips, generated-file stability, generated changed-byte allowlists, typed
signed conversions, and generated-kit warning checks are **not applicable**:
neither device passed the pre-mutation critical mapping gate, and no output kit
was created to test.

No standalone type checker is configured in `pyproject.toml` or `Justfile`;
the local environment also reports `No module named pyright`. Ruff and the
architecture type-hygiene gates passed.

## Hardware Safety

- No MIDI device was accessed.
- No MIDI port was opened.
- No SysEx message was sent.
- No reference dump was modified.
