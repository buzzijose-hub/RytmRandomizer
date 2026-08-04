# AL16 R1 Architecture Before and After

> Status: in-flight (PR #222)

| Concern | Before | After |
| --- | --- | --- |
| Recipe facts | No canonical AL16 bank contract | `data.al16_rytm` owns states, pad roles, value domains, and known mappings |
| Export contract | No Rytm evidence result | `Al16RytmKitExportResult` records blocked output and deterministic sidecars |
| File failures | A4-local classifier | Neutral `LocalFileExportErrorCode` is shared by A4 and AL16 adapters |
| Codec use | Existing Rytm codec only | Exporter composes the codec without changing its format contract |
| Hardware boundary | Passive CLI invariant | AL16 imports and tests prove zero MIDI dependency or port access |
| Output safety | Sidecar paths could collide | Canonical path checks reject reference, recipe, output, or sidecar overlap |
| Scope | Future sixteen-kit bank | Phase R1 mechanically permits only the AL02 evidence audit |

No device subpackage, top-level module, MIDI adapter, or alternate codec was
introduced. The registered CLI remains an argument/process adapter; compiler
and evidence orchestration stay under `cockpit/export`.
