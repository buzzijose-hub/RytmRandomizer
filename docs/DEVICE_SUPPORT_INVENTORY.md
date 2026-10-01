# Device Support Inventory

The passive inventory is generated from the current canonical catalogs, typed
kit codecs, recipe validators, calibration records and Cockpit policy. It is
not a replacement wire map and never grants hardware readiness.

## Reproduce

```powershell
Set-Location "C:\Users\Jose Buzzi\Documents\RytmRandomizer"
.\.venv\Scripts\python.exe -m rytm_randomizer.cli device-support-inventory-report
.\.venv\Scripts\python.exe -m rytm_randomizer.cli device-support-inventory-report --json
```

The JSON is deterministic for a given source revision. It includes every MIDI
catalog entry and named native field-map row, addresses, machine compatibility,
numeric bounds or selector choices, precision, offline support, conditional live
support, recovery, protection, blockers and repository-relative evidence paths.
Native locations are relative to a track sound unless labelled kit-absolute.
Paired MIDI addresses do not establish a native-to-MIDI conversion.

Current dimensions are 323 Rytm MIDI rows, 10 typed Rytm source-machine layouts,
106 A4 native locations per track (98 semantic field names plus eight fraction
components), 91 A4 synth-track MIDI controls and 105 A4 MIDI rows including the
manual CC catalog. Coupled TUN/FIN and word components are not independent
controls. These counts must not be presented as complete device support.

## Read The Evidence

`domain_authority` distinguishes verified enum choices, typed codec/display
domains and storage-only bounds. A storage range is not a claim that every raw
integer is a meaningful display value. The raw accessors in the codecs also
cover sample start/end and Rytm LFO-depth words; their recipe restrictions and
experimental depth evidence must be read alongside the named field-map rows.
The inventory does not promote raw-accessor coverage into new semantic mappings.
For example, Rytm `default_note` is codec-only: no typed-recipe binding exists.
Rytm recipe source layouts list machine-specific parameter names; the catalog's
broader machine/pad compatibility is reported separately from the stricter
typed-recipe compatibility. Missing source layouts are explicit gaps.

| Surface | Supported In Software | Remaining Boundary |
| --- | --- | --- |
| Capture | Round-trip decode of supplied/supervised kit dumps; cancellable input session; stale-result refusal | Saved-KIT bytes do not prove unsaved front-panel RAM synchronization |
| Rytm targeted mutation | Depth, seed, targets/locks, source-linked candidates and exact prepared CC7 plan | In-scope paired controls refuse the entire plan; source must be manually restored and freshly captured before each Show Forge audition |
| A4 native recipes | Typed enums, coupled pitch, exact Q8.8 frequencies and Q8.7 depth components in offline kit files | General Cockpit mutation/audition is narrower; native encoding evidence is not live-send evidence |
| Show Kit Forge A4 | Source-preserving Filter 1 Frequency artifact and retained local evidence | General A4/BOTH SEND remains blocked; other fields are not promoted by file-codec coverage |
| Favorites/packages | Local candidate selection, favorite records, exact retained files and validated show-pack persistence | Not a hardware save or restore; manual instrument save and fresh return captures are required |
| Recovery | Applied-delta receipts and local history are available; local UNDO does not restore hardware | Stop, manually reload the backed-up saved KIT and freshly capture it before another candidate; automated hardware restoration is not implemented |
| Pi | PR #252 touchscreen and packaging groundwork | Non-simulation appliance APPLY refuses; ARM64, boot, kiosk and physical acceptance remain unproven |

The report includes exact A4 calibration captures/write-return records, but
those receipts apply only to their recorded fields, values and target context.
`tests/fixtures/rio145` contains specific target-unit returns, not validation
of every possible recipe or every track/control. No software fixture can grant
physical validation. The experimental Rytm LFO-depth encoder still calls for
dedicated Rytm precision evidence; never round it into a single CC packet.

## Protection Versus Gaps

Unknown/reserved bytes, source identity, sample identity and non-targeted
sections are deliberately preserved. Patterns, songs, chains, project editing,
sample uploads and automatic hardware saving are outside this kit workflow.
Scenes, performance macros, routing, retrig and choke are protected from
targeted mutations, even where a separate codec can describe some bytes.

Missing native source-machine layouts, machine-specific note tuning, broad
A4 FX/CV/polyphony/performance semantics, native-to-MIDI precision conversion,
unsaved-state synchronization and general dual output are implementation or
evidence gaps, not additional knobs secretly enabled by a catalog count.
For a missing machine/note pair, require approved machine-specific tuning
evidence or an explicitly verified raw value. Do not interpolate a Tune value.

## Studio Handoff

Use [Quickstart section 6a](COCKPIT_QUICKSTART.md#6a-remaining-operator-present-studio-rehearsal),
the [ordered physical checklist](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md),
[Architecture section 6](ARCHITECTURE.md#6-where-to-put-new-work), and
[the passive CLI diagram](ARCHITECTURE_DIAGRAMS.md#14-passive-cli-command-flow).
Begin with backed-up spare sources and one isolated Rytm CC7 change, not a
multi-track bank. Keep any limited legacy A4 probe in a separate supervised
session. A passing Rytm audition/restore/return comparison unlocks a larger
Rytm experiment, not A4 sending or show readiness.
