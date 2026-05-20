# Rytm Snapshot Pad Compatibility Design

Date: 2026-05-20

## Context

PRs #46, #47, and #48 are now merged into `modularize-v1.34`. The new base has the Rytm 12-pad machine matrix in `rytm_randomizer/data/rytm_machine_catalog.py`, a passive matrix report in `rytm_randomizer/reports/rytm_machine_matrix.py`, and the Device Strategy boundary for Rytm and Analog Four.

The old `codex/snapshot-pad-compatibility` branch contains useful snapshot-pad validation ideas, but it diverges from the new base and conflicts across CLI, docs, devices, and dual-machine files. This milestone ports the idea, not the old branch shape.

## Goal

Add a passive, operator-facing Rytm snapshot-pad compatibility checkpoint. Given the current Rytm machine catalog and snapshot planner readiness, the project should be able to explain which of the 12 Rytm pads are ready for snapshot-based mutation, which are only machine-selectable today, and why blocked pads are blocked.

## Non-Goals

- No armed MIDI sends.
- No hardware snapshot capture.
- No continuous hardware tracking.
- No Analog Four snapshot behavior in this PR.
- No GUI work.
- No audio analyzer or genre-tag kit design.
- No V1.34 parity fixture regeneration.
- No changes to the existing four-pad scene/runtime behavior.

## Recommended Approach

Use the new base architecture:

1. Keep the existing Rytm machine matrix as the legal pad-machine source of truth.
2. Add a passive compatibility/reporting layer that summarizes snapshot readiness per pad.
3. Wire a read-only CLI report through the existing passive CLI command registry.
4. Preserve the Device Strategy boundary by leaving runtime planning and rendering untouched in this PR.

This produces a clean first PR after the governance reset. It also gives the next PR a precise contract for turning compatibility data into actual 12-pad snapshot mutation routing.

## Design

### Data Shape

Create a small immutable report model under the report layer, not a new top-level package. Each pad report should include:

- `pad`: 1-based pad number.
- `track_code`: Rytm track code such as `BD`, `OH`, or `CB`.
- `label`: operator-facing pad label.
- `allowed_machine_count`: number of legal machines from the matrix.
- `mutable_machine_count`: number of legal machines whose current support status is `mutable_v134`.
- `machine_selectable_count`: number of legal machines that can be selected but are not yet snapshot-mutable.
- `snapshot_ready`: `True` only when at least one legal machine on that pad is snapshot-mutable today.
- `readiness_reason`: short operator-facing sentence explaining the readiness state.

The report should derive all counts from `RYTM_PAD_CAPABILITIES` and `RYTM_MACHINE_PROFILES`. It must not duplicate machine lists or hardcode Pad 10 exceptions outside tests.

### Readiness Rule

For PR1, readiness is intentionally conservative:

- A pad is snapshot-ready when it has at least one legal machine profile with `support_status == "mutable_v134"`.
- A pad is blocked when all legal machines are currently `machine_selectable`.
- The report must distinguish "legal on the pad" from "safe to mutate from snapshot today".

This means Pads 1-4 should report ready because the V1.34-backed mutable profiles already exist there. Pads 5-12 may be partially or fully blocked depending on which legal machines have `mutable_v134` support through the current catalog.

### CLI

Add one passive command:

```powershell
python -m rytm_randomizer.cli rytm-snapshot-pad-compatibility-report
```

The command must:

- Open no MIDI port.
- Send no MIDI.
- Require no hardware.
- Accept no arguments in this PR.
- Print deterministic text suitable for fixture testing.

### Error Handling

This report has no user-supplied pad or machine argument, so runtime errors should only occur if internal data drifts. Data drift should fail loudly in tests, not be hidden from the operator.

The next PR may add pad-specific CLI options; if it does, it should reuse the clearer pad validation pattern from the old branch: non-integer pads say "Snapshot pad must be an integer", and out-of-range pads say "Snapshot pad must be between 1 and 12".

### Documentation

Update only docs affected by the new passive surface:

- `README.md` if the command becomes user-facing.
- `docs/STATUS.md` with a short checkpoint entry.
- CLI help fixture if the command appears in `--help`.

Avoid broad docs churn.

## Alternatives Considered

### Port the Old Branch Whole

Rejected. The old branch conflicts with the new base and predates the current Device Strategy and governance shape. A whole-branch merge would reintroduce stale architecture.

### Start with Analog Four

Rejected for this PR. Analog Four is already represented in the Device Strategy base, but Jose's immediate live-performance blocker is Rytm 12-pad snapshot readiness. Analog Four snapshot support should follow after the Rytm compatibility report is clean.

### Build Runtime Mutation Immediately

Rejected for this PR. Runtime mutation needs this compatibility contract first so the armed path can refuse unsafe pads with clear reasons.

## Test Plan

Use TDD with focused tests first:

```powershell
python -m pytest tests/test_rytm_snapshot_pad_compatibility_report.py -n 0
python -m pytest tests/test_cli.py -n 0
python -m pytest tests/test_real_midi_passive_cli_safety.py -n 0
python -m pytest tests/architecture/ -q
python -m pytest -m fast
python -m pytest
python -m ruff check .
python -m black --check --target-version=py311 .
python -m isort --profile black --check-only .
```

Acceptance checks:

- The report covers exactly 12 pads.
- Pad 10 is still `OH / Open Hihat`.
- The report says Pad 10 is not XT Classic territory.
- The report distinguishes legal machine selection from snapshot mutation readiness.
- The CLI command is passive and deterministic.
- Passive CLI safety tests still prove no real MIDI import, port opening, or hardware mutation.
- Architecture tests remain green.

## Follow-Up Sequence

1. Rytm snapshot-pad compatibility report.
2. Rytm snapshot mutation routing for all 12 pads, using the compatibility contract.
3. Analog Four snapshot foundation through `devices/analog_four.py` and `devices/strategies/`.
4. Later: audio analyzer and genre/tag kit design that choose engines using the same compatibility and Device Strategy boundaries.
