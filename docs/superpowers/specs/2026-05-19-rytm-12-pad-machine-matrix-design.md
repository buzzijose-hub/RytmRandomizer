# Rytm 12-Pad Machine Matrix Design

Date: 2026-05-19

## Context

Jose confirmed real hardware response across all 12 Analog Rytm MK2 pads, and the current project has just absorbed the PR #43/#44/#45 governance and Device Strategy rules. The next safe milestone is a passive, testable source of truth for which Rytm machines are valid on each pad before runtime mutation expands beyond the V1.34 four-pad anchor layer.

This design uses the Analog Rytm MK2 OS 1.72 pad/machine table Jose attached:

- Pad 1 BD: BD machines, SY machines, SD machines, UT machines.
- Pad 2 SD: SD machines, SY machines, BD machines, UT machines.
- Pad 3 RS: RS machines, SY machines, BD machines, SD machines, CP machines, UT machines.
- Pad 4 CP: CP machines, SY machines, BD machines, SD machines, RS machines, UT machines.
- Pad 5 BT: BT Classic, UT machines.
- Pads 6-8 LT/MT/HT: XT Classic, UT machines.
- Pad 9 CH: CH machines, HH machines, OH machines, UT machines.
- Pad 10 OH: OH machines, HH machines, CH machines, UT machines.
- Pad 11 CY: CY machines, CB machines, UT machines.
- Pad 12 CB: CB machines, CY machines, UT machines.

## Goal

Add a passive Rytm 12-pad machine matrix that can answer, in code and in a CLI report, which engines each pad can legally host. This is the foundation for 12-pad runtime mutation, snapshot-based mutation, and later audio-analyzer or genre-tag kit design.

## Non-Goals

- No armed MIDI sends.
- No runtime mutation of pads 5-12 in this slice.
- No SysEx kit parsing or snapshot capture changes.
- No Analog Four changes.
- No V1.34 parity fixture regeneration.
- No changes to the four-pad scene command behavior.

## Recommended Approach

Use the existing data/report/CLI architecture:

1. Add a Rytm-specific fact table under `rytm_randomizer/data/`.
2. Add a passive report formatter under `rytm_randomizer/reports/`.
3. Wire one read-only CLI command through the existing passive CLI surface.
4. Update README/status docs so the new README freshness guard stays satisfied.

This is the lowest-risk path because it follows `docs/ARCHITECTURE.md` section 6 for a new fact table and passive report. It also avoids the earlier rejected pattern of creating `rytm_randomizer/essence/` or any new top-level device package.

## Architecture

### Data Layer

Create `rytm_randomizer/data/rytm_machine_catalog.py`.

It will define frozen dataclasses:

- `RytmMachineProfile`: stable machine key, label, family, CC15 value, support status, and tags for future selection.
- `RytmPadCapability`: pad number, track code, display label, and the allowed machine keys for that pad.

The module will expose immutable tuples/mappings such as:

- `RYTM_MACHINE_PROFILES`
- `RYTM_PAD_CAPABILITIES`
- `RYTM_MACHINE_PROFILES_BY_KEY`
- `RYTM_PAD_CAPABILITIES_BY_PAD`

It will also expose small pure helper functions:

- `get_rytm_machine_profile(key: str) -> RytmMachineProfile`
- `get_rytm_pad_capability(pad: int) -> RytmPadCapability`
- `allowed_machine_profiles_for_pad(pad: int) -> tuple[RytmMachineProfile, ...]`
- `is_machine_allowed_on_pad(pad: int, machine_key: str) -> bool`

All data stays passive and stdlib-only. It must not import `mido`, `devices`, `shell`, `engines`, or any runtime sender.

### Report Layer

Create `rytm_randomizer/reports/rytm_machine_matrix.py`.

The report will summarize:

- Total pads: 12.
- Total concrete machine profiles: 33.
- Total allowed pad-machine slots: 116.
- Total CC15-selectable slots: 116.
- Pads 6-8 show XT Classic.
- Pad 10 is Open Hihat and does not show XT Classic.
- No pending/unknown machine values.

It will render as a passive report using the existing report formatter conventions, including a safety section that makes clear it opens no MIDI port and sends no MIDI.

### CLI Layer

Wire a new passive command:

```bash
python -m rytm_randomizer.cli rytm-12-pad-machine-matrix-report
```

The command only reads data and formats text. It must remain safe under the passive CLI safety tests.

### Documentation

Update:

