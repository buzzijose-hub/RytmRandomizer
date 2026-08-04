# AL16 R1 Maintainability Audit

> Status: in-flight (PR #222)

This pre-closeout audit records the starting maintainability risk for the
contained Phase R1 exporter. Scores use 1 (high risk) through 5 (low risk).

| Dimension | Score | Required response |
| --- | ---: | --- |
| Onboarding | 3 | Keep one operator command and document evidence-only output. |
| Naming | 4 | Keep AL16, AL02, semantic, normalized, and raw value terms distinct. |
| Coupling | 3 | Reuse the existing Rytm codec and Elektron envelope instead of copying them. |
| Magic values | 2 | Move pad roles, states, converters, and layout facts into the data layer. |
| Configuration | 4 | Require explicit reference, recipe, slot, and output arguments. |
| Tests | 3 | Pin determinism, fail-closed gaps, input preservation, and passive behavior. |
| Build | 4 | Keep the build dependency-free and reproducible with a bounded timestamp. |
| Errors | 3 | Return stable local-file error codes and precise mapping-gap evidence. |
| Versioning | 5 | Preserve the frozen V1.34 runtime and existing codec contracts. |
| Future change | 2 | Separate today's evidence audit from a future verified writer. |

The audit authorized one implementation workstream because the compiler,
canonical facts, tests, and evidence files share a tight contract. Parallel
work was limited to read-only review dimensions.
