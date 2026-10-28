# Reference Sound Architecture Delta

> Status: in-flight (integrated source; final acceptance pending).

| Boundary | Before | After |
| --- | --- | --- |
| Device codecs/native domains | Existing A4/Rytm verified codecs and source-dependent fields | Reused unchanged through public Device capability; no encoder, offset or registry fork. |
| Analysis | Existing extractor, Audio Patch DNA and isolated A4 analysis worker | Shared strict typed serializer/validators and bounded PCM provenance; packaged spawned runtime repaired. |
| Candidates | Existing A4 inference/eight directions and Rytm proposals | Actual source-preserving native KIT alternatives on both device paths, with semantic/readback and byte-diff proofs. |
| Retention | Existing LibraryStore and canonical atomic writer | Registered reference_sound_store with content-addressed artifacts, typed manifests, OS namespace lock and compare-and-swap publication. |
| Async ownership | Existing authenticated command reader and capture task | Reference analysis shares the bounded off-reader pattern; immutable prepared handoff and cancellation/context checks before owner publication. |
| Errors | Generic fallback for several new refusals | Closed reason vocabulary, fixed private messages and reason-specific logs/counters, including direct guardrail decisions. |
| Frontend | Description/profile compiler, native scopes and Show Kit Forge | Separate Reference sound panel/model/wire DTOs; original/segment/supplied-recording playback, exact alternatives, ranking/refinement/favorites/export/recall. |
| Verification | Existing unit/browser/native lifecycle helpers | Adversarial source/session/worker tests and exact packaged reference journey delegating existing process ownership. |

No new Device Protocol, live sender, automatic restoration or hardware authority
is introduced. The QA script was moved from incorrectly tracked `Scripts` to
canonical `scripts`; no existing legacy PowerShell file moved. Public ownership
and the graph live in [architecture](../../ARCHITECTURE.md) and
[diagrams](../../ARCHITECTURE_DIAGRAMS.md#reference-sound-workflow).