- `README.md`: replace the stale "No Pads 5-12 expansion yet" safety line with a more precise statement: pads 5-12 have a passive machine matrix only; armed runtime mutation still remains gated.
- `docs/STATUS.md`: add a current-status note about the 12-pad machine matrix checkpoint.

## Machine Catalog

The catalog should include these 33 machine profiles and CC15 machine values:

| Key | Label | Family | CC15 |
| --- | --- | --- | --- |
| `bd_hard` | BD Hard | BD | 0 |
| `bd_classic` | BD Classic | BD | 1 |
| `bd_fm` | BD FM | BD | 13 |
| `bd_plastic` | BD Plastic | BD | 21 |
| `bd_silky` | BD Silky | BD | 22 |
| `bd_sharp` | BD Sharp | BD | 26 |
| `bd_acoustic` | BD Acoustic | BD | 30 |
| `sd_hard` | SD Hard | SD | 2 |
| `sd_classic` | SD Classic | SD | 3 |
| `sd_fm` | SD FM | SD | 14 |
| `sd_natural` | SD Natural | SD | 23 |
| `sd_acoustic` | SD Acoustic | SD | 31 |
| `dual_vco` | SY Dual VCO | SY | 28 |
| `sy_chip` | SY Chip | SY | 29 |
| `sy_raw` | SY Raw | SY | 32 |
| `rs_hard` | RS Hard | RS | 4 |
| `rs_classic` | RS Classic | RS | 5 |
| `cp_classic` | CP Classic | CP | 6 |
| `bt_classic` | BT Classic | BT | 7 |
| `xt_classic` | XT Classic | XT | 8 |
| `ch_classic` | CH Classic | CH | 9 |
| `ch_metallic` | CH Metallic | CH | 17 |
| `oh_classic` | OH Classic | OH | 10 |
| `oh_metallic` | OH Metallic | OH | 18 |
| `hh_basic` | HH Basic | HH | 24 |
| `hh_lab` | HH Lab | HH | 33 |
| `cy_classic` | CY Classic | CY | 11 |
| `cy_metallic` | CY Metallic | CY | 19 |
| `cy_ride` | CY Ride | CY | 25 |
| `cb_classic` | CB Classic | CB | 12 |
| `cb_metallic` | CB Metallic | CB | 20 |
| `ut_noise` | UT Noise | UT | 15 |
| `ut_impulse` | UT Impulse | UT | 16 |

The implementation plan should still include one explicit check against the OS 1.72 manual before code is committed, but production code will not carry `None` or placeholder machine values.

## Validation Rules

Tests must assert:

- Exactly 12 pad capabilities exist.
- Exactly 33 machine profiles exist.
- Exactly 116 legal pad-machine slots exist.
- Every machine key referenced by a pad exists in the machine registry.
- Every machine has an integer CC15 value in 0-127.
- Pad 10 is `OH / Open Hihat`.
- Pad 10 allows OH/HH/CH/UT families and rejects `xt_classic`.
- Pads 6, 7, and 8 allow `xt_classic`.
- Pad 9 allows CH/HH/OH/UT families.
- Pad 11 allows CY/CB/UT families.
- Pad 12 allows CB/CY/UT families.
- The report contains the safety/passive wording and the key totals.
- The CLI command returns the report without importing or opening real MIDI.

## Error Handling

Unknown machine keys and pad numbers should raise `KeyError` with specific messages. The report command itself should not accept pad-specific arguments in this slice, so command-line misuse follows the existing CLI unknown/usage behavior.

## Test Plan

The implementation will use TDD:

1. Add failing data-layer tests for pad/machine cardinality and the Pad 10/Open Hat correction.
2. Add the smallest catalog implementation to pass.
3. Add failing report tests for totals and safety text.
4. Add the report renderer.
5. Add failing CLI tests for command dispatch/help text.
6. Wire the CLI command.
7. Run architecture and fast/full verification.

Target commands:

```bash
python -m pytest tests/test_data_rytm_machine_catalog.py -n 0
python -m pytest tests/test_rytm_machine_matrix_report.py -n 0
python -m pytest tests/test_cli*.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

## Acceptance Criteria

- A reviewer can inspect the passive report and confirm the OS 1.72 12-pad machine eligibility map.
- The implementation does not touch hardware.
- The implementation does not mutate V1.34 four-pad scenes.
- The branch contains no new top-level package under `rytm_randomizer/`.
- The new code lives in `data/`, `reports/`, `cli.py`/help surfaces, and docs/tests only.
- README and status docs describe the new state accurately.
- The next milestone can use this matrix to choose legal machines for snapshot-mode and 12-pad runtime mutation.
