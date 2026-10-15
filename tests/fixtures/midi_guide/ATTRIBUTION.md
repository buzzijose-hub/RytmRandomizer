# Retained MIDI Guide References

Source data: Pencil Research and MIDI Guide community contributors.
[Dataset](https://github.com/pencilresearch/midi),
[device index](https://midi.guide/d/elektron/),
[CC-BY-SA-4.0 license](https://github.com/pencilresearch/midi/blob/main/LICENSE).
The upstream README notes that device-specific portions may be owned by their
respective manufacturers. Preserve upstream attribution and that caveat.

The two CSVs are unmodified mechanical copies of the user's supplied originals.
Scoped Git attributes disable text conversion, including on Windows checkouts.
The generated ledger and adapted reference claims are CC-BY-SA-4.0; this does
not change the existing PolyForm Noncommercial 1.0.0 license of implementation code.

Verified upstream dataset commit: `a52a7c9e1a81a4e95f31ec8b6a660071d11ecd6b`.

| File | Records | SHA256 | Git Blob | Last Upstream Change |
| --- | ---: | --- | --- | --- |
| Analog Four MKII.csv | 230 | da38d8ec8df47d4a6c39034b2f1c829475ac301c712d26c0a4b4787ae259ea69 | 53a1a26263782ce8f044b112a33642de27f547cd | 1bf3ced25095dff32f71f8930da7415206d47130 |
| Analog Rytm MKII.csv | 322 | c370aa520117322ef559147b94b9cee9c392f6482a5147f0ea2485a07ace0cc5 | 46cc786dc106f35a00a9412057f8ee63192aa308 | 3a072c57adfe7cfc85327b65617324d002cafca0 |

Original locations: `G:/ELEKTRON/Analog Four MKII.csv` and
`G:/ELEKTRON/Analog Rytm MKII.csv`.
Original audit-v2 and provenance were supplied under the user's
`ShowKitForgeStudio/parameter-csv-audit-2026-10-14` directory and are copied
unchanged. `audit.json` was superseded and is not used. The new upstream blob
verification supplements, but does not overwrite, the older provenance's
unresolved upstream-identity statement. The June 10 A4 upstream change refers
to OS1.55/manual/live-monitor work: a third-party claim, not our hardware receipt.

None of these files is an Overbridge export, target-unit capture, native saved
object mapping or authorization to mutate/send. Reproduce from retained inputs
with `python scripts/reconcile_midi_csv.py --check`.
