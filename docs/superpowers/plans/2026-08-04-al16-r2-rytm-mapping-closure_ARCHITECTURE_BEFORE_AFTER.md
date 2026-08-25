# AL16 R2 Architecture Before and After

> Status: in-flight (PR #224)

| Concern | Before | After |
| --- | --- | --- |
| Requested values | Gap paths survived manifest loading, but requested values were discarded | `MappingGapRequest` preserves each path and its validated requested scalar |
| Observation contract | `candidate_changed` showed only whether bytes differed | Every observation places `requested_semantic_value` beside `configured_bytes` without auto-verdicts |
| Manifest trust | Gap metadata and semantic audits were not joined strictly | Exactly one critical audit must match every gap; missing and duplicate audits fail closed |
| Bounds safety | Slicing could silently truncate an invalid location | Explicit `offset + width <= len(unpacked)` validation rejects invalid canonical facts |
| Report evolution | Report shape was unversioned | Report-level schema version 1 is serialized and tested |
| CLI role | Passive adapter rendered bounded evidence | It remains passive and now reports header-diff counts with typed payload construction |
| Hardware boundary | No MIDI dependency in the workflow | Unchanged: no enumeration, provider construction, port access, or transmission |

No new top-level package, device family, codec, MIDI adapter, or writer was
introduced. The existing strict Rytm codec, Elektron envelope, canonical layout,
and AL16 manifest remain the sources of truth.
