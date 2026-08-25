# AL16 R2 Maintainability Audit

> Status: in-flight (PR #224)

This pre-closeout audit records the starting maintainability risk for the
offline Analog Rytm mapping-evidence workflow. Scores use 1 (high risk)
through 5 (low risk).

| Gate 14 question | Score | Required response |
| --- | ---: | --- |
| Onboarding curve | 3 | Keep one passive command, one plan, and a replay playbook that names every input. |
| Naming hygiene | 4 | Keep recipe requests, configured bytes, observations, and promoted mappings distinct. |
| Coupling / module boundaries | 4 | Keep comparison logic in `cockpit/export` and reuse the strict Rytm codec and canonical data facts. |
| Magic numbers / strings | 3 | Reuse layout metadata and named report schema constants; do not introduce exporter-local offsets. |
| Configuration vs convention | 4 | Require explicit reference, configured KIT, recipe, manifest, and report paths. |
| Test maintainability | 3 | Share the 18-gap fixture and pin provenance, bounds, requested values, and passive behavior. |
| Build / dev loop friction | 4 | Use focused single-process tests locally and the repository review gate before publication. |
| Error messages | 3 | Fail at the malformed manifest or out-of-bounds layout fact that caused the evidence failure. |
| Versioning / release | 5 | Leave the frozen V1.34 runtime, hardware-pinned dependencies, and release surface unchanged. |
| Future-proofing | 3 | Preserve typed requested values so a future reviewer can compare intent with observed bytes without changing the report contract. |

The audit authorized one implementation workstream because the evidence model,
renderer, CLI adapter, and focused tests form one tight contract. Independent
review and documentation checks remain parallel read-only dimensions.
