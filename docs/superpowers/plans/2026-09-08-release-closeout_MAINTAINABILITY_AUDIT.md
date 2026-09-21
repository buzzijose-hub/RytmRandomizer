# Release closeout maintainability baseline

> Status: in-flight — retrospective preflight for the remaining closeout

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gate 14. This baseline
was reconstructed from the September 8 review findings on September 13. It is
not a claim that the original updater program had this audit before coding.
Scores use 1 for a blocker, 2 for material gaps, 3 for workable boundaries,
4 for clear tested boundaries and 5 for completely evidenced delivery.

| Dimension | Baseline | Required improvement |
| --- | --- | --- |
| Onboarding curve | 2 — docs called implemented work pending; receipts were local. | Tracked plan/state/log and accurate entry-point maps. |
| Naming | 3 — typed states existed, but UI and native vocabulary differed. | One TypeScript protocol accepting actual native states. |
| Coupling | 2 — policy tests did not execute transport, IPC or shutdown composition. | Exercise actual native boundaries and retain checked artifact identity. |
| Constants/dispatch | 3 — typed policy was strong; duplicate refusal maps and partial SemVer remained. | Shared persisted-state vocabulary and one SemVer parser. |
| Configuration | 2 — empty signing key and local-only controls hid native posture. | Authoritative launch settings and explicit keyless limitations. |
| Test maintainability | 2 — 24 skipped browser placeholders and mocked terminal assumptions. | Executable native acceptance with explicit prerequisites and inert install. |
| Build/dev loop | 3 — reusable workflows existed but competed for resources. | One heavy job; shared caches; verified artifact provenance. |
| Errors | 2 — stale callbacks, missing activity and consent acknowledgment obscured failures. | Bounded native journal, truthful retry and independent Doctor export. |
| Version/release | 2 — signature presence was mistaken for verified signing. | Verify actual signature bytes/source/target set before signed manifests. |
| Future extension | 3 — registry and strategy boundaries existed but extension guidance was scattered. | Explicit store, event, manifest and device extension paths. |

The [repair ledger](../../2026-09-08-updater-repair-ledger.md) records findings;
the [post-repair report](2026-09-08-release-closeout_MAINTAINABILITY_REPORT.md)
tracks evidence and remaining limits. No score substitutes for a required gate.
