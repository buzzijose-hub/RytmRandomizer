# Audio Reference Suitability

The audio-reference suitability policy decides which workflows a measured
`AudioFeatureAnalysis` can support. It is a passive evidence gate, not an
artistic-quality score and not a claim that the source can be recreated.

## Workflow lanes

| Lane | Ready evidence | Limited or blocked behavior |
|---|---|---|
| Focused patch DNA | Non-zero focused duration and high-confidence measurement | Long or lower-confidence material is segmented or reviewed first |
| Note-specific synthesis | Dominant pitch, pitch confidence >= 0.75, tonal stability >= 0.60 | Weak pitch remains a hint; missing pitch is blocked |
| Rhythm analysis | Duration >= 0.25 normalized units, measured BPM, tempo stability >= 0.50, rhythmic activity | Short, unstable, or sparse material is limited; missing tempo is blocked |
| Long-form segmentation | Duration reaches the extractor's normalized eight-second ceiling | Sources below the ceiling do not require segmentation under this policy |

Every result includes the measured value, operator, required threshold, and
pass/fail decision for each check. The stable assessment ID hashes the input
identity, policy version, lane decisions, and recommendation.

## Interpretation

`ready` means the evidence clears this policy for that workflow. `limited`
means it may inform interpretation but must not become an unqualified hardware
parameter claim. `blocked` means the required evidence is absent.
`not_applicable` means the workflow is unnecessary for the measured source.

The module performs no audio decoding, file I/O, model inference, MIDI port
enumeration, MIDI/SysEx transmission, or hardware access.
