# MIDI CSV Ledger Closeout

## Delivered Contract

- `reports.midi_csv_reconciliation.build_midi_csv_reconciliation(a4_csv,
  rytm_csv, audit_v2, provenance)` accepts explicit local `Path` inputs and
  returns `MidiCsvReconciliationLedger`.
- `serialize_midi_csv_ledger(ledger)` and
  `format_midi_csv_gap_summary(ledger)` return deterministic bytes.
- `scripts/reconcile_midi_csv.py --check` reproduces the retained full-source
  ledger without G: or any hardware. Running without `--check` publishes JSON
  and Markdown together through the existing atomic write-set owner.
- Parser and matcher are separate narrow modules. Source schemas, scope aliases,
  evidence references and pinned fallback provenance live in `data/`, not reports.
  `MIDI_GUIDE_SOURCES` owns filenames, input hashes, source URLs, attribution and
  license. Its `upstream_revision` and `upstream_blob_sha1` are consumed when
  present; old-base fallback IDs retain independently verified original blobs.

The implementation worktree began at `07cdc166`. The facts dependency was
cherry-picked from parent commit `28ef60de` as local `1fcd2429` so the real
descriptive APIs could be exercised. Parent already has that dependency: apply
only this worker's final own-files commit, not the dependency again.

## Row Completion

552 verbatim source records: 230 A4 and 322 Rytm. 403 complete-address matches,
24 unique partial-address matches and 125 reference-only A4 rows. The latter
include FX/CV and the unbound Noise Color row. BT Classic Sweep Depth is a
separate canonical omission, corroborated by manual pages 93/105. Raw CSVs,
original audit-v2 and original provenance are retained without rewriting.

Each entry separates CSV claims, canonical MIDI domains, canonical reference
knowledge, native claims/evidence, current support-inventory policy, runtime
binding, protection, manual recovery and physical blockers. Sparse/interval
usage claims are retained; overlaps are explicit. Machine identity code claims
and native identities are a separate unresolved comparison, not a converter.

## Actual Verification

- Final focused pytest: **40 passed in 0.91s**, primary project venv, checkout
  `PYTHONPATH`, `tests/test_midi_csv_reconciliation.py -n 0`.
- Earlier focused result: 34 passed / 3 failed. Fixed two test assumptions
  (Noise Color scope and BD Classic CC19 = Hold) and regenerated stale output.
  Intermediate corrected result: 39 passed in 0.81s.
- Ruff default and extra `PLR,ERA,ARG` production ratchets: passed.
- Strict Pyright: 0 errors, 0 warnings at the final production checkpoint.
- Black/isort own-file checks and generation/check-mode: recorded at commit.
- Original and retained SHA256s match; both locally computed Git blobs agree
  with the parent-verified upstream blobs.
- Official Rytm OS1.72 PDF fetched/read locally, 13,216,102 bytes, SHA256
  `6485fc5eee11cd210913fa6041cde889b74ddaff19042220cea1db4b7b5d985f`.
  Relevant address/machine sections inspected; no PDF bytes redistributed.

No full suite, architecture suite, coverage run or build was performed by this
worker. Parent reserved integration gates. No branch/PR/push or descendant agent
was created, and no MIDI/USB enumeration, opening, arming or sending occurred.

## Integration And Remaining Gates

Parent owns `data/__init__.py`, shared tests, snapshot integration and packaging
notices. Optional source-spec exports are `MidiCsvSourceSpec`, `MIDI_CSV_SOURCES`,
and any source-contract constants parent needs; report code imports its owning
modules directly. No runtime command registration is required for this file tool.

After applying the own-files commit, run `scripts/reconcile_midi_csv.py --check`
against the assembled tree. If another owner changes canonical inventory data,
regenerate the two ledger artifacts before the final full-suite checkpoint.
Require the actual integration suite and coverage summary; no touched-file
coverage percentage is claimed here. Shared README/architecture/diagram/status
updates and the packaged CC-BY-SA notice belong to the parent bundle.

A4/BOTH output, all CY Ride SRC controls, high-resolution paired controls,
unsaved-state coherence and automatic restoration remain held. Rytm
`validated_runtime` is a software category, not a per-row physical receipt.
Limited Pad 2 observations are not expanded to other pads or parameters.
Canonical descriptions and the CSV do not promote SEND, native offsets,
candidate eligibility or touring readiness. Existing pins and V1.34 goldens
remain untouched.

## Review And Learning

Sequential review was necessary because no descendant agents were allowed.
Architecture: existing data/reports/scripts directories and passive inventory
dependency only. Abstraction: Device/inventory and atomic publication reused;
the MIDI monitor was surveyed but is not a lossless CSV matcher. Side effects:
explicit file reads only, plus requested artifact writes; full generation passed
with hardware-library imports trapped. Facts: no mutable policy or addresses
were copied into reports. Docs: complete generated row ledger, gap index,
license separation and reproduction instructions retained. Integration gates
are still parent-owned, so this receipt is not a merge-readiness verdict.

The important reusable lesson is that source usage strings can mix sparse
choices with a catch-all interval. Expanding or flattening these would erase
the contradiction. Keep claims, missing cells and representations distinct,
and resolve identity with context and address evidence before consulting labels.
