# Advisory fixtures — detected, reported, deliberately NOT blocking

These three manifests carry real defects, and spec §4 says a client must
still accept them. They were originally filed under `invalid/`, whose
contract is "both the Python validator and the Rust policy layer refuse
every file". That over-claimed:

| fixture | why it does not block |
|---|---|
| `build_not_object.json` | §4: "`build` is informational provenance (never validated for update eligibility — **a client must not refuse an update over provenance fields**)". |
| `platform_entry_unknown_field.json` | §4: "Unknown top-level keys are ignored (forward compatibility)". A v2 client adding `sha256` must not be refused by a v1 validator. |
| `minimum_version_exceeds_version.json` | §4: "`minimum_version` is **advisory-banner-only** in v1 (reserved; making it blocking is a deliberate future decision, **not a hotfix**)". |

The validator still *reports* each one — they surface as advisory
violations — so the information is not lost. What changed is only whether
`manifest_is_acceptable()` returns False.

Moving them here keeps `invalid/` honest: every file under `invalid/` is
refused by both implementations, which is what
`tests/test_update_manifest_corpus.py` now asserts fixture-by-fixture.
