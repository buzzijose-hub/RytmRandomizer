# Appliance parameter evidence and optional controls

`rytm_randomizer.cockpit.capture.appliance_capabilities.appliance_capability_matrix()`
provides the versioned JSON-compatible matrix consumed by appliance diagnostics
and the parameter UI. It computes its rows from the existing catalogs rather
than a checked-in copy that could drift. It performs no MIDI or filesystem I/O.
`parameter_capabilities(device_id)` returns immutable rows;
`get_parameter_capability(parameter_id)` uses an exact identity.

The matrix includes every Rytm manual catalog row, including each engine's SRC
parameters, all A4 synth CC and NRPN-only rows, track/performance/modulation
rows, and native-only A4 controls such as FIN, Noise Color, Drift, Portamento,
Legato and Resonance Boost. Each existing A4 mapped field occurs in at least
one row. Fraction bytes are members of their exact modulation-depth field;
they are not independently randomized controls. Every row carries source and
validation references, explicit blockers, and protection defaults.

| Matrix field | Meaning |
|---|---|
| `parameter_id` | Stable device/engine/page/parameter identity; labels are not unique across Rytm engines. |
| `cockpit_key` | Existing Rytm compact key or A4 native field name; an alias confers no output authority. |
| `page`, `catalog_section` | UI sound page and original source section. Rytm engine-named catalog sections are normalized to the SRC page. |
| `native_fields`, `native_offsets` | Existing decoded saved-KIT fields and track-relative offsets (Rytm FX offsets are kit-relative). No guessed MIDI-to-offset conversion. |
| `native_domain` | Stored representation, including pitch, Q8.8 and Q8.7 precision. |
| `display_domain`, `legal_domain` | Exact textual bounds/steps or listed enum values, with `catalog`, `codec_range`, `calibration`, or `unknown` authority. A codec range describes supported software values, not physical validation of every possible value. |
| `midi_domain` | Catalog transport representation; A4 conversions remain unvalidated. |
| `capture_support`, `baseline_coverage` | Mapped saved-state decoding versus documented-only rows. Saved state does not prove current unsaved RAM. |
| `mutation_policy`, `send_support` | Conditional, session-checked CC7 eligibility or a visible refusal. |
| `restore_support` | Only exact successfully applied parameter deltas can be considered for Rytm restoration; A4 remains blocked. No whole-KIT restoration claim. |
| `offline_render_support` | Mapped codec, validated offline candidate, narrow validated saved-file exporter, or unsupported. |
| `default_protected`, `protection_reasons` | Application-write locks. They do not disable the instruments' own LFOs, scenes, parameter locks or performance control. |

For Rytm, resolve `cockpit_parameter_mapping(pad.machine, key)` and then the row
whose `(machine_key, catalog_section, parameter)` matches the canonical mapping. A global
dictionary keyed only by `tun` or `dec` loses engine-specific domains. Actual
capture promotion is still decided by the canonical capture bridge, and
ArmedApply remains the Cockpit's output boundary. A matrix row cannot arm,
confirm, synchronize, or manufacture a restore baseline. Paired-CC LFO Depth
is blocked until precision-preserving conversion and restoration are proved.

Tuning, samples, machine identity, routing, high-impact modulation and
sequencing/performance controls are protected by default. All A4 AMP controls
are protected for the OXI AMP pumping workflow. Unknown selector domains
remain blocked. Known enums list their legal choices and must never be
interpolated as continuous values.

## Existing evidence boundaries

A4 Filter 1 Frequency retains calibrated 1/256 native precision and the
offline captured-KIT candidate scope. Filter 2 Resonance's three
operator-confirmed saved-file transfers remain separately represented as
`validated_saved_file`. Neither establishes live CC/NRPN authority, unsaved
working-state capture, automatic request/response behavior, or restoration.
The observed A4 current-KIT dump returned previous saved values after unsaved
front-panel edits. The existing [hardware procedure](MANUAL_HARDWARE_VALIDATION.md)
and [saved-file results](hardware-validation/2026-07-16-a4-saved-kit-roundtrip-results.md)
remain the evidence authorities. The RIO145 typed codecs and returned fixtures
are reused without repeating their completed mapping experiments.

Every A4 live mutation/send/restore row stays blocked by the existing stage
policy. The matrix-wide automatic-request, complete-unsaved-synchronization
and whole-KIT-restore capabilities are false. Simulation must be labeled and
cannot grant any of these capabilities.

## Captured A4 offline projection

`cockpit.capture.appliance_a4.appliance_snapshot_from_a4_capture()` re-decodes
the retained saved-KIT frame and verifies its exact native payload and
fingerprint before projecting 98 mapped controls on each of the four tracks.
It uses the existing `A4Kit`/`A4Sound` accessors and keeps the retained frame,
unknown bytes and original capture untouched. Documented-only rows have no
projected value. Invalid mapped native values refuse projection without
clipping or substituting simulation values.

`appliance_a4_parameter_encoding(parameter_id)` exposes the per-cell integer
domain and exact display conversion used by preview mutation. Q8.8 words keep
their low byte; Q8.7 depths retain every 1/128 step; pitch words retain hidden
half steps. Detune is a separate bipolar byte in -64..63, rather than an
oscillator pitch word. FIN is displayed but cannot be independently mutated
because it shares the pitch word. Unknown selector domains also remain
immutable. Display strings use integer arithmetic, independent of the active
Decimal precision. The calibrated Filter 1 domain remains 0..127.00; broader
codec ranges are labeled as software evidence, not hardware validation.
The immutable `data.analog_four_kit_fields.A4_NATIVE_FIELD_DOMAINS` table is the
single native-format authority for these scales, centers and bounds. Both the
matrix and projection derive from it; the typed codec imports the same pitch,
FIN and modulation constants. Field-specific calibration remains separate.

This metadata grants offline preview eligibility only. The row's default
protections, categorical choice restrictions, OXI AMP locks and explicit
per-track/page/parameter scope still apply. Live send and hardware restoration
remain false, and captured saved values do not claim the instrument's current
unsaved state.

## Optional physical input layer

`rytm_randomizer.cockpit.appliance_controls` maps one push encoder plus MUTATE,
UNDO and ANCHOR buttons to the same local command intent sink used by touch.
The encoder emits `focus_step`; its push emits `activate_focus`. Buttons emit
`mutate`, `undo`, or `capture_anchor` (the appliance command operation `anchor`).
These intents cannot request ARM or APPLY. Capture and return-to-anchor remain
distinct actions, and all normal stale-plan, capture, arming and confirmation
checks still apply downstream.

`ApplianceControlMapping` configures button assignments, encoder step and
debounce. `ApplianceBoardConfiguration` must explicitly select a board, a
`/dev/gpiochipN`, and unique chip-line assignments. No default wiring or pin
numbers exist. Both encoder phase lines must be selected together. An
`ApplianceInputAdapter` is dependency-injected; hardware-specific packages are
optional. Constructing the mapper does not import GPIO or access a pin.
`ConfiguredApplianceControls.start()` refuses a missing board configuration,
and polling forwards only board-configured sources.

Inputs use bounded event IDs, one signed detent per encoder event, press/release
edges, and monotonic timestamps. Repeats, stale/duplicate events and contact
bounce cannot repeatedly fire mutation. Polling is bounded to 128 events and
128 remembered identities. Shutdown drops transient input state. Mock-adapter
tests verify explicit configuration, bounded polling, remapping, release,
failure cleanup and the absence of implicit pin activity.
