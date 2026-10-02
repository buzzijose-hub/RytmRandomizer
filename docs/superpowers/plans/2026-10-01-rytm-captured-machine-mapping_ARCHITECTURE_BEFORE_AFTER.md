# Captured Rytm mapping: architecture before and after

> Status: in-flight — local software verified; protected delivery and physical acceptance pending.

This describes the composed correction delivered through existing [PR #254](https://github.com/buzzijose-hub/RytmRandomizer/pull/254),
starting from `941643c551abfa225f45c70a954b6671d1cbb5f4` against
`modularize-v1.34`. The Pi prototype at `8cfa6f7b` supplied the diagnosis;
it is not a stacked PR base or a requirement to deploy Pi software.
See the [plan](2026-10-01-rytm-captured-machine-mapping.md) for scope and the
[run log](2026-10-01-rytm-captured-machine-mapping_RUN_LOG.md) for source-specific receipts.

## Existing production surfaces

| Module | Before | After |
| --- | --- | --- |
| [Rytm snapshot decoder](../../../rytm_randomizer/devices/strategies/analog_rytm_snapshot_decoder.py) | Every machine fact on tom pads 6–8 stayed candidate-only, including fixture-proven XT Classic. | Exact raw XT ID `0x08`, obtained from the canonical machine catalog, is promoted on these pads. Raw `0x88` is not promoted merely because masking yields 8; other tom IDs remain pending. |
| [Cockpit reverse parameter map](../../../rytm_randomizer/cockpit/data/rytm_parameter_map.py) | Existing machine aliases accepted section `SRC`, while the canonical shell emitted the owning machine key. | Both `SRC` and the exact owning machine section are accepted. Other machine sections are rejected; existing aliases and exact control matching remain unchanged. |
| [Capture bridge](../../../rytm_randomizer/cockpit/capture/bridge.py) | Machine SRC events were dropped by the section mismatch. A shell fallback label alone could otherwise look like usable machine identity. | SRC projection requires a promoted machine fact whose decoded ID matches the event's canonical machine. Unverified, absent or mismatched facts are omitted; common fields and exact captured bytes remain available. |
| [Inventory data](../../../rytm_randomizer/data/device_support_inventory.py) | Report rows described known families, without a canonical registry-to-evidence summary. | An immutable registered-ID-to-evidence-family table supplies report identity only. Pi omission prose no longer embeds changeable PR status. |
| [Data facade](../../../rytm_randomizer/data/__init__.py) | Exported evidence and omission facts. | Also exports the canonical registry/evidence binding; no duplicate registry is introduced. |
| [Passive inventory report](../../../rytm_randomizer/reports/device_support_inventory.py) | Family rows did not expose registered devices with no matching evidence. One count key used mixed case. | Sorted `all_devices()` summaries expose every registered ID. Unknown evidence bindings report zero rows and `no_support_evidence`, without inheriting another family's support. The count key is `a4_synth_track_midi_controls`. |
| [Lazy MIDI provider](../../../rytm_randomizer/mido_provider.py) | Its wire wrapper accepted neutral CC shapes, while the existing A4 helper supplied the public `type` shape. The approved probe failed before backend send. | Compatibility work recognizes the existing public CC shape at this boundary, retaining kind/field checks and backend-message reconstruction. Composed fake-backend verification and the same bounded approved physical retry must precede any acceptance claim. |
| [Native updater transport](../../../desktop/shell/src/update_transport.rs) | The beacon could construct its TLS client before the updater asynchronously installed the shared provider. Same-head CI could pass or panic depending on scheduling. | Ensure a process provider before beacon-client construction, reusing the already locked ring provider. Preserve an existing provider and TLS policy; hosted Rust/native acceptance remains required because no local Cargo toolchain is installed. |

## Shape and reuse

No production module, Protocol, device family, codec, sender or transport was
added, deleted or renamed. The new `RegisteredDeviceSupport` TypedDict describes
report identity and evidence counts. Two small helpers compose existing seams:
`_has_promoted_machine_fact()` checks capture identity, and
`_registered_device_support()` joins the canonical registry to existing report
rows. Neither constructs a real provider or authorizes output.

The decoder reuses canonical machine facts; the bridge reuses the existing
snapshot-shell anchor and reversible key/control lookup. The report reuses
`all_devices()`, immutable data facts and passive CLI formatting. Shared retained
frame helpers remain in `tests/conftest.py`.

The A4 compatibility follow-up reuses `neutral_cc_fields()` and
`WireOutputPort`; it adds no sender, Protocol or alternate output route. Public
app-to-provider tests preserve the real message's `type` spelling instead of
adding attributes that mask the production mismatch. The native TLS repair
uses the existing beacon transport and locked provider, without introducing
another HTTP stack, retry or update policy.

The composed retained original October 1 frame and RIO initialized/returned
fixtures each project **324 keys, including 60 SRC keys**, with all three XT
rows ready for the existing mutation scope. These are offline byte/projection
receipts. Eleven missing alias families and uncertain native/live conversions
remain separate work in the [mapping inventory](../../RYTM_MAPPING_STATUS.md).

## Boundaries retained

Capture promotion logs retain fingerprint and omitted/promoted counts. The
report explicitly sets `hardware_access` and `hardware_validation_granted` to
false; registry presence is not readiness. Input-only capture approval does not
authorize output. Target/lock checks, changed paired-control whole-plan refusal,
manual saved-KIT reload and fresh matching capture still govern Studio audition.

V1.34 frozen fixtures and hardware-pinned dependencies remain unchanged. The
software correction does not establish automatic unsaved-state recovery,
general A4/BOTH SEND, Pi boot/ARM64 operation or touring readiness. The running
studio app is not updated merely by producing these artifacts.
