# Captured Rytm mapping: replay and handoff

> Status: in-flight — replay recorded; publication and protected plan termination pending.

This is an offline replay of the correction in existing [PR #254](https://github.com/buzzijose-hub/RytmRandomizer/pull/254),
based on `941643c551abfa225f45c70a954b6671d1cbb5f4` and targeting
`modularize-v1.34`. Continue that logical PR; do not stack it on PR #252 or
publish a separate learning PR. No scheduled job or automatic merge is created.

## Resume from evidence

1. Read [AGENTS.md](../../../AGENTS.md), [CONTRIBUTING.md](../../../CONTRIBUTING.md),
   the [plan](2026-10-01-rytm-captured-machine-mapping.md),
   [state](2026-10-01-rytm-captured-machine-mapping_STATE.json) and
   [run log](2026-10-01-rytm-captured-machine-mapping_RUN_LOG.md).
2. Inspect the actual delivery checkout's `git status --short --branch` and
   `git rev-parse HEAD`. Match PR head, base, receipts and pending work; do not
   infer current approval from an older review or prototype run.
3. Preserve the original dirty user checkout, running studio checkout, retained
   frames and concurrent changes. Never reset, clean or force-push them. Use
   declared disjoint ownership and an isolated checkout for new writing work.
4. Validate the existing state against its
   [schema](2026-10-01-rytm-captured-machine-mapping_STATE.schema.json).
   Status and phase are descriptive checkpoints, not a new scheduler or MIDI
   authorization model. Missing evidence stays pending.

The baseline audit and initial records were retrospective. Gate 14 remains
unchecked until its required acknowledgment and actual post-merge reassessment
are recorded. The documented historical worktree/timing limitations must not be
rewritten as compliant execution.

## Passive replay

From the delivery checkout, use the repository virtualenv after the normal
development setup. On Windows, consult the
[Python invocation guide](../../../.claude/skills/python-on-windows/SKILL.md)
and resolve the actual interpreter, avoiding Store shims:

```powershell
$replayPython = (Resolve-Path .venv/Scripts/python.exe).Path
$env:RYTM_RAND_MIDI_BACKEND = 'off'
& $replayPython -m rytm_randomizer.cli device-support-inventory-report
& $replayPython -m rytm_randomizer.cli device-support-inventory-report --json
& $replayPython -m pytest tests/test_devices_strategies_snapshot_decoder.py tests/cockpit/test_data_rytm_parameter_map.py tests/cockpit/test_ws_kit_capture_handlers.py tests/test_device_support_inventory.py tests/test_data_layer.py -n 0
```

These tests use the existing injected providers and retained fixtures; the CLI
report performs no discovery, port opening or send. Do not enable capture or
construct a real provider to reproduce the software correction. A supplied
studio frame is additional evidence, not required to invent or replace the
committed RIO fixtures.

Check the actual regressions, not only the test count:

- XT raw ID `0x08` on pads 6–8 is promoted; `0x88`, other unverified tom IDs,
  unknown IDs, absent facts and mismatched event owners cannot become SRC
  mutation parameters.
- The canonical owning section reaches the existing alias; unrelated sections
  and control mismatches stay omitted. Exact source bytes and common fields
  survive the composed decode → anchor → Cockpit projection.
- Targets and locks remain effective. Changed paired controls refuse the whole
  plan; supported positive cases use genuine retained-source candidates with
  deterministic seeds/scopes. Unchanged, locked and untargeted paired rows do
  not block supported single-CC changes.
- Registry summaries equal `all_devices()` in text and JSON. A newly registered
  unsupported device appears with zero evidence and no physical validation
  grant; existing family counts do not increase merely from registration.

The coordinator then runs the repository's full coverage, architecture, frozen
parity, lint, strict touched-production typing, Vulture and review gates. Keep
one resource-heavy job at a time. Never use `-o addopts=''`, regenerate V1.34
fixtures, widen architecture allowlists or change hardware dependency pins to
obtain a passing replay. A failed check requires investigation and a focused
repair, followed by affected composed gates.

## Receipt and delivery rules

The coordinator's final composed Studio receipt at this checkpoint is
**9,823 passed, 5 skipped, 6 warnings in 269.56 seconds**, with **18 production
modules at 100% line and branch coverage**, **99.37% pure branch coverage**, zero
strict typing findings across those 18 modules, and passing lint/Vulture checks.
It is a software receipt for the verified delivery candidate, not a hardware
observation or proof of an as-yet-unrecorded publication SHA. Preserve the earlier
failed runs in the log; new code changes invalidate affected receipts.

Record actual final commit, hosted checks and scoped review findings in the
state/log before reporting publication. Request review on the updated existing
PR and retain protected maintainer/CODEOWNER approval; do not self-approve,
bypass hooks or merge automatically. Local publication can finish while the
plan remains in-flight for protected merge and post-merge reassessment.

Input capture and output authority are separate. Hardware acceptance requires
operator-approved backed-up sources, exact endpoint selection, fresh matching
capture, complete plan review, explicit ARM and separate SEND confirmation.
Manual reload and physically verified recovery remain necessary. This replay
does not perform those steps or grant A4/BOTH, Pi or touring readiness.

On STOP or budget exhaustion, preserve work and record the existing
`INTERRUPTED` or `BUDGET_EXCEEDED` status with remaining work. On resume, reconcile
actual source and receipts before proceeding; elapsed time is never approval.
