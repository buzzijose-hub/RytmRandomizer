# Release closeout maintainability reassessment

> Status: in-flight — all local gates passed; owner exception approval and hosted review pending

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 14. Compare the
[baseline](2026-09-08-release-closeout_MAINTAINABILITY_AUDIT.md). These are current
source/evidence scores at validation `7cc10e92`, with final local static checks
passed. Outstanding owner exception approval and hosted checks keep protected
closeout incomplete.

| Dimension | Before → current | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 2 → 4 | Plan, state/schema, log, ledger, architecture and replay links are tracked. All 45 companion relative-file links resolve; state/schema structure passes a local check. Final clean-tree verification remains open. |
| Naming | 3 → 4 | Shared `updateProtocol.ts` recognizes native failed/skipped states and owns snapshots/acknowledgments. Final combined frontend passed 1,010 tests / 71 files in 40.58s with all configured coverage at 100%; ESLint/build passed. |
| Coupling | 2 → 4 | Current real Wry/IPC/plugin recorder matrix passed 32 cases in 53.5s. Separate signed Windows PE handoff passed both install-on-quit and install-now in 8.2s, exercising actual installer/successor processes. Production NSIS/MSI, macOS and Linux installation remain unverified. |
| Constants/dispatch | 3 → 4 | Refusal codes share `data/persisted_state.py`; native eligibility uses SemVer. Architecture checks passed in the 9,922-test combined suite; strict Pyright passed all 51 touched production modules. |
| Configuration | 2 → 4 | Native channel/freeze reflected honestly; bundled key controls download authority. Production credentials remain unconfigured. |
| Test maintainability | 2 → 4 | Combined Python passed 9,922 tests / six skips; all 51 touched production files have 100% line/branch coverage. Browser passed 32 tests / two existing skips; no updater/native skips. Native prerequisites fail explicitly and the shared recorder fixture replaces skipped placeholders. |
| Build/dev loop | 3 → 4 | Worker/resource caps, shared environments, clean bundle output and verified artifact assembly. Cross-platform hosted validation remains required. |
| Errors | 2 → 4 | Typed failure callbacks and bounded journal hydrate; Doctor reads fresh activity independently. Beacon callback/rotation locking/keyless history and installed-version startup confirmation are covered by the current 186 passing default Rust tests and 32-case native matrix. |
| Version/release | 2 → 4 | Real Minisign verification, four-target provenance, stable-promotion metadata and shared hardware-path checks. No production release or OS signing receipt. |
| Future extension | 3 → 4 | Existing store registry, native policy/sink, shared IPC and release helpers are documented; separate Digitakt Device/Strategy work remains passive. |

No observed score regressed, but pending required verification cannot be averaged
away. The [state](2026-09-08-release-closeout_STATE.json) keeps final checks and
protected approval open. The [run report](2026-09-08-release-closeout_RUN_REPORT.md)
distinguishes recorded subsets from final composed evidence and identifies the
exact installer/successor hashes for the two successful isolated Windows PE
handoffs. That proof does not establish production NSIS/MSI, macOS or Linux
installation, production signing credentials, or physical studio observations.
Combined full Python, frontend and browser checks passed at `7cc10e92`. Final
Rust/Python static checks also passed. Updater hosted checks and protected
review remain pending; local evidence does not replace owner exception approval.
