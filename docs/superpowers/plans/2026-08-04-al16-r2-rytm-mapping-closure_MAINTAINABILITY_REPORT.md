# AL16 R2 Maintainability Report

> Status: in-flight (PR #224)

| Gate 14 question | Before | After |
| --- | --- | --- |
| Onboarding curve | Evidence inputs were described only in the plan | The plan, replay playbook, run report, and index provide one discoverable path |
| Naming hygiene | A changed byte could be shown without the recipe expectation | `MappingGapRequest` and `requested_semantic_value` keep intent beside observation |
| Coupling / module boundaries | Manifest paths and values were joined informally by readers | The passive analyzer performs one validated join without changing codec or data ownership |
| Magic numbers / strings | Report versioning was implicit | A named schema constant and report-level `schema_version` make evolution explicit |
| Configuration vs convention | Inputs were already explicit | Explicit path roles remain collision-checked and no machine-local path enters evidence output |
| Test maintainability | Two test modules duplicated the 18-gap path set | The canonical test fixture is shared and malformed joins are covered directly |
| Build / dev loop friction | Review repair had no bounded verification record | The run log records focused single-process commands and the replay playbook preserves them |
| Error messages | Missing requested values could disappear before review | Missing, duplicate, non-scalar, and non-finite manifest values fail at the manifest boundary |
| Versioning / release | Report shape had no top-level version | Schema version 1 is serialized and tested; no release or dependency surface changed |
| Future-proofing | A reviewer had to cross-reference the manifest manually | Every observation now carries the exact requested scalar beside configured bytes |

No dimension regressed. Residual risk remains explicit: observations are still
`review_required`, candidate locations are not writer mappings, and AL02 remains
blocked until saved-KIT evidence is captured and reviewed.
