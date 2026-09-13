# Release closeout maintainability reassessment

> Status: in-flight — post-repair source assessment; final composed checks pending

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 14. Compare the
[baseline](2026-09-08-release-closeout_MAINTAINABILITY_AUDIT.md). These are current
source/evidence scores, not a completed post-merge audit of an untested tree.

| Dimension | Before → current | Evidence and remaining work |
| --- | --- | --- |
| Onboarding curve | 2 → 4 | Plan, state/schema, log, ledger, architecture and replay links are tracked. All 45 companion relative-file links resolve; state/schema structure passes a local check. Final clean-tree verification remains open. |
| Naming | 3 → 4 | Shared `updateProtocol.ts` recognizes native failed/skipped states and owns snapshots/acknowledgments. Merged frontend passed 1,009 tests / 71 files with all configured coverage at 100%. |
| Coupling | 2 → 4 | Current real Wry/IPC/plugin recorder matrix passed 32 cases in 53.5s. Separate signed Windows PE handoff passed both install-on-quit and install-now in 8.2s, exercising actual installer/successor processes. Production NSIS/MSI, macOS and Linux installation remain unverified. |
| Constants/dispatch | 3 → 4 | Refusal codes share `data/persisted_state.py`; native eligibility uses SemVer. Final architecture/types remain required. |
| Configuration | 2 → 4 | Native channel/freeze reflected honestly; bundled key controls download authority. Production credentials remain unconfigured. |
| Test maintainability | 2 → 4 | Native prerequisites fail explicitly, recorder scope documented, shared fixture replaces skipped placeholders. Final composed rerun required. |
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
Final combined full Python, browser, linter and hosted checks remain pending;
the successful native and merged frontend subsets do not complete those gates.
