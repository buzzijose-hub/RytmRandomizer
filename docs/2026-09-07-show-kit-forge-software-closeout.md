# Show Kit Forge software and Windows handoff

Date: 2026-09-07. Software checks, the identified Windows build and the actual
packaged GUI smoke passed. Source CI passed on all three operating systems.
Required maintainer review remains `CHANGES_REQUESTED`, and physical validation is pending.
No merge or review-policy bypass is claimed.

## Exact executable and source

Launch [rytm-randomizer-shell.exe](<C:/Users/Jose Buzzi/Documents/ShowKitForgeStudio/show-kit-forge-studio-076ef67a3276/rytm-randomizer-shell.exe>)
from the intact portable directory:

`C:/Users/Jose Buzzi/Documents/ShowKitForgeStudio/show-kit-forge-studio-076ef67a3276`

- Source: **`076ef67a3276bdd27ec6657f9dff77ccf207a5e2`**.
- [Windows build 34149935386](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/34149935386), attempt 1: **SUCCESS**.
- Command: `npm exec --yes --package=@tauri-apps/cli@2.11.4 -- tauri build --no-bundle`.
- Tools: Python 3.11.9, Rust 1.98.1 and Node v20.20.2. This is an unsigned studio build.
- The later documentation-only receipt commit does not change the binary source.

Keep `binaries/rytm-sidecar.exe` beside the shell in its supplied subdirectory.
The [build manifest](<C:/Users/Jose Buzzi/Documents/ShowKitForgeStudio/show-kit-forge-studio-076ef67a3276/BUILD-MANIFEST.json>)
records the source, workflow, tools, packaging overrides and hashes. Downloaded
binary hashes were verified against it:

| Binary | SHA-256 |
|---|---|
| `rytm-randomizer-shell.exe` | `1e8f8b2daa1ec620e19cd18ba89f61231964f43e4de68c40a55f9f954f50407c` |
| `binaries/rytm-sidecar.exe` | `500b2b17a45e4c24068bca4cfeba178d30542b87569f8e52f1589d69c55904aa` |

## Actual packaged smoke

The [smoke receipt](<C:/Users/Jose Buzzi/Documents/ShowKitForgeStudio/show-kit-forge-studio-076ef67a3276/studio-procedure/SMOKE-RECEIPT.json>)
records **PASS at `2026-09-07T18:06:53.332Z`** with
`RYTM_RAND_MIDI_BACKEND=off` and temporary token/data roots.

- The exact packaged shell launched its bundled sidecar child. Its window title
  was `Show Kit Forge studio 076ef67a3276`; it did not depend on local Python.
- The sidecar used loopback port **64055**. The shell injected the string
  `"64055"` and a token; authenticated bootstrap and catalog access succeeded.
- `/health` reported `mode: mock` and `connection_phase: searching`.
- The actual embedded UI at `http://tauri.localhost/` acknowledged the Forge
  catalog refresh. Window and Forge screenshots accompany the receipt.
- Only `hello` and `show_bank_list` were requested. No capture, arm or physical
  output was requested. The smoke's own process tree was stopped afterward.

This proves the packaged software connection, not a hardware save or restoration.
`studio-procedure/HANDOFF-MANIFEST.json` lists the local receipt, screenshots,
blank `STUDIO-CHECKLIST.md` and the `a4-scratch/` reference files with hashes.

## Verification and repaired build failures

The feature Python evidence at `8e7c37eb6473af358a654ad908b9163ecdb8fb9e`
remains unchanged by the later workflow/frontend fixes: **8,926 passed, 5 skipped**;
all 32 touched production modules cover 6,458 statements and 1,558 branches at
100%; whole-package pure branch coverage is 99.3597%. Architecture has 805 cases
and V1.34 parity has 685 cases; all 505 frozen JSON fixtures remain unchanged.

After the port repair, frontend verification passed **852 tests in 62 files**,
with all coverage metrics at 100%: 3,286 statements, 2,475 branches, 1,128
functions and 2,959 lines. Typecheck, lint and production build passed.
Playwright passed **21 tests with 2 existing skips in 51.3 seconds** using
disabled/fake MIDI; screenshots were inspected. Detailed static checks and
earlier timed runs remain in the [run report](superpowers/plans/2026-09-04-show-kit-forge_RUN_REPORT.md).

Build `34146674528` exposed historical CRLF normalization in the source check.
The narrow `git diff --ignore-cr-at-eol --exit-code` repair preserves fixtures;
an eight-case proof retains substantive, whitespace and binary-change detection.
The manifest records that policy and lists only the packaging configuration edit.

The subsequent `4cb0def` build `34147444366` compiled and matched its hashes but
failed the real GUI smoke: the shell supplied string port `50477` while the
frontend dialed `4317`. Its artifact is retained outside the Studio folder for
diagnosis. The repaired client resolves a validated loopback port on every dial,
preserving explicit URL overrides; 43 new regressions cover that behavior.
The successful `076ef67a` artifact is the only copy exposed in the Studio folder.

## Remaining review and physical work

[PR #238](https://github.com/buzzijose-hub/RytmRandomizer/pull/238) is one bundled
PR against `modularize-v1.34`. Its [finding ledger](2026-09-07-show-kit-forge-review-reconciliation.md)
records repairs and retained minor tradeoffs. Source [push CI](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/34149921382)
and [PR CI](https://github.com/buzzijose-hub/RytmRandomizer/actions/runs/34149925207)
both passed. The documentation-only receipt commit has no product or build changes;
its own final check receipt is maintained in the consolidated PR comment.
Required maintainer review remains pending. The observed review decision is
`CHANGES_REQUESTED`, with `edward-rosado` requested; existing branch protection,
code-owner review and conversation-resolution requirements remain in force.

A4 preparation remains inert: `ready = false`, `hardware_send_validated = false`,
A4 SEND blocked and no persistent KIT SAVE. First perform the documented manual
scratch transfer, listening check, save and recapture in disposable slot 20,
with the immutable source protected elsewhere. Keep all physical observations
blank until an operator actually performs them.

That scratch result cannot establish live transport. Verify the value and
destination behavior for paired CC18/50 or NRPN(1,40); saved-KIT Q8.8 is not a
live message mapping. Then implement and review the chosen transport through
the existing guarded seam, with fake-based refusal tests. Bind source/candidate
hashes, targets minus locks, fresh capture/reload proof, connection generation,
exact port, per-action confirmation and recovery slot to one expiring plan.
A persistent SysEx route also needs an implemented and physically verified
capture/restore contract.

Use the [studio checklist](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md)
for the Rytm one-pad audition, untouched-pad check and manual source restoration,
then paired manual saves, semantic recaptures and fresh whole-payload show-time
preflight. Software reset sends no restore bytes. OXI retains sequencing ownership.

## Workspace preservation

Three task-created scratch worktrees were removed after integration. Their
32 backup files were hash-preserved outside the checkout at
`C:/Users/Jose Buzzi/Documents/RytmRandomizer-worktree-backups/pr238-20260907`.
The main checkout and original dirty checkouts remain untouched. The failed
`4cb0def` artifact is preserved with the task backups, outside the Studio folder.
