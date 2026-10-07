# Device Support Inventory

The passive inventory enumerates `devices.all_devices()` and is generated from
the current canonical catalogs, typed
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

`registered_devices` contains every canonical registry ID, its display name,
track count and evidence-row count. Devices with no report evidence are shown
as `no_support_evidence` in JSON and text; they never inherit another family's
support. Family-specific parameter rows remain descriptive Rytm/A4 facts.
Registration and parameter evidence answer different questions. A future
registry inventory surface can cross-link this report without replacing it.
The count key `a4_synth_track_midi_controls` uses lowercase casing.

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
| Show Kit Forge A4 | Source-linked, parameter-scoped native offline candidates; exact domain-index sampling, canonical render/readback and unknown-byte isolation | General A4/BOTH SEND remains blocked; source-unknown selectors, independent FIN, OXI AMP and default-only fields are immutable |
| Favorites/packages | Local candidate selection, favorite records, exact retained files and validated show-pack persistence | Not a hardware save or restore; manual instrument save and fresh return captures are required |
| Recovery | Applied-delta receipts and local history are available; local UNDO does not restore hardware | Stop, manually reload the backed-up saved KIT and freshly capture it before another candidate; automated hardware restoration is not implemented |
| Pi | PR #252 touchscreen and packaging groundwork | Non-simulation appliance APPLY refuses; ARM64, boot, kiosk and physical acceptance remain unproven |

### October 6 Native Scope And Original Retention

`a4_studio_native_fields` is the reproducible Studio policy projection from the
public optional Device native-field capability. Its 106 rows include read-only
word components; **72 field keys** can be mutable when the actual source value
is known. This is not 106 independent controls or a physical validation count.
Unknown native selector codes stay immutable even if the target code is known.
The row contains exact native offsets/encoding, display quantum, domain grid or
canonical enum codes, protection reason, evidence and unconditional live block.
The older `parameters` rows also describe broader codec storage ranges. They
must not be used as Studio sampling ranges; the native capability owns those.

TUN changes only the evidenced coarse component and retains the complete source
FIN residual and hidden half-step. Independent FIN and modulation fractions are
read-only. AMP remains OXI-protected. `lfo1_phase`, `osc1_sub` and `osc2_sub`
remain read-only because the retained evidence establishes only defaults.
See [the field-level evidence table](A4_OFFLINE_NATIVE_FIELD_EVIDENCE.md).

Library schema 3 retains exact original framed `.syx` bytes and full hashes,
separately from payload projections and semantic rehearsal favorites. File
import validates the registered family codec but never enters the live capture
map or establishes physical freshness. Show Bank v3 retains the immutable full
profile and generation algorithm so exact candidate replay does not depend on
an installed profile registry. Original sources, generated A4 frames, recipe,
scope, locks and local favorite identity survive restart and validated package
round trips. Native packages require canonical deterministic replay; rehashing
metadata cannot legitimize protected or excluded byte changes.

Import into an existing store requires an explicitly supplied unused bank ID
when the original ID already exists. Neither bank is overwritten. Import and
candidate recall revoke output and clear preparation; catalog records grant no
SEND or show-ready authority. Bank history, frames, package entries and reads
remain bounded, and manifest-last atomic publication preserves the prior
complete state on interrupted writes.

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

The [captured Rytm mapping audit](RYTM_MAPPING_STATUS.md) records a separate
source-bound audit of all 33 machine families. The accompanying correction
retains SRC aliases through capture and promotes fixture-proven XT Classic
identity on pads 6–8. All224 SRC rows now have reversible descriptive bindings,
including68 formerly unnamed rows across eleven families. A shared conservative
policy blocks protected or disputed controls in capture, mutation and planning;
native/live semantic and precision evidence remains incomplete. Its Pi matrix
counts describe the pinned PR #252 source, while this
report's 105 A4 MIDI rows use the grouping described above.

The October 5 review repair blocks every CY Ride SRC row with
`src_cy_ride_slot_unverified`, including compact/fallback aliases. Its eight
descriptive catalog rows and source bytes remain available; a changed effective
proposal refuses the whole plan, including any otherwise supported common subset.
This is a shared-policy refusal, not missing MIDI addresses. Common controls are
not blanket-blocked for a CY Ride pad, and locked/untargeted SRC rows cannot
invalidate supported changes elsewhere. The report lists this evidence gap
explicitly under `cy_ride_source_slots`.

The [exact fallback audit](RYTM_MAPPING_STATUS.md#october-5-fallback-src-audit)
reconciles the previous 29 eligible continuous rows to **25 documented-only
eligible rows and four newly blocked CY Ride rows**. It records keys, names,
CC/NRPN, saved primary-byte slots, evidence class and policy, with a reproducible
catalog/inventory check. None is newly hardware-validated. The unchanged
initialized frame projects 328 parameters; the RIO return now projects 325,
with all 264 common values retained in each.

Use [Quickstart section 6a](COCKPIT_QUICKSTART.md#6a-remaining-operator-present-studio-rehearsal),
the [ordered physical checklist](hardware-validation/2026-09-04-show-kit-forge-studio-checklist.md),
[Architecture section 6](ARCHITECTURE.md#6-where-to-put-new-work), and
[the passive CLI diagram](ARCHITECTURE_DIAGRAMS.md#14-passive-cli-command-flow).
Begin with backed-up spare sources and one isolated Rytm CC7 change, not a
multi-track bank. Keep any limited legacy A4 probe in a separate supervised
session. A passing Rytm audition/restore/return comparison unlocks a larger
Rytm experiment, not A4 sending or show readiness.
