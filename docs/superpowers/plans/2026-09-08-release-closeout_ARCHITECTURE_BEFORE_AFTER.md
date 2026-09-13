# Release closeout architecture changes

> Status: in-flight — final integration validation pending

Per [PLAN_REQUIREMENTS.md](../../PLAN_REQUIREMENTS.md), Gates 17–18.

| Boundary | Before review | Repaired ownership |
| --- | --- | --- |
| Manifest eligibility | Adapter synthesized metadata, erasing rollout/hardware flags. | `update_transport` preserves plugin `raw_json`; `update_policy` validates it. |
| Artifact identity | A later check could select different bytes. | Retain the checked Update/version/URL/signature and verified bytes until installation. |
| Scheduling | Policy existed without reliable launch/four-hour dispatch. | Monotonic `CheckSchedule` starts after transport attachment; single-flight driver rejects overlap. |
| Consent/lifecycle | UI could acknowledge locally; exit paths diverged. | Native boolean acceptance for exact version/choice, one teardown, supervisor exit before install. |
| State delivery | Frontend could miss startup events or use the wrong event transport. | Shared Tauri listener subscribes then queries snapshot; stale replies cannot overwrite later state. |
| Diagnostics | Optional Updates mount controlled whether activity existed in the UI. | Doctor independently queries the shared snapshot adapter and exports a bounded native journal. |
| Release | Key presence and constructed names implied signed artifacts. | Actual artifact hashes, provenance, native signature sidecars and four-target validation gate manifests. |
| Persisted stores | Library/profile refusal maps were copied. | Pure shared schema/refusal registry; owning stores retain I/O and metrics. Other stores are not implicitly enrolled. |
| Fleet | First page only; “lower bound” understated bias. | Paged release enumeration; report that offline/opt-out undercounts and repeated requests can inflate. |
| Native tests | Browser placeholders bypassed shell/plugin boundaries. | Debug-only Wry/WebView2 fixture uses production shell/IPC/verifier; OS installation is recorded. |

No new MIDI port, SEND, persistent KIT SAVE or device family boundary is added
by the updater. Forge stays in `cockpit/show_bank`; passive Digitakt remains its
own PR and `devices/strategies` change. The primary dirty checkout is preserved.

See [architecture](../../ARCHITECTURE.md#67-desktop-updater-and-release-boundaries),
[diagram](../../ARCHITECTURE_DIAGRAMS.md#desktop-update-components),
[native fixture](../../../desktop/web/native-e2e/README.md) and
[verification report](2026-09-08-release-closeout_RUN_REPORT.md).
