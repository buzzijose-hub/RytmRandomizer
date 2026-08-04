# AL16 R1 Maintainability Report

> Status: in-flight (PR #222)

| Dimension | Before | After |
| --- | --- | --- |
| Onboarding | Evidence behavior was implicit | README and CLI help state that R1 emits evidence, not a kit |
| Naming | Semantic and encoded values could blur | Typed semantic, normalized, and raw fields are recorded separately |
| Coupling | New writer risked duplicating envelope logic | A dedicated Rytm saved-kit codec composes shared Elektron envelope and u14 helpers |
| Magic values | Exporter-local facts were possible | Canonical AL16 state, role, converter, and layout facts live in `data/` |
| Configuration | Output behavior was underspecified | Reference, recipe, destination slot, and output are explicit and collision-checked |
| Tests | Happy-path pressure could hide gaps | Exact 18-gap, zero-mutation, determinism, drift, collision, transaction rollback, evidence-hash, and no-MIDI tests are pinned |
| Build | Wall-clock timestamps were unstable | Unix epoch is the default; valid `SOURCE_DATE_EPOCH` is optional |
| Errors | Similar exporters classified errors separately | Shared `LocalFileExportErrorCode` and portable-name validation classify bounded file failures |
| Versioning | Frozen behavior was at risk | V1.34 parity and existing codec round trips remain byte-identical |
| Future change | Audit and writer could be confused | Phase R1 accepts only AL02 and withholds `.syx` until mappings are verified |

Residual risk is explicit: 18 critical mappings remain unverified, so AL02 is
not loadable and no `.syx` exists. That is the intended fail-closed result, not
a hidden partial success.
