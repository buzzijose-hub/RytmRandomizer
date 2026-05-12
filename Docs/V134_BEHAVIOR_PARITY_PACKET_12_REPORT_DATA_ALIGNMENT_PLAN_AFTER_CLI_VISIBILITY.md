# V1.34 Behavior Parity Packet 12 Report Data Alignment Plan After CLI Visibility

## 1. Purpose

Plan a tiny future passive report-data alignment update after accepted Packet 12
CLI visibility.

This is a documentation-only plan.

It does not implement report data alignment.

It adds no tests, fixture changes, CLI wiring, runtime execution, dispatch,
MIDI, ports, package metadata changes, active behavior, or hardware behavior.

## 2. Current Clean Baseline

Current branch:

- `modularize-v1.34`

Current HEAD before this planning slice:

- `c8e1b8d Add behavior parity next branch selection review after Packet 12 CLI visibility`

Current phase:

- Passive/Mock Foundation Phase
- behavior-parity implementation phase
- Packet 12 behavior-parity coverage report implemented and accepted
- Packet 12 behavior-parity report CLI visibility implemented and accepted
- report data alignment after CLI visibility now being planned

Hardware status:

- Analog Rytm MKII off
- Analog Four MKII off
- hardware not required

## 3. Accepted Upstream State

Accepted upstream review:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_PACKET_12_CLI_VISIBILITY_REVIEW.md`

Accepted upstream selection:

- `Docs/V134_BEHAVIOR_PARITY_NEXT_BRANCH_SELECTION_AFTER_PACKET_12_CLI_VISIBILITY.md`

Accepted upstream milestone:

- `c8e1b8d Add behavior parity next branch selection review after Packet 12 CLI visibility`

Accepted next planning target:

- docs-only Packet 12 report data alignment plan after CLI visibility

## 4. Current Report Data Observation

The current passive CLI command exists and is accepted:

```powershell
python -m rytm_randomizer.cli behavior-parity-report
```

The command prints only the existing formatted behavior-parity coverage report.

Current report data still says:

- `cli_visibility: absent`
- parked scope includes `Packet 12 CLI visibility`

That was correct before the CLI visibility implementation.

Now that CLI visibility is accepted, a tiny future alignment update should make
the report data reflect the current accepted state.

## 5. Selected Future Alignment

If this plan is reviewed and accepted, the future implementation should:

- change report boundary data from `cli_visibility: absent` to
  `cli_visibility: present`
- remove `Packet 12 CLI visibility` from parked scope
- keep `fourth runtime-adjacent candidate` parked
- keep `profile 4 mock mapper support` parked
- keep absent execution/MIDI/hardware behavior explicit
- keep the report passive, read-only, deterministic, and in-memory only
- keep the existing `behavior-parity-report` command passive/read-only

## 6. Future Files To Update

Future implementation should update only these files unless review finds a
specific reason to do otherwise:

- `rytm_randomizer/behavior_parity_coverage_report.py`
- `tests/test_behavior_parity_coverage_report.py`
- `tests/fixtures/cli_behavior_parity_report_expected.txt`

`tests/test_cli.py` should not need behavioral changes unless its fixture usage
requires a narrow assertion update.

`Scripts/closeout_check.ps1` should not need changes because both Passive CLI
and Behavior Parity Coverage Report tests are already in closeout.

## 7. Future TDD Plan

Future implementation should use a tiny RED/GREEN flow.

### RED Step 1: Update Report Tests First

Update `tests/test_behavior_parity_coverage_report.py` expectations so:

- `parked_scope` equals:
  - `fourth runtime-adjacent candidate`
  - `profile 4 mock mapper support`
- `cli_visibility` equals `present`
- `parked_scope_count` equals `2`
- formatted report no longer includes `- Packet 12 CLI visibility`
- formatted report includes `- cli_visibility: present`

Run:

```powershell
python -m pytest tests\test_behavior_parity_coverage_report.py -q
```

Expected RED result:

- failures proving the report data still says `cli_visibility: absent`
- failures proving parked scope still includes `Packet 12 CLI visibility`

### GREEN Step 2: Update Report Data Only

Update `rytm_randomizer/behavior_parity_coverage_report.py` only enough to:

- remove `Packet 12 CLI visibility` from `PARKED_SCOPE`
- set `REPORT_BOUNDARY["cli_visibility"]` to `present`

Run:

```powershell
python -m pytest tests\test_behavior_parity_coverage_report.py -q
```

Expected GREEN result:

- all Behavior Parity Coverage Report tests pass

### Fixture Step 3: Update Passive CLI Fixture

Update `tests/fixtures/cli_behavior_parity_report_expected.txt` so the passive
CLI fixture matches the aligned formatted report:

- remove `- Packet 12 CLI visibility`
- change `- cli_visibility: absent` to `- cli_visibility: present`

Run:

```powershell
python -m pytest tests\test_cli.py -q
```

Expected GREEN result:

- Passive CLI tests pass
- `behavior-parity-report` output remains deterministic

### Closeout Step 4: Run Full Verification

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\Scripts\closeout_check.ps1
git diff -- rytm_hybrid_randomizer_v134.py
git diff -- pyproject.toml requirements.txt setup.py setup.cfg
git status --short
```

Expected result:

- closeout passes
- V1.34 reference diff is empty
- package metadata diff is empty
- only the planned report/test/fixture files are changed before commit

## 8. Future Implementation Boundaries

Future implementation must not add:

- new CLI commands
- CLI execution wiring
- selected pad switching execution
- selected pad target state mutation
- selected pad anchor return execution
- current anchor return execution
- isolated pad mutation execution
- runtime mutation
- dispatch
- command execution
- scene execution
- MIDI
- ports
- package metadata changes
- active behavior
- hardware behavior
- fourth runtime-adjacent candidate
- profile `4` mock mapper support
- Analog Four support
- Pads 5-12 support
- SysEx
- GUI/capture

## 9. Why This Alignment Comes Before Expansion

This alignment should happen before more behavior-parity expansion because:

- the report is now visible to the user through the passive CLI
- visible reports should describe the accepted state accurately
- the update is tiny and low-risk
- it keeps parked scope meaningful
- it avoids mixing report cleanup with a future behavior packet
- it avoids prematurely selecting a fourth runtime-adjacent candidate
- it avoids profile `4` mock mapper expansion

## 10. Non-Goals

This plan does not authorize:

- implementation in this slice
- new tests in this slice
- fixture changes in this slice
- CLI command changes
- closeout script changes
- active behavior
- runtime execution
- MIDI implementation
- port opening
- hardware validation

## 11. Next Recommended Task

Review and accept this Packet 12 report data alignment plan.

After review, if accepted, perform the tiny TDD implementation described in
this plan.

Hardware remains off.

## 13. Review Status

This plan is reviewed and accepted by:

- `Docs/V134_BEHAVIOR_PARITY_PACKET_12_REPORT_DATA_ALIGNMENT_PLAN_AFTER_CLI_VISIBILITY_REVIEW.md`

The review accepts the next selected branch:

- tiny TDD Packet 12 report data alignment implementation

The review adds no report data implementation, tests, fixtures, CLI changes,
CLI execution wiring, dispatch, command execution, runtime execution, MIDI,
ports, package metadata changes, active behavior, or hardware behavior.

## 12. Decision

The future report data alignment target is planned.

No implementation in this slice.

Hardware remains off.
