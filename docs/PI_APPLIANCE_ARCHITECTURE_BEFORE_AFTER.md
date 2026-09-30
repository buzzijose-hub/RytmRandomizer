# Pi appliance architecture before and after

Baseline `892aaffc`; implemented checkpoint `97fd6216`. The authoritative
current graph remains [ARCHITECTURE.md](ARCHITECTURE.md) and
[ARCHITECTURE_DIAGRAMS.md](ARCHITECTURE_DIAGRAMS.md).

| Responsibility before | Appliance addition or change | Retained boundary |
| --- | --- | --- |
| Desktop Cockpit React UI and authenticated WS client | `desktop/web/src/appliance/` supplies touch navigation, dialogs, state hooks and optional control intents. | Same production bundle, protocol and full Studio route. |
| Cockpit session, engine, Snapshot/PadDelta, ProfileRegistry, HistoryStore | `cockpit/appliance.py` composes revision-bound scope, candidate, local history and rule profiles; `cockpit/data/appliance.py` owns fixed-shape records. | Existing pure mutation and history services; explicit empty appliance targets do not change legacy empty-target semantics. |
| Saved-KIT capture service and registry-resolved device codecs | `cockpit/capture/appliance_a4.py` projects canonical native fields; `appliance_capabilities.py` joins catalog/provenance/domain facts. Capture accepts a neutral cancellation signal and rejects stale generations. | Device/Strategy and canonical framing; no new automatic request or output capability. |
| Existing device facts and typed A4 field views | `data/appliance_parameter_bindings.py` and `data/device_targets.py` own pure facts; `devices/analog_four_fields.py` exposes the existing public field types. | Frozen `devices/__init__.py` source restored; no duplicate codec, resolver or registry. |
| Existing `dual_machine/targets.py` resolver | Reads the canonical immutable target facts through a deliberately reviewed `dual_machine → data` edge. | Resolver stays public at its original path; no dependency on concrete device families or offending-file allowlist. |
| Existing WebSocket authentication, capture and ArmedApply lifecycle | `cockpit/ws/appliance_handlers.py` validates appliance operations and revisions; server composition seals simulation authority and adds private bootstrap routes through `cockpit/appliance_runtime.py`. | One existing command dispatcher and output seam; no live appliance APPLY based on saved-state evidence. |
| No appliance physical-input bridge | `cockpit/appliance_controls.py` adds `ApplianceInputAdapter`, explicit board configuration, bounded event mapping and the shared UI intent sink. | Input-only Protocol; selected pins required; no MIDI methods. |
| Desktop packaging and Python/frontend tools | `scripts/pi_appliance.py` and `installer-assets/pi-appliance/` add source-bound packaging, private launch, supervised kiosk and verified rollback. | Shared Python source/frontend lockfile; per-user services, preserved profiles, no host boot/firmware mutation. |

New Protocol seams are `ApplianceInputAdapter` and the optional
`CancellableSysexCaptureProvider` extension. The latter accepts a concrete
`threading.Event` cancellation parameter without importing Cockpit into the
MIDI provider. Optional engine arguments supply per-cell native
bounds and depth to the existing engine. Shared strict object validation and
`A4Kit.iter_sounds()` are reused instead of local copies.

No existing public module or device family was deleted or renamed. The proposed
temporary `devices/targets.py` relocation was not retained; the original
resolver remains in `dual_machine/targets.py`. The final change adds no second
envelope, registry, sender, desktop shell or package-root family. Internal helper
renames only clarify their orchestration roles and do not change the public API.

Readable/decoded, previewable, sendable and restorable remain separate
capabilities. The [capability matrix](PI_APPLIANCE_CAPABILITIES.md) is the extension
guide; physical observation must precede any new live-ready claim.
