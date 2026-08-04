# AL16 R2 Replay Playbook

> Status: in-flight (PR #224)

## Resume the run

1. Open the `codex/al16-r2-rytm-mapping-closure` worktree.
2. Read the plan, state file, and append-only run log.
3. Reconcile `git status --short --branch` with PR #224.
4. Run the focused analyzer and CLI tests with `-n 0` before editing.
5. Preserve the frozen V1.34 fixtures and hardware-pinned dependencies.
6. Never promote a candidate location from this report automatically.
7. Run architecture, parity, typing, lint, coverage, and the repository review gate before push.
8. Update the state and run log after every material review or verification event.

## Reproduce the passive report

```powershell
Set-Location (Join-Path $env:USERPROFILE "Documents\RytmRandomizer")

.\.venv\Scripts\python.exe -m rytm_randomizer.cli `
  al16-rytm-mapping-evidence `
  --reference output\local\reference\RYTM_Test1_Init_Kit.syx `
  --configured output\local\al16\AL02_LOCK_RYTM_CONFIGURED.syx `
  --recipe specs\al16\AL02_LOCK_RYTM.yaml `
  --gap-manifest output\al16\AL02_LOCK_RYTM_manifest.json `
  --report output\local\al16\AL02_LOCK_RYTM_mapping_evidence.json
```

The command requires local files, validates provenance before comparison, and
writes a schema-versioned review-required report. It does not enumerate MIDI,
open a port, transmit SysEx, or update the writer allowlist.

## Recovery rules

- If local changes are present, inspect and preserve them; do not reset or stash.
- If PR head differs, fetch and reconcile without force-pushing.
- If a report input is missing, stop with the existing structured local-file error.
- If provenance differs, preserve both files and investigate; do not bypass the hash check.
- If a canonical location exceeds the decoded payload, treat it as a data-contract defect.
- If interrupted, set state phase to `interrupted`, record `last_event`, and resume from this playbook.

## Termination

The run is complete when the repair commit is pushed, hosted checks pass,
CODEOWNER approval is fresh on the exact head, and the plan artifacts record
the final state. The studio capture remains a separate operator phase and does
not weaken the offline review-repair completion criteria.
