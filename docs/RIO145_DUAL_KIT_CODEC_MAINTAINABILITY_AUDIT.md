# RIO145 dual-kit codec maintainability audit

Date: 2026-08-08
Plan: `docs/superpowers/plans/2026-08-08-rio145-dual-kit-codec-integration.md`
Stage: post-implementation closeout

## Findings

1. **Onboarding curve:** existing envelope, A4 saved-KIT, Rytm saved-KIT, and
   exporter modules are discoverable from `docs/ARCHITECTURE.md`; the handoff's
   standalone package is not. The integration must document its adapter and
   source-of-truth boundaries beside the existing modules.
2. **Naming:** handoff names are broadly clear, but `payload` means a 2,410-byte
   A4 object there and a 2,415-byte decoded representation here. Public names
   must say `object` or `decoded` rather than relying on ambiguous `payload`.
3. **Coupling:** the handoff duplicates generic SysEx packing and both device
   models. Importing it wholesale would create competing authorities. Only
   field/converter knowledge and evidence should move; envelope and wire logic
   must delegate to current codecs.
4. **Magic values:** object sizes, offsets, product IDs, enums, and validation
   statuses require `Final` constants or typed enums. Recipe inputs must not be
   treated as interchangeable raw integers.
5. **Configuration:** destination slot 14/A14 belongs to deployment metadata,
   not codec behavior. Recipe paths and output paths are explicit arguments.
6. **Test maintainability:** the 42 source tests use compact fixture helpers.
   Import them through shared repo-native fixture loaders and add cross-codec
   assertions rather than duplicating binary parsing helpers per file.
7. **Build loop:** focused integration tests should run with `-n 0`; full repo
   verification retains normal xdist. Deterministic builds need one check mode.
8. **Errors:** failures must identify device family, field path, expected value,
   and missing evidence. Unsupported fields fail closed without partial output.
9. **Versioning:** this is evidence integration, not a package-version fork.
   The repository remains the sole release/version authority.
10. **Future-proofing:** adding another returned KIT should require a fixture,
    metadata record, and validation test, not another codec. Adding a supported
    semantic field should touch its field strategy, recipe schema, and tests.

## Baseline risks

- A4's five-byte decoded metadata prefix can cause offset corruption if hidden.
- A copied standalone envelope implementation would drift from current codecs.
- Native pattern support would violate the OXI sequencing boundary.
- Binary-return evidence could be overstated as sonic/reference equivalence.
- RIO-A pad 11 intentional silence could be misclassified as missing coverage.

All five risks are blockers for PR closeout and have direct acceptance tests in
the linked plan.

## Post-implementation result

- The integration delegates Elektron envelope handling to the canonical
  snapshot helpers and cross-validates Rytm output with the existing saved-KIT
  codec. Native A4 and Rytm saved-KIT paths select MSB-first mask ordering;
  LSB-first remains limited to the named legacy synthetic Rytm body decoder.
  A native-fixture divergence witness prevents those contracts from being
  conflated. No competing envelope or hardware adapter was introduced.
- A4 object offsets are isolated behind the explicit five-byte-prefix adapter;
  field and recipe modules use typed enums, frozen records, named constants,
  and fail-closed validation.
- The passive command registry exposes six file-only RIO145 operations. No
  RIO145 production or test path imports a MIDI backend, enumerates ports,
  opens ports, or sends MIDI/SysEx.
- The 12 real-machine fixtures are immutable and hash-pinned. Generated A4 and
  Rytm KITs reproduce their target-unit-return native objects with zero native
  payload differences after destination-slot normalization.
- The focused RIO145 suite passes 118 tests with 100 percent statement and
  branch coverage across all seven new production modules. Strict Pyright
  passes all 11 touched production modules with zero diagnostics.
- Repository closeout passes 748 architecture tests, 685 frozen V1.34 parity
  tests, and the 7,821-test full suite with 4 skips. Ruff, Black, and isort are
  clean on the exact implementation tree.
- Deterministic A4 and Rytm builds are byte-identical across repeated runs;
  both target-unit returns validate with zero native payload differences after
  destination-slot normalization. OXI evidence contains 360 events through
  bar 191 and remains file-only.
- Binary validation remains explicitly classified as target-unit acceptance
  evidence, not listening refinement or sonic-equivalence proof. OXI One
  remains the sole pattern and arrangement owner.

The remaining closeout work is exact-path staging, publication, and CODEOWNER
review. These are release-process checks, not unresolved maintainability
findings in the RIO145 implementation.
